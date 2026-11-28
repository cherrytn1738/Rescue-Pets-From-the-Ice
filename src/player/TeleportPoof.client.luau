-- The PLOT button's teleport, as everyone nearby sees it (GameEvent "Teleported" from PlazaService: { UserId, From, To }):
-- a poof of snow and a quick white flash where the player left and where they arrived. Within
-- GameConfig.Teleport.PoofRange studs of the camera only; none at all with reduced effects (Effects.Reduced).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage.GameConfig)
local ClientState = require(script.Parent.ClientState)
local Effects = require(script.Parent.Effects)

local SNOW = Color3.fromRGB(240, 248, 255)
local PIECES = 14
local FLASH_SECONDS = 0.35

local function poof(at: Vector3)
	-- a burst of snow out of the ground round the feet
	for index = 1, PIECES do
		local angle = index / PIECES * math.pi * 2
		local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
		Effects.Debris({
			Size = Vector3.one * (0.6 + math.random() * 0.7),
			CFrame = CFrame.new(at + out * 1.2 + Vector3.new(0, -1.5 + math.random(), 0)),
			Color = SNOW,
			Material = Enum.Material.Snow,
			Transparency = 0.1,
			Velocity = out * (10 + math.random() * 6) + Vector3.new(0, 9 + math.random() * 7, 0),
			Life = 0.9,
		})
	end
	-- a soft white flash that swells and fades
	local flash = Instance.new("Part")
	flash.Name = "TeleportFlash"
	flash.Shape = Enum.PartType.Ball
	flash.Anchored = true
	flash.CanCollide, flash.CanQuery, flash.CanTouch = false, false, false
	flash.CastShadow = false
	flash.Material = Enum.Material.Neon
	flash.Color = SNOW
	flash.Transparency = 0.35
	flash.Size = Vector3.one * 2
	flash.CFrame = CFrame.new(at)
	flash.Parent = Effects.Folder()
	TweenService:Create(flash, TweenInfo.new(FLASH_SECONDS, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 7, Transparency = 1 }):Play()
	task.delay(FLASH_SECONDS + 0.05, function()
		flash:Destroy()
	end)
end

ClientState.Event("Teleported", function(payload)
	if type(payload) ~= "table" or Effects.Reduced() then
		return
	end
	local camera = Workspace.CurrentCamera
	for _, at in { payload.From, payload.To } do
		if typeof(at) == "Vector3" and camera and (camera.CFrame.Position - at).Magnitude <= GameConfig.Teleport.PoofRange then
			poof(at)
		end
	end
end)
