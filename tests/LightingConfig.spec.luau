-- LightingConfig spec: the warm winter sunset's settings stay sane in every preset (a late-afternoon sun, a warm sun and
-- cool shadows clearly darker than the lit snow, a subtle grade, the uploaded sunset sky, the lamps), the default is the
-- golden sunset, and Apply sets a preset on the Lighting service and its effects.
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end

	local LightingConfig = assert(loadstring(sources.LightingConfig, "LightingConfig"))()

	-- the presets: the golden sunset is the default, the pink dusk is kept to compare; the old names are the default's
	local presets = LightingConfig.Presets
	check(LightingConfig.Default == "PinkDusk" and presets.GoldenSunset ~= nil and presets.PinkDusk ~= nil,
		"two presets, the pink dusk by default")
	check(LightingConfig.Lighting == presets.PinkDusk.Lighting and LightingConfig.Atmosphere == presets.PinkDusk.Atmosphere,
		"LightingConfig.Lighting and the effects are the default preset's")
	check(presets.PinkDusk.Lighting.Brightness < 3 and presets.PinkDusk.Lighting.Brightness >= 2.4,
		"the pink dusk's sun a gentle step softer than the first pass (3.0), never dull")

	local function luminance(c: Color3): number
		return 0.2126 * c.R + 0.7152 * c.G + 0.0722 * c.B
	end
	for name, preset in presets do
		local L = preset.Lighting
		-- the light
		check(L.ClockTime == presets.GoldenSunset.Lighting.ClockTime and L.GeographicLatitude == presets.GoldenSunset.Lighting.GeographicLatitude,
			name .. ": the sun stands where the skybox bakes its glow (one ClockTime and latitude for every preset)")
		check(L.ClockTime >= 16.5 and L.ClockTime <= 17.8, name .. ": a late-afternoon sun, low over the mountains")
		local top, shade = L.ColorShift_Top, L.OutdoorAmbient
		check(top.R > top.G and top.G > top.B, name .. ": the sunlight is warm")
		check(shade.B > shade.R and shade.B > shade.G, name .. ": the shadows are cool blue")
		check(L.GlobalShadows == true and L.ShadowSoftness > 0 and L.ShadowSoftness < 0.5, name .. ": long, soft shadows")
		check(math.abs(L.ExposureCompensation) <= 0.3 and L.Brightness >= 1.5 and L.Brightness <= 10, name .. ": bright, never washed out")

		-- the haze and the post-processing, all subtle
		local a = preset.Atmosphere
		check(a.Density > 0.05 and a.Density < 0.45 and a.Haze > 0 and a.Color.R >= a.Color.B, name .. ": a light, warm haze")
		check(preset.Bloom.Intensity <= 0.6 and preset.Bloom.Threshold >= 1, name .. ": a gentle bloom")
		local grade = preset.ColorCorrection
		check(grade.TintColor.R >= grade.TintColor.B and math.abs(grade.Contrast) <= 0.3 and math.abs(grade.Saturation) <= 0.25, name .. ": a soft warm grade")
		check(preset.SunRays.Intensity > 0 and preset.SunRays.Intensity <= 0.3, name .. ": sun rays when looking towards the sun")
	end

	-- the golden sunset against the pink dusk it replaced: golden (not pink) light, blue (not lavender) shadows, less haze
	local golden, pink = presets.GoldenSunset, presets.PinkDusk
	local function hue(c: Color3): number
		return (c:ToHSV())
	end
	check(hue(golden.Lighting.ColorShift_Top) > hue(pink.Lighting.ColorShift_Top), "the golden sunlight is more golden (less red) than the pink dusk's")
	check(golden.Lighting.OutdoorAmbient.B - golden.Lighting.OutdoorAmbient.R > pink.Lighting.OutdoorAmbient.B - pink.Lighting.OutdoorAmbient.R,
		"its shadows are bluer, less lavender")
	check(golden.Atmosphere.Density < pink.Atmosphere.Density and golden.Atmosphere.Haze < pink.Atmosphere.Haze and golden.Atmosphere.Offset > pink.Atmosphere.Offset,
		"less haze, starting further out: the plots stay crisp")
	check(luminance(golden.Lighting.OutdoorAmbient) < luminance(golden.Lighting.ColorShift_Top) * 0.6,
		"the shadows are clearly darker than the sunlight (the pink dusk's lavender ones weren't)")
	check(golden.Lighting.EnvironmentDiffuseScale < pink.Lighting.EnvironmentDiffuseScale, "less of the pink sky on the shaded sides")
	check(golden.ColorCorrection.Contrast > pink.ColorCorrection.Contrast, "a touch more contrast")

	-- the sky: six uploaded faces and a big sun
	for _, face in { "SkyboxBk", "SkyboxDn", "SkyboxFt", "SkyboxLf", "SkyboxRt", "SkyboxUp" } do
		local id = LightingConfig.Sky.Faces[face]
		check(type(id) == "number" and id > 0, face .. " is uploaded")
	end
	check(LightingConfig.Sky.SunAngularSize >= 15, "a big, soft sun")

	-- the lamps
	local lamps = LightingConfig.Lamps
	for name, spec in { Gate = lamps.Gate, Leaderboard = lamps.Leaderboard, Plaza = lamps.Plaza } do
		check(spec.Range > 0 and spec.Range <= 40 and spec.Brightness > 0 and spec.Brightness <= 4, name .. " lamps: a soft, warm light")
		check(spec.Color.R >= spec.Color.B, name .. " lamps are warm")
	end

	-- Apply: the service's properties, the four effects (made when missing), the sky
	local made = {}
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
			table.insert(made, instance)
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
	local L = Config.Lighting
	check(fakeLighting.ClockTime == L.ClockTime and fakeLighting.OutdoorAmbient == L.OutdoorAmbient, "Apply sets the Lighting service")
	check(attributes.LightingPreset == "PinkDusk", "...to the default preset, and says which (the Lighting attribute LightingPreset)")
	for _, name in { "Atmosphere", "Bloom", "ColorCorrection", "SunRays" } do
		check(children[name] ~= nil, "Apply makes the " .. name .. " effect")
	end
	check(children.Atmosphere.Haze == LightingConfig.Atmosphere.Haze, "...with the config's values")
	local sky = fakeLighting:FindFirstChildOfClass("Sky")
	check(sky and sky.SkyboxUp == "rbxassetid://" .. LightingConfig.Sky.Faces.SkyboxUp, "Apply puts up the sunset sky")
	check(type(report) == "string" and string.find(report, "skybox", 1, true) ~= nil, "Apply reports what it did")

	-- another preset, and an unknown one
	Config.Apply(fakeLighting, "GoldenSunset")
	check(fakeLighting.OutdoorAmbient == Config.Presets.GoldenSunset.Lighting.OutdoorAmbient and children.Atmosphere.Haze == Config.Presets.GoldenSunset.Atmosphere.Haze
		and attributes.LightingPreset == "GoldenSunset", "Apply with a preset's name switches to it, the effects too")
	local before = fakeLighting.OutdoorAmbient
	check(Config.Apply(fakeLighting, "Disco") == nil and fakeLighting.OutdoorAmbient == before and attributes.LightingPreset == "GoldenSunset",
		"an unknown preset changes nothing")

	return passed
end
