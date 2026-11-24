-- RebirthConfig matches docs/GAME_DESIGN.md ("Rebirth", "Pets", "Data and code structure").
-- Run: python tools/run_specs.py RebirthConfig
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local DesignDoc = assert(loadstring(sources.DesignDoc))()
	local doc = DesignDoc.new(sources["GAME_DESIGN.md"])
	local text = sources["GAME_DESIGN.md"]
	local RebirthConfig = assert(loadstring(sources.RebirthConfig))()
	local LayerConfig = assert(loadstring(sources.LayerConfig))()

	-- Frost Cores = floor(cube root(crystals this run / 1,000,000)), +5% crystals each.
	check(string.find(text, "\\sqrt[3]{\\text{crystals earned this run} \\div 1{,}000{,}000}", 1, true) ~= nil
		and RebirthConfig.CrystalsPerCoreUnit == 1_000_000, "the Frost Core formula divides by 1,000,000 under a cube root")
	check(string.find(text, "Frost Cores, which add 5% crystals each", 1, true) and RebirthConfig.FrostCoreBonus == 0.05, "each Frost Core adds 5%")
	for crystals, cores in { [0] = 0, [999_999] = 0, [1_000_000] = 1, [7_999_999] = 1, [8_000_000] = 2, [27_000_000] = 3, [1e15] = 1000, [1e15 - 1e6] = 999 } do
		check(RebirthConfig.FrostCoresFor(crystals) == cores, `{crystals} crystals earn {cores} Frost Cores`)
	end

	-- When.
	local layer, level = string.match(text, "once the player reaches Layer (%d+) %(%a+ %a+, level (%d+)%)")
	check(tonumber(level) == RebirthConfig.RequiredLevel, "rebirth needs level 31")
	check(LayerConfig.Layers[tonumber(layer)].MinLevel == RebirthConfig.RequiredLevel, "...the first level of Layer 4")

	-- Ranks.
	local ranks = doc:Table({ "Rank", "Title", "Name-tag and border colour", "Opens" })
	check(#ranks == #RebirthConfig.Ranks, "five ranks")
	for index, row in ranks do
		local rank = RebirthConfig.Ranks[index]
		check(rank.Rank == DesignDoc.Number(row.Rank) and rank.Title == row.Title, "rank " .. row.Rank .. " is " .. row.Title)
		check(rank.Colour == row["Name-tag and border colour"], row.Title .. " is " .. row["Name-tag and border colour"])
		local slot = tonumber(string.match(row.Opens, "(%d)%a%a pet slot"))
		local opens = tonumber(string.match(row.Opens, "Layer (%d+)"))
		check(rank.PetSlot == slot, row.Title .. " opens pet slot " .. tostring(slot))
		check(rank.OpensLayer == opens, row.Title .. " opens layer " .. tostring(opens))
		if opens and LayerConfig.Layers[opens] then
			check(LayerConfig.Layers[opens].RequiresRebirths == rank.Rank, "Layer " .. opens .. " needs rebirth " .. rank.Rank .. " in LayerConfig too")
		end
	end
	check(RebirthConfig.RankFor(0) == nil and RebirthConfig.RankFor(7).Title == "Core Keeper", "a player keeps the highest rank reached")
	check(RebirthConfig.PetSlotsFor(0, 1) == 1 and RebirthConfig.PetSlotsFor(3, 1) == 2 and RebirthConfig.PetSlotsFor(9, 1) == 3
		and RebirthConfig.PetSlotsFor(10, 1) == 4, "slots: 1, then 2 at rebirth 3, 3 at 6, 4 at 10")
	check(RebirthConfig.MaxLayerFor(2, 5, #LayerConfig.Layers) == 5 and RebirthConfig.MaxLayerFor(3, 5, #LayerConfig.Layers) == 6
		and RebirthConfig.MaxLayerFor(10, 5, #LayerConfig.Layers) == 6, "rebirth 3 opens Frozen Core; Layer 7 waits for its update")

	-- What a rebirth resets, from the save table (PascalCase names in the save).
	local function pascal(name)
		return string.upper(string.sub(name, 1, 1)) .. string.sub(name, 2)
	end
	for _, row in doc:Table({ "Field", "Type", "Reset on rebirth" }) do
		local resets = row["Reset on rebirth"]
		for docName in string.gmatch(row.Field, "%a+") do
			local name = pascal(docName)
			if string.find(resets, "^Yes") or (resets == "This run only" and docName == "crystalsThisRun") then
				check(table.find(RebirthConfig.ResetOnRebirth, name) ~= nil, name .. " resets on rebirth")
				check(table.find(RebirthConfig.KeptOnRebirth, name) == nil, name .. " isn't also kept")
			elseif string.find(resets, "^No") and not string.find(row.Field, "tutorialStep", 1, true) and docName ~= "purchaseIds" then
				check(table.find(RebirthConfig.KeptOnRebirth, name) ~= nil, name .. " is kept on rebirth")
			elseif resets == "This run only" then
				check(table.find(RebirthConfig.KeptOnRebirth, name) ~= nil, name .. " (all time) is kept")
			end
		end
	end

	return passed
end
