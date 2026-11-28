-- Teleport spec: the PLOT button's request (TeleportRules, GameConfig.Teleport): a short cooldown, and nothing for a
-- player without a plot, without a live character, or jailed.
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end

	local GameConfig = assert(loadstring(sources.GameConfig, "GameConfig"))()
	local TeleportRules = assert(loadstring(sources.TeleportRules, "TeleportRules"))()
	local settings = GameConfig.Teleport
	check(settings.CooldownSeconds >= 2 and settings.CooldownSeconds <= 5, "about a 3-second cooldown")
	check(settings.StreamSeconds > 0 and settings.StreamSeconds <= 5, "the plot streams in before landing, briefly")
	check(settings.PoofRange > 0, "nearby players see the poof")

	local cooldown = settings.CooldownSeconds
	local function request(changes)
		local r = { now = 100, lastAt = nil, hasPlot = true, alive = true, jailed = false }
		for k, v in changes or {} do
			r[k] = v
		end
		return r
	end
	check(TeleportRules.Check(request(), cooldown), "a player with a plot and a live character goes")
	check(TeleportRules.Check(request({ lastAt = 100 - cooldown }), cooldown), "...again once the cooldown is over")
	local ok, reason = TeleportRules.Check(request({ lastAt = 100 - cooldown + 0.5 }), cooldown)
	check(not ok and reason == "cooldown", "not within the cooldown")
	ok, reason = TeleportRules.Check(request({ hasPlot = false }), cooldown)
	check(not ok and reason == "no plot", "not without a plot")
	ok, reason = TeleportRules.Check(request({ alive = false }), cooldown)
	check(not ok and reason == "no character", "not while dead or without a character")
	ok, reason = TeleportRules.Check(request({ jailed = true }), cooldown)
	check(not ok and reason == "jailed", "not out of the admin's jail")

	return passed
end
