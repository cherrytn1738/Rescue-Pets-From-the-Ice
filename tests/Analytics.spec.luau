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
	check(type(Config.Onboarding) == "table" and #Config.Onboarding == 0, "the onboarding funnel ships empty (the game adds its steps)")
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
		return { Name = name, __fakePlayer = true, Parent = fakePlayers, IsA = function(_, class)
			return class == "Player"
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
		end },
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

	-- The shipped (empty) funnel: the real config loaded into the module logs no onboarding at all.
	services.ReplicatedStorage.AnalyticsConfig = Config
	local emptyChunk = assert(loadstring(sources.Analytics, "Analytics"))
	setfenv(emptyChunk, env)
	local EmptyAnalytics = emptyChunk()
	local cara = newPlayer("Cara")
	datas[cara] = { Funnels = Rules.New() }
	EmptyAnalytics.Onboarding(cara, "Joined")
	check(take() == "" and datas[cara].Funnels.Onboarding == 0, "with the shipped empty funnel, onboarding logs nothing")

	return passed
end
