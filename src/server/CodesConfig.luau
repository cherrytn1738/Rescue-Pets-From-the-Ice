--[[
CodesConfig: the promo codes players can redeem in the Codes window. Server only, on purpose: a code
listed here never reaches a player's computer until they type it, so codes can be added before they
are announced.

Each code:
 * Code     the text players type. Not case-sensitive, letters and digits only (CodeRules.Normalize).
 * Reward   what it gives: the same reward table a Robux product uses, granted through
            PurchaseRewards (the reward kinds it knows are listed there; this game has none yet,
            so a code can't give anything until the game adds its first reward kind).
            Example once a kind exists: { Kind = "<kind>", Amount = 100 }
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
	},

	-- Attempts per player: at least MinSeconds apart, and at most PerMinute in any minute (stops
	-- guessing codes by trying thousands).
	RateLimit = { MinSeconds = 1, PerMinute = 6 },
}
