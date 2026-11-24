--[[
Effects (client): shared bits for world effects.
  Effects.Reduced()            the player's "reduced effects" setting (halves particles, no camera shake)
  Effects.Count(n)             n particles, halved with reduced effects
  Effects.Shake(strength, seconds)  a camera shake (skipped with reduced effects)
  Effects.Debris(props)        a short-lived loose part flying off (chips, shards, crystals)
  Effects.Sound(name)          a sound effect from AudioConfig (quiet until the game has sound ids)
]]
local Debris = game:GetService("Debris")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local UIKit = require(ReplicatedStorage.UIKit)
local ClientState = require(script.Parent.ClientState)

local Effects = {}

local shakeUntil, shakeStrength = 0, 0
local folder

function Effects.Reduced(): boolean
	local data = ClientState.Data()
	return data ~= nil and data.Settings ~= nil and data.Settings.ReducedEffects == true
end

function Effects.Count(n: number): number
	return if Effects.Reduced() then math.max(1, math.floor(n / 2)) else n
end

function Effects.Shake(strength: number, seconds: number)
	if Effects.Reduced() then
		return
	end
	shakeStrength = math.max(if os.clock() < shakeUntil then shakeStrength else 0, strength)
	shakeUntil = math.max(shakeUntil, os.clock() + seconds)
end

function Effects.Folder(): Folder
	if not folder or not folder.Parent then
		folder = Workspace:FindFirstChild("ClientEffects") or Instance.new("Folder")
		folder.Name = "ClientEffects"
		folder.Parent = Workspace
	end
	return folder
end

-- props: Size, CFrame, Color, Material, Transparency, Velocity, Spin, Life, Shape
function Effects.Debris(props)
	local part = Instance.new("Part")
	part.Size = props.Size or Vector3.one * 0.6
	part.CFrame = props.CFrame
	part.Color = props.Color or Color3.new(1, 1, 1)
	part.Material = props.Material or Enum.Material.Ice
	part.Transparency = props.Transparency or 0
	part.CanCollide = props.CanCollide == true
	part.CanQuery, part.CanTouch = false, false
	part.CastShadow = false
	if props.Shape then
		part.Shape = props.Shape
	end
	part.AssemblyLinearVelocity = props.Velocity or Vector3.zero
	part.AssemblyAngularVelocity = props.Spin or Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 12
	part.Parent = Effects.Folder()
	Debris:AddItem(part, props.Life or 1.2)
	return part
end

function Effects.Sound(name: string)
	pcall(UIKit.PlaySound, name)
end

RunService:BindToRenderStep("IceShake", Enum.RenderPriority.Camera.Value + 1, function()
	local now = os.clock()
	if now < shakeUntil then
		local fade = math.clamp((shakeUntil - now) / 0.4, 0, 1)
		local s = shakeStrength * fade
		local camera = Workspace.CurrentCamera
		camera.CFrame = camera.CFrame * CFrame.new((math.random() - 0.5) * s, (math.random() - 0.5) * s, 0)
			* CFrame.Angles(0, 0, math.rad((math.random() - 0.5) * s * 2))
	end
end)

return Effects
