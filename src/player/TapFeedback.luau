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

function TapFeedback.Tap(screenPosition: Vector2?)
	local index = player:GetAttribute("PlotIndex")
	if type(index) == "number" then
		IceBlocks.Hit(index, 0.3)
	end
	local camera = workspace.CurrentCamera
	local at = screenPosition or (camera.ViewportSize / 2)
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.AnchorPoint = Vector2.new(0.5, 0.5)
	label.Size = UDim2.fromOffset(160, 44)
	label.Position = UDim2.fromOffset(at.X + math.random(-20, 20), at.Y - 20)
	label.Font = UITheme.Font
	label.TextScaled = true
	label.TextColor3 = Color3.fromRGB(190, 240, 255)
	label.TextStrokeTransparency = 0
	label.Text = "+" .. NumberFormat.Short(math.max(1, TapFeedback.TapValue()))
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

return TapFeedback
