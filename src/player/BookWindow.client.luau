-- The Creature Book (docs/GAME_DESIGN.md, "The Creature Book"): a page per rarity plus the Golden page.
-- Each entry shows the creature (a dark silhouette until rescued, with a hint where to look), its first
-- layer, how many were rescued and a "New!" badge until viewed; each page shows its permanent reward
-- and whether it's complete; the title shows the completion %. The first rescue of a creature opens the
-- book on its page and the silhouette fills in with colour. Viewing a page clears its New! badges
-- (PetRequest "MarkSeen"). The rewards themselves are worked out by the server (EconomyRules.BookBonus).
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local EconomyRules = require(ReplicatedStorage.EconomyRules)
local IceLooks = require(ReplicatedStorage.IceLooks)
local LayerConfig = require(ReplicatedStorage.LayerConfig)
local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)
local ClientState = require(script.Parent.ClientState)
local PetViewport = require(script.Parent.PetViewport)

local remote = ReplicatedStorage:WaitForChild("PetRequest") :: RemoteFunction
local Colors = UIKit.Colors

local TILE = 200
local TAB_WIDTH, TAB_GAP = 150, 8
-- On the smallest phones the full names don't fit: the tabs shrink and take these short names (the
-- header line under them still names the page in full).
local SHORT_NAMES = { Common = "COM", Uncommon = "UNC", Rare = "RARE", Epic = "EPIC", Legendary = "LEG", Mythic = "MYTH", Golden = "GOLD" }
local PAGES = {}
for _, page in CreatureConfig.Book do
	table.insert(PAGES, { Id = page.Page, Name = string.upper(page.Page), Width = TAB_WIDTH })
end
local SHORT_BELOW = 120 -- tabs narrower than this take the short names (full ones would shrink too small)

-- Every tab fits on the row: as wide as TAB_WIDTH, narrower when the window is (then short names).
local function fitTabs(tabsController, width: number)
	local each = math.clamp(math.floor((width - 8) / #PAGES) - TAB_GAP, 64, TAB_WIDTH)
	local short = each < SHORT_BELOW
	for _, tab in PAGES do
		local button = tabsController.buttons[tab.Id]
		if button then
			button.Size = UDim2.new(0, each, 1, -8)
			UIKit.SetButton(button, if short then SHORT_NAMES[tab.Id] or string.sub(tab.Name, 1, 4) else tab.Name)
		end
	end
end

local page = "Common"
local tabs, header, rewardLine, grid, gridLayout
local entries = {} -- [creature id] = tile, for the current page
local reveal = nil -- a creature id whose silhouette fills in when shown

local window = ShowcaseKit.Window("BookWindow", "Creature Book", {
	width = 980,
	height = 660,
	onLayout = function(width, height)
		tabs.frame.Position, tabs.frame.Size = UDim2.fromOffset(0, 0), UDim2.fromOffset(width, 56)
		fitTabs(tabs, width)
		header.Position, header.Size = UDim2.fromOffset(0, 62), UDim2.fromOffset(width, 30)
		rewardLine.Position, rewardLine.Size = UDim2.fromOffset(0, 94), UDim2.fromOffset(width, 28)
		grid.Position, grid.Size = UDim2.fromOffset(0, 128), UDim2.fromOffset(width, height - 128)
	end,
})
local content = window.content

local render
tabs = UIKit.Tabs(content, PAGES, function(id)
	page = id
	render()
end)
tabs.Select(page)
header = UIKit.Label(content, "Header", "", 26, Colors.Gold)
header.TextXAlignment = Enum.TextXAlignment.Center
rewardLine = UIKit.Label(content, "Reward", "", 22, Colors.Muted)
rewardLine.TextXAlignment = Enum.TextXAlignment.Center
grid, gridLayout = UIKit.Scroll(content, "Grid", "Grid")
gridLayout.CellSize = UDim2.fromOffset(TILE, TILE + 60)

local function rewardText(reward): string
	local parts = {}
	if reward.CrystalBonus then
		table.insert(parts, `+{math.floor(reward.CrystalBonus * 100 + 0.5)}% crystals`)
	end
	if reward.NameTagBorder then
		table.insert(parts, `a {string.lower(reward.NameTagBorder)} name-tag border`)
	end
	if reward.Trail then
		table.insert(parts, `an {string.lower(reward.Trail)} trail`)
	end
	if reward.Title then
		table.insert(parts, `the title "{reward.Title}"`)
	end
	if reward.PickSkin then
		table.insert(parts, `a {string.lower(reward.PickSkin)} ice pick skin`)
	end
	return table.concat(parts, " and ")
end

-- The whole book's completion: every creature found, and every Golden version made.
local function completion(data): number
	local found, total = 0, 0
	for _, bookPage in EconomyRules.BookPages(data) do
		found += bookPage.Found
		total += bookPage.Count
	end
	return if total > 0 then found / total else 0
end

local function creaturesOn(pageId: string)
	local list = {}
	for _, creature in CreatureConfig.Creatures do
		if pageId == "Golden" or creature.Rarity == pageId then
			table.insert(list, creature)
		end
	end
	return list
end

function render()
	local data = ClientState.Data()
	if not data or not window.IsOpen() then
		return
	end
	for _, tile in entries do
		tile.card:Destroy()
	end
	table.clear(entries)
	local pages = EconomyRules.BookPages(data)
	local current
	for _, bookPage in pages do
		if bookPage.Page == page then
			current = bookPage
		end
	end
	header.Text = `{current.Found}/{current.Count} found on this page · book {math.floor(completion(data) * 100)}% complete`
	rewardLine.Text = (if current.Complete then "✔ Reward earned: " else "Complete the page: ") .. rewardText(current.Reward)
	rewardLine.TextColor3 = if current.Complete then Colors.Good else Colors.Muted

	local viewedNew = {}
	for order, creature in creaturesOn(page) do
		local golden = page == "Golden"
		local found = if golden then data.BookGolden[creature.Id] == true else (data.BookSeen[creature.Id] or 0) > 0
		local card = ShowcaseKit.Card(grid, creature.Id, if found then (if golden then "Gold" else "Blue") else "Locked")
		card.LayoutOrder = order
		local holder = Instance.new("Frame")
		holder.BackgroundTransparency = 1
		holder.Position, holder.Size = UDim2.fromOffset(10, 6), UDim2.new(1, -20, 0, TILE - 34)
		holder.ZIndex = 4
		holder.Parent = card
		local look = if not found then "Silhouette" elseif golden then "Golden" else "Normal"
		local revealing = reveal == creature.Id and found and not golden
		local view = PetViewport.new(holder, creature.Id, if revealing then "Silhouette" else look)
		local name = UIKit.Label(card, "Name", if found then creature.Name else "???", 22, nil, true)
		name.Position, name.Size = UDim2.new(0, 8, 1, -84), UDim2.new(1, -16, 0, 28)
		name.TextScaled = true
		name.TextXAlignment = Enum.TextXAlignment.Center
		name.ZIndex = 6
		local layer = LayerConfig.Get(creature.FirstLayer)
		local detail
		if golden then
			detail = if found then "Golden version made" else "Combine 5 into a Golden one"
		elseif found then
			detail = `Rescued x{data.BookSeen[creature.Id]} · from {layer.Name}`
		else
			detail = `Found in {layer.Name} or deeper`
		end
		local line = UIKit.Label(card, "Detail", detail, 16, if found then IceLooks.RarityColors[creature.Rarity] else Colors.Muted, true)
		line.Position, line.Size = UDim2.new(0, 8, 1, -54), UDim2.new(1, -16, 0, 46)
		line.TextScaled = true
		line.TextXAlignment = Enum.TextXAlignment.Center
		line.ZIndex = 6
		if not golden and table.find(data.BookNew, creature.Id) then
			ShowcaseKit.Sticker(card, "NEW!", "Locked")
			table.insert(viewedNew, creature.Id)
		end
		entries[creature.Id] = { card = card, view = view }
		if revealing then
			-- the first-rescue moment: the silhouette fills in with colour
			task.delay(0.9, function()
				if view.frame.Parent then
					view:SetLook("Normal")
					UIKit.PlaySound("BookReveal")
				end
			end)
		end
	end
	reveal = nil
	if #viewedNew > 0 then
		task.spawn(function()
			pcall(function()
				remote:InvokeServer("MarkSeen", viewedNew)
			end)
		end)
	end
end

-- The HUD button shows the completion.
local bookButton = UIKit.MenuButton("Book")
local function label()
	local data = ClientState.Data()
	local visual = bookButton:FindFirstChild("Visual")
	local text = visual and visual:FindFirstChild("Label", true)
	if data and text and text:IsA("TextLabel") then
		text.Text = `BOOK {math.floor(completion(data) * 100)}%`
	end
end

ClientState.Changed(function()
	label()
end)
bookButton.Activated:Connect(function()
	window.Toggle()
	render()
end)

-- The first rescue of a creature: after the rescue banner, the book flies open on its page.
ClientState.Event("Rescue", function(payload)
	if not payload.First then
		return
	end
	local creature = CreatureConfig.Get(payload.CreatureId)
	if not creature then
		return
	end
	task.wait(3.2)
	page = creature.Rarity
	tabs.Select(page)
	reveal = creature.Id
	if not window.IsOpen() then
		UIKit.CloseAll()
		window.Open()
	end
	render()
end)
