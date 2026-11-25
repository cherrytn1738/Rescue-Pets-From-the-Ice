-- The Upgrades panel (docs/GAME_DESIGN.md, "Screens" and "Upgrades in detail"): a grid of square
-- upgrade tiles sorted by price, dimmed until affordable, with an Owned tab. The list is the next tier
-- of each upgrade line (EconomyRules.UpgradeList); the server checks every unlock rule and price
-- (BuyUpgrade). Each tile shows its icon (UITheme.Icons, rendered from the game's models: the pick tier,
-- the building with an up-arrow badge, Frost Touch, the ice upgrades); without the picture, its kind's
-- emoji. The bottom line shows your crystals, or for a few seconds the answer to a purchase.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EconomyRules = require(ReplicatedStorage.EconomyRules)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)
local UpgradeConfig = require(ReplicatedStorage.UpgradeConfig)
local ClientState = require(script.Parent.ClientState)

local remote = ReplicatedStorage:WaitForChild("BuyUpgrade") :: RemoteFunction
local Colors = UIKit.Colors

local TILE = 196
local KIND_LOOK = {
	IcePick = { Emoji = "⛏️", Palette = "Teal" },
	FrostTouch = { Emoji = "❄️", Palette = "Aurora" },
	Building = { Emoji = "🏗️", Palette = "Orange" },
	Ice = { Emoji = "💎", Palette = "Purple" },
}

local MESSAGE_SECONDS = 3
local messageUntil = 0

-- The icon key (UITheme.Icons) for an upgrade, and whether the up-arrow badge goes on it.
local function iconFor(upgrade): (string, boolean)
	if upgrade.Kind == "IcePick" then
		return "Pick" .. tostring(upgrade.Tier), false
	elseif upgrade.Kind == "FrostTouch" then
		return "FrostTouch", false
	elseif upgrade.Kind == "Building" then
		return "Building_" .. tostring(upgrade.Building), true
	end
	return tostring(upgrade.Upgrade), false
end

local view = "Shop"
local tabs, grid, gridLayout, feedback
local tiles = {}
local busy = false

local window = ShowcaseKit.Window("UpgradesWindow", "Upgrades", {
	width = 940,
	height = 640,
	onLayout = function(width, height)
		tabs.frame.Position, tabs.frame.Size = UDim2.fromOffset(0, 0), UDim2.fromOffset(width, 56)
		feedback.Position, feedback.Size = UDim2.fromOffset(0, height - 30), UDim2.fromOffset(width, 28)
		grid.Position, grid.Size = UDim2.fromOffset(0, 64), UDim2.fromOffset(width, height - 100)
	end,
})
local content = window.content

local refresh
tabs = UIKit.Tabs(content, { { Id = "Shop", Name = "UPGRADES", Width = 190 }, { Id = "Owned", Name = "OWNED" } }, function(id)
	view = id
	refresh()
end)
tabs.Select("Shop")
feedback = UIKit.Label(content, "Feedback", "", 22, Colors.Gold)
feedback.TextXAlignment = Enum.TextXAlignment.Center
grid, gridLayout = UIKit.Scroll(content, "Grid", "Grid")
gridLayout.CellSize = UDim2.fromOffset(TILE, TILE + 30)

local function buy(upgradeId: string)
	if busy then
		return
	end
	busy = true
	local ok, reply = pcall(function()
		return remote:InvokeServer(upgradeId)
	end)
	busy = false
	messageUntil = os.clock() + MESSAGE_SECONDS
	if ok and type(reply) == "table" then
		feedback.Text = tostring(reply.message or "")
		feedback.TextColor3 = if reply.ok then Colors.Good else Colors.Error
		UIKit.PlaySound(if reply.ok then "BuyUpgrade" else "Invalid")
		-- the tile flashes (docs/GAME_DESIGN.md: "Buying flashes the card"; the station puffs: BuildMoments)
		local tile = reply.ok and tiles[upgradeId]
		if tile and tile.card.Parent then
			ShowcaseKit.SetCardPalette(tile.card, "Ice")
			task.delay(0.25, function()
				if tile.card.Parent then
					ShowcaseKit.SetCardPalette(tile.card, tile.palette)
				end
			end)
		end
	else
		feedback.Text = "The server didn't answer. Try again."
		feedback.TextColor3 = Colors.Error
	end
end

local function tileFor(upgrade)
	local tile = tiles[upgrade.Id]
	if tile then
		return tile
	end
	local look = KIND_LOOK[upgrade.Kind]
	local card = ShowcaseKit.Card(grid, upgrade.Id, look.Palette)
	local key, badged = iconFor(upgrade)
	local image = UIKit.IconImage(key)
	local icon
	if image then
		icon = Instance.new("ImageLabel")
		icon.Name = "Icon"
		icon.BackgroundTransparency = 1
		icon.Image = image
		icon.ScaleType = Enum.ScaleType.Fit
		icon.AnchorPoint = Vector2.new(0.5, 0)
		icon.Position, icon.Size = UDim2.new(0.5, 0, 0, 4), UDim2.fromOffset(62, 62)
		icon.Parent = card
		local badgeImage = badged and UIKit.IconImage("UpgradeBadge")
		if badgeImage then
			local badge = Instance.new("ImageLabel")
			badge.Name = "Badge"
			badge.BackgroundTransparency = 1
			badge.Image = badgeImage
			badge.ScaleType = Enum.ScaleType.Fit
			badge.AnchorPoint = Vector2.new(1, 1)
			badge.Position, badge.Size = UDim2.fromScale(1.08, 1.04), UDim2.fromScale(0.5, 0.5)
			badge.ZIndex = 6
			badge.Parent = icon
		end
	else
		icon = UIKit.Label(card, "Icon", look.Emoji, 52)
		icon.Position, icon.Size = UDim2.fromOffset(0, 8), UDim2.new(1, 0, 0, 56)
		icon.TextXAlignment = Enum.TextXAlignment.Center
	end
	local name = UIKit.Label(card, "Name", upgrade.Name, 22, nil, true)
	name.Position, name.Size = UDim2.fromOffset(8, 64), UDim2.new(1, -16, 0, 50)
	name.TextXAlignment = Enum.TextXAlignment.Center
	name.TextScaled = true
	local effect = UIKit.Label(card, "Effect", EconomyRules.Describe(upgrade), 16, Colors.Muted, true)
	effect.Position, effect.Size = UDim2.fromOffset(8, 114), UDim2.new(1, -16, 0, 40)
	effect.TextXAlignment = Enum.TextXAlignment.Center
	effect.TextScaled = true
	local button = UIKit.Button(card, "BuyButton", "", "Buy", 22)
	button.Position, button.Size = UDim2.new(0, 10, 1, -62), UDim2.new(1, -20, 0, 52)
	for _, item in { icon, name, effect, button } do
		item.ZIndex = 5
	end
	button.Activated:Connect(function()
		if button.Active then
			buy(upgrade.Id)
		end
	end)
	tile = { card = card, button = button, palette = look.Palette }
	tiles[upgrade.Id] = tile
	return tile
end

function refresh()
	local data = ClientState.Data()
	if not data or not window.IsOpen() then
		return
	end
	if os.clock() >= messageUntil then
		feedback.Text = `You have 💎 {NumberFormat.Short(data.Crystals)} crystals`
		feedback.TextColor3 = Colors.Gold
	end
	for _, tile in tiles do
		tile.card.Visible = false
	end
	if view == "Owned" then
		for order, id in data.Upgrades do
			local upgrade = UpgradeConfig.Get(id)
			if upgrade then
				local tile = tileFor(upgrade)
				tile.card.Visible = true
				tile.card.LayoutOrder = order
				UIKit.SetButton(tile.button, "OWNED", "Gold", false)
				ShowcaseKit.SetCardPalette(tile.card, tile.palette)
			end
		end
		return
	end
	for order, entry in EconomyRules.UpgradeList(data) do
		local upgrade = entry.Upgrade
		local tile = tileFor(upgrade)
		tile.card.Visible = true
		tile.card.LayoutOrder = order
		local affordable = entry.Unlocked and data.Crystals >= upgrade.Cost
		local caption = if entry.Unlocked then "💎 " .. NumberFormat.Short(upgrade.Cost) else tostring(entry.Reason)
		UIKit.SetButton(tile.button, caption, if affordable then "Buy" else "Done", affordable)
		-- dimmed until affordable
		ShowcaseKit.SetCardPalette(tile.card, if affordable then tile.palette else "Locked")
	end
end

ClientState.Changed(function()
	refresh()
end)
UIKit.MenuButton("Upgrades").Activated:Connect(function()
	window.Toggle()
	messageUntil = 0
	refresh()
end)
