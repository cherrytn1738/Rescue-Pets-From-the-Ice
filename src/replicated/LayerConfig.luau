--[[
LayerConfig: the glacier's ice layers and the ice block (docs/GAME_DESIGN.md, "Glacier depth" and
"The ice block"). Every number here is a starting value for the economy simulation.

 * Layers[n]: Number, Id, Name, MinLevel/MaxLevel (the block levels it covers), Look (the doc's
   description), IceLookId (the ice look's asset or material, nil until it is made), Odds (percent
   chance of each rarity when a block in this layer rolls its creature; they add up to 100), and
   RequiresRebirths (a layer that only opens with rebirths).
 * Layer 5 is the floor until rebirths open deeper layers: blocks past its MaxLevel stay in the
   deepest layer the player has opened, with HP still rising (LayerForLevel).
 * The server always rolls from the current layer's table; Lucky Ice and the Mythic Block product
   change the odds on top of it.
 * The tests in tests/LayerConfig.spec.luau check these tables against the design doc.
]]
local LayerConfig = {}

LayerConfig.LevelsPerLayer = 10
LayerConfig.FloorLayer = 5 -- the deepest layer reachable without rebirths

LayerConfig.Layers = {
	{ Number = 1, Id = "FreshSnow", Name = "Fresh Snow", MinLevel = 1, MaxLevel = 10, Look = "Packed white snow, soft edges", IceLookId = nil,
		Odds = { Common = 75, Uncommon = 25 } },
	{ Number = 2, Id = "BlueIce", Name = "Blue Ice", MinLevel = 11, MaxLevel = 20, Look = "Clear pale blue", IceLookId = nil,
		Odds = { Common = 60, Uncommon = 30, Rare = 10 } },
	{ Number = 3, Id = "AncientIce", Name = "Ancient Ice", MinLevel = 21, MaxLevel = 30, Look = "Deep blue with trapped bubbles", IceLookId = nil,
		Odds = { Common = 50, Uncommon = 30, Rare = 15, Epic = 5 } },
	{ Number = 4, Id = "CrystalIce", Name = "Crystal Ice", MinLevel = 31, MaxLevel = 40, Look = "Faceted, sparkling", IceLookId = nil,
		Odds = { Common = 45, Uncommon = 30, Rare = 16, Epic = 7, Legendary = 2 } },
	{ Number = 5, Id = "PrimordialIce", Name = "Primordial Ice", MinLevel = 41, MaxLevel = 50, Look = "Dark teal with glowing veins", IceLookId = nil,
		Odds = { Common = 40, Uncommon = 30, Rare = 18, Epic = 8.5, Legendary = 3, Mythic = 0.5 } },
	-- Opened at rebirth 3 (RebirthConfig).
	{ Number = 6, Id = "FrozenCore", Name = "Frozen Core", MinLevel = 51, MaxLevel = 60, Look = "Black ice lit from inside", IceLookId = nil,
		RequiresRebirths = 3,
		Odds = { Common = 35, Uncommon = 28, Rare = 20, Epic = 11, Legendary = 5, Mythic = 1 } },
}

-- The ice block. BlockHP(L) = BaseHp × HpGrowth^(L - 1).
LayerConfig.Block = {
	BaseHp = 100,
	HpGrowth = 1.5,
	CrackStages = { 20, 40, 60, 80, 100 }, -- percent damage at each crack stage (100 = it shatters)
	HeightAtFirstLevel = 14, -- studs, at level 1 (about 2.5 avatars)
	HeightAtLevel50 = 20, -- studs, by level 50
}

function LayerConfig.BlockHp(level: number): number
	return LayerConfig.Block.BaseHp * LayerConfig.Block.HpGrowth ^ (level - 1)
end

-- The layer a block of this level is made of, for a player who has opened layers up to
-- maxLayerOpened: the layer whose level range holds it, or the deepest opened layer once the level is
-- past every opened layer's range.
function LayerConfig.LayerForLevel(level: number, maxLayerOpened: number)
	local deepest = LayerConfig.Layers[1]
	for _, layer in LayerConfig.Layers do
		if layer.Number <= maxLayerOpened then
			if level >= layer.MinLevel and level <= layer.MaxLevel then
				return layer
			end
			if layer.Number > deepest.Number then
				deepest = layer
			end
		end
	end
	return deepest
end

function LayerConfig.Get(number: number)
	return LayerConfig.Layers[number]
end

return LayerConfig
