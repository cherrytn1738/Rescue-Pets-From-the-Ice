--[[
Audio: plays the game's sounds on a client, through two SoundGroups: "Music" and "SFX" (everything
else). Client only (UIKit and the client scripts use it); every id and volume is in AudioConfig. A
name AudioConfig doesn't list plays nothing (AudioConfig is empty until the game has sounds).

 * Audio.Play(name)            a sound effect or UI sound, heard everywhere (2D).
 * Audio.PlayAt(name, where)   a sound effect at a point or part in the world (3D; louder near).
 * Audio.Group(kind)           the "Music" or "SFX" SoundGroup.
 * Audio.Preview(setting, v)   a volume while its slider is dragged, before the server has it.

Volumes come from the player's MusicVolume / SfxVolume attributes when the server sets them (a
saved volume setting), and AudioConfig.DefaultVolumes otherwise. Any other Sound that appears in the
Workspace (footsteps, sounds the server plays) is put in the SFX group, so the volume covers it too.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")
local Workspace = game:GetService("Workspace")

local AudioConfig = require(ReplicatedStorage.AudioConfig)

local Audio = {}

local GROUP_FOR_SETTING = { MusicVolume = "Music", SfxVolume = "SFX" }
local preview = {} -- [setting] = a volume shown while its slider is dragged

function Audio.Group(kind: string): SoundGroup
	local group = SoundService:FindFirstChild(kind)
	if not group then
		group = Instance.new("SoundGroup")
		group.Name = kind
		group.Volume = 1
		group.Parent = SoundService
	end
	return group :: SoundGroup
end

-- The player's volume for "MusicVolume" or "SfxVolume" (0..1).
function Audio.Volume(setting: string): number
	if preview[setting] then
		return preview[setting]
	end
	local player = Players.LocalPlayer
	local value = player and player:GetAttribute(setting)
	return if type(value) == "number" then math.clamp(value, 0, 1) else AudioConfig.DefaultVolumes[setting]
end

local function applyVolumes()
	for setting, kind in GROUP_FOR_SETTING do
		-- At the default slider position each sound plays at its AudioConfig volume; the slider
		-- scales that (0 = silent, all the way up = 1 / the default as loud).
		Audio.Group(kind).Volume = Audio.Volume(setting) / AudioConfig.DefaultVolumes[setting]
	end
end

-- value = nil ends the preview (the saved value, once the server has it, takes over).
function Audio.Preview(setting: string, value: number?)
	preview[setting] = if value then math.clamp(value, 0, 1) else nil
	applyVolumes()
end

local function cue(name: string)
	return AudioConfig.Sfx[name] or AudioConfig.Ui[name]
end

local lastPlayed = {} -- [name] = os.clock()
local function allowed(name: string, entry): boolean
	local now = os.clock()
	if lastPlayed[name] and now - lastPlayed[name] < (entry.Cooldown or 0.05) then
		return false
	end
	lastPlayed[name] = now
	return true
end

local function newSound(entry, name: string): Sound
	local sound = Instance.new("Sound")
	sound.Name = "SFX_" .. name
	sound.SoundId = entry.Id
	sound.Volume = entry.Volume or 0.5
	sound.PlaybackSpeed = entry.Speed or 1
	sound.SoundGroup = Audio.Group("SFX")
	return sound
end

local pooled = {} -- [name] = the 2D Sound reused for that cue (or that layer of it)
local function playPooled(key: string, entry)
	local sound = pooled[key]
	if not sound then
		sound = newSound(entry, key)
		sound.Parent = SoundService
		pooled[key] = sound
	end
	sound.TimePosition = entry.StartAt or 0
	sound:Play()
end

-- A cue with Layers plays each layer together (a layer may start Delay seconds later), as one sound
-- with one Cooldown.
function Audio.Play(name: string)
	local entry = cue(name)
	if not entry or not allowed(name, entry) then
		return
	end
	if entry.Layers then
		for index, layer in entry.Layers do
			if (layer.Delay or 0) > 0 then
				task.delay(layer.Delay, playPooled, name .. index, layer)
			else
				playPooled(name .. index, layer)
			end
		end
	else
		playPooled(name, entry)
	end
end

-- where: a BasePart (the sound follows it) or a Vector3.
function Audio.PlayAt(name: string, where: BasePart | Vector3)
	local entry = cue(name)
	if not entry or not allowed(name .. tostring(where), entry) then
		return
	end
	local holder
	if typeof(where) == "Vector3" then
		holder = Instance.new("Attachment")
		holder.Name = "SoundSpot"
		holder.WorldPosition = where
		holder.Parent = Workspace.Terrain
	end
	local sound = newSound(entry, name)
	sound.RollOffMinDistance = entry.RollOffMin or 12
	sound.RollOffMaxDistance = entry.RollOffMax or 160
	sound.Parent = holder or where
	sound.TimePosition = entry.StartAt or 0
	sound:Play()
	task.delay(entry.Lifetime or 4, function()
		sound:Destroy()
		if holder then
			holder:Destroy()
		end
	end)
end

if RunService:IsClient() then
	applyVolumes()
	local player = Players.LocalPlayer
	for setting in GROUP_FOR_SETTING do
		player:GetAttributeChangedSignal(setting):Connect(applyVolumes)
	end
	-- Sounds the game didn't make through here (footsteps, the server's hit sounds) follow the
	-- SFX slider too.
	local sfx = Audio.Group("SFX")
	local function adopt(sound: Instance)
		if sound:IsA("Sound") and sound.SoundGroup == nil then
			sound.SoundGroup = sfx
		end
	end
	for _, descendant in Workspace:GetDescendants() do
		adopt(descendant)
	end
	Workspace.DescendantAdded:Connect(adopt)
end

return Audio
