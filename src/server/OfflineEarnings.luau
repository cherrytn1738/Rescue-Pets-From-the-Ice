--[[
OfflineEarnings: when a player rejoins, they earn for the time they were away. Server only.

 - The time away is the server's clock only: PlayerData's saved LeftAt (os.time() at their last save)
   against os.time() now. It is taken once per session (PlayerData.TakeLeftAt), so it pays once.
 - WHAT earns is the game's: nothing earns until gameplay registers an earner with SetEarner. With no
   earner, nothing is paid and no popup shows.
 - The player's OfflineEarnings attribute ({ Amount, Seconds, Capped, Label, At } as JSON) is what the
   "While you were away" popup shows (OfflineEarningsPopup.client). Display only.

SetEarner(earner): earner(player, data, secondsAway, settings) -> amount, label?
  data is the player's live save (PlayerData.Edit). The earner works out the amount with
  OfflineEarningsRules (Earnings or Plan, with `settings` = OfflineEarningsRules.Settings, so the cap
  applies), puts it into the data itself, and returns the amount and a short label for the popup
  ("coins"). It must not yield: it runs while nothing else changes the data.

Studio: [Offline] lines in Output say how long a joining player counts as away and what they earned.
The Workspace attribute StudioTimeAway (seconds) replaces the real time away for a save that has a
LeftAt (any earlier Play wrote one), to test a long absence. The debug menu's "Offline earnings now"
pays as if away N seconds (Pay).
]]
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local PlayerData = require(script.Parent.PlayerData)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local OfflineEarningsRules = require(ReplicatedStorage.OfflineEarningsRules)

local OfflineEarnings = {}

local SETTINGS = OfflineEarningsRules.Settings
local earner = nil

local function studioLog(message: string)
	if RunService:IsStudio() then
		print("[Offline] " .. message)
	end
end

-- Gameplay calls this once (before PlayerData.Start) with the function that pays for time away.
function OfflineEarnings.SetEarner(callback)
	earner = callback
end

-- Pays the player as if they had been away `secondsAway`. Returns the amount paid (0 for nothing).
function OfflineEarnings.Pay(player: Player, secondsAway: number): number
	local data = PlayerData.Edit(player)
	if not data or type(secondsAway) ~= "number" or secondsAway ~= secondsAway or secondsAway <= 0 then
		return 0
	end
	local away = OfflineEarningsRules.Describe(secondsAway)
	if not earner then
		studioLog(`{player.Name}: away {away}; nothing earns offline yet (no earner set)`)
		return 0
	end
	local ok, amount, label = pcall(earner, player, data, secondsAway, SETTINGS)
	if not ok then
		warn(`[Offline] the earner failed for {player.Name}: {amount}`)
		return 0
	end
	if type(amount) ~= "number" or amount ~= amount or amount <= 0 or amount == math.huge then
		studioLog(`{player.Name}: away {away}, nothing earned`)
		return 0
	end
	label = if type(label) == "string" then label else ""
	PlayerData.MarkImportant(player)
	PlayerData.Publish(player)
	player:SetAttribute("OfflineEarnings", HttpService:JSONEncode({
		Amount = amount,
		Seconds = secondsAway,
		Capped = OfflineEarningsRules.IsCapped(secondsAway, SETTINGS),
		Label = label,
		At = os.time(),
	}))
	studioLog(`{player.Name}: away {away}, earned {NumberFormat.Short(amount)} {label}`)
	return amount
end

local function onLoaded(player: Player)
	local leftAt = PlayerData.TakeLeftAt(player)
	if not leftAt then
		return -- a new player: never away
	end
	local now = os.time()
	local secondsAway = OfflineEarningsRules.SecondsAway(leftAt, now)
	if leftAt > now then
		warn(`[Offline] {player.Name}'s saved leave time is {leftAt - now} s in the future; nothing paid`)
	end
	local fake = Workspace:GetAttribute("StudioTimeAway")
	if RunService:IsStudio() and type(fake) == "number" and fake == fake and fake >= 0 and fake < math.huge then
		studioLog(`StudioTimeAway: {player.Name} counts as away {fake} s (really {secondsAway} s)`)
		secondsAway = math.floor(fake)
	end
	if secondsAway > 0 then
		OfflineEarnings.Pay(player, secondsAway)
	end
end

-- Call before PlayerData.Start, so the first player's load is seen.
function OfflineEarnings.Start()
	PlayerData.OnLoaded(onLoaded)
end

return OfflineEarnings
