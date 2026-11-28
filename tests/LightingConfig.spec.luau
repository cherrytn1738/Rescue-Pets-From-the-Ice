-- LightingConfig spec: the day-night cycle's three looks stay sane (a clear day with a higher, less orange sun; the pink
-- dusk exactly as chosen; a moonlit blue night that is never too dark), each with its own uploaded sky; the cycle's order
-- and lengths and the look for any time (LookAt, LookFor: the debug menu's forced look, the Settings switch, the fast
-- cycle); the lamps and the aurora; and Apply sets a look on the Lighting service, its effects and its sky.
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end

	local LightingConfig = assert(loadstring(sources.LightingConfig, "LightingConfig"))()
	local presets = LightingConfig.Presets
	local day, dusk, night = presets.Day, presets.PinkDusk, presets.Night

	-- the looks
	check(day and dusk and night and presets.GoldenSunset == nil, "three looks: Day, PinkDusk, Night (the golden sunset became the day)")
	check(LightingConfig.Default == "PinkDusk" and LightingConfig.Lighting == dusk.Lighting and LightingConfig.Sky == dusk.Sky,
		"the fixed look is the pink dusk (Edit mode, the cycle off), and the old names are its parts")

	local function luminance(c: Color3): number
		return 0.2126 * c.R + 0.7152 * c.G + 0.0722 * c.B
	end
	for name, preset in presets do
		local L = preset.Lighting
		check(L.GeographicLatitude == 38 and L.GlobalShadows == true and L.ShadowSoftness > 0 and L.ShadowSoftness < 0.5, name .. ": soft shadows")
		check(math.abs(L.ExposureCompensation) <= 0.5 and L.Brightness >= 1 and L.Brightness <= 10, name .. ": bright enough, never washed out")
		check(preset.Bloom.Intensity <= 0.7 and preset.Bloom.Threshold >= 1, name .. ": a gentle bloom")
		local grade = preset.ColorCorrection
		check(math.abs(grade.Contrast) <= 0.3 and math.abs(grade.Saturation) <= 0.25 and grade.Brightness == 0, name .. ": a soft grade")
		check(preset.Atmosphere.Density > 0.05 and preset.Atmosphere.Density < 0.45, name .. ": a light haze")
		for _, face in { "SkyboxBk", "SkyboxDn", "SkyboxFt", "SkyboxLf", "SkyboxRt", "SkyboxUp" } do
			check(type(preset.Sky.Faces[face]) == "number" and preset.Sky.Faces[face] > 0, `{name}: {face} is uploaded`)
		end
		check(type(preset.Lamps) == "boolean" and type(preset.Aurora) == "boolean", name .. ": says whether the lamps and the aurora are on")
	end
	check(day.Sky.Faces.SkyboxUp ~= dusk.Sky.Faces.SkyboxUp and night.Sky.Faces.SkyboxUp ~= dusk.Sky.Faces.SkyboxUp
		and day.Sky.Faces.SkyboxUp ~= night.Sky.Faces.SkyboxUp, "one skybox per look")

	-- the pink dusk exactly as chosen (the favourite look: change it only on purpose)
	local D = dusk.Lighting
	check(D.ClockTime == 17.1 and D.Brightness == 2.7 and D.ExposureCompensation == -0.05 and D.OutdoorAmbient == Color3.fromRGB(100, 112, 165)
		and D.ColorShift_Top == Color3.fromRGB(255, 165, 85) and D.EnvironmentDiffuseScale == 0.32, "the pink dusk's light is unchanged")
	check(dusk.Atmosphere.Haze == 1.6 and dusk.Atmosphere.Glare == 0.4 and dusk.SunRays.Intensity == 0.11 and dusk.Bloom.Intensity == 0.42
		and dusk.Sky.Faces.SkyboxUp == 134378334693788 and dusk.Sky.SunAngularSize == 24, "...its effects and its sunset sky too")

	-- day: a higher, less orange sun, crisp white snow, soft blue shadows, a blue sky
	local function hue(c: Color3): number
		return (c:ToHSV())
	end
	local _, daySat = day.Lighting.ColorShift_Top:ToHSV()
	local _, duskSat = D.ColorShift_Top:ToHSV()
	check(math.abs(day.Lighting.ClockTime - 12) < math.abs(D.ClockTime - 12), "the day's sun stands higher than the dusk's")
	check(day.Lighting.ColorShift_Top.R >= day.Lighting.ColorShift_Top.G and day.Lighting.ColorShift_Top.G >= day.Lighting.ColorShift_Top.B
		and daySat < duskSat * 0.6, "a warm sun, much less orange than the dusk's")
	check(day.Lighting.OutdoorAmbient.B > day.Lighting.OutdoorAmbient.R and luminance(day.Lighting.OutdoorAmbient) > luminance(D.OutdoorAmbient) * 0.9,
		"soft blue shadows, no darker than the dusk's")
	check(not day.Lamps and not day.Aurora, "no lamps and no aurora in the day")

	-- night: moonlit and blue, never too dark to play
	local N = night.Lighting
	check(night.Sky.SunTexture == "rbxasset://sky/moon.jpg" and N.ClockTime > 6 and N.ClockTime < 18 and N.Brightness < day.Lighting.Brightness / 2,
		"night: a dim moon (drawn as the sun, so Roblox doesn't darken the starry skybox)")
	check(day.Sky.SunTexture == nil and dusk.Sky.SunTexture == nil, "...and the real sun again by day and at dusk")
	check(N.ColorShift_Top.B > N.ColorShift_Top.R and N.OutdoorAmbient.B > N.OutdoorAmbient.R and N.OutdoorAmbient.B > N.OutdoorAmbient.G,
		"blue moonlight and blue snow")
	check(luminance(N.OutdoorAmbient) >= 0.3 and N.ExposureCompensation >= 0, "never too dark to play")
	check(night.Sky.SunAngularSize > day.Sky.MoonAngularSize, "a big moon (the stars are baked into the night sky)")
	check(night.Lamps and night.Aurora and dusk.Lamps and not dusk.Aurora, "lamps at dusk and night, the aurora at night")
	check(night.Bloom.Intensity >= dusk.Bloom.Intensity and night.Bloom.Threshold <= dusk.Bloom.Threshold, "the glows shine more at night")
	check(hue(N.ColorShift_Top) > 0.5, "...not warm")

	-- the cycle
	local cycle = LightingConfig.Cycle
	check(#cycle.Order == 3 and cycle.Order[1] == "Day" and cycle.Order[2] == "PinkDusk" and cycle.Order[3] == "Night", "day -> pink dusk -> night -> day")
	check(cycle.Minutes.Day == 8 and cycle.Minutes.PinkDusk == 6 and cycle.Minutes.Night == 6 and LightingConfig.CycleSeconds() == 1200,
		"8 + 6 + 6 minutes: a 20-minute cycle")
	check(cycle.FadeSeconds >= 0 and cycle.FadeSeconds <= 4 and cycle.FadeDepth > 0 and cycle.FadeDepth < 1, "a quick fade at each switch (about 2 s)")
	check(cycle.FastSeconds >= 60 and cycle.FastSeconds <= 180, "the fast cycle takes about 2 minutes")
	local function lookAt(seconds)
		return (LightingConfig.LookAt(seconds))
	end
	check(lookAt(0) == "Day" and lookAt(479.9) == "Day" and lookAt(480) == "PinkDusk" and lookAt(839.9) == "PinkDusk"
		and lookAt(840) == "Night" and lookAt(1199.9) == "Night" and lookAt(1200) == "Day" and lookAt(1200 * 50 + 900) == "Night",
		"each look for its minutes, round and round")
	check(lookAt(-1) == "Night", "a time just before the start is the end of the last look")
	local _, left = LightingConfig.LookAt(100)
	check(math.abs(left - 380) < 1e-6, "LookAt says how long the look has left")

	local now = 10000
	check(LightingConfig.LookFor(now, now - 500, 1, nil, true) == "PinkDusk", "the cycle's look from its start")
	check(LightingConfig.LookFor(now, now - 50, 10, nil, true) == "PinkDusk", "...faster with the fast cycle")
	check(LightingConfig.LookFor(now, now - 900, 1, nil, false) == "PinkDusk" and LightingConfig.LookFor(now, now - 10, 1, nil, false) == "PinkDusk",
		"the cycle off in Settings: always the pink dusk")
	check(LightingConfig.LookFor(now, now - 10, 1, "Night", true) == "Night" and LightingConfig.LookFor(now, now - 10, 1, "Night", false) == "Night",
		"a look the debug menu forced shows for everyone")
	check(LightingConfig.LookFor(now, now - 10, 1, "Disco", true) == "Day", "an unknown forced look is ignored")
	check(LightingConfig.LookFor(now, nil, nil, nil, true) == "PinkDusk", "no cycle published yet (Edit mode): the pink dusk")

	-- the aurora
	local aurora = LightingConfig.Aurora
	check(type(aurora.Texture) == "number" and aurora.Texture > 0, "the aurora's texture is uploaded")
	check(#aurora.Curtains >= 2 and aurora.Segments <= 40 and aurora.Scroll > 0 and aurora.Scroll < 0.2 and aurora.Ripple.Seconds >= 6,
		"a few curtains, slow and soft (cheap on phones)")
	for _, curtain in aurora.Curtains do
		check(curtain.Colour.G >= curtain.Colour.R or curtain.Colour.B >= curtain.Colour.R, "aurora curtains are green, teal or violet")
		check(curtain.Distance >= 300 and curtain.Height >= 150, "...high and far, in the sky")
	end

	-- the lamps
	local lamps = LightingConfig.Lamps
	for name, spec in { Gate = lamps.Gate, Leaderboard = lamps.Leaderboard, Plaza = lamps.Plaza, Plot = lamps.Plot } do
		check(spec.Range > 0 and spec.Range <= 40 and spec.Brightness > 0 and spec.Brightness <= 4, name .. " lamps: a soft, warm light")
		check(spec.Color.R >= spec.Color.B, name .. " lamps are warm")
	end
	check(#lamps.Plot.Spots >= 2, "a few lamps on every plot")
	for _, spot in lamps.Plot.Spots do
		check(math.abs(spot.X) < 50 and spot.Z > 0 and spot.Z < 50 and spot.Height > 2, "plot lamps stand inside the plot, by the gate and the stage")
	end

	-- Apply: the service's properties, the four effects (made when missing), the sky
	local function fakeInstance(className, name)
		return { ClassName = className, Name = name, IsA = function(self, c)
			return self.ClassName == c
		end, Destroy = function() end }
	end
	local children = {}
	local attributes = {}
	local fakeLighting = {
		SetAttribute = function(_, name, value)
			attributes[name] = value
		end,
		FindFirstChild = function(_, name)
			return children[name]
		end,
		FindFirstChildOfClass = function(_, className)
			for _, child in children do
				if child.ClassName == className then
					return child
				end
			end
			return nil
		end,
		GetChildren = function()
			local list = {}
			for _, child in children do
				table.insert(list, child)
			end
			return list
		end,
	}
	local apply = assert(loadstring(sources.LightingConfig, "LightingConfig"))
	setfenv(apply, setmetatable({
		Instance = { new = function(className)
			local instance = fakeInstance(className, className)
			return setmetatable(instance, { __newindex = function(t, k, v)
				rawset(t, k, v)
				if k == "Parent" and v == fakeLighting then
					children[rawget(t, "Name")] = t
				end
			end })
		end },
	}, { __index = getfenv(1) }))
	local Config = apply()
	local report = Config.Apply(fakeLighting)
	check(fakeLighting.ClockTime == 17.1 and fakeLighting.OutdoorAmbient == Config.Lighting.OutdoorAmbient, "Apply sets the Lighting service")
	check(Config.Style.LightingStyle == "Realistic" and Config.Style.PrioritizeLightingQuality == false,
		"Unified Lighting: Realistic, without prioritising lighting quality (the developer's choice)")
	check(fakeLighting.LightingStyle == Enum.LightingStyle.Realistic and fakeLighting.PrioritizeLightingQuality == false,
		"Apply sets the lighting style")
	check(attributes.LightingPreset == "PinkDusk", "...to the fixed look by default, and says which (the Lighting attribute LightingPreset)")
	for _, name in { "Atmosphere", "Bloom", "ColorCorrection", "SunRays" } do
		check(children[name] ~= nil, "Apply makes the " .. name .. " effect")
	end
	check(children.Atmosphere.Haze == dusk.Atmosphere.Haze, "...with the look's values")
	local sky = fakeLighting:FindFirstChildOfClass("Sky")
	check(sky and sky.SkyboxUp == "rbxassetid://" .. dusk.Sky.Faces.SkyboxUp and sky.SunAngularSize == 24, "Apply puts up the look's sky")
	check(type(report) == "string" and string.find(report, "skybox", 1, true) ~= nil, "Apply reports what it did")

	Config.Apply(fakeLighting, "Night")
	check(fakeLighting.ClockTime == N.ClockTime and children.Atmosphere.Haze == night.Atmosphere.Haze and attributes.LightingPreset == "Night"
		and sky.SkyboxUp == "rbxassetid://" .. night.Sky.Faces.SkyboxUp and sky.SunTextureId == "rbxasset://sky/moon.jpg",
		"Apply with a look's name switches to it: light, effects and the skybox")
	local before = fakeLighting.OutdoorAmbient
	check(Config.Apply(fakeLighting, "Disco") == nil and fakeLighting.OutdoorAmbient == before and attributes.LightingPreset == "Night",
		"an unknown look changes nothing")

	return passed
end
