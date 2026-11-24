--[[
RescueMoment (client): your own rescue (docs/GAME_DESIGN.md, "The rescue moment"). The shatter itself
plays for everyone (IceBlocks); for the owner the creature then shakes off the frost, a banner shows its
rarity, it shrinks from its size in the ice to pet size and runs to you. The server already gave the
pet (PetService); this is the show. New layers get their banner and the ground shakes.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local IceLooks = require(ReplicatedStorage.IceLooks)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local PetAnimator = require(ReplicatedStorage.Pets.PetAnimator)
local PetLooks = require(ReplicatedStorage.Pets.PetLooks)
local Banners = require(script.Parent.Banners)
local ClientState = require(script.Parent.ClientState)
local Effects = require(script.Parent.Effects)
local IceBlocks = require(script.Parent.IceBlocks)

local RescueMoment = {}

local player = Players.LocalPlayer

local function frostPuff(position: Vector3)
	for _ = 1, Effects.Count(10) do
		Effects.Debris({
			Size = Vector3.one * (0.4 + math.random() * 0.5),
			CFrame = CFrame.new(position + Vector3.new((math.random() - 0.5) * 3, math.random() * 3, (math.random() - 0.5) * 3)),
			Color = Color3.fromRGB(240, 250, 255),
			Material = Enum.Material.Snow,
			Velocity = Vector3.new((math.random() - 0.5) * 8, 6 + math.random() * 6, (math.random() - 0.5) * 8),
			Life = 0.9,
		})
	end
end

local function play(creatureId: string, view)
	local data = PetLooks.Data(creatureId)
	local clips = PetLooks.Clips(creatureId)
	if not data then
		return
	end
	local start = view.base * CFrame.new(0, 0.2, 0)
	local model = PetLooks.Build(creatureId, start, "Normal")
	if not model then
		return
	end
	local petHeight = model:GetExtentsSize().Y
	local bigScale = (view.block.Size.Y * IceLooks.SilhouetteShare) / math.max(petHeight, 0.5)
	model:ScaleTo(bigScale)
	model.Parent = Effects.Folder()
	local animator = clips and PetAnimator.new(model, data, clips)
	if animator then
		animator:Play("Cheer", true, 0.1)
	end
	frostPuff(start.Position + Vector3.new(0, 2, 0))
	Effects.Sound("RescueJingle")

	local t0 = os.clock()
	local connection
	connection = RunService.RenderStepped:Connect(function(dt)
		local t = os.clock() - t0
		if not model.Parent then
			connection:Disconnect()
			return
		end
		if animator then
			pcall(animator.Step, animator, dt)
		end
		if t < 1.1 then
			-- shake off the frost, then shrink to pet size
			local shrink = math.clamp((t - 0.35) / 0.6, 0, 1)
			local scale = bigScale + (1 - bigScale) * (1 - (1 - shrink) ^ 2)
			if math.abs(model:GetScale() - scale) > 1e-3 then
				model:ScaleTo(scale)
			end
			local shiver = if t < 0.4 then CFrame.Angles(0, 0, math.rad(math.sin(t * 60) * 6)) else CFrame.identity
			model:PivotTo(start * shiver)
		elseif t < 3.0 then
			-- run to the player
			if model:GetScale() ~= 1 then
				model:ScaleTo(1)
			end
			if animator and animator.Name ~= "Hop" then
				animator:Play("Hop", true, 0.15)
			end
			local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
			local target = if root then root.Position - Vector3.new(0, 2.9, 0) else start.Position
			local here = model:GetPivot().Position
			local toward = target - here
			local flat = Vector3.new(toward.X, 0, toward.Z)
			local step = math.min(flat.Magnitude, 26 * dt)
			if flat.Magnitude > 3 then
				local nextPos = here + flat.Unit * step
				local y = here.Y + (target.Y - here.Y) * math.min(1, dt * 4)
				model:PivotTo(CFrame.lookAt(Vector3.new(nextPos.X, y, nextPos.Z), Vector3.new(target.X, y, target.Z)))
			end
		else
			frostPuff(model:GetPivot().Position)
			model:Destroy()
			connection:Disconnect()
		end
	end)
end

function RescueMoment.Start()
	local pendingCreature = nil
	ClientState.Event("Rescue", function(payload)
		local creature = CreatureConfig.Get(payload.CreatureId)
		if not creature then
			return
		end
		local color = IceLooks.RarityColors[creature.Rarity]
		local subtitle = `{string.upper(creature.Rarity)}  ·  +{NumberFormat.Short(payload.Burst or 0)} crystals`
		if payload.First then
			subtitle = "NEW!  " .. subtitle
		end
		Banners.Big(creature.Name .. " rescued!", subtitle, color, 2.8)
		if payload.InventoryFull then
			Banners.Toast("Your pet inventory is full (50). Delete some pets to keep new ones.", Color3.fromRGB(255, 120, 120))
		end
		if creature.Rarity == "Epic" or creature.Rarity == "Legendary" or creature.Rarity == "Mythic" then
			Effects.Sound("BigFanfare")
		end
		pendingCreature = payload.CreatureId
	end)
	IceBlocks.OnShatter(function(plotIndex, creatureId, view)
		if plotIndex == player:GetAttribute("PlotIndex") and creatureId then
			play(creatureId, view)
		end
	end)
	ClientState.Event("NewLayer", function(payload)
		Banners.Big(`Layer {payload.Layer}: {payload.Name}`, "Rarer creatures ahead", Color3.fromRGB(150, 225, 255), 3)
		Effects.Shake(1.1, 1.2)
		Effects.Sound("NewLayer")
	end)
	ClientState.Event("Announce", function(payload)
		Banners.Toast(payload.Text, IceLooks.RarityColors[payload.Rarity])
	end)
	return pendingCreature
end

return RescueMoment
