--[[
LightingConfig: every lighting setting of the game in one place (docs/GAME_DESIGN.md, "Art direction"): a warm,
cinematic winter sunset. The sun sits low behind the mountains and throws long soft shadows across the snow; sunlit
snow is golden-amber (a little peach where it is brightest), the shadows a cool blue, clearly darker; a light haze
makes only the far mountains glow; a soft warm grade with a touch of contrast, a gentle bloom and sun rays when
looking towards the sun.

 * Presets: the looks, by name. Default (GoldenSunset) is what every server starts with; PinkDusk is the first pass,
   kept to compare (debug menu F2: "Lighting preset" switches the server live). Each holds:
   - Lighting: the Lighting service's own properties.
   - Atmosphere, Bloom, ColorCorrection, SunRays: the effects (each made if missing). DepthOfField stays off.
   Every preset keeps the same ClockTime and latitude: the skybox's baked sun glow is drawn round that sun.
 * Sky: the sunset skybox (tools/make_skybox.py, uploaded as group 921449746; assets/textures/sky/upload_manifest.json)
   and the sun's size. The skybox bakes its sun glow where Roblox draws the sun at this ClockTime and latitude, so
   change those together (make_skybox.py reads them from here).
 * Lamps: warm lights where the low sun leaves things dark (LightingService puts them on at start): the plot gates'
   posts, the leaderboards and the plaza.
LightingConfig.Apply(Lighting, preset?) sets the service and its effects (the default preset when none is named):
LightingService at the start of every server (so the place file is never the only copy), and tools/studio/lighting.luau
in Edit mode (so Studio shows the same).
Lighting.Technology (Future) can't be set from a script: it's set by hand in the place.
]]
local LightingConfig = {}

local function rgb(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

-- The looks (presets). Both share the sun's place (ClockTime, GeographicLatitude: the skybox bakes its glow there), the
-- sky and the lamps; the debug menu (F2, "Lighting preset") switches between them live for a side-by-side look.
LightingConfig.Default = "GoldenSunset"
LightingConfig.Presets = {
	-- The default: golden-amber sunlight on the snow (a little peach where it is brightest), cool blue shadows clearly
	-- darker than the lit snow, a light haze that only makes the far mountains glow, a touch more contrast.
	GoldenSunset = {
		Lighting = {
			ClockTime = 17.1, -- late afternoon: the sun low over the mountains (13 degrees up; any lower and the peaks shade the plots)
			GeographicLatitude = 38,
			-- a strong sun against dark blue ambient: at 13 degrees the sun barely lights flat snow, so a weaker sun let the
			-- ambient colour take over everything (the pink dusk's lavender film)
			Brightness = 6.5,
			ExposureCompensation = -0.1, -- (higher and the sunlit snow clips to white, losing its gold)
			Ambient = rgb(40, 50, 76), -- indoors and under roofs: a dark cool blue, never black
			OutdoorAmbient = rgb(70, 104, 158), -- the shadows on the snow: cool blue, well below the lit snow (darker went navy)
			EnvironmentDiffuseScale = 0.05, -- almost none of the sky on the shaded sides (more turns the snow pink)
			EnvironmentSpecularScale = 0.15, -- (more mirrors the pink sky into the shadows: lavender)
			GlobalShadows = true,
			ShadowSoftness = 0.2, -- long, soft-edged shadows
			-- golden-amber sunlight; any deeper (more orange) and the snow reads as desert sand
			ColorShift_Top = rgb(255, 196, 118),
			ColorShift_Bottom = rgb(15, 25, 55),
		},
		Atmosphere = {
			Density = 0.14,
			Offset = 0.4, -- the haze starts far out: the plots stay crisp
			Color = rgb(255, 206, 150), -- a golden haze
			Decay = rgb(235, 165, 115), -- far things fade to warm amber
			Glare = 0.3, -- the sun's halo when looking towards it
			Haze = 0.9, -- only the distant mountains glow
		},
		Bloom = { Enabled = true, Intensity = 0.25, Size = 24, Threshold = 2 }, -- (only the brightest things: the strong sun made gold glow)
		ColorCorrection = {
			Enabled = true,
			Brightness = 0.0,
			Contrast = 0.2,
			Saturation = 0.08,
			TintColor = rgb(255, 248, 238), -- a soft warm grade
		},
		SunRays = { Enabled = true, Intensity = 0.12, Spread = 0.55 },
	},
	-- The first pass: pink and peach sunlight, blue-violet shadows, a thick warm haze (kept for comparison).
	PinkDusk = {
		Lighting = {
			ClockTime = 17.1,
			GeographicLatitude = 38,
			Brightness = 3.0,
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
			Glare = 0.5,
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
		SunRays = { Enabled = true, Intensity = 0.14, Spread = 0.6 },
	},
}

-- The default preset's parts, by their old names (make_skybox.py and the specs read these).
local default = LightingConfig.Presets[LightingConfig.Default]
LightingConfig.Lighting = default.Lighting
LightingConfig.Atmosphere = default.Atmosphere
LightingConfig.Bloom = default.Bloom
LightingConfig.ColorCorrection = default.ColorCorrection
LightingConfig.SunRays = default.SunRays

LightingConfig.Sky = {
	-- the sunset skybox (assets/textures/sky/upload_manifest.json; tools/make_skybox.py)
	Faces = {
		SkyboxBk = 74529492771906,
		SkyboxDn = 122642767365993,
		SkyboxFt = 129032932102952,
		SkyboxLf = 131452679739982,
		SkyboxRt = 127399318612123,
		SkyboxUp = 134378334693788,
	},
	SunAngularSize = 24, -- a big, soft sun
	MoonAngularSize = 8,
	StarCount = 0,
	CelestialBodiesShown = true,
}

-- The lamps: warm point lights (Range studs, Brightness) where the low sun leaves things dark.
LightingConfig.Lamps = {
	-- on the front of each plot gate's two posts, near the top
	Gate = { Color = rgb(255, 196, 120), Range = 18, Brightness = 1.4, Height = 0.82 },
	-- over each leaderboard, shining down on its face
	Leaderboard = { Color = rgb(255, 214, 160), Range = 20, Brightness = 2.2, Angle = 75, Out = 6, Up = 4 },
	-- round the plaza: a ring of soft lights just above the ground
	Plaza = { Color = rgb(255, 190, 120), Range = 26, Brightness = 1.1, Radius = 44, Count = 8, Height = 9 },
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
	local faces = LightingConfig.Sky.Faces
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
		sky.SunAngularSize = LightingConfig.Sky.SunAngularSize
		sky.MoonAngularSize = LightingConfig.Sky.MoonAngularSize
		sky.StarCount = LightingConfig.Sky.StarCount
		sky.CelestialBodiesShown = LightingConfig.Sky.CelestialBodiesShown
	end
	Lighting:SetAttribute("LightingPreset", presetName)
	return `lighting: {presetName}{if skySet then ", with the sunset skybox" else " (the skybox ids aren't set yet)"}`
end

return LightingConfig
