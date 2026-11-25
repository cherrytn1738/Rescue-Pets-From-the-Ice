--[[
RobuxShop: the shop window's requests, and the startup price check. Server only.

Clients never open Robux prompts themselves. The shop sends an intent on the PurchaseRequest
RemoteFunction; the server checks it, prepares what the receipt will need, and opens Roblox's prompt:
  ("BuyPass", passKey)                 a game pass the player doesn't own yet
  ("Buy", productKey)                  a developer product for themselves
  ("Gift", itemKey, recipientId)       a product or a pass for another player in this server (Gifting.Prepare)
-> { ok, message } for the window's feedback line. The client never sends a price, an amount or an
id. Nothing here grants anything: receipts do (Receipts), and pass ownership (GamePasses).

An item without a real id is never prompted. In Studio it runs a SIMULATED purchase instead
(Receipts.Simulate / a Studio pass override), so the whole flow can be tried before the item is
created on the Creator Hub.
]]
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Analytics = require(script.Parent.Analytics)
local GamePasses = require(script.Parent.GamePasses)
local Gifting = require(script.Parent.Gifting)
local PaidRandomPolicy = require(script.Parent.PaidRandomPolicy)
local PlayerData = require(script.Parent.PlayerData)
local PurchaseRewards = require(script.Parent.PurchaseRewards)
local Receipts = require(script.Parent.Receipts)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local MonetizationRules = require(ReplicatedStorage.MonetizationRules)

local RobuxShop = {}

local REQUEST_COOLDOWN = 0.5 -- requests closer together than this are refused
local PROMPT_SECONDS = 30 -- an open prompt blocks the next request until it closes, or this long
local SECONDS_BETWEEN_PRICE_LOOKUPS = 0.25

local lastRequest = {} -- [player] = os.clock()
local lastGiftAt = {} -- [player] = os.clock() their last gift prompt opened
local promptOpenUntil = {} -- [player] = os.clock() when the open-prompt lock ends

local function reply(ok: boolean, message: string)
	return { ok = ok, message = message }
end

local function simulatedNote(decision): string
	return if decision == Enum.ProductPurchaseDecision.PurchaseGranted then "Studio: simulated purchase granted (no id yet)" else "Studio: simulated purchase NOT granted (see Output)"
end

local actions = {}

function actions.BuyPass(player: Player, passKey)
	local pass = MonetizationConfig.GetPass(passKey)
	if not pass then
		return reply(false, "Unknown item")
	end
	if GamePasses.Owns(player, pass.Key) then
		return reply(false, `You already own {pass.Name}.`)
	end
	if not MonetizationConfig.IsLive(pass) then
		if RunService:IsStudio() then
			GamePasses.SetStudioOverride(player, pass.Key, true)
			Analytics.RobuxPrompted(player, pass.Key)
			Analytics.RobuxPurchased(player, pass.Key)
			print(`[Purchase] SIMULATED {player.Name} bought the {pass.Name} pass (Studio, no id yet)`)
			return reply(true, `Studio: {pass.Name} given for this session (no pass id yet)`)
		end
		return reply(false, "That isn't on sale yet.")
	end
	promptOpenUntil[player] = os.clock() + PROMPT_SECONDS
	MarketplaceService:PromptGamePassPurchase(player, pass.Id)
	Analytics.RobuxPrompted(player, pass.Key)
	return reply(true, "")
end

function actions.Buy(player: Player, productKey)
	local product = MonetizationConfig.GetProduct(productKey)
	if not product then
		return reply(false, "Unknown item")
	end
	-- Don't take Robux for something that can't apply right now.
	local ok, problem = PurchaseRewards.CanGive(player, product)
	if not ok then
		return reply(false, problem or "You can't buy that right now.")
	end
	if not MonetizationConfig.IsLive(product) then
		if RunService:IsStudio() then
			local decision, note = Receipts.Simulate(player, product)
			Analytics.RobuxPrompted(player, product.Key)
			if decision == Enum.ProductPurchaseDecision.PurchaseGranted then
				Analytics.RobuxPurchased(player, product.Key)
			end
			return reply(decision == Enum.ProductPurchaseDecision.PurchaseGranted, `{simulatedNote(decision)}: {note}`)
		end
		return reply(false, "That isn't on sale yet.")
	end
	promptOpenUntil[player] = os.clock() + PROMPT_SECONDS
	MarketplaceService:PromptProductPurchase(player, product.Id)
	Analytics.RobuxPrompted(player, product.Key)
	return reply(true, "")
end

function actions.Gift(player: Player, productKey, recipientId)
	local product = MonetizationConfig.GetGiftable(productKey) -- a product, or a pass
	if not product or type(recipientId) ~= "number" or recipientId % 1 ~= 0 then
		return reply(false, "Pick a player to gift to.")
	end
	if MonetizationConfig.IsPaidRandom(product) and not PaidRandomPolicy.IsAllowed(player) then
		return reply(false, PaidRandomPolicy.REFUSED)
	end
	local simulate = not MonetizationConfig.IsGiftLive(product)
	if simulate and not RunService:IsStudio() then
		return reply(false, "Gifting that isn't on sale yet.")
	end
	if not MonetizationRules.GiftRequestReady(lastGiftAt[player], os.clock()) then
		return reply(false, "Wait a moment before starting another gift.")
	end
	promptOpenUntil[player] = os.clock() + PROMPT_SECONDS
	local ok, message = Gifting.Prepare(player, product, Players:GetPlayerByUserId(recipientId))
	if not ok then
		promptOpenUntil[player] = nil
		return reply(false, message or "The gift couldn't be started.")
	end
	lastGiftAt[player] = os.clock()
	if simulate then
		promptOpenUntil[player] = nil
		Gifting.PromptFinished(player, product, true)
		local decision, note = Receipts.Simulate(player, product, { gift = true })
		Analytics.RobuxPrompted(player, product.Key)
		if decision == Enum.ProductPurchaseDecision.PurchaseGranted then
			Analytics.RobuxPurchased(player, product.Key)
		end
		return reply(decision == Enum.ProductPurchaseDecision.PurchaseGranted, `{simulatedNote(decision)}: {note}`)
	end
	if player.Parent == Players then
		MarketplaceService:PromptProductPurchase(player, product.GiftId)
		Analytics.RobuxPrompted(player, product.Key)
	end
	return reply(true, "")
end

local function onRequest(player: Player, action, key, extra)
	local handler = type(action) == "string" and actions[action]
	if not handler or type(key) ~= "string" or #key > 32 then
		return reply(false, "Unknown request")
	end
	local now = os.clock()
	if now - (lastRequest[player] or -math.huge) < REQUEST_COOLDOWN then
		return reply(false, "Too fast")
	end
	lastRequest[player] = now
	if now < (promptOpenUntil[player] or -math.huge) then
		return reply(false, "Finish the purchase window that's open first.")
	end
	if not PlayerData.IsReady(player) then
		return reply(false, "Your data is still loading.")
	end
	return handler(player, key, extra)
end

-- Roblox charges the Creator Hub price, not the config's. At server start this asks Roblox about
-- every configured id and warns about a wrong id, an item that isn't for sale, or a price that
-- differs from ExpectedPrice. It only reads and warns; nothing waits for it.
local function priceCheck()
	local entries, hidden = MonetizationConfig.AllPriced()
	local problems = 0
	for _, entry in entries do
		local infoType = if entry.InfoType == "GamePass" then Enum.InfoType.GamePass else Enum.InfoType.Product
		local ok, info = pcall(MarketplaceService.GetProductInfo, MarketplaceService, entry.Id, infoType)
		local problem
		if not ok or typeof(info) ~= "table" then
			problem = `id {entry.Id} was not found as a {entry.InfoType} ({tostring(info)})`
		elseif info.IsForSale == false or type(info.PriceInRobux) ~= "number" then
			problem = "is not for sale on the Creator Hub"
		elseif info.PriceInRobux ~= entry.ExpectedPrice then
			problem = `costs {info.PriceInRobux} Robux on the Creator Hub, but MonetizationConfig expects {entry.ExpectedPrice}`
		end
		if problem then
			problems += 1
			warn(`[PriceCheck] {entry.Label}: {problem}`)
		end
		task.wait(SECONDS_BETWEEN_PRICE_LOOKUPS)
	end
	local summary = `[PriceCheck] {#entries} items checked, {problems} problems, {hidden} hidden (no id yet)`
	if problems > 0 then
		warn(summary)
	else
		print(summary)
	end
end

function RobuxShop.Start()
	local remote = ReplicatedStorage:WaitForChild("PurchaseRequest") :: RemoteFunction
	remote.OnServerInvoke = onRequest

	-- Prompt results. Never grant here: only receipts (and pass ownership) grant.
	MarketplaceService.PromptProductPurchaseFinished:Connect(function(userId, productId, purchased)
		local player = Players:GetPlayerByUserId(userId)
		if not player then
			return
		end
		promptOpenUntil[player] = nil
		local kind, product = MonetizationConfig.FindByProductId(productId)
		if purchased and product then
			Analytics.RobuxPurchased(player, product.Key)
		end
		if kind == "Gift" then
			Gifting.PromptFinished(player, product, purchased)
		end
	end)
	MarketplaceService.PromptGamePassPurchaseFinished:Connect(function(player, gamePassId, purchased)
		promptOpenUntil[player] = nil -- GamePasses handles the purchase itself
		local pass = purchased and MonetizationConfig.GetPassById(gamePassId)
		if pass then
			Analytics.RobuxPurchased(player, pass.Key)
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		lastRequest[player], promptOpenUntil[player], lastGiftAt[player] = nil, nil, nil
	end)
	task.spawn(priceCheck)
end

return RobuxShop
