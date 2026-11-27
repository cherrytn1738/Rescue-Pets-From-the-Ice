--[[
IceBlockLook (client): the ice block's look, drawn over IceBlocks' plain block part, which stays the hitbox and still
moves with the sled and the shudder (docs/GAME_DESIGN.md, "The ice block"; every setting in IceLooks).

A block is built from the kit ReplicatedStorage.IceTemplates.Kit (tools/blender/ice_block.py; IceBlockService copies
it from ServerStorage): the body and its crack lines, one of three shape variants (snow cap, icicles and base crystals,
bubbles), the layer's extra (Fresh Snow's drifts, Ancient Ice's dense bubbles, Crystal Ice's clusters, the veins of
Primordial Ice and the Frozen Core) and, on a Mythic Block bought with Robux, the glowing corner crystal clusters. Its
parts take the layer's atlas, are scaled to the block's height and moved with the block every frame (so a tap can
squash it). On top:
 - the creature: a frosty outline in the rarity colour (a Highlight outline; soft white for Common), two glowing eyes
   that blink, and at crack stages 3 and 4 a little of its real colours through the frost;
 - the glow behind the creature (a camera-facing beam set back behind it; Common none), drifting motes (Epic and up),
   base mist, a shimmer sweeping across the faces, the crack lines of each stage and the frost thinning;
 - the rarity aura (IceLooks.Auras): a soft ring of light behind the block (beams: seen across the plaza), Epic's purple
   wisps, Legendary's flames, embers, pulse and light rays, Mythic's rainbow, spiralling sparkles and bright pulses;
 - chunks breaking off at each crack stage, the pre-cut pieces flung apart on a rescue, and the aura's burst.
Particles follow the effect rules (EffectsRules.AmbientScale: your plot at full rate, others at half within 60 studs,
none beyond; reduced effects halves them and drops the rays, flames and spirals). The beams (glow, ring, rays) are
not particles and always show, so a rare block is seen from across the plaza.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local EffectsConfig = require(ReplicatedStorage.EffectsConfig)
local EffectsRules = require(ReplicatedStorage.EffectsRules)
local IceLooks = require(ReplicatedStorage.IceLooks)
local PetLooks = require(ReplicatedStorage.Pets.PetLooks)
local Effects = require(script.Parent.Effects)

local IceBlockLook = {}

local SETTINGS = IceLooks.New
local AURAS = IceLooks.Auras
local SHIMMER_FACES = { Enum.NormalId.Front, Enum.NormalId.Back, Enum.NormalId.Left, Enum.NormalId.Right }
local DEFAULT_EYES = { EY = true, IR = true, WH = true, SH = true, PU = true }
local player = Players.LocalPlayer

local function kit(): Model?
	local templates = ReplicatedStorage:FindFirstChild("IceTemplates")
	return templates and templates:FindFirstChild("Kit")
end

-- Whether the kit is here (without it, IceBlocks keeps the classic look).
function IceBlockLook.Available(): boolean
	return kit() ~= nil
end

-- Loads every layer's atlas and the aura textures up front (a block whose atlas hasn't loaded shows grey).
function IceBlockLook.Preload()
	local ids = {}
	for _, id in IceLooks.Textures do
		table.insert(ids, id)
	end
	pcall(function()
		game:GetService("ContentProvider"):PreloadAsync(ids)
	end)
end

local function make(className: string, parent: Instance, props)
	local thing = Instance.new(className)
	for key, value in props do
		thing[key] = value
	end
	thing.Parent = parent
	return thing
end

local function range(pair): NumberRange
	return NumberRange.new(pair[1], pair[2])
end

-- How much of a particle effect runs on this block (the effect rules), refreshed every CheckSeconds.
local function ruleScale(view): number
	local isOwn = view.plot:GetAttribute("Owner") == player.UserId
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	local from = if root then root.Position else Workspace.CurrentCamera.CFrame.Position
	return EffectsRules.AmbientScale(isOwn, (from - view.block.Position).Magnitude, Effects.Reduced())
end

local function rarityColour(rarity: string, now: number): Color3
	local info = IceLooks.Rarities[rarity] or IceLooks.Rarities.Common
	if info.Rainbow then
		return Color3.fromHSV((now / IceLooks.Creature.RainbowSeconds) % 1, 0.65, 1)
	end
	return info.Colour
end

-- Removes a look (a new block, or the classic look again).
function IceBlockLook.Clear(view)
	local look = view.look
	if not look then
		return
	end
	view.glow.Parent = view.core -- (the block's light moved to the look's centre: keep it)
	look.folder:Destroy()
	for _, thing in look.extras do
		thing:Destroy()
	end
	view.look = nil
end

-- A camera-facing beam between two new attachments on the block part.
local function newBeam(look, block: BasePart, name: string, props)
	local a0 = make("Attachment", block, { Name = name .. "A" })
	local a1 = make("Attachment", block, { Name = name .. "B" })
	table.insert(look.extras, a0)
	table.insert(look.extras, a1)
	props.Name, props.Attachment0, props.Attachment1 = name, a0, a1
	props.FaceCamera, props.Segments, props.LightInfluence = true, 1, 0
	props.TextureMode, props.TextureLength = Enum.TextureMode.Stretch, 1
	local beam = make("Beam", block, props)
	table.insert(look.extras, beam)
	return { beam = beam, a0 = a0, a1 = a1 }
end

local function newEmitter(look, parent: Instance, name: string, rate: number, props)
	props.Name = name
	local e = make("ParticleEmitter", parent, props)
	table.insert(look.extras, e)
	table.insert(look.emitters, { emitter = e, rate = rate })
	return e
end

-- Builds the look for the view's current block (the block part is already sized and placed).
function IceBlockLook.Build(view, height: number, layerNumber: number, rarity: string, variant: number, mythic: boolean)
	IceBlockLook.Clear(view)
	local layerLook = IceLooks.LayerLooks[layerNumber] or IceLooks.LayerLooks[1]
	local atlas = IceLooks.Textures[layerLook.Atlas] or ""
	local roles = { "Shell", "Crack1", "Crack2", "Crack3", "Crack4", `V{variant}Snow` }
	if not layerLook.NoCrystals and not mythic then
		table.insert(roles, `V{variant}Crystals`)
	end
	table.insert(roles, if layerLook.DenseBubbles then "DenseBubbles" else `V{variant}Inner`)
	if layerLook.Extra then
		table.insert(roles, layerLook.Extra)
	end
	if mythic then
		table.insert(roles, "MythicGlass")
		table.insert(roles, "MythicGlow")
	end

	local scale = height / IceLooks.TemplateHeight
	local folder = make("Folder", view.folder, { Name = "IceLook" })
	local look = {
		folder = folder, height = height, scale = scale, layer = layerLook, rarity = rarity, mythic = mythic, atlas = atlas,
		parts = {}, offsets = {}, sizes = {}, shells = {}, inners = {}, cracks = {}, glows = {}, extras = {}, emitters = {},
		shimmer = {}, rays = {}, orbiters = {}, alpha = 1, ruleAt = 0, rule = 1, pulseAt = 0, lastPivot = nil,
	}
	local pivot = view.block.CFrame * CFrame.new(0, -height / 2, 0)
	local source = kit()
	for _, role in roles do
		local template = source and source:FindFirstChild("Ice" .. role)
		if not template then
			continue
		end
		local part = template:Clone()
		local offset = CFrame.new(template.Position * scale) * template.CFrame.Rotation
		part.Size = template.Size * scale
		part.Anchored = true
		part.CanCollide, part.CanQuery, part.CanTouch = false, false, false
		if part.TextureID ~= "" then
			part.TextureID = atlas
		end
		if role == "Veins" then
			part.Color = layerLook.VeinColor or part.Color
		end
		part.CFrame = pivot * offset
		part.Parent = folder
		table.insert(look.parts, part)
		table.insert(look.offsets, offset)
		table.insert(look.sizes, part.Size)
		local stage = tonumber(string.match(role, "^Crack(%d)$"))
		if stage then
			look.cracks[stage] = part
		elseif role == "Shell" then
			table.insert(look.shells, part)
		elseif role == "DenseBubbles" or string.match(role, "Inner$") then
			table.insert(look.inners, part)
		elseif role == "MythicGlow" then
			table.insert(look.glows, part)
		end
	end

	-- the shimmer: a soft band scrolled across the shell's faces
	local tile = height * SETTINGS.Shimmer.TileHeights
	for _, shell in look.shells do
		for index, face in SHIMMER_FACES do
			local texture = make("Texture", shell, { Name = "Shimmer", Face = face, Texture = IceLooks.Textures.Shimmer or "",
				StudsPerTileU = tile, StudsPerTileV = tile, Transparency = SETTINGS.Shimmer.Transparency })
			table.insert(look.shimmer, { texture = texture, phase = index * 0.17 })
		end
	end

	-- the creature's middle: the glow behind it and the block's light
	local block = view.block
	look.centre = make("Attachment", block, { Name = "LookCentre", Position = Vector3.new(0, -height / 2 + height * 0.36, 0) })
	table.insert(look.extras, look.centre)
	view.glow.Parent = look.centre
	look.glowSize = height * SETTINGS.Glow.Size
	look.glowBeam = newBeam(look, block, "RarityGlow", { Width0 = look.glowSize, Width1 = look.glowSize, Texture = IceLooks.Textures.Glow or "",
		LightEmission = layerLook.GlowEmission or 1, Brightness = layerLook.GlowBrightness or 1.5 })
	if layerLook.InnerLight then
		look.innerLight = make("PointLight", look.centre, { Name = "InnerLight", Color = layerLook.InnerLight, Brightness = 1.6, Range = height * 1.1, Shadows = false })
	end

	-- drifting motes, Crystal Ice's sparkles, mist rolling out round the base
	look.motes = newEmitter(look, block, "Motes", SETTINGS.Motes.Rate, {
		Texture = EffectsConfig.Texture("SoftGlow"), Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
		Lifetime = range(SETTINGS.Motes.Lifetime), Speed = range(SETTINGS.Motes.Speed), SpreadAngle = Vector2.new(180, 180),
		Acceleration = Vector3.new(0, 0.12, 0), LightEmission = 1, Brightness = 2, Transparency = NumberSequence.new(0.15),
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.25, SETTINGS.Motes.Size), NumberSequenceKeypoint.new(1, 0) }),
	})
	if layerLook.Sparkles then
		newEmitter(look, block, "Sparkles", SETTINGS.Sparkles.Rate, {
			Texture = EffectsConfig.Texture("Sparkle"), Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
			Lifetime = NumberRange.new(0.5, 1), Speed = NumberRange.new(0), LightEmission = 1, Color = ColorSequence.new(Color3.fromRGB(225, 252, 255)),
			Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.4, 0.7), NumberSequenceKeypoint.new(1, 0) }),
		})
	end
	local mistSource = make("Part", view.folder, { Name = "MistSource", Transparency = 1, Anchored = true, CanCollide = false, CanQuery = false,
		CanTouch = false, CastShadow = false, Size = Vector3.new(block.Size.X * 1.02, 0.4, block.Size.Z * 1.02) })
	table.insert(look.extras, mistSource)
	look.mistSource = mistSource
	newEmitter(look, mistSource, "Mist", SETTINGS.Mist.Rate, {
		Texture = EffectsConfig.Texture("SmokePuff"), Shape = Enum.ParticleEmitterShape.Cylinder, ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward,
		ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface, Lifetime = range(SETTINGS.Mist.Lifetime), Speed = range(SETTINGS.Mist.Speed), Drag = 0.6,
		Acceleration = Vector3.new(0, 0.1, 0), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-12, 12),
		Size = NumberSequence.new(SETTINGS.Mist.Size[1], SETTINGS.Mist.Size[2]), Color = ColorSequence.new(Color3.fromRGB(212, 234, 255)),
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, SETTINGS.Mist.Transparency), NumberSequenceKeypoint.new(1, 1) }),
	})

	-- the rarity aura (a Mythic Block always wears the Mythic one: it should look special whatever it holds)
	local aura = AURAS[rarity]
	if mythic and rarity ~= "Legendary" then
		aura = AURAS.Mythic
	end
	look.aura = aura
	if aura then
		local size = height * aura.Halo
		look.halo = newBeam(look, block, "AuraRing", { Width0 = size, Width1 = size, Texture = IceLooks.Textures.Halo or "",
			LightEmission = AURAS.HaloEmission, Brightness = AURAS.HaloBrightness })
		look.haloSize = size
		-- flames and wisps come off a box a little wider than the block, so they show outside the ice, not under its frost
		local auraBox = make("Part", view.folder, { Name = "AuraBox", Transparency = 1, Anchored = true, CanCollide = false, CanQuery = false,
			CanTouch = false, CastShadow = false, Size = block.Size * Vector3.new(AURAS.ParticleBox, 1.05, AURAS.ParticleBox) })
		table.insert(look.extras, auraBox)
		look.auraBox = auraBox
		local surface = { Shape = Enum.ParticleEmitterShape.Box, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface, EmissionDirection = Enum.NormalId.Top, ZOffset = 1 }
		local function on(props)
			for key, value in surface do
				props[key] = value
			end
			return props
		end
		if aura.Wisps then
			newEmitter(look, auraBox, "Wisps", aura.Wisps.Rate, on({
				Texture = EffectsConfig.Texture("SmokePuff"), Lifetime = NumberRange.new(1.6, 2.6), Speed = NumberRange.new(0.8, 1.8),
				Acceleration = Vector3.new(0, 1.6, 0), Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-20, 20), LightEmission = 0.15,
				Color = ColorSequence.new(aura.Wisps.Colour), Size = NumberSequence.new(1.6, 4.2),
				Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.2, 0.35), NumberSequenceKeypoint.new(1, 1) }),
			}))
		end
		if aura.Flames then
			look.flames = newEmitter(look, auraBox, "Flames", aura.Flames.Rate, on({
				Texture = IceLooks.Textures.Flame or "", Lifetime = NumberRange.new(0.45, 0.9), Speed = NumberRange.new(1.5, 3.2),
				Acceleration = Vector3.new(0, 3, 0), LightEmission = 0.3, Brightness = 1.4,
				Color = ColorSequence.new(aura.Flames.Colour, aura.Flames.Tip),
				Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.2), NumberSequenceKeypoint.new(0.3, 3.4), NumberSequenceKeypoint.new(0.55, 2.6),
					NumberSequenceKeypoint.new(0.75, 3.0), NumberSequenceKeypoint.new(1, 0.4) }),
				Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(0.3, 0.12), NumberSequenceKeypoint.new(1, 1) }),
			}))
			newEmitter(look, auraBox, "Embers", aura.Embers.Rate, on({
				Texture = EffectsConfig.Texture("Ember"), Lifetime = NumberRange.new(1.2, 2.2), Speed = NumberRange.new(4, 7),
				SpreadAngle = Vector2.new(25, 25), Acceleration = Vector3.new(0, 1, 0), Drag = 0.3, LightEmission = 1, Brightness = 2,
				Color = ColorSequence.new(aura.Embers.Colour), Size = NumberSequence.new(0.35, 0),
			}))
		end
		if aura.Rays then
			for i = 1, aura.Rays.Count do
				local ray = newBeam(look, block, "Ray" .. i, { Width0 = height * aura.Rays.Width[1], Width1 = height * aura.Rays.Width[2],
					Texture = IceLooks.Textures.Ray or "", LightEmission = 0.6, Brightness = 2 })
				table.insert(look.rays, ray)
			end
		end
		if aura.Sparkles then
			for i = 1, aura.Sparkles.Orbiters do
				local orbiter = make("Attachment", block, { Name = "Orbiter" .. i })
				table.insert(look.extras, orbiter)
				local e = newEmitter(look, orbiter, "Spiral", aura.Sparkles.Rate, {
					Texture = EffectsConfig.Texture("Sparkle"), Lifetime = NumberRange.new(0.9, 1.4), Speed = NumberRange.new(0.3, 0.8),
					SpreadAngle = Vector2.new(180, 180), LightEmission = 1, Brightness = 2.5,
					Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.9), NumberSequenceKeypoint.new(1, 0) }),
				})
				table.insert(look.orbiters, { attachment = orbiter, emitter = e, phase = (i - 1) / aura.Sparkles.Orbiters })
			end
		end
	end

	view.look = look
	IceBlockLook.SetCreature(view)
end

-- The creature: its frosty outline in the rarity colour, its glowing eyes, and its real colours kept for the reveal.
function IceBlockLook.SetCreature(view)
	local look = view.look
	local sil = view.silhouette
	if not look or not sil then
		return
	end
	-- the glow centres on the creature (just built, it stands on the block's base; IceBlocks lifts it every frame)
	local box = sil.model:GetBoundingBox()
	local middle = view.block.CFrame:PointToObjectSpace(box.Position)
	look.centre.Position = Vector3.new(0, middle.Y + look.height * SETTINGS.CreatureLift, 0)
	if look.outline then
		look.outline:Destroy()
	end
	look.outline = make("Highlight", sil.model, { Name = "FrostOutline", Adornee = sil.model, DepthMode = Enum.HighlightDepthMode.Occluded,
		FillTransparency = 1, OutlineTransparency = IceLooks.Creature.Outline })
	local eyeKeys = sil.data.Eyes or DEFAULT_EYES
	look.eyes, look.body = {}, {}
	for _, part in sil.model:GetChildren() do
		if part:IsA("BasePart") and sil.data.Colors[part.Name] then
			local real = Color3.fromHex(sil.data.Colors[part.Name])
			if eyeKeys[part.Name] then
				part.Material = Enum.Material.Neon
				table.insert(look.eyes, part)
			else
				table.insert(look.body, { part = part, real = real })
			end
		end
	end
	look.blinkAt = os.clock() + math.random() * 3
	look.revealed = -1
end

-- A tap on this block: squash and recover (restarts, never stacks).
function IceBlockLook.Hit(view)
	if view.look then
		view.look.squashAt = os.clock()
	end
end

-- A flung piece: solid ice (Transparency 0: the atlas's colour without its see-through), a touch smaller than its
-- place in the block, so neighbours don't jam against each other.
local function chunkFrom(look, template: BasePart, pivot: CFrame): BasePart
	local part = template:Clone()
	part.Size = template.Size * look.scale * 0.94
	part.Transparency = 0
	part.CFrame = pivot * CFrame.new(template.Position * look.scale) * template.CFrame.Rotation
	if part.TextureID ~= "" then
		part.TextureID = look.atlas
	end
	part.Anchored = false
	part.CanCollide, part.CanQuery, part.CanTouch = true, false, false
	part.CastShadow = false
	part.Parent = Effects.Folder()
	return part
end

-- Fades a flung piece out over its last seconds, then removes it.
local function fadeAway(part: BasePart, life: number, fadeFrom: number)
	task.delay(fadeFrom, function()
		local start, base = os.clock(), part.Transparency
		local span = math.max(0.05, life - fadeFrom)
		while part.Parent and os.clock() - start < span do
			part.Transparency = base + (1 - base) * (os.clock() - start) / span
			task.wait()
		end
		part:Destroy()
	end)
end

-- A crack stage: one or two chunks break off the top edges and fall.
function IceBlockLook.BreakChunks(view, stage: number)
	local look = view.look
	local source = kit()
	if not look or not source then
		return
	end
	local pivot = view.block.CFrame * CFrame.new(0, -look.height / 2, 0)
	local count = math.random(SETTINGS.Chunks.PerStage[1], SETTINGS.Chunks.PerStage[2])
	for i = 1, count do
		local template = source:FindFirstChild("IceChunk" .. ((stage + i) % 3 + 1))
		if template then
			local part = chunkFrom(look, template, pivot)
			local out = (part.Position - view.block.Position) * Vector3.new(1, 0, 1)
			out = if out.Magnitude > 0 then out.Unit else Vector3.xAxis
			part.AssemblyLinearVelocity = out * (6 + math.random() * 6) + Vector3.new(0, 6 + math.random() * 5, 0)
			part.AssemblyAngularVelocity = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 10
			fadeAway(part, SETTINGS.Chunks.Life, SETTINGS.Chunks.Life * 0.6)
		end
	end
end

-- The rescue: the block breaks into its own pre-cut pieces, flung out and fading; a rare block bursts in its aura colour.
function IceBlockLook.Shatter(view)
	local look = view.look
	local source = kit()
	if not look or not source then
		return
	end
	local pivot = view.block.CFrame * CFrame.new(0, -look.height / 2, 0)
	local centre = view.block.Position
	local pieces = SETTINGS.Pieces
	for _, template in source:GetChildren() do
		if template:IsA("BasePart") and string.match(template.Name, "^IcePiece") then
			local part = chunkFrom(look, template, pivot)
			local out = part.Position - centre
			out = if out.Magnitude > 0.1 then out.Unit else Vector3.yAxis
			local speed = pieces.Speed[1] + math.random() * (pieces.Speed[2] - pieces.Speed[1])
			part.AssemblyLinearVelocity = Vector3.new(out.X, 0, out.Z) * speed + Vector3.new(0, pieces.Up[1] + math.random() * (pieces.Up[2] - pieces.Up[1]), 0)
			part.AssemblyAngularVelocity = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 9
			fadeAway(part, pieces.Life, pieces.FadeFrom)
		end
	end
	local burst = AURAS.Burst[look.rarity]
	if burst then
		local now = os.clock()
		for i = 1, Effects.Count(burst) do
			local colour = if (IceLooks.Rarities[look.rarity] or {}).Rainbow then Color3.fromHSV((i / burst + now * 0.1) % 1, 0.7, 1) else rarityColour(look.rarity, now)
			Effects.Debris({
				Size = Vector3.one * (0.35 + math.random() * 0.45),
				CFrame = CFrame.new(centre + Vector3.new((math.random() - 0.5) * 4, (math.random() - 0.3) * look.height * 0.6, (math.random() - 0.5) * 4))
					* CFrame.Angles(math.random() * 6, math.random() * 6, 0),
				Color = colour,
				Material = Enum.Material.Neon,
				Velocity = Vector3.new((math.random() - 0.5) * 40, 18 + math.random() * 26, (math.random() - 0.5) * 40),
				Life = 1.6,
			})
		end
		look.flashAt = now -- the ring flares as it fades
	end
end

-- Every frame: place the parts (with the tap squash), cracks and frost by stage, the creature, the glow and the aura.
function IceBlockLook.Update(view, present: boolean, stage: number, now: number, dt: number)
	local look = view.look
	if not look then
		return
	end
	local height = look.height
	-- the parts follow the block (only when it moved or squashes)
	local pivot = view.block.CFrame * CFrame.new(0, -height / 2, 0)
	local squash = 0
	if look.squashAt then
		local t = (now - look.squashAt) / SETTINGS.TapSquash.Seconds
		if t < 1 then
			squash = SETTINGS.TapSquash.Amount * math.sin(math.pi * t)
		else
			look.squashAt = nil
		end
	end
	if squash > 0 or look.squashed or look.lastPivot ~= pivot then
		local stretch = Vector3.new(1 + squash / 2, 1 - squash, 1 + squash / 2)
		local frames = table.create(#look.parts)
		for i, offset in look.offsets do
			frames[i] = pivot * CFrame.new(offset.Position * stretch) * offset.Rotation
		end
		if squash > 0 or look.squashed then
			for i, part in look.parts do
				part.Size = look.sizes[i] * stretch
			end
		end
		look.squashed = squash > 0
		Workspace:BulkMoveTo(look.parts, frames, Enum.BulkMoveMode.FireCFrameChanged)
		look.lastPivot = pivot
		look.mistSource.CFrame = pivot * CFrame.new(0, 0.4, 0)
		if look.auraBox then
			look.auraBox.CFrame = view.block.CFrame
		end
	end
	local hidden = if present then 0 else 1
	if look.hidden ~= hidden then
		look.hidden = hidden
		for _, part in look.parts do
			part.LocalTransparencyModifier = hidden
		end
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

	-- a rescue fades the aura out quickly (with a flare); a new block shows at once
	if present then
		look.alpha = 1
	else
		look.alpha = math.max(0, look.alpha - dt / AURAS.FadeSeconds)
	end
	local alpha = look.alpha
	local info = IceLooks.Rarities[look.rarity] or IceLooks.Rarities.Common
	local colour = rarityColour(look.rarity, now)
	local aura = look.aura

	-- the creature: outline, blinking eyes, real colours showing through at the last crack stages
	if look.outline then
		look.outline.Enabled = present
		look.outline.OutlineColor = colour
	end
	if look.eyes then
		local blink = IceLooks.Creature.Blink
		if now >= look.blinkAt then
			look.blinkUntil = now + blink.Seconds
			look.blinkAt = now + blink.Every[1] + math.random() * (blink.Every[2] - blink.Every[1])
		end
		local shut = now < (look.blinkUntil or 0)
		for _, eye in look.eyes do
			eye.Color = if shut then PetLooks.SilhouetteColor else colour
		end
		local reveal = IceLooks.Creature.Reveal[math.clamp(stage, 0, 4)] or 0
		if reveal ~= look.revealed then
			look.revealed = reveal
			for _, entry in look.body do
				entry.part.Color = PetLooks.SilhouetteColor:Lerp(entry.real, reveal)
			end
		end
	end

	-- the glow behind the creature
	local strength = info.Glow * alpha
	if aura and aura.Pulse then
		strength *= 1 - aura.Pulse.Depth * (0.5 + 0.5 * math.sin(now * aura.Pulse.Speed))
	end
	if stage >= 4 then
		strength *= 1.2
	end
	local camera = Workspace.CurrentCamera
	local toCamera = view.block.CFrame:VectorToObjectSpace(camera.CFrame.Position - view.block.Position)
	toCamera = Vector3.new(toCamera.X, 0, toCamera.Z)
	toCamera = if toCamera.Magnitude > 1e-3 then toCamera.Unit else Vector3.zAxis
	local glow = look.glowBeam
	local middle = look.centre.Position - toCamera * height * SETTINGS.Glow.Behind
	glow.a0.Position = middle - Vector3.new(0, look.glowSize / 2, 0)
	glow.a1.Position = middle + Vector3.new(0, look.glowSize / 2, 0)
	glow.beam.Enabled = strength > 0.01
	glow.beam.Color = ColorSequence.new(colour:Lerp(Color3.new(1, 1, 1), SETTINGS.Glow.Whiten))
	glow.beam.Transparency = NumberSequence.new(1 - (1 - SETTINGS.Glow.Transparency) * math.clamp(strength, 0, 1))
	if look.innerLight then
		look.innerLight.Enabled = present
	end
	for _, part in look.glows do -- the Mythic Block's crystal cores cycle the rainbow
		part.Color = Color3.fromHSV((now / IceLooks.Creature.RainbowSeconds + 0.3) % 1, 0.55, 1)
	end

	-- the particles: the effect rules, checked every CheckSeconds
	if now >= look.ruleAt then
		look.ruleAt = now + EffectsConfig.Rules.CheckSeconds
		look.rule = ruleScale(view)
		look.reduced = Effects.Reduced()
	end
	for _, entry in look.emitters do
		local name = entry.emitter.Name
		local on = present and look.rule > 0
		if name == "Motes" then
			on = on and info.Motes == true
		elseif look.reduced and (name == "Flames" or name == "Spiral") then
			on = false -- (the simpler aura)
		end
		entry.emitter.Enabled = on
		entry.emitter.Rate = entry.rate * look.rule
	end
	look.motes.Color = ColorSequence.new(colour)

	-- the aura: a ring behind the block, rays, spirals, pulses
	if look.halo then
		local pulse = 1
		if aura.Pulse then
			pulse = 1 - aura.Pulse.Depth * (0.5 + 0.5 * math.sin(now * aura.Pulse.Speed))
		elseif aura.PulseEvery then
			local since = now % aura.PulseEvery
			if since < aura.PulseSeconds then
				pulse = 1 + 0.8 * math.sin(math.pi * since / aura.PulseSeconds)
				if since < dt and look.rule > 0 then
					for _, orbiter in look.orbiters do
						orbiter.emitter:Emit(math.max(1, math.floor(8 * look.rule)))
					end
				end
			end
		end
		local flare = if look.flashAt and now - look.flashAt < AURAS.FadeSeconds then 1.6 else 1
		local back = view.block.Size.X * 0.55 -- (just behind the block: further back, perspective shrinks the ring behind it)
		local at = Vector3.new(0, height * 0.1, 0) - toCamera * back -- (a little high: the ring stays off the stage)
		local size = look.haloSize * (if pulse > 1 then 1 + (pulse - 1) * 0.12 else 1) * flare
		look.halo.a0.Position = at - Vector3.new(0, size / 2, 0)
		look.halo.a1.Position = at + Vector3.new(0, size / 2, 0)
		look.halo.beam.Width0, look.halo.beam.Width1 = size, size
		look.halo.beam.Enabled = alpha > 0
		local ringColour = if aura == AURAS.Mythic then Color3.fromHSV((now / IceLooks.Creature.RainbowSeconds) % 1, 0.65, 1) else colour
		look.halo.beam.Color = ColorSequence.new(ringColour)
		local ring = math.clamp(1 - (1 - aura.HaloTransparency) * math.min(pulse, 1.4) * alpha, 0, 1)
		look.halo.beam.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(AURAS.HaloFadeBottom, ring), NumberSequenceKeypoint.new(1, ring) })
		-- Legendary's rays fan up from behind the cap, swaying slowly
		if #look.rays > 0 then
			local rays = aura.Rays
			local right = toCamera:Cross(Vector3.yAxis).Unit
			local top = Vector3.new(0, height / 2 + 0.4, 0) - toCamera * view.block.Size.X * 0.3
			for i, ray in look.rays do
				local angle = math.rad((i - (#look.rays + 1) / 2) / ((#look.rays - 1) / 2) * rays.Spread / 2 + math.sin(now * 0.35 + i * 1.7) * 6)
				local direction = Vector3.yAxis * math.cos(angle) + right * math.sin(angle)
				ray.a0.Position = top
				ray.a1.Position = top + direction * height * rays.Length
				ray.beam.Enabled = alpha > 0 and not look.reduced
				ray.beam.Color = ColorSequence.new(colour)
				ray.beam.Transparency = NumberSequence.new(math.clamp(1 - (1 - rays.Transparency) * pulse * alpha * (0.75 + 0.25 * math.sin(now * 0.9 + i)), 0, 1))
			end
		end
		-- Mythic's sparkles spiral up round the block
		if aura.Sparkles then
			local loop = aura.Sparkles.LoopSeconds
			local radius = view.block.Size.X * 0.62
			for _, orbiter in look.orbiters do
				local t = (now / loop + orbiter.phase) % 1
				local angle = t * math.pi * 4 + orbiter.phase * math.pi * 2
				orbiter.attachment.Position = Vector3.new(math.cos(angle) * radius, -height / 2 + t * height * 1.15, math.sin(angle) * radius)
				orbiter.emitter.Color = ColorSequence.new(Color3.fromHSV((now / IceLooks.Creature.RainbowSeconds + orbiter.phase * 0.5) % 1, 0.6, 1))
			end
		end
	end

	-- the shimmer sweeps across each face in turn
	local tile = height * SETTINGS.Shimmer.TileHeights
	for _, s in look.shimmer do
		s.texture.OffsetStudsU = ((now / SETTINGS.Shimmer.Period + s.phase) % 1) * tile
		s.texture.Transparency = if present then SETTINGS.Shimmer.Transparency else 1
	end
end

return IceBlockLook
