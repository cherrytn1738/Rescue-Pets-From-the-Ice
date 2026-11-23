--[[
PetRules: the pet rules as pure functions (docs/GAME_DESIGN.md, "Pets"), shared by the server
(PetService), the Pets panel and the specs.

  Slots(rebirths, passSlots)     equip slots: 1, plus rebirth ranks (2nd at 3, 3rd at 6, 4th at 10),
                                 plus the slot passes, at most CreatureConfig.Pets.MaxEquipSlots.
  Best(pets, slots)              the uids Equip Best would equip: the highest bonuses.
  CombineGroup(pets, uid, equipped)  the five uids a Golden combine would use for that pet (the pet
                                 itself plus four more non-Golden copies of the same creature,
                                 unequipped ones first), or nil when there aren't five.
  Sorted(pets)                   the inventory in display order: best bonus first.
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local EconomyRules = require(ReplicatedStorage.EconomyRules)
local RebirthConfig = require(ReplicatedStorage.RebirthConfig)

local PetRules = {}

function PetRules.Slots(rebirths: number, passSlots: number): number
	local pets = CreatureConfig.Pets
	return math.min(pets.MaxEquipSlots, RebirthConfig.PetSlotsFor(rebirths, pets.BaseEquipSlots) + passSlots)
end

local RARITY_RANK = {}
for index, rarity in CreatureConfig.Rarities do
	RARITY_RANK[rarity.Id] = index
end

local function better(a, b): boolean
	local bonusA, bonusB = EconomyRules.PetBonusOf(a), EconomyRules.PetBonusOf(b)
	if bonusA ~= bonusB then
		return bonusA > bonusB
	end
	if a.CreatureId ~= b.CreatureId then
		return a.CreatureId < b.CreatureId
	end
	return a.Uid < b.Uid
end

function PetRules.Sorted(pets)
	local list = table.clone(pets)
	table.sort(list, better)
	return list
end

function PetRules.Best(pets, slots: number)
	local best = {}
	for index, pet in PetRules.Sorted(pets) do
		if index > slots then
			break
		end
		table.insert(best, pet.Uid)
	end
	return best
end

function PetRules.CombineGroup(pets, uid: string, equipped)
	local target
	for _, pet in pets do
		if pet.Uid == uid then
			target = pet
		end
	end
	if not target or target.Golden then
		return nil
	end
	local group = { target.Uid }
	-- unequipped copies first, so a combine takes as few equipped pets as possible
	for _, wantEquipped in { false, true } do
		for _, pet in pets do
			if #group >= CreatureConfig.Pets.GoldenCombineCount then
				break
			end
			local isEquipped = table.find(equipped, pet.Uid) ~= nil
			if pet.Uid ~= uid and not pet.Golden and pet.CreatureId == target.CreatureId and isEquipped == wantEquipped then
				table.insert(group, pet.Uid)
			end
		end
	end
	if #group < CreatureConfig.Pets.GoldenCombineCount then
		return nil
	end
	return group
end

function PetRules.RarityRank(rarityId: string): number
	return RARITY_RANK[rarityId] or 0
end

return PetRules
