--[[
BuildingConfig: the eight buildings that break the ice on their own (docs/GAME_DESIGN.md, "Economy",
"Buildings in detail", "Detail levels" and "Plot and map layout"). Starting values for the economy
simulation.

 * Buildings[n]: Id (saved: never rename one), Name, Breaks (how it breaks the ice), BaseCost
   (crystals), DamagePerSecond (per copy), Pad (its pad: Index, X and Z in studs from the centre of
   the ice, +Z the open front toward the plaza, and Size), Stations (its five tier forms at 1, 10, 25, 50
   and 100 owned: Scrappy, Workshop, Frost-tech, Enchanted, Legendary; StationModelIds nil until the
   models are uploaded), UpgradeParts (the five upgrades' parts: better part, lights, moving extra, hit
   effect, signature), LegendaryForm and SignatureAura (the Legendary form's name and its aura).
 * cost(n) = BaseCost × CostGrowth^n for the copy after n owned; Cost and CostOfNext below.
 * Building upgrades (their costs and unlocks) are in UpgradeConfig.
 * Checked against the design doc by tests/BuildingConfig.spec.luau.
]]
local BuildingConfig = {}

BuildingConfig.CostGrowth = 1.15 -- each copy costs 15% more than the last
BuildingConfig.StationMilestones = { 1, 10, 25, 50, 100 } -- owned counts where the station grows
-- The five tier themes (one per milestone): every tier is a new form, not a bigger copy.
BuildingConfig.Tiers = {
	{ Tier = 1, Owned = 1, Theme = "Scrappy", Look = "Wood, rope, nails, hand-made" },
	{ Tier = 2, Owned = 10, Theme = "Workshop", Look = "Brass and iron, gears, steam, rivets" },
	{ Tier = 3, Owned = 25, Theme = "Frost-tech", Look = "Blue crystals power it, glowing coils, ice-blue light" },
	{ Tier = 4, Owned = 50, Theme = "Enchanted", Look = "Parts float, rune rings spin, gems glow" },
	{ Tier = 5, Owned = 100, Theme = "Legendary", Look = "A creature or monument with a personality: eyes, a face, a crown, gold and aurora light" },
}
BuildingConfig.MasterworkBonus = 0.10 -- +10% damage at detail level 10
BuildingConfig.MaxDetailLevel = 10
BuildingConfig.FadedScale = 0.6 -- an older station once the next building up is owned
BuildingConfig.PlotSize = 100 -- studs, square

BuildingConfig.Buildings = {
	{ Id = "IcePickPost", Name = "Ice Pick Post", Breaks = "A spring-loaded ice pick on a post", BaseCost = 15, DamagePerSecond = 0.1,
		Pad = { Index = 1, X = 24, Z = 38, Size = 8 },
		Stations = { "Wooden post with a pick", "Brass clockwork hammer arm", "Crystal-tipped piston picks with blue coils", "Enchanted picks orbiting a rune pillar", "Frost Golem: a giant ice-golem fist pounding the ice" },
		UpgradeParts = { "Steel pick heads", "Lantern on the post", "Spring that bounces with each swing", "Ice chips", "Diamond picks with a frost trail" },
		LegendaryForm = "Frost Golem", SignatureAura = "Swirling snow flurries and a frost ring that creeps across the ground" },
	{ Id = "HeatLamp", Name = "Heat Lamp", Breaks = "Melts the surface", BaseCost = 120, DamagePerSecond = 1,
		Pad = { Index = 2, X = -25, Z = 38, Size = 8 },
		Stations = { "Camping lantern", "Brass street lamp", "Crystal heat-coil tower", "A floating sun orb inside spinning rune rings", "Captive Star: a tiny sun in a golden cage" },
		UpgradeParts = { "Brighter bulbs", "Orange beacon", "Turning reflector", "Heat shimmer and sparks", "White-hot sun bulb with light rays" },
		LegendaryForm = "Captive Star", SignatureAura = "Sun rays turning slowly, heat shimmer and orbiting embers" },
	{ Id = "ChiselMill", Name = "Chisel Mill", Breaks = "A water wheel drives a row of chisels", BaseCost = 1_300, DamagePerSecond = 8,
		Pad = { Index = 3, X = -40, Z = 18, Size = 10 },
		Stations = { "Wooden water wheel", "Brass gear mill", "Crystal turbine with glowing water", "A waterwheel spinning in mid-air under a waterfall from nowhere", "Kraken Mill: tentacles holding chisels" },
		UpgradeParts = { "Steel chisels", "Lamps on the frame", "Faster wheel with splashing water", "Chips and sparks", "Crystal chisels and glowing water" },
		LegendaryForm = "Kraken Mill", SignatureAura = "Water droplets and bubbles spiralling around it in a teal mist" },
	{ Id = "IceDrill", Name = "Ice Drill", Breaks = "Drills up from under the block", BaseCost = 14_000, DamagePerSecond = 50,
		Pad = { Index = 4, X = -40, Z = -12, Size = 10 },
		Stations = { "Hand drill on an A-frame", "Steam drill rig with a brass boiler", "Crystal drill tower with glowing coils", "Floating drill inside rune rings", "Mecha Mole Titan: a giant robot mole with a drill nose and glowing eyes" },
		UpgradeParts = { "Steel bits", "Warning lamps", "Gears and steam", "Chips and sparks", "Diamond bits with a crystal trail" },
		LegendaryForm = "Mecha Mole Titan", SignatureAura = "Steam venting from its back, sparks from its claws and cyan energy rings around the drill" },
	{ Id = "WreckingCrane", Name = "Wrecking Crane", Breaks = "Swings a wrecking ball", BaseCost = 150_000, DamagePerSecond = 280,
		Pad = { Index = 5, X = -25, Z = -38, Size = 12 },
		Stations = { "Small wooden crane", "Steampunk crane", "Crystal magnet crane on an energy chain", "A floating crane arm swinging a storm-cloud ball", "Titan Arm: a golem arm swinging a meteor" },
		UpgradeParts = { "Spiked steel ball", "Cab lights and beacon", "Swinging counterweight and pulleys", "Shockwave ring on impact", "Molten ball with a lava trail" },
		LegendaryForm = "Titan Arm", SignatureAura = "Small rocks orbiting the meteor and a dust storm at its base" },
	{ Id = "FlamethrowerTurret", Name = "Flamethrower Turret", Breaks = "Blasts it with fire", BaseCost = 1_600_000, DamagePerSecond = 1_500,
		Pad = { Index = 6, X = 0, Z = -42, Size = 12 },
		Stations = { "Torch on a stand", "Brass flamethrower", "Blue-flame crystal cannon", "Enchanted brazier with fire spirits", "Dragon Turret: a dragon statue breathing fire" },
		UpgradeParts = { "Steel nozzles", "Pilot lights", "Rotating turret and fuel gauges", "Blue-hot flame", "White-purple plasma flame" },
		LegendaryForm = "Dragon Turret", SignatureAura = "Drifting embers, curling smoke and an ember ring on the ground" },
	{ Id = "LavaPump", Name = "Lava Pump", Breaks = "Sprays lava from underground", BaseCost = 22_000_000, DamagePerSecond = 8_000,
		Pad = { Index = 7, X = 26, Z = -39, Size = 14 },
		Stations = { "Hand pump and bucket", "Steam pump and pipes", "Crystal-cooled lava pipes", "Volcano altar with floating lava orbs", "Volcano Forge: a mini volcano with a lava heart" },
		UpgradeParts = { "Reinforced hoses", "Warning lamps", "Pumping pistons", "Lava splashes", "Lava fountain with glowing rocks" },
		LegendaryForm = "Volcano Forge", SignatureAura = "Lava sparks shooting up, heat haze and glowing smoke" },
	{ Id = "SunMirrorTower", Name = "Sun Mirror Tower", Breaks = "Focuses sunlight into a beam", BaseCost = 350_000_000, DamagePerSecond = 45_000,
		Pad = { Index = 8, X = 40, Z = -9, Size = 16 },
		Stations = { "Polished shield on a pole", "Brass telescope tower", "Crystal prism tower splitting light", "Mirrors orbiting a column of light", "Celestial Observatory: a sun disk with orbiting planets" },
		UpgradeParts = { "Polished mirror", "Beacon on top", "Mirrors that turn to track the sun", "Brighter beam with heat glow", "Rainbow beam" },
		LegendaryForm = "Celestial Observatory", SignatureAura = "Twinkling stars, a slow aurora ribbon and orbiting mini planets that glow" },
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
