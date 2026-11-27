--[[
build_templates.luau: builds the station, tool and plot templates from the uploaded models (Edit mode only:
the command bar, or MCP execute_luau). Re-running replaces the old templates. Save the place afterwards:
the templates live in the place file (ServerStorage), not in Git.

  ONLY = nil              every building and the tools
  ONLY = "IcePickPost"    one building (all five tiers and their upgrade sets)
  ONLY = "Tools"          the tools (every tier with an uploaded model)
  ONLY = "Plot"           the plot's own parts (MapConfig.PlotModels: the arch, the ice stage, the walls)
  ONLY = "Plaza"          the plaza's parts (MapConfig.PlazaModels: the leaderboard board)
  ONLY = "Ice"            the ice block's kit (IceLooks.KitModelId: tools/blender/ice_block.py)

Out:
  ServerStorage.BuildingTemplates.<Id>.T<tier>   a Model: "Root" (its PrimaryPart: an invisible part at
      the pad centre on the ground, front -Z, carrying the named Attachments from BuildingModels), the
      station's MeshParts, and Upgrades.U1..U5 (the tier's upgrade part sets, in the station's space).
  ServerStorage.ToolTemplates.Tool<tier>         a Tool: an invisible Handle at the tool's Grip, its MeshParts
      welded to it (a drill's bit on a Weld BitJoint), Attachments Tip, TrailA, TrailB and Bit, a SwingTrail
      (off), the attributes Tier and Family, and its family's grip (SwingConfig).
  ServerStorage.PlotTemplates.<PlotArch|PlotStage|PlotWallLong|PlotWallShort>   a Model of MeshParts in plot
      space, its pivot at the origin on the ground; nothing collides (the plot's own Parts do). "...Trim" meshes
      are untextured with the attribute RankColour: RankService gives them the owner's rebirth colour.
  ServerStorage.PlazaTemplates.<LeaderboardBoard>   the same, in plaza-spot space (PlazaService places it).
  ServerStorage.IceTemplates.Kit   a Model of every ice block mesh in block space (its pivot on the ground at the
      middle, front -Z) at the level-1 size: the body, cracks, shape variants, layer extras, Mythic Block crystals,
      shatter pieces and chunks (IceBlockLook picks a block's parts). IceBlockService copies the folder to
      ReplicatedStorage for the clients.

Every MeshPart (store-assets/buildings/IMPORT_NOTES.md): the palette texture, white, SmoothPlastic,
RenderFidelity Automatic (Roblox's level of detail: a full server of maxed plots was 1.3M triangles at
Precise, too much for phones); "...Glow" meshes Neon and no shadow; the base Box-collides, big body parts
Hull-collide, everything else Box and no collision. The import arrives 100x too big round the Blender
origin (the pad centre), so every part is scaled back about the origin.
]]
local ONLY = ONLY_OVERRIDE -- (the MCP runner replaces this; nil = everything)

local InsertService = game:GetService("InsertService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

-- Fresh copies of the configs: Studio's require keeps the first copy it loaded in a session, so a config
-- Rojo has updated since (new ids, new attachment points) would be missed. Clones are new modules.
local fresh = Instance.new("Folder")
fresh.Name = "BuildTemplatesConfigs"
for _, name in { "BuildingConfig", "BuildingModels", "UpgradeConfig", "MapConfig", "IceLooks", "SwingConfig" } do
	ReplicatedStorage[name]:Clone().Parent = fresh
end
fresh.Parent = ServerStorage
local BuildingConfig = require(fresh.BuildingConfig)
local BuildingModels = require(fresh.BuildingModels)
local UpgradeConfig = require(fresh.UpgradeConfig)
local MapConfig = require(fresh.MapConfig)
local IceLooks = require(fresh.IceLooks)
local SwingConfig = require(fresh.SwingConfig)
fresh:Destroy()

local PALETTE = BuildingConfig.PaletteTextureId
local PRECISE = false -- Automatic level of detail for every MeshPart (store-assets/buildings/IMPORT_NOTES.md)
local report = {}

local function say(line)
	table.insert(report, line)
end

local function folder(parent: Instance, name: string): Folder
	local f = parent:FindFirstChild(name)
	if not f then
		f = Instance.new("Folder")
		f.Name = name
		f.Parent = parent
	end
	return f
end

-- An attachment frame from BuildingModels ({ Position, Out, Up }): +Y points Out (an emitter's Top), +Z
-- along Up's side, as BuildingEffects expects.
local function attachmentCFrame(a): CFrame
	local up = if a.Out.Magnitude > 0 then a.Out.Unit else Vector3.yAxis
	local look = if a.Up.Magnitude > 0 then a.Up.Unit else Vector3.zAxis
	local right = look:Cross(up)
	if right.Magnitude < 1e-3 then
		return CFrame.new(a.Position)
	end
	return CFrame.fromMatrix(a.Position, right.Unit, up)
end

-- The MeshParts of an uploaded model, scaled back to studs about the origin. `expectedHeight` (studs, the
-- model's top) tells the import scale: 100x by default, 25x for the buildings (exported at a quarter scale
-- so no part passes Roblox's 2048-stud cap), 1x for a 1:1 import.
local function load(assetId: number, expectedHeight: number?, knownFactor: number?)
	local container = InsertService:LoadAsset(assetId)
	local parts = {}
	for _, d in container:GetDescendants() do
		if d:IsA("MeshPart") then
			table.insert(parts, d)
		end
	end
	local top = 0
	for _, p in parts do
		top = math.max(top, p.Position.Y + p.Size.Y / 2)
	end
	local factor = knownFactor or 100
	if expectedHeight and not knownFactor then
		local ratio = top / expectedHeight
		factor = if ratio < 5 then 1 elseif ratio < 50 then 25 else 100
	end
	for _, p in parts do
		local rotation = p.CFrame.Rotation
		p.Size = p.Size / factor
		p.CFrame = CFrame.new(p.Position / factor) * rotation
		p.Parent = nil
	end
	container:Destroy()
	return parts, factor
end

local function style(p: MeshPart, collide: boolean, fidelity: Enum.CollisionFidelity)
	local glow = string.sub(p.Name, -4) == "Glow"
	p.Anchored = true
	p.TextureID = PALETTE
	p.Color = Color3.new(1, 1, 1)
	p.Material = if glow then Enum.Material.Neon else Enum.Material.SmoothPlastic
	p.CastShadow = not glow
	p.RenderFidelity = if PRECISE then Enum.RenderFidelity.Precise else Enum.RenderFidelity.Automatic
	p.CollisionFidelity = fidelity
	p.CanCollide = collide
	p.CanQuery = collide
	p.CanTouch = false
	p.DoubleSided = false
end

-- Collision: the base (the biggest footprint standing on the ground) Box-collides; big solid body parts
-- Hull-collide; trim, glow, working parts and the rest don't collide.
local function styleStation(parts)
	local base, best = nil, 0
	for _, p in parts do
		local footprint = p.Size.X * p.Size.Z
		if p.Position.Y - p.Size.Y / 2 < 0.4 and footprint > best and string.sub(p.Name, -4) ~= "Glow" then
			base, best = p, footprint
		end
	end
	for _, p in parts do
		local glow = string.sub(p.Name, -4) == "Glow"
		if p == base then
			style(p, true, Enum.CollisionFidelity.Box)
		elseif not glow and p.Size.Magnitude > 6 and p.Size.X * p.Size.Y * p.Size.Z > 25 then
			style(p, true, Enum.CollisionFidelity.Hull)
		else
			style(p, false, Enum.CollisionFidelity.Box)
		end
	end
	return base
end

local function root(attachments): Part
	local r = Instance.new("Part")
	r.Name = "Root"
	r.Anchored = true
	r.CanCollide, r.CanQuery, r.CanTouch = false, false, false
	r.Transparency = 1
	r.Size = Vector3.new(1, 0.2, 1)
	r.CFrame = CFrame.identity
	for name, a in attachments do
		local att = Instance.new("Attachment")
		att.Name = name
		att.CFrame = attachmentCFrame(a)
		att.Parent = r
	end
	return r
end

local function buildBuilding(building)
	local ids = BuildingConfig.ModelIds[building.Id]
	local out = folder(folder(ServerStorage, "BuildingTemplates"), building.Id)
	for tier = 1, 5 do
		local info = BuildingModels.Buildings[building.Id][tier]
		local stationId = ids and ids.Stations[tier]
		if not stationId then
			say(`SKIPPED {building.Id} T{tier}: no asset id`)
			continue
		end
		local old = out:FindFirstChild("T" .. tier)
		if old then
			old:Destroy()
		end
		local model = Instance.new("Model")
		model.Name = "T" .. tier
		local r = root(info.Attachments)
		r.Parent = model
		model.PrimaryPart = r
		local parts, factor = load(stationId, info.Height or info.Size.Y)
		local base = styleStation(parts)
		for _, p in parts do
			p.Parent = model
		end
		local sets = Instance.new("Folder")
		sets.Name = "Upgrades"
		sets.Parent = model
		local upgradeCount = 0
		if ids.Upgrades[tier] then
			local ups = load(ids.Upgrades[tier], nil, factor) -- (exported like its station)
			local prefix = building.Id .. "T" .. tier .. "U"
			for _, p in ups do
				local u = string.match(p.Name, "^" .. prefix .. "(%d)")
				if u then
					local set = sets:FindFirstChild("U" .. u)
					if not set then
						set = Instance.new("Model")
						set.Name = "U" .. u
						set.Parent = sets
					end
					style(p, false, Enum.CollisionFidelity.Box)
					p.Parent = set
					upgradeCount += 1
				else
					say(`  {building.Id} T{tier}: upgrade mesh {p.Name} has no U number (dropped)`)
					p:Destroy()
				end
			end
		end
		model.WorldPivot = CFrame.identity
		model:SetAttribute("BuildingId", building.Id)
		model:SetAttribute("Tier", tier)
		model.Parent = out
		local size = model:GetExtentsSize()
		local missing = {}
		for _, name in { "Work", "Hit", "Aura", "Top", "NamePlate" } do
			if not r:FindFirstChild(name) then
				table.insert(missing, name)
			end
		end
		say(string.format("%s T%d: %d meshes (import x%d), %d upgrade meshes in %d sets, base %s, size %.1f x %.1f x %.1f (manifest %.1f x %.1f x %.1f)%s",
			building.Id, tier, #parts, factor, upgradeCount, #sets:GetChildren(), base and base.Name or "NONE",
			size.X, size.Y, size.Z, info.Size.X, info.Size.Y, info.Size.Z, if #missing > 0 then " MISSING " .. table.concat(missing, ",") else ""))
		task.wait()
	end
end

-- A tool template: an invisible Handle at the tool's Grip, its MeshParts welded to it (a drill's "...Bit" on a Weld
-- BitJoint whose C0 sits on its axis, so the client can spin it), the Tip, TrailA, TrailB and Bit attachments, and a
-- SwingTrail between TrailA and TrailB (off: PickSwing turns it on during a slash).
local function buildTool(info)
	local model = BuildingModels.Tools[info.Tier]
	if not info.ModelId or not model then
		say(`SKIPPED tool {info.Tier} {info.Name}: no asset id or attachments yet`)
		return
	end
	local out = folder(ServerStorage, "ToolTemplates")
	local old = out:FindFirstChild("Tool" .. info.Tier)
	if old then
		old:Destroy()
	end
	local tool = Instance.new("Tool")
	tool.Name = "Tool" .. info.Tier
	tool.CanBeDropped = false
	tool.RequiresHandle = true
	tool.ManualActivationOnly = true
	tool.ToolTip = info.Name
	tool:SetAttribute("Tier", info.Tier)
	tool:SetAttribute("Family", info.Family)
	local grip = attachmentCFrame(model.Attachments.Grip)
	local handle = Instance.new("Part")
	handle.Name = "Handle"
	handle.Size = Vector3.new(0.3, 0.3, 0.3)
	handle.Transparency = 1
	handle.CanCollide, handle.CanQuery, handle.CanTouch = false, false, false
	handle.Massless = true
	handle.CFrame = CFrame.new(grip.Position) -- (the tool's own axes: handle along +Y, the striking side toward -X)
	handle.Parent = tool
	local parts, factor = load(info.ModelId, 4.2)
	local bit
	for _, p in parts do
		style(p, false, Enum.CollisionFidelity.Box)
		p.CanQuery = false
		p.Anchored = false
		p.Massless = true
		p.Parent = tool
		if string.sub(p.Name, -3) == "Bit" then
			bit = p
		else
			local weld = Instance.new("WeldConstraint")
			weld.Part0, weld.Part1 = handle, p
			weld.Parent = p
		end
	end
	local attachments = {}
	for _, name in { "Tip", "TrailA", "TrailB", "Bit" } do
		local a = model.Attachments[name]
		if a then
			local att = Instance.new("Attachment")
			att.Name = name
			att.CFrame = CFrame.new(-grip.Position) * attachmentCFrame(a)
			att.Parent = handle
			attachments[name] = att
		end
	end
	if bit and attachments.Bit then
		local joint = Instance.new("Weld") -- (a Weld: the character's Animator resets every Motor6D in the rig each frame)
		joint.Name = "BitJoint"
		joint.Part0, joint.Part1 = handle, bit
		joint.C0 = attachments.Bit.CFrame -- (its +Y is the bit's axis: the client turns C0 about Y)
		joint.C1 = bit.CFrame:ToObjectSpace(handle.CFrame * attachments.Bit.CFrame)
		joint.Parent = handle
	end
	if attachments.TrailA and attachments.TrailB then
		local settings = SwingConfig.Trail
		local trail = Instance.new("Trail")
		trail.Name = "SwingTrail"
		trail.Attachment0, trail.Attachment1 = attachments.TrailA, attachments.TrailB
		trail.Enabled = false
		trail.Lifetime = settings.Lifetime
		trail.MinLength = 0.05
		trail.Transparency = NumberSequence.new(settings.Transparency[1], settings.Transparency[2])
		trail.WidthScale = NumberSequence.new(settings.WidthScale[1], settings.WidthScale[2])
		trail.LightEmission = settings.LightEmission
		trail.Parent = handle
	end
	tool.Grip = SwingConfig.Family(info.Family).Grip
	tool.Parent = out
	say(string.format("Tool%d %s (%s): %d meshes (import x%d)%s", info.Tier, info.Name, info.Family, #parts, factor, if bit then ", a spinning bit" else ""))
end

local TRIM_COLOUR = Color3.fromRGB(205, 222, 240) -- RankService's colour for a plot without a rank
local PLOT_IMPORT = 10 -- tools/blender/plot_parts.py exports at a tenth (the 100-stud wall)
local function buildPlotPart(name: string, assetId: number, folderName: string?)
	local out = folder(ServerStorage, folderName or "PlotTemplates")
	local old = out:FindFirstChild(name)
	if old then
		old:Destroy()
	end
	local model = Instance.new("Model")
	model.Name = name
	local parts = load(assetId, nil, PLOT_IMPORT)
	local trims = 0
	for _, p in parts do
		style(p, false, Enum.CollisionFidelity.Box)
		if string.sub(p.Name, -4) == "Trim" then
			p.TextureID = ""
			p.Color = TRIM_COLOUR
			p:SetAttribute("RankColour", true)
			trims += 1
		end
		p.Parent = model
	end
	model.WorldPivot = CFrame.identity
	model.Parent = out
	local size = model:GetExtentsSize()
	say(string.format("%s.%s: %d meshes (%d rank trim), size %.1f x %.1f x %.1f", out.Name, name, #parts, trims, size.X, size.Y, size.Z))
end

-- The ice block's kit: every mesh takes an ice atlas (IceBlockLook swaps in the layer's); the shell, bubbles, Mythic
-- glass, shatter pieces and chunks are just above transparent (Roblox then honours the atlas's alpha); the veins and
-- the Mythic crystal cores are Neon, untextured (coloured in game); the rest opaque.
local ICE_IMPORT = 10 -- tools/blender/ice_block.py exports at a tenth, like the plot parts
local SEE_THROUGH = { Shell = true, DenseBubbles = true, MythicGlass = true }
local function buildIceKit(assetId: number)
	local out = folder(ServerStorage, "IceTemplates")
	for _, old in out:GetChildren() do
		old:Destroy() -- (the old look options too)
	end
	local model = Instance.new("Model")
	model.Name = "Kit"
	local count = 0
	for _, p in load(assetId, nil, ICE_IMPORT) do
		local role = string.match(p.Name, "^Ice(.+)$") or p.Name
		style(p, false, Enum.CollisionFidelity.Box)
		p.TextureID = IceLooks.Textures.BlueIce
		p.CastShadow = role == "Shell" or string.match(role, "Snow$") ~= nil
		if SEE_THROUGH[role] or string.match(role, "Inner$") or string.match(role, "^Piece") or string.match(role, "^Chunk") then
			p.Transparency = IceLooks.New.ShellTransparency
		elseif role == "Veins" or role == "MythicGlow" then
			p.TextureID = ""
			p.Material = Enum.Material.Neon
			p.Color = Color3.fromRGB(150, 240, 255)
		end
		p:SetAttribute("Role", role)
		p.Parent = model
		count += 1
	end
	model.WorldPivot = CFrame.identity
	model.Parent = out
	local size = model:GetExtentsSize()
	say(string.format("IceTemplates.Kit: %d meshes, size %.1f x %.1f x %.1f", count, size.X, size.Y, size.Z))
end

if ONLY == "Ice" then
	if not IceLooks.Textures.BlueIce or not IceLooks.KitModelId then
		return "IceLooks.Textures.BlueIce or IceLooks.KitModelId is missing (tools/write_asset_ids.py)"
	end
	buildIceKit(IceLooks.KitModelId)
	return table.concat(report, "\n")
end
if not PALETTE then
	return "BuildingConfig.PaletteTextureId is missing"
end
if ONLY == "Plot" then
	for name, assetId in MapConfig.PlotModels do
		buildPlotPart(name, assetId)
		task.wait()
	end
	return table.concat(report, "\n")
end
if ONLY == "Plaza" then
	for name, assetId in MapConfig.PlazaModels do
		buildPlotPart(name, assetId, "PlazaTemplates") -- (tools/blender/plaza_boards.py: the same tenth scale)
		task.wait()
	end
	return table.concat(report, "\n")
end
for _, building in BuildingConfig.Buildings do
	if ONLY == nil or ONLY == building.Id then
		buildBuilding(building)
	end
end
if ONLY == nil or ONLY == "Tools" then
	for _, info in UpgradeConfig.Tools do
		buildTool(info)
		task.wait()
	end
end
return table.concat(report, "\n")
