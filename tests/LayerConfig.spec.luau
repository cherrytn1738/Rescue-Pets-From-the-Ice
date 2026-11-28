-- LayerConfig matches docs/GAME_DESIGN.md ("Glacier depth", "The ice block", "Plot and map layout").
-- Run: python tools/run_specs.py LayerConfig
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local DesignDoc = assert(loadstring(sources.DesignDoc))()
	local doc = DesignDoc.new(sources["GAME_DESIGN.md"])
	local text = sources["GAME_DESIGN.md"]
	local LayerConfig = assert(loadstring(sources.LayerConfig))()
	local RARITIES = { "Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic" }

	-- The layer table.
	local rows = doc:Table({ "Layer", "Block levels", "Ice look" })
	check(#rows == #LayerConfig.Layers, "one layer per row of the doc's table (" .. #rows .. ")")
	for index, row in rows do
		local layer = LayerConfig.Layers[index]
		local number, name = string.match(row.Layer, "^(%d+)%.%s*(.+)$")
		check(layer.Number == tonumber(number) and layer.Number == index, `layer {index} is number {number}`)
		check(layer.Name == name and layer.Id == DesignDoc.IdOf(name), `layer {index} is {name}`)
		check(layer.Look == row["Ice look"], `{name}'s look matches the doc`)
		local low, high = DesignDoc.Range(row["Block levels"])
		if low then
			check(layer.MinLevel == low and layer.MaxLevel == high, `{name} covers levels {low}-{high}`)
			local rebirths = tonumber(string.match(row["Block levels"], "rebirth (%d+)"))
			check(layer.RequiresRebirths == rebirths, `{name} opens at rebirth {tostring(rebirths)}`)
		else
			check(false, `{name}'s block levels can be read from the doc`)
		end
		local total = 0
		for _, rarity in RARITIES do
			local expected = DesignDoc.Number(row[rarity]) -- nil for "–"
			check(layer.Odds[rarity] == expected, `{name} {rarity} odds are {tostring(expected)}%`)
			total += layer.Odds[rarity] or 0
		end
		check(math.abs(total - 100) < 1e-9, `{name}'s odds add up to 100% ({total})`)
	end
	for key in LayerConfig.Layers[1].Odds do
		check(table.find(RARITIES, key) ~= nil, "odds only name real rarities: " .. key)
	end

	-- Levels per layer, and the floor.
	for _, layer in LayerConfig.Layers do
		check(layer.MaxLevel - layer.MinLevel + 1 == LayerConfig.LevelsPerLayer, layer.Name .. " spans " .. LayerConfig.LevelsPerLayer .. " levels")
	end
	check(string.find(text, "every 10 levels they reach a new ice layer", 1, true) and LayerConfig.LevelsPerLayer == 10, "a new layer every 10 levels")
	check(string.find(text, "**Layer 5 is the floor**", 1, true) and LayerConfig.FloorLayer == 5, "layer 5 is the floor")
	check(LayerConfig.LayerForLevel(1, 5).Number == 1 and LayerConfig.LayerForLevel(25, 5).Number == 3, "levels 1 and 25 are layers 1 and 3")
	check(LayerConfig.LayerForLevel(55, 5).Number == 5, "past level 50, blocks stay in the floor layer")
	check(LayerConfig.LayerForLevel(55, 6).Number == 6 and LayerConfig.LayerForLevel(80, 6).Number == 6, "with Frozen Core open, deeper blocks are Frozen Core")

	-- Block HP: BlockHP(L) = 100 × 1.5^(L−1).
	local base, growth = string.match(text, "\\text{BlockHP}%(L%) = (%d+) \\times ([%d%.]+)")
	check(tonumber(base) == LayerConfig.Block.BaseHp and tonumber(growth) == LayerConfig.Block.HpGrowth, "block HP base and growth match the formula")
	check(LayerConfig.BlockHp(1) == 100 and LayerConfig.BlockHp(3) == 225, "BlockHp(1) = 100, BlockHp(3) = 225")
	local from, slower = string.match(text, "Past level (%d+), each block has ([%d%.]+) times the HP of the one before")
	check(tonumber(from) == LayerConfig.Block.SlowerFromLevel and tonumber(slower) == LayerConfig.Block.SlowerHpGrowth,
		"past level 40, block HP grows by the doc's slower factor")
	local function near(x, y)
		return math.abs(x - y) <= 1e-9 * math.max(1, math.abs(y))
	end
	check(near(LayerConfig.BlockHp(40), 100 * 1.5 ^ 39) and near(LayerConfig.BlockHp(41), 100 * 1.5 ^ 39 * tonumber(slower)),
		"level 40 is still 1.5 a level; level 41 grows by the slower factor")
	check(near(LayerConfig.BlockHp(31), 100 * 1.5 ^ 30), "the first run's blocks (up to level 31) are unchanged")

	-- Crack stages and block size.
	local stages = doc:Table({ "Damage", "What changes" })
	check(#stages == #LayerConfig.Block.CrackStages, "five crack stages")
	for index, row in stages do
		check(LayerConfig.Block.CrackStages[index] == DesignDoc.Number(row.Damage), "crack stage " .. index .. " at " .. row.Damage)
	end
	check(tonumber(string.match(text, "(%d+) studs tall at level 1")) == LayerConfig.Block.HeightAtFirstLevel, "the block is 14 studs tall at level 1")
	check(tonumber(string.match(text, "growing to (%d+) studs by level 50")) == LayerConfig.Block.HeightAtLevel50, "...and 20 by level 50")

	return passed
end
