-- Spec for offline earnings: the maths in src/replicated/OfflineEarningsRules.luau (the rate, the cap,
-- the server-clock edge cases, the time text) and the REAL src/server/OfflineEarnings.luau against a
-- fake PlayerData, Workspace and clock (the earner hook, the popup attribute, StudioTimeAway). The
-- saving side (LeftAt written by every save, read once per session) is in tests/PlayerData.spec.luau.
-- Run: python tools/run_specs.py OfflineEarnings
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end
	local function near(a, b)
		return math.abs(a - b) < 1e-6
	end

	local R = assert(loadstring(sources.OfflineEarningsRules))()
	local settings = { Rate = 1.0, CapSeconds = 406 } -- test numbers (the shipped ones are placeholders)
	check(R.Settings.Rate == 0.5 and R.Settings.CapSeconds == 3600, "the shipped settings: 50% of income, at most 2 hours away (the doc)")
	check(not R.IsCapped(7200, R.Settings) and R.IsCapped(7201, R.Settings), "...earning stops after 2 hours away")

	-- One income source ------------------------------------------------------------------------------
	check(R.Earnings(1, 100, settings) == 100, "1/s away 100 s earns 100")
	check(R.Earnings(1, 406, settings) == 406, "...away exactly the cap earns the cap")
	check(R.Earnings(1, 407, settings) == 406, "...away longer is capped")
	check(R.Earnings(1, 7 * 86400, settings) == 406, "...away a week is still capped")
	check(R.Earnings(250, 3600, settings) == 250 * 406, "the cap is in seconds of the source's own income")
	check(near(R.Earnings(2.5, 10, settings), 25), "fractional income adds up exactly")
	check(R.Earnings(0, 100, settings) == 0 and R.Earnings(-3, 100, settings) == 0, "no income, nothing earned")
	check(R.Earnings(0 / 0, 100, settings) == 0 and R.Earnings(math.huge, 100, settings) == 0, "an income that isn't a real number earns nothing")
	check(R.Earnings(5, 0, settings) == 0 and R.Earnings(5, -50, settings) == 0, "no time away, nothing earned")

	local half = { Rate = 0.5, CapSeconds = 406 }
	check(R.Earnings(10, 100, half) == 500, "rate 0.5: half the income for the time away")
	check(R.Earnings(10, 2000, half) == 4060, "...still capped at the cap's seconds of full income")
	check(R.IsCapped(406, settings) == false and R.IsCapped(407, settings) == true, "capped once away longer than the cap")
	check(R.IsCapped(800, half) == false and R.IsCapped(813, half) == true, "with rate 0.5 the cap is reached after twice the time")

	-- Several sources: each capped on its own -------------------------------------------------------------
	local list = { { key = 1, income = 1 }, { key = 2, income = 10 }, { key = 5, income = 1000 }, { key = 7, income = 0 } }
	local amounts, total = R.Plan(list, 60, settings)
	check(amounts[1] == 60 and amounts[2] == 600 and amounts[5] == 60000, "60 s away: every source earns 60 s of its own income")
	check(amounts[7] == nil, "a source earning nothing isn't listed")
	check(total == 60660, "the total adds every source")
	amounts, total = R.Plan(list, 10000, settings)
	check(amounts[1] == 406 and amounts[2] == 4060 and amounts[5] == 406000 and total == 410466, "long away: each source stops at its own cap")
	amounts, total = R.Plan({}, 10000, settings)
	check(next(amounts) == nil and total == 0, "nothing listed, nothing earned")
	check(list[1].amount == nil and #list == 4, "the caller's list isn't changed")

	-- The server's clock --------------------------------------------------------------------------------
	local now = 1_800_000_000
	check(R.SecondsAway(now - 600, now) == 600, "left 10 minutes ago: 600 s away")
	check(R.SecondsAway(now, now) == 0, "left this very second: 0")
	check(R.SecondsAway(now + 30, now) == 0, "a leave time in the future (a clock that went back): 0, never negative")
	check(R.SecondsAway(nil, now) == 0, "no leave time (a new player): 0")
	check(R.SecondsAway("1799999000", now) == 0, "a leave time that is text: 0")
	check(R.SecondsAway(0, now) == 0 and R.SecondsAway(-100, now) == 0, "a zero or negative leave time: 0")
	check(R.SecondsAway(now - 10.5, now) == 0, "a leave time that isn't whole seconds: 0")
	check(R.SecondsAway(0 / 0, now) == 0 and R.SecondsAway(math.huge, now) == 0, "NaN or infinite leave times: 0")
	check(R.SecondsAway(now - 600, 0 / 0) == 0, "a broken clock now: 0")
	check(R.SecondsAway(1, now) == now - 1, "a very old leave time is a long time away (the cap keeps it small)")
	check(R.Earnings(1, R.SecondsAway(1, now), settings) == 406, "...so it still pays only the cap")
	check(R.CleanLeftAt(now) == now and R.CleanLeftAt(-1) == nil and R.CleanLeftAt(2.5) == nil and R.CleanLeftAt("x") == nil, "CleanLeftAt keeps only whole positive times")

	-- What the popup says ---------------------------------------------------------------------------------
	check(R.Describe(45) == "45s" and R.Describe(0) == "0s" and R.Describe(-5) == "0s", "seconds")
	check(R.Describe(406) == "6m 46s" and R.Describe(120) == "2m", "minutes")
	check(R.Describe(3 * 3600 + 12 * 60 + 9) == "3h 12m" and R.Describe(7200) == "2h", "hours")
	check(R.Describe(2 * 86400 + 5 * 3600) == "2d 5h" and R.Describe(86400) == "1d", "days")
	check(R.RuleText(R.Settings) == "You earn half your building income for up to 2 hours away.", "the popup's rule text matches the rule")
	check(R.RuleText({ Rate = 1, CapSeconds = 3600 }) == "You earn all your building income for up to 1 hour away."
		and R.RuleText({ Rate = 0.25, CapSeconds = 900 }) == "You earn 25% of your building income for up to 1 hour away.", "...for other settings too")

	-- The real OfflineEarnings, against fakes ------------------------------------------------------------------
	local realHttp = game:GetService("HttpService")
	local inStudio = true
	local workspaceAttributes = {}
	local clockNow = now
	local loadedCallbacks, dataOf, leftAtOf, important = {}, {}, {}, 0
	local fakePlayerData = {
		OnLoaded = function(fn) table.insert(loadedCallbacks, fn) end,
		Edit = function(player) return dataOf[player] end,
		TakeLeftAt = function(player)
			local leftAt = leftAtOf[player]
			leftAtOf[player] = nil
			return leftAt
		end,
		MarkImportant = function() important += 1 end,
		Publish = function() end,
	}
	local modules = {
		OfflineEarningsRules = R,
		NumberFormat = assert(loadstring(sources.NumberFormat))(),
		PlayerData = fakePlayerData,
	}
	local services = {
		HttpService = realHttp,
		ReplicatedStorage = modules,
		RunService = { IsStudio = function() return inStudio end },
		Workspace = { GetAttribute = function(_, name) return workspaceAttributes[name] end },
	}
	local chunk = assert(loadstring(sources.OfflineEarnings, "OfflineEarnings"))
	setfenv(chunk, setmetatable({
		game = { GetService = function(_, name) return assert(services[name], "unexpected service " .. name) end },
		script = { Parent = modules },
		require = function(module) return module end,
		os = { time = function() return clockNow end, clock = os.clock },
		print = function() end,
		warn = function() end,
	}, { __index = getfenv(1) }))
	local OfflineEarnings = chunk()
	OfflineEarnings.Start()
	check(#loadedCallbacks == 1, "Start listens for players' data loading")

	local function newPlayer(name)
		local attributes = {}
		return {
			Name = name,
			GetAttribute = function(_, key) return attributes[key] end,
			SetAttribute = function(_, key, value) attributes[key] = value end,
		}
	end
	local function popup(player)
		local raw = player:GetAttribute("OfflineEarnings")
		return raw and realHttp:JSONDecode(raw)
	end
	local function join(player, leftAt)
		dataOf[player] = dataOf[player] or { Points = 0 }
		leftAtOf[player] = leftAt
		for _, fn in loadedCallbacks do
			fn(player, dataOf[player])
		end
	end

	-- No earner yet (the game has nothing that earns): nothing is paid, no popup.
	local ana = newPlayer("Ana")
	join(ana, now - 600)
	check(ana:GetAttribute("OfflineEarnings") == nil and important == 0, "no earner: nothing paid, no popup")
	check(OfflineEarnings.Pay(ana, 100) == 0, "...and Pay pays nothing")

	-- An earner: 2 points a second, capped by the rules.
	local calls = {}
	OfflineEarnings.SetEarner(function(player, data, secondsAway, given)
		table.insert(calls, secondsAway)
		local amount = R.Earnings(2, secondsAway, given)
		data.Points += amount
		return amount, "points"
	end)
	local ben = newPlayer("Ben")
	join(ben, now - 100)
	local shown = popup(ben)
	-- (the shipped settings: 50% while away, so 2 points/s for 100 s pays 100)
	check(dataOf[ben].Points == 100 and shown and shown.Amount == 100 and shown.Seconds == 100 and shown.Label == "points" and shown.Capped == false and shown.At == now,
		"away 100 s: the earner pays it, and the popup attribute says how much, how long and what")
	check(important == 1, "...and an important save is asked for")
	join(ben, nil)
	check(#calls == 1, "a new player (no leave time) earns nothing")
	join(ben, now + 50)
	check(#calls == 1, "a leave time in the future pays nothing")
	local cara = newPlayer("Cara")
	join(cara, now - 10 * 86400)
	check(popup(cara).Capped == true and popup(cara).Amount == 2 * R.Settings.CapSeconds, "away for days: capped at the settings' cap, and the popup says so")

	-- StudioTimeAway replaces the real gap, in Studio only, for a save that has a leave time.
	workspaceAttributes.StudioTimeAway = 30
	local dan = newPlayer("Dan")
	join(dan, now - 5000)
	check(popup(dan).Seconds == 30 and dataOf[dan].Points == 30, "StudioTimeAway: counts as away that long")
	local eve = newPlayer("Eve")
	join(eve, nil)
	check(eve:GetAttribute("OfflineEarnings") == nil, "...but never for a new player")
	inStudio = false
	local fay = newPlayer("Fay")
	join(fay, now - 40)
	check(popup(fay).Seconds == 40, "...and it is ignored outside Studio")
	inStudio = true
	workspaceAttributes.StudioTimeAway = nil

	-- Pay directly (the debug menu), and earners that misbehave.
	check(OfflineEarnings.Pay(ana, 50) == 50 and dataOf[ana].Points == 50, "debug: Pay as if away N seconds (at 50%)")
	check(OfflineEarnings.Pay(ana, 0) == 0 and OfflineEarnings.Pay(ana, -5) == 0 and OfflineEarnings.Pay(ana, 0 / 0) == 0, "no time away: nothing")
	check(OfflineEarnings.Pay(newPlayer("NoData"), 50) == 0, "data not ready: nothing")
	OfflineEarnings.SetEarner(function() error("boom") end)
	check(OfflineEarnings.Pay(ana, 50) == 0, "an earner that errors pays nothing (and doesn't break the join)")
	OfflineEarnings.SetEarner(function() return 0 / 0 end)
	local before = ana:GetAttribute("OfflineEarnings")
	check(OfflineEarnings.Pay(ana, 50) == 0 and ana:GetAttribute("OfflineEarnings") == before, "an earner that returns nonsense: nothing, no new popup")

	return passed
end
