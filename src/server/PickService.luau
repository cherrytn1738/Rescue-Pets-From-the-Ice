--[[
PickService: the ice pick every player carries (docs/GAME_DESIGN.md, "The ice pick"). Server only.

The pick is a Tool named "IcePick", cloned from ServerStorage.PickTemplates.Pick<tier> (built in Studio
by tools/studio/build_templates.luau from the uploaded models) and held in the right hand. Once a
second it checks that each player holds the pick for their tier (EconomyRules.PickTier), so buying a
pick, a rebirth, a debug reset or a respawn all end up with the right one. Without a template the player
simply holds nothing (the game still plays: taps don't need the tool).

The tool is only a look: tapping stays in TapInput.client (TapBatch), and PickSwing.client plays the
swing on each tap. The Tool's attribute Tier says which pick it is.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local EconomyRules = require(ReplicatedStorage.EconomyRules)
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

-- Makes sure the player holds the pick for their tier.
function PickService.Refresh(player: Player)
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	local data = PlayerData.Edit(player) -- (read only: Get would copy the whole save every second)
	if not humanoid or humanoid.Health <= 0 or not data then
		return
	end
	local tier = EconomyRules.PickTier(data)
	local current = held(player)
	if current and current:GetAttribute("Tier") == tier then
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
	tool:SetAttribute("Tier", tier)
	tool.Parent = player:FindFirstChildOfClass("Backpack") or character
	humanoid:EquipTool(tool)
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
