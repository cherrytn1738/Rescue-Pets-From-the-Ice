--[[
SettingsService: the Settings screen (docs/GAME_DESIGN.md, "Screens": music, sound effects, reduced
effects for low-end phones). Server only. SaveSettings (RemoteEvent) sends { Music, Sounds,
ReducedEffects }; the server checks them, saves them (Settings) and sets the player attributes Audio
reads (MusicVolume, SfxVolume) and ReducedEffects.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PlayerData = require(script.Parent.PlayerData)

local SettingsService = {}

local lastSave = {}

local function apply(player: Player, settings)
	player:SetAttribute("MusicVolume", settings.Music)
	player:SetAttribute("SfxVolume", settings.Sounds)
	player:SetAttribute("ReducedEffects", settings.ReducedEffects)
end

local function volume(value): number?
	if type(value) ~= "number" or value ~= value then
		return nil
	end
	return math.clamp(value, 0, 1)
end

function SettingsService.Save(player: Player, settings): boolean
	if type(settings) ~= "table" then
		return false
	end
	local now = os.clock()
	if lastSave[player] and now - lastSave[player] < 0.5 then
		return false
	end
	lastSave[player] = now
	local data = PlayerData.Edit(player)
	local music, sounds = volume(settings.Music), volume(settings.Sounds)
	if not data or not music or not sounds or type(settings.ReducedEffects) ~= "boolean" then
		return false
	end
	data.Settings = { Music = music, Sounds = sounds, ReducedEffects = settings.ReducedEffects }
	apply(player, data.Settings)
	PlayerData.Publish(player)
	return true
end

function SettingsService.Start()
	ReplicatedStorage:WaitForChild("SaveSettings").OnServerEvent:Connect(SettingsService.Save)
	PlayerData.OnLoaded(function(player, data)
		apply(player, data.Settings)
	end)
	Players.PlayerRemoving:Connect(function(player)
		lastSave[player] = nil
	end)
end

return SettingsService
