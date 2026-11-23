--[[
IceBlocks (client): draws every plot's ice block from the attributes the server puts on
Workspace.Plots.PlotN.Block (IceBlockService): Present, Level, Layer, CreatureId, Rarity, Hp, HpMax,
Stage, ArriveAt. Display only.

Greybox for now (Milestone 2): a see-through block of the layer's colour, sized by level
(BlockRules.Height), on the plot's mound, with the overhead HP bar (crack %, level and layer).
IceBlocks.Hit(plotIndex, strength) makes a block shudder (taps, buildings).
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local BlockRules = require(ReplicatedStorage.BlockRules)
local LayerConfig = require(ReplicatedStorage.LayerConfig)
local MapConfig = require(ReplicatedStorage.MapConfig)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local UITheme = require(ReplicatedStorage.UITheme)

local IceBlocks = {}

local LAYER_COLOURS = {
	Color3.fromRGB(236, 244, 255), -- Fresh Snow
	Color3.fromRGB(165, 215, 255), -- Blue Ice
	Color3.fromRGB(60, 115, 210), -- Ancient Ice
	Color3.fromRGB(150, 235, 255), -- Crystal Ice
	Color3.fromRGB(25, 95, 105), -- Primordial Ice
	Color3.fromRGB(20, 22, 34), -- Frozen Core
}

local views = {} -- [plot] = view

local function overhead(parent: BasePart)
	local gui = Instance.new("BillboardGui")
	gui.Name = "Overhead"
	gui.Size = UDim2.fromOffset(260, 74)
	gui.MaxDistance = 160
	gui.LightInfluence = 0
	gui.Parent = parent

	local title = Instance.new("TextLabel")
	title.Name = "Title"
	title.BackgroundTransparency = 1
	title.Size = UDim2.new(1, 0, 0, 26)
	title.Font = UITheme.Font
	title.TextScaled = true
	title.TextColor3 = Color3.new(1, 1, 1)
	title.TextStrokeTransparency = 0
	title.Parent = gui

	local trough = Instance.new("Frame")
	trough.Name = "Bar"
	trough.Position = UDim2.fromOffset(0, 30)
	trough.Size = UDim2.new(1, 0, 0, 30)
	trough.BackgroundColor3 = UITheme.Progress.trough
	trough.Parent = gui
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 10)
	corner.Parent = trough
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 3
	stroke.Parent = trough

	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.BackgroundColor3 = Color3.new(1, 1, 1)
	fill.Size = UDim2.fromScale(1, 1)
	fill.Parent = trough
	local fillCorner = corner:Clone()
	fillCorner.Parent = fill
	local gradient = Instance.new("UIGradient")
	gradient.Rotation = 90
	gradient.Color = ColorSequence.new(UITheme.Progress.top, UITheme.Progress.bottom)
	gradient.Parent = fill

	local text = Instance.new("TextLabel")
	text.Name = "Text"
	text.BackgroundTransparency = 1
	text.Size = UDim2.fromScale(1, 1)
	text.Font = UITheme.Font
	text.TextScaled = true
	text.TextColor3 = Color3.new(1, 1, 1)
	text.TextStrokeTransparency = 0
	text.ZIndex = 3
	text.Parent = trough
	return gui
end

local function makeView(plot: Model)
	-- (computed, not read from the plot: with streaming on, a far plot's parts may not be here)
	local index = plot:GetAttribute("Index")
	local base = MapConfig.BlockBase(index)
	local folder = plot:WaitForChild("Block")
	local block = Instance.new("Part")
	block.Name = "IceBlock"
	block.Anchored = true
	block.CanCollide = true
	block.CastShadow = true
	block.Material = Enum.Material.Ice
	block.Transparency = 0.25
	block.Size = Vector3.new(10, 14, 10)
	block.Parent = Workspace:FindFirstChild("ClientIce") or (function()
		local f = Instance.new("Folder")
		f.Name = "ClientIce"
		f.Parent = Workspace
		return f
	end)()
	local view = {
		plot = plot,
		folder = folder,
		index = index,
		base = base,
		block = block,
		gui = overhead(block),
		shake = 0,
		shownHp = nil,
	}
	views[plot] = view
	return view
end

local function update(view, dt: number)
	local folder = view.folder
	local present = folder:GetAttribute("Present") == true
	local level = folder:GetAttribute("Level") or 1
	local layer = folder:GetAttribute("Layer") or 1
	local hp = folder:GetAttribute("Hp") or 0
	local hpMax = folder:GetAttribute("HpMax") or 1
	local height = BlockRules.Height(level)
	local size = Vector3.new(height * 0.78, height, height * 0.78)
	view.shake = math.max(0, view.shake - dt * 6)
	local wobble = if view.shake > 0 then CFrame.Angles(math.rad(math.sin(os.clock() * 60) * view.shake * 2), 0, math.rad(math.cos(os.clock() * 53) * view.shake * 2)) else CFrame.identity
	if present then
		view.block.Transparency = if layer == 1 then 0.08 else 0.3
		view.block.Size = size
		view.block.Color = LAYER_COLOURS[layer] or LAYER_COLOURS[1]
		view.block.CFrame = view.base * CFrame.new(0, height / 2 - 0.5, 0) * wobble
	else
		view.block.Transparency = 1
		view.block.CFrame = view.base * CFrame.new(0, -height, 0)
	end
	view.block.CanCollide = present
	-- the HP bar counts smoothly toward the server's value
	view.shownHp = if view.shownHp then view.shownHp + (hp - view.shownHp) * math.min(1, dt * 10) else hp
	local share = BlockRules.DamageShare(view.shownHp, hpMax)
	local gui = view.gui
	gui.Enabled = present
	gui.StudsOffsetWorldSpace = Vector3.new(0, height / 2 + 3, 0)
	local layerInfo = LayerConfig.Get(layer)
	gui.Title.Text = `Level {level} · {layerInfo and layerInfo.Name or ""}`
	gui.Bar.Fill.Size = UDim2.fromScale(math.clamp(1 - share, 0, 1), 1)
	gui.Bar.Text.Text = `{NumberFormat.Short(math.max(0, view.shownHp))} HP · {math.floor(share * 100)}% cracked`
end

-- A tap or a building hit: the block shudders.
function IceBlocks.Hit(plotIndex: number, strength: number?)
	local plots = Workspace:FindFirstChild("Plots")
	local plot = plots and plots:FindFirstChild("Plot" .. plotIndex)
	local view = plot and views[plot]
	if view then
		view.shake = math.min(1, view.shake + (strength or 0.35))
	end
end

function IceBlocks.View(plotIndex: number)
	local plots = Workspace:FindFirstChild("Plots")
	local plot = plots and plots:FindFirstChild("Plot" .. plotIndex)
	return plot and views[plot]
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
			update(view, dt)
		end
	end)
end

return IceBlocks
