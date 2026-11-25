--[[
RobuxPerks: what every Robux item does (docs/GAME_DESIGN.md, "Monetization"; the items and their numbers are
in MonetizationConfig). Server only.

Reward kinds (PurchaseRewards.Kinds: bought, gifted, simulated and code rewards all come through these; Give
never yields and never saves, the caller records the receipt and saves):
 * Pass: a pass received as a gift: saved in the recipient's GiftedPasses (GamePasses.GiveGifted).
 * CrystalBundle: Seconds of the player's steady income (Economy.SteadyIncome: no rushes).
 * ShatterNow: breaks the block on their mound now (refused while the next block is still on its sled).
 * ServerFrostRush: x Multiplier crystals for everyone in this server for Seconds, the buyer's name announced;
   another one while it runs adds Seconds (MonetizationRules.RushEndsAt). Not saved: it ends with the server.
 * MythicBlock: one more Mythic Block waiting (data.MythicBlocks); IceBlockService rolls the next block from
   its odds.
Pass perks (GamePasses.Owns, so a bought, gifted or Studio-given pass all count):
 * CrystalMultiplier (2x Crystals, VIP) through Economy.AddExtra; Lucky (Lucky Ice) through
   IceBlockService.AddLuck; AutoTapsPerSecond (Auto Pick): every tick, the server taps for the player while
   they're in their own plot (TapService.AutoTaps, inside the same 20-a-second cap). The VIP name tag is
   RankService's, the lounge door PlazaService's and VipLounge.client's; pet slots PetService's.
The Server Frost Rush is on Workspace attributes ServerRushEndsAt (server clock), ServerRushMultiplier and
ServerRushBy (the HUD shows it).
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local MonetizationRules = require(ReplicatedStorage.MonetizationRules)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local Economy = require(script.Parent.Economy)
local GamePasses = require(script.Parent.GamePasses)
local IceBlockService = require(script.Parent.IceBlockService)
local PlayerData = require(script.Parent.PlayerData)
local PlotService = require(script.Parent.PlotService)
local PurchaseRewards = require(script.Parent.PurchaseRewards)
local TapService = require(script.Parent.TapService)

local RobuxPerks = {}

local serverRush = { endsAt = 0, multiplier = 1, by = "" } -- os.clock() time
local autoTapCarry = {} -- [player] = the fraction of an Auto Pick tap not landed yet

-- The product of every owned pass's CrystalMultiplier (1 = none).
function RobuxPerks.PassMultiplier(player: Player): number
	local total = 1
	for _, pass in MonetizationConfig.Passes do
		if pass.CrystalMultiplier and GamePasses.Owns(player, pass.Key) then
			total *= pass.CrystalMultiplier
		end
	end
	return total
end

function RobuxPerks.AutoTapsPerSecond(player: Player): number
	local rate = 0
	for _, pass in MonetizationConfig.Passes do
		if pass.AutoTapsPerSecond and GamePasses.Owns(player, pass.Key) then
			rate += pass.AutoTapsPerSecond
		end
	end
	return rate
end

function RobuxPerks.IsLucky(player: Player): boolean
	for _, pass in MonetizationConfig.Passes do
		if pass.Lucky and GamePasses.Owns(player, pass.Key) then
			return true
		end
	end
	return false
end

-- The Server Frost Rush's multiplier now (1 when none is running).
function RobuxPerks.ServerRushMultiplier(): number
	return if os.clock() < serverRush.endsAt then serverRush.multiplier else 1
end

-- What a crystal bundle of `seconds` pays this player now: their steady income (no rushes).
function RobuxPerks.BundleAmount(player: Player, data, seconds: number): number
	return MonetizationRules.BundleCrystals(Economy.SteadyIncome(player, data), seconds)
end

-- Starts (or lengthens) the Server Frost Rush. byName: who is announced.
function RobuxPerks.StartServerRush(multiplier: number, seconds: number, byName: string)
	local now = os.clock()
	local wasRunning = now < serverRush.endsAt
	serverRush.endsAt = MonetizationRules.RushEndsAt(now, serverRush.endsAt, seconds)
	serverRush.multiplier = if wasRunning then math.max(serverRush.multiplier, multiplier) else multiplier
	serverRush.by = byName
	Workspace:SetAttribute("ServerRushEndsAt", Workspace:GetServerTimeNow() + (serverRush.endsAt - now))
	Workspace:SetAttribute("ServerRushMultiplier", serverRush.multiplier)
	Workspace:SetAttribute("ServerRushBy", byName)
	local event = ReplicatedStorage:FindFirstChild("GameEvent")
	if event then
		event:FireAllClients("ServerRush", {
			By = byName,
			Multiplier = serverRush.multiplier,
			Minutes = math.floor(seconds / 60 + 0.5),
			Extended = wasRunning,
		})
	end
	print(`[Purchase] Server Frost Rush by {byName}: x{serverRush.multiplier} until {math.floor(serverRush.endsAt - now)} s from now`)
end

local Kinds = PurchaseRewards.Kinds

Kinds.Pass = {
	CanGive = function(player, reward)
		local pass = MonetizationConfig.GetPass(reward.Pass)
		if not pass then
			return false, PurchaseRewards.UNKNOWN_KIND
		end
		if GamePasses.Owns(player, pass.Key) then
			return false, `{player.DisplayName} already has {pass.Name}.`
		end
		return true
	end,
	Give = function(player, reward)
		local pass = MonetizationConfig.GetPass(reward.Pass)
		local data = PlayerData.Edit(player)
		GamePasses.GiveGifted(player, data, pass.Key)
		return `the {pass.Name} pass`
	end,
}

Kinds.CrystalBundle = {
	CanGive = function(_, reward)
		return type(reward.Seconds) == "number" and reward.Seconds > 0, PurchaseRewards.UNKNOWN_KIND
	end,
	Give = function(player, reward)
		local data = PlayerData.Edit(player)
		local amount = RobuxPerks.BundleAmount(player, data, reward.Seconds)
		Economy.Grant(player, data, amount)
		return `{NumberFormat.Short(amount)} crystals`
	end,
}

Kinds.ShatterNow = {
	CanGive = function(player)
		if not IceBlockService.CanShatter(player) then
			return false, "Wait for your next block to arrive, then shatter it."
		end
		return true
	end,
	Give = function(player)
		local rarity = IceBlockService.Rarity(player)
		if not IceBlockService.Shatter(player) then
			return nil, "Wait for your next block to arrive, then shatter it."
		end
		return `your {rarity or ""} block, shattered`
	end,
}

Kinds.ServerFrostRush = {
	CanGive = function(_, reward)
		return type(reward.Multiplier) == "number" and type(reward.Seconds) == "number", PurchaseRewards.UNKNOWN_KIND
	end,
	Give = function(player, reward, context)
		local name = player.DisplayName
		if context and context.giftFrom then
			name = `{player.DisplayName} (a gift from {context.giftFrom})`
		end
		RobuxPerks.StartServerRush(reward.Multiplier, reward.Seconds, name)
		return `a Server Frost Rush (x{reward.Multiplier} for everyone, {math.floor(reward.Seconds / 60)} minutes)`
	end,
}

Kinds.MythicBlock = {
	Give = function(player)
		local data = PlayerData.Edit(player)
		data.MythicBlocks += 1
		return if data.MythicBlocks > 1 then `a Mythic Block ({data.MythicBlocks} waiting)` else "a Mythic Block (your next block)"
	end,
}

function RobuxPerks.Start()
	Economy.AddExtra(RobuxPerks.PassMultiplier)
	Economy.AddExtra(RobuxPerks.ServerRushMultiplier, true)
	IceBlockService.AddLuck(RobuxPerks.IsLucky)
	-- Auto Pick: the server taps for you while you're in your own plot, inside the 20-a-second cap.
	Economy.OnTick(function(player, _, dt)
		local rate = RobuxPerks.AutoTapsPerSecond(player)
		if rate <= 0 or not PlotService.InOwnPlot(player) then
			autoTapCarry[player] = nil
			return
		end
		local pending = (autoTapCarry[player] or 0) + rate * dt
		local whole = math.floor(pending)
		autoTapCarry[player] = pending - whole
		if whole > 0 then
			TapService.AutoTaps(player, whole)
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		autoTapCarry[player] = nil
	end)
end

return RobuxPerks
