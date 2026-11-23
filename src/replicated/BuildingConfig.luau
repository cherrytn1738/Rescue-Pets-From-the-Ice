--[[
BuildingConfig: the eight buildings that break the ice on their own (docs/GAME_DESIGN.md, "Economy",
"Buildings in detail", "Detail levels" and "Plot and map layout"). Starting values for the economy
simulation.

 * Buildings[n]: Id (saved: never rename one), Name, Breaks (how it breaks the ice), BaseCost
   (crystals), DamagePerSecond (per copy), Pad (its pad: Index, X and Z in studs from the centre of
   the ice, +Z the open front toward the plaza, and Size), Stations (the five looks at 1, 10, 25, 50 and
   100 owned, with StationModelIds nil until the models are made), UpgradeParts (the doc's list of
   parts its five upgrades add, in order).
 * cost(n) = BaseCost × CostGrowth^n for the copy after n owned; Cost and CostOfNext below.
 * Building upgrades (their costs and unlocks) are in UpgradeConfig.
 * Checked against the design doc by tests/BuildingConfig.spec.luau.
]]
local BuildingConfig = {}

BuildingConfig.CostGrowth = 1.15 -- each copy costs 15% more than the last
BuildingConfig.StationMilestones = { 1, 10, 25, 50, 100 } -- owned counts where the station grows
BuildingConfig.MasterworkBonus = 0.10 -- +10% damage at detail level 10
BuildingConfig.MaxDetailLevel = 10
BuildingConfig.FadedScale = 0.6 -- an older station once the next building up is owned
BuildingConfig.PlotSize = 100 -- studs, square

BuildingConfig.Buildings = {
	{ Id = "IcePickPost", Name = "Ice Pick Post", Breaks = "A spring-loaded ice pick on a post", BaseCost = 15, DamagePerSecond = 0.1,
		Pad = { Index = 1, X = 24, Z = 38, Size = 8 },
		Stations = { "One post", "Three posts", "Five posts on a stone base", "Bigger base, gear on top", "Golden base" },
		UpgradeParts = "Stone, iron, gold, diamond pick heads" },
	{ Id = "HeatLamp", Name = "Heat Lamp", Breaks = "Melts the surface", BaseCost = 120, DamagePerSecond = 1,
		Pad = { Index = 2, X = -25, Z = 38, Size = 8 },
		Stations = { "One lamp", "Lamp cluster", "Lamps on a pole frame", "Floodlight rig", "Golden sun lamp" },
		UpgradeParts = "Brighter bulbs, orange, red, white-hot glow" },
	{ Id = "ChiselMill", Name = "Chisel Mill", Breaks = "A water wheel drives a row of chisels", BaseCost = 1_300, DamagePerSecond = 8,
		Pad = { Index = 3, X = -40, Z = 18, Size = 10 },
		Stations = { "Small wheel, 2 chisels", "4 chisels", "Bigger wheel, 6 chisels", "Twin wheels", "Golden mill" },
		UpgradeParts = "Iron, steel, gold, crystal chisels" },
	{ Id = "IceDrill", Name = "Ice Drill", Breaks = "Drills up from under the block", BaseCost = 14_000, DamagePerSecond = 50,
		Pad = { Index = 4, X = -40, Z = -12, Size = 10 },
		Stations = { "Hand drill on a frame", "Motor drill", "Twin drills", "Drill tower", "Golden drill tower" },
		UpgradeParts = "Bigger bits, spiral bits, diamond bits, plasma bit" },
	{ Id = "WreckingCrane", Name = "Wrecking Crane", Breaks = "Swings a wrecking ball", BaseCost = 150_000, DamagePerSecond = 280,
		Pad = { Index = 5, X = -25, Z = -38, Size = 12 },
		Stations = { "Small crane", "Taller boom", "Two balls", "Heavy-duty crane", "Golden crane" },
		UpgradeParts = "Iron, spiked, steel, molten ball" },
	{ Id = "FlamethrowerTurret", Name = "Flamethrower Turret", Breaks = "Blasts it with fire", BaseCost = 1_600_000, DamagePerSecond = 1_500,
		Pad = { Index = 6, X = 0, Z = -42, Size = 12 },
		Stations = { "One nozzle", "Twin nozzles", "Rotating turret", "Quad turret", "Golden turret" },
		UpgradeParts = "Orange, blue, purple, white flame" },
	{ Id = "LavaPump", Name = "Lava Pump", Breaks = "Sprays lava from underground", BaseCost = 22_000_000, DamagePerSecond = 8_000,
		Pad = { Index = 7, X = 26, Z = -39, Size = 14 },
		Stations = { "Small pump, one hose", "Two hoses", "Lava pool beside it", "Lava fountain", "Golden pump" },
		UpgradeParts = "Hotter lava colours, bigger splashes" },
	{ Id = "SunMirrorTower", Name = "Sun Mirror Tower", Breaks = "Focuses sunlight into a beam", BaseCost = 350_000_000, DamagePerSecond = 45_000,
		Pad = { Index = 8, X = 40, Z = -9, Size = 16 },
		Stations = { "One mirror", "Mirror ring", "Taller tower", "Twin towers", "Golden tower" },
		UpgradeParts = "Wider beam, double beam, rainbow beam" },
}

for _, building in BuildingConfig.Buildings do
	building.StationModelIds = {} -- [milestone index] = asset id, once made
end

local byId = {}
for _, building in BuildingConfig.Buildings do
	byId[building.Id] = building
end

function BuildingConfig.Get(id: string)
	return byId[id]
end

-- The price of the next copy when `owned` are owned.
function BuildingConfig.Cost(building, owned: number): number
	return building.BaseCost * BuildingConfig.CostGrowth ^ owned
end

-- The price of the next `count` copies together.
function BuildingConfig.CostOfNext(building, owned: number, count: number): number
	local growth = BuildingConfig.CostGrowth
	return building.BaseCost * growth ^ owned * (growth ^ count - 1) / (growth - 1)
end

return BuildingConfig
