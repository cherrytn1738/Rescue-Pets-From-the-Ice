--[[
WelcomeBack: the Welcome Back screen's "x2" offer, the developer product Double Welcome Back
(MonetizationConfig "DoubleWelcomeBack", reward kind WelcomeBackDouble). Server only. The rules are
WelcomeBackRules (pure, specced); this module applies them to the player's save.

 * When offline earnings are paid (OfflineEarnings.OnPaid), the offer is saved in data.WelcomeBack: the amount
   just paid and the time. The player attribute WelcomeBackOffer ({ Amount, Until } as JSON, or nil) tells the
   screen whether to show the x2 button, and until when.
 * x2 goes through the shop's normal purchase request (PurchaseRequest "Buy"): CanGive with { Prompting = true }
   checks the offer is open, OnPrompt marks it prompted (saved soon after), OnPromptFinished reopens it if the
   player didn't buy. The receipt (Receipts) pays the prompted offer's saved amount once and removes the offer.
 * Claim! (PurchaseRequest "CloseOffer") closes an offer that isn't prompted.
The base amount was already paid at join, as before; the x2 pays the same amount again.
]]
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local NumberFormat = require(ReplicatedStorage.NumberFormat)
local WelcomeBackRules = require(ReplicatedStorage.WelcomeBackRules)
local Economy = require(script.Parent.Economy)
local OfflineEarnings = require(script.Parent.OfflineEarnings)
local PlayerData = require(script.Parent.PlayerData)
local PurchaseRewards = require(script.Parent.PurchaseRewards)

local WelcomeBack = {}

local function publish(player: Player, data)
	local view = WelcomeBackRules.View(data and data.WelcomeBack, os.time())
	player:SetAttribute("WelcomeBackOffer", if view then HttpService:JSONEncode(view) else nil)
end

local function offerOf(player: Player)
	local data = PlayerData.Edit(player)
	return data, data and data.WelcomeBack
end

PurchaseRewards.Kinds.WelcomeBackDouble = {
	-- Prompting: x2 can be offered now. A receipt: there is a prompted offer to pay.
	CanGive = function(player, _, context)
		local _, offer = offerOf(player)
		if context.Prompting then
			local problem = WelcomeBackRules.PromptProblem(offer, os.time())
			return problem == nil, problem
		end
		local amount, problem = WelcomeBackRules.Grant(offer)
		return amount ~= nil, problem
	end,
	-- The receipt: the offer's saved amount, once (no yields; Receipts records the receipt and saves).
	Give = function(player, _, context)
		local data, offer = offerOf(player)
		local amount, problem = WelcomeBackRules.Grant(offer)
		if not amount then
			return nil, problem
		end
		data.WelcomeBack = nil
		Economy.Grant(player, data, amount, "Bundle", context.Key)
		publish(player, data)
		return `{NumberFormat.Short(amount)} crystals`
	end,
	OnPrompt = function(player)
		local data, offer = offerOf(player)
		if offer and WelcomeBackRules.IsOpen(offer, os.time()) then
			WelcomeBackRules.Prompt(offer, os.time())
			PlayerData.MarkImportant(player) -- saved, so a receipt after a server stop still finds it
			publish(player, data)
		end
	end,
	OnPromptFinished = function(player, _, purchased)
		local data, offer = offerOf(player)
		if offer then
			WelcomeBackRules.PromptClosed(offer, purchased)
			publish(player, data)
		end
	end,
	-- Claim!: the screen closed without buying.
	OnClose = function(player)
		local data, offer = offerOf(player)
		if data then
			data.WelcomeBack = WelcomeBackRules.Claim(offer)
			publish(player, data)
		end
		return true
	end,
}

-- Call before PlayerData.Start (with OfflineEarnings.Start), so the first player's payout is seen.
function WelcomeBack.Start()
	OfflineEarnings.OnPaid(function(player, data, amount)
		data.WelcomeBack = WelcomeBackRules.Make(data.WelcomeBack, amount, os.time())
		publish(player, data)
	end)
	-- After the payout (registered later): an old offer that isn't open or pending any more is dropped.
	PlayerData.OnLoaded(function(player)
		local data, offer = offerOf(player)
		if data and offer and not WelcomeBackRules.IsOpen(offer, os.time()) and not WelcomeBackRules.IsPending(offer, os.time()) then
			data.WelcomeBack = nil
		end
		publish(player, data)
	end)
end

return WelcomeBack
