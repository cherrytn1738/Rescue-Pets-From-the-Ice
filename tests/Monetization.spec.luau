--[[
Spec for the Robux purchases: MonetizationConfig and MonetizationRules, and the REAL Receipts,
Gifting, PurchaseRewards, GamePasses and PlayerData modules run against fakes (tests/FakeDataStore.luau,
fake players, a fake MarketplaceService and PaidRandomPolicy). No live save, purchase, player or
Instance is touched.

The game's real config is empty, so this spec fills the shared config with test-only items and
registers a test-only reward kind, "Coins", which adds to a TestCoins field in the save (PlayerData
keeps fields it doesn't know) and is capped at COIN_CAP, so "can't apply now" can be tested.

Covers: the empty real config, config checks, pass ownership, a product grant, an unknown reward
kind, a reward that can't apply now, paid random items in a restricted region, duplicate and retried
receipts, a lost save response, a save outage, a crash after the save but before Roblox heard
"granted", a crash after the grant but before the save, gifting (here, offline, from another
server), and shutdown.

Run: python tools/run_specs.py Monetization
]]
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local realHttp = game:GetService("HttpService")
	local realTypeof = typeof
	local Decision = Enum.ProductPurchaseDecision
	local Granted, NotYet = Decision.PurchaseGranted, Decision.NotProcessedYet
	local FakeDataStore = assert(loadstring(sources.FakeDataStore))()
	local STORE = "IcePets_PlayerData"
	local COIN_CAP = 10_000

	-- Pure modules (shared by every fake server) ---------------------------------------------------
	local modules = {}
	local function loadPure(name)
		local chunk = assert(loadstring(sources[name], name))
		setfenv(chunk, setmetatable({
			game = { GetService = function() return modules end },
			script = { Parent = modules },
			require = function(module)
				return module
			end,
		}, { __index = getfenv(1) }))
		modules[name] = chunk()
		return modules[name]
	end
	for _, name in {
		"MonetizationConfig", "MonetizationRules", "AnalyticsConfig", "AnalyticsRules",
		-- the game configs PlayerData checks saved ids against
		"LayerConfig", "CreatureConfig", "BuildingConfig", "UpgradeConfig",
	} do
		loadPure(name)
	end
	local Config, Rules = modules.MonetizationConfig, modules.MonetizationRules

	-- The real config: only the two pet-slot passes, both without ids yet (none of the old game's items).
	check(#Config.Passes == 2 and #Config.Products == 0, "the game's MonetizationConfig has only the pet-slot passes")
	check(Config.GetPass("ExtraPetSlot").PetSlots == 1 and Config.GetPass("PetSquad").PetSlots == 2, "...Extra Pet Slot adds 1 slot and Pet Squad 2")
	check(Config.GetPass("ExtraPetSlot").ExpectedPrice == 449 and Config.GetPass("PetSquad").ExpectedPrice == 899, "...at the doc's prices")
	check(not Config.IsLive(Config.GetPass("ExtraPetSlot")) and not Config.IsLive(Config.GetPass("PetSquad")), "...and neither has a real id yet")
	check(Config.GetProduct("Anything") == nil and Config.GetPass("Anything") == nil and Config.FindByProductId(1) == nil, "...so nothing else is found")
	local priced, hidden = Config.AllPriced()
	check(#priced == 0 and hidden == 2, "...and PriceCheck has nothing to check (2 hidden)")

	-- Config checks catch mistakes at load.
	local function invalid(config)
		return not pcall(Config.Validate, config)
	end
	local tabs = Config.Shop
	check(invalid({ Shop = tabs, Passes = {}, Products = { { Key = "A", Name = "A", Tab = "Products", Id = 1, GiftId = 0, ExpectedPrice = 5 } } }),
		"a product without a Reward is refused")
	check(invalid({ Shop = tabs, Passes = {}, Products = {
		{ Key = "A", Name = "A", Tab = "Products", Id = 7, GiftId = 0, ExpectedPrice = 5, Reward = { Kind = "Coins" } },
		{ Key = "B", Name = "B", Tab = "Products", Id = 7, GiftId = 0, ExpectedPrice = 5, Reward = { Kind = "Coins" } },
	} }), "the same product id pasted twice is refused")
	check(invalid({ Shop = tabs, Passes = {}, Products = {
		{ Key = "A", Name = "A", Tab = "Nowhere", Id = 0, GiftId = 0, ExpectedPrice = 5, Reward = { Kind = "Coins" } },
	} }), "a product in a tab the shop doesn't have is refused")
	check(invalid({ Shop = tabs, Passes = {}, Products = {
		{ Key = "A", Name = "A", Tab = "Products", Id = 0, GiftId = 0, ExpectedPrice = 5, PaidRandom = true, Reward = { Kind = "Coins" } },
	} }), "a paid random item without its odds is refused")
	check(invalid({ Shop = tabs, Passes = { { Key = "P", Name = "P", Id = 0, ExpectedPrice = 5 }, { Key = "P", Name = "Q", Id = 0, ExpectedPrice = 5 } }, Products = {} }),
		"a repeated key is refused")

	-- Test items (ids given here; the real config has none).
	for index, pass in {
		{ Key = "PassA", Name = "Pass A", Id = 101, ExpectedPrice = 99 },
		{ Key = "PassB", Name = "Pass B", Id = 102, ExpectedPrice = 199 },
	} do
		Config.Passes[index] = pass
	end
	for index, product in {
		{ Key = "Coins100", Name = "100 Coins", Tab = "Products", Id = 1001, GiftId = 2001, ExpectedPrice = 25, Reward = { Kind = "Coins", Amount = 100 } },
		{ Key = "Coins1K", Name = "1,000 Coins", Tab = "Products", Id = 1002, GiftId = 2002, ExpectedPrice = 99, Reward = { Kind = "Coins", Amount = 1000 } },
		{ Key = "Coins5K", Name = "5,000 Coins", Tab = "Products", Id = 1003, GiftId = 2003, ExpectedPrice = 399, Reward = { Kind = "Coins", Amount = 5000 } },
		{ Key = "LuckyBox", Name = "Lucky Box", Tab = "Products", Id = 1004, GiftId = 2004, ExpectedPrice = 49, PaidRandom = true,
			Odds = { { Name = "50 Coins", Chance = 0.5 }, { Name = "Also 50 Coins", Chance = 0.5 } }, Reward = { Kind = "Coins", Amount = 50 } },
		{ Key = "Mystery", Name = "Not built yet", Tab = "Products", Id = 1005, GiftId = 2005, ExpectedPrice = 10, Reward = { Kind = "NotBuiltYet" } },
	} do
		Config.Products[index] = product
	end
	Config.Validate(Config)
	check(true, "the test items pass the config checks")

	-- Rules -------------------------------------------------------------------------------------------
	check(Config.FindByProductId(1001) == "Product", "a product id finds its product")
	local kind, found = Config.FindByProductId(2001)
	check(kind == "Gift" and found.Key == "Coins100", "a gift product id finds the product it gives")
	check(Config.FindByProductId(0) == nil and Config.FindByProductId(999999) == nil, "an unknown or empty id sells nothing")
	check(not Config.IsLive({ Id = 0 }) and Config.IsLive({ Id = 5 }), "an item without a real id isn't live (never shown, never prompted)")
	check(Config.GetPassById(101).Key == "PassA" and Config.GetPassById(999) == nil, "a pass id finds its pass")

	local list = {}
	for index = 1, Rules.MaxReceipts + 5 do
		Rules.RememberReceipt(list, { Id = "r" .. index })
	end
	Rules.RememberReceipt(list, { Id = "r" .. (Rules.MaxReceipts + 5) })
	check(#list == Rules.MaxReceipts and list[1].Id == "r6" and Rules.FindReceipt(list, "r55"), "receipts: the most recent 50 are kept, each once")
	local gifts = {}
	for index = 1, Rules.MaxGifts + 3 do
		Rules.RememberGift(gifts, "g" .. index)
	end
	check(#gifts == Rules.MaxGifts and gifts[1] == "g4", "received gift ids: the most recent 100 are kept")
	check(Rules.GiftStillOnItsWay({ State = "purchased", At = 100 }, 200) and not Rules.GiftStillOnItsWay({ State = "prompted", At = 100 }, 200)
		and not Rules.GiftStillOnItsWay({ State = "purchased", At = 100 }, 100 + Rules.GiftWaitSeconds), "a bought gift blocks the next one until its receipt (or an hour)")
	check(Rules.GiftRequestReady(nil, 10) and not Rules.GiftRequestReady(10, 12) and Rules.GiftRequestReady(10, 10 + Rules.GiftRequestSeconds),
		"one gift prompt every few seconds")
	check(Rules.IsValidReceipt({ PlayerId = 1, PurchaseId = "x" }, 1) and not Rules.IsValidReceipt({ PlayerId = 2, PurchaseId = "x" }, 1)
		and not Rules.IsValidReceipt({ PlayerId = 1, PurchaseId = "" }, 1), "a receipt must be this player's and have a PurchaseId")

	-- Fake servers (the real modules, on one shared fake DataStore and clock) -------------------------
	local now = 1000000
	local store = FakeDataStore.new()
	local guid = 0
	local function record(userId)
		return store.saved[STORE] and store.saved[STORE]["Player_" .. userId]
	end

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

	local function newServer()
		local server = { notices = {}, logs = {}, ownsPass = {}, inStudio = false }
		local spawnEnabled = false
		local fakeTask = {
			wait = function(seconds)
				now += seconds or 0
			end,
			spawn = function(fn, ...)
				if spawnEnabled then
					fn(...)
				end
			end,
		}
		local players = { PlayerAdded = signal(), PlayerRemoving = signal(), list = {} }
		function players:GetPlayers()
			return table.clone(self.list)
		end
		function players:GetPlayerByUserId(id)
			for _, player in self.list do
				if player.UserId == id then
					return player
				end
			end
			return nil
		end
		server.players = players
		local marketplace = {
			PromptGamePassPurchaseFinished = signal(),
			UserOwnsGamePassAsync = function(_, userId, passId)
				if server.lookupFails then
					error("simulated web error")
				end
				return server.ownsPass[userId] ~= nil and server.ownsPass[userId][passId] == true
			end,
		}
		server.marketplace = marketplace
		local replicated = setmetatable({
			PurchaseNotice = {
				FireClient = function(_, player, payload)
					table.insert(server.notices, { player = player, payload = payload })
				end,
			},
			FindFirstChild = function(self, name)
				return rawget(self, name)
			end,
		}, { __index = modules })
		local workspaceAttributes = {}
		local services = {
			Players = players,
			DataStoreService = store.service,
			MarketplaceService = marketplace,
			ReplicatedStorage = replicated,
			RunService = {
				IsStudio = function()
					return server.inStudio
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
		}
		local serverModules = {}
		local function log(...)
			local parts = {}
			for _, part in { ... } do
				table.insert(parts, tostring(part))
			end
			table.insert(server.logs, table.concat(parts, " "))
		end
		local env = setmetatable({
			game = {
				GetService = function(_, name)
					return assert(services[name], "unexpected service " .. name)
				end,
				BindToClose = function(_, fn)
					server.close = fn
				end,
				PlaceId = 0,
			},
			workspace = {
				GetAttribute = function(_, name)
					return workspaceAttributes[name]
				end,
				SetAttribute = function(_, name, value)
					workspaceAttributes[name] = value
				end,
				GetServerTimeNow = function()
					return now
				end,
			},
			task = fakeTask,
			os = {
				clock = function()
					return now
				end,
				time = function()
					return math.floor(now)
				end,
			},
			script = { Parent = serverModules },
			require = function(module)
				return module
			end,
			print = log,
			warn = log,
			typeof = function(value)
				return if type(value) == "table" and value.IsFakePlayer then "Instance" else realTypeof(value)
			end,
		}, { __index = getfenv(1) })
		local function load(name)
			local chunk = assert(loadstring(sources[name], name))
			setfenv(chunk, env)
			serverModules[name] = chunk()
			return serverModules[name]
		end

		local PlayerData = load("PlayerData")
		server.PlayerData = PlayerData
		server.GamePasses = load("GamePasses")
		-- Roblox's paid random item policy per player: server.restricted[userId] = true restricts one.
		server.restricted = {}
		serverModules.PaidRandomPolicy = {
			REFUSED = "Random items bought with Robux aren't available in your region.",
			IsAllowed = function(player)
				return not server.restricted[player.UserId]
			end,
			WaitForAnswer = function(player)
				return not server.restricted[player.UserId]
			end,
		}
		server.PurchaseRewards = load("PurchaseRewards")
		-- The test-only reward kind: coins in the save, capped.
		server.PurchaseRewards.Kinds.Coins = {
			CanGive = function(player, reward)
				local data = PlayerData.Edit(player)
				if (data.TestCoins or 0) + reward.Amount > COIN_CAP then
					return false, "Your coin jar is full."
				end
				return true
			end,
			Give = function(player, reward)
				local data = PlayerData.Edit(player)
				data.TestCoins = (data.TestCoins or 0) + reward.Amount
				return `{reward.Amount} coins`
			end,
		}
		server.Gifting = load("Gifting")
		server.Receipts = load("Receipts")
		server.GamePasses.Start()
		server.Receipts.Start()
		PlayerData.Start()
		spawnEnabled = true

		function server.join(userId, name)
			local attributes = {}
			local player = { UserId = userId, Name = name, DisplayName = name, Parent = players, IsFakePlayer = true }
			function player:GetAttribute(attribute)
				return attributes[attribute]
			end
			function player:SetAttribute(attribute, value)
				attributes[attribute] = value
			end
			function player:Kick(reason)
				self.KickReason = reason
			end
			function player:IsA(className)
				return className == "Player"
			end
			table.insert(players.list, player)
			players.PlayerAdded:Fire(player)
			return player
		end
		function server.leave(player)
			players.PlayerRemoving:Fire(player)
			table.remove(players.list, table.find(players.list, player))
			player.Parent = nil
		end
		-- The server dies: nothing more runs and nothing more is saved. Its leases stay in the
		-- records until they run out.
		function server.crash()
			spawnEnabled = false
			players.list = {}
		end
		-- Roblox calls the ProcessReceipt handler.
		function server.receipt(player, productKey: string, purchaseId: string, gift: boolean?)
			local product = Config.GetProduct(productKey)
			return marketplace.ProcessReceipt({
				PlayerId = player.UserId, PurchaseId = purchaseId,
				ProductId = if gift then product.GiftId else product.Id,
				CurrencySpent = product.ExpectedPrice, CurrencyType = Enum.CurrencyType.Robux,
			})
		end
		function server.lastNotice(player)
			for index = #server.notices, 1, -1 do
				if server.notices[index].player == player then
					return server.notices[index].payload
				end
			end
			return nil
		end
		function server.coins(player)
			local data = server.PlayerData.Get(player)
			return data and (data.TestCoins or 0)
		end
		return server
	end

	-- Passes ----------------------------------------------------------------------------------------
	local A = newServer()
	A.ownsPass[1] = { [101] = true }
	local changes = {}
	A.GamePasses.OnChanged(function(player, passKey, owns)
		table.insert(changes, { player = player, key = passKey, owns = owns })
	end)
	local buyer = A.join(1, "Buyer")
	check(A.GamePasses.IsLookedUp(buyer), "a joining player's passes are looked up")
	check(A.GamePasses.Owns(buyer, "PassA") and buyer:GetAttribute("Owns_PassA") == true, "a pass the player owns is found at join (and shown)")
	check(not A.GamePasses.Owns(buyer, "PassB") and buyer:GetAttribute("Owns_PassB") == false, "...and a pass they don't own isn't")
	A.marketplace.PromptGamePassPurchaseFinished:Fire(buyer, 102, true)
	check(A.GamePasses.Owns(buyer, "PassB") and buyer:GetAttribute("Owns_PassB") == true, "a pass bought in the game counts at once, without a rejoin")
	check(changes[#changes].key == "PassB" and changes[#changes].owns == true, "...and the systems showing it are told")
	check(A.lastNotice(buyer).Kind == "PassOwned" and A.lastNotice(buyer).Item == "Pass B", "...and the buyer sees a notice")
	local cancelled = A.join(4, "Cancelled")
	A.marketplace.PromptGamePassPurchaseFinished:Fire(cancelled, 101, false)
	check(not A.GamePasses.Owns(cancelled, "PassA"), "a cancelled pass prompt gives nothing")
	A.marketplace.PromptGamePassPurchaseFinished:Fire(cancelled, 99999, true)
	check(not A.GamePasses.Owns(cancelled, "PassA") and not A.GamePasses.Owns(cancelled, "PassB"), "an unknown pass id gives nothing")
	check(not A.GamePasses.Owns({ Name = "Not a player" }, "PassA"), "anything that isn't a real player owns nothing")
	A.lookupFails = true
	local unlucky = A.join(5, "Unlucky")
	check(not A.GamePasses.Owns(unlucky, "PassA"), "a failed ownership lookup grants nothing this session")
	A.lookupFails = false
	check(not A.GamePasses.SetStudioOverride(unlucky, "PassA", true) and not A.GamePasses.Owns(unlucky, "PassA"), "the Studio pass switch does nothing in a live server")
	A.inStudio = true
	check(A.GamePasses.SetStudioOverride(unlucky, "PassA", true) and A.GamePasses.Owns(unlucky, "PassA"), "in Studio the debug menu can give a pass for the session")
	check(not A.GamePasses.SetStudioOverride(unlucky, "NoSuchPass", true), "...but only a pass the config has")
	A.GamePasses.SetStudioOverride(buyer, "PassA", false)
	check(not A.GamePasses.Owns(buyer, "PassA"), "...or take one away, even one Roblox says is owned")
	A.GamePasses.SetStudioOverride(buyer, "PassA", nil)
	check(A.GamePasses.Owns(buyer, "PassA"), "...and nil goes back to what Roblox says")
	A.inStudio = false
	check(record(1).Owns_PassA == nil and record(1).Passes == nil, "pass ownership is never saved")

	-- Products ----------------------------------------------------------------------------------------
	check(A.receipt(buyer, "Coins100", "coins-1") == Granted, "a product's receipt is granted")
	check(A.coins(buyer) == 100, "...and gives exactly its reward")
	check(record(1).TestCoins == 100 and Rules.FindReceipt(record(1).Receipts, "coins-1") ~= nil, "...saved with its receipt before Roblox hears granted")
	check(A.lastNotice(buyer).Kind == "Purchased" and A.lastNotice(buyer).Other == "100 coins", "...and the buyer sees what they got")
	check(A.receipt(buyer, "Coins100", "coins-1") == Granted and A.coins(buyer) == 100, "a duplicate receipt (same PurchaseId) gives nothing, and is acknowledged")
	check(#record(1).Receipts == 1, "...and isn't recorded twice")

	-- A reward kind the game hasn't built yet: never taken for nothing.
	local unknownOk, unknownProblem = A.PurchaseRewards.CanGive(buyer, Config.GetProduct("Mystery"))
	check(not unknownOk and unknownProblem == A.PurchaseRewards.UNKNOWN_KIND, "a product whose reward kind isn't registered can't be given (refused before the prompt)")
	check(A.receipt(buyer, "Mystery", "mystery-1") == NotYet and not Rules.FindReceipt(A.PlayerData.Get(buyer).Receipts, "mystery-1"),
		"...and its receipt is left unresolved, not marked granted")
	check(A.PurchaseRewards.CanGive(buyer, { Key = "Code_X", Name = "x", Reward = { Kind = "Coins", Amount = 1 } }),
		"a promo code's reward (a product-shaped table) goes through the same kinds")

	check(A.marketplace.ProcessReceipt({ PlayerId = 999, PurchaseId = "nobody-1", ProductId = 1001 }) == NotYet,
		"a receipt for a player who isn't in this server is left for Roblox to retry when they join")
	check(A.marketplace.ProcessReceipt({ PlayerId = 1, PurchaseId = "unknown-1", ProductId = 424242 }) == NotYet,
		"a receipt for a product the config doesn't know is left unresolved")

	-- Can't apply now: the reward refuses, and the retry later grants it.
	local full = A.join(2, "Full")
	A.PlayerData.Edit(full).TestCoins = COIN_CAP - 50
	local canBuy, fullProblem = A.PurchaseRewards.CanGive(full, Config.GetProduct("Coins100"))
	check(not canBuy and fullProblem == "Your coin jar is full.", "a reward that can't apply now: the player is told before the prompt opens")
	check(A.receipt(full, "Coins100", "full-1") == NotYet, "...and a receipt that arrives anyway is refused, not marked granted")
	check(A.coins(full) == COIN_CAP - 50 and not Rules.FindReceipt(A.PlayerData.Get(full).Receipts, "full-1"), "...nothing was given or recorded")
	A.PlayerData.Edit(full).TestCoins = 0
	check(A.receipt(full, "Coins100", "full-1") == Granted and A.coins(full) == 100, "once it can apply, Roblox's retry grants it")

	-- Paid random items in a region that restricts them ------------------------------------------------
	A.restricted[7] = true
	local blocked = A.join(7, "Blocked")
	local boxOk, boxProblem = A.PurchaseRewards.CanGive(blocked, Config.GetProduct("LuckyBox"))
	check(not boxOk and string.find(boxProblem, "region", 1, true), "paid random items restricted: one is refused before the prompt")
	check(A.PurchaseRewards.CanGive(blocked, Config.GetProduct("Coins100")), "...but an item that isn't random is fine")
	check(A.receipt(blocked, "LuckyBox", "blocked-1") == NotYet and A.coins(blocked) == 0
		and not Rules.FindReceipt(A.PlayerData.Get(blocked).Receipts, "blocked-1"), "a paid random receipt for a restricted player is refused, nothing given or recorded")
	check(A.receipt(blocked, "Coins100", "blocked-2") == Granted, "...while their other purchase is granted as usual")
	local giftOk, giftProblem = A.Gifting.Prepare(buyer, Config.GetProduct("LuckyBox"), blocked)
	check(not giftOk and string.find(giftProblem, "their region", 1, true), "a paid random item can't be gifted to a restricted player")
	check(not A.Gifting.Prepare(blocked, Config.GetProduct("LuckyBox"), buyer), "...and a restricted player can't buy one as a gift")
	A.restricted[7] = nil
	check(A.receipt(blocked, "LuckyBox", "blocked-1") == Granted and A.coins(blocked) == 150, "once allowed, Roblox's retry of the receipt grants it")

	-- Save trouble -----------------------------------------------------------------------------------
	store.loseResponse.Player_1 = true
	local coinsBefore = A.coins(buyer)
	check(A.receipt(buyer, "Coins1K", "lost-1") == Granted, "a save whose response was lost still confirms (LastWriteId)...")
	check(record(1).TestCoins == coinsBefore + 1000 and A.coins(buyer) == coinsBefore + 1000, "...and the reward was given once")
	store.outage.Player_1 = true
	coinsBefore = A.coins(buyer)
	check(A.receipt(buyer, "Coins1K", "outage-1") == NotYet, "a receipt whose save fails isn't acknowledged")
	check(A.coins(buyer) == coinsBefore + 1000 and record(1).TestCoins == coinsBefore
		and Rules.FindReceipt(A.PlayerData.Get(buyer).Receipts, "outage-1") ~= nil, "...the grant and its receipt wait in the session, together, for the next save")
	store.outage.Player_1 = nil
	check(A.receipt(buyer, "Coins1K", "outage-1") == Granted, "Roblox's retry after the outage is granted...")
	check(A.coins(buyer) == coinsBefore + 1000 and record(1).TestCoins == coinsBefore + 1000, "...without giving the reward twice")

	-- Crashes ------------------------------------------------------------------------------------------
	-- After the save, before Roblox heard "granted": the next server finds the saved receipt.
	A.receipt(buyer, "Coins5K", "crash-after")
	local savedCoins = record(1).TestCoins
	A.crash()
	now += 200 -- the dead server's lease runs out
	local B = newServer()
	local buyerB = B.join(1, "Buyer")
	check(B.coins(buyerB) == savedCoins, "after a crash the next server loads the saved grant")
	check(B.receipt(buyerB, "Coins5K", "crash-after") == Granted and B.coins(buyerB) == savedCoins,
		"Roblox's retry (saved, but the crash came before 'granted') finds the receipt and gives nothing more")
	-- After the grant, before the save: nothing was saved, so the retry in the next server grants it.
	store.outage.Player_1 = true
	check(B.receipt(buyerB, "Coins100", "crash-before") == NotYet and B.coins(buyerB) == savedCoins + 100, "(granted in memory, but its save failed)")
	B.crash()
	store.outage.Player_1 = nil
	now += 200
	local C = newServer()
	local buyerC = C.join(1, "Buyer")
	check(C.coins(buyerC) == savedCoins, "the grant the crashed server never saved isn't there")
	check(C.receipt(buyerC, "Coins100", "crash-before") == Granted and C.coins(buyerC) == savedCoins + 100, "...so Roblox's retry grants it, once")
	check(C.receipt(buyerC, "Coins100", "crash-before") == Granted and C.coins(buyerC) == savedCoins + 100, "...and a further retry gives nothing")
	-- Rejoin: a receipt retried at the next join, in the same server.
	C.leave(buyerC)
	buyerC = C.join(1, "Buyer")
	check(C.receipt(buyerC, "Coins100", "crash-before") == Granted and C.coins(buyerC) == savedCoins + 100, "a receipt retried after a rejoin gives nothing more")

	-- Gifting ------------------------------------------------------------------------------------------
	local giver = C.join(10, "Giver")
	local friend = C.join(11, "Friend")
	local coins100 = Config.GetProduct("Coins100")
	local started, startProblem = C.Gifting.Prepare(giver, coins100, giver)
	check(not started and startProblem, "a gift can't be sent to yourself")
	local writeKey = STORE .. "/Player_10"
	local writesBefore = store.calls[writeKey] or 0
	check(C.Gifting.Prepare(giver, coins100, friend) == true, "a gift for another player in the server can start")
	local intent = C.PlayerData.Get(giver).PendingGifts.Coins100
	check(intent and intent.Recipient == 11 and intent.Key == "Player_11" and intent.Store == STORE and intent.State == "prompted",
		"...the recipient (and where their record is) is noted in the buyer's data before the prompt opens")
	check((store.calls[writeKey] or 0) == writesBefore and record(10).PendingGifts.Coins100 == nil,
		"...without a save: asking for a gift prompt costs no DataStore write")
	C.Gifting.PromptFinished(giver, coins100, true)
	check(record(10).PendingGifts.Coins100 and record(10).PendingGifts.Coins100.State == "purchased" and record(10).PendingGifts.Coins100.Recipient == 11,
		"a bought gift's recipient is saved at once (a receipt that only arrives after a rejoin still finds it)")
	check(C.receipt(giver, "Coins100", "gift-1", true) == Granted, "the gift product's receipt is granted")
	local giftReceipt = Rules.FindReceipt(record(10).Receipts, "gift-1")
	check(giftReceipt and giftReceipt.For == 11 and giftReceipt.Product == "Coins100", "...the buyer's saved receipt records who it was for")
	check(record(10).PendingGifts.Coins100 == nil, "...and the intent is cleared")
	check(C.coins(friend) == 100, "the recipient gets it at once (they're here)")
	check(C.coins(giver) == 0, "...the buyer doesn't get it")
	check(table.find(record(11).ReceivedGifts, "gift-1") and #record(11).GiftInbox == 0, "...it is saved as received and leaves their inbox")
	local received = C.lastNotice(friend)
	check(received.Kind == "GiftReceived" and received.Other == "Giver" and received.Item == "100 Coins", "the recipient's notice names the buyer")
	check(C.lastNotice(giver).Kind == "GiftSent" and C.lastNotice(giver).Other == "Friend", "the buyer is told it's on its way")
	check(C.receipt(giver, "Coins100", "gift-1", true) == Granted and C.coins(friend) == 100, "a duplicate gift receipt gives nothing more")
	C.Gifting.Apply(friend, { { Id = "gift-1", Product = "Coins100", From = 10, FromName = "Giver" } })
	check(C.coins(friend) == 100, "a gift that arrives again is given only once")
	C.PlayerData.Edit(friend).TestCoins = COIN_CAP
	local fullGift, fullGiftProblem = C.Gifting.Prepare(giver, coins100, friend)
	check(not fullGift and string.find(fullGiftProblem, "coin jar is full", 1, true), "a gift that can't apply to the recipient now is refused before the prompt")
	C.PlayerData.Edit(friend).TestCoins = 100
	check(C.receipt(giver, "Coins1K", "gift-nobody", true) == NotYet, "a gift receipt with no saved recipient is left for a retry")
	local coins1k = Config.GetProduct("Coins1K")
	local writesBeforeCancel = store.calls[writeKey] or 0
	C.Gifting.Prepare(giver, coins1k, friend)
	C.Gifting.PromptFinished(giver, coins1k, false)
	check(record(10).PendingGifts.Coins1K == nil and C.PlayerData.Get(giver).PendingGifts.Coins1K == nil, "a cancelled gift prompt drops the intent")
	check((store.calls[writeKey] or 0) == writesBeforeCancel, "...and asking then cancelling saved nothing at all")
	for _ = 1, 20 do
		C.Gifting.Prepare(giver, coins1k, friend)
		C.Gifting.PromptFinished(giver, coins1k, false)
	end
	check((store.calls[writeKey] or 0) == writesBeforeCancel, "asking and cancelling 20 times in a row costs no DataStore writes")
	C.Gifting.Prepare(giver, coins1k, friend)
	C.Gifting.PromptFinished(giver, coins1k, true)
	local again, againProblem = C.Gifting.Prepare(giver, coins1k, friend)
	check(not again and string.find(againProblem, "on its way", 1, true), "a bought gift blocks the same gift until its receipt arrives")
	check(C.receipt(giver, "Coins1K", "gift-2", true) == Granted and C.coins(friend) == 1100, "a gift adds the exact reward to the recipient")

	-- Gifts for a player who left: queued in their save, given at their next join (another server).
	local away = C.join(12, "Away")
	check(C.Gifting.Prepare(giver, coins1k, away) == true, "(a gift for a player who is about to leave)")
	C.Gifting.PromptFinished(giver, coins1k, true)
	C.leave(away)
	check(C.receipt(giver, "Coins1K", "gift-away", true) == Granted, "a gift for a player who left in the meantime is still granted...")
	check(record(12).GiftInbox[1] and record(12).GiftInbox[1].Id == "gift-away" and record(12).TestCoins == nil, "...queued in their saved inbox, not given yet")
	local D = newServer()
	local awayD = D.join(12, "Away")
	check(D.coins(awayD) == 1000, "...and given when they next join, in another server")
	check(#record(12).GiftInbox == 0 and table.find(record(12).ReceivedGifts, "gift-away"), "...once: saved as received, gone from the inbox")
	check(D.lastNotice(awayD).Kind == "GiftReceived" and D.lastNotice(awayD).Other == "Giver", "...with a notice naming the buyer")

	-- A gift another server queues while the recipient plays here: the recipient's own save keeps
	-- it (never overwrites the inbox) and gives it.
	C.PlayerData.UpdateRecord(STORE, "Player_12", function(saved)
		saved.GiftInbox = saved.GiftInbox or {}
		table.insert(saved.GiftInbox, { Id = "gift-remote", Product = "Coins100", From = 10, FromName = "Giver" })
		return saved
	end)
	check(record(12).GiftInbox[1].Id == "gift-remote", "(another server queues a gift into a player's record)")
	D.PlayerData.SaveNow(awayD)
	check(D.coins(awayD) == 1100, "the recipient's next save finds it and gives it")
	D.PlayerData.SaveNow(awayD)
	check(#record(12).GiftInbox == 0 and table.find(record(12).ReceivedGifts, "gift-remote") and D.coins(awayD) == 1100, "...once, and it leaves the inbox")
	-- A gift that can't be given yet waits in the inbox until it can.
	D.PlayerData.Edit(awayD).TestCoins = COIN_CAP
	C.PlayerData.UpdateRecord(STORE, "Player_12", function(saved)
		table.insert(saved.GiftInbox, { Id = "gift-wait", Product = "Coins100", From = 10, FromName = "Giver" })
		return saved
	end)
	D.PlayerData.SaveNow(awayD)
	check(D.coins(awayD) == COIN_CAP and record(12).GiftInbox[1].Id == "gift-wait", "a gift that can't apply yet waits in the inbox")
	D.PlayerData.Edit(awayD).TestCoins = 0
	D.PlayerData.SaveNow(awayD)
	check(D.coins(awayD) == 100, "...and is given once it can (the next save finds it again)")
	D.PlayerData.SaveNow(awayD)
	check(#record(12).GiftInbox == 0 and D.coins(awayD) == 100, "...once")
	-- A gift of a product the game no longer sells is dropped from the inbox, never given.
	C.PlayerData.UpdateRecord(STORE, "Player_12", function(saved)
		table.insert(saved.GiftInbox, { Id = "gift-gone", Product = "NoLongerSold", From = 10, FromName = "Giver" })
		return saved
	end)
	D.PlayerData.SaveNow(awayD)
	check(#record(12).GiftInbox == 0 and D.coins(awayD) == 100, "a queued gift for a product that no longer exists is dropped")

	-- Shutdown -------------------------------------------------------------------------------------
	local coinsAtClose = C.coins(friend)
	C.close()
	check(record(11).Session == nil and record(11).TestCoins == coinsAtClose, "shutdown saves and releases everyone")
	check(C.receipt(friend, "Coins100", "during-close") == NotYet, "a receipt during shutdown is left for the next server")
	check(record(11).TestCoins == coinsAtClose, "...and gives nothing here")

	-- A gift whose buyer's server crashes after queuing it but before saving the buyer's receipt:
	-- the recipient gets it once, and Roblox's retry in the next server finds it already given.
	local E = newServer()
	local giverE, friendE = E.join(10, "Giver"), E.join(11, "Friend")
	check(E.Gifting.Prepare(giverE, coins100, friendE) == true, "(a gift starts)")
	E.Gifting.PromptFinished(giverE, coins100, true)
	store.outage.Player_10 = true
	check(E.receipt(giverE, "Coins100", "gift-crash", true) == NotYet, "(queued for the recipient, but the buyer's save fails)")
	E.crash()
	store.outage.Player_10 = nil
	now += 200
	local F = newServer()
	local friendCoinsBefore = record(11).TestCoins
	local friendF = F.join(11, "Friend")
	check(F.coins(friendF) == friendCoinsBefore + 100 or F.coins(friendF) == friendCoinsBefore,
		"(the recipient's record holds the gift, given here or already given)")
	local giverF = F.join(10, "Giver")
	check(F.receipt(giverF, "Coins100", "gift-crash", true) == Granted, "Roblox's retry for the buyer is granted...")
	F.PlayerData.SaveNow(friendF)
	check(F.coins(friendF) == friendCoinsBefore + 100 and #record(11).GiftInbox == 0, "...and the recipient has the gift exactly once")
	check(Rules.FindReceipt(record(10).Receipts, "gift-crash").For == 11, "...and the buyer's receipt records who it was for")

	return passed
end
