-- IceLooks spec: the ice block's look (IceBlockLook draws it): the kit and textures, every layer and rarity, the
-- creature, the auras and the effect rules they follow.
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end

	local IceLooks = assert(loadstring(sources.IceLooks))()
	local LayerConfig = assert(loadstring(sources.LayerConfig))()
	local CreatureConfig = assert(loadstring(sources.CreatureConfig))()

	-- The kit and every texture it uses are uploaded
	check(type(IceLooks.KitModelId) == "number" and IceLooks.KitModelId > 0, "the ice block kit is uploaded")
	local function uploaded(id)
		return type(id) == "string" and string.match(id, "^rbxassetid://%d+$") ~= nil
	end
	for _, key in { "Glow", "Shimmer", "Halo", "Ray", "Flame" } do
		check(uploaded(IceLooks.Textures[key]), key .. " texture is uploaded")
	end
	check(IceLooks.TemplateHeight == LayerConfig.Block.HeightAtFirstLevel, "the kit is built at the level-1 height")
	check(IceLooks.Variants >= 2 and IceLooks.Variants <= 3, "two or three shape variants")

	-- A look for every layer, with its own uploaded atlas
	check(#IceLooks.LayerLooks == #LayerConfig.Layers, "one look per layer")
	for number, layer in LayerConfig.Layers do
		local look = IceLooks.LayerLooks[number]
		check(look.Atlas == layer.Id and uploaded(IceLooks.Textures[look.Atlas]), layer.Name .. " has its own uploaded atlas")
		check(look.GlowEmission >= 0 and look.GlowEmission <= 1 and look.GlowBrightness > 0 and look.GlowBrightness <= 2.5,
			layer.Name .. ": the creature's glow stays modest (no milky wash)")
		check(look.Extra == nil or look.Extra == "Drifts" or look.Extra == "CrystalClusters" or look.Extra == "Veins", layer.Name .. ": a known extra")
		if look.Extra == "Veins" then
			check(typeof(look.VeinColor) == "Color3", layer.Name .. ": its veins have a colour")
		end
	end
	check(IceLooks.LayerLooks[1].GlowEmission <= 0.2, "on white snow the glow is a colour, not added light (it went milky)")
	check(IceLooks.LayerLooks[1].NoCrystals == true, "Fresh Snow is snow: no icicles or crystals")
	check(IceLooks.LayerLooks[3].DenseBubbles == true, "Ancient Ice is full of trapped bubbles")
	check(IceLooks.LayerLooks[6].InnerLight ~= nil, "the Frozen Core is lit from inside")

	-- Every rarity: Common has no glow, the glow grows with the rarity; Legendary is amber, not yellow
	local last = -1
	for _, name in { "Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic" } do
		local info = IceLooks.Rarities[name]
		check(info ~= nil and typeof(info.Colour) == "Color3", name .. " has a look")
		check(info.Glow >= last and info.Glow <= 1, name .. ": the glow grows with the rarity")
		last = info.Glow
		check(CreatureConfig.GetRarity(name) ~= nil, name .. " is a real rarity")
	end
	check(IceLooks.Rarities.Common.Glow == 0, "Common has no glow")
	local amber = IceLooks.Rarities.Legendary.Colour
	check(amber.R > 0.9 and amber.G < 0.65 and amber.B < 0.3, "Legendary is amber (gold reads green through blue ice)")
	check(IceLooks.Rarities.Mythic.Rainbow == true and not IceLooks.Rarities.Legendary.Rainbow, "Mythic cycles the rainbow")
	check(IceLooks.Rarities.Epic.Motes and not IceLooks.Rarities.Rare.Motes, "motes from Epic up")

	-- The creature: a solid outline, eyes that blink, a little colour at the last two crack stages, never all of it
	local creature = IceLooks.Creature
	check(creature.Outline >= 0 and creature.Outline < 0.3, "the outline is clearly visible")
	check(creature.Blink.Every[1] >= 2 and creature.Blink.Every[2] >= creature.Blink.Every[1] and creature.Blink.Seconds < 0.4, "the eyes blink now and then, briefly")
	check(creature.Reveal[1] == nil and creature.Reveal[2] == nil, "no colours show before crack stage 3")
	check(creature.Reveal[3] > 0 and creature.Reveal[4] > creature.Reveal[3] and creature.Reveal[4] < 0.6, "a little colour at stages 3 and 4, the rest a surprise")

	-- The auras: only Epic and up, growing with the rarity; ring and rays never opaque
	local auras = IceLooks.Auras
	check(auras.Common == nil and auras.Uncommon == nil and auras.Rare == nil, "no aura below Epic")
	check(auras.Epic.Wisps and auras.Legendary.Flames and auras.Legendary.Embers and auras.Legendary.Rays and auras.Legendary.Pulse, "Epic wisps; Legendary flames, embers, rays and a pulse")
	check(auras.Mythic.Sparkles and auras.Mythic.PulseEvery > 1, "Mythic: spiralling sparkles and a bright pulse every few seconds")
	check(auras.Epic.Halo < auras.Legendary.Halo and auras.Legendary.Halo < auras.Mythic.Halo, "the ring grows with the rarity")
	for name, aura in { Epic = auras.Epic, Legendary = auras.Legendary, Mythic = auras.Mythic } do
		check(aura.HaloTransparency >= 0.2 and aura.HaloTransparency < 1, name .. ": the ring shows but never covers")
		check(auras.Burst[name] and auras.Burst[name] > 0, name .. ": a bigger burst on the shatter")
	end
	local legendaryRays = auras.Legendary.Rays
	check(legendaryRays.Transparency >= 0.2 and legendaryRays.Count <= 8, "a few soft light rays")
	check(auras.HaloEmission <= 0.5, "the ring is mostly colour (added light vanishes on snow and sky)")
	check(auras.HaloFadeBottom > 0 and auras.HaloFadeBottom < 0.5, "the ring fades towards the ground (the stage stays clean)")
	check(auras.FadeSeconds > 0 and auras.FadeSeconds < 1, "an aura fades quickly when the block shatters")
	check(auras.ParticleBox > 1, "flames and wisps come off outside the ice")

	-- The block: just above transparent, frost thinning, a small tap squash, the shatter's pieces
	local new = IceLooks.New
	check(new.ShellTransparency > 0 and new.ShellTransparency < 0.1, "the shell runs just above transparent (the atlas's alpha counts)")
	check(new.ThinPerStage > 0 and new.ShellTransparency + 4 * new.ThinPerStage < 0.5, "the frost thins with each crack stage but never vanishes")
	check(new.TapSquash.Amount > 0 and new.TapSquash.Amount <= 0.05 and new.TapSquash.Seconds < 0.3, "a tap squashes the block about 3%, quickly")
	check(new.Chunks.PerStage[1] >= 1 and new.Chunks.PerStage[2] <= 2, "one or two chunks break off at each crack stage")
	check(new.Pieces.Life > new.Pieces.FadeFrom, "the shatter's pieces fade out before they go")
	check(new.Glow.Size > 0.5 and new.Glow.Size < 1, "the creature's glow is smaller than the block (it washed the whole block)")
	check(new.LightScale > 0 and new.LightScale < 1, "the block's light is dimmed under the new look")
	for name, range in { MoteLife = new.Motes.Lifetime, MoteSpeed = new.Motes.Speed, MistSize = new.Mist.Size, MistLife = new.Mist.Lifetime, MistSpeed = new.Mist.Speed } do
		check(range[1] > 0 and range[1] <= range[2], name .. " is a range, low to high")
	end
	check(new.Shimmer.Period >= 3 and new.Shimmer.TileHeights >= 2, "the shimmer sweeps slowly, now and then")

	-- The tools: a spark colour per tier, and the magical tiers (11-18) each with a light and a themed hit effect
	check(#IceLooks.ToolSparks == 18, "a spark colour for each of the 18 tools")
	local textures = { SoftGlow = true, Sparkle = true, Snowflake = true, Ember = true, SmokePuff = true, Star = true, WaterDroplet = true }
	local kinds = {}
	for tier = 1, 18 do
		local magic = IceLooks.ToolMagic[tier]
		check((magic ~= nil) == (tier >= 11), "tool " .. tier .. (if tier >= 11 then " is magical" else " is a real material"))
		if magic then
			local hit = IceLooks.MagicHits[magic.Hit]
			check(hit ~= nil and textures[hit.Texture], "tool " .. tier .. "'s hit effect " .. tostring(magic.Hit) .. " exists, with a known texture")
			check(magic.Light[1] > 0 and magic.Light[2] > 0 and magic.Light[2] <= 2, "tool " .. tier .. " has a soft light")
			check(hit.Count >= 6 and hit.Speed[1] <= hit.Speed[2] and hit.Life[1] <= hit.Life[2] and hit.Light <= 0.6,
				magic.Hit .. ": a burst with sane ranges, its added light kept low (it vanishes against snow)")
			check(not kinds[magic.Hit], magic.Hit .. " belongs to one tool only")
			kinds[magic.Hit] = true
		end
	end
	check(IceLooks.MagicHits.Starburst.Count >= 20 and IceLooks.ToolMagic[18].Hit == "Starburst", "the Starbreaker gets the big starburst")

	return passed
end
