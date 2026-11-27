--[[
GoldenGlacierService: the Golden Glacier rush (docs/GAME_DESIGN.md, "Social and events";
GameConfig.GoldenGlacier). Server only.

Every 5-8 minutes a golden block falls into the plaza's landing ring after a countdown (everyone is
told). While it stands, taps near it (GoldenTap, the same 20-a-second cap as the ice) knock its HP down.
When it breaks, everyone who tapped it gets a Frost Rush (x3 crystals for 60 s) and whoever tapped it
most gets x5. Nobody breaks it in time: it melts, no rush. The state is on Workspace.GoldenGlacier's
attributes (State "Idle" | "Countdown" | "Active", LandsAt, EndsAt, Hp, HpMax) for every client to draw;
a player's rush is on their FrostRushEndsAt / FrostRushMultiplier attributes (server clock).
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage.GameConfig)
local Analytics = require(script.Parent.Analytics)
local Economy = require(script.Parent.Economy)
local PlazaService = require(script.Parent.PlazaService)
local TapService = require(script.Parent.TapService)

local GoldenGlacierService = {}

local SETTINGS = GameConfig.GoldenGlacier
local state -- the Folder with the attributes
local contributions = {} -- [player] = taps this block
local rushes = {} -- [player] = { endsAt = os.clock() time, multiplier }
local gameEvent
local random = Random.new()
local spawnNow = false
local listeners = {}

-- callback(player, multiplier) when a player gets a Frost Rush.
function GoldenGlacierService.OnRush(callback)
	table.insert(listeners, callback)
end

function GoldenGlacierService.RushMultiplier(player: Player): number
	local rush = rushes[player]
	if rush and os.clock() < rush.endsAt then
		return rush.multiplier
	end
	return 1
end

local function giveRush(player: Player, multiplier: number)
	rushes[player] = { endsAt = os.clock() + SETTINGS.RushSeconds, multiplier = multiplier }
	player:SetAttribute("FrostRushEndsAt", Workspace:GetServerTimeNow() + SETTINGS.RushSeconds)
	player:SetAttribute("FrostRushMultiplier", multiplier)
	for _, callback in listeners do
		task.spawn(callback, player, multiplier)
	end
end

local function nearBlock(player: Player): boolean
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	return root ~= nil and (root.Position - PlazaService.GoldenSpot).Magnitude <= SETTINGS.Radius
end

local function onTap(player: Player, count)
	if state:GetAttribute("State") ~= "Active" then
		return
	end
	if type(count) ~= "number" or count ~= count or count % 1 ~= 0 or count < 1 or count > 1000 or not nearBlock(player) then
		return
	end
	local allowed = TapService.Allow(player, count)
	if allowed <= 0 then
		return
	end
	if not contributions[player] then
		Analytics.Custom(player, "GlacierJoined")
	end
	contributions[player] = (contributions[player] or 0) + allowed
	state:SetAttribute("Hp", math.max(0, state:GetAttribute("Hp") - allowed))
end

-- One golden block, start to finish. Returns when it breaks or melts.
local function runBlock()
	table.clear(contributions)
	local players = #Players:GetPlayers()
	local hp = SETTINGS.TapsPerPlayer * math.max(1, players)
	local now = Workspace:GetServerTimeNow()
	state:SetAttribute("HpMax", hp)
	state:SetAttribute("Hp", hp)
	state:SetAttribute("LandsAt", now + SETTINGS.CountdownSeconds)
	state:SetAttribute("EndsAt", now + SETTINGS.CountdownSeconds + SETTINGS.ActiveSeconds)
	state:SetAttribute("State", "Countdown")
	gameEvent:FireAllClients("Golden", { Text = `A Golden Glacier lands in the plaza in {SETTINGS.CountdownSeconds} seconds!` })
	task.wait(SETTINGS.CountdownSeconds)
	state:SetAttribute("State", "Active")
	local deadline = os.clock() + SETTINGS.ActiveSeconds
	while os.clock() < deadline and state:GetAttribute("Hp") > 0 do
		task.wait(0.1)
	end
	if state:GetAttribute("Hp") > 0 then
		local tappers = 0
		for _ in contributions do
			tappers += 1
		end
		for player in contributions do
			if player.Parent == Players then
				Analytics.Custom(player, "GlacierEscaped", tappers)
			end
		end
		state:SetAttribute("State", "Idle")
		gameEvent:FireAllClients("Golden", { Text = "The Golden Glacier melted away..." })
		return
	end
	-- broken: a rush for everyone who tapped it, x5 for the top tapper
	local top, topTaps = nil, 0
	for player, taps in contributions do
		if taps > topTaps and player.Parent == Players then
			top, topTaps = player, taps
		end
	end
	for player in contributions do
		if player.Parent == Players then
			local multiplier = if player == top then SETTINGS.TopMultiplier else SETTINGS.RushMultiplier
			giveRush(player, multiplier)
			Analytics.Custom(player, "GlacierWon", multiplier, if player == top then "Place - Top" else "Place - Helper")
		end
	end
	state:SetAttribute("State", "Idle")
	state:SetAttribute("Broken", (state:GetAttribute("Broken") or 0) + 1)
	gameEvent:FireAllClients("Golden", {
		Text = if top then `The Golden Glacier broke! Frost Rush for everyone who tapped it, x{SETTINGS.TopMultiplier} for {top.DisplayName}!` else "The Golden Glacier broke!",
		Broken = true,
	})
	print(`[Golden] broken by {#Players:GetPlayers()} player(s); top: {top and top.Name or "nobody"} ({topTaps} taps)`)
end

-- Debug: the next golden block falls now.
function GoldenGlacierService.SpawnNow(): boolean
	if state:GetAttribute("State") ~= "Idle" then
		return false
	end
	spawnNow = true
	return true
end

function GoldenGlacierService.Start()
	gameEvent = ReplicatedStorage:WaitForChild("GameEvent")
	state = Instance.new("Folder")
	state.Name = "GoldenGlacier"
	state:SetAttribute("State", "Idle")
	state:SetAttribute("Spot", PlazaService.GoldenSpot)
	state.Parent = Workspace
	ReplicatedStorage:WaitForChild("GoldenTap").OnServerEvent:Connect(onTap)
	Economy.AddExtra(GoldenGlacierService.RushMultiplier, true, "GoldenGlacier")
	Players.PlayerRemoving:Connect(function(player)
		contributions[player] = nil
		rushes[player] = nil
	end)
	task.spawn(function()
		while true do
			local waitUntil = os.clock() + random:NextNumber(SETTINGS.MinSeconds, SETTINGS.MaxSeconds)
			while os.clock() < waitUntil and not spawnNow do
				task.wait(0.5)
			end
			spawnNow = false
			if #Players:GetPlayers() > 0 then
				local ok, err = pcall(runBlock)
				if not ok then
					warn("[Golden] " .. tostring(err))
					state:SetAttribute("State", "Idle")
				end
			end
		end
	end)
end

return GoldenGlacierService
