-- SwingConfig spec: each tool family's swing (variants, keyframes, timing, impact, grip) and the fast-tapping rules
-- (PickSwing.client).
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end

	local SwingConfig = assert(loadstring(sources.SwingConfig))()
	local BuildingConfig = assert(loadstring(sources.BuildingConfig))()
	local chunk = assert(loadstring(sources.UpgradeConfig, "UpgradeConfig"))
	setfenv(chunk, setmetatable({
		script = { Parent = { BuildingConfig = BuildingConfig } },
		require = function(module)
			return module
		end,
	}, { __index = getfenv(1) }))
	local UpgradeConfig = chunk()

	-- Every tool's family has a swing; the five families all appear
	check(#SwingConfig.FamilyOrder == 5, "five families")
	for _, tool in UpgradeConfig.Tools do
		check(SwingConfig.Families[tool.Family] ~= nil, tool.Name .. ": its family (" .. tool.Family .. ") has a swing")
	end

	local function checkAnimation(name, length)
		local frames = SwingConfig.R15[name]
		check(type(frames) == "table" and #frames >= 3, name .. " has keyframes")
		local time = -1
		for _, frame in frames do
			check(frame.Time > time and frame.Time <= length + 1e-6, name .. ": keyframes in order, inside the swing")
			time = frame.Time
			for part, entry in frame.Poses do
				check(SwingConfig.R15Parents[part] ~= nil, `{name}: {part} is a joint in the R15 tree`)
				check(type(entry[1]) == "number" and type(entry[2]) == "number" and type(entry[3]) == "number", `{name}: {part} has three angles`)
				check(typeof(SwingConfig.PoseCFrame(entry)) == "CFrame", `{name}: {part} makes a CFrame`)
			end
		end
		check(frames[1].Time == 0 and math.abs(frames[#frames].Time - length) < 1e-6, name .. " starts at 0 and lasts the whole swing")
		local id = SwingConfig.AnimationIds.R15[name]
		check(type(id) == "number" and id >= 0 and id % 1 == 0, name .. " has an animation id (0 = not uploaded)")
		return frames
	end

	for _, familyName in SwingConfig.FamilyOrder do
		local family = SwingConfig.Families[familyName]
		check(#family.Variants >= 2 and #family.Variants <= 3, familyName .. ": two or three variants")
		check(family.WindUpEnd < family.ImpactAt and family.ImpactAt < family.Length, familyName .. ": wind-up, then the strike, then the rest")
		check(family.Nudge.Strength > 0 and family.Nudge.Strength < 0.5, familyName .. ": the camera nudge stays small")
		check(family.Impact.Chips > 0 and family.Impact.ChipSize > 0 and family.Impact.Sparks > 0, familyName .. ": an impact burst")
		check(typeof(family.Grip) == "CFrame", familyName .. ": a grip")

		-- Variants take turns: never the same twice running, every one comes up
		local seen, previous = {}, nil
		for _ = 1, 9 do
			local nextOne = SwingConfig.NextVariant(family, previous)
			check(nextOne ~= previous, familyName .. ": the same variant never plays twice running")
			seen[nextOne] = true
			previous = nextOne
		end
		for _, name in family.Variants do
			check(seen[name], familyName .. ": " .. name .. " comes up in turn")
		end

		-- Fast tapping speeds the swing up instead of queueing; a slow tap plays at normal speed
		check(SwingConfig.SpeedFor(family, nil) == 1 and SwingConfig.SpeedFor(family, family.Length + 1) == 1, familyName .. ": an unhurried tap, normal speed")
		check(SwingConfig.SpeedFor(family, family.Length / 2) > 1, familyName .. ": a tap halfway through a swing, faster")
		check(SwingConfig.SpeedFor(family, 0.01) == family.MaxSpeed and family.MaxSpeed <= 3, familyName .. ": very fast tapping is capped at MaxSpeed")
		local last = 0
		for _, gap in { 0.5, 0.3, 0.2, 0.1, 0.05 } do
			local speed = SwingConfig.SpeedFor(family, gap)
			check(speed >= last, familyName .. ": quicker taps never play slower")
			last = speed
		end

		-- The keyframes: in order, inside the swing, starting and ending at the hold, the strike at ImpactAt
		for _, name in family.Variants do
			local frames = checkAnimation(name, family.Length)
			local first, final = frames[1].Poses, frames[#frames].Poses
			for part, entry in first do
				local other = final[part]
				check(other and other[1] == entry[1] and other[2] == entry[2] and other[3] == entry[3], `{name}: {part} ends where it starts (the hold)`)
			end
			local strike = false
			for _, frame in frames do
				if math.abs(frame.Time - family.ImpactAt) < 1e-6 then
					strike = true
				end
			end
			check(strike, name .. " has its strike keyframe at ImpactAt (the camera nudge)")
			check(frames[1].Poses.LeftUpperLeg == nil, name .. " leaves the legs free (the family's Dip bends the knees)")
		end
		local dip = SwingConfig.R15[family.Dip]
		check(dip ~= nil and dip[1].Poses.LeftUpperLeg ~= nil, familyName .. ": its dip moves the legs")
		checkAnimation(family.Dip, SwingConfig.LengthOf(family.Dip))
	end

	-- The family feel: the hammer is slower and hits harder, the sword quicker, swords trail
	local families = SwingConfig.Families
	check(families.Hammer.Length > families.Pick.Length and families.Hammer.ImpactAt > families.Pick.ImpactAt, "the hammer winds up slower")
	check(families.Hammer.Nudge.Strength > families.Pick.Nudge.Strength and families.Hammer.Impact.Chips > families.Pick.Impact.Chips
		and families.Hammer.Impact.ChipSize > 1, "...and lands a bigger impact (a stronger nudge, chunkier chips)")
	check(families.Sword.Length < families.Pick.Length and #families.Sword.Variants == 3 and families.Sword.Trail, "the sword: a quick 3-hit combo with a trail")
	check(families.Sword.Variants[1] == "SlashRight" and families.Sword.Variants[2] == "SlashLeft" and families.Sword.Variants[3] == "SlashOverhead", "...right, left, overhead")
	check(families.Axe.Variants[1] == "ChopLeft" and families.Axe.Variants[2] == "ChopRight", "the axe chops alternate left and right")
	check(SwingConfig.Family("NoSuchFamily") == families.Pick and SwingConfig.Family(nil) == families.Pick, "an unknown family swings like a pick")
	check(SwingConfig.BitSpin.Speed > 0 and SwingConfig.BitSpin.Seconds > 0 and SwingConfig.BitSpin.Seconds < 1, "a drill bit spins briefly on the hit")

	return passed
end
