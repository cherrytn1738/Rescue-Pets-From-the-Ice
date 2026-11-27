--[[
TapFeedback (client): what a tap on the ice shows at once (docs/GAME_DESIGN.md, "Every hit"):
 * in the world: the block shudders, ice chips, crystal bits and your pick's sparks fly off it;
 * the tap sound, capped (AudioConfig.Rules.Tap, SoundRules.TapLimiter) so an autoclicker can't stack dozens; a
   fast streak lifts its pitch a little;
 * at the cursor (EffectsConfig.ClickBurst): a small white flash with short streaks shooting out where you
   clicked or touched (the streaks are left out with reduced effects), and "+N" popping up 30-70 px away at a
   random angle, with a little jiggle, floating up and fading. With a gamepad both show at the ice block.
N is what the tap earns: the server's TapValue attribute (Economy.TapValue, the tap's damage times every
multiplier), so it matches the crystal counter. The client never sends an amount: it only counts taps.
Auto Pick's taps happen on the server and show nothing here. Bursts and numbers come from small pools (at most
MaxBursts and MaxNumbers at once, the oldest reused) driven by one per-frame update, so fast tapping stays cheap.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Audio = require(ReplicatedStorage.Audio)
local AudioConfig = require(ReplicatedStorage.AudioConfig)
local EconomyRules = require(ReplicatedStorage.EconomyRules)
local EffectsConfig = require(ReplicatedStorage.EffectsConfig)
local IceLooks = require(ReplicatedStorage.IceLooks)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local SoundRules = require(ReplicatedStorage.SoundRules)
local UIKit = require(ReplicatedStorage.UIKit)
local UITheme = require(ReplicatedStorage.UITheme)
local ClientState = require(script.Parent.ClientState)
local Effects = require(script.Parent.Effects)
local IceBlocks = require(script.Parent.IceBlocks)

local TapFeedback = {}

local player = Players.LocalPlayer
local SETTINGS = EffectsConfig.ClickBurst
local WHITE = Color3.new(1, 1, 1)
local gui

-- (IgnoreGuiInset off: the same coordinates as an InputObject's Position and Camera:WorldToScreenPoint)
local function screen()
	if gui and gui.Parent then
		return gui
	end
	gui = Instance.new("ScreenGui")
	gui.Name = "TapFeedback"
	gui.IgnoreGuiInset = false
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 3
	gui.Parent = player:WaitForChild("PlayerGui")
	return gui
end

-- The crystals one tap earns: the server's figure (TapValue), or this client's estimate until it arrives.
function TapFeedback.TapValue(): number
	local value = player:GetAttribute("TapValue")
	if type(value) == "number" and value == value then
		return value
	end
	local data = ClientState.Data()
	if not data then
		return 1
	end
	local ok, estimate = pcall(function()
		return EconomyRules.TapDamage(data) * EconomyRules.Multiplier(data)
	end)
	return if ok then estimate else 1
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

-- The click burst and the "+N" ---------------------------------------------------------------------

local bursts, numbers = {}, {} -- pools: { frame, parts..., startedAt (nil = free) }
local nextBurst, nextNumber = 1, 1

local function lerp(a: number, b: number, t: number): number
	return a + (b - a) * t
end

local function newBurst()
	local frame = Instance.new("Frame")
	frame.Name = "Burst"
	frame.BackgroundTransparency = 1
	frame.Size = UDim2.fromOffset(0, 0)
	frame.Visible = false
	frame.Parent = screen()
	local flash = Instance.new("Frame")
	flash.Name = "Flash"
	flash.AnchorPoint = Vector2.new(0.5, 0.5)
	flash.BackgroundColor3 = WHITE
	flash.BorderSizePixel = 0
	flash.Parent = frame
	UIKit.Corner(flash, 999)
	local streaks = {}
	for i = 1, SETTINGS.Streaks do
		local streak = Instance.new("Frame")
		streak.Name = "Streak" .. i
		streak.AnchorPoint = Vector2.new(0.5, 0.5)
		streak.BackgroundColor3 = WHITE
		streak.BorderSizePixel = 0
		streak.Parent = frame
		UIKit.Corner(streak, 3)
		table.insert(streaks, { frame = streak, angle = 0 })
	end
	return { frame = frame, flash = flash, streaks = streaks, startedAt = nil, plain = false }
end

local function newNumber()
	local label = UIKit.Label(screen(), "TapNumber", "", SETTINGS.NumberHeight, WHITE)
	label.AnchorPoint = Vector2.new(0.5, 0.5)
	label.Size = UDim2.fromOffset(220, SETTINGS.NumberHeight + 8)
	label.TextXAlignment = Enum.TextXAlignment.Center
	label.TextTruncate = Enum.TextTruncate.None
	label.Visible = false
	label.ZIndex = 2
	local scale = Instance.new("UIScale")
	scale.Parent = label
	return { label = label, scale = scale, outline = label.Outline, startedAt = nil, at = Vector2.zero, tilt = 0 }
end

local function showBurst(at: Vector2, plain: boolean)
	if #bursts < SETTINGS.MaxBursts then
		table.insert(bursts, newBurst())
	end
	local burst = bursts[nextBurst] or bursts[1]
	nextBurst = (nextBurst % SETTINGS.MaxBursts) + 1
	burst.frame.Position = UDim2.fromOffset(at.X, at.Y)
	burst.frame.Visible = true
	burst.plain = plain
	local turn = math.random() * 360
	for i, streak in burst.streaks do
		streak.angle = math.rad(turn + (i - 1) * 360 / #burst.streaks + (math.random() - 0.5) * 24)
		streak.frame.Visible = not plain
	end
	burst.startedAt = os.clock()
end

local function showNumber(at: Vector2, text: string)
	if #numbers < SETTINGS.MaxNumbers then
		table.insert(numbers, newNumber())
	end
	local number = numbers[nextNumber] or numbers[1]
	nextNumber = (nextNumber % SETTINGS.MaxNumbers) + 1
	local angle = math.random() * math.pi * 2
	local distance = lerp(SETTINGS.NumberDistance[1], SETTINGS.NumberDistance[2], math.random())
	number.at = at + Vector2.new(math.cos(angle), math.sin(angle)) * distance * UIKit.HudScale()
	number.tilt = (if math.random() < 0.5 then -1 else 1) * SETTINGS.Wobble
	number.label.Text = text
	number.label.TextSize = math.floor(SETTINGS.NumberHeight * UIKit.HudScale())
	number.label.Visible = true
	number.startedAt = os.clock()
end

local function update()
	local now = os.clock()
	local hud = UIKit.HudScale()
	for _, burst in bursts do
		if burst.startedAt then
			local t = (now - burst.startedAt) / SETTINGS.BurstSeconds
			if t >= 1 then
				burst.startedAt = nil
				burst.frame.Visible = false
			else
				local ease = 1 - (1 - t) ^ 3
				local size = lerp(SETTINGS.FlashSize[1], SETTINGS.FlashSize[2], ease) * hud
				burst.flash.Size = UDim2.fromOffset(size, size)
				burst.flash.BackgroundTransparency = lerp(0.05, 1, t)
				if not burst.plain then
					local reach = lerp(SETTINGS.StreakReach[1], SETTINGS.StreakReach[2], ease) * hud
					local length = lerp(SETTINGS.StreakLength[1], SETTINGS.StreakLength[2], t) * hud
					for _, streak in burst.streaks do
						local direction = Vector2.new(math.cos(streak.angle), math.sin(streak.angle))
						streak.frame.Position = UDim2.fromOffset(direction.X * reach, direction.Y * reach)
						streak.frame.Size = UDim2.fromOffset(length, math.max(2, 3 * hud))
						streak.frame.Rotation = math.deg(streak.angle)
						streak.frame.BackgroundTransparency = lerp(0, 1, t ^ 1.5)
					end
				end
			end
		end
	end
	for _, number in numbers do
		if number.startedAt then
			local seconds = now - number.startedAt
			local t = seconds / SETTINGS.NumberSeconds
			if t >= 1 then
				number.startedAt = nil
				number.label.Visible = false
			else
				-- pop: up past full size, then settle back; a rotate wobble that dies away
				local scale
				if seconds < 0.08 then
					scale = lerp(0.4, SETTINGS.PopScale, seconds / 0.08)
				elseif seconds < 0.22 then
					local s = (seconds - 0.08) / 0.14
					scale = lerp(SETTINGS.PopScale, 1, 1 - (1 - s) ^ 2)
				else
					scale = 1
				end
				number.scale.Scale = scale
				number.label.Rotation = number.tilt * math.exp(-seconds * 7) * math.cos(seconds * 38)
				local rise = SETTINGS.NumberRise * hud * (1 - (1 - t) ^ 2)
				number.label.Position = UDim2.fromOffset(number.at.X, number.at.Y - rise)
				local fade = math.clamp((t - 0.5) / 0.5, 0, 1)
				number.label.TextTransparency = fade
				number.outline.Transparency = fade
			end
		end
	end
end
RunService.RenderStepped:Connect(update)

-- Where a gamepad tap shows: the ice block on screen (or the screen's centre).
local function blockOnScreen(index: number?): Vector2
	local camera = workspace.CurrentCamera
	local view = index and IceBlocks.View(index)
	if view and view.block then
		local point, visible = camera:WorldToScreenPoint(view.block.Position)
		if visible then
			return Vector2.new(point.X, point.Y)
		end
	end
	return camera.ViewportSize / 2
end

-- A number floating up from where you tapped (the Golden Glacier's taps).
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
-- Your tap on your own block. screenPosition: where you clicked or touched (nil: a gamepad button).
function TapFeedback.Tap(screenPosition: Vector2?)
	local index = player:GetAttribute("PlotIndex")
	local view = type(index) == "number" and IceBlocks.View(index) or nil
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
	-- the burst and "+N" (only while there is a block to earn from: none while the next one slides in)
	if view and view.present then
		local at = screenPosition or blockOnScreen(index)
		showBurst(at, Effects.Reduced())
		showNumber(at, "+" .. NumberFormat.Short(math.max(1, TapFeedback.TapValue())))
	end
end

function TapFeedback.Streak(): number
	return streak
end

-- os.clock() of your last tap (the building chip and the income tick stay quiet just after one).
function TapFeedback.LastTapAt(): number
	return lastTapAt
end

return TapFeedback
