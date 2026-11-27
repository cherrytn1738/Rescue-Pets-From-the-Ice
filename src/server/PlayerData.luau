--[[
PlayerData: the player save. Copied from Steal Pets (itself adapted from the roblox-player-data
skill's reference module) and reset to schema 1 for this game.

 - One record per player (key Player_<UserId>), read and written only with UpdateAsync.
 - A session lease inside the record, so only one server owns it at a time.
 - A failed load is never a "new player": the session gets no gameplay, is kicked, and never saves.
 - Schema versions with validation and clamping; unknown fields are kept.
 - Autosave (60 s + jitter), "important save soon", PlayerRemoving and BindToClose saves.
 - Safe when a write commits but its response is lost (LastWriteId).
 - Studio uses its own stores unless you opt in to live saves (StudioUseLiveSaves).

The store names are this game's own (IcePets_*). They must never be the Steal Pets names
("PlayerData", "PlayerData_Studio", ...), so this code can never read or write that game's saves.

The session's data table is the real state. Other modules change it through Edit() with the
server's own numbers; attributes are display copies that are never read back.
Robux receipts and gifts: every granted receipt is saved in Receipts in the same save as its reward
(Receipts.luau); a gift is queued in the recipient's saved GiftInbox (UpdateRecord) and given once
(ReceivedGifts). The owner's own saves MERGE the inbox, never overwrite it.
]]
local DataStoreService = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local AnalyticsConfig = require(ReplicatedStorage.AnalyticsConfig)
local AnalyticsRules = require(ReplicatedStorage.AnalyticsRules)
local BuildingConfig = require(ReplicatedStorage.BuildingConfig)
local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local LayerConfig = require(ReplicatedStorage.LayerConfig)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local MonetizationRules = require(ReplicatedStorage.MonetizationRules)
local UpgradeConfig = require(ReplicatedStorage.UpgradeConfig)

local LIVE_STORE = "IcePets_PlayerData"
local STUDIO_STORE = "IcePets_PlayerData_Studio" -- Studio's default: test progress never reaches live saves
local STUDIO_FRESH_STORE = "IcePets_PlayerData_StudioFresh" -- a brand-new throwaway record every Play

local SCHEMA_VERSION = 1
local AUTOSAVE_SECONDS = 60
-- MarkImportant saves on the next tick, but at most once every IMPORTANT_GAP_SECONDS per player: gameplay
-- marks many things important (a rescue, a build, a pet), and one DataStore key shouldn't be written more
-- often than every ~6 s. Robux grants don't wait: they use SaveNow.
local IMPORTANT_GAP_SECONDS = 15
local LEASE_SECONDS = 180 -- how long a claim lasts without being renewed
local LEASE_SAFETY_SECONDS = 15 -- stop gameplay this long before the lease could run out
local LEASE_HELD = "data is still in use by another server"
local LEASE_WAIT_ATTEMPTS = 4 -- a quick server hop: the old server may still be saving
local LEASE_WAIT_SECONDS = 5
local MAX_ATTEMPTS = 3 -- tries per request, with backoff
local REQUEST_SECONDS = 20 -- the deadline for one request, retries included
local SHUTDOWN_SECONDS = 25 -- Roblox allows about 30 seconds for all BindToClose callbacks

local ONBOARDING_STEPS = #AnalyticsConfig.Onboarding -- (Funnels)
local PROGRESS_STEPS = { -- (Funnels: the progression funnels' step counts)
	Layers = #AnalyticsConfig.Progression.Layers.Steps,
	Ranks = #AnalyticsConfig.Progression.Ranks.Steps,
}
local MAX_ID_TEXT = 64 -- purchase ids, gift ids, names, store names and keys
local MAX_USER_ID = 2 ^ 53 -- (Studio test players have negative ids)
local MAX_CODES = 200 -- redeemed codes kept (the most recent)
local CODE_PATTERN = "^[A-Z0-9]+$" -- a redeemed code as saved: CodeRules.Normalize's form
local MAX_CODE_TEXT = 32

-- The game's own fields (docs/GAME_DESIGN.md, "Data and code structure").
local MAX_AMOUNT = 1e300 -- crystals: a Luau number reaches about 1e308 (the design's "big numbers")
local MAX_LEVEL = 1_000_000 -- block levels
local MAX_OWNED = 1_000_000 -- copies of one building
local MAX_REBIRTHS = 1_000_000
local MAX_LAYER = 100
local MAX_UID_TEXT = 64 -- a pet's uid (a GUID)
local TUTORIAL_FIRST, TUTORIAL_DONE = 1, 5 -- the design's five tutorial steps; 5 = done (the code shown)
local INVENTORY_SIZE = CreatureConfig.Pets.InventorySize
local MAX_EQUIPPED = CreatureConfig.Pets.MaxEquipSlots

local PlayerData = {}
PlayerData.SCHEMA_VERSION = SCHEMA_VERSION

local sessions = {} -- [player] = session; session.data is the real state (server only)
local started, shuttingDown = false, false
local savedListener, giftListener
local loadedListeners = {}

local function isInteger(value, min, max)
	return type(value) == "number" and value == value and value % 1 == 0 and value >= min and value <= max
end

local function deepCopy(value)
	if type(value) ~= "table" then
		return value
	end
	local copy = {}
	for key, item in value do
		copy[key] = deepCopy(item)
	end
	return copy
end

-- A crystal amount: a finite, non-negative number (crystals can be fractional: damage × multipliers).
local function isAmount(value)
	return type(value) == "number" and value == value and value >= 0 and value <= MAX_AMOUNT
end

-- Game fields ------------------------------------------------------------------------------------

-- The block in progress: { CreatureId, HpLeft }, or nil (the server rolls a new block). It isn't
-- paid for, so one that can't be read is simply rolled again.
local function cleanBlock(block)
	if type(block) ~= "table" or not CreatureConfig.Get(block.CreatureId) or not isAmount(block.HpLeft) then
		return nil
	end
	return { CreatureId = block.CreatureId, HpLeft = block.HpLeft }
end

-- One pet: { Uid, CreatureId, Golden, Locked (true, or absent) }. A pet whose creature this game doesn't
-- know, or with an unreadable uid, is dropped.
local function cleanPet(pet)
	if type(pet) ~= "table" or type(pet.Uid) ~= "string" or #pet.Uid == 0 or #pet.Uid > MAX_UID_TEXT
		or not CreatureConfig.Get(pet.CreatureId) then
		return nil
	end
	return { Uid = pet.Uid, CreatureId = pet.CreatureId, Golden = pet.Golden == true, Locked = if pet.Locked == true then true else nil }
end

-- Purchase bookkeeping --------------------------------------------------------------------------

local function isIdText(value)
	return type(value) == "string" and #value > 0 and #value <= MAX_ID_TEXT
end

local function isUserId(value)
	return isInteger(value, -MAX_USER_ID, MAX_USER_ID) and value ~= 0
end

-- A granted receipt: { Id = PurchaseId, Product, At, For = recipient (gifts) }. Unreadable ones drop.
local function cleanReceipt(entry)
	if type(entry) ~= "table" or not isIdText(entry.Id) then
		return nil
	end
	return {
		Id = entry.Id,
		Product = if isIdText(entry.Product) then entry.Product else "",
		At = if isInteger(entry.At, 0, MAX_USER_ID) then entry.At else 0,
		For = if isUserId(entry.For) then entry.For else nil,
	}
end

-- A queued gift in the recipient's inbox: { Id = the buyer's PurchaseId, Product, From, FromName }.
-- A product this game doesn't sell (any more) can't be given, so it drops.
local function cleanGift(entry)
	if type(entry) ~= "table" or not isIdText(entry.Id) or not MonetizationConfig.GetGiftable(entry.Product) or not isUserId(entry.From) then
		return nil
	end
	return {
		Id = entry.Id,
		Product = entry.Product,
		From = entry.From,
		FromName = if isIdText(entry.FromName) then entry.FromName else "Someone",
	}
end

-- The buyer's saved gift intent (Gifting.Prepare): who receives it and where their record is.
local function cleanIntent(intent)
	if type(intent) ~= "table" or not isUserId(intent.Recipient) or not isIdText(intent.Store) or not isIdText(intent.Key)
		or (intent.State ~= "prompted" and intent.State ~= "purchased") then
		return nil
	end
	return {
		Recipient = intent.Recipient,
		RecipientName = if isIdText(intent.RecipientName) then intent.RecipientName else "someone",
		Store = intent.Store,
		Key = intent.Key,
		State = intent.State,
		At = if isInteger(intent.At, 0, MAX_USER_ID) then intent.At else 0,
	}
end

-- Schema history (bump SCHEMA_VERSION and add a step for every change once the game is live):
--   1  The game (docs/GAME_DESIGN.md, "Data and code structure"): Crystals, CrystalsThisRun,
--        CrystalsAllTime, BlockLevel, CurrentBlock ({ CreatureId, HpLeft } or none), Buildings
--        ({ [building id] = count }), Upgrades (upgrade ids), Pets ({ Uid, CreatureId, Golden }),
--        Equipped (pet uids), BookSeen ({ [creature id] = rescue count }), FrostCores, Rebirths,
--        MaxLayerOpened, CreaturesRescued, TutorialStep. The doc's codesRedeemed is Codes, lastOnline is
--        LeftAt and purchaseIds is Receipts (below). Bought pass ownership is never saved (GamePasses);
--        a pass received as a gift is (GiftedPasses).
--      Robux bookkeeping: Receipts ({ Id, Product, At, For }), PendingGifts ({ [product key] = intent }),
--        GiftInbox (store only: gifts other players sent, not given yet), ReceivedGifts (gift ids given),
--        GiftedPasses ({ [pass key] = true }: passes received as gifts; Roblox has no record of those, so
--        they are saved), MythicBlocks (Mythic Block products bought and not rolled yet);
--        Codes (redeemed promo codes, CodeRules.Normalize's form); Funnels (how far the one-time
--        analytics funnels are logged: onboarding, and the progression funnels' Layers, Ranks and the
--        player's funnel session ProgressId, AnalyticsRules); LeftAt (store only: the server's os.time() at
--        the last save, for offline earnings). Plus Session and LastWriteId (lease bookkeeping).
--      Nothing is live yet, so changes still go into schema 1; after launch every change bumps it.
-- Rules: progress that can't be read fails closed (never rewritten with a default); unknown ids
-- (a creature, building or upgrade that no longer exists) are dropped; a missing field gets its
-- default.
-- Returns a clean record, or nil and a reason (the load then FAILS and nothing is overwritten).
-- Only a missing record (nil) is a new player.
local function validate(record)
	if record ~= nil and type(record) ~= "table" then
		return nil, "record is not a table"
	end
	local isNew = record == nil
	local data = if isNew then {} else table.clone(record) -- fields this code doesn't know are kept
	local version = if isNew then SCHEMA_VERSION else (data.SchemaVersion or 1)
	-- A NEWER version than this server knows (an old server still running after an update) also
	-- fails: never rewrite data you can't read.
	if not isInteger(version, 1, SCHEMA_VERSION) then
		return nil, "unsupported schema version " .. tostring(version)
	end

	-- Crystals: amounts. Missing starts at 0; anything else that isn't an amount fails closed.
	for _, field in { "Crystals", "CrystalsThisRun", "CrystalsAllTime" } do
		if data[field] == nil then
			data[field] = 0
		elseif not isAmount(data[field]) then
			return nil, "invalid " .. field
		end
	end

	-- Whole-number progress: missing gets its default; unreadable fails closed.
	local counters = {
		{ "BlockLevel", 1, 1, MAX_LEVEL },
		{ "FrostCores", 0, 0, MAX_AMOUNT },
		{ "Rebirths", 0, 0, MAX_REBIRTHS },
		{ "MaxLayerOpened", LayerConfig.FloorLayer, 1, MAX_LAYER },
		{ "CreaturesRescued", 0, 0, MAX_AMOUNT },
	}
	for _, counter in counters do
		local field, default, min, max = counter[1], counter[2], counter[3], counter[4]
		if data[field] == nil then
			data[field] = default
		elseif not isInteger(data[field], min, max) then
			return nil, "invalid " .. field
		end
	end

	-- The block in progress: rolled again if it can't be read.
	data.CurrentBlock = cleanBlock(data.CurrentBlock)

	-- Buildings: { [id] = count }. Not a table fails closed; unknown buildings are dropped; a count
	-- that isn't a whole number fails closed (they were paid for); zero counts are dropped.
	if data.Buildings ~= nil and type(data.Buildings) ~= "table" then
		return nil, "invalid Buildings"
	end
	local buildings = {}
	for id, count in data.Buildings or {} do
		if BuildingConfig.Get(id) then
			if not isInteger(count, 0, MAX_OWNED) then
				return nil, "invalid Buildings count for " .. tostring(id)
			end
			if count > 0 then
				buildings[id] = count
			end
		end
	end
	data.Buildings = buildings

	-- Upgrades: a list of ids. Not a list fails closed; unknown and repeated ids are dropped.
	if data.Upgrades ~= nil and type(data.Upgrades) ~= "table" then
		return nil, "invalid Upgrades"
	end
	local upgrades = {}
	for _, id in data.Upgrades or {} do
		if UpgradeConfig.Get(id) and not table.find(upgrades, id) then
			table.insert(upgrades, id)
		end
	end
	data.Upgrades = upgrades

	-- Pets: not a list fails closed; unreadable pets and repeated uids are dropped; at most a full
	-- inventory. Equipped: uids of owned pets, no repeats, at most the maximum slots.
	if data.Pets ~= nil and type(data.Pets) ~= "table" then
		return nil, "invalid Pets"
	end
	if data.Equipped ~= nil and type(data.Equipped) ~= "table" then
		return nil, "invalid Equipped"
	end
	local pets, uids = {}, {}
	for _, entry in data.Pets or {} do
		local pet = cleanPet(entry)
		if pet and not uids[pet.Uid] and #pets < INVENTORY_SIZE then
			uids[pet.Uid] = true
			table.insert(pets, pet)
		end
	end
	data.Pets = pets
	local equipped = {}
	for _, uid in data.Equipped or {} do
		if type(uid) == "string" and uids[uid] and not table.find(equipped, uid) and #equipped < MAX_EQUIPPED then
			table.insert(equipped, uid)
		end
	end
	data.Equipped = equipped

	-- The Creature Book: { [creature id] = rescue count }. Not a table fails closed; unknown creatures
	-- are dropped; a seen creature whose count can't be read stays seen, with a count of 1.
	if data.BookSeen ~= nil and type(data.BookSeen) ~= "table" then
		return nil, "invalid BookSeen"
	end
	local book = {}
	for id, count in data.BookSeen or {} do
		if CreatureConfig.Get(id) then
			book[id] = if isInteger(count, 1, MAX_AMOUNT) then count else 1
		end
	end
	data.BookSeen = book

	-- More Creature Book state, all display or rewards that are worked out again from it, so nothing
	-- here fails the load: BookGolden { [creature id] = true } (a Golden version was ever made: the
	-- Golden page), BookNew (creature ids with a "New!" badge not yet viewed).
	local golden = {}
	if type(data.BookGolden) == "table" then
		for id, value in data.BookGolden do
			if CreatureConfig.Get(id) and value == true then
				golden[id] = true
			end
		end
	end
	data.BookGolden = golden
	local fresh = {}
	if type(data.BookNew) == "table" then
		for _, id in data.BookNew do
			if CreatureConfig.Get(id) and book[id] and not table.find(fresh, id) then
				table.insert(fresh, id)
			end
		end
	end
	data.BookNew = fresh

	-- The daily chest: the day number (os.time() // 86400, UTC) it was last opened, 0 = never.
	data.DailyClaimDay = if isInteger(data.DailyClaimDay, 0, MAX_AMOUNT) then data.DailyClaimDay else 0

	-- Settings (the gear button): music and sound volume 0-1, and reduced effects for low-end phones.
	local settings = if type(data.Settings) == "table" then data.Settings else {}
	local function volume(value)
		return if type(value) == "number" and value == value then math.clamp(value, 0, 1) else 1
	end
	-- (AutoEquip: on unless turned off)
	data.Settings = { Music = volume(settings.Music), Sounds = volume(settings.Sounds), ReducedEffects = settings.ReducedEffects == true,
		AutoEquip = settings.AutoEquip ~= false }

	-- Tutorial: a new player starts it; a step that can't be read counts as done.
	if isNew then
		data.TutorialStep = TUTORIAL_FIRST
	elseif not isInteger(data.TutorialStep, TUTORIAL_FIRST, TUTORIAL_DONE) then
		data.TutorialStep = TUTORIAL_DONE
	end

	-- Purchases: missing (a new player) starts empty. They guard paid grants, so a field that isn't a
	-- table fails closed; unreadable entries are dropped; lists keep their most recent entries.
	for _, field in { "Receipts", "PendingGifts", "GiftInbox", "ReceivedGifts" } do
		if data[field] ~= nil and type(data[field]) ~= "table" then
			return nil, "invalid " .. field
		end
	end
	local receipts = {}
	for _, entry in data.Receipts or {} do
		local receipt = cleanReceipt(entry)
		if receipt and not MonetizationRules.FindReceipt(receipts, receipt.Id) then
			table.insert(receipts, receipt)
		end
	end
	while #receipts > MonetizationRules.MaxReceipts do
		table.remove(receipts, 1)
	end
	data.Receipts = receipts
	local pendingGifts = {}
	for key, intent in data.PendingGifts or {} do
		if MonetizationConfig.GetGiftable(key) then
			pendingGifts[key] = cleanIntent(intent)
		end
	end
	data.PendingGifts = pendingGifts
	local received = {}
	for _, id in data.ReceivedGifts or {} do
		if isIdText(id) and not table.find(received, id) then
			table.insert(received, id)
		end
	end
	while #received > MonetizationRules.MaxGifts do
		table.remove(received, 1)
	end
	data.ReceivedGifts = received
	local inbox = {}
	for _, entry in data.GiftInbox or {} do
		local gift = cleanGift(entry)
		if gift and #inbox < MonetizationRules.MaxGifts and not table.find(received, gift.Id) then
			table.insert(inbox, gift)
		end
	end
	data.GiftInbox = inbox

	-- Paid things the save holds: GiftedPasses ({ [pass key] = true }; a key not in the config any more is
	-- kept, in case it comes back) and MythicBlocks (bought, not rolled yet). A field that can't be read
	-- fails closed; unreadable entries are dropped.
	if data.GiftedPasses ~= nil and type(data.GiftedPasses) ~= "table" then
		return nil, "invalid GiftedPasses"
	end
	local gifted = {}
	for key, value in data.GiftedPasses or {} do
		if type(key) == "string" and #key <= 32 and string.match(key, "^%w+$") and value == true then
			gifted[key] = true
		end
	end
	data.GiftedPasses = gifted
	if data.MythicBlocks ~= nil and not isInteger(data.MythicBlocks, 0, MAX_AMOUNT) then
		return nil, "invalid MythicBlocks"
	end
	data.MythicBlocks = data.MythicBlocks or 0

	-- Codes: missing starts with none. It stops a code paying twice, so a field that isn't a list fails
	-- closed; entries that aren't a code's saved form and repeats are dropped (a code taken out of
	-- CodesConfig stays, in case it comes back); the list keeps its most recent entries.
	if data.Codes ~= nil and type(data.Codes) ~= "table" then
		return nil, "invalid Codes"
	end
	local codes = {}
	for _, code in data.Codes or {} do
		if type(code) == "string" and #code <= MAX_CODE_TEXT and string.match(code, CODE_PATTERN) and not table.find(codes, code) then
			table.insert(codes, code)
		end
	end
	while #codes > MAX_CODES do
		table.remove(codes, 1)
	end
	data.Codes = codes

	-- LeftAt: a time that can't be read pays no offline earnings (and is replaced on the next save).
	-- It never stays in the session's data: load() takes it out.
	local leftAt = data.LeftAt
	if not (type(leftAt) == "number" and leftAt == leftAt and leftAt > 0 and leftAt < math.huge and leftAt % 1 == 0) then
		data.LeftAt = nil
	end

	-- Funnels: only analytics bookkeeping, so nothing here fails the load.
	if isNew then
		data.Funnels = AnalyticsRules.New()
	else
		data.Funnels = AnalyticsRules.Clean(data.Funnels, ONBOARDING_STEPS, PROGRESS_STEPS)
	end

	data.SchemaVersion = SCHEMA_VERSION
	return data
end

-- Where a player's record lives. Studio never touches live saves unless the Workspace attribute
-- StudioUseLiveSaves is true. StudioFreshSave plays as a brand-new player on a throwaway record.
local function storeFor(userId)
	local key = "Player_" .. userId
	if not RunService:IsStudio() then
		return LIVE_STORE, key
	end
	if workspace:GetAttribute("StudioUseLiveSaves") == true then
		warn("[PlayerData] Studio is using LIVE saves (StudioUseLiveSaves)")
		return LIVE_STORE, key
	end
	if workspace:GetAttribute("StudioFreshSave") == true then
		return STUDIO_FRESH_STORE, "Fresh_" .. userId .. "_" .. os.time()
	end
	return STUDIO_STORE, key
end

local function owns(record, session)
	return type(record) == "table" and type(record.Session) == "table" and record.Session.Id == session.id
end

-- One UpdateAsync with bounded retries and backoff, inside one deadline. The transform must not
-- yield and may run more than once, so it resets anything it reports at its top.
local updateRequests = 0 -- UpdateAsync calls made by this server (PlayerData.RequestCount, debug menu)

local function update(storeName, key, transform, deadline)
	local lastError = "request deadline passed"
	for attempt = 1, MAX_ATTEMPTS do
		if os.clock() >= deadline then
			break
		end
		updateRequests += 1
		local ok, result = pcall(function()
			return DataStoreService:GetDataStore(storeName):UpdateAsync(key, function(current)
				if os.clock() >= deadline then
					return nil -- nil cancels the write
				end
				return transform(current)
			end)
		end)
		if ok then
			return true, result
		end
		lastError = tostring(result)
		local backoff = 2 ^ attempt
		if attempt < MAX_ATTEMPTS and os.clock() + backoff < deadline then
			task.wait(backoff)
		end
	end
	return false, lastError
end

-- How many UpdateAsync requests this server has made (loads, saves, gifts), for the DataStore budget.
function PlayerData.RequestCount(): number
	return updateRequests
end

-- Gameplay may use a player's data only while this is true.
function PlayerData.IsReady(player)
	local session = sessions[player]
	return session ~= nil
		and session.loaded
		and not session.closing
		and not session.failed
		and not shuttingDown
		and player.Parent == Players
		and os.time() < session.expiresAt - LEASE_SAFETY_SECONDS
end

-- Display copies for clients: the HUD reads player attributes, never the save, and the server never
-- reads them back. (The server tick will refresh Crystals about 4 times a second.)
local function publish(player, session)
	local data = session.data
	player:SetAttribute("Crystals", data.Crystals)
	player:SetAttribute("BlockLevel", data.BlockLevel)
	player:SetAttribute("Rebirths", data.Rebirths)
	player:SetAttribute("FrostCores", data.FrostCores)
	-- Everything the panels show (Build, Upgrades, Pets, Book, Rebirth), as one JSON copy. The client
	-- works prices out from it with the same rules (EconomyRules); the server checks every request.
	player:SetAttribute("Progress", HttpService:JSONEncode({
		Buildings = data.Buildings,
		Upgrades = data.Upgrades,
		Pets = data.Pets,
		Equipped = data.Equipped,
		BookSeen = data.BookSeen,
		BookNew = data.BookNew,
		BookGolden = data.BookGolden,
		BlockLevel = data.BlockLevel,
		MaxLayerOpened = data.MaxLayerOpened,
		FrostCores = data.FrostCores,
		Rebirths = data.Rebirths,
		CrystalsThisRun = data.CrystalsThisRun,
		CreaturesRescued = data.CreaturesRescued,
		TutorialStep = data.TutorialStep,
		Settings = data.Settings,
		DailyClaimDay = data.DailyClaimDay,
		MythicBlocks = data.MythicBlocks,
	}))
end

-- A session that can't be trusted stops: no gameplay, and it never saves.
local function fail(player, session, reason)
	if session.failed then
		return
	end
	session.failed = true
	player:SetAttribute("DataLoaded", false)
	warn(string.format("[PlayerData] FAILED %d: %s. No save will be written.", player.UserId, reason))
	if player.Parent == Players then
		player:Kick("Your data couldn't be loaded safely. Please rejoin in a few minutes.")
	end
end

-- What this session writes: a checked deep copy of its data, or nil if the runtime state is invalid.
local function gameFieldsValid(data): boolean
	if not (isAmount(data.Crystals) and isAmount(data.CrystalsThisRun) and isAmount(data.CrystalsAllTime)
		and isInteger(data.BlockLevel, 1, MAX_LEVEL) and isInteger(data.FrostCores, 0, MAX_AMOUNT)
		and isInteger(data.Rebirths, 0, MAX_REBIRTHS) and isInteger(data.MaxLayerOpened, 1, MAX_LAYER)
		and isInteger(data.CreaturesRescued, 0, MAX_AMOUNT) and isInteger(data.TutorialStep, TUTORIAL_FIRST, TUTORIAL_DONE)) then
		return false
	end
	if data.CurrentBlock ~= nil and cleanBlock(data.CurrentBlock) == nil then
		return false
	end
	if type(data.Buildings) ~= "table" or type(data.Upgrades) ~= "table" or type(data.Pets) ~= "table"
		or type(data.Equipped) ~= "table" or type(data.BookSeen) ~= "table" then
		return false
	end
	for id, count in data.Buildings do
		if not BuildingConfig.Get(id) or not isInteger(count, 0, MAX_OWNED) then
			return false
		end
	end
	local seenUpgrades = {}
	for _, id in data.Upgrades do
		if not UpgradeConfig.Get(id) or seenUpgrades[id] then
			return false
		end
		seenUpgrades[id] = true
	end
	if #data.Pets > INVENTORY_SIZE or #data.Equipped > MAX_EQUIPPED then
		return false
	end
	local uids = {}
	for _, pet in data.Pets do
		if cleanPet(pet) == nil or uids[pet.Uid] or (pet.Golden ~= true and pet.Golden ~= false)
			or (pet.Locked ~= nil and pet.Locked ~= true) then
			return false
		end
		uids[pet.Uid] = true
	end
	local seenEquipped = {}
	for _, uid in data.Equipped do
		if not uids[uid] or seenEquipped[uid] then
			return false
		end
		seenEquipped[uid] = true
	end
	for id, count in data.BookSeen do
		if not CreatureConfig.Get(id) or not isInteger(count, 1, MAX_AMOUNT) then
			return false
		end
	end
	if type(data.BookGolden) ~= "table" or type(data.BookNew) ~= "table" or type(data.Settings) ~= "table"
		or not isInteger(data.DailyClaimDay, 0, MAX_AMOUNT) then
		return false
	end
	for id, value in data.BookGolden do
		if not CreatureConfig.Get(id) or value ~= true then
			return false
		end
	end
	for _, id in data.BookNew do
		if not CreatureConfig.Get(id) then
			return false
		end
	end
	return true
end

local function snapshot(session)
	local data = session.data
	if not gameFieldsValid(data) then
		return nil
	end
	if type(data.Receipts) ~= "table" or #data.Receipts > MonetizationRules.MaxReceipts
		or type(data.PendingGifts) ~= "table" or type(data.ReceivedGifts) ~= "table"
		or type(data.GiftedPasses) ~= "table" or not isInteger(data.MythicBlocks, 0, MAX_AMOUNT) then
		return nil
	end
	for _, receipt in data.Receipts do
		if type(receipt) ~= "table" or not isIdText(receipt.Id) then
			return nil
		end
	end
	if type(data.Codes) ~= "table" or #data.Codes > MAX_CODES then
		return nil
	end
	for _, code in data.Codes do
		if type(code) ~= "string" or not string.match(code, CODE_PATTERN) then
			return nil
		end
	end
	if not AnalyticsRules.IsClean(data.Funnels, ONBOARDING_STEPS, PROGRESS_STEPS) then
		return nil
	end
	local copy = deepCopy(data)
	copy.GiftInbox = nil -- never written from memory: save() merges the stored inbox
	return copy
end

-- Writes the session's data. release = true is the final save: it also gives up the lease.
-- Returns whether the write is confirmed.
local function save(player, session, release)
	if not session.loaded or session.failed then
		return false
	end
	local data = snapshot(session)
	if not data then
		fail(player, session, "runtime data is invalid; save refused")
		return false
	end
	session.saving = true
	-- A change made while this save yields sets the flag again and gets its own save.
	local important = session.importantSavePending
	session.importantSavePending = false
	local writeId = HttpService:GenerateGUID(false)
	local rejection, arrivals
	local ok, record = update(session.storeName, session.key, function(current)
		rejection, arrivals = nil, {}
		-- A retry after our own write committed (its response was lost): it is already there.
		if type(current) == "table" and current.LastWriteId == writeId then
			return current
		end
		if not owns(current, session) or type(current.Session.ExpiresAt) ~= "number" or current.Session.ExpiresAt <= os.time() then
			rejection = "the session lease was lost or expired"
			return nil
		end
		local updated = table.clone(current) -- unknown fields are kept
		for field, value in data do
			updated[field] = value
		end
		-- Other players' gifts are added to the stored inbox (UpdateRecord): keep what is there, minus
		-- the gifts this session has given. Whatever is left hasn't been given yet: it "arrives".
		local kept = {}
		for _, entry in (if type(current.GiftInbox) == "table" then current.GiftInbox else {}) do
			local gift = cleanGift(entry)
			if gift and not table.find(data.ReceivedGifts, gift.Id) then
				table.insert(kept, gift)
				table.insert(arrivals, gift)
			end
		end
		updated.GiftInbox = kept
		updated.LastWriteId = writeId
		updated.LeftAt = os.time() -- the server's clock: when this player was last known to be here
		if release then
			updated.Session = nil
		else
			updated.Session = { Id = session.id, ExpiresAt = os.time() + LEASE_SECONDS }
		end
		return updated
	end, os.clock() + REQUEST_SECONDS)
	session.saving = false
	if ok and type(record) == "table" and record.LastWriteId == writeId then
		if not release then
			session.expiresAt = record.Session.ExpiresAt
		end
		if savedListener and not session.throwaway then
			task.spawn(savedListener, player.UserId, data, release)
		end
		if not release and giftListener and #arrivals > 0 then
			task.spawn(giftListener, player, arrivals)
		end
		return true
	end
	if rejection then
		fail(player, session, rejection)
	else
		if important then
			session.importantSavePending = true
		end
		warn(string.format("[PlayerData] save failed for %d: %s", player.UserId, tostring(record)))
	end
	return false
end

local function close(player, session)
	session.closing = true
	player:SetAttribute("DataLoaded", false)
	-- Still loading: the loader calls close again when its request finishes.
	if session.loading or session.closeStarted then
		return
	end
	session.closeStarted = true
	while session.saving do
		task.wait(0.1)
	end
	save(player, session, true)
	session.finished = true
	if sessions[player] == session then
		sessions[player] = nil
	end
end

local function load(player)
	if sessions[player] or shuttingDown then
		return
	end
	local storeName, key = storeFor(player.UserId)
	local session = {
		id = HttpService:GenerateGUID(false),
		storeName = storeName,
		key = key,
		throwaway = storeName == STUDIO_FRESH_STORE, -- kept off future leaderboards
		loading = true,
		loaded = false,
		expiresAt = 0,
	}
	sessions[player] = session
	player:SetAttribute("DataLoaded", false)
	local rejection, isNew = nil, false
	local ok, record
	for attempt = 1, LEASE_WAIT_ATTEMPTS do
		ok, record = update(storeName, key, function(current)
			rejection = nil
			if session.closing or shuttingDown then
				return nil
			end
			local data, reason = validate(current)
			if not data then
				rejection = reason
				return nil
			end
			local lease = data.Session
			if lease ~= nil then
				if type(lease) ~= "table" or type(lease.Id) ~= "string" or not isInteger(lease.ExpiresAt, 0, math.huge) then
					rejection = "invalid session lease"
					return nil
				end
				if lease.Id ~= session.id and lease.ExpiresAt > os.time() then
					rejection = LEASE_HELD
					return nil
				end
			end
			-- NEW is remembered across a retry of our own committed claim.
			isNew = current == nil or (owns(current, session) and isNew)
			data.Session = { Id = session.id, ExpiresAt = os.time() + LEASE_SECONDS }
			return data
		end, os.clock() + REQUEST_SECONDS)
		if rejection ~= LEASE_HELD or session.closing or attempt == LEASE_WAIT_ATTEMPTS then
			break
		end
		task.wait(LEASE_WAIT_SECONDS)
	end
	session.loading = false
	if not ok or not owns(record, session) then
		if not session.closing then
			fail(player, session, rejection or tostring(record))
		end
		session.finished = true
		sessions[player] = nil
		return
	end
	session.expiresAt = record.Session.ExpiresAt
	local data = deepCopy(record)
	local inbox = data.GiftInbox or {}
	data.Session, data.LastWriteId, data.GiftInbox = nil, nil, nil -- (the inbox lives in the store only)
	-- When they left last time: offline earnings read it once (TakeLeftAt). Saves write a new one.
	session.leftAt = data.LeftAt
	data.LeftAt = nil
	session.data = data
	session.loaded = true
	session.nextSave = os.clock() + AUTOSAVE_SECONDS + math.random(0, 10) -- jitter spreads the saves
	publish(player, session)
	print(string.format("[PlayerData] %s %d (%s)", if isNew then "NEW" else "LOADED", player.UserId, storeName))
	if session.closing or shuttingDown or player.Parent ~= Players then
		close(player, session)
	elseif os.time() >= session.expiresAt - LEASE_SAFETY_SECONDS then
		fail(player, session, "load finished too close to the lease deadline")
	else
		player:SetAttribute("DataLoaded", true)
		for _, callback in loadedListeners do
			task.spawn(callback, player, data)
		end
		-- Gifts queued while the player was away.
		if giftListener and #inbox > 0 then
			task.spawn(giftListener, player, inbox)
		end
	end
end

-- Gameplay API ---------------------------------------------------------------------------------

-- A copy for reading. Changing it changes nothing.
function PlayerData.Get(player)
	if not PlayerData.IsReady(player) then
		return nil
	end
	return deepCopy(sessions[player].data)
end

-- The LIVE data table, or nil while the player's data isn't ready. Change it only from the
-- server's own numbers and keep every field valid (each save checks it).
function PlayerData.Edit(player)
	if not PlayerData.IsReady(player) then
		return nil
	end
	return sessions[player].data
end

-- Refreshes the display copies after a change made through Edit.
function PlayerData.Publish(player)
	local session = sessions[player]
	if session and session.loaded then
		publish(player, session)
	end
end

-- Debug menu: the player's live data becomes a brand-new player's (in place: the session and its
-- lease stay, and other modules' references to the table stay valid). Saved on the next tick.
-- Returns whether it reset.
function PlayerData.ResetToNew(player): boolean
	local session = sessions[player]
	if not session or not PlayerData.IsReady(player) then
		return false
	end
	local fresh = validate(nil)
	fresh.GiftInbox = nil
	-- Purchase bookkeeping survives a reset: it is what stops a receipt or a gift paying twice; and what
	-- was paid for and not used up stays too (gifted passes, Mythic Blocks not rolled yet).
	for _, field in { "Receipts", "PendingGifts", "ReceivedGifts", "GiftedPasses", "MythicBlocks" } do
		fresh[field] = session.data[field]
	end
	session.leftAt = nil -- a fresh save has never been away
	table.clear(session.data)
	for field, value in fresh do
		session.data[field] = value
	end
	session.importantSavePending = true
	publish(player, session)
	return true
end

-- The server time of this player's last save before this session (when they left, or the last
-- autosave before a crash), or nil (a new player, or already taken). Returns it only once per
-- session, so offline earnings are paid once.
function PlayerData.TakeLeftAt(player): number?
	local session = sessions[player]
	if not session or not PlayerData.IsReady(player) then
		return nil
	end
	local leftAt = session.leftAt
	session.leftAt = nil
	return leftAt
end

-- A throwaway record (Studio's StudioFreshSave): kept off leaderboards.
function PlayerData.IsThrowaway(player): boolean
	local session = sessions[player]
	return session ~= nil and session.throwaway == true
end

-- Asks for a save on the next tick (within 5 seconds) instead of the next autosave.
-- For anything paid for or rare.
function PlayerData.MarkImportant(player)
	local session = sessions[player]
	if session then
		session.importantSavePending = true
	end
end

-- Waits up to `seconds` for the player's data. Returns the live data table, or nil. Yields.
function PlayerData.WaitForData(player, seconds)
	local deadline = os.clock() + (seconds or 30)
	while not PlayerData.IsReady(player) do
		local session = sessions[player]
		if os.clock() >= deadline or player.Parent ~= Players or (session and session.failed) then
			return nil
		end
		task.wait(0.25)
	end
	return sessions[player].data
end

-- Saves now (after any save already running). True once the write is confirmed. Yields.
function PlayerData.SaveNow(player)
	local session = sessions[player]
	if not session or not PlayerData.IsReady(player) then
		return false
	end
	while session.saving do
		task.wait(0.1)
	end
	if sessions[player] ~= session or session.closing or session.failed then
		return false
	end
	return save(player, session, false)
end

-- callback(player, liveData) runs in its own thread once a player's data has loaded.
function PlayerData.OnLoaded(callback)
	table.insert(loadedListeners, callback)
end

-- callback(userId, savedData, final) runs after each confirmed save, in its own thread
-- (for leaderboard mirrors later). final is the save made as the player leaves.
function PlayerData.OnSaved(callback)
	savedListener = callback
end

-- Where a loaded player's record lives: its store name and key (a gift intent saves these, so the
-- gift reaches this exact record even after the recipient leaves). nil while not ready.
function PlayerData.RecordLocation(player)
	local session = sessions[player]
	if not session or not PlayerData.IsReady(player) then
		return nil
	end
	return session.storeName, session.key
end

-- One UpdateAsync on any player's saved record (here, in another server or offline), for writes
-- such as queuing a gift. transform(record) gets the saved table (nil if there is none) and returns
-- the changed table, or nil to cancel; it must not yield and may run more than once. Only write fields
-- the owner's own saves merge instead of overwriting (GiftInbox). Returns true when it committed. Yields.
function PlayerData.UpdateRecord(storeName: string, key: string, transform): boolean
	return (update(storeName, key, transform, os.clock() + REQUEST_SECONDS))
end

-- callback(player, gifts) runs in its own thread with gifts queued for a loaded player that
-- haven't been given yet: on join, and after any save finds new ones (another server added them, or
-- one couldn't be given before). The callback gives each one once and adds its id to ReceivedGifts.
function PlayerData.OnGiftsArrived(callback)
	giftListener = callback
end

-- Lifecycle -------------------------------------------------------------------------------------

-- Every 5 seconds: save flagged sessions, renew leases on schedule, and stop any session whose
-- lease could run out. (Public so tests can drive it.)
function PlayerData.AutosaveTick()
	for player, session in sessions do
		if session.loaded and not session.closing and not session.failed then
			if os.time() >= session.expiresAt - LEASE_SAFETY_SECONDS then
				fail(player, session, "autosave could not renew the lease in time")
			elseif not session.saving then
				local now = os.clock()
				local important = session.importantSavePending and now - (session.lastImportantSave or -math.huge) >= IMPORTANT_GAP_SECONDS
				if important or now >= session.nextSave then
					if important then
						session.lastImportantSave = now
					end
					session.nextSave = now + AUTOSAVE_SECONDS
					task.spawn(save, player, session, false)
				end
			end
		end
	end
end

-- The server is closing: stops gameplay saves for everyone, then saves and releases every session at
-- once. Yields until all are written (true) or `seconds` pass (false). Safe to call more than once
-- (SoftShutdown calls it before teleporting players, and BindToClose again).
function PlayerData.CloseAll(seconds: number): boolean
	shuttingDown = true
	local pending = {}
	for player, session in sessions do
		table.insert(pending, session)
		task.spawn(close, player, session)
	end
	local deadline = os.clock() + seconds
	while os.clock() < deadline do
		local done = true
		for _, session in pending do
			if not session.finished then
				done = false
				break
			end
		end
		if done then
			return true
		end
		task.wait(0.1)
	end
	return false
end

function PlayerData.Start()
	if started then
		return
	end
	started = true
	Players.PlayerAdded:Connect(load)
	Players.PlayerRemoving:Connect(function(player)
		local session = sessions[player]
		if session then
			close(player, session)
		end
	end)
	for _, player in Players:GetPlayers() do
		task.spawn(load, player)
	end
	task.spawn(function()
		while not shuttingDown do
			task.wait(5)
			PlayerData.AutosaveTick()
		end
	end)
	-- Closing the server (and pressing Stop in Studio): save everyone at once, within the time limit.
	game:BindToClose(function()
		if not PlayerData.CloseAll(SHUTDOWN_SECONDS) then
			warn("[PlayerData] shutdown deadline reached before every save finished")
		end
	end)
end

return PlayerData
