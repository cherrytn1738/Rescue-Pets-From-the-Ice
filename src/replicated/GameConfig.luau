-- Game-wide settings shared by the server and clients (docs/GAME_DESIGN.md, "Technical design").
return {
	Version = 1,
	GameName = "Rescue Pets From the Ice",

	-- Tapping: the client counts taps and sends the total every BatchSeconds; the server allows up to
	-- MaxPerSecond (a short burst of up to BurstSeconds' worth is allowed, then the rate) and logs a
	-- player who keeps going over (at most once every OverLimitLogSeconds).
	Taps = {
		BatchSeconds = 0.25,
		MaxPerSecond = 20,
		BurstSeconds = 1,
		OverLimitLogSeconds = 30,
		RateWindowSeconds = 5, -- the HUD's crystals/s counts taps over this window
	},

	-- The server tick: building damage, block HP and crystals, this many times a second.
	TicksPerSecond = 4,
}
