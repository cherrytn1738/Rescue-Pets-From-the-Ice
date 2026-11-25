--[[
IceLooks: how the ice block looks (docs/GAME_DESIGN.md, "Glacier depth", "The ice block" and
"Technical design"). Display only; the client's IceBlocks draws from it.

 * Layers[n] (LayerConfig layer numbers): the ice's Color, Material, Transparency at the start (more
   frost, so the silhouette is a blur) and Clear (the transparency at the last crack stage), and an
   Extra effect: "Bubbles" (Ancient Ice), "Sparkles" (Crystal Ice), "Veins" (Primordial Ice),
   "InnerLight" (Frozen Core).
 * Glow[rarity]: the light inside the block, from the moment it arrives: none for Common and
   Uncommon; Mode "Pulse" (Legendary) breathes, "Rainbow" (Mythic) cycles the hue.
 * Silhouette: the creature inside is SilhouetteShare of the block's height.
 * Stages (by crack stage 0-4): how the inside reads. 0 = a dark blur behind heavy frost; 1 hairline
   cracks; 2 chunks fall, the shape is clear; 3 the eyes show and blink; 4 it wiggles, the glow
   brightens, a heartbeat.
]]
local IceLooks = {}

IceLooks.Layers = {
	{ Color = Color3.fromRGB(240, 246, 255), Material = Enum.Material.Snow, Transparency = 0.32, Clear = 0.2 }, -- Fresh Snow: packed white snow, soft edges
	{ Color = Color3.fromRGB(170, 218, 255), Material = Enum.Material.Ice, Transparency = 0.42, Clear = 0.6 }, -- Blue Ice: clear pale blue
	{ Color = Color3.fromRGB(55, 105, 205), Material = Enum.Material.Ice, Transparency = 0.38, Clear = 0.55, Extra = "Bubbles" }, -- Ancient Ice
	{ Color = Color3.fromRGB(160, 238, 255), Material = Enum.Material.Glass, Transparency = 0.45, Clear = 0.62, Extra = "Sparkles" }, -- Crystal Ice
	{ Color = Color3.fromRGB(22, 98, 108), Material = Enum.Material.Ice, Transparency = 0.36, Clear = 0.52, Extra = "Veins", VeinColor = Color3.fromRGB(80, 255, 220) }, -- Primordial Ice
	{ Color = Color3.fromRGB(16, 18, 30), Material = Enum.Material.Glass, Transparency = 0.3, Clear = 0.48, Extra = "InnerLight", VeinColor = Color3.fromRGB(255, 120, 60) }, -- Frozen Core
}

IceLooks.Glow = {
	Rare = { Color = Color3.fromRGB(110, 180, 255), Brightness = 2.5, Range = 18 },
	Epic = { Color = Color3.fromRGB(185, 95, 255), Brightness = 3, Range = 20 },
	-- (amber, not gold: gold light through the blue ice read lime green)
	Legendary = { Color = Color3.fromRGB(255, 120, 20), Brightness = 4, Range = 24, Mode = "Pulse" },
	Mythic = { Color = Color3.fromRGB(255, 255, 255), Brightness = 4.5, Range = 26, Mode = "Rainbow" },
}

-- The rarity colours used by banners and labels (also the Book's page tabs).
IceLooks.RarityColors = {
	Common = Color3.fromRGB(205, 215, 230),
	Uncommon = Color3.fromRGB(110, 225, 130),
	Rare = Color3.fromRGB(90, 170, 255),
	Epic = Color3.fromRGB(185, 105, 255),
	Legendary = Color3.fromRGB(255, 200, 50),
	Mythic = Color3.fromRGB(255, 110, 200),
}

IceLooks.SilhouetteShare = 0.6
IceLooks.BlockWidthShare = 0.8 -- the block is this wide (and deep) for its height
IceLooks.SledDistance = 46 -- studs behind the mound the next block slides in from
IceLooks.SledSeconds = 0.9 -- the slide itself (the rest of the wait the block is out of sight)
IceLooks.GlowBoostAtStage4 = 1.8
IceLooks.Particles = { Chips = 5, Sparkles = 3, Shards = 26, Fountain = 40 } -- halved with reduced effects

-- The sparks your taps throw, by ice pick tier (docs/GAME_DESIGN.md, "Upgrades": wood, stone, iron, gold,
-- diamond, cosmic, "each with its own spark colour").
IceLooks.PickSparks = {
	Color3.fromRGB(255, 170, 90), -- wood: warm orange
	Color3.fromRGB(215, 215, 205), -- stone: pale grey
	Color3.fromRGB(235, 245, 255), -- iron: white-hot
	Color3.fromRGB(255, 215, 70), -- gold
	Color3.fromRGB(120, 245, 255), -- diamond: cyan
	Color3.fromRGB(205, 120, 255), -- cosmic: violet
}

-- The crystals (the tap spray, building-hit pops and the rescue fountain) by how many ice upgrade tiers the
-- player owns (Bigger Burst, Crystal Yield, Fast Sled: 7 in all): white, then blue, then gold.
IceLooks.CrystalColours = {
	{ MinTiers = 0, Color = Color3.fromRGB(235, 248, 255) },
	{ MinTiers = 3, Color = Color3.fromRGB(110, 200, 255) },
	{ MinTiers = 6, Color = Color3.fromRGB(255, 210, 80) },
}

-- The crystal colour for this many ice upgrade tiers.
function IceLooks.CrystalColour(iceTiers: number): Color3
	local colour = IceLooks.CrystalColours[1].Color
	for _, step in IceLooks.CrystalColours do
		if iceTiers >= step.MinTiers then
			colour = step.Color
		end
	end
	return colour
end

-- Building hits on your own block pop a few crystals, at most this often (seconds).
IceLooks.HitCrystalSeconds = 0.6

-- Rescue confetti in the rarity colour (your own rescues).
IceLooks.Confetti = 36

return IceLooks
