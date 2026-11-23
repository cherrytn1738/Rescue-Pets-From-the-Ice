-- The HUD shell: the menu buttons down the left edge, nothing else yet.
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
	{ Name = "Shop", Icon = "Shop", Text = "SHOP", Palette = "Glacier" },
	{ Name = "Codes", Icon = "Codes", Text = "CODES", Palette = "Purple" },
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

-- Layout ------------------------------------------------------------------------------------------

local function layout()
	local scale = UIKit.HudScale()
	menuScale.Scale = scale
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
