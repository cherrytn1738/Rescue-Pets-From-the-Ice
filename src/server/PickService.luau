--[[
PickService: the ice pick every player carries (docs/GAME_DESIGN.md, "The ice pick"). Server only.

The pick is a Tool named "IcePick", cloned from ServerStorage.PickTemplates.Pick<tier> (built in Studio
by tools/studio/build_templates.luau from the uploaded models) and held in the right hand. Once a
second it checks that each player holds the pick for their tier (EconomyRules.PickTier), so buying a
pick, a rebirth, a debug reset or a respawn all end up with the right one. Without a template the player
simply holds nothing (the game still plays: taps don't need the tool).

The tool is only a look: tapping stays in TapInput.client (TapBatch), which also plays the swing on each
tap. The Tool's attribute Tier says which pick it is. SetTier is the debug menu's "Set ice pick tier".
The Creature Book's Golden page (all 18 Golden) gives the golden ice pick skin: the same pick in gold
(attribute Skin "Golden").
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local EconomyRules = require(ReplicatedStorage.EconomyRules)
local UpgradeConfig = require(ReplicatedStorage.UpgradeConfig)
local PlayerData = require(script.Parent.PlayerData)

local PickService = {}

local CHECK_SECONDS = 1
local warned = {}

local function template(tier: number): Tool?
	local folder = ServerStorage:FindFirstChild("PickTemplates")
	local tool = folder and folder:FindFirstChild("Pick" .. tier)
	if not tool and not warned[tier] then
		warned[tier] = true
		warn(`[Pick] no template PickTemplates.Pick{tier} (run tools/studio/build_templates.luau)`)
	end
	return tool
end

local function held(player: Player): Tool?
	local character = player.Character
	local tool = character and character:FindFirstChild("IcePick")
	if tool then
		return tool
	end
	local backpack = player:FindFirstChildOfClass("Backpack")
	return backpack and backpack:FindFirstChild("IcePick")
end

-- The pick skin the Creature Book gives (the Golden page's PickSkin), or "".
local function skinFor(data): string
	if type(data.BookSeen) ~= "table" then
		return ""
	end
	for _, page in EconomyRules.BookPages(data) do
		if page.Complete and page.Reward.PickSkin then
			return page.Reward.PickSkin
		end
	end
	return ""
end

local GOLD = Color3.fromRGB(255, 200, 60)
local function applySkin(tool: Tool, skin: string)
	if skin ~= "Golden" then
		return
	end
	for _, part in tool:GetDescendants() do
		if part:IsA("MeshPart") then
			part.TextureID = ""
			part.Color = GOLD
			part.Material = Enum.Material.Foil
		elseif part:IsA("BasePart") then
			part.Color = GOLD
			part.Material = Enum.Material.Foil
		end
	end
end

-- Makes sure the player holds the pick for their tier (and their book's skin).
function PickService.Refresh(player: Player)
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	local data = PlayerData.Edit(player) -- (read only: Get would copy the whole save every second)
	if not humanoid or humanoid.Health <= 0 or not data then
		return
	end
	local tier = EconomyRules.PickTier(data)
	local skin = skinFor(data)
	local current = held(player)
	if current and current:GetAttribute("Tier") == tier and (current:GetAttribute("Skin") or "") == skin then
		if current.Parent ~= character then
			humanoid:EquipTool(current) -- always in hand
		end
		return
	end
	local source = template(tier)
	if not source then
		return
	end
	if current then
		current:Destroy()
	end
	local tool = source:Clone()
	tool.Name = "IcePick"
	tool.Grip = UpgradeConfig.PickGrip -- (the config's grip, whatever the template was built with)
	tool:SetAttribute("Tier", tier)
	tool:SetAttribute("Skin", skin)
	applySkin(tool, skin)
	tool.Parent = player:FindFirstChildOfClass("Backpack") or character
	humanoid:EquipTool(tool)
end

-- Debug: the player owns exactly the pick tiers up to `tier` (the IcePick<n> upgrades; other upgrades stay),
-- and holds that pick at once. Returns whether it changed anything.
function PickService.SetTier(player: Player, tier: number): boolean
	local data = PlayerData.Edit(player)
	if not data or type(tier) ~= "number" or tier < 1 or tier > #UpgradeConfig.IcePick or tier % 1 ~= 0 then
		return false
	end
	local kept = {}
	for _, id in data.Upgrades do
		if not string.match(id, "^IcePick%d+$") then
			table.insert(kept, id)
		end
	end
	for n = 2, tier do
		table.insert(kept, "IcePick" .. n)
	end
	table.clear(data.Upgrades) -- (in place: other systems hold this table)
	for _, id in kept do
		table.insert(data.Upgrades, id)
	end
	PlayerData.Publish(player)
	PlayerData.MarkImportant(player)
	PickService.Refresh(player)
	return true
end

function PickService.Start()
	task.spawn(function()
		while true do
			task.wait(CHECK_SECONDS)
			for _, player in Players:GetPlayers() do
				task.spawn(PickService.Refresh, player)
			end
		end
	end)
end

return PickService
