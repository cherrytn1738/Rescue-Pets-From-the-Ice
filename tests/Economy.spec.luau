-- Economy spec: EconomyRules and BlockRules (pure rules), and the server's tap cap and shop
-- (TapService, ShopService) against fakes. Run: python tools/run_specs.py Economy
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end
	local function near(a, b)
		return math.abs(a - b) <= 1e-6 * math.max(1, math.abs(b))
	end

	local modules = {}
	local function loadPure(name)
		local chunk = assert(loadstring(sources[name], name))
		setfenv(chunk, setmetatable({
			game = { GetService = function()
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
	for _, name in { "BuildingConfig", "CreatureConfig", "LayerConfig", "RebirthConfig", "UpgradeConfig", "GameConfig", "NumberFormat", "EconomyRules", "BlockRules", "PetRules" } do
		loadPure(name)
	end
	local R, B = modules.EconomyRules, modules.BlockRules
	local BuildingConfig, LayerConfig, UpgradeConfig = modules.BuildingConfig, modules.LayerConfig, modules.UpgradeConfig

	local function save(overrides)
		local data = {
			Crystals = 0, CrystalsThisRun = 0, CrystalsAllTime = 0, BlockLevel = 1, Buildings = {}, Upgrades = {},
			Pets = {}, Equipped = {}, BookSeen = {}, BookGolden = {}, FrostCores = 0, Rebirths = 0, MaxLayerOpened = 5,
		}
		for key, value in overrides or {} do
			data[key] = value
		end
		return data
	end

	-- Taps and the tools ------------------------------------------------------------------------------
	check(R.TapDamage(save()) == 1, "a new player taps for 1 (the Wooden Pick)")
	check(R.TapDamage(save({ Upgrades = { "Tool2", "Tool3", "Tool4" } })) == UpgradeConfig.Tools[4].TapDamage, "the Iron Pick taps for its damage")
	check(R.ToolTier(save({ Upgrades = { "Tool2" } })) == 2, "the tool tier is the best one owned")
	check(R.ToolTier(save({ Upgrades = { "IcePick3" } })) == 1, "an old ice pick id counts for nothing here (PlayerData turns it into tools on load)")
	check(string.find(R.Describe(UpgradeConfig.Get("Tool10")), "damage per tap", 1, true) ~= nil, "a tool's line says its damage per tap")

	-- Buildings ----------------------------------------------------------------------------------------
	local posts = save({ Buildings = { IcePickPost = 10 } })
	check(near(R.BuildingDps(posts, "IcePickPost"), 1), "10 Ice Pick Posts deal 1 damage a second")
	local upgraded = save({ Buildings = { IcePickPost = 10 }, Upgrades = { "IcePickPostUpgrade1", "IcePickPostUpgrade2" } })
	check(near(R.BuildingDps(upgraded, "IcePickPost"), 4), "two building upgrades double it twice")
	check(R.DetailLevel(upgraded, "IcePickPost") == 4, "detail level: 2 count milestones + 2 upgrades")
	local master = save({ Buildings = { HeatLamp = 100 }, Upgrades = { "HeatLampUpgrade1", "HeatLampUpgrade2", "HeatLampUpgrade3", "HeatLampUpgrade4", "HeatLampUpgrade5" } })
	check(R.IsMasterwork(master, "HeatLamp") and R.DetailLevel(master, "HeatLamp") == 10, "100 owned and 5 upgrades is a Masterwork")
	check(near(R.BuildingDps(master, "HeatLamp"), 100 * 1 * 32 * 1.1), "a Masterwork deals +10%")
	check(near(R.TotalBuildingDps(save({ Buildings = { IcePickPost = 10, HeatLamp = 2 } })), 3), "total building damage adds every building")

	-- Frost Touch: taps add a share of building damage
	local touch = save({ Buildings = { WreckingCrane = 1 }, Upgrades = { "FrostTouch1" } })
	check(near(R.TapDamage(touch), 1 + 0.01 * 280), "Frost Touch I: taps add 1% of building damage/s")

	-- Buying: the 1.15 curve, x10, Max
	local count, cost = R.BuildingPurchase(save({ Crystals = 0 }), "IcePickPost", 1)
	check(count == 1 and near(cost, 15), "the first Ice Pick Post costs 15")
	count, cost = R.BuildingPurchase(save({ Buildings = { IcePickPost = 3 } }), "IcePickPost", 10)
	check(count == 10 and near(cost, 15 * 1.15 ^ 3 * (1.15 ^ 10 - 1) / 0.15), "x10 costs the doc's sum")
	local rich = save({ Crystals = 1000 })
	count, cost = R.BuildingPurchase(rich, "IcePickPost", "Max")
	check(cost <= 1000 and BuildingConfig.CostOfNext(BuildingConfig.Get("IcePickPost"), 0, count + 1) > 1000, "Max buys as many as the crystals pay for")
	count = R.BuildingPurchase(save({ Crystals = 3 }), "IcePickPost", "Max")
	check(count == 1, "Max shows at least one copy's price")

	-- Upgrade unlock rules
	check(not R.UpgradeUnlocked(save(), "Tool3"), "tool tiers go in order")
	check(R.UpgradeUnlocked(save(), "Tool2"), "the Stone Hammer is open from the start")
	local deepTools = {}
	for tier = 2, 13 do
		table.insert(deepTools, "Tool" .. tier)
	end
	local gate = UpgradeConfig.Get("Tool14").UnlockLevel
	check(type(gate) == "number" and not R.UpgradeUnlocked(save({ Upgrades = deepTools, BlockLevel = gate - 1 }), "Tool14"), "the deep tools wait for their block level")
	local ok, reason = R.UpgradeUnlocked(save({ Upgrades = deepTools, BlockLevel = gate - 1 }), "Tool14")
	check(not ok and reason == `Reach level {gate}`, "...and say which level")
	check(R.UpgradeUnlocked(save({ Upgrades = deepTools, BlockLevel = gate }), "Tool14"), "...and open there")
	check(not R.UpgradeUnlocked(save(), "IcePickPostUpgrade1"), "a building upgrade needs a copy")
	check(R.UpgradeUnlocked(save({ Buildings = { IcePickPost = 1 } }), "IcePickPostUpgrade1"), "...one copy opens the 1st")
	check(not R.UpgradeUnlocked(save({ Buildings = { IcePickPost = 10 } }), "IcePickPostUpgrade2"), "the 2nd needs the 1st first")
	check(R.UpgradeUnlocked(save({ Buildings = { IcePickPost = 10 }, Upgrades = { "IcePickPostUpgrade1" } }), "IcePickPostUpgrade2"), "...and 10 copies")
	check(not R.UpgradeUnlocked(save(), "FrostTouch1") and R.UpgradeUnlocked(save({ Buildings = { WreckingCrane = 1 } }), "FrostTouch1"), "Frost Touch I needs a Wrecking Crane")
	check(not R.UpgradeUnlocked(save(), "CrystalYield2"), "ice upgrade tiers go in order")
	check(not R.UpgradeUnlocked(save({ Upgrades = { "Tool2" } }), "Tool2"), "an owned upgrade can't be bought again")
	local list = R.UpgradeList(save({ Buildings = { IcePickPost = 1 } }))
	for i = 2, #list do
		check(list[i - 1].Upgrade.Cost <= list[i].Upgrade.Cost, "the upgrade list is sorted by price")
	end

	-- Multipliers
	check(near(R.Multiplier(save()), 1), "a new player's multiplier is 1")
	check(near(R.Multiplier(save({ FrostCores = 4 })), 1.2), "each Frost Core adds 5%")
	check(near(R.Multiplier(save({ Upgrades = { "CrystalYield1", "CrystalYield2" } })), 1.2), "Crystal Yield: +10% per tier")
	local pets = save({ Pets = { { Uid = "a", CreatureId = "SnowBunny", Golden = false }, { Uid = "b", CreatureId = "PolarBearCub", Golden = true } }, Equipped = { "a", "b" } })
	check(near(R.PetBonus(pets), 0.10 + 0.50 * 2), "equipped pets add their bonuses (Golden doubles)")
	check(near(R.Multiplier(pets, 2), (1 + 1.1) * 2), "...and the server's extras multiply on top")
	local book = save({ BookSeen = { SnowBunny = 1, PenguinChick = 2, FrostMouse = 1, PuffinPal = 1 } })
	check(near(R.BookBonus(book), 0.05), "a full Common page gives +5%")
	check(R.BurstSeconds(save()) == 30 and R.BurstSeconds(save({ Upgrades = { "BiggerBurst1" } })) == 45, "Bigger Burst: 30 -> 45 s")
	check(R.SledSeconds(save()) == LayerConfig.Block.ArriveSeconds and R.SledSeconds(save({ Upgrades = { "FastSled1", "FastSled2" } })) == LayerConfig.Block.ArriveSeconds - 2, "Fast Sled: 1 s sooner per tier")
	for _, upgrade in UpgradeConfig.Upgrades do
		check(R.Describe(upgrade) ~= "", `{upgrade.Id} has a description`)
	end

	-- Block rules --------------------------------------------------------------------------------------
	local layer1 = LayerConfig.Get(1)
	check(B.RollRarity(layer1, 0) == "Common" and B.RollRarity(layer1, 74.9) == "Common" and B.RollRarity(layer1, 75) == "Uncommon", "Fresh Snow: 75% Common, then Uncommon")
	local layer5 = LayerConfig.Get(5)
	check(B.RollRarity(layer5, 99.6) == "Mythic", "Primordial Ice's last 0.5% is Mythic")
	check(B.RollRarity(layer5, 99.0, true) == "Mythic", "Lucky Ice doubles Mythic (1%)")
	local counts = {}
	for i = 0, 999 do
		local creature = B.RollCreature(1, i / 10, (i % 7) / 7)
		counts[creature.Rarity] = (counts[creature.Rarity] or 0) + 1
		check(creature.FirstLayer <= 1, "a Fresh Snow block only holds Fresh Snow creatures")
	end
	check(counts.Common == 750 and counts.Uncommon == 250, "1000 even rolls in Fresh Snow: 750 Common, 250 Uncommon")
	check(B.RollCreature(2, 95, 0).Rarity == "Rare", "Blue Ice can hold a Rare")
	-- The first run's guaranteed Rare (CreatureConfig.FirstRunGuarantee)
	local guarantee = modules.CreatureConfig.FirstRunGuarantee
	check(guarantee.Rarity == "Rare" and guarantee.ByRescue == 12, "first run: a Rare by the 12th rescue")
	local commonsOnly = { SnowBunny = 6, SealPup = 4 }
	check(B.NeedsFirstRunGuarantee(0, 10, commonsOnly, guarantee) == nil, "rescue 11: no guarantee yet")
	check(B.NeedsFirstRunGuarantee(0, 11, commonsOnly, guarantee) == "Rare", "rescue 12 with no Rare yet: the block must be at least Rare")
	check(B.NeedsFirstRunGuarantee(0, 20, commonsOnly, guarantee) == "Rare", "...and every block after it until one is rescued")
	check(B.NeedsFirstRunGuarantee(0, 11, { SnowBunny = 6, GlacierOtter = 1 }, guarantee) == nil
		and B.NeedsFirstRunGuarantee(0, 11, { MiniYeti = 1 }, guarantee) == nil, "not once a Rare or better is in the book")
	check(B.NeedsFirstRunGuarantee(0, 11, { GlacierOtter = 0, Nonsense = 3 }, guarantee) == "Rare", "a 0 count or an unknown id doesn't count")
	check(B.NeedsFirstRunGuarantee(1, 11, commonsOnly, guarantee) == nil, "never after a rebirth")
	local raisedOk = true
	for i = 0, 99 do
		local creature = B.RollCreature(2, i, (i % 5) / 5, false, "Rare")
		raisedOk = raisedOk and creature.Rarity == "Rare" and creature.FirstLayer <= 2
	end
	check(raisedOk, "in Blue Ice, every roll raised to Rare is a Blue Ice Rare")
	check(B.RollCreature(3, 99.9, 0, false, "Rare").Rarity == "Epic", "a roll already better than Rare stays better")
	check(B.RollCreature(1, 0, 0, false, "Rare").Rarity == "Uncommon", "in Fresh Snow (no Rares) it falls back, and the guarantee waits for the next block")
	check(B.Height(1) == 14 and B.Height(50) == 20 and B.Height(80) == 20, "the block is 14 studs at level 1, 20 by level 50")
	check(B.CrackStage(100, 100) == 0 and B.CrackStage(80, 100) == 1 and B.CrackStage(19, 100) == 4, "crack stages at 20/40/60/80%")

	-- The tap cap (TapService) against a fake clock ---------------------------------------------------
	local clock = 0
	local warnings = {}
	local fakeServer = {
		Economy = { RecordTaps = function() end },
		IceBlockService = { Damage = function(_, _, amount)
			return amount
		end },
		PlayerData = { Edit = function()
			return save()
		end },
		PlotService = { InOwnPlot = function()
			return true
		end },
	}
	local chunk = assert(loadstring(sources.TapService, "TapService"))
	setfenv(chunk, setmetatable({
		game = { GetService = function(_, name)
			if name == "ReplicatedStorage" then
				return modules
			end
			return { PlayerRemoving = { Connect = function() end } }
		end },
		script = { Parent = fakeServer },
		require = function(module)
			return module
		end,
		os = { clock = function()
			return clock
		end },
		warn = function(message)
			table.insert(warnings, message)
		end,
	}, { __index = getfenv(1) }))
	local TapService = chunk()
	local tapper = { Name = "Tapper", UserId = 5 }
	check(TapService.Allow(tapper, 5) == 5, "a normal batch is allowed")
	check(TapService.Allow(tapper, 100) == 15, "a huge batch is cut to what's left of a second's taps")
	check(#warnings == 1, "...and the player is logged")
	clock = 0.25
	check(TapService.Allow(tapper, 10) == 5, "after 0.25 s, 5 more taps (20 a second)")
	local total = 0
	for step = 1, 40 do
		clock = 0.25 + step * 0.25
		total += TapService.Allow(tapper, 50)
	end
	check(total <= 20 * 10 + 1, "an autoclicker never beats 20 taps a second")
	check(#warnings == 1, "...and the log is throttled")

	-- Steady income (Economy.SteadyIncome: crystal bundles and the daily chest): the HUD's rate with the
	-- permanent bonuses but no rushes, taps at least MonetizationConfig.BundleTapsPerSecond --------------------
	modules.MonetizationConfig = { BundleTapsPerSecond = 4 }
	modules.OfflineEarningsRules = {}
	local economyServer = { OfflineEarnings = {}, PlayerData = {} }
	local econClock = 100
	local econChunk = assert(loadstring(sources.Economy, "Economy"))
	setfenv(econChunk, setmetatable({
		game = { GetService = function(_, name)
			if name == "ReplicatedStorage" then
				return modules
			end
			return {}
		end },
		script = { Parent = economyServer },
		require = function(module)
			return module
		end,
		os = { clock = function()
			return econClock
		end },
	}, { __index = getfenv(1) }))
	local Economy = econChunk()
	local earner = { Name = "Earner", UserId = 6 }
	local save = { Buildings = { IcePickPost = 10 }, Upgrades = {}, Pets = {}, Equipped = {}, BookSeen = {}, BookGolden = {}, FrostCores = 4 }
	Economy.AddExtra(function()
		return 2 -- a pass
	end)
	Economy.AddExtra(function()
		return 3 -- a rush
	end, true)
	local permanent = modules.EconomyRules.Multiplier(save, 2)
	check(near(Economy.Multiplier(earner, save), modules.EconomyRules.Multiplier(save, 6)), "the HUD's multiplier counts the rush")
	check(near(Economy.PermanentMultiplier(earner, save), permanent), "...the permanent one doesn't")
	local idle = (modules.EconomyRules.TotalBuildingDps(save) + 4 * modules.EconomyRules.TapDamage(save)) * permanent
	check(near(Economy.SteadyIncome(earner, save), idle), "not tapping (the shop is open): taps count at 4 a second, no rush")
	Economy.RecordTaps(earner, 20 * modules.GameConfig.Taps.RateWindowSeconds)
	local tapping = (modules.EconomyRules.TotalBuildingDps(save) + 20 * modules.EconomyRules.TapDamage(save)) * permanent
	check(near(Economy.SteadyIncome(earner, save), tapping), "tapping 20 a second: the HUD's tap rate counts")
	check(Economy.SteadyIncome(earner, save) < Economy.CrystalsPerSecond(earner, save), "...still below the HUD's rate while a rush runs")

	-- The click's "+N" (TapValue, published for TapFeedback): what one tap pays, rushes and passes included
	check(near(Economy.TapValue(earner, save), modules.EconomyRules.TapDamage(save) * Economy.Multiplier(earner, save)),
		"TapValue is one tap's damage times the full multiplier (what IceBlockService.Damage pays per tap)")
	check(Economy.TapValue(earner, save) > modules.EconomyRules.TapDamage(save) * permanent, "...and counts the rush running")

	return passed
end
