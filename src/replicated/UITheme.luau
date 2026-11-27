-- Every colour, size, asset and timing the game's UI uses (UIKit builds everything from these). The
-- look is the roblox-ui-style skill's "showcase" style recoloured for the ice: one rounded bold font,
-- dark navy outlines on everything, glacier-blue gradient windows with a faint checker, frosty white
-- rims, chunky studded buttons whose colour says what they do. Recolour here only.
--
-- Assets: only images checked to be public library assets are listed (the checker and the Robux
-- icon). This game's own pictures (HUD icons, shop pictures, picture sheets) start empty: add each id
-- once it is uploaded to the group (tools/upload_models.py). Code that reads these tables works with
-- them empty (text instead of an icon, no corner picture).
local function rgb(r, g, b)
	return Color3.fromRGB(r, g, b)
end
local WHITE = Color3.new(1, 1, 1)

local UITheme = {}

UITheme.Font = Enum.Font.FredokaOne

UITheme.Colors = {
	Outline = rgb(12, 20, 36), -- the thick outline on every window, card, button and label (dark navy)
	CaptionOutline = rgb(10, 26, 44), -- button captions
	Text = WHITE,
	Muted = rgb(214, 236, 255), -- detail lines (pale ice white)
	Gold = rgb(255, 214, 64), -- key values and good news
	Error = rgb(255, 84, 104), -- errors and refusals
	Good = rgb(130, 255, 200), -- owned, done, success (mint)
	Accent = rgb(110, 230, 255), -- a neutral highlight (glacier cyan)
	Card = rgb(28, 52, 84), -- a dark recessed card on a window (deep ice slate)
	CardRim = rgb(110, 160, 210), -- that card's inner rim
	Selected = rgb(190, 240, 255), -- the rim of a selected card or row (bright frost)
	Well = rgb(12, 26, 46), -- the dark area that holds a window's list
	Silhouette = rgb(8, 14, 26), -- an undiscovered item
	Field = rgb(14, 30, 52), -- text boxes
	Placeholder = rgb(130, 160, 195), -- a text box's placeholder
	Scrim = rgb(4, 12, 24),
}

-- Window themes: the window's gradient, its faint checker tint, the title's gradient end colour.
UITheme.Windows = {
	-- Normal menus: glacier blue.
	Ice = { top = rgb(120, 205, 255), bottom = rgb(36, 110, 200), checker = rgb(10, 40, 90), title = rgb(215, 245, 255) },
	-- The dark one colour cards sit on.
	Polar = { top = rgb(40, 70, 110), bottom = rgb(16, 32, 58), checker = rgb(0, 0, 0), title = rgb(180, 235, 255) },
	-- The showcase window (ShowcaseKit): a deep ice-blue, see-through panel with a thick dark border and
	-- a pure white title, so bright colour cards stand out on it.
	Showcase = { top = rgb(46, 78, 118), bottom = rgb(18, 36, 64), checker = rgb(0, 10, 30), title = WHITE, transparency = 0.16, outline = 6 },
}

-- Button kinds by meaning. Keep the meanings when you recolour.
UITheme.Buttons = {
	Go = { rgb(100, 235, 190), rgb(20, 165, 140) }, -- available action: go, equip, confirm, redeem (glacier green)
	Buy = { rgb(140, 255, 160), rgb(30, 185, 110) }, -- purchase and claim (cool green)
	Done = { rgb(170, 186, 204), rgb(112, 128, 150) }, -- equipped, selected elsewhere, disabled, unselected tab
	Locked = { rgb(255, 90, 110), rgb(210, 30, 60) }, -- locked, destructive
	Neutral = { rgb(90, 190, 255), rgb(30, 110, 230) }, -- neutral actions, the selected tab
	Gift = { rgb(180, 140, 255), rgb(122, 84, 230) }, -- gifting, codes
	Gold = { rgb(255, 226, 100), rgb(230, 160, 30) }, -- owned / maxed
	Close = { rgb(255, 76, 96), rgb(215, 20, 50) }, -- the window close button
	Frost = { rgb(230, 244, 255), rgb(150, 190, 225) }, -- quiet HUD buttons (settings)
}

-- Colour card palettes (the Robux shop and other colour cards): face gradient, lighter inner rim,
-- name tint.
UITheme.CardPalettes = {
	Ice = { top = rgb(205, 238, 255), bottom = rgb(100, 170, 230), rim = WHITE, name = WHITE },
	Glacier = { top = rgb(80, 225, 255), bottom = rgb(20, 120, 200), rim = rgb(190, 245, 255), name = rgb(230, 252, 255) },
	Aurora = { top = rgb(60, 230, 190), bottom = rgb(40, 60, 160), rim = rgb(170, 255, 235), name = rgb(220, 255, 245) },
	Green = { top = rgb(110, 225, 120), bottom = rgb(25, 140, 90), rim = rgb(190, 255, 190), name = rgb(235, 255, 225) },
	Teal = { top = rgb(50, 215, 200), bottom = rgb(15, 115, 135), rim = rgb(170, 255, 240), name = rgb(225, 255, 250) },
	Blue = { top = rgb(80, 175, 255), bottom = rgb(28, 78, 215), rim = rgb(175, 220, 255), name = rgb(225, 245, 255) },
	Purple = { top = rgb(165, 120, 255), bottom = rgb(80, 45, 195), rim = rgb(215, 195, 255), name = rgb(245, 235, 255) },
	Pink = { top = rgb(255, 130, 210), bottom = rgb(195, 45, 150), rim = rgb(255, 205, 240), name = rgb(255, 235, 250) },
	Gold = { top = rgb(255, 210, 60), bottom = rgb(230, 135, 20), rim = rgb(255, 240, 165), name = rgb(255, 252, 215) },
	Orange = { top = rgb(255, 155, 50), bottom = rgb(205, 60, 25), rim = rgb(255, 212, 145), name = rgb(255, 240, 195) },
	Crimson = { top = rgb(240, 65, 95), bottom = rgb(145, 15, 50), rim = rgb(255, 165, 180), name = rgb(255, 228, 232) },
	Slate = { top = rgb(150, 168, 195), bottom = rgb(78, 92, 120), rim = rgb(215, 228, 245), name = rgb(240, 246, 255) },
	Locked = { top = rgb(66, 76, 96), bottom = rgb(36, 42, 58), rim = rgb(118, 130, 156), name = rgb(196, 206, 224) },
}

-- Progress bars: an ice-blue fill in a dark recessed trough.
UITheme.Progress = { trough = rgb(10, 26, 48), top = rgb(150, 240, 255), bottom = rgb(40, 150, 240), bevel = rgb(16, 80, 160) }

-- Public library images (the same ids as the roblox-ui-style skill's Theme).
UITheme.Assets = {
	Checker = "rbxassetid://385956923", -- faint checkerboard (tinted and faded in use)
	Robux = "rbxassetid://11560341132", -- white Robux icon (Creator Store)
}

-- The icon set (UIKit.Icon / UIKit.IconImage, keyed by name). Rendered from the game's own models by
-- tools/icons/compose_icons.py --ui (store-assets/ui-icons/, original, made for this game), uploaded as
-- group 921449746 (store-assets/ui-icons/upload_manifest.json). A missing key shows as text instead.
UITheme.Icons = {
	-- the HUD menu
	Build = "rbxassetid://85794462682522",
	Upgrades = "rbxassetid://98369261128948",
	Pets = "rbxassetid://119156189567977",
	Book = "rbxassetid://130307156552089",
	Rebirth = "rbxassetid://119002750297089",
	Home = "rbxassetid://77155447367974",
	Shop = "rbxassetid://120557887995853",
	Codes = "rbxassetid://131827593577086",
	-- the Build window (each building's tier-1 station)
	Building_ChiselMill = "rbxassetid://99961407371116",
	Building_FlamethrowerTurret = "rbxassetid://97345125768912",
	Building_HeatLamp = "rbxassetid://118767728936322",
	Building_IceDrill = "rbxassetid://78775902196885",
	Building_IcePickPost = "rbxassetid://116570461396234",
	Building_LavaPump = "rbxassetid://100257002467306",
	Building_SunMirrorTower = "rbxassetid://132354686137893",
	Building_WreckingCrane = "rbxassetid://110047670337897",
	-- the Upgrades window (a building upgrade is its building's icon with UpgradeBadge on it)
	Pick1 = "rbxassetid://131315085446588",
	Pick2 = "rbxassetid://76309498309335",
	Pick3 = "rbxassetid://98117823681410",
	Pick4 = "rbxassetid://89124148260955",
	Pick5 = "rbxassetid://103611508689600",
	Pick6 = "rbxassetid://110555225812857",
	FrostTouch = "rbxassetid://83885185754286",
	BiggerBurst = "rbxassetid://101644423518291",
	CrystalYield = "rbxassetid://87468174560263",
	FastSled = "rbxassetid://76695650631595",
	UpgradeBadge = "rbxassetid://99395304409533",
}

-- Picture sheets (ShowcaseKit.SheetPicture): images of Cell x Cell cells, PerRow to a row, in the
-- order listed. Groups = { [group] = { { Image = id, Cells = { item ids } }, ... } }. Empty for now.
UITheme.Sheets = {
	Cell = 256,
	PerRow = 4,
	Groups = {},
}

-- The Robux shop's pictures, keyed by product or pass key (and ShopBasket, the shop window's corner
-- picture). Empty until this game's products exist.
UITheme.ShopIcons = {}

-- The showcase look (ShowcaseKit): window title, corner picture and close button sizes, in menu units.
UITheme.Showcase = { TitleSize = 92, TitleRise = 50, TitleOutline = 8, CornerIcon = 170, CloseSize = 78, SectionSize = 44, CardTitle = 38 }

UITheme.Sizes = {
	Outline = 4, -- windows, cards, buttons
	ThinOutline = 3, -- tiles, troughs, fields
	WindowCorner = 16,
	CardCorner = 12,
	ButtonCorner = 8,
	Pad = 12, -- inside windows and cards
	Gap = 10, -- between cards and rows
	TitleRise = 44, -- how far a window's title rides above its top edge
	CloseSize = 58,
}

-- Responsive scale: min(screen / Baseline) clamped to [Min, Max], times Menu, never below MenuFloor
-- (menus stay big and tappable on phones). The HUD uses Hud x the menu scale.
UITheme.Scale = { Baseline = Vector2.new(1050, 620), Min = 0.52, Max = 1.18, Menu = 0.95, MenuFloor = 0.75, Hud = 0.75 }

UITheme.Motion = { Hover = 1.05, Press = 0.94, HoverTime = 0.08, PressTime = 0.05, ReleaseTime = 0.12, OpenTime = 0.22, CloseTime = 0.12 }

UITheme.Blur = { Menu = 8 } -- while a window is open
-- The "Added to the Book" card (BookMoment.client): Size px (menu units), at most ScreenShare of the screen's height;
-- it pops in (PopSeconds), the NEW! sticker stamps (StampSeconds), it holds (HoldSeconds; a tap skips), flies into the
-- BOOK button (FlySeconds, shrinking to EndScale) and the % counts up (CountSeconds). Sparkles per stamp (none with
-- reduced effects). A completed page's flourish shows FlourishSeconds. Below banners (30), above windows (20).
UITheme.BookMoment = {
	DisplayOrder = 29,
	Size = Vector2.new(250, 330),
	ScreenShare = 0.62,
	AfterRescueSeconds = 0.35,
	PopSeconds = 0.32,
	StampSeconds = 0.16,
	HoldSeconds = 1.1,
	FlySeconds = 0.6,
	EndScale = 0.12,
	CountSeconds = 0.45,
	Sparkles = 10,
	FlourishSeconds = 2.2,
}
-- The tutorial's spotlight (Spotlight): the screen goes black at Darkness (0..1 opacity) round a cut-out with rounded
-- Corner (px), Padding px round the target, and a Glow ring pulsing PulseSpeed (radians/s); the instruction is
-- TextSize, at most TextWidth px wide. Above windows (20), below banners and notices (30+) and the debug windows.
UITheme.Spotlight = {
	DisplayOrder = 25,
	Darkness = 0.6,
	Corner = 14,
	Padding = 8,
	Glow = rgb(190, 240, 255),
	PulseSpeed = 4,
	TextSize = 32,
	TextColor = rgb(255, 240, 150),
	TextWidth = 440,
	TextBacking = 0.55, -- the words' dark rounded backing (opacity)
	FadeSeconds = 0.2,
}
UITheme.WindowTransparency = 0.08

return UITheme
