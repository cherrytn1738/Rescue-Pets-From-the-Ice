--[[
build_world.luau: the snowy world round the plots (Edit mode only: the command bar, or MCP execute_luau).
Re-running replaces what it built before. Save the place afterwards: terrain, scenery and the sky live in the
place file, not in Git.

 - Removes the default Baseplate (its grid texture) and clears the terrain.
 - Terrain: snow ground with its top at MapConfig.Ground, out to GROUND_HALF studs; in every plot the drifts and
   ice patches from MapConfig.PlotGround (the plots' own floors are invisible, so this terrain is what shows);
   a frozen pond in each gap between plots; a ring of snowy hills beyond the plots and a ring of big hazy
   mountains further out. Nothing stands between the plaza and any plot's open front: everything outside the
   plots starts CLEAR_RADIUS studs from the plaza's centre, past the plots' back corners.
 - Workspace.Scenery: clumps of snowy pines (store-assets/scenery/Pines.fbx, uploaded as group 921449746) on the
   hills, coloured by mesh name; trunks and needles collide, snow doesn't.
 - Lighting.Sky: the winter sky (assets/textures/sky/, uploaded as group 921449746).
Light enough for phones: three terrain voxel layers under the ground, one shared mesh per pine part.
]]
local InsertService = game:GetService("InsertService")
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

-- A fresh copy of MapConfig (Studio's require keeps the first copy it loaded in a session).
local fresh = ReplicatedStorage.MapConfig:Clone()
fresh.Parent = ServerStorage
local MapConfig = require(fresh)
fresh:Destroy()

local PINES = 138595808045459 -- store-assets/scenery/upload_manifest.json
local SKY = { -- assets/textures/sky/upload_manifest.json (tools/make_skybox.py)
	SkyboxBk = 113070635814835,
	SkyboxDn = 100435546213305,
	SkyboxFt = 100780803505256,
	SkyboxLf = 91102508470648,
	SkyboxRt = 77382841776376,
	SkyboxUp = 122741017703354,
}
local GROUND_HALF = 900
-- Smooth terrain draws a filled layer's surface about half a voxel (2 studs) above the layer's top, so every fill
-- here is that much lower; the report measures where the surface really is.
local SURFACE_LIFT = 2
local CLEAR_RADIUS = 255 -- the plots' back corners reach about 230
local SEED = 2611

local terrain = Workspace.Terrain
local ground = MapConfig.Ground
local fillTop = ground - SURFACE_LIFT
local report = {}
local random = Random.new(SEED)

local baseplate = Workspace:FindFirstChild("Baseplate")
if baseplate then
	baseplate:Destroy()
	table.insert(report, "Baseplate removed")
end
terrain:Clear()
terrain:SetMaterialColor(Enum.Material.Snow, Color3.fromRGB(232, 240, 250))
terrain:SetMaterialColor(Enum.Material.Ice, Color3.fromRGB(170, 212, 242))
terrain:SetMaterialColor(Enum.Material.Glacier, Color3.fromRGB(150, 196, 232))

-- The ground, in chunks (one huge fill can stall Studio): three voxel layers of snow under MapConfig.Ground.
local CHUNK = 300
for x = -GROUND_HALF, GROUND_HALF - CHUNK, CHUNK do
	for z = -GROUND_HALF, GROUND_HALF - CHUNK, CHUNK do
		terrain:FillBlock(CFrame.new(x + CHUNK / 2, fillTop - 6, z + CHUNK / 2), Vector3.new(CHUNK, 12, CHUNK), Enum.Material.Snow)
	end
	task.wait()
end

-- Where the surface really is, on open ground and on the pads (it must not cover them).
local function surfaceAt(at: Vector3): number
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { terrain }
	local hit = Workspace:Raycast(Vector3.new(at.X, ground + 60, at.Z), Vector3.new(0, -120, 0), params)
	return if hit then hit.Position.Y else -math.huge
end

-- A low mound: a sphere cap `height` tall and `radius` across its foot.
local function mound(at: Vector3, radius: number, height: number, material: Enum.Material)
	local sphere = (radius * radius + height * height) / (2 * height)
	terrain:FillBall(Vector3.new(at.X, fillTop + height - sphere, at.Z), sphere, material)
end

-- Flat ice set into the snow.
local function ice(at: Vector3, radius: number, material: Enum.Material?)
	terrain:FillCylinder(CFrame.new(at.X, fillTop - 2, at.Z), 4, radius, material or Enum.Material.Ice)
end

-- Inside the plots.
for index = 1, MapConfig.PlotCount do
	for _, drift in MapConfig.PlotGround.Drifts do
		mound(MapConfig.PlotPoint(index, drift.X, drift.Z), drift.Radius, drift.Height, Enum.Material.Snow)
	end
	for _, patch in MapConfig.PlotGround.IcePatches do
		ice(MapConfig.PlotPoint(index, patch.X, patch.Z), patch.Radius)
	end
end
task.wait()

local function onRing(degrees: number, distance: number): Vector3
	local a = math.rad(degrees)
	return Vector3.new(math.sin(a) * distance, ground, math.cos(a) * distance)
end

-- A frozen pond in each gap between plots (plot i's centre is at (i - 1) * 360 / PlotCount degrees).
local ponds = {}
for index = 1, MapConfig.PlotCount do
	local at = onRing((index - 0.5) * 360 / MapConfig.PlotCount, CLEAR_RADIUS - 3)
	ice(at, 15, Enum.Material.Ice)
	ice(at, 9, Enum.Material.Glacier)
	table.insert(ponds, at)
end

-- Snowy hills just beyond the plots, then big mountains far out (the Atmosphere hazes them).
local hills = 0
for i = 1, 30 do
	local radius = random:NextNumber(35, 75)
	local at = onRing(i * 12 + random:NextNumber(-4, 4), CLEAR_RADIUS + 25 + radius + random:NextNumber(0, 110))
	mound(at, radius, random:NextNumber(12, 34), Enum.Material.Snow)
	hills += 1
	if i % 6 == 0 then
		task.wait()
	end
end
for i = 1, 16 do
	local radius = random:NextNumber(150, 230)
	local at = onRing(i * 22.5 + random:NextNumber(-6, 6), random:NextNumber(640, 760))
	mound(at, radius, random:NextNumber(70, 150), Enum.Material.Snow)
	hills += 1
	task.wait()
end
local highestPad = -math.huge
local BuildingConfig = require(ReplicatedStorage.BuildingConfig)
for index = 1, MapConfig.PlotCount do
	for _, building in BuildingConfig.Buildings do
		highestPad = math.max(highestPad, surfaceAt(MapConfig.PlotPoint(index, building.Pad.X, building.Pad.Z)))
	end
end
table.insert(report, string.format("terrain surface: %.2f on open ground (MapConfig.Ground %.2f), highest under a pad %.2f",
	surfaceAt(Vector3.new(0, 0, 100)), ground, highestPad))
table.insert(report, string.format("terrain: ground %d studs square, %d drifts and %d ice patches per plot, %d ponds, %d hills and mountains",
	GROUND_HALF * 2, #MapConfig.PlotGround.Drifts, #MapConfig.PlotGround.IcePatches, #ponds, hills))

-- The pines: load the two models, scale them back from the import (25x) and pivot each at its foot.
local LOOKS = {
	Trunk = { Color3.fromRGB(96, 70, 52), true },
	Needles = { Color3.fromRGB(46, 92, 79), true },
	Snow = { Color3.fromRGB(240, 246, 252), false },
}
local container = InsertService:LoadAsset(PINES)
local templates = {}
for _, part in container:GetDescendants() do
	if part:IsA("MeshPart") then
		local model, role = string.match(part.Name, "^(Pine%a-)(%u%l+)$")
		local look = LOOKS[role]
		if model and look then
			part.Size /= 25
			part.CFrame = CFrame.new(part.Position / 25) * part.CFrame.Rotation
			part.Color = look[1]
			part.Material = Enum.Material.SmoothPlastic
			part.Anchored = true
			part.CanCollide, part.CanQuery, part.CanTouch = look[2], false, false
			part.CollisionFidelity = if role == "Trunk" then Enum.CollisionFidelity.Box else Enum.CollisionFidelity.Hull
			part.RenderFidelity = Enum.RenderFidelity.Automatic
			part.DoubleSided = false
			templates[model] = templates[model] or Instance.new("Model")
			templates[model].Name = model
			part.Parent = templates[model]
		end
	end
end
container:Destroy()
for _, model in templates do
	local box, size = model:GetBoundingBox()
	model.WorldPivot = CFrame.new(box.Position.X, box.Position.Y - size.Y / 2, box.Position.Z)
end

local old = Workspace:FindFirstChild("Scenery")
if old then
	old:Destroy()
end
local scenery = Instance.new("Folder")
scenery.Name = "Scenery"
scenery.Parent = Workspace
local trees = Instance.new("Folder")
trees.Name = "Pines"
trees.Parent = scenery

local rayParams = RaycastParams.new()
rayParams.FilterType = Enum.RaycastFilterType.Include
rayParams.FilterDescendantsInstances = { terrain }
local placed = {}
local function free(at: Vector3, gap: number): boolean
	for _, p in ponds do
		if (Vector3.new(at.X, 0, at.Z) - Vector3.new(p.X, 0, p.Z)).Magnitude < 22 then
			return false
		end
	end
	for _, p in placed do
		if (at - p).Magnitude < gap then
			return false
		end
	end
	return true
end
local count = 0
if templates.PineTall and templates.PineShort then
	for clump = 1, 26 do
		local centre = onRing(clump * (360 / 26) + random:NextNumber(-5, 5), CLEAR_RADIUS + 15 + random:NextNumber(0, 230))
		for _ = 1, random:NextInteger(2, 5) do
			local at = centre + Vector3.new(random:NextNumber(-22, 22), 0, random:NextNumber(-22, 22))
			if Vector3.new(at.X, 0, at.Z).Magnitude < CLEAR_RADIUS + 8 or not free(at, 9) then
				continue
			end
			local hit = Workspace:Raycast(Vector3.new(at.X, ground + 400, at.Z), Vector3.new(0, -600, 0), rayParams)
			if not hit then
				continue
			end
			local tall = random:NextNumber() < 0.55
			local tree = (if tall then templates.PineTall else templates.PineShort):Clone()
			tree:ScaleTo(random:NextNumber(0.8, 1.5))
			tree:PivotTo(CFrame.new(hit.Position - Vector3.new(0, 0.6, 0)) * CFrame.Angles(0, random:NextNumber(0, math.pi * 2), 0))
			tree.Parent = trees
			table.insert(placed, Vector3.new(at.X, 0, at.Z))
			count += 1
		end
	end
end
table.insert(report, string.format("%d pines in Workspace.Scenery.Pines", count))

-- The sky.
local sky = Lighting:FindFirstChildOfClass("Sky") or Instance.new("Sky")
local skySet = true
for face, id in SKY do
	if id == 0 then
		skySet = false
	end
end
if skySet then
	for face, id in SKY do
		sky[face] = "rbxassetid://" .. id
	end
	sky.CelestialBodiesShown = true
	sky.StarCount = 0
	sky.SunAngularSize = 14
	sky.Parent = Lighting
end
table.insert(report, if skySet then "sky: the winter skybox" else "sky: NOT SET (no ids yet)")
return table.concat(report, "\n")
