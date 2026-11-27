-- Spec for the tool a player carries (src/server/PickService.luau): the real PickService against a fake save, fake
-- players, characters and tool templates. Nothing real is touched.
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
	local templates = node("ToolTemplates", "Folder", serverStorage)
	local made = {}
	for _, tier in { 1, 2, 4, 7, 10 } do -- (some tiers have no template: they hold the nearest of their family)
		made[tier] = node("Tool" .. tier, "Tool", templates)
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
	for _, name in { "BuildingConfig", "CreatureConfig", "LayerConfig", "RebirthConfig", "UpgradeConfig", "GameConfig", "NumberFormat", "EconomyRules", "SwingConfig" } do
		loadPure(name)
	end
	local UpgradeConfig, SwingConfig = modules.UpgradeConfig, modules.SwingConfig

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
	local function heldTool(character)
		return character:FindFirstChild("IceTool")
	end
	local function heldTier(character)
		local tool = heldTool(character)
		return tool and tool:GetAttribute("Tier")
	end

	-- Every tool's model is uploaded or not made yet; every family has its grip.
	local models = 0
	for _, tool in UpgradeConfig.Tools do
		check(tool.ModelId == nil or (type(tool.ModelId) == "number" and tool.ModelId > 0), tool.Name .. ": an uploaded model id or none yet")
		models += if tool.ModelId then 1 else 0
		check(typeof(SwingConfig.Family(tool.Family).Grip) == "CFrame" and SwingConfig.Families[tool.Family] ~= nil, tool.Name .. ": its family has a grip")
	end
	check(models >= 5, "the five sample tools (Iron Pick, Gold Hammer, Crystal Axe, Ice Drill, Diamond Sword) are uploaded")

	local player, character, humanoid = newPlayer("Picker")
	PickService.Refresh(player)
	check(heldTool(character) == nil, "data not ready: no tool yet")

	dataOf[player] = { Upgrades = {} }
	PickService.Refresh(player)
	local tool = heldTool(character)
	check(tool ~= nil and tool.source == made[1] and heldTier(character) == 1, "a new player holds the Wooden Pick (Tool1), named IceTool")
	check(tool.Grip == SwingConfig.Families.Pick.Grip and tool:GetAttribute("Family") == "Pick" and tool.ToolTip == "Wooden Pick", "...with the pick family's grip, its family and its name")

	PickService.Refresh(player)
	check(heldTool(character) == tool, "refreshing again keeps the same tool (no flicker)")

	tool.Parent = player:FindFirstChildOfClass("Backpack")
	PickService.Refresh(player)
	check(tool.Parent == character, "a tool put away in the backpack is put back in hand")

	table.insert(dataOf[player].Upgrades, "Tool2")
	PickService.Refresh(player)
	check(heldTier(character) == 2 and tool.destroyed and heldTool(character).source == made[2], "buying a tool: the old one goes, the new one is in hand")
	check(heldTool(character).Grip == SwingConfig.Families.Hammer.Grip and heldTool(character):GetAttribute("Family") == "Hammer", "...held with its own family's grip")

	humanoid.Health = 0
	table.insert(dataOf[player].Upgrades, "Tool3")
	table.insert(dataOf[player].Upgrades, "Tool4")
	PickService.Refresh(player)
	check(heldTier(character) == 2, "a dead character gets nothing new (the next one does)")
	humanoid.Health = 100
	PickService.Refresh(player)
	check(heldTier(character) == 4 and heldTool(character).source == made[4], "...and the next one does")

	-- A tier without a template holds the nearest tool of its family, with one warning.
	dataOf[player].Upgrades = {}
	for tier = 2, 11 do
		table.insert(dataOf[player].Upgrades, "Tool" .. tier)
	end
	PickService.Refresh(player)
	PickService.Refresh(player)
	check(heldTier(character) == 11 and heldTool(character).source == made[4] and heldTool(character):GetAttribute("Family") == "Pick",
		"the Flame Pick (no template yet) holds the nearest pick, as tier 11")
	check(#warnings == 1 and string.find(warnings[1], "Tool11", 1, true), "...with one warning")

	-- The debug action's SetTier.
	dataOf[player].Upgrades = { "FrostTouch1", "Tool2", "Tool3", "Tool4" }
	local before = published
	check(PickService.SetTier(player, 18), "SetTier 18")
	local owned = {}
	for _, id in dataOf[player].Upgrades do
		owned[id] = true
	end
	check(owned.FrostTouch1 and owned.Tool2 and owned.Tool17 and owned.Tool18 and #dataOf[player].Upgrades == 18, "SetTier: other upgrades stay, tools 2 to 18 owned")
	check(heldTier(character) == 18 and heldTool(character).source == made[10] and published > before and important > 0,
		"...the Starbreaker (held as the nearest sword for now) is in hand at once, and the save is published and marked")
	check(PickService.SetTier(player, 1) and #dataOf[player].Upgrades == 1 and owned.FrostTouch1 and heldTier(character) == 1, "SetTier 1: back to the Wooden Pick")
	check(not PickService.SetTier(player, 0) and not PickService.SetTier(player, 19) and not PickService.SetTier(player, 2.5) and not PickService.SetTier(player, "3"), "SetTier refuses tiers that don't exist")
	-- The Creature Book's Golden page (all 18 Golden) gives the golden skin, on whatever tool is held.
	local golden = {}
	for _, creature in modules.CreatureConfig.Creatures do
		golden[creature.Id] = true
	end
	dataOf[player].BookSeen, dataOf[player].BookGolden = {}, golden
	PickService.Refresh(player)
	check(heldTool(character):GetAttribute("Skin") == "Golden" and heldTier(character) == 1, "a full Golden page: the same tool in the golden skin")
	PickService.SetTier(player, 7)
	check(heldTool(character):GetAttribute("Skin") == "Golden" and heldTier(character) == 7, "...and the Gold Hammer too")
	dataOf[player].BookGolden = {}
	PickService.Refresh(player)
	check(heldTool(character):GetAttribute("Skin") == "", "...and without it, the normal tool")
	local stranger = newPlayer("NoData")
	check(not PickService.SetTier(stranger, 3), "SetTier refuses a player whose data isn't ready")

	-- No templates at all: a warning, nothing in hand, no error.
	templates.Parent = nil
	local other, otherCharacter = newPlayer("Other")
	dataOf[other] = { Upgrades = { "Tool2", "Tool3", "Tool4", "Tool5" } }
	local warned = #warnings
	PickService.Refresh(other)
	PickService.Refresh(other)
	check(heldTool(otherCharacter) == nil and #warnings == warned + 1, "no template at all: one warning, no tool, no error")

	return passed
end
