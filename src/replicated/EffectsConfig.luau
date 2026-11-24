--[[
EffectsConfig: every building's particles, beams and lights (docs/GAME_DESIGN.md, "Effects and auras").
Client only (BuildingEffects.client reads it). Each tier adds a layer on top of the one before; every
Legendary form has a signature aura; a Masterwork adds gold on top.

  EffectsConfig.Textures[key]      the shared particle textures (assets/textures/particles/*.png), uploaded
                                   to the group: an id, or nil until uploaded (then Placeholder is used).
  EffectsConfig.Rules              the performance rules (own plot full; other plots half rate within 60
                                   studs, none beyond; at most 2 lights per building; a hit-effect cap per
                                   second; reduced effects: no hit effects, half the ambient particles).
  EffectsConfig.For(buildingId, tier, masterwork) -> { Ambient = { emitter... }, Hit = { emitter... },
                                   Lights = { light... }, Beams = { beam... } }
     emitter = { Name, Attachment, Texture, Color = { c0, c1 }, Rate (per second; Hit: Burst = count),
                 Size = { start, end }, Lifetime = { min, max }, Speed = { min, max }, Spread (degrees),
                 LightEmission, Transparency = { start, end }, Acceleration (Vector3), Spin (degrees/s),
                 Drag, ZOffset, Orbit (true: particles emitted round the attachment in a ring of radius R) }
     light   = { Name, Attachment, Color, Brightness, Range, Pulse (seconds per pulse, optional) }
     beam    = { Name, From, To, Texture, Color, Width, Speed }
  Attachment names are the stations' own (BuildingModels); tests/Effects.spec.luau checks that every one
  named here exists on its model.
]]
local EffectsConfig = {}

EffectsConfig.Textures = {
	SoftGlow = nil,
	Sparkle = nil,
	Snowflake = nil,
	Ember = nil,
	SmokePuff = nil,
	Star = nil,
	WaterDroplet = nil,
	Rune1 = nil,
	Rune2 = nil,
	Rune3 = nil,
	Rune4 = nil,
}
-- Until the textures are uploaded (as group 921449746): Roblox's built-in particle texture.
EffectsConfig.Placeholder = "rbxasset://textures/particles/sparkles_main.dds"
EffectsConfig.TextureFiles = { -- for the upload: assets/textures/particles/<file>
	SoftGlow = "soft_glow.png", Sparkle = "sparkle.png", Snowflake = "snowflake.png", Ember = "ember.png",
	SmokePuff = "smoke_puff.png", Star = "star.png", WaterDroplet = "water_droplet.png",
	Rune1 = "rune_1.png", Rune2 = "rune_2.png", Rune3 = "rune_3.png", Rune4 = "rune_4.png",
}

EffectsConfig.Rules = {
	OtherPlotRate = 0.5, -- other players' plots: ambient effects at half rate...
	OtherPlotDistance = 60, -- ...within 60 studs, none beyond
	MaxLightsPerBuilding = 2,
	HitEffectsPerSecond = 8, -- across all your buildings: a fast tick never floods the screen
	ReducedAmbient = 0.5, -- the reduced-effects setting halves ambient particles...
	ReducedHits = false, -- ...and turns hit effects off
	HitIntervalSeconds = { 1.6, 0.6 }, -- a building's visible hits: every 1.6 s with one copy, faster as more are owned, down to 0.6 s
	CheckSeconds = 0.5, -- how often the distance and setting rules are re-applied
}

local function rgb(r, g, b)
	return Color3.fromRGB(r, g, b)
end

-- Each building's colour: the Enchanted aura ring and motes, and its Legendary ground ring.
EffectsConfig.BuildingColours = {
	IcePickPost = rgb(150, 220, 255),
	HeatLamp = rgb(255, 190, 90),
	ChiselMill = rgb(90, 220, 210),
	IceDrill = rgb(110, 230, 255),
	WreckingCrane = rgb(200, 170, 120),
	FlamethrowerTurret = rgb(255, 120, 60),
	LavaPump = rgb(255, 100, 40),
	SunMirrorTower = rgb(255, 230, 140),
}

local WHITE = rgb(255, 255, 255)
local GOLD = rgb(255, 214, 64)
local ICE = rgb(150, 225, 255)

-- The layers by tier (each tier keeps the layers below it).
local function tierLayers(tier: number, colour: Color3)
	local ambient, hit, lights, beams = {}, {}, {}, {}
	-- 1 Scrappy: no ambient; a puff of dust on every hit
	table.insert(hit, { Name = "Dust", Attachment = "Hit", Texture = "SmokePuff", Color = { rgb(220, 205, 185), rgb(200, 190, 180) }, Burst = 6,
		Size = { 0.6, 1.4 }, Lifetime = { 0.4, 0.7 }, Speed = { 3, 6 }, Spread = 50, Transparency = { 0.3, 1 }, Drag = 4 })
	if tier >= 2 then -- Workshop: steam puffs, a warm lantern light; hits add a few sparks
		table.insert(ambient, { Name = "Steam", Attachment = "Steam1", Texture = "SmokePuff", Color = { WHITE, rgb(220, 230, 240) }, Rate = 2,
			Size = { 0.6, 2.2 }, Lifetime = { 1.2, 2 }, Speed = { 2, 3 }, Spread = 12, Transparency = { 0.35, 1 }, Acceleration = Vector3.new(0, 1.5, 0) })
		table.insert(lights, { Name = "Lantern", Attachment = "Lamp1", Color = rgb(255, 190, 110), Brightness = 1.6, Range = 10 })
		table.insert(hit, { Name = "Sparks", Attachment = "Hit", Texture = "Sparkle", Color = { rgb(255, 220, 120), rgb(255, 140, 40) }, Burst = 5,
			Size = { 0.3, 0.05 }, Lifetime = { 0.3, 0.5 }, Speed = { 8, 14 }, Spread = 60, LightEmission = 1, Acceleration = Vector3.new(0, -20, 0) })
	end
	if tier >= 3 then -- Frost-tech: cold mist at the base, ice sparkles, a pulsing blue light; hits: ice chips and blue sparks
		table.insert(ambient, { Name = "ColdMist", Attachment = "Aura", Texture = "SmokePuff", Color = { rgb(210, 240, 255), rgb(170, 215, 255) }, Rate = 3,
			Size = { 2, 4 }, Lifetime = { 2, 3 }, Speed = { 0.3, 0.8 }, Spread = 90, Transparency = { 0.6, 1 }, Orbit = true, R = 3 })
		table.insert(ambient, { Name = "IceSparkles", Attachment = "Top", Texture = "Sparkle", Color = { ICE, WHITE }, Rate = 3,
			Size = { 0.4, 0 }, Lifetime = { 0.8, 1.4 }, Speed = { 0.5, 1.5 }, Spread = 180, LightEmission = 1 })
		table.insert(lights, { Name = "CoilPulse", Attachment = "Work", Color = rgb(110, 200, 255), Brightness = 2, Range = 9, Pulse = 1.6 })
		table.insert(hit, { Name = "IceChips", Attachment = "Hit", Texture = "Snowflake", Color = { ICE, WHITE }, Burst = 6,
			Size = { 0.35, 0.15 }, Lifetime = { 0.4, 0.8 }, Speed = { 6, 10 }, Spread = 55, Acceleration = Vector3.new(0, -25, 0), Spin = 200 })
	end
	if tier >= 4 then -- Enchanted: an aura ring in the building's colour, crystal motes, orbiting runes, light beams from gems
		table.insert(ambient, { Name = "AuraRing", Attachment = "Aura", Texture = "SoftGlow", Color = { colour, colour }, Rate = 6,
			Size = { 1.2, 0.6 }, Lifetime = { 1.5, 2 }, Speed = { 0, 0.2 }, Spread = 0, LightEmission = 0.8, Transparency = { 0.4, 1 }, Orbit = true, R = 4 })
		table.insert(ambient, { Name = "Motes", Attachment = "Aura", Texture = "Sparkle", Color = { colour, WHITE }, Rate = 4,
			Size = { 0.3, 0.1 }, Lifetime = { 2, 3 }, Speed = { 1, 2 }, Spread = 25, LightEmission = 1, Orbit = true, R = 2.5 })
		table.insert(ambient, { Name = "Runes", Attachment = "Aura", Texture = "Rune1", Color = { rgb(200, 180, 255), rgb(150, 110, 255) }, Rate = 1.5,
			Size = { 0.6, 0.4 }, Lifetime = { 3, 4 }, Speed = { 0.4, 0.8 }, Spread = 10, LightEmission = 1, Orbit = true, R = 3.5, Spin = 30 })
		table.insert(beams, { Name = "GemBeam", From = "Lamp1", To = "Top", Texture = "SoftGlow", Color = colour, Width = 0.4, Speed = 0.5 })
		hit = { hit[1], { Name = "RuneFlash", Attachment = "Hit", Texture = "Rune2", Color = { rgb(220, 200, 255), colour }, Burst = 2,
			Size = { 0.8, 1.6 }, Lifetime = { 0.3, 0.4 }, Speed = { 0, 1 }, Spread = 10, LightEmission = 1, Transparency = { 0, 1 } },
			{ Name = "SparkleBurst", Attachment = "Hit", Texture = "Sparkle", Color = { WHITE, colour }, Burst = 8,
			Size = { 0.4, 0 }, Lifetime = { 0.4, 0.7 }, Speed = { 5, 9 }, Spread = 180, LightEmission = 1 } }
	end
	if tier >= 5 then -- Legendary: a glowing ground ring, a slow light pulse; hits: a big themed burst and a small shockwave
		table.insert(ambient, { Name = "GroundRing", Attachment = "Aura", Texture = "SoftGlow", Color = { colour, GOLD }, Rate = 10,
			Size = { 1.4, 0.8 }, Lifetime = { 1.5, 2 }, Speed = { 0, 0 }, Spread = 0, LightEmission = 1, Transparency = { 0.3, 1 }, Orbit = true, R = 5 })
		lights = { { Name = "LegendPulse", Attachment = "Top", Color = colour, Brightness = 2.5, Range = 14, Pulse = 2.5 }, lights[1] }
		table.insert(hit, { Name = "Shockwave", Attachment = "Hit", Texture = "SoftGlow", Color = { WHITE, colour }, Burst = 12,
			Size = { 0.6, 0.2 }, Lifetime = { 0.35, 0.45 }, Speed = { 10, 12 }, Spread = 90, LightEmission = 1, Orbit = true, R = 0.5 })
	end
	return ambient, hit, lights, beams
end

-- The Legendary forms' signature auras (the doc's table), on top of the tier layers.
EffectsConfig.Signatures = {
	IcePickPost = { -- Frost Golem: swirling snow flurries and a frost ring that creeps across the ground
		{ Name = "Flurries", Attachment = "Top", Texture = "Snowflake", Color = { WHITE, ICE }, Rate = 8, Size = { 0.4, 0.2 }, Lifetime = { 2, 3 },
			Speed = { 2, 4 }, Spread = 180, Spin = 90, Orbit = true, R = 3, Acceleration = Vector3.new(0, -1, 0) },
		{ Name = "FrostRing", Attachment = "Aura", Texture = "Snowflake", Color = { ICE, WHITE }, Rate = 6, Size = { 0.8, 1.6 }, Lifetime = { 2.5, 3 },
			Speed = { 0.6, 1 }, Spread = 0, Transparency = { 0.2, 1 }, Orbit = true, R = 3.5 },
	},
	HeatLamp = { -- Captive Star: sun rays turning slowly, heat shimmer and orbiting embers
		{ Name = "SunRays", Attachment = "Work", Texture = "Star", Color = { rgb(255, 240, 180), rgb(255, 200, 90) }, Rate = 3, Size = { 2.5, 3.5 },
			Lifetime = { 2, 2.5 }, Speed = { 0, 0 }, Spread = 0, LightEmission = 1, Transparency = { 0.5, 1 }, Spin = 15 },
		{ Name = "HeatShimmer", Attachment = "Work", Texture = "SoftGlow", Color = { rgb(255, 230, 200), rgb(255, 200, 150) }, Rate = 4,
			Size = { 1.5, 3 }, Lifetime = { 1, 1.5 }, Speed = { 1, 2 }, Spread = 30, Transparency = { 0.85, 1 }, Acceleration = Vector3.new(0, 2, 0) },
		{ Name = "OrbitEmbers", Attachment = "Work", Texture = "Ember", Color = { rgb(255, 200, 90), rgb(255, 90, 30) }, Rate = 6, Size = { 0.3, 0.1 },
			Lifetime = { 2, 3 }, Speed = { 0.5, 1 }, Spread = 180, LightEmission = 1, Orbit = true, R = 2.5 },
	},
	ChiselMill = { -- Kraken Mill: water droplets and bubbles spiralling around it in a teal mist
		{ Name = "Droplets", Attachment = "Top", Texture = "WaterDroplet", Color = { rgb(150, 240, 230), rgb(90, 200, 220) }, Rate = 8,
			Size = { 0.3, 0.2 }, Lifetime = { 1.5, 2.5 }, Speed = { 2, 3 }, Spread = 180, Orbit = true, R = 3, Acceleration = Vector3.new(0, -6, 0) },
		{ Name = "Bubbles", Attachment = "Aura", Texture = "SoftGlow", Color = { rgb(200, 255, 250), rgb(120, 230, 220) }, Rate = 5, Size = { 0.3, 0.5 },
			Lifetime = { 2, 3 }, Speed = { 1.5, 2.5 }, Spread = 10, Transparency = { 0.3, 1 }, Orbit = true, R = 3.5 },
		{ Name = "TealMist", Attachment = "Aura", Texture = "SmokePuff", Color = { rgb(90, 220, 210), rgb(60, 180, 190) }, Rate = 3, Size = { 2.5, 4 },
			Lifetime = { 2.5, 3.5 }, Speed = { 0.3, 0.6 }, Spread = 90, Transparency = { 0.65, 1 }, Orbit = true, R = 3 },
	},
	IceDrill = { -- Mecha Mole Titan: steam from its back, sparks from its claws, cyan energy rings round the drill
		{ Name = "BackSteam", Attachment = "Steam1", Texture = "SmokePuff", Color = { WHITE, rgb(220, 230, 240) }, Rate = 4, Size = { 0.8, 2.6 },
			Lifetime = { 1, 1.8 }, Speed = { 3, 5 }, Spread = 15, Transparency = { 0.3, 1 }, Acceleration = Vector3.new(0, 2, 0) },
		{ Name = "BackSteam2", Attachment = "Steam2", Texture = "SmokePuff", Color = { WHITE, rgb(220, 230, 240) }, Rate = 4, Size = { 0.8, 2.6 },
			Lifetime = { 1, 1.8 }, Speed = { 3, 5 }, Spread = 15, Transparency = { 0.3, 1 }, Acceleration = Vector3.new(0, 2, 0) },
		{ Name = "ClawSparks", Attachment = "Hit", Texture = "Sparkle", Color = { rgb(255, 230, 140), rgb(255, 160, 60) }, Rate = 3, Size = { 0.25, 0 },
			Lifetime = { 0.3, 0.6 }, Speed = { 4, 8 }, Spread = 60, LightEmission = 1, Acceleration = Vector3.new(0, -20, 0) },
		{ Name = "DrillRings", Attachment = "Work", Texture = "SoftGlow", Color = { rgb(110, 230, 255), rgb(60, 180, 255) }, Rate = 14, Size = { 0.5, 0.2 },
			Lifetime = { 0.8, 1 }, Speed = { 2, 3 }, Spread = 0, LightEmission = 1, Orbit = true, R = 1.3 },
	},
	WreckingCrane = { -- Titan Arm: small rocks orbiting the meteor and a dust storm at its base
		{ Name = "OrbitRocks", Attachment = "Work", Texture = "SmokePuff", Color = { rgb(120, 110, 100), rgb(90, 80, 75) }, Rate = 5, Size = { 0.4, 0.4 },
			Lifetime = { 2, 3 }, Speed = { 0.5, 1 }, Spread = 180, Orbit = true, R = 2, Spin = 120 },
		{ Name = "DustStorm", Attachment = "Aura", Texture = "SmokePuff", Color = { rgb(210, 190, 160), rgb(170, 150, 130) }, Rate = 8, Size = { 2, 4 },
			Lifetime = { 1.5, 2.5 }, Speed = { 2, 4 }, Spread = 90, Transparency = { 0.5, 1 }, Orbit = true, R = 4 },
	},
	FlamethrowerTurret = { -- Dragon Turret: drifting embers, curling smoke and an ember ring on the ground
		{ Name = "Embers", Attachment = "Top", Texture = "Ember", Color = { rgb(255, 200, 90), rgb(255, 80, 30) }, Rate = 8, Size = { 0.3, 0.1 },
			Lifetime = { 2, 3 }, Speed = { 1, 2 }, Spread = 60, LightEmission = 1, Acceleration = Vector3.new(0, 1.5, 0) },
		{ Name = "CurlingSmoke", Attachment = "Work", Texture = "SmokePuff", Color = { rgb(80, 75, 75), rgb(40, 40, 45) }, Rate = 3, Size = { 1, 3 },
			Lifetime = { 2, 3 }, Speed = { 1, 2 }, Spread = 20, Transparency = { 0.5, 1 }, Spin = 40, Acceleration = Vector3.new(0, 2, 0) },
		{ Name = "EmberRing", Attachment = "Aura", Texture = "Ember", Color = { rgb(255, 160, 60), rgb(255, 70, 20) }, Rate = 10, Size = { 0.4, 0.1 },
			Lifetime = { 1.5, 2 }, Speed = { 0, 0.3 }, Spread = 0, LightEmission = 1, Orbit = true, R = 4.5 },
	},
	LavaPump = { -- Volcano Forge: lava sparks shooting up, heat haze and glowing smoke
		{ Name = "LavaSparks", Attachment = "Top", Texture = "Ember", Color = { rgb(255, 220, 100), rgb(255, 80, 20) }, Rate = 10, Size = { 0.35, 0.1 },
			Lifetime = { 1, 1.8 }, Speed = { 10, 16 }, Spread = 25, LightEmission = 1, Acceleration = Vector3.new(0, -20, 0) },
		{ Name = "HeatHaze", Attachment = "Top", Texture = "SoftGlow", Color = { rgb(255, 220, 190), rgb(255, 180, 140) }, Rate = 4, Size = { 2, 4 },
			Lifetime = { 1, 1.6 }, Speed = { 1, 2 }, Spread = 30, Transparency = { 0.85, 1 } },
		{ Name = "GlowingSmoke", Attachment = "Top", Texture = "SmokePuff", Color = { rgb(255, 120, 50), rgb(70, 50, 50) }, Rate = 3, Size = { 1.5, 4 },
			Lifetime = { 2, 3 }, Speed = { 2, 3 }, Spread = 20, LightEmission = 0.4, Transparency = { 0.4, 1 } },
	},
	SunMirrorTower = { -- Celestial Observatory: twinkling stars, a slow aurora ribbon, orbiting glowing mini planets
		{ Name = "Twinkles", Attachment = "Top", Texture = "Star", Color = { WHITE, rgb(255, 240, 180) }, Rate = 6, Size = { 0.4, 0 },
			Lifetime = { 1.5, 2.5 }, Speed = { 0.5, 1 }, Spread = 180, LightEmission = 1, Orbit = true, R = 6 },
		{ Name = "AuroraRibbon", Attachment = "Top", Texture = "SoftGlow", Color = { rgb(92, 255, 176), rgb(180, 140, 255) }, Rate = 8, Size = { 1.5, 0.8 },
			Lifetime = { 3, 4 }, Speed = { 0.4, 0.6 }, Spread = 0, LightEmission = 1, Transparency = { 0.5, 1 }, Orbit = true, R = 5 },
		{ Name = "MiniPlanets", Attachment = "Top", Texture = "SoftGlow", Color = { rgb(255, 200, 120), rgb(140, 200, 255) }, Rate = 1, Size = { 0.9, 0.9 },
			Lifetime = { 5, 6 }, Speed = { 0, 0 }, Spread = 0, LightEmission = 1, Orbit = true, R = 4 },
	},
}

-- A Masterwork: a golden sparkle aura and floating gold motes, and gold sparks in every hit.
EffectsConfig.Masterwork = {
	Ambient = {
		{ Name = "GoldAura", Attachment = "Aura", Texture = "Sparkle", Color = { GOLD, WHITE }, Rate = 8, Size = { 0.4, 0 }, Lifetime = { 1.2, 2 },
			Speed = { 0.5, 1.5 }, Spread = 30, LightEmission = 1, Orbit = true, R = 4 },
		{ Name = "GoldMotes", Attachment = "Top", Texture = "SoftGlow", Color = { GOLD, rgb(255, 240, 160) }, Rate = 3, Size = { 0.35, 0.1 },
			Lifetime = { 2.5, 3.5 }, Speed = { 0.3, 0.8 }, Spread = 180, LightEmission = 1 },
	},
	Hit = {
		{ Name = "GoldSparks", Attachment = "Hit", Texture = "Sparkle", Color = { GOLD, rgb(255, 170, 40) }, Burst = 5, Size = { 0.35, 0.05 },
			Lifetime = { 0.3, 0.6 }, Speed = { 8, 14 }, Spread = 70, LightEmission = 1, Acceleration = Vector3.new(0, -20, 0) },
	},
}

-- What runs on one building's station: its tier's layers, the Legendary signature at tier 5, and the
-- Masterwork's gold at detail 10. Lights are capped at Rules.MaxLightsPerBuilding.
function EffectsConfig.For(buildingId: string, tier: number, masterwork: boolean?)
	local colour = EffectsConfig.BuildingColours[buildingId] or WHITE
	local ambient, hit, lights, beams = tierLayers(tier, colour)
	if tier >= 5 then
		for _, emitter in EffectsConfig.Signatures[buildingId] or {} do
			table.insert(ambient, emitter)
		end
	end
	if masterwork then
		for _, emitter in EffectsConfig.Masterwork.Ambient do
			table.insert(ambient, emitter)
		end
		for _, emitter in EffectsConfig.Masterwork.Hit do
			table.insert(hit, emitter)
		end
	end
	while #lights > EffectsConfig.Rules.MaxLightsPerBuilding do
		table.remove(lights)
	end
	return { Ambient = ambient, Hit = hit, Lights = lights, Beams = beams }
end

-- The texture to use for a key: its uploaded id, or the placeholder.
function EffectsConfig.Texture(key: string): string
	return EffectsConfig.Textures[key] or EffectsConfig.Placeholder
end

return EffectsConfig
