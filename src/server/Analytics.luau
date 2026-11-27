--[[
Analytics: sends the game's funnels (AnalyticsConfig) to Roblox's AnalyticsService. Server only.

AnalyticsRules decides which steps to log, so each is logged once and in order:
  * Onboarding: once per player, ever. Its progress is saved (PlayerData `Funnels`), so a rejoin
    never logs a step again.
  * Shops: once per visit. A visit is one funnel session (a GUID), kept in memory only.

Events only record in a published game, so in Studio nothing is sent: each step prints an
`[Analytics]` line instead. Nothing personal is sent: the player object (Roblox needs it), the step
number and AnalyticsConfig's names.

Also (AnalyticsConfig): the two progression funnels (layers reached, rebirth ranks; one funnel session
per player, its id kept in the save), the crystal economy (every source and sink; steady flows are
added up and sent every few minutes) and the Golden Glacier custom events.

Hooks: a "Joined" onboarding step (if AnalyticsConfig has one) is logged when the player's data loads;
gameplay calls Analytics.Onboarding(player, key) for its other steps. RobuxShop calls RobuxPrompted and
RobuxPurchased. The Robux shop window says when it opens or closes and when an INFO button is tapped,
on the ShopVisit RemoteEvent (validated, rate-limited); everything else is something the server saw
itself.
]]
local AnalyticsService = game:GetService("AnalyticsService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local PlayerData = require(script.Parent.PlayerData)
local AnalyticsConfig = require(ReplicatedStorage.AnalyticsConfig)
local AnalyticsRules = require(ReplicatedStorage.AnalyticsRules)
local LayerConfig = require(ReplicatedStorage.LayerConfig)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local NumberFormat = require(ReplicatedStorage.NumberFormat)

local Analytics = {}

local IS_STUDIO = RunService:IsStudio()
local ONBOARDING_STEPS = #AnalyticsConfig.Onboarding

local visits = {} -- [player] = { [shop] = visit } (AnalyticsRules.NewVisit)
local visitRequests = {} -- [player] = { last = os.clock(), times = { os.clock()... } } (ShopVisit rate limit)

local function isPlayer(value): boolean
	return typeof(value) == "Instance" and value:IsA("Player") and value.Parent == Players
end

-- One event to Roblox (never from Studio). A failed call only warns: analytics never breaks gameplay.
local function send(player: Player, description: string, call: () -> ())
	if IS_STUDIO then
		print(`[Analytics] {player.Name}: {description}`)
		return
	end
	local ok, problem = pcall(call)
	if not ok then
		warn(`[Analytics] {description} wasn't sent: {problem}`)
	end
end

local function logOnboarding(player: Player, steps: { number })
	for _, step in steps do
		local name = AnalyticsConfig.Onboarding[step].Name
		send(player, `Onboarding {step} {name}`, function()
			AnalyticsService:LogOnboardingFunnelStepEvent(player, step, name)
		end)
	end
end

local function logFunnel(player: Player, funnel: string, sessionId: string?, stepNames: { string }, steps: { number })
	local visitNote = if sessionId then " (session " .. string.sub(sessionId, 1, 8) .. ")" else ""
	for _, step in steps do
		local name = stepNames[step]
		send(player, `{funnel} {step} {name}{visitNote}`, function()
			AnalyticsService:LogFunnelStepEvent(player, funnel, sessionId, step, name)
		end)
	end
end

-- The player's saved funnel progress, or nil while their data isn't ready.
local function funnels(player: Player)
	local data = isPlayer(player) and PlayerData.Edit(player)
	return data and data.Funnels
end

-- The player reached an onboarding step (an AnalyticsConfig.Onboarding Key). Unknown keys do nothing.
function Analytics.Onboarding(player: Player, key: string)
	local state = funnels(player)
	local step = AnalyticsConfig.OnboardingStep[key]
	if state and step then
		logOnboarding(player, AnalyticsRules.Reach(state, step, ONBOARDING_STEPS))
	end
end

-- Progression ------------------------------------------------------------------------------------

local function logProgress(player: Player, state, funnelKey: string, reached: number)
	local config = AnalyticsConfig.Progression[funnelKey]
	local steps, logged = AnalyticsRules.ProgressSteps(state[funnelKey], reached, #config.Steps)
	if #steps == 0 then
		return
	end
	state[funnelKey] = logged
	state.ProgressId = state.ProgressId or HttpService:GenerateGUID(false)
	logFunnel(player, config.Funnel, state.ProgressId, config.Steps, steps)
end

-- Logs the progression steps the player's save has reached and not logged yet: the layer of their
-- current block level, and the rank of their rebirth count. Call after anything that can raise them
-- (a load, a rescue, a rebirth); it's cheap when nothing is new.
function Analytics.Progress(player: Player)
	local state = funnels(player)
	local data = state and PlayerData.Edit(player)
	if not data then
		return
	end
	local layer = LayerConfig.LayerForLevel(data.BlockLevel, data.MaxLayerOpened)
	if layer then
		logProgress(player, state, "Layers", layer.Number)
	end
	logProgress(player, state, "Ranks", AnalyticsRules.RankStep(data.Rebirths, AnalyticsConfig.Progression.Ranks.Rebirths))
end

-- Economy ----------------------------------------------------------------------------------------

local ECONOMY = AnalyticsConfig.Economy
local pending = {} -- [player] = { [flow .. key .. sku] = { flow, key, sku, amount } } (batched flows)

local function sendEconomy(player: Player, flow: string, key: string, sku: string, amount: number, balance: number)
	local config = if flow == "Source" then ECONOMY.Sources[key] else ECONOMY.Sinks[key]
	local flowType = if flow == "Source" then Enum.AnalyticsEconomyFlowType.Source else Enum.AnalyticsEconomyFlowType.Sink
	balance = math.max(0, balance)
	send(player, `Economy {flow} {ECONOMY.Currency} {NumberFormat.Short(amount)} ({config.TransactionType}, {sku}), balance {NumberFormat.Short(balance)}`, function()
		AnalyticsService:LogEconomyEvent(player, flowType, ECONOMY.Currency, amount, balance, config.TransactionType, sku)
	end)
end

local function addFlow(player: Player, flow: string, key: string, amount: number, sku: string?, balance: number?)
	local config = if flow == "Source" then ECONOMY.Sources[key] else ECONOMY.Sinks[key]
	if not config or not isPlayer(player) or type(amount) ~= "number" or amount ~= amount or amount <= 0 or amount == math.huge then
		return
	end
	sku = string.sub(tostring(config.Sku or sku or key), 1, 50)
	if not config.Batched then
		sendEconomy(player, flow, key, sku, amount, balance or player:GetAttribute("Crystals") or 0)
		return
	end
	local list = pending[player]
	if not list then
		list = {}
		pending[player] = list
	end
	local id = flow .. "|" .. key .. "|" .. sku
	local entry = list[id]
	if entry then
		entry.amount += amount
	else
		list[id] = { flow = flow, key = key, sku = sku, amount = amount }
	end
end

-- Crystals the player just got. source: an AnalyticsConfig.Economy.Sources key; balance: their
-- crystals after it (batched sources use the balance when they're sent); sku: for sources without
-- their own (a code, a product key). Unknown sources (the debug menu) send nothing.
function Analytics.CrystalsEarned(player: Player, source: string, amount: number, balance: number?, sku: string?)
	addFlow(player, "Source", source, amount, sku, balance)
end

-- Crystals the player just spent. sink: "Building" or "Upgrade"; sku: the building or upgrade id.
function Analytics.CrystalsSpent(player: Player, sink: string, amount: number, balance: number?, sku: string?)
	addFlow(player, "Sink", sink, amount, sku, balance)
end

-- Sends the player's batched crystal flows now (every FlushSeconds, when they leave, at shutdown and
-- from the debug menu).
function Analytics.FlushEconomy(player: Player)
	local list = pending[player]
	pending[player] = nil
	if not list then
		return 0
	end
	local balance = player:GetAttribute("Crystals") or 0
	local sent = 0
	for _, entry in list do
		sendEconomy(player, entry.flow, entry.key, entry.sku, entry.amount, balance)
		sent += 1
	end
	return sent
end

-- Custom events ----------------------------------------------------------------------------------

-- A custom event (AnalyticsConfig.Custom key), with an optional value and CustomField01 text.
function Analytics.Custom(player: Player, key: string, value: number?, field: string?)
	local name = AnalyticsConfig.Custom[key]
	if not name or not isPlayer(player) then
		return
	end
	local fields = if field then { [Enum.AnalyticsCustomFieldKeys.CustomField01.Name] = field } else nil
	send(player, `Custom {name} {tostring(value or 1)}{if field then " (" .. field .. ")" else ""}`, function()
		AnalyticsService:LogCustomEvent(player, name, value or 1, fields)
	end)
end

-- Shops ------------------------------------------------------------------------------------------

local function shopStep(player: Player, shop: string, visit, step: number)
	local config = AnalyticsConfig.Shops[shop]
	logFunnel(player, config.Funnel, visit.Id, config.Steps, AnalyticsRules.VisitStep(visit, step, #config.Steps))
end

-- A new visit to `shop` (an AnalyticsConfig.Shops key, "Robux"): a new funnel session, step 1 logged.
function Analytics.ShopOpened(player: Player, shop: string)
	local config = AnalyticsConfig.Shops[shop]
	if not config or not isPlayer(player) then
		return
	end
	local visit, steps = AnalyticsRules.NewVisit(HttpService:GenerateGUID(false))
	visits[player] = visits[player] or {}
	visits[player][shop] = visit
	logFunnel(player, config.Funnel, visit.Id, config.Steps, steps)
end

local function currentVisit(player: Player, shop: string, mustBeOpen: boolean)
	local visit = visits[player] and visits[player][shop]
	if visit and (visit.Open or not mustBeOpen) then
		return visit
	end
	return nil
end

-- The Robux shop's purchase prompt opened for `key` (a product or pass key). Counts only while the
-- shop window is open (a popup elsewhere that prompts the same item doesn't count).
function Analytics.RobuxPrompted(player: Player, key: string)
	local visit = currentVisit(player, "Robux", true)
	if visit then
		visit.Prompted[key] = true
		shopStep(player, "Robux", visit, 3)
	end
end

-- A purchase prompt for `key` closed with a purchase. Counts for the visit that opened it, even if
-- the window was closed meanwhile.
function Analytics.RobuxPurchased(player: Player, key: string)
	local visit = currentVisit(player, "Robux", false)
	if visit and visit.Prompted[key] then
		shopStep(player, "Robux", visit, 4)
	end
end

local NEW_VISIT_SECONDS = 15
local lastOpenAt = {} -- [player] = os.clock() of their last counted shop visit

-- The ShopVisit RemoteEvent: (action "Open" | "Close" | "Info", shop "Robux", key for Info).
local function rateOk(player: Player): boolean
	local now = os.clock()
	local entry = visitRequests[player] or { last = -math.huge, times = {} }
	visitRequests[player] = entry
	if now - entry.last < AnalyticsConfig.VisitRate.MinSeconds then
		return false
	end
	while entry.times[1] and now - entry.times[1] > 60 do
		table.remove(entry.times, 1)
	end
	if #entry.times >= AnalyticsConfig.VisitRate.PerMinute then
		return false
	end
	entry.last = now
	table.insert(entry.times, now)
	return true
end

local function onVisit(player: Player, action, shop, key)
	if shop ~= "Robux" or type(action) ~= "string" or not rateOk(player) then
		return
	end
	if action == "Open" then
		-- one visit at a time, and a new one at most every NEW_VISIT_SECONDS (a spammed "Open" can't inflate
		-- the funnel or spend the analytics budget)
		local now = os.clock()
		if currentVisit(player, "Robux", true) or now - (lastOpenAt[player] or -math.huge) < NEW_VISIT_SECONDS then
			return
		end
		lastOpenAt[player] = now
		Analytics.ShopOpened(player, "Robux")
	elseif action == "Close" then
		local visit = currentVisit(player, "Robux", true)
		if visit then
			visit.Open = false
		end
	elseif action == "Info" then
		if type(key) ~= "string" or #key > 32 or not (MonetizationConfig.GetProduct(key) or MonetizationConfig.GetPass(key)) then
			return
		end
		local visit = currentVisit(player, "Robux", true)
		if visit then
			shopStep(player, "Robux", visit, 2)
		end
	end
end

-- Call before PlayerData.Start, so the first player's load is seen.
function Analytics.Start()
	PlayerData.OnLoaded(function(player)
		Analytics.Onboarding(player, "Joined")
		Analytics.Progress(player)
	end)
	local remote = ReplicatedStorage:WaitForChild("ShopVisit") :: RemoteEvent
	remote.OnServerEvent:Connect(onVisit)
	Players.PlayerRemoving:Connect(function(player)
		Analytics.FlushEconomy(player)
		visits[player], visitRequests[player], lastOpenAt[player] = nil, nil, nil
	end)
	-- batched crystal flows: every FlushSeconds, and at shutdown
	task.spawn(function()
		while true do
			task.wait(ECONOMY.FlushSeconds)
			for _, player in Players:GetPlayers() do
				Analytics.FlushEconomy(player)
			end
		end
	end)
	game:BindToClose(function()
		for _, player in Players:GetPlayers() do
			Analytics.FlushEconomy(player)
		end
	end)
end

return Analytics
