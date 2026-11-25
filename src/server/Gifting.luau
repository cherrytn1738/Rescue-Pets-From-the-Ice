--[[
Gifting: a player buys a Robux product for another player in the same server. Server only.

Every product has its own gift product (MonetizationConfig GiftId, the same price). The gift is
written into the RECIPIENT's saved record, so it arrives once even if they leave, rejoin, or the
server shuts down in between:
 1. Prepare, before the buyer's prompt opens: checks both players and that the gift would apply to
    the recipient now, then notes the intent in the BUYER's session data (PendingGifts[product key] =
    who, and where their record is). Nothing is saved yet, so asking (and cancelling) costs no
    DataStore writes; RobuxShop also lets a player open one gift prompt every
    MonetizationRules.GiftRequestSeconds.
 2. PromptFinished: cancelled drops the intent; bought keeps it and saves it straight away, so the
    receipt finds the recipient even if it only arrives after a rejoin or in another server.
 3. ClaimGift, the gift product's receipt (from Receipts): adds { Id = PurchaseId, Product, From,
    FromName } to the recipient's saved GiftInbox with UpdateAsync (skipped if it is already queued
    or given there, so a retried receipt queues it once). Only then is the buyer's receipt recorded
    ({ Id, Product, For = recipient }) and saved, and Roblox told it is granted.
 4. Apply, on the recipient's server (now if they're here, at their next join, or after a save
    finds it): gives each gift not in ReceivedGifts and adds its id there in the same data, then
    saves. A gift that can't apply yet stays in the inbox and is tried again.
PlayerData's saves keep the stored inbox minus what was given, so a gift queued by another server
meanwhile is never lost.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PaidRandomPolicy = require(script.Parent.PaidRandomPolicy)
local PlayerData = require(script.Parent.PlayerData)
local PurchaseRewards = require(script.Parent.PurchaseRewards)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local MonetizationRules = require(ReplicatedStorage.MonetizationRules)

local Gifting = {}

local Decision = Enum.ProductPurchaseDecision
local DATA_WAIT_SECONDS = 10

local function notice(player: Player, payload)
	local remote = ReplicatedStorage:FindFirstChild("PurchaseNotice")
	if remote and player.Parent == Players then
		remote:FireClient(player, payload)
	end
end

-- Step 1. Returns true when the prompt may open, or false and a message for the buyer. Doesn't save.
function Gifting.Prepare(buyer: Player, product, recipient: Player?): (boolean, string?)
	local data = PlayerData.Edit(buyer)
	if not data then
		return false, "Your data is still loading."
	end
	if typeof(recipient) ~= "Instance" or recipient.Parent ~= Players then
		return false, "That player isn't in this server any more."
	end
	if recipient == buyer then
		return false, "Pick another player to send a gift to."
	end
	local store, key = PlayerData.RecordLocation(recipient)
	if not store then
		return false, `{recipient.DisplayName} is still loading. Try again soon.`
	end
	-- A paid random item: both the buyer and the recipient must be allowed to buy one where they are
	-- (PaidRandomPolicy).
	if MonetizationConfig.IsPaidRandom(product) then
		if not PaidRandomPolicy.IsAllowed(buyer) then
			return false, PaidRandomPolicy.REFUSED
		elseif not PaidRandomPolicy.IsAllowed(recipient) then
			return false, `{recipient.DisplayName} can't get random items bought with Robux in their region.`
		end
	end
	local ok, problem = PurchaseRewards.CanGive(recipient, product)
	if not ok then
		return false, `Can't gift that to {recipient.DisplayName} now: {problem}`
	end
	local existing = data.PendingGifts[product.Key]
	if MonetizationRules.GiftStillOnItsWay(existing, os.time()) then
		return false, "Your last gift of this is still on its way. Try again shortly."
	end
	data.PendingGifts[product.Key] = {
		Recipient = recipient.UserId,
		RecipientName = recipient.DisplayName,
		Store = store,
		Key = key,
		State = "prompted",
		At = os.time(),
	}
	return true
end

-- Step 2, from the server's PromptProductPurchaseFinished for a gift product. Bought: saved now
-- (the only save a gift's prompt causes). Yields.
function Gifting.PromptFinished(buyer: Player, product, purchased: boolean)
	local data = PlayerData.Edit(buyer)
	local intent = data and data.PendingGifts[product.Key]
	if not intent then
		return
	end
	if purchased then
		intent.State = "purchased"
		intent.At = os.time()
		if not PlayerData.SaveNow(buyer) then
			PlayerData.MarkImportant(buyer) -- (tried again on the next save tick)
		end
	elseif intent.State ~= "purchased" then
		data.PendingGifts[product.Key] = nil
	end
end

-- Adds the gift to the recipient's saved inbox unless it is already queued or given there.
-- Returns whether it is now safely on their record. Yields.
local function queue(intent, entry): boolean
	local landed = false
	local ok = PlayerData.UpdateRecord(intent.Store, intent.Key, function(record)
		landed = false -- UpdateAsync can run the transform more than once
		if type(record) ~= "table" then
			return nil -- no saved record (never happens for a loaded player): left for a retry
		end
		local received = if type(record.ReceivedGifts) == "table" then record.ReceivedGifts else {}
		if table.find(received, entry.Id) then
			landed = true
			return nil -- already given
		end
		local inbox = if type(record.GiftInbox) == "table" then record.GiftInbox else {}
		for _, queued in inbox do
			if type(queued) == "table" and queued.Id == entry.Id then
				landed = true
				return nil -- already queued
			end
		end
		if #inbox >= MonetizationRules.MaxGifts then
			return nil -- their inbox is full: left for a retry
		end
		local updated = table.clone(record)
		updated.GiftInbox = table.clone(inbox)
		table.insert(updated.GiftInbox, entry)
		landed = true
		return updated
	end)
	return ok and landed
end

-- Step 3, a gift product's receipt. Returns Roblox's decision and a note for the log.
function Gifting.ClaimGift(buyer: Player, receipt, product)
	local data = PlayerData.WaitForData(buyer, DATA_WAIT_SECONDS)
	if not data or not MonetizationRules.IsValidReceipt(receipt, buyer.UserId) then
		return Decision.NotProcessedYet, "the buyer's data isn't ready"
	end
	if MonetizationRules.FindReceipt(data.Receipts, receipt.PurchaseId) then
		return (if PlayerData.SaveNow(buyer) then Decision.PurchaseGranted else Decision.NotProcessedYet), "already granted, nothing given"
	end
	if MonetizationConfig.IsPaidRandom(product) and not PaidRandomPolicy.IsAllowed(buyer) then
		return Decision.NotProcessedYet, "paid random items are restricted for the buyer; nothing given"
	end
	local intent = data.PendingGifts[product.Key]
	if not intent then
		warn(`[Gift] receipt {receipt.PurchaseId} for {product.Name} has no saved recipient; left for a retry`)
		return Decision.NotProcessedYet, "no saved recipient"
	end
	-- queue() yields, so a second call for this receipt could get here too. That's safe: the
	-- recipient's inbox is keyed by PurchaseId, so the gift is queued once.
	local entry = { Id = receipt.PurchaseId, Product = product.Key, From = buyer.UserId, FromName = buyer.DisplayName }
	if not queue(intent, entry) then
		return Decision.NotProcessedYet, `couldn't reach {intent.RecipientName}'s save; left for a retry`
	end
	data = PlayerData.Edit(buyer)
	if not data then
		return Decision.NotProcessedYet, "the buyer's data isn't ready"
	end
	if data.PendingGifts[product.Key] == intent then
		data.PendingGifts[product.Key] = nil
	end
	MonetizationRules.RememberReceipt(data.Receipts, { Id = receipt.PurchaseId, Product = product.Key, At = os.time(), For = intent.Recipient })
	if not PlayerData.SaveNow(buyer) then
		return Decision.NotProcessedYet, "queued, but the buyer's save failed; the retry only saves"
	end
	-- The recipient is here (and it's their record): give it now rather than at their next save.
	local recipient = Players:GetPlayerByUserId(intent.Recipient)
	if recipient then
		local store, key = PlayerData.RecordLocation(recipient)
		if store == intent.Store and key == intent.Key then
			task.spawn(Gifting.Apply, recipient, { entry })
		end
	end
	notice(buyer, { Kind = "GiftSent", Item = product.Name, Other = intent.RecipientName })
	return Decision.PurchaseGranted, `queued for {intent.RecipientName} ({intent.Recipient})`
end

-- Step 4: gives queued gifts to a loaded recipient, once each. Yields (saves).
function Gifting.Apply(player: Player, entries)
	if type(entries) ~= "table" or not PlayerData.WaitForData(player, DATA_WAIT_SECONDS) then
		return
	end
	local hasPaidRandom = false
	for _, entry in entries do
		local product = type(entry) == "table" and MonetizationConfig.GetGiftable(entry.Product)
		hasPaidRandom = hasPaidRandom or MonetizationConfig.IsPaidRandom(product)
	end
	if hasPaidRandom then
		-- (at join, Roblox's answer may not be in yet; a restricted recipient's gift stays in the inbox)
		PaidRandomPolicy.WaitForAnswer(player, DATA_WAIT_SECONDS)
	end

	-- From here to the save nothing yields: each gift is given and remembered together.
	local data = PlayerData.Edit(player)
	if not data then
		return
	end
	local applied = {}
	for _, entry in entries do
		local product = type(entry) == "table" and type(entry.Id) == "string" and MonetizationConfig.GetGiftable(entry.Product)
		if product and not table.find(data.ReceivedGifts, entry.Id) then
			local given, problem = PurchaseRewards.Give(player, product, { giftFrom = entry.FromName })
			if given then
				MonetizationRules.RememberGift(data.ReceivedGifts, entry.Id)
				table.insert(applied, { product = product, entry = entry, given = given })
			else
				print(`[Gift] {product.Name} from {entry.FromName} waits in {player.Name}'s inbox: {problem}`)
			end
		end
	end
	if #applied == 0 then
		return
	end
	PlayerData.Publish(player)
	PlayerData.SaveNow(player) -- (if it fails, the next save writes it; ReceivedGifts stops a repeat)
	for _, info in applied do
		print(`[Gift] {player.Name} got {info.product.Name} from {info.entry.FromName}: {info.given}`)
		notice(player, { Kind = "GiftReceived", Item = info.product.Name, Other = info.entry.FromName })
	end
end

function Gifting.Start()
	PlayerData.OnGiftsArrived(Gifting.Apply)
end

return Gifting
