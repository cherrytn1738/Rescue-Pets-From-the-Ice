-- The tutorial's spotlight and words (docs/GAME_DESIGN.md, "UI and controls"), following the saved step
-- (TutorialService on the server moves it on):
--   1 Tap the ice!  2 Build an Ice Pick Post (15 crystals)  3 Free your first creature  4 Equip your new pet
--   5 done: the tutorial code is shown once.
-- Each step lights what to click (Spotlight: the rest of the screen goes dark and can't be clicked):
--   the ice block in your plot (steps 1 and 3; off your plot only the words show, and the guide line,
--   PlotGuide, shows the way home), the BUILD button and then the Ice Pick Post's buy button in the Build
--   window (step 2), the PETS button and then EQUIP BEST in the Pets window (step 4).
-- Another window open (a popup, the shop) hides the spotlight until it closes.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local MapConfig = require(ReplicatedStorage.MapConfig)
local UIKit = require(ReplicatedStorage.UIKit)
local ClientState = require(script.Parent:WaitForChild("ClientState"))
local IceBlocks = require(script.Parent:WaitForChild("IceBlocks"))
local Spotlight = require(script.Parent:WaitForChild("Spotlight"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

-- Each step: the words while its window is closed, the HUD button that opens it, and inside that window
-- the control to press (found by name) with its own words.
local STEPS = {
	{ Text = "Tap the ice to crack it!", Target = "Ice" },
	{ Text = "Build an Ice Pick Post: press BUILD", Target = "Build", Window = "BuildWindow",
		Find = { "IcePickPost", "BuyButton" }, InWindow = "Buy the Ice Pick Post!" },
	{ Text = "Keep tapping: free your first creature!", Target = "Ice" },
	{ Text = "Equip your new pet: press PETS", Target = "Pets", Window = "PetsWindow",
		Find = { "EquipBest" }, InWindow = "Press EQUIP BEST to equip your pet!" },
}

local buttons = {}

local codeShown = false
ClientState.Event("TutorialDone", function(payload)
	if codeShown then
		return
	end
	codeShown = true
	local Banners = require(script.Parent:WaitForChild("Banners"))
	Banners.Big("Tutorial done!", `Free code: {payload.Code} (CODES button)`, Color3.fromRGB(130, 255, 200), 6)
end)

local function inOwnPlot(index: number): boolean
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not root then
		return false
	end
	local localPos = MapConfig.PlotCFrame(index):PointToObjectSpace(root.Position)
	local half = MapConfig.PlotSize / 2 + MapConfig.TapMargin
	return math.abs(localPos.X) <= half and math.abs(localPos.Z) <= half
end

-- The control inside an open window: the path of names under it (the first match of each).
local function findIn(window: ScreenGui, path: { string }): GuiObject?
	local node: Instance? = window
	for _, name in path do
		node = node and node:FindFirstChild(name, true)
	end
	return if node and node:IsA("GuiObject") then node else nil
end

local function menuButton(name: string): GuiButton?
	if buttons[name] == nil then
		buttons[name] = false
		task.spawn(function()
			buttons[name] = UIKit.MenuButton(name)
		end)
	end
	return buttons[name] or nil
end

RunService.RenderStepped:Connect(function()
	local data = ClientState.Data()
	local step = data and data.TutorialStep or 5
	local info = STEPS[step]
	if not info then
		Spotlight.Hide()
		return
	end
	if info.Target == "Ice" then
		if UIKit.AnyWindowOpen() then
			Spotlight.Hide()
			return
		end
		local index = player:GetAttribute("PlotIndex")
		local view = type(index) == "number" and IceBlocks.View(index) or nil
		if view and view.present and inOwnPlot(index) then
			Spotlight.Show(view.block, info.Text)
		else
			Spotlight.Show(nil, info.Text)
		end
		return
	end
	local window = playerGui:FindFirstChild(info.Window)
	local windowOpen = window ~= nil and window:IsA("ScreenGui") and window.Enabled
	if windowOpen then
		local control = findIn(window, info.Find)
		Spotlight.Show(control, if control then info.InWindow else info.Text)
	elseif UIKit.AnyWindowOpen() then
		Spotlight.Hide() -- (another window: the spotlight waits until it closes)
	else
		local button = menuButton(info.Target)
		Spotlight.Show(button, info.Text)
	end
end)
