--[[
Audio: plays the game's sounds on a client, through two SoundGroups: "Music" and "SFX" (everything
else). Client only (UIKit and the client scripts use it); every id and volume is in AudioConfig. A
name AudioConfig doesn't list, or an entry without an id, plays nothing.

 * Audio.Play(name, options?)  a sound effect or UI sound, heard everywhere (2D). options: Volume (a
                               share of the entry's volume) and Speed (times the entry's speed). Returns
                               whether it played (false in its Cooldown).
 * Audio.Preload()             loads every sound up front (done when a client starts).
 * Audio.PlayAt(name, where)   a sound effect at a point or part in the world (3D; louder near).
 * Audio.Group(kind)           the "Music" or "SFX" SoundGroup.
 * Audio.Preview(setting, v)   a volume while its slider is dragged, before the server has it.

Volumes come from the player's MusicVolume / SfxVolume attributes when the server sets them (a
saved volume setting), and AudioConfig.DefaultVolumes otherwise. Any other Sound that appears in the
Workspace (footsteps, sounds the server plays) is put in the SFX group, so the volume covers it too.
]]
local ContentProvider = game:GetService("ContentProvider")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")
local Workspace = game:GetService("Workspace")

local AudioConfig = require(ReplicatedStorage.AudioConfig)
local SoundRules = require(ReplicatedStorage.SoundRules)

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

-- The entry's variants: Ids, or its one Id ("" or nil = none).
local function idsOf(entry): { string }
	if entry.Ids then
		return entry.Ids
	end
	return if type(entry.Id) == "string" and entry.Id ~= "" then { entry.Id } else {}
end

local lastVariant = {} -- [name] = the variant played last (the next one differs)
local function pickId(name: string, entry): string?
	local ids = idsOf(entry)
	if #ids == 0 then
		return nil
	end
	local index = SoundRules.PickVariant(#ids, lastVariant[name], math.random)
	lastVariant[name] = index
	return ids[index]
end

local function speedOf(entry, options): number
	local jitter = entry.PitchJitter or 0
	local speed = (entry.Speed or 1) * (options and options.Speed or 1)
	return speed * (1 + (math.random() * 2 - 1) * jitter)
end

local function newSound(entry, name: string, soundId: string): Sound
	local sound = Instance.new("Sound")
	sound.Name = "SFX_" .. name
	sound.SoundId = soundId
	sound.Volume = entry.Volume or 0.5
	sound.PlaybackSpeed = entry.Speed or 1
	sound.SoundGroup = Audio.Group("SFX")
	return sound
end

-- The 2D Sounds, reused: [key|soundId] = the entry's Voices copies, played round-robin (a new play takes
-- the oldest copy, so at most Voices of one sound ever overlap).
local pooled = {}
local nextVoice = {}
local function voiceFor(key: string, entry, soundId: string): Sound
	local poolKey = key .. "|" .. soundId
	local voices = pooled[poolKey]
	if not voices then
		voices = {}
		for index = 1, math.max(1, entry.Voices or 1) do
			local sound = newSound(entry, key, soundId)
			sound.Name = `SFX_{key}_{index}`
			sound.Parent = SoundService
			voices[index] = sound
		end
		pooled[poolKey] = voices
		nextVoice[poolKey] = 1
	end
	local index = nextVoice[poolKey]
	nextVoice[poolKey] = index % #voices + 1
	return voices[index]
end

local function playPooled(key: string, entry, options)
	local soundId = pickId(key, entry)
	if not soundId then
		return
	end
	local sound = voiceFor(key, entry, soundId)
	sound.Volume = (entry.Volume or 0.5) * (options and options.Volume or 1)
	sound.PlaybackSpeed = speedOf(entry, options)
	sound.TimePosition = entry.StartAt or 0
	sound:Play()
end

-- A cue with Layers plays each layer together (a layer may start Delay seconds later), as one sound
-- with one Cooldown.
function Audio.Play(name: string, options: { Volume: number?, Speed: number? }?): boolean
	local entry = cue(name)
	if not entry or not allowed(name, entry) then
		return false
	end
	if entry.Layers then
		for index, layer in entry.Layers do
			if (layer.Delay or 0) > 0 then
				task.delay(layer.Delay, playPooled, name .. index, layer, options)
			else
				playPooled(name .. index, layer, options)
			end
		end
	else
		playPooled(name, entry, options)
	end
	return true
end

-- Loads every sound effect and UI sound up front, so the first tap or click isn't silent while it loads.
function Audio.Preload()
	local sounds = {}
	for _, list in { AudioConfig.Sfx, AudioConfig.Ui } do
		for name, entry in list do
			for index, part in entry.Layers or { entry } do
				local key = if entry.Layers then name .. index else name
				for _, soundId in idsOf(part) do
					local voices = pooled[key .. "|" .. soundId]
					if not voices then
						voiceFor(key, part, soundId)
						voices = pooled[key .. "|" .. soundId]
					end
					table.insert(sounds, voices[1])
				end
			end
		end
	end
	task.spawn(function()
		pcall(ContentProvider.PreloadAsync, ContentProvider, sounds)
	end)
end

-- where: a BasePart (the sound follows it) or a Vector3.
function Audio.PlayAt(name: string, where: BasePart | Vector3)
	local entry = cue(name)
	if not entry or not allowed(name .. tostring(where), entry) then
		return
	end
	local soundId = pickId(name, entry)
	if not soundId then
		return
	end
	local holder
	if typeof(where) == "Vector3" then
		holder = Instance.new("Attachment")
		holder.Name = "SoundSpot"
		holder.WorldPosition = where
		holder.Parent = Workspace.Terrain
	end
	local sound = newSound(entry, name, soundId)
	sound.PlaybackSpeed = speedOf(entry, nil)
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
	Audio.Preload()
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
