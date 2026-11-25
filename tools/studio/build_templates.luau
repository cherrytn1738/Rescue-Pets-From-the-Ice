--[[
build_templates.luau: builds the station and ice pick templates from the uploaded models (Edit mode only:
the command bar, or MCP execute_luau). Re-running replaces the old templates. Save the place afterwards:
the templates live in the place file (ServerStorage), not in Git.

  ONLY = nil              every building and the picks
  ONLY = "IcePickPost"    one building (all five tiers and their upgrade sets)
  ONLY = "Picks"          the six ice picks

Out:
  ServerStorage.BuildingTemplates.<Id>.T<tier>   a Model: "Root" (its PrimaryPart: an invisible part at
      the pad centre on the ground, front -Z, carrying the named Attachments from BuildingModels), the
      station's MeshParts, and Upgrades.U1..U5 (the tier's upgrade part sets, in the station's space).
  ServerStorage.PickTemplates.Pick<tier>         a Tool: an invisible Handle at the pick's Grip, the pick's
      MeshParts welded to it, and Attachments Tip and Trail.

Every MeshPart (store-assets/buildings/IMPORT_NOTES.md): the palette texture, white, SmoothPlastic,
RenderFidelity Automatic; "...Glow" meshes Neon and no shadow; the base Box-collides, big body parts
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
for _, name in { "BuildingConfig", "BuildingModels", "UpgradeConfig" } do
	ReplicatedStorage[name]:Clone().Parent = fresh
end
fresh.Parent = ServerStorage
local BuildingConfig = require(fresh.BuildingConfig)
local BuildingModels = require(fresh.BuildingModels)
local UpgradeConfig = require(fresh.UpgradeConfig)
fresh:Destroy()

local PALETTE = BuildingConfig.PaletteTextureId
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
	p.RenderFidelity = Enum.RenderFidelity.Automatic
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

local function buildPick(pick)
	local info = BuildingModels.Picks[pick.Tier]
	if not pick.ModelId then
		say(`SKIPPED pick {pick.Tier}: no asset id`)
		return
	end
	local out = folder(ServerStorage, "PickTemplates")
	local old = out:FindFirstChild("Pick" .. pick.Tier)
	if old then
		old:Destroy()
	end
	local tool = Instance.new("Tool")
	tool.Name = "Pick" .. pick.Tier
	tool.CanBeDropped = false
	tool.RequiresHandle = true
	tool.ManualActivationOnly = true
	tool.ToolTip = pick.Name
	tool:SetAttribute("Tier", pick.Tier)
	local grip = attachmentCFrame(info.Attachments.Grip)
	local handle = Instance.new("Part")
	handle.Name = "Handle"
	handle.Size = Vector3.new(0.3, 0.3, 0.3)
	handle.Transparency = 1
	handle.CanCollide, handle.CanQuery, handle.CanTouch = false, false, false
	handle.Massless = true
	handle.CFrame = CFrame.new(grip.Position) -- (the pick's own axes: handle along +Y, head on top)
	handle.Parent = tool
	local parts, factor = load(pick.ModelId, 3.5)
	for _, p in parts do
		style(p, false, Enum.CollisionFidelity.Box)
		p.Anchored = false
		p.Massless = true
		p.Parent = tool
		local weld = Instance.new("WeldConstraint")
		weld.Part0, weld.Part1 = handle, p
		weld.Parent = p
	end
	for _, name in { "Tip", "Trail" } do
		local a = info.Attachments[name]
		if a then
			local att = Instance.new("Attachment")
			att.Name = name
			att.CFrame = CFrame.new(-grip.Position) * attachmentCFrame(a)
			att.Parent = handle
		end
	end
	tool.Grip = UpgradeConfig.PickGrip
	tool.Parent = out
	say(string.format("Pick%d %s: %d meshes (import x%d)", pick.Tier, pick.Name, #parts, factor))
end

if not PALETTE then
	return "BuildingConfig.PaletteTextureId is missing"
end
for _, building in BuildingConfig.Buildings do
	if ONLY == nil or ONLY == building.Id then
		buildBuilding(building)
	end
end
if ONLY == nil or ONLY == "Picks" then
	for _, pick in UpgradeConfig.IcePick do
		buildPick(pick)
		task.wait()
	end
end
return table.concat(report, "\n")
