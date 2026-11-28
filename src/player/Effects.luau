--[[
Effects (client): shared bits for world effects.
  Effects.Reduced()            the player's "reduced effects" setting (halves particles, no camera shake)
  Effects.Count(n)             n particles, halved with reduced effects
  Effects.Shake(strength, seconds)  a camera shake (skipped with reduced effects)
  Effects.Dip(depth, seconds)  the camera dips down and comes back up (a new layer; skipped with reduced effects)
  Effects.Nudge(depth, seconds) a tiny jolt down and back (the pick's impact; skipped with reduced effects)
  Effects.Debris(props)        a short-lived loose part flying off (chips, shards, crystals)
  Effects.Sound(name)          a sound effect from AudioConfig (quiet until the game has sound ids)
]]
local Debris = game:GetService("Debris")
local PhysicsService = game:GetService("PhysicsService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local MapConfig = require(ReplicatedStorage.MapConfig)
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

local nudgeStart, nudgeSeconds, nudgeDepth = 0, 0, 0
function Effects.Nudge(depth: number, seconds: number)
	if Effects.Reduced() then
		return
	end
	nudgeStart, nudgeSeconds, nudgeDepth = os.clock(), seconds, depth
end

local dipStart, dipSeconds, dipDepth = 0, 0, 0
function Effects.Dip(depth: number, seconds: number)
	if Effects.Reduced() then
		return
	end
	dipStart, dipSeconds, dipDepth = os.clock(), seconds, depth
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
-- A flying piece's collision group: it passes through the ring round the ice (MapConfig.BlockRing) but still
-- bounces on the ground. (The group is registered by the server; until it replicates the piece stays Default.)
function Effects.DebrisGroup(part: BasePart)
	local group = MapConfig.BlockRing.DebrisGroup
	if PhysicsService:IsCollisionGroupRegistered(group) then
		part.CollisionGroup = group
	end
end

function Effects.Debris(props)
	local part = Instance.new("Part")
	part.Size = props.Size or Vector3.one * 0.6
	part.CFrame = props.CFrame
	part.Color = props.Color or Color3.new(1, 1, 1)
	part.Material = props.Material or Enum.Material.Ice
	part.Transparency = props.Transparency or 0
	part.CanCollide = props.CanCollide == true
	part.CanQuery, part.CanTouch = false, false
	if part.CanCollide then
		Effects.DebrisGroup(part) -- (flies through the invisible ring round the ice)
	end
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
	if now - dipStart < dipSeconds then
		local share = math.sin(math.pi * (now - dipStart) / dipSeconds) -- down and back up
		local camera = Workspace.CurrentCamera
		camera.CFrame = camera.CFrame * CFrame.new(0, -dipDepth * share, 0) * CFrame.Angles(math.rad(-6 * share), 0, 0)
	end
	if now - nudgeStart < nudgeSeconds then
		local share = math.sin(math.pi * (now - nudgeStart) / nudgeSeconds)
		local camera = Workspace.CurrentCamera
		camera.CFrame = camera.CFrame * CFrame.new(0, -nudgeDepth * share, nudgeDepth * 0.5 * share)
	end
	if now < shakeUntil then
		local fade = math.clamp((shakeUntil - now) / 0.4, 0, 1)
		local s = shakeStrength * fade
		local camera = Workspace.CurrentCamera
		camera.CFrame = camera.CFrame * CFrame.new((math.random() - 0.5) * s, (math.random() - 0.5) * s, 0)
			* CFrame.Angles(0, 0, math.rad((math.random() - 0.5) * s * 2))
	end
end)

return Effects
