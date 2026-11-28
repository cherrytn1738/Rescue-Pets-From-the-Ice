-- Game-wide settings shared by the server and clients (docs/GAME_DESIGN.md, "Technical design").
return {
	Version = 1,
	GameName = "Rescue Pets From the Ice",

	-- Tapping: the client counts taps and sends the total every BatchSeconds; the server allows up to
	-- MaxPerSecond (a short burst of up to BurstSeconds' worth is allowed, then the rate) and quietly ignores
	-- the rest (Auto Pick's taps count inside the same cap). Faster clicking helps up to the cap, not past it.
	Taps = {
		BatchSeconds = 0.25,
		MaxPerSecond = 10,
		BurstSeconds = 1,
		RateWindowSeconds = 5, -- the HUD's crystals/s counts taps over this window
	},

	-- The PLOT button (the HUD; GoHome): the server moves you to your plot's tapping spot, facing your ice block, at most
	-- once every CooldownSeconds. It first streams your plot in around the spot (waiting at most StreamSeconds), so you
	-- never land in an empty area. Everyone within PoofRange studs sees the snow poof where you leave and arrive.
	Teleport = { CooldownSeconds = 3, StreamSeconds = 3, PoofRange = 150 },

	-- The server tick: building damage, block HP and crystals, this many times a second.
	TicksPerSecond = 4,

	-- The Golden Glacier rush (docs/GAME_DESIGN.md, "Social and events"): every 5-8 minutes a golden
	-- block falls into the plaza after a countdown. Everyone who taps it before it breaks gets a Frost
	-- Rush (x3 crystals for 60 s); whoever tapped it most gets x5. Our starting values: its HP is
	-- TapsPerPlayer taps for each player in the server, and it melts (no rush) if nobody breaks it in
	-- ActiveSeconds. Taps count only within Radius studs of it.
	GoldenGlacier = {
		MinSeconds = 300,
		MaxSeconds = 480,
		CountdownSeconds = 10,
		ActiveSeconds = 60,
		TapsPerPlayer = 100,
		RushSeconds = 60,
		RushMultiplier = 3,
		TopMultiplier = 5,
		Radius = 40,
	},

	-- The daily crystal chest: once a UTC day, IncomeSeconds of the player's crystals per second (at
	-- least Minimum). Our starting values; the doc names the chest, not the amount.
	Daily = { IncomeSeconds = 300, Minimum = 100 },

	-- The group reward: members of the game's group earn +10% crystals.
	Group = { Id = 921449746, Bonus = 0.10 },

	-- The plaza leaderboards (OrderedDataStore). Crystals are stored as floor(log10(total) * 1000)
	-- (OrderedDataStore holds whole numbers up to about 9e18); rebirths and rescues as they are. Studio
	-- uses its own boards. Written and read every RefreshSeconds.
	Leaderboards = {
		RefreshSeconds = 120,
		Top = 10,
		Boards = {
			{ Id = "Crystals", Title = "All-time crystals", Field = "CrystalsAllTime", Log = true },
			{ Id = "Rebirths", Title = "Rebirths", Field = "Rebirths" },
			{ Id = "Rescued", Title = "Creatures rescued", Field = "CreaturesRescued" },
		},
	},
}
