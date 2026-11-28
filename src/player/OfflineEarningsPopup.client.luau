-- The Welcome Back screen (docs/GAME_DESIGN.md, "Screens"): pictures more than words. A clock with a snowflake over
-- the corner, a huge "Welcome Back!", one short line, a big crystal pile with slowly turning rays behind it, the amount
-- in big gold numbers counting up, the time away; a rainbow x2 button (Double Welcome Back, with its Robux price) and
-- a big green Claim!. The server already paid the crystals (OfflineEarnings); this shows the player's OfflineEarnings
-- attribute ({ Amount, Seconds, Capped, Label, At } as JSON). x2 shows while the WelcomeBackOffer attribute
-- ({ Amount, Until }) says the offer is open; buying it goes through the shop's request (PurchaseRequest "Buy"), and
-- the server pays the saved amount once (WelcomeBack). Claim! closes the offer (PurchaseRequest "CloseOffer").
local ContentProvider = game:GetService("ContentProvider")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local OfflineEarningsRules = require(ReplicatedStorage.OfflineEarningsRules)
local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)
local PriceCache = require(script.Parent.PriceCache)

local localPlayer = Players.LocalPlayer
local purchaseRequest = ReplicatedStorage:WaitForChild("PurchaseRequest") :: RemoteFunction
local Colors = UIKit.Colors
local PRODUCT = MonetizationConfig.GetProduct("DoubleWelcomeBack")
local COUNT_UP_SECONDS = 0.9
local GOLD_RAYS = Color3.fromRGB(255, 214, 90)

local subtitle, burst, pile, amountLabel, awayLabel, doubleButton, claimButton, robuxBadge, setPrice, feedback
local amount, label = 0, "crystals"
local offer = nil -- { Amount, Until } while x2 can be bought
local buying, doubled = false, false
local waiting = false -- Roblox's purchase prompt is open (the server hides the offer meanwhile)
local waitVersion = 0
local spin = nil

local window
window = ShowcaseKit.Window("OfflineEarningsWindow", "Welcome Back!", {
	cornerIcon = UIKit.IconImage("WelcomeClock"),
	width = 720,
	height = 560,
	-- gamepad: start on Claim!, never on the purchase
	firstSelection = function()
		return claimButton
	end,
	onLayout = function(width, height)
		local compact = height < 360
		local lineHeight = if compact then 26 else 32
		local amountHeight = if compact then 50 else 68
		local awayHeight = if compact then 20 else 26
		local buttonHeight = if compact then 58 else 72
		subtitle.Position, subtitle.Size = UDim2.fromOffset(0, 0), UDim2.fromOffset(width, lineHeight)
		local buttonsTop = height - buttonHeight
		local awayTop = buttonsTop - (if compact then 30 else 34) - awayHeight -- (clear of the price badge on x2)
		local amountTop = awayTop - amountHeight
		awayLabel.Position, awayLabel.Size = UDim2.fromOffset(0, awayTop), UDim2.fromOffset(width, awayHeight)
		amountLabel.Position, amountLabel.Size = UDim2.fromOffset(width / 2, amountTop + amountHeight / 2), UDim2.fromOffset(width, amountHeight)
		-- the crystal pile fills the space between the line and the amount
		local zoneTop = lineHeight + 4
		local zone = math.max(60, amountTop - zoneTop)
		local size = math.min(zone, if compact then 130 else 200)
		pile.Position, pile.Size = UDim2.fromOffset(width / 2, zoneTop + zone / 2), UDim2.fromOffset(size, size)
		burst.Position, burst.Size = pile.Position, UDim2.fromOffset(size * 2.1, size * 2.1)
		-- the buttons: x2 and Claim! side by side (Claim! alone, centred, without an offer)
		local showDouble = doubleButton.Visible
		local claimWidth = math.min(if showDouble then 230 else 280, width * 0.4)
		local doubleWidth = math.min(330, width * 0.52)
		local gap = 26
		if showDouble then
			local total = doubleWidth + gap + claimWidth
			local left = (width - total) / 2
			doubleButton.Position, doubleButton.Size = UDim2.fromOffset(left + doubleWidth / 2, buttonsTop + buttonHeight / 2), UDim2.fromOffset(doubleWidth, buttonHeight)
			claimButton.Position = UDim2.fromOffset(left + doubleWidth + gap + claimWidth / 2, buttonsTop + buttonHeight / 2)
		else
			claimButton.Position = UDim2.fromOffset(width / 2, buttonsTop + buttonHeight / 2)
		end
		claimButton.Size = UDim2.fromOffset(claimWidth, buttonHeight)
		feedback.Position, feedback.Size = UDim2.fromOffset(0, buttonsTop - 26), UDim2.fromOffset(width, 24)
	end,
	onClose = function()
		if spin then
			spin:Cancel()
			spin = nil
		end
		-- closing without buying (Claim!, X or B) closes the offer on the server
		if offer and not doubled and not buying then
			task.spawn(function()
				pcall(function()
					purchaseRequest:InvokeServer("CloseOffer", PRODUCT.Key)
				end)
			end)
		end
		offer = nil
	end,
})
local content = window.content

subtitle = UIKit.Label(content, "Subtitle", "Your buildings broke ice while you were away:", 28)
subtitle.TextXAlignment = Enum.TextXAlignment.Center
UIKit.FitOneLine(subtitle, 28)

burst = ShowcaseKit.Picture(content, "Rays", "Sunburst")
burst.ImageColor3 = GOLD_RAYS
burst.ImageTransparency = 0.25
burst.ZIndex = 1
pile = ShowcaseKit.Picture(content, "CrystalPile", "CrystalPile")
pile.ZIndex = 3

amountLabel = UIKit.Label(content, "Amount", "", 72, Colors.Gold)
amountLabel.AnchorPoint = Vector2.new(0.5, 0.5)
amountLabel.TextXAlignment = Enum.TextXAlignment.Center
amountLabel.ZIndex = 4
UIKit.FitOneLine(amountLabel, 72)
awayLabel = UIKit.Label(content, "Away", "", 24, Colors.Muted)
awayLabel.TextXAlignment = Enum.TextXAlignment.Center
UIKit.FitOneLine(awayLabel, 24)
feedback = UIKit.Label(content, "Feedback", "", 20, Colors.Error)
feedback.TextXAlignment = Enum.TextXAlignment.Center

doubleButton = UIKit.Button(content, "DoubleButton", "", "Gold", 40)
doubleButton.AnchorPoint = Vector2.new(0.5, 0.5)
ShowcaseKit.Rainbow(doubleButton)
robuxBadge, setPrice = ShowcaseKit.RobuxBadge(doubleButton.Visual)
robuxBadge.AnchorPoint = Vector2.new(1, 0.5)
robuxBadge.Position = UDim2.new(1, 18, 0, 4)
robuxBadge.Rotation = 6
robuxBadge.ZIndex = 6
for _, item in robuxBadge:GetDescendants() do
	if item:IsA("GuiObject") then
		item.ZIndex = 7
	end
end
claimButton = UIKit.Button(content, "ClaimButton", "Claim!", "Buy", 40)
claimButton.AnchorPoint = Vector2.new(0.5, 0.5)

local function amountText(value: number): string
	return "+" .. NumberFormat.Short(value) .. (if label ~= "" then " " .. string.upper(label) else "")
end

-- Counts the amount up from `from` to `to` (ease-out), then a small pop.
local countVersion = 0
local function countUp(from: number, to: number)
	countVersion += 1
	local version = countVersion
	local started = os.clock()
	task.spawn(function()
		while version == countVersion do
			local t = math.min(1, (os.clock() - started) / COUNT_UP_SECONDS)
			local eased = 1 - (1 - t) ^ 3
			amountLabel.Text = amountText(from + (to - from) * eased)
			if t >= 1 then
				break
			end
			task.wait()
		end
		if version == countVersion then
			ShowcaseKit.PopIn(amountLabel, 0, 1.25)
		end
	end)
end

local function offerOpen(): boolean
	return offer ~= nil and not doubled and Workspace:GetServerTimeNow() < offer.Until
end

local function refreshOffer()
	local show = PRODUCT ~= nil and not doubled and (waiting or offerOpen())
	if doubleButton.Visible ~= show then
		doubleButton.Visible = show
		if window.IsOpen() then
			window.Layout() -- (Claim! moves to the centre, or back beside x2)
		end
	end
	if show then
		local busy = buying or waiting or offer == nil
		UIKit.SetButton(doubleButton, if busy then "..." else "x2  +" .. NumberFormat.Short(offer.Amount * 2), nil, not busy)
	end
end

local function readOffer()
	local raw = localPlayer:GetAttribute("WelcomeBackOffer")
	offer = nil
	if type(raw) == "string" then
		local ok, view = pcall(HttpService.JSONDecode, HttpService, raw)
		if ok and type(view) == "table" and type(view.Amount) == "number" and type(view.Until) == "number" then
			offer = view
		end
	end
end

if PRODUCT then
	setPrice(PRODUCT.ExpectedPrice)
	if MonetizationConfig.IsLive(PRODUCT) then
		setPrice(PriceCache.Get(PRODUCT.Id, Enum.InfoType.Product, PRODUCT.ExpectedPrice, setPrice))
	end
end

doubleButton.Activated:Connect(function()
	if buying or not offerOpen() or not doubleButton.Active then
		return
	end
	buying = true
	feedback.Text = ""
	refreshOffer()
	local ok, reply = pcall(function()
		return purchaseRequest:InvokeServer("Buy", PRODUCT.Key)
	end)
	buying = false
	if not ok or type(reply) ~= "table" or not reply.ok then
		feedback.Text = if ok and type(reply) == "table" then tostring(reply.message) else "Try again in a moment."
	elseif not doubled then
		-- the prompt is open: "..." until it's bought (PurchaseNotice) or closed (the offer comes back), at most 60 s
		waiting = true
		waitVersion += 1
		local version = waitVersion
		task.delay(60, function()
			if version == waitVersion and waiting then
				waiting = false
				refreshOffer()
			end
		end)
	end
	refreshOffer()
end)
claimButton.Activated:Connect(function()
	window.Close()
end)

-- The x2 arrived (the receipt was granted): count up to double, then close.
ReplicatedStorage:WaitForChild("PurchaseNotice").OnClientEvent:Connect(function(payload)
	if type(payload) ~= "table" or payload.Kind ~= "Purchased" or not PRODUCT or payload.Item ~= PRODUCT.Name then
		return
	end
	doubled = true
	doubleButton.Visible = false
	if window.IsOpen() then
		UIKit.PlaySound("Reward")
		countUp(amount, amount * 2)
		ShowcaseKit.PopIn(pile, 0, 0.6)
		UIKit.SetButton(claimButton, "Claim!", "Buy", true)
		task.delay(2.2, function()
			if window.IsOpen() then
				window.Close()
			end
		end)
	end
end)
localPlayer:GetAttributeChangedSignal("WelcomeBackOffer"):Connect(function()
	readOffer()
	if offer then
		waiting = false -- (the prompt closed without buying: x2 is back)
	end
	refreshOffer()
end)

local lastShown = nil
local function show()
	local raw = localPlayer:GetAttribute("OfflineEarnings")
	if type(raw) ~= "string" or raw == lastShown then
		return
	end
	local ok, info = pcall(HttpService.JSONDecode, HttpService, raw)
	if not ok or type(info) ~= "table" or type(info.Amount) ~= "number" or info.Amount <= 0 then
		return
	end
	lastShown = raw
	local seconds = tonumber(info.Seconds) or 0
	amount = info.Amount
	label = if type(info.Label) == "string" then info.Label else ""
	doubled, buying, waiting = false, false, false
	feedback.Text = ""
	awayLabel.Text = `Away for {OfflineEarningsRules.Describe(seconds)}` .. (if info.Capped then ` (earns up to {OfflineEarningsRules.Describe(OfflineEarningsRules.Settings.CapSeconds / OfflineEarningsRules.Settings.Rate)})` else "")
	amountLabel.Text = "+0"
	-- let the join settle (the HUD appears first) while the screen's pictures load (at most a few seconds)
	local corner = window.panel:FindFirstChild("CornerIcon")
	local loaded = false
	task.spawn(function()
		pcall(function()
			ContentProvider:PreloadAsync({ pile, burst, corner, doubleButton, claimButton })
		end)
		loaded = true
	end)
	local waited = os.clock()
	task.wait(1)
	while not loaded and os.clock() - waited < 3 do
		task.wait(0.1)
	end
	readOffer()
	refreshOffer()
	window.Open()
	UIKit.PlaySound("Reward")
	-- the pop-in: the clock, the pile and its rays, the number, the buttons
	if corner then
		ShowcaseKit.PopIn(corner, 0.05, 0.2)
	end
	ShowcaseKit.PopIn(pile, 0.1)
	ShowcaseKit.PopIn(burst, 0.1, 0.5)
	ShowcaseKit.PopIn(doubleButton, 0.35)
	ShowcaseKit.PopIn(claimButton, 0.45)
	burst.Rotation = 0
	spin = TweenService:Create(burst, TweenInfo.new(24, Enum.EasingStyle.Linear, Enum.EasingDirection.In, -1), { Rotation = 360 })
	spin:Play()
	countUp(0, amount)
	-- the offer ends while the screen is open: x2 goes
	task.spawn(function()
		while window.IsOpen() do
			refreshOffer()
			task.wait(1)
		end
	end)
end

localPlayer:GetAttributeChangedSignal("OfflineEarnings"):Connect(show)
task.spawn(show)
