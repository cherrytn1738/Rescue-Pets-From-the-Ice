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
	-- (see-through dark ice: near-opaque black glass hid the silhouette, the veins and any rarity glow)
	{ Color = Color3.fromRGB(30, 34, 60), Material = Enum.Material.Ice, Transparency = 0.45, Clear = 0.6, Extra = "InnerLight", VeinColor = Color3.fromRGB(255, 120, 60) }, -- Frozen Core
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

-- The redesigned block, built in Blender (tools/blender/ice_block.py, textures tools/make_ice_textures.py) and
-- drawn by IceBlockLook. Part 1 of the redesign: three options for one test case (Blue Ice), shown only in
-- Studio with the client switch Workspace "StudioIceOption" = "A" (faceted iceberg), "B" (carved block) or "C"
-- (crystal geode); without it every block keeps the look above.
IceLooks.Options = { "A", "B", "C" }
IceLooks.TemplateHeight = 14 -- the templates are built at the level-1 size and scaled with the level
IceLooks.New = {
	-- the shell's transparency: just above 0, so Roblox uses the atlas's alpha (frosty rims, a clear middle);
	-- each crack stage thins the frost (the creature gets clearer as you get closer to freeing it)
	ShellTransparency = 0.02,
	ThinPerStage = 0.075,
	CreatureCentre = 0.36, -- the creature's middle, times the block's height
	CreatureLift = 0.05, -- the creature stands this far (times the height) above the block's bottom
	-- the soft glow behind the creature: added light (LightEmission 1; a plain colour reads darker than pale ice)
	Glow = { Size = 1.1, Behind = 0.24, Transparency = 0.25, Brightness = 2.2, Whiten = 0.15 },
	-- a tint over an option's whole shell (C: a deeper, geode blue)
	ShellTint = { C = Color3.fromRGB(150, 192, 255) },
	Rim = { OutlineTransparency = 0.3, FillTransparency = 1, Whiten = 0.45 }, -- the creature's rim light: the rarity colour, lightened
	Motes = { Rate = 2.5, Size = 0.6, Lifetime = { 3, 5 }, Speed = { 0.15, 0.5 } }, -- drifting motes (rare and up)
	Mist = { Rate = 3.5, Size = { 2.5, 6 }, Lifetime = { 2.5, 4 }, Speed = { 1.2, 2.4 }, Transparency = 0.35 },
	Shimmer = { Period = 7, TileHeights = 4, Transparency = 0.5 }, -- a soft band sweeping across the faces
}

-- BEGIN ASSET IDS (generated by tools/write_asset_ids.py from the upload manifests; don't edit by hand)
IceLooks.Textures = {
	Atlas = "rbxassetid://104417678687508",
	Glow = "rbxassetid://138336382402637",
	Shimmer = "rbxassetid://119012227357167",
}
IceLooks.OptionModelIds = {
	A = 93574148754606,
	B = 109948280058251,
	C = 86807805934381,
}
-- END ASSET IDS

return IceLooks
