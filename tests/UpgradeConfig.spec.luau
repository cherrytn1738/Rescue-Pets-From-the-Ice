-- UpgradeConfig matches docs/GAME_DESIGN.md ("Economy" and "Upgrades in detail").
-- Run: python tools/run_specs.py UpgradeConfig
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
	local chunk = assert(loadstring(sources.UpgradeConfig, "UpgradeConfig"))
	setfenv(chunk, setmetatable({
		script = { Parent = { BuildingConfig = BuildingConfig } },
		require = function(module)
			return module
		end,
	}, { __index = getfenv(1) }))
	local UpgradeConfig = chunk()

	-- Ice pick tiers.
	local picks = doc:Table({ "Tier", "Pick", "Tap damage", "Cost (crystals)" })
	check(#picks == #UpgradeConfig.IcePick, "six ice pick tiers")
	for index, row in picks do
		local tier = UpgradeConfig.IcePick[index]
		check(tier.Tier == DesignDoc.Number(row.Tier) and tier.Name == row.Pick, "tier " .. index .. " is the " .. row.Pick)
		check(tier.TapDamage == DesignDoc.Number(row["Tap damage"]), row.Pick .. " deals " .. row["Tap damage"])
		check(tier.Cost == (DesignDoc.Number(row["Cost (crystals)"]) or 0), row.Pick .. " costs " .. row["Cost (crystals)"])
		if index > 1 then
			local previous = UpgradeConfig.IcePick[index - 1]
			check(tier.TapDamage == previous.TapDamage * 2, row.Pick .. " doubles tap damage")
			check(index == 2 or tier.Cost == previous.Cost * 10, row.Pick .. " costs 10 times the last")
		end
	end

	-- Frost Touch.
	local touches = doc:Table({ "Upgrade", "Effect", "Cost (crystals)", "Unlocks when" })
	check(#touches == #UpgradeConfig.FrostTouch, "three Frost Touch tiers")
	for index, row in touches do
		local touch = UpgradeConfig.FrostTouch[index]
		check(touch.Name == row.Upgrade, "Frost Touch " .. index .. " is " .. row.Upgrade)
		check(math.abs(touch.TapShareOfBuildingDps - DesignDoc.Number(row.Effect) / 100) < 1e-12, row.Upgrade .. " adds " .. row.Effect)
		check(touch.Cost == DesignDoc.Number(row["Cost (crystals)"]), row.Upgrade .. " costs " .. row["Cost (crystals)"])
		local building = BuildingConfig.Get(touch.UnlockOwns)
		check(building and string.find(row["Unlocks when"], building.Name, 1, true), row.Upgrade .. " unlocks with " .. row["Unlocks when"])
	end

	-- Building upgrades.
	local tiers = doc:Table({ "Upgrade", "Unlocks at", "Cost" })
	local rules = UpgradeConfig.BuildingUpgrades
	check(#tiers == 5 and #rules.UnlockAtOwned == 5, "five upgrades per building")
	for index, row in tiers do
		check(rules.UnlockAtOwned[index] == DesignDoc.Number(row["Unlocks at"]), "building upgrade " .. index .. " unlocks at " .. row["Unlocks at"])
		check(rules.CostMultipliers[index] == DesignDoc.Number(row.Cost), "building upgrade " .. index .. " costs base × " .. tostring(DesignDoc.Number(row.Cost)))
	end
	check(string.find(text, "Each doubles that building's damage", 1, true) and rules.DamageMultiplier == 2, "each doubles the building's damage")
	local buildingUpgrades = 0
	for _, upgrade in UpgradeConfig.Upgrades do
		if upgrade.Kind == "Building" then
			buildingUpgrades += 1
			local building = BuildingConfig.Get(upgrade.Building)
			check(upgrade.Cost == building.BaseCost * rules.CostMultipliers[upgrade.Index], upgrade.Id .. " costs base × multiplier")
		end
	end
	check(buildingUpgrades == 40 and string.find(text, "five per building (40 in all)", 1, true), "40 building upgrades")

	-- Ice upgrades.
	local ice = doc:Table({ "Upgrade", "Effect", "Tiers", "Tier costs (crystals)" })
	check(#ice == #UpgradeConfig.IceUpgrades, "three ice upgrades")
	for index, row in ice do
		local upgrade = UpgradeConfig.IceUpgrades[index]
		check(upgrade.Name == row.Upgrade and upgrade.Id == DesignDoc.IdOf(row.Upgrade), "ice upgrade " .. index .. " is " .. row.Upgrade)
		check(upgrade.Tiers == DesignDoc.Number(row.Tiers), row.Upgrade .. " has " .. row.Tiers .. " tiers")
		local costs = {}
		for cell in string.gmatch(row["Tier costs (crystals)"], "[^/]+") do
			table.insert(costs, DesignDoc.Number(cell))
		end
		check(#costs == upgrade.Tiers and table.concat(costs, ",") == table.concat(upgrade.Costs, ","), row.Upgrade .. " tiers cost " .. row["Tier costs (crystals)"])
		for tier, cost in costs do
			check(UpgradeConfig.Get(upgrade.Id .. tier).Cost == cost, upgrade.Id .. tier .. " costs " .. cost)
		end
	end
	local burst = {}
	for seconds in string.gmatch(ice[1].Effect, "(%d+)") do
		table.insert(burst, tonumber(seconds))
	end
	check(table.concat(burst, ",") == table.concat(UpgradeConfig.IceUpgrades[1].BurstSeconds, ","), "Bigger Burst: 30 → 45 → 60 seconds")
	check(DesignDoc.Number(ice[2].Effect) / 100 == UpgradeConfig.IceUpgrades[2].YieldPerTier, "Crystal Yield: +10% per tier")
	check(DesignDoc.Number(ice[3].Effect) == UpgradeConfig.IceUpgrades[3].SecondsSoonerPerTier, "Fast Sled: 1 second sooner per tier")

	-- The full list.
	local ids, total = {}, 0
	for _, upgrade in UpgradeConfig.Upgrades do
		check(not ids[upgrade.Id] and UpgradeConfig.Get(upgrade.Id) == upgrade, "upgrade ids are unique and findable: " .. upgrade.Id)
		ids[upgrade.Id] = true
		total += 1
		check(type(upgrade.Cost) == "number" and upgrade.Cost > 0, upgrade.Id .. " has a positive cost")
	end
	check(total >= 50 and total <= 70 and string.find(text, "About 60 in all at launch", 1, true), "about 60 upgrades in all (" .. total .. ")")
	check(UpgradeConfig.Get("IcePick1") == nil, "the wooden pick is the start, not an upgrade")

	return passed
end
