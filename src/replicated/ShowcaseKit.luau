--[[
ShowcaseKit: the big, bright "showcase" pieces of the UI (the shop look), built on UIKit and its
tokens (UITheme: Windows.Showcase, Showcase, CardPalettes, ShopIcons, Sheets). Reuse these instead of
building raw Instances. Client only. Sizes in menu units.

  Window(name, title, options)  UIKit.Window in the showcase look: a deep ice-blue see-through panel
                                with a thick dark border, a very large white outlined title on its top
                                edge, a big picture over its top-left corner (options.cornerIcon, an
                                image id; none while the game has no pictures yet) and a big red close
                                button over its top-right corner. Other options as UIKit.Window.
  Panel(parent, name)           a dark rounded panel with the thick dark outline (pop-ups inside windows).
  SectionHeader(parent, text)   "~ Passes ~": big white outlined text, one line, fitted to its width.
  Card(parent, name, palette)   a colour card: a saturated gradient (a UITheme.CardPalettes key), a
                                faint frosty checker, a thick light border inside a dark outline.
                                Cards never clip, so a picture may poke out of them.
  SetCardPalette(card, palette) recolours a card (its state changed).
  CardPicture(card, image)      the card's big item picture (an image id, or nil: an empty picture
                                the caller can fill later); the caller places it.
  CardTitle(card, text, palette) the card's big outlined title (up to two lines, shrinks to fit).
  CardText(card, text)          a short outlined line of detail under the title.
  BuyButton(parent)             the chunky green buy button: the Robux icon and an outlined price.
                                Returns button, set(kind, text, showRobux).
  InfoButton(parent, kind?)     the "i INFO" pill (the odds of a paid random item; Roblox wants the word).
  Sticker(card, text, kind)     a tilted sticker on a card's top-right corner (OWNED, NO ID YET).
  SheetPicture(parent, group, id) a picture from a sheet (UITheme.Sheets.Groups[group]), or nil if no
                                sheet has a cell for it (all of them, until the game's sheets exist).
                                SetSilhouette(picture, on) tints it dark (an undiscovered item).
  HudButton(parent, name, image, text, palette)  the HUD's big square button: a colour card face, an
                                oversized picture poking out of its top and a big outlined label. With
                                no image (nil or ""), the label grows to fill the button instead.
                                button.Visual.Icon / .Label as UIKit.HudButton's.

Picture-first screens (the Rebirth and Welcome Back screens: big icons and numbers, few words):
  Picture(parent, name, key)    a picture from the icon set (UITheme.Icons[key]), fitted, centred (AnchorPoint 0.5);
                                hidden while the key has no id. SetPicture(picture, key) changes it.
  PopIn(object, delay?, from?)  pops an object in: it grows from `from` (0.3) with a little overshoot after `delay`
                                seconds (a UIScale "PopScale"; give the object AnchorPoint 0.5, 0.5).
  RobuxBadge(parent)            a small green price pill with the Robux icon. Returns the pill and set(price).
  Rainbow(button)               turns a UIKit.Button's face into a slowly shimmering rainbow (a premium offer).
  Tick(parent)                  the small green tick in a corner of a picture (UITheme.Icons.Tick).
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local UIKit = require(ReplicatedStorage.UIKit)
local UITheme = require(ReplicatedStorage.UITheme)

local ShowcaseKit = {}

local WHITE = Color3.new(1, 1, 1)
local Colors = UITheme.Colors
local Look = UITheme.Showcase

local function paletteFor(paletteName: string?)
	return UITheme.CardPalettes[paletteName or ""] or UITheme.CardPalettes.Blue
end

function ShowcaseKit.Window(name: string, title: string, options)
	options = table.clone(options or {})
	options.theme = options.theme or "Showcase"
	options.titleSize = options.titleSize or Look.TitleSize
	options.titleRise = options.titleRise or Look.TitleRise
	options.titleOutline = options.titleOutline or Look.TitleOutline
	options.closeSize = options.closeSize or Look.CloseSize
	options.cornerIconSize = options.cornerIconSize or Look.CornerIcon
	if options.cornerIcon == "" then
		options.cornerIcon = nil
	end
	return UIKit.Window(name, title, options)
end

function ShowcaseKit.Panel(parent: Instance, name: string): Frame
	local theme = UITheme.Windows.Showcase
	local panel = Instance.new("Frame")
	panel.Name = name
	panel.BackgroundColor3 = WHITE
	panel.BorderSizePixel = 0
	panel.Parent = parent
	UIKit.Corner(panel, UITheme.Sizes.WindowCorner)
	UIKit.Stroke(panel, nil, 5)
	UIKit.Gradient(panel, theme.top, theme.bottom)
	UIKit.Rim(panel, 8, WHITE, 2, 0.75, 12)
	return panel
end

function ShowcaseKit.SectionHeader(parent: Instance, text: string): TextLabel
	local label = UIKit.Label(parent, "Section", `~ {text} ~`, Look.SectionSize)
	label.TextXAlignment = Enum.TextXAlignment.Center
	label.TextTruncate = Enum.TextTruncate.None
	UIKit.FitOneLine(label, Look.SectionSize, 5)
	return label
end

function ShowcaseKit.Card(parent: Instance, name: string, paletteName: string): Frame
	local palette = paletteFor(paletteName)
	local card = Instance.new("Frame")
	card.Name = name
	card.BackgroundColor3 = WHITE
	card.BorderSizePixel = 0
	card.Parent = parent
	UIKit.Corner(card, 14)
	UIKit.Stroke(card, nil, 5) -- the dark outer outline
	UIKit.Gradient(card, palette.top, palette.bottom)
	-- a faint frosty checker over the face
	local frost = UIKit.Checker(card, WHITE, 40, NumberSequence.new(0.86, 0.94))
	frost.Name = "Frost"
	UIKit.Corner(frost, 14)
	-- the thick light border inside the outline
	local border = Instance.new("Frame")
	border.Name = "Border"
	border.BackgroundTransparency = 1
	border.AnchorPoint, border.Position = Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.5)
	border.Size = UDim2.new(1, -6, 1, -6)
	border.Parent = card
	UIKit.Corner(border, 11)
	UIKit.Stroke(border, palette.rim, 5)
	return card
end

-- Recolours a card (an item unlocked, owned...).
function ShowcaseKit.SetCardPalette(card: Frame, paletteName: string)
	local palette = paletteFor(paletteName)
	local gradient = card:FindFirstChildOfClass("UIGradient")
	if gradient then
		gradient.Color = ColorSequence.new(palette.top, palette.bottom)
	end
	local border = card:FindFirstChild("Border")
	local stroke = border and border:FindFirstChildOfClass("UIStroke")
	if stroke then
		stroke.Color = palette.rim
	end
end

function ShowcaseKit.CardPicture(card: Frame, image: string?): ImageLabel
	local picture = Instance.new("ImageLabel")
	picture.Name = "Picture"
	picture.BackgroundTransparency = 1
	picture.Image = image or ""
	picture.ScaleType = Enum.ScaleType.Fit
	picture.ZIndex = 4
	picture.Parent = card
	return picture
end

function ShowcaseKit.CardTitle(card: Frame, text: string, paletteName: string): TextLabel
	local palette = paletteFor(paletteName)
	local title = UIKit.Label(card, "CardTitle", text, Look.CardTitle, WHITE, true)
	title.TextScaled = true
	title.TextYAlignment = Enum.TextYAlignment.Center
	title.ZIndex = 5
	title.Outline.Thickness = 5
	local limit = Instance.new("UITextSizeConstraint")
	limit.MinTextSize, limit.MaxTextSize = 14, Look.CardTitle
	limit.Parent = title
	UIKit.Gradient(title, WHITE, palette.name)
	return title
end

function ShowcaseKit.CardText(card: Frame, text: string): TextLabel
	local label = UIKit.Label(card, "CardText", text, 18, WHITE, true)
	label.TextYAlignment = Enum.TextYAlignment.Top
	label.ZIndex = 5
	label.Outline.Thickness = 3
	return label
end

function ShowcaseKit.BuyButton(parent: Instance): (TextButton, (string, string, boolean?) -> ())
	local button = UIKit.Button(parent, "BuyButton", "", "Go", 32)
	local visual = button.Visual
	local row = Instance.new("Frame")
	row.Name = "Price"
	row.BackgroundTransparency = 1
	row.Size = UDim2.new(1, -12, 1, -6)
	row.Position = UDim2.fromOffset(6, 0)
	row.Parent = visual
	local rowLayout = Instance.new("UIListLayout")
	rowLayout.FillDirection = Enum.FillDirection.Horizontal
	rowLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	rowLayout.VerticalAlignment = Enum.VerticalAlignment.Center
	rowLayout.Padding = UDim.new(0, 8)
	rowLayout.SortOrder = Enum.SortOrder.LayoutOrder
	rowLayout.Parent = row
	-- the Robux icon: white over a slightly bigger dark copy (its outline)
	local iconHolder = Instance.new("Frame")
	iconHolder.Name = "RobuxIcon"
	iconHolder.BackgroundTransparency = 1
	iconHolder.Size = UDim2.fromOffset(34, 34)
	iconHolder.Parent = row
	local shadow = Instance.new("ImageLabel")
	shadow.Name = "Outline"
	shadow.BackgroundTransparency = 1
	shadow.Image = UITheme.Assets.Robux
	shadow.ImageColor3 = Colors.CaptionOutline
	shadow.ScaleType = Enum.ScaleType.Fit
	shadow.AnchorPoint, shadow.Position = Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.5)
	shadow.Size = UDim2.new(1, 6, 1, 6)
	shadow.Parent = iconHolder
	local icon = Instance.new("ImageLabel")
	icon.Name = "Robux"
	icon.BackgroundTransparency = 1
	icon.Image = UITheme.Assets.Robux
	icon.ImageColor3 = WHITE
	icon.ScaleType = Enum.ScaleType.Fit
	icon.Size = UDim2.fromScale(1, 1)
	icon.Parent = iconHolder
	local price = UIKit.Label(row, "Amount", "", 32)
	price.AutomaticSize = Enum.AutomaticSize.X
	price.Size = UDim2.fromOffset(0, 40)
	price.LayoutOrder = 2
	price.TextTruncate = Enum.TextTruncate.None
	price.Outline.Color = Colors.CaptionOutline
	price.Outline.Thickness = 4
	-- set(kind, text, showRobux)
	return button, function(kind: string, text: string, showRobux: boolean?)
		UIKit.SetButton(button, "", kind)
		iconHolder.Visible = showRobux == true
		price.Text = text
		price.TextSize = if #text > 7 then 24 else 32 -- (CAN'T GIFT, GIFT 2399)
	end
end

function ShowcaseKit.InfoButton(parent: Instance, kind: string?): TextButton
	local button = UIKit.Button(parent, "InfoButton", "INFO", kind or "Neutral", 24)
	button.Size = UDim2.fromOffset(108, 46)
	local visual = button.Visual
	local circle = Instance.new("Frame")
	circle.Name = "Circle"
	circle.AnchorPoint = Vector2.new(0, 0.5)
	circle.Position = UDim2.new(0, 9, 0.5, -2)
	circle.Size = UDim2.fromOffset(28, 28)
	circle.BackgroundColor3 = WHITE
	circle.Parent = visual
	UIKit.Corner(circle, 14)
	UIKit.Stroke(circle, nil, 3)
	local i = Instance.new("TextLabel")
	i.Name = "I"
	i.BackgroundTransparency = 1
	i.Size = UDim2.fromScale(1, 1)
	i.Text = "i"
	i.Font = UIKit.Font
	i.TextSize = 24
	i.TextColor3 = Colors.Outline
	i.Parent = circle
	local word = visual.Caption
	word.Position, word.Size = UDim2.fromOffset(40, 0), UDim2.new(1, -46, 1, -6)
	return button
end

function ShowcaseKit.Sticker(card: Frame, text: string, kind: string): Frame
	local colors = UITheme.Buttons[kind] or UITheme.Buttons.Done
	local tag = Instance.new("Frame")
	tag.Name = "Sticker"
	tag.AnchorPoint = Vector2.new(1, 0)
	tag.Position = UDim2.new(1, 8, 0, -10)
	tag.Size = UDim2.fromOffset(124, 32)
	tag.Rotation = 8
	tag.BackgroundColor3 = WHITE
	tag.ZIndex = 8
	tag.Parent = card
	UIKit.Corner(tag, 8)
	UIKit.Stroke(tag, nil, 3)
	UIKit.Gradient(tag, colors[1], colors[2])
	local label = UIKit.Label(tag, "Text", text, 19)
	label.Size, label.ZIndex, label.TextXAlignment = UDim2.fromScale(1, 1), 9, Enum.TextXAlignment.Center
	return tag
end

-- Pictures from the sheets -----------------------------------------------------------------------

local sheetCells = {} -- [group] = { [id] = { image, offset } }
for group, sheets in UITheme.Sheets.Groups do
	local cells = {}
	local size, perRow = UITheme.Sheets.Cell, UITheme.Sheets.PerRow
	for _, sheet in sheets do
		for index, id in sheet.Cells do
			local row, column = (index - 1) // perRow, (index - 1) % perRow
			cells[id] = { image = sheet.Image, offset = Vector2.new(column * size, row * size) }
		end
	end
	sheetCells[group] = cells
end

function ShowcaseKit.SheetPicture(parent: Instance, group: string, id: string): ImageLabel?
	local cell = sheetCells[group] and sheetCells[group][id]
	if not cell then
		return nil
	end
	local picture = Instance.new("ImageLabel")
	picture.Name = "Picture"
	picture.BackgroundTransparency = 1
	picture.Image = cell.image
	picture.ImageRectOffset = cell.offset
	picture.ImageRectSize = Vector2.new(UITheme.Sheets.Cell, UITheme.Sheets.Cell)
	picture.ScaleType = Enum.ScaleType.Fit
	picture.ZIndex = 4
	picture.Parent = parent
	return picture
end

-- An undiscovered item: the same picture, dark and a little see-through.
function ShowcaseKit.SetSilhouette(picture: ImageLabel, on: boolean, tint: Color3?)
	picture.ImageColor3 = if on then Colors.Silhouette else (tint or WHITE)
	picture.ImageTransparency = if on then 0.15 else 0
end

-- Picture-first screens ----------------------------------------------------------------------------

function ShowcaseKit.SetPicture(picture: ImageLabel, key: string?)
	local image = if key then UIKit.IconImage(key) else nil
	picture.Image = image or ""
	picture.Visible = image ~= nil
end

function ShowcaseKit.Picture(parent: Instance, name: string, key: string?): ImageLabel
	local picture = Instance.new("ImageLabel")
	picture.Name = name
	picture.BackgroundTransparency = 1
	picture.ScaleType = Enum.ScaleType.Fit
	picture.AnchorPoint = Vector2.new(0.5, 0.5)
	picture.Parent = parent
	ShowcaseKit.SetPicture(picture, key)
	return picture
end

function ShowcaseKit.PopIn(object: GuiObject, delay: number?, from: number?)
	local scale = object:FindFirstChild("PopScale") :: UIScale?
	if not scale then
		scale = Instance.new("UIScale")
		scale.Name = "PopScale"
		scale.Parent = object
	end
	local pop = scale :: UIScale
	pop.Scale = from or 0.3
	task.delay(delay or 0, function()
		TweenService:Create(pop, TweenInfo.new(0.34, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	end)
end

function ShowcaseKit.RobuxBadge(parent: Instance): (Frame, (number) -> ())
	local pill = Instance.new("Frame")
	pill.Name = "RobuxBadge"
	pill.BackgroundColor3 = WHITE
	pill.Size = UDim2.fromOffset(92, 40)
	pill.Parent = parent
	UIKit.Corner(pill, 20)
	UIKit.Stroke(pill, nil, 4)
	UIKit.Gradient(pill, UITheme.Buttons.Buy[1], UITheme.Buttons.Buy[2])
	local icon = Instance.new("ImageLabel")
	icon.Name = "Robux"
	icon.BackgroundTransparency = 1
	icon.Image = UITheme.Assets.Robux
	icon.ScaleType = Enum.ScaleType.Fit
	icon.AnchorPoint = Vector2.new(0, 0.5)
	icon.Position, icon.Size = UDim2.new(0, 7, 0.5, 0), UDim2.fromOffset(26, 26)
	icon.Parent = pill
	local price = UIKit.Label(pill, "Price", "", 26)
	price.AnchorPoint = Vector2.new(0, 0.5)
	price.Position, price.Size = UDim2.new(0, 36, 0.5, -1), UDim2.new(1, -40, 1, 0)
	price.TextXAlignment = Enum.TextXAlignment.Center
	price.TextTruncate = Enum.TextTruncate.None
	price.Outline.Color = Colors.CaptionOutline
	price.Outline.Thickness = 3
	return pill, function(robux: number)
		price.Text = tostring(robux)
	end
end

local RAINBOW = ColorSequence.new({
	ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 80, 110)),
	ColorSequenceKeypoint.new(0.18, Color3.fromRGB(255, 160, 50)),
	ColorSequenceKeypoint.new(0.36, Color3.fromRGB(255, 225, 60)),
	ColorSequenceKeypoint.new(0.54, Color3.fromRGB(90, 225, 110)),
	ColorSequenceKeypoint.new(0.72, Color3.fromRGB(60, 190, 255)),
	ColorSequenceKeypoint.new(0.88, Color3.fromRGB(120, 110, 255)),
	ColorSequenceKeypoint.new(1, Color3.fromRGB(215, 90, 255)),
})

function ShowcaseKit.Rainbow(button: TextButton)
	local face = button.Visual:FindFirstChild("Face") :: UIGradient
	face.Rotation = 0
	face.Color = RAINBOW
	face.Offset = Vector2.new(-0.15, 0)
	TweenService:Create(face, TweenInfo.new(2.4, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { Offset = Vector2.new(0.15, 0) }):Play()
end

function ShowcaseKit.Tick(parent: Instance): ImageLabel
	local tick = ShowcaseKit.Picture(parent, "Tick", "Tick")
	tick.AnchorPoint = Vector2.new(1, 1)
	tick.Position, tick.Size = UDim2.new(1, 6, 1, 4), UDim2.fromScale(0.55, 0.55)
	tick.ZIndex = 8
	return tick
end

-- The HUD's buttons ---------------------------------------------------------------------------------

function ShowcaseKit.HudButton(parent: Instance, name: string, image: string?, text: string, paletteName: string): TextButton
	local palette = paletteFor(paletteName)
	local hasImage = type(image) == "string" and image ~= ""
	local button = UIKit.Button(parent, name, "", "Go")
	local visual = button.Visual
	visual.Face.Color = ColorSequence.new(palette.top, palette.bottom)
	visual.UIStroke.Thickness = 5
	-- a bolder frosty checker than a normal button's
	local studs = visual.Studs
	studs.ImageColor3 = WHITE
	studs.TileSize = UDim2.fromOffset(32, 32)
	studs.UIGradient.Transparency = NumberSequence.new(0.78, 0.9)
	-- a thick light border inside the outline
	local rim = visual.Rim
	rim.Size = UDim2.new(1, -7, 1, -7)
	rim.UIStroke.Color = palette.rim
	rim.UIStroke.Thickness = 4
	rim.UIStroke.Transparency = 0
	local icon = Instance.new("ImageLabel")
	icon.Name = "Icon"
	icon.BackgroundTransparency = 1
	icon.Image = if hasImage then image :: string else ""
	icon.Visible = hasImage
	icon.ScaleType = Enum.ScaleType.Fit
	icon.AnchorPoint = Vector2.new(0.5, 0.5)
	icon.Position = UDim2.fromScale(0.5, 0.36)
	icon.Size = UDim2.fromScale(1.08, 1.08)
	icon.Rotation = -6
	icon.ZIndex = visual.ZIndex + 3
	icon.Parent = visual
	local maxText = if hasImage then 26 else 34
	local label = UIKit.Label(visual, "Label", text, maxText)
	if hasImage then
		label.AnchorPoint, label.Position, label.Size = Vector2.new(0.5, 1), UDim2.new(0.5, 0, 1, -4), UDim2.new(1, 10, 0, 30)
	else
		-- No picture yet: the word is the button.
		label.AnchorPoint, label.Position, label.Size = Vector2.new(0.5, 0.5), UDim2.new(0.5, 0, 0.5, -2), UDim2.new(1, -10, 0, 44)
	end
	label.TextXAlignment = Enum.TextXAlignment.Center
	label.TextTruncate = Enum.TextTruncate.None
	label.TextScaled = true
	label.Outline.Thickness = if hasImage then 4 else 5
	label.Outline.Color = Colors.CaptionOutline
	label.ZIndex = visual.ZIndex + 4
	local limit = Instance.new("UITextSizeConstraint")
	limit.MinTextSize, limit.MaxTextSize = 12, maxText
	limit.Parent = label
	return button
end

return ShowcaseKit
