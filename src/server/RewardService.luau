--[[
RewardService: the free rewards (docs/GAME_DESIGN.md, "Social and events"; GameConfig.Daily, .Group).
Server only.
 - The daily crystal chest (the plaza's DailyPrompt): once a UTC day (DailyClaimDay in the save),
   Daily.IncomeSeconds of the player's crystals per second, at least Daily.Minimum.
 - The group reward: members of the game's group earn +10% crystals (checked on join; the plaza's
   GroupPrompt says whether it's on). Player attribute InGroup.
 - The "Crystals" reward kind (PurchaseRewards), so codes (and later products) can give crystals.
Messages go to the player as GameEvent "Notice".
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage.GameConfig)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local Economy = require(script.Parent.Economy)
local PlayerData = require(script.Parent.PlayerData)
local PlazaService = require(script.Parent.PlazaService)
local PurchaseRewards = require(script.Parent.PurchaseRewards)

local RewardService = {}

local members = {} -- [player] = true for group members
local gameEvent

local function notice(player: Player, text: string)
	gameEvent:FireClient(player, "Notice", { Text = text })
end

function RewardService.Today(now: number?): number
	return (now or os.time()) // 86400
end

function RewardService.DailyAmount(crystalsPerSecond: number): number
	return math.max(GameConfig.Daily.Minimum, math.floor(GameConfig.Daily.IncomeSeconds * crystalsPerSecond))
end

function RewardService.ClaimDaily(player: Player): (boolean, string)
	local data = PlayerData.Edit(player)
	if not data then
		return false, "Your data isn't ready yet."
	end
	local today = RewardService.Today()
	if data.DailyClaimDay >= today then
		local left = 86400 - os.time() % 86400
		return false, `Already opened today. Come back in {left // 3600}h {(left % 3600) // 60}m.`
	end
	local amount = RewardService.DailyAmount(Economy.CrystalsPerSecond(player, data))
	data.DailyClaimDay = today
	Economy.Grant(player, data, amount)
	PlayerData.MarkImportant(player)
	PlayerData.Publish(player)
	return true, `Daily chest: +{NumberFormat.Short(amount)} crystals!`
end

function RewardService.Start()
	gameEvent = ReplicatedStorage:WaitForChild("GameEvent")
	PurchaseRewards.Kinds.Crystals = {
		CanGive = function(player)
			return PlayerData.Edit(player) ~= nil, "Your data isn't ready yet."
		end,
		Give = function(player, reward)
			local data = PlayerData.Edit(player)
			local amount = if type(reward.Amount) == "number" then reward.Amount else 0
			if not data or amount <= 0 then
				return nil, "Couldn't give the crystals."
			end
			Economy.Grant(player, data, amount)
			PlayerData.Publish(player)
			return `{NumberFormat.Short(amount)} crystals`
		end,
	}
	Economy.AddExtra(function(player)
		return if members[player] then 1 + GameConfig.Group.Bonus else 1
	end)
	PlayerData.OnLoaded(function(player)
		local ok, isMember = pcall(player.IsInGroupAsync, player, GameConfig.Group.Id)
		members[player] = if ok and isMember == true then true else nil
		player:SetAttribute("InGroup", members[player] == true)
	end)
	Players.PlayerRemoving:Connect(function(player)
		members[player] = nil
	end)
	local daily = PlazaService.Prompt("DailyPrompt")
	if daily then
		daily.Triggered:Connect(function(player)
			local _, message = RewardService.ClaimDaily(player)
			notice(player, message)
		end)
	end
	local group = PlazaService.Prompt("GroupPrompt")
	if group then
		group.Triggered:Connect(function(player)
			notice(player, if members[player] then "Group member: you earn +10% crystals!" else "Join the game's group for +10% crystals (then rejoin).")
		end)
	end
end

return RewardService
