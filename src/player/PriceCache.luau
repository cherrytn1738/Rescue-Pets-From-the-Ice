-- PriceCache (client): price buttons show Roblox's price, because Roblox charges the price set on
-- the Creator Hub, not the one in MonetizationConfig. Each price is looked up once per session and
-- cached; until it arrives (or if the lookup fails) the config's ExpectedPrice is shown.
--   show(PriceCache.Get(id, Enum.InfoType.Product, product.ExpectedPrice, show))
-- Enum.InfoType.Product for developer products (gift products too), Enum.InfoType.GamePass for
-- passes. Only for items with a real id.
local MarketplaceService = game:GetService("MarketplaceService")

local PriceCache = {}

local prices = {} -- ["Product:123"] = Robux
local waiting = {} -- ["Product:123"] = { callbacks } while its lookup runs

-- Returns the live price if known, else `fallback`; onLoaded(price) runs once if it arrives later.
function PriceCache.Get(id: number, infoType: Enum.InfoType, fallback: number, onLoaded: ((number) -> ())?): number
	local key = infoType.Name .. ":" .. tostring(id)
	if prices[key] then
		return prices[key]
	end
	if waiting[key] then
		if onLoaded then
			table.insert(waiting[key], onLoaded)
		end
		return fallback
	end
	waiting[key] = { onLoaded }
	task.spawn(function()
		local ok, info = pcall(MarketplaceService.GetProductInfo, MarketplaceService, id, infoType)
		local callbacks = waiting[key]
		waiting[key] = nil
		if ok and typeof(info) == "table" and type(info.PriceInRobux) == "number" then
			prices[key] = info.PriceInRobux
			for _, callback in callbacks do
				task.spawn(callback, info.PriceInRobux)
			end
		end
		-- On failure nothing is cached, so the next Get tries again.
	end)
	return fallback
end

return PriceCache
