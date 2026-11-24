-- The tutorial's arrow and words (docs/GAME_DESIGN.md, "UI and controls"), following the saved step
-- (TutorialService on the server moves it on):
--   1 Tap the ice!  2 Build an Ice Pick Post (15 crystals)  3 Free your first creature  4 Equip your new pet
--   5 done: the tutorial code is shown once.
-- The arrow is a bouncing pointer over the ice block (steps 1 and 3) or next to the HUD button to press
-- (BUILD for step 2, PETS for step 4); off your plot, the guide line (PlotGuide) shows the way home.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local BlockRules = require(ReplicatedStorage.BlockRules)
local MapConfig = require(ReplicatedStorage.MapConfig)
local UIKit = require(ReplicatedStorage.UIKit)
local ClientState = require(script.Parent:WaitForChild("ClientState"))

local player = Players.LocalPlayer
local STEPS = {
	{ Text = "Tap the ice to crack it!", Target = "Ice" },
	{ Text = "Build an Ice Pick Post: press BUILD", Target = "Build" },
	{ Text = "Keep tapping: free your first creature!", Target = "Ice" },
	{ Text = "Equip your new pet: press PETS", Target = "Pets" },
}

local _, root = UIKit.Screen("Tutorial", 8)
local bubble = UIKit.Label(root, "Bubble", "", 34, Color3.fromRGB(255, 240, 150))
bubble.AnchorPoint = Vector2.new(0.5, 0)
bubble.Position = UDim2.new(0.5, 0, 0, 170)
bubble.Size = UDim2.fromOffset(700, 44)
bubble.TextXAlignment = Enum.TextXAlignment.Center
local pointer = UIKit.Label(root, "Pointer", "👉", 60)
pointer.Size = UDim2.fromOffset(70, 70)
pointer.Visible = false

-- the 3D arrow over the ice: a glowing wedge pointing down, spinning
local cone = Instance.new("WedgePart")
cone.Name = "TutorialArrow"
cone.Anchored, cone.CanCollide, cone.CanQuery, cone.CanTouch = true, false, false, false
cone.Material = Enum.Material.Neon
cone.Color = Color3.fromRGB(255, 225, 80)
cone.Size = Vector3.new(1, 3, 3)
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

RunService.RenderStepped:Connect(function()
	local data = ClientState.Data()
	local step = data and data.TutorialStep or 5
	local info = STEPS[step]
	bubble.Visible = info ~= nil and not UIKit.AnyWindowOpen()
	pointer.Visible = false
	cone.Parent = nil
	if not info then
		return
	end
	bubble.Text = info.Text
	local bob = math.sin(os.clock() * 5)
	if info.Target == "Ice" then
		local index = player:GetAttribute("PlotIndex")
		local level = player:GetAttribute("BlockLevel") or 1
		if index then
			local top = MapConfig.BlockBase(index).Position + Vector3.new(0, BlockRules.Height(level) + 4 + bob, 0)
			cone.CFrame = CFrame.new(top) * CFrame.Angles(0, os.clock(), 0) * CFrame.Angles(math.rad(-90), 0, 0)
			cone.Parent = Workspace
		end
	else
		if not buttons[info.Target] then
			task.spawn(function()
				buttons[info.Target] = UIKit.MenuButton(info.Target)
			end)
		end
		local button = buttons[info.Target]
		if button and button.AbsoluteSize.X > 0 then
			pointer.Visible = not UIKit.AnyWindowOpen()
			pointer.Position = UDim2.fromOffset(button.AbsolutePosition.X + button.AbsoluteSize.X + 6 + bob * 6, button.AbsolutePosition.Y + button.AbsoluteSize.Y / 2 - 35)
		end
	end
end)
