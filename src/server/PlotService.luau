--[[
PlotService: the players' plots (docs/GAME_DESIGN.md, "Plot and map layout"). Server only.

 - Builds MapConfig.PlotCount greybox plots in Workspace.Plots at start: a snow square, the snow
   mound for the ice, eight numbered building pads and a low border wall open at the front.
 - Gives each joining player the first free plot (player attribute PlotIndex; the plot's attributes
   Owner (user id) and OwnerName) and frees it when they leave.
 - Shows each owned building on its pad, facing the ice: the real station for its tier (a clone of
   ServerStorage.BuildingTemplates.<Id>.T<tier>, built in Studio by tools/studio/build_templates.luau)
   with the upgrade part sets the player owns, shrunk to 60% and without its Neon glow once the next
   building up is owned, and a "Name x37" badge. A greybox stand-in is the fallback while a template
   is missing.
 - Plot.Block (a Folder) carries the ice block's attributes; every client draws the block from them
   (IceBlockView.client).
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

local BuildingConfig = require(ReplicatedStorage.BuildingConfig)
local EconomyRules = require(ReplicatedStorage.EconomyRules)
local MapConfig = require(ReplicatedStorage.MapConfig)

local PlotService = {}

local SNOW = Color3.fromRGB(236, 244, 252)
local SNOW_SHADE = Color3.fromRGB(205, 222, 240)
local PAD = Color3.fromRGB(150, 170, 195)
local SIGN = Color3.fromRGB(60, 110, 170)
-- Greybox colours, one per building (stand-ins until the art is approved).
local STAND_IN_COLOURS = {
	IcePickPost = Color3.fromRGB(160, 120, 80),
	HeatLamp = Color3.fromRGB(255, 170, 60),
	ChiselMill = Color3.fromRGB(120, 150, 200),
	IceDrill = Color3.fromRGB(200, 200, 90),
	WreckingCrane = Color3.fromRGB(230, 180, 40),
	FlamethrowerTurret = Color3.fromRGB(220, 80, 50),
	LavaPump = Color3.fromRGB(200, 50, 30),
	SunMirrorTower = Color3.fromRGB(255, 230, 120),
}

local plotsFolder
local plots = {} -- [index] = Model
local owners = {} -- [index] = player
local listeners = {}

local function part(parent: Instance, name: string, size: Vector3, cframe: CFrame, color: Color3, material: Enum.Material?): Part
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.Size = size
	p.CFrame = cframe
	p.Color = color
	p.Material = material or Enum.Material.Snow
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = parent
	return p
end

local function label(parent: Instance, text: string, offset: Vector3, size: UDim2?): BillboardGui
	local gui = Instance.new("BillboardGui")
	gui.Name = "Label"
	gui.Size = size or UDim2.fromScale(10, 2.5) -- in studs, so it shrinks with distance like the world
	gui.StudsOffsetWorldSpace = offset
	gui.MaxDistance = 160
	gui.AlwaysOnTop = false
	gui.Parent = parent
	local text_ = Instance.new("TextLabel")
	text_.Name = "Text"
	text_.BackgroundTransparency = 1
	text_.Size = UDim2.fromScale(1, 1)
	text_.Font = Enum.Font.FredokaOne
	text_.TextScaled = true
	text_.TextColor3 = Color3.new(1, 1, 1)
	text_.TextStrokeTransparency = 0
	text_.Text = text
	text_.Parent = gui
	return gui
end

-- A station's name tag: small, and hidden until NameTags.client shows it (near the station, or your own plot).
local function nameTag(parent: Instance): BillboardGui
	local size = BuildingConfig.NameTags.Size
	local gui = label(parent, "", Vector3.zero, UDim2.fromScale(size.X, size.Y))
	gui.Enabled = false
	gui:SetAttribute("NameTag", true)
	return gui
end

local function buildPlot(index: number): Model
	local cf = MapConfig.PlotCFrame(index)
	local size = MapConfig.PlotSize
	local model = Instance.new("Model")
	model.Name = "Plot" .. index
	model:SetAttribute("Index", index)
	model:SetAttribute("Owner", 0)
	model:SetAttribute("OwnerName", "")

	-- The floor: the place's snow terrain shows through (drifts and ice patches: MapConfig.PlotGround); the
	-- Base is an invisible floor just above it.
	local base = part(model, "Base", Vector3.new(size, 1, size), cf * CFrame.new(0, -0.3, 0), SNOW)
	base.Transparency = 1
	base.CastShadow = false
	model.PrimaryPart = base
	local footpath = MapConfig.PlotGround.Footpath
	local pathLength = size / 2 - footpath.FromZ
	part(model, "Footpath", Vector3.new(footpath.Width, 0.4, pathLength), cf * CFrame.new(0, 0.15, footpath.FromZ + pathLength / 2), footpath.Color)
	local mound = MapConfig.Mound
	part(model, "Mound", Vector3.new(mound.Size, mound.Height, mound.Size), cf * CFrame.new(0, mound.Height / 2, 0), SNOW_SHADE)
	part(model, "MoundTop", Vector3.new(mound.Size - 6, 1, mound.Size - 6), cf * CFrame.new(0, mound.Height + 0.5, 0), SNOW)

	-- The border: a low wall on three sides, and the front (+Z, toward the plaza) open in the middle.
	local border = Instance.new("Folder")
	border.Name = "Border"
	border.Parent = model
	local b = MapConfig.Border
	local half = size / 2
	part(border, "Back", Vector3.new(size, b.Height, b.Thickness), cf * CFrame.new(0, b.Height / 2, -half), SNOW_SHADE)
	part(border, "Left", Vector3.new(b.Thickness, b.Height, size), cf * CFrame.new(-half, b.Height / 2, 0), SNOW_SHADE)
	part(border, "Right", Vector3.new(b.Thickness, b.Height, size), cf * CFrame.new(half, b.Height / 2, 0), SNOW_SHADE)
	local side = (size - b.FrontGap) / 2
	part(border, "FrontLeft", Vector3.new(side, b.Height, b.Thickness), cf * CFrame.new(-half + side / 2, b.Height / 2, half), SNOW_SHADE)
	part(border, "FrontRight", Vector3.new(side, b.Height, b.Thickness), cf * CFrame.new(half - side / 2, b.Height / 2, half), SNOW_SHADE)

	-- The pads, numbered as in the doc.
	local pads = Instance.new("Folder")
	pads.Name = "Pads"
	pads.Parent = model
	for _, building in BuildingConfig.Buildings do
		local pad = building.Pad
		local p = part(pads, building.Id, Vector3.new(pad.Size, 0.4, pad.Size), cf * CFrame.new(pad.X, 0.4, pad.Z), PAD, Enum.Material.Slate)
		p:SetAttribute("PadIndex", pad.Index)
	end

	local stands = Instance.new("Folder")
	stands.Name = "Buildings"
	stands.Parent = model

	-- The name sign: an arch over the open front (the beam is "Sign", carrying the owner's name).
	local arch = MapConfig.Arch
	local top = arch.ClearHeight + arch.BeamHeight
	local postX = b.FrontGap / 2 + arch.PostSize / 2
	for _, sideX in { -1, 1 } do
		local post = part(border, sideX < 0 and "ArchLeft" or "ArchRight", Vector3.new(arch.PostSize, top, arch.PostSize), cf * CFrame.new(sideX * postX, top / 2, half), SIGN, Enum.Material.SmoothPlastic)
		part(post, "Cap", Vector3.new(arch.PostSize + 1, 1, arch.PostSize + 1), cf * CFrame.new(sideX * postX, top + 0.5, half), SNOW)
	end
	local sign = part(model, "Sign", Vector3.new(b.FrontGap + 2 * arch.PostSize, arch.BeamHeight, arch.BeamDepth), cf * CFrame.new(0, arch.ClearHeight + arch.BeamHeight / 2, half), SIGN, Enum.Material.SmoothPlastic)
	label(sign, "Free plot", Vector3.new(0, arch.BeamHeight / 2 + 2.5, 0), UDim2.fromScale(22, 4.5)).Name = "OwnerLabel"

	local block = Instance.new("Folder")
	block.Name = "Block"
	block:SetAttribute("Present", false)
	block.Parent = model
	local anchor = Instance.new("Part")
	anchor.Name = "BlockAnchor" -- the centre of the mound top, where the block stands
	anchor.Anchored = true
	anchor.CanCollide, anchor.CanQuery, anchor.CanTouch = false, false, false
	anchor.Transparency = 1
	anchor.Size = Vector3.one
	anchor.CFrame = MapConfig.BlockBase(index)
	anchor.Parent = model

	model.Parent = plotsFolder
	return model
end

function PlotService.Start()
	plotsFolder = Instance.new("Folder")
	plotsFolder.Name = "Plots"
	plotsFolder.Parent = Workspace
	for index = 1, MapConfig.PlotCount do
		plots[index] = buildPlot(index)
	end
	Players.PlayerRemoving:Connect(PlotService.Release)
	-- (Players spawn in the plaza; the Home button and the guide line bring them here: PlazaService.)
end

-- Sends the player's character to their plot.
function PlotService.SendHome(player: Player): boolean
	local index = PlotService.IndexOf(player)
	local character = player.Character
	if not index or not character then
		return false
	end
	character:PivotTo(PlotService.ArrivalCFrame(index))
	return true
end

-- Gives the player the first free plot. Returns its index, or nil when every plot is taken.
function PlotService.Assign(player: Player): number?
	for index = 1, MapConfig.PlotCount do
		if owners[index] == player then
			return index
		end
	end
	for index = 1, MapConfig.PlotCount do
		if not owners[index] then
			owners[index] = player
			local plot = plots[index]
			plot:SetAttribute("Owner", player.UserId)
			plot:SetAttribute("OwnerName", player.DisplayName)
			plot.Sign.OwnerLabel.Text.Text = player.DisplayName .. "'s plot"
			player:SetAttribute("PlotIndex", index)
			for _, callback in listeners do
				task.spawn(callback, player, index)
			end
			return index
		end
	end
	warn("[Plots] no free plot for " .. player.Name)
	return nil
end

-- callback(player, index) runs whenever a player gets a plot.
function PlotService.OnAssigned(callback)
	table.insert(listeners, callback)
end

function PlotService.Release(player: Player)
	for index = 1, MapConfig.PlotCount do
		if owners[index] == player then
			owners[index] = nil
			local plot = plots[index]
			plot:SetAttribute("Owner", 0)
			plot:SetAttribute("OwnerName", "")
			plot.Sign.OwnerLabel.Text.Text = "Free plot"
			plot.Buildings:ClearAllChildren()
			local block = plot.Block
			for name in block:GetAttributes() do
				block:SetAttribute(name, nil)
			end
			block:SetAttribute("Present", false)
		end
	end
end

function PlotService.IndexOf(player: Player): number?
	for index, owner in owners do
		if owner == player then
			return index
		end
	end
	return nil
end

function PlotService.PlotOf(player: Player): Model?
	local index = PlotService.IndexOf(player)
	return index and plots[index]
end

function PlotService.Plot(index: number): Model?
	return plots[index]
end

-- Is the player's character standing in their own plot (with a little slack)?
function PlotService.InOwnPlot(player: Player): boolean
	local index = PlotService.IndexOf(player)
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not index or not root then
		return false
	end
	local localPos = MapConfig.PlotCFrame(index):PointToObjectSpace(root.Position)
	local half = MapConfig.PlotSize / 2 + MapConfig.TapMargin
	return math.abs(localPos.X) <= half and math.abs(localPos.Z) <= half and localPos.Y > -10 and localPos.Y < 60
end

-- Where a player arrives in their plot: in front of the ice, facing it.
function PlotService.ArrivalCFrame(index: number): CFrame
	local spot = MapConfig.PlotPoint(index, MapConfig.TapSpot.X, MapConfig.TapSpot.Z, 4)
	local ice = MapConfig.PlotPoint(index, 0, 0, 4)
	return CFrame.lookAt(spot, ice)
end

-- The stations ---------------------------------------------------------------------------------

-- Which station tier a count of copies shows (1-5 at the StationMilestones; 0 below the first).
local function tierFor(owned: number): number
	local tier = 0
	for index, milestone in BuildingConfig.StationMilestones do
		if owned >= milestone then
			tier = index
		end
	end
	return tier
end

-- The real station for a building's tier, if its template has been built in Studio.
local warnedMissing = {}
local function template(id: string, tier: number): Model?
	local folder = ServerStorage:FindFirstChild("BuildingTemplates")
	local set = folder and folder:FindFirstChild(id)
	local model = set and set:FindFirstChild("T" .. tier)
	if not model and not warnedMissing[id .. tier] then
		warnedMissing[id .. tier] = true
		warn(`[Plot] no template BuildingTemplates.{id}.T{tier}: showing a stand-in`)
	end
	return model
end

-- Which of a building's five upgrades the player owns ({ [1..5] = true }) and a short key for them.
local function ownedUpgrades(data, id: string)
	local owned, key = {}, ""
	for index = 1, 5 do
		if table.find(data.Upgrades, id .. "Upgrade" .. index) then
			owned[index] = true
			key ..= index
		end
	end
	return owned, key
end

-- Where a station stands: on its pad's top, turned so its front (-Z) faces the ice in the middle.
local function padCFrame(plotCFrame: CFrame, pad): CFrame
	local at = Vector3.new(pad.X, 0.6, pad.Z)
	return plotCFrame * CFrame.lookAt(at, Vector3.new(0, 0.6, 0))
end

-- A clone of the tier's template with only the owned upgrade sets; faded ones shrink and stop glowing.
local function realStation(source: Model, upgrades, faded: boolean): Model
	local model = source:Clone()
	local sets = model:FindFirstChild("Upgrades")
	if sets then
		for index = 1, 5 do
			local set = sets:FindFirstChild("U" .. index)
			if set and not upgrades[index] then
				set:Destroy()
			end
		end
	end
	if faded then
		for _, d in model:GetDescendants() do
			if d:IsA("BasePart") and d.Material == Enum.Material.Neon then
				d.Material = Enum.Material.SmoothPlastic
			end
		end
		model:ScaleTo(BuildingConfig.FadedScale)
	end
	return model
end

-- The fence ring the faded Ice Pick Posts become: posts round the ice, an invisible Root on the pad for the badge.
local function fenceStation(plotCFrame: CFrame, pad): Model
	local fence = BuildingConfig.Fence
	local model = Instance.new("Model")
	local root = Instance.new("Part")
	root.Name = "Root"
	root.Anchored = true
	root.CanCollide, root.CanQuery, root.CanTouch = false, false, false
	root.Transparency = 1
	root.Size = Vector3.new(1, 0.2, 1)
	root.CFrame = plotCFrame * CFrame.new(pad.X, 0.6, pad.Z)
	root.Parent = model
	model.PrimaryPart = root
	model:SetAttribute("Fence", true)
	local source = template(fence.Building, 1)
	if not source then
		return model
	end
	local prefix = fence.Building .. "T1"
	for slot = 0, fence.Slots - 1 do
		local fromFront = math.min(slot, fence.Slots - slot)
		if fromFront <= fence.FrontGap then
			continue
		end
		local angle = slot / fence.Slots * math.pi * 2
		local post = Instance.new("Model")
		post.Name = "FencePost" .. slot
		for _, piece in source:GetChildren() do
			if piece:IsA("MeshPart") and table.find(fence.Parts, string.sub(piece.Name, #prefix + 1)) then
				local copy = piece:Clone()
				copy.CanCollide, copy.CanQuery = false, false
				copy.Parent = post
			end
		end
		post.WorldPivot = CFrame.identity
		post:ScaleTo(fence.Scale)
		local at = Vector3.new(math.sin(angle) * fence.Radius, 0.2, math.cos(angle) * fence.Radius)
		post:PivotTo(plotCFrame * CFrame.lookAt(at, Vector3.new(0, 0.2, 0)))
		post.Parent = model
	end
	return model
end

-- How big a building's stand-in is: its pad, a little bigger at each count milestone; taller for
-- buildings further up the list.
local function standInSize(building, order: number, owned: number): Vector3
	local milestones = tierFor(owned)
	local footprint = building.Pad.Size * (0.45 + 0.1 * milestones)
	local height = (3 + order * 1.6) * (0.8 + 0.12 * milestones)
	return Vector3.new(footprint, height, footprint)
end

-- Redraws the player's stations from their save. A station is rebuilt only when its look changes
-- (tier, owned upgrade sets, faded); otherwise just its badge and attributes update.
function PlotService.RefreshBuildings(player: Player, data)
	local index = PlotService.IndexOf(player)
	if not index then
		return
	end
	local folder = plots[index].Buildings
	local cf = MapConfig.PlotCFrame(index)
	-- the highest building owned: everything below it fades (shrinks to 60%)
	local topOrder = 0
	for order, building in BuildingConfig.Buildings do
		if (data.Buildings[building.Id] or 0) > 0 then
			topOrder = order
		end
	end
	for order, building in BuildingConfig.Buildings do
		local owned = data.Buildings[building.Id] or 0
		local station = folder:FindFirstChild(building.Id)
		if owned <= 0 then
			if station then
				station:Destroy()
			end
			continue
		end
		local tier = tierFor(owned)
		local faded = order < topOrder
		local upgrades, upgradeKey = ownedUpgrades(data, building.Id)
		local source = template(building.Id, tier)
		local fenced = faded and building.Id == BuildingConfig.Fence.Building
		local look = `{tier}:{upgradeKey}:{faded}:{source ~= nil}:{fenced}`
		if station and station:GetAttribute("Look") ~= look then
			station:Destroy()
			station = nil
		end
		local height
		if fenced then
			if not station then
				station = fenceStation(cf, building.Pad)
				station.Name = building.Id
				station:SetAttribute("Look", look)
				nameTag(station.PrimaryPart)
				station.Parent = folder
			end
			height = 2
		elseif source then
			if not station then
				station = realStation(source, upgrades, faded)
				station.Name = building.Id
				station:SetAttribute("Look", look)
				nameTag(station.PrimaryPart)
				station:PivotTo(padCFrame(cf, building.Pad))
				station.Parent = folder
			end
			height = source:GetExtentsSize().Y * (if faded then BuildingConfig.FadedScale else 1)
		else
			local size = standInSize(building, order, owned) * (if faded then BuildingConfig.FadedScale else 1)
			if not station then
				station = part(folder, building.Id, size, CFrame.identity, STAND_IN_COLOURS[building.Id], Enum.Material.SmoothPlastic)
				station.CanCollide = false
				station:SetAttribute("Look", look)
				nameTag(station)
			end
			station.Size = size
			station.CFrame = cf * CFrame.new(building.Pad.X, 0.6 + size.Y / 2, building.Pad.Z)
			height = size.Y / 2 -- (the badge sits on the stand-in's centre)
		end
		local badge = if station:IsA("Model") then station.PrimaryPart.Label else station.Label
		local detail = EconomyRules.DetailLevel(data, building.Id)
		badge.StudsOffsetWorldSpace = Vector3.new(0, height + 2, 0)
		badge.Text.Text = `{building.Name} ×{owned}` .. (if detail >= BuildingConfig.MaxDetailLevel then " ★" else ` ({detail}/10)`)
		station:SetAttribute("Owned", owned)
		station:SetAttribute("Detail", detail)
		station:SetAttribute("Faded", faded)
	end
end

return PlotService
