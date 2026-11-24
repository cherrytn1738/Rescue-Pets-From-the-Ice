-- The HUD: the menu buttons down the left edge (BUILD, UPGRADES, PETS, BOOK, REBIRTH, HOME, SHOP, CODES), the settings gear and the crystal counter.
--
--   Menu (left edge): a grid of big square buttons, two to a row: SHOP (the Robux shop) and CODES.
--     Each window finds its button by name (UIKit.MenuButton("Shop") finds "ShopButton") and opens
--     itself. A new window adds one entry to MENU. On touch screens (and Studio's pretend phone screen,
--     StudioScreenSize) the menu sits at the top left, clear of the thumbstick and the jump button.
--   Gamepad: D-pad left selects the first button; from there the D-pad reaches every button (UIKit's
--     selection rim).
--
-- Counters (the game's currency and the like) come with the gameplay; they show display copies the
-- server publishes as player attributes, never values the client decides.
local GuiService = game:GetService("GuiService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)

local BUTTON = 104 -- the grid's squares, in HUD units
local GAP = 14 -- (room for the pictures poking out of each button's top)
local TOP_ROOM = 20 -- the top row's pictures poke above the grid
local COLUMNS = 2
-- Each button: its name (the window looks for <Name>Button), its picture (a UITheme.Icons key; the
-- word alone until the icon is uploaded), its caption and its card palette.
local MENU = {
	{ Name = "Build", Icon = "Build", Text = "BUILD", Palette = "Orange" },
	{ Name = "Upgrades", Icon = "Upgrades", Text = "UPGRADES", Palette = "Green" },
	{ Name = "Pets", Icon = "Pets", Text = "PETS", Palette = "Pink" },
	{ Name = "Book", Icon = "Book", Text = "BOOK", Palette = "Teal" },
	{ Name = "Rebirth", Icon = "Rebirth", Text = "REBIRTH", Palette = "Purple" },
	{ Name = "Home", Icon = "Home", Text = "HOME", Palette = "Ice" },
	{ Name = "Shop", Icon = "Shop", Text = "SHOP", Palette = "Glacier" },
	{ Name = "Codes", Icon = "Codes", Text = "CODES", Palette = "Slate" },
}
local Icons = UIKit.Theme.Icons

local _, root = UIKit.Screen("HUD", 5)

-- The menu ----------------------------------------------------------------------------------------

local rows = math.ceil(#MENU / COLUMNS)
local gridWidth = BUTTON * COLUMNS + GAP * (COLUMNS - 1)
local gridHeight = BUTTON * rows + GAP * (rows - 1)

local menu = Instance.new("Frame")
menu.Name = "Menu"
menu.BackgroundTransparency = 1
menu.Size = UDim2.fromOffset(gridWidth, TOP_ROOM + gridHeight)
menu.Parent = root
local menuScale = Instance.new("UIScale")
menuScale.Parent = menu

local grid = Instance.new("Frame")
grid.Name = "Grid"
grid.BackgroundTransparency = 1
grid.Position = UDim2.fromOffset(0, TOP_ROOM)
grid.Size = UDim2.fromOffset(gridWidth, gridHeight)
grid.Parent = menu
local gridLayout = Instance.new("UIGridLayout")
gridLayout.CellSize = UDim2.fromOffset(BUTTON, BUTTON)
gridLayout.CellPadding = UDim2.fromOffset(GAP, GAP)
gridLayout.SortOrder = Enum.SortOrder.LayoutOrder
gridLayout.Parent = grid
for order, def in MENU do
	local button = ShowcaseKit.HudButton(grid, def.Name .. "Button", Icons[def.Icon], def.Text, def.Palette)
	button.LayoutOrder = order
end

-- The crystal counter (top centre): crystals and crystals per second, counting smoothly toward the
-- server's display copies (the Crystals and CrystalsPerSecond attributes, ~4 updates a second).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local localPlayer = Players.LocalPlayer

local counter = Instance.new("Frame")
counter.Name = "Counter"
counter.BackgroundTransparency = 1
counter.AnchorPoint = Vector2.new(0.5, 0)
counter.Position = UDim2.new(0.5, 0, 0, 6)
counter.Size = UDim2.fromOffset(420, 104)
counter.Parent = root
local counterScale = Instance.new("UIScale")
counterScale.Parent = counter
local crystalsLabel = UIKit.Label(counter, "Crystals", "0", 56)
crystalsLabel.Size = UDim2.new(1, 0, 0, 62)
crystalsLabel.TextXAlignment = Enum.TextXAlignment.Center
local rateLabel = UIKit.Label(counter, "Rate", "+0/s", 30, UIKit.Colors.Gold)
rateLabel.Position = UDim2.fromOffset(0, 62)
rateLabel.Size = UDim2.new(1, 0, 0, 34)
rateLabel.TextXAlignment = Enum.TextXAlignment.Center

-- The level and layer badge, and the Frost Rush timer while one runs.
local badge = UIKit.Label(counter, "Badge", "", 24, UIKit.Colors.Muted)
badge.Position = UDim2.fromOffset(0, 96)
badge.Size = UDim2.new(1, 0, 0, 28)
badge.TextXAlignment = Enum.TextXAlignment.Center
local rush = UIKit.Label(counter, "FrostRush", "", 28, Color3.fromRGB(140, 230, 255))
rush.Position = UDim2.fromOffset(0, 124)
rush.Size = UDim2.new(1, 0, 0, 32)
rush.TextXAlignment = Enum.TextXAlignment.Center
counter.Size = UDim2.fromOffset(420, 160)
local LayerConfig = require(ReplicatedStorage.LayerConfig)
local Workspace = game:GetService("Workspace")

-- The settings gear, top right of the counter.
local gear = UIKit.Button(root, "SettingsButton", "⚙", "Frost", 34)
gear.AnchorPoint = Vector2.new(1, 0)
gear.Position = UDim2.new(1, -12, 0, 6)
gear.Size = UDim2.fromOffset(58, 58)
local gearScale = Instance.new("UIScale")
gearScale.Parent = gear

-- HOME: back to your plot (the server moves you: GoHome).
local goHome = ReplicatedStorage:WaitForChild("GoHome") :: RemoteEvent

local shown = nil
RunService.RenderStepped:Connect(function(dt)
	local target = localPlayer:GetAttribute("Crystals")
	if type(target) ~= "number" then
		return
	end
	local rate = localPlayer:GetAttribute("CrystalsPerSecond") or 0
	-- count toward the target; a spend (target below) drops at once
	if not shown or target < shown then
		shown = target
	else
		shown = math.min(target, shown + math.max((target - shown) * math.min(1, dt * 8), rate * dt))
	end
	crystalsLabel.Text = "💎 " .. NumberFormat.Short(shown)
	rateLabel.Text = "+" .. NumberFormat.Rate(rate) .. "/s"
	local level = localPlayer:GetAttribute("BlockLevel") or 1
	local index = localPlayer:GetAttribute("PlotIndex")
	local plot = index and Workspace:FindFirstChild("Plots") and Workspace.Plots:FindFirstChild("Plot" .. index)
	local layer = LayerConfig.Get(plot and plot.Block:GetAttribute("Layer") or 1)
	badge.Text = `Level {level} · {layer and layer.Name or ""}`
	local endsAt = localPlayer:GetAttribute("FrostRushEndsAt")
	local left = if type(endsAt) == "number" then endsAt - Workspace:GetServerTimeNow() else 0
	rush.Visible = left > 0
	if left > 0 then
		rush.Text = `❄ FROST RUSH x{localPlayer:GetAttribute("FrostRushMultiplier") or 3}  {math.floor(left // 60)}:{string.format("%02d", math.floor(left % 60))}`
	end
end)

grid:WaitForChild("HomeButton").Activated:Connect(function()
	goHome:FireServer()
end)

-- Layout ------------------------------------------------------------------------------------------

local function layout()
	local scale = UIKit.HudScale()
	menuScale.Scale = scale
	counterScale.Scale = scale
	gearScale.Scale = scale
	local touch = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
	if touch or UIKit.IsPretendScreen() then
		-- Touch: the top left, clear of the thumbstick (bottom left) and the jump button (bottom right).
		menu.AnchorPoint = Vector2.new(0, 0)
		menu.Position = UDim2.fromOffset(12, 6)
	else
		menu.AnchorPoint = Vector2.new(0, 0.5)
		menu.Position = UDim2.new(0, 14, 0.46, 0)
	end
end
UIKit.OnScreenChanged(layout)
layout()

-- Gamepad: D-pad left (with nothing selected and no window open) selects the first button; the D-pad
-- then moves round every button on screen, A presses one, B lets go.
local firstButton = grid:FindFirstChild(MENU[1].Name .. "Button")
UserInputService.InputBegan:Connect(function(input, processed)
	if input.KeyCode == Enum.KeyCode.DPadLeft and not processed and not GuiService.SelectedObject and not UIKit.AnyWindowOpen() then
		GuiService.SelectedObject = firstButton
	end
end)

print("[HUD] ready")
