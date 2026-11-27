--[[
Spotlight (client): the tutorial's highlight. The whole screen, HUD and windows included, goes dark (black at
UITheme.Spotlight.Darkness) except a cut-out with slightly rounded corners and a soft pulsing glow round what the
player should click; the step's short instruction sits next to it, inside the screen. It fades in and out
(FadeSeconds) when the target or step changes.
  Spotlight.Show(target, text)  target: a GuiObject (a menu button, a card, a buy button), a BasePart in the world
                                (its box is followed on screen as the camera moves), or nil (no cut-out: the dark
                                layer goes and only the instruction shows, at the top).
  Spotlight.Hide()              nothing shown.
  Spotlight.AllowsTap(point)    false while a world target is lit and `point` (a click or touch, GUI coordinates)
                                is outside its cut-out (TapInput: only the lit block can be tapped).
Only the lit thing can be clicked: while a cut-out shows, every other button on the game's own screens (UIKit.Screen)
is made non-interactable (Interactable off; put back when the spotlight moves or goes). Roblox's touch controls
(the jump button) and the F2 debug and F3 admin windows are never touched.
The dark layer itself takes no input, so walking, jumping, the thumbstick and turning the camera all still work.
With a gamepad the lit button is selected.
]]
local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TextService = game:GetService("TextService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local UIKit = require(ReplicatedStorage.UIKit)
local UITheme = require(ReplicatedStorage.UITheme)

local Spotlight = {}

local LOOK = UITheme.Spotlight
local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")

local gui, root = UIKit.Screen("Tutorial", LOOK.DisplayOrder)
gui:SetAttribute("Spotlight", true)

local hole = Instance.new("Frame") -- the cut-out: its huge stroke is the dark layer round it
hole.Name = "Hole"
hole.BackgroundTransparency = 1
hole.Visible = false
hole.Parent = root
UIKit.Corner(hole, LOOK.Corner)
local dark = Instance.new("UIStroke")
dark.Name = "Dark"
dark.Color = Color3.new(0, 0, 0)
dark.Thickness = 4000 -- (reaches past any screen edge)
dark.Transparency = 1
dark.Parent = hole

local function glowRing(name: string, grow: number, thickness: number): UIStroke
	local ring = Instance.new("Frame")
	ring.Name = name
	ring.BackgroundTransparency = 1
	ring.Position = UDim2.fromOffset(-grow, -grow)
	ring.Size = UDim2.new(1, grow * 2, 1, grow * 2)
	ring.Parent = hole
	UIKit.Corner(ring, LOOK.Corner + grow)
	local stroke = Instance.new("UIStroke")
	stroke.Color = LOOK.Glow
	stroke.Thickness = thickness
	stroke.Transparency = 1
	stroke.Parent = ring
	return stroke
end
local glowInner = glowRing("Glow", 2, 3)
local glowOuter = glowRing("GlowSoft", 6, 7)

-- the instruction: outlined words on a soft dark rounded backing sized to them, so they read over anything
local backing = Instance.new("Frame")
backing.Name = "Bubble"
backing.BackgroundColor3 = Color3.new(0, 0, 0)
backing.BackgroundTransparency = 1
backing.BorderSizePixel = 0
backing.ZIndex = 3
backing.Parent = root
UIKit.Corner(backing, 12)
local PAD = Vector2.new(14, 7)
local bubble = UIKit.Label(backing, "Text", "", LOOK.TextSize, LOOK.TextColor, true)
bubble.Position = UDim2.fromOffset(PAD.X, PAD.Y)
bubble.Size = UDim2.new(1, -PAD.X * 2, 1, -PAD.Y * 2)
bubble.TextXAlignment = Enum.TextXAlignment.Center
bubble.TextYAlignment = Enum.TextYAlignment.Center
bubble.TextTransparency = 1
bubble.Outline.Transparency = 1
bubble.ZIndex = 4

local target: Instance? = nil
local text = ""
local shown = 0 -- 0..1: the fade
local fadeTween: Tween? = nil
local fade = Instance.new("NumberValue")
local holeRect: Rect? = nil -- the cut-out on screen (GUI coordinates) while a target is lit and visible
local disabled = {} -- [button] = true: buttons we made non-interactable
local locked = false -- whether the other buttons are locked now
local selectedFor: Instance? = nil

local function fadeTo(value: number)
	if fadeTween then
		fadeTween:Cancel()
	end
	fadeTween = TweenService:Create(fade, TweenInfo.new(LOOK.FadeSeconds, Enum.EasingStyle.Quad), { Value = value })
	fadeTween:Play()
end

-- Buttons ----------------------------------------------------------------------------------------------------

-- Only the game's own screens (UIKit.Screen marks them) are locked: never Roblox's touch controls (the jump
-- button), the F2/F3 tool windows or the spotlight itself.
local function ownGuiSkipped(screenGui: ScreenGui?): boolean
	return not screenGui or screenGui:GetAttribute("UIKitScreen") ~= true or screenGui:GetAttribute("Spotlight") == true
end

local function shouldDisable(button: Instance): boolean
	if not button:IsA("GuiButton") then
		return false
	end
	if target and target:IsA("GuiObject") and (button == target or button:IsDescendantOf(target) or target:IsDescendantOf(button)) then
		return false
	end
	return not ownGuiSkipped(button:FindFirstAncestorWhichIsA("ScreenGui"))
end

local function restoreAll()
	for button in disabled do
		if button.Parent then
			button.Interactable = true
		end
	end
	table.clear(disabled)
end

local function disableOthers()
	for button in disabled do
		if not shouldDisable(button) and button.Parent then
			button.Interactable = true
			disabled[button] = nil
		end
	end
	for _, item in playerGui:GetDescendants() do
		if not disabled[item] and shouldDisable(item) and item.Interactable then
			item.Interactable = false
			disabled[item] = true
		end
	end
end

playerGui.DescendantAdded:Connect(function(item)
	if locked and target and not disabled[item] and shouldDisable(item) and item.Interactable then
		item.Interactable = false
		disabled[item] = true
	end
end)

-- Where things are -------------------------------------------------------------------------------------------

local function shownOnScreen(object: GuiObject): boolean
	local node: Instance? = object
	while node and not node:IsA("ScreenGui") do
		if node:IsA("GuiObject") and not node.Visible then
			return false
		end
		node = node.Parent
	end
	return node ~= nil and (node :: ScreenGui).Enabled and object.AbsoluteSize.X > 2
end

-- The target's box on screen, in this GUI's coordinates (nil: not on screen now).
local function targetRect(): Rect?
	if not target or not target.Parent then
		return nil
	end
	if target:IsA("GuiObject") then
		if not shownOnScreen(target) then
			return nil
		end
		local at, size = target.AbsolutePosition - root.AbsolutePosition, target.AbsoluteSize
		return Rect.new(at.X - LOOK.Padding, at.Y - LOOK.Padding, at.X + size.X + LOOK.Padding, at.Y + size.Y + LOOK.Padding)
	elseif target:IsA("BasePart") then
		local camera = Workspace.CurrentCamera
		local cf, half = target.CFrame, target.Size / 2
		local low, high = Vector2.new(math.huge, math.huge), Vector2.new(-math.huge, -math.huge)
		for _, x in { -1, 1 } do
			for _, y in { -1, 1 } do
				for _, z in { -1, 1 } do
					local point, inFront = camera:WorldToScreenPoint(cf:PointToWorldSpace(half * Vector3.new(x, y, z)))
					if point.Z <= 0 then
						return nil -- (behind the camera)
					end
					local p = Vector2.new(point.X, point.Y) - root.AbsolutePosition
					low, high = low:Min(p), high:Max(p)
				end
			end
		end
		local screen = UIKit.ScreenSize()
		if high.X < 0 or high.Y < 0 or low.X > screen.X or low.Y > screen.Y then
			return nil
		end
		local pad = LOOK.Padding * 1.5
		return Rect.new(low.X - pad, low.Y - pad, high.X + pad, high.Y + pad)
	end
	return nil
end

-- Puts the instruction next to the cut-out (beside it near a screen edge, else below or above: the first side it
-- fits), inside the screen. The text is measured only when it or the screen changes (resizing a label every frame
-- to measure it kept it from drawing).
local measured = { key = "", width = 0, height = 0, size = 0 }
local function placeBubble(rect: Rect?)
	local screen = UIKit.ScreenSize()
	local margin = 12
	local key = text .. "|" .. screen.X .. "|" .. UIKit.HudScale()
	if key ~= measured.key then
		local width = math.min(LOOK.TextWidth, screen.X - margin * 2)
		local textSize = math.max(18, math.floor(LOOK.TextSize * math.min(1, UIKit.HudScale() * 1.1)))
		local bounds = TextService:GetTextSize(text, textSize, bubble.Font, Vector2.new(width - PAD.X * 2, 1e4))
		measured = { key = key, width = math.min(width, bounds.X + PAD.X * 2 + 6), height = math.min(bounds.Y + PAD.Y * 2 + 4, screen.Y / 2), size = textSize }
		bubble.TextSize = textSize
		bubble.Outline.Thickness = math.clamp(textSize / 9, 2, 4)
		backing.Size = UDim2.fromOffset(measured.width, measured.height)
	end
	local width, height = measured.width, measured.height
	if not rect then
		backing.Position = UDim2.fromOffset((screen.X - width) / 2, screen.Y * 0.22)
		return
	end
	local gap = 16
	local centreX = (rect.Min.X + rect.Max.X) / 2 - width / 2
	local centreY = (rect.Min.Y + rect.Max.Y) / 2 - height / 2
	local x, y
	local middle = (rect.Min.X + rect.Max.X) / 2
	if middle < screen.X * 0.18 and rect.Max.X + gap + width <= screen.X - margin then
		x, y = rect.Max.X + gap, centreY -- (near the left edge, like the HUD's menu: beside it, into the screen)
	elseif middle > screen.X * 0.82 and rect.Min.X - gap - width >= margin then
		x, y = rect.Min.X - gap - width, centreY
	elseif rect.Max.Y + gap + height <= screen.Y - margin then
		x, y = centreX, rect.Max.Y + gap
	elseif rect.Min.Y - gap - height >= margin then
		x, y = centreX, rect.Min.Y - gap - height
	elseif rect.Max.X + gap + width <= screen.X - margin then
		x, y = rect.Max.X + gap, centreY
	else
		x, y = rect.Min.X - gap - width, centreY
	end
	x = math.clamp(x, margin, math.max(margin, screen.X - margin - width))
	y = math.clamp(y, margin, math.max(margin, screen.Y - margin - height))
	backing.Position = UDim2.fromOffset(x, y)
end

RunService.RenderStepped:Connect(function()
	local rect = targetRect()
	holeRect = rect
	-- the other buttons are locked only while a cut-out is actually showing (nothing lit: nothing locked)
	if rect and target and not locked then
		locked = true
		disableOthers()
	elseif not rect and locked then
		locked = false
		restoreAll()
	end
	local f = fade.Value
	if rect then
		hole.Visible = true
		hole.Position = UDim2.fromOffset(rect.Min.X, rect.Min.Y)
		hole.Size = UDim2.fromOffset(rect.Width, rect.Height)
	else
		hole.Visible = false
	end
	dark.Transparency = 1 - LOOK.Darkness * f
	local pulse = 0.5 + 0.5 * math.sin(os.clock() * LOOK.PulseSpeed)
	glowInner.Transparency = 1 - f * (0.95 - 0.45 * pulse)
	glowOuter.Transparency = 1 - f * (0.45 - 0.3 * pulse)
	backing.Visible = text ~= "" and f > 0.01
	if bubble.Text ~= text then
		bubble.Text = text
	end
	bubble.TextTransparency = 1 - f
	bubble.Outline.Transparency = 1 - f
	backing.BackgroundTransparency = 1 - LOOK.TextBacking * f
	if backing.Visible then
		placeBubble(rect)
	end
	-- a gamepad selects the lit button (once per target, and again if the selection wanders off it)
	if target and target:IsA("GuiButton") and rect and UIKit.UsingGamepad() then
		if selectedFor ~= target or GuiService.SelectedObject == nil then
			selectedFor = target
			GuiService.SelectedObject = target
		end
	end
end)

-- API --------------------------------------------------------------------------------------------------------

local wanted: Instance? = nil
local wantedText = ""
local switching = false

-- Moves the spotlight to the wanted target: the old cut-out fades out first, then the new one fades in.
local function switchTo()
	if switching then
		return
	end
	switching = true
	if fade.Value > 0.02 and target ~= nil then
		fadeTo(0)
		task.wait(LOOK.FadeSeconds)
	end
	switching = false
	if wanted ~= target then
		target = wanted
		selectedFor = nil
		locked = false -- (the frame update locks the other buttons once the new cut-out is on screen)
		restoreAll()
	end
	text = wantedText
	fadeTo(if wantedText ~= "" or target then 1 else 0)
	if wanted ~= target then
		task.spawn(switchTo) -- (it changed again while fading)
	end
end

function Spotlight.Show(newTarget: Instance?, newText: string)
	wantedText = newText
	if newTarget ~= wanted or (wanted == nil and text == "" and newText ~= "") then
		wanted = newTarget
		task.spawn(switchTo)
	elseif not switching then
		text = newText
	end
end

function Spotlight.Hide()
	if wanted ~= nil or wantedText ~= "" then
		wanted, wantedText = nil, ""
		task.spawn(function()
			fadeTo(0)
			task.wait(LOOK.FadeSeconds)
			if wanted == nil then
				target = nil
				locked = false
				restoreAll()
				text = ""
			end
		end)
	end
end

function Spotlight.AllowsTap(point: Vector2?): boolean
	if not target or not target:IsA("BasePart") or not point then
		return true
	end
	local rect = holeRect
	if not rect then
		return true -- (the block isn't on screen: nothing is lit)
	end
	local p = point - root.AbsolutePosition
	return p.X >= rect.Min.X and p.X <= rect.Max.X and p.Y >= rect.Min.Y and p.Y <= rect.Max.Y
end

function Spotlight.Target(): Instance?
	return target
end

return Spotlight
