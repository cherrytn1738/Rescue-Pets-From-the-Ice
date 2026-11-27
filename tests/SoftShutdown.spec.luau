--[[
Spec for the soft shutdown (src/server/SoftShutdown.luau), loaded with fakes: players, PlayerData,
TeleportService, Announcements, a clock and a task library that runs each thread step by step. Live
teleports can't run in Studio, so this is where the "save first, then move" order is checked.
Run: python tools/run_specs.py SoftShutdown
]]
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local clock = 0
	local steps = {} -- what happened, in order
	local function listeners()
		local list = {}
		return list, { Connect = function(_, fn)
			table.insert(list, fn)
		end }
	end
	local addedList, added = listeners()
	local removingList, removing = listeners()
	local players = {}
	local fakePlayers = {
		PlayerAdded = added,
		PlayerRemoving = removing,
		GetPlayers = function()
			return table.clone(players)
		end,
	}
	local teleportWorks = true
	local fakeTeleport = {
		TeleportAsync = function(_, placeId, list, options)
			if not teleportWorks then
				error("teleport failed")
			end
			table.insert(steps, { "Teleport", placeId, #list, options })
			for _, player in list do
				local index = table.find(players, player)
				if index then
					table.remove(players, index)
				end
				for _, fn in removingList do
					fn(player)
				end
			end
		end,
	}
	local workspaceAttributes = {}
	local fakeWorkspace = {
		SetAttribute = function(_, key, value)
			workspaceAttributes[key] = value
		end,
	}
	local isStudio = false
	local closeFn, restartSignal = nil, nil
	local fakeGame = {
		PrivateServerId = "",
		PrivateServerOwnerId = 0,
		PlaceId = 88645847284794,
		GetService = function(_, name)
			return ({
				Players = fakePlayers,
				RunService = { IsStudio = function()
					return isStudio
				end },
				TeleportService = fakeTeleport,
				Workspace = fakeWorkspace,
			})[name]
		end,
		BindToClose = function(_, fn)
			closeFn = fn
		end,
		ServerRestartScheduled = { Connect = function(_, fn)
			restartSignal = fn
		end },
	}
	local marked, shown = {}, {}
	local parent = {
		PlayerData = {
			CloseAll = function(seconds)
				table.insert(steps, { "CloseAll", seconds })
				return true
			end,
			MarkImportant = function(player)
				table.insert(marked, player)
			end,
		},
		Announcements = { Show = function(title, text)
			table.insert(shown, title .. ": " .. text)
		end },
	}
	local threads = {}
	local fakeTask = {
		wait = function(seconds)
			clock += seconds or 0
			coroutine.yield()
		end,
		spawn = function(fn, ...)
			table.insert(threads, coroutine.create(fn))
		end,
		delay = function(seconds, fn)
			table.insert(threads, coroutine.create(function()
				clock += seconds
				fn()
			end))
		end,
	}
	local fakeInstance = { new = function(class)
		assert(class == "TeleportOptions", "unexpected Instance " .. class)
		local options = {}
		function options:SetTeleportData(data)
			self.Data = data
		end
		return options
	end }
	local chunk = assert(loadstring(sources.SoftShutdown, "SoftShutdown"))
	setfenv(chunk, setmetatable({
		game = fakeGame,
		script = { Parent = parent },
		require = function(module)
			return module
		end,
		task = fakeTask,
		os = { clock = function()
			return clock
		end, time = function()
			return 1_000_000
		end },
		Instance = fakeInstance,
		print = function() end,
		warn = function(text)
			table.insert(steps, { "warn", text })
		end,
	}, { __index = getfenv(1) }))
	local SoftShutdown = chunk()

	-- Pure rules ----------------------------------------------------------------------------------------
	check(SoftShutdown.Plan("DeveloperShutdown", false, 3) == "Hop", "Shut Down All Servers, live: save and hop through a holding server")
	check(SoftShutdown.Plan("DeveloperShutdown", true, 3) == "StudioLog", "...in Studio (pressing Stop): save and log only")
	check(SoftShutdown.Plan("DeveloperUpdate", false, 3) == "Message" and SoftShutdown.Plan("RobloxMaintenance", false, 1) == "Message",
		"Restart Servers / maintenance: Roblox moves the players; save and show the screen")
	for _, reason in { "ServerEmpty", "OutOfMemory", "Moderation", "Unknown" } do
		check(SoftShutdown.Plan(reason, false, 3) == "None", `{reason}: nothing extra`)
	end
	check(SoftShutdown.Plan("DeveloperShutdown", false, 0) == "None", "an empty server: nothing")
	check(SoftShutdown.IsHolding("abc", 0) and not SoftShutdown.IsHolding("", 0) and not SoftShutdown.IsHolding("abc", 123),
		"a holding server is a reserved server with no owner (never a public or a bought private server)")
	check(SoftShutdown.ScheduledText(300) == "This server restarts for an update in 5 minutes. Your progress is saved, and you'll come straight back.", "the warning text")
	check(string.find(SoftShutdown.ScheduledText(61), "in 2 minutes", 1, true) and string.find(SoftShutdown.ScheduledText(20), "in 1 minute.", 1, true),
		"minutes round up, one minute is singular")

	-- Closing a live server -----------------------------------------------------------------------------
	SoftShutdown.Start()
	check(type(closeFn) == "function" and type(restartSignal) == "function", "Start binds to close and listens for scheduled restarts")
	local function runToEnd(fn, ...)
		local thread = coroutine.create(fn)
		local ok, problem = coroutine.resume(thread, ...)
		assert(ok, problem)
		while coroutine.status(thread) ~= "dead" do
			ok, problem = coroutine.resume(thread)
			assert(ok, problem)
		end
	end

	players = { { Name = "A" }, { Name = "B" } }
	runToEnd(closeFn, Enum.CloseReason.DeveloperShutdown)
	check(workspaceAttributes.SoftShutdown == SoftShutdown.Message, "everyone sees the update screen")
	check(#steps == 2 and steps[1][1] == "CloseAll" and steps[2][1] == "Teleport", "every save is written and released BEFORE anyone moves")
	local teleport = steps[2]
	check(teleport[2] == fakeGame.PlaceId and teleport[3] == 2 and teleport[4].ShouldReserveServer == true and teleport[4].Data.SoftShutdown == true,
		"...then everyone goes together to one new reserved server of this place")
	check(#players == 0, "...and the server waits for them to leave")

	table.clear(steps)
	players = { { Name = "A" } }
	teleportWorks = false
	runToEnd(closeFn, Enum.CloseReason.DeveloperShutdown)
	local warnings = 0
	for _, step in steps do
		if step[1] == "warn" then
			warnings += 1
		end
	end
	check(steps[1][1] == "CloseAll" and warnings == 3, "a failing teleport is tried 3 times and logged (the save is already done)")
	teleportWorks = true

	table.clear(steps)
	workspaceAttributes.SoftShutdown = nil
	players = { { Name = "A" } }
	runToEnd(closeFn, Enum.CloseReason.DeveloperUpdate)
	check(#steps == 1 and steps[1][1] == "CloseAll" and workspaceAttributes.SoftShutdown ~= nil, "Restart Servers: save and show the screen; no teleport of our own")

	table.clear(steps)
	workspaceAttributes.SoftShutdown = nil
	runToEnd(closeFn, Enum.CloseReason.ServerEmpty)
	check(#steps == 0 and workspaceAttributes.SoftShutdown == nil, "any other reason: nothing")

	-- A delayed restart: a warning now and at one minute, every save marked
	players = { { Name = "A" }, { Name = "B" } }
	threads = {}
	restartSignal(DateTime.fromUnixTimestamp(1_000_000 + 300), Enum.CloseReason.DeveloperUpdate)
	check(#marked == 2 and #shown == 1 and string.find(shown[1], "in 5 minutes", 1, true), "a scheduled restart warns everyone and marks their saves")
	check(#threads == 1, "...and plans the one-minute warning")
	runToEnd(function()
		coroutine.resume(threads[1])
	end)
	check(#shown == 2 and string.find(shown[2], "in 1 minute.", 1, true), "the one-minute warning")

	-- The holding server -----------------------------------------------------------------------------------
	table.clear(steps)
	threads = {}
	workspaceAttributes.SoftShutdown = nil
	players = { { Name = "A" } }
	clock = 0
	SoftShutdown.RunHoldingServer()
	check(workspaceAttributes.SoftShutdown == SoftShutdown.Message, "the holding server shows the update screen")
	check(#addedList == 1 and #threads == 1, "it watches arrivals and runs one sending loop")
	local loop = threads[1]
	coroutine.resume(loop) -- 1 s
	check(#steps == 0, "nobody is sent back straight away")
	local late = { Name = "Late" }
	table.insert(players, late)
	addedList[1](late)
	for _ = 1, 5 do
		coroutine.resume(loop)
	end
	check(#steps == 1 and steps[1][1] == "Teleport" and steps[1][2] == fakeGame.PlaceId and steps[1][3] == 1 and steps[1][4] == nil,
		"after 5 s the first player goes back to a public server of this place")
	coroutine.resume(loop)
	check(#steps == 2 and steps[2][3] == 1, "...and the late arrival 5 s after they came")
	check(#players == 0, "everyone has left the holding server")

	return passed
end
