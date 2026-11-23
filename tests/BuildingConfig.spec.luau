-- BuildingConfig matches docs/GAME_DESIGN.md ("Economy", "Buildings in detail", "Detail levels",
-- "Plot and map layout"). Run: python tools/run_specs.py BuildingConfig
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	local DesignDoc = assert(loadstring(sources.DesignDoc))()
	local doc = DesignDoc.new(sources["GAME_DESIGN.md"])
	local text = sources["GAME_DESIGN.md"]
	local BuildingConfig = assert(loadstring(sources.BuildingConfig))()
	local buildings = BuildingConfig.Buildings

	-- Cost and damage.
	local economy = doc:Table({ "Building", "How it breaks the ice", "Base cost (crystals)", "Damage per second" })
	check(#economy == 8 and #buildings == 8, "eight buildings")
	for index, row in economy do
		local building = buildings[index]
		check(building.Name == row.Building and building.Id == DesignDoc.IdOf(row.Building), "building " .. index .. " is " .. row.Building)
		check(building.Breaks == row["How it breaks the ice"], row.Building .. ": how it breaks the ice")
		check(building.BaseCost == DesignDoc.Number(row["Base cost (crystals)"]), row.Building .. " costs " .. row["Base cost (crystals)"])
		check(building.DamagePerSecond == DesignDoc.Number(row["Damage per second"]), row.Building .. " deals " .. row["Damage per second"] .. "/s")
	end

	-- Stations and upgrade parts.
	local looks = doc:Table({ "Building", "1 owned", "10", "25", "50", "100" })
	for index, row in looks do
		local building = buildings[index]
		check(building.Name == row.Building, "station row " .. index .. " is " .. row.Building)
		for milestone, header in { "1 owned", "10", "25", "50", "100" } do
			check(building.Stations[milestone] == row[header], row.Building .. " station at " .. header)
		end
		check(building.UpgradeParts == row["Upgrade parts (in order)"], row.Building .. " upgrade parts")
	end
	local milestones = doc:Table({ "Owned", "Ice Pick Post station" })
	for index, row in milestones do
		check(BuildingConfig.StationMilestones[index] == DesignDoc.Number(row.Owned), "station milestone " .. index .. " at " .. row.Owned)
	end

	-- Pads.
	local function signed(cell)
		local value = DesignDoc.Number(cell)
		if string.find(cell, "−", 1, true) or string.find(cell, "-", 1, true) then
			value = -value
		end
		return value
	end
	local pads = doc:Table({ "Pad", "Building", "Position (X, Z)", "Pad size" })
	check(#pads == 8, "eight pads")
	for _, row in pads do
		local name = string.gsub(row.Building, "%s*%b()", "")
		local building = BuildingConfig.Get(DesignDoc.IdOf(name))
		check(building ~= nil, "the pad's building exists: " .. name)
		local x, z = string.match(row["Position (X, Z)"], "^%(([^,]+),%s*([^%)]+)%)$")
		check(building.Pad.Index == DesignDoc.Number(row.Pad), name .. " is on pad " .. row.Pad)
		check(building.Pad.X == signed(x) and building.Pad.Z == signed(z), name .. " pad at " .. row["Position (X, Z)"])
		check(building.Pad.Size == DesignDoc.Number(row["Pad size"]), name .. " pad size " .. row["Pad size"])
	end

	-- Rules.
	check(string.find(text, "Each copy costs 15% more than the last", 1, true) and BuildingConfig.CostGrowth == 1.15, "each copy costs 15% more")
	check(string.find(text, "\\text{base} \\times 1.15^{\\,n}", 1, true) ~= nil, "the doc's cost formula uses 1.15^n")
	local pick = BuildingConfig.Get("IcePickPost")
	check(BuildingConfig.Cost(pick, 0) == 15 and math.abs(BuildingConfig.Cost(pick, 2) - 15 * 1.15 ^ 2) < 1e-9, "cost(n) = base × 1.15^n")
	local together = BuildingConfig.Cost(pick, 4) + BuildingConfig.Cost(pick, 5) + BuildingConfig.Cost(pick, 6)
	check(math.abs(BuildingConfig.CostOfNext(pick, 4, 3) - together) < 1e-6, "the cost of the next k is the sum of their costs")
	check(tonumber(string.match(text, "A Masterwork also deals %+(%d+)%% damage")) / 100 == BuildingConfig.MasterworkBonus, "Masterwork +10% damage")
	check(tonumber(string.match(text, "shrinks to (%d+)%%")) / 100 == BuildingConfig.FadedScale, "older stations shrink to 60%")
	check(tonumber(string.match(text, "Each plot is a (%d+) × %d+ stud square")) == BuildingConfig.PlotSize, "a 100 × 100 plot")
	check(string.find(text, "detail level from 0 to 10", 1, true) and BuildingConfig.MaxDetailLevel == 10, "detail levels go to 10")

	return passed
end
