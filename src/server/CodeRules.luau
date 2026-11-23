--[[
CodeRules: promo code rules on plain values (tests/Codes.spec.luau). CodeService reads the player's
save and the clock, asks these, and grants through PurchaseRewards.

(Copied from Steal Pets. Its "codes only work after the tutorial" rule is gone: this game has no
tutorial yet. If one is added, put the check back into Check and CodeService.)
]]
local CodeRules = {}

CodeRules.MaxLength = 32

-- What a typed code becomes: spaces trimmed, upper case. nil for nothing, too long, or anything but
-- letters and digits (so a saved code is always this form; PlayerData checks the same pattern).
function CodeRules.Normalize(text): string?
	if type(text) ~= "string" then
		return nil
	end
	local trimmed = string.upper((string.gsub(text, "^%s+", ""):gsub("%s+$", "")))
	if trimmed == "" or #trimmed > CodeRules.MaxLength or not string.match(trimmed, "^[A-Z0-9]+$") then
		return nil
	end
	return trimmed
end

-- "YYYY-MM-DD" -> the last second of that day, UTC (os.time). nil for no expiry; errors on a date it
-- can't read (a config mistake should fail in Studio, not let a code run forever).
function CodeRules.ExpiresAt(text: string?): number?
	if text == nil then
		return nil
	end
	local year, month, day = string.match(tostring(text), "^(%d%d%d%d)%-(%d%d)%-(%d%d)$")
	assert(year, "a code's Expires must be YYYY-MM-DD, got " .. tostring(text))
	local start = DateTime.fromUniversalTime(tonumber(year), tonumber(month), tonumber(day), 0, 0, 0)
	return start.UnixTimestamp + 86400 - 1
end

-- The config's code for this normalized text, or nil.
function CodeRules.Find(config, code: string?)
	if code == nil then
		return nil
	end
	for _, entry in config.Codes do
		if CodeRules.Normalize(entry.Code) == code then
			return entry
		end
	end
	return nil
end

-- Can this player redeem this code now? Returns true, or false and a reason:
-- Unknown (no such code), Expired (past its date, or switched off), Used (already redeemed).
-- redeemed: the player's saved Codes; now: os.time().
function CodeRules.Check(entry, code: string?, redeemed, now: number): (boolean, string?)
	if entry == nil or code == nil then
		return false, "Unknown"
	end
	if entry.Active ~= true then
		return false, "Expired"
	end
	local expiresAt = CodeRules.ExpiresAt(entry.Expires)
	if expiresAt and now > expiresAt then
		return false, "Expired"
	end
	if table.find(redeemed, code) then
		return false, "Used"
	end
	return true, nil
end

-- Rate limit: history is this player's recent attempt times (os.clock), oldest first. Returns
-- whether one more attempt is allowed now, and records it if so.
function CodeRules.AllowAttempt(history, now: number, limit): boolean
	while history[1] and now - history[1] >= 60 do
		table.remove(history, 1)
	end
	local last = history[#history]
	if (last and now - last < limit.MinSeconds) or #history >= limit.PerMinute then
		return false
	end
	table.insert(history, now)
	return true
end

-- The message a player sees for each refusal.
CodeRules.Messages = {
	Empty = "Type a code first.",
	Unknown = "That code doesn't exist. Check the spelling.",
	Expired = "That code has expired.",
	Used = "You already redeemed that code.",
	TooFast = "Too many tries. Wait a moment, then try again.",
	DataNotReady = "Your data is still loading.",
}

-- Load-time check of a code list: every code readable, no two the same once normalized, every
-- expiry date readable.
function CodeRules.Validate(config)
	local seen = {}
	for _, entry in config.Codes do
		local code = CodeRules.Normalize(entry.Code)
		assert(code, "unreadable code " .. tostring(entry.Code))
		assert(not seen[code], "code listed twice: " .. code)
		seen[code] = true
		assert(type(entry.Reward) == "table", code .. " has no reward")
		CodeRules.ExpiresAt(entry.Expires)
	end
end

return CodeRules
