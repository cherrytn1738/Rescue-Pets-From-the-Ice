--[[
Analytics: sends the game's funnels (AnalyticsConfig) to Roblox's AnalyticsService. Server only.

AnalyticsRules decides which steps to log, so each is logged once and in order:
  * Onboarding: once per player, ever. Its progress is saved (PlayerData `Funnels`), so a rejoin
    never logs a step again.
  * Shops: once per visit. A visit is one funnel session (a GUID), kept in memory only.

Events only record in a published game, so in Studio nothing is sent: each step prints an
`[Analytics]` line instead. Nothing personal is sent: the player object (Roblox needs it), the step
number and AnalyticsConfig's names.

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
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)

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
	local visitNote = if sessionId then " (visit " .. string.sub(sessionId, 1, 8) .. ")" else ""
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
	end)
	local remote = ReplicatedStorage:WaitForChild("ShopVisit") :: RemoteEvent
	remote.OnServerEvent:Connect(onVisit)
	Players.PlayerRemoving:Connect(function(player)
		visits[player], visitRequests[player] = nil, nil
	end)
end

return Analytics
