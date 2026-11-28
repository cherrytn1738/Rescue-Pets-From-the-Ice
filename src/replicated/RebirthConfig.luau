--[[
RebirthConfig: rebirths, Frost Cores and rebirth ranks (docs/GAME_DESIGN.md, "Rebirth" and "Pets").
Starting values for the economy simulation.

 * A rebirth needs block level RequiredLevel (Layer 4, Crystal Ice). It resets the run and grants
   Frost Cores = floor(cube root(crystals earned this run / CrystalsPerCoreUnit)); each Frost Core adds
   FrostCoreBonus (+5%) crystals forever.
 * Ranks[n]: Rank (the rebirth count that reaches it), Title, Colour (name tag and plot border),
   PetSlot (the equip slot it opens), OpensLayer (the LayerConfig layer it opens; Layer 7 comes in an
   update and isn't in LayerConfig yet). A player keeps the highest rank reached.
 * ResetOnRebirth / KeptOnRebirth: which saved fields (PlayerData) a rebirth resets and keeps.
 * Checked against the design doc by tests/RebirthConfig.spec.luau.
]]
local RebirthConfig = {}

RebirthConfig.RequiredLevel = 31
RebirthConfig.GoalFromLevel = 25 -- the HUD shows the rebirth goal from this block level
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
	if type(crystalsThisRun) ~= "number" or crystalsThisRun ~= crystalsThisRun then
		return 0
	end
	local units = math.max(0, crystalsThisRun) / RebirthConfig.CrystalsPerCoreUnit
	local cores = math.floor(units ^ (1 / 3))
	-- Past 2^50 cores, adding 1 no longer changes a double: the exact-cube nudges below would never end (a frozen
	-- server at about 1e51 crystals in a run). That far, the cube root is as exact as a number can be anyway.
	if cores >= 2 ^ 50 or cores ~= cores then
		return if cores ~= cores then 0 else cores
	end
	while (cores + 1) ^ 3 <= units do
		cores += 1
	end
	while cores > 0 and cores ^ 3 > units do
		cores -= 1
	end
	return cores
end

-- The HUD's rebirth goal (docs/GAME_DESIGN.md, "Rebirth"): nil below GoalFromLevel; otherwise
-- { Ready, LevelsLeft, Cores } (the Frost Cores a rebirth would give now).
function RebirthConfig.Goal(level: number, crystalsThisRun: number)
	if type(level) ~= "number" or level < RebirthConfig.GoalFromLevel then
		return nil
	end
	return {
		Ready = level >= RebirthConfig.RequiredLevel,
		LevelsLeft = math.max(0, RebirthConfig.RequiredLevel - level),
		Cores = RebirthConfig.FrostCoresFor(crystalsThisRun or 0),
	}
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
