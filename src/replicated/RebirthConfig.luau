--[[
RebirthConfig: rebirths, Frost Cores and rebirth ranks (docs/GAME_DESIGN.md, "Rebirth" and "Pets").
Starting values for the economy simulation.

 * A rebirth needs block level RequiredLevel (Layer 3, Ancient Ice). It resets the run and grants
   Frost Cores = floor(cube root(crystals earned this run / CrystalsPerCoreUnit)); each Frost Core adds
   FrostCoreBonus (+5%) crystals forever.
 * Ranks[n]: Rank (the rebirth count that reaches it), Title, Colour (name tag and plot border),
   PetSlot (the equip slot it opens), OpensLayer (the LayerConfig layer it opens; Layer 7 comes in an
   update and isn't in LayerConfig yet). A player keeps the highest rank reached.
 * ResetOnRebirth / KeptOnRebirth: which saved fields (PlayerData) a rebirth resets and keeps.
 * Checked against the design doc by tests/RebirthConfig.spec.luau.
]]
local RebirthConfig = {}

RebirthConfig.RequiredLevel = 21
RebirthConfig.FrostCoreBonus = 0.05
RebirthConfig.CrystalsPerCoreUnit = 1_000_000

RebirthConfig.Ranks = {
	{ Rank = 1, Title = "Ice Breaker", Colour = "Light blue" },
	{ Rank = 2, Title = "Frost Finder", Colour = "Teal" },
	{ Rank = 3, Title = "Glacier Diver", Colour = "Purple", PetSlot = 2, OpensLayer = 6 },
	{ Rank = 6, Title = "Core Keeper", Colour = "Gold", PetSlot = 3 },
	{ Rank = 10, Title = "Glacier Legend", Colour = "Rainbow", PetSlot = 4, OpensLayer = 7 },
}

-- The rank colours as Color3 (name tag and plot border). "Rainbow" cycles on the client.
RebirthConfig.ColourValues = {
	["Light blue"] = Color3.fromRGB(150, 215, 255),
	Teal = Color3.fromRGB(60, 210, 190),
	Purple = Color3.fromRGB(175, 110, 255),
	Gold = Color3.fromRGB(255, 205, 60),
	Rainbow = Color3.fromRGB(255, 120, 200),
}

-- Saved fields (PlayerData) a rebirth resets, and the ones it keeps.
RebirthConfig.ResetOnRebirth = { "Crystals", "CrystalsThisRun", "BlockLevel", "CurrentBlock", "Buildings", "Upgrades" }
RebirthConfig.KeptOnRebirth = { "CrystalsAllTime", "Pets", "Equipped", "BookSeen", "FrostCores", "Rebirths", "MaxLayerOpened", "CreaturesRescued" }

-- Frost Cores earned for a run: floor(cube root(crystalsThisRun / 1,000,000)), exact for whole cubes.
function RebirthConfig.FrostCoresFor(crystalsThisRun: number): number
	local units = math.max(0, crystalsThisRun) / RebirthConfig.CrystalsPerCoreUnit
	local cores = math.floor(units ^ (1 / 3))
	while (cores + 1) ^ 3 <= units do
		cores += 1
	end
	while cores > 0 and cores ^ 3 > units do
		cores -= 1
	end
	return cores
end

-- The highest rank reached with this many rebirths, or nil before the first.
function RebirthConfig.RankFor(rebirths: number)
	local reached = nil
	for _, rank in RebirthConfig.Ranks do
		if rebirths >= rank.Rank then
			reached = rank
		end
	end
	return reached
end

-- Equip slots earned from rebirth ranks (passes add more on top).
function RebirthConfig.PetSlotsFor(rebirths: number, baseSlots: number): number
	local slots = baseSlots
	for _, rank in RebirthConfig.Ranks do
		if rebirths >= rank.Rank and rank.PetSlot then
			slots = math.max(slots, rank.PetSlot)
		end
	end
	return slots
end

-- The deepest layer opened with this many rebirths (floorLayer without any), limited to the layers
-- that exist (layerCount).
function RebirthConfig.MaxLayerFor(rebirths: number, floorLayer: number, layerCount: number): number
	local deepest = floorLayer
	for _, rank in RebirthConfig.Ranks do
		if rebirths >= rank.Rank and rank.OpensLayer and rank.OpensLayer <= layerCount then
			deepest = math.max(deepest, rank.OpensLayer)
		end
	end
	return deepest
end

return RebirthConfig
