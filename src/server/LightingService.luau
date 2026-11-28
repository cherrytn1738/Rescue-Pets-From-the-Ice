--[[
LightingService: the game's lighting at the start of every server (LightingConfig: the warm winter sunset), and the
lamps where the low sun leaves things dark (LightingConfig.Lamps):
 * a warm lantern light on the front of both posts of every plot gate;
 * a spotlight over each leaderboard, shining down on its face;
 * a ring of soft warm lights round the plaza, between the paths.
The lamps are invisible anchored parts holding the lights (Workspace.Lamps), so they never block or show.
]]
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local LightingConfig = require(ReplicatedStorage.LightingConfig)
local MapConfig = require(ReplicatedStorage.MapConfig)

local LightingService = {}

local LAMPS = LightingConfig.Lamps

local function holder(parent: Instance, name: string, cframe: CFrame): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Size = Vector3.one * 0.4
	part.CFrame = cframe
	part.Anchored = true
	part.CanCollide, part.CanQuery, part.CanTouch = false, false, false
	part.Transparency = 1
	part.CastShadow = false
	part.Parent = parent
	return part
end

local function pointLight(part: Part, spec)
	local light = Instance.new("PointLight")
	light.Color = spec.Color
	light.Range = spec.Range
	light.Brightness = spec.Brightness
	light.Shadows = false
	light.Parent = part
	return light
end

-- The lamps (once: a second call replaces them).
function LightingService.PlaceLamps()
	local old = Workspace:FindFirstChild("Lamps")
	if old then
		old:Destroy()
	end
	local folder = Instance.new("Folder")
	folder.Name = "Lamps"
	folder.Parent = Workspace
	-- the plot gates: on the front of each post (plot space: the posts stand at the open front, +Z)
	local arch = MapConfig.Arch
	local postX = MapConfig.Border.FrontGap / 2 + arch.PostSize / 2
	local half = MapConfig.PlotSize / 2
	for index = 1, MapConfig.PlotCount do
		local plot = MapConfig.PlotCFrame(index)
		for _, side in { -1, 1 } do
			local at = plot * CFrame.new(side * postX, arch.ClearHeight * LAMPS.Gate.Height, half + arch.PostSize)
			pointLight(holder(folder, `GateLamp{index}{if side < 0 then "Left" else "Right"}`, at), LAMPS.Gate)
		end
	end
	-- the leaderboards: a spotlight above and in front of each board's face, aimed at its middle
	local plaza = Workspace:FindFirstChild("Plaza")
	for _, board in (if plaza then plaza:GetChildren() else {}) do
		local face = board:IsA("Model") and string.sub(board.Name, 1, 5) == "Board" and board:FindFirstChild("Face")
		if face and face:IsA("BasePart") then
			local spec = LAMPS.Leaderboard
			local from = (face.CFrame * CFrame.new(0, face.Size.Y / 2 + spec.Up, -spec.Out)).Position
			local lamp = holder(folder, "BoardLamp" .. string.sub(board.Name, 6), CFrame.lookAt(from, face.Position))
			local light = Instance.new("SpotLight")
			light.Face = Enum.NormalId.Front
			light.Color = spec.Color
			light.Range = spec.Range
			light.Brightness = spec.Brightness
			light.Angle = spec.Angle
			light.Shadows = false
			light.Parent = lamp
		end
	end
	-- the plaza: a ring between the paths (the paths leave towards each plot's front)
	local spec = LAMPS.Plaza
	for k = 1, spec.Count do
		local angle = (k - 0.5) / spec.Count * math.pi * 2
		local at = Vector3.new(math.sin(angle) * spec.Radius, MapConfig.Ground + spec.Height, math.cos(angle) * spec.Radius)
		pointLight(holder(folder, "PlazaLamp" .. k, CFrame.new(at)), spec)
	end
	return folder
end

function LightingService.Start()
	LightingConfig.Apply(Lighting)
	LightingService.PlaceLamps()
end

return LightingService
