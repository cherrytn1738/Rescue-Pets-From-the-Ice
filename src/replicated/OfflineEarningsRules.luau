--[[
OfflineEarningsRules: what a player earned while they were away. Pure functions, so
tests/OfflineEarnings.spec.luau can run every case; the server (OfflineEarnings) applies them, the
popup (OfflineEarningsPopup.client) only shows the result.

Time comes from the server's clock only: PlayerData saves os.time() as LeftAt with every save (the
final save on leaving, or the last autosave before a crash), and the next join compares it with
os.time(). A time that can't be read, or one later than now, pays nothing.

What earns, and how much per second, is up to the game (OfflineEarnings.SetEarner). These rules
only turn "income per second" and "seconds away" into an amount, with the rate and the cap below.
]]
local OfflineEarningsRules = {}

-- The tuning (docs/GAME_DESIGN.md, "Technical design": building income only, at 50%, capped at 2 hours).
--  Rate        the share of normal income earned while away (0.5 = half).
--  CapSeconds  each income source earns for at most this many seconds of its own income: 2 hours
--              away at 50% is 3,600 seconds of income, so the time away stops counting after 2 hours.
OfflineEarningsRules.Settings = {
	Rate = 0.5,
	CapSeconds = 3600,
}

local function isWholePositive(value): boolean
	return type(value) == "number" and value == value and value > 0 and value < math.huge and value % 1 == 0
end

-- A saved LeftAt as it may be trusted: a whole number of seconds after 1970, or nil.
function OfflineEarningsRules.CleanLeftAt(value): number?
	return if isWholePositive(value) then value else nil
end

-- Seconds between leaving (the saved server time) and now; 0 when leftAt can't be read, or when the
-- gap is negative (a clock that went back, or a time in the future).
function OfflineEarningsRules.SecondsAway(leftAt, now): number
	if not isWholePositive(leftAt) or type(now) ~= "number" or now ~= now or now == math.huge then
		return 0
	end
	return math.max(0, math.floor(now - leftAt))
end

-- What one income source earned: Rate x its income for the time away, at most CapSeconds of its own
-- income.
function OfflineEarningsRules.Earnings(incomePerSecond: number, secondsAway: number, settings): number
	if type(incomePerSecond) ~= "number" or incomePerSecond ~= incomePerSecond or incomePerSecond <= 0 or incomePerSecond == math.huge then
		return 0
	end
	if type(secondsAway) ~= "number" or secondsAway ~= secondsAway or secondsAway <= 0 then
		return 0
	end
	return incomePerSecond * math.min(secondsAway * settings.Rate, settings.CapSeconds)
end

-- Every source's earnings. sources: { { key, income } }. Returns { [key] = amount } (sources that
-- earned something) and the total. Each source is capped on its own.
function OfflineEarningsRules.Plan(sources, secondsAway: number, settings)
	local amounts, total = {}, 0
	for _, source in sources do
		local amount = OfflineEarningsRules.Earnings(source.income, secondsAway, settings)
		if amount > 0 then
			amounts[source.key] = amount
			total += amount
		end
	end
	return amounts, total
end

-- Whether earning stopped before the player came back (the popup says so).
function OfflineEarningsRules.IsCapped(secondsAway: number, settings): boolean
	return secondsAway * settings.Rate > settings.CapSeconds
end

-- "45s", "6m 46s", "3h 12m", "2d 5h".
function OfflineEarningsRules.Describe(seconds: number): string
	seconds = math.max(0, math.floor(seconds))
	if seconds < 60 then
		return `{seconds}s`
	elseif seconds < 3600 then
		local minutes, rest = seconds // 60, seconds % 60
		return if rest > 0 then `{minutes}m {rest}s` else `{minutes}m`
	elseif seconds < 86400 then
		local hours, minutes = seconds // 3600, (seconds % 3600) // 60
		return if minutes > 0 then `{hours}h {minutes}m` else `{hours}h`
	end
	local days, hours = seconds // 86400, (seconds % 86400) // 3600
	return if hours > 0 then `{days}d {hours}h` else `{days}d`
end

return OfflineEarningsRules
