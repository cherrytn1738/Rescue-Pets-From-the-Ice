-- The "While you were away" popup: what the player earned while they were offline, and how long they
-- were gone, in the showcase look. The server already paid it (OfflineEarnings); this only shows the
-- player's OfflineEarnings attribute ({ Amount, Seconds, Capped, Label, At } as JSON). Nothing shows
-- until the game has something that earns offline.
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local NumberFormat = require(ReplicatedStorage.NumberFormat)
local OfflineEarningsRules = require(ReplicatedStorage.OfflineEarningsRules)
local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)

local localPlayer = Players.LocalPlayer
local Colors = UIKit.Colors
local COUNT_UP_SECONDS = 0.9
local icons = UIKit.Theme.Icons or {}

local awayLine, amountLabel, capLine, okButton

local window = ShowcaseKit.Window("OfflineEarningsWindow", "While You Were Away", {
	cornerIcon = icons.OfflineEarnings, -- (no picture until this game uploads its own icons)
	width = 600,
	height = 340,
	onLayout = function(width, height)
		local compact = height < 240
		awayLine.Position, awayLine.Size = UDim2.fromOffset(0, 6), UDim2.fromOffset(width, 30)
		amountLabel.Position, amountLabel.Size = UDim2.fromOffset(0, 42), UDim2.fromOffset(width, if compact then 64 else 86)
		local below = if compact then 110 else 136
		capLine.Position, capLine.Size = UDim2.fromOffset(0, below), UDim2.fromOffset(width, 24)
		okButton.Position = UDim2.fromOffset(width / 2, height - 66)
		okButton.Size = UDim2.fromOffset(math.min(240, width), 62)
	end,
})
local content = window.content

awayLine = UIKit.Label(content, "Away", "", 26, Colors.Muted)
awayLine.TextXAlignment = Enum.TextXAlignment.Center
amountLabel = UIKit.Label(content, "Amount", "", 80, Colors.Gold)
amountLabel.TextXAlignment = Enum.TextXAlignment.Center
capLine = UIKit.Label(content, "Cap", "", 20, Colors.Muted)
capLine.TextXAlignment = Enum.TextXAlignment.Center
okButton = UIKit.Button(content, "CollectButton", "NICE!", "Go", 34)
okButton.AnchorPoint = Vector2.new(0.5, 0)
okButton.Activated:Connect(window.Close)

-- Counts the amount up (ease-out), then a small pop.
local countVersion = 0
local function countUp(total: number, label: string)
	countVersion += 1
	local version = countVersion
	local started = os.clock()
	local suffix = if label ~= "" then " " .. label else ""
	task.spawn(function()
		while version == countVersion do
			local t = math.min(1, (os.clock() - started) / COUNT_UP_SECONDS)
			local eased = 1 - (1 - t) ^ 3
			amountLabel.Text = "+" .. NumberFormat.Short(total * eased) .. suffix
			if t >= 1 then
				break
			end
			task.wait()
		end
		if version == countVersion then
			amountLabel.TextSize = 92
			TweenService:Create(amountLabel, TweenInfo.new(0.25, Enum.EasingStyle.Back), { TextSize = 80 }):Play()
		end
	end)
end

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
	local label = if type(info.Label) == "string" then info.Label else ""
	awayLine.Text = `You were away for {OfflineEarningsRules.Describe(seconds)}. You earned:`
	capLine.Text = if info.Capped
		then `You earn for up to {OfflineEarningsRules.Describe(OfflineEarningsRules.Settings.CapSeconds)} while you're away.`
		else ""
	amountLabel.Text = "+0"
	task.wait(1) -- let the join settle (the HUD appears first)
	window.Open()
	UIKit.PlaySound("Reward")
	countUp(info.Amount, label)
end

localPlayer:GetAttributeChangedSignal("OfflineEarnings"):Connect(show)
task.spawn(show)
