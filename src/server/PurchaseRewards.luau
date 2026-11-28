--[[
PurchaseRewards: turns a Robux product's configured reward (or a promo code's) into a change in the
game. Bought, gifted, simulated (Studio, debug) purchases and codes all come through here, so a gift
gives exactly what buying it gives. Server only.

 * CanGive(player, product, context) -> true, or false and a message: whether it would apply RIGHT
   NOW. The shop checks it before opening Roblox's prompt, and Give checks it again, because things
   change between the prompt and the receipt.
 * Give(player, product, context) -> what was given (a short text), or nil and a message. Never
   yields and never saves: the caller records the receipt (or code) and saves, so the grant and its
   record are written together. nil means "can't apply now": the receipt answers NotProcessedYet and
   Roblox tries again later, instead of taking Robux for nothing.
 * A paid random item never applies to a player whose region restricts paid random items
   (PaidRandomPolicy).

Reward kinds: a product's Reward = { Kind = "...", ... } names a kind registered in
PurchaseRewards.Kinds. The game has none yet (no currency or items exist); each system that can be
sold registers its own kind, for example:

	PurchaseRewards.Kinds.Coins = {
		CanGive = function(player, reward, context) return true end, -- (bool, message?)
		Give = function(player, reward, context) ... return "100 coins" end, -- (text?, message?), no yields
	}

A product whose kind isn't registered can't be given: the shop refuses it and its receipt stays
unresolved (NotProcessedYet), so no one pays for nothing.
context: { giftFrom = the sender's name, for a gift; Prompting = true when the shop asks before opening Roblox's
prompt (a receipt's CanGive has no Prompting); anything else the caller adds }.

A kind may also have hooks the shop calls around Roblox's prompt (WelcomeBackDouble uses them: its offer is
bound to the prompt): OnPrompt(player, reward) just before the prompt opens, OnPromptFinished(player, reward,
purchased) when it closes, and OnClose(player, reward) -> (ok, message?) for the shop's "CloseOffer" request.
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PaidRandomPolicy = require(script.Parent.PaidRandomPolicy)
local PlayerData = require(script.Parent.PlayerData)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)

local PurchaseRewards = {}

-- [kind name] = { CanGive = (player, reward, context) -> (boolean, string?),
--                 Give = (player, reward, context) -> (string?, string?) }
PurchaseRewards.Kinds = {}

PurchaseRewards.UNKNOWN_KIND = "This reward isn't available yet."

function PurchaseRewards.CanGive(player: Player, product, context): (boolean, string?)
	if not PlayerData.Edit(player) then
		return false, "Your data is still loading."
	end
	if MonetizationConfig.IsPaidRandom(product) and not PaidRandomPolicy.IsAllowed(player) then
		return false, PaidRandomPolicy.REFUSED
	end
	local reward = type(product) == "table" and product.Reward
	local kind = type(reward) == "table" and PurchaseRewards.Kinds[reward.Kind]
	if not kind then
		return false, PurchaseRewards.UNKNOWN_KIND
	end
	if kind.CanGive then
		return kind.CanGive(player, reward, context or {})
	end
	return true
end

local function kindOf(product)
	local reward = type(product) == "table" and product.Reward
	return type(reward) == "table" and PurchaseRewards.Kinds[reward.Kind] or nil
end

-- The shop is opening Roblox's prompt for this product (after CanGive with { Prompting = true }).
function PurchaseRewards.Prompting(player: Player, product)
	local kind = kindOf(product)
	if kind and kind.OnPrompt then
		kind.OnPrompt(player, product.Reward)
	end
end

-- Roblox's prompt for this product closed (purchased or not). Never grants: receipts do.
function PurchaseRewards.PromptFinished(player: Player, product, purchased: boolean)
	local kind = kindOf(product)
	if kind and kind.OnPromptFinished then
		kind.OnPromptFinished(player, product.Reward, purchased == true)
	end
end

-- The player closed an offer without buying (only kinds with OnClose have offers).
function PurchaseRewards.Close(player: Player, product): (boolean, string?)
	local kind = kindOf(product)
	if not kind or not kind.OnClose then
		return false, "Nothing to close."
	end
	return kind.OnClose(player, product.Reward)
end

function PurchaseRewards.Give(player: Player, product, context): (string?, string?)
	-- (Key: the product's key, for analytics; a caller's context may name its own Source and Sku)
	context = table.clone(context or {})
	context.Key = context.Key or product.Key
	local ok, problem = PurchaseRewards.CanGive(player, product, context)
	if not ok then
		return nil, problem
	end
	return PurchaseRewards.Kinds[product.Reward.Kind].Give(player, product.Reward, context)
end

return PurchaseRewards
