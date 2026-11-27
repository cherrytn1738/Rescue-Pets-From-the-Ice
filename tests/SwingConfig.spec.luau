-- SwingConfig spec: the ice pick swing's variants, keyframes and the fast-tapping rules (PickSwing.client).
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end

	local SwingConfig = assert(loadstring(sources.SwingConfig))()

	-- Variants take turns: never the same twice running, every one comes up
	check(#SwingConfig.Variants >= 2 and #SwingConfig.Variants <= 3, "two or three variants")
	local seen, previous = {}, nil
	for _ = 1, 9 do
		local nextOne = SwingConfig.NextVariant(previous)
		check(nextOne ~= previous, "the same variant never plays twice running")
		seen[nextOne] = true
		previous = nextOne
	end
	for _, name in SwingConfig.Variants do
		check(seen[name], name .. " comes up in turn")
	end

	-- Fast tapping speeds the swing up instead of queueing; a slow tap plays at normal speed
	check(SwingConfig.SpeedFor(nil) == 1 and SwingConfig.SpeedFor(SwingConfig.Length + 1) == 1, "an unhurried tap: normal speed")
	check(SwingConfig.SpeedFor(SwingConfig.Length / 2) > 1, "a tap halfway through a swing: faster")
	check(SwingConfig.SpeedFor(0.01) == SwingConfig.MaxSpeed and SwingConfig.MaxSpeed <= 3, "very fast tapping: capped at MaxSpeed")
	local last = 0
	for _, gap in { 0.5, 0.3, 0.2, 0.1, 0.05 } do
		local speed = SwingConfig.SpeedFor(gap)
		check(speed >= last, "quicker taps never play slower")
		last = speed
	end

	-- The keyframes: in order, inside the swing, starting and ending at the hold, the strike at ImpactAt
	check(SwingConfig.WindUpEnd < SwingConfig.ImpactAt and SwingConfig.ImpactAt < SwingConfig.Length, "wind-up, then the strike, then the rest")
	for _, name in { table.unpack(SwingConfig.Variants), "Dip" } do
		local frames = SwingConfig.R15[name]
		check(type(frames) == "table" and #frames >= 3, name .. " has keyframes")
		local time = -1
		for _, frame in frames do
			check(frame.Time > time and frame.Time <= SwingConfig.Length + 1e-6, name .. ": keyframes in order, inside the swing")
			time = frame.Time
			for part, entry in frame.Poses do
				check(SwingConfig.R15Parents[part] ~= nil, `{name}: {part} is a joint in the R15 tree`)
				check(type(entry[1]) == "number" and type(entry[2]) == "number" and type(entry[3]) == "number", `{name}: {part} has three angles`)
				check(typeof(SwingConfig.PoseCFrame(entry)) == "CFrame", `{name}: {part} makes a CFrame`)
			end
		end
		check(frames[1].Time == 0 and math.abs(frames[#frames].Time - SwingConfig.Length) < 1e-6, name .. " starts at 0 and lasts the whole swing")
	end
	for _, name in SwingConfig.Variants do
		local frames = SwingConfig.R15[name]
		local first, final = frames[1].Poses, frames[#frames].Poses
		for part, entry in first do
			local other = final[part]
			check(other and other[1] == entry[1] and other[2] == entry[2] and other[3] == entry[3], `{name}: {part} ends where it starts (the hold)`)
		end
		local strike = false
		for _, frame in frames do
			if math.abs(frame.Time - SwingConfig.ImpactAt) < 1e-6 then
				strike = true
			end
		end
		check(strike, name .. " has its strike keyframe at ImpactAt (the camera nudge)")
		check(frames[1].Poses.LeftUpperLeg == nil, name .. " leaves the legs free (the Dip animation bends the knees)")
	end

	-- Uploaded animations: a whole number id for every variant and the dip
	for _, name in { table.unpack(SwingConfig.Variants), "Dip" } do
		local id = SwingConfig.AnimationIds.R15[name]
		check(type(id) == "number" and id >= 0 and id % 1 == 0, name .. " has an animation id (0 = not uploaded)")
	end
	check(SwingConfig.Nudge.Strength > 0 and SwingConfig.Nudge.Strength < 0.5, "the camera nudge is tiny")

	return passed
end
