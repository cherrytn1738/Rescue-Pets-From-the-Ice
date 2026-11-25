-- Short number text: 1200 -> "1.2K", 2500000 -> "2.5M"; Money adds "$" ("$1.2K"). (Change the
-- symbol, or add a function for the game's own currency, once the design names it.)
local NumberFormat = {}

-- The design's suffixes ("Technical design": K, M, B, T, Qa, Qi, Sx, Sp, Oc, No, Dc, then Ud ... Tg, 1e93).
-- Ice block HP outgrows Dc (1e33) around level 200, so the list goes on; past Tg a number shows as "1.82e96".
local SUFFIXES = {
	"", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc",
	"Ud", "Dd", "Td", "Qad", "Qid", "Sxd", "Spd", "Ocd", "Nod", "Vg",
	"Uvg", "Dvg", "Tvg", "Qavg", "Qivg", "Sxvg", "Spvg", "Ocvg", "Novg", "Tg",
}

function NumberFormat.Short(value: number): string
	if value ~= value or math.abs(value) == math.huge then
		return "0"
	end
	value = math.floor(value)
	if math.abs(value) < 1000 then
		return tostring(value)
	end
	if math.abs(value) >= 1000 ^ #SUFFIXES then
		local text = string.format("%.2e", value) -- 1.82e+96
		return (string.gsub(string.gsub(text, "e%+?0*", "e"), "%.?0+e", "e"))
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
