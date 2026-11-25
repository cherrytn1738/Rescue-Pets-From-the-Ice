-- The Pets panel (docs/GAME_DESIGN.md, "Pets" and "Screens"): the equipped slots on top (locked
-- slots say what opens them: a rebirth rank or a pass), the inventory grid (best first, each with its
-- 3D picture, rarity and bonus), Equip Best, and for the picked pet: equip/unequip, combine 5 into a
-- Golden one, lock (a locked pet can't be deleted or combined away), delete. With no pet picked, the
-- delete button opens "Delete all below <rarity>" (skips locked, equipped and Golden pets; asks to
-- confirm). Every action is a request (PetRequest); the server checks ownership, slots and counts.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local EconomyRules = require(ReplicatedStorage.EconomyRules)
local IceLooks = require(ReplicatedStorage.IceLooks)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local PetRules = require(ReplicatedStorage.PetRules)
local RebirthConfig = require(ReplicatedStorage.RebirthConfig)
local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)
local ClientState = require(script.Parent.ClientState)
local PetViewport = require(script.Parent.PetViewport)

local remote = ReplicatedStorage:WaitForChild("PetRequest") :: RemoteFunction
local player = Players.LocalPlayer
local Colors = UIKit.Colors

local TILE = 150
local SLOT = 92

local CLEANUP_RARITIES = { "Uncommon", "Rare", "Epic", "Legendary", "Mythic" } -- "delete all below" choices

local selected = nil -- a pet uid
local slotsRow, summary, grid, gridLayout, actions, feedback
local equipButton, combineButton, lockButton, deleteButton, bestButton
local cleanup, cleanupTitle, cleanupButtons, cleanupCancel = nil, nil, {}, nil
local cleanupPick = nil -- the rarity picked once in the cleanup panel (a second press deletes)
local tiles = {} -- [uid] = { card, viewport }
local slotFrames = {}

local window = ShowcaseKit.Window("PetsWindow", "Pets", {
	width = 960,
	height = 660,
	onLayout = function(width, height)
		slotsRow.Position, slotsRow.Size = UDim2.fromOffset(0, 0), UDim2.fromOffset(width, SLOT + 10)
		summary.Position, summary.Size = UDim2.fromOffset(0, SLOT + 14), UDim2.fromOffset(width, 30)
		actions.Position, actions.Size = UDim2.fromOffset(0, height - 70), UDim2.fromOffset(width, 64)
		feedback.Position, feedback.Size = UDim2.fromOffset(0, height - 100), UDim2.fromOffset(width, 28)
		grid.Position, grid.Size = UDim2.fromOffset(0, SLOT + 50), UDim2.fromOffset(width, height - SLOT - 156)
		local buttonWidth = (width - 40) / 5
		for i, button in { bestButton, equipButton, combineButton, lockButton, deleteButton } do
			button.Position = UDim2.fromOffset((i - 1) * (buttonWidth + 10), 0)
			button.Size = UDim2.fromOffset(buttonWidth, 60)
		end
		cleanup.Position, cleanup.Size = grid.Position, grid.Size
		cleanupTitle.Position, cleanupTitle.Size = UDim2.fromOffset(10, 12), UDim2.new(1, -20, 0, 34)
		local count = #CLEANUP_RARITIES
		local each = math.min(170, (width - 40 - 10 * (count - 1)) / count)
		local rowLeft = (width - (each * count + 10 * (count - 1))) / 2
		for i, button in cleanupButtons do
			button.Position = UDim2.fromOffset(rowLeft + (i - 1) * (each + 10), 58)
			button.Size = UDim2.fromOffset(each, 84)
		end
		cleanupCancel.Position, cleanupCancel.Size = UDim2.new(0.5, -110, 0, 158), UDim2.fromOffset(220, 56)
	end,
})
local content = window.content

slotsRow = Instance.new("Frame")
slotsRow.Name = "Slots"
slotsRow.BackgroundTransparency = 1
slotsRow.Parent = content
local slotLayout = Instance.new("UIListLayout")
slotLayout.FillDirection = Enum.FillDirection.Horizontal
slotLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
slotLayout.Padding = UDim.new(0, 10)
slotLayout.Parent = slotsRow
summary = UIKit.Label(content, "Summary", "", 24, Colors.Gold)
summary.TextXAlignment = Enum.TextXAlignment.Center
grid, gridLayout = UIKit.Scroll(content, "Grid", "Grid")
gridLayout.CellSize = UDim2.fromOffset(TILE, TILE + 36)
actions = Instance.new("Frame")
actions.Name = "Actions"
actions.BackgroundTransparency = 1
actions.Parent = content
bestButton = UIKit.Button(actions, "EquipBest", "EQUIP BEST", "Go", 26)
equipButton = UIKit.Button(actions, "Equip", "EQUIP", "Neutral", 26)
combineButton = UIKit.Button(actions, "Combine", "GOLDEN (5)", "Gold", 24)
lockButton = UIKit.Button(actions, "Lock", "LOCK", "Neutral", 26)
deleteButton = UIKit.Button(actions, "Delete", "DELETE", "Locked", 26)
feedback = UIKit.Label(content, "Feedback", "", 22, Colors.Gold)
feedback.TextXAlignment = Enum.TextXAlignment.Center

-- "Delete all below <rarity>": a panel over the grid
cleanup = UIKit.Card(content, "Cleanup")
cleanup.Visible = false
cleanup.ZIndex = 20
cleanupTitle = UIKit.Label(cleanup, "Title", "Delete every pet below:", 28)
cleanupTitle.TextXAlignment = Enum.TextXAlignment.Center
cleanupTitle.ZIndex = 21
for i, rarityId in CLEANUP_RARITIES do
	local button = UIKit.Button(cleanup, rarityId .. "Below", string.upper(rarityId), "Done", 22)
	button.ZIndex = 21
	cleanupButtons[i] = button
end
cleanupCancel = UIKit.Button(cleanup, "Cancel", "CANCEL", "Neutral", 26)
cleanupCancel.ZIndex = 21

-- What opens each slot past the first: the rebirth ranks, then the passes.
local function slotUnlocks()
	local list = {}
	for _, rank in RebirthConfig.Ranks do
		if rank.PetSlot then
			table.insert(list, `Rebirth {rank.Rank}`)
		end
	end
	for _, pass in MonetizationConfig.Passes do
		for _ = 1, pass.PetSlots or 0 do
			table.insert(list, `{pass.Name} R${pass.ExpectedPrice}`)
		end
	end
	return list
end

local busy = false
local function request(action, argument)
	if busy then
		return nil
	end
	busy = true
	local ok, reply = pcall(function()
		return remote:InvokeServer(action, argument)
	end)
	busy = false
	if not ok or type(reply) ~= "table" then
		feedback.Text, feedback.TextColor3 = "The server didn't answer. Try again.", Colors.Error
		return nil
	end
	if reply.message and reply.message ~= "" then
		feedback.Text = reply.message
		feedback.TextColor3 = if reply.ok then Colors.Good else Colors.Error
	end
	UIKit.PlaySound(if reply.ok then "Equip" else "Invalid")
	return reply
end

local confirmDelete = false
local function refresh()
	local data = ClientState.Data()
	if not data or not window.IsOpen() then
		return
	end
	local slots = player:GetAttribute("PetSlots") or 1
	local byUid = {}
	for _, pet in data.Pets do
		byUid[pet.Uid] = pet
	end
	if selected and not byUid[selected] then
		selected = nil
	end

	-- the slots row
	for _, frame in slotFrames do
		frame:Destroy()
	end
	table.clear(slotFrames)
	local unlocks = slotUnlocks()
	for index = 1, CreatureConfig.Pets.MaxEquipSlots do
		local card = UIKit.Card(slotsRow, "Slot" .. index)
		card.Size = UDim2.fromOffset(SLOT, SLOT)
		card.LayoutOrder = index
		table.insert(slotFrames, card)
		local uid = data.Equipped[index]
		if index <= slots and uid and byUid[uid] then
			local view = PetViewport.new(card, byUid[uid].CreatureId, if byUid[uid].Golden then "Golden" else "Normal")
			view.frame.ZIndex = 5
		elseif index > slots then
			local lock = UIKit.Label(card, "Lock", "🔒\n" .. (unlocks[index - 1] or ""), 16, Colors.Muted, true)
			lock.Size = UDim2.fromScale(1, 1)
			lock.TextXAlignment = Enum.TextXAlignment.Center
			lock.TextScaled = true
			lock.ZIndex = 5
		end
	end
	summary.Text = `{#data.Equipped}/{slots} equipped · pets give +{math.floor(EconomyRules.PetBonus(data) * 100 + 0.5)}% crystals · {#data.Pets}/{CreatureConfig.Pets.InventorySize} pets`

	-- the inventory grid, best first
	local seen = {}
	for order, pet in PetRules.Sorted(data.Pets) do
		seen[pet.Uid] = true
		local tile = tiles[pet.Uid]
		if not tile then
			local creature = CreatureConfig.Get(pet.CreatureId)
			local card = ShowcaseKit.Card(grid, pet.Uid, if pet.Golden then "Gold" else "Slate")
			local holder = Instance.new("Frame")
			holder.BackgroundTransparency = 1
			holder.Position, holder.Size = UDim2.fromOffset(8, 6), UDim2.new(1, -16, 0, TILE - 20)
			holder.ZIndex = 4
			holder.Parent = card
			local view = PetViewport.new(holder, pet.CreatureId, if pet.Golden then "Golden" else "Normal")
			local name = UIKit.Label(card, "Name", (if pet.Golden then "Golden " else "") .. creature.Name, 18, nil, true)
			name.Position, name.Size = UDim2.new(0, 6, 1, -54), UDim2.new(1, -12, 0, 26)
			name.TextScaled = true
			name.TextXAlignment = Enum.TextXAlignment.Center
			name.ZIndex = 6
			local bonus = UIKit.Label(card, "Bonus", `+{math.floor(EconomyRules.PetBonusOf(pet) * 100 + 0.5)}%`, 18, IceLooks.RarityColors[creature.Rarity])
			bonus.Position, bonus.Size = UDim2.new(0, 6, 1, -28), UDim2.new(1, -12, 0, 22)
			bonus.TextXAlignment = Enum.TextXAlignment.Center
			bonus.ZIndex = 6
			local tick = UIKit.Label(card, "Equipped", "✔", 30, Colors.Good)
			tick.Position, tick.Size = UDim2.fromOffset(8, 4), UDim2.fromOffset(34, 34)
			tick.ZIndex = 7
			local lockMark = UIKit.Label(card, "LockMark", "🔒", 24)
			lockMark.AnchorPoint = Vector2.new(1, 0)
			lockMark.Position, lockMark.Size = UDim2.new(1, -6, 0, 4), UDim2.fromOffset(30, 30)
			lockMark.ZIndex = 7
			local button = Instance.new("TextButton")
			button.Name = "Pick"
			button.BackgroundTransparency = 1
			button.Text = ""
			button.Size = UDim2.fromScale(1, 1)
			button.ZIndex = 8
			button.Parent = card
			UIKit.MarkSelectable(button)
			button.Activated:Connect(function()
				selected = if selected == pet.Uid then nil else pet.Uid
				confirmDelete = false
				cleanup.Visible, grid.Visible, cleanupPick = false, true, nil
				refresh()
			end)
			tile = { card = card, view = view, tick = tick, lockMark = lockMark, golden = pet.Golden }
			tiles[pet.Uid] = tile
		end
		tile.card.LayoutOrder = order
		tile.tick.Visible = table.find(data.Equipped, pet.Uid) ~= nil
		tile.lockMark.Visible = pet.Locked == true
		local stroke = tile.card:FindFirstChildOfClass("UIStroke")
		if stroke then
			stroke.Color = if selected == pet.Uid then Color3.fromRGB(255, 230, 90) else Colors.Outline
			stroke.Thickness = if selected == pet.Uid then 7 else 5
		end
	end
	for uid, tile in tiles do
		if not seen[uid] then
			tile.card:Destroy()
			tiles[uid] = nil
		end
	end

	-- the actions for the picked pet
	local pet = selected and byUid[selected]
	local equipped = pet and table.find(data.Equipped, pet.Uid) ~= nil
	UIKit.SetButton(equipButton, if equipped then "UNEQUIP" else "EQUIP", if pet then "Neutral" else "Done", pet ~= nil)
	local canCombine = pet and PetRules.CombineGroup(data.Pets, pet.Uid, data.Equipped) ~= nil
	UIKit.SetButton(combineButton, "GOLDEN (5)", if canCombine then "Gold" else "Done", canCombine == true)
	UIKit.SetButton(lockButton, if pet and pet.Locked then "UNLOCK" else "LOCK", if pet then "Neutral" else "Done", pet ~= nil)
	if pet then
		UIKit.SetButton(deleteButton, if pet.Locked then "LOCKED" elseif confirmDelete then "SURE?" else "DELETE",
			if pet.Locked then "Done" else "Locked", not pet.Locked)
	else
		-- nothing picked: the button opens "Delete all below"
		UIKit.SetButton(deleteButton, "DELETE BELOW…", if #data.Pets > 0 then "Locked" else "Done", #data.Pets > 0)
	end
	UIKit.SetButton(bestButton, "EQUIP BEST", if #data.Pets > 0 then "Go" else "Done", #data.Pets > 0)

	-- the cleanup panel's counts
	if cleanup.Visible then
		for i, rarityId in CLEANUP_RARITIES do
			local count = #PetRules.BelowRarity(data.Pets, rarityId, data.Equipped)
			local caption = if cleanupPick == rarityId then `DELETE {count}?` else `{string.upper(rarityId)}\n({count} pet{if count == 1 then "" else "s"})`
			UIKit.SetButton(cleanupButtons[i], caption, if cleanupPick == rarityId then "Locked" elseif count > 0 then "Neutral" else "Done", count > 0)
		end
	end
end

local function showCleanup(show: boolean)
	cleanup.Visible = show
	grid.Visible = not show
	cleanupPick = nil
	refresh()
end

for i, rarityId in CLEANUP_RARITIES do
	cleanupButtons[i].Activated:Connect(function()
		if not cleanupButtons[i].Active then
			return
		end
		if cleanupPick ~= rarityId then
			cleanupPick = rarityId -- first press: ask to confirm
			refresh()
			return
		end
		cleanupPick = nil
		local reply = request("DeleteBelow", rarityId)
		if reply and reply.ok then
			showCleanup(false)
		else
			refresh()
		end
	end)
end
cleanupCancel.Activated:Connect(function()
	showCleanup(false)
end)
lockButton.Activated:Connect(function()
	if lockButton.Active and selected then
		request("Lock", selected)
	end
end)

bestButton.Activated:Connect(function()
	if bestButton.Active then
		request("EquipBest")
	end
end)
equipButton.Activated:Connect(function()
	local data = ClientState.Data()
	if not equipButton.Active or not selected or not data then
		return
	end
	request(if table.find(data.Equipped, selected) then "Unequip" else "Equip", selected)
end)
combineButton.Activated:Connect(function()
	if combineButton.Active and selected then
		local reply = request("CombineGolden", selected)
		if reply and reply.ok then
			UIKit.PlaySound("GoldenSparkle")
			selected = reply.uid
		end
	end
end)
deleteButton.Activated:Connect(function()
	if not deleteButton.Active then
		return
	end
	if not selected then
		showCleanup(not cleanup.Visible)
		return
	end
	if not confirmDelete then
		confirmDelete = true
		refresh()
		return
	end
	confirmDelete = false
	request("Delete", { selected })
end)

ClientState.Changed(function()
	refresh()
end)
player:GetAttributeChangedSignal("PetSlots"):Connect(refresh)
UIKit.MenuButton("Pets").Activated:Connect(function()
	window.Toggle()
	feedback.Text = ""
	confirmDelete = false
	cleanup.Visible, grid.Visible, cleanupPick = false, true, nil
	refresh()
end)
