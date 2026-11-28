-- Spec for promo codes: the rules (src/server/CodeRules.luau), the shipped CodesConfig, and the real
-- CodeService against a fake save and fake rewards (PurchaseRewards). Nothing real is touched.
-- Run: python tools/run_specs.py Codes
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local CodeRules = assert(loadstring(sources.CodeRules))()

	-- Typing a code --------------------------------------------------------------------------------
	check(CodeRules.Normalize("RELEASE") == "RELEASE" and CodeRules.Normalize("release") == "RELEASE" and CodeRules.Normalize("ReLeAsE") == "RELEASE",
		"codes aren't case-sensitive")
	check(CodeRules.Normalize("  frosty \n") == "FROSTY", "spaces around a code are ignored")
	check(CodeRules.Normalize("") == nil and CodeRules.Normalize("   ") == nil and CodeRules.Normalize(nil) == nil and CodeRules.Normalize(5) == nil, "nothing typed, or not text: no code")
	check(CodeRules.Normalize("RE LEASE") == nil and CodeRules.Normalize("release!") == nil and CodeRules.Normalize("ÉCLAIR") == nil, "only letters and digits")
	check(CodeRules.Normalize(string.rep("A", 32)) ~= nil and CodeRules.Normalize(string.rep("A", 33)) == nil, "at most 32 characters")

	-- Expiry dates ----------------------------------------------------------------------------------
	local endOf2026 = DateTime.fromUniversalTime(2026, 12, 31, 23, 59, 59).UnixTimestamp
	check(CodeRules.ExpiresAt("2026-12-31") == endOf2026, "Expires = \"2026-12-31\": works until the end of that day, UTC")
	check(CodeRules.ExpiresAt(nil) == nil, "no Expires: never expires")
	check(not pcall(CodeRules.ExpiresAt, "31/12/2026") and not pcall(CodeRules.ExpiresAt, "soon"), "an unreadable date is a config error, not a code that runs forever")

	-- The rules -------------------------------------------------------------------------------------
	local release = { Code = "RELEASE", Reward = { Kind = "Test", Amount = 5 }, Active = true }
	local dated = { Code = "SUMMER", Reward = { Kind = "Test", Amount = 1 }, Active = true, Expires = "2026-06-30" }
	local off = { Code = "OFF", Reward = { Kind = "Test", Amount = 1 }, Active = false }
	local config = { Codes = { release, dated, off } }
	check(CodeRules.Find(config, "RELEASE") == release and CodeRules.Find(config, "NOPE") == nil and CodeRules.Find(config, nil) == nil, "finding a code")
	local now = DateTime.fromUniversalTime(2026, 6, 15, 12, 0, 0).UnixTimestamp
	check(CodeRules.Check(release, "RELEASE", {}, now), "a new, active code works")
	local ok, why = CodeRules.Check(release, "RELEASE", { "FROSTY", "RELEASE" }, now)
	check(not ok and why == "Used", "once per player: a redeemed code is Used")
	ok, why = CodeRules.Check(nil, "NOPE", {}, now)
	check(not ok and why == "Unknown", "a code that doesn't exist is Unknown")
	ok, why = CodeRules.Check(nil, nil, {}, now)
	check(not ok and why == "Unknown", "unreadable text is Unknown too")
	check(CodeRules.Check(dated, "SUMMER", {}, DateTime.fromUniversalTime(2026, 6, 30, 23, 59, 0).UnixTimestamp), "a dated code still works on its last day")
	ok, why = CodeRules.Check(dated, "SUMMER", {}, DateTime.fromUniversalTime(2026, 7, 1, 0, 0, 1).UnixTimestamp)
	check(not ok and why == "Expired", "...and is Expired the day after")
	ok, why = CodeRules.Check(off, "OFF", {}, now)
	check(not ok and why == "Expired", "a code switched off (Active = false) reads as Expired")
	for _, reason in { "Empty", "Unknown", "Expired", "Used", "TooFast", "DataNotReady" } do
		check(type(CodeRules.Messages[reason]) == "string" and #CodeRules.Messages[reason] > 0, "a clear message for " .. reason)
	end

	-- Rate limit ------------------------------------------------------------------------------------
	local history, limit = {}, { MinSeconds = 1, PerMinute = 6 }
	check(CodeRules.AllowAttempt(history, 0, limit) and not CodeRules.AllowAttempt(history, 0.5, limit), "attempts at least 1 s apart")
	for t = 1, 5 do
		CodeRules.AllowAttempt(history, t, limit)
	end
	check(#history == 6 and not CodeRules.AllowAttempt(history, 10, limit), "at most 6 attempts in any minute")
	check(CodeRules.AllowAttempt(history, 61, limit), "...and more once the minute has passed")

	-- The config ------------------------------------------------------------------------------------
	check(not pcall(CodeRules.Validate, { Codes = { { Code = "DUP", Reward = {} }, { Code = "dup", Reward = {} } } }), "a code listed twice (any case) is a config error")
	check(not pcall(CodeRules.Validate, { Codes = { { Code = "BAD CODE", Reward = {} } } }), "an unreadable code is a config error")
	check(not pcall(CodeRules.Validate, { Codes = { { Code = "NOREWARD" } } }), "a code with no reward is a config error")
	check(pcall(CodeRules.Validate, config), "a good list passes")

	-- The real CodeService, against fakes --------------------------------------------------------------
	local clock, time = 1000, now
	local fakeOs = { clock = function() return clock end, time = function() return time end }
	local dataOf, important, published = {}, 0, 0
	local fakeData = {
		Edit = function(player) return dataOf[player] end,
		MarkImportant = function() important += 1 end,
		Publish = function() published += 1 end,
	}
	-- Fake rewards: "Test" adds Amount to a counter; "Limited" needs room (a stand-in for any reward
	-- that can't always apply); anything else is a kind the game doesn't know.
	local room, given = {}, {}
	local fakeRewards = {
		Give = function(player, product)
			table.insert(given, product)
			local reward = product.Reward
			if reward.Kind == "Test" then
				dataOf[player].Points += reward.Amount
				return `{reward.Amount} points`
			elseif reward.Kind == "Limited" then
				if (room[player] or 0) < 1 then
					return nil, `No room for the {product.Name}.`
				end
				room[player] -= 1
				return product.Name
			end
			return nil, "This reward isn't available yet."
		end,
	}
	local modules = {}
	local function load(name, fakes)
		local chunk = assert(loadstring(sources[name], name))
		setfenv(chunk, setmetatable({
			game = { GetService = function(_, service)
				return if service == "ReplicatedStorage" or service == "Players" then modules else game:GetService(service)
			end },
			script = { Parent = modules },
			require = function(module) return module end,
			os = fakeOs,
			print = function() end,
		}, { __index = getfenv() }))
		modules[name] = chunk()
		for key, value in fakes or {} do
			modules[key] = value
		end
		return modules[name]
	end
	load("CodeRules")
	local CodesConfig = load("CodesConfig")
	check(type(CodesConfig.Codes) == "table" and #CodesConfig.Codes == 8, "CodesConfig ships with the tutorial and launch codes and six likes milestone codes")
	local milestones = 0
	for _, entry in CodesConfig.Codes do
		if string.sub(entry.Code, 1, 5) == "LIKES" then
			milestones += 1
			check(entry.Reward.Kind == "CrystalBundle" and entry.Reward.Seconds > 0 and entry.Active == false,
				`{entry.Code} pays minutes of income and stays off until its milestone`)
		else
			check(entry.Reward.Kind == "Crystals" and entry.Reward.Amount > 0 and entry.Active, `{entry.Code} gives crystals`)
		end
	end
	check(milestones == 6, "six likes milestone codes")
	check(CodesConfig.RateLimit.MinSeconds == 1 and CodesConfig.RateLimit.PerMinute == 6, "the rate limit: 1 s apart, 6 a minute")
	check(pcall(modules.CodeRules.Validate, CodesConfig), "the shipped list is valid")
	-- Test-only codes, added before CodeService checks the list.
	table.insert(CodesConfig.Codes, { Code = "RELEASE", Reward = { Kind = "Test", Amount = 5 }, Active = true })
	table.insert(CodesConfig.Codes, { Code = "FROSTY", Reward = { Kind = "Test", Amount = 10 }, Active = true })
	table.insert(CodesConfig.Codes, { Code = "OLDCODE", Reward = { Kind = "Test", Amount = 1 }, Active = true, Expires = "2020-01-01" })
	table.insert(CodesConfig.Codes, { Code = "ROOMTEST", Name = "Ice Crate", Reward = { Kind = "Limited" }, Active = true })
	table.insert(CodesConfig.Codes, { Code = "NOKIND", Reward = { Kind = "Unbuilt" }, Active = true })
	modules.PlayerData = fakeData
	modules.PurchaseRewards = fakeRewards
	local CodeService = load("CodeService")

	local player = { Name = "Coder", UserId = 5 }
	local function redeem(text)
		clock += 11 -- past the 1 s spacing, and at most 6 a minute
		return CodeService.Redeem(player, text)
	end
	local reply = redeem("RELEASE")
	check(not reply.ok and reply.message == CodeRules.Messages.DataNotReady and #given == 0, "data not loaded yet: refused, nothing given")
	dataOf[player] = { Points = 0, Codes = {} }
	reply = redeem("release")
	check(reply.ok and dataOf[player].Points == 5 and dataOf[player].Codes[1] == "RELEASE", "RELEASE (any case): its reward, and the code is saved as redeemed")
	check(given[1].Key == "Code_RELEASE" and given[1].Name == "reward" and given[1].Reward.Kind == "Test", "the reward goes through PurchaseRewards as product Code_<CODE>")
	check(important >= 1 and published >= 1 and string.find(reply.message, "5 points", 1, true), "...an important save is asked for, and the message says what it gave")
	reply = redeem(" Release ")
	check(not reply.ok and reply.message == CodeRules.Messages.Used and dataOf[player].Points == 5 and #dataOf[player].Codes == 1, "the same code again: already redeemed, nothing given")
	reply = redeem("ROOMTEST")
	check(not reply.ok and string.find(reply.message, "No room for the Ice Crate", 1, true) and #dataOf[player].Codes == 1,
		"a reward that can't apply now: refused with a clear message, and NOT used up (its own Name in the message)")
	room[player] = 1
	reply = redeem("roomtest")
	check(reply.ok and dataOf[player].Codes[2] == "ROOMTEST" and room[player] == 0, "...and works once it can")
	reply = redeem("NOKIND")
	check(not reply.ok and reply.message == "This reward isn't available yet." and #dataOf[player].Codes == 2, "a reward kind the game doesn't have: refused, code not used up")
	reply = redeem("NOSUCHCODE")
	check(not reply.ok and reply.message == CodeRules.Messages.Unknown, "an unknown code: clear message")
	reply = redeem("OLDCODE")
	check(not reply.ok and reply.message == CodeRules.Messages.Expired and #dataOf[player].Codes == 2, "an expired code: clear message, nothing given")
	reply = redeem("   ")
	check(not reply.ok and reply.message == CodeRules.Messages.Empty, "nothing typed: clear message")
	reply = redeem({ "not", "text" })
	check(not reply.ok and reply.message == CodeRules.Messages.Empty, "a non-text request from a client is refused")
	reply = redeem("FROSTY")
	check(reply.ok and dataOf[player].Points == 15, "FROSTY: its reward")
	-- Rate limit: two attempts in the same second.
	clock += 5
	CodeService.Redeem(player, "NOPE")
	reply = CodeService.Redeem(player, "RELEASE")
	check(not reply.ok and reply.message == CodeRules.Messages.TooFast, "attempts closer than 1 s apart are refused")
	local spammer = { Name = "Spammer", UserId = 6 }
	dataOf[spammer] = { Points = 0, Codes = {} }
	local refused = 0
	for _ = 1, 10 do
		clock += 1.5
		if CodeService.Redeem(spammer, "GUESS").message == CodeRules.Messages.TooFast then
			refused += 1
		end
	end
	check(refused == 4, "guessing codes: only 6 attempts a minute get an answer")
	check(CodeService.ResetRedeemed(player) == 3 and #dataOf[player].Codes == 0, "debug: resetting forgets the redeemed codes")
	reply = redeem("RELEASE")
	check(reply.ok and dataOf[player].Points == 20, "...so they work again")
	-- A save never holds more than 200 redeemed codes (more and the save is refused): the oldest goes.
	local collector = { Name = "Collector", UserId = 7 }
	local many = {}
	for i = 1, 200 do
		many[i] = "OLD" .. i
	end
	dataOf[collector] = { Points = 0, Codes = many }
	clock += 60
	reply = CodeService.Redeem(collector, "FROSTY")
	check(reply.ok and #dataOf[collector].Codes == 200 and dataOf[collector].Codes[200] == "FROSTY" and dataOf[collector].Codes[1] == "OLD2",
		"redeeming with 200 codes saved keeps the most recent 200 (the save would refuse more)")

	return passed
end
