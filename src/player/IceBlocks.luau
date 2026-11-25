--[[
IceBlocks (client): draws every plot's ice block from the attributes the server puts on
Workspace.Plots.PlotN.Block (IceBlockService): Present, Level, Layer, CreatureId, Rarity, Hp, HpMax,
Stage (crack stage 0-4), ArriveAt, Rescued and RescueCount. Display only (docs/GAME_DESIGN.md, "The ice
block"; the look is in IceLooks):

 - the ice in its layer's look (colour, material, frost), sized by level (BlockRules.Height);
 - the creature inside: its own voxel model in the Silhouette look at 60% of the block's height;
 - its rarity glow from the moment the block arrives (a light and a soft aura; Legendary pulses,
   Mythic cycles through the rainbow);
 - the crack stages: 20% hairline cracks, 40% chunks fall off (the shape is clear), 60% the eyes show and
   blink, 80% it wiggles, the glow brightens and a heartbeat plays;
 - (the HP bar, the crack %, the level and layer and the rarity are on your HUD while you're in your plot:
   HUD.client; nothing floats above the block, where it covered the ice);
 - the next block sliding in on its sled; the shatter (shards and a crystal fountain) for everyone, and
   for the owner the rescue moment (RescueMoment);
 - the sounds (AudioConfig, SoundRules): your own block's crack stages, shatter and rescue jingle, and now
   and then a quiet chip as your buildings hit it; from other plots only Legendary and Mythic rescue
   jingles, quieter, within AudioConfig.Rules.OtherPlots.MaxDistance studs.
IceBlocks.Hit(plotIndex, strength) makes a block shudder (your taps: TapFeedback).
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Audio = require(ReplicatedStorage.Audio)
local AudioConfig = require(ReplicatedStorage.AudioConfig)
local BlockRules = require(ReplicatedStorage.BlockRules)
local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local IceLooks = require(ReplicatedStorage.IceLooks)
local LayerConfig = require(ReplicatedStorage.LayerConfig)
local MapConfig = require(ReplicatedStorage.MapConfig)
local PetLooks = require(ReplicatedStorage.Pets.PetLooks)
local SoundRules = require(ReplicatedStorage.SoundRules)
local Effects = require(script.Parent.Effects)

local IceBlocks = {}

local player = Players.LocalPlayer
local views = {} -- [plot] = view
local rescueListeners = {}
local container
local chipGate = SoundRules.ChipGate(AudioConfig.Rules.BuildingChip, math.random)
local lastOwnTapAt = -math.huge -- (IceBlocks.Hit on your own plot: a tap)

-- How far the camera's subject (your character, or the camera) is from a point, in studs.
local function listenerDistance(point: Vector3): number
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	local from = if root then root.Position else Workspace.CurrentCamera.CFrame.Position
	return (from - point).Magnitude
end

local function containerFolder()
	if not container or not container.Parent then
		container = Instance.new("Folder")
		container.Name = "ClientIce"
		container.Parent = Workspace
	end
	return container
end

-- callback(plotIndex, creatureId, view) when a block shatters (RescueMoment listens for the owner's).
function IceBlocks.OnShatter(callback)
	table.insert(rescueListeners, callback)
end

-- Pieces welded to the block move with it (the shudder, the sled).
local function weldTo(block: BasePart, part: BasePart)
	part.Anchored = false
	part.Massless = true
	part.CanCollide, part.CanQuery, part.CanTouch = false, false, false
	part.CastShadow = false
	local weld = Instance.new("WeldConstraint")
	weld.Part0, weld.Part1 = block, part
	weld.Parent = part
	part.Parent = block
end

-- Cracks: thin white lines on the block's sides, in four groups (one per crack stage), placed by a
-- seed so a block always cracks the same way.
local CRACKS_PER_STAGE = { 6, 9, 10, 12 }
local function makeCracks(view, size: Vector3, seed: number)
	if view.cracks then
		for _, group in view.cracks do
			for _, part in group do
				part:Destroy()
			end
		end
	end
	view.cracks = {}
	local rng = Random.new(seed)
	local block = view.block
	local faces = {
		{ normal = Vector3.zAxis, right = Vector3.xAxis, half = size.Z / 2, w = size.X },
		{ normal = -Vector3.zAxis, right = -Vector3.xAxis, half = size.Z / 2, w = size.X },
		{ normal = Vector3.xAxis, right = -Vector3.zAxis, half = size.X / 2, w = size.Z },
		{ normal = -Vector3.xAxis, right = Vector3.zAxis, half = size.X / 2, w = size.Z },
		{ normal = Vector3.yAxis, right = Vector3.xAxis, half = size.Y / 2, w = size.X, top = true },
	}
	for stage, count in CRACKS_PER_STAGE do
		local group = {}
		for _ = 1, count do
			local face = faces[rng:NextInteger(1, #faces)]
			local length = size.Y * (0.12 + 0.05 * stage) * (0.6 + rng:NextNumber() * 0.8)
			local thick = 0.1 + 0.05 * stage
			local up = if face.top then Vector3.zAxis else Vector3.yAxis
			local across = rng:NextNumber(-0.42, 0.42) * face.w
			local height = if face.top then rng:NextNumber(-0.4, 0.4) * size.Z else rng:NextNumber(-0.42, 0.42) * size.Y
			local centre = face.normal * (face.half + 0.03) + face.right * across + up * height
			local angle = rng:NextNumber(-1.2, 1.2)
			local part = Instance.new("Part")
			part.Name = "Crack"
			part.Size = Vector3.new(thick, length, 0.06)
			part.Color = Color3.fromRGB(240, 252, 255)
			part.Material = Enum.Material.SmoothPlastic
			part.Transparency = 1
			local frame = CFrame.fromMatrix(centre, face.right, up)
			part.CFrame = block.CFrame * frame * CFrame.Angles(0, 0, angle)
			weldTo(block, part)
			table.insert(group, part)
		end
		view.cracks[stage] = group
	end
end

local function makeExtras(view, size: Vector3, layer: number, seed: number)
	if view.extras then
		view.extras:Destroy()
	end
	local look = IceLooks.Layers[layer] or IceLooks.Layers[1]
	local extras = Instance.new("Folder")
	extras.Name = "Extras"
	extras.Parent = view.block
	view.extras = extras
	local rng = Random.new(seed + 7)
	if look.Extra == "Bubbles" then
		for _ = 1, Effects.Count(14) do
			local bubble = Instance.new("Part")
			bubble.Shape = Enum.PartType.Ball
			bubble.Size = Vector3.one * rng:NextNumber(0.4, 1.1)
			bubble.Color = Color3.fromRGB(230, 245, 255)
			bubble.Material = Enum.Material.Glass
			bubble.Transparency = 0.45
			bubble.CFrame = view.block.CFrame * CFrame.new(rng:NextNumber(-0.42, 0.42) * size.X, rng:NextNumber(-0.45, 0.45) * size.Y, rng:NextNumber(-0.42, 0.42) * size.Z)
			weldTo(view.block, bubble)
			bubble.Parent = extras
		end
	elseif look.Extra == "Veins" or look.Extra == "InnerLight" then
		for _ = 1, 8 do
			local vein = Instance.new("Part")
			vein.Size = Vector3.new(0.18, size.Y * rng:NextNumber(0.25, 0.55), 0.18)
			vein.Color = look.VeinColor
			vein.Material = Enum.Material.Neon
			vein.Transparency = 0.2
			vein.CFrame = view.block.CFrame * CFrame.new(rng:NextNumber(-0.4, 0.4) * size.X, rng:NextNumber(-0.3, 0.3) * size.Y, rng:NextNumber(-0.4, 0.4) * size.Z)
				* CFrame.Angles(rng:NextNumber(-1, 1), rng:NextNumber(0, 6), rng:NextNumber(-1, 1))
			weldTo(view.block, vein)
			vein.Parent = extras
		end
		if look.Extra == "InnerLight" then
			local light = Instance.new("PointLight")
			light.Color = look.VeinColor
			light.Brightness = 2
			light.Range = 16
			light.Parent = view.core
			light.Name = "InnerLight"
			light:SetAttribute("Extra", true)
		end
	elseif look.Extra == "Sparkles" then
		local sparkles = Instance.new("ParticleEmitter")
		sparkles.Name = "Sparkles"
		sparkles.Texture = "rbxasset://textures/particles/sparkles_main.dds"
		sparkles.Rate = if Effects.Reduced() then 3 else 7
		sparkles.Lifetime = NumberRange.new(0.6, 1.2)
		sparkles.Speed = NumberRange.new(0)
		sparkles.Size = NumberSequence.new(0.6, 0)
		sparkles.LightEmission = 1
		sparkles.Color = ColorSequence.new(Color3.fromRGB(220, 250, 255))
		local attachment = Instance.new("Attachment")
		attachment.Parent = view.core
		sparkles.Parent = view.block
	end
	-- an inner light left over from the last layer goes
	if look.Extra ~= "InnerLight" then
		local old = view.core:FindFirstChild("InnerLight")
		if old then
			old:Destroy()
		end
	end
end

local function buildSilhouette(view, creatureId: string, height: number)
	if view.silhouette then
		view.silhouette.model:Destroy()
		view.silhouette = nil
	end
	local data = PetLooks.Data(creatureId)
	if not data then
		return
	end
	local model = PetLooks.Build(creatureId, view.base, "Silhouette")
	if not model then
		return
	end
	local petHeight = model:GetExtentsSize().Y
	local scale = (height * IceLooks.SilhouetteShare) / math.max(petHeight, 0.5)
	model:ScaleTo(scale)
	for _, part in model:GetDescendants() do
		if part:IsA("BasePart") then
			part.CanCollide, part.CanQuery, part.CanTouch = false, false, false
			part.CastShadow = false
		end
	end
	model.Parent = view.folder
	view.silhouette = { model = model, data = data, creatureId = creatureId, eyes = false }
end

local function makeView(plot: Model)
	local index = plot:GetAttribute("Index")
	local base = MapConfig.BlockBase(index)
	local folder = Instance.new("Folder")
	folder.Name = "IceView" .. index
	folder.Parent = containerFolder()
	local block = Instance.new("Part")
	block.Name = "IceBlock"
	block.Anchored = true
	block.Size = Vector3.new(10, 14, 10)
	block.CFrame = base
	block.CastShadow = true
	block.Parent = folder
	local core = Instance.new("Part")
	core.Name = "Core"
	core.Transparency = 1
	core.Size = Vector3.one
	core.CFrame = base
	weldTo(block, core)
	local glow = Instance.new("PointLight")
	glow.Name = "Glow"
	glow.Enabled = false
	glow.Shadows = false
	glow.Parent = core
	local aura = Instance.new("Part")
	aura.Name = "Aura"
	aura.Shape = Enum.PartType.Ball
	aura.Material = Enum.Material.Neon
	aura.Transparency = 1
	aura.Size = Vector3.one * 6
	aura.CFrame = base
	weldTo(block, aura)
	local view = {
		plot = plot,
		index = index,
		folder = folder,
		attrs = plot:WaitForChild("Block"),
		base = base * CFrame.Angles(0, math.pi, 0), -- the creature faces the plot's open front (+Z)
		block = block,
		core = core,
		glow = glow,
		aura = aura,
		shake = 0,
		key = nil, -- level..creature: rebuild cracks and silhouette when it changes
		stage = 0,
		present = false,
		slideStart = -math.huge,
		rescueCount = plot.Block:GetAttribute("RescueCount") or 0,
		lastHp = nil,
		heartbeatAt = 0,
	}
	views[plot] = view
	return view
end

local function shatter(view, creatureId: string)
	local block = view.block
	local size = block.Size
	local look = IceLooks.Layers[view.layer or 1] or IceLooks.Layers[1]
	local origin = block.Position
	for _ = 1, Effects.Count(IceLooks.Particles.Shards) do
		local offset = Vector3.new((math.random() - 0.5) * size.X, (math.random() - 0.5) * size.Y, (math.random() - 0.5) * size.Z)
		local out = Vector3.new(offset.X, 0, offset.Z).Unit
		if out ~= out then
			out = Vector3.xAxis
		end
		Effects.Debris({
			Size = Vector3.new(math.random() * 1.6 + 0.6, math.random() * 1.6 + 0.6, math.random() * 0.6 + 0.3),
			CFrame = CFrame.new(origin + offset) * CFrame.Angles(math.random() * 6, math.random() * 6, 0),
			Color = look.Color,
			Material = look.Material,
			Transparency = 0.25,
			Velocity = out * (18 + math.random() * 18) + Vector3.new(0, 14 + math.random() * 16, 0),
			CanCollide = true,
			Life = 1.8,
		})
	end
	-- the crystal fountain
	for i = 1, Effects.Count(IceLooks.Particles.Fountain) do
		task.delay(i * 0.02, function()
			Effects.Debris({
				Size = Vector3.one * (0.5 + math.random() * 0.4),
				CFrame = CFrame.new(origin + Vector3.new(0, size.Y * 0.3, 0)) * CFrame.Angles(0, math.random() * 6, math.rad(45)),
				Color = Color3.fromRGB(120, 230, 255),
				Material = Enum.Material.Neon,
				Velocity = Vector3.new((math.random() - 0.5) * 22, 34 + math.random() * 20, (math.random() - 0.5) * 22),
				CanCollide = true,
				Life = 2.2,
			})
		end)
	end
	-- the sound: your own block's shatter and jingle; another plot's jingle only for the rarest, nearby
	local isMine = view.plot:GetAttribute("Owner") == player.UserId
	if isMine then
		Effects.Sound("Shatter")
	end
	local creature = creatureId and CreatureConfig.Get(creatureId)
	local jingle, volume = SoundRules.RescueCue(isMine, creature and creature.Rarity, listenerDistance(origin), AudioConfig.Rules.OtherPlots)
	if jingle then
		task.delay(AudioConfig.Rules.JingleDelay, Audio.Play, jingle, { Volume = volume })
	end
	for _, callback in rescueListeners do
		task.spawn(callback, view.index, creatureId, view)
	end
end

local function update(view, dt: number)
	local attrs = view.attrs
	local present = attrs:GetAttribute("Present") == true
	local level = attrs:GetAttribute("Level") or 1
	local layer = attrs:GetAttribute("Layer") or 1
	local hp = attrs:GetAttribute("Hp") or 0
	local creatureId = attrs:GetAttribute("CreatureId")
	local rarity = attrs:GetAttribute("Rarity") or "Common"
	local stage = attrs:GetAttribute("Stage") or 0
	local isMine = view.plot:GetAttribute("Owner") == player.UserId
	local look = IceLooks.Layers[layer] or IceLooks.Layers[1]
	local height = BlockRules.Height(level)
	local size = Vector3.new(height * IceLooks.BlockWidthShare, height, height * IceLooks.BlockWidthShare)

	-- a rescue: shatter
	local rescues = attrs:GetAttribute("RescueCount") or 0
	if rescues ~= view.rescueCount then
		view.rescueCount = rescues
		shatter(view, attrs:GetAttribute("Rescued"))
	end

	-- a new block: its look, cracks, silhouette
	local key = `{level}:{creatureId}:{layer}`
	if present and creatureId and key ~= view.key then
		view.key = key
		view.layer = layer
		view.block.Size = size
		view.block.CFrame = view.base * CFrame.new(0, height / 2 - 0.5, 0)
		makeCracks(view, size, level * 131 + #creatureId)
		makeExtras(view, size, layer, level)
		buildSilhouette(view, creatureId, height)
		view.stage = 0
	end
	if present and not view.present then
		view.slideStart = os.clock() -- the sled brings it in
	end
	view.present = present

	-- building hits make it shudder a little (taps shake it harder: Hit); on your own block, now and then a
	-- quiet chip (none just after your own tap: its sound covers it)
	if view.lastHp and hp < view.lastHp - 1e-9 and present then
		view.shake = math.max(view.shake, 0.08)
		if chipGate:Allow(os.clock(), isMine, lastOwnTapAt) then
			Audio.Play("BuildingChip")
		end
	end
	view.lastHp = hp

	-- the crack stage moment (owner: a louder crack and a camera nudge; chunks fall at 40%)
	if stage ~= view.stage then
		if stage > view.stage and present then
			if isMine then
				Effects.Sound("Crack" .. math.clamp(stage, 1, 4))
				Effects.Shake(0.35, 0.25)
			end
			if stage >= 2 and view.stage < 2 then
				for _ = 1, Effects.Count(5) do
					local top = view.block.CFrame * CFrame.new((math.random() - 0.5) * size.X, size.Y / 2, (math.random() - 0.5) * size.Z)
					Effects.Debris({ Size = Vector3.one * (1 + math.random() * 1.4), CFrame = top, Color = look.Color, Material = look.Material,
						Transparency = 0.2, Velocity = Vector3.new((math.random() - 0.5) * 10, 6, (math.random() - 0.5) * 10), CanCollide = true, Life = 2.5 })
				end
			end
		end
		view.stage = stage
	end

	-- where it is: on the mound, sliding in from behind, or out of sight
	view.shake = math.max(0, view.shake - dt * 5)
	local now = os.clock()
	local wobble = if view.shake > 0 then CFrame.Angles(math.rad(math.sin(now * 61) * view.shake * 2.5), 0, math.rad(math.cos(now * 53) * view.shake * 2.5)) else CFrame.identity
	local slide = math.clamp((now - view.slideStart) / IceLooks.SledSeconds, 0, 1)
	local eased = 1 - (1 - slide) ^ 3
	local sledOffset = CFrame.new(0, 0, (1 - eased) * IceLooks.SledDistance) -- (view.base is turned to face the front: +Z here is the back)
	local blockCF = view.base * sledOffset * CFrame.new(0, height / 2 - 0.5, 0) * wobble
	view.block.CFrame = blockCF
	view.block.CanCollide = present
	view.block.Color = look.Color
	view.block.Material = look.Material
	local frost = look.Transparency + (look.Clear - look.Transparency) * (stage / 4)
	view.block.Transparency = if present then frost else 1

	-- cracks by stage
	for index, group in view.cracks or {} do
		local visible = present and stage >= index
		for _, part in group do
			part.Transparency = if visible then 0.15 else 1
		end
	end
	if view.extras then
		for _, part in view.extras:GetChildren() do
			if part:IsA("BasePart") then
				part.LocalTransparencyModifier = if present then 0 else 1
			end
		end
	end

	-- the creature inside: wiggles at 80%, eyes from 60% (blinking)
	local sil = view.silhouette
	if sil then
		local wiggle = if stage >= 4 then CFrame.Angles(0, math.rad(math.sin(now * 9) * 8), math.rad(math.sin(now * 13) * 5)) else CFrame.identity
		sil.model:PivotTo(view.base * sledOffset * CFrame.new(0, 0.2, 0) * wiggle * (if present then CFrame.identity else CFrame.new(0, -500, 0)))
		local eyesOn = present and stage >= 3 and (now % 3.2) > 0.18
		if eyesOn ~= sil.eyes then
			sil.eyes = eyesOn
			PetLooks.ShowEyes(sil.model, sil.data, eyesOn)
		end
	end

	-- the rarity glow (from the start); brighter at 80%
	local glow = IceLooks.Glow[rarity]
	if glow and present then
		local boost = if stage >= 4 then IceLooks.GlowBoostAtStage4 else 1
		local color = glow.Color
		local brightness = glow.Brightness * boost
		if glow.Mode == "Pulse" then
			brightness *= 0.65 + 0.35 * math.sin(now * 3)
		elseif glow.Mode == "Rainbow" then
			color = Color3.fromHSV((now * 0.15) % 1, 0.75, 1)
		end
		view.glow.Enabled = true
		view.glow.Color, view.glow.Brightness, view.glow.Range = color, brightness, glow.Range
		view.aura.Color = color
		view.aura.Size = Vector3.one * height * 0.55
		view.aura.Transparency = math.clamp(0.88 - 0.05 * brightness / glow.Brightness, 0.7, 0.92)
	else
		view.glow.Enabled = false
		view.aura.Transparency = 1
	end

	-- the heartbeat at 80% (your own block)
	if isMine and present and stage >= 4 and now >= view.heartbeatAt then
		view.heartbeatAt = now + 1.1
		Effects.Sound("Heartbeat")
	end
end

-- A tap or a building hit: the block shudders.
function IceBlocks.Hit(plotIndex: number, strength: number?)
	local view = IceBlocks.View(plotIndex)
	if view then
		view.shake = math.min(1, view.shake + (strength or 0.35))
		if view.plot:GetAttribute("Owner") == player.UserId then
			lastOwnTapAt = os.clock()
		end
	end
end

function IceBlocks.View(plotIndex: number)
	for plot, view in views do
		if view.index == plotIndex then
			return view
		end
	end
	return nil
end

function IceBlocks.Start()
	local plots = Workspace:WaitForChild("Plots")
	local function add(plot)
		if plot:IsA("Model") and not views[plot] then
			task.spawn(makeView, plot)
		end
	end
	plots.ChildAdded:Connect(add)
	for _, plot in plots:GetChildren() do
		add(plot)
	end
	RunService.RenderStepped:Connect(function(dt)
		for _, view in views do
			local ok, err = pcall(update, view, dt)
			if not ok then
				warn("[IceBlocks] " .. tostring(err))
			end
		end
	end)
end

return IceBlocks
