--[[
CodesConfig: the promo codes players can redeem in the Codes window. Server only, on purpose: a code
listed here never reaches a player's computer until they type it, so codes can be added before they
are announced.

Each code:
 * Code     the text players type. Not case-sensitive, letters and digits only (CodeRules.Normalize).
 * Reward   what it gives: the same reward table a Robux product uses, granted through
            PurchaseRewards: { Kind = "Crystals", Amount = 100 } (a fixed amount, RewardService) or
            { Kind = "CrystalBundle", Seconds = 600 } (minutes of the player's own income, RobuxPerks).
 * Active   false switches a code off (it then reads as expired).
 * Expires  optional, "YYYY-MM-DD": the code works until the end of that day, UTC.

Each player can redeem each code once (their save's Codes list). A reward that can't apply right
now is refused and the code is NOT used up, so it still works later.

Example:
	{ Code = "RELEASE", Reward = { Kind = "<kind>", Amount = 100 }, Active = true, Expires = "2027-01-31" },
]]
return {
	-- Our picks (the doc asks for a launch code and a tutorial-completion code; names and amounts are
	-- starting values). Crystals rewards are registered by Economy.
	Codes = {
		{ Code = "THAWED", Reward = { Kind = "Crystals", Amount = 250 }, Active = true }, -- shown when the tutorial is done
		{ Code = "ICELAUNCH", Reward = { Kind = "Crystals", Amount = 500 }, Active = true }, -- the launch code
		-- Milestone codes for likes (docs/GAME_DESIGN.md, "Social and events"). Off until the game reaches
		-- the milestone: then set Active = true, publish, and announce the code (docs/LAUNCH_CHECKLIST.md).
		-- Each pays minutes of the player's own income (the CrystalBundle reward kind), so it is worth the
		-- same at every stage of the game.
		{ Code = "LIKES1K", Reward = { Kind = "CrystalBundle", Seconds = 300 }, Active = false }, -- 1,000 likes
		{ Code = "LIKES5K", Reward = { Kind = "CrystalBundle", Seconds = 600 }, Active = false }, -- 5,000 likes
		{ Code = "LIKES10K", Reward = { Kind = "CrystalBundle", Seconds = 900 }, Active = false }, -- 10,000 likes
		{ Code = "LIKES25K", Reward = { Kind = "CrystalBundle", Seconds = 1200 }, Active = false }, -- 25,000 likes
		{ Code = "LIKES50K", Reward = { Kind = "CrystalBundle", Seconds = 1800 }, Active = false }, -- 50,000 likes
		{ Code = "LIKES100K", Reward = { Kind = "CrystalBundle", Seconds = 3600 }, Active = false }, -- 100,000 likes
	},

	-- Attempts per player: at least MinSeconds apart, and at most PerMinute in any minute (stops
	-- guessing codes by trying thousands).
	RateLimit = { MinSeconds = 1, PerMinute = 6 },
}
