--[[
LightingConfig: every lighting setting of the game in one place (docs/GAME_DESIGN.md, "Art direction"): a day-night
cycle of three looks, each fixed while it lasts (no blending), Day -> PinkDusk -> Night -> Day.

 * Presets (the looks), by name; Default (PinkDusk) is the fixed look: Edit mode, the server's own Lighting at start,
   and every player who turned the cycle off in Settings. Each holds:
   - Lighting: the Lighting service's own properties (each look has its own ClockTime: the sun or the moon stands
     where its skybox bakes its glow).
   - Atmosphere, Bloom, ColorCorrection, SunRays: the effects (each made if missing). DepthOfField stays off.
   - Sky: the look's skybox (tools/make_skybox.py, uploaded as group 921449746; assets/textures/sky/upload_manifest.json),
     the sun's texture (the night draws the moon as its sun), the sun's and moon's size.
   - Lamps: whether the lamps are on (dusk and night).
   - Aurora: whether the northern lights move across the sky (night).
 * Cycle: the order, each look's length (minutes), the switch's fade (seconds, 0 = instant) and the whole cycle's length
   with the debug menu's fast cycle. LookFor() says which look shows for a time: the server only publishes the cycle's
   start (Workspace attributes DayCycleStart, DayCycleSpeed, DayCycleLook: LightingService), and every client applies
   its own lighting from it (DayNight.client), so nobody waits on the network and everyone switches together.
 * Aurora: the northern lights' curtains (Beams with the aurora texture, built by DayNight.client).
 * Lamps: warm lights where the low sun or the night leaves things dark (LightingService places them at start, off in
   the day look): the plot gates' posts, the leaderboards, the plaza, and on every plot by its gate and its stage.
 * Style: the place's Unified Lighting settings (Lighting.LightingStyle, Lighting.PrioritizeLightingQuality; they replaced
   Lighting.Technology). Apply sets them where they differ, so the place and every server match.
LightingConfig.Apply(Lighting, preset?) sets the style, the service, its effects and the sky: the server at start, each
client at every switch, tools/studio/lighting.luau in Edit mode.
]]
local LightingConfig = {}

local function rgb(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

-- The fixed look (Edit mode, the server at start, the cycle turned off in Settings).
LightingConfig.Default = "PinkDusk"

-- Unified Lighting (the developer's choice, 2026-11-28): Realistic, without prioritising lighting quality over speed.
LightingConfig.Style = {
	LightingStyle = "Realistic", -- an Enum.LightingStyle name: Realistic or Soft
	PrioritizeLightingQuality = false,
}

LightingConfig.Presets = {
	-- Day (a winter afternoon): bright and clear, a blue sky, crisp white snow, soft blue shadows, a warm sun higher
	-- and less orange than the sunset's (from the golden sunset look, the sun raised to 43 degrees).
	Day = {
		Lighting = {
			ClockTime = 15, -- the sun 43 degrees up (make_skybox.py SUN_DAY)
			GeographicLatitude = 38,
			Brightness = 3,
			ExposureCompensation = -0.2, -- (brighter and the snow from above is a white sheet)
			Ambient = rgb(70, 82, 104),
			OutdoorAmbient = rgb(92, 112, 158), -- soft blue shadows (brighter flattened the slopes)
			EnvironmentDiffuseScale = 0.25, -- a little of the blue sky on the shaded sides
			EnvironmentSpecularScale = 0.35,
			GlobalShadows = true,
			ShadowSoftness = 0.25,
			ColorShift_Top = rgb(255, 240, 214), -- a warm sun, barely orange
			ColorShift_Bottom = rgb(30, 40, 62),
		},
		Atmosphere = {
			Density = 0.2,
			Offset = 0.3,
			Color = rgb(206, 224, 244),
			Decay = rgb(152, 182, 222),
			Glare = 0.12,
			Haze = 0.8,
		},
		Bloom = { Enabled = true, Intensity = 0.25, Size = 24, Threshold = 1.8 },
		ColorCorrection = { Enabled = true, Brightness = 0, Contrast = 0.18, Saturation = 0.1, TintColor = rgb(255, 252, 248) },
		SunRays = { Enabled = true, Intensity = 0.06, Spread = 0.5 },
		Sky = {
			Faces = { -- assets/textures/sky/day/
				SkyboxBk = 122979432845792, SkyboxDn = 95270645121379, SkyboxFt = 99323392251546,
				SkyboxLf = 77034042115053, SkyboxRt = 85576364847485, SkyboxUp = 122599972465594,
			},
			SunAngularSize = 16, MoonAngularSize = 8, StarCount = 0, CelestialBodiesShown = true,
		},
		Lamps = false,
		Aurora = false,
	},
	-- Pink dusk (the warm winter sunset): pink and peach sunlight, blue-violet shadows, a warm haze. The favourite.
	PinkDusk = {
		Lighting = {
			ClockTime = 17.1,
			GeographicLatitude = 38,
			Brightness = 2.7, -- (3.0 in the first pass: a gentle step down, a softer sun on the snow)
			ExposureCompensation = -0.05,
			Ambient = rgb(55, 60, 95),
			OutdoorAmbient = rgb(100, 112, 165),
			EnvironmentDiffuseScale = 0.32,
			EnvironmentSpecularScale = 0.5,
			GlobalShadows = true,
			ShadowSoftness = 0.22,
			ColorShift_Top = rgb(255, 165, 85),
			ColorShift_Bottom = rgb(20, 20, 50),
		},
		Atmosphere = {
			Density = 0.28,
			Offset = 0.16,
			Color = rgb(255, 205, 165),
			Decay = rgb(200, 135, 130),
			Glare = 0.4, -- (0.5 in the first pass: a softer sun glow)
			Haze = 1.6,
		},
		Bloom = { Enabled = true, Intensity = 0.42, Size = 26, Threshold = 1.35 },
		ColorCorrection = {
			Enabled = true,
			Brightness = 0.0,
			Contrast = 0.14,
			Saturation = 0.15,
			TintColor = rgb(255, 240, 224),
		},
		SunRays = { Enabled = true, Intensity = 0.11, Spread = 0.6 }, -- (0.14 in the first pass)
		Sky = {
			Faces = { -- assets/textures/sky/ (the sunset)
				SkyboxBk = 74529492771906, SkyboxDn = 122642767365993, SkyboxFt = 129032932102952,
				SkyboxLf = 131452679739982, SkyboxRt = 127399318612123, SkyboxUp = 134378334693788,
			},
			SunAngularSize = 24, MoonAngularSize = 8, StarCount = 0, CelestialBodiesShown = true, -- a big, soft sun
		},
		Lamps = true,
		Aurora = false,
	},
	-- Night: moonlit and blue, never too dark to play. A deep blue starry sky with a big moon, the northern lights, pale
	-- blue snow; the lamps, the rarity glows and the building effects carry the scene.
	Night = {
		Lighting = {
			-- (a morning ClockTime on purpose: at a night-time one Roblox darkens a custom skybox nearly to black, hiding the
			-- night sky's blue and its stars. The "sun" here is drawn with the moon's texture (Sky.SunTexture) and lights the
			-- snow with a dim blue light, 43 degrees up where the night sky bakes the moon's glow: make_skybox.py MOON_NIGHT.)
			ClockTime = 9,
			GeographicLatitude = 38,
			Brightness = 1,
			ExposureCompensation = 0,
			Ambient = rgb(36, 46, 86),
			OutdoorAmbient = rgb(64, 84, 138), -- pale blue snow even out of the moonlight
			EnvironmentDiffuseScale = 0.25,
			EnvironmentSpecularScale = 0.3,
			GlobalShadows = true,
			ShadowSoftness = 0.3,
			ColorShift_Top = rgb(150, 180, 255), -- blue moonlight
			ColorShift_Bottom = rgb(20, 30, 70),
		},
		Atmosphere = {
			Density = 0.24,
			Offset = 0.2,
			Color = rgb(64, 84, 142),
			Decay = rgb(40, 60, 120),
			Glare = 0,
			Haze = 1.2,
		},
		Bloom = { Enabled = true, Intensity = 0.55, Size = 28, Threshold = 1.1 }, -- (the glows and auras shine more)
		ColorCorrection = { Enabled = true, Brightness = 0, Contrast = 0.1, Saturation = 0.05, TintColor = rgb(226, 236, 255) },
		SunRays = { Enabled = false, Intensity = 0, Spread = 0.5 },
		Sky = {
			Faces = { -- assets/textures/sky/night/
				SkyboxBk = 120652674737428, SkyboxDn = 133675510622637, SkyboxFt = 133648367975067,
				SkyboxLf = 87376954858011, SkyboxRt = 110021717690534, SkyboxUp = 102514024280218,
			},
			-- the moon (drawn as the sun, see ClockTime); the stars are baked into the sky
			SunTexture = "rbxasset://sky/moon.jpg", SunAngularSize = 14, MoonAngularSize = 8, StarCount = 0, CelestialBodiesShown = true,
		},
		Lamps = true,
		Aurora = true,
	},
}

-- The default preset's parts, by their old names (the specs read these).
local default = LightingConfig.Presets[LightingConfig.Default]
LightingConfig.Lighting = default.Lighting
LightingConfig.Atmosphere = default.Atmosphere
LightingConfig.Bloom = default.Bloom
LightingConfig.ColorCorrection = default.ColorCorrection
LightingConfig.SunRays = default.SunRays
LightingConfig.Sky = default.Sky

-- The cycle: the looks in order, each fixed for its Minutes; the switch dims the screen and back over FadeSeconds (the
-- new look applied in the middle; 0 = instant). FastSeconds: the whole cycle with the debug menu's fast cycle on.
LightingConfig.Cycle = {
	Order = { "Day", "PinkDusk", "Night" },
	Minutes = { Day = 8, PinkDusk = 6, Night = 6 },
	FadeSeconds = 2,
	FadeDepth = 0.55, -- how far the fade dims the screen (ColorCorrection brightness below 0)
	FastSeconds = 120,
}

-- The whole cycle, in seconds (at normal speed).
function LightingConfig.CycleSeconds(): number
	local total = 0
	for _, name in LightingConfig.Cycle.Order do
		total += LightingConfig.Cycle.Minutes[name] * 60
	end
	return total
end

-- The look at a point of the cycle (seconds since it started, at normal speed, any size), and the seconds left in it.
function LightingConfig.LookAt(seconds: number): (string, number)
	local total = LightingConfig.CycleSeconds()
	local into = seconds % total
	for _, name in LightingConfig.Cycle.Order do
		local length = LightingConfig.Cycle.Minutes[name] * 60
		if into < length then
			return name, length - into
		end
		into -= length
	end
	local last = LightingConfig.Cycle.Order[#LightingConfig.Cycle.Order]
	return last, 0
end

-- Which look a player sees: a look the debug menu forced (the whole server), else the fixed look for a player who
-- turned the cycle off, else the cycle's look at `now` (server time) from its start and speed.
function LightingConfig.LookFor(now: number, start: number?, speed: number?, forced: string?, cycleOn: boolean): string
	if type(forced) == "string" and LightingConfig.Presets[forced] then
		return forced
	end
	if not cycleOn or type(start) ~= "number" then
		return LightingConfig.Default
	end
	return (LightingConfig.LookAt((now - start) * (if type(speed) == "number" and speed > 0 then speed else 1)))
end

-- The northern lights (the night look): curtains of light high round the map, each a Beam with the aurora texture
-- (make_skybox.py) that scrolls slowly along it and ripples (its curve swings); a slow, soft fade in and out.
LightingConfig.Aurora = {
	Texture = 121345685087118, -- assets/textures/sky/Aurora.png
	-- each curtain: Angle (degrees round the map, 0 = +Z), Distance from the middle, Height of its bottom edge, Length
	-- along the sky, Width (the curtain's height), Colour tint
	Curtains = {
		{ Angle = 200, Distance = 650, Height = 260, Length = 900, Width = 220, Colour = rgb(150, 255, 200) },
		{ Angle = 245, Distance = 700, Height = 330, Length = 800, Width = 180, Colour = rgb(140, 245, 240) },
		{ Angle = 150, Distance = 720, Height = 300, Length = 700, Width = 200, Colour = rgb(190, 200, 255) },
	},
	Transparency = 0.25, -- (the texture's own alpha does the rest)
	Brightness = 2,
	LightEmission = 1,
	Scroll = 0.03, -- texture units a second along the curtain
	Ripple = { Size = 60, Seconds = 14 }, -- the curve's swing (studs) and one full swing
	Segments = 24,
}

-- The lamps: warm point lights (Range studs, Brightness), on for the looks with Lamps = true.
LightingConfig.Lamps = {
	-- on the front of each plot gate's two posts, near the top
	Gate = { Color = rgb(255, 196, 120), Range = 18, Brightness = 1.4, Height = 0.82 },
	-- over each leaderboard, shining down on its face
	Leaderboard = { Color = rgb(255, 214, 160), Range = 20, Brightness = 2.2, Angle = 75, Out = 6, Up = 4 },
	-- round the plaza: a ring of soft lights just above the ground
	Plaza = { Color = rgb(255, 182, 108), Range = 24, Brightness = 0.75, Radius = 44, Count = 8, Height = 9 },
	-- on every plot (plot space: x across, z towards the open front): inside the gate, and by the stage's front corners
	Plot = {
		Color = rgb(255, 188, 115), Range = 22, Brightness = 0.8,
		Spots = { { X = 0, Z = 40, Height = 7 }, { X = -17, Z = 17, Height = 6 }, { X = 17, Z = 17, Height = 6 } },
	},
}

local function effect(Lighting: Instance, className: string, name: string)
	local found = Lighting:FindFirstChild(name)
	if found and not found:IsA(className) then
		found:Destroy()
		found = nil
	end
	if not found then
		found = Instance.new(className)
		found.Name = name
		found.Parent = Lighting
	end
	return found
end

-- Sets the Lighting service, its effects and the sky to a preset (default: LightingConfig.Default). Returns a short
-- report. An unknown preset name is refused (nil and the reason).
function LightingConfig.Apply(Lighting: Lighting, presetName: string?): string?
	presetName = presetName or LightingConfig.Default
	local preset = LightingConfig.Presets[presetName :: string]
	if not preset then
		return nil
	end
	-- the style only where it differs (a property this Studio doesn't have yet is skipped)
	pcall(function()
		local style = (Enum :: any).LightingStyle[LightingConfig.Style.LightingStyle]
		if (Lighting :: any).LightingStyle ~= style then
			(Lighting :: any).LightingStyle = style
		end
	end)
	pcall(function()
		if (Lighting :: any).PrioritizeLightingQuality ~= LightingConfig.Style.PrioritizeLightingQuality then
			(Lighting :: any).PrioritizeLightingQuality = LightingConfig.Style.PrioritizeLightingQuality
		end
	end)
	for property, value in preset.Lighting do
		(Lighting :: any)[property] = value
	end
	local sets = {
		{ "Atmosphere", "Atmosphere", preset.Atmosphere },
		{ "BloomEffect", "Bloom", preset.Bloom },
		{ "ColorCorrectionEffect", "ColorCorrection", preset.ColorCorrection },
		{ "SunRaysEffect", "SunRays", preset.SunRays },
	}
	for _, set in sets do
		local made = effect(Lighting, set[1], set[2])
		for property, value in set[3] do
			made[property] = value
		end
	end
	for _, focus in Lighting:GetChildren() do
		if focus:IsA("DepthOfFieldEffect") then
			focus.Enabled = false
		end
	end
	local sky = Lighting:FindFirstChildOfClass("Sky")
	local skyLook = preset.Sky or LightingConfig.Sky
	local faces = skyLook.Faces
	local skySet = faces.SkyboxBk ~= 0
	if skySet then
		if not sky then
			sky = Instance.new("Sky")
			sky.Parent = Lighting
		end
		for face, id in faces do
			(sky :: any)[face] = "rbxassetid://" .. id
		end
	end
	if sky then
		sky.SunTextureId = skyLook.SunTexture or "rbxasset://sky/sun.jpg"
		sky.SunAngularSize = skyLook.SunAngularSize
		sky.MoonAngularSize = skyLook.MoonAngularSize
		sky.StarCount = skyLook.StarCount
		sky.CelestialBodiesShown = skyLook.CelestialBodiesShown
	end
	Lighting:SetAttribute("LightingPreset", presetName)
	return `lighting: {presetName}{if skySet then ", with its skybox" else " (the skybox ids aren't set yet)"}`
end

return LightingConfig
