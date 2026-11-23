--[[
AudioConfig: every sound and music track the game plays, in one place (Audio and UIKit read it).

Empty for now: this game has no sounds yet, so UIKit.PlaySound and Audio.Play play nothing. Add an
entry when a sound is chosen, and note beside its id where it comes from and its licence (Roblox's own
library, creator "Roblox"; Roblox's licensed partner libraries on the Creator Store, "ProSoundEffects"
or "APMOfficial"; or the developer's own recording, uploaded to the group).

An entry: Id ("rbxassetid://..."), Volume (0..1, at the default SFX slider), and optionally Speed
(playback speed, changes the pitch), StartAt (seconds to skip), Cooldown (seconds before the same
sound may play again), RollOffMin / RollOffMax (studs, for sounds in the world), Lifetime (seconds a
3D sound is kept). A 2D cue may instead have Layers: a list of entries played together (each may
start Delay seconds later), with the cue's one Cooldown.

Names the UI kit already plays (fill these first): Ui.Click (a button press), Ui.Locked (a press on a
button that can't act), Ui.Open and Ui.Close (a window), Ui.Invalid (an error), Ui.Reward.
]]
local AudioConfig = {}

-- Where the music and sound effects volumes start (0..1) until the player's own setting is known
-- (the MusicVolume / SfxVolume player attributes, once the game saves a volume setting). At the
-- default each sound plays at its Volume.
AudioConfig.DefaultVolumes = { MusicVolume = 0.5, SfxVolume = 0.8 }

-- UI sounds (UIKit buttons and windows).
AudioConfig.Ui = {}

-- Sound effects.
AudioConfig.Sfx = {}

return AudioConfig
