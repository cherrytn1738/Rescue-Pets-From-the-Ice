--[[
AnalyticsConfig: every funnel the game sends to Roblox's analytics (AnalyticsService), in one place.
Only the server sends them (src/server/Analytics.luau); events only record in a published game, so
Studio sends nothing and prints `[Analytics]` lines instead.

NEVER rename a step or a funnel, or reorder steps, once the game is live: the Creator Hub charts are
keyed by funnel name and step number, and a rename splits a chart in two. Add new steps at the end.

Roblox counts a step as reached when that step OR ANY LATER ONE is logged (a later step completes the
earlier ones), so the server only ever logs a funnel's steps in order (AnalyticsRules).

  Onboarding  one-time, per player (LogOnboardingFunnelStepEvent). A step reached early waits until
              every step before it is logged.
  Shops       recurring, one funnel session (a GUID) per visit to the shop (LogFunnelStepEvent).

Nothing personal is sent: the player object (which Roblox needs), step numbers and these names.
]]
local AnalyticsConfig = {}

-- The onboarding funnel: EMPTY until the game's first-session steps are designed
-- (docs/GAME_DESIGN.md). Step numbers are the list order. Each step:
--   { Key = "Joined", Name = "Joined" }   Key: what code passes to Analytics.Onboarding;
--                                         Name: what the Creator Hub chart shows (short, stable).
-- A step with Key "Joined" is logged by Analytics itself when a player's data loads; the game logs
-- every other step with Analytics.Onboarding(player, key).
-- The game's first-session funnel (docs/GAME_DESIGN.md, "Technical design": Joined, First tap, First
-- building, First rescue, First pet equipped, Tutorial done, First rebirth).
AnalyticsConfig.Onboarding = {
	{ Key = "Joined", Name = "Joined" },
	{ Key = "FirstTap", Name = "First tap" },
	{ Key = "FirstBuilding", Name = "First building" },
	{ Key = "FirstRescue", Name = "First rescue" },
	{ Key = "FirstPetEquipped", Name = "First pet equipped" },
	{ Key = "TutorialDone", Name = "Tutorial done" },
	{ Key = "FirstRebirth", Name = "First rebirth" },
}

AnalyticsConfig.Shops = {
	-- The Robux shop window (SHOP button). Step 2 is a tap on an item's INFO button, or its buy
	-- button (which opens its card's purchase); step 3 is Roblox's purchase prompt opening from this
	-- visit; step 4 is the prompt closing with a purchase.
	Robux = {
		Funnel = "RobuxShop",
		Steps = { "Opened shop", "Viewed item", "Prompt shown", "Purchased" },
	},
}

-- Progression: two one-time funnels (each step logged once per player, ever), sent with the recurring
-- funnel API under one funnel session per player (a random id kept in the save, `Funnels.ProgressId`;
-- never the user id). Two funnels, not one, because layers and rebirth ranks don't come in a fixed
-- order against each other (layer 5 can come before or after rank 3), and a funnel step completes
-- every step before it. Layer steps are LayerConfig layer numbers 1-6; rank steps are the rebirth
-- counts of the ranks in `Ranks` (RebirthConfig.Ranks: rank 1 is the first rebirth).
AnalyticsConfig.Progression = {
	Layers = {
		Funnel = "LayersReached",
		Steps = { "Layer 1 Fresh Snow", "Layer 2 Blue Ice", "Layer 3 Ancient Ice", "Layer 4 Crystal Ice", "Layer 5 Primordial Ice", "Layer 6 Frozen Core" },
	},
	Ranks = {
		Funnel = "RebirthRanks",
		Rebirths = { 1, 3, 6, 10 },
		Steps = { "Rank 1 Ice Breaker", "Rank 3 Glacier Diver", "Rank 6 Core Keeper", "Rank 10 Glacier Legend" },
	},
}

-- Economy events: every crystal earned and spent (LogEconomyEvent, currency "Crystals"). Steady
-- flows (taps, buildings, rescues, the rush share) are added up per player and sent every
-- FlushSeconds (and when the player leaves or the server closes), so a player costs about one event a
-- minute; one-off flows (daily chest, codes, offline, bundles, upgrades) are sent at once.
-- Each source: TransactionType (Roblox's Enum.AnalyticsEconomyTransactionType name, or a custom one)
-- and Sku (the item column on the Creator Hub; a source with Sku = nil passes its own: a code, a
-- product key, a building id). NEVER rename a currency, source Sku or transaction type once live.
AnalyticsConfig.Economy = {
	Currency = "Crystals",
	FlushSeconds = 300,
	Sources = {
		Taps = { TransactionType = "Gameplay", Sku = "Taps", Batched = true },
		AutoPick = { TransactionType = "Gameplay", Sku = "AutoPick", Batched = true },
		Buildings = { TransactionType = "Gameplay", Sku = "Buildings", Batched = true },
		Rescue = { TransactionType = "Gameplay", Sku = "Rescue", Batched = true },
		-- the extra crystals a rush adds to taps, buildings and rescues (the part above x1)
		GoldenGlacier = { TransactionType = "Gameplay", Sku = "GoldenGlacierRush", Batched = true },
		ServerFrostRush = { TransactionType = "IAP", Sku = "ServerFrostRush", Batched = true },
		DailyChest = { TransactionType = "TimedReward", Sku = "DailyChest" },
		Offline = { TransactionType = "TimedReward", Sku = "Offline" },
		Code = { TransactionType = "Code" }, -- Sku: the code
		Bundle = { TransactionType = "IAP" }, -- Sku: the product key (CrystalPouch, ...)
		Debug = nil, -- (debug-menu crystals are never sent)
	},
	Sinks = {
		Building = { TransactionType = "Shop", Batched = true }, -- Sku: the building id
		Upgrade = { TransactionType = "Shop" }, -- Sku: the upgrade id
	},
}

-- Custom events (LogCustomEvent). NEVER rename one once live.
AnalyticsConfig.Custom = {
	GlacierJoined = "GoldenGlacierJoined", -- a player's first tap on a Golden Glacier (value 1)
	GlacierWon = "GoldenGlacierWon", -- the glacier broke: each tapper's rush multiplier is the value;
	-- CustomField01 "Place - Top" (most damage) or "Place - Helper"
	GlacierEscaped = "GoldenGlacierEscaped", -- it melted away unbroken: value = players who tapped it
}

-- The ShopVisit RemoteEvent (the Robux shop window says it opened, closed, or an INFO was tapped).
AnalyticsConfig.VisitRate = { MinSeconds = 0.2, PerMinute = 40 }

-- The step number of an onboarding step's Key.
AnalyticsConfig.OnboardingStep = {}
for number, step in AnalyticsConfig.Onboarding do
	AnalyticsConfig.OnboardingStep[step.Key] = number
end

return AnalyticsConfig
