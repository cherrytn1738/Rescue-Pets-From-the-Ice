--[[
Spec for the analytics helpers: src/replicated/AnalyticsConfig.luau, src/replicated/AnalyticsRules.luau
and the REAL src/server/Analytics.luau, run against fakes (a fake AnalyticsService that records every
event, fake players, PlayerData and the ShopVisit remote). Nothing is sent to Roblox. The shipped
onboarding funnel is empty, so the module is also run with a test funnel and a test shop catalogue.
(Saving the progress: tests/PlayerData.spec.luau.)
Run: python tools/run_specs.py Analytics
]]
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local Config = assert(loadstring(sources.AnalyticsConfig))()
	local Rules = assert(loadstring(sources.AnalyticsRules))()

	-- The shipped definitions ---------------------------------------------------------------------------
	check(type(Config.Onboarding) == "table" and #Config.Onboarding == 7 and Config.Onboarding[1].Key == "Joined" and Config.Onboarding[7].Key == "FirstRebirth",
		"the onboarding funnel has the doc's seven steps, Joined first and First rebirth last")
	local function shortStableName(name)
		return type(name) == "string" and #name > 0 and #name <= 24 and string.match(name, "^[%w ]+$") ~= nil
	end
	check(Config.Shops.Robux.Funnel == "RobuxShop" and #Config.Shops.Robux.Steps == 4, "the Robux shop funnel has 4 steps")
	for _, shop in Config.Shops do
		for _, name in shop.Steps do
			check(shortStableName(name), `shop step "{name}" is short`)
		end
	end
	check(Config.VisitRate.MinSeconds > 0 and Config.VisitRate.PerMinute > 0, "the ShopVisit remote is rate-limited")

	-- A test funnel (what a game's onboarding could look like) ------------------------------------------
	local testOnboarding = {
		{ Key = "Joined", Name = "Joined" },
		{ Key = "StepTwo", Name = "Step two" },
		{ Key = "StepThree", Name = "Step three" },
		{ Key = "StepFour", Name = "Step four" },
		{ Key = "StepFive", Name = "Step five" },
	}
	local STEPS = #testOnboarding

	-- Onboarding: once each, in order -----------------------------------------------------------------
	local state = Rules.New()
	check(state.Onboarding == 0 and #state.Waiting == 0 and state.Rebirths == nil, "a new player: nothing logged, no Rebirths field")
	local function reach(step)
		return table.concat(Rules.Reach(state, step, STEPS), ",")
	end
	check(reach(1) == "1" and reach(2) == "2", "steps 1 and 2")
	check(reach(1) == "" and reach(2) == "", "a step already logged is never logged again")
	check(reach(5) == "" and state.Onboarding == 2 and state.Waiting[1] == 5, "a step reached early waits")
	check(reach(5) == "", "...and isn't queued twice")
	check(reach(3) == "3", "step 3")
	check(reach(4) == "4,5", "step 4, then the waiting step 5, in order")
	check(reach(5) == "" and reach(6) == "" and reach(0) == "" and #state.Waiting == 0, "nothing after the last step, no unknown steps")
	check(Rules.Reached(state, 5) and not Rules.Reached(Rules.New(), 1), "Reached")
	check(#Rules.Reach(Rules.New(), 1, 0) == 0, "with an empty funnel nothing is ever logged")

	-- Saved values ------------------------------------------------------------------------------------
	local cleaned = Rules.Clean({ Onboarding = 2, Waiting = { 5, 1, 4, 4, "x", 2.5 } }, STEPS)
	check(cleaned.Onboarding == 2 and table.concat(cleaned.Waiting, ",") == "4,5", "Clean keeps later, known, unrepeated waiting steps, sorted")
	for _, junk in { "x", 5, true } do
		check(Rules.Clean(junk, STEPS).Onboarding == STEPS, `{tostring(junk)} counts as done`)
	end
	check(Rules.Clean({ Onboarding = 40 }, STEPS).Onboarding == STEPS, "an out-of-range step counts as done")
	check(Rules.Clean({ Onboarding = 0, Waiting = {} }, 0).Onboarding == 0 and Rules.IsClean(Rules.New(), 0), "with an empty funnel a new player's value is clean")
	check(Rules.IsClean(cleaned, STEPS) and not Rules.IsClean({ Onboarding = 2, Waiting = { 1 } }, STEPS), "IsClean")
	check(not Rules.IsClean(nil, STEPS) and not Rules.IsClean({ Onboarding = 1 }, STEPS), "IsClean: not a table, or no Waiting list")

	-- Saved progression counts (the progression funnels) ----------------------------------------------
	local P = { Layers = 6, Ranks = 4 }
	local old = Rules.Clean({ Onboarding = 1, Waiting = {} }, STEPS, P)
	check(old.Layers == 0 and old.Ranks == 0 and old.ProgressId == nil, "a save from before the progression funnels starts them at 0")
	local bad = Rules.Clean({ Onboarding = 1, Waiting = {}, Layers = 9, Ranks = "x", ProgressId = 5 }, STEPS, P)
	check(bad.Layers == 6 and bad.Ranks == 4 and bad.ProgressId == nil, "unreadable progression counts count as done; a bad session id is dropped")
	local kept = Rules.Clean({ Onboarding = 1, Waiting = {}, Layers = 2, Ranks = 1, ProgressId = "abc" }, STEPS, P)
	check(kept.Layers == 2 and kept.Ranks == 1 and kept.ProgressId == "abc", "good progression counts and the session id are kept")
	check(Rules.Clean({ Onboarding = 1, Waiting = {}, ProgressId = string.rep("a", 65) }, STEPS, P).ProgressId == nil, "an overlong session id is dropped")
	check(Rules.Clean("junk", STEPS, P).Layers == 6, "a Funnels that isn't a table counts every progression step as done too")
	check(Rules.IsClean(kept, STEPS, P) and Rules.IsClean(Rules.New(), STEPS, P), "IsClean with progression counts")
	check(not Rules.IsClean({ Onboarding = 1, Waiting = {}, Layers = 7, Ranks = 0 }, STEPS, P)
		and not Rules.IsClean({ Onboarding = 1, Waiting = {}, Layers = 1, Ranks = 0, ProgressId = 5 }, STEPS, P)
		and not Rules.IsClean({ Onboarding = 1, Waiting = {} }, STEPS, P), "IsClean refuses bad or missing progression counts and a bad session id")

	-- Progression steps -------------------------------------------------------------------------------
	local steps, logged = Rules.ProgressSteps(0, 3, 6)
	check(table.concat(steps, ",") == "1,2,3" and logged == 3, "reaching step 3 first logs 1, 2 and 3")
	steps, logged = Rules.ProgressSteps(3, 2, 6)
	check(#steps == 0 and logged == 3, "a lower step (a rebirth resets the level) logs nothing")
	steps, logged = Rules.ProgressSteps(3, 9, 6)
	check(table.concat(steps, ",") == "4,5,6" and logged == 6, "never past the last step")
	check(#Rules.ProgressSteps(0, 0 / 0, 6) == 0 and #Rules.ProgressSteps(0, "3", 6) == 0, "an unreadable step logs nothing")
	local ranks = { 1, 3, 6, 10 }
	check(Rules.RankStep(0, ranks) == 0 and Rules.RankStep(1, ranks) == 1 and Rules.RankStep(2, ranks) == 1 and Rules.RankStep(5, ranks) == 2
		and Rules.RankStep(10, ranks) == 4 and Rules.RankStep(99, ranks) == 4 and Rules.RankStep(nil, ranks) == 0, "RankStep: the rank step a rebirth count reaches")

	-- Rush shares -------------------------------------------------------------------------------------
	check(#Rules.RushShares({}) == 0, "no rush: no share")
	local one = Rules.RushShares({ { Source = "GoldenGlacier", Multiplier = 2 } })
	check(#one == 1 and one[1].Source == "GoldenGlacier" and math.abs(one[1].Share - 0.5) < 1e-9, "a x2 rush made half of a grant")
	local two = Rules.RushShares({ { Source = "GoldenGlacier", Multiplier = 2 }, { Source = "ServerFrostRush", Multiplier = 2 } })
	check(#two == 2 and math.abs(two[1].Share - 0.375) < 1e-9 and math.abs(two[2].Share - 0.375) < 1e-9, "two x2 rushes (x4): 3/4 of the grant, split evenly")
	local mixed = Rules.RushShares({ { Source = "GoldenGlacier", Multiplier = 5 }, { Source = "ServerFrostRush", Multiplier = 2 } })
	check(math.abs(mixed[1].Share + mixed[2].Share - 0.9) < 1e-9 and mixed[1].Share > mixed[2].Share, "x5 and x2 (x10): 90% of the grant, the bigger rush the bigger share")

	-- The shipped progression, economy and custom definitions -----------------------------------------
	local LayerConfig = assert(loadstring(sources.LayerConfig))()
	local RebirthConfig = assert(loadstring(sources.RebirthConfig))()
	check(#Config.Progression.Layers.Steps == #LayerConfig.Layers, "one layer step per layer")
	for number, layer in LayerConfig.Layers do
		check(Config.Progression.Layers.Steps[number] == `Layer {number} {layer.Name}`, `layer step {number} names layer {number}`)
	end
	check(#Config.Progression.Ranks.Steps == #Config.Progression.Ranks.Rebirths, "one rank step per rank")
	for index, rebirths in Config.Progression.Ranks.Rebirths do
		local rank = RebirthConfig.RankFor(rebirths)
		check(rank and rank.Rank == rebirths and Config.Progression.Ranks.Steps[index] == `Rank {rebirths} {rank.Title}`, `rank step {index} is rank {rebirths}`)
	end
	check(Config.Progression.Ranks.Rebirths[1] == 1, "the first rank step is the first rebirth")
	for _, funnel in Config.Progression do
		for _, name in funnel.Steps do
			check(shortStableName(name), `progression step "{name}" is short`)
		end
	end
	check(Config.Progression.Layers.Funnel ~= Config.Progression.Ranks.Funnel and Config.Progression.Layers.Funnel ~= Config.Shops.Robux.Funnel, "every funnel has its own name")
	check(Config.Economy.Currency == "Crystals" and Config.Economy.FlushSeconds >= 60, "one currency, sent at most every minute per player")
	local sourceCount = 0
	for key, source in Config.Economy.Sources do
		sourceCount += 1
		check(type(source.TransactionType) == "string" and #source.TransactionType > 0, `crystal source {key} has a transaction type`)
	end
	check(sourceCount == 10, "ten crystal sources (taps, Auto Pick, buildings, rescues, the two rushes, daily chest, offline, codes, bundles)")
	check(Config.Economy.Sinks.Building.Batched and not Config.Economy.Sinks.Upgrade.Batched, "building purchases are batched, upgrades sent at once")
	for _, name in Config.Custom do
		check(type(name) == "string" and #name <= 32, `custom event {name}`)
	end

	-- Shop visits -------------------------------------------------------------------------------------
	local visit, first = Rules.NewVisit("abc")
	check(visit.Id == "abc" and table.concat(first, ",") == "1", "a visit logs Opened shop at once")
	check(table.concat(Rules.VisitStep(visit, 3, 4), ",") == "2,3", "a prompt straight from a buy button fills in Viewed item")
	check(#Rules.VisitStep(visit, 2, 4) == 0 and #Rules.VisitStep(visit, 3, 4) == 0, "each visit step once")
	check(#Rules.VisitStep(visit, 5, 4) == 0 and #Rules.VisitStep(nil, 2, 4) == 0, "no unknown steps, no visit")

	-- The real Analytics module, with fakes ------------------------------------------------------------
	-- The config, with the test funnel in place of the empty one.
	local configChunk = assert(loadstring(sources.AnalyticsConfig))
	local TestConfig = configChunk()
	TestConfig.Onboarding = testOnboarding
	TestConfig.OnboardingStep = {}
	for number, step in testOnboarding do
		TestConfig.OnboardingStep[step.Key] = number
	end
	-- A test catalogue: one product and one pass (the shipped one is empty).
	local fakeMonetization = {
		GetProduct = function(key) return if key == "TestPack" then { Key = key } else nil end,
		GetPass = function(key) return if key == "TestPass" then { Key = key } else nil end,
	}

	local events = {} -- every event the fake AnalyticsService got, as text
	local fakeAnalytics = {}
	function fakeAnalytics:LogOnboardingFunnelStepEvent(player, step, name)
		table.insert(events, `{player.Name} onboarding {step} {name}`)
	end
	function fakeAnalytics:LogFunnelStepEvent(player, funnel, sessionId, step, name)
		table.insert(events, `{player.Name} {funnel} {sessionId or "-"} {step} {name}`)
	end
	function fakeAnalytics:LogEconomyEvent(player, flowType, currency, amount, balance, transactionType, sku)
		table.insert(events, `{player.Name} economy {flowType.Name} {currency} {amount} {balance} {transactionType} {sku}`)
	end
	function fakeAnalytics:LogCustomEvent(player, name, value, fields)
		table.insert(events, `{player.Name} custom {name} {value} {fields and fields.CustomField01 or "-"}`)
	end
	local function listeners()
		local list = {}
		return list, {
			Connect = function(_, fn)
				table.insert(list, fn)
			end,
		}
	end
	local fakePlayers = { PlayerRemoving = select(2, listeners()) }
	local function newPlayer(name)
		local attributes = {}
		return { Name = name, __fakePlayer = true, Parent = fakePlayers, Attributes = attributes, IsA = function(_, class)
			return class == "Player"
		end, GetAttribute = function(_, key)
			return attributes[key]
		end }
	end
	local visitListeners, visitSignal = listeners()
	local guid = 0
	local services = {
		AnalyticsService = fakeAnalytics,
		HttpService = { GenerateGUID = function()
			guid += 1
			return `visit{guid}`
		end },
		Players = fakePlayers,
		RunService = { IsStudio = function()
			return false
		end },
		ReplicatedStorage = {
			AnalyticsConfig = TestConfig, AnalyticsRules = Rules, MonetizationConfig = fakeMonetization,
			LayerConfig = { LayerForLevel = function(level)
				return if type(level) == "number" then { Number = math.min(6, (level - 1) // 10 + 1) } else nil
			end },
			NumberFormat = { Short = function(value)
				return tostring(value)
			end },
			WaitForChild = function(_, name)
				assert(name == "ShopVisit", "unexpected remote " .. name)
				return { OnServerEvent = visitSignal }
			end,
		},
	}
	local datas = {}
	local loadedList, loadedSignal = listeners()
	local parent = {
		PlayerData = {
			OnLoaded = function(fn)
				loadedSignal:Connect(fn)
			end,
			Edit = function(player)
				return datas[player]
			end,
		},
	}
	local clock = 0
	local env = setmetatable({
		game = { GetService = function(_, name)
			return assert(services[name], "unexpected service " .. name)
		end, BindToClose = function() end },
		task = { spawn = function() end }, -- (the flush loop never runs in the spec)
		script = { Parent = parent },
		require = function(module)
			return module
		end,
		typeof = function(value)
			return if type(value) == "table" and value.__fakePlayer then "Instance" else typeof(value)
		end,
		os = { clock = function()
			return clock
		end },
		print = function() end,
		warn = function() end,
	}, { __index = getfenv(1) })
	local chunk = assert(loadstring(sources.Analytics, "Analytics"))
	setfenv(chunk, env)
	local Analytics = chunk()
	Analytics.Start()
	local function fire(list, ...)
		for _, fn in list do
			fn(...)
		end
	end
	local function take()
		local copy = table.clone(events)
		table.clear(events)
		return table.concat(copy, " | ")
	end

	local ana = newPlayer("Ana")
	datas[ana] = { Funnels = Rules.New() }
	fire(loadedList, ana, datas[ana])
	check(take() == "Ana onboarding 1 Joined", "joining logs the Joined step")
	fire(loadedList, ana, datas[ana])
	check(take() == "", "a rejoin logs nothing again")
	Analytics.Onboarding(ana, "StepThree")
	check(take() == "", "a step reached early waits")
	Analytics.Onboarding(ana, "StepTwo")
	check(take() == "Ana onboarding 2 Step two | Ana onboarding 3 Step three", "...and logs right after the step before it, in order")
	Analytics.Onboarding(ana, "StepTwo")
	Analytics.Onboarding(ana, "NotAStep")
	check(take() == "", "a step again, or an unknown key: nothing")
	check(datas[ana].Funnels.Onboarding == 3, "the progress is in the player's data (saved)")

	local ben = newPlayer("Ben")
	Analytics.Onboarding(ben, "Joined")
	check(take() == "", "nothing while the player's data isn't ready")
	Analytics.Onboarding({ Name = "Dummy" }, "Joined")
	check(take() == "", "something that isn't a player logs nothing")

	-- The Robux shop
	local function visitEvent(player, ...)
		clock += 1
		fire(visitListeners, player, ...)
	end
	Analytics.RobuxPrompted(ana, "TestPack")
	check(take() == "", "a prompt from outside the shop logs nothing")
	visitEvent(ana, "Open", "Robux")
	check(take() == "Ana RobuxShop visit1 1 Opened shop", "opening the shop starts a visit")
	visitEvent(ana, "Info", "Robux", "TestPack")
	visitEvent(ana, "Info", "Robux", "TestPack")
	check(take() == "Ana RobuxShop visit1 2 Viewed item", "INFO, once per visit")
	Analytics.RobuxPurchased(ana, "TestPack")
	check(take() == "", "a purchase that wasn't prompted from this visit logs nothing")
	Analytics.RobuxPrompted(ana, "TestPack")
	Analytics.RobuxPrompted(ana, "TestPack")
	check(take() == "Ana RobuxShop visit1 3 Prompt shown", "the prompt, once")
	visitEvent(ana, "Close", "Robux")
	Analytics.RobuxPurchased(ana, "TestPack")
	Analytics.RobuxPurchased(ana, "TestPack")
	check(take() == "Ana RobuxShop visit1 4 Purchased", "the purchase counts for its visit even after the window closed, once")
	Analytics.RobuxPrompted(ana, "TestPack")
	check(take() == "", "a prompt after the window closed doesn't count")
	visitEvent(ana, "Open", "Robux")
	check(take() == "", "reopening straight away isn't a new visit (spamming Open can't inflate the funnel)")
	visitEvent(ana, "Close", "Robux")
	clock += 16
	visitEvent(ana, "Open", "Robux")
	Analytics.RobuxPrompted(ana, "TestPass")
	check(take() == "Ana RobuxShop visit2 1 Opened shop | Ana RobuxShop visit2 2 Viewed item | Ana RobuxShop visit2 3 Prompt shown",
		"a new visit is a new session; a buy button fills in Viewed item")
	visitEvent(ana, "Info", "Robux", "NotAThing")
	visitEvent(ana, "Info", "Robux", string.rep("A", 40))
	visitEvent(ana, "Open", "Gear")
	visitEvent(ana, 42, "Robux")
	check(take() == "", "unknown items, shops and actions from the client are ignored")
	visitEvent(ana, "Close", "Robux")
	fire(visitListeners, ana, "Open", "Robux") -- at the same moment: too fast
	check(take() == "", "the ShopVisit remote is rate-limited")
	Analytics.ShopOpened(ana, "Gear")
	check(take() == "", "a shop that isn't in the config logs nothing")

	-- Progression funnels: one session per player, kept in the save
	local dan = newPlayer("Dan")
	datas[dan] = { Funnels = Rules.New(), BlockLevel = 1, MaxLayerOpened = 5, Rebirths = 0 }
	fire(loadedList, dan, datas[dan])
	local joined = take()
	local id = datas[dan].Funnels.ProgressId
	check(type(id) == "string" and joined == `Dan onboarding 1 Joined | Dan LayersReached {id} 1 Layer 1 Fresh Snow`,
		"joining logs layer 1 under the player's own progression session (no rank yet)")
	check(datas[dan].Funnels.Layers == 1 and datas[dan].Funnels.Ranks == 0, "...and the progress is in the save")
	datas[dan].BlockLevel = 31
	Analytics.Progress(dan)
	check(take() == `Dan LayersReached {id} 2 Layer 2 Blue Ice | Dan LayersReached {id} 3 Layer 3 Ancient Ice | Dan LayersReached {id} 4 Layer 4 Crystal Ice`,
		"skipped layers are filled in, in order, in the same session")
	datas[dan].BlockLevel = 1
	datas[dan].Rebirths = 3
	Analytics.Progress(dan)
	check(take() == `Dan RebirthRanks {id} 1 Rank 1 Ice Breaker | Dan RebirthRanks {id} 2 Rank 3 Glacier Diver`, "a rebirth logs its ranks; the reset level logs no layer")
	Analytics.Progress(dan)
	check(take() == "" and datas[dan].Funnels.ProgressId == id, "nothing twice, and the session id stays")
	Analytics.Progress(ben)
	check(take() == "", "no progression while the player's data isn't ready")

	-- Crystals: steady flows add up until the flush; one-off flows go at once with their balance
	Analytics.CrystalsEarned(dan, "Taps", 10, 100)
	Analytics.CrystalsEarned(dan, "Taps", 5, 105)
	Analytics.CrystalsEarned(dan, "Buildings", 20, 125)
	Analytics.CrystalsSpent(dan, "Building", 50, 75, "HeatLamp")
	Analytics.CrystalsSpent(dan, "Building", 70, 5, "HeatLamp")
	check(take() == "", "taps, buildings and building purchases wait for the flush")
	Analytics.CrystalsEarned(dan, "DailyChest", 300, 305)
	Analytics.CrystalsEarned(dan, "Code", 250, 555, "THAWED")
	Analytics.CrystalsEarned(dan, "Bundle", 1000, 1555, "CrystalPouch")
	Analytics.CrystalsSpent(dan, "Upgrade", 100, 1455, "StonePick")
	check(take() == "Dan economy Source Crystals 300 305 TimedReward DailyChest | Dan economy Source Crystals 250 555 Code THAWED"
		.. " | Dan economy Source Crystals 1000 1555 IAP CrystalPouch | Dan economy Sink Crystals 100 1455 Shop StonePick",
		"the daily chest, a code, a bundle and an upgrade are sent at once, with the balance after them")
	Analytics.CrystalsEarned(dan, "Debug", 5, 0)
	Analytics.CrystalsEarned(dan, "Taps", -1, 0)
	Analytics.CrystalsEarned(dan, "Taps", 0 / 0, 0)
	Analytics.CrystalsEarned(dan, "Taps", math.huge, 0)
	Analytics.CrystalsEarned({ Name = "Dummy" }, "DailyChest", 5, 0)
	check(take() == "", "unknown sources, bad amounts and non-players send nothing")
	dan.Attributes.Crystals = 1455
	check(Analytics.FlushEconomy(dan) == 3, "the flush sends one event per batched flow")
	local flushed = table.clone(events)
	table.sort(flushed)
	table.clear(events)
	check(table.concat(flushed, " | ") == "Dan economy Sink Crystals 120 1455 Shop HeatLamp | Dan economy Source Crystals 15 1455 Gameplay Taps | Dan economy Source Crystals 20 1455 Gameplay Buildings",
		"...added up, with the balance at the flush")
	check(Analytics.FlushEconomy(dan) == 0 and take() == "", "a second flush has nothing to send")

	-- Custom events
	Analytics.Custom(dan, "GlacierWon", 5, "Place - Top")
	Analytics.Custom(dan, "GlacierJoined")
	Analytics.Custom(dan, "NotAnEvent")
	check(take() == "Dan custom GoldenGlacierWon 5 Place - Top | Dan custom GoldenGlacierJoined 1 -", "custom events by their config key; unknown keys send nothing")

	-- The shipped funnel: the real config's first step (Joined) is logged as step 1.
	services.ReplicatedStorage.AnalyticsConfig = Config
	local emptyChunk = assert(loadstring(sources.Analytics, "Analytics"))
	setfenv(emptyChunk, env)
	local EmptyAnalytics = emptyChunk()
	local cara = newPlayer("Cara")
	datas[cara] = { Funnels = Rules.New() }
	EmptyAnalytics.Onboarding(cara, "Joined")
	check(string.find(take(), "onboarding 1 Joined", 1, true) ~= nil and datas[cara].Funnels.Onboarding == 1, "with the shipped funnel, Joined is step 1")
	EmptyAnalytics.Onboarding(cara, "FirstRebirth")
	check(datas[cara].Funnels.Onboarding == 1, "...and a later step reached early waits for the ones before it")

	return passed
end
