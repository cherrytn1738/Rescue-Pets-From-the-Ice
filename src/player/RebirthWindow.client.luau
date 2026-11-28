-- The Rebirth screen (docs/GAME_DESIGN.md, "Rebirth" and "Screens"): pictures more than words. A rebirth badge over the
-- corner; Before -> After cards for the crystal bonus from Frost Cores, with the Frost Cores this rebirth gives shown big
-- on the arrow; a smaller Before -> After for the rank (badge and name), with the next unlock as an icon and "at
-- Rebirth N"; one red "Resets ..." line with an icon for each; a "Kept" row of icons with green ticks; the block level
-- against the rebirth level as a bar; a big green REBIRTH button, greyed until the bar is full (pressed twice: SURE?).
-- Every number comes from the player's server-published data (ClientState) and RebirthConfig; the server does the
-- rebirth (RebirthRequest).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local NumberFormat = require(ReplicatedStorage.NumberFormat)
local RebirthConfig = require(ReplicatedStorage.RebirthConfig)
local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)
local Banners = require(script.Parent.Banners)
local ClientState = require(script.Parent.ClientState)

local remote = ReplicatedStorage:WaitForChild("RebirthRequest") :: RemoteFunction
local Colors = UIKit.Colors
local CORE_BLUE = Color3.fromRGB(140, 230, 255)

local sure = false
local parts = {} -- every piece, by name (built below, placed by layout)

local function commas(value: number): string
	if value >= 1e6 then
		return NumberFormat.Short(value)
	end
	local text = tostring(math.floor(value))
	while true do
		local changed
		text, changed = string.gsub(text, "^(-?%d+)(%d%d%d)", "%1,%2")
		if changed == 0 then
			return text
		end
	end
end

local function rankIconKey(rebirths: number): string
	local rank = RebirthConfig.RankFor(rebirths)
	return if rank then "Rank" .. rank.Rank else "Rank0"
end

-- The first rank at or after `fromRebirth` that opens something (a pet slot or a layer), or nil.
local function nextUnlock(fromRebirth: number)
	for _, rank in RebirthConfig.Ranks do
		if rank.Rank >= fromRebirth and (rank.PetSlot or rank.OpensLayer) then
			return rank
		end
	end
	return nil
end

local window
window = ShowcaseKit.Window("RebirthWindow", "Rebirth", {
	cornerIcon = UIKit.IconImage("RebirthBadge"),
	width = 800,
	height = 640,
	-- gamepad: start on the close button, so mashing A can't rebirth by accident (REBIRTH needs two presses)
	firstSelection = function()
		return window and window.panel:FindFirstChild("Close")
	end,
	onLayout = function(width, height)
		local compact = height < 400
		local p = parts
		local headerHeight = if compact then 0 else 30
		local cardHeight = if compact then 84 else 124
		local rankHeight = if compact then 50 else 74
		local rowHeight = if compact then 38 else 46
		local keptHeight = if compact then 44 else 58
		local barHeight = if compact then 40 else 42
		local buttonHeight = if compact then 54 else 72
		-- spread any spare height between the rows
		local used = headerHeight + cardHeight + rankHeight + rowHeight + keptHeight
			+ (if compact then math.max(barHeight, buttonHeight) else barHeight + buttonHeight)
		local rows = if compact then 4 else 6
		local gap = math.clamp((height - used) / rows, 4, 16)
		local y = 0

		-- Before -> After
		local middle = if compact then 160 else 180
		local cardWidth = (width - middle) / 2
		p.BeforeHeader.Visible, p.AfterHeader.Visible = not compact, not compact
		p.BeforeHeader.Position, p.BeforeHeader.Size = UDim2.fromOffset(0, y), UDim2.fromOffset(cardWidth, headerHeight)
		p.AfterHeader.Position, p.AfterHeader.Size = UDim2.fromOffset(cardWidth + middle, y), UDim2.fromOffset(cardWidth, headerHeight)
		y += headerHeight
		for _, side in { { p.BeforeCard, 0 }, { p.AfterCard, cardWidth + middle } } do
			local card, x = side[1], side[2]
			card.Position, card.Size = UDim2.fromOffset(x + cardWidth / 2, y + cardHeight / 2), UDim2.fromOffset(cardWidth, cardHeight)
			local icon = card.Core
			local iconSize = cardHeight * 0.86
			icon.Position, icon.Size = UDim2.fromOffset(cardHeight * 0.5, cardHeight / 2), UDim2.fromOffset(iconSize, iconSize)
			local textLeft = cardHeight * 0.92
			card.Value.Position, card.Value.Size = UDim2.fromOffset(textLeft, cardHeight * 0.1), UDim2.fromOffset(cardWidth - textLeft - 10, cardHeight * 0.52)
			card.Unit.Position, card.Unit.Size = UDim2.fromOffset(textLeft, cardHeight * 0.6), UDim2.fromOffset(cardWidth - textLeft - 10, cardHeight * 0.3)
		end
		-- the arrow, with the Frost Cores this rebirth gives above it
		local mid = cardWidth + middle / 2
		local arrowSize = if compact then 58 else 70
		p.Arrow.Position, p.Arrow.Size = UDim2.fromOffset(mid, y + cardHeight * 0.68), UDim2.fromOffset(arrowSize, arrowSize)
		p.Gain.Position, p.Gain.Size = UDim2.fromOffset(mid, y + cardHeight * 0.22), UDim2.fromOffset(middle, cardHeight * 0.4)
		y += cardHeight + gap

		-- the rank: badge and name -> the next, then the next unlock
		local rank = p.RankRow
		rank.Position, rank.Size = UDim2.fromOffset(width / 2, y + rankHeight / 2), UDim2.fromOffset(width, rankHeight)
		local badge = rankHeight * 0.84
		local unlockWidth = math.min(250, width * 0.32)
		local pairWidth = (width - unlockWidth - 12) / 2
		local arrow = rankHeight * 0.5
		rank.FromBadge.Position, rank.FromBadge.Size = UDim2.fromOffset(10 + badge / 2, rankHeight / 2), UDim2.fromOffset(badge, badge)
		rank.FromName.Position, rank.FromName.Size = UDim2.fromOffset(14 + badge, 0), UDim2.fromOffset(pairWidth - badge - arrow - 18, rankHeight)
		rank.RankArrow.Position, rank.RankArrow.Size = UDim2.fromOffset(pairWidth - arrow / 2 - 2, rankHeight / 2), UDim2.fromOffset(arrow, arrow)
		rank.ToBadge.Position, rank.ToBadge.Size = UDim2.fromOffset(pairWidth + 6 + badge / 2, rankHeight / 2), UDim2.fromOffset(badge, badge)
		rank.ToName.Position, rank.ToName.Size = UDim2.fromOffset(pairWidth + 10 + badge, 0), UDim2.fromOffset(pairWidth - badge - 14, rankHeight)
		local unlockLeft = width - unlockWidth
		local unlockSize = rankHeight * 0.8
		rank.Divider.Position, rank.Divider.Size = UDim2.fromOffset(unlockLeft - 6, 8), UDim2.fromOffset(3, rankHeight - 16)
		rank.UnlockA.Position, rank.UnlockA.Size = UDim2.fromOffset(unlockLeft + unlockSize / 2 + 2, rankHeight / 2), UDim2.fromOffset(unlockSize, unlockSize)
		rank.UnlockB.Position, rank.UnlockB.Size = UDim2.fromOffset(unlockLeft + unlockSize * 1.5 + 2, rankHeight / 2), UDim2.fromOffset(unlockSize, unlockSize)
		local icons = if rank.UnlockB.Visible then 2 else 1
		rank.UnlockAt.Position = UDim2.fromOffset(unlockLeft + unlockSize * icons + 8, 0)
		rank.UnlockAt.Size = UDim2.fromOffset(unlockWidth - unlockSize * icons - 14, rankHeight)
		y += rankHeight + gap

		-- what resets (one red line, then its icons) and what's kept (KEPT, then icons with ticks): each a centred group
		local function iconRow(row, count, rowHeightNow, labelWidth)
			local size = rowHeightNow * 0.92
			local groupWidth = labelWidth + 10 + count * (size + 6)
			row.Position = UDim2.fromOffset((width - groupWidth) / 2, y)
			row.Size = UDim2.fromOffset(groupWidth, rowHeightNow)
			row.Label.Position, row.Label.Size = UDim2.fromOffset(0, 0), UDim2.fromOffset(labelWidth, rowHeightNow)
			for index = 1, count do
				local icon = row:FindFirstChild("Icon" .. index)
				icon.Position = UDim2.fromOffset(labelWidth + 10 + (size + 6) * (index - 1) + size / 2, rowHeightNow / 2)
				icon.Size = UDim2.fromOffset(size, size)
			end
		end
		iconRow(p.ResetRow, 4, rowHeight, math.min(560, width - 4 * (rowHeight * 0.92 + 6) - 10))
		y += rowHeight + gap
		iconRow(p.KeptRow, 5, keptHeight, if compact then 90 else 120)
		y += keptHeight + gap

		-- the level bar and REBIRTH: stacked, or side by side when short
		if compact then
			local buttonWidth = math.min(260, width * 0.36)
			local barWidth = width - buttonWidth - 20
			p.Bar.Position, p.Bar.Size = UDim2.fromOffset(0, height - buttonHeight / 2 - barHeight / 2), UDim2.fromOffset(barWidth, barHeight)
			p.Confirm.Position, p.Confirm.Size = UDim2.fromOffset(width - buttonWidth / 2, height - buttonHeight / 2), UDim2.fromOffset(buttonWidth, buttonHeight)
		else
			local barWidth = math.min(620, width)
			p.Bar.Position, p.Bar.Size = UDim2.fromOffset((width - barWidth) / 2, height - buttonHeight - gap - barHeight), UDim2.fromOffset(barWidth, barHeight)
			p.Confirm.Position, p.Confirm.Size = UDim2.fromOffset(width / 2, height - buttonHeight / 2), UDim2.fromOffset(math.min(360, width), buttonHeight)
		end
		p.Feedback.Position, p.Feedback.Size = UDim2.fromOffset(0, p.Bar.Position.Y.Offset - 26), UDim2.fromOffset(width, 24)
	end,
})
local content = window.content

-- Before -> After -------------------------------------------------------------------------------------
for _, side in { "Before", "After" } do
	local header = UIKit.Label(content, side .. "Header", string.upper(side), 30)
	header.TextXAlignment = Enum.TextXAlignment.Center
	parts[side .. "Header"] = header
	local card = ShowcaseKit.Card(content, side .. "Card", "Gold")
	card.AnchorPoint = Vector2.new(0.5, 0.5)
	local core = ShowcaseKit.Picture(card, "Core", "FrostCore")
	core.ZIndex = 5
	local value = UIKit.Label(card, "Value", "", 54)
	value.TextXAlignment = Enum.TextXAlignment.Center
	value.ZIndex = 6
	UIKit.FitOneLine(value, 54)
	local unit = UIKit.Label(card, "Unit", "CRYSTALS", 26)
	unit.TextXAlignment = Enum.TextXAlignment.Center
	unit.ZIndex = 6
	UIKit.FitOneLine(unit, 26)
	parts[side .. "Card"] = card
end
parts.Arrow = ShowcaseKit.Picture(content, "Arrow", "ArrowRight")
-- +334 (Frost Cores this rebirth gives): a small core and a big cyan number
local gain = Instance.new("Frame")
gain.Name = "Gain"
gain.BackgroundTransparency = 1
gain.AnchorPoint = Vector2.new(0.5, 0.5)
gain.Parent = content
local gainLayout = Instance.new("UIListLayout")
gainLayout.FillDirection = Enum.FillDirection.Horizontal
gainLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
gainLayout.VerticalAlignment = Enum.VerticalAlignment.Center
gainLayout.Padding = UDim.new(0, 2)
gainLayout.SortOrder = Enum.SortOrder.LayoutOrder
gainLayout.Parent = gain
local gainCore = ShowcaseKit.Picture(gain, "Core", "FrostCore")
gainCore.AnchorPoint = Vector2.new(0, 0)
gainCore.Size = UDim2.fromOffset(40, 40)
local gainText = UIKit.Label(gain, "Cores", "", 44, CORE_BLUE)
gainText.AutomaticSize = Enum.AutomaticSize.X
gainText.Size = UDim2.fromOffset(0, 46)
gainText.TextTruncate = Enum.TextTruncate.None
gainText.LayoutOrder = 2
parts.Gain = gain

-- The rank row: a dark card ------------------------------------------------------------------------
local rankRow = UIKit.Card(content, "RankRow")
rankRow.AnchorPoint = Vector2.new(0.5, 0.5)
parts.RankRow = rankRow
for _, name in { "FromBadge", "ToBadge", "UnlockA", "UnlockB" } do
	ShowcaseKit.Picture(rankRow, name, nil).ZIndex = 3
end
ShowcaseKit.Picture(rankRow, "RankArrow", "ArrowRight").ZIndex = 3
for _, name in { "FromName", "ToName" } do
	local label = UIKit.Label(rankRow, name, "", 30)
	label.ZIndex = 3
	UIKit.FitOneLine(label, 30)
end
local divider = Instance.new("Frame")
divider.Name = "Divider"
divider.BackgroundColor3 = Colors.CardRim
divider.BackgroundTransparency = 0.4
divider.BorderSizePixel = 0
divider.Parent = rankRow
local unlockAt = UIKit.Label(rankRow, "UnlockAt", "", 26, Colors.Gold)
unlockAt.ZIndex = 3
UIKit.FitOneLine(unlockAt, 26)

-- What resets, what's kept ---------------------------------------------------------------------------
local function iconRow(name: string, text: string, color: Color3, keys: { string }, ticks: boolean): Frame
	local row = Instance.new("Frame")
	row.Name = name
	row.BackgroundTransparency = 1
	row.Parent = content
	local label = UIKit.Label(row, "Label", text, 30, color)
	label.TextXAlignment = Enum.TextXAlignment.Right
	UIKit.FitOneLine(label, 30)
	for index, key in keys do
		local icon = ShowcaseKit.Picture(row, "Icon" .. index, key)
		if ticks then
			ShowcaseKit.Tick(icon)
		end
	end
	return row
end
parts.ResetRow = iconRow("ResetRow", "Resets crystals, buildings, upgrades and level!", Colors.Error, { "CrystalPile", "Build", "Upgrades", "IceBlock" }, false)
parts.KeptRow = iconRow("KeptRow", "KEPT", Colors.Good, { "Pets", "Book", "FrostCore", "Rank0", "RobuxItems" }, true)

-- The level bar, REBIRTH -------------------------------------------------------------------------------
local bar, setBar = UIKit.ProgressBar(content, "LevelBar")
bar.Label.TextSize = 28
parts.Bar = bar
local feedback = UIKit.Label(content, "Feedback", "", 22, Colors.Gold)
feedback.TextXAlignment = Enum.TextXAlignment.Center
parts.Feedback = feedback
local confirm = UIKit.Button(content, "Confirm", "REBIRTH", "Buy", 40)
confirm.AnchorPoint = Vector2.new(0.5, 0.5)
parts.Confirm = confirm

local function refresh()
	local data = ClientState.Data()
	if not data or not window.IsOpen() then
		return
	end
	local cores = RebirthConfig.FrostCoresFor(data.CrystalsThisRun)
	local ready = data.BlockLevel >= RebirthConfig.RequiredLevel
	local percent = RebirthConfig.FrostCoreBonus * 100
	parts.BeforeCard.Value.Text = `+{commas(data.FrostCores * percent)}%`
	parts.AfterCard.Value.Text = `+{commas((data.FrostCores + cores) * percent)}%`
	gainText.Text = `+{commas(cores)}`
	-- the rank now -> after this rebirth, and the next thing a rank opens
	local after = data.Rebirths + 1
	local now, next = RebirthConfig.RankFor(data.Rebirths), RebirthConfig.RankFor(after)
	ShowcaseKit.SetPicture(rankRow.FromBadge, rankIconKey(data.Rebirths))
	ShowcaseKit.SetPicture(rankRow.ToBadge, rankIconKey(after))
	rankRow.FromName.Text = if now then now.Title else "No rank"
	rankRow.ToName.Text = if next then next.Title else "No rank"
	rankRow.FromName.TextColor3 = if now then RebirthConfig.ColourValues[now.Colour] or Colors.Text else Colors.Muted
	rankRow.ToName.TextColor3 = if next then RebirthConfig.ColourValues[next.Colour] or Colors.Text else Colors.Muted
	local unlock = nextUnlock(after)
	local keys = {}
	if unlock and unlock.PetSlot then
		table.insert(keys, "UnlockPetSlot")
	end
	if unlock and unlock.OpensLayer then
		table.insert(keys, "UnlockLayer")
	end
	ShowcaseKit.SetPicture(rankRow.UnlockA, keys[1])
	ShowcaseKit.SetPicture(rankRow.UnlockB, keys[2])
	unlockAt.Text = if unlock then `at Rebirth {unlock.Rank}` else ""
	divider.Visible = unlock ~= nil
	ShowcaseKit.SetPicture(parts.KeptRow.Icon4, rankIconKey(after))
	-- the level bar fills up to the rebirth level
	local level = math.min(data.BlockLevel, RebirthConfig.RequiredLevel)
	setBar(level / RebirthConfig.RequiredLevel, `Level {level} / {RebirthConfig.RequiredLevel}`)
	if not ready then
		UIKit.SetButton(confirm, "REBIRTH", "Done", false)
	else
		UIKit.SetButton(confirm, if sure then (if cores == 0 then "0 CORES. SURE?" else "SURE?") else "REBIRTH", "Buy", true)
	end
	window.Layout()
end

confirm.Activated:Connect(function()
	if not confirm.Active then
		return
	end
	if not sure then
		sure = true
		refresh()
		return
	end
	sure = false
	local ok, reply = pcall(function()
		return remote:InvokeServer("Rebirth")
	end)
	if ok and type(reply) == "table" then
		feedback.Text = tostring(reply.message)
		feedback.TextColor3 = if reply.ok then Colors.Good else Colors.Error
		if reply.ok then
			window.Close()
		end
	end
	refresh()
end)

-- The rebirth moment: the screen frosts over and clears, then the new rank's banner.
local _, frostRoot = UIKit.Screen("RebirthFrost", 40)
local frost = Instance.new("Frame")
frost.BackgroundColor3 = Color3.fromRGB(225, 245, 255)
frost.BackgroundTransparency = 1
frost.Size = UDim2.fromScale(1, 1)
frost.Parent = frostRoot
ClientState.Event("Rebirth", function(payload)
	UIKit.PlaySound("Rebirth")
	TweenService:Create(frost, TweenInfo.new(0.6), { BackgroundTransparency = 0.05 }):Play()
	task.wait(0.9)
	TweenService:Create(frost, TweenInfo.new(1.2), { BackgroundTransparency = 1 }):Play()
	Banners.Big(`Rebirth {payload.Rebirths}!`, `{payload.Title or ""} · +{payload.Cores} Frost Cores`, Color3.fromRGB(190, 150, 255), 3)
end)

local function popIn()
	local corner = window.panel:FindFirstChild("CornerIcon")
	if corner then
		ShowcaseKit.PopIn(corner, 0.05, 0.2)
	end
	ShowcaseKit.PopIn(parts.BeforeCard, 0.08)
	ShowcaseKit.PopIn(parts.AfterCard, 0.16)
	ShowcaseKit.PopIn(parts.Gain, 0.26)
	ShowcaseKit.PopIn(parts.Arrow, 0.22)
	ShowcaseKit.PopIn(rankRow, 0.3, 0.6)
	ShowcaseKit.PopIn(confirm, 0.42)
end

-- The HUD button lights up (gold) once a rebirth is possible.
local button = UIKit.MenuButton("Rebirth")
ClientState.Changed(function(data)
	refresh()
	local ready = data.BlockLevel >= RebirthConfig.RequiredLevel
	local visual = button:FindFirstChild("Visual")
	local gradient = visual and visual:FindFirstChildOfClass("UIGradient")
	if gradient then
		gradient.Enabled = true
	end
	button:SetAttribute("Ready", ready)
	if visual then
		visual.BackgroundColor3 = if ready then Color3.fromRGB(255, 220, 90) else Color3.new(1, 1, 1)
	end
end)
button.Activated:Connect(function()
	sure = false
	feedback.Text = ""
	window.Toggle()
	if window.IsOpen() then
		popIn()
	end
	refresh()
end)
