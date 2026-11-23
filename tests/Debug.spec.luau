-- Spec for the debug menu: its access rules and input checks (src/server/DebugRules.luau) with fake
-- players and fake actions, and the real action list (src/server/DebugActions.luau) loaded against
-- fake systems and an EMPTY MonetizationConfig. Run: python tools/run_specs.py Debug
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local DebugRules = assert(loadstring(sources.DebugRules))()
	local DebugConfig = assert(loadstring(sources.DebugConfig))()

	-- Who has access ------------------------------------------------------------------------------
	check(#DebugConfig.AllowedUserIds == 0, "the allowlist is empty by default")
	check(DebugRules.HasAccess(123, true, {}), "in Studio, everyone has access")
	check(DebugRules.HasAccess(-1, true, {}), "...including Clients-and-Servers test players")
	check(not DebugRules.HasAccess(123, false, {}), "a live server with an empty allowlist: nobody has access")
	check(DebugRules.HasAccess(123, false, { 123 }), "a live server: a listed user id has access")
	check(not DebugRules.HasAccess(456, false, { 123 }), "a live server: anyone not listed has no access")
	check(not DebugRules.HasAccess("123", false, { 123 }), "a user id that isn't a number never matches")
	check(not DebugRules.HasAccess(123, false, nil), "a missing allowlist means no access")

	-- Fake world ------------------------------------------------------------------------------------
	local runs = {}
	local function fakeAction(id, extra)
		local action = {
			Id = id,
			Label = id,
			Params = {},
			Run = function(target, args)
				table.insert(runs, { id = id, target = target, args = args })
				return `{id} done`
			end,
		}
		for key, value in extra or {} do
			action[key] = value
		end
		return action
	end
	local actions = {
		SetCount = fakeAction("SetCount", { Params = { { Name = "Amount", Label = "Amount", Kind = "number", Min = 1, Max = 1000, Integer = true, Default = 50 } } }),
		PickColour = fakeAction("PickColour", { Params = { { Name = "Colour", Label = "Colour", Kind = "choice", Choices = { { Value = "Ice", Label = "Ice" }, { Value = "Snow", Label = "Snow" } }, Default = "Ice" } } }),
		Note = fakeAction("Note", { Params = { { Name = "Note", Label = "Note", Kind = "text", MaxLength = 8, Pattern = "^%a*$", Optional = true } } }),
		Rename = fakeAction("Rename", { Params = { { Name = "Name", Label = "Name", Kind = "text", MaxLength = 8, Pattern = "^%a*$" } } }),
		Switch = fakeAction("Switch", { NoTarget = true }),
		Reset = fakeAction("Reset", { Confirm = true }),
		Broken = fakeAction("Broken", {
			Run = function()
				error("Player2's data isn't ready", 0)
			end,
		}),
	}
	local tester = { Name = "Tester", UserId = 111 }
	local other = { Name = "Player2", UserId = 222 }
	local stranger = { Name = "Stranger", UserId = 999 }
	local inServer = { [111] = tester, [222] = other, [999] = stranger }
	local logs = {}
	local clock = 0
	local env = {
		isStudio = false,
		allowlist = { 111, 222 },
		actions = actions,
		now = 0,
		lastRequestAt = {},
		cooldown = 0.1,
		findTarget = function(userId)
			return inServer[userId]
		end,
		log = function(text)
			table.insert(logs, text)
		end,
	}
	local function send(player, actionId, targetUserId, args, confirmed)
		clock += 1 -- past the cooldown unless a test says otherwise
		env.now = clock
		return DebugRules.Handle({ player = player, actionId = actionId, targetUserId = targetUserId, args = args, confirmed = confirmed }, env)
	end

	-- A player without access: rejected, logged, and nothing runs ------------------------------------
	local reply = send(stranger, "SetCount", 999, { Amount = 10 })
	check(not reply.ok and reply.message == "No access", "a non-debug player in a live server is rejected")
	check(#runs == 0, "...and the action never runs")
	check(string.find(logs[#logs], "REJECTED", 1, true) and string.find(logs[#logs], "999", 1, true), "...and the rejection is logged with their user id")
	reply = send(stranger, "Switch", nil, nil)
	check(not reply.ok and #runs == 0, "a non-debug player can't run actions without a target either")
	reply = send(stranger, "SetCount", 111, { Amount = 10 })
	check(not reply.ok and #runs == 0, "a non-debug player can't target a debug player")

	-- Access is checked on every request, not once ----------------------------------------------------
	reply = send(tester, "SetCount", 111, { Amount = 10 })
	check(reply.ok and #runs == 1 and runs[1].target == tester and runs[1].args.Amount == 10, "an allowlisted player's request runs on the target")
	env.allowlist = { 222 }
	reply = send(tester, "SetCount", 111, { Amount = 10 })
	check(not reply.ok and #runs == 1, "removed from the allowlist: the very next request is rejected")
	env.allowlist = {}
	reply = send(other, "SetCount", 222, { Amount = 10 })
	check(not reply.ok and #runs == 1, "an empty allowlist in a live server rejects everyone")
	env.isStudio = true
	reply = send(stranger, "SetCount", 999, { Amount = 10 })
	check(reply.ok and #runs == 2, "in Studio, any player in the test can use it")
	env.isStudio = false
	env.allowlist = { 111, 222 }

	-- Rate limit --------------------------------------------------------------------------------------
	env.now = clock + 1
	DebugRules.Handle({ player = tester, actionId = "Switch" }, env)
	env.now += 0.05
	reply = DebugRules.Handle({ player = tester, actionId = "Switch" }, env)
	check(not reply.ok and reply.message == "Too fast", "two requests within the cooldown: the second is refused")
	clock = env.now

	-- Actions and targets -----------------------------------------------------------------------------
	check(send(tester, "FreeRobux", 111, {}).message == "Unknown action", "an unknown action id is refused")
	check(send(tester, 42, 111, {}).message == "Unknown action", "an action id that isn't text is refused")
	check(not send(tester, "SetCount", 333, { Amount = 5 }).ok, "a target who isn't in the server is refused")
	check(not send(tester, "SetCount", "111", { Amount = 5 }).ok, "a target id that isn't a number is refused")
	check(not send(tester, "SetCount", 111.5, { Amount = 5 }).ok, "a fractional target id is refused")
	local before = #runs
	reply = send(tester, "SetCount", 222, { Amount = 5 })
	check(reply.ok and runs[#runs].target == other, "one tester can target another player")
	reply = send(tester, "Switch", 333, nil)
	check(reply.ok and runs[#runs].target == nil, "an action without a target ignores the target field")
	check(#runs == before + 2, "(only the valid requests ran)")

	-- Number inputs ---------------------------------------------------------------------------------
	local function amountReply(value)
		return send(tester, "SetCount", 111, { Amount = value })
	end
	check(not amountReply(0).ok and not amountReply(1001).ok, "numbers outside their range are refused")
	check(amountReply(1).ok and amountReply(1000).ok, "the range's ends are allowed")
	check(not amountReply(2.5).ok, "a whole-number input refuses fractions")
	check(not amountReply(0 / 0).ok, "NaN is refused")
	check(not amountReply(math.huge).ok, "infinity is refused")
	check(not amountReply("100").ok, "a number sent as text is refused")
	reply = send(tester, "SetCount", 111, {})
	check(reply.ok and runs[#runs].args.Amount == 50, "a missing number with a default uses the default")
	check(not send(tester, "SetCount", 111, "Amount=5").ok, "args that aren't a table are refused")
	reply = send(tester, "SetCount", 111, { Amount = 7, Sneaky = "drop table" })
	check(reply.ok and runs[#runs].args.Sneaky == nil, "extra keys are ignored, not passed on")

	-- Choice inputs ---------------------------------------------------------------------------------
	check(send(tester, "PickColour", 111, { Colour = "Snow" }).ok and runs[#runs].args.Colour == "Snow", "a known choice is accepted")
	check(not send(tester, "PickColour", 111, { Colour = "Lava" }).ok, "an unknown id is refused")
	check(not send(tester, "PickColour", 111, { Colour = 1 }).ok, "a choice that isn't one of the values is refused")
	check(send(tester, "PickColour", 111, {}).ok and runs[#runs].args.Colour == "Ice", "a missing choice uses its default")

	-- Text inputs -----------------------------------------------------------------------------------
	check(send(tester, "Note", 111, { Note = "Frosty" }).ok and runs[#runs].args.Note == "Frosty", "valid text is accepted")
	check(send(tester, "Note", 111, {}).ok and runs[#runs].args.Note == "", "optional text may be left empty")
	check(not send(tester, "Note", 111, { Note = "Fro<st>" }).ok, "text with characters outside its pattern is refused")
	check(not send(tester, "Note", 111, { Note = "Supercalifragilistic" }).ok, "text over its length limit is refused")
	check(not send(tester, "Note", 111, { Note = 5 }).ok, "text that isn't a string is refused")
	check(not send(tester, "Rename", 111, {}).ok, "required text can't be left empty")

	-- Confirm step ----------------------------------------------------------------------------------
	before = #runs
	reply = send(tester, "Reset", 111, nil)
	check(not reply.ok and reply.message == "Needs confirming" and #runs == before, "a confirm action without the confirmation doesn't run")
	reply = send(tester, "Reset", 111, nil, true)
	check(reply.ok and #runs == before + 1, "with the confirmation it runs")

	-- Results -----------------------------------------------------------------------------------------
	reply = send(tester, "SetCount", 111, { Amount = 3 })
	check(reply.ok and reply.message == "SetCount done", "the action's message comes back to the menu")
	reply = send(tester, "Broken", 111, nil)
	check(not reply.ok and reply.message == "Player2's data isn't ready", "an action's refusal comes back as a short message")

	-- The real action list, against fake systems and an empty MonetizationConfig ---------------------
	local calls = {}
	local function record(name)
		return function(...)
			table.insert(calls, { name = name, args = { ... } })
			return 0
		end
	end
	local liveData = { Receipts = {}, Codes = {}, Funnels = { Onboarding = 3, Waiting = { 5 } } }
	local inStudio = true
	local workspaceAttributes = {}
	local fakeWorkspace = {
		SetAttribute = function(_, name, value)
			workspaceAttributes[name] = value
		end,
	}
	local server = {
		PlayerData = {
			Edit = function()
				return liveData
			end,
			Get = function()
				return liveData
			end,
			SaveNow = function()
				return true
			end,
			ResetToNew = function(player)
				table.insert(calls, { name = "ResetToNew", args = { player } })
				return true
			end,
			MarkImportant = record("MarkImportant"),
		},
		CodeService = { ResetRedeemed = function()
			table.insert(calls, { name = "ResetRedeemed" })
			return 2
		end },
		GamePasses = { SetStudioOverride = record("SetStudioOverride") },
		Gifting = { Prepare = record("Prepare"), PromptFinished = record("PromptFinished") },
		OfflineEarnings = { Pay = record("Pay") },
		Receipts = { Simulate = record("Simulate") },
		IceBlockService = { Shatter = record("Shatter"), ForceNextCreature = record("ForceNextCreature"), Reroll = record("Reroll") },
		PetService = { Give = record("Give") },
		PlotService = { SendHome = record("SendHome") },
	}
	local replicated = {
		AnalyticsConfig = { Onboarding = {} },
		CreatureConfig = { Creatures = { { Id = "SnowBunny", Name = "Snow Bunny", Rarity = "Common" } } },
		AnalyticsRules = { New = function()
			return { Onboarding = 0, Waiting = {} }
		end },
		MonetizationConfig = {
			Passes = {},
			Products = {},
			IsLive = function()
				return false
			end,
			GetPass = function()
				return nil
			end,
			GetProduct = function()
				return nil
			end,
		},
	}
	local services = {
		HttpService = game:GetService("HttpService"),
		Players = { GetPlayerByUserId = function()
			return nil
		end },
		ReplicatedStorage = replicated,
		RunService = { IsStudio = function()
			return inStudio
		end },
		Workspace = fakeWorkspace,
	}
	local chunk = assert(loadstring(sources.DebugActions, "DebugActions"))
	setfenv(chunk, setmetatable({
		game = { GetService = function(_, name)
			return assert(services[name], "unexpected service " .. tostring(name))
		end },
		script = { Parent = server },
		require = function(module)
			return module
		end,
		print = function() end,
	}, { __index = getfenv() }))
	local DebugActions = chunk()

	local ids = {}
	for _, entry in DebugActions.Catalog do
		ids[entry.Id] = entry
		check(entry.Run == nil, `the catalogue sent to clients has no code ({entry.Id})`)
		for _, param in entry.Params do
			if param.Kind == "choice" then
				check(#param.Choices >= 1 and param.Default ~= nil, `{entry.Id}.{param.Name} has at least one choice and a default, even with empty configs`)
			end
		end
	end
	for _, id in { "SaveNow", "ShowSave", "ResetSave", "OfflineEarningsNow", "AnalyticsProgress", "AnalyticsRestart", "ResetCodes", "GivePass", "RemovePass", "SimulateReceipt", "DuplicateReceipt", "FreshSave", "UseLiveSaves", "FakeTimeAway", "PaidRandomRestricted", "TeleportToPlayer", "SetWalkSpeed", "Respawn" } do
		check(ids[id] ~= nil, `the debug menu has {id}`)
	end
	check(ids.ResetSave.Confirm and ids.UseLiveSaves.Confirm, "resetting a save and switching to live saves both ask first")

	local me = { Name = "Tester", UserId = 1 }
	local function run(id, args)
		return pcall(DebugActions.ById[id].Run, me, args or {}, me)
	end
	local ok, message = run("GivePass", { Pass = ids.GivePass.Params[1].Default })
	check(not ok and string.find(message, "no game passes yet", 1, true), "with no passes configured, giving one says so (and gives nothing)")
	ok, message = run("SimulateReceipt", { Product = ids.SimulateReceipt.Params[1].Default, GiftTo = 0 })
	check(not ok and string.find(message, "no products yet", 1, true), "with no products configured, simulating a receipt says so")
	check(#calls == 0, "...and neither touched the monetization systems")

	ok = run("ResetSave")
	check(ok and calls[#calls].name == "ResetToNew" and calls[#calls].args[1] == me, "resetting a save goes through PlayerData.ResetToNew")
	ok, message = run("ResetCodes")
	check(ok and message == "Forgot 2 redeemed codes for Tester", "resetting codes goes through CodeService.ResetRedeemed")
	ok = run("OfflineEarningsNow", { Seconds = 600 })
	check(ok and calls[#calls].name == "Pay" and calls[#calls].args[2] == 600, "offline earnings pay through OfflineEarnings.Pay(player, seconds)")
	ok, message = run("AnalyticsProgress")
	check(ok and string.find(message, "onboarding 3 of 0 (waiting: 5)", 1, true), "the funnel state reads the save's Funnels")
	ok = run("AnalyticsRestart")
	check(ok and liveData.Funnels.Onboarding == 0 and #liveData.Funnels.Waiting == 0, "starting the funnels again resets them with AnalyticsRules.New")

	ok = run("FreshSave", { State = "On" })
	check(ok and workspaceAttributes.StudioFreshSave == true, "the fresh-save switch sets StudioFreshSave in Studio")
	ok = run("FreshSave", { State = "Off" })
	check(ok and workspaceAttributes.StudioFreshSave == nil, "...and Off removes it")
	ok = run("FakeTimeAway", { Seconds = 3600 })
	check(ok and workspaceAttributes.StudioTimeAway == 3600, "fake time away sets StudioTimeAway")
	inStudio = false
	ok, message = run("UseLiveSaves", { State = "On" })
	check(not ok and message == "Studio only" and workspaceAttributes.StudioUseLiveSaves == nil, "outside Studio the test switches refuse")
	ok, message = run("FreshSave", { State = "On" })
	check(not ok and message == "Studio only", "...every one of them")

	-- Nothing from the old game is left in the menu.
	local source = string.lower(sources.DebugActions)
	for _, word in { "zoo", "steal", "rebirth", "trail", "egg", "gear", "zoodex", "tutorial", "safari", "mutation" } do
		check(string.find(source, word, 1, true) == nil, `DebugActions doesn't mention "{word}"`)
	end

	return passed
end
