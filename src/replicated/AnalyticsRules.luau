--[[
AnalyticsRules: which funnel steps to log now, so each step is logged once and in order. Pure
functions (no services), used by src/server/Analytics.luau and PlayerData, tested by
tests/Analytics.spec.luau.

A player's saved progress (PlayerData, `Funnels`):
  { Onboarding = steps logged (0..#steps), Waiting = { step numbers reached but not logged yet },
    Layers = layer funnel steps logged, Ranks = rank funnel steps logged,
    ProgressId = the player's progression funnel session id (a random GUID; absent until first used) }
`progress` below is the progression funnels' step counts: { Layers = n, Ranks = n }.
A shop visit lives only in memory: { Id = funnel session id, Step = steps logged, Open, Prompted = { [key] = true } }.
]]
local AnalyticsRules = {}

local function isInteger(value, min, max): boolean
	return type(value) == "number" and value == value and value % 1 == 0 and value >= min and value <= max
end

-- A new player's progress: nothing logged yet.
function AnalyticsRules.New()
	return { Onboarding = 0, Waiting = {}, Layers = 0, Ranks = 0 }
end

local NO_PROGRESS = { Layers = 0, Ranks = 0 }

-- A saved value, cleaned. Analytics isn't worth failing a load over: a value that can't be read
-- counts as done (nothing more is logged for it).
-- A progression count that is missing (a save from before the progression funnels) starts at 0.
function AnalyticsRules.Clean(saved, onboardingSteps: number, progress)
	progress = progress or NO_PROGRESS
	if type(saved) ~= "table" then
		return { Onboarding = onboardingSteps, Waiting = {}, Layers = progress.Layers, Ranks = progress.Ranks }
	end
	local state = AnalyticsRules.New()
	state.Onboarding = if isInteger(saved.Onboarding, 0, onboardingSteps) then saved.Onboarding else onboardingSteps
	for _, funnel in { "Layers", "Ranks" } do
		local value = saved[funnel]
		state[funnel] = if value == nil then 0 elseif isInteger(value, 0, progress[funnel]) then value else progress[funnel]
	end
	if type(saved.ProgressId) == "string" and #saved.ProgressId > 0 and #saved.ProgressId <= 64 then
		state.ProgressId = saved.ProgressId
	end
	local seen = {}
	for _, step in (if type(saved.Waiting) == "table" then saved.Waiting else {}) do
		if isInteger(step, state.Onboarding + 1, onboardingSteps) and not seen[step] then
			seen[step] = true
			table.insert(state.Waiting, step)
		end
	end
	table.sort(state.Waiting)
	return state
end

-- Whether a saved value is already clean (PlayerData's check before each save).
function AnalyticsRules.IsClean(saved, onboardingSteps: number, progress): boolean
	progress = progress or NO_PROGRESS
	if type(saved) ~= "table" or not isInteger(saved.Onboarding, 0, onboardingSteps) or type(saved.Waiting) ~= "table" then
		return false
	end
	if not isInteger(saved.Layers, 0, progress.Layers) or not isInteger(saved.Ranks, 0, progress.Ranks) then
		return false
	end
	if saved.ProgressId ~= nil and (type(saved.ProgressId) ~= "string" or #saved.ProgressId == 0 or #saved.ProgressId > 64) then
		return false
	end
	for _, step in saved.Waiting do
		if not isInteger(step, saved.Onboarding + 1, onboardingSteps) then
			return false
		end
	end
	return true
end

-- Whether onboarding `step` has been reached (logged, or waiting for an earlier step).
function AnalyticsRules.Reached(state, step: number): boolean
	return step <= state.Onboarding or table.find(state.Waiting, step) ~= nil
end

-- The player reached onboarding `step`. Returns the steps to log now, in order: none if it was
-- reached before; this one and any waiting after it once every earlier step is logged; otherwise it
-- waits.
function AnalyticsRules.Reach(state, step: number, onboardingSteps: number): { number }
	if not isInteger(step, 1, onboardingSteps) or AnalyticsRules.Reached(state, step) then
		return {}
	end
	table.insert(state.Waiting, step)
	table.sort(state.Waiting)
	local toLog = {}
	while state.Waiting[1] == state.Onboarding + 1 do
		state.Onboarding += 1
		table.remove(state.Waiting, 1)
		table.insert(toLog, state.Onboarding)
	end
	return toLog
end

-- Shop visits ------------------------------------------------------------------------------------

-- A new visit (step 1, "Opened shop", is logged at once): returns the visit and { 1 }.
function AnalyticsRules.NewVisit(sessionId: string)
	return { Id = sessionId, Step = 1, Open = true, Prompted = {} }, { 1 }
end

-- The visit reached `step`. Returns the steps to log, in order: the ones between the last logged
-- and this one are filled in (a buy press opens the item's card), each step once per visit.
function AnalyticsRules.VisitStep(visit, step: number, stepCount: number): { number }
	if not visit or not isInteger(step, 1, stepCount) or step <= visit.Step then
		return {}
	end
	local toLog = {}
	for number = visit.Step + 1, step do
		table.insert(toLog, number)
	end
	visit.Step = step
	return toLog
end

-- Progression ------------------------------------------------------------------------------------

-- A progression funnel: `logged` steps are logged and the player has now reached step `reached`.
-- Returns the steps to log now, in order (each once; any skipped in between are filled in), and the
-- new logged count.
function AnalyticsRules.ProgressSteps(logged: number, reached: number, stepCount: number): ({ number }, number)
	local toLog = {}
	if not isInteger(reached, 1, math.huge) then
		return toLog, logged
	end
	for step = logged + 1, math.min(reached, stepCount) do
		table.insert(toLog, step)
	end
	return toLog, math.max(logged, math.min(reached, stepCount))
end

-- The rank funnel step reached with this many rebirths (0 before the first rank).
function AnalyticsRules.RankStep(rebirths: number, rankRebirths: { number }): number
	local step = 0
	for index, needed in rankRebirths do
		if type(rebirths) == "number" and rebirths >= needed then
			step = index
		end
	end
	return step
end

-- Economy ------------------------------------------------------------------------------------------

-- How much of a boosted grant each running rush added. rushes: { { Source, Multiplier } } (only those
-- above 1). With every rush together multiplying by M, a grant of A holds A * (1 - 1/M) of rush
-- crystals, split between the rushes by their share of log(M) (exact for multiplying rushes). Returns
-- { { Source, Share } } with the shares as fractions of the grant.
function AnalyticsRules.RushShares(rushes)
	local total, logSum = 1, 0
	for _, rush in rushes do
		total *= rush.Multiplier
		logSum += math.log(rush.Multiplier)
	end
	local shares = {}
	if total <= 1 or logSum <= 0 then
		return shares
	end
	local rushFraction = 1 - 1 / total
	for _, rush in rushes do
		table.insert(shares, { Source = rush.Source, Share = rushFraction * math.log(rush.Multiplier) / logSum })
	end
	return shares
end

return AnalyticsRules
