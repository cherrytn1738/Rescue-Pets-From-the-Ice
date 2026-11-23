-- The Robux shop, opened from the SHOP button, in the showcase look (ShowcaseKit): one scrolling page
-- of sections (MonetizationConfig.Shop.Tabs: "~ Passes ~", then the products' tabs), each a set of
-- colour cards: the item's picture (its config Icon, if it has one), its name and a green buy button
-- with Roblox's live price. The buttons along the top jump to a section (and light up as the page
-- scrolls past it). The GIFT toggle picks another player in the server, and the products are then
-- bought for them (passes can't be gifted). With nothing in MonetizationConfig the page says so.
-- Paid random items get an "i INFO" button that shows their description and every chance (the
-- config's Odds) before purchase, as Roblox requires. No crossed-out prices.
--
-- The window only asks: a buy button sends an intent on PurchaseRequest (the item's key, and who it
-- is for). The server checks it, opens Roblox's purchase prompt, and the receipt grants it. Prices
-- on the buttons are Roblox's live prices (PriceCache). Items without a real id are never shown in a
-- live game; in Studio they show a NO ID YET sticker and buying one runs a simulated purchase.
-- The server's PurchaseNotice RemoteEvent (bought, gift sent, gift received, pass owned) shows in the
-- window's feedback line, or as a short banner when the window is closed.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local visitRemote = ReplicatedStorage:WaitForChild("ShopVisit") :: RemoteEvent
local noticeRemote = ReplicatedStorage:WaitForChild("PurchaseNotice") :: RemoteEvent

local PriceCache = require(script.Parent:WaitForChild("PriceCache"))
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)

local localPlayer = Players.LocalPlayer
local Colors = UIKit.Colors
local remote = ReplicatedStorage:WaitForChild("PurchaseRequest") :: RemoteFunction

local IS_STUDIO = RunService:IsStudio()
local CARD_HEIGHT = 174
local COMPACT_CARD_HEIGHT = 136 -- short windows (a landscape phone): no line of detail
local CARD_GAP = 14 -- between cards in a row
local ROW_GAP = 30 -- between rows (the pictures poke over the cards' top edges)
local HEADER_HEIGHT = 60
local NOTICE_SECONDS = 4

-- Card colours (UITheme.CardPalettes keys; a missing key falls back to Blue).
local PASS_PALETTE = "Purple"
local PRODUCT_PALETTE = "Blue"

local giftMode = false
local giftTarget: Player? = nil
local busy = false

-- Paid random items are hidden for players whose region restricts them. The server says so
-- (PaidRandomPolicy); until it has, they count as restricted.
local function paidRandomRestricted(): boolean
	return localPlayer:GetAttribute("PaidRandomItems") ~= "Allowed"
end

-- Shown: items with a real id; in Studio, every item. Never a paid random item the player can't buy.
local function shown(entry): boolean
	if MonetizationConfig.IsPaidRandom(entry) and paidRandomRestricted() then
		return false
	end
	return MonetizationConfig.IsLive(entry) or IS_STUDIO
end

-- The items of a section that this player is shown.
local function sectionItems(sectionId: string): { { entry: any, isPass: boolean } }
	local items = {}
	if sectionId == "Passes" then
		for _, pass in MonetizationConfig.Passes do
			if shown(pass) then
				table.insert(items, { entry = pass, isPass = true })
			end
		end
	else
		for _, product in MonetizationConfig.Products do
			if product.Tab == sectionId and shown(product) then
				table.insert(items, { entry = product, isPass = false })
			end
		end
	end
	return items
end

local refresh, say, window
local tabs, giftToggle, giftRow, list, feedback, infoPanel, infoText
local listWidth = 0
local compact = false -- a short window: smaller cards and headers
local sectionTop = {} -- [section id] = its header's y in the page

local function layout(width: number, height: number)
	tabs.frame.Position, tabs.frame.Size = UDim2.fromOffset(0, 0), UDim2.fromOffset(width - 160, 54)
	giftToggle.Position, giftToggle.Size = UDim2.fromOffset(width - 150, 3), UDim2.fromOffset(150, 48)
	giftRow.Position, giftRow.Size = UDim2.fromOffset(0, 60), UDim2.fromOffset(width, 48)
	local top = if giftMode then 112 else 60
	list.Position, list.Size = UDim2.fromOffset(0, top), UDim2.fromOffset(width, math.max(100, height - top - 32))
	infoPanel.Position, infoPanel.Size = UDim2.fromOffset(20, top + 10), UDim2.fromOffset(math.max(200, width - 40), math.max(100, height - top - 52))
	feedback.Position, feedback.Size = UDim2.fromOffset(0, height - 28), UDim2.fromOffset(width, 28)
	-- The cards are laid out for the page's size: a new width (or a short window) rebuilds them.
	local short = height < 420
	if width ~= listWidth or short ~= compact then
		listWidth, compact = width, short
		if window and window.IsOpen() then
			task.defer(refresh)
		end
	end
end

window = ShowcaseKit.Window("ShopWindow", "Shop", {
	width = 900,
	height = 620,
	onLayout = layout,
	onOpen = function()
		say("")
		refresh()
		visitRemote:FireServer("Open", "Robux") -- (analytics only: the shop funnel's visits)
	end,
	onClose = function()
		infoPanel.Visible = false
		visitRemote:FireServer("Close", "Robux")
	end,
})
local content = window.content

-- The page's CanvasPosition is in screen pixels; everything else here is in menu units.
local function pageScale(): number
	local scale = window.panel:FindFirstChildOfClass("UIScale")
	return if scale and scale.Scale > 0 then scale.Scale else 1
end
local function scrollTo(unitsY: number)
	list.CanvasPosition = Vector2.new(0, math.max(0, unitsY) * pageScale())
end

-- The jump buttons: each scrolls the page to its section.
tabs = UIKit.Tabs(content, MonetizationConfig.Shop.Tabs, function(id)
	if sectionTop[id] then
		scrollTo(sectionTop[id])
	end
end, 140)

giftToggle = UIKit.Button(content, "GiftToggle", "GIFT: OFF", "Done", 24)

-- The gift row: who the products are for (players in this server).
giftRow = Instance.new("ScrollingFrame")
giftRow.Name = "GiftRow"
giftRow.BackgroundTransparency = 1
giftRow.BorderSizePixel = 0
giftRow.ScrollBarThickness = 4
giftRow.ScrollingDirection = Enum.ScrollingDirection.X
giftRow.AutomaticCanvasSize = Enum.AutomaticSize.X
giftRow.CanvasSize = UDim2.new()
giftRow.Visible = false
giftRow.Parent = content
local giftLayout = Instance.new("UIListLayout")
giftLayout.FillDirection = Enum.FillDirection.Horizontal
giftLayout.Padding = UDim.new(0, 8)
giftLayout.SortOrder = Enum.SortOrder.LayoutOrder
giftLayout.VerticalAlignment = Enum.VerticalAlignment.Center
giftLayout.Parent = giftRow

-- The page: sections and cards placed by hand (no layout object), straight on the dark window.
list = UIKit.Scroll(content, "List")
list.BackgroundTransparency = 1
list.ScrollBarThickness = 10
list.AutomaticCanvasSize = Enum.AutomaticSize.None
local listLayout = list:FindFirstChildOfClass("UIListLayout")
if listLayout then
	listLayout:Destroy()
end
local listStroke = list:FindFirstChildOfClass("UIStroke")
if listStroke then
	listStroke.Enabled = false
end

-- The INFO panel of a paid random item: its description and every chance, over the page.
infoPanel = ShowcaseKit.Panel(content, "InfoPanel")
infoPanel.Visible = false
infoPanel.ZIndex = 20
infoText = UIKit.Label(infoPanel, "Text", "", 22, nil, true)
infoText.Position, infoText.Size = UDim2.new(0, 20, 0, 16), UDim2.new(1, -40, 1, -84)
infoText.TextYAlignment = Enum.TextYAlignment.Top
infoText.ZIndex = 21
local infoClose = UIKit.Button(infoPanel, "CloseInfo", "CLOSE", "Done", 22)
infoClose.Position, infoClose.Size = UDim2.new(1, -150, 1, -60), UDim2.fromOffset(130, 46)
infoClose.ZIndex = 21
infoClose.Activated:Connect(function()
	infoPanel.Visible = false
end)

feedback = UIKit.Label(content, "Feedback", "", 22, Colors.Muted)
feedback.TextXAlignment = Enum.TextXAlignment.Center

function say(text: string, color: Color3?)
	feedback.Text = text
	feedback.TextColor3 = color or Colors.Muted
end

-- The jump button of the section the page is scrolled to lights up.
local function updateJump()
	local current, best = nil, -math.huge
	for id, y in sectionTop do
		if y <= list.CanvasPosition.Y / pageScale() + 40 and y > best then
			current, best = id, y
		end
	end
	if current and tabs.selected ~= current then
		tabs.Select(current)
	end
end
list:GetPropertyChangedSignal("CanvasPosition"):Connect(updateJump)

-- Cards ------------------------------------------------------------------------------------------

local function showInfo(entry)
	local lines = { entry.Name, "" }
	if entry.Description then
		table.insert(lines, entry.Description)
		table.insert(lines, "")
	end
	table.insert(lines, "Chances:")
	for _, odd in entry.Odds or {} do
		table.insert(lines, `{odd.Name}: {string.format("%.2f", odd.Chance * 100)}%`)
	end
	infoText.Text = table.concat(lines, "\n")
	infoPanel.Visible = true
	visitRemote:FireServer("Info", "Robux", entry.Key)
end

local function clearPage()
	table.clear(sectionTop)
	for _, child in list:GetChildren() do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
end

local function send(action: string, key: string, recipient: number?)
	if busy then
		return
	end
	busy = true
	say("...")
	local ok, reply = pcall(function()
		return remote:InvokeServer(action, key, recipient)
	end)
	busy = false
	if not ok or type(reply) ~= "table" then
		say("The shop didn't answer. Try again.", Colors.Error)
	elseif reply.ok then
		say(reply.message or "", Colors.Good)
	else
		say(reply.message or "You can't buy that right now.", Colors.Error)
		UIKit.PlaySound("Invalid")
	end
end

-- One colour card at (x, y) in the page: picture, name, a line of detail, INFO for paid random
-- items, and the buy button.
local function card(entry, isPass: boolean, x: number, y: number, width: number, height: number)
	local paletteName = if isPass then PASS_PALETTE else PRODUCT_PALETTE
	local box = ShowcaseKit.Card(list, entry.Key, paletteName)
	box.Position, box.Size = UDim2.fromOffset(x, y), UDim2.fromOffset(width, height)

	local textX = 16
	if type(entry.Icon) == "string" and entry.Icon ~= "" then
		local pictureSize = math.floor(math.min(height + 24, width * 0.38))
		local picture = ShowcaseKit.CardPicture(box, entry.Icon)
		picture.Position, picture.Size = UDim2.fromOffset(-6, -22), UDim2.fromOffset(pictureSize, pictureSize)
		picture.Rotation = -6
		textX = pictureSize - 2
	end
	local textWidth = width - textX - 14
	local title = ShowcaseKit.CardTitle(box, entry.Name, paletteName)
	local withLine = entry.Description ~= nil and not compact
	title.Position, title.Size = UDim2.fromOffset(textX, 8), UDim2.fromOffset(textWidth, if withLine then 50 else height - 82)
	if withLine then
		local line = ShowcaseKit.CardText(box, entry.Description)
		line.Position, line.Size = UDim2.fromOffset(textX, 58), UDim2.fromOffset(textWidth, 40)
		line.TextScaled = true
		local limit = Instance.new("UITextSizeConstraint")
		limit.MinTextSize, limit.MaxTextSize = 11, 18
		limit.Parent = line
	end

	-- the bottom row: [INFO] [ price ]
	local rowY = height - 12 - 54
	local buyX = textX
	if MonetizationConfig.IsPaidRandom(entry) then
		local info = ShowcaseKit.InfoButton(box)
		info.Position, info.Size = UDim2.fromOffset(textX, rowY + 4), UDim2.fromOffset(108, 48)
		info.ZIndex = 6
		info.Activated:Connect(function()
			showInfo(entry)
		end)
		buyX = textX + 118
	end
	local button, setPrice = ShowcaseKit.BuyButton(box)
	button.Position, button.Size = UDim2.fromOffset(buyX, rowY), UDim2.fromOffset(width - buyX - 14, 56)
	button.ZIndex = 6

	local owned = isPass and localPlayer:GetAttribute("Owns_" .. entry.Key) == true
	local gifting = giftMode and not isPass
	local id = if gifting then entry.GiftId else entry.Id
	local live = if gifting then MonetizationConfig.IsGiftLive(entry) else MonetizationConfig.IsLive(entry)
	if owned then
		ShowcaseKit.Sticker(box, "OWNED", "Gold")
	elseif not live then
		ShowcaseKit.Sticker(box, "NO ID YET", "Locked") -- (Studio only: live games never show these)
	end

	local function showPrice(price: number)
		if button.Parent then
			setPrice("Buy", if gifting and giftTarget then `GIFT {price}` else tostring(price), true)
		end
	end
	if owned then
		setPrice("Gold", "OWNED")
	elseif giftMode and isPass then
		setPrice("Done", "CAN'T GIFT")
	elseif gifting and not live and not IS_STUDIO then
		setPrice("Done", "NO GIFTING")
	else
		local fallback = entry.ExpectedPrice
		showPrice(if live then PriceCache.Get(id, if isPass then Enum.InfoType.GamePass else Enum.InfoType.Product, fallback, showPrice) else fallback)
	end

	button.Activated:Connect(function()
		if owned then
			say(`You already own {entry.Name}.`)
		elseif isPass then
			if giftMode then
				say("Game passes can't be gifted. Turn GIFT off to buy one.", Colors.Error)
			else
				send("BuyPass", entry.Key)
			end
		elseif giftMode then
			if not giftTarget or giftTarget.Parent ~= Players then
				say("Pick who the gift is for first.", Colors.Error)
			else
				send("Gift", entry.Key, giftTarget.UserId)
			end
		else
			send("Buy", entry.Key)
		end
	end)
end

-- The gift row ---------------------------------------------------------------------------------

local function refreshGiftRow()
	for _, child in giftRow:GetChildren() do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
	if giftTarget and giftTarget.Parent ~= Players then
		giftTarget = nil
	end
	local label = UIKit.Label(giftRow, "GiftTo", "GIFT TO:", 22)
	label.LayoutOrder = 0
	label.Size = UDim2.fromOffset(100, 40)
	local others = 0
	for order, player in Players:GetPlayers() do
		if player ~= localPlayer then
			others += 1
			local button = UIKit.Button(giftRow, "Player_" .. player.UserId, player.DisplayName, if player == giftTarget then "Gift" else "Done", 22)
			button.LayoutOrder = order
			button.Size = UDim2.fromOffset(160, 42)
			button.Activated:Connect(function()
				giftTarget = player
				refresh()
			end)
		end
	end
	if others == 0 then
		local none = UIKit.Label(giftRow, "Nobody", "No one else is in this server yet", 20, Colors.Muted)
		none.LayoutOrder = 1
		none.Size = UDim2.fromOffset(360, 40)
	end
end

-- Drawing ------------------------------------------------------------------------------------------

function refresh()
	UIKit.SetButton(giftToggle, if giftMode then "GIFT: ON" else "GIFT: OFF", if giftMode then "Gift" else "Done")
	giftRow.Visible = giftMode
	if giftMode then
		refreshGiftRow()
	end
	window.Layout()
	local keepScroll = list.CanvasPosition

	clearPage()
	-- Wide pages get two cards a row; phones one.
	local inner = listWidth - 26 -- the page's padding and scroll bar
	local columns = if inner >= 680 then 2 else 1
	local cardWidth = math.floor((inner - (columns - 1) * CARD_GAP) / columns)
	local cardHeight = if compact then COMPACT_CARD_HEIGHT else CARD_HEIGHT
	local headerHeight = if compact then 46 else HEADER_HEIGHT
	local y, any = 0, false
	for _, tab in MonetizationConfig.Shop.Tabs do
		local items = sectionItems(tab.Id)
		local jump = tabs.buttons[tab.Id]
		if jump then
			jump.Visible = #items > 0
		end
		if #items > 0 then
			any = true
			sectionTop[tab.Id] = y
			local header = ShowcaseKit.SectionHeader(list, tab.Name)
			header.Position, header.Size = UDim2.fromOffset(0, y), UDim2.fromOffset(inner, headerHeight - 8)
			y += headerHeight + 18 -- (room for the first row's pictures)
			for index, item in items do
				local column = (index - 1) % columns
				local row = (index - 1) // columns
				card(item.entry, item.isPass, column * (cardWidth + CARD_GAP), y + row * (cardHeight + ROW_GAP), cardWidth, cardHeight)
			end
			y += math.ceil(#items / columns) * (cardHeight + ROW_GAP) + 4
		end
	end
	giftToggle.Visible = any
	if not any then
		local empty = UIKit.Label(list, "Empty", "Nothing for sale yet.", 30, Colors.Muted)
		empty.TextXAlignment = Enum.TextXAlignment.Center
		empty.Position, empty.Size = UDim2.fromOffset(0, 40), UDim2.fromOffset(inner, 60)
		y = 120
	end
	list.CanvasSize = UDim2.fromOffset(0, y + 10)
	list.CanvasPosition = keepScroll
	updateJump()
end

giftToggle.Activated:Connect(function()
	giftMode = not giftMode
	say(if giftMode then "Gifts: pick a player, then a product." else "")
	refresh()
end)
for _, pass in MonetizationConfig.Passes do
	localPlayer:GetAttributeChangedSignal("Owns_" .. pass.Key):Connect(function()
		if window.IsOpen() then
			refresh()
		end
	end)
end
local function playersChanged()
	if window.IsOpen() and giftMode then
		refresh()
	end
end
Players.PlayerAdded:Connect(playersChanged)
Players.PlayerRemoving:Connect(function(player)
	if player == giftTarget then
		giftTarget = nil
	end
	task.defer(playersChanged)
end)
localPlayer:GetAttributeChangedSignal("PaidRandomItems"):Connect(function()
	if window.IsOpen() then
		refresh()
	end
end)

-- Purchase notices -----------------------------------------------------------------------------

local _, noticeRoot = UIKit.Screen("PurchaseNotices", 40)
local banner = UIKit.Label(noticeRoot, "Notice", "", 30, Colors.Good)
banner.AnchorPoint = Vector2.new(0.5, 0)
banner.Position, banner.Size = UDim2.new(0.5, 0, 0, 90), UDim2.fromOffset(700, 44)
banner.TextXAlignment = Enum.TextXAlignment.Center
banner.Visible = false
local noticeCount = 0

local NOTICE_TEXT = {
	Purchased = function(item, other)
		return `Thanks! You got {other or item}.`
	end,
	GiftSent = function(item, other)
		return `Your {item} gift is on its way to {other}.`
	end,
	GiftReceived = function(item, other)
		return `{other} sent you {item}!`
	end,
	PassOwned = function(item)
		return `You own {item} now!`
	end,
}

noticeRemote.OnClientEvent:Connect(function(payload)
	local format = type(payload) == "table" and NOTICE_TEXT[payload.Kind]
	if not format then
		return
	end
	local text = format(tostring(payload.Item or ""), if payload.Other ~= nil then tostring(payload.Other) else nil)
	if window.IsOpen() then
		say(text, Colors.Good)
		return
	end
	noticeCount += 1
	local mine = noticeCount
	banner.Text = text
	banner.Visible = true
	task.delay(NOTICE_SECONDS, function()
		if noticeCount == mine then
			banner.Visible = false
		end
	end)
end)

UIKit.MenuButton("Shop").Activated:Connect(window.Toggle)
