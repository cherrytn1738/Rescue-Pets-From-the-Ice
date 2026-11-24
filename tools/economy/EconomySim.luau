--[[
EconomySim: plays the game's economy from the real config modules (LayerConfig, BuildingConfig,
UpgradeConfig, CreatureConfig, RebirthConfig) and the real rules (EconomyRules, BlockRules,
PetRules), and checks the design doc's targets (docs/GAME_DESIGN.md, "Economy"):
  - the first building within 30 s
  - the first rescue within 60 s
  - the first rebirth after about 30-40 minutes (reaching Layer 4, level RebirthConfig.RequiredLevel)
Run: python tools/economy_sim.py  (Studio open in Edit mode, like the spec runner)

The simulated player:
  - taps at a steady rate (each scenario sets taps per second), only while a block is on the mound;
  - buys greedily: whatever item pays for itself soonest (cost / extra income, plus the time to
    afford it), as soon as it can afford it. "Income" counts the dead time while the sled brings the
    next block and the rescue fountain, so Fast Sled and Bigger Burst are valued too;
  - keeps every rescued pet, equips the best ones it has slots for, and combines 5 into a Golden;
  - (the report notes when the rebirth level is reached and how many Frost Cores it would earn).
Pet rolls use a fixed seed, so a run repeats exactly.
]]
return function(sources)
	local modules = {}
	local function load(name)
		local chunk = assert(loadstring(sources[name], name))
		setfenv(chunk, setmetatable({
			game = { GetService = function(_, service)
				assert(service == "ReplicatedStorage", "the sim only has the replicated modules")
				return modules
			end },
			script = { Parent = modules },
			require = function(module)
				return module
			end,
		}, { __index = getfenv(1) }))
		modules[name] = chunk()
		return modules[name]
	end
	for _, name in { "BuildingConfig", "CreatureConfig", "LayerConfig", "RebirthConfig", "UpgradeConfig", "EconomyRules", "BlockRules", "PetRules" } do
		load(name)
	end
	local BuildingConfig, LayerConfig, RebirthConfig, UpgradeConfig = modules.BuildingConfig, modules.LayerConfig, modules.RebirthConfig, modules.UpgradeConfig
	local EconomyRules, BlockRules, PetRules, CreatureConfig = modules.EconomyRules, modules.BlockRules, modules.PetRules, modules.CreatureConfig

	local DT = 0.25

	local function newSave()
		return {
			Crystals = 0, CrystalsThisRun = 0, CrystalsAllTime = 0, BlockLevel = 1, Buildings = {}, Upgrades = {},
			Pets = {}, Equipped = {}, BookSeen = {}, BookGolden = {}, FrostCores = 0, Rebirths = 0,
			MaxLayerOpened = LayerConfig.FloorLayer, CreaturesRescued = 0,
		}
	end

	local function deepCopy(value)
		if type(value) ~= "table" then
			return value
		end
		local copy = {}
		for k, v in value do
			copy[k] = deepCopy(v)
		end
		return copy
	end

	-- Steady-state crystals per second for this save at `taps` taps a second, counting the sled's dead
	-- time and the rescue fountain.
	local runWith
	local function income(data, taps)
		local damage = EconomyRules.TapDamage(data) * taps + EconomyRules.TotalBuildingDps(data)
		local mult = EconomyRules.Multiplier(data)
		if damage <= 0 then
			return 0
		end
		local blockTime = LayerConfig.BlockHp(data.BlockLevel) / damage
		local cycle = blockTime + EconomyRules.SledSeconds(data)
		local perSecond = damage * mult
		return (perSecond * blockTime + EconomyRules.BurstSeconds(data) * perSecond) / cycle
	end

	-- Every item the player could buy now (or save up for): { kind, id, cost, apply(data) }.
	local function candidates(data)
		local list = {}
		for _, building in BuildingConfig.Buildings do
			local owned = data.Buildings[building.Id] or 0
			table.insert(list, { kind = "Building", id = building.Id, cost = BuildingConfig.Cost(building, owned), apply = function(d)
				d.Buildings[building.Id] = (d.Buildings[building.Id] or 0) + 1
			end })
		end
		for _, upgrade in UpgradeConfig.Upgrades do
			if EconomyRules.UpgradeUnlocked(data, upgrade.Id) then
				table.insert(list, { kind = "Upgrade", id = upgrade.Id, cost = upgrade.Cost, apply = function(d)
					table.insert(d.Upgrades, upgrade.Id)
				end })
			end
		end
		return list
	end

	-- The item that pays back soonest: cost / extra income + time to afford it.
	local function bestBuy(data, taps)
		local now = income(data, taps)
		local best, bestScore = nil, math.huge
		for _, item in candidates(data) do
			local copy = deepCopy(data)
			item.apply(copy)
			local gain = income(copy, taps) - now
			if gain > 0 then
				local wait = math.max(0, item.cost - data.Crystals) / math.max(now, 1e-9)
				local score = item.cost / gain + wait
				if score < bestScore then
					best, bestScore = item, score
				end
			end
		end
		return best
	end

	local function run(scenario)
		local defaultGrowth = LayerConfig.Block.HpGrowth
		LayerConfig.Block.HpGrowth = scenario.hpGrowth or defaultGrowth
		local ok, result = pcall(function()
			return runWith(scenario)
		end)
		LayerConfig.Block.HpGrowth = defaultGrowth
		assert(ok, result)
		return result
	end

	function runWith(scenario)
		local rng = Random.new(scenario.seed or 7)
		local data = newSave()
		local t = 0
		local hp = LayerConfig.BlockHp(1)
		local creature = BlockRules.RollCreature(1, rng:NextNumber(0, 100), rng:NextNumber())
		local sledLeft = 0
		local log = { firstBuilding = nil, firstRescue = nil, layers = {}, rescues = 0, levelAt = {}, coresAt = {} }
		local target = nil
		local tapCarry = 0
		local purchases = 0
		local nextReview = 0
		local limit = scenario.minutes * 60

		local function rescue()
			log.rescues += 1
			log.firstRescue = log.firstRescue or t
			local burst = EconomyRules.BurstSeconds(data) * (EconomyRules.TapDamage(data) * scenario.taps + EconomyRules.TotalBuildingDps(data)) * EconomyRules.Multiplier(data)
			data.Crystals += burst
			data.CrystalsThisRun += burst
			data.BookSeen[creature.Id] = (data.BookSeen[creature.Id] or 0) + 1
			if #data.Pets < CreatureConfig.Pets.InventorySize then
				table.insert(data.Pets, { Uid = tostring(log.rescues), CreatureId = creature.Id, Golden = false })
			end
			-- combine any five of a kind
			for _, pet in table.clone(data.Pets) do
				local group = PetRules.CombineGroup(data.Pets, pet.Uid, data.Equipped)
				if group then
					for _, uid in group do
						for i, p in data.Pets do
							if p.Uid == uid then
								table.remove(data.Pets, i)
								break
							end
						end
					end
					table.insert(data.Pets, { Uid = "g" .. log.rescues, CreatureId = pet.CreatureId, Golden = true })
					data.BookGolden[pet.CreatureId] = true
					break
				end
			end
			data.Equipped = PetRules.Best(data.Pets, PetRules.Slots(data.Rebirths, 0))
			data.BlockLevel += 1
			log.levelAt[data.BlockLevel] = t
			local layer = LayerConfig.LayerForLevel(data.BlockLevel, data.MaxLayerOpened)
			if not log.layers[layer.Number] then
				log.layers[layer.Number] = t
			end
			sledLeft = EconomyRules.SledSeconds(data)
			hp = LayerConfig.BlockHp(data.BlockLevel)
			creature = BlockRules.RollCreature(layer.Number, rng:NextNumber(0, 100), rng:NextNumber())
		end

		while t < limit do
			t += DT
			if sledLeft > 0 then
				sledLeft -= DT
			else
				tapCarry += scenario.taps * DT
				local taps = math.floor(tapCarry)
				tapCarry -= taps
				local damage = taps * EconomyRules.TapDamage(data) + EconomyRules.TotalBuildingDps(data) * DT
				local crystals = damage * EconomyRules.Multiplier(data)
				data.Crystals += crystals
				data.CrystalsThisRun += crystals
				hp -= damage
				if hp <= 0 then
					rescue()
				end
			end
			-- shopping: the plan is reviewed every few seconds (income changes with rescues and pets)
			if t >= nextReview then
				nextReview = t + 5
				target = bestBuy(data, scenario.taps)
			end
			if not log.firstBuilding then
				-- the tutorial's step 2: "At 15 crystals, build an Ice Pick Post"
				local post = BuildingConfig.Get("IcePickPost")
				target = { kind = "Building", id = post.Id, cost = BuildingConfig.Cost(post, 0), apply = function(d)
					d.Buildings[post.Id] = (d.Buildings[post.Id] or 0) + 1
				end }
			end
			while target and data.Crystals >= target.cost do
				data.Crystals -= target.cost
				target.apply(data)
				purchases += 1
				if target.kind == "Building" and not log.firstBuilding then
					log.firstBuilding = t
				end
				target = bestBuy(data, scenario.taps)
			end
			for _, cores in { 1, 2, 3, 5 } do
				if not log.coresAt[cores] and data.BlockLevel >= RebirthConfig.RequiredLevel and RebirthConfig.FrostCoresFor(data.CrystalsThisRun) >= cores then
					log.coresAt[cores] = t
				end
			end
		end
		log.data = data
		log.income = income(data, scenario.taps)
		return log
	end

	local function mmss(seconds)
		if not seconds then
			return "never"
		end
		return string.format("%d:%02d", seconds // 60, math.floor(seconds % 60))
	end

	local lines = {}
	local function say(text)
		table.insert(lines, text)
	end
	local scenarios = {
		{ name = "Relaxed (2 taps/s)", taps = 2, minutes = 120 },
		{ name = "Normal (4 taps/s)", taps = 4, minutes = 120 },
		{ name = "Fast (7 taps/s)", taps = 7, minutes = 120 },
		{ name = "Capped (20 taps/s)", taps = 20, minutes = 120 },
	}
	for _, scenario in scenarios do
		local log = run(scenario)
		local data = log.data
		say(`== {scenario.name} ==`)
		say(`first building {mmss(log.firstBuilding)} (target <= 0:30)  first rescue {mmss(log.firstRescue)} (target <= 1:00)`)
		local layerLine = {}
		for layer = 2, 5 do
			table.insert(layerLine, `L{layer} {mmss(log.layers[layer])}`)
		end
		say("layers reached: " .. table.concat(layerLine, "  "))
		local lv = {}
		for _, level in { 5, 10, 15, 21, 25, 30, 35, 40 } do
			table.insert(lv, `{level}:{mmss(log.levelAt[level])}`)
		end
		say("levels: " .. table.concat(lv, " "))
		local pace = {}
		for _, range in { { 1, 10 }, { 11, 20 }, { 21, 30 }, { 31, 40 } } do
			local from, to = log.levelAt[range[1] + 1] or (if range[1] == 1 then 0 else nil), log.levelAt[range[2] + 1]
			if from and to then
				table.insert(pace, `levels {range[1]}-{range[2]}: {string.format("%.1f", (to - from) / (range[2] - range[1] + (if range[1] == 1 then 1 else 0)) / 60)} min/rescue`)
			end
		end
		say("rescue pace (target 1-3 min): " .. table.concat(pace, ", "))
		say(`rebirth unlocked (level {RebirthConfig.RequiredLevel}) {mmss(log.levelAt[RebirthConfig.RequiredLevel])}; worth 1 Frost Core {mmss(log.coresAt[1])}, 2 cores {mmss(log.coresAt[2])}, 3 cores {mmss(log.coresAt[3])}, 5 cores {mmss(log.coresAt[5])} (target: first rebirth 30-40 min)`)
		local owned = {}
		for _, building in BuildingConfig.Buildings do
			if data.Buildings[building.Id] then
				table.insert(owned, `{building.Id} {data.Buildings[building.Id]}`)
			end
		end
		say(`after {scenario.minutes} min: level {data.BlockLevel}, {log.rescues} rescues, {#data.Upgrades} upgrades, crystals this run {string.format("%.3g", data.CrystalsThisRun)}, income {string.format("%.3g", log.income)}/s, pets bonus +{math.floor(EconomyRules.PetBonus(data) * 100)}%`)
		say("buildings: " .. table.concat(owned, ", "))
	end
	return table.concat(lines, "\n")
end
