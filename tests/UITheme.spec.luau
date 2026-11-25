--[[
Spec for src/replicated/UITheme.luau (the ice palette), AudioConfig.luau and NumberFormat.luau, and a
text check of the UI kit. UIKit, ShowcaseKit and HUD.client are only READ as text, never run: running
UIKit in Edit mode would switch ProximityPromptService off in the saved place.

Run: python tools/run_specs.py UITheme
]]
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local UITheme = assert(loadstring(sources.UITheme))()
	local AudioConfig = assert(loadstring(sources.AudioConfig))()
	local NumberFormat = assert(loadstring(sources.NumberFormat))()

	-- Tokens ------------------------------------------------------------------------------------------
	check(UITheme.Font == Enum.Font.FredokaOne, "one rounded bold font")
	for _, name in { "Outline", "CaptionOutline", "Text", "Muted", "Gold", "Error", "Good", "Accent", "Card", "CardRim", "Selected", "Well", "Silhouette", "Field", "Placeholder", "Scrim" } do
		check(typeof(UITheme.Colors[name]) == "Color3", "Colors." .. name .. " is a Color3")
	end
	for _, name in { "Ice", "Polar", "Showcase" } do
		local theme = UITheme.Windows[name]
		check(theme and typeof(theme.top) == "Color3" and typeof(theme.bottom) == "Color3" and typeof(theme.checker) == "Color3" and typeof(theme.title) == "Color3",
			"window theme " .. name .. " has top, bottom, checker and title")
	end
	for _, kind in { "Go", "Buy", "Done", "Locked", "Neutral", "Gift", "Gold", "Close", "Frost" } do
		local faces = UITheme.Buttons[kind]
		check(faces and typeof(faces[1]) == "Color3" and typeof(faces[2]) == "Color3", "button kind " .. kind .. " has two faces")
	end
	-- The palettes the copied windows and the HUD name.
	for _, name in { "Ice", "Glacier", "Aurora", "Green", "Teal", "Blue", "Purple", "Pink", "Gold", "Orange", "Crimson", "Slate", "Locked" } do
		local palette = UITheme.CardPalettes[name]
		check(palette and typeof(palette.top) == "Color3" and typeof(palette.bottom) == "Color3" and typeof(palette.rim) == "Color3" and typeof(palette.name) == "Color3",
			"card palette " .. name .. " has top, bottom, rim and name")
	end
	check(typeof(UITheme.Progress.trough) == "Color3" and typeof(UITheme.Progress.top) == "Color3", "progress bar colours")
	check(type(UITheme.Sizes.Outline) == "number" and typeof(UITheme.Scale.Baseline) == "Vector2", "sizes and the responsive baseline")

	-- The ice look: windows and buttons are cool (blue at least as strong as red), except the kinds whose
	-- colour is their meaning (Locked, Close, Gold, Gift).
	for _, name in { "Ice", "Polar", "Showcase" } do
		local top = UITheme.Windows[name].top
		check(top.B >= top.R, "window " .. name .. " is a cool blue")
	end
	for _, kind in { "Go", "Buy", "Done", "Neutral", "Frost" } do
		local face = UITheme.Buttons[kind][1]
		check(face.B >= face.R or face.G >= face.R, "button " .. kind .. " is a cool colour")
	end

	-- Contrast (WCAG ratio) ---------------------------------------------------------------------------
	local function channel(value)
		return if value <= 0.03928 then value / 12.92 else ((value + 0.055) / 1.055) ^ 2.4
	end
	local function luminance(color: Color3)
		return 0.2126 * channel(color.R) + 0.7152 * channel(color.G) + 0.0722 * channel(color.B)
	end
	local function contrast(a: Color3, b: Color3)
		local la, lb = luminance(a), luminance(b)
		return (math.max(la, lb) + 0.05) / (math.min(la, lb) + 0.05)
	end
	local C = UITheme.Colors
	check(contrast(C.Text, C.Outline) >= 12, "white text against its dark outline")
	check(contrast(C.Text, C.Card) >= 7, "white text on a dark card")
	check(contrast(C.Text, C.Field) >= 7, "typed text in a text box")
	check(contrast(C.Placeholder, C.Field) >= 3, "a text box's placeholder")
	check(contrast(C.Muted, C.Well) >= 7, "detail text on a window's well")
	check(contrast(C.Gold, C.Well) >= 7, "gold key values on a window's well")
	check(contrast(C.Error, C.Well) >= 4.5, "error text on a window's well")
	check(contrast(C.Text, UITheme.Windows.Showcase.bottom) >= 7, "white text on the showcase window")
	for kind, faces in UITheme.Buttons do
		check(contrast(C.CaptionOutline, faces[1]) >= 3 and contrast(C.CaptionOutline, faces[2]) >= 3, "the outline stands out on the " .. kind .. " button")
	end
	for name, palette in UITheme.CardPalettes do
		if name == "Locked" then
			-- Dark on purpose (a locked card): its white outlined text must read instead.
			check(contrast(C.Text, palette.top) >= 7, "white text on the Locked card")
		else
			check(contrast(C.Outline, palette.top) >= 3, "the outline stands out on the " .. name .. " card")
		end
	end

	-- No old asset ids --------------------------------------------------------------------------------
	-- The only images allowed in the UI files are the public library ones in UITheme.Assets; the
	-- game's own pictures (Icons, Sheets, ShopIcons) start empty. The sounds are the game's own (SoundRules spec).
	local allowed = {}
	for _, id in UITheme.Assets do
		allowed[id] = true
	end
	check(allowed["rbxassetid://385956923"] and allowed["rbxassetid://11560341132"], "the checker and the Robux icon")
	check(next(UITheme.Icons) == nil, "no icons yet")
	check(next(UITheme.ShopIcons) == nil, "no shop pictures yet")
	check(next(UITheme.Sheets.Groups) == nil, "no picture sheets yet")
	check(AudioConfig.Ui.Click ~= nil and AudioConfig.Sfx.Tap ~= nil, "the game's own sounds")
	check(AudioConfig.DefaultVolumes.SfxVolume > 0 and AudioConfig.DefaultVolumes.MusicVolume > 0, "default volumes")
	for _, file in { "UITheme", "UIKit", "ShowcaseKit", "Audio", "AudioConfig", "NumberFormat", "HUD" } do
		local text = assert(sources[file], file .. " exists")
		for id in string.gmatch(text, "rbxassetid://%d+") do
			check(allowed[id], file .. " uses only allowed images (" .. id .. ")")
		end
		for _, word in { "Safari", "Zoodex", "Steal" } do -- (rebirths are this game's own too)
			check(not string.find(text, word), file .. " has no Steal Pets name (" .. word .. ")")
		end
	end

	-- The kit's API the copied windows call -----------------------------------------------------------
	for _, name in { "Label", "Button", "SetButton", "Scroll", "Tabs", "TextBox", "MenuButton", "PlaySound", "Window", "Screen",
		"OnScreenChanged", "HudScale", "MenuScale", "IsPretendScreen", "AnyWindowOpen", "UsingGamepad", "Icon", "FitOneLine" } do
		check(string.find(sources.UIKit, "function UIKit." .. name .. "(", 1, true), "UIKit." .. name .. " exists")
	end
	for _, name in { "Window", "Card", "CardPicture", "CardTitle", "CardText", "BuyButton", "InfoButton", "SectionHeader", "Sticker", "HudButton" } do
		check(string.find(sources.ShowcaseKit, "function ShowcaseKit." .. name .. "(", 1, true), "ShowcaseKit." .. name .. " exists")
	end
	check(string.find(sources.UIKit, "ProximityPromptService.Enabled = true", 1, true), "UIKit turns prompts back on when it loads")
	check(string.find(sources.UIKit, "StudioScreenSize", 1, true) and string.find(sources.UIKit, "StudioGamepad", 1, true), "the Studio switches")
	check(string.find(sources.HUD, '"Shop"', 1, true) and string.find(sources.HUD, '"Codes"', 1, true), "the HUD builds SHOP and CODES")

	-- NumberFormat ------------------------------------------------------------------------------------
	check(NumberFormat.Short(950) == "950", "small numbers stay whole")
	check(NumberFormat.Short(1200) == "1.2K", "thousands")
	check(NumberFormat.Short(1.5e33) == "1.5Dc", "decillions")
	check(NumberFormat.Short(1.8214294876533983e72) == "1.82Tvg", "past Dc the suffixes go on (level 400 ice HP)")
	check(NumberFormat.Short(18.2e93) == "18.2Tg", "the last suffix")
	check(NumberFormat.Short(1.82e96) == "1.82e96", "past the last suffix: a short exponent")
	check(NumberFormat.Short(3e100) == "3e100", "an exponent without trailing zeros")
	check(#NumberFormat.Short(1e300) <= 8, "the largest numbers stay short")
	check(NumberFormat.Short(0 / 0) == "0", "not a number shows 0")
	check(NumberFormat.Money(2500000) == "$2.5M", "money")
	check(NumberFormat.MoneyPrecise(186910) == "$186.91K", "precise money never rounds up")

	return passed
end
