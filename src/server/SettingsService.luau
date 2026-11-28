--[[
SettingsService: the Settings screen (docs/GAME_DESIGN.md, "Screens": music, sound effects, reduced
effects for low-end phones, auto-equip best pets, the day-night cycle). Server only. SaveSettings (RemoteEvent) sends
{ Music, Sounds, ReducedEffects, AutoEquip, DayNight (both optional: unchanged when left out) }; the server checks them, saves
them (Settings) and sets the player attributes Audio reads (MusicVolume, SfxVolume) and ReducedEffects.
Turning auto-equip on equips the best pets at once.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PetService = require(script.Parent.PetService)
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
	if not data or not music or not sounds or type(settings.ReducedEffects) ~= "boolean"
		or (settings.AutoEquip ~= nil and type(settings.AutoEquip) ~= "boolean")
		or (settings.DayNight ~= nil and type(settings.DayNight) ~= "boolean") then
		return false
	end
	local autoEquip = if settings.AutoEquip == nil then data.Settings.AutoEquip ~= false else settings.AutoEquip
	local turnedOn = autoEquip and data.Settings.AutoEquip == false
	local dayNight = if settings.DayNight == nil then data.Settings.DayNight ~= false else settings.DayNight
	data.Settings = { Music = music, Sounds = sounds, ReducedEffects = settings.ReducedEffects, AutoEquip = autoEquip, DayNight = dayNight }
	apply(player, data.Settings)
	if turnedOn then
		PetService.AutoEquip(player, data)
	end
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
