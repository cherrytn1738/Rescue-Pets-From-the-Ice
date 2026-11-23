-- Short number text: 1200 -> "1.2K", 2500000 -> "2.5M"; Money adds "$" ("$1.2K"). (Change the
-- symbol, or add a function for the game's own currency, once the design names it.)
local NumberFormat = {}

local SUFFIXES = { "", "K", "M", "B", "T", "Qa", "Qi" }

function NumberFormat.Short(value: number): string
	value = math.floor(value)
	if math.abs(value) < 1000 then
		return tostring(value)
	end

	local index = 1
	while math.abs(value) >= 1000 and index < #SUFFIXES do
		value /= 1000
		index += 1
	end

	local text
	if math.abs(value) >= 100 then
		text = string.format("%.0f", value)
	elseif math.abs(value) >= 10 then
		text = string.format("%.1f", value)
	else
		text = string.format("%.2f", value)
	end
	if text:find("%.") then
		text = (text:gsub("0+$", ""))
		text = (text:gsub("%.$", ""))
	end
	return text .. SUFFIXES[index]
end

function NumberFormat.Money(value: number): string
	return "$" .. NumberFormat.Short(value)
end

-- Two decimals once abbreviated, for the HUD's cash counter: 186910 -> "$186.91K",
-- 2500000000000 -> "$2.5T" (trailing zeros dropped), 950 -> "$950".
function NumberFormat.MoneyPrecise(value: number): string
	value = math.floor(value)
	if math.abs(value) < 1000 then
		return "$" .. tostring(value)
	end
	local index = 1
	while math.abs(value) >= 1000 and index < #SUFFIXES do
		value /= 1000
		index += 1
	end
	local text = string.format("%.2f", math.floor(value * 100) / 100) -- never rounds up past the real amount
	text = (text:gsub("0+$", ""))
	text = (text:gsub("%.$", ""))
	return "$" .. text .. SUFFIXES[index]
end

return NumberFormat
