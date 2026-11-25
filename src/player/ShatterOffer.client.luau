-- The Shatter Now offer (docs/GAME_DESIGN.md, "Monetization" and "Gameplay view"): a button on the right edge
-- while a block stands on your mound and you're in your own plot. It shows bigger, gold and gently pulsing
-- when a Rare or better creature is inside (the glowing blocks are when it sells). Pressing it asks the
-- server to buy the ShatterNow product (PurchaseRequest); the server checks everything and the receipt
-- breaks the block. Hidden in a live game until the product has a real id.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local MapConfig = require(ReplicatedStorage.MapConfig)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local UIKit = require(ReplicatedStorage.UIKit)
local Banners = require(script.Parent.Banners)
local PriceCache = require(script.Parent.PriceCache)

local PRODUCT = MonetizationConfig.GetProduct("ShatterNow")
local BIG_FROM = "Rare" -- this rarity and rarer: the big offer
local player = Players.LocalPlayer
local remote = ReplicatedStorage:WaitForChild("PurchaseRequest") :: RemoteFunction

if not PRODUCT or (not RunService:IsStudio() and not MonetizationConfig.IsLive(PRODUCT)) then
	return
end

local rarityRank = {}
for index, rarity in CreatureConfig.Rarities do
	rarityRank[rarity.Id] = index
end

local _, root = UIKit.Screen("ShatterOffer", 6)
local holder = Instance.new("Frame")
holder.Name = "Offer"
holder.BackgroundTransparency = 1
holder.AnchorPoint = Vector2.new(1, 0.5)
holder.Position = UDim2.new(1, -14, 0.62, 0)
holder.Size = UDim2.fromOffset(210, 74)
holder.Visible = false
holder.Parent = root
local scale = Instance.new("UIScale")
scale.Parent = holder
local button = UIKit.Button(holder, "ShatterNowButton", "SHATTER NOW", "Neutral", 24)
button.Size = UDim2.fromScale(1, 1)

local big = nil -- (nil: the button's text and colour need setting)
local price = PRODUCT.ExpectedPrice
local function priceText(): string
	return `SHATTER NOW\nR$ {price}`
end
if MonetizationConfig.IsLive(PRODUCT) then
	price = PriceCache.Get(PRODUCT.Id, Enum.InfoType.Product, PRODUCT.ExpectedPrice, function(live)
		price = live
		big = nil
	end)
end

local function inOwnPlot(index: number?): boolean
	local character = player.Character
	local rootPart = character and character:FindFirstChild("HumanoidRootPart")
	if type(index) ~= "number" or not rootPart then
		return false
	end
	local at = MapConfig.PlotCFrame(index):PointToObjectSpace(rootPart.Position)
	local half = MapConfig.PlotSize / 2 + MapConfig.TapMargin
	return math.abs(at.X) <= half and math.abs(at.Z) <= half
end

local busy = false
button.Activated:Connect(function()
	if busy then
		return
	end
	busy = true
	local ok, reply = pcall(function()
		return remote:InvokeServer("Buy", PRODUCT.Key)
	end)
	busy = false
	if not ok or type(reply) ~= "table" then
		Banners.Toast("The server didn't answer. Try again.", Color3.fromRGB(255, 120, 120))
	elseif not reply.ok and reply.message and reply.message ~= "" then
		Banners.Toast(reply.message, Color3.fromRGB(255, 120, 120))
	end
end)

RunService.RenderStepped:Connect(function()
	local index = player:GetAttribute("PlotIndex")
	local plots = Workspace:FindFirstChild("Plots")
	local plot = if type(index) == "number" and plots then plots:FindFirstChild("Plot" .. index) else nil
	local block = if plot then plot:FindFirstChild("Block") else nil
	-- (typeof: an error "index boolean" was seen twice at join in a streaming test; never index a non-Instance)
	local present = typeof(block) == "Instance" and block:GetAttribute("Present") == true
	holder.Visible = present and inOwnPlot(index) and not UIKit.AnyWindowOpen()
	if not holder.Visible then
		return
	end
	local rank = rarityRank[block:GetAttribute("Rarity") or ""] or 1
	local nowBig = rank >= rarityRank[BIG_FROM]
	if nowBig ~= big then
		big = nowBig
		UIKit.SetButton(button, priceText(), if big then "Gold" else "Neutral")
	end
	local pulse = if big then 1 + 0.04 * math.sin(os.clock() * 4) else 1
	scale.Scale = UIKit.HudScale() * (if big then 1.35 else 1) * pulse
end)
