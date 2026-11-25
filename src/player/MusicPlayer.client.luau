-- MusicPlayer: the background music (AudioConfig.Music): the Plot track while you're in your own plot, the
-- Plaza track everywhere else, each looping, crossfading over FadeSeconds when you walk in or out. Played in
-- Audio's "Music" SoundGroup, so the Music slider (Settings) sets its volume. A track without an id plays
-- nothing, with no warning (the ids are empty until the developer picks licensed tracks).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")

local Audio = require(ReplicatedStorage.Audio)
local AudioConfig = require(ReplicatedStorage.AudioConfig)
local MapConfig = require(ReplicatedStorage.MapConfig)

local MUSIC = AudioConfig.Music
local player = Players.LocalPlayer

local tracks = {} -- [name] = { sound, volume = its full volume, level = 0..1 now }
for _, name in { "Plaza", "Plot" } do
	local entry = MUSIC[name]
	if entry and type(entry.Id) == "string" and entry.Id ~= "" then
		local sound = Instance.new("Sound")
		sound.Name = "Music_" .. name
		sound.SoundId = entry.Id
		sound.Looped = true
		sound.Volume = 0
		sound.SoundGroup = Audio.Group("Music")
		sound.Parent = SoundService
		tracks[name] = { sound = sound, volume = entry.Volume or 0.3, level = 0 }
	end
end
if next(tracks) == nil then
	return -- no music chosen yet
end

local function inOwnPlot(): boolean
	local index = player:GetAttribute("PlotIndex")
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if type(index) ~= "number" or not root then
		return false
	end
	local at = MapConfig.PlotCFrame(index):PointToObjectSpace(root.Position)
	local half = MapConfig.PlotSize / 2 + MapConfig.TapMargin
	return math.abs(at.X) <= half and math.abs(at.Z) <= half
end

local wanted = "Plaza"
local checkAt = 0
RunService.Heartbeat:Connect(function(dt)
	local now = os.clock()
	if now >= checkAt then
		checkAt = now + 0.25
		wanted = if inOwnPlot() then "Plot" else "Plaza"
	end
	local step = dt / math.max(MUSIC.FadeSeconds or 2, 0.05)
	for name, track in tracks do
		local target = if name == wanted then 1 else 0
		track.level = if track.level < target then math.min(target, track.level + step) else math.max(target, track.level - step)
		track.sound.Volume = track.volume * track.level
		if track.level > 0 and not track.sound.IsPlaying then
			track.sound:Resume() -- (picks up where it paused, so a loop isn't restarted on every walk in)
		elseif track.level == 0 and track.sound.IsPlaying then
			track.sound:Pause()
		end
	end
end)
