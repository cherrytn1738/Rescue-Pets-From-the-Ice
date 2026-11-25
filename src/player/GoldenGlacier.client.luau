-- The Golden Glacier (docs/GAME_DESIGN.md, "Social and events"), drawn from Workspace.GoldenGlacier's
-- attributes (GoldenGlacierService): during the countdown a golden block hangs high over the plaza ring
-- with the seconds left, then crashes down (shake, shards); while it stands, its HP bar shows the taps
-- left. Taps near it go to the server on GoldenTap (TapInput). Messages show as toasts.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage.GameConfig)
local UITheme = require(ReplicatedStorage.UITheme)
local Banners = require(script.Parent:WaitForChild("Banners"))
local ClientState = require(script.Parent:WaitForChild("ClientState"))
local Effects = require(script.Parent:WaitForChild("Effects"))

local player = Players.LocalPlayer
local state = Workspace:WaitForChild("GoldenGlacier")
local SIZE = Vector3.new(11, 13, 11)

local block = Instance.new("Part")
block.Name = "GoldenGlacierBlock"
block.Anchored = true
block.Size = SIZE
-- golden ice (a flat Glass block with a strong light read as one blown-out yellow square under Future lighting)
block.Color = Color3.fromRGB(255, 196, 70)
block.Material = Enum.Material.Ice
block.Transparency = 0.08
block.Reflectance = 0.05
local light = Instance.new("PointLight")
light.Color = Color3.fromRGB(255, 210, 110)
light.Range = 24
light.Brightness = 1.2
light.Parent = block
local gui = Instance.new("BillboardGui")
gui.Size = UDim2.fromScale(14, 4)
-- in front of the block's lower half (pushed toward the camera, so the block never hides it), so it stays
-- mid-screen next to the block instead of climbing into the HUD's crystal counter
gui.StudsOffsetWorldSpace = Vector3.new(0, -2, 0)
gui.StudsOffset = Vector3.new(0, 0, SIZE.X / 2 + 2.5)
gui.LightInfluence = 0
gui.MaxDistance = 400
gui.Parent = block
local label = Instance.new("TextLabel")
-- white on a dark plate: readable against the gold block and the snow
label.BackgroundColor3 = Color3.fromRGB(40, 28, 6)
label.BackgroundTransparency = 0.3
label.Size = UDim2.fromScale(1, 1)
label.Font = UITheme.Font
label.TextScaled = true
label.TextColor3 = Color3.new(1, 1, 1)
label.TextStrokeTransparency = 0
local labelCorner = Instance.new("UICorner")
labelCorner.CornerRadius = UDim.new(0.3, 0)
labelCorner.Parent = label
label.Parent = gui

local landed = false
local lastState = "Idle"

local function spot(): Vector3
	return state:GetAttribute("Spot") or Vector3.new(0, 0, -34)
end

RunService.RenderStepped:Connect(function()
	local current = state:GetAttribute("State") or "Idle"
	local now = Workspace:GetServerTimeNow()
	local ground = spot() + Vector3.new(0, SIZE.Y / 2, 0)
	if current == "Countdown" then
		if lastState ~= "Countdown" then
			Effects.Sound("GoldenAlarm") -- (everyone: the race is about to start)
		end
		local left = math.max(0, (state:GetAttribute("LandsAt") or now) - now)
		local fall = math.clamp(1 - left / GameConfig.GoldenGlacier.CountdownSeconds, 0, 1)
		local height = 140 * (1 - fall ^ 6)
		block.CFrame = CFrame.new(ground + Vector3.new(0, height, 0)) * CFrame.Angles(0, now % (math.pi * 2), 0)
		label.Text = `GOLDEN GLACIER in {math.ceil(left)}`
		block.Parent = Workspace
		landed = false
	elseif current == "Active" then
		if not landed then
			landed = true
			local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
			if root and (root.Position - ground).Magnitude < 150 then
				Effects.Shake(1.2, 0.8)
			end
			Effects.Sound("GoldenCrash")
		end
		block.CFrame = CFrame.new(ground)
		local hp, hpMax = state:GetAttribute("Hp") or 0, state:GetAttribute("HpMax") or 1
		local left = math.max(0, (state:GetAttribute("EndsAt") or now) - now)
		label.Text = `TAP IT! {hp}/{hpMax}  ·  {math.ceil(left)}s`
		block.Parent = Workspace
	else
		if lastState == "Active" then
			for _ = 1, Effects.Count(24) do
				Effects.Debris({
					Size = Vector3.one * (0.8 + math.random()),
					CFrame = CFrame.new(ground + Vector3.new((math.random() - 0.5) * 8, (math.random() - 0.5) * 10, (math.random() - 0.5) * 8)),
					Color = block.Color,
					Material = Enum.Material.Neon,
					Velocity = Vector3.new((math.random() - 0.5) * 40, 20 + math.random() * 25, (math.random() - 0.5) * 40),
					CanCollide = true,
					Life = 2,
				})
			end
		end
		block.Parent = nil
	end
	lastState = current
end)

ClientState.Event("Golden", function(payload)
	Banners.Toast(payload.Text, Color3.fromRGB(255, 220, 100))
end)
