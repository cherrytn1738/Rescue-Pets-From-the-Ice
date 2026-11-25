--[[
lighting.luau: the place's lighting (run once in Edit mode from the command bar or MCP execute_luau, then
save the place: Lighting lives in the place file). A bright snowy afternoon that gives the models depth:
Future lighting with soft shadows, a light blue Atmosphere, sky-lit diffuse and specular, subtle Bloom (only
Neon and the brightest highlights glow) and a light ColorCorrection. The snow is held under white by the
exposure and the ambient, so the HUD stays readable over it.

Lighting.Technology can't be set from a script without plugin access: if the report says so, set
Lighting > Technology = Future in the Properties window by hand.
]]
local Lighting = game:GetService("Lighting")
local report = {}

local ok = pcall(function()
	Lighting.Technology = Enum.Technology.Future
end)
table.insert(report, if ok then "Technology = Future" else "Technology: SET BY HAND (Lighting > Technology = Future)")

Lighting.ClockTime = 14.8 -- an afternoon sun, low enough to throw shadows across the models
Lighting.GeographicLatitude = 30
Lighting.Brightness = 2.6
Lighting.ExposureCompensation = -0.15 -- keeps the snow from blowing out to white
Lighting.Ambient = Color3.fromRGB(70, 78, 92)
Lighting.OutdoorAmbient = Color3.fromRGB(128, 142, 165) -- the cool fill of a snowy day (shadows stay blue, not black)
Lighting.EnvironmentDiffuseScale = 0.55 -- the sky lights the shaded sides: rounder shapes
Lighting.EnvironmentSpecularScale = 0.75 -- soft sky reflections on metal and gloss
Lighting.GlobalShadows = true
Lighting.ShadowSoftness = 0.35
Lighting.ColorShift_Top = Color3.fromRGB(255, 244, 226) -- a little warmth on the sunlit tops
Lighting.ColorShift_Bottom = Color3.fromRGB(0, 0, 0)

local function effect(className: string, name: string)
	local e = Lighting:FindFirstChild(name)
	if e and not e:IsA(className) then
		e:Destroy()
		e = nil
	end
	if not e then
		e = Instance.new(className)
		e.Name = name
		e.Parent = Lighting
	end
	return e
end

local atmosphere = effect("Atmosphere", "Atmosphere")
atmosphere.Density = 0.3
atmosphere.Offset = 0.12
atmosphere.Color = Color3.fromRGB(205, 224, 245)
atmosphere.Decay = Color3.fromRGB(120, 146, 182)
atmosphere.Glare = 0.15
atmosphere.Haze = 0.8

-- Post-processing, kept subtle: a soft wide bloom only on Neon and the brightest highlights, a little more
-- contrast and saturation than the raw render, and light sun rays. (DepthOfField stays off.)
local bloom = effect("BloomEffect", "Bloom")
bloom.Enabled = true
bloom.Intensity = 0.35
bloom.Size = 30
bloom.Threshold = 1.7

local grade = effect("ColorCorrectionEffect", "ColorCorrection")
grade.Enabled = true
grade.Brightness = 0.01
grade.Contrast = 0.12
grade.Saturation = 0.16
grade.TintColor = Color3.fromRGB(250, 252, 255)

local rays = effect("SunRaysEffect", "SunRays")
rays.Enabled = true
rays.Intensity = 0.05
rays.Spread = 0.5

local focus = Lighting:FindFirstChildOfClass("DepthOfFieldEffect")
if focus then
	focus.Enabled = false
end

table.insert(report, "lighting set: save the place")
return table.concat(report, "\n")
