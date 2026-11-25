-- Pets spec: PetRules (slots, Equip Best, Golden combine), the Creature Book pages (EconomyRules), the
-- ice looks, and PetService's requests against a fake save. Run: python tools/run_specs.py Pets
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end

	local modules = {}
	local function loadPure(name)
		local chunk = assert(loadstring(sources[name], name))
		setfenv(chunk, setmetatable({
			game = { GetService = function()
				return modules
			end },
			script = { Parent = modules },
			require = function(module)
				return module
			end,
		}, { __index = getfenv(1) }))
		modules[name] = chunk()
		return modules[name]
	end
	for _, name in { "BuildingConfig", "CreatureConfig", "LayerConfig", "RebirthConfig", "UpgradeConfig", "MonetizationConfig", "EconomyRules", "PetRules", "IceLooks" } do
		loadPure(name)
	end
	local PetRules, R, CreatureConfig, IceLooks = modules.PetRules, modules.EconomyRules, modules.CreatureConfig, modules.IceLooks

	-- Slots: 1, +1 at rebirth 3, 6 and 10, plus passes, at most 7
	check(PetRules.Slots(0, 0) == 1, "one slot at the start")
	check(PetRules.Slots(2, 0) == 1 and PetRules.Slots(3, 0) == 2, "the 2nd slot at rebirth 3")
	check(PetRules.Slots(6, 0) == 3 and PetRules.Slots(10, 0) == 4, "the 3rd at rebirth 6, the 4th at rebirth 10")
	check(PetRules.Slots(0, 3) == 4 and PetRules.Slots(10, 3) == 7, "both passes add 3; the maximum is 7")
	check(PetRules.Slots(50, 9) == CreatureConfig.Pets.MaxEquipSlots, "never more than the maximum")

	local function pet(uid, id, golden)
		return { Uid = uid, CreatureId = id, Golden = golden == true }
	end
	local pets = { pet("a", "SnowBunny"), pet("b", "MiniYeti"), pet("c", "SealPup"), pet("d", "SnowBunny", true), pet("e", "AuroraFox") }
	local best = PetRules.Best(pets, 3)
	check(#best == 3 and best[1] == "e" and best[2] == "b" and best[3] == "c", "Equip Best: the three biggest bonuses (Mythic, Epic, Uncommon)")
	check(PetRules.Sorted(pets)[5].Uid == "a", "the inventory sorts best first")

	-- Golden combine: 5 of the same creature, not Golden; unequipped copies first
	local five = { pet("1", "SealPup"), pet("2", "SealPup"), pet("3", "SealPup"), pet("4", "SealPup"), pet("5", "SealPup"), pet("6", "SealPup"), pet("g", "SealPup", true) }
	local group = PetRules.CombineGroup(five, "1", { "2" })
	check(group and #group == 5 and group[1] == "1", "five Seal Pups combine")
	check(group and not table.find(group, "2") and not table.find(group, "g"), "...leaving the equipped one and never using a Golden")
	check(PetRules.CombineGroup(five, "g", {}) == nil, "a Golden pet can't be combined again")
	check(PetRules.CombineGroup({ pet("1", "SealPup"), pet("2", "SealPup") }, "1", {}) == nil, "two copies aren't enough")
	local withLocked = table.clone(five)
	withLocked[3] = { Uid = "3", CreatureId = "SealPup", Golden = false, Locked = true }
	local lockedGroup = PetRules.CombineGroup(withLocked, "1", {})
	check(lockedGroup and not table.find(lockedGroup, "3"), "a combine never uses a locked copy")
	check(PetRules.CombineGroup(withLocked, "3", {}) == nil, "...and a locked pet can't be combined")

	-- Delete all below a rarity: skips locked, equipped and Golden pets
	local mixed = {
		pet("c1", "SnowBunny"), pet("c2", "SnowBunny"), { Uid = "c3", CreatureId = "SnowBunny", Golden = false, Locked = true },
		pet("c4", "SnowBunny", true), pet("c5", "SnowBunny"), pet("u1", "SealPup"), pet("e1", "MiniYeti"), pet("m1", "AuroraFox"),
	}
	local belowUncommon = PetRules.BelowRarity(mixed, "Uncommon", { "c5" })
	check(#belowUncommon == 2 and table.find(belowUncommon, "c1") and table.find(belowUncommon, "c2"),
		"below Uncommon: the Commons, but not the locked, Golden or equipped one")
	local belowMythic = PetRules.BelowRarity(mixed, "Mythic", {})
	check(#belowMythic == 5 and not table.find(belowMythic, "m1") and not table.find(belowMythic, "c3") and not table.find(belowMythic, "c4"),
		"below Mythic: everything else that isn't locked or Golden")
	check(#PetRules.BelowRarity(mixed, "Common", {}) == 0 and #PetRules.BelowRarity(mixed, "Nonsense", {}) == 0, "nothing is below Common, or an unknown rarity")
	check(PetRules.SameSet({ "a", "b" }, { "b", "a" }) and not PetRules.SameSet({ "a" }, { "a", "b" }) and not PetRules.SameSet({ "a", "c" }, { "a", "b" }),
		"SameSet compares uid lists as sets")

	-- Creature Book pages and rewards
	local data = { Pets = {}, Equipped = {}, BookSeen = {}, BookGolden = {}, Upgrades = {}, Buildings = {}, FrostCores = 0 }
	local pages = R.BookPages(data)
	check(#pages == 7 and pages[7].Page == "Golden" and pages[7].Count == 18, "seven pages: six rarities and Golden (all 18)")
	for _, creature in CreatureConfig.Creatures do
		if creature.Rarity == "Rare" then
			data.BookSeen[creature.Id] = 1
		end
	end
	check(math.abs(R.BookBonus(data) - 0.10) < 1e-9, "a complete Rare page gives +10%")
	for _, creature in CreatureConfig.Creatures do
		data.BookGolden[creature.Id] = true
	end
	check(R.BookPages(data)[7].Complete, "every Golden version completes the Golden page")
	check(R.BookPages(data)[7].Reward.Title == "Ice Keeper", "...whose reward is the Ice Keeper title")

	-- Ice looks: every layer and every glowing rarity has a look
	for layer = 1, #modules.LayerConfig.Layers do
		local look = IceLooks.Layers[layer]
		check(look and look.Color and look.Material and look.Clear >= look.Transparency - 0.2, `layer {layer} has an ice look`)
	end
	for _, rarity in CreatureConfig.Rarities do
		check((rarity.Glow == "None") == (IceLooks.Glow[rarity.Id] == nil), `{rarity.Id}: a glow exactly when the doc gives one`)
		check(IceLooks.RarityColors[rarity.Id] ~= nil, `{rarity.Id} has a banner colour`)
	end
	check(IceLooks.Glow.Legendary.Mode == "Pulse" and IceLooks.Glow.Mythic.Mode == "Rainbow", "Legendary pulses, Mythic shifts through the rainbow")
	check(IceLooks.SilhouetteShare == 0.6, "the creature inside is 60% of the block's height")

	-- PetService against a fake save ------------------------------------------------------------------
	local save = {
		Pets = { pet("p1", "SnowBunny"), pet("p2", "SnowBunny"), pet("p3", "SnowBunny"), pet("p4", "SnowBunny"), pet("p5", "SnowBunny"), pet("p6", "MiniYeti") },
		Equipped = { "p1" }, BookSeen = { SnowBunny = 5, MiniYeti = 1 }, BookGolden = {}, BookNew = { "MiniYeti" },
		Rebirths = 0, CreaturesRescued = 6, TutorialStep = 5, Settings = { AutoEquip = false },
	}
	local attributes = {}
	local owned = {}
	local notices = {}
	local fakePlayer = { Name = "Tester", UserId = 7, Parent = true, SetAttribute = function(_, k, v)
		attributes[k] = v
	end }
	modules.GameEvent = { FireClient = function(_, _, kind, payload)
		table.insert(notices, { kind, payload })
	end }
	local server = {
		GamePasses = { Owns = function(_, key)
			return owned[key] == true
		end, OnChanged = function() end },
		PlayerData = { Edit = function()
			return save
		end, Publish = function() end, MarkImportant = function() end, OnLoaded = function() end },
	}
	local clock = 0
	local guid = 0
	local chunk = assert(loadstring(sources.PetService, "PetService"))
	setfenv(chunk, setmetatable({
		game = { GetService = function(_, name)
			if name == "ReplicatedStorage" then
				return modules
			elseif name == "HttpService" then
				return {
					GenerateGUID = function()
						guid += 1
						return "guid-" .. guid
					end,
					JSONEncode = function(_, value)
						return game:GetService("HttpService"):JSONEncode(value)
					end,
				}
			end
			return { PlayerRemoving = { Connect = function() end } }
		end },
		script = { Parent = server },
		require = function(module)
			return module
		end,
		os = { clock = function()
			clock += 1
			return clock
		end },
		task = { spawn = function() end, delay = function(_, fn)
			fn()
		end },
	}, { __index = getfenv(1) }))
	local PetService = chunk()
	local function ask(action, argument)
		return PetService.Handle(fakePlayer, action, argument)
	end
	check(not ask("Equip", "p6").ok, "one slot: a second pet can't be equipped")
	owned.PetSquad = true
	check(PetService.Slots(fakePlayer, save) == 3, "Pet Squad adds two slots")
	check(ask("Equip", "p6").ok and #save.Equipped == 2, "...so now it can")
	check(not ask("Equip", "nope").ok, "an unknown pet can't be equipped")
	check(not ask("Explode", "p1").ok, "an unknown request is refused")
	local reply = ask("CombineGolden", "p2")
	check(reply.ok and #save.Pets == 2 and save.BookGolden.SnowBunny == true, "five Snow Bunnies become one Golden (the Golden page counts it)")
	local goldenUid = reply.uid
	check(table.find(save.Equipped, goldenUid) ~= nil, "the Golden one takes the equipped bunny's slot")
	check(ask("EquipBest").ok and save.Equipped[1] == goldenUid or save.Equipped[1] == "p6", "Equip Best")
	-- abusive lists (a repeated uid used to delete an unpicked pet and leave a broken save)
	local petsBefore, equippedBefore = #save.Pets, #save.Equipped
	check(not ask("Delete", { "p6", "p6" }).ok and #save.Pets == petsBefore and #save.Equipped == equippedBefore, "a repeated uid in Delete is refused, nothing deleted")
	check(not ask("Delete", { "p6", extra = "p6" }).ok and #save.Pets == petsBefore, "a list with extra keys is refused")
	check(not ask("Delete", "p6").ok and not ask("Delete", {}).ok and not ask("Delete", { 5 }).ok, "Delete needs a list of uid strings")
	check(not ask("MarkSeen", { a = "MiniYeti" }).ok, "MarkSeen needs a plain list")
		check(ask("Delete", { "p6" }).ok and #save.Pets == 1 and not table.find(save.Equipped, "p6"), "deleting an equipped pet unequips it")
	check(not ask("Delete", { "p6" }).ok, "a deleted pet can't be deleted again")
	check(ask("MarkSeen", { "MiniYeti" }).ok and #save.BookNew == 0, "viewing the book clears the New! badge")
	owned.PetSquad = false
	PetService.Publish(fakePlayer, save)
	check(#save.Equipped <= 1 and attributes.PetSlots == 1, "losing a slot pass unequips the extras")
	local first = PetService.Rescue(fakePlayer, save, "SpiritWhale")
	check(first and save.BookSeen.SpiritWhale == 1 and table.find(save.BookNew, "SpiritWhale") and save.CreaturesRescued == 7, "a rescue: the pet, the book count, a New! badge, the rescue count")
	for i = 1, CreatureConfig.Pets.InventorySize do
		table.insert(save.Pets, pet("fill" .. i, "SealPup"))
	end
	check(PetService.Rescue(fakePlayer, save, "SealPup") == nil and save.BookSeen.SealPup == 1, "a full inventory still fills the book, but no pet joins")

	-- Lock, Delete below, auto-equip
	table.clear(save.Pets)
	table.clear(save.Equipped)
	for _, entry in { { "k1", "SnowBunny" }, { "k2", "SnowBunny" }, { "k3", "SealPup" }, { "k4", "MiniYeti" } } do
		table.insert(save.Pets, pet(entry[1], entry[2]))
	end
	table.insert(save.Equipped, "k3")
	check(ask("Lock", "k1").ok and save.Pets[1].Locked == true, "a pet can be locked")
	check(not ask("Delete", { "k1" }).ok and #save.Pets == 4, "a locked pet can't be deleted")
	check(not ask("Lock", "nope").ok and not ask("Lock", { "k1" }).ok, "Lock needs one of your pets")
	check(not ask("DeleteBelow", "Common").ok and not ask("DeleteBelow", "Nonsense").ok and not ask("DeleteBelow", 3).ok,
		"Delete below needs a real rarity above Common")
	check(ask("DeleteBelow", "Epic").ok and #save.Pets == 3 and save.Pets[1].Uid == "k1",
		"Delete below Epic: the unlocked Common goes; the locked one, the equipped Uncommon and the Epic stay")
	check(not ask("DeleteBelow", "Uncommon").ok and #save.Pets == 3, "...and a second time there's nothing left to delete")
	check(ask("Lock", "k1").ok and save.Pets[1].Locked == nil, "unlocking clears the lock")
	-- auto-equip: off here (Settings.AutoEquip = false), so a better pet waits
	local whale = PetService.Rescue(fakePlayer, save, "SpiritWhale")
	check(whale and not table.find(save.Equipped, whale.Uid), "auto-equip off: a new Mythic isn't equipped")
	save.Settings.AutoEquip = true
	save.TutorialStep = 4
	local fox = PetService.Rescue(fakePlayer, save, "AuroraFox")
	check(fox and not table.find(save.Equipped, fox.Uid), "auto-equip waits for the tutorial (its Equip step teaches it)")
	save.TutorialStep = 5
	table.clear(notices)
	local bunny = PetService.Rescue(fakePlayer, save, "SnowBunny")
	check(bunny and #save.Equipped == 1 and (save.Equipped[1] == whale.Uid or save.Equipped[1] == fox.Uid),
		"auto-equip on: the best pet is equipped after a rescue (a Mythic, not the new Common)")
	check(#notices == 0, "...with no notice when the new pet isn't the one equipped")
	table.remove(save.Pets, #save.Pets) -- (room for one more)
	owned.PetSquad = true
	local yeti = PetService.Rescue(fakePlayer, save, "MiniYeti")
	check(yeti and #save.Equipped == 3 and table.find(save.Equipped, whale.Uid) and table.find(save.Equipped, fox.Uid) and table.find(save.Equipped, yeti.Uid),
		"with three slots, the three best (two Mythics and the new Epic) are equipped")
	check(#notices == 1 and notices[1][1] == "Notice", "...and the player is told about the new one")

	return passed
end
