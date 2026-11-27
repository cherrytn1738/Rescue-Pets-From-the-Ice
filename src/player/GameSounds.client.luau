-- GameSounds: the sounds no window or effect owns (AudioConfig, SoundRules):
--  - the very soft income tick while your crystals rise (now and then: Rules.CrystalTick, not while you're
--    tapping);
--  - the debug menu's "Play a sound" (DebugSound), to hear any cue on its own.
-- The rest: taps (TapFeedback), the block's cracks, shatter, rescue jingles and building chips (IceBlocks),
-- new creatures and completed Book pages (BookMoment), buying (BuildWindow, UpgradesWindow), Golden pets (PetsWindow), rebirths
-- (RebirthWindow), and every kit button and window (UIKit).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Audio = require(ReplicatedStorage.Audio)
local AudioConfig = require(ReplicatedStorage.AudioConfig)
local SoundRules = require(ReplicatedStorage.SoundRules)
local ClientState = require(script.Parent.ClientState)
local TapFeedback = require(script.Parent.TapFeedback)

local player = Players.LocalPlayer
local RULES = AudioConfig.Rules

-- the income tick
local tickGate = SoundRules.TickGate(RULES.CrystalTick, math.random)
local lastCrystals = player:GetAttribute("Crystals")
player:GetAttributeChangedSignal("Crystals"):Connect(function()
	local crystals = player:GetAttribute("Crystals")
	local rose = type(crystals) == "number" and type(lastCrystals) == "number" and crystals > lastCrystals
	lastCrystals = crystals
	if rose and tickGate:Allow(os.clock(), TapFeedback.LastTapAt()) then
		Audio.Play("CrystalTick")
	end
end)

-- the debug menu's sound test
ClientState.Event("DebugSound", function(payload)
	if type(payload) == "table" and type(payload.Name) == "string" then
		Audio.Play(payload.Name, { Volume = tonumber(payload.Volume) or 1 })
	end
end)
