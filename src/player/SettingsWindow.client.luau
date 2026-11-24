-- The Settings screen (docs/GAME_DESIGN.md, "Screens"): music and sound volume, and reduced effects for
-- low-end phones (half the particles, no camera shake). Opened from the gear button; saved on the
-- server (SaveSettings), which sets the volume attributes Audio reads.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Audio = require(ReplicatedStorage.Audio)
local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)
local ClientState = require(script.Parent.ClientState)

local remote = ReplicatedStorage:WaitForChild("SaveSettings") :: RemoteEvent
local Colors = UIKit.Colors
local player = Players.LocalPlayer

local current = { Music = 1, Sounds = 1, ReducedEffects = false }
local musicLabel, musicSlider, setMusic, soundLabel, soundSlider, setSound, effectsLabel, effectsButton

local function save()
	remote:FireServer(table.clone(current))
end

local window = ShowcaseKit.Window("SettingsWindow", "Settings", {
	width = 640,
	height = 420,
	onLayout = function(width)
		musicLabel.Position, musicLabel.Size = UDim2.fromOffset(0, 0), UDim2.fromOffset(width, 32)
		musicSlider.Position, musicSlider.Size = UDim2.fromOffset(20, 40), UDim2.fromOffset(width - 40, 34)
		soundLabel.Position, soundLabel.Size = UDim2.fromOffset(0, 96), UDim2.fromOffset(width, 32)
		soundSlider.Position, soundSlider.Size = UDim2.fromOffset(20, 136), UDim2.fromOffset(width - 40, 34)
		effectsLabel.Position, effectsLabel.Size = UDim2.fromOffset(0, 196), UDim2.fromOffset(width, 32)
		effectsButton.Position, effectsButton.Size = UDim2.fromOffset(width / 2 - 150, 236), UDim2.fromOffset(300, 64)
	end,
})
local content = window.content
musicLabel = UIKit.Label(content, "MusicLabel", "Music", 28)
musicLabel.TextXAlignment = Enum.TextXAlignment.Center
musicSlider, setMusic = UIKit.Slider(content, "Music", function(value)
	current.Music = value
	Audio.Preview("MusicVolume", value)
end, function(value)
	current.Music = value
	save()
end)
soundLabel = UIKit.Label(content, "SoundLabel", "Sound effects", 28)
soundLabel.TextXAlignment = Enum.TextXAlignment.Center
soundSlider, setSound = UIKit.Slider(content, "Sounds", function(value)
	current.Sounds = value
	Audio.Preview("SfxVolume", value)
end, function(value)
	current.Sounds = value
	save()
end)
effectsLabel = UIKit.Label(content, "EffectsLabel", "Reduced effects (for low-end phones)", 24, Colors.Muted)
effectsLabel.TextXAlignment = Enum.TextXAlignment.Center
effectsButton = UIKit.Button(content, "ReducedEffects", "OFF", "Done", 30)
effectsButton.Activated:Connect(function()
	current.ReducedEffects = not current.ReducedEffects
	UIKit.SetButton(effectsButton, if current.ReducedEffects then "ON" else "OFF", if current.ReducedEffects then "Go" else "Done")
	save()
end)

local function load()
	local data = ClientState.Data()
	if data and data.Settings then
		current.Music = data.Settings.Music or 1
		current.Sounds = data.Settings.Sounds or 1
		current.ReducedEffects = data.Settings.ReducedEffects == true
	end
	setMusic(current.Music)
	setSound(current.Sounds)
	UIKit.SetButton(effectsButton, if current.ReducedEffects then "ON" else "OFF", if current.ReducedEffects then "Go" else "Done")
end

local gear = player:WaitForChild("PlayerGui"):WaitForChild("HUD"):WaitForChild("Root"):WaitForChild("SettingsButton")
gear.Activated:Connect(function()
	load()
	window.Toggle()
end)
