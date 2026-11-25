--[[
MonetizationRules: the Robux rules as pure functions on plain values, so tests/Monetization.spec.luau
can run every case. The server (Receipts, Gifting, RobuxShop) and PlayerData use them.
]]
local MonetizationRules = {}

MonetizationRules.MaxReceipts = 50 -- recent receipts kept per player; Roblox only retries recent ones
MonetizationRules.MaxGifts = 100 -- recent gift ids remembered per player, and queued gifts at most
MonetizationRules.GiftWaitSeconds = 3600 -- a bought gift blocks gifting that product again this long
MonetizationRules.GiftRequestSeconds = 5 -- a player opens at most one gift prompt this often

-- May this player open another gift prompt now? (lastAt: when their last one opened, or nil.)
function MonetizationRules.GiftRequestReady(lastAt: number?, now: number): boolean
	return lastAt == nil or now - lastAt >= MonetizationRules.GiftRequestSeconds
end

-- Receipts ---------------------------------------------------------------------------------------
-- A saved receipt: { Id = PurchaseId, Product = product key, At = os.time(), For = recipient's user
-- id (gifts only) }.

function MonetizationRules.FindReceipt(receipts, purchaseId: string)
	for _, entry in receipts do
		if entry.Id == purchaseId then
			return entry
		end
	end
	return nil
end

-- Adds a receipt (once), keeping the most recent MaxReceipts.
function MonetizationRules.RememberReceipt(receipts, entry)
	if MonetizationRules.FindReceipt(receipts, entry.Id) then
		return
	end
	table.insert(receipts, entry)
	while #receipts > MonetizationRules.MaxReceipts do
		table.remove(receipts, 1)
	end
end

-- Adds a received gift id (once), keeping the most recent MaxGifts.
function MonetizationRules.RememberGift(received, giftId: string)
	if table.find(received, giftId) then
		return
	end
	table.insert(received, giftId)
	while #received > MonetizationRules.MaxGifts do
		table.remove(received, 1)
	end
end

-- Whether a saved gift intent still blocks a new gift of the same product: it is bought and its
-- receipt hasn't arrived yet (for up to GiftWaitSeconds).
function MonetizationRules.GiftStillOnItsWay(intent, now: number): boolean
	return type(intent) == "table" and intent.State == "purchased" and now - (intent.At or 0) < MonetizationRules.GiftWaitSeconds
end

-- A receipt from Roblox (or a simulated one) that belongs to this player.
function MonetizationRules.IsValidReceipt(receipt, userId: number): boolean
	return type(receipt) == "table"
		and receipt.PlayerId == userId
		and type(receipt.PurchaseId) == "string"
		and #receipt.PurchaseId > 0
		and #receipt.PurchaseId <= 64
end

-- A crystal bundle: `seconds` of an income of `perSecond` crystals a second (0 for anything unreadable).
function MonetizationRules.BundleCrystals(perSecond: number, seconds: number): number
	if type(perSecond) ~= "number" or type(seconds) ~= "number" or perSecond ~= perSecond or seconds ~= seconds then
		return 0
	end
	local amount = math.max(0, perSecond) * math.max(0, seconds)
	return if amount < math.huge then amount else 0
end

-- When a Server Frost Rush bought at `now` ends: `seconds` from now, or added to one still running.
function MonetizationRules.RushEndsAt(now: number, endsAt: number, seconds: number): number
	return math.max(now, endsAt) + seconds
end

return MonetizationRules
