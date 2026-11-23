--[[
AnalyticsRules: which funnel steps to log now, so each step is logged once and in order. Pure
functions (no services), used by src/server/Analytics.luau and PlayerData, tested by
tests/Analytics.spec.luau.

A player's saved progress (PlayerData, `Funnels`):
  { Onboarding = steps logged (0..#steps), Waiting = { step numbers reached but not logged yet } }
A shop visit lives only in memory: { Id = funnel session id, Step = steps logged, Open, Prompted = { [key] = true } }.
]]
local AnalyticsRules = {}

local function isInteger(value, min, max): boolean
	return type(value) == "number" and value == value and value % 1 == 0 and value >= min and value <= max
end

-- A new player's progress: nothing logged yet.
function AnalyticsRules.New()
	return { Onboarding = 0, Waiting = {} }
end

-- A saved value, cleaned. Analytics isn't worth failing a load over: a value that can't be read
-- counts as done (nothing more is logged for it).
function AnalyticsRules.Clean(saved, onboardingSteps: number)
	if type(saved) ~= "table" then
		return { Onboarding = onboardingSteps, Waiting = {} }
	end
	local state = AnalyticsRules.New()
	state.Onboarding = if isInteger(saved.Onboarding, 0, onboardingSteps) then saved.Onboarding else onboardingSteps
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
function AnalyticsRules.IsClean(saved, onboardingSteps: number): boolean
	if type(saved) ~= "table" or not isInteger(saved.Onboarding, 0, onboardingSteps) or type(saved.Waiting) ~= "table" then
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

return AnalyticsRules
