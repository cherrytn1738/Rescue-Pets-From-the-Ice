--[[
LightingService: the day-night cycle's server side (LightingConfig: Day -> PinkDusk -> Night). The server only says
when this server's cycle started and how fast it runs; every client applies its own lighting from that
(DayNight.client), so the cycle costs no network traffic and everyone switches together. Workspace attributes:
 * DayCycleStart: the server time (Workspace:GetServerTimeNow()) the cycle started. A new server starts at a random
   point in the day look.
 * DayCycleSpeed: 1, or the debug menu's fast cycle (the whole cycle in LightingConfig.Cycle.FastSeconds).
 * DayCycleLook: a look the debug menu forced on the whole server (none: the cycle runs).
At start the server's own Lighting gets the fixed look (LightingConfig.Default), and the lamps go in (Workspace.Lamps,
invisible anchored parts holding the lights, which the clients turn on for dusk and night):
 * a warm lantern light on the front of both posts of every plot gate;
 * a spotlight over each leaderboard, shining down on its face;
 * a ring of soft warm lights round the plaza, between the paths;
 * on every plot, a light inside the gate and one by each front corner of the stage.
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
	-- every plot: inside the gate and by the stage (plot space)
	local plotSpec = LAMPS.Plot
	for index = 1, MapConfig.PlotCount do
		for k, spot in plotSpec.Spots do
			local at = MapConfig.PlotPoint(index, spot.X, spot.Z, spot.Height)
			pointLight(holder(folder, `PlotLamp{index}_{k}`, CFrame.new(at)), plotSpec)
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

local function speedNow(): number
	local speed = Workspace:GetAttribute("DayCycleSpeed")
	return if type(speed) == "number" and speed > 0 then speed else 1
end

-- Forces a look on the whole server (the debug menu), or none (nil: the cycle runs again). False for an unknown look.
function LightingService.SetLook(name: string?): boolean
	if name ~= nil and not LightingConfig.Presets[name] then
		return false
	end
	Workspace:SetAttribute("DayCycleLook", name)
	return true
end

-- The debug menu's fast cycle (the whole cycle in LightingConfig.Cycle.FastSeconds) on or off. The cycle carries on
-- from the same point: the start moves so the current look and its progress stay where they are.
function LightingService.SetFast(on: boolean)
	local now = Workspace:GetServerTimeNow()
	local start = Workspace:GetAttribute("DayCycleStart") or now
	local progress = (now - start) * speedNow()
	local speed = if on then LightingConfig.CycleSeconds() / LightingConfig.Cycle.FastSeconds else 1
	Workspace:SetAttribute("DayCycleSpeed", speed)
	Workspace:SetAttribute("DayCycleStart", now - progress / speed)
end

function LightingService.Start()
	LightingConfig.Apply(Lighting)
	LightingService.PlaceLamps()
	-- a random point in the day look
	local day = LightingConfig.Cycle.Minutes[LightingConfig.Cycle.Order[1]] * 60
	Workspace:SetAttribute("DayCycleSpeed", 1)
	Workspace:SetAttribute("DayCycleStart", Workspace:GetServerTimeNow() - math.random() * day)
end

return LightingService
