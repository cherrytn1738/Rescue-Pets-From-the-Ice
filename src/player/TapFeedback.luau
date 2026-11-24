--[[
TapFeedback (client): what a tap shows at once, before the server answers (docs/GAME_DESIGN.md,
"Every hit"): the block shudders and a "+N" floats up from where you tapped. N is this client's
estimate of the crystals the tap earns (the server pays the real amount).
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local EconomyRules = require(ReplicatedStorage.EconomyRules)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local UITheme = require(ReplicatedStorage.UITheme)
local ClientState = require(script.Parent.ClientState)
local Effects = require(script.Parent.Effects)
local IceBlocks = require(script.Parent.IceBlocks)

local TapFeedback = {}

local player = Players.LocalPlayer
local gui

local function screen()
	if gui and gui.Parent then
		return gui
	end
	gui = Instance.new("ScreenGui")
	gui.Name = "TapFeedback"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 3
	gui.Parent = player:WaitForChild("PlayerGui")
	return gui
end

-- The crystals one tap is worth, as far as this client can tell.
function TapFeedback.TapValue(): number
	local data = ClientState.Data()
	if not data then
		return 1
	end
	local ok, value = pcall(function()
		return EconomyRules.TapDamage(data) * EconomyRules.Multiplier(data)
	end)
	return if ok then value else 1
end

-- Ice chips off the block and a little crystal spray (the doc's "Every hit").
local function chips(index: number)
	local view = IceBlocks.View(index)
	local camera = workspace.CurrentCamera
	if not view or not view.present then
		return
	end
	local block = view.block
	local toward = (camera.CFrame.Position - block.Position) * Vector3.new(1, 0, 1)
	toward = if toward.Magnitude > 0 then toward.Unit else Vector3.zAxis
	local surface = block.Position + toward * (block.Size.X / 2) + Vector3.new(0, (math.random() - 0.3) * block.Size.Y * 0.5, 0)
	for _ = 1, Effects.Count(4) do
		Effects.Debris({
			Size = Vector3.one * (0.3 + math.random() * 0.35),
			CFrame = CFrame.new(surface + Vector3.new((math.random() - 0.5) * 3, 0, (math.random() - 0.5) * 3)),
			Color = block.Color,
			Material = Enum.Material.Ice,
			Velocity = toward * (10 + math.random() * 10) + Vector3.new((math.random() - 0.5) * 10, 10 + math.random() * 8, (math.random() - 0.5) * 10),
			Life = 0.7,
		})
	end
	for _ = 1, Effects.Count(2) do
		Effects.Debris({
			Size = Vector3.one * 0.35,
			CFrame = CFrame.new(surface) * CFrame.Angles(0, 0, math.rad(45)),
			Color = Color3.fromRGB(120, 230, 255),
			Material = Enum.Material.Neon,
			Velocity = toward * 6 + Vector3.new((math.random() - 0.5) * 6, 16 + math.random() * 6, (math.random() - 0.5) * 6),
			Life = 0.8,
		})
	end
end

-- A number floating up from where you tapped.
function TapFeedback.Float(screenPosition: Vector2?, text: string, color: Color3?)
	local camera = workspace.CurrentCamera
	local at = screenPosition or (camera.ViewportSize / 2)
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.AnchorPoint = Vector2.new(0.5, 0.5)
	label.Size = UDim2.fromOffset(160, 44)
	label.Position = UDim2.fromOffset(at.X + math.random(-20, 20), at.Y - 20)
	label.Font = UITheme.Font
	label.TextScaled = true
	label.TextColor3 = color or Color3.fromRGB(190, 240, 255)
	label.TextStrokeTransparency = 0
	label.Text = text
	label.Parent = screen()
	local tween = TweenService:Create(label, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
		Position = label.Position - UDim2.fromOffset(0, 90),
		TextTransparency = 1,
		TextStrokeTransparency = 1,
	})
	tween:Play()
	tween.Completed:Once(function()
		label:Destroy()
	end)
end

local streak, lastTapAt = 0, 0
function TapFeedback.Tap(screenPosition: Vector2?)
	local index = player:GetAttribute("PlotIndex")
	if type(index) == "number" then
		IceBlocks.Hit(index, 0.3)
		chips(index)
	end
	-- the crunch, higher during a fast streak (once the game has a crunch sound)
	local now = os.clock()
	streak = if now - lastTapAt < 0.35 then math.min(streak + 1, 20) else 0
	lastTapAt = now
	Effects.Sound("Crunch")
	TapFeedback.Float(screenPosition, "+" .. NumberFormat.Short(math.max(1, TapFeedback.TapValue())))
end

function TapFeedback.Streak(): number
	return streak
end

return TapFeedback
