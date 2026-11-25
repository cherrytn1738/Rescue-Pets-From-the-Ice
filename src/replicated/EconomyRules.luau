--[[
EconomyRules: the game's money maths as pure functions of a save (PlayerData's data table), so the
server, the UI, the specs and the economy simulation all use the same numbers. Every number comes
from the config modules (docs/GAME_DESIGN.md, "Economy", "Upgrades in detail", "Pets", "Rebirth").

    Crystals/s = (tap damage x taps/s + building damage/s) x Multiplier

Multiplier(data, extra) = pet bonus x Creature Book bonus x Crystal Yield x Frost Cores x extra
  pet bonus      1 + the bonuses of the equipped pets (a Golden pet's bonus is doubled)
  book bonus     1 + the crystal bonus of every completed Creature Book page
  Crystal Yield  1 + 10% per tier owned
  Frost Cores    1 + 5% per core
  extra          what only the server knows: passes, Frost Rush, the group bonus (1 when omitted)

Damage:
  TapDamage(data)        the ice pick tier's damage, plus the Frost Touch share of building damage/s
  BuildingDps(data, id)  copies x base damage/s x 2^(its upgrades bought) x Masterwork (+10%)
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local BuildingConfig = require(ReplicatedStorage.BuildingConfig)
local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local LayerConfig = require(ReplicatedStorage.LayerConfig)
local RebirthConfig = require(ReplicatedStorage.RebirthConfig)
local UpgradeConfig = require(ReplicatedStorage.UpgradeConfig)

local EconomyRules = {}

local function owns(data, upgradeId: string): boolean
	return table.find(data.Upgrades, upgradeId) ~= nil
end
EconomyRules.Owns = owns

-- Upgrades --------------------------------------------------------------------------------------

-- The highest ice pick tier owned (1 = the wooden pick everyone starts with).
function EconomyRules.PickTier(data): number
	local tier = 1
	for _, pick in UpgradeConfig.IcePick do
		if pick.Tier > 1 and owns(data, "IcePick" .. pick.Tier) then
			tier = math.max(tier, pick.Tier)
		end
	end
	return tier
end

-- How many tiers of an ice upgrade (BiggerBurst, CrystalYield, FastSled) are owned.
function EconomyRules.IceTier(data, iceId: string): number
	local tiers = 0
	for _, ice in UpgradeConfig.IceUpgrades do
		if ice.Id == iceId then
			for tier = 1, ice.Tiers do
				if owns(data, iceId .. tier) then
					tiers = tier
				end
			end
		end
	end
	return tiers
end

-- How many ice upgrade tiers the player owns in all (the crystals' colour: IceLooks.CrystalColour).
function EconomyRules.IceTiersTotal(data): number
	local total = 0
	for _, ice in UpgradeConfig.IceUpgrades do
		total += EconomyRules.IceTier(data, ice.Id)
	end
	return total
end

local function iceUpgrade(iceId: string)
	for _, ice in UpgradeConfig.IceUpgrades do
		if ice.Id == iceId then
			return ice
		end
	end
	error("no ice upgrade " .. iceId)
end

-- How many of a building's five upgrades are bought.
function EconomyRules.BuildingUpgradeCount(data, buildingId: string): number
	local count = 0
	for index = 1, #UpgradeConfig.BuildingUpgrades.UnlockAtOwned do
		if owns(data, buildingId .. "Upgrade" .. index) then
			count += 1
		end
	end
	return count
end

-- The building's detail level, 0-10: a point per count milestone reached and per upgrade bought.
function EconomyRules.DetailLevel(data, buildingId: string): number
	local owned = data.Buildings[buildingId] or 0
	local structure = 0
	for _, milestone in BuildingConfig.StationMilestones do
		if owned >= milestone then
			structure += 1
		end
	end
	return structure + EconomyRules.BuildingUpgradeCount(data, buildingId)
end

function EconomyRules.IsMasterwork(data, buildingId: string): boolean
	return EconomyRules.DetailLevel(data, buildingId) >= BuildingConfig.MaxDetailLevel
end

-- Damage -----------------------------------------------------------------------------------------

function EconomyRules.BuildingDps(data, buildingId: string): number
	local building = BuildingConfig.Get(buildingId)
	local owned = data.Buildings[buildingId] or 0
	if not building or owned <= 0 then
		return 0
	end
	local dps = owned * building.DamagePerSecond
		* UpgradeConfig.BuildingUpgrades.DamageMultiplier ^ EconomyRules.BuildingUpgradeCount(data, buildingId)
	if EconomyRules.IsMasterwork(data, buildingId) then
		dps *= 1 + BuildingConfig.MasterworkBonus
	end
	return dps
end

function EconomyRules.TotalBuildingDps(data): number
	local total = 0
	for _, building in BuildingConfig.Buildings do
		total += EconomyRules.BuildingDps(data, building.Id)
	end
	return total
end

-- The Frost Touch share of building damage each tap adds: the best tier owned.
function EconomyRules.FrostTouchShare(data): number
	local share = 0
	for _, touch in UpgradeConfig.FrostTouch do
		if owns(data, touch.Id) then
			share = math.max(share, touch.TapShareOfBuildingDps)
		end
	end
	return share
end

-- The damage of one tap.
function EconomyRules.TapDamage(data): number
	local pick = UpgradeConfig.IcePick[EconomyRules.PickTier(data)]
	return pick.TapDamage + EconomyRules.FrostTouchShare(data) * EconomyRules.TotalBuildingDps(data)
end

-- Bonuses ----------------------------------------------------------------------------------------

-- The equipped pets' bonus: the sum of their rarity bonuses (doubled for a Golden pet).
function EconomyRules.PetBonus(data): number
	local byUid = {}
	for _, pet in data.Pets do
		byUid[pet.Uid] = pet
	end
	local bonus = 0
	for _, uid in data.Equipped do
		bonus += EconomyRules.PetBonusOf(byUid[uid])
	end
	return bonus
end

-- One pet's bonus (0 for nil).
function EconomyRules.PetBonusOf(pet): number
	local creature = pet and CreatureConfig.Get(pet.CreatureId)
	if not creature then
		return 0
	end
	local bonus = CreatureConfig.GetRarity(creature.Rarity).Bonus
	if pet.Golden then
		bonus *= CreatureConfig.Pets.GoldenBonusMultiplier
	end
	return bonus
end

-- Creature Book pages: { Page, Count, Found, Complete } in CreatureConfig.Book order. A rarity page
-- counts creatures ever rescued (BookSeen); the Golden page counts Golden versions ever made (BookGolden).
function EconomyRules.BookPages(data)
	local pages = {}
	for _, page in CreatureConfig.Book do
		local found = 0
		for _, creature in CreatureConfig.Creatures do
			if page.Page == "Golden" then
				if data.BookGolden and data.BookGolden[creature.Id] then
					found += 1
				end
			elseif creature.Rarity == page.Page and (data.BookSeen[creature.Id] or 0) > 0 then
				found += 1
			end
		end
		table.insert(pages, { Page = page.Page, Count = page.Count, Found = found, Complete = found >= page.Count, Reward = page })
	end
	return pages
end

-- The Creature Book's permanent crystal bonus (0.05 = +5%).
function EconomyRules.BookBonus(data): number
	local bonus = 0
	for _, page in EconomyRules.BookPages(data) do
		if page.Complete then
			bonus += page.Reward.CrystalBonus or 0
		end
	end
	return bonus
end

-- Every crystal multiplier the save decides, times `extra` (passes, Frost Rush, group: server only).
function EconomyRules.Multiplier(data, extra: number?): number
	local yield = 1 + iceUpgrade("CrystalYield").YieldPerTier * EconomyRules.IceTier(data, "CrystalYield")
	local cores = 1 + RebirthConfig.FrostCoreBonus * data.FrostCores
	return (1 + EconomyRules.PetBonus(data)) * (1 + EconomyRules.BookBonus(data)) * yield * cores * (extra or 1)
end

-- The rescue fountain: how many seconds of income it is worth (Bigger Burst).
function EconomyRules.BurstSeconds(data): number
	return iceUpgrade("BiggerBurst").BurstSeconds[EconomyRules.IceTier(data, "BiggerBurst") + 1]
end

-- How long the next block takes to slide in after a rescue (Fast Sled).
function EconomyRules.SledSeconds(data): number
	local sled = iceUpgrade("FastSled")
	return math.max(0, LayerConfig.Block.ArriveSeconds - sled.SecondsSoonerPerTier * EconomyRules.IceTier(data, "FastSled"))
end

-- Buying ------------------------------------------------------------------------------------------

-- What buying `amount` copies costs (1, 10, 100, or "Max": as many as the crystals pay for, at
-- least 1 so the button can show a price). Returns count, cost.
function EconomyRules.BuildingPurchase(data, buildingId: string, amount): (number, number)
	local building = BuildingConfig.Get(buildingId)
	local owned = data.Buildings[buildingId] or 0
	if amount == "Max" then
		-- cost of k = base*g^n*(g^k - 1)/(g - 1) <= crystals  ->  k = floor(log_g(1 + crystals*(g-1)/(base*g^n)))
		local g = BuildingConfig.CostGrowth
		local first = BuildingConfig.Cost(building, owned)
		local count = math.floor(math.log(1 + data.Crystals * (g - 1) / first) / math.log(g) + 1e-9)
		while count > 0 and BuildingConfig.CostOfNext(building, owned, count) > data.Crystals do
			count -= 1
		end
		count = math.max(1, count)
		return count, BuildingConfig.CostOfNext(building, owned, count)
	end
	return amount, BuildingConfig.CostOfNext(building, owned, amount)
end

-- Whether an upgrade can be bought now (ignoring its price). Returns ok, reason.
-- Tiers go in order; a building upgrade needs its copies (UnlockAtOwned) and the one before it;
-- Frost Touch needs a copy of its building.
function EconomyRules.UpgradeUnlocked(data, upgradeId: string): (boolean, string?)
	local upgrade = UpgradeConfig.Get(upgradeId)
	if not upgrade then
		return false, "Unknown upgrade"
	end
	if owns(data, upgradeId) then
		return false, "Already owned"
	end
	if upgrade.Kind == "IcePick" then
		if upgrade.Tier > 2 and not owns(data, "IcePick" .. (upgrade.Tier - 1)) then
			return false, "Buy the " .. UpgradeConfig.IcePick[upgrade.Tier - 1].Name .. " first"
		end
	elseif upgrade.Kind == "FrostTouch" then
		if (data.Buildings[upgrade.UnlockOwns] or 0) < 1 then
			return false, "Own a " .. BuildingConfig.Get(upgrade.UnlockOwns).Name
		end
	elseif upgrade.Kind == "Building" then
		if (data.Buildings[upgrade.Building] or 0) < upgrade.UnlockAtOwned then
			return false, `Own {upgrade.UnlockAtOwned} {BuildingConfig.Get(upgrade.Building).Name}`
		end
		if upgrade.Index > 1 and not owns(data, upgrade.Building .. "Upgrade" .. (upgrade.Index - 1)) then
			return false, "Buy upgrade " .. (upgrade.Index - 1) .. " first"
		end
	elseif upgrade.Kind == "Ice" then
		if upgrade.Tier > 1 and not owns(data, upgrade.Upgrade .. (upgrade.Tier - 1)) then
			return false, "Buy tier " .. (upgrade.Tier - 1) .. " first"
		end
	end
	return true
end

-- The upgrades a player can see in the Upgrades panel: everything not owned whose previous step is
-- owned (the next tier of each line), sorted by price. Locked ones are included with a reason.
function EconomyRules.UpgradeList(data)
	local list = {}
	for _, upgrade in UpgradeConfig.Upgrades do
		if not owns(data, upgrade.Id) then
			local ok, reason = EconomyRules.UpgradeUnlocked(data, upgrade.Id)
			-- shown: what can be bought now, and the next upgrade of a building already owned
			local isNext = ok or (upgrade.Kind == "Building" and (data.Buildings[upgrade.Building] or 0) > 0
				and not string.find(reason or "", "first", 1, true))
			if isNext then
				table.insert(list, { Upgrade = upgrade, Unlocked = ok, Reason = reason })
			end
		end
	end
	table.sort(list, function(a, b)
		if a.Upgrade.Cost ~= b.Upgrade.Cost then
			return a.Upgrade.Cost < b.Upgrade.Cost
		end
		return a.Upgrade.Id < b.Upgrade.Id
	end)
	return list
end

-- One line saying what an upgrade does, for the Upgrades panel.
function EconomyRules.Describe(upgrade): string
	if upgrade.Kind == "IcePick" then
		return `Tap damage {UpgradeConfig.IcePick[upgrade.Tier].TapDamage}`
	elseif upgrade.Kind == "FrostTouch" then
		for _, touch in UpgradeConfig.FrostTouch do
			if touch.Id == upgrade.Id then
				return `Taps add {math.floor(touch.TapShareOfBuildingDps * 100 + 0.5)}% of building damage/s`
			end
		end
	elseif upgrade.Kind == "Building" then
		return `{BuildingConfig.Get(upgrade.Building).Name} damage x{UpgradeConfig.BuildingUpgrades.DamageMultiplier}`
	elseif upgrade.Kind == "Ice" then
		local ice = iceUpgrade(upgrade.Upgrade)
		if ice.BurstSeconds then
			return `Rescue fountain: {ice.BurstSeconds[upgrade.Tier + 1]} s of income`
		elseif ice.YieldPerTier then
			return `+{math.floor(ice.YieldPerTier * 100 + 0.5)}% crystals per damage`
		elseif ice.SecondsSoonerPerTier then
			return `Next block arrives {ice.SecondsSoonerPerTier} s sooner`
		end
	end
	return ""
end

return EconomyRules
