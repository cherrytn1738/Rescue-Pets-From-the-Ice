--[[
Spec for src/server/PlayerData.luau (schema 1).

Runs the REAL PlayerData module against fakes (tests/FakeDataStore.luau, fake players, a fake
clock). No live save, player or Instance is touched. Run: python tools/run_specs.py PlayerData

setfenv swaps the module's globals (game, workspace, os, task, require) for fakes, so the module
needs no test hooks. The game's MonetizationConfig and AnalyticsConfig are empty until this game
adds its products and onboarding steps, so the spec gives PlayerData test versions of both: one
test product and ten onboarding steps. The game configs (CreatureConfig, BuildingConfig,
UpgradeConfig, LayerConfig) are the real ones, and the save's fields are checked against the design
doc's "Data and code structure" table. A failed check errors with its message.
]]
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local FakeDataStore = assert(loadstring(sources.FakeDataStore))()
	local LIVE, STUDIO, FRESH = "IcePets_PlayerData", "IcePets_PlayerData_Studio", "IcePets_PlayerData_StudioFresh"

	-- Test configs (the real ones are empty for now).
	local testProducts = {
		TestProduct = { Key = "TestProduct", Name = "Test product", ProductId = 1, Reward = { Kind = "Test" } },
		OtherProduct = { Key = "OtherProduct", Name = "Other product", ProductId = 2, Reward = { Kind = "Test" } },
	}
	local TestMonetizationConfig = {
		Passes = {},
		Products = { testProducts.TestProduct, testProducts.OtherProduct },
		GetProduct = function(key)
			return testProducts[key]
		end,
		GetPass = function()
			return nil
		end,
		IsPaidRandom = function()
			return false
		end,
	}
	local TestAnalyticsConfig = { Onboarding = { "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10" } }
	local STEPS = #TestAnalyticsConfig.Onboarding

	-- Loads a replicated module whose own requires (if any) see the test configs.
	local testReplicated = { MonetizationConfig = TestMonetizationConfig, AnalyticsConfig = TestAnalyticsConfig }
	local function loadShared(name)
		local chunk = assert(loadstring(sources[name], name))
		setfenv(chunk, setmetatable({
			game = {
				GetService = function()
					return testReplicated
				end,
			},
			script = { Parent = testReplicated },
			require = function(module)
				return module
			end,
		}, { __index = getfenv(1) }))
		return chunk()
	end
	local MonetizationRules = loadShared("MonetizationRules")
	local AnalyticsRules = loadShared("AnalyticsRules")
	testReplicated.MonetizationRules = MonetizationRules
	testReplicated.AnalyticsRules = AnalyticsRules
	-- The game's real configs (the save checks ids against them).
	for _, name in { "LayerConfig", "CreatureConfig", "BuildingConfig", "UpgradeConfig" } do
		testReplicated[name] = loadShared(name)
	end
	local CreatureConfig, LayerConfig = testReplicated.CreatureConfig, testReplicated.LayerConfig
	local realHttp = game:GetService("HttpService")

	-- A fake clock: task.wait moves time on instantly.
	local now = 1000000
	local spawnEnabled = false
	local fakeTask = {
		wait = function(seconds)
			now += seconds or 0
		end,
		-- Loops started inside Start() (the autosave loop) are dropped; later threads run at once.
		spawn = function(fn, ...)
			if spawnEnabled then
				fn(...)
			end
		end,
	}

	local function signal()
		local callbacks = {}
		return {
			Connect = function(_, fn)
				table.insert(callbacks, fn)
			end,
			Fire = function(_, ...)
				for _, fn in callbacks do
					fn(...)
				end
			end,
		}
	end

	local players = { PlayerAdded = signal(), PlayerRemoving = signal(), list = {} }
	function players:GetPlayers()
		return table.clone(self.list)
	end
	local function join(userId)
		local attributes = {}
		local player = { UserId = userId, Parent = players }
		function player:GetAttribute(name)
			return attributes[name]
		end
		function player:SetAttribute(name, value)
			attributes[name] = value
		end
		function player:Kick(reason)
			self.KickReason = reason
		end
		table.insert(players.list, player)
		players.PlayerAdded:Fire(player)
		return player
	end
	local function leave(player)
		players.PlayerRemoving:Fire(player) -- (Roblox fires it while Parent is still Players)
		table.remove(players.list, table.find(players.list, player))
		player.Parent = nil
	end

	local workspaceAttributes = {}
	local fakeWorkspace = {
		GetAttribute = function(_, name)
			return workspaceAttributes[name]
		end,
		SetAttribute = function(_, name, value)
			workspaceAttributes[name] = value
		end,
	}
	local inStudio = false
	local guid = 0
	local store = FakeDataStore.new()
	local closeCallback
	local services = {
		Players = players,
		DataStoreService = store.service,
		RunService = {
			IsStudio = function()
				return inStudio
			end,
		},
		HttpService = {
			GenerateGUID = function()
				guid += 1
				return "guid-" .. guid
			end,
			JSONEncode = function(_, value)
				return realHttp:JSONEncode(value)
			end,
		},
		ReplicatedStorage = testReplicated,
	}
	local env = setmetatable({
		game = {
			GetService = function(_, name)
				return assert(services[name], "unexpected service " .. name)
			end,
			BindToClose = function(_, fn)
				closeCallback = fn
			end,
		},
		workspace = fakeWorkspace,
		task = fakeTask,
		os = {
			clock = function()
				return now
			end,
			time = function()
				return math.floor(now)
			end,
		},
		require = function(module)
			return module
		end,
		print = function() end,
		warn = function() end,
	}, { __index = getfenv(1) })
	local chunk = assert(loadstring(sources.PlayerData, "PlayerData"))
	setfenv(chunk, env)
	local PlayerData = chunk()

	-- The store names are this game's own: never the Steal Pets ones.
	local storeNames = {}
	for name in string.gmatch(sources.PlayerData, '_STORE = "([^"]+)"') do
		storeNames[name] = true
	end
	check(storeNames[LIVE] and storeNames[STUDIO] and storeNames[FRESH], "the stores are " .. LIVE .. ", " .. STUDIO .. " and " .. FRESH)
	for _, oldName in { "PlayerData", "PlayerData_Studio", "PlayerData_StudioFresh" } do
		check(not storeNames[oldName], "the old game's store name " .. oldName .. " is not used")
	end
	check(PlayerData.SCHEMA_VERSION == 1, "the schema starts at 1")

	local loadedCalls = {}
	PlayerData.OnLoaded(function(player)
		table.insert(loadedCalls, player.UserId)
	end)
	PlayerData.Start()
	spawnEnabled = true

	local function record(userId, storeName)
		local saved = store.saved[storeName or LIVE]
		return saved and saved["Player_" .. userId]
	end
	local function put(userId, value)
		store.saved[LIVE] = store.saved[LIVE] or {}
		store.saved[LIVE]["Player_" .. userId] = value
	end

	-- New player: defaults, a lease, and the loaded callback.
	local newbie = join(1)
	local data = PlayerData.Get(newbie)
	check(PlayerData.IsReady(newbie), "a new player is ready")
	check(#data.Receipts == 0 and next(data.PendingGifts) == nil and #data.ReceivedGifts == 0 and #data.Codes == 0,
		"a new player starts with no receipts, gift intents, received gifts or codes")
	check(data.GiftInbox == nil and data.LeftAt == nil and data.Session == nil, "the inbox, leave time and lease never sit in the session's data")
	check(data.Funnels.Onboarding == 0 and #data.Funnels.Waiting == 0, "...and has logged no funnel steps")
	check(record(1).Session ~= nil and record(1).SchemaVersion == 1, "login writes schema 1 and claims the lease")
	check(table.find(loadedCalls, 1) ~= nil, "OnLoaded runs once the data is ready")
	check(newbie:GetAttribute("DataLoaded") == true, "DataLoaded is published")
	local copy = PlayerData.Get(newbie)
	table.insert(copy.Codes, "CHANGED")
	check(#PlayerData.Get(newbie).Codes == 0, "Get hands out a copy: changing it changes nothing")
	table.insert(PlayerData.Edit(newbie).Codes, "WELCOME")
	leave(newbie)
	check(record(1).Session == nil and record(1).Codes[1] == "WELCOME", "leaving saves and releases the lease")
	check(newbie:GetAttribute("DataLoaded") == false, "DataLoaded goes false on leaving")

	-- Rejoin: everything comes back.
	newbie = join(1)
	check(PlayerData.Get(newbie).Codes[1] == "WELCOME", "rejoining loads the saved data")
	leave(newbie)

	-- The game's fields (docs/GAME_DESIGN.md, "Data and code structure"): defaults for a new player.
	local starter = join(30)
	data = PlayerData.Get(starter)
	check(data.Crystals == 0 and data.CrystalsThisRun == 0 and data.CrystalsAllTime == 0, "a new player has no crystals")
	check(data.BlockLevel == 1 and data.CurrentBlock == nil, "...starts at block level 1 with no block rolled yet")
	check(next(data.Buildings) == nil and #data.Upgrades == 0, "...with no buildings or upgrades")
	check(#data.Pets == 0 and #data.Equipped == 0 and next(data.BookSeen) == nil, "...no pets, none equipped, an empty Creature Book")
	check(data.FrostCores == 0 and data.Rebirths == 0 and data.CreaturesRescued == 0, "...no Frost Cores, rebirths or rescues")
	check(data.MaxLayerOpened == LayerConfig.FloorLayer, "...and every layer down to the floor layer (" .. LayerConfig.FloorLayer .. ") open")
	check(data.TutorialStep == 1, "...on the tutorial's first step")
	check(starter:GetAttribute("Crystals") == 0 and starter:GetAttribute("BlockLevel") == 1, "display attributes are published")

	-- Every field of the design doc's table is in a new save (under this code's PascalCase names; the
	-- doc's codesRedeemed, lastOnline and purchaseIds are Codes, LeftAt and Receipts).
	local DesignDoc = assert(loadstring(sources.DesignDoc))()
	local doc = DesignDoc.new(sources["GAME_DESIGN.md"])
	local renamed = { codesRedeemed = "Codes", lastOnline = "LeftAt", purchaseIds = "Receipts" }
	local fieldRows = doc:Table({ "Field", "Type", "Reset on rebirth" })
	check(#fieldRows == 14, "the doc's save table has its 14 rows")
	for _, row in fieldRows do
		for docName in string.gmatch(row.Field, "[%a]+") do
			local name = renamed[docName] or (string.upper(string.sub(docName, 1, 1)) .. string.sub(docName, 2))
			local present = data[name] ~= nil or name == "CurrentBlock" or name == "LeftAt"
			check(present, "the save has the doc's field " .. docName .. " (as " .. name .. ")")
		end
	end

	-- Progress is saved and comes back.
	local live = PlayerData.Edit(starter)
	live.Crystals, live.CrystalsThisRun, live.CrystalsAllTime = 1234.5, 2000, 1e40
	live.BlockLevel, live.CurrentBlock = 24, { CreatureId = "FrostDragonHatchling", HpLeft = 31.25 }
	live.Buildings.IcePickPost, live.Buildings.HeatLamp = 12, 3
	table.insert(live.Upgrades, "IcePick2")
	table.insert(live.Upgrades, "IcePickPostUpgrade1")
	table.insert(live.Pets, { Uid = "pet-1", CreatureId = "SnowBunny", Golden = false })
	table.insert(live.Pets, { Uid = "pet-2", CreatureId = "AuroraFox", Golden = true })
	table.insert(live.Equipped, "pet-2")
	live.BookSeen.SnowBunny, live.BookSeen.AuroraFox = 6, 1
	live.FrostCores, live.Rebirths, live.MaxLayerOpened, live.CreaturesRescued, live.TutorialStep = 7, 3, 6, 9, 5
	leave(starter)
	local saved = record(30)
	check(saved.Crystals == 1234.5 and saved.CrystalsAllTime == 1e40 and saved.BlockLevel == 24, "crystals (fractional and huge) and the block level are saved")
	check(saved.CurrentBlock.CreatureId == "FrostDragonHatchling" and saved.CurrentBlock.HpLeft == 31.25, "the block in progress is saved with its creature and HP")
	check(saved.Buildings.IcePickPost == 12 and saved.Buildings.HeatLamp == 3, "building counts are saved")
	starter = join(30)
	data = PlayerData.Get(starter)
	check(data.Crystals == 1234.5 and data.CrystalsThisRun == 2000 and data.BlockLevel == 24 and data.CurrentBlock.HpLeft == 31.25,
		"rejoining loads the crystals, level and block")
	check(data.Buildings.HeatLamp == 3 and data.Upgrades[2] == "IcePickPostUpgrade1" and #data.Pets == 2 and data.Pets[2].Golden == true,
		"...the buildings, upgrades and pets")
	check(data.Equipped[1] == "pet-2" and data.BookSeen.SnowBunny == 6 and data.FrostCores == 7 and data.Rebirths == 3
		and data.MaxLayerOpened == 6 and data.CreaturesRescued == 9 and data.TutorialStep == 5, "...and the rest")
	check(starter:GetAttribute("Crystals") == 1234.5 and starter:GetAttribute("Rebirths") == 3, "the attributes show the loaded values")
	leave(starter)

	-- Loading cleans what it can: unknown ids are dropped, a broken block is rolled again.
	put(31, {
		SchemaVersion = 1,
		CurrentBlock = { CreatureId = "Dinosaur", HpLeft = 10 },
		Buildings = { IcePickPost = 2, RetiredBuilding = 4, HeatLamp = 0 },
		Upgrades = { "IcePick2", "IcePick2", "NoSuchUpgrade", 5 },
		Pets = {
			{ Uid = "a", CreatureId = "SealPup", Golden = "yes" },
			{ Uid = "a", CreatureId = "SealPup" },
			{ Uid = "b", CreatureId = "Dinosaur" },
			{ Uid = "", CreatureId = "SealPup" },
			"junk",
			{ Uid = "c", CreatureId = "MiniYeti", Golden = true },
		},
		Equipped = { "c", "c", "b", "nope", 7, "a" },
		BookSeen = { SealPup = 3, MiniYeti = "lots", Dinosaur = 2 },
		TutorialStep = 99,
	})
	local messyGame = join(31)
	data = PlayerData.Get(messyGame)
	check(PlayerData.IsReady(messyGame) and data.CurrentBlock == nil, "a block with an unknown creature is rolled again")
	check(data.Buildings.IcePickPost == 2 and data.Buildings.RetiredBuilding == nil and data.Buildings.HeatLamp == nil, "unknown buildings and zero counts are dropped")
	check(#data.Upgrades == 1 and data.Upgrades[1] == "IcePick2", "unknown, repeated and junk upgrades are dropped")
	check(#data.Pets == 2 and data.Pets[1].Uid == "a" and data.Pets[1].Golden == false and data.Pets[2].Uid == "c",
		"pets: repeated uids, unknown creatures, empty uids and junk are dropped; Golden is a boolean")
	check(#data.Equipped == 2 and data.Equipped[1] == "c" and data.Equipped[2] == "a", "equipped: only owned pets, each once")
	check(data.BookSeen.SealPup == 3 and data.BookSeen.MiniYeti == 1 and data.BookSeen.Dinosaur == nil, "the book keeps seen creatures (an unreadable count is 1) and drops unknown ones")
	check(data.TutorialStep == 5, "a tutorial step that can't be read counts as done")
	leave(messyGame)
	local tooMany = {}
	for index = 1, CreatureConfig.Pets.InventorySize + 5 do
		table.insert(tooMany, { Uid = "p" .. index, CreatureId = "SnowBunny" })
	end
	local allUids = {}
	for index = 1, 10 do
		table.insert(allUids, "p" .. index)
	end
	put(32, { SchemaVersion = 1, Pets = tooMany, Equipped = allUids })
	local hoarderPets = join(32)
	data = PlayerData.Get(hoarderPets)
	check(#data.Pets == CreatureConfig.Pets.InventorySize and #data.Equipped == CreatureConfig.Pets.MaxEquipSlots,
		"at most a full inventory (" .. CreatureConfig.Pets.InventorySize .. ") and the maximum equip slots (" .. CreatureConfig.Pets.MaxEquipSlots .. ")")
	leave(hoarderPets)

	-- Progress that can't be read fails closed, untouched.
	local broken = {
		{ Crystals = -5 }, { Crystals = "lots" }, { CrystalsThisRun = true }, { CrystalsAllTime = { 5 } },
		{ BlockLevel = 0 }, { BlockLevel = 2.5 }, { FrostCores = -1 }, { Rebirths = "3" }, { MaxLayerOpened = 0 },
		{ CreaturesRescued = 1.5 }, { Buildings = "oops" }, { Buildings = { IcePickPost = 2.5 } }, { Upgrades = "oops" },
		{ Pets = "oops" }, { Equipped = 5 }, { BookSeen = "oops" },
	}
	for index, fields in broken do
		local userId = 200 + index
		local stored = { SchemaVersion = 1 }
		local field, value = next(fields)
		stored[field] = value
		put(userId, stored)
		local player = join(userId)
		check(not PlayerData.IsReady(player) and player.KickReason ~= nil, `unreadable {field} ({tostring(value)}) fails closed`)
		leave(player)
		check(record(userId).Session == nil and record(userId)[field] ~= nil, `...and the record is left as it was`)
	end

	-- Invalid game data at runtime is never saved.
	local nextRuntimeId = 40
	for name, breakIt in {
		negativeCrystals = function(d) d.Crystals = -1 end,
		unknownBuilding = function(d) d.Buildings.Volcano = 1 end,
		equippedNotOwned = function(d) table.insert(d.Equipped, "ghost") end,
		badBlock = function(d) d.CurrentBlock = { CreatureId = "SnowBunny", HpLeft = -3 } end,
	} do
		nextRuntimeId += 1
		local player = join(nextRuntimeId)
		breakIt(PlayerData.Edit(player))
		check(not PlayerData.SaveNow(player) and player.KickReason ~= nil, "a runtime save with " .. name .. " is refused")
		leave(player)
	end

	-- Loading keeps what it doesn't know (the game's own fields until this code knows them).
	put(2, { SchemaVersion = 1, ExtraField = "keep me", Nested = { A = 1 } })
	local veteran = join(2)
	check(PlayerData.IsReady(veteran) and PlayerData.Get(veteran).ExtraField == "keep me", "an unknown field loads")
	leave(veteran)
	check(record(2).ExtraField == "keep me" and record(2).Nested.A == 1, "...and is kept by every save")
	put(21, { ExtraField = "no version" })
	local noVersion = join(21)
	check(PlayerData.IsReady(noVersion), "a record without a SchemaVersion loads as schema 1")
	leave(noVersion)
	check(record(21).SchemaVersion == 1 and record(21).ExtraField == "no version", "...and is saved with SchemaVersion = 1")

	-- Robux receipts and gifts.
	local arrivedGifts = {}
	PlayerData.OnGiftsArrived(function(player, gifts)
		for _, gift in gifts do
			table.insert(arrivedGifts, { userId = player.UserId, id = gift.Id })
		end
	end)
	for _, field in { "Receipts", "PendingGifts", "GiftInbox", "ReceivedGifts" } do
		put(47, { SchemaVersion = 1, [field] = "oops" })
		local broken = join(47)
		check(not PlayerData.IsReady(broken) and broken.KickReason ~= nil and record(47)[field] == "oops", field .. " that isn't a table fails closed, untouched")
		leave(broken)
	end
	local manyReceipts = { { Id = "keep", Product = "TestProduct", At = 5, For = 11 }, { Id = "" }, 5, { Id = "keep" }, { Id = string.rep("x", 100) } }
	for index = 1, 52 do
		table.insert(manyReceipts, { Id = "r" .. index, Product = "TestProduct", At = index })
	end
	put(48, {
		SchemaVersion = 1,
		Receipts = manyReceipts,
		PendingGifts = {
			TestProduct = { Recipient = 11, RecipientName = "Friend", Store = LIVE, Key = "Player_11", State = "purchased", At = 7 },
			OtherProduct = { Recipient = "nobody", Store = LIVE, Key = "Player_11", State = "prompted" },
			RetiredProduct = { Recipient = 11, Store = LIVE, Key = "Player_11", State = "prompted" },
		},
		ReceivedGifts = { "g1", "g1", 5 },
		GiftInbox = {
			{ Id = "g2", Product = "TestProduct", From = 10, FromName = "Giver" },
			{ Id = "g1", Product = "TestProduct", From = 10 },
			{ Id = "g3", Product = "RetiredProduct", From = 10 },
			{ Id = "g4", Product = "TestProduct", From = "ten" },
		},
	})
	local messy = join(48)
	data = PlayerData.Get(messy)
	check(PlayerData.IsReady(messy) and #data.Receipts == MonetizationRules.MaxReceipts and data.Receipts[#data.Receipts].Id == "r52",
		"unreadable or repeated receipts are dropped, and only the most recent " .. MonetizationRules.MaxReceipts .. " are kept")
	check(data.PendingGifts.TestProduct and data.PendingGifts.TestProduct.State == "purchased" and data.PendingGifts.OtherProduct == nil and data.PendingGifts.RetiredProduct == nil,
		"a readable gift intent is kept; a broken one, or one for a product no longer sold, is dropped")
	check(#data.ReceivedGifts == 1 and data.ReceivedGifts[1] == "g1", "received gift ids: repeats and junk are dropped")
	check(#arrivedGifts == 1 and arrivedGifts[1].userId == 48 and arrivedGifts[1].id == "g2",
		"at join, the queued gifts not yet received are handed to the gift system (bad and already-received ones dropped)")
	leave(messy)

	-- The owner's save MERGES the stored inbox: a gift another server adds meanwhile is kept, and a
	-- gift this session has given leaves it.
	local recipient = join(49)
	table.clear(arrivedGifts)
	local saved49 = store.saved[LIVE].Player_49
	saved49.GiftInbox = { { Id = "from-elsewhere", Product = "TestProduct", From = 10, FromName = "Giver" }, { Id = "given-here", Product = "TestProduct", From = 10 } }
	table.insert(PlayerData.Edit(recipient).ReceivedGifts, "given-here")
	check(PlayerData.SaveNow(recipient), "(the recipient saves)")
	check(#record(49).GiftInbox == 1 and record(49).GiftInbox[1].Id == "from-elsewhere", "a save keeps a gift another server queued and drops the one it has given")
	check(#arrivedGifts == 1 and arrivedGifts[1].id == "from-elsewhere", "...and hands the new gift to the gift system")
	-- A reset (debug) never forgets receipts: they are what stops a purchase paying twice.
	local live49 = PlayerData.Edit(recipient)
	table.insert(live49.Receipts, { Id = "paid-1", Product = "TestProduct", At = 1 })
	table.insert(live49.Codes, "SPENT")
	live49.Funnels.Onboarding = 4
	check(PlayerData.ResetToNew(recipient), "(a debug reset)")
	data = PlayerData.Get(recipient)
	check(data.Receipts[1].Id == "paid-1" and data.ReceivedGifts[1] == "given-here", "a debug reset keeps the receipts and received gifts")
	check(#data.Codes == 0 and data.Funnels.Onboarding == 0, "...and starts the codes and funnels again")
	check(live49 == PlayerData.Edit(recipient), "...in place: other modules' references to the live table stay valid")
	-- UpdateRecord: a write to any player's record (a gift), here or offline.
	check(PlayerData.UpdateRecord(LIVE, "Player_2", function(saved)
		saved.GiftInbox = { { Id = "offline-gift", Product = "TestProduct", From = 49, FromName = "Recipient" } }
		return saved
	end) and record(2).GiftInbox[1].Id == "offline-gift", "UpdateRecord writes into an offline player's record")
	check(select(1, PlayerData.RecordLocation(recipient)) == LIVE and select(2, PlayerData.RecordLocation(recipient)) == "Player_49",
		"RecordLocation says where a loaded player's record is")
	leave(recipient)
	PlayerData.OnGiftsArrived(nil)

	-- Redeemed promo codes.
	put(51, { SchemaVersion = 1, Codes = "oops" })
	local badCodes = join(51)
	check(not PlayerData.IsReady(badCodes) and badCodes.KickReason ~= nil and record(51).Codes == "oops", "Codes that isn't a list fails closed, untouched")
	leave(badCodes)
	put(52, { SchemaVersion = 1, Codes = { "RELEASE", "RELEASE", "release", 5, "BAD CODE", string.rep("A", 40), "WINTER", "OLDCODE" } })
	local messyCodes = join(52)
	data = PlayerData.Get(messyCodes)
	check(PlayerData.IsReady(messyCodes) and table.concat(data.Codes, ",") == "RELEASE,WINTER,OLDCODE",
		"redeemed codes: repeats, junk and too-long entries are dropped; a code no longer in the config stays")
	leave(messyCodes)
	local manyCodes = {}
	for index = 1, 205 do
		table.insert(manyCodes, "CODE" .. index)
	end
	put(53, { SchemaVersion = 1, Codes = manyCodes })
	local hoarder = join(53)
	data = PlayerData.Get(hoarder)
	check(#data.Codes == 200 and data.Codes[1] == "CODE6" and data.Codes[200] == "CODE205", "only the most recent 200 redeemed codes are kept")
	table.insert(PlayerData.Edit(hoarder).Codes, "not a code")
	check(not PlayerData.SaveNow(hoarder) and record(53).Codes[1] == "CODE6" and #record(53).Codes == 200,
		"a save with an unreadable redeemed code is refused (the stored record keeps its readable list)")
	leave(hoarder)

	-- LeftAt: the server's clock at every save, for offline earnings.
	local returning = join(64)
	check(PlayerData.TakeLeftAt(returning) == nil, "a new player has no leave time (pays nothing)")
	now += 30
	check(PlayerData.SaveNow(returning) and record(64).LeftAt == math.floor(now), "an autosave writes the server's time (a crash checkpoint)")
	check(PlayerData.Get(returning).LeftAt == nil, "the leave time never sits in the session's data")
	now += 45
	leave(returning)
	local leaveTime = math.floor(now)
	check(record(64).LeftAt == leaveTime and record(64).Session == nil, "the final save writes the leave time and releases the lease")
	now += 600
	local back = join(64)
	check(PlayerData.TakeLeftAt(back) == leaveTime, "the next join reads the leave time")
	check(PlayerData.TakeLeftAt(back) == nil, "...only once per session (offline earnings pay once)")
	leave(back)
	check(record(64).LeftAt == math.floor(now), "...and its own leave replaces it")
	for userId, junk in { [65] = "yesterday", [66] = -5, [67] = 12.5, [68] = 0 / 0, [69] = math.huge } do
		put(userId, { SchemaVersion = 1, LeftAt = junk })
		local player = join(userId)
		check(PlayerData.IsReady(player) and PlayerData.TakeLeftAt(player) == nil, `a leave time that can't be read ({tostring(junk)}) loads but pays nothing`)
		leave(player)
		check(record(userId).LeftAt == math.floor(now), "...and is replaced by a real one on leaving")
	end
	put(71, { SchemaVersion = 1, LeftAt = 1000 })
	local resetMe = join(71)
	check(PlayerData.ResetToNew(resetMe) and PlayerData.TakeLeftAt(resetMe) == nil, "a debug reset forgets the leave time")
	leave(resetMe)

	-- Funnels: how far the one-time analytics funnels have been logged.
	local fresh = join(96)
	PlayerData.Edit(fresh).Funnels.Onboarding, PlayerData.Edit(fresh).Funnels.Waiting = 3, { 6 }
	check(PlayerData.SaveNow(fresh) and record(96).Funnels.Onboarding == 3 and record(96).Funnels.Waiting[1] == 6,
		"funnel progress is saved, waiting steps too (a rejoin never logs a step twice)")
	leave(fresh)
	put(99, { SchemaVersion = 1, Funnels = { Onboarding = "lots", Waiting = { 1, 99, 5, 5 } } })
	local odd = join(99)
	data = PlayerData.Get(odd)
	check(PlayerData.IsReady(odd) and data.Funnels.Onboarding == STEPS and #data.Funnels.Waiting == 0,
		"unreadable funnel progress counts as done and never fails the load")
	leave(odd)
	put(100, { SchemaVersion = 1, Funnels = { Onboarding = 2, Waiting = { 5, 1, 5, 9, 12 } } })
	local waiting = join(100)
	data = PlayerData.Get(waiting)
	check(#data.Funnels.Waiting == 2 and data.Funnels.Waiting[1] == 5 and data.Funnels.Waiting[2] == 9, "waiting steps keep only later, known, unrepeated steps, in order")
	leave(waiting)
	put(101, { SchemaVersion = 1, Funnels = "nope" })
	local notTable = join(101)
	data = PlayerData.Get(notTable)
	check(PlayerData.IsReady(notTable) and data.Funnels.Onboarding == STEPS, "a Funnels that isn't a table counts as done")
	leave(notTable)

	-- Data that can't be read fails closed: no gameplay, a kick, and the record is never rewritten.
	put(3, { SchemaVersion = 99, ExtraField = "future" })
	local future = join(3)
	check(not PlayerData.IsReady(future) and future.KickReason ~= nil, "a newer schema than this server knows fails closed")
	leave(future)
	check(record(3).SchemaVersion == 99 and record(3).Session == nil and record(3).ExtraField == "future", "...and is left exactly as it was")
	put(4, "not a table")
	local junkRecord = join(4)
	leave(junkRecord)
	check(record(4) == "not a table" and junkRecord.KickReason ~= nil, "a record that isn't a table fails closed, untouched")
	put(13, { SchemaVersion = 1, Session = "oops" })
	local badLease = join(13)
	leave(badLease)
	check(record(13).Session == "oops" and badLease.KickReason ~= nil, "an unreadable lease fails closed")

	-- An outage: bounded retries, then a failed session that never saves defaults.
	store.outage.Player_5 = true
	local unlucky = join(5)
	check(not PlayerData.IsReady(unlucky) and store.calls[LIVE .. "/Player_5"] == 3, "retries are bounded (3 attempts)")
	check(unlucky.KickReason ~= nil and PlayerData.Edit(unlucky) == nil and PlayerData.Get(unlucky) == nil, "a failed load is kicked and has no data to play with")
	check(not PlayerData.SaveNow(unlucky), "...and can't save")
	leave(unlucky)
	check(record(5) == nil, "a failed load never writes defaults")
	store.outage.Player_5 = nil

	-- Another server's live lease is respected; a crashed server's expired lease is taken over.
	put(6, { SchemaVersion = 1, Session = { Id = "other-server", ExpiresAt = math.floor(now) + 600 } })
	local hopper = join(6)
	check(not PlayerData.IsReady(hopper) and record(6).Session.Id == "other-server", "a live lease elsewhere is never taken")
	leave(hopper)
	put(7, { SchemaVersion = 1, Codes = { "KEPT" }, Session = { Id = "crashed-server", ExpiresAt = math.floor(now) - 1 } })
	local crashed = join(7)
	check(PlayerData.IsReady(crashed) and record(7).Session.Id ~= "crashed-server", "an expired lease is taken over")
	check(PlayerData.Get(crashed).Codes[1] == "KEPT", "...with the data it held")
	leave(crashed)

	-- Lost response on the final save: the retry finds its own write and still releases.
	local lossy = join(8)
	table.insert(PlayerData.Edit(lossy).Codes, "LOSSY")
	store.loseResponse.Player_8 = true
	leave(lossy)
	check(record(8).Session == nil and record(8).Codes[1] == "LOSSY" and lossy.KickReason == nil, "a lost response on the final save still releases the lease")

	-- Autosave and important saves.
	local saver = join(9)
	local saverData = PlayerData.Edit(saver)
	table.insert(saverData.Codes, "FIRST")
	PlayerData.AutosaveTick()
	check(#record(9).Codes == 0, "nothing is saved before the autosave is due")
	PlayerData.MarkImportant(saver)
	PlayerData.AutosaveTick()
	check(record(9).Codes[1] == "FIRST", "an important change is saved on the next tick")
	table.insert(saverData.Codes, "SECOND")
	now += 75
	PlayerData.AutosaveTick()
	check(record(9).Codes[2] == "SECOND", "the autosave saves after about a minute")
	check(PlayerData.SaveNow(saver), "SaveNow confirms a save")

	-- Invalid runtime data is never saved: the session fails instead.
	saverData.Receipts = "broken"
	check(not PlayerData.SaveNow(saver) and record(9).Codes[2] == "SECOND" and saver.KickReason ~= nil, "invalid runtime data is refused and the session stops")
	check(not PlayerData.IsReady(saver), "...the session is no longer ready")
	leave(saver)
	check(type(record(9).Receipts) == "table", "...and leaving doesn't save it either")

	-- Studio uses its own stores; live saves only on purpose.
	inStudio = true
	local tester = join(11)
	check(record(11) == nil and record(11, STUDIO) ~= nil, "Studio never touches the live store")
	table.insert(PlayerData.Edit(tester).Codes, "STUDIO")
	leave(tester)
	tester = join(11)
	check(PlayerData.Get(tester).Codes[1] == "STUDIO", "the Studio record keeps its own data between plays")
	leave(tester)
	fakeWorkspace:SetAttribute("StudioFreshSave", true)
	tester = join(11)
	check(#PlayerData.Get(tester).Codes == 0 and store.saved[FRESH] ~= nil and record(11, FRESH) == nil, "StudioFreshSave plays as a new player on a throwaway key")
	leave(tester)
	fakeWorkspace:SetAttribute("StudioFreshSave", nil)
	fakeWorkspace:SetAttribute("StudioUseLiveSaves", true)
	tester = join(14)
	check(record(14) ~= nil and record(14, STUDIO) == nil, "StudioUseLiveSaves (on purpose only) uses the live store")
	leave(tester)
	fakeWorkspace:SetAttribute("StudioUseLiveSaves", nil)
	inStudio = false

	-- Shutdown saves everyone still here and releases their leases.
	local stayer = join(12)
	table.insert(PlayerData.Edit(stayer).Codes, "STAYER")
	closeCallback()
	check(record(12).Codes[1] == "STAYER" and record(12).Session == nil, "BindToClose saves and releases every session")

	return passed
end
