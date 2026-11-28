-- Tapping the ice (docs/GAME_DESIGN.md, "UI and controls"): inside your plot, a tap anywhere that
-- isn't a button swings your ice pick at the block. Phone: tap; PC: click (Space jumps, as everywhere);
-- gamepad: R2 or A (where you can tap, A taps instead of jumping).
-- The client only counts taps and sends the total every GameConfig.Taps.BatchSeconds (TapBatch);
-- the server caps the rate, decides the damage and pays the crystals. TapFeedback shows the hit at once,
-- and the ice pick in the player's hand (PickService) swings (PickSwing: three animated variants in turn).
-- The backpack bar is hidden, so the pick can't be put away.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ContextActionService = game:GetService("ContextActionService")
local GuiService = game:GetService("GuiService")
local StarterGui = game:GetService("StarterGui")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage.GameConfig)
local MapConfig = require(ReplicatedStorage.MapConfig)
local UIKit = require(ReplicatedStorage.UIKit)
local PickSwing = require(script.Parent.PickSwing)
local Spotlight = require(script.Parent.Spotlight)
local TapFeedback = require(script.Parent.TapFeedback)

local player = Players.LocalPlayer
local remote = ReplicatedStorage:WaitForChild("TapBatch") :: RemoteEvent
local goldenRemote = ReplicatedStorage:WaitForChild("GoldenTap") :: RemoteEvent
local golden = workspace:WaitForChild("GoldenGlacier")
local TAPS = GameConfig.Taps

local pending = 0
local goldenPending = 0
-- The server's tap cap, mirrored here (TapService: MaxPerSecond, with BurstSeconds' worth in hand): a click past
-- it still swings and chips the ice, but it isn't sent and shows no "+N" (the server would ignore it anyway).
local tokens = TAPS.MaxPerSecond * TAPS.BurstSeconds
local tokensAt = os.clock()
local function takeToken(): boolean
	local now = os.clock()
	tokens = math.min(TAPS.MaxPerSecond * TAPS.BurstSeconds, tokens + (now - tokensAt) * TAPS.MaxPerSecond)
	tokensAt = now
	if tokens < 1 then
		return false
	end
	tokens -= 1
	return true
end

pcall(StarterGui.SetCoreGuiEnabled, StarterGui, Enum.CoreGuiType.Backpack, false)

local function swingPick()
	PickSwing.Swing()
end

local function inOwnPlot(): boolean
	local index = player:GetAttribute("PlotIndex")
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if type(index) ~= "number" or not root then
		return false
	end
	local localPos = MapConfig.PlotCFrame(index):PointToObjectSpace(root.Position)
	local half = MapConfig.PlotSize / 2 + MapConfig.TapMargin
	return math.abs(localPos.X) <= half and math.abs(localPos.Z) <= half
end

-- Outside your plot, taps only count on a standing Golden Glacier you're close to.
local function nearGolden(): boolean
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	local spot = golden:GetAttribute("Spot")
	return root ~= nil and golden:GetAttribute("State") == "Active" and typeof(spot) == "Vector3"
		and (root.Position - spot).Magnitude <= GameConfig.GoldenGlacier.Radius
end

local TAP_INPUTS = {
	[Enum.UserInputType.MouseButton1] = true,
	[Enum.UserInputType.Touch] = true,
}
local TAP_KEYS = {
	[Enum.KeyCode.ButtonR2] = true,
}
-- Gamepad A is also the jump button: where you can tap (your plot, or near a standing Golden Glacier) it
-- taps INSTEAD of jumping (a high-priority action that sinks it); anywhere else it jumps as usual. On PC
-- a click taps, so Space always jumps. (Phones keep their jump button.)
local SINK_KEYS = { Enum.KeyCode.ButtonA }

local function tap(screenPosition: Vector2?)
	if UIKit.AnyWindowOpen() or not Spotlight.AllowsTap(screenPosition) then
		return -- (the tutorial's spotlight: only the lit block can be tapped)
	end
	local mine, onGolden = inOwnPlot(), false
	if not mine then
		onGolden = nearGolden()
		if not onGolden then
			return
		end
	end
	swingPick()
	local counted = takeToken()
	if mine then
		if counted then
			pending += 1
		end
		TapFeedback.Tap(screenPosition, counted)
	elseif counted then
		goldenPending += 1
		TapFeedback.Float(screenPosition, "+1", Color3.fromRGB(255, 220, 100))
	end
end

UserInputService.InputBegan:Connect(function(input, processed)
	if processed then
		return -- a button, the thumbstick, the chat...
	end
	if TAP_INPUTS[input.UserInputType] then
		tap(Vector2.new(input.Position.X, input.Position.Y))
	elseif input.UserInputType == Enum.UserInputType.Keyboard or input.UserInputType.Name:find("Gamepad") then
		if TAP_KEYS[input.KeyCode] then
			tap(nil)
		end
	end
end)

local function tapsHere(): boolean
	return not UIKit.AnyWindowOpen() and GuiService.SelectedObject == nil and (inOwnPlot() or nearGolden())
end
ContextActionService:BindActionAtPriority("IceTapKeys", function(_, inputState)
	if not tapsHere() then
		return Enum.ContextActionResult.Pass -- jump (or press the selected button) as usual
	end
	if inputState == Enum.UserInputState.Begin then
		tap(nil)
	end
	return Enum.ContextActionResult.Sink
end, false, Enum.ContextActionPriority.High.Value, table.unpack(SINK_KEYS))

task.spawn(function()
	while true do
		task.wait(TAPS.BatchSeconds)
		if pending > 0 then
			local count = pending
			pending = 0
			remote:FireServer(count)
		end
		if goldenPending > 0 then
			local count = goldenPending
			goldenPending = 0
			goldenRemote:FireServer(count)
		end
	end
end)
