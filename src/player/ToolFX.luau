--[[
ToolFX (client): the tools' extras (docs/GAME_DESIGN.md, "The tools' look"), on every player's tool.
 * A swing's extras: the trail during the slash (the swords, and every magical tool; in the tier's spark colour) and a
   drill's bit spinning on the hit. Your own swings call ToolFX.Trail / ToolFX.SpinBit from PickSwing; other players'
   swings are seen through their Animator (AnimationPlayed fires on every client for a character's animations, which
   replicate from its owner), so everyone sees them with no network traffic of ours.
 * The magical tiers (IceLooks.ToolMagic): a soft light in the tool's colour, and the themed hit effect at the strike
   (ToolFX.Hit, from TapFeedback: IceLooks.MagicHits).
 * Your new tool: the "New tool! <name>" banner with the tool spinning in it (Banners: it waits its turn and never
   takes input, so tapping goes on), and a flash on the tool as it appears in your hand.
Reduced effects keeps the tools and drops the trail, the light, the hit effects and the flash's sparkles.
]]
local Debris = game:GetService("Debris")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local EffectsConfig = require(ReplicatedStorage.EffectsConfig)
local IceLooks = require(ReplicatedStorage.IceLooks)
local SwingConfig = require(ReplicatedStorage.SwingConfig)
local UpgradeConfig = require(ReplicatedStorage.UpgradeConfig)
local Banners = require(script.Parent.Banners)
local ClientState = require(script.Parent.ClientState)
local Effects = require(script.Parent.Effects)

local ToolFX = {}

ToolFX.ToolName = "IceTool" -- (PickService's name for the held tool)

local player = Players.LocalPlayer
local WHITE = Color3.new(1, 1, 1)
local GOLD = Color3.fromRGB(255, 200, 60)

local function tierOf(tool: Instance): number
	return tool:GetAttribute("Tier") or 1
end

-- The tool's colour: its tier's sparks (gold with the golden skin).
function ToolFX.Colour(tool: Instance): Color3
	if tool:GetAttribute("Skin") == "Golden" then
		return GOLD
	end
	return IceLooks.ToolSparks[tierOf(tool)] or WHITE
end

-- Does this tool draw a trail when it swings: a sword, or any magical tool.
function ToolFX.HasTrail(tool: Instance, family): boolean
	return family.Trail == true or IceLooks.ToolMagic[tierOf(tool)] ~= nil
end

-- The swing's trail: on from the top of the wind-up to just after the strike. startAt: where the swing started in its
-- animation (seconds); speed: its playback speed; current(): is this swing still the one playing (a swing that's been
-- cut into leaves the trail to the next one).
function ToolFX.Trail(tool: Instance, family, startAt: number, speed: number, current: () -> boolean)
	local swingTrail = tool:FindFirstChild("SwingTrail", true)
	if not swingTrail or not swingTrail:IsA("Trail") or Effects.Reduced() then
		return
	end
	local colour = ToolFX.Colour(tool)
	swingTrail.Color = ColorSequence.new(colour:Lerp(WHITE, 0.4), colour)
	local on = math.max(0, family.WindUpEnd - startAt) / speed
	local off = (family.ImpactAt + SwingConfig.Trail.AfterImpact - startAt) / speed
	task.delay(on, function()
		if current() and swingTrail.Parent then
			swingTrail.Enabled = true
		end
	end)
	task.delay(off, function()
		if current() and swingTrail.Parent then
			swingTrail.Enabled = false
		end
	end)
end

-- A drill's bit spinning after the hit, slowing to a stop: the tool's BitJoint (a Weld whose C0 sits on the bit's
-- axis) turned about Y on this client only.
local spinning = {}
function ToolFX.SpinBit(tool: Instance)
	local joint = tool:FindFirstChild("BitJoint", true)
	if not joint or not joint:IsA("Weld") then
		return
	end
	local spin = spinning[joint]
	if spin then
		spin.left = SwingConfig.BitSpin.Seconds
		return
	end
	spin = { left = SwingConfig.BitSpin.Seconds, angle = 0, base = joint.C0 }
	spinning[joint] = spin
	local connection
	connection = RunService.RenderStepped:Connect(function(dt)
		spin.left -= dt
		if not joint.Parent or spin.left <= 0 then
			joint.C0 = spin.base
			connection:Disconnect()
			spinning[joint] = nil
			return
		end
		spin.angle += SwingConfig.BitSpin.Speed * (spin.left / SwingConfig.BitSpin.Seconds) * dt
		joint.C0 = spin.base * CFrame.Angles(0, spin.angle, 0)
	end)
end

-- The magical tools' hit effects ----------------------------------------------------------------------------

local hitEmitters = {} -- [kind] = { holder, burst, flash }

local function emitterFor(kind: string)
	local made = hitEmitters[kind]
	if made and made.holder.Parent then
		return made
	end
	local spec = IceLooks.MagicHits[kind]
	local holder = Instance.new("Attachment")
	holder.Name = "MagicHit" .. kind
	holder.Parent = workspace.Terrain
	local burst = Instance.new("ParticleEmitter")
	burst.Name = "Burst"
	burst.Texture = EffectsConfig.Texture(spec.Texture)
	burst.Color = ColorSequence.new(spec.Colours[1], spec.Colours[2])
	burst.Rate = 0
	burst.EmissionDirection = Enum.NormalId.Top
	burst.SpreadAngle = Vector2.new(spec.Spread, spec.Spread)
	burst.Speed = NumberRange.new(spec.Speed[1], spec.Speed[2])
	burst.Size = NumberSequence.new(spec.Size[1], spec.Size[2])
	burst.Lifetime = NumberRange.new(spec.Life[1], spec.Life[2])
	burst.Acceleration = Vector3.new(0, -spec.Gravity, 0)
	burst.Drag = 2
	burst.Rotation = NumberRange.new(0, 360)
	burst.RotSpeed = NumberRange.new(-spec.Spin, spec.Spin)
	burst.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.7, 0.15), NumberSequenceKeypoint.new(1, 1) })
	burst.LightEmission = spec.Light
	burst.Brightness = 2
	burst.ZOffset = 1
	burst.Parent = holder
	local flash
	if spec.Flash then
		flash = Instance.new("ParticleEmitter")
		flash.Name = "Flash"
		flash.Texture = EffectsConfig.Texture("SoftGlow")
		flash.Color = ColorSequence.new(spec.Colours[1])
		flash.Rate = 0
		flash.Speed = NumberRange.new(0)
		flash.Lifetime = NumberRange.new(spec.Flash[2])
		flash.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, spec.Flash[1] * 0.4), NumberSequenceKeypoint.new(0.3, spec.Flash[1]),
			NumberSequenceKeypoint.new(1, 0) })
		flash.Transparency = NumberSequence.new(0.2, 1)
		flash.LightEmission = 1
		flash.ZOffset = 1.5
		flash.Parent = holder
	end
	made = { holder = holder, burst = burst, flash = flash, count = spec.Count }
	hitEmitters[kind] = made
	return made
end

-- The magical tier's hit effect where your tap struck (out: the way the chips fly).
function ToolFX.Hit(tier: number, at: Vector3, out: Vector3)
	local magic = IceLooks.ToolMagic[tier]
	if not magic or Effects.Reduced() then
		return
	end
	local made = emitterFor(magic.Hit)
	-- the holder's +Y (the emitters' Top) along `out`
	made.holder.WorldCFrame = CFrame.lookAt(at, at + out) * CFrame.Angles(-math.pi / 2, 0, 0)
	made.burst:Emit(made.count)
	if made.flash then
		made.flash:Emit(1)
	end
end

-- The magical tiers' light ---------------------------------------------------------------------------------

local function dress(tool: Instance)
	if not tool:IsA("Tool") then
		return
	end
	local magic = IceLooks.ToolMagic[tierOf(tool)]
	local handle = tool:FindFirstChild("Handle")
	if not handle then
		return
	end
	local holder = handle:FindFirstChild("Tip") or handle -- (the striking end: the glowing pieces)
	local light = holder:FindFirstChild("MagicLight")
	if magic and not light then
		light = Instance.new("PointLight")
		light.Name = "MagicLight"
		light.Shadows = false
		light.Parent = holder
	end
	if light then
		light.Color = ToolFX.Colour(tool)
		light.Range = if magic then magic.Light[1] else 0
		light.Brightness = if magic then magic.Light[2] else 0
		light.Enabled = magic ~= nil and not Effects.Reduced()
	end
end

-- Other players' swings, through their Animator -------------------------------------------------------------

local variantOf = {} -- [animation id] = variant name
for name, id in SwingConfig.AnimationIds.R15 do
	if id > 0 then
		variantOf["rbxassetid://" .. id] = name
	end
end
local familyOf = {} -- [variant] = family name
for familyName, family in SwingConfig.Families do
	for _, variant in family.Variants do
		familyOf[variant] = familyName
	end
end

local lastSwing = {} -- [character] = os.clock() of its latest swing
local function watchSwings(character: Model)
	local humanoid = character:WaitForChild("Humanoid", 10)
	local animator = humanoid and humanoid:WaitForChild("Animator", 10)
	if not animator then
		return
	end
	animator.AnimationPlayed:Connect(function(track: AnimationTrack)
		local animation = track.Animation
		local variant = animation and variantOf[animation.AnimationId]
		local familyName = variant and familyOf[variant]
		local tool = character:FindFirstChild(ToolFX.ToolName)
		if not familyName or not tool then
			return
		end
		local started = os.clock()
		lastSwing[character] = started
		local current = function()
			return lastSwing[character] == started
		end
		local family = SwingConfig.Family(familyName)
		local speed = math.max(track.Speed, 0.1)
		local startAt = math.clamp(track.TimePosition, 0, family.WindUpEnd)
		if ToolFX.HasTrail(tool, family) then
			ToolFX.Trail(tool, family, startAt, speed, current)
		end
		task.delay(math.max(0, family.ImpactAt - startAt) / speed, function()
			if current() then
				ToolFX.SpinBit(tool)
			end
		end)
	end)
end

-- Your new tool: the banner with the tool spinning, and a flash in your hand -------------------------------------

-- A ViewportFrame over the banner's title with a copy of the tool turning in it. Returns its clean-up.
local function spinningTool(frame: Frame, tool: Tool)
	local viewport = Instance.new("ViewportFrame")
	viewport.Name = "ToolSpin"
	viewport.BackgroundTransparency = 1
	viewport.AnchorPoint = Vector2.new(0.5, 1)
	viewport.Position = UDim2.new(0.5, 0, 0, 14)
	viewport.Size = UDim2.fromOffset(250, 250)
	viewport.Ambient = Color3.fromRGB(175, 180, 195)
	viewport.LightColor = WHITE
	viewport.LightDirection = Vector3.new(-1, -1.5, -1)
	viewport.Parent = frame
	local world = Instance.new("WorldModel")
	world.Parent = viewport
	local model = Instance.new("Model")
	for _, part in tool:GetDescendants() do
		if part:IsA("BasePart") and part.Transparency < 1 then
			local copy = part:Clone()
			for _, child in copy:GetChildren() do
				if not child:IsA("SpecialMesh") and not child:IsA("SurfaceAppearance") then
					child:Destroy() -- (welds, trails, lights: the copy only needs to be seen)
				end
			end
			copy.Anchored = true
			copy.CFrame = part.CFrame
			copy.Parent = model
		end
	end
	model.Parent = world
	local box, size = model:GetBoundingBox()
	local centre = box.Position
	local base = {}
	for _, part in model:GetChildren() do
		base[part] = CFrame.new(-centre) * part.CFrame
	end
	-- the tool's own axes: the handle along the hand's grip; stand it up (its longest side upright) and turn it
	local handle = tool:FindFirstChild("Handle")
	local upright = if handle then (CFrame.new(handle.Position) * handle.CFrame.Rotation):Inverse() else CFrame.identity
	upright = upright - upright.Position
	local camera = Instance.new("Camera")
	camera.FieldOfView = 30
	local reach = math.max(size.X, size.Y, size.Z)
	camera.CFrame = CFrame.lookAt(Vector3.new(0, 0, reach * 2.1), Vector3.zero)
	camera.Parent = viewport
	viewport.CurrentCamera = camera
	local started = os.clock()
	local connection = RunService.RenderStepped:Connect(function()
		local turn = CFrame.Angles(math.rad(-12), (os.clock() - started) * 2.6, 0) * CFrame.Angles(0, 0, math.rad(-20))
		local parts, frames = {}, {}
		for part, offset in base do
			table.insert(parts, part)
			table.insert(frames, turn * upright * offset)
		end
		world:BulkMoveTo(parts, frames, Enum.BulkMoveMode.FireCFrameChanged)
	end)
	return function()
		connection:Disconnect()
		viewport:Destroy()
	end
end

local function flash(tool: Tool, colour: Color3)
	local highlight = Instance.new("Highlight")
	highlight.Name = "NewToolFlash"
	highlight.Adornee = tool
	highlight.FillColor = WHITE
	highlight.OutlineColor = colour
	highlight.FillTransparency = 0.05
	highlight.OutlineTransparency = 0
	highlight.DepthMode = Enum.HighlightDepthMode.Occluded
	highlight.Parent = tool
	TweenService:Create(highlight, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { FillTransparency = 1, OutlineTransparency = 1 }):Play()
	Debris:AddItem(highlight, 0.8)
	local handle = tool:FindFirstChild("Handle")
	local tip = handle and (handle:FindFirstChild("Tip") or handle)
	if tip and not Effects.Reduced() then
		local sparkles = Instance.new("ParticleEmitter")
		sparkles.Texture = EffectsConfig.Texture("Sparkle")
		sparkles.Color = ColorSequence.new(WHITE, colour)
		sparkles.Rate = 0
		sparkles.Speed = NumberRange.new(4, 9)
		sparkles.SpreadAngle = Vector2.new(180, 180)
		sparkles.Size = NumberSequence.new(0.6, 0)
		sparkles.Lifetime = NumberRange.new(0.4, 0.7)
		sparkles.LightEmission = 1
		sparkles.Parent = tip
		sparkles:Emit(16)
		Debris:AddItem(sparkles, 1)
	end
end

local lastTier: number? = nil
local function onOwnTool(tool: Tool)
	local tier = tierOf(tool)
	local previous = lastTier
	lastTier = tier
	if not previous or tier <= previous then
		return -- (joining, a respawn, a rebirth, a new skin: no new tool)
	end
	local info = UpgradeConfig.Tools[tier]
	local colour = IceLooks.ToolSparks[tier] or WHITE
	Banners.Big("New tool!", info and info.Name or "", colour, 2.8, function(frame)
		return spinningTool(frame, tool)
	end)
	flash(tool, colour)
end

-- Every character: dress its tool when it's equipped; others' swings; your new tools.
local function watchCharacter(owner: Player, character: Model)
	local function onChild(child: Instance)
		if child.Name ~= ToolFX.ToolName or not child:IsA("Tool") then
			return
		end
		dress(child)
		child:GetAttributeChangedSignal("Skin"):Connect(function()
			dress(child)
		end)
		if owner == player then
			onOwnTool(child)
		end
	end
	for _, child in character:GetChildren() do
		task.spawn(onChild, child)
	end
	character.ChildAdded:Connect(onChild)
	if owner ~= player then
		task.spawn(watchSwings, character)
	end
end

local function watchPlayer(owner: Player)
	if owner.Character then
		task.spawn(watchCharacter, owner, owner.Character)
	end
	owner.CharacterAdded:Connect(function(character)
		watchCharacter(owner, character)
	end)
end

function ToolFX.Start()
	for _, owner in Players:GetPlayers() do
		watchPlayer(owner)
	end
	Players.PlayerAdded:Connect(watchPlayer)
	Players.PlayerRemoving:Connect(function(owner)
		if owner.Character then
			lastSwing[owner.Character] = nil
		end
	end)
	-- reduced effects on or off: every tool's light follows
	local reduced = Effects.Reduced()
	ClientState.Changed(function()
		if Effects.Reduced() ~= reduced then
			reduced = Effects.Reduced()
			for _, owner in Players:GetPlayers() do
				local tool = owner.Character and owner.Character:FindFirstChild(ToolFX.ToolName)
				if tool then
					dress(tool)
				end
			end
		end
	end)
end

return ToolFX
