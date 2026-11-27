--[[
MonetizationConfig: every Robux item the game sells, in one place (the server and the shop read it).
Copied from Steal Pets with every item removed: the lists below are empty, ready for this game's
own passes and products. Paste ids here and nowhere else; docs/ROBUX_PRODUCTS.md is the checklist
for creating them on the Creator Hub.

Adding an item:
 1. Create it on the Creator Hub (docs/ROBUX_PRODUCTS.md) and note its id and price.
 2. Add an entry to Passes or Products below with that Id and ExpectedPrice.
 3. A product's Reward.Kind must be a kind the server knows: register it in
    src/server/PurchaseRewards.luau (PurchaseRewards.Kinds) with the system that grants it.
 4. Run the Monetization spec and check the [PriceCheck] line in Output after the next Play.

Fields:
 * Key: a short unique name (letters and digits). Saved receipts and gifts name it, so never rename
   one that has been sold.
 * Name, Description: what the shop card shows.
 * Id: the real id from the Creator Hub. 0 = not created yet. An item without a real id is never
   shown in a live game and the server never prompts it (MonetizationConfig.IsLive). In Studio the
   shop still shows it with a "NO ID YET" sticker, and buying it runs a simulated purchase through
   the real receipt handler, so the whole flow can be tested before the item exists.
 * GiftId (products only): a second developer product, at the same price, that buys this product
   for another player in the same server (Gifting). 0 = gifting this product isn't on sale yet.
 * ExpectedPrice: the price set on the Creator Hub. Roblox charges the Hub's price, not this one: the
   shop shows the live price, and PriceCheck warns at server start when they differ.
 * Tab (products only): the shop section it is shown in (an Id from Shop.Tabs).
 * Icon (optional): an image id ("rbxassetid://...") for the card's picture.
 * Reward (products only): what the server grants, { Kind = "...", ... }. The receipt handler reads
   it from here, never from a client.
 * PaidRandom (products only): true for a paid random item under Roblox's rules (a random reward, or
   anything that changes the odds of one). It must list its Odds ({ { Name = "...", Chance = 0.25 },
   ... }, chances adding up to 1) so the shop can show them before purchase, and players whose
   region restricts paid random items can't buy it or be gifted it (PaidRandomPolicy).

Example (not live: copy it into a list and replace the ids):
	{ Key = "ExamplePass", Name = "Example Pass", Id = 0, ExpectedPrice = 99, Description = "..." }
	{ Key = "ExampleProduct", Name = "Example", Tab = "Products", Id = 0, GiftId = 0, ExpectedPrice = 49,
		Reward = { Kind = "SomeKind" } }
]]
local MonetizationConfig = {}

-- Game passes (docs/GAME_DESIGN.md, "Monetization"): bought once per account; Roblox's ownership record is
-- the truth (GamePasses), or the save for a pass received as a gift (GiftedPasses). Every pass can be
-- gifted: GiftId is a developer product "Gift: <name>" at the same price (0 until it exists). What each
-- pass does (RobuxPerks):
--  * CrystalMultiplier: all crystals times this (2x Crystals: 2, VIP: 1.2).
--  * AutoTapsPerSecond: the server taps this often for you while you're in your own plot (Auto Pick);
--    they share the 20-taps-a-second cap with your own taps (TapService).
--  * GoldNameTag / Lounge (VIP): a gold name tag, and the VIP lounge in the plaza lets you in.
--  * Lucky: doubles the chance of Legendary and Mythic blocks (BlockRules, Lucky Ice).
--  * PetSlots: equip slots the pass adds (PetService).
-- Created on Roblox by tools/create_products.py (ids also in docs/ROBUX_PRODUCTS.md and
-- store-assets/icons/products_manifest.json).
MonetizationConfig.Passes = {
	{ Key = "DoubleCrystals", Name = "2x Crystals", Id = 2102063611, GiftId = 3736501716, ExpectedPrice = 349, CrystalMultiplier = 2,
		Description = "Doubles all your crystals, forever." },
	{ Key = "AutoPick", Name = "Auto Pick", Id = 2100372547, GiftId = 3736501737, ExpectedPrice = 199, AutoTapsPerSecond = 5,
		Description = "Taps the ice 5 times a second for you while you're in your plot." },
	{ Key = "VIP", Name = "VIP", Id = 2098692454, GiftId = 3736501753, ExpectedPrice = 299, CrystalMultiplier = 1.2, GoldNameTag = true, Lounge = true,
		Description = "+20% crystals, a gold name tag and the VIP lounge in the plaza." },
	{ Key = "ExtraPetSlot", Name = "Extra Pet Slot", Id = 2099292504, GiftId = 3736501769, ExpectedPrice = 399, PetSlots = 1,
		Description = "One more pet follows you." },
	{ Key = "PetSquad", Name = "Pet Squad", Id = 2101811657, GiftId = 3736501785, ExpectedPrice = 699, PetSlots = 2,
		Description = "Two more pets follow you (with Extra Pet Slot, +3 in all)." },
	{ Key = "LuckyIce", Name = "Lucky Ice", Id = 2100576395, GiftId = 3736501801, ExpectedPrice = 349, Lucky = true,
		Description = "Doubles your chance of Legendary and Mythic blocks." },
}
-- A pass given as a gift: the "Pass" reward kind saves it for the recipient (RobuxPerks).
for _, pass in MonetizationConfig.Passes do
	pass.Reward = { Kind = "Pass", Pass = pass.Key }
end

-- Developer products: bought any number of times. Each has a gift twin (GiftId, same price).
-- Reward kinds (RobuxPerks): CrystalBundle (Seconds of your current income: see BundleTapsPerSecond),
-- ShatterNow (breaks the block on your mound now), ServerFrostRush (Multiplier for everyone in the server
-- for Seconds, your name announced; another one adds Seconds), MythicBlock (your next block rolls from
-- Odds: a paid random item; Count of them, 1 when left out).
local MYTHIC_BLOCK_ODDS = {
	{ Name = "Rare", Chance = 0.50 },
	{ Name = "Epic", Chance = 0.30 },
	{ Name = "Legendary", Chance = 0.15 },
	{ Name = "Mythic", Chance = 0.05 },
}

MonetizationConfig.Products = {
	{ Key = "CrystalPouch", Name = "Crystal Pouch", Tab = "Products", Id = 3736501812, GiftId = 3736501820, ExpectedPrice = 29,
		Description = "10 minutes of your crystal income, right now.", Reward = { Kind = "CrystalBundle", Seconds = 600 } },
	{ Key = "CrystalSack", Name = "Crystal Sack", Tab = "Products", Id = 3736501831, GiftId = 3736501841, ExpectedPrice = 99,
		Description = "1 hour of your crystal income, right now.", Reward = { Kind = "CrystalBundle", Seconds = 3600 } },
	{ Key = "CrystalChest", Name = "Crystal Chest", Tab = "Products", Id = 3736501853, GiftId = 3736501858, ExpectedPrice = 499,
		Description = "6 hours of your crystal income, right now.", Reward = { Kind = "CrystalBundle", Seconds = 21600 } },
	{ Key = "GiantCrystalChest", Name = "Giant Crystal Chest", Tab = "Products", Id = 3736773791, GiftId = 3736773801, ExpectedPrice = 999,
		Description = "24 hours of your crystal income, right now.", Reward = { Kind = "CrystalBundle", Seconds = 86400 } },
	{ Key = "ShatterNow", Name = "Shatter Now", Tab = "Products", Id = 3736501870, GiftId = 3736501879, ExpectedPrice = 29,
		Description = "Breaks your current ice block instantly and frees the creature.", Reward = { Kind = "ShatterNow" } },
	{ Key = "ServerFrostRush", Name = "Server Frost Rush", Tab = "Products", Id = 3736501890, GiftId = 3736501900, ExpectedPrice = 99,
		Description = "x2 crystals for everyone in the server for 15 minutes, with your name announced.",
		Reward = { Kind = "ServerFrostRush", Multiplier = 2, Seconds = 900 } },
	{ Key = "MythicBlock", Name = "Mythic Block", Tab = "Products", Id = 3736501911, GiftId = 3736501923, ExpectedPrice = 199,
		Description = "Your next ice block rolls with much better odds. Tap INFO for the odds.",
		Reward = { Kind = "MythicBlock" }, PaidRandom = true,
		-- Shown in the shop before purchase; the roll uses exactly these (BlockRules.RollMythicBlock). The
		-- creature is any one of that rarity from the whole roster, so the odds hold on every layer.
		Odds = MYTHIC_BLOCK_ODDS },
	{ Key = "MythicBlock3", Name = "Mythic Block x3", Tab = "Products", Id = 3736773813, GiftId = 3736773819, ExpectedPrice = 499,
		Description = "Your next three ice blocks roll with much better odds. Tap INFO for the odds.",
		Reward = { Kind = "MythicBlock", Count = 3 }, PaidRandom = true,
		Odds = MYTHIC_BLOCK_ODDS }, -- (each of the three rolls like a single Mythic Block)
}

-- A crystal bundle (and the daily chest) pays Seconds of "your income": the HUD's crystals per second with
-- the permanent bonuses (pets, book, Frost Cores, passes, group) but without rushes (Economy.SteadyIncome).
-- Your taps count at your recent rate, but at least this many a second (so opening the shop, which stops
-- you tapping, or having no buildings yet still pays something).
MonetizationConfig.BundleTapsPerSecond = 4

MonetizationConfig.Shop = {
	-- The shop's sections, in page order. Passes always go in "Passes"; a product names its Tab.
	Tabs = {
		{ Id = "Passes", Name = "PASSES" },
		{ Id = "Products", Name = "ITEMS" },
	},
}

-- Lookups --------------------------------------------------------------------------------------

-- True only for an item that exists on the Creator Hub (a real id).
function MonetizationConfig.IsLive(entry): boolean
	return type(entry) == "table" and type(entry.Id) == "number" and entry.Id > 0
end

-- True when buying this product for someone else is on sale (its gift product has a real id).
function MonetizationConfig.IsGiftLive(product): boolean
	return type(product) == "table" and type(product.GiftId) == "number" and product.GiftId > 0
end

function MonetizationConfig.IsPaidRandom(product): boolean
	return type(product) == "table" and product.PaidRandom == true
end

local function findByKey(list, key)
	for _, entry in list do
		if entry.Key == key then
			return entry
		end
	end
	return nil
end

function MonetizationConfig.GetProduct(key)
	return type(key) == "string" and findByKey(MonetizationConfig.Products, key) or nil
end

function MonetizationConfig.GetPass(key)
	return type(key) == "string" and findByKey(MonetizationConfig.Passes, key) or nil
end

-- Anything that can be bought as a gift: a product, or a pass (keys are unique across both lists).
function MonetizationConfig.GetGiftable(key)
	return MonetizationConfig.GetProduct(key) or MonetizationConfig.GetPass(key)
end

function MonetizationConfig.GetPassById(gamePassId)
	for _, pass in MonetizationConfig.Passes do
		if MonetizationConfig.IsLive(pass) and pass.Id == gamePassId then
			return pass
		end
	end
	return nil
end

-- What a developer product id sells: "Product", product | "Gift", product or pass (bought for someone
-- else) | nil
function MonetizationConfig.FindByProductId(productId)
	if type(productId) ~= "number" or productId <= 0 then
		return nil
	end
	for _, product in MonetizationConfig.Products do
		if product.Id == productId then
			return "Product", product
		elseif product.GiftId == productId then
			return "Gift", product
		end
	end
	for _, pass in MonetizationConfig.Passes do
		if pass.GiftId == productId then
			return "Gift", pass
		end
	end
	return nil
end

-- Every item with a real id, for PriceCheck: { Label, Id, InfoType ("Product"/"GamePass"),
-- ExpectedPrice }, and how many are still hidden (no id yet).
function MonetizationConfig.AllPriced()
	local entries, hidden = {}, 0
	local function add(label, id, infoType, price)
		if type(id) == "number" and id > 0 then
			table.insert(entries, { Label = label, Id = id, InfoType = infoType, ExpectedPrice = price })
		else
			hidden += 1
		end
	end
	for _, product in MonetizationConfig.Products do
		add(product.Name, product.Id, "Product", product.ExpectedPrice)
		add("Gift: " .. product.Name, product.GiftId, "Product", product.ExpectedPrice)
	end
	for _, pass in MonetizationConfig.Passes do
		add(pass.Name, pass.Id, "GamePass", pass.ExpectedPrice)
		add("Gift: " .. pass.Name, pass.GiftId, "Product", pass.ExpectedPrice)
	end
	return entries, hidden
end

-- Checks the lists, so a config mistake fails in Studio instead of in a live purchase. Runs on load;
-- public so the spec can check a test config.
function MonetizationConfig.Validate(config)
	local tabs = {}
	for _, tab in config.Shop.Tabs do
		tabs[tab.Id] = true
	end
	local seenKeys, seenProductIds, seenPassIds = {}, {}, {}
	local function checkEntry(entry)
		assert(type(entry.Key) == "string" and string.match(entry.Key, "^%w+$") and #entry.Key <= 32,
			"a Robux item needs a Key of letters and digits (32 at most)")
		assert(not seenKeys[entry.Key], "duplicate Robux item key " .. entry.Key)
		seenKeys[entry.Key] = true
		assert(type(entry.Name) == "string", entry.Key .. " needs a Name")
		assert(type(entry.Id) == "number" and entry.Id >= 0, entry.Key .. " needs an Id (0 until it exists)")
		assert(type(entry.ExpectedPrice) == "number" and entry.ExpectedPrice > 0, entry.Key .. " needs an ExpectedPrice")
	end
	for _, product in config.Products do
		checkEntry(product)
		assert(tabs[product.Tab], product.Key .. " needs a Tab from Shop.Tabs")
		assert(type(product.GiftId) == "number" and product.GiftId >= 0, product.Key .. " needs a GiftId (0 until it exists)")
		assert(type(product.Reward) == "table" and type(product.Reward.Kind) == "string", product.Key .. " needs a Reward with a Kind")
		if product.PaidRandom then
			assert(type(product.Odds) == "table" and #product.Odds > 0, product.Key .. " is a paid random item: list its Odds")
			local total = 0
			for _, odd in product.Odds do
				assert(type(odd.Name) == "string" and type(odd.Chance) == "number" and odd.Chance > 0, product.Key .. " has a bad Odds entry")
				total += odd.Chance
			end
			assert(math.abs(total - 1) < 1e-6, product.Key .. "'s Odds must add up to 1")
		end
		for _, id in { product.Id, product.GiftId } do
			if id > 0 then
				-- The same id pasted twice would sell one item under another's name.
				assert(not seenProductIds[id], "developer product id " .. id .. " is used twice")
				seenProductIds[id] = true
			end
		end
	end
	for _, pass in config.Passes do
		checkEntry(pass)
		if pass.Id > 0 then
			assert(not seenPassIds[pass.Id], "game pass id " .. pass.Id .. " is used twice")
			seenPassIds[pass.Id] = true
		end
		local giftId = pass.GiftId or 0
		assert(type(giftId) == "number" and giftId >= 0, pass.Key .. " needs a GiftId (0 until it exists)")
		if giftId > 0 then
			assert(not seenProductIds[giftId], "developer product id " .. giftId .. " is used twice")
			seenProductIds[giftId] = true
		end
	end
end

MonetizationConfig.Validate(MonetizationConfig)

return MonetizationConfig
