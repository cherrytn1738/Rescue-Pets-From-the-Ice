-- The Build panel (docs/GAME_DESIGN.md, "Screens" and "How buildings, upgrades and pets look"):
-- eight building cards with the number owned, the price, damage per second, a bar for its share of
-- building income and the detail pips (0-10); buy x1, x10, x100 or Max. Locked buildings show as "???"
-- until the player is close to affording them; the best building the player can afford now glows gold.
-- Prices come from EconomyRules on the server's display copies; the server checks every purchase
-- (BuyBuilding). Building previews in 3D come with the building art.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local BuildingConfig = require(ReplicatedStorage.BuildingConfig)
local EconomyRules = require(ReplicatedStorage.EconomyRules)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)
local ClientState = require(script.Parent.ClientState)

local remote = ReplicatedStorage:WaitForChild("BuyBuilding") :: RemoteFunction
local Colors = UIKit.Colors

local ROW_HEIGHT = 128
local REVEAL_SHARE = 0.25 -- a locked building shows once the player has this share of its price
local AMOUNTS = { { Id = "1", Name = "x1" }, { Id = "10", Name = "x10" }, { Id = "100", Name = "x100" }, { Id = "Max", Name = "MAX" } }

local amount: any = 1
local tabs, list, feedback
local rows = {}

local window = ShowcaseKit.Window("BuildWindow", "Build", {
	width = 940,
	height = 640,
	onLayout = function(width, height)
		tabs.frame.Position, tabs.frame.Size = UDim2.fromOffset(0, 0), UDim2.fromOffset(width, 56)
		feedback.Position, feedback.Size = UDim2.fromOffset(0, height - 30), UDim2.fromOffset(width, 28)
		list.Position, list.Size = UDim2.fromOffset(0, 64), UDim2.fromOffset(width, height - 100)
		for _, row in rows do
			row.layout(width - 30)
		end
	end,
})
local content = window.content

tabs = UIKit.Tabs(content, AMOUNTS, function(id)
	amount = if id == "Max" then "Max" else tonumber(id)
	local data = ClientState.Data()
	if data then
		for _, row in rows do
			row.refresh(data)
		end
	end
end, 120)
tabs.Select("1")
feedback = UIKit.Label(content, "Feedback", "", 22, Colors.Gold)
feedback.TextXAlignment = Enum.TextXAlignment.Center
list = UIKit.Scroll(content, "List", "List")

local function pips(level: number): string
	return string.rep("★", level) .. string.rep("☆", BuildingConfig.MaxDetailLevel - level)
end

local function revealed(data, order: number, building): boolean
	if (data.Buildings[building.Id] or 0) > 0 or order == 1 then
		return true
	end
	local previous = BuildingConfig.Buildings[order - 1]
	return (data.Buildings[previous.Id] or 0) > 0 or data.Crystals >= building.BaseCost * REVEAL_SHARE
end

local busy = false
for order, building in BuildingConfig.Buildings do
	local card = ShowcaseKit.Card(list, building.Id, "Blue")
	card.LayoutOrder = order
	card.Size = UDim2.new(1, -6, 0, ROW_HEIGHT)
	local title = UIKit.Label(card, "Name", building.Name, 34)
	local detail = UIKit.Label(card, "Detail", "", 20, Colors.Muted)
	local pipLabel = UIKit.Label(card, "Pips", "", 18, Colors.Gold)
	local bar, setBar = UIKit.ProgressBar(card, "Share")
	local buy = UIKit.Button(card, "BuyButton", "", "Buy", 26)
	for _, item in { title, detail, pipLabel, bar, buy } do
		item.ZIndex = 5
	end

	local row = {}
	function row.layout(width: number)
		local right = 210
		title.Position, title.Size = UDim2.fromOffset(18, 10), UDim2.fromOffset(width * 0.5, 40)
		detail.Position, detail.Size = UDim2.fromOffset(18, 52), UDim2.fromOffset(width - right - 40, 26)
		pipLabel.Position, pipLabel.Size = UDim2.fromOffset(18, 84), UDim2.fromOffset(width * 0.45, 26)
		bar.Position, bar.Size = UDim2.fromOffset(width * 0.5, 86), UDim2.fromOffset(math.max(80, width * 0.5 - right - 10), 26)
		buy.Position, buy.Size = UDim2.fromOffset(width - right + 6, 18), UDim2.fromOffset(right - 16, ROW_HEIGHT - 36)
	end
	function row.refresh(data, best: string?, totalDps: number?)
		local owned = data.Buildings[building.Id] or 0
		local show = revealed(data, order, building)
		local count, cost = EconomyRules.BuildingPurchase(data, building.Id, amount)
		local dps = EconomyRules.BuildingDps(data, building.Id)
		local each = building.DamagePerSecond * (2 ^ EconomyRules.BuildingUpgradeCount(data, building.Id))
		local level = EconomyRules.DetailLevel(data, building.Id)
		title.Text = if show then building.Name else "???"
		detail.Text = if show
			then `Owned {owned} · {NumberFormat.Rate(each)} dmg/s each · {building.Breaks}`
			else "Keep earning crystals to find out..."
		pipLabel.Text = if show then pips(level) .. (if level >= BuildingConfig.MaxDetailLevel then "  MASTERWORK" else "") else ""
		bar.Visible = show and owned > 0
		local share = if totalDps and totalDps > 0 then dps / totalDps else 0
		setBar(share, `{math.floor(share * 100 + 0.5)}% of building income`)
		local affordable = data.Crystals >= cost
		UIKit.SetButton(buy, (if count > 1 then `x{count}\n` else "") .. "💎 " .. NumberFormat.Short(cost),
			if affordable and show then "Buy" else "Done", affordable and show)
		ShowcaseKit.SetCardPalette(card, if not show then "Locked" elseif best == building.Id then "Gold" elseif owned > 0 then "Blue" else "Slate")
	end
	rows[building.Id] = row

	buy.Activated:Connect(function()
		if busy or not buy.Active then
			return
		end
		busy = true
		local ok, reply = pcall(function()
			return remote:InvokeServer(building.Id, amount)
		end)
		busy = false
		if ok and type(reply) == "table" then
			feedback.Text = tostring(reply.message or "")
			feedback.TextColor3 = if reply.ok then Colors.Good else Colors.Error
			UIKit.PlaySound(if reply.ok then "BuyBuilding" else "Invalid")
			if reply.ok then
				-- the card flashes
				ShowcaseKit.SetCardPalette(card, "Ice")
			end
		else
			feedback.Text = "The server didn't answer. Try again."
			feedback.TextColor3 = Colors.Error
		end
	end)
end

local function refreshAll(data)
	if not window.IsOpen() then
		return
	end
	-- the "next affordable" building: the most expensive one the player can buy right now
	local best = nil
	for _, building in BuildingConfig.Buildings do
		if data.Crystals >= BuildingConfig.Cost(building, data.Buildings[building.Id] or 0) then
			best = building.Id
		end
	end
	local total = EconomyRules.TotalBuildingDps(data)
	for _, row in rows do
		row.refresh(data, best, total)
	end
end

ClientState.Changed(refreshAll)
UIKit.MenuButton("Build").Activated:Connect(function()
	window.Toggle()
	feedback.Text = ""
	local data = ClientState.Data()
	if data then
		refreshAll(data)
	end
end)
