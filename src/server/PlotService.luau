--[[
PlotService: the players' plots (docs/GAME_DESIGN.md, "Plot and map layout"). Server only.

 - Builds MapConfig.PlotCount greybox plots in Workspace.Plots at start: a snow square, the snow
   mound for the ice, eight numbered building pads and a low border wall open at the front.
 - Gives each joining player the first free plot (player attribute PlotIndex; the plot's attributes
   Owner (user id) and OwnerName) and frees it when they leave.
 - Shows each owned building as a greybox stand-in on its pad (sized by building and by how many are
   owned; shrunk once the next building up is owned), with a "Name x37" badge. Plain parts until the
   building art is approved.
 - Plot.Block (a Folder) carries the ice block's attributes; every client draws the block from them
   (IceBlockView.client).
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local BuildingConfig = require(ReplicatedStorage.BuildingConfig)
local EconomyRules = require(ReplicatedStorage.EconomyRules)
local MapConfig = require(ReplicatedStorage.MapConfig)

local PlotService = {}

local SNOW = Color3.fromRGB(236, 244, 252)
local SNOW_SHADE = Color3.fromRGB(205, 222, 240)
local PAD = Color3.fromRGB(150, 170, 195)
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

local function buildPlot(index: number): Model
	local cf = MapConfig.PlotCFrame(index)
	local size = MapConfig.PlotSize
	local model = Instance.new("Model")
	model.Name = "Plot" .. index
	model:SetAttribute("Index", index)
	model:SetAttribute("Owner", 0)
	model:SetAttribute("OwnerName", "")

	local base = part(model, "Base", Vector3.new(size, 1, size), cf * CFrame.new(0, -0.3, 0), SNOW)
	model.PrimaryPart = base
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

	local sign = part(model, "Sign", Vector3.new(16, 4, 1), cf * CFrame.new(0, 6, half + 2), Color3.fromRGB(60, 110, 170), Enum.Material.SmoothPlastic)
	label(sign, "Free plot", Vector3.new(0, 3.5, 0), UDim2.fromScale(18, 3.5)).Name = "OwnerLabel"

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
	-- A player arrives at their plot, in front of the ice, whenever they spawn.
	local function watch(player: Player)
		player.CharacterAdded:Connect(function(character)
			local index = PlotService.IndexOf(player)
			if index then
				task.defer(function()
					character:PivotTo(PlotService.ArrivalCFrame(index))
				end)
			end
		end)
	end
	Players.PlayerAdded:Connect(watch)
	for _, player in Players:GetPlayers() do
		watch(player)
	end
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
			PlotService.SendHome(player)
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

-- The greybox stand-ins -------------------------------------------------------------------------

-- How big a building's stand-in is: its pad, a little bigger at each count milestone; taller for
-- buildings further up the list.
local function standInSize(building, order: number, owned: number): Vector3
	local milestones = 0
	for _, milestone in BuildingConfig.StationMilestones do
		if owned >= milestone then
			milestones += 1
		end
	end
	local footprint = building.Pad.Size * (0.45 + 0.1 * milestones)
	local height = (3 + order * 1.6) * (0.8 + 0.12 * milestones)
	return Vector3.new(footprint, height, footprint)
end

-- Redraws the player's building stand-ins from their save.
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
		local stand = folder:FindFirstChild(building.Id)
		if owned <= 0 then
			if stand then
				stand:Destroy()
			end
			continue
		end
		local size = standInSize(building, order, owned)
		if order < topOrder then
			size *= BuildingConfig.FadedScale
		end
		if not stand then
			stand = part(folder, building.Id, size, CFrame.identity, STAND_IN_COLOURS[building.Id], Enum.Material.SmoothPlastic)
			stand.CanCollide = false
			label(stand, "", Vector3.new(0, 0, 0), UDim2.fromScale(11, 2.2))
		end
		stand.Size = size
		stand.CFrame = cf * CFrame.new(building.Pad.X, 0.6 + size.Y / 2, building.Pad.Z)
		local detail = EconomyRules.DetailLevel(data, building.Id)
		stand.Label.StudsOffsetWorldSpace = Vector3.new(0, size.Y / 2 + 2, 0)
		stand.Label.Text.Text = `{building.Name} ×{owned}` .. (if detail >= BuildingConfig.MaxDetailLevel then " ★" else ` ({detail}/10)`)
		stand:SetAttribute("Owned", owned)
		stand:SetAttribute("Detail", detail)
	end
end

return PlotService
