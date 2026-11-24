--[[
LeaderboardRules: how the plaza leaderboards store and show values (docs/GAME_DESIGN.md, "Technical
design"). OrderedDataStore keeps whole numbers up to about 9e18, so a crystal total is stored as
floor(log10(total) * 1000) and shown back as about 10^(stored / 1000). Counts (rebirths, rescues) are
stored as they are.
]]
local LeaderboardRules = {}

function LeaderboardRules.Encode(value: number, log: boolean?): number
	if type(value) ~= "number" or value ~= value or value < 1 then
		return 0
	end
	if log then
		return math.floor(math.log10(value) * 1000)
	end
	return math.floor(math.min(value, 9e18))
end

function LeaderboardRules.Decode(stored: number, log: boolean?): number
	if log then
		return if stored > 0 then 10 ^ (stored / 1000) else 0
	end
	return stored
end

-- The store's name: Studio keeps its own boards, so tests never touch the live ones.
function LeaderboardRules.StoreName(boardId: string, isStudio: boolean): string
	return "IcePets_Board_" .. boardId .. (if isStudio then "_Studio" else "")
end

return LeaderboardRules
