--[[
UIKit: the game's one UI kit, in the roblox-ui-style "showcase" look recoloured for the ice (UITheme).
Every HUD piece and window is built from it, so they all match. Client only.

Building blocks   Corner, Stroke, Rim, Gradient, Checker, Label, Card, Scroll, ProgressBar, TextBox
Buttons           Button / SetButton (the studded button), CloseButton, HudButton (big square with an
                  icon and a label), Tabs
Screens           Screen(name, order) -> gui, root. The root is the usable screen (below Roblox's top
                  bar). OnScreenChanged(callback) runs on every resize. MenuScale / HudScale: the
                  responsive rule, from the screen size.
Windows           Window(name, title, options): the modal window. One open at a time; while any is
                  open, world proximity prompts are hidden and the world is softly blurred; closing
                  the last one always restores both. The game starts with prompts on.

Sounds            PlaySound(name): a UI sound from AudioConfig. Silent until the game adds its sounds.

Gamepad           Every button, tab, slider and list is selectable, with a gold rim when selected
                  (SelectionRim) and the hover lift. A window selects its first control when it opens
                  with a gamepad (options.firstSelection() picks another, options.manualSelection
                  leaves it to the window), keeps the selection inside itself, and B closes it. A
                  selected slider moves with the D-pad (left / right). UsingGamepad() says whether
                  the player's last input was a gamepad.

Studio test switch: the Workspace attribute StudioScreenSize (a Vector2, for example 844, 390) lays
the whole UI out as if the screen were that size, in its top-left corner, with a red edge, for
phone-size screenshots. StudioGamepad = true makes UsingGamepad() answer yes (gamepad tests from MCP).
Both are set on the CLIENT, ignored outside Studio, and must be removed before saving the place.

Never run this module (or a window script) in Edit mode: it switches ProximityPromptService off while
a window is open, and that switch is saved with the place.
]]
local GuiService = game:GetService("GuiService")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TextService = game:GetService("TextService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Audio = require(ReplicatedStorage.Audio)
local UITheme = require(ReplicatedStorage.UITheme)

local UIKit = {}
UIKit.Theme = UITheme
UIKit.Colors = UITheme.Colors
UIKit.Font = UITheme.Font

local WHITE = Color3.new(1, 1, 1)
local Sizes = UITheme.Sizes

-- Was the player's last input a gamepad's? (Studio: the Workspace attribute StudioGamepad = true
-- pretends so, for tests that send gamepad buttons from MCP: those arrive as keyboard input.)
function UIKit.UsingGamepad(): boolean
	if RunService:IsStudio() and Workspace:GetAttribute("StudioGamepad") == true then
		return true
	end
	return UserInputService:GetLastInputType().Name:sub(1, 7) == "Gamepad"
end

-- The gamepad selection's look: a thick gold rim a little outside the selected control (Roblox
-- draws a copy of this over whatever is selected).
local selectionRim = Instance.new("Frame")
selectionRim.Name = "SelectionRim"
selectionRim.BackgroundTransparency = 1
selectionRim.Position, selectionRim.Size = UDim2.fromOffset(-6, -6), UDim2.new(1, 12, 1, 12)
do
	local stroke = Instance.new("UIStroke")
	stroke.Color, stroke.Thickness = UITheme.Colors.Selected, 5
	stroke.Parent = selectionRim
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, 12)
	corner.Parent = selectionRim
end
UIKit.SelectionRim = selectionRim

-- Gives any control the gold selection rim and makes it selectable.
function UIKit.MarkSelectable(object: GuiObject)
	object.Selectable = true
	object.SelectionImageObject = selectionRim
end

-- Building blocks ---------------------------------------------------------------------------------

function UIKit.Corner(parent: Instance, radius: number): UICorner
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, radius)
	corner.Parent = parent
	return corner
end

-- An outline on the object's border (not around its text).
function UIKit.Stroke(parent: Instance, color: Color3?, thickness: number?, transparency: number?): UIStroke
	local stroke = Instance.new("UIStroke")
	stroke.Color = color or UITheme.Colors.Outline
	stroke.Thickness = thickness or Sizes.Outline
	stroke.Transparency = transparency or 0
	stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	stroke.Parent = parent
	return stroke
end

-- The soft white rim inside windows, cards and buttons that makes them look raised.
function UIKit.Rim(parent: Instance, inset: number, color: Color3?, thickness: number?, transparency: number?, radius: number?): Frame
	local rim = Instance.new("Frame")
	rim.Name = "Rim"
	rim.AnchorPoint, rim.Position = Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.5)
	rim.Size = UDim2.new(1, -inset, 1, -inset)
	rim.BackgroundTransparency, rim.BorderSizePixel = 1, 0
	if radius then
		UIKit.Corner(rim, radius)
	end
	UIKit.Stroke(rim, color or WHITE, thickness or 2, transparency or 0.6)
	rim.Parent = parent
	return rim
end

-- A vertical gradient. The object needs a white background for the colours to show.
function UIKit.Gradient(parent: Instance, top: Color3, bottom: Color3): UIGradient
	local gradient = Instance.new("UIGradient")
	gradient.Rotation, gradient.Color = 90, ColorSequence.new(top, bottom)
	gradient.Parent = parent
	return gradient
end

-- The faint tiled checker (windows) or stud pattern (buttons).
function UIKit.Checker(parent: Instance, color: Color3, tile: number, fade: NumberSequence?): ImageLabel
	local image = Instance.new("ImageLabel")
	image.Name, image.BackgroundTransparency = "Checker", 1
	image.Size, image.Image = UDim2.fromScale(1, 1), UITheme.Assets.Checker
	image.ScaleType, image.TileSize = Enum.ScaleType.Tile, UDim2.fromOffset(tile, tile)
	image.ImageColor3 = color
	image.ZIndex = parent:IsA("GuiObject") and parent.ZIndex or 1
	local gradient = Instance.new("UIGradient")
	gradient.Rotation = 90
	gradient.Transparency = fade or NumberSequence.new(0.9, 0.8)
	gradient.Parent = image
	image.Parent = parent
	return image
end

-- A label in the house style: the rounded font, a heavy outline in proportion to its size, a fixed
-- TextSize in menu units (windows scale everything with a UIScale). wrap = true wraps long lines.
function UIKit.Label(parent: Instance, name: string, text: string, size: number, color: Color3?, wrap: boolean?): TextLabel
	local label = Instance.new("TextLabel")
	label.Name, label.Text, label.Font = name, text, UITheme.Font
	label.TextSize, label.TextColor3 = size, color or UITheme.Colors.Text
	label.BackgroundTransparency = 1
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.TextWrapped = wrap == true
	label.TextTruncate = if wrap then Enum.TextTruncate.None else Enum.TextTruncate.AtEnd
	local outline = Instance.new("UIStroke")
	outline.Name = "Outline"
	outline.Color = UITheme.Colors.Outline
	outline.Thickness = math.clamp(size / 9, 2, 6)
	outline.Parent = label
	label.Parent = parent
	return label
end

-- Keeps a label on ONE line at the largest TextSize (up to maxSize) that fits its width and height
-- (in offsets). TextScaled wraps or clips several words on a narrow phone; this measures instead.
function UIKit.FitOneLine(label: TextLabel, maxSize: number, maxOutline: number?)
	label.TextWrapped = false
	local function fit()
		local width, height = label.Size.X.Offset, label.Size.Y.Offset
		if width <= 0 then
			return
		end
		local natural = TextService:GetTextSize(label.Text, 100, label.Font, Vector2.new(1e6, 1e6)).X / 100
		local largest = math.max(10, math.min(maxSize, height * 0.95))
		label.TextSize = if natural > 0 then math.clamp(math.floor(width * 0.9 / natural), 10, largest) else largest
		local outline = label:FindFirstChild("Outline")
		if outline then
			outline.Thickness = math.clamp(label.TextSize / 9, 2, maxOutline or 6)
		end
	end
	label:GetPropertyChangedSignal("Text"):Connect(fit)
	label:GetPropertyChangedSignal("Size"):Connect(fit)
	fit()
end

-- A dark recessed card (rows and tiles on a window), with the outline and a soft rim.
function UIKit.Card(parent: Instance, name: string): Frame
	local card = Instance.new("Frame")
	card.Name = name
	card.BackgroundColor3 = UITheme.Colors.Card
	card.BorderSizePixel = 0
	UIKit.Corner(card, Sizes.CardCorner)
	UIKit.Stroke(card, nil, Sizes.ThinOutline)
	UIKit.Rim(card, 6, UITheme.Colors.CardRim, 2, 0.4, 9)
	card.Parent = parent
	return card
end

-- A scrolling list or grid on the window's dark well. kind: "List" (rows) or "Grid" (tiles).
-- Returns the ScrollingFrame and its layout. Its top padding leaves room for anything poking up.
function UIKit.Scroll(parent: Instance, name: string, kind: string?): (ScrollingFrame, UIListLayout | UIGridLayout)
	local scroll = Instance.new("ScrollingFrame")
	scroll.Name = name
	scroll.BackgroundColor3 = UITheme.Colors.Well
	scroll.BackgroundTransparency = 0.25
	scroll.BorderSizePixel = 0
	scroll.ScrollBarThickness = 8
	scroll.ScrollBarImageColor3 = UITheme.Colors.Muted
	scroll.AutomaticCanvasSize = Enum.AutomaticSize.Y
	scroll.CanvasSize = UDim2.new()
	scroll.ScrollingDirection = Enum.ScrollingDirection.Y
	UIKit.Corner(scroll, Sizes.CardCorner)
	UIKit.Stroke(scroll, nil, Sizes.ThinOutline)
	local layout: any
	if kind == "Grid" then
		layout = Instance.new("UIGridLayout")
		layout.CellPadding = UDim2.fromOffset(Sizes.Gap, Sizes.Gap)
		layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	else
		layout = Instance.new("UIListLayout")
		layout.Padding = UDim.new(0, 8)
	end
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = scroll
	-- A gamepad can select the list itself and scroll it with the right thumbstick (a list of
	-- pictures with no buttons is then still reachable).
	UIKit.MarkSelectable(scroll)
	local padding = Instance.new("UIPadding")
	padding.PaddingTop, padding.PaddingBottom = UDim.new(0, 10), UDim.new(0, 10)
	padding.PaddingLeft, padding.PaddingRight = UDim.new(0, 10), UDim.new(0, 16)
	padding.Parent = scroll
	scroll.Parent = parent
	return scroll, layout
end

-- An orange-to-gold bar in a recessed trough. Returns the trough and set(share 0-1, text).
function UIKit.ProgressBar(parent: Instance, name: string): (Frame, (number, string?) -> ())
	local trough = Instance.new("Frame")
	trough.Name, trough.BorderSizePixel = name, 0
	trough.BackgroundColor3, trough.ClipsDescendants = UITheme.Progress.trough, true
	UIKit.Corner(trough, 10)
	UIKit.Stroke(trough, nil, Sizes.ThinOutline)
	local fill = Instance.new("Frame")
	fill.Name, fill.BorderSizePixel, fill.BackgroundColor3 = "Fill", 0, WHITE
	fill.Size = UDim2.fromScale(0, 1)
	UIKit.Corner(fill, 10)
	UIKit.Gradient(fill, UITheme.Progress.top, UITheme.Progress.bottom)
	local bevel = Instance.new("Frame")
	bevel.Name, bevel.BorderSizePixel, bevel.BackgroundColor3 = "Bevel", 0, UITheme.Progress.bevel
	bevel.Size, bevel.Position = UDim2.new(1, 0, 0, 3), UDim2.new(0, 0, 1, -3)
	bevel.Parent = fill
	fill.Parent = trough
	local text = UIKit.Label(trough, "Label", "", 20)
	text.Size, text.ZIndex, text.TextXAlignment = UDim2.fromScale(1, 1), 3, Enum.TextXAlignment.Center
	trough.Parent = parent
	return trough, function(share: number, caption: string?)
		local amount = math.clamp(share, 0, 1)
		fill.Size = UDim2.fromScale(amount, 1)
		fill.Visible = amount > 0
		text.Text = caption or string.format("%d%%", math.floor(amount * 100))
	end
end

-- A slider in the progress bar's look: the orange-to-gold fill in a recessed trough, with a round
-- knob. Drag it (mouse or touch) or tap anywhere along it. onChange(value 0..1) runs while it moves;
-- onRelease(value) once it is let go. Returns the trough and set(value) (no callbacks).
function UIKit.Slider(parent: Instance, name: string, onChange: (number) -> (), onRelease: (number) -> ()): (Frame, (number) -> ())
	local trough, setBar = UIKit.ProgressBar(parent, name)
	trough.ClipsDescendants = false
	trough.Active = true
	local knob = Instance.new("Frame")
	knob.Name = "Knob"
	knob.AnchorPoint = Vector2.new(0.5, 0.5)
	knob.Size = UDim2.new(0, 34, 0, 34)
	knob.BackgroundColor3 = WHITE
	knob.ZIndex = 4
	knob.Parent = trough
	UIKit.Corner(knob, 17)
	UIKit.Stroke(knob, nil, Sizes.ThinOutline)
	UIKit.Gradient(knob, WHITE, UITheme.Colors.Muted)

	local value = 0
	local function show(newValue: number)
		value = math.clamp(newValue, 0, 1)
		setBar(value, "") -- (the caller shows the number: the knob would cover a centred one)
		knob.Position = UDim2.new(value, 0, 0.5, 0)
	end
	local dragging: InputObject? = nil
	local function valueAt(x: number): number
		local left, width = trough.AbsolutePosition.X, trough.AbsoluteSize.X
		return if width > 0 then (x - left) / width else value
	end
	local function isPress(input: InputObject): boolean
		return input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch
	end
	trough.InputBegan:Connect(function(input)
		if isPress(input) and not dragging then
			dragging = input
			show(valueAt(input.Position.X))
			onChange(value)
		end
	end)
	UserInputService.InputChanged:Connect(function(input)
		if not dragging then
			return
		end
		local moving = (dragging.UserInputType == Enum.UserInputType.MouseButton1 and input.UserInputType == Enum.UserInputType.MouseMovement)
			or input == dragging
		if moving then
			show(valueAt(input.Position.X))
			onChange(value)
		end
	end)
	UserInputService.InputEnded:Connect(function(input)
		if dragging and (input == dragging or (dragging.UserInputType == Enum.UserInputType.MouseButton1 and input.UserInputType == Enum.UserInputType.MouseButton1)) then
			dragging = nil
			onRelease(value)
		end
	end)
	-- Gamepad: select the slider, then D-pad left / right moves it a tenth at a time (sideways the
	-- selection stays on it); it saves a moment after the last press.
	UIKit.MarkSelectable(trough)
	trough:SetAttribute("Slider", true)
	trough.NextSelectionLeft, trough.NextSelectionRight = trough, trough
	local stepVersion = 0
	UserInputService.InputBegan:Connect(function(input)
		if GuiService.SelectedObject ~= trough then
			return
		end
		local step = if input.KeyCode == Enum.KeyCode.DPadRight then 0.1 elseif input.KeyCode == Enum.KeyCode.DPadLeft then -0.1 else 0
		if step == 0 then
			return
		end
		show(math.floor((value + step) * 10 + 0.5) / 10)
		onChange(value)
		stepVersion += 1
		local version = stepVersion
		task.delay(0.6, function()
			if version == stepVersion then
				onRelease(value)
			end
		end)
	end)
	return trough, show
end

-- A dark text field with the outline.
function UIKit.TextBox(parent: Instance, name: string, placeholder: string): TextBox
	local box = Instance.new("TextBox")
	box.Name = name
	box.BackgroundColor3 = UITheme.Colors.Field
	box.BorderSizePixel = 0
	box.Font = UITheme.Font
	box.TextSize = 30
	box.TextColor3 = UITheme.Colors.Text
	box.PlaceholderText = placeholder
	box.PlaceholderColor3 = UITheme.Colors.Placeholder
	box.Text = ""
	box.ClearTextOnFocus = false
	box.TextXAlignment = Enum.TextXAlignment.Center
	UIKit.Corner(box, 10)
	UIKit.Stroke(box, nil, Sizes.ThinOutline)
	local padding = Instance.new("UIPadding")
	padding.PaddingLeft, padding.PaddingRight = UDim.new(0, 12), UDim.new(0, 12)
	padding.Parent = box
	box.Parent = parent
	return box
end

-- The image id of an icon from the game's set (UITheme.Icons), or nil while it has no picture.
function UIKit.IconImage(key: string): string?
	local image = UITheme.Icons[key]
	return if type(image) == "string" and image ~= "" then image else nil
end

-- An icon from the game's set (UITheme.Icons: "Shop", "Codes"...), as an image fitted into the
-- label's box. A key with no image is shown as text (an emoji or a short word), sized `size`; the set
-- is empty until the game's icons are uploaded. The caller sets the size.
function UIKit.Icon(parent: Instance, name: string, key: string, size: number): GuiObject
	local image = UITheme.Icons[key]
	if image then
		local icon = Instance.new("ImageLabel")
		icon.Name = name
		icon.BackgroundTransparency = 1
		icon.Image = image
		icon.ScaleType = Enum.ScaleType.Fit
		icon.Size = UDim2.fromOffset(size * 1.3, size * 1.3)
		icon.Parent = parent
		return icon
	end
	local icon = Instance.new("TextLabel")
	icon.Name = name
	icon.BackgroundTransparency = 1
	icon.Text = key
	icon.TextSize = size
	icon.Font = Enum.Font.BuilderSans
	icon.TextColor3 = WHITE
	icon.Parent = parent
	return icon
end

-- Sounds ----------------------------------------------------------------------------------------

-- A UI sound or sound effect by name (AudioConfig.Ui / .Sfx), at the player's SFX volume. A name
-- with no entry plays nothing.
function UIKit.PlaySound(name: string)
	Audio.Play(name)
end

-- Buttons ---------------------------------------------------------------------------------------

-- Hover and press motion: the button itself never changes size (a steady click area); only the
-- UIScale inside its centred Visual moves. A press on an inactive button plays a soft "locked" thunk.
local function pressable(button: GuiButton, scale: UIScale)
	local hovered, tween = false, nil
	local function to(value: number, seconds: number, style: Enum.EasingStyle?)
		if tween then
			tween:Cancel()
		end
		tween = TweenService:Create(scale, TweenInfo.new(seconds, style or Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Scale = value })
		tween:Play()
	end
	local function resting(): number
		-- Touch taps fire MouseEnter too and never MouseLeave, so touch never "hovers".
		local hovering = hovered and UserInputService:GetLastInputType() ~= Enum.UserInputType.Touch
		return if hovering and button.Active then UITheme.Motion.Hover else 1
	end
	button.MouseEnter:Connect(function()
		hovered = true
		to(resting(), UITheme.Motion.HoverTime)
	end)
	button.MouseLeave:Connect(function()
		hovered = false
		to(resting(), UITheme.Motion.HoverTime)
	end)
	button.MouseButton1Down:Connect(function()
		if not button.Active then
			UIKit.PlaySound("Locked")
			return
		end
		UIKit.PlaySound("Click")
		to(UITheme.Motion.Press, UITheme.Motion.PressTime)
	end)
	button.MouseButton1Up:Connect(function()
		to(resting(), UITheme.Motion.ReleaseTime, Enum.EasingStyle.Back)
	end)
	-- Gamepad: the selected button lifts like a hovered one, inside the gold rim.
	button.SelectionGained:Connect(function()
		to(UITheme.Motion.Hover, UITheme.Motion.HoverTime)
	end)
	button.SelectionLost:Connect(function()
		to(resting(), UITheme.Motion.HoverTime)
	end)
	button.SelectionImageObject = selectionRim
end

local function visualFor(button: GuiButton): (Frame, UIScale)
	local visual = Instance.new("Frame")
	visual.Name, visual.AnchorPoint, visual.Position = "Visual", Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.5)
	visual.Size, visual.BorderSizePixel, visual.BackgroundColor3 = UDim2.fromScale(1, 1), 0, WHITE
	visual.ZIndex = button.ZIndex
	visual.Parent = button
	local scale = Instance.new("UIScale")
	scale.Name = "PressScale"
	scale.Parent = visual
	return visual, scale
end

-- The studded button: an invisible TextButton (the steady click area) holding a centred Visual: a
-- gradient face in the kind's colours (UITheme.Buttons), a faint stud pattern, a darker bottom edge,
-- a white inner rim, the thick outline and a big outlined caption. captionSize: menu units (28).
function UIKit.Button(parent: Instance, name: string, text: string, kind: string?, captionSize: number?): TextButton
	local button = Instance.new("TextButton")
	button.Name, button.Text, button.AutoButtonColor, button.BackgroundTransparency = name, "", false, 1
	button.Parent = parent
	local visual, scale = visualFor(button)
	UIKit.Corner(visual, Sizes.ButtonCorner)
	UIKit.Stroke(visual, nil, Sizes.Outline)
	UIKit.Gradient(visual, WHITE, WHITE).Name = "Face"
	local studs = UIKit.Checker(visual, WHITE, 22, NumberSequence.new(0.88, 0.92))
	studs.Name = "Studs"
	UIKit.Corner(studs, Sizes.ButtonCorner)
	local edge = Instance.new("Frame") -- the darker bottom edge that makes it look pressable
	edge.Name, edge.BorderSizePixel = "Edge", 0
	edge.Size, edge.Position = UDim2.new(1, 0, 0, 6), UDim2.new(0, 0, 1, -6)
	edge.BackgroundColor3, edge.BackgroundTransparency = Color3.new(0, 0, 0), 0.72
	edge.Parent = visual
	UIKit.Corner(edge, Sizes.ButtonCorner)
	UIKit.Rim(visual, 6, WHITE, 2, 0.55, 5)
	local caption = UIKit.Label(visual, "Caption", text, captionSize or 28)
	caption.Size, caption.Position = UDim2.new(1, -12, 1, -6), UDim2.fromOffset(6, 0)
	caption.TextXAlignment = Enum.TextXAlignment.Center
	caption.TextTruncate = Enum.TextTruncate.None
	caption.TextScaled = true
	local limit = Instance.new("UITextSizeConstraint")
	limit.MinTextSize, limit.MaxTextSize = 10, captionSize or 28
	limit.Parent = caption
	caption.Outline.Color = UITheme.Colors.CaptionOutline
	pressable(button, scale)
	UIKit.SetButton(button, text, kind or "Neutral", true)
	return button
end

-- Changes a button's caption, kind and whether it acts. enabled = false keeps the look; a press only
-- plays the "locked" thunk. Leave any argument nil to keep it.
function UIKit.SetButton(button: TextButton, text: string?, kind: string?, enabled: boolean?)
	local visual = button:FindFirstChild("Visual")
	if not visual then
		return
	end
	if kind then
		local colors = UITheme.Buttons[kind] or UITheme.Buttons.Done
		button:SetAttribute("Kind", kind)
		visual.Face.Color = ColorSequence.new(colors[1], colors[2])
	end
	if text then
		visual.Caption.Text = text
	end
	if enabled ~= nil then
		button.Active = enabled
		-- (it stays selectable: a gamepad selection on it isn't lost when it greys out, and pressing
		-- it plays the "locked" thunk like a click)
	end
end

-- The red close button with a white outlined X (AnchorPoint at its centre, so it can sit on a corner).
function UIKit.CloseButton(parent: Instance): TextButton
	local button = Instance.new("TextButton")
	button.Name, button.Text, button.AutoButtonColor, button.BackgroundTransparency = "Close", "", false, 1
	button.AnchorPoint, button.ZIndex = Vector2.new(0.5, 0.5), 20
	button.Size = UDim2.fromOffset(Sizes.CloseSize, Sizes.CloseSize)
	local visual, scale = visualFor(button)
	UIKit.Corner(visual, 12)
	UIKit.Stroke(visual, nil, Sizes.Outline)
	UIKit.Gradient(visual, UITheme.Buttons.Close[1], UITheme.Buttons.Close[2])
	UIKit.Rim(visual, 8, WHITE, 2, 0.5, 8).ZIndex = 21
	local x = UIKit.Label(visual, "X", "X", 42)
	x.Size, x.Position, x.ZIndex, x.TextXAlignment = UDim2.fromScale(1, 1), UDim2.fromOffset(0, -2), 22, Enum.TextXAlignment.Center
	pressable(button, scale)
	button.Parent = parent
	return button
end

-- A big square HUD button: an icon (UITheme.Icons key) over a short label (SHOP, CODES...).
function UIKit.HudButton(parent: Instance, name: string, iconKey: string, text: string, kind: string): TextButton
	local button = UIKit.Button(parent, name, "", kind)
	local visual = button.Visual
	local icon = UIKit.Icon(visual, "Icon", iconKey, 46)
	icon.AnchorPoint, icon.Position, icon.Size = Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.4), UDim2.fromScale(1, 0.6)
	icon.ZIndex = visual.ZIndex + 2
	local label = UIKit.Label(visual, "Label", text, 20)
	label.AnchorPoint, label.Position, label.Size = Vector2.new(0.5, 1), UDim2.new(0.5, 0, 1, -7), UDim2.new(1, -6, 0, 22)
	label.TextXAlignment = Enum.TextXAlignment.Center
	label.TextTruncate = Enum.TextTruncate.None
	label.Outline.Color = UITheme.Colors.CaptionOutline
	label.ZIndex = visual.ZIndex + 2
	return button
end

-- A row of tabs (a horizontal scroller when they don't fit). tabs: { { Id, Name } }.
-- onSelect(id) runs when one is picked. Returns { frame, buttons, Select(id), selected }.
function UIKit.Tabs(parent: Instance, tabs, onSelect: (string) -> (), tabWidth: number?)
	local strip = Instance.new("ScrollingFrame")
	strip.Name = "Tabs"
	strip.BackgroundTransparency = 1
	strip.BorderSizePixel = 0
	strip.ScrollBarThickness = 4
	strip.ScrollingDirection = Enum.ScrollingDirection.X
	strip.Selectable = false -- (a gamepad selects the tabs, not the strip)
	strip.AutomaticCanvasSize = Enum.AutomaticSize.X
	strip.CanvasSize = UDim2.new()
	strip.Parent = parent
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Horizontal
	layout.Padding = UDim.new(0, 8)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.VerticalAlignment = Enum.VerticalAlignment.Center
	layout.Parent = strip
	local padding = Instance.new("UIPadding")
	padding.PaddingLeft, padding.PaddingRight = UDim.new(0, 4), UDim.new(0, 4)
	padding.Parent = strip
	local controller = { frame = strip, buttons = {}, selected = nil }
	function controller.Select(id: string)
		controller.selected = id
		for tabId, button in controller.buttons do
			UIKit.SetButton(button, nil, if tabId == id then "Neutral" else "Done")
		end
	end
	for order, tab in tabs do
		local button = UIKit.Button(strip, tab.Id .. "Tab", tab.Name, "Done", 24)
		button.LayoutOrder = order
		button.Size = UDim2.new(0, tab.Width or tabWidth or 130, 1, -8)
		button.Activated:Connect(function()
			controller.Select(tab.Id)
			onSelect(tab.Id)
		end)
		controller.buttons[tab.Id] = button
	end
	return controller
end

-- Screens ---------------------------------------------------------------------------------------

local screenChanged = Instance.new("BindableEvent")

-- The full screen size (the camera's viewport), or Studio's pretend size (StudioScreenSize).
function UIKit.Viewport(): Vector2
	if RunService:IsStudio() then
		local pretend = Workspace:GetAttribute("StudioScreenSize")
		if typeof(pretend) == "Vector2" and pretend.X > 100 and pretend.Y > 100 then
			return pretend
		end
	end
	local camera = Workspace.CurrentCamera
	return camera and camera.ViewportSize or Vector2.new(1050, 620)
end

-- The part of the screen a ScreenGui gets: the viewport below Roblox's top bar.
function UIKit.ScreenSize(): Vector2
	local inset = GuiService:GetGuiInset()
	local viewport = UIKit.Viewport()
	return Vector2.new(viewport.X, math.max(100, viewport.Y - inset.Y))
end

function UIKit.IsPretendScreen(): boolean
	return RunService:IsStudio() and typeof(Workspace:GetAttribute("StudioScreenSize")) == "Vector2"
end

-- The menu scale: min(screen / baseline) clamped, times the menu factor, never below the floor.
function UIKit.MenuScale(): number
	local s = UITheme.Scale
	local viewport = UIKit.Viewport()
	local fit = math.clamp(math.min(viewport.X / s.Baseline.X, viewport.Y / s.Baseline.Y), s.Min, s.Max)
	return math.max(s.MenuFloor, fit * s.Menu)
end

-- The HUD's scale: a bit smaller than menus.
function UIKit.HudScale(): number
	return UIKit.MenuScale() * UITheme.Scale.Hud
end

-- Is this a small screen (a phone): the short side under 500 px?
function UIKit.IsSmallScreen(): boolean
	local viewport = UIKit.Viewport()
	return math.min(viewport.X, viewport.Y) < 500
end

-- callback() runs whenever the screen size (or the Studio pretend size) changes.
function UIKit.OnScreenChanged(callback: () -> ()): RBXScriptConnection
	return screenChanged.Event:Connect(callback)
end

local function watchScreen()
	local function fire()
		screenChanged:Fire()
	end
	local function watchCamera(camera: Camera?)
		if camera then
			camera:GetPropertyChangedSignal("ViewportSize"):Connect(fire)
		end
	end
	watchCamera(Workspace.CurrentCamera)
	Workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(function()
		watchCamera(Workspace.CurrentCamera)
		fire()
	end)
	Workspace:GetAttributeChangedSignal("StudioScreenSize"):Connect(fire)
end
if RunService:IsClient() then
	watchScreen()
end

-- A ScreenGui and its root frame: the usable screen (or the Studio pretend screen, top left).
-- Put everything inside root. Returns gui, root.
function UIKit.Screen(name: string, displayOrder: number): (ScreenGui, Frame)
	local gui = Instance.new("ScreenGui")
	gui.Name = name
	gui.DisplayOrder = displayOrder
	gui.ResetOnSpawn = false
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui:SetAttribute("UIKitScreen", true) -- (the game's own screens: the tutorial's spotlight locks only these)
	local root = Instance.new("Frame")
	root.Name = "Root"
	root.BackgroundTransparency = 1
	root.Parent = gui
	local edge -- the red outline of a pretend screen (Studio only)
	local function size()
		if UIKit.IsPretendScreen() then
			root.Size = UDim2.fromOffset(UIKit.ScreenSize().X, UIKit.ScreenSize().Y)
			if not edge then
				edge = Instance.new("Frame")
				edge.Name = "StudioScreenEdge"
				edge.BackgroundTransparency = 1
				edge.Size = UDim2.fromScale(1, 1)
				edge.ZIndex = 100
				UIKit.Stroke(edge, Color3.fromRGB(255, 40, 40), 2)
				edge.Parent = root
			end
		else
			root.Size = UDim2.fromScale(1, 1)
			if edge then
				edge:Destroy()
				edge = nil
			end
		end
	end
	size()
	UIKit.OnScreenChanged(size)
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	return gui, root
end

-- Windows ---------------------------------------------------------------------------------------
-- One open at a time. While any is open: world prompts hidden (a prompt's on-screen button would
-- catch clicks meant for the window), the world softly blurred. Closing the last one restores both.

local openWindows = {} -- [window] = true
local allWindows = {} -- [window] = true
local blur: BlurEffect? = nil

local function updateWorld()
	local anyOpen = next(openWindows) ~= nil
	ProximityPromptService.Enabled = not anyOpen
	if anyOpen and not blur then
		blur = Instance.new("BlurEffect")
		blur.Name = "UIBlur"
		blur.Parent = Lighting
	end
	if blur then
		blur.Size = UITheme.Blur.Menu
		blur.Enabled = anyOpen
	end
end

-- Is any window open right now?
function UIKit.AnyWindowOpen(): boolean
	return next(openWindows) ~= nil
end

-- Closes every open window (a cutscene, a respawn...).
function UIKit.CloseAll()
	for window in table.clone(openWindows) do
		window.Close()
	end
end

-- The modal window: a scrim, then a centred panel (scaled to the screen) holding the glacier-blue
-- gradient box, the big outlined title riding over its top edge (with an emoji icon beside it), the
-- red close button on its top-right corner, and `content`: the area inside the box where the window
-- puts its own things, in menu units.
-- options: width, height (largest size, menu units), theme (a UITheme.Windows key), icon (an icon key,
--   beside the title), onLayout(width, height) after every resize with the content's size, onOpen(),
--   onClose(). Bigger looks (ShowcaseKit.Window sets these): titleSize, titleRise, titleOutline,
--   closeSize, cornerIcon (an image id: a big picture over the window's top-left corner) and
--   cornerIconSize.
-- Returns window: { gui, root, panel, box, content, title, Open(), Close(), Toggle(), IsOpen() }.
function UIKit.Window(name: string, titleText: string, options)
	options = options or {}
	local theme = UITheme.Windows[options.theme or "Ice"] or UITheme.Windows.Ice
	local rise = options.titleRise or Sizes.TitleRise
	local titleSize = options.titleSize or 64
	local closeSize = options.closeSize or Sizes.CloseSize
	local cornerSize = options.cornerIconSize or 140
	local gui, root = UIKit.Screen(name, options.displayOrder or 20)
	gui.Enabled = false

	local scrim = Instance.new("TextButton") -- swallows clicks behind the window
	scrim.Name = "Scrim"
	scrim.Text = ""
	scrim.AutoButtonColor = false
	scrim.Size = UDim2.fromScale(1, 1)
	scrim.BackgroundColor3 = UITheme.Colors.Scrim
	scrim.BackgroundTransparency = 0.55
	scrim.BorderSizePixel = 0
	scrim.Selectable = false
	scrim:SetAttribute("NoHover", true) -- a click catcher, not a button (HoverClick.client)
	scrim.Parent = root

	local panel = Instance.new("Frame")
	panel.Name = "Panel"
	panel.AnchorPoint, panel.Position = Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.5)
	panel.BackgroundTransparency = 1
	panel.Parent = root
	-- Gamepad selection stays inside the window while it is open.
	panel.SelectionGroup = true
	panel.SelectionBehaviorUp = Enum.SelectionBehavior.Stop
	panel.SelectionBehaviorDown = Enum.SelectionBehavior.Stop
	panel.SelectionBehaviorLeft = Enum.SelectionBehavior.Stop
	panel.SelectionBehaviorRight = Enum.SelectionBehavior.Stop
	local scale = Instance.new("UIScale")
	scale.Name = "WindowScale"
	scale.Parent = panel

	local box = Instance.new("Frame")
	box.Name = "Box"
	box.Position = UDim2.fromOffset(0, rise)
	box.Size = UDim2.new(1, 0, 1, -rise)
	box.BackgroundColor3 = WHITE
	box.BackgroundTransparency = theme.transparency or UITheme.WindowTransparency
	box.BorderSizePixel = 0
	box.Parent = panel
	UIKit.Corner(box, Sizes.WindowCorner)
	UIKit.Stroke(box, nil, theme.outline or Sizes.Outline)
	UIKit.Gradient(box, theme.top, theme.bottom)
	local checker = UIKit.Checker(box, theme.checker, 30)
	UIKit.Corner(checker, Sizes.WindowCorner)
	UIKit.Rim(box, 8, WHITE, 2, 0.65, 12)

	-- The title rides centred over the box's top edge: white fading to the theme's title colour,
	-- a heavy outline and a soft drop shadow, one line (fitted).
	local title = UIKit.Label(panel, "Title", titleText, titleSize)
	title.AnchorPoint, title.ZIndex, title.TextXAlignment = Vector2.new(0.5, 0.5), 6, Enum.TextXAlignment.Center
	title.TextTruncate = Enum.TextTruncate.None
	UIKit.Gradient(title, WHITE, theme.title)
	local shadow = UIKit.Label(panel, "TitleShadow", titleText, titleSize, UITheme.Colors.Outline)
	shadow.AnchorPoint, shadow.ZIndex, shadow.TextTransparency = Vector2.new(0.5, 0.5), 5, 0.45
	shadow.TextXAlignment = Enum.TextXAlignment.Center
	shadow.TextTruncate = Enum.TextTruncate.None
	shadow.Outline.Transparency = 0.45
	title:GetPropertyChangedSignal("Text"):Connect(function()
		shadow.Text = title.Text
	end)
	title:GetPropertyChangedSignal("TextSize"):Connect(function()
		shadow.TextSize = title.TextSize
		shadow.Outline.Thickness = title.Outline.Thickness
	end)
	local icon = if options.icon and not options.cornerIcon then UIKit.Icon(panel, "TitleIcon", options.icon, 52) else nil
	if icon then
		icon.AnchorPoint, icon.ZIndex, icon.Rotation = Vector2.new(1, 0.5), 7, -10
		icon.Size = UDim2.fromOffset(64, 64)
	end
	-- A big picture over the box's top-left corner, tilted (the showcase look).
	local corner = nil
	if options.cornerIcon then
		corner = Instance.new("ImageLabel")
		corner.Name = "CornerIcon"
		corner.BackgroundTransparency = 1
		corner.Image = options.cornerIcon
		corner.ScaleType = Enum.ScaleType.Fit
		corner.AnchorPoint = Vector2.new(0.5, 0.5)
		corner.Size = UDim2.fromOffset(cornerSize, cornerSize)
		corner.Rotation = -8
		corner.ZIndex = 7
		corner.Parent = panel
	end

	local closeButton = UIKit.CloseButton(panel)
	closeButton.ZIndex = 20
	closeButton.Size = UDim2.fromOffset(closeSize, closeSize)
	closeButton.Visual.X.TextSize = math.floor(closeSize * 0.72)

	local content = Instance.new("Frame")
	content.Name = "Content"
	content.BackgroundTransparency = 1
	content.Parent = box

	local window = { gui = gui, root = root, panel = panel, box = box, content = content, title = title }
	local isOpen, version = false, 0
	local returnTo: GuiObject? = nil -- what was selected before the window opened (a HUD button)

	-- Gamepad: options.firstSelection(), else the window's top-left control, else the close button.
	local function isShown(item: GuiObject): boolean
		local node: Instance? = item
		while node and node ~= content do
			if node:IsA("GuiObject") and not node.Visible then
				return false
			end
			node = node.Parent
		end
		return item.AbsoluteSize.X > 0
	end
	local function selectFirst()
		if not isOpen or not UIKit.UsingGamepad() then
			return
		end
		local chosen = options.firstSelection and options.firstSelection()
		if not chosen then
			for _, item in content:GetDescendants() do
				if item:IsA("GuiObject") and item.Selectable and (item:IsA("GuiButton") or item:IsA("TextBox") or item:GetAttribute("Slider"))
					and isShown(item) then
					local at, best = item.AbsolutePosition, chosen and chosen.AbsolutePosition
					if not best or at.Y < best.Y - 4 or (math.abs(at.Y - best.Y) <= 4 and at.X < best.X) then
						chosen = item
					end
				end
			end
		end
		GuiService.SelectedObject = chosen or closeButton
	end
	window.SelectFirst = selectFirst

	local function layout()
		local menuScale = UIKit.MenuScale()
		local screen = root.AbsoluteSize
		if screen.X < 10 then
			screen = UIKit.ScreenSize()
		end
		local width = math.min(options.width or 760, math.max(260, (screen.X - 16) / menuScale))
		local height = math.min(options.height or 560, math.max(240, (screen.Y - 10) / menuScale))
		panel.Size = UDim2.fromOffset(width, height)
		if isOpen then
			scale.Scale = menuScale
		end
		window.scale = menuScale
		title.Position = UDim2.fromOffset(width / 2, rise + 2)
		local sides = if corner then 2 * math.max(cornerSize * 0.75, closeSize) else 190
		title.Size = UDim2.fromOffset(math.max(140, width - sides), titleSize * 1.12)
		if corner then
			-- mostly inside the window, so it stays on a phone screen
			corner.Position = UDim2.fromOffset(cornerSize * 0.42, rise - 18)
		end
		shadow.Position, shadow.Size = title.Position + UDim2.fromOffset(0, 5), title.Size
		if icon then
			local textWidth = math.min(TextService:GetTextSize(title.Text, title.TextSize, title.Font, Vector2.new(1e6, 1e6)).X, title.Size.X.Offset)
			icon.Position = UDim2.fromOffset(width / 2 - textWidth / 2 - 6, rise - 2)
		end
		closeButton.Position = UDim2.new(1, -math.floor(closeSize * 0.4), 0, rise + 4)
		local pad = Sizes.Pad + 4
		local top = math.max(36, math.floor(titleSize * 0.55)) -- below the title's lower half
		content.Position = UDim2.fromOffset(pad, top)
		content.Size = UDim2.new(1, -pad * 2, 1, -top - pad)
		if options.onLayout then
			options.onLayout(width - pad * 2, height - rise - top - pad)
		end
	end
	UIKit.FitOneLine(title, titleSize, options.titleOutline)
	-- Laid out on Open and on every resize while open (never before the window script has built its
	-- content, and a closed window needs no layout).
	title:GetPropertyChangedSignal("TextSize"):Connect(function()
		if icon and isOpen then
			layout()
		end
	end)
	UIKit.OnScreenChanged(function()
		if isOpen then
			task.defer(layout)
		end
	end)
	root:GetPropertyChangedSignal("AbsoluteSize"):Connect(function()
		if isOpen then
			layout()
		end
	end)

	function window.IsOpen(): boolean
		return isOpen
	end

	function window.Open()
		if isOpen then
			return
		end
		for other in table.clone(openWindows) do
			other.Close()
		end
		isOpen = true
		version += 1
		openWindows[window] = true
		updateWorld()
		layout()
		gui.Enabled = true
		local selected = GuiService.SelectedObject
		returnTo = if selected and not selected:IsDescendantOf(gui) then selected else nil
		if not options.manualSelection then
			task.defer(selectFirst)
		end
		UIKit.PlaySound("Open")
		local target = window.scale
		scale.Scale = target * 0.88
		TweenService:Create(scale, TweenInfo.new(UITheme.Motion.OpenTime, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = target }):Play()
		if options.onOpen then
			options.onOpen()
		end
	end

	function window.Close()
		if not isOpen then
			return
		end
		isOpen = false
		version += 1
		local myVersion = version
		openWindows[window] = nil
		updateWorld() -- prompts come back straight away
		local selected = GuiService.SelectedObject
		if selected and selected:IsDescendantOf(gui) then
			-- Back to the HUD button that opened it while a gamepad is in use; otherwise nothing.
			local back = returnTo
			GuiService.SelectedObject = if back and back.Parent and back.Visible and UIKit.UsingGamepad() then back else nil
		end
		returnTo = nil
		UIKit.PlaySound("Close")
		local shrink = TweenService:Create(scale, TweenInfo.new(UITheme.Motion.CloseTime, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Scale = window.scale * 0.9 })
		shrink:Play()
		task.delay(UITheme.Motion.CloseTime, function()
			if myVersion == version and not isOpen then
				gui.Enabled = false
			end
		end)
		if options.onClose then
			options.onClose()
		end
	end

	function window.Toggle()
		if isOpen then
			window.Close()
		else
			window.Open()
		end
	end

	-- Re-run the layout (after the window changed what it shows).
	window.Layout = layout

	closeButton.Activated:Connect(window.Close)
	-- A tap outside the window closes it. Frames inside the window don't catch taps, so a tap on the
	-- window's own background reaches the scrim too: that one is ignored.
	scrim.Activated:Connect(function(input)
		local at = input and input.Position
		if at then
			local corner, size = box.AbsolutePosition, box.AbsoluteSize
			-- (whether the position counts the top bar differs by input; inside either way counts)
			local inset = GuiService:GetGuiInset().Y
			for _, y in { at.Y, at.Y - inset } do
				if at.X >= corner.X and at.X <= corner.X + size.X and y >= corner.Y and y <= corner.Y + size.Y then
					return
				end
			end
		end
		window.Close()
	end)
	allWindows[window] = true
	return window
end

if RunService:IsClient() then
	-- Gamepad: B closes the open window (it may arrive marked as processed: B also clears the selection).
	UserInputService.InputBegan:Connect(function(input)
		if input.KeyCode == Enum.KeyCode.ButtonB and next(openWindows) then
			UIKit.CloseAll()
		end
	end)
	-- Windows rebuild their rows and cards when something changes (a purchase, a new target), which
	-- destroys a selected button: select its rebuilt copy (the same path), or the first control.
	local lastSelectedPath: { string }? = nil
	local function findByPath(path: { string }): Instance?
		local node: Instance? = game
		for _, name in path do
			node = node and node:FindFirstChild(name)
		end
		return node
	end
	GuiService:GetPropertyChangedSignal("SelectedObject"):Connect(function()
		local selected = GuiService.SelectedObject
		if selected then
			local path, node = {}, selected
			while node and node ~= game do
				table.insert(path, 1, node.Name)
				node = node.Parent
			end
			lastSelectedPath = path
			return
		end
		local path = lastSelectedPath
		if not path or not next(openWindows) or not UIKit.UsingGamepad() then
			return
		end
		task.delay(0.05, function()
			if GuiService.SelectedObject or not next(openWindows) then
				return
			end
			local again = findByPath(path)
			if again and again:IsA("GuiObject") and again.Selectable and again.Visible then
				GuiService.SelectedObject = again
			else
				for window in openWindows do
					window.SelectFirst()
				end
			end
		end)
	end)
	-- Picking up a gamepad while a window is open selects its first control.
	UserInputService.LastInputTypeChanged:Connect(function()
		if UIKit.UsingGamepad() and not GuiService.SelectedObject then
			for window in openWindows do
				window.SelectFirst()
			end
		end
	end)
end

-- The HUD's menu button with this name (Shop, Codes), once the HUD has built it. Windows connect to
-- it to open themselves. (Yields until the button exists: a window whose button the HUD never builds
-- waits for good, so add the button to HUD.client's MENU first.)
function UIKit.MenuButton(name: string): GuiButton
	local hud = Players.LocalPlayer:WaitForChild("PlayerGui"):WaitForChild("HUD")
	local button = hud:FindFirstChild(name .. "Button", true)
	while not button do
		hud.DescendantAdded:Wait()
		button = hud:FindFirstChild(name .. "Button", true)
	end
	return button :: GuiButton
end

-- The game starts with world prompts on: the switch is a property of the place, so a place saved
-- while it was off (this module once run in Edit mode by a test) would otherwise hide every prompt.
if RunService:IsClient() then
	ProximityPromptService.Enabled = true
end

return UIKit
