--[[
ShopService: buying buildings and upgrades with crystals (docs/GAME_DESIGN.md, "Economy" and
"Upgrades in detail"). Server only. The client only asks; the server works out every price with
EconomyRules and checks every unlock rule.

  BuyBuilding (RemoteFunction): (buildingId, amount) with amount 1, 10, 100 or "Max"
  BuyUpgrade  (RemoteFunction): (upgradeId)
Both answer { ok, message, count? } and fire GameEvent "Built" / "Upgraded" to the buyer (the station
puff and the card flash). Requests are limited to a few a second.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local BuildingConfig = require(ReplicatedStorage.BuildingConfig)
local EconomyRules = require(ReplicatedStorage.EconomyRules)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local UpgradeConfig = require(ReplicatedStorage.UpgradeConfig)
local Economy = require(script.Parent.Economy)
local PlayerData = require(script.Parent.PlayerData)
local PlotService = require(script.Parent.PlotService)

local ShopService = {}

local AMOUNTS = { [1] = true, [10] = true, [100] = true, Max = true }
local REQUEST_GAP = 0.1
local lastRequest = {}
local buyListeners = {}

local gameEvent

-- callback(player, data, kind ("Building" | "Upgrade"), id, count) after every purchase.
function ShopService.OnBought(callback)
	table.insert(buyListeners, callback)
end

local function tooFast(player: Player): boolean
	local now = os.clock()
	if lastRequest[player] and now - lastRequest[player] < REQUEST_GAP then
		return true
	end
	lastRequest[player] = now
	return false
end

local function bought(player, data, kind, id, count)
	PlayerData.Publish(player)
	PlayerData.MarkImportant(player)
	for _, callback in buyListeners do
		task.spawn(callback, player, data, kind, id, count)
	end
end

function ShopService.BuyBuilding(player: Player, buildingId, amount)
	if tooFast(player) then
		return { ok = false, message = "Slow down a little." }
	end
	if type(buildingId) ~= "string" or not BuildingConfig.Get(buildingId) or not AMOUNTS[amount] then
		return { ok = false, message = "Unknown building." }
	end
	local data = PlayerData.Edit(player)
	if not data then
		return { ok = false, message = "Your data isn't ready yet." }
	end
	local building = BuildingConfig.Get(buildingId)
	local count, cost = EconomyRules.BuildingPurchase(data, buildingId, amount)
	if not Economy.Spend(data, cost) then
		return { ok = false, message = `Not enough crystals ({NumberFormat.Short(cost)} needed).` }
	end
	local first = (data.Buildings[buildingId] or 0) == 0
	data.Buildings[buildingId] = (data.Buildings[buildingId] or 0) + count
	PlotService.RefreshBuildings(player, data)
	gameEvent:FireClient(player, "Built", { BuildingId = buildingId, Count = count, Owned = data.Buildings[buildingId], First = first })
	bought(player, data, "Building", buildingId, count)
	return { ok = true, message = `Built {count} {building.Name}!`, count = count }
end

function ShopService.BuyUpgrade(player: Player, upgradeId)
	if tooFast(player) then
		return { ok = false, message = "Slow down a little." }
	end
	if type(upgradeId) ~= "string" or not UpgradeConfig.Get(upgradeId) then
		return { ok = false, message = "Unknown upgrade." }
	end
	local data = PlayerData.Edit(player)
	if not data then
		return { ok = false, message = "Your data isn't ready yet." }
	end
	local upgrade = UpgradeConfig.Get(upgradeId)
	local unlocked, reason = EconomyRules.UpgradeUnlocked(data, upgradeId)
	if not unlocked then
		return { ok = false, message = reason }
	end
	if not Economy.Spend(data, upgrade.Cost) then
		return { ok = false, message = `Not enough crystals ({NumberFormat.Short(upgrade.Cost)} needed).` }
	end
	table.insert(data.Upgrades, upgradeId)
	if upgrade.Kind == "Building" then
		PlotService.RefreshBuildings(player, data)
	end
	gameEvent:FireClient(player, "Upgraded", { UpgradeId = upgradeId })
	bought(player, data, "Upgrade", upgradeId, 1)
	return { ok = true, message = `{upgrade.Name} bought!` }
end

function ShopService.Start()
	gameEvent = ReplicatedStorage:WaitForChild("GameEvent")
	ReplicatedStorage:WaitForChild("BuyBuilding").OnServerInvoke = ShopService.BuyBuilding
	ReplicatedStorage:WaitForChild("BuyUpgrade").OnServerInvoke = ShopService.BuyUpgrade
	PlayerData.OnLoaded(function(player, data)
		-- the plot is assigned when the data loads (IceBlockService); wait for it, then draw
		for _ = 1, 40 do
			if PlotService.IndexOf(player) then
				break
			end
			task.wait(0.1)
		end
		PlotService.RefreshBuildings(player, data)
	end)
	Players.PlayerRemoving:Connect(function(player)
		lastRequest[player] = nil
	end)
end

return ShopService
