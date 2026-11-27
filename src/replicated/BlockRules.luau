--[[
BlockRules: the ice block's pure rules (docs/GAME_DESIGN.md, "Glacier depth" and "The ice block"),
shared by the server (IceBlockService), the client's ice look and the specs.

  RollRarity(layer, roll, lucky)   the rarity for a roll in [0, 100): walks the layer's odds table.
                                   lucky (the Lucky Ice pass) doubles Legendary and Mythic, taken
                                   from Common.
  RollCreature(layerNumber, rarityRoll, pickRoll, lucky, atLeast)  the creature: the rarity (raised to
                                   atLeast when given and the roll is lower), then one of the
                                   pool's creatures of that rarity (pickRoll in [0, 1)). A rarity
                                   with nobody in the pool falls back to the next rarity down.
  NeedsFirstRunGuarantee(rebirths, rescued, bookSeen, guarantee)  the rarity the next block must
                                   be at least (CreatureConfig.FirstRunGuarantee), or nil: only
                                   with 0 rebirths, from rescue number ByRescue on, while no
                                   creature of that rarity or better is in the book.
  RollMythicBlock(odds, roll, pickRoll)  the Mythic Block product's creature: the rarity from its own
                                   odds ({ { Name, Chance } }, adding up to 1; roll in [0, 1)), then one
                                   of that rarity from the whole roster, so its odds hold on any layer.
  Height(level)                    the block's height in studs (14 at level 1, 20 by level 50).
  CrackStage(hpLeft, hpMax)        0-4: how many of the crack stages (20/40/60/80%) are reached.
  DamageShare(hpLeft, hpMax)       0-1.
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local LayerConfig = require(ReplicatedStorage.LayerConfig)

local BlockRules = {}

local RARITY_ORDER = {}
for index, rarity in CreatureConfig.Rarities do
	RARITY_ORDER[rarity.Id] = index
end

-- The layer's odds as an ordered list { { Rarity, Percent } }, with Lucky Ice applied.
function BlockRules.Odds(layer, lucky: boolean?)
	local list = {}
	for _, rarity in CreatureConfig.Rarities do
		local percent = layer.Odds[rarity.Id]
		if percent and percent > 0 then
			table.insert(list, { Rarity = rarity.Id, Percent = percent })
		end
	end
	if lucky then
		local extra = 0
		for _, entry in list do
			if entry.Rarity == "Legendary" or entry.Rarity == "Mythic" then
				extra += entry.Percent
				entry.Percent *= 2
			end
		end
		for _, entry in list do
			if entry.Rarity == "Common" then
				entry.Percent = math.max(0, entry.Percent - extra)
			end
		end
	end
	return list
end

function BlockRules.RollRarity(layer, roll: number, lucky: boolean?): string
	local odds = BlockRules.Odds(layer, lucky)
	local total = 0
	for _, entry in odds do
		total += entry.Percent
	end
	local at = roll * total / 100
	for _, entry in odds do
		if at < entry.Percent then
			return entry.Rarity
		end
		at -= entry.Percent
	end
	return odds[#odds].Rarity
end

function BlockRules.RollMythicBlock(odds, roll: number, pickRoll: number)
	local rarity = odds[#odds].Name
	local at = roll
	for _, entry in odds do
		if at < entry.Chance then
			rarity = entry.Name
			break
		end
		at -= entry.Chance
	end
	local matching = {}
	for _, creature in CreatureConfig.Creatures do
		if creature.Rarity == rarity then
			table.insert(matching, creature)
		end
	end
	return matching[math.clamp(math.floor(pickRoll * #matching) + 1, 1, #matching)]
end

function BlockRules.NeedsFirstRunGuarantee(rebirths: number, rescued: number, bookSeen, guarantee): string?
	if rebirths ~= 0 or rescued + 1 < guarantee.ByRescue then
		return nil
	end
	local wanted = RARITY_ORDER[guarantee.Rarity]
	for creatureId, count in bookSeen do
		local creature = CreatureConfig.Get(creatureId)
		if creature and count > 0 and RARITY_ORDER[creature.Rarity] >= wanted then
			return nil
		end
	end
	return guarantee.Rarity
end

function BlockRules.RollCreature(layerNumber: number, rarityRoll: number, pickRoll: number, lucky: boolean?, atLeast: string?)
	local layer = LayerConfig.Get(layerNumber)
	local rarity = BlockRules.RollRarity(layer, rarityRoll, lucky)
	if atLeast and RARITY_ORDER[atLeast] and RARITY_ORDER[rarity] < RARITY_ORDER[atLeast] then
		rarity = atLeast
	end
	local pool = CreatureConfig.PoolForLayer(layerNumber)
	for index = RARITY_ORDER[rarity], 1, -1 do
		local wanted = CreatureConfig.Rarities[index].Id
		local matching = {}
		for _, creature in pool do
			if creature.Rarity == wanted then
				table.insert(matching, creature)
			end
		end
		if #matching > 0 then
			return matching[math.clamp(math.floor(pickRoll * #matching) + 1, 1, #matching)]
		end
	end
	return pool[1]
end

function BlockRules.Height(level: number): number
	local block = LayerConfig.Block
	local t = math.clamp((level - 1) / 49, 0, 1)
	return block.HeightAtFirstLevel + (block.HeightAtLevel50 - block.HeightAtFirstLevel) * t
end

function BlockRules.DamageShare(hpLeft: number, hpMax: number): number
	if hpMax <= 0 then
		return 1
	end
	return math.clamp(1 - hpLeft / hpMax, 0, 1)
end

function BlockRules.CrackStage(hpLeft: number, hpMax: number): number
	local percent = BlockRules.DamageShare(hpLeft, hpMax) * 100 + 1e-9 -- (20% of 100 HP is 20%, not 19.999...)
	local stage = 0
	for index, threshold in LayerConfig.Block.CrackStages do
		if threshold < 100 and percent >= threshold then
			stage = index
		end
	end
	return stage
end

return BlockRules
