--[[
EconomySim: plays the game's economy from the real config modules (LayerConfig, BuildingConfig,
UpgradeConfig, CreatureConfig, RebirthConfig) and the real rules (EconomyRules, BlockRules,
PetRules), and checks the design doc's targets (docs/GAME_DESIGN.md, "Economy"):
  - the first building within 30 s
  - the first rescue within 60 s
  - the first rebirth after about 30-40 minutes (reaching Layer 4, level RebirthConfig.RequiredLevel)
  - a new tool about every 2-3 minutes in the first run, the top tools only in later runs (layers 5-6)
  - taps a meaningful share of the damage all run (the share at each layer, with and without Frost Touch)
Run: python tools/economy_sim.py  (Studio open in Edit mode, like the spec runner)
     python tools/economy_sim.py --first   (the first runs only: quicker)

The simulated player:
  - taps at a steady rate (each scenario sets taps per second), only while a block is on the mound;
  - buys greedily: whatever item pays for itself soonest (cost / extra income, plus the time to
    afford it), as soon as it can afford it. "Income" counts the dead time while the sled brings the
    next block and the rescue fountain, so Fast Sled and Bigger Burst are valued too;
  - keeps every rescued pet, equips the best ones it has slots for, and combines 5 into a Golden;
  - rebirths (RebirthService's rules) once it is past the rebirth level and a new block would take longer than
    REBIRTH_WHEN_BLOCK_OVER seconds to break (the pull to rebirth), or the run passes MAX_RUN_MINUTES.
Pet rolls use a fixed seed, so a run repeats exactly. Every tap speed plays its first run on three seeds (averaged), and
the 4 taps/s player plays the same three seeds run after run (ten runs each).
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
	for _, name in { "BuildingConfig", "CreatureConfig", "LayerConfig", "RebirthConfig", "UpgradeConfig", "NumberFormat", "EconomyRules", "BlockRules", "PetRules" } do
		load(name)
	end
	local BuildingConfig, LayerConfig, RebirthConfig, UpgradeConfig = modules.BuildingConfig, modules.LayerConfig, modules.RebirthConfig, modules.UpgradeConfig
	local EconomyRules, BlockRules, PetRules, CreatureConfig = modules.EconomyRules, modules.BlockRules, modules.PetRules, modules.CreatureConfig
	local NumberFormat = modules.NumberFormat

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

	local REBIRTH_WHEN_BLOCK_OVER = 240 -- seconds: a block slower than this to break, past the rebirth level, means rebirth
	local MAX_RUN_MINUTES = 75

	local function mmss(seconds)
		if not seconds then
			return "never"
		end
		return string.format("%d:%02d", seconds // 60, math.floor(seconds % 60))
	end

	-- RebirthService's rules: Frost Cores for the run, the rank's layers and slots, the run's fields reset.
	local function rebirth(data)
		local cores = RebirthConfig.FrostCoresFor(data.CrystalsThisRun)
		data.FrostCores += cores
		data.Rebirths += 1
		data.MaxLayerOpened = math.max(data.MaxLayerOpened, RebirthConfig.MaxLayerFor(data.Rebirths, LayerConfig.FloorLayer, #LayerConfig.Layers))
		data.Crystals, data.CrystalsThisRun, data.BlockLevel = 0, 0, 1
		data.Buildings, data.Upgrades = {}, {}
		data.Equipped = PetRules.Best(data.Pets, PetRules.Slots(data.Rebirths, 0))
		return cores
	end

	-- One run, from a fresh run (level 1, nothing bought) until the rebirth (or `scenario.minutes`).
	local function playRun(data, scenario, rng, clock)
		local taps = scenario.taps
		local t = 0
		local hp = LayerConfig.BlockHp(1)
		local layer = LayerConfig.LayerForLevel(1, data.MaxLayerOpened)
		local creature = BlockRules.RollCreature(layer.Number, rng:NextNumber(0, 100), rng:NextNumber())
		local sledLeft = 0
		local log = { firstBuilding = nil, firstRescue = nil, layers = {}, rescues = 0, levelAt = {}, coresAt = {},
			tools = {}, share = {} }
		local target = nil
		local tapCarry = 0
		local nextReview = 0
		local limit = (scenario.minutes or MAX_RUN_MINUTES) * 60
		local rebirthNow = false
		local nextSample = 0
		log.samples = {}

		local function rescue()
			log.rescues += 1
			log.firstRescue = log.firstRescue or t
			local burst = EconomyRules.BurstSeconds(data) * (EconomyRules.TapDamage(data) * taps + EconomyRules.TotalBuildingDps(data)) * EconomyRules.Multiplier(data)
			data.Crystals += burst
			data.CrystalsThisRun += burst
			data.BookSeen[creature.Id] = (data.BookSeen[creature.Id] or 0) + 1
			if #data.Pets < CreatureConfig.Pets.InventorySize then
				table.insert(data.Pets, { Uid = tostring(clock.uid), CreatureId = creature.Id, Golden = false })
				clock.uid += 1
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
					table.insert(data.Pets, { Uid = "g" .. clock.uid, CreatureId = pet.CreatureId, Golden = true })
					clock.uid += 1
					data.BookGolden[pet.CreatureId] = true
					break
				end
			end
			data.Equipped = PetRules.Best(data.Pets, PetRules.Slots(data.Rebirths, 0))
			data.BlockLevel += 1
			log.levelAt[data.BlockLevel] = t
			layer = LayerConfig.LayerForLevel(data.BlockLevel, data.MaxLayerOpened)
			if not log.layers[layer.Number] then
				log.layers[layer.Number] = t
			end
			sledLeft = EconomyRules.SledSeconds(data)
			hp = LayerConfig.BlockHp(data.BlockLevel)
			creature = BlockRules.RollCreature(layer.Number, rng:NextNumber(0, 100), rng:NextNumber())
			if not scenario.minutes and data.BlockLevel >= RebirthConfig.RequiredLevel then
				local damage = EconomyRules.TapDamage(data) * taps + EconomyRules.TotalBuildingDps(data)
				if hp / damage > REBIRTH_WHEN_BLOCK_OVER then
					rebirthNow = true
				end
			end
		end

		while t < limit and not rebirthNow do
			t += DT
			if sledLeft > 0 then
				sledLeft -= DT
			else
				tapCarry += taps * DT
				local count = math.floor(tapCarry)
				tapCarry -= count
				local toolDamage = UpgradeConfig.Tools[EconomyRules.ToolTier(data)].TapDamage
				local tapDamage = EconomyRules.TapDamage(data)
				local buildingDps = EconomyRules.TotalBuildingDps(data)
				local damage = count * tapDamage + buildingDps * DT
				-- the share of damage from taps, per layer (at the steady tap rate, not the tap carry)
				local share = log.share[layer.Number] or { tool = 0, taps = 0, total = 0 }
				log.share[layer.Number] = share
				share.tool += toolDamage * taps * DT
				share.taps += tapDamage * taps * DT
				share.total += (tapDamage * taps + buildingDps) * DT
				local crystals = damage * EconomyRules.Multiplier(data)
				data.Crystals += crystals
				data.CrystalsThisRun += crystals
				hp -= damage
				if hp <= 0 then
					rescue()
				end
			end
			if t >= nextSample then
				nextSample += 60
				table.insert(log.samples, { t = t, level = data.BlockLevel, buildingDps = EconomyRules.TotalBuildingDps(data),
					tapDamage = EconomyRules.TapDamage(data), mult = EconomyRules.Multiplier(data), income = income(data, taps) })
			end
			-- shopping: the plan is reviewed every few seconds (income changes with rescues and pets)
			if t >= nextReview then
				nextReview = t + 5
				target = bestBuy(data, taps)
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
				if target.kind == "Building" and not log.firstBuilding then
					log.firstBuilding = t
				end
				local upgrade = target.kind == "Upgrade" and UpgradeConfig.Get(target.id)
				if upgrade and upgrade.Kind == "Tool" then
					log.tools[upgrade.Tier] = { t = t, level = data.BlockLevel }
				elseif upgrade and upgrade.Kind == "FrostTouch" then
					log.touches = log.touches or {}
					table.insert(log.touches, `{upgrade.Name} {mmss(t)} (L{data.BlockLevel})`)
				end
				target = bestBuy(data, taps)
			end
		end
		log.length = t
		log.level = data.BlockLevel
		log.income = income(data, taps)
		log.petBonus = EconomyRules.PetBonus(data)
		log.crystalsThisRun = data.CrystalsThisRun
		log.toolTier = EconomyRules.ToolTier(data)
		return log
	end

	local function pct(part, whole)
		return if whole > 0 then string.format("%d%%", math.floor(part / whole * 100 + 0.5)) else "-"
	end

	local lines = {}
	local function say(text)
		table.insert(lines, text)
	end

	local function sayFirstRun(log)
		say(`first building {mmss(log.firstBuilding)} (target <= 0:30)  first rescue {mmss(log.firstRescue)} (target <= 1:00)`)
		local layerLine = {}
		for number = 2, 5 do
			table.insert(layerLine, `L{number} {mmss(log.layers[number])}`)
		end
		say("layers reached: " .. table.concat(layerLine, "  "))
		local pace = {}
		for _, range in { { 1, 10 }, { 11, 20 }, { 21, 30 } } do
			local from, to = log.levelAt[range[1] + 1] or (if range[1] == 1 then 0 else nil), log.levelAt[range[2] + 1]
			if from and to then
				table.insert(pace, `levels {range[1]}-{range[2]}: {string.format("%.1f", (to - from) / (range[2] - range[1] + (if range[1] == 1 then 1 else 0)) / 60)} min/rescue`)
			end
		end
		say("rescue pace (target 1-3 min): " .. table.concat(pace, ", "))
		say(`rebirth level ({RebirthConfig.RequiredLevel}) at {mmss(log.levelAt[RebirthConfig.RequiredLevel])} (target 30-40 min), worth {RebirthConfig.FrostCoresFor(log.crystalsThisRun)} Frost Cores at the rebirth`)
	end

	local function sayTools(log)
		local parts, last, gaps = {}, 0, {}
		for tier = 2, #UpgradeConfig.Tools do
			local bought = log.tools[tier]
			if bought then
				table.insert(parts, `T{tier} {mmss(bought.t)} (L{bought.level})`)
				table.insert(gaps, bought.t - last)
				last = bought.t
			end
		end
		say("tools bought: " .. (if #parts > 0 then table.concat(parts, ", ") else "none"))
		say("Frost Touch bought: " .. (if log.touches then table.concat(log.touches, ", ") else "none"))
		if #gaps > 0 then
			local total, longest = 0, 0
			for _, gap in gaps do
				total += gap
				longest = math.max(longest, gap)
			end
			say(`  {#gaps} tools, one every {string.format("%.1f", total / #gaps / 60)} min on average (longest wait {string.format("%.1f", longest / 60)} min)`)
		end
	end

	local function sayShare(log)
		local parts = {}
		for number = 1, #LayerConfig.Layers do
			local share = log.share[number]
			if share and share.total > 0 then
				table.insert(parts, `L{number} {pct(share.taps, share.total)} (tool {pct(share.tool, share.total)})`)
			end
		end
		say("tap share of damage by layer, with Frost Touch (the tool alone): " .. table.concat(parts, ", "))
	end

	local only = sources.SimOnly -- (optional) "first": the first runs only
	local SEEDS = 3
	local function seedRng(seed)
		return Random.new(seed * 101)
	end

	-- 1. Every tap speed's first run, three seeds each (the same seeds as the normal player's runs below).
	-- Auto Pick taps 2 a second on top of the player's own; the server takes at most 10 a second (GameConfig.Taps).
	local speeds = {
		{ name = "Relaxed (2 taps/s)", taps = 2 },
		{ name = "Normal (4 taps/s)", taps = 4 },
		{ name = "Normal with Auto Pick (4 + 2 taps/s)", taps = 6 },
		{ name = "Fast (7 taps/s)", taps = 7 },
		{ name = "Capped (10 taps/s, the server's cap)", taps = 10 },
	}
	local rebirthTimes = {}
	for _, scenario in speeds do
		say(`== {scenario.name}, first run, seeds 1-{SEEDS} ==`)
		local times = {}
		local shares = {}
		for seed = 1, SEEDS do
			local data = newSave()
			local log = playRun(data, scenario, seedRng(seed), { uid = 1 })
			say(`-- seed {seed}`)
			sayFirstRun(log)
			sayTools(log)
			sayShare(log)
			table.insert(times, log.levelAt[RebirthConfig.RequiredLevel] or math.huge)
			for number, share in log.share do
				local sum = shares[number] or { tool = 0, taps = 0, total = 0 }
				shares[number] = sum
				sum.tool += share.tool / share.total
				sum.taps += share.taps / share.total
				sum.total += 1
			end
		end
		local total = 0
		for _, t in times do
			total += t
		end
		local parts = {}
		for number = 1, #LayerConfig.Layers do
			local sum = shares[number]
			if sum then
				table.insert(parts, `L{number} {pct(sum.taps, sum.total)} (tool {pct(sum.tool, sum.total)})`)
			end
		end
		table.insert(rebirthTimes, { name = scenario.name, average = total / #times, times = times, share = table.concat(parts, ", ") })
	end

	-- 2. The normal player (4 taps/s), three seeds, run after run.
	local RUNS = if only == "first" then 0 else (tonumber(sources.SimRuns) or 10)
	local summary = {}
	local deepest = {}
	local runSeeds = if RUNS > 0 then SEEDS else 0
	for seed = 1, runSeeds do
		local data = newSave()
		local rng = seedRng(seed)
		local clock = { uid = 1 }
		deepest[seed] = {}
		say(`== Normal (4 taps/s), seed {seed}, run after run ==`)
		for runNumber = 1, RUNS do
			local log = playRun(data, { name = "Normal", taps = 4 }, rng, clock)
			local layer = LayerConfig.LayerForLevel(log.level, data.MaxLayerOpened)
			table.insert(deepest[seed], `{log.level} ({log.length // 60}m)`)
			say(`-- run {runNumber}: Frost Cores {data.FrostCores}, pets +{math.floor(log.petBonus * 100)}%, {log.length // 60} min, deepest level {log.level} (L{layer.Number}), tool T{log.toolTier}, income {string.format("%.3g", log.income)}/s`)
			if seed == 1 and (runNumber == 1 or runNumber == RUNS) then
				local parts = {}
				for _, sample in log.samples do
					table.insert(parts, string.format("%dm L%d B%s tap%s x%.1f I%s", sample.t // 60, sample.level, NumberFormat.Short(sample.buildingDps),
						NumberFormat.Short(sample.tapDamage), sample.mult, NumberFormat.Short(sample.income)))
				end
				say("each minute: " .. table.concat(parts, "; "))
			end
			if runNumber > 1 then
				sayTools(log)
				sayShare(log)
			end
			for tier, bought in log.tools do
				local row = summary[tier] or {}
				summary[tier] = row
				if not row[seed] then
					row[seed] = { run = runNumber, t = bought.t, level = bought.level }
				end
			end
			if runNumber < RUNS then
				rebirth(data)
			end
		end
	end

	say("== Time to the rebirth level (31), first run, the average of seeds 1-3 ==")
	for _, row in rebirthTimes do
		local cells = {}
		for _, t in row.times do
			table.insert(cells, mmss(t))
		end
		say(string.format("%-40s %s  (%s)", row.name, mmss(row.average), table.concat(cells, ", ")))
	end
	say("== Tap share of damage by layer, first run, the average of seeds 1-3, with Frost Touch (the tool alone) ==")
	for _, row in rebirthTimes do
		say(string.format("%-40s %s", row.name, row.share))
	end
	if RUNS > 0 then
		say("== Deepest level each run (4 taps/s; the run's length) ==")
		for seed = 1, SEEDS do
			say(`seed {seed}: ` .. table.concat(deepest[seed], ", "))
		end
		say("== The tools: first bought (4 taps/s, seeds 1 | 2 | 3) ==")
		for _, tool in UpgradeConfig.Tools do
			local row = summary[tool.Tier]
			local cells = {}
			for seed = 1, SEEDS do
				local cell = row and row[seed]
				table.insert(cells, if cell then `run {cell.run} {mmss(cell.t)} L{cell.level}` else "-")
			end
			say(string.format("T%-2d %-15s dmg %-9s cost %-9s %s", tool.Tier, tool.Name, NumberFormat.Short(tool.TapDamage), NumberFormat.Short(tool.Cost), table.concat(cells, " | ")))
		end
	end
	return table.concat(lines, "\n")
end
