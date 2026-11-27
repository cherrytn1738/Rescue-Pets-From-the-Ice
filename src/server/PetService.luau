--[[
PetService: rescued creatures become pets (docs/GAME_DESIGN.md, "Pets" and "The Creature Book").
Server only.

 - Rescue(player, data, creatureId): the Creature Book counts it (BookSeen; a first rescue gets a
   "New!" badge in BookNew), CreaturesRescued goes up, and a pet joins the inventory (at most
   CreatureConfig.Pets.InventorySize; a full inventory still fills the book). Returns the pet or nil.
 - Auto-equip (Settings.AutoEquip, on by default; off in Settings): after a rescue, the best pets are
   equipped (PetRules.Best), once the tutorial is done (its "Equip your new pet" step still teaches it),
   or from the player's CreatureConfig.Pets.AutoEquipAfterRescues-th rescue on, so nobody plays with no pet.
 - PetRequest (RemoteFunction): the client asks, the server checks ownership, slots and counts:
     ("Equip", uid) ("Unequip", uid) ("EquipBest") ("Delete", { uids }) ("CombineGolden", uid)
     ("Lock", uid) (locks or unlocks it: a locked pet can't be deleted or combined away)
     ("DeleteBelow", rarity id) (every pet of a lower rarity that isn't locked, equipped or Golden)
     ("MarkSeen", { creature ids })   -> { ok, message }
 - Slots: PetRules.Slots(rebirths, slots from passes with PetSlots that the player owns).
 - Every client draws every player's equipped pets from the player attribute EquippedPets (JSON
   { { Uid, CreatureId, Golden } }); PetFollow.client builds and animates them.
]]
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local PetRules = require(ReplicatedStorage.PetRules)
local GamePasses = require(script.Parent.GamePasses)
local PlayerData = require(script.Parent.PlayerData)

local PetService = {}

local MAX_LIST = 60 -- uids or ids in one request
local TUTORIAL_DONE = 5 -- TutorialService's last step
local AUTO_EQUIP_NOTICE_DELAY = 2.5
local lastRequest = {} -- [player] = os.clock()
local REQUEST_GAP = 0.15
local equipListeners = {}

-- callback(player, data) after any change to what's equipped.
function PetService.OnEquipChanged(callback)
	table.insert(equipListeners, callback)
end

function PetService.PassSlots(player: Player): number
	local slots = 0
	for _, pass in MonetizationConfig.Passes do
		if pass.PetSlots and GamePasses.Owns(player, pass.Key) then
			slots += pass.PetSlots
		end
	end
	return slots
end

function PetService.Slots(player: Player, data): number
	return PetRules.Slots(data.Rebirths, PetService.PassSlots(player))
end

local function findPet(data, uid)
	for index, pet in data.Pets do
		if pet.Uid == uid then
			return pet, index
		end
	end
	return nil
end

-- Publishes what's equipped (for every client's pet followers) and the slot count.
function PetService.Publish(player: Player, data)
	-- a lost slot (a pass removed in Studio) unequips the extras
	local slots = PetService.Slots(player, data)
	while #data.Equipped > slots do
		table.remove(data.Equipped)
	end
	local out = {}
	for _, uid in data.Equipped do
		local pet = findPet(data, uid)
		if pet then
			table.insert(out, { Uid = pet.Uid, CreatureId = pet.CreatureId, Golden = pet.Golden })
		end
	end
	player:SetAttribute("EquippedPets", HttpService:JSONEncode(out))
	player:SetAttribute("PetSlots", slots)
	PlayerData.Publish(player)
end

local function changed(player: Player, data)
	PetService.Publish(player, data)
	PlayerData.MarkImportant(player)
	for _, callback in equipListeners do
		task.spawn(callback, player, data)
	end
end

function PetService.Rescue(player: Player, data, creatureId: string)
	local first = (data.BookSeen[creatureId] or 0) == 0
	data.BookSeen[creatureId] = (data.BookSeen[creatureId] or 0) + 1
	data.CreaturesRescued += 1
	if first and not table.find(data.BookNew, creatureId) then
		table.insert(data.BookNew, creatureId)
	end
	if #data.Pets >= CreatureConfig.Pets.InventorySize then
		return nil
	end
	local pet = { Uid = HttpService:GenerateGUID(false), CreatureId = creatureId, Golden = false }
	table.insert(data.Pets, pet)
	if PetService.AutoEquip(player, data) then
		local creature = CreatureConfig.Get(creatureId)
		if table.find(data.Equipped, pet.Uid) and creature then
			-- (after the rescue banner)
			task.delay(AUTO_EQUIP_NOTICE_DELAY, function()
				if player.Parent then
					ReplicatedStorage.GameEvent:FireClient(player, "Notice", { Text = `Auto-equipped your new {creature.Name}!` })
				end
			end)
		end
	else
		PetService.Publish(player, data)
	end
	return pet
end

-- Equips the best pets if the player has auto-equip on (and the tutorial is done, or they have rescued
-- enough creatures). Returns whether the equipped set changed.
function PetService.AutoEquip(player: Player, data): boolean
	if data.Settings.AutoEquip == false then
		return false
	end
	if data.TutorialStep < TUTORIAL_DONE and data.CreaturesRescued < CreatureConfig.Pets.AutoEquipAfterRescues then
		return false
	end
	local best = PetRules.Best(data.Pets, PetService.Slots(player, data))
	if PetRules.SameSet(best, data.Equipped) then
		return false
	end
	data.Equipped = best
	changed(player, data)
	return true
end

-- Gives a pet directly (debug).
function PetService.Give(player: Player, creatureId: string, golden: boolean): boolean
	local data = PlayerData.Edit(player)
	if not data or not CreatureConfig.Get(creatureId) or #data.Pets >= CreatureConfig.Pets.InventorySize then
		return false
	end
	if (data.BookSeen[creatureId] or 0) == 0 and not table.find(data.BookNew, creatureId) then
		table.insert(data.BookNew, creatureId)
	end
	data.BookSeen[creatureId] = math.max(1, data.BookSeen[creatureId] or 0)
	if golden then
		if not data.BookGolden[creatureId] and not table.find(data.BookNew, "Golden:" .. creatureId) then
			table.insert(data.BookNew, "Golden:" .. creatureId)
		end
		data.BookGolden[creatureId] = true
	end
	table.insert(data.Pets, { Uid = HttpService:GenerateGUID(false), CreatureId = creatureId, Golden = golden })
	changed(player, data)
	return true
end

-- A list of pet uids from a client: 1 to MAX_LIST short strings, no repeats (a repeated uid would make Delete
-- remove a second, unpicked pet), nothing but the list's own entries.
local function uidList(value)
	if type(value) ~= "table" or #value == 0 or #value > MAX_LIST then
		return nil
	end
	local seen, count = {}, 0
	for key, uid in value do
		count += 1
		if type(key) ~= "number" or type(uid) ~= "string" or #uid > 64 or seen[uid] then
			return nil
		end
		seen[uid] = true
	end
	return if count == #value then value else nil
end

-- Equipped must only hold owned, distinct uids (the save refuses anything else): a last guard after
-- every request.
local function cleanEquipped(data)
	local owned, seen, kept = {}, {}, {}
	for _, pet in data.Pets do
		owned[pet.Uid] = true
	end
	for _, uid in data.Equipped do
		if owned[uid] and not seen[uid] then
			seen[uid] = true
			table.insert(kept, uid)
		end
	end
	if #kept ~= #data.Equipped then
		table.clear(data.Equipped)
		for _, uid in kept do
			table.insert(data.Equipped, uid)
		end
	end
end

local actions = {}

function actions.Equip(player, data, uid)
	if type(uid) ~= "string" or not findPet(data, uid) then
		return false, "You don't have that pet."
	end
	if table.find(data.Equipped, uid) then
		return true, "Already equipped.", nil, true -- (nothing changed: no save)
	end
	if #data.Equipped >= PetService.Slots(player, data) then
		return false, "Your pet slots are full. Unequip one first."
	end
	table.insert(data.Equipped, uid)
	return true, "Equipped!"
end

function actions.Unequip(player, data, uid)
	local at = type(uid) == "string" and table.find(data.Equipped, uid)
	if not at then
		return false, "That pet isn't equipped."
	end
	table.remove(data.Equipped, at)
	return true, "Unequipped."
end

function actions.EquipBest(player, data)
	data.Equipped = PetRules.Best(data.Pets, PetService.Slots(player, data))
	return true, "Equipped your best pets!"
end

function actions.Delete(player, data, uids)
	uids = uidList(uids)
	if not uids then
		return false, "Pick the pets to delete."
	end
	for _, uid in uids do
		local pet = findPet(data, uid)
		if not pet then
			return false, "You don't have that pet."
		elseif pet.Locked then
			return false, "That pet is locked. Unlock it first."
		end
	end
	for _, uid in uids do
		local _, index = findPet(data, uid)
		if not index then
			continue -- (can't happen with a checked list: never table.remove(list, nil), which removes the last one)
		end
		table.remove(data.Pets, index)
		local at = table.find(data.Equipped, uid)
		if at then
			table.remove(data.Equipped, at)
		end
	end
	return true, if #uids == 1 then "Pet deleted." else `{#uids} pets deleted.`
end

function actions.DeleteBelow(player, data, rarityId)
	if type(rarityId) ~= "string" or PetRules.RarityRank(rarityId) < 2 then
		return false, "Pick a rarity."
	end
	local uids = PetRules.BelowRarity(data.Pets, rarityId, data.Equipped)
	if #uids == 0 then
		return false, `No pets below {rarityId} to delete (locked, equipped and Golden pets are kept).`
	end
	return actions.Delete(player, data, uids)
end

function actions.Lock(player, data, uid)
	local pet = type(uid) == "string" and findPet(data, uid)
	if not pet then
		return false, "You don't have that pet."
	end
	pet.Locked = if pet.Locked then nil else true
	return true, if pet.Locked then "Locked: it can't be deleted." else "Unlocked."
end

function actions.CombineGolden(player, data, uid)
	if type(uid) ~= "string" then
		return false, "Pick a pet."
	end
	local group = PetRules.CombineGroup(data.Pets, uid, data.Equipped)
	if not group then
		return false, `You need {CreatureConfig.Pets.GoldenCombineCount} of the same pet (not Golden, not locked).`
	end
	local target = findPet(data, uid)
	-- if any of the five was equipped, the Golden one takes that slot
	local equippedAt = nil
	for _, member in group do
		local at = table.find(data.Equipped, member)
		if at and (not equippedAt or at < equippedAt) then
			equippedAt = at
		end
	end
	for _, member in group do
		local _, index = findPet(data, member)
		table.remove(data.Pets, index)
		local at = table.find(data.Equipped, member)
		if at then
			table.remove(data.Equipped, at)
		end
	end
	local golden = { Uid = HttpService:GenerateGUID(false), CreatureId = target.CreatureId, Golden = true }
	table.insert(data.Pets, golden)
	if equippedAt then
		table.insert(data.Equipped, math.min(equippedAt, #data.Equipped + 1), golden.Uid)
	end
	local first = not data.BookGolden[target.CreatureId]
	data.BookGolden[target.CreatureId] = true
	if first and not table.find(data.BookNew, "Golden:" .. target.CreatureId) then
		table.insert(data.BookNew, "Golden:" .. target.CreatureId) -- (its New! badge on the Golden page)
	end
	return true, `Golden {CreatureConfig.Get(target.CreatureId).Name}!` .. (if first then " (new in the Golden page)" else ""), golden.Uid
end

function actions.MarkSeen(player, data, ids)
	if type(ids) ~= "table" or #ids > MAX_LIST or (#ids == 0 and next(ids) ~= nil) then
		return false, "Nothing to mark."
	end
	local removed = 0
	for index = 1, #ids do
		local id = ids[index]
		local at = type(id) == "string" and table.find(data.BookNew, id)
		if at then
			table.remove(data.BookNew, at)
			removed += 1
		end
	end
	return true, "", nil, removed == 0 -- (nothing removed: no save)
end

function PetService.Handle(player: Player, action, argument)
	if type(action) ~= "string" or not actions[action] then
		return { ok = false, message = "Unknown request." }
	end
	local now = os.clock()
	if lastRequest[player] and now - lastRequest[player] < REQUEST_GAP then
		return { ok = false, message = "Slow down a little." }
	end
	lastRequest[player] = now
	local data = PlayerData.Edit(player)
	if not data then
		return { ok = false, message = "Your data isn't ready yet." }
	end
	local ok, message, extra, unchanged = actions[action](player, data, argument)
	cleanEquipped(data)
	if ok and not unchanged then
		changed(player, data)
	end
	return { ok = ok, message = message, uid = extra }
end

function PetService.Start()
	local remote = ReplicatedStorage:WaitForChild("PetRequest") :: RemoteFunction
	remote.OnServerInvoke = PetService.Handle
	PlayerData.OnLoaded(function(player, data)
		PetService.Publish(player, data)
	end)
	GamePasses.OnChanged(function(player)
		local data = PlayerData.Edit(player)
		if data then
			PetService.Publish(player, data)
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		lastRequest[player] = nil
	end)
end

return PetService
