--[[
IceLooks: how the ice block looks (docs/GAME_DESIGN.md, "Glacier depth", "The ice block" and
"Technical design"). Display only; the client's IceBlocks draws from it.

 * Layers[n] (LayerConfig layer numbers): the ice's Color, Material, Transparency at the start (more
   frost, so the silhouette is a blur) and Clear (the transparency at the last crack stage), and an
   Extra effect: "Bubbles" (Ancient Ice), "Sparkles" (Crystal Ice), "Veins" (Primordial Ice),
   "InnerLight" (Frozen Core).
 * Glow[rarity]: the light inside the block, from the moment it arrives: none for Common; Mode "Pulse"
   (Legendary) breathes, "Rainbow" (Mythic) cycles the hue.
 * The redesigned look (below: New, LayerLooks, Rarities, Creature, Auras) is drawn by IceBlockLook.
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
	Uncommon = { Color = Color3.fromRGB(110, 230, 140), Brightness = 1.5, Range = 14 },
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

-- The sparks your taps throw (and a sword's trail), by tool tier (docs/GAME_DESIGN.md, "Tools": "each tier gets
-- its own spark colour").
IceLooks.ToolSparks = {
	Color3.fromRGB(255, 170, 90), -- Wooden Pick: warm orange
	Color3.fromRGB(215, 215, 205), -- Stone Hammer: pale grey
	Color3.fromRGB(255, 140, 70), -- Copper Axe: copper
	Color3.fromRGB(235, 245, 255), -- Iron Pick: white-hot
	Color3.fromRGB(190, 220, 255), -- Steel Sword: steel blue
	Color3.fromRGB(140, 230, 255), -- Frost Spear: frost
	Color3.fromRGB(255, 215, 70), -- Gold Hammer: gold
	Color3.fromRGB(110, 245, 255), -- Crystal Axe: crystal cyan
	Color3.fromRGB(150, 205, 255), -- Ice Drill: ice blue
	Color3.fromRGB(90, 200, 255), -- Diamond Sword: diamond blue
	Color3.fromRGB(255, 120, 40), -- Flame Pick: fire
	Color3.fromRGB(255, 238, 90), -- Thunder Hammer: lightning
	Color3.fromRGB(90, 255, 170), -- Aurora Blade: aurora green
	Color3.fromRGB(255, 75, 30), -- Lava Axe: lava
	Color3.fromRGB(255, 240, 170), -- Starfall Spear: starlight
	Color3.fromRGB(90, 170, 255), -- Comet Hammer: comet blue
	Color3.fromRGB(205, 120, 255), -- Cosmic Pick: violet
	Color3.fromRGB(255, 170, 240), -- Starbreaker: starburst pink
}

-- The magical tools (tiers 11-18; docs/GAME_DESIGN.md, "The tools' look"): a soft light in the tool's spark colour
-- (Light: range in studs, brightness), the swing trail on every family (not only swords), and a hit effect in its
-- theme at the strike (Hit: a MagicHits entry). Reduced effects keeps the tools and drops all three (ToolFX).
IceLooks.ToolMagic = {
	[11] = { Hit = "Embers", Light = { 7, 1.1 } }, -- Flame Pick: fire
	[12] = { Hit = "Lightning", Light = { 7, 1.2 } }, -- Thunder Hammer
	[13] = { Hit = "Aurora", Light = { 7, 1.0 } }, -- Aurora Blade
	[14] = { Hit = "Lava", Light = { 7, 1.2 } }, -- Lava Axe
	[15] = { Hit = "Starfall", Light = { 8, 1.1 } }, -- Starfall Spear: falling stars
	[16] = { Hit = "Comet", Light = { 8, 1.2 } }, -- Comet Hammer: comet fire
	[17] = { Hit = "Cosmic", Light = { 8, 1.2 } }, -- Cosmic Pick: cosmic sparkles
	[18] = { Hit = "Starburst", Light = { 10, 1.4 } }, -- Starbreaker: the big starburst
}
-- The themed hit effects: particles burst out of the strike point (EffectsConfig textures), along the face's normal.
--   Texture, Colours (start, end), Count, Speed {min, max}, Spread (degrees), Size {start, end} (studs), Life {min, max}
--   (seconds), Gravity (studs/s^2, + pulls down, - floats up), Spin (degrees/s), Light (0-1 additive: kept low, since added
--   light vanishes against snow and sky), and Flash {size, seconds} (a soft glow at the point).
local function c(r, g, b)
	return Color3.fromRGB(r, g, b)
end
IceLooks.MagicHits = {
	Embers = { Texture = "Ember", Colours = { c(255, 210, 70), c(255, 70, 20) }, Count = 22, Speed = { 5, 11 }, Spread = 60,
		Size = { 1.8, 0.3 }, Life = { 0.7, 1.1 }, Gravity = -10, Spin = 120, Light = 0.35, Flash = { 5, 0.2 } },
	Lightning = { Texture = "Sparkle", Colours = { c(255, 255, 220), c(255, 225, 60) }, Count = 18, Speed = { 10, 20 }, Spread = 80,
		Size = { 1.4, 0 }, Life = { 0.25, 0.45 }, Gravity = 0, Spin = 0, Light = 0.5, Flash = { 6, 0.16 } },
	Aurora = { Texture = "SoftGlow", Colours = { c(90, 255, 170), c(180, 120, 255) }, Count = 9, Speed = { 3, 6 }, Spread = 70,
		Size = { 3, 0 }, Life = { 0.9, 1.3 }, Gravity = -5, Spin = 40, Light = 0.3, Flash = { 4, 0.2 } },
	Lava = { Texture = "Ember", Colours = { c(255, 220, 80), c(230, 50, 10) }, Count = 16, Speed = { 10, 16 }, Spread = 45,
		Size = { 1.3, 0.5 }, Life = { 0.6, 0.95 }, Gravity = 34, Spin = 60, Light = 0.3, Flash = { 4, 0.16 } },
	Starfall = { Texture = "Star", Colours = { c(255, 250, 210), c(255, 210, 90) }, Count = 12, Speed = { 5, 11 }, Spread = 70,
		Size = { 1.8, 0.3 }, Life = { 0.8, 1.2 }, Gravity = 12, Spin = 180, Light = 0.4, Flash = { 4, 0.18 } },
	Comet = { Texture = "Sparkle", Colours = { c(200, 240, 255), c(60, 150, 255) }, Count = 18, Speed = { 8, 14 }, Spread = 45,
		Size = { 2.2, 0 }, Life = { 0.5, 0.85 }, Gravity = 4, Spin = 0, Light = 0.5, Flash = { 6, 0.22 } },
	Cosmic = { Texture = "Star", Colours = { c(230, 170, 255), c(120, 60, 255) }, Count = 14, Speed = { 3, 9 }, Spread = 90,
		Size = { 1.5, 0 }, Life = { 0.8, 1.2 }, Gravity = -3, Spin = 240, Light = 0.4, Flash = { 5, 0.2 } },
	Starburst = { Texture = "Star", Colours = { c(255, 245, 200), c(255, 140, 230) }, Count = 26, Speed = { 14, 28 }, Spread = 180,
		Size = { 3.2, 0 }, Life = { 0.6, 1.0 }, Gravity = 0, Spin = 200, Light = 0.5, Flash = { 11, 0.28 } },
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

-- The ice block's look: the carved block (tools/blender/ice_block.py, one kit for every layer; per-layer atlases from
-- tools/make_ice_textures.py), drawn by IceBlockLook over IceBlocks' plain block (which stays the hitbox). Without
-- the kit template (ServerStorage.IceTemplates.Kit) the blocks keep the classic look above.
IceLooks.TemplateHeight = 14 -- the kit is built at the level-1 size and scaled with the level
IceLooks.Variants = 3 -- shape variants (snow cap, icicles, base crystals, bubbles), picked at random per block
IceLooks.New = {
	-- the shell's transparency: just above 0, so Roblox uses the atlas's alpha (frosty rims, a clear middle);
	-- each crack stage thins the frost (the creature gets clearer as you get closer to freeing it)
	ShellTransparency = 0.02,
	ThinPerStage = 0.075,
	CreatureLift = 0.05, -- the creature stands this far (times the height) above the block's bottom
	-- the soft glow behind the creature (a camera-facing beam): its size and depth times the height; how much it adds
	-- light and how bright it is are the layer's GlowEmission and GlowBrightness (added light reads on dark ice, a plain
	-- colour on white snow)
	Glow = { Size = 0.85, Behind = 0.24, Transparency = 0.3, Whiten = 0.1 },
	LightScale = 0.3, -- the block's point light (IceLooks.Glow) is this strong with this look: it flooded white snow
	Motes = { Rate = 2.5, Size = 0.6, Lifetime = { 3, 5 }, Speed = { 0.15, 0.5 } }, -- drifting motes (Epic and up)
	Mist = { Rate = 3.5, Size = { 2.5, 6 }, Lifetime = { 2.5, 4 }, Speed = { 1.2, 2.4 }, Transparency = 0.35 },
	Shimmer = { Period = 7, TileHeights = 4, Transparency = 0.5 }, -- a soft band sweeping across the faces
	Sparkles = { Rate = 6 }, -- Crystal Ice's sparkles in the ice
	TapSquash = { Amount = 0.03, Seconds = 0.16 }, -- every tap: squash and recover (restarts, never stacks)
	Chunks = { PerStage = { 1, 2 }, Life = 2.2 }, -- chunks breaking off at each crack stage
	Pieces = { Speed = { 10, 20 }, Up = { 16, 26 }, Life = 1.8, FadeFrom = 1.1 }, -- the shatter's pre-cut pieces
}

-- Each layer (LayerConfig numbers): its atlas (IceLooks.Textures key), an extra (the kit's Drifts, CrystalClusters or
-- Veins), DenseBubbles in place of the variant's bubbles, no icicles or base crystals on snow, the veins' colour, a
-- light inside, and how much the creature's glow adds light (GlowEmission: 0 a plain colour, 1 added light).
IceLooks.LayerLooks = {
	{ Atlas = "FreshSnow", Extra = "Drifts", NoCrystals = true, GlowEmission = 0, GlowBrightness = 1 },
	{ Atlas = "BlueIce", GlowEmission = 0.7, GlowBrightness = 1.6 },
	{ Atlas = "AncientIce", DenseBubbles = true, GlowEmission = 1, GlowBrightness = 2 },
	{ Atlas = "CrystalIce", Extra = "CrystalClusters", Sparkles = true, GlowEmission = 0.6, GlowBrightness = 1.4 },
	{ Atlas = "PrimordialIce", Extra = "Veins", VeinColor = Color3.fromRGB(80, 255, 220), GlowEmission = 1, GlowBrightness = 2 },
	{ Atlas = "FrozenCore", Extra = "Veins", VeinColor = Color3.fromRGB(255, 120, 50), InnerLight = Color3.fromRGB(255, 130, 60), GlowEmission = 1, GlowBrightness = 2 },
}

-- The creature inside, by rarity: its colour (the glow, its frosty outline and its eyes; Legendary amber, not gold,
-- which reads green through blue ice; Mythic cycles the rainbow), how strong the glow behind it is (Common: none),
-- and whether motes drift round it.
IceLooks.Rarities = {
	Common = { Colour = Color3.fromRGB(232, 242, 255), Glow = 0 },
	Uncommon = { Colour = Color3.fromRGB(110, 230, 140), Glow = 0.55 },
	Rare = { Colour = Color3.fromRGB(90, 175, 255), Glow = 0.7 },
	Epic = { Colour = Color3.fromRGB(190, 105, 255), Glow = 0.85, Motes = true },
	Legendary = { Colour = Color3.fromRGB(255, 140, 35), Glow = 1, Motes = true },
	Mythic = { Colour = Color3.fromRGB(255, 120, 220), Glow = 1, Motes = true, Rainbow = true },
}
IceLooks.Creature = {
	Outline = 0, -- the outline's transparency (a Highlight outline round the silhouette)
	Blink = { Every = { 3, 5.5 }, Seconds = 0.15 }, -- the glowing eyes blink now and then
	Reveal = { [3] = 0.22, [4] = 0.42 }, -- how much of its real colours shows through at crack stages 3 and 4
	RainbowSeconds = 8, -- Mythic: one turn of the rainbow
}

-- The rarity auras off the block (Epic and up): a soft ring of light behind the whole block (a beam, so it shows
-- across the plaza and never washes over the block or the creature), plus particles near you (the effect rules:
-- your plot at full rate, others at half within 60 studs, none beyond; reduced effects: the ring and fewer
-- particles, no rays or spirals).
IceLooks.Auras = {
	Epic = { Halo = 2.3, HaloTransparency = 0.5, Wisps = { Rate = 9, Colour = Color3.fromRGB(165, 95, 255) } },
	-- (stronger since the sunset: the warm snow and orange sky took some of its contrast)
	Legendary = {
		Halo = 2.6, HaloTransparency = 0.22, Pulse = { Speed = 2, Depth = 0.3 },
		Flames = { Rate = 34, Colour = Color3.fromRGB(255, 175, 40), Tip = Color3.fromRGB(255, 60, 10) },
		Embers = { Rate = 16, Colour = Color3.fromRGB(255, 140, 30) },
		Rays = { Count = 5, Length = 1.5, Width = { 0.18, 0.66 }, Spread = 44, Transparency = 0.25 },
	},
	Mythic = {
		Halo = 2.9, HaloTransparency = 0.3, PulseEvery = 3.5, PulseSeconds = 0.5,
		Sparkles = { Rate = 18, Orbiters = 2, LoopSeconds = 2.8 },
	},
	-- the ring and the flames are mostly plain colour (added light vanishes against bright snow and sky); the ring fades
	-- out towards the ground, so the stage under the block stays clean
	HaloEmission = 0.2,
	HaloBrightness = 1.4,
	HaloFadeBottom = 0.3,
	ParticleBox = 1.18, -- the flames and wisps come off a box this much wider than the block (outside the ice)
	FadeSeconds = 0.35, -- how fast an aura fades when the block shatters
	Burst = { Epic = 18, Legendary = 30, Mythic = 44 }, -- the shatter's extra burst in the aura's colour
}

-- BEGIN ASSET IDS (generated by tools/write_asset_ids.py from the upload manifests; don't edit by hand)
IceLooks.Textures = {
	FreshSnow = "rbxassetid://114602828856860",
	BlueIce = "rbxassetid://118232142318427",
	AncientIce = "rbxassetid://111223972877647",
	CrystalIce = "rbxassetid://126663887658563",
	PrimordialIce = "rbxassetid://100770305195930",
	FrozenCore = "rbxassetid://125764290350747",
	Glow = "rbxassetid://138336382402637",
	Shimmer = "rbxassetid://119012227357167",
	Halo = "rbxassetid://95835941638534",
	Ray = "rbxassetid://116885948215574",
	Flame = "rbxassetid://71126004192467",
}
IceLooks.KitModelId = 121512291794378
-- END ASSET IDS

return IceLooks
