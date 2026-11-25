-- SoundRules spec: when the game's sounds play (src/replicated/SoundRules.luau, settings in
-- AudioConfig.Rules): the tap-sound cap against an autoclicker, the other-plot rescue jingle rule (rarity
-- and distance), the building chip, the income tick and variant picking; plus AudioConfig's own entries.
-- Run: python tools/run_specs.py SoundRules
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end
	local function load(name)
		return assert(loadstring(sources[name], name))()
	end
	local SoundRules = load("SoundRules")
	local AudioConfig = load("AudioConfig")
	local RULES = AudioConfig.Rules

	-- The tap cap ---------------------------------------------------------------------------------------
	-- An autoclicker at 100 taps a second for 3 seconds: never more than MaxOverlap tap sounds at once,
	-- never two closer than MinGap, and the taps still sound (most of the time there is one playing).
	local tap = RULES.Tap
	check(tap.MaxOverlap >= 1 and tap.MaxOverlap <= 4, "a small overlap cap")
	local limiter = SoundRules.TapLimiter(tap)
	local played, lastAt, mostAtOnce = 0, -math.huge, 0
	for i = 0, 299 do
		local now = i / 100
		if limiter:Allow(now) then
			played += 1
			check(now - lastAt >= tap.MinGap - 1e-9, "taps sound at least MinGap apart")
			lastAt = now
		end
		mostAtOnce = math.max(mostAtOnce, limiter:Playing(now))
	end
	check(mostAtOnce <= tap.MaxOverlap, `at most {tap.MaxOverlap} tap sounds at once (saw {mostAtOnce})`)
	check(played <= 3 / tap.MinGap + 1, "an autoclicker can't play more than one sound per MinGap")
	check(played >= 3 * tap.MaxOverlap / tap.Length * 0.5, `fast tapping still sounds ({played} in 3 s)`)
	-- a normal fast player (8 taps a second) hears every tap
	local human = SoundRules.TapLimiter(tap)
	local heard = 0
	for i = 0, 23 do
		if human:Allow(i / 8) then
			heard += 1
		end
	end
	check(heard == 24, "every tap sounds at 8 taps a second")
	-- a crazy burst at one instant gives one sound, not dozens
	local burst = SoundRules.TapLimiter(tap)
	local inBurst = 0
	for _ = 1, 50 do
		if burst:Allow(10) then
			inBurst += 1
		end
	end
	check(inBurst == 1, "50 taps in the same frame play one sound")
	-- the streak pitch
	check(SoundRules.TapSpeed(0, tap) == 1, "a single tap at normal pitch")
	check(math.abs(SoundRules.TapSpeed(tap.StreakMax, tap) - (1 + tap.StreakPitch)) < 1e-9, "a long streak at most StreakPitch higher")
	check(SoundRules.TapSpeed(tap.StreakMax * 5, tap) == SoundRules.TapSpeed(tap.StreakMax, tap), "the streak pitch is capped")
	check(tap.StreakPitch <= 0.15, "the streak lift stays small")

	-- Rescue jingles: own plot always, other plots only the rarest, nearby, quieter -------------------------
	local other = RULES.OtherPlots
	check(other.MaxDistance == 60, "other plots are heard within 60 studs")
	check(other.Volume > 0 and other.Volume < 1, "other plots' jingles are quieter")
	for _, rarity in { "Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic" } do
		local cue, volume = SoundRules.RescueCue(true, rarity, 500, other)
		check(cue == "Rescue" .. rarity and volume == 1, `your own {rarity} jingle always plays, at full volume, at any distance`)
		check(AudioConfig.Sfx[cue] ~= nil, `a jingle for {rarity}`)
		local near = SoundRules.RescueCue(false, rarity, 10, other)
		local rare = rarity == "Legendary" or rarity == "Mythic"
		check((near ~= nil) == rare, `another plot's {rarity} jingle {if rare then "plays" else "is silent"} nearby`)
	end
	local cue, volume = SoundRules.RescueCue(false, "Mythic", 60, other)
	check(cue == "RescueMythic" and volume == other.Volume, "another plot's Mythic at exactly 60 studs, quieter")
	check(SoundRules.RescueCue(false, "Mythic", 60.5, other) == nil, "...and not past 60 studs")
	check(SoundRules.RescueCue(false, "Legendary", 0 / 0, other) == nil, "an unknown distance is silent")
	check(SoundRules.RescueCue(true, nil, 0, other) == nil, "no rarity, no jingle")
	-- jingles grow grander: each rarity's jingle at least as loud as the one below
	local lastVolume = 0
	for _, rarity in { "Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic" } do
		check(AudioConfig.Sfx["Rescue" .. rarity].Volume >= lastVolume, `{rarity}'s jingle isn't quieter than the rarity below`)
		lastVolume = AudioConfig.Sfx["Rescue" .. rarity].Volume
	end

	-- Building chips: own plot only, occasional, never right after a tap ----------------------------------
	local chips = RULES.BuildingChip
	local always = function()
		return 0
	end
	local gate = SoundRules.ChipGate(chips, always)
	check(not gate:Allow(100, false, nil), "never a chip from another plot")
	local chipCount = 0
	for i = 0, 999 do -- a building hitting your block 10 times a second for 100 seconds
		if gate:Allow(i / 10, true, nil) then
			chipCount += 1
		end
	end
	check(chipCount <= 100 / chips.MinGap + 1, `at most one chip every {chips.MinGap} s ({chipCount} in 100 s)`)
	check(chipCount >= 1, "chips do happen")
	local quiet = SoundRules.ChipGate(chips, always)
	check(not quiet:Allow(50, true, 50 - chips.QuietAfterTap / 2), "no chip just after your own tap")
	check(quiet:Allow(50, true, 50 - chips.QuietAfterTap - 0.01), "...a chip once the tap is past")
	local never = SoundRules.ChipGate(chips, function()
		return 0.999
	end)
	check(not never:Allow(10, true, nil), "a failed chance plays nothing")
	check(chips.Chance > 0 and chips.Chance < 1, "chips are a chance, not every gap")
	check(AudioConfig.Sfx.BuildingChip.Volume <= AudioConfig.Sfx.Tap.Volume / 2, "a chip is much quieter than a tap")

	-- The income tick -------------------------------------------------------------------------------------
	local tick = SoundRules.TickGate(RULES.CrystalTick, always)
	local ticks = 0
	for i = 0, 99 do -- crystals rising 4 times a second for 25 seconds (and every chance taken)
		if tick:Allow(i / 4, nil) then
			ticks += 1
		end
	end
	check(ticks <= 25 / RULES.CrystalTick.MinGap + 1, "the income tick is occasional")
	check(RULES.CrystalTick.Chance > 0 and RULES.CrystalTick.Chance < 1, "...and a chance, so it isn't a clock")
	local unlucky = SoundRules.TickGate(RULES.CrystalTick, function()
		return 0.999
	end)
	check(not unlucky:Allow(5, nil) and not unlucky:Allow(5 + RULES.CrystalTick.MinGap / 2, nil), "a missed chance waits a full gap")
	check(not SoundRules.TickGate(RULES.CrystalTick, always):Allow(10, 9.9), "no tick while tapping")
	check(AudioConfig.Sfx.CrystalTick.Volume <= 0.1, "the income tick is very soft")

	-- Variants never repeat back to back ----------------------------------------------------------------
	local seed = 7
	local function random(n)
		seed = (seed * 1103515245 + 12345) % 2147483648
		return seed % n + 1
	end
	local last = nil
	local seen = {}
	for _ = 1, 200 do
		local pick = SoundRules.PickVariant(4, last, random)
		check(pick >= 1 and pick <= 4 and pick ~= last, "a variant in range, never the last one again")
		seen[pick] = true
		last = pick
	end
	check(#seen == 4, "every variant gets played")
	check(SoundRules.PickVariant(1, 1, random) == 1, "one variant always plays")

	-- AudioConfig's entries -----------------------------------------------------------------------------
	local ids = {}
	for name, soundId in AudioConfig.Files do
		check(string.match(soundId, "^rbxassetid://%d+$") ~= nil, `{name} has a real asset id`)
		check(not ids[soundId], `{name}'s id is its own`)
		ids[soundId] = true
	end
	for listName, list in { Sfx = AudioConfig.Sfx, Ui = AudioConfig.Ui } do
		for name, entry in list do
			local entryIds = entry.Ids or { entry.Id }
			check(#entryIds >= 1, `{listName}.{name} has a sound`)
			for _, soundId in entryIds do
				check(ids[soundId], `{listName}.{name} uses an uploaded file`)
			end
			check(type(entry.Volume) == "number" and entry.Volume > 0 and entry.Volume <= 1, `{listName}.{name} has a volume in 0..1`)
			check((entry.PitchJitter or 0) <= 0.1, `{listName}.{name} jitters its pitch only a little`)
		end
	end
	check(#AudioConfig.Sfx.Tap.Ids >= 3 and (AudioConfig.Sfx.Tap.PitchJitter or 0) > 0, "taps have variants and a random pitch")
	for _, name in { "Click", "Locked", "Open", "Close", "Invalid" } do
		check(AudioConfig.Ui[name] ~= nil, `the UI kit's {name} sound`)
	end
	for stage = 1, 4 do
		check(AudioConfig.Sfx["Crack" .. stage] ~= nil, `crack stage {stage} has a sound`)
	end
	for _, name in { "Shatter", "GoldenSparkle", "BuyBuilding", "BuyUpgrade", "Rebirth", "BookPage", "BookNew", "Heartbeat", "GoldenAlarm" } do
		check(AudioConfig.Sfx[name] ~= nil, `the {name} sound`)
	end
	-- music: two slots, empty until chosen
	for _, name in { "Plaza", "Plot" } do
		local track = AudioConfig.Music[name]
		check(track and type(track.Id) == "string" and track.Volume > 0 and track.Volume <= 1, `the {name} music slot`)
	end
	check(AudioConfig.Music.FadeSeconds > 0, "music crossfades")

	return passed
end
