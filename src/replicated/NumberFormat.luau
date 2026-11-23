-- Short number text: 1200 -> "1.2K", 2500000 -> "2.5M"; Money adds "$" ("$1.2K"). (Change the
-- symbol, or add a function for the game's own currency, once the design names it.)
local NumberFormat = {}

-- The design's suffixes ("Technical design": K, M, B, T, Qa, Qi, Sx, Sp, Oc, No, Dc).
local SUFFIXES = { "", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc" }

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

-- A rate or a small amount with one decimal below 100 ("0.4", "12.5"), else Short.
function NumberFormat.Rate(value: number): string
	if math.abs(value) < 100 then
		local text = string.format("%.1f", value)
		return (string.gsub(text, "%.0$", ""))
	end
	return NumberFormat.Short(value)
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
