-- Effects spec: EffectsConfig against the models (every attachment it names exists on its station in
-- BuildingModels, generated from the Blender pipeline), against the doc ("Effects and auras"), and the
-- performance rules (EffectsRules). Run: python tools/run_specs.py Effects
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local modules = {}
	local function loadPure(name)
		local chunk = assert(loadstring(sources[name], name))
		setfenv(chunk, setmetatable({
			game = { GetService = function()
				return modules
			end },
			script = { Parent = modules },
			require = function(module)
				return module
			end,
		}, { __index = getfenv(1) }))
		modules[name] = chunk()
		return modules[name]
	end
	for _, name in { "BuildingConfig", "EffectsConfig", "EffectsRules", "BuildingModels" } do
		loadPure(name)
	end
	local BuildingConfig, Effects, Rules, Models = modules.BuildingConfig, modules.EffectsConfig, modules.EffectsRules, modules.BuildingModels
	local text = sources["GAME_DESIGN.md"]

	-- Every attachment named for every building, tier and the Masterwork exists on that station.
	for _, building in BuildingConfig.Buildings do
		local model = Models.Buildings[building.Id]
		check(model ~= nil, building.Id .. " has its station models (BuildingModels)")
		for tier = 1, 5 do
			local station = model[tier]
			check(station ~= nil, `{building.Id} tier {tier} is built`)
			check(station.FitsPad, `{building.Id} tier {tier} fits its {building.Pad.Size}-stud pad`)
			local set = Effects.For(building.Id, tier, tier == 5)
			for _, group in { set.Ambient, set.Hit, set.Lights } do
				for _, effect in group do
					check(station.Attachments[effect.Attachment] ~= nil, `{building.Id} tier {tier}: {effect.Name} on {effect.Attachment}, which the model has`)
				end
			end
			for _, beam in set.Beams do
				check(station.Attachments[beam.From] ~= nil and station.Attachments[beam.To] ~= nil, `{building.Id} tier {tier}: beam {beam.Name} from {beam.From} to {beam.To}`)
			end
			check(#set.Lights <= Effects.Rules.MaxLightsPerBuilding, `{building.Id} tier {tier}: at most 2 lights`)
			check((set.Ring ~= nil) == (tier == 5), `{building.Id} tier {tier}: a ground ring only on the Legendary`)
			if set.Ring then
				check(station.Attachments[set.Ring.Spec.Attachment] ~= nil, `{building.Id} Legendary: its ground ring's {set.Ring.Spec.Attachment} point exists`)
			end
			for _, group in { set.Ambient, set.Hit } do
				for _, emitter in group do
					check(Effects.TextureFiles[emitter.Texture] ~= nil, `{emitter.Name} uses a shared texture ({emitter.Texture})`)
					check(type(emitter.Lifetime) == "table" and type(emitter.Size) == "table" and type(emitter.Color) == "table", `{emitter.Name} has lifetimes, sizes and colours`)
				end
			end
		end
		check(Effects.Signatures[building.Id] ~= nil and #Effects.Signatures[building.Id] >= 2, building.Name .. " (" .. building.LegendaryForm .. ") has a signature aura")
		check(Effects.BuildingColours[building.Id] ~= nil, building.Name .. " has an aura colour")
	end

	-- The tier layers follow the doc's table.
	check(#Effects.For("IceDrill", 1).Ambient == 0 and Effects.For("IceDrill", 1).Hit[1].Name == "Dust", "Scrappy: no ambient effects, a puff of dust on hits")
	local workshop = Effects.For("IceDrill", 2)
	check(workshop.Ambient[1].Name == "Steam" and workshop.Lights[1].Name == "Lantern", "Workshop: steam puffs and a warm lantern light")
	local names = {}
	for _, emitter in Effects.For("IceDrill", 4).Ambient do
		names[emitter.Name] = true
	end
	check(names.ColdMist and names.IceSparkles and names.AuraRing and names.Motes and names.Runes, "Enchanted keeps Frost-tech's mist and sparkles and adds the aura ring, motes and runes")
	local master = Effects.For("IceDrill", 5, true)
	local hasGold = false
	for _, emitter in master.Ambient do
		hasGold = hasGold or emitter.Name == "GoldAura"
	end
	check(hasGold, "a Masterwork adds a golden sparkle aura")

	-- Performance rules (the doc's numbers).
	check(string.find(text, "half rate within 60 studs and none beyond", 1, true) and Effects.Rules.OtherPlotDistance == 60 and Effects.Rules.OtherPlotRate == 0.5, "other plots: half rate within 60 studs")
	check(string.find(text, "At most 2 lights per building", 1, true) and Effects.Rules.MaxLightsPerBuilding == 2, "at most 2 lights per building")
	check(Rules.AmbientScale(true, 500, false) == 1, "your own plot: everything")
	check(Rules.AmbientScale(false, 59, false) == 0.5 and Rules.AmbientScale(false, 61, false) == 0, "another plot: half within 60 studs, none beyond")
	check(Rules.AmbientScale(true, 0, true) == 0.5, "reduced effects halve ambient particles")
	check(not Rules.HitsAllowed(true, 0, true) and Rules.HitsAllowed(true, 0, false) and not Rules.HitsAllowed(false, 80, false), "reduced effects: no hit effects; none on far plots")
	check(Rules.TierFor(0) == 0 and Rules.TierFor(1) == 1 and Rules.TierFor(24) == 2 and Rules.TierFor(25) == 3 and Rules.TierFor(100) == 5, "tiers at 1, 10, 25, 50, 100 owned")
	check(Rules.HitInterval(1) > Rules.HitInterval(50) and Rules.HitInterval(100) >= Effects.Rules.HitIntervalSeconds[2], "more copies hit faster, up to a cap")
	local bucket = Rules.NewHitBucket(8)
	local taken = 0
	for step = 0, 99 do
		if bucket:Take(step * 0.01) then
			taken += 1
		end
	end
	check(taken <= 8 + 8 + 1, "the hit cap holds: about 8 a second")

	-- The particle textures the doc names.
	for _, key in { "SoftGlow", "Sparkle", "Snowflake", "Ember", "SmokePuff", "Star", "WaterDroplet", "Rune1" } do
		check(Effects.TextureFiles[key] ~= nil, "the shared texture " .. key)
	end

	-- The click burst and "+N" at the cursor (TapFeedback)
	local burst = Effects.ClickBurst
	check(burst ~= nil, "EffectsConfig.ClickBurst exists")
	if burst then
		check(math.abs(burst.BurstSeconds - 0.25) < 0.05, "the burst lasts about 0.25 s")
		check(math.abs(burst.NumberSeconds - 0.7) < 0.1, "the number lasts about 0.7 s")
		check(burst.NumberDistance[1] == 30 and burst.NumberDistance[2] == 70, "the number appears 30-70 px from the click")
		check(burst.MaxNumbers >= 1 and burst.MaxNumbers <= 12, "at most about 12 numbers at once (a reused pool)")
		check(burst.MaxBursts >= 1 and burst.MaxBursts <= 12 and burst.Streaks >= 3, "a small pool of bursts, each with a few streaks")
		check(burst.PopScale > 1 and burst.Wobble > 0, "the number pops past full size and wobbles")
	end

	return passed
end
