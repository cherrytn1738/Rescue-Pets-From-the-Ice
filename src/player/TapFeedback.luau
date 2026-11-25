--[[
TapFeedback (client): what a tap shows at once, before the server answers (docs/GAME_DESIGN.md,
"Every hit"): the block shudders, the tap sound plays and a "+N" floats up from where you tapped. N is
this client's estimate of the crystals the tap earns (the server pays the real amount). The tap sound
always plays but is capped (AudioConfig.Rules.Tap, SoundRules.TapLimiter), so an autoclicker can't stack
dozens; a fast streak lifts its pitch a little.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Audio = require(ReplicatedStorage.Audio)
local AudioConfig = require(ReplicatedStorage.AudioConfig)
local EconomyRules = require(ReplicatedStorage.EconomyRules)
local IceLooks = require(ReplicatedStorage.IceLooks)
local SoundRules = require(ReplicatedStorage.SoundRules)
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

-- Your crystal and spark colours (ice upgrades, ice pick tier).
local function colours(): (Color3, Color3)
	local data = ClientState.Data()
	if not data then
		return IceLooks.CrystalColour(0), IceLooks.PickSparks[1]
	end
	return IceLooks.CrystalColour(EconomyRules.IceTiersTotal(data)), IceLooks.PickSparks[EconomyRules.PickTier(data)] or IceLooks.PickSparks[1]
end

-- Ice chips off the block, a little crystal spray and your pick's sparks (the doc's "Every hit").
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
	local crystal, spark = colours()
	for _ = 1, Effects.Count(2) do
		Effects.Debris({
			Size = Vector3.one * 0.35,
			CFrame = CFrame.new(surface) * CFrame.Angles(0, 0, math.rad(45)),
			Color = crystal,
			Material = Enum.Material.Neon,
			Velocity = toward * 6 + Vector3.new((math.random() - 0.5) * 6, 16 + math.random() * 6, (math.random() - 0.5) * 6),
			Life = 0.8,
		})
	end
	for _ = 1, Effects.Count(3) do
		Effects.Debris({
			Size = Vector3.new(0.12, 0.12, 0.7),
			CFrame = CFrame.lookAt(surface, surface + toward + Vector3.new((math.random() - 0.5) * 2, math.random(), (math.random() - 0.5) * 2)),
			Color = spark,
			Material = Enum.Material.Neon,
			Velocity = toward * (16 + math.random() * 10) + Vector3.new((math.random() - 0.5) * 14, 6 + math.random() * 10, (math.random() - 0.5) * 14),
			Spin = Vector3.zero,
			Life = 0.35,
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
local tapSounds = SoundRules.TapLimiter(AudioConfig.Rules.Tap)
function TapFeedback.Tap(screenPosition: Vector2?)
	local index = player:GetAttribute("PlotIndex")
	if type(index) == "number" then
		IceBlocks.Hit(index, 0.3)
		chips(index)
	end
	-- the tap sound (capped), a little higher during a fast streak
	local now = os.clock()
	streak = if now - lastTapAt < 0.35 then math.min(streak + 1, 20) else 0
	lastTapAt = now
	if tapSounds:Allow(now) then
		Audio.Play("Tap", { Speed = SoundRules.TapSpeed(streak, AudioConfig.Rules.Tap) })
	end
	TapFeedback.Float(screenPosition, "+" .. NumberFormat.Short(math.max(1, TapFeedback.TapValue())))
end

function TapFeedback.Streak(): number
	return streak
end

-- os.clock() of your last tap (the building chip and the income tick stay quiet just after one).
function TapFeedback.LastTapAt(): number
	return lastTapAt
end

return TapFeedback
