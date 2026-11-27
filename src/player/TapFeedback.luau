--[[
TapFeedback (client): what a tap on the ice shows at once (docs/GAME_DESIGN.md, "Every hit"):
 * in the world: the block shudders, and ice chips, crystal bits and your tool's sparks burst out of the spot you
   hit (where the click's ray meets the block, along the face's normal and towards the camera; EffectsConfig.TapChips,
   from a small pool of parts this script moves itself);
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
local SwingConfig = require(ReplicatedStorage.SwingConfig)
local UIKit = require(ReplicatedStorage.UIKit)
local UITheme = require(ReplicatedStorage.UITheme)
local UpgradeConfig = require(ReplicatedStorage.UpgradeConfig)
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

-- Your crystal and spark colours (ice upgrades, tool tier) and your tool family's impact (SwingConfig: a hammer's
-- chunkier burst, a sword's extra sparks).
local function colours(): (Color3, Color3, { Chips: number, ChipSize: number, Sparks: number })
	local data = ClientState.Data()
	if not data then
		return IceLooks.CrystalColour(0), IceLooks.ToolSparks[1], SwingConfig.Family("Pick").Impact
	end
	local tier = EconomyRules.ToolTier(data)
	local tool = UpgradeConfig.Tools[tier]
	return IceLooks.CrystalColour(EconomyRules.IceTiersTotal(data)), IceLooks.ToolSparks[tier] or IceLooks.ToolSparks[1],
		SwingConfig.Family(tool and tool.Family).Impact
end

-- Ice chips, crystal bits and pick sparks out of the spot you hit ---------------------------------------------

local CHIPS = EffectsConfig.TapChips
local pieces = {} -- the pool: { part, kind, position, velocity, spin, turn, born, life }
local nextPiece = 1
local PARKED = CFrame.new(0, -10000, 0)

local function newPiece()
	local part = Instance.new("Part")
	part.Name = "TapChip"
	part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch = true, false, false, false
	part.CastShadow = false
	part.CFrame = PARKED
	part.Parent = Effects.Folder()
	return { part = part, born = nil }
end

local function emit(kind: string, at: Vector3, velocity: Vector3, size: Vector3, color: Color3, material: Enum.Material)
	if #pieces < CHIPS.MaxParts then
		table.insert(pieces, newPiece())
	end
	local piece = pieces[nextPiece] or pieces[1]
	nextPiece = (nextPiece % CHIPS.MaxParts) + 1
	local part = piece.part
	if not part.Parent then
		part.Parent = Effects.Folder()
	end
	part.Size, part.Color, part.Material, part.Transparency = size, color, material, 0
	piece.kind, piece.position, piece.velocity = kind, at, velocity
	piece.turn = CFrame.Angles(math.random() * 6, math.random() * 6, math.random() * 6)
	piece.spin = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 14
	piece.born, piece.life = os.clock(), CHIPS.Life[kind] or 0.6
end

-- Moves every live piece (one BulkMoveTo a frame) and parks the finished ones.
local movedParts, movedFrames = {}, {}
RunService.RenderStepped:Connect(function(dt)
	table.clear(movedParts)
	table.clear(movedFrames)
	local now = os.clock()
	for _, piece in pieces do
		if piece.born then
			local age = now - piece.born
			local part = piece.part
			if age >= piece.life then
				piece.born = nil
				table.insert(movedParts, part)
				table.insert(movedFrames, PARKED)
			else
				local gravity = if piece.kind == "Spark" then CHIPS.Gravity * 0.25 else CHIPS.Gravity
				piece.velocity -= Vector3.new(0, gravity * dt, 0)
				piece.position += piece.velocity * dt
				local frame
				if piece.kind == "Spark" then
					local v = piece.velocity
					frame = CFrame.lookAt(piece.position, piece.position + (if v.Magnitude > 0.01 then v else Vector3.yAxis))
				else
					piece.turn *= CFrame.Angles(piece.spin.X * dt, piece.spin.Y * dt, piece.spin.Z * dt)
					frame = CFrame.new(piece.position) * piece.turn
				end
				local fadeFrom = piece.life * 0.6
				part.Transparency = if age > fadeFrom then (age - fadeFrom) / (piece.life - fadeFrom) else 0
				table.insert(movedParts, part)
				table.insert(movedFrames, frame)
			end
		end
	end
	if #movedParts > 0 then
		workspace:BulkMoveTo(movedParts, movedFrames, Enum.BulkMoveMode.FireCFrameChanged)
	end
end)

-- Where a tap strikes the block, and that face's outward normal. A click or touch: where its ray meets the block;
-- a miss (a counted tap anywhere in the plot): the nearest point on the face towards the camera. A gamepad (no
-- point): the middle of that face.
function TapFeedback.StrikePoint(block: BasePart, screenPosition: Vector2?): (Vector3, Vector3)
	local camera = workspace.CurrentCamera
	local cf, half = block.CFrame, block.Size / 2
	local eye = cf:PointToObjectSpace(camera.CFrame.Position)
	-- the face towards the camera: the axis the camera is furthest outside of (relative to the block's size)
	local axes = { Vector3.xAxis, Vector3.yAxis, Vector3.zAxis }
	local best, bestRatio = 1, -math.huge
	for i, axis in axes do
		local ratio = math.abs(eye:Dot(axis)) / math.max(half:Dot(axis), 0.01)
		if ratio > bestRatio then
			best, bestRatio = i, ratio
		end
	end
	local localNormal = axes[best] * (if eye:Dot(axes[best]) >= 0 then 1 else -1)
	local normal = cf:VectorToWorldSpace(localNormal)
	local centre = cf:PointToWorldSpace(localNormal * half)
	if not screenPosition then
		return centre, normal
	end
	local ray = camera:ScreenPointToRay(screenPosition.X, screenPosition.Y)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { block }
	local hit = workspace:Raycast(ray.Origin, ray.Direction * 1000, params)
	if hit then
		return hit.Position, hit.Normal
	end
	-- missed: where the ray crosses the face's plane, kept inside the face
	local facing = ray.Direction:Dot(normal)
	if facing >= -1e-3 then
		return centre, normal
	end
	local t = (centre - ray.Origin):Dot(normal) / facing
	local onPlane = cf:PointToObjectSpace(ray.Origin + ray.Direction * t)
	local inside = Vector3.new(
		if best == 1 then localNormal.X * half.X else math.clamp(onPlane.X, -half.X * 0.95, half.X * 0.95),
		if best == 2 then localNormal.Y * half.Y else math.clamp(onPlane.Y, -half.Y * 0.95, half.Y * 0.95),
		if best == 3 then localNormal.Z * half.Z else math.clamp(onPlane.Z, -half.Z * 0.95, half.Z * 0.95)
	)
	return cf:PointToWorldSpace(inside), normal
end

-- A small white glint where the pick strikes (one pooled emitter, moved to the point).
local glintEmitter
local function glint(at: Vector3)
	if not glintEmitter or not glintEmitter.Parent then
		local holder = Instance.new("Attachment")
		holder.Name = "TapGlint"
		holder.Parent = workspace.Terrain
		glintEmitter = Instance.new("ParticleEmitter")
		glintEmitter.Texture = EffectsConfig.Texture("Sparkle")
		glintEmitter.Rate = 0
		glintEmitter.Speed = NumberRange.new(0)
		glintEmitter.Lifetime = NumberRange.new(EffectsConfig.TapGlint.Life)
		glintEmitter.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, EffectsConfig.TapGlint.Size * 0.4),
			NumberSequenceKeypoint.new(0.3, EffectsConfig.TapGlint.Size), NumberSequenceKeypoint.new(1, 0) })
		glintEmitter.Rotation = NumberRange.new(0, 90)
		glintEmitter.LightEmission = 1
		glintEmitter.Brightness = 3
		glintEmitter.ZOffset = 1
		glintEmitter.Parent = holder
	end
	glintEmitter.Parent.WorldPosition = at
	glintEmitter:Emit(1)
end

-- Ice chips off the spot you hit, a little crystal spray and your pick's sparks (the doc's "Every hit").
local function chips(index: number, screenPosition: Vector2?)
	local view = IceBlocks.View(index)
	if not view or not view.present then
		return
	end
	local block = view.block
	local point, normal = TapFeedback.StrikePoint(block, screenPosition)
	local camera = workspace.CurrentCamera
	local toCamera = camera.CFrame.Position - point
	toCamera = if toCamera.Magnitude > 0 then toCamera.Unit else normal
	local out = (normal + toCamera * CHIPS.TowardCamera).Unit
	local at = point + normal * 0.15
	glint(at)
	local function direction(): Vector3
		local stray = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 2 * CHIPS.Spread
		return (out + stray + Vector3.new(0, 0.35, 0)).Unit
	end
	local function speed(): number
		return CHIPS.Speed[1] + math.random() * (CHIPS.Speed[2] - CHIPS.Speed[1])
	end
	local crystal, spark, impact = colours()
	for _ = 1, Effects.Count(math.round(CHIPS.Chips * impact.Chips)) do
		emit("Chip", at, direction() * speed(), Vector3.one * (0.25 + math.random() * 0.3) * impact.ChipSize, block.Color, Enum.Material.Ice)
	end
	for _ = 1, Effects.Count(CHIPS.Crystals) do
		emit("Crystal", at, direction() * speed() * 0.8 + Vector3.new(0, 6, 0), Vector3.one * 0.32, crystal, Enum.Material.Neon)
	end
	for _ = 1, Effects.Count(math.round(CHIPS.Sparks * impact.Sparks)) do
		emit("Spark", at, direction() * speed() * 1.4, Vector3.new(0.1, 0.1, 0.65), spark, Enum.Material.Neon)
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
		chips(index, screenPosition)
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
