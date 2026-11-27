-- Spec for the admin window (F3): its access rules (src/server/AdminRules.luau and AdminConfig) with
-- fake players and fake commands, and the real command list (AdminCommands) loaded with a fake
-- PlayerEffects. Run: python tools/run_specs.py Admin
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local modules = {}
	local function load(name)
		local chunk = assert(loadstring(sources[name], name))
		setfenv(chunk, setmetatable({
			game = { GetService = function(_, service) return modules[service] or modules end, PrivateServerId = "", PlaceVersion = 0, JobId = "" },
			script = { Parent = modules },
			require = function(module)
				return module
			end,
		}, { __index = getfenv() }))
		modules[name] = chunk()
		return modules[name]
	end
	load("DebugRules")
	local AdminRules = load("AdminRules")
	local AdminConfig = load("AdminConfig")

	-- The allowlist ---------------------------------------------------------------------------------
	local DEVELOPER = 11704150663
	check(#AdminConfig.AllowedUserIds == 1 and AdminConfig.AllowedUserIds[1] == DEVELOPER, "the allowlist holds only the developer's user id")
	check(AdminRules.Access(DEVELOPER, false, AdminConfig.AllowedUserIds) == "Developer", "live server: the developer has every command")
	check(AdminRules.Access(123, false, AdminConfig.AllowedUserIds) == nil, "live server: anyone else has none")
	check(AdminRules.Access(-1, false, AdminConfig.AllowedUserIds) == nil, "live server: a Studio test id is nobody")
	check(AdminRules.Access(tostring(DEVELOPER), false, AdminConfig.AllowedUserIds) == nil, "a user id that isn't a number never matches")
	check(AdminRules.Access(DEVELOPER, false, nil) == nil, "a missing allowlist means nobody")
	check(AdminRules.Access(123, true, {}) == "Developer" and AdminRules.Access(-2, true, {}) == "Developer", "Studio: everyone, test players included")

	-- Fake world ----------------------------------------------------------------------------------------
	local runs = {}
	local function command(id, extra)
		local entry = {
			Id = id, Group = "Test", Label = id, Params = {}, NoTarget = true,
			Run = function(target, args, caller)
				table.insert(runs, { id = id, target = target, args = args, caller = caller })
				return "done " .. id
			end,
		}
		for key, value in extra or {} do
			entry[key] = value
		end
		return entry
	end
	local list = {
		command("Count", { Params = { { Name = "Count", Label = "Count", Kind = "number", Min = 1, Max = 40, Integer = true, Default = 15 } } }),
		command("Launch", { NoTarget = false }),
		command("Big", { Confirm = true }),
		command("Broken", { Run = function() error("nothing to launch", 0) end }),
	}
	local byId = {}
	for _, entry in list do
		byId[entry.Id] = entry
	end
	local developer = { Name = "Dev", UserId = DEVELOPER }
	local stranger = { Name = "Stranger", UserId = 777 }
	local victim = { Name = "Victim", UserId = 999 }
	local logs = {}
	local function env(isStudio, clock)
		return {
			isStudio = isStudio,
			allowlist = AdminConfig.AllowedUserIds,
			commands = byId,
			now = clock,
			lastRequestAt = {},
			cooldown = AdminConfig.RequestCooldownSeconds,
			findTarget = function(userId)
				return if userId == victim.UserId then victim elseif userId == developer.UserId then developer else nil
			end,
			log = function(text)
				table.insert(logs, text)
			end,
		}
	end
	local live = env(false, 100)
	local function send(environment, player, id, target, args, confirmed)
		environment.now += 1 -- past the cooldown
		return AdminRules.Handle({ player = player, commandId = id, targetUserId = target, args = args, confirmed = confirmed }, environment)
	end

	-- Live server: the developer -------------------------------------------------------------------------
	local reply = send(live, developer, "Count", nil, { Count = 20 })
	check(reply.ok and runs[#runs].id == "Count" and runs[#runs].args.Count == 20 and runs[#runs].caller == developer, "the developer runs a command in a live server")
	check(string.find(logs[#logs], "[Admin] Dev ran Count", 1, true) ~= nil, "...and it's logged")
	reply = send(live, developer, "Count", nil, {})
	check(reply.ok and runs[#runs].args.Count == 15, "a missing input gets its default")
	check(not send(live, developer, "Count", nil, { Count = 41 }).ok and not send(live, developer, "Count", nil, { Count = 2.5 }).ok, "inputs out of range are refused")
	check(not send(live, developer, "Count", nil, "junk").ok, "inputs that aren't a table are refused")
	check(not send(live, developer, "Nope", nil, nil).ok and not send(live, developer, nil, nil, nil).ok, "an unknown command is refused")
	reply = send(live, developer, "Launch", victim.UserId, nil)
	check(reply.ok and runs[#runs].target == victim, "a player command gets its target")
	check(not send(live, developer, "Launch", 4242, nil).ok, "a target who isn't in the server is refused")
	check(not send(live, developer, "Big", nil, nil).ok and send(live, developer, "Big", nil, nil, true).ok, "a command that asks first needs confirming")
	reply = send(live, developer, "Broken", nil, nil)
	check(not reply.ok and reply.message == "nothing to launch", "a command's refusal comes back as its message")
	local before = #runs
	live.now += 0.1
	reply = AdminRules.Handle({ player = developer, commandId = "Count", args = {} }, live)
	check(not reply.ok and reply.message == "Too fast" and #runs == before, "requests faster than the cooldown are refused")

	-- Live server: everyone else ------------------------------------------------------------------------
	before = #runs
	local logCount = #logs
	reply = send(live, stranger, "Count", nil, { Count = 5 })
	check(not reply.ok and reply.message == "No access" and #runs == before, "a player who isn't on the allowlist is rejected; nothing runs")
	check(#logs == logCount + 1 and string.find(logs[#logs], "REJECTED Stranger (777) tried Count", 1, true) ~= nil, "...and the attempt is logged")
	reply = send(live, stranger, "Launch", victim.UserId, nil)
	check(not reply.ok and #runs == before, "...for every command")
	check(#AdminRules.Catalog(list, AdminRules.Access(stranger.UserId, false, AdminConfig.AllowedUserIds)) == 0, "...and is shown no commands")
	local catalog = AdminRules.Catalog(list, "Developer")
	check(#catalog == #list and catalog[1].Run == nil, "the developer sees every command, without their code")

	-- Studio -------------------------------------------------------------------------------------------
	local studio = env(true, 500)
	reply = send(studio, stranger, "Count", nil, { Count = 3 })
	check(reply.ok and runs[#runs].caller == stranger, "in Studio everyone may run admin commands")
	reply = send(studio, { Name = "Player1", UserId = -1 }, "Big", nil, nil, true)
	check(reply.ok, "...including a Studio test player")

	-- The real command list, with a fake PlayerEffects --------------------------------------------------
	local effects = { busy = nil, done = {} }
	modules.PlayerEffects = {
		Busy = function()
			return effects.busy
		end,
		Launch = function(target)
			table.insert(effects.done, "Launch " .. target.Name)
		end,
		Rocket = function(target)
			table.insert(effects.done, "Rocket " .. target.Name)
		end,
		Jail = function(target)
			table.insert(effects.done, "Jail " .. target.Name)
		end,
	}
	modules.Players = { GetPlayers = function() return { developer } end, MaxPlayers = 12 }
	modules.Workspace = { DistributedGameTime = 125 }
	local shown, broadcast = {}, {}
	local filterWorks, broadcastWorks = true, true
	modules.Announcements = {
		Show = function(title, text)
			table.insert(shown, title .. ": " .. text)
		end,
		Broadcast = function(title, text)
			if not broadcastWorks then
				return false, "MessagingService is down"
			end
			table.insert(broadcast, title .. ": " .. text)
			return true, nil
		end,
	}
	modules.RunService = { IsStudio = function()
		return false
	end }
	modules.TextService = { FilterStringAsync = function(_, text, userId)
		if not filterWorks then
			error("filter unavailable")
		end
		return { GetNonChatStringForBroadcastAsync = function()
			return `filtered({userId}): {text}`
		end }
	end }
	local AdminCommands = load("AdminCommands")
	for _, id in { "ServerInfo", "Announce", "AnnounceAll", "Launch", "Rocket", "Jail", "Kick" } do
		check(AdminCommands.ById[id] ~= nil, `the admin window has {id}`)
	end
	check(AdminCommands.ById.Kick.Confirm == true, "kicking asks first")
	local ok, message = pcall(AdminCommands.ById.Launch.Run, victim, {}, developer)
	check(ok and effects.done[#effects.done] == "Launch Victim", "Launch goes through PlayerEffects")
	effects.busy = "jailed"
	ok, message = pcall(AdminCommands.ById.Rocket.Run, victim, {}, developer)
	check(not ok and message == "Victim is jailed right now; try again in a moment", "one effect at a time per target")
	effects.busy = nil
	ok, message = pcall(AdminCommands.ById.Kick.Run, developer, {}, developer)
	check(not ok and string.find(message, "yourself", 1, true), "the developer can't kick themselves")
	local kicked = nil
	ok = pcall(AdminCommands.ById.Kick.Run, { Name = "Victim", Kick = function(_, why) kicked = why end }, {}, developer)
	check(ok and type(kicked) == "string", "Kick removes the target with a message")
	ok, message = pcall(AdminCommands.ById.ServerInfo.Run)
	check(ok and string.find(message, "1 / 12 players, up 2 min 5 s", 1, true), "server info reports players and uptime")

	-- Announcements: developer only (the allowlist above), filtered, confirmed first
	local announce, announceAll = AdminCommands.ById.Announce, AdminCommands.ById.AnnounceAll
	check(announce.NoTarget and announce.Confirm and announceAll.NoTarget and announceAll.Confirm, "both announcements ask first and go to everyone")
	local DebugRules = modules.DebugRules
	local args = DebugRules.ValidateArgs(announce.Params, { Text = "Double crystals weekend!" })
	check(args and args.Text == "Double crystals weekend!", "a normal message passes the input check")
	check(DebugRules.ValidateArgs(announce.Params, { Text = string.rep("a", 151) }) == nil, "...a message over 150 characters doesn't")
	check(DebugRules.ValidateArgs(announce.Params, { Text = "" }) == nil and DebugRules.ValidateArgs(announce.Params, { Text = "line\nbreak" }) == nil, "...nor an empty one or a line break")
	ok, message = pcall(announce.Run, nil, args, developer)
	check(ok and shown[#shown] == `ANNOUNCEMENT: filtered({DEVELOPER}): Double crystals weekend!` and string.find(message, "1 player", 1, true),
		"Announce shows the FILTERED text to this server")
	ok = pcall(announceAll.Run, nil, args, developer)
	check(ok and broadcast[#broadcast] == `ANNOUNCEMENT: filtered({DEVELOPER}): Double crystals weekend!`, "AnnounceAll publishes the filtered text to every server")
	broadcastWorks = false
	ok, message = pcall(announceAll.Run, nil, args, developer)
	check(not ok and string.find(message, "MessagingService is down", 1, true), "...and says so when publishing fails")
	filterWorks = false
	local before = #shown
	ok, message = pcall(announce.Run, nil, args, developer)
	check(not ok and #shown == before and string.find(message, "filter", 1, true), "live, an unfiltered message is never shown")

	-- Nothing from the old game is left -------------------------------------------------------------------
	for _, name in { "AdminCommands", "AdminService", "PlayerEffects", "AdminConfig" } do
		local source = string.lower(sources[name])
		for _, word in { "zoo", "steal", "pet", "trail", "egg", "gear", "ragdoll", "mutation", "abuse", "panel" } do
			check(string.find(source, word, 1, true) == nil, `{name} doesn't mention "{word}"`)
		end
	end

	return passed
end
