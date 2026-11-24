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

-- The ShopVisit RemoteEvent (the Robux shop window says it opened, closed, or an INFO was tapped).
AnalyticsConfig.VisitRate = { MinSeconds = 0.2, PerMinute = 40 }

-- The step number of an onboarding step's Key.
AnalyticsConfig.OnboardingStep = {}
for number, step in AnalyticsConfig.Onboarding do
	AnalyticsConfig.OnboardingStep[step.Key] = number
end

return AnalyticsConfig
