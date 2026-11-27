--[[
CreatureConfig: the rarities, the 18 launch creatures, pet rules and the Creature Book
(docs/GAME_DESIGN.md, "Pets", "Creature roster" and "The Creature Book"). Starting values for the
economy simulation.

 * Rarities[n]: Id, Bonus (crystal bonus while equipped: 0.10 = +10%), Glow (seen through the ice;
   "None" = only a dark silhouette), Announce (the whole server is told when such a block arrives).
 * Creatures[n]: Id (saved: never rename one), Name, Rarity, FirstLayer (the first LayerConfig layer it
   appears in; it keeps appearing in every deeper layer), Look (the doc's description), ModelId (the
   voxel pet model, nil until it is built and uploaded as group 921449746).
 * Book: the Creature Book's page rewards. Pages are kept through rebirths.
 * FirstRunGuarantee: the first run's guaranteed Rare (or better).
 * Checked against the design doc by tests/CreatureConfig.spec.luau.
]]
local CreatureConfig = {}

CreatureConfig.Rarities = {
	{ Id = "Common", Bonus = 0.10, Glow = "None", Announce = false },
	{ Id = "Uncommon", Bonus = 0.25, Glow = "None", Announce = false },
	{ Id = "Rare", Bonus = 0.50, Glow = "SoftBlue", Announce = false },
	{ Id = "Epic", Bonus = 1.00, Glow = "Purple", Announce = false },
	{ Id = "Legendary", Bonus = 2.00, Glow = "PulsingAmber", Announce = true },
	{ Id = "Mythic", Bonus = 4.00, Glow = "ShiftingRainbow", Announce = true },
}

CreatureConfig.Creatures = {
	{ Id = "SnowBunny", Name = "Snow Bunny", Rarity = "Common", FirstLayer = 1, Look = "Round white bunny with fluffy earmuff ears", ModelId = nil },
	{ Id = "PenguinChick", Name = "Penguin Chick", Rarity = "Common", FirstLayer = 1, Look = "Grey fluffball with a tiny orange beak", ModelId = nil },
	{ Id = "FrostMouse", Name = "Frost Mouse", Rarity = "Common", FirstLayer = 1, Look = "Pale blue mouse with an icicle tail", ModelId = nil },
	{ Id = "PuffinPal", Name = "Puffin Pal", Rarity = "Common", FirstLayer = 1, Look = "Puffin with a frosty striped beak", ModelId = nil },
	{ Id = "ArcticFoxKit", Name = "Arctic Fox Kit", Rarity = "Uncommon", FirstLayer = 1, Look = "White fox cub with a blue tail tip", ModelId = nil },
	{ Id = "SealPup", Name = "Seal Pup", Rarity = "Uncommon", FirstLayer = 1, Look = "Round white pup with big dark eyes", ModelId = nil },
	{ Id = "SnowyOwlet", Name = "Snowy Owlet", Rarity = "Uncommon", FirstLayer = 1, Look = "Big-eyed owl chick with frosted feathers", ModelId = nil },
	{ Id = "IceHedgehog", Name = "Ice Hedgehog", Rarity = "Uncommon", FirstLayer = 1, Look = "Hedgehog whose spikes are icicles", ModelId = nil },
	{ Id = "PolarBearCub", Name = "Polar Bear Cub", Rarity = "Rare", FirstLayer = 2, Look = "Chubby cub wearing a scarf", ModelId = nil },
	{ Id = "GlacierOtter", Name = "Glacier Otter", Rarity = "Rare", FirstLayer = 2, Look = "Otter floating on its back, holding a snowflake", ModelId = nil },
	{ Id = "FrostTurtle", Name = "Frost Turtle", Rarity = "Rare", FirstLayer = 3, Look = "Turtle with a shell of ice crystals", ModelId = nil },
	{ Id = "MiniYeti", Name = "Mini Yeti", Rarity = "Epic", FirstLayer = 3, Look = "Small shaggy yeti with a big grin", ModelId = nil },
	{ Id = "CrystalStag", Name = "Crystal Stag", Rarity = "Epic", FirstLayer = 3, Look = "Fawn with glowing crystal antlers", ModelId = nil },
	{ Id = "IceWolfPup", Name = "Ice Wolf Pup", Rarity = "Epic", FirstLayer = 4, Look = "Silver wolf pup with glowing blue eyes", ModelId = nil },
	{ Id = "FrostDragonHatchling", Name = "Frost Dragon Hatchling", Rarity = "Legendary", FirstLayer = 4, Look = "Baby dragon, pale blue scales, frosty breath", ModelId = nil },
	{ Id = "SnowPhoenix", Name = "Snow Phoenix", Rarity = "Legendary", FirstLayer = 5, Look = "White bird with icy flame feathers", ModelId = nil },
	{ Id = "AuroraFox", Name = "Aurora Fox", Rarity = "Mythic", FirstLayer = 5, Look = "Fox whose tail ripples with northern lights", ModelId = nil },
	{ Id = "SpiritWhale", Name = "Spirit Whale", Rarity = "Mythic", FirstLayer = 5, Look = "Small floating whale made of aurora light", ModelId = nil },
}

CreatureConfig.Pets = {
	InventorySize = 50,
	BaseEquipSlots = 1, -- more from rebirth ranks (RebirthConfig) and two passes
	MaxEquipSlots = 7,
	GoldenCombineCount = 5, -- 5 of the same pet combine into a Golden one
	GoldenBonusMultiplier = 2, -- a Golden pet has double the bonus
	AutoEquipAfterRescues = 3, -- auto-equip also starts at this many rescues, even with the tutorial unfinished
}

-- The first run's guaranteed Rare: while Rebirths = 0 and no creature of Rarity or better has been
-- rescued yet, the block for rescue number ByRescue (and any after it, until one is rescued) holds at
-- least that rarity. Rares first appear in Blue Ice (level 11), so it lands on rescue 11 or 12.
CreatureConfig.FirstRunGuarantee = {
	Rarity = "Rare",
	ByRescue = 12,
}

-- Creature Book page rewards (permanent). CrystalBonus 0.05 = +5% crystals.
CreatureConfig.Book = {
	{ Page = "Common", Count = 4, CrystalBonus = 0.05 },
	{ Page = "Uncommon", Count = 4, CrystalBonus = 0.05 },
	{ Page = "Rare", Count = 3, CrystalBonus = 0.10 },
	{ Page = "Epic", Count = 3, CrystalBonus = 0.10, NameTagBorder = "Frosty" },
	{ Page = "Legendary", Count = 2, CrystalBonus = 0.15, NameTagBorder = "Golden" },
	{ Page = "Mythic", Count = 2, Trail = "Aurora" },
	{ Page = "Golden", Count = 18, Title = "Ice Keeper", PickSkin = "Golden" }, -- a Golden version of every creature
}

-- A Book page's reward in words ("+5% crystals", "+10% crystals and a frosty name-tag border").
function CreatureConfig.BookRewardText(page): string
	local parts = {}
	if page.CrystalBonus then
		table.insert(parts, `+{math.floor(page.CrystalBonus * 100 + 0.5)}% crystals`)
	end
	if page.NameTagBorder then
		table.insert(parts, `a {string.lower(page.NameTagBorder)} name-tag border`)
	end
	if page.Trail then
		table.insert(parts, `an {string.lower(page.Trail)} trail`)
	end
	if page.Title then
		table.insert(parts, `the title "{page.Title}"`)
	end
	if page.PickSkin then
		table.insert(parts, `a {string.lower(page.PickSkin)} ice pick skin`)
	end
	return table.concat(parts, " and ")
end

local byId, rarityById = {}, {}
for _, creature in CreatureConfig.Creatures do
	byId[creature.Id] = creature
end
for _, rarity in CreatureConfig.Rarities do
	rarityById[rarity.Id] = rarity
end

function CreatureConfig.Get(id: string)
	return byId[id]
end

function CreatureConfig.GetRarity(id: string)
	return rarityById[id]
end

-- The creatures a block in layer `layerNumber` can hold: every creature whose first layer is at or
-- above it.
function CreatureConfig.PoolForLayer(layerNumber: number)
	local pool = {}
	for _, creature in CreatureConfig.Creatures do
		if creature.FirstLayer <= layerNumber then
			table.insert(pool, creature)
		end
	end
	return pool
end

return CreatureConfig
