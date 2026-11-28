--[[
PickService: the tool every player carries (docs/GAME_DESIGN.md, "Tools": 18 tiers in five families). Server only.

The tool is a Tool named "IceTool", cloned from ServerStorage.ToolTemplates.Tool<tier> (built in Studio by
tools/studio/build_templates.luau with ONLY = "Tools" from the uploaded models) and held in the right hand with its
family's grip (SwingConfig.Families[family].Grip). Once a second it checks that each player holds the tool for their
tier (EconomyRules.ToolTier), so buying a tool, a rebirth, a debug reset or a respawn all end up with the right one.
A tier whose model isn't made yet holds the nearest tool of the same family (or any family), with one warning.
Without any template the player simply holds nothing (the game still plays: taps don't need the tool).

The tool is only a look: tapping stays in TapInput.client (TapBatch), which also plays the swing on each tap
(PickSwing). The Tool's attributes say which it is: Tier, Family, Skin. SetTier is the debug menu's "Set tool
tier". The Creature Book's Golden page (all 18 Golden) gives the golden skin: whatever tool you hold, in gold
(attribute Skin "Golden").
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local EconomyRules = require(ReplicatedStorage.EconomyRules)
local SwingConfig = require(ReplicatedStorage.SwingConfig)
local UpgradeConfig = require(ReplicatedStorage.UpgradeConfig)
local PlayerData = require(script.Parent.PlayerData)

local PickService = {}

PickService.ToolName = "IceTool"

local CHECK_SECONDS = 1
local warned = {}

local function templateOf(tier: number): Tool?
	local folder = ServerStorage:FindFirstChild("ToolTemplates")
	return folder and folder:FindFirstChild("Tool" .. tier)
end

-- The template for a tier: its own, else the nearest tier of its family that has one, else the nearest of any.
local function template(tier: number): Tool?
	local own = templateOf(tier)
	if own then
		return own
	end
	local family = UpgradeConfig.Tools[tier] and UpgradeConfig.Tools[tier].Family
	local best, bestScore = nil, math.huge
	for _, tool in UpgradeConfig.Tools do
		local found = templateOf(tool.Tier)
		if found then
			local score = math.abs(tool.Tier - tier) + (if tool.Family == family then 0 else 100)
			if score < bestScore then
				best, bestScore = found, score
			end
		end
	end
	if not warned[tier] then
		warned[tier] = true
		warn(`[Tool] no template ToolTemplates.Tool{tier}` .. (if best then `: holding {best.Name} instead` else "") .. " (run tools/studio/build_templates.luau)")
	end
	return best
end

local function held(player: Player): Tool?
	local character = player.Character
	local tool = character and character:FindFirstChild(PickService.ToolName)
	if tool then
		return tool
	end
	local backpack = player:FindFirstChildOfClass("Backpack")
	return backpack and backpack:FindFirstChild(PickService.ToolName)
end

-- The tool skin the Creature Book gives (the Golden page's PickSkin), or "".
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
local GOLD_GLOW = Color3.fromRGB(255, 230, 140)
local function applySkin(tool: Tool, skin: string)
	if skin ~= "Golden" then
		return
	end
	for _, part in tool:GetDescendants() do
		if part:IsA("MeshPart") and string.sub(part.Name, -4) == "Glow" then
			part.TextureID = "" -- (a magical tool's glowing pieces stay lit: glowing gold)
			part.Color = GOLD_GLOW
			part.Material = Enum.Material.Neon
		elseif part:IsA("MeshPart") then
			part.TextureID = ""
			part.Color = GOLD
			part.Material = Enum.Material.Foil
		elseif part:IsA("BasePart") then
			part.Color = GOLD
			part.Material = Enum.Material.Foil
		end
	end
end

-- Makes sure the player holds the tool for their tier (and their book's skin).
function PickService.Refresh(player: Player)
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	local data = PlayerData.Edit(player) -- (read only: Get would copy the whole save every second)
	if not humanoid or humanoid.Health <= 0 or not data then
		return
	end
	local tier = EconomyRules.ToolTier(data)
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
	local info = UpgradeConfig.Tools[tier]
	local tool = source:Clone()
	tool.Name = PickService.ToolName
	tool.ToolTip = info.Name
	tool.Grip = SwingConfig.Family(info.Family).Grip -- (the family's grip, whatever the template was built with)
	tool:SetAttribute("Tier", tier)
	tool:SetAttribute("Family", info.Family)
	tool:SetAttribute("Skin", skin)
	applySkin(tool, skin)
	tool.Parent = player:FindFirstChildOfClass("Backpack") or character
	humanoid:EquipTool(tool)
end

-- Debug: the player owns exactly the tool tiers up to `tier` (the Tool<n> upgrades; other upgrades stay), and holds
-- that tool at once. Returns whether it changed anything.
function PickService.SetTier(player: Player, tier: number): boolean
	local data = PlayerData.Edit(player)
	if not data or type(tier) ~= "number" or tier < 1 or tier > #UpgradeConfig.Tools or tier % 1 ~= 0 then
		return false
	end
	local kept = {}
	for _, id in data.Upgrades do
		if not string.match(id, "^Tool%d+$") then
			table.insert(kept, id)
		end
	end
	for n = 2, tier do
		table.insert(kept, "Tool" .. n)
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
