-- World spec (Milestone 4): rebirths (RebirthService.Apply), the tutorial steps
-- (TutorialService.Advance), the daily chest (RewardService), leaderboard encoding (LeaderboardRules),
-- and the map and rush settings. Server modules load against fakes. Run: python tools/run_specs.py World
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
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
	for _, name in { "BuildingConfig", "CreatureConfig", "LayerConfig", "RebirthConfig", "UpgradeConfig", "GameConfig", "NumberFormat", "MapConfig", "LeaderboardRules", "AnalyticsConfig" } do
		loadPure(name)
	end
	local RebirthConfig, LayerConfig, GameConfig, MapConfig = modules.RebirthConfig, modules.LayerConfig, modules.GameConfig, modules.MapConfig

	local recorded = {}
	local function recorder(name)
		return function(...)
			table.insert(recorded, { name = name, args = { ... } })
		end
	end
	local function loadServer(name, server)
		local chunk = assert(loadstring(sources[name], name))
		setfenv(chunk, setmetatable({
			game = { GetService = function(_, service)
				if service == "ReplicatedStorage" then
					return modules
				end
				return { PlayerRemoving = { Connect = function() end } }
			end },
			script = { Parent = server },
			require = function(module)
				return module
			end,
		}, { __index = getfenv(1) }))
		return chunk()
	end

	local function save(overrides)
		local data = {
			Crystals = 1234, CrystalsThisRun = 8_000_000, CrystalsAllTime = 9e9, BlockLevel = 31,
			CurrentBlock = { CreatureId = "SnowBunny", HpLeft = 5 }, Buildings = { IcePickPost = 40 }, Upgrades = { "IcePick2" },
			Pets = { { Uid = "a", CreatureId = "SnowBunny", Golden = false } }, Equipped = { "a" }, BookSeen = { SnowBunny = 3 },
			BookGolden = {}, FrostCores = 1, Rebirths = 0, MaxLayerOpened = 5, CreaturesRescued = 3, TutorialStep = 1,
		}
		for key, value in overrides or {} do
			data[key] = value
		end
		return data
	end

	-- Rebirths ----------------------------------------------------------------------------------------
	local Rebirth = loadServer("RebirthService", {
		Analytics = {}, IceBlockService = {}, PetService = {}, PlayerData = {}, PlotService = {},
	})
	local data = save({ BlockLevel = 30 })
	local cores, reason = Rebirth.Apply(data)
	check(cores == nil and string.find(reason, "31", 1, true), "a rebirth needs level 31 (Layer 4)")
	check(data.Crystals == 1234 and data.Buildings.IcePickPost == 40, "...and a refused rebirth changes nothing")
	data = save()
	cores = Rebirth.Apply(data)
	check(cores == 2, "8M crystals this run earn floor(cube root(8)) = 2 Frost Cores")
	check(data.Crystals == 0 and data.CrystalsThisRun == 0 and data.BlockLevel == 1 and data.CurrentBlock == nil, "crystals, this run's total, the level and the block reset")
	check(next(data.Buildings) == nil and #data.Upgrades == 0, "buildings and upgrades reset")
	check(#data.Pets == 1 and data.Equipped[1] == "a" and data.BookSeen.SnowBunny == 3 and data.CrystalsAllTime == 9e9, "pets, the book and the all-time total are kept")
	check(data.FrostCores == 3 and data.Rebirths == 1, "Frost Cores add up; the rebirth counts")
	data = save({ Rebirths = 2, CrystalsThisRun = 0 })
	check(Rebirth.Apply(data) == 0 and data.Rebirths == 3, "a rebirth worth 0 cores is allowed (the screen warns)")
	check(data.MaxLayerOpened == 6, "rebirth 3 (Glacier Diver) opens Layer 6, Frozen Core")
	data = save({ Rebirths = 9, MaxLayerOpened = 6 })
	Rebirth.Apply(data)
	check(data.MaxLayerOpened == 6, "rebirth 10's Layer 7 isn't in the game yet, so 6 stays the deepest")
	for _, field in RebirthConfig.ResetOnRebirth do
		local fresh = save()
		Rebirth.Apply(fresh)
		local value = fresh[field]
		check(value == nil or value == 0 or value == 1 or (type(value) == "table" and next(value) == nil), `{field} is reset`)
	end

	-- The tutorial ------------------------------------------------------------------------------------
	local events = {}
	modules.GameEvent = { FireClient = function(_, _, kind, payload)
		table.insert(events, { kind = kind, payload = payload })
	end }
	modules.WaitForChild = function(self, name)
		return self[name]
	end
	local onboarded = {}
	local hook = function() end
	local Tutorial = loadServer("TutorialService", {
		Analytics = { Onboarding = function(_, key)
			table.insert(onboarded, key)
		end },
		Economy = { OnTick = hook }, IceBlockService = { OnRescue = hook }, PetService = { OnEquipChanged = hook },
		ShopService = { OnBought = hook }, TapService = { OnTaps = hook },
		PlayerData = { MarkImportant = hook, Publish = hook, OnLoaded = hook },
	})
	Tutorial.Start()
	local player = { Name = "New", UserId = 9 }
	local function advance(d)
		return Tutorial.Advance(player, d)
	end
	local t = save({ Crystals = 10, Buildings = {}, CreaturesRescued = 0, Equipped = {}, TutorialStep = 1 })
	check(not advance(t) and t.TutorialStep == 1, "step 1 (tap the ice) until 15 crystals")
	t.Crystals = 15
	check(advance(t) and t.TutorialStep == 2, "15 crystals: step 2, build an Ice Pick Post")
	t.Buildings.IcePickPost = 1
	advance(t)
	check(t.TutorialStep == 3, "the first building: step 3, free the first creature")
	t.CreaturesRescued = 1
	advance(t)
	check(t.TutorialStep == 4, "the first rescue: step 4, equip your new pet")
	t.Equipped = { "a" }
	advance(t)
	check(t.TutorialStep == 5, "a pet equipped: the tutorial is done")
	check(table.find(onboarded, "TutorialDone") ~= nil, "...the funnel logs Tutorial done")
	local shown = events[#events]
	check(shown and shown.kind == "TutorialDone" and shown.payload.Code == "THAWED", "...and the tutorial code is shown")
	local veteran = save({ TutorialStep = 1, Crystals = 0, CreaturesRescued = 5, Equipped = { "a" } })
	advance(veteran)
	check(veteran.TutorialStep == 5, "a player who has already done it all goes straight to the end")

	-- The daily chest ---------------------------------------------------------------------------------
	local Reward = loadServer("RewardService", { Economy = {}, PlayerData = {}, PlazaService = {}, PurchaseRewards = { Kinds = {} } })
	check(Reward.Today(86400 * 20000 + 5) == 20000 and Reward.Today(86400 * 20001 - 1) == 20000, "a day is a UTC day")
	check(Reward.DailyAmount(0) == GameConfig.Daily.Minimum, "a new player's chest gives the minimum")
	check(Reward.DailyAmount(10) == math.max(GameConfig.Daily.Minimum, 10 * GameConfig.Daily.IncomeSeconds), "...later, 5 minutes of income")

	-- Leaderboards ----------------------------------------------------------------------------------
	local L = modules.LeaderboardRules
	check(L.Encode(1e6, true) == 6000 and L.Encode(1e300, true) == 300000, "crystals are stored as floor(log10 x 1000)")
	check(math.abs(L.Decode(6000, true) - 1e6) < 1, "...and shown back")
	check(L.Encode(0.5, true) == 0 and L.Encode(0 / 0) == 0, "nothing below 1 is stored")
	check(L.Encode(37) == 37, "counts are stored as they are")
	check(L.StoreName("Crystals", true) ~= L.StoreName("Crystals", false), "Studio has its own boards")

	-- Map and rush settings ---------------------------------------------------------------------------
	check(MapConfig.PlotCount == 8, "eight plots per server")
	-- The name sign arches over the open front: a viewer's line of sight (eye 6 studs up) to the top of the
	-- tallest ice passes under its beam from anywhere on the path, highest at the arch for the farthest viewer
	-- (the plaza's centre). Its posts stand outside the opening.
	local arch = MapConfig.Arch
	local half = MapConfig.PlotSize / 2
	local iceTop = MapConfig.Mound.Height + LayerConfig.Block.HeightAtLevel50
	local far = MapConfig.RingRadius - half
	check(6 + (iceTop - 6) * far / (far + half) < arch.ClearHeight, "the tallest ice is in full view under the arch from the plaza and the path")
	check(arch.PostSize > 0 and arch.BeamHeight > 0 and MapConfig.Border.FrontGap / 2 + arch.PostSize <= MapConfig.PlotSize / 2, "the arch's posts stand on the front wall, outside the opening")
	for index = 1, MapConfig.PlotCount do
		local cf = MapConfig.PlotCFrame(index)
		local front = (cf * CFrame.new(0, 0, 1)).Position - cf.Position
		check(front:Dot(-cf.Position.Unit) > 0.99, `plot {index}'s open front (+Z) faces the plaza`)
		for other = index + 1, MapConfig.PlotCount do
			local gap = (MapConfig.PlotCFrame(other).Position - cf.Position).Magnitude
			check(gap > MapConfig.PlotSize * 1.05, `plots {index} and {other} don't overlap`)
		end
	end
	-- The owner's name boards stand on the front walls beside the gate's pillars (the visible pillars are twice the
	-- collision post's width), under the beam and above the wall, inside the plot.
	local board = arch.Board
	check(board.CentreX - board.Width / 2 > MapConfig.Border.FrontGap / 2 + 2 * arch.PostSize, "the name boards stand clear of the gate's pillars")
	check(board.CentreX + board.Width / 2 < half, "the name boards stay on the front walls")
	check(board.Bottom > MapConfig.Border.Height and board.Bottom + board.Height < arch.ClearHeight, "the name boards stand on the wall, low beside the gate")
	for _, name in { "PlotArch", "PlotStage", "PlotWallLong", "PlotWallShort" } do
		local id = MapConfig.PlotModels[name]
		check(type(id) == "number" and id > 0 and id % 1 == 0, name .. " has an asset id")
	end
	-- The ground inside a plot (drifts, ice patches: build_world.luau shapes them into the terrain) stays inside the
	-- plot and clear of every pad, the mound with the ice, and the footpath to the open front.
	local ground = MapConfig.PlotGround
	local mound = MapConfig.Mound.Size / 2
	check(ground.Footpath.FromZ > mound and ground.Footpath.Width < MapConfig.Border.FrontGap, "the footpath runs from the mound through the open front")
	local shapes = {}
	for _, drift in ground.Drifts do
		check(drift.Height > 0 and drift.Height < drift.Radius, "a drift is a low mound")
		table.insert(shapes, drift)
	end
	for _, patch in ground.IcePatches do
		table.insert(shapes, patch)
	end
	for _, shape in shapes do
		local where = `the ground shape at ({shape.X}, {shape.Z})`
		check(math.abs(shape.X) <= half and math.abs(shape.Z) <= half, where .. " is inside the plot")
		check(math.max(math.abs(shape.X), math.abs(shape.Z)) - shape.Radius > mound, where .. " is off the mound")
		check(math.abs(shape.X) - shape.Radius > ground.Footpath.Width / 2 or shape.Z + shape.Radius < ground.Footpath.FromZ, where .. " is off the footpath")
		for _, building in modules.BuildingConfig.Buildings do
			local pad = building.Pad
			local clear = pad.Size / 2 + shape.Radius
			check(math.abs(shape.X - pad.X) >= clear or math.abs(shape.Z - pad.Z) >= clear, where .. " is clear of the " .. building.Id .. " pad")
		end
	end
	local rush = GameConfig.GoldenGlacier
	check(rush.MinSeconds == 300 and rush.MaxSeconds == 480, "a Golden Glacier every 5-8 minutes")
	check(rush.RushMultiplier == 3 and rush.RushSeconds == 60 and rush.TopMultiplier == 5, "Frost Rush: x3 for 60 s, x5 for the top tapper")
	check(GameConfig.Group.Bonus == 0.10 and GameConfig.Group.Id == 921449746, "the group reward: +10% for the game's group")
	check(#modules.AnalyticsConfig.Onboarding == 7, "the onboarding funnel has the doc's seven steps")

	return passed
end
