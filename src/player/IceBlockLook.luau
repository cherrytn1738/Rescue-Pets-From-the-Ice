--[[
IceBlockLook (client): the redesigned ice block, drawn over IceBlocks' plain block (docs/GAME_DESIGN.md, "The ice
block"; settings in IceLooks.New). Part 1 of the redesign: three looks for the developer to choose from, built in
Blender (tools/blender/ice_block.py) and shown only in Studio with the client switch Workspace "StudioIceOption"
= "A", "B" or "C"; without it nothing here runs and every block keeps its classic look.

A look is the template ReplicatedStorage.IceTemplates.IceBlock<option> (copied there by IceBlockService), scaled
to the block's height and welded to IceBlocks' block part (which stays the invisible hitbox and still moves with
the sled and the shudder), plus:
 - a soft round glow in the rarity colour behind the creature: a camera-facing Beam (unlit, drawn among the
   ice's see-through parts; a BillboardGui or SurfaceGui behind the ice was hidden by it), moved every frame to
   stay behind the creature from every side; and a rim light on the creature (a Highlight's outline);
 - drifting motes in the rarity colour (Rare and up), a little frost mist rolling out round the base, and a slow
   shimmer band sweeping across the faces (a scrolling Texture on the shell);
 - the crack lines of each crack stage (the template's Crack1-4), and the frost thinning as the cracks grow.
The reduced-effects setting halves the motes and the mist.
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local EffectsConfig = require(ReplicatedStorage.EffectsConfig)
local IceLooks = require(ReplicatedStorage.IceLooks)
local Effects = require(script.Parent.Effects)

local IceBlockLook = {}

local SETTINGS = IceLooks.New
local SHIMMER_FACES = { Enum.NormalId.Front, Enum.NormalId.Back, Enum.NormalId.Left, Enum.NormalId.Right }

-- The look this client shows: "A", "B" or "C" (Studio only, the StudioIceOption switch), or nil for the classic one.
function IceBlockLook.Option(): string?
	if not RunService:IsStudio() then
		return nil
	end
	local option = Workspace:GetAttribute("StudioIceOption")
	if type(option) ~= "string" or not table.find(IceLooks.Options, option) then
		return nil
	end
	local templates = ReplicatedStorage:FindFirstChild("IceTemplates")
	return if templates and templates:FindFirstChild("IceBlock" .. option) then option else nil
end

local function weld(block: BasePart, part: BasePart)
	part.Anchored = false
	part.Massless = true
	part.CanCollide, part.CanQuery, part.CanTouch = false, false, false
	local w = Instance.new("WeldConstraint")
	w.Part0, w.Part1 = block, part
	w.Parent = part
end

local function emitter(parent: Instance, name: string): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Name = name
	e.Parent = parent
	return e
end

-- Removes a look (a new block, another option, or the classic look again).
function IceBlockLook.Clear(view)
	local look = view.look
	if not look then
		return
	end
	view.glow.Parent = view.core -- (the block's light moved to the look's centre: keep it)
	look.model:Destroy()
	for _, thing in look.extras do
		thing:Destroy()
	end
	view.look = nil
end

-- Builds the look for the view's current block: the block part (view.block) is already sized and placed.
function IceBlockLook.Build(view, option: string, height: number, rarity: string)
	IceBlockLook.Clear(view)
	local template = ReplicatedStorage.IceTemplates:FindFirstChild("IceBlock" .. option)
	local model = template:Clone()
	model:ScaleTo(height / IceLooks.TemplateHeight)
	model:PivotTo(view.block.CFrame * CFrame.new(0, -height / 2, 0))
	local look = { model = model, option = option, height = height, shells = {}, inners = {}, cracks = {}, parts = {}, extras = {}, shimmer = {} }
	for _, part in model:GetDescendants() do
		if part:IsA("BasePart") then
			weld(view.block, part)
			table.insert(look.parts, part)
			local role = part:GetAttribute("Role")
			local stage = role and tonumber(string.match(role, "^Crack(%d)$"))
			if stage then
				look.cracks[stage] = part
			elseif role == "Shell" then
				table.insert(look.shells, part)
				part.Color = SETTINGS.ShellTint[option] or part.Color
			elseif role == "Inner" then
				table.insert(look.inners, part)
			end
		end
	end
	model.Parent = view.folder

	-- the shimmer: a soft band scrolled across the shell's faces
	local tile = height * SETTINGS.Shimmer.TileHeights
	for _, shell in look.shells do
		for index, face in SHIMMER_FACES do
			local texture = Instance.new("Texture")
			texture.Name = "Shimmer"
			texture.Face = face
			texture.Texture = IceLooks.Textures.Shimmer or ""
			texture.StudsPerTileU, texture.StudsPerTileV = tile, tile
			texture.Transparency = SETTINGS.Shimmer.Transparency
			texture.Parent = shell
			table.insert(look.shimmer, { texture = texture, phase = index * 0.17 })
		end
	end

	-- the glow behind the creature, and the creature's light, at its middle
	local centre = Instance.new("Attachment")
	centre.Name = "LookCentre"
	centre.Position = Vector3.new(0, -height / 2 + height * SETTINGS.CreatureCentre, 0)
	centre.Parent = view.block
	table.insert(look.extras, centre)
	local glowSize = height * SETTINGS.Glow.Size
	local bottom, top = Instance.new("Attachment"), Instance.new("Attachment")
	bottom.Name, top.Name = "GlowBottom", "GlowTop"
	bottom.Parent, top.Parent = view.block, view.block
	table.insert(look.extras, bottom)
	table.insert(look.extras, top)
	local beam = Instance.new("Beam")
	beam.Name = "RarityGlow"
	beam.Attachment0, beam.Attachment1 = bottom, top
	beam.FaceCamera = true
	beam.Segments = 1
	beam.Width0, beam.Width1 = glowSize, glowSize
	beam.Texture = IceLooks.Textures.Glow or ""
	beam.TextureMode = Enum.TextureMode.Stretch
	beam.TextureLength = 1
	beam.LightInfluence = 0
	beam.LightEmission = 1
	beam.Brightness = SETTINGS.Glow.Brightness
	beam.Parent = view.block
	table.insert(look.extras, beam)
	look.glowBeam, look.glowBottom, look.glowTop, look.glowSize = beam, bottom, top, glowSize
	look.centre = centre
	view.glow.Parent = centre

	-- drifting motes inside the block (the block part's box), and mist rolling out round the base
	local motes = emitter(view.block, "Motes")
	motes.Texture = EffectsConfig.Texture("SoftGlow")
	motes.Shape = Enum.ParticleEmitterShape.Box
	motes.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	motes.Lifetime = NumberRange.new(SETTINGS.Motes.Lifetime[1], SETTINGS.Motes.Lifetime[2])
	motes.Speed = NumberRange.new(SETTINGS.Motes.Speed[1], SETTINGS.Motes.Speed[2])
	motes.SpreadAngle = Vector2.new(180, 180)
	motes.Acceleration = Vector3.new(0, 0.12, 0)
	motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.25, SETTINGS.Motes.Size), NumberSequenceKeypoint.new(1, 0) })
	motes.Transparency = NumberSequence.new(0.15)
	motes.LightEmission = 1
	motes.Brightness = 2
	table.insert(look.extras, motes)
	look.motes = motes
	local mistSource = Instance.new("Part")
	mistSource.Name = "MistSource"
	mistSource.Transparency = 1
	mistSource.Size = Vector3.new(view.block.Size.X * 1.02, 0.4, view.block.Size.Z * 1.02)
	mistSource.CFrame = view.block.CFrame * CFrame.new(0, -height / 2 + 0.4, 0)
	mistSource.CastShadow = false
	weld(view.block, mistSource)
	mistSource.Parent = view.folder
	table.insert(look.extras, mistSource)
	local mist = emitter(mistSource, "Mist")
	mist.Texture = EffectsConfig.Texture("SmokePuff")
	mist.Shape = Enum.ParticleEmitterShape.Cylinder
	mist.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
	mist.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
	mist.EmissionDirection = Enum.NormalId.Top
	mist.Lifetime = NumberRange.new(SETTINGS.Mist.Lifetime[1], SETTINGS.Mist.Lifetime[2])
	mist.Speed = NumberRange.new(SETTINGS.Mist.Speed[1], SETTINGS.Mist.Speed[2])
	mist.Drag = 0.6
	mist.Acceleration = Vector3.new(0, 0.1, 0)
	mist.Rotation = NumberRange.new(0, 360)
	mist.RotSpeed = NumberRange.new(-12, 12)
	mist.Size = NumberSequence.new(SETTINGS.Mist.Size[1], SETTINGS.Mist.Size[2])
	mist.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, SETTINGS.Mist.Transparency), NumberSequenceKeypoint.new(1, 1) })
	mist.Color = ColorSequence.new(Color3.fromRGB(212, 234, 255)) -- (a touch of blue: pure white is lost on the snow)
	mist.LightInfluence = 1
	look.mist = mist

	view.look = look
	IceBlockLook.SetCreature(view)
end

-- The creature's rim light (a Highlight's outline in the rarity colour), once its silhouette is built; the glow
-- centres on the creature's middle.
function IceBlockLook.SetCreature(view)
	local look = view.look
	local sil = view.silhouette
	if not look or not sil then
		return
	end
	-- (just built, the creature stands on the block's base; IceBlocks lifts it by CreatureLift every frame)
	local box = sil.model:GetBoundingBox()
	local middle = view.block.CFrame:PointToObjectSpace(box.Position)
	look.centre.Position = Vector3.new(0, middle.Y + look.height * SETTINGS.CreatureLift, 0)
	if look.rim then
		look.rim:Destroy()
	end
	local rim = Instance.new("Highlight")
	rim.Name = "RimLight"
	rim.DepthMode = Enum.HighlightDepthMode.Occluded
	rim.FillTransparency = SETTINGS.Rim.FillTransparency
	rim.OutlineTransparency = SETTINGS.Rim.OutlineTransparency
	rim.Adornee = sil.model
	rim.Parent = sil.model
	look.rim = rim
end

-- Every frame: visibility, cracks and frost by stage, the glow, motes and rim by rarity, the shimmer.
function IceBlockLook.Update(view, present: boolean, stage: number, rarity: string, now: number)
	local look = view.look
	if not look then
		return
	end
	local hidden = if present then 0 else 1
	for _, part in look.parts do
		part.LocalTransparencyModifier = hidden
	end
	for index, crack in look.cracks do
		crack.Transparency = if stage >= index then 0 else 1
	end
	local thin = SETTINGS.ThinPerStage * math.clamp(stage, 0, 4)
	for _, shell in look.shells do
		shell.Transparency = SETTINGS.ShellTransparency + thin
	end
	for _, inner in look.inners do
		inner.Transparency = SETTINGS.ShellTransparency + thin * 1.5
	end

	-- the rarity: Common shows no glow and no motes; the glow brightens at the last crack stage
	local glow = IceLooks.Glow[rarity]
	local colour = IceLooks.RarityColors[rarity] or Color3.new(1, 1, 1)
	local strength = if glow then 1 else 0
	if glow and glow.Mode == "Pulse" then
		strength *= 0.75 + 0.25 * math.sin(now * 3)
	elseif glow and glow.Mode == "Rainbow" then
		colour = Color3.fromHSV((now * 0.15) % 1, 0.7, 1)
	end
	if stage >= 4 then
		strength *= 1.25
	end
	-- the glow: a camera-facing beam from below the creature's middle to above it, set back behind the creature
	local camera = Workspace.CurrentCamera
	local toCamera = view.block.CFrame:VectorToObjectSpace(camera.CFrame.Position - look.centre.WorldPosition)
	toCamera = Vector3.new(toCamera.X, 0, toCamera.Z)
	toCamera = if toCamera.Magnitude > 1e-3 then toCamera.Unit else Vector3.zAxis
	local middle = look.centre.Position - toCamera * look.height * SETTINGS.Glow.Behind
	look.glowBottom.Position = middle - Vector3.new(0, look.glowSize / 2, 0)
	look.glowTop.Position = middle + Vector3.new(0, look.glowSize / 2, 0)
	look.glowBeam.Enabled = present and strength > 0
	look.glowBeam.Color = ColorSequence.new(colour:Lerp(Color3.new(1, 1, 1), SETTINGS.Glow.Whiten))
	look.glowBeam.Transparency = NumberSequence.new(1 - (1 - SETTINGS.Glow.Transparency) * math.clamp(strength, 0, 1))
	local reduced = Effects.Reduced()
	look.motes.Enabled = present and glow ~= nil
	look.motes.Rate = SETTINGS.Motes.Rate * (if reduced then EffectsConfig.Rules.ReducedAmbient else 1)
	look.motes.Color = ColorSequence.new(colour)
	look.mist.Enabled = present
	look.mist.Rate = SETTINGS.Mist.Rate * (if reduced then EffectsConfig.Rules.ReducedAmbient else 1)
	if look.rim then
		look.rim.Enabled = present
		look.rim.OutlineColor = if glow then colour:Lerp(Color3.new(1, 1, 1), SETTINGS.Rim.Whiten) else Color3.fromRGB(225, 240, 255)
		look.rim.FillColor = colour
	end

	-- the shimmer sweeps across each face in turn
	local tile = look.height * SETTINGS.Shimmer.TileHeights
	for _, s in look.shimmer do
		s.texture.OffsetStudsU = ((now / SETTINGS.Shimmer.Period + s.phase) % 1) * tile
		s.texture.Transparency = if present then SETTINGS.Shimmer.Transparency else 1
	end
end

return IceBlockLook
