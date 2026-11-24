-- Tapping the ice (docs/GAME_DESIGN.md, "UI and controls"): inside your plot, a tap anywhere that
-- isn't a button swings your ice pick at the block. Phone: tap; PC: click or Space; gamepad: R2 or A.
-- The client only counts taps and sends the total every GameConfig.Taps.BatchSeconds (TapBatch);
-- the server caps the rate, decides the damage and pays the crystals. TapFeedback shows the hit at once.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage.GameConfig)
local MapConfig = require(ReplicatedStorage.MapConfig)
local UIKit = require(ReplicatedStorage.UIKit)
local TapFeedback = require(script.Parent.TapFeedback)

local player = Players.LocalPlayer
local remote = ReplicatedStorage:WaitForChild("TapBatch") :: RemoteEvent
local goldenRemote = ReplicatedStorage:WaitForChild("GoldenTap") :: RemoteEvent
local golden = workspace:WaitForChild("GoldenGlacier")
local TAPS = GameConfig.Taps

local pending = 0
local goldenPending = 0
local lastTap = 0
local MIN_GAP = 1 / TAPS.MaxPerSecond -- taps faster than the server allows don't even count here

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
	[Enum.KeyCode.Space] = true,
	[Enum.KeyCode.ButtonR2] = true,
	[Enum.KeyCode.ButtonA] = true,
}

local function tap(screenPosition: Vector2?)
	if UIKit.AnyWindowOpen() then
		return
	end
	local mine, onGolden = inOwnPlot(), false
	if not mine then
		onGolden = nearGolden()
		if not onGolden then
			return
		end
	end
	local now = os.clock()
	if now - lastTap < MIN_GAP then
		return
	end
	lastTap = now
	if mine then
		pending += 1
		TapFeedback.Tap(screenPosition)
	else
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
