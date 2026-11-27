--[[
Economy: crystals on the server (docs/GAME_DESIGN.md, "Economy" and "Technical design"). Server only.

 - Grant(player, amount): adds crystals (and to this run's and all-time totals).
 - Multiplier(player): EconomyRules.Multiplier from the save, times the server-only extras (game
   passes, Frost Rush, the group bonus): other systems register those with AddExtra.
 - The server tick (GameConfig.TicksPerSecond): every building's damage goes into the player's block
   (IceBlockService.Damage, which pays the crystals), and the display attributes are refreshed:
   Crystals and CrystalsPerSecond (building damage/s plus the player's recent tapping, times the
   multiplier).
 - Offline earnings: building income only, at OfflineEarningsRules.Settings (50%, 2 hours).
 - Tap rate: RecordTaps(player, taps) keeps the last few seconds of taps for crystals/s.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local AnalyticsRules = require(ReplicatedStorage.AnalyticsRules)
local EconomyRules = require(ReplicatedStorage.EconomyRules)
local GameConfig = require(ReplicatedStorage.GameConfig)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local OfflineEarningsRules = require(ReplicatedStorage.OfflineEarningsRules)
local OfflineEarnings = require(script.Parent.OfflineEarnings)
local PlayerData = require(script.Parent.PlayerData)

local Economy = {}

local MAX_CRYSTALS = 1e300 -- PlayerData's MAX_AMOUNT
local extras = {} -- { { callback = function(player) -> multiplier, temporary = boolean, source = string? } }
local grantListeners = {}
-- crystals from these sources are multiplied by the rushes running, so the rushes' share is reported
-- under the rush's own source (analytics)
local BOOSTED = { Taps = true, AutoPick = true, Buildings = true, Rescue = true }
local tapLog = {} -- [player] = { { time, taps } }
local tickListeners = {}

-- A server-only crystal multiplier source: callback(player) -> number (1 = none). temporary: a rush
-- (the Golden Glacier's Frost Rush, the Server Frost Rush), left out of SteadyIncome. source: a rush's
-- name for analytics (the crystals it adds are reported as coming from it).
function Economy.AddExtra(callback, temporary: boolean?, source: string?)
	table.insert(extras, { callback = callback, temporary = temporary == true, source = source })
end

-- callback(player, source, amount, balance, sku) after every Grant that names its source (analytics).
-- A boosted grant made while rushes run is reported in parts: each rush's share under its own source.
function Economy.OnGrant(callback)
	table.insert(grantListeners, callback)
end

local function reportGrant(player: Player, source: string, amount: number, balance: number, sku: string?)
	local parts = { { Source = source, Amount = amount } }
	if BOOSTED[source] then
		local rushes = {}
		for _, extra in extras do
			if extra.temporary and extra.source then
				local ok, value = pcall(extra.callback, player)
				if ok and type(value) == "number" and value > 1 and value < math.huge then
					table.insert(rushes, { Source = extra.source, Multiplier = value })
				end
			end
		end
		for _, share in AnalyticsRules.RushShares(rushes) do
			table.insert(parts, { Source = share.Source, Amount = amount * share.Share })
			parts[1].Amount -= amount * share.Share
		end
	end
	for _, callback in grantListeners do
		for _, part in parts do
			local ok, err = pcall(callback, player, part.Source, part.Amount, balance, sku)
			if not ok then
				warn("[Economy] grant listener failed: " .. tostring(err))
			end
		end
	end
end

function Economy.ExtraMultiplier(player: Player, permanentOnly: boolean?): number
	local total = 1
	for _, extra in extras do
		if permanentOnly and extra.temporary then
			continue
		end
		local ok, value = pcall(extra.callback, player)
		if ok and type(value) == "number" and value == value and value > 0 and value < math.huge then
			total *= value
		end
	end
	return total
end

function Economy.Multiplier(player: Player, data): number
	return EconomyRules.Multiplier(data, Economy.ExtraMultiplier(player))
end

-- The multiplier without any rush running: pets, book, Crystal Yield, Frost Cores, passes, group.
function Economy.PermanentMultiplier(player: Player, data): number
	return EconomyRules.Multiplier(data, Economy.ExtraMultiplier(player, true))
end

-- Adds crystals to the live save. amount must be a real, non-negative number. source (optional): where
-- they came from, for analytics (an AnalyticsConfig.Economy.Sources key); sku: its item, if any.
function Economy.Grant(player: Player, data, amount: number, source: string?, sku: string?)
	if type(amount) ~= "number" or amount ~= amount or amount <= 0 or amount == math.huge then
		return
	end
	-- (capped at MAX_CRYSTALS: the save refuses amounts above it, which would stop the player's session)
	data.Crystals = math.min(MAX_CRYSTALS, data.Crystals + amount)
	data.CrystalsThisRun = math.min(MAX_CRYSTALS, data.CrystalsThisRun + amount)
	data.CrystalsAllTime = math.min(MAX_CRYSTALS, data.CrystalsAllTime + amount)
	if source and #grantListeners > 0 then
		reportGrant(player, source, amount, data.Crystals, sku)
	end
end

-- Spends crystals. Returns false (and spends nothing) if the player can't afford it.
function Economy.Spend(data, cost: number): boolean
	if type(cost) ~= "number" or cost ~= cost or cost < 0 or data.Crystals < cost then
		return false
	end
	data.Crystals = math.max(0, data.Crystals - cost)
	return true
end

function Economy.RecordTaps(player: Player, taps: number)
	local log = tapLog[player]
	if not log then
		log = {}
		tapLog[player] = log
	end
	table.insert(log, { os.clock(), taps })
end

-- Taps per second over the last RateWindowSeconds.
function Economy.TapRate(player: Player): number
	local log = tapLog[player]
	if not log then
		return 0
	end
	local window = GameConfig.Taps.RateWindowSeconds
	local since = os.clock() - window
	while log[1] and log[1][1] < since do
		table.remove(log, 1)
	end
	local taps = 0
	for _, entry in log do
		taps += entry[2]
	end
	return taps / window
end

-- What the HUD shows as crystals per second.
function Economy.CrystalsPerSecond(player: Player, data): number
	local damage = EconomyRules.TotalBuildingDps(data) + Economy.TapRate(player) * EconomyRules.TapDamage(data)
	return damage * Economy.Multiplier(player, data)
end

-- "Your income" for crystal bundles and the daily chest: the HUD's crystals per second without rushes
-- (permanent bonuses only). Taps count at the player's recent rate, but at least
-- MonetizationConfig.BundleTapsPerSecond, so opening the shop (and so stopping tapping) or being new
-- with no buildings doesn't pay nothing.
function Economy.SteadyIncome(player: Player, data): number
	local taps = math.max(Economy.TapRate(player), MonetizationConfig.BundleTapsPerSecond)
	local damage = EconomyRules.TotalBuildingDps(data) + taps * EconomyRules.TapDamage(data)
	return damage * Economy.PermanentMultiplier(player, data)
end

-- callback(player, data, dt) runs every tick for every ready player (IceBlockService applies the
-- building damage here).
function Economy.OnTick(callback)
	table.insert(tickListeners, callback)
end

local function tick(dt: number)
	for _, player in Players:GetPlayers() do
		local data = PlayerData.Edit(player)
		if data then
			for _, callback in tickListeners do
				local ok, err = pcall(callback, player, data, dt)
				if not ok then
					warn("[Economy] tick failed: " .. tostring(err))
				end
			end
			player:SetAttribute("Crystals", data.Crystals)
			player:SetAttribute("CrystalsPerSecond", Economy.CrystalsPerSecond(player, data))
		end
	end
end

function Economy.Start()
	Players.PlayerRemoving:Connect(function(player)
		tapLog[player] = nil
	end)
	-- Offline: building income only (taps don't earn while away), at the settings' rate and cap.
	OfflineEarnings.SetEarner(function(player, data, secondsAway, settings)
		local income = EconomyRules.TotalBuildingDps(data) * Economy.Multiplier(player, data)
		local amount = OfflineEarningsRules.Earnings(income, secondsAway, settings)
		if amount > 0 then
			Economy.Grant(player, data, amount, "Offline")
		end
		return amount, "crystals"
	end)
	task.spawn(function()
		local step = 1 / GameConfig.TicksPerSecond
		local last = os.clock()
		while true do
			task.wait(step)
			local now = os.clock()
			tick(math.min(now - last, 1))
			last = now
		end
	end)
end

return Economy
