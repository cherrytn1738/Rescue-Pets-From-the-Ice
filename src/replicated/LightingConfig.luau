--[[
LightingConfig: every lighting setting of the game in one place (docs/GAME_DESIGN.md, "Art direction"): a warm,
cinematic winter sunset. The sun sits low behind the mountains and throws long soft shadows across the snow; sunlit
snow is golden-orange with pink and peach, the shadows a cool blue-violet; a warm haze makes the far mountains glow;
a soft warm grade, a gentle bloom and sun rays when looking towards the sun.

 * Lighting: the Lighting service's own properties.
 * Atmosphere, Bloom, ColorCorrection, SunRays: the effects (each made if missing). DepthOfField stays off.
 * Sky: the sunset skybox (tools/make_skybox.py, uploaded as group 921449746; assets/textures/sky/upload_manifest.json)
   and the sun's size. The skybox bakes its sun glow where Roblox draws the sun at this ClockTime and latitude, so
   change those together (make_skybox.py reads them from here).
 * Lamps: warm lights where the low sun leaves things dark (LightingService puts them on at start): the plot gates'
   posts, the leaderboards and the plaza.
LightingConfig.Apply(Lighting) sets the service and its effects: LightingService at the start of every server (so
the place file is never the only copy), and tools/studio/lighting.luau in Edit mode (so Studio shows the same).
Lighting.Technology (Future) can't be set from a script: it's set by hand in the place.
]]
local LightingConfig = {}

local function rgb(r: number, g: number, b: number): Color3
	return Color3.fromRGB(r, g, b)
end

LightingConfig.Lighting = {
	ClockTime = 17.1, -- late afternoon: the sun low over the mountains (13 degrees up; any lower and the peaks shade the plots)
	GeographicLatitude = 38,
	Brightness = 3.0,
	ExposureCompensation = -0.05,
	Ambient = rgb(55, 60, 95), -- indoors and under roofs: dusky violet, never black
	OutdoorAmbient = rgb(100, 112, 165), -- the shadows on the snow: cool blue-violet
	EnvironmentDiffuseScale = 0.32, -- a little of the sunset sky on the shaded sides (more turned everything pink)
	EnvironmentSpecularScale = 0.5,
	GlobalShadows = true,
	ShadowSoftness = 0.22, -- long, soft-edged shadows
	ColorShift_Top = rgb(255, 165, 85), -- the low sun's golden-orange on everything it lights
	ColorShift_Bottom = rgb(20, 20, 50),
}

LightingConfig.Atmosphere = {
	Density = 0.28,
	Offset = 0.16,
	Color = rgb(255, 205, 165), -- a warm peach haze
	Decay = rgb(200, 135, 130), -- far things fade to a warm rose
	Glare = 0.5, -- the sun's halo when looking towards it
	Haze = 1.6, -- the distant mountains glow
}

LightingConfig.Bloom = { Enabled = true, Intensity = 0.42, Size = 26, Threshold = 1.35 }

LightingConfig.ColorCorrection = {
	Enabled = true,
	Brightness = 0.0,
	Contrast = 0.14,
	Saturation = 0.15,
	TintColor = rgb(255, 240, 224), -- a soft warm grade
}

LightingConfig.SunRays = { Enabled = true, Intensity = 0.14, Spread = 0.6 }

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

-- Sets the Lighting service, its effects and the sky. Returns a short report.
function LightingConfig.Apply(Lighting: Lighting): string
	for property, value in LightingConfig.Lighting do
		(Lighting :: any)[property] = value
	end
	local sets = {
		{ "Atmosphere", "Atmosphere", LightingConfig.Atmosphere },
		{ "BloomEffect", "Bloom", LightingConfig.Bloom },
		{ "ColorCorrectionEffect", "ColorCorrection", LightingConfig.ColorCorrection },
		{ "SunRaysEffect", "SunRays", LightingConfig.SunRays },
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
	return if skySet then "lighting: the sunset, with its skybox" else "lighting: the sunset (the skybox ids aren't set yet)"
end

return LightingConfig
