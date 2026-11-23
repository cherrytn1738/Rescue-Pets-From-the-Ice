--[[
UpgradeConfig: every one-time upgrade in the Upgrades panel (docs/GAME_DESIGN.md, "Upgrades in
detail"). Starting values for the economy simulation. All upgrades reset on rebirth.

Three kinds:
 * IcePick: the tap power tiers. Tier 1 (the wooden pick) is what every run starts with; each later
   tier doubles tap damage and costs 10 times the last.
 * FrostTouch: each tier makes every tap also deal a share of the player's building damage per second.
   Unlocked by owning a building.
 * Building upgrades: five per building (BuildingConfig), each doubling that building's damage and
   adding its next upgrade part. The n-th unlocks at UnlockAtOwned[n] copies and costs
   building.BaseCost × CostMultipliers[n].
 * IceUpgrades: Bigger Burst, Crystal Yield, Fast Sled, each with a few tiers.

Upgrades (built below) lists every upgrade with a saved Id (never rename one), Kind, Name and Cost;
ById finds one. The save's Upgrades field holds these ids.
]]
local BuildingConfig = require(script.Parent.BuildingConfig)

local UpgradeConfig = {}

UpgradeConfig.IcePick = {
	{ Tier = 1, Name = "Wooden pick", TapDamage = 1, Cost = 0 }, -- the start
	{ Tier = 2, Name = "Stone pick", TapDamage = 2, Cost = 100 },
	{ Tier = 3, Name = "Iron pick", TapDamage = 4, Cost = 1_000 },
	{ Tier = 4, Name = "Gold pick", TapDamage = 8, Cost = 10_000 },
	{ Tier = 5, Name = "Diamond pick", TapDamage = 16, Cost = 100_000 },
	{ Tier = 6, Name = "Cosmic pick", TapDamage = 32, Cost = 1_000_000 },
}

UpgradeConfig.FrostTouch = {
	{ Id = "FrostTouch1", Name = "Frost Touch I", TapShareOfBuildingDps = 0.01, Cost = 50_000, UnlockOwns = "WreckingCrane" },
	{ Id = "FrostTouch2", Name = "Frost Touch II", TapShareOfBuildingDps = 0.02, Cost = 5_000_000, UnlockOwns = "FlamethrowerTurret" },
	{ Id = "FrostTouch3", Name = "Frost Touch III", TapShareOfBuildingDps = 0.03, Cost = 500_000_000, UnlockOwns = "SunMirrorTower" },
}

UpgradeConfig.BuildingUpgrades = {
	UnlockAtOwned = { 1, 10, 25, 50, 100 },
	CostMultipliers = { 10, 50, 500, 5_000, 50_000 }, -- × the building's base cost
	DamageMultiplier = 2, -- each one doubles that building's damage
}

UpgradeConfig.IceUpgrades = {
	{ Id = "BiggerBurst", Name = "Bigger Burst", Tiers = 2, Costs = { 5_000, 250_000 },
		BurstSeconds = { 30, 45, 60 } }, -- the rescue fountain is worth this many seconds of income (no tier, tier 1, tier 2)
	{ Id = "CrystalYield", Name = "Crystal Yield", Tiers = 3, Costs = { 20_000, 1_000_000, 50_000_000 },
		YieldPerTier = 0.10 }, -- +10% crystals per point of damage, per tier
	{ Id = "FastSled", Name = "Fast Sled", Tiers = 2, Costs = { 2_000, 100_000 },
		SecondsSoonerPerTier = 1 }, -- the next block arrives 1 second sooner, per tier
}

-- Every upgrade, with its saved id.
UpgradeConfig.Upgrades = {}
UpgradeConfig.ById = {}

local function add(upgrade)
	table.insert(UpgradeConfig.Upgrades, upgrade)
	UpgradeConfig.ById[upgrade.Id] = upgrade
end

for _, tier in UpgradeConfig.IcePick do
	if tier.Tier > 1 then
		add({ Id = "IcePick" .. tier.Tier, Kind = "IcePick", Name = tier.Name, Tier = tier.Tier, Cost = tier.Cost })
	end
end
for _, touch in UpgradeConfig.FrostTouch do
	add({ Id = touch.Id, Kind = "FrostTouch", Name = touch.Name, Cost = touch.Cost, UnlockOwns = touch.UnlockOwns })
end
for _, building in BuildingConfig.Buildings do
	for index, unlockAt in UpgradeConfig.BuildingUpgrades.UnlockAtOwned do
		add({
			Id = building.Id .. "Upgrade" .. index,
			Kind = "Building",
			Name = building.Name .. " upgrade " .. index,
			Building = building.Id,
			Index = index,
			UnlockAtOwned = unlockAt,
			Cost = building.BaseCost * UpgradeConfig.BuildingUpgrades.CostMultipliers[index],
		})
	end
end
for _, ice in UpgradeConfig.IceUpgrades do
	for tier = 1, ice.Tiers do
		add({
			Id = ice.Id .. tier,
			Kind = "Ice",
			Name = ice.Name .. " " .. tier,
			Upgrade = ice.Id,
			Tier = tier,
			Cost = ice.Costs[tier],
		})
	end
end

function UpgradeConfig.Get(id: string)
	return UpgradeConfig.ById[id]
end

return UpgradeConfig
