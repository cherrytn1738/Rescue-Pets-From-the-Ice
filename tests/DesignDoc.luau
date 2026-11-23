--[[
DesignDoc (tests only): reads the tables in docs/GAME_DESIGN.md, so the config specs can check the
config modules against the doc itself rather than a copy of its numbers. The spec runner passes the
doc as sources["GAME_DESIGN.md"].

  local DesignDoc = loadstring(sources.DesignDoc)()
  local doc = DesignDoc.new(sources["GAME_DESIGN.md"])
  local rows = doc:Table({ "Building", "How it breaks the ice" })   -- the table whose header starts so
  rows[1]["Base cost (crystals)"]   -- a cell, by header text
  DesignDoc.Number("1.6M")          -- 1600000; "1,300" -> 1300; "75%" -> 75; "× 50" -> 50; "–" -> nil
]]
local DesignDoc = {}
DesignDoc.__index = DesignDoc

local function trim(text: string): string
	return (string.gsub(text, "^%s*(.-)%s*$", "%1"))
end

local function cells(line: string)
	local inner = string.match(line, "^%s*|(.*)|%s*$")
	if not inner then
		return nil
	end
	local list = {}
	for cell in string.gmatch(inner .. "|", "(.-)|") do
		table.insert(list, trim(cell))
	end
	return list
end

function DesignDoc.new(text: string)
	assert(type(text) == "string" and #text > 0, "docs/GAME_DESIGN.md is missing from sources (run the specs with tools/run_specs.py)")
	local self = setmetatable({ tables = {} }, DesignDoc)
	local current = nil
	for line in string.gmatch(text .. "\n", "(.-)\r?\n") do
		local row = cells(line)
		if row then
			if not current then
				current = { header = row, rows = {} }
				table.insert(self.tables, current)
			elseif not string.match(row[1], "^%-+$") then
				local named = {}
				for index, header in current.header do
					named[header] = row[index]
					named[index] = row[index]
				end
				table.insert(current.rows, named)
			end
		else
			current = nil
		end
	end
	return self
end

-- The rows of the one table whose header begins with these cells. Errors if there isn't exactly one.
function DesignDoc:Table(headerStart)
	local found = nil
	for _, candidate in self.tables do
		local matches = true
		for index, text in headerStart do
			if candidate.header[index] ~= text then
				matches = false
				break
			end
		end
		if matches then
			assert(found == nil, "two tables in the design doc start with " .. table.concat(headerStart, " | "))
			found = candidate
		end
	end
	assert(found, "no table in the design doc starts with " .. table.concat(headerStart, " | "))
	return found.rows
end

local SUFFIXES = { K = 1e3, M = 1e6, B = 1e9, T = 1e12 }

-- The number in a cell: "1,300", "1.6M", "75%", "+10%", "× 5,000", "0.5%". nil for "–" and words.
function DesignDoc.Number(text: string?): number?
	if text == nil then
		return nil
	end
	local digits, suffix = string.match(text, "(%d[%d,]*%.?%d*)%s*([KMBT]?)")
	if not digits then
		return nil
	end
	local value = tonumber((string.gsub(digits, ",", "")))
	if value and suffix ~= "" then
		value *= SUFFIXES[suffix]
	end
	return value
end

-- Same as Number, but for cells that may hold a range ("1–10"): both ends.
function DesignDoc.Range(text: string): (number?, number?)
	local low, high = string.match(text, "^(%d+)%D+(%d+)$") -- (the dash is a multi-byte en dash)
	return tonumber(low), tonumber(high)
end

-- "Fresh Snow" -> "FreshSnow"; "Arctic Fox Kit" -> "ArcticFoxKit".
function DesignDoc.IdOf(name: string): string
	return (string.gsub(name, "[^%w]", ""))
end

return DesignDoc
