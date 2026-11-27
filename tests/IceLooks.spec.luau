-- IceLooks spec: the redesigned ice block's options, uploaded ids and settings (IceBlockLook draws them).
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end

	local IceLooks = assert(loadstring(sources.IceLooks))()

	-- Every option has its uploaded model, and the textures it uses are uploaded
	check(#IceLooks.Options == 3, "three look options to choose from")
	for _, option in IceLooks.Options do
		local id = IceLooks.OptionModelIds[option]
		check(type(id) == "number" and id > 0, "option " .. option .. " has an uploaded model")
	end
	for _, key in { "Atlas", "Glow", "Shimmer" } do
		local id = IceLooks.Textures[key]
		check(type(id) == "string" and string.match(id, "^rbxassetid://%d+$") ~= nil, key .. " texture is uploaded")
	end
	check(IceLooks.TemplateHeight == 14, "the templates are built at the level-1 height")

	-- The shell: just above transparent (Roblox only honours a texture's alpha then), and still frosted at the
	-- last crack stage
	local new = IceLooks.New
	check(new.ShellTransparency > 0 and new.ShellTransparency < 0.1, "the shell runs just above transparent")
	check(new.ThinPerStage > 0 and new.ShellTransparency + 4 * new.ThinPerStage < 0.5, "the frost thins with each crack stage but never vanishes")
	check(new.CreatureCentre > 0.2 and new.CreatureCentre < 0.6 and new.CreatureLift >= 0 and new.CreatureLift < 0.2, "the creature stands low in the block")

	-- The glow: soft and behind the creature, never a solid white wash
	check(new.Glow.Size > 0.5 and new.Glow.Size <= 1.3, "the glow is about the block's height across")
	check(new.Glow.Behind > 0 and new.Glow.Behind < 0.4, "the glow sits behind the creature, inside the block")
	check(new.Glow.Transparency > 0 and new.Glow.Transparency < 0.8, "the glow shows, but never fully opaque")
	check(new.Glow.Brightness > 0 and new.Glow.Brightness <= 3, "the glow's brightness stays modest (no milky wash)")
	check(new.Glow.Whiten >= 0 and new.Glow.Whiten < 0.5, "the glow keeps the rarity colour")
	check(IceLooks.Glow.Common == nil, "Common has no glow")

	-- Particles and the shimmer: few and slow
	for name, range in { MoteLife = new.Motes.Lifetime, MoteSpeed = new.Motes.Speed, MistSize = new.Mist.Size, MistLife = new.Mist.Lifetime, MistSpeed = new.Mist.Speed } do
		check(range[1] > 0 and range[1] <= range[2], name .. " is a range, low to high")
	end
	check(new.Motes.Rate > 0 and new.Motes.Rate <= 5, "a few drifting motes")
	check(new.Mist.Rate > 0 and new.Mist.Rate <= 5, "a little mist")
	check(new.Shimmer.Period >= 3 and new.Shimmer.TileHeights >= 2, "the shimmer sweeps slowly, now and then")
	for option in new.ShellTint do
		check(table.find(IceLooks.Options, option) ~= nil, "a shell tint belongs to an option (" .. option .. ")")
	end

	return passed
end
