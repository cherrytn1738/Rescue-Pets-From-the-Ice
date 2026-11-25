--[[
AudioConfig: every sound and music track the game plays, in one place (Audio, SoundRules and UIKit read it).

Every sound effect here is original, made for this game: synthesised by tools/make_sfx.py into
store-assets/audio/<Name>.ogg and uploaded as group 921449746 (tools/upload_models.py; the ids are in
store-assets/audio/upload_manifest.json). Licence: the game's own. To change one, edit make_sfx.py, re-run
it, upload the changed files (a changed sound becomes a NEW asset id) and paste the new id below.

An entry: Id ("rbxassetid://...") or Ids (variants, one picked at random, never the same twice in a row),
Volume (0..1, at the default SFX slider), and optionally Speed (playback speed, changes the pitch),
PitchJitter (a random +-share of Speed each play: 0.05 = +-5%), Voices (copies that can sound at once; a
new play takes the oldest; default 1), StartAt (seconds to skip), Cooldown (seconds before the same sound
may play again; default 0.05), RollOffMin / RollOffMax (studs, for sounds in the world), Lifetime (seconds
a 3D sound is kept). A 2D cue may instead have Layers: a list of entries played together (each may start
Delay seconds later), with the cue's one Cooldown.

Names the UI kit plays: Ui.Click (a button press), Ui.Locked (a press on a button that can't act), Ui.Open
and Ui.Close (a window), Ui.Invalid (an error), Ui.Reward.
]]
local AudioConfig = {}

local function id(number: number): string
	return "rbxassetid://" .. number
end

-- The uploaded files (store-assets/audio/<Name>.ogg; original, made for this game, group 921449746).
local Files = {
	BookNew = id(116859084848172),
	BookPage = id(72693009271940),
	BuyBuilding = id(75418146893361),
	BuyUpgrade = id(75297340858020),
	Click = id(129253337286961),
	Crack1 = id(77419908506636),
	Crack2 = id(99080075358091),
	Crack3 = id(108098856889355),
	Crack4 = id(76333914492141),
	CrystalTick = id(139889104044428),
	GoldenSparkle = id(83955552934976),
	Nope = id(84881498913979),
	Rebirth = id(104386884141424),
	RescueCommon = id(106813164133930),
	RescueUncommon = id(132347920075228),
	RescueRare = id(76052515314353),
	RescueEpic = id(137387529764021),
	RescueLegendary = id(133679996816314),
	RescueMythic = id(115484746980726),
	Shatter = id(93089824607966),
	TapIce1 = id(89493292392432),
	TapIce2 = id(78887809259112),
	TapIce3 = id(135293938975947),
	TapIce4 = id(98596548969935),
	WindowClose = id(123968088944203),
	WindowOpen = id(112841126634548),
}
AudioConfig.Files = Files

local TAP_VARIANTS = { Files.TapIce1, Files.TapIce2, Files.TapIce3, Files.TapIce4 }

-- Where the music and sound effects sliders start (0..1) until the player's own setting is known (the
-- MusicVolume / SfxVolume player attributes, from the saved Settings, whose default is 1 too). At the default
-- each sound plays at its Volume below; a lower slider scales every sound down.
AudioConfig.DefaultVolumes = { MusicVolume = 1, SfxVolume = 1 }

-- UI sounds (UIKit buttons and windows).
AudioConfig.Ui = {
	Click = { Id = Files.Click, Volume = 0.35, PitchJitter = 0.04, Voices = 2 },
	Locked = { Id = Files.Nope, Volume = 0.25, Cooldown = 0.3 },
	Open = { Id = Files.WindowOpen, Volume = 0.35 },
	Close = { Id = Files.WindowClose, Volume = 0.3 },
	Invalid = { Id = Files.Nope, Volume = 0.4, Cooldown = 0.3 },
	Reward = { Id = Files.BookNew, Volume = 0.5 },
}

-- Sound effects.
AudioConfig.Sfx = {
	-- your own taps on the ice (TapFeedback; capped by Rules.Tap)
	Tap = { Ids = TAP_VARIANTS, Volume = 0.4, PitchJitter = 0.06, Voices = 3, Cooldown = 0 },
	-- your buildings' hits, now and then (IceBlocks; Rules.BuildingChip): the tap sound, lower and quiet
	BuildingChip = { Ids = TAP_VARIANTS, Volume = 0.12, Speed = 0.78, PitchJitter = 0.05 },
	-- your block's crack stages (20/40/60/80%), each deeper
	Crack1 = { Id = Files.Crack1, Volume = 0.4 },
	Crack2 = { Id = Files.Crack2, Volume = 0.45 },
	Crack3 = { Id = Files.Crack3, Volume = 0.5 },
	Crack4 = { Id = Files.Crack4, Volume = 0.55 },
	Shatter = { Id = Files.Shatter, Volume = 0.55 },
	-- the rescue jingle by rarity (your own; other plots: Rules.OtherPlots)
	RescueCommon = { Id = Files.RescueCommon, Volume = 0.45 },
	RescueUncommon = { Id = Files.RescueUncommon, Volume = 0.48 },
	RescueRare = { Id = Files.RescueRare, Volume = 0.5 },
	RescueEpic = { Id = Files.RescueEpic, Volume = 0.55 },
	RescueLegendary = { Id = Files.RescueLegendary, Volume = 0.6 },
	RescueMythic = { Id = Files.RescueMythic, Volume = 0.65 },
	GoldenSparkle = { Id = Files.GoldenSparkle, Volume = 0.45 }, -- a pet turned Golden
	CrystalTick = { Id = Files.CrystalTick, Volume = 0.06, PitchJitter = 0.08 }, -- income (Rules.CrystalTick)
	BuyBuilding = { Id = Files.BuyBuilding, Volume = 0.45 },
	BuyUpgrade = { Id = Files.BuyUpgrade, Volume = 0.45 },
	CodeRedeem = { Id = Files.BuyUpgrade, Volume = 0.45 },
	Rebirth = { Id = Files.Rebirth, Volume = 0.6 },
	BookPage = { Id = Files.BookPage, Volume = 0.5 }, -- a Creature Book page completed
	BookNew = { Id = Files.BookNew, Volume = 0.45 }, -- a new creature in the book
	BookReveal = { Id = Files.BookNew, Volume = 0.35 }, -- its card fills in (Book window)
	NewLayer = { Id = Files.Crack4, Volume = 0.55, Speed = 0.7 }, -- a deeper layer opened: a low rumble
	GoldenCrash = { Id = Files.Shatter, Volume = 0.5, Speed = 0.85 }, -- the Golden Glacier lands
}

-- When sounds play (SoundRules; tests/SoundRules.spec.luau).
AudioConfig.Rules = {
	-- Your taps always sound, but at most MaxOverlap at once (one lasts about Length seconds) and at least
	-- MinGap apart, so an autoclicker can't stack dozens. A fast streak lifts the pitch by up to StreakPitch.
	Tap = { MaxOverlap = 3, Length = 0.22, MinGap = 0.06, StreakPitch = 0.08, StreakMax = 20 },
	-- Buildings' hits on your own block: at most one chip every MinGap seconds, each time with Chance, and
	-- none within QuietAfterTap seconds of your own tap. Never from other plots.
	BuildingChip = { MinGap = 2.5, Chance = 0.45, QuietAfterTap = 0.8 },
	-- Other players' plots: only these rarities' rescue jingles, within MaxDistance studs, at Volume times
	-- the jingle's own. Their taps, cracks and shatters are silent.
	OtherPlots = { Rarities = { Legendary = true, Mythic = true }, MaxDistance = 60, Volume = 0.45 },
	-- The income tick: while crystals rise, a chance (Chance) every MinGap seconds, so it comes now and then
	-- rather than like a clock; not while you're tapping.
	CrystalTick = { MinGap = 2, Chance = 0.35, QuietAfterTap = 0.8 },
	-- A rescue's jingle starts this long after the shatter; a new creature's book ding BookDelay after the
	-- rescue, and a completed book page PageDelay after the change.
	JingleDelay = 0.15,
	BookDelay = 1.1,
	PageDelay = 1.8,
}

-- Music (MusicPlayer.client): Plaza outside your plot, Plot inside it, looping, crossfading over FadeSeconds.
-- The ids are EMPTY on purpose: the developer picks licensed tracks from the Creator Store (Toolbox, Audio,
-- creator "Roblox" / APM / ProSoundEffects) and pastes "rbxassetid://..." here with its source and licence.
-- With no id nothing plays and nothing warns.
AudioConfig.Music = {
	FadeSeconds = 2.5,
	Plaza = { Id = "", Volume = 0.35 }, -- light, playful winter tune, ~100-120 BPM (bells, pizzicato, glockenspiel)
	Plot = { Id = "", Volume = 0.3 }, -- calm, cosy loop, ~80-95 BPM (soft piano / music box / mallets, no vocals)
}

return AudioConfig
