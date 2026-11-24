-- The glowing guide line from you to your plot (docs/GAME_DESIGN.md, "Plot and map layout": "a glowing
-- arrow and a short path lead from spawn to the player's plot"). Shown while you're outside your plot;
-- the HOME button takes you straight there.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local MapConfig = require(ReplicatedStorage.MapConfig)

local player = Players.LocalPlayer

local anchor = Instance.new("Part")
anchor.Name = "PlotGuideTarget"
anchor.Anchored, anchor.CanCollide, anchor.CanQuery, anchor.CanTouch = true, false, false, false
anchor.Transparency = 1
anchor.Size = Vector3.one
local targetAttachment = Instance.new("Attachment")
targetAttachment.Parent = anchor
local beam = Instance.new("Beam")
beam.Name = "PlotGuide"
beam.Color = ColorSequence.new(Color3.fromRGB(120, 230, 255), Color3.fromRGB(255, 235, 120))
beam.LightEmission = 1
beam.Width0, beam.Width1 = 0.8, 0.8
beam.FaceCamera = true
beam.Texture = "rbxasset://textures/particles/sparkles_main.dds"
beam.TextureMode = Enum.TextureMode.Wrap
beam.TextureLength = 3
beam.TextureSpeed = 2
beam.Transparency = NumberSequence.new(0.15)
beam.Attachment1 = targetAttachment
beam.Parent = anchor

local marker -- a tall light column over your plot's entrance
local function ensureMarker(index: number)
	if marker and marker:GetAttribute("Index") == index then
		return
	end
	if marker then
		marker:Destroy()
	end
	marker = Instance.new("Part")
	marker.Name = "HomeMarker"
	marker.Anchored, marker.CanCollide, marker.CanQuery, marker.CanTouch = true, false, false, false
	marker.Material = Enum.Material.Neon
	marker.Color = Color3.fromRGB(255, 235, 120)
	marker.Transparency = 0.55
	marker.Shape = Enum.PartType.Cylinder
	marker.Size = Vector3.new(60, 2.5, 2.5)
	marker.CFrame = CFrame.new(MapConfig.PlotPoint(index, MapConfig.TapSpot.X, MapConfig.PlotSize / 2, 30)) * CFrame.Angles(0, 0, math.rad(90))
	marker:SetAttribute("Index", index)
	marker.Parent = Workspace
end

RunService.Heartbeat:Connect(function()
	local index = player:GetAttribute("PlotIndex")
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if type(index) ~= "number" or not root then
		anchor.Parent = nil
		return
	end
	ensureMarker(index)
	local localPos = MapConfig.PlotCFrame(index):PointToObjectSpace(root.Position)
	local half = MapConfig.PlotSize / 2
	local inside = math.abs(localPos.X) <= half and math.abs(localPos.Z) <= half
	marker.Transparency = if inside then 1 else 0.55
	if inside then
		anchor.Parent = nil
		return
	end
	local rootAttachment = root:FindFirstChild("PlotGuideAttachment")
	if not rootAttachment then
		rootAttachment = Instance.new("Attachment")
		rootAttachment.Name = "PlotGuideAttachment"
		rootAttachment.Position = Vector3.new(0, -2, 0)
		rootAttachment.Parent = root
	end
	beam.Attachment0 = rootAttachment
	anchor.CFrame = CFrame.new(MapConfig.PlotPoint(index, MapConfig.TapSpot.X, MapConfig.TapSpot.Z, 1))
	anchor.Parent = Workspace
end)
