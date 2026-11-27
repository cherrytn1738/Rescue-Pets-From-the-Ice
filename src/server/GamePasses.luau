--[[
GamePasses: who owns which game pass. Server only.

Roblox's ownership record is the truth:
 * checked at join with UserOwnsGamePassAsync (in a pcall: a failed lookup grants nothing this
   session and never takes anything away)
 * a pass bought in the game counts at once: PromptGamePassPurchaseFinished fires on the server, so
   it can be trusted. Every perk reads Owns() when it applies, and OnChanged listeners refresh what
   was already shown, so nobody has to rejoin
 * never saved, and never taken from the client. The one exception: a pass received as a GIFT (bought
   as the pass's gift product by another player) has no Roblox record, so it is saved in the
   recipient's GiftedPasses and counts as owned (Give(), from the "Pass" reward kind)
 * published as Owns_<Key> player attributes for the UI only; the server never reads them back

Studio: a test purchase of a pass never becomes real ownership, and a pass without an id can't be
prompted at all, so the debug menu (and the shop, for a pass with no id yet) sets a Studio-only
override for this session: SetStudioOverride. Never saved, ignored outside Studio.

Studio switch StudioIgnoreOwnedPasses (Workspace attribute, true; read only in Studio): what Roblox
says at join is ignored, so the developer's account (which owns every pass) plays as a normal player.
A pass bought in this session (a Studio test purchase), a gifted pass and a debug override still count.
It applies at once: turning it on or off refreshes every player's passes.
]]
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local PlayerData = require(script.Parent.PlayerData)

local GamePasses = {}

local owned = {} -- [player] = { [passKey] = true }: what Roblox says at join (this session only)
local boughtHere = {} -- [player] = { [passKey] = true }: bought in this session (counts even when ignoring owned passes)
local studioOverrides = {} -- [player] = { [passKey] = true / false } (Studio only)
local changedListeners = {}
local lookedUp = {} -- [player] = true once their join lookup has finished

local function fireChanged(player: Player, passKey: string)
	local owns = GamePasses.Owns(player, passKey)
	player:SetAttribute("Owns_" .. passKey, owns)
	for _, callback in changedListeners do
		task.spawn(callback, player, passKey, owns)
	end
end

local function ignoringOwned(): boolean
	return RunService:IsStudio() and Workspace:GetAttribute("StudioIgnoreOwnedPasses") == true
end

-- The one ownership check every perk uses. Anything that isn't a real Player owns nothing.
function GamePasses.Owns(player, passKey: string): boolean
	if typeof(player) ~= "Instance" or not player:IsA("Player") then
		return false
	end
	if RunService:IsStudio() and studioOverrides[player] then
		local override = studioOverrides[player][passKey]
		if override ~= nil then
			return override
		end
	end
	if boughtHere[player] ~= nil and boughtHere[player][passKey] == true then
		return true
	end
	if not ignoringOwned() and owned[player] ~= nil and owned[player][passKey] == true then
		return true
	end
	local data = PlayerData.Get(player)
	return data ~= nil and type(data.GiftedPasses) == "table" and data.GiftedPasses[passKey] == true
end

-- A pass received as a gift: saved in the live data (the caller saves), and counts at once. Never yields.
function GamePasses.GiveGifted(player: Player, data, passKey: string)
	data.GiftedPasses[passKey] = true
	task.spawn(fireChanged, player, passKey)
end

-- Whether this player's passes have been looked up since they joined (until then Owns() is false
-- for every pass Roblox hasn't confirmed yet). Anything that pays a pass perk once at join waits for it.
function GamePasses.IsLookedUp(player: Player): boolean
	return lookedUp[player] == true
end

-- callback(player, passKey, owns) runs in its own thread whenever a player's ownership of a pass
-- may have changed (bought in the game, looked up at join, a Studio override).
function GamePasses.OnChanged(callback)
	table.insert(changedListeners, callback)
end

-- Studio only (debug menu): owns = true / false for this session, nil = back to what Roblox says.
function GamePasses.SetStudioOverride(player: Player, passKey: string, owns: boolean?): boolean
	if not RunService:IsStudio() or not MonetizationConfig.GetPass(passKey) then
		return false
	end
	studioOverrides[player] = studioOverrides[player] or {}
	studioOverrides[player][passKey] = owns
	fireChanged(player, passKey)
	return true
end

local function askRoblox(player: Player, pass): boolean
	if not MonetizationConfig.IsLive(pass) then
		return false
	end
	local ok, result = pcall(MarketplaceService.UserOwnsGamePassAsync, MarketplaceService, player.UserId, pass.Id)
	return ok and result == true
end

local function onPlayerAdded(player: Player)
	for _, pass in MonetizationConfig.Passes do
		player:SetAttribute("Owns_" .. pass.Key, false)
	end
	local found = {}
	for _, pass in MonetizationConfig.Passes do
		if askRoblox(player, pass) then
			found[pass.Key] = true
		end
	end
	if player.Parent ~= Players then
		return -- left while we were asking
	end
	owned[player] = owned[player] or {}
	for passKey in found do
		owned[player][passKey] = true -- merged: a purchase may have arrived while we asked
	end
	lookedUp[player] = true
	for _, pass in MonetizationConfig.Passes do
		fireChanged(player, pass.Key)
	end
end

function GamePasses.Start()
	-- passes received as gifts count once the save is loaded
	PlayerData.OnLoaded(function(player, data)
		for passKey in data.GiftedPasses or {} do
			if MonetizationConfig.GetPass(passKey) then
				fireChanged(player, passKey)
			end
		end
	end)
	Players.PlayerAdded:Connect(onPlayerAdded)
	for _, player in Players:GetPlayers() do
		task.spawn(onPlayerAdded, player)
	end
	Players.PlayerRemoving:Connect(function(player)
		owned[player] = nil
		boughtHere[player] = nil
		studioOverrides[player] = nil
		lookedUp[player] = nil
	end)
	if RunService:IsStudio() then
		Workspace:GetAttributeChangedSignal("StudioIgnoreOwnedPasses"):Connect(function()
			if ignoringOwned() then
				warn("[Studio] StudioIgnoreOwnedPasses is on: passes your account owns are ignored (remove the attribute before saving the place)")
			end
			for _, player in Players:GetPlayers() do
				for _, pass in MonetizationConfig.Passes do
					task.spawn(fireChanged, player, pass.Key)
				end
			end
		end)
		if ignoringOwned() then
			warn("[Studio] StudioIgnoreOwnedPasses is on: passes your account owns are ignored (remove the attribute before saving the place)")
		end
	end
	-- A pass bought through an in-game prompt counts straight away (no rejoin).
	MarketplaceService.PromptGamePassPurchaseFinished:Connect(function(player, gamePassId, purchased)
		local pass = purchased and MonetizationConfig.GetPassById(gamePassId)
		if not pass or player.Parent ~= Players then
			return
		end
		boughtHere[player] = boughtHere[player] or {}
		boughtHere[player][pass.Key] = true
		print(`[Purchase] {player.Name} bought the {pass.Name} pass`)
		fireChanged(player, pass.Key)
		local notice = ReplicatedStorage:FindFirstChild("PurchaseNotice")
		if notice then
			notice:FireClient(player, { Kind = "PassOwned", Item = pass.Name })
		end
	end)
end

return GamePasses
