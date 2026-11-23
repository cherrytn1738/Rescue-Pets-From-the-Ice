-- CreatureConfig matches docs/GAME_DESIGN.md ("Pets", "Creature roster", "The Creature Book").
-- Run: python tools/run_specs.py CreatureConfig
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local DesignDoc = assert(loadstring(sources.DesignDoc))()
	local doc = DesignDoc.new(sources["GAME_DESIGN.md"])
	local text = sources["GAME_DESIGN.md"]
	local CreatureConfig = assert(loadstring(sources.CreatureConfig))()
	local LayerConfig = assert(loadstring(sources.LayerConfig))()

	local function layerNumberNamed(name)
		for _, layer in LayerConfig.Layers do
			if layer.Name == name then
				return layer.Number
			end
		end
		return nil
	end

	-- Rarities: bonus and glow.
	local bonusRows = doc:Table({ "Rarity", "Crystal bonus when equipped" })
	check(#bonusRows == #CreatureConfig.Rarities, "six rarities")
	for index, row in bonusRows do
		local rarity = CreatureConfig.Rarities[index]
		check(rarity.Id == row.Rarity, "rarity " .. index .. " is " .. row.Rarity)
		check(math.abs(rarity.Bonus - DesignDoc.Number(row["Crystal bonus when equipped"]) / 100) < 1e-9, row.Rarity .. " bonus is " .. row["Crystal bonus when equipped"])
		check(string.lower(rarity.Glow) == string.lower(DesignDoc.IdOf(row["Glow through the ice"])), row.Rarity .. " glows " .. row["Glow through the ice"])
	end
	for _, row in doc:Table({ "Rarity", "Glow through the ice" }) do
		local told = string.find(row["Glow through the ice"], "server is told", 1, true) ~= nil
		for rarityName in string.gmatch(row.Rarity, "%a+") do
			check(CreatureConfig.GetRarity(rarityName).Announce == told, rarityName .. (if told then " blocks are" else " blocks aren't") .. " announced")
		end
	end

	-- The roster.
	local roster = doc:Table({ "Creature", "Rarity", "First found in", "Look" })
	check(#roster == 18 and #CreatureConfig.Creatures == 18, "18 creatures")
	local ids = {}
	for index, row in roster do
		local creature = CreatureConfig.Creatures[index]
		check(creature.Name == row.Creature and creature.Id == DesignDoc.IdOf(row.Creature), "creature " .. index .. " is " .. row.Creature)
		check(creature.Rarity == row.Rarity, row.Creature .. " is " .. row.Rarity)
		check(creature.FirstLayer == layerNumberNamed(row["First found in"]), row.Creature .. " is first found in " .. row["First found in"])
		check(creature.Look == row.Look, row.Creature .. "'s look matches the doc")
		check(not ids[creature.Id], "ids are unique: " .. creature.Id)
		ids[creature.Id] = true
	end
	local poolLine = string.match(text, "%*%*Pool:%*%*[^\n]*%(([^%)]+)%)")
	for count, rarityName in string.gmatch(poolLine, "(%d+) (%a+)") do
		local have = 0
		for _, creature in CreatureConfig.Creatures do
			if creature.Rarity == rarityName then
				have += 1
			end
		end
		check(have == tonumber(count), rarityName .. ": " .. count .. " creatures")
	end
	-- Every rarity a layer can roll has a creature to roll.
	for _, layer in LayerConfig.Layers do
		for rarityName, odds in layer.Odds do
			local found = false
			for _, creature in CreatureConfig.PoolForLayer(layer.Number) do
				found = found or creature.Rarity == rarityName
			end
			check(odds <= 0 or found, layer.Name .. " can roll a " .. rarityName .. " creature")
		end
	end

	-- Pet rules.
	local pets = CreatureConfig.Pets
	check(tonumber(string.match(text, "%*%*Inventory:%*%* (%d+) pets")) == pets.InventorySize, "inventory of 50")
	check(string.find(text, "**Equip slots:** 1 at the start", 1, true) and pets.BaseEquipSlots == 1, "1 equip slot at the start")
	check(tonumber(string.match(text, "for a maximum of (%d+)")) == pets.MaxEquipSlots, "at most 7 slots")
	check(tonumber(string.match(text, "combine (%d+) of the same pet into a Golden version with double the bonus")) == pets.GoldenCombineCount
		and pets.GoldenBonusMultiplier == 2, "5 make a Golden pet with double the bonus")

	-- Creature Book pages.
	local pages = doc:Table({ "Page completed", "Permanent reward" })
	check(#pages == #CreatureConfig.Book, "seven book pages")
	for index, row in pages do
		local page = CreatureConfig.Book[index]
		local name, count = string.match(row["Page completed"], "^(%a+) %(%D*(%d+)%)$")
		check(page.Page == name and page.Count == tonumber(count), "page " .. index .. " is " .. name .. " (" .. count .. ")")
		local reward = row["Permanent reward"]
		local bonus = string.match(reward, "%+(%d+)%% crystals")
		check(page.CrystalBonus == (if bonus then tonumber(bonus) / 100 else nil), name .. " page bonus: " .. reward)
		if string.find(reward, "frosty name-tag border", 1, true) then
			check(page.NameTagBorder == "Frosty", name .. " page: frosty border")
		elseif string.find(reward, "golden name-tag border", 1, true) then
			check(page.NameTagBorder == "Golden", name .. " page: golden border")
		end
		if string.find(reward, "aurora trail", 1, true) then
			check(page.Trail == "Aurora", name .. " page: aurora trail")
		end
		if string.find(reward, "Ice Keeper", 1, true) then
			check(page.Title == "Ice Keeper" and page.PickSkin == "Golden", name .. " page: Ice Keeper title and golden pick")
		end
	end

	return passed
end
