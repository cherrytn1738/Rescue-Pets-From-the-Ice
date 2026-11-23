--[[
Receipts: the game's ONE MarketplaceService.ProcessReceipt handler. Server only.

MarketplaceService keeps only the last function assigned to ProcessReceipt, so nothing else may set
it. Every developer product and every gift product comes through here and is found by its
ProductId in MonetizationConfig (what it gives comes from config, never from a client).

Roblox calls this after a player pays, and again later (for example when they rejoin) until it
answers PurchaseGranted. Each receipt pays exactly once:
 1. The player isn't in this server, the product is unknown, or their data isn't ready
    -> NotProcessedYet (Roblox retries; nothing is ever granted into data that won't be saved).
 2. Its PurchaseId is already in the saved Receipts -> granted before: give nothing, make sure that
    is saved, PurchaseGranted.
 3. Give the reward (PurchaseRewards) and record the PurchaseId in the SAME data, with no yield in
    between, so a second call for the same receipt (Roblox can call again while this one saves)
    always finds it. Can't apply now -> NotProcessedYet, Roblox retries later. A paid random item
    for a player whose region restricts them -> refused with NotProcessedYet, nothing given
    (PaidRandomPolicy; the shop never prompts it for them).
 4. Save now. Saved -> PurchaseGranted. Not saved -> NotProcessedYet: the retry finds step 2.
    If the server dies before the save, nothing was saved, and the retry (in the next server)
    grants it then. If it dies after the save but before Roblox heard "granted", the retry finds
    the saved receipt and grants nothing.
 5. Tell the player (the PurchaseNotice RemoteEvent), for the notice only.
Gift products (bought for another player) go to Gifting.ClaimGift.

Studio: Receipts.Simulate runs a fake receipt through exactly this code (the debug menu, and the
shop for products without an id yet). Simulated receipts never reach a live save (Studio uses its
own store, see PlayerData).
]]
local HttpService = game:GetService("HttpService")
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Gifting = require(script.Parent.Gifting)
local PaidRandomPolicy = require(script.Parent.PaidRandomPolicy)
local PlayerData = require(script.Parent.PlayerData)
local PurchaseRewards = require(script.Parent.PurchaseRewards)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local MonetizationRules = require(ReplicatedStorage.MonetizationRules)

local Receipts = {}

local Decision = Enum.ProductPurchaseDecision
local DATA_WAIT_SECONDS = 10
local POLICY_WAIT_SECONDS = 15 -- a receipt retried at join waits for Roblox's answer about paid random items

local function notice(player: Player, payload)
	local remote = ReplicatedStorage:FindFirstChild("PurchaseNotice")
	if remote and player.Parent == Players then
		remote:FireClient(player, payload)
	end
end

local function savedDecision(player: Player)
	return if PlayerData.SaveNow(player) then Decision.PurchaseGranted else Decision.NotProcessedYet
end

local function grantProduct(player: Player, receipt, product)
	local data = PlayerData.WaitForData(player, DATA_WAIT_SECONDS)
	if not data then
		return Decision.NotProcessedYet, "their data isn't ready"
	end
	if not MonetizationRules.IsValidReceipt(receipt, player.UserId) then
		return Decision.NotProcessedYet, "the receipt isn't this player's"
	end
	if MonetizationRules.FindReceipt(data.Receipts, receipt.PurchaseId) then
		return savedDecision(player), "already granted, nothing given"
	end
	-- A paid random item for a player whose region restricts them: refused, nothing given. It stays
	-- unresolved (Roblox keeps the receipt) rather than being marked granted for nothing.
	if MonetizationConfig.IsPaidRandom(product) and not PaidRandomPolicy.WaitForAnswer(player, POLICY_WAIT_SECONDS) then
		warn(`[PaidRandom] {player.Name}'s receipt {receipt.PurchaseId} for {product.Name} refused: paid random items are restricted for them`)
		return Decision.NotProcessedYet, "paid random items are restricted for this player; nothing given"
	end

	-- From here to RememberReceipt nothing yields.
	data = PlayerData.Edit(player)
	if not data then
		return Decision.NotProcessedYet, "their data isn't ready"
	end
	if MonetizationRules.FindReceipt(data.Receipts, receipt.PurchaseId) then
		return savedDecision(player), "already granted, nothing given" -- (another call granted it meanwhile)
	end
	local given, problem = PurchaseRewards.Give(player, product)
	if not given then
		return Decision.NotProcessedYet, `can't apply now ({problem}); Roblox retries later`
	end
	MonetizationRules.RememberReceipt(data.Receipts, { Id = receipt.PurchaseId, Product = product.Key, At = os.time() })
	PlayerData.Publish(player)

	-- Saved BEFORE Roblox hears "granted".
	if not PlayerData.SaveNow(player) then
		return Decision.NotProcessedYet, `gave {given}, but the save failed; the retry only saves`
	end
	notice(player, { Kind = "Purchased", Item = product.Name, Other = given })
	return Decision.PurchaseGranted, `gave {given}`
end

-- One receipt for a known product. Returns the decision and a short note for the log.
function Receipts.Handle(player: Player, receipt, kind: string, product)
	if kind == "Gift" then
		return Gifting.ClaimGift(player, receipt, product)
	end
	return grantProduct(player, receipt, product)
end

local function processReceipt(receipt)
	local player = Players:GetPlayerByUserId(receipt.PlayerId)
	if not player then
		return Decision.NotProcessedYet -- not in this server: Roblox retries, e.g. when they rejoin
	end
	local kind, product = MonetizationConfig.FindByProductId(receipt.ProductId)
	if not kind then
		warn(`[Purchase] unknown developer product {receipt.ProductId} (receipt {receipt.PurchaseId}); left for a retry`)
		return Decision.NotProcessedYet
	end
	local ok, decision, note = pcall(Receipts.Handle, player, receipt, kind, product)
	if not ok then
		warn(`[Purchase] receipt {receipt.PurchaseId} for {product.Name} failed: {decision}`)
		return Decision.NotProcessedYet
	end
	print(`[Purchase] {player.Name} {if kind == "Gift" then "gift: " else ""}{product.Name} ({receipt.PurchaseId}): {decision.Name}, {note}`)
	return decision
end

-- Studio only: a fake receipt for `product`, through exactly the code above. options.gift: the
-- gift product (Gifting.Prepare must have saved the recipient first). options.purchaseId: replay
-- that receipt (a duplicate, or a retry after a rejoin). Returns the decision, a note and the id.
function Receipts.Simulate(player: Player, product, options: { gift: boolean?, purchaseId: string? }?)
	if not RunService:IsStudio() then
		return nil, "Studio only"
	end
	options = options or {}
	local kind = if options.gift then "Gift" else "Product"
	local receipt = {
		PlayerId = player.UserId,
		PurchaseId = options.purchaseId or ("Studio-" .. HttpService:GenerateGUID(false)),
		ProductId = if options.gift then product.GiftId else product.Id,
		CurrencySpent = product.ExpectedPrice,
		CurrencyType = Enum.CurrencyType.Robux,
		PlaceIdWherePurchased = game.PlaceId,
	}
	local decision, note = Receipts.Handle(player, receipt, kind, product)
	print(`[Purchase] SIMULATED {player.Name} {if options.gift then "gift: " else ""}{product.Name} ({receipt.PurchaseId}): {decision.Name}, {note}`)
	return decision, note, receipt.PurchaseId
end

function Receipts.Start()
	MarketplaceService.ProcessReceipt = processReceipt
	Gifting.Start()
end

return Receipts
