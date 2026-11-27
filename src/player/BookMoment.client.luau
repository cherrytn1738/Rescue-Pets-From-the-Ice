-- The "Added to the Book" moment (docs/GAME_DESIGN.md, "The Creature Book"): the first time a creature is found
-- (its BookSeen count goes from 0 to 1) or its first Golden version is made, after the rescue banner a card with
-- its 3D picture and name, framed in its rarity colour (gold for a Golden one), pops into the middle of the screen,
-- a NEW! sticker stamps onto it with the new-creature ding, and after about a second it shrinks and flies along a
-- curve into the BOOK menu button, which bounces, flashes and counts its % up. If that entry completes a Book
-- page, a short "Page complete!" flourish follows with the book-page sound.
-- It never blocks play: it takes no input but a tap on the card (which skips to the fly-in), several new entries
-- queue up, it waits (a few seconds at most) for the rescue banner and for an open window to close, and banners
-- and toasts wait while it's on screen (Banners.Hold; toasts already wait while a card is queued), so nothing
-- overlaps: rescue banner, card, page flourish, toasts. Reduced effects keeps the card and the fly-in and drops the sparkles.
-- This script also owns the BOOK button's % (shown when no moment is waiting, else counted up as each card lands).
-- Found from the save's own copy (ClientState): a rescue, a Golden combine or a debug gift all show it.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Audio = require(ReplicatedStorage.Audio)
local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local EconomyRules = require(ReplicatedStorage.EconomyRules)
local IceLooks = require(ReplicatedStorage.IceLooks)
local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)
local UITheme = require(ReplicatedStorage.UITheme)
local Banners = require(script.Parent:WaitForChild("Banners"))
local ClientState = require(script.Parent:WaitForChild("ClientState"))
local Effects = require(script.Parent:WaitForChild("Effects"))
local PetViewport = require(script.Parent:WaitForChild("PetViewport"))

local LOOK = UITheme.BookMoment
local GOLD = Color3.fromRGB(255, 205, 60)
local PALETTES = { Common = "Ice", Uncommon = "Green", Rare = "Blue", Epic = "Purple", Legendary = "Gold", Mythic = "Pink" }

local _, root = UIKit.Screen("BookMoment", LOOK.DisplayOrder)
local bookButton: GuiButton? = nil
task.spawn(function()
	bookButton = UIKit.MenuButton("Book")
end)

-- The BOOK button's % ---------------------------------------------------------------------------------------

local shownPercent = nil
local function setPercent(percent: number)
	shownPercent = percent
	local visual = bookButton and bookButton:FindFirstChild("Visual")
	local label = visual and visual:FindFirstChild("Label", true)
	if label and label:IsA("TextLabel") then
		label.Text = `BOOK {percent}%`
	end
end

local function countUp(to: number)
	local from = shownPercent or to
	local start = os.clock()
	while true do
		local t = math.clamp((os.clock() - start) / LOOK.CountSeconds, 0, 1)
		setPercent(math.floor(from + (to - from) * t + 0.5))
		if t >= 1 then
			break
		end
		RunService.RenderStepped:Wait()
	end
end

-- Little sparkles (not with reduced effects) --------------------------------------------------------------

local function sparkle(at: Vector2, color: Color3, reach: number, seconds: number)
	local star = Instance.new("TextLabel")
	star.BackgroundTransparency = 1
	star.AnchorPoint = Vector2.new(0.5, 0.5)
	star.Size = UDim2.fromOffset(22, 22)
	star.Position = UDim2.fromOffset(at.X, at.Y)
	star.Text = "✦"
	star.Font = UITheme.Font
	star.TextScaled = true
	star.TextColor3 = color
	star.ZIndex = 30
	star.Parent = root
	local angle = math.random() * math.pi * 2
	local goal = at + Vector2.new(math.cos(angle), math.sin(angle)) * reach * (0.6 + math.random() * 0.4)
	local tween = TweenService:Create(star, TweenInfo.new(seconds, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
		Position = UDim2.fromOffset(goal.X, goal.Y),
		TextTransparency = 1,
		Rotation = math.random(-90, 90),
	})
	tween:Play()
	tween.Completed:Once(function()
		star:Destroy()
	end)
end

-- The card ------------------------------------------------------------------------------------------------

local function bezier(a: Vector2, b: Vector2, c: Vector2, t: number): Vector2
	return a:Lerp(b, t):Lerp(b:Lerp(c, t), t)
end

local function playCard(item)
	local creature = CreatureConfig.Get(item.CreatureId)
	if not creature then
		return
	end
	local golden = item.Golden
	local colour = if golden then GOLD else IceLooks.RarityColors[creature.Rarity]
	local reduced = Effects.Reduced()
	local screen = UIKit.ScreenSize()
	local fit = math.min(UIKit.MenuScale(), screen.Y * LOOK.ScreenShare / LOOK.Size.Y, screen.X * 0.6 / LOOK.Size.X)
	local centre = Vector2.new(screen.X / 2, screen.Y * 0.53)

	-- a tap on the card skips to the fly-in (it's a button: the tap doesn't reach the ice)
	local holder = Instance.new("TextButton")
	holder.Name = "BookCard"
	holder.Text, holder.AutoButtonColor, holder.BackgroundTransparency = "", false, 1
	holder.AnchorPoint = Vector2.new(0.5, 0.5)
	holder.Size = UDim2.fromOffset(LOOK.Size.X, LOOK.Size.Y)
	holder.Position = UDim2.fromOffset(centre.X, centre.Y)
	holder.Selectable = false
	holder.Parent = root
	local scale = Instance.new("UIScale")
	scale.Scale = 0
	scale.Parent = holder
	local glow = Instance.new("Frame") -- the rarity-coloured frame round the card
	glow.Name = "Glow"
	glow.BackgroundTransparency = 1
	glow.AnchorPoint, glow.Position = Vector2.new(0.5, 0.5), UDim2.fromScale(0.5, 0.5)
	glow.Size = UDim2.new(1, 14, 1, 14)
	glow.Parent = holder
	UIKit.Corner(glow, 20)
	UIKit.Stroke(glow, colour, 7, 0.1)
	local card = ShowcaseKit.Card(holder, "Card", if golden then "Gold" else PALETTES[creature.Rarity] or "Ice")
	card.Size = UDim2.fromScale(1, 1)
	local header = UIKit.Label(card, "Header", if golden then "NEW ON THE GOLDEN PAGE!" else "ADDED TO THE BOOK!", 22, Color3.fromRGB(255, 245, 190))
	header.Position, header.Size = UDim2.fromOffset(10, 12), UDim2.new(1, -20, 0, 26)
	header.TextXAlignment = Enum.TextXAlignment.Center
	header.TextScaled = true
	header.ZIndex = 6
	local well = Instance.new("Frame") -- the picture's dark well
	well.Name = "Well"
	well.BackgroundColor3 = Color3.fromRGB(10, 26, 48)
	well.BackgroundTransparency = 0.35
	well.Position, well.Size = UDim2.fromOffset(18, 46), UDim2.new(1, -36, 0, LOOK.Size.Y - 150)
	well.ZIndex = 4
	well.Parent = card
	UIKit.Corner(well, 12)
	local view = PetViewport.new(well, creature.Id, if golden then "Golden" else "Normal")
	local name = UIKit.Label(card, "Name", (if golden then "Golden " else "") .. creature.Name, 34)
	name.Position, name.Size = UDim2.new(0, 12, 1, -98), UDim2.new(1, -24, 0, 40)
	name.TextXAlignment = Enum.TextXAlignment.Center
	name.TextScaled = true
	name.ZIndex = 6
	local rarity = UIKit.Label(card, "Rarity", string.upper(creature.Rarity), 24, colour)
	rarity.Position, rarity.Size = UDim2.new(0, 12, 1, -54), UDim2.new(1, -24, 0, 30)
	rarity.TextXAlignment = Enum.TextXAlignment.Center
	rarity.ZIndex = 6
	local sticker = ShowcaseKit.Sticker(card, "NEW!", if golden then "Gold" else "Locked")
	sticker.Size = UDim2.fromOffset(120, 40)
	sticker.Position = UDim2.new(1, 12, 0, 40) -- (on the picture's corner, clear of the header)
	sticker.Visible = false
	local stickerScale = Instance.new("UIScale")
	stickerScale.Parent = sticker

	local skip = false
	holder.Activated:Connect(function()
		skip = true
	end)

	-- pop in
	TweenService:Create(scale, TweenInfo.new(LOOK.PopSeconds, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = fit }):Play()
	task.wait(LOOK.PopSeconds)
	-- the NEW! sticker stamps on: big and tilted, slamming down, the ding, a jolt
	sticker.Visible = true
	stickerScale.Scale = 2.6
	sticker.Rotation = -18
	local stamp = TweenInfo.new(LOOK.StampSeconds, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	TweenService:Create(stickerScale, stamp, { Scale = 1 }):Play()
	TweenService:Create(sticker, stamp, { Rotation = 8 }):Play()
	task.wait(LOOK.StampSeconds)
	Audio.Play("BookNew")
	holder.Rotation = -3
	TweenService:Create(holder, TweenInfo.new(0.25, Enum.EasingStyle.Elastic, Enum.EasingDirection.Out), { Rotation = 0 }):Play()
	if not reduced then
		local at = sticker.AbsolutePosition + sticker.AbsoluteSize / 2 - root.AbsolutePosition
		for _ = 1, LOOK.Sparkles do
			sparkle(at, if golden then GOLD else Color3.new(1, 1, 1), 90 * fit, 0.55)
		end
	end
	-- hold (a tap skips)
	local holdUntil = os.clock() + LOOK.HoldSeconds
	while os.clock() < holdUntil and not skip do
		task.wait()
	end

	-- the fly-in: a curve into the BOOK button, shrinking
	local button = bookButton
	local target = if button and button.AbsoluteSize.X > 0
		then button.AbsolutePosition + button.AbsoluteSize / 2 - root.AbsolutePosition
		else Vector2.new(60, screen.Y / 2)
	local control = Vector2.new(centre.X + (target.X - centre.X) * 0.35, math.min(centre.Y, target.Y) - 140 * fit)
	local start = os.clock()
	local lastTrail = 0
	while true do
		local t = math.clamp((os.clock() - start) / LOOK.FlySeconds, 0, 1)
		local eased = t * t * (3 - 2 * t)
		local at = bezier(centre, control, target, eased)
		holder.Position = UDim2.fromOffset(at.X, at.Y)
		scale.Scale = fit + (LOOK.EndScale - fit) * eased
		holder.Rotation = -12 * eased
		if not reduced and os.clock() - lastTrail > 0.04 then
			lastTrail = os.clock()
			sparkle(at, colour, 24, 0.4)
		end
		if t >= 1 then
			break
		end
		RunService.RenderStepped:Wait()
	end
	view:Destroy()
	holder:Destroy()

	-- the BOOK button: a bounce, a white flash and the % counting up
	if button then
		local visual = button:FindFirstChild("Visual")
		local press = visual and visual:FindFirstChild("PressScale")
		if press then
			press.Scale = 1.3
			TweenService:Create(press, TweenInfo.new(0.45, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
		end
		if visual then
			local flash = Instance.new("Frame")
			flash.Name = "BookFlash"
			flash.BackgroundColor3 = Color3.new(1, 1, 1)
			flash.BackgroundTransparency = 0.15
			flash.Size = UDim2.fromScale(1, 1)
			flash.ZIndex = 20
			flash.Parent = visual
			UIKit.Corner(flash, UITheme.Sizes.ButtonCorner)
			local fade = TweenService:Create(flash, TweenInfo.new(0.5), { BackgroundTransparency = 1 })
			fade:Play()
			fade.Completed:Once(function()
				flash:Destroy()
			end)
		end
		if not reduced then
			for _ = 1, 6 do
				sparkle(target, colour, 50, 0.45)
			end
		end
	end
	countUp(item.Percent)
end

-- A completed page's flourish (after its card lands).
local function flourish(pageId: string)
	local page = nil
	for _, bookPage in CreatureConfig.Book do
		if bookPage.Page == pageId then
			page = bookPage
		end
	end
	if not page then
		return
	end
	Banners.Big("Page complete!", `{pageId} page · {CreatureConfig.BookRewardText(page)}`, GOLD, LOOK.FlourishSeconds)
	Audio.Play("BookPage")
end

-- The queue -----------------------------------------------------------------------------------------------

local queue = {} -- { CreatureId, Golden, Percent, Pages = { page ids } }
local running = false
local known = nil -- what the last copy of the save had: { seen, golden, complete, found }

local function waitForRoom()
	-- after the rescue banner (and any other big banner), and once no window is open (each at most a few seconds:
	-- the toasts are waiting too)
	task.wait(LOOK.AfterRescueSeconds)
	local waited = 0
	while Banners.Busy() and waited < 8 do
		waited += task.wait(0.1)
	end
	waited = 0
	while UIKit.AnyWindowOpen() and waited < 6 do
		waited += task.wait(0.2)
	end
end

local function run()
	if running then
		return
	end
	running = true
	Banners.HoldToasts() -- (toasts wait for the cards: banner, card, then toasts)
	while #queue > 0 do
		local item = table.remove(queue, 1)
		waitForRoom()
		Banners.Hold()
		local ok, err = pcall(playCard, item)
		Banners.Release()
		if not ok then
			warn("[BookMoment] " .. tostring(err))
		end
		for _, pageId in item.Pages do
			flourish(pageId)
		end
	end
	running = false
	Banners.ReleaseToasts()
	local data = ClientState.Data()
	if data then
		setPercent(math.floor(EconomyRules.BookCompletion(data) * 100))
	end
end

ClientState.Changed(function(data)
	local seen, golden, complete = {}, {}, {}
	for id, count in data.BookSeen do
		if type(count) == "number" and count > 0 then
			seen[id] = true
		end
	end
	for id, made in data.BookGolden do
		if made == true then
			golden[id] = true
		end
	end
	local found, total = 0, 0
	for _, page in EconomyRules.BookPages(data) do
		found += page.Found
		total += page.Count
		if page.Complete then
			complete[page.Page] = true
		end
	end
	if not known then
		known = { seen = seen, golden = golden, complete = complete, found = found }
		setPercent(math.floor(EconomyRules.BookCompletion(data) * 100))
		return
	end
	local added = {}
	for _, creature in CreatureConfig.Creatures do
		if seen[creature.Id] and not known.seen[creature.Id] then
			table.insert(added, { CreatureId = creature.Id, Golden = false, Pages = {}, Page = creature.Rarity })
		end
	end
	for _, creature in CreatureConfig.Creatures do
		if golden[creature.Id] and not known.golden[creature.Id] then
			table.insert(added, { CreatureId = creature.Id, Golden = true, Pages = {}, Page = "Golden" })
		end
	end
	local newPages = {}
	for pageId in complete do
		if not known.complete[pageId] then
			table.insert(newPages, pageId)
		end
	end
	local before = known.found
	known = { seen = seen, golden = golden, complete = complete, found = found }
	if #added == 0 then
		if not running and #queue == 0 then
			setPercent(math.floor(EconomyRules.BookCompletion(data) * 100))
		end
		return
	end
	for index, item in added do
		item.Percent = math.floor(math.min(found, before + index) / math.max(total, 1) * 100)
	end
	-- each completed page follows the card of the entry on it that finished it (the last one on that page)
	for _, pageId in newPages do
		local owner = added[#added]
		for _, item in added do
			if item.Page == pageId then
				owner = item
			end
		end
		table.insert(owner.Pages, pageId)
	end
	for _, item in added do
		table.insert(queue, item)
	end
	task.spawn(run)
end)
