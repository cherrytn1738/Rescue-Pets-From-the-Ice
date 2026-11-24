--[[
PetViewport (client): a creature's 3D picture in a UI tile (the Pets panel, the Creature Book), built
from its voxel model in any look (Normal, Golden, Silhouette).
  local view = PetViewport.new(parent, creatureId, look)  -- a ViewportFrame filling parent
  view:SetLook(look)   view:Destroy()
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PetLooks = require(ReplicatedStorage.Pets.PetLooks)

local PetViewport = {}
PetViewport.__index = PetViewport

function PetViewport.new(parent: GuiObject, creatureId: string, look: string?)
	local self = setmetatable({}, PetViewport)
	local frame = Instance.new("ViewportFrame")
	frame.Name = "Viewport"
	frame.BackgroundTransparency = 1
	frame.Size = UDim2.fromScale(1, 1)
	frame.Ambient = Color3.fromRGB(170, 180, 200)
	frame.LightColor = Color3.fromRGB(255, 255, 255)
	frame.LightDirection = Vector3.new(-1, -1.4, -1)
	frame.ZIndex = (parent :: any).ZIndex + 1
	frame.Parent = parent
	local camera = Instance.new("Camera")
	camera.FieldOfView = 30
	camera.Parent = frame
	frame.CurrentCamera = camera
	self.frame, self.camera, self.creatureId = frame, camera, creatureId
	local model = PetLooks.Build(creatureId, CFrame.Angles(0, math.rad(200), 0), look or "Normal")
	if model then
		model.Parent = frame
		local size = model:GetExtentsSize()
		local radius = math.max(size.X, size.Y, size.Z) * 0.62
		local centre = Vector3.new(0, size.Y / 2, 0)
		local distance = radius / math.tan(math.rad(camera.FieldOfView / 2)) * 1.05
		camera.CFrame = CFrame.lookAt(centre + Vector3.new(0.1, 0.3, 0.95).Unit * distance, centre)
		self.model = model
		self.data = PetLooks.Data(creatureId)
	end
	return self
end

function PetViewport:SetLook(look: string)
	if self.model and self.data then
		PetLooks.Apply(self.model, self.data, look)
	end
end

function PetViewport:Destroy()
	self.frame:Destroy()
end

return PetViewport
