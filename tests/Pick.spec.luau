-- Spec for the ice pick a player carries (src/server/PickService.luau): the real PickService against a fake
-- save, fake players, characters and pick templates. Nothing real is touched.
-- Run: python tools/run_specs.py Pick
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, "FAILED: " .. message)
		passed += 1
	end

	-- Fake instances: just what PickService uses (names, parents, attributes, Clone, Destroy).
	local all = {}
	local function node(name: string, class: string, parent)
		local n = { Name = name, ClassName = class, Parent = parent, attributes = {} }
		function n:FindFirstChild(child)
			for _, other in all do
				if other.Parent == self and other.Name == child then
					return other
				end
			end
			return nil
		end
		function n:FindFirstChildOfClass(className)
			for _, other in all do
				if other.Parent == self and other.ClassName == className then
					return other
				end
			end
			return nil
		end
		function n:GetAttribute(key)
			return self.attributes[key]
		end
		function n:SetAttribute(key, value)
			self.attributes[key] = value
		end
		function n:Clone()
			local copy = node(self.Name, self.ClassName, nil)
			for key, value in self.attributes do
				copy.attributes[key] = value
			end
			copy.source = self
			return copy
		end
		function n:Destroy()
			self.Parent = nil
			self.destroyed = true
		end
		function n:GetDescendants()
			local found = {}
			for _, other in all do
				local up = other.Parent
				while up do
					if up == self then
						table.insert(found, other)
						break
					end
					up = up.Parent
				end
			end
			return found
		end
		function n:IsA(className)
			return self.ClassName == className
		end
		table.insert(all, n)
		return n
	end

	local serverStorage = node("ServerStorage", "ServerStorage")
	local templates = node("PickTemplates", "Folder", serverStorage)
	local picks = {}
	for tier = 1, 6 do
		picks[tier] = node("Pick" .. tier, "Tool", templates)
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
	for _, name in { "BuildingConfig", "CreatureConfig", "LayerConfig", "RebirthConfig", "UpgradeConfig", "GameConfig", "NumberFormat", "EconomyRules" } do
		loadPure(name)
	end
	local UpgradeConfig = modules.UpgradeConfig

	local dataOf, published, important = {}, 0, 0
	modules.PlayerData = {
		Edit = function(player)
			return dataOf[player]
		end,
		Publish = function()
			published += 1
		end,
		MarkImportant = function()
			important += 1
		end,
	}
	local playerList = {}
	local warnings = {}
	local chunk = assert(loadstring(sources.PickService, "PickService"))
	setfenv(chunk, setmetatable({
		game = { GetService = function(_, service)
			if service == "ServerStorage" then
				return serverStorage
			elseif service == "Players" then
				return { GetPlayers = function()
					return playerList
				end }
			end
			return modules
		end },
		script = { Parent = modules },
		require = function(module)
			return module
		end,
		warn = function(message)
			table.insert(warnings, message)
		end,
	}, { __index = getfenv(1) }))
	local PickService = chunk()

	-- A player with a character, a humanoid and a backpack.
	local function newPlayer(name)
		local player = node(name, "Player")
		node("Backpack", "Backpack", player)
		local character = node(name, "Model")
		player.Character = character
		local humanoid = node("Humanoid", "Humanoid", character)
		humanoid.Health = 100
		function humanoid:EquipTool(tool)
			tool.Parent = character
		end
		table.insert(playerList, player)
		return player, character, humanoid
	end
	local function heldTier(character)
		local tool = character:FindFirstChild("IcePick")
		return tool and tool:GetAttribute("Tier")
	end

	-- The templates' ids come from the uploads.
	for _, pick in UpgradeConfig.IcePick do
		check(type(pick.ModelId) == "number" and pick.ModelId > 0, pick.Name .. " has an uploaded model id")
	end
	check(typeof(UpgradeConfig.PickGrip) == "CFrame", "the hand's grip on the pick is configured")

	local player, character, humanoid = newPlayer("Picker")
	PickService.Refresh(player)
	check(character:FindFirstChild("IcePick") == nil, "data not ready: no pick yet")

	dataOf[player] = { Upgrades = {} }
	PickService.Refresh(player)
	local tool = character:FindFirstChild("IcePick")
	check(tool ~= nil and tool.source == picks[1] and heldTier(character) == 1, "a new player holds the wooden pick (Pick1), named IcePick")
	check(tool ~= nil and tool.Grip == UpgradeConfig.PickGrip, "the pick is held with the config's grip (head along the swing)")

	PickService.Refresh(player)
	check(character:FindFirstChild("IcePick") == tool, "refreshing again keeps the same tool (no flicker)")

	tool.Parent = player:FindFirstChildOfClass("Backpack")
	PickService.Refresh(player)
	check(tool.Parent == character, "a pick put away in the backpack is put back in hand")

	table.insert(dataOf[player].Upgrades, "IcePick2")
	table.insert(dataOf[player].Upgrades, "IcePick3")
	PickService.Refresh(player)
	check(heldTier(character) == 3 and tool.destroyed, "buying picks: the old one goes, the new tier is in hand")

	humanoid.Health = 0
	table.insert(dataOf[player].Upgrades, "IcePick4")
	PickService.Refresh(player)
	check(heldTier(character) == 3, "a dead character gets nothing new (the next one does)")
	humanoid.Health = 100

	-- The debug action's SetTier.
	dataOf[player].Upgrades = { "FrostTouch1", "IcePick2", "IcePick3", "IcePick4" }
	local before = published
	check(PickService.SetTier(player, 6), "SetTier 6")
	local owned = {}
	for _, id in dataOf[player].Upgrades do
		owned[id] = true
	end
	check(owned.FrostTouch1 and owned.IcePick2 and owned.IcePick5 and owned.IcePick6 and #dataOf[player].Upgrades == 6, "SetTier: other upgrades stay, picks 2 to 6 owned")
	check(heldTier(character) == 6 and published > before and important > 0, "...the cosmic pick is in hand at once, and the save is published and marked")
	check(PickService.SetTier(player, 1) and #dataOf[player].Upgrades == 1 and owned.FrostTouch1 and heldTier(character) == 1, "SetTier 1: back to the wooden pick")
	check(not PickService.SetTier(player, 0) and not PickService.SetTier(player, 7) and not PickService.SetTier(player, 2.5) and not PickService.SetTier(player, "3"), "SetTier refuses tiers that don't exist")
	-- The Creature Book's Golden page (all 18 Golden) gives the golden pick skin.
	local golden = {}
	for _, creature in modules.CreatureConfig.Creatures do
		golden[creature.Id] = true
	end
	dataOf[player].BookSeen, dataOf[player].BookGolden = {}, golden
	PickService.Refresh(player)
	check(character:FindFirstChild("IcePick"):GetAttribute("Skin") == "Golden" and heldTier(character) == 1, "a full Golden page: the same tier's pick in the golden skin")
	dataOf[player].BookGolden = {}
	PickService.Refresh(player)
	check(character:FindFirstChild("IcePick"):GetAttribute("Skin") == "", "...and without it, the normal pick")
	local stranger = newPlayer("NoData")
	check(not PickService.SetTier(stranger, 3), "SetTier refuses a player whose data isn't ready")

	-- A missing template: a warning once, nothing in hand, no error.
	picks[2].Parent = nil
	local other, otherCharacter = newPlayer("Other")
	dataOf[other] = { Upgrades = { "IcePick2" } }
	PickService.Refresh(other)
	PickService.Refresh(other)
	check(otherCharacter:FindFirstChild("IcePick") == nil and #warnings == 1, "no template for a tier: one warning, no pick, no error")

	return passed
end
