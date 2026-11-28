-- LightingConfig spec: the warm winter sunset's settings stay sane (a late-afternoon sun, a warm sun and cool shadows,
-- a subtle grade, the uploaded sunset sky, the lamps), and Apply sets them on the Lighting service and its effects.
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end

	local LightingConfig = assert(loadstring(sources.LightingConfig, "LightingConfig"))()
	local L = LightingConfig.Lighting

	-- the light
	check(L.ClockTime >= 16.5 and L.ClockTime <= 17.8, "a late-afternoon sun, low over the mountains")
	local top, shade = L.ColorShift_Top, L.OutdoorAmbient
	check(top.R > top.G and top.G > top.B, "the sunlight is golden-orange")
	check(shade.B > shade.R and shade.B > shade.G, "the shadows are cool blue-violet")
	check(L.GlobalShadows == true and L.ShadowSoftness > 0 and L.ShadowSoftness < 0.5, "long, soft shadows")
	check(math.abs(L.ExposureCompensation) <= 0.3 and L.Brightness >= 1.5 and L.Brightness <= 4, "bright, never washed out")

	-- the haze and the post-processing, all subtle
	local a = LightingConfig.Atmosphere
	check(a.Density > 0.1 and a.Density < 0.45 and a.Haze > 0 and a.Color.R >= a.Color.B, "a light, warm haze")
	check(LightingConfig.Bloom.Intensity <= 0.6 and LightingConfig.Bloom.Threshold >= 1, "a gentle bloom")
	local grade = LightingConfig.ColorCorrection
	check(grade.TintColor.R >= grade.TintColor.B and math.abs(grade.Contrast) <= 0.25 and math.abs(grade.Saturation) <= 0.25, "a soft warm grade")
	check(LightingConfig.SunRays.Intensity > 0 and LightingConfig.SunRays.Intensity <= 0.3, "sun rays when looking towards the sun")

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
	local fakeLighting = {
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
	check(fakeLighting.ClockTime == L.ClockTime and fakeLighting.OutdoorAmbient == L.OutdoorAmbient, "Apply sets the Lighting service")
	for _, name in { "Atmosphere", "Bloom", "ColorCorrection", "SunRays" } do
		check(children[name] ~= nil, "Apply makes the " .. name .. " effect")
	end
	check(children.Atmosphere.Haze == LightingConfig.Atmosphere.Haze, "...with the config's values")
	local sky = fakeLighting:FindFirstChildOfClass("Sky")
	check(sky and sky.SkyboxUp == "rbxassetid://" .. LightingConfig.Sky.Faces.SkyboxUp, "Apply puts up the sunset sky")
	check(type(report) == "string" and string.find(report, "skybox", 1, true) ~= nil, "Apply reports what it did")

	return passed
end
