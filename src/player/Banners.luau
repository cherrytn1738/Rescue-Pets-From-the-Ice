--[[
Banners (client): the big moments on screen, in the house style (UIKit labels).
  Banners.Big(title, subtitle, color, seconds?, decorate?)   a big centre banner (rarity reveal, new layer, new tool),
                                                  one at a time; decorate(frame) adds something to it while it shows
                                                  (the new tool turning) and returns its clean-up
  Banners.Toast(text, color?)                     a short line at the top (announcements, notices)
  Banners.Hold() / Banners.Release()              another big moment is on screen (the Book card): banners and
                                                  toasts wait until it's released
  Banners.HoldToasts() / Banners.ReleaseToasts()  only the toasts wait (the Book card waiting for the rescue
                                                  banner to finish: the order is banner, card, toasts)
  Banners.Busy()                                  a big banner is showing or waiting
One thing at a time, so each is readable: a toast that arrives while a big banner (or a held moment) is on screen
waits for it to finish (a Legendary rescue's banner and the server's "X freed a Legendary" toast used to overlap).
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local UIKit = require(ReplicatedStorage.UIKit)

local Banners = {}

local _, root = UIKit.Screen("Banners", 30)
local queue = {}
local showing = false
local holds = 0
local toastHolds = 0
local waitingToasts = {} -- toasts that arrived while something big was on screen
local showToast

local bigFrame = Instance.new("Frame")
bigFrame.Name = "Big"
bigFrame.BackgroundTransparency = 1
bigFrame.AnchorPoint = Vector2.new(0.5, 0.5)
bigFrame.Position = UDim2.fromScale(0.5, 0.34)
bigFrame.Size = UDim2.fromOffset(900, 190)
bigFrame.Visible = false
bigFrame.Parent = root
local bigScale = Instance.new("UIScale")
bigScale.Parent = bigFrame
local title = UIKit.Label(bigFrame, "Title", "", 84)
title.Size = UDim2.new(1, 0, 0, 100)
title.TextXAlignment = Enum.TextXAlignment.Center
title.TextScaled = true
local subtitle = UIKit.Label(bigFrame, "Subtitle", "", 40)
subtitle.Position = UDim2.fromOffset(0, 104)
subtitle.Size = UDim2.new(1, 0, 0, 56)
subtitle.TextXAlignment = Enum.TextXAlignment.Center
subtitle.TextScaled = true

local function flushToasts()
	if showing or holds > 0 or toastHolds > 0 then
		return
	end
	for _, toast in waitingToasts do
		showToast(toast.text, toast.color)
	end
	table.clear(waitingToasts)
end

local function nextBig()
	if holds > 0 then
		showing = false
		return -- (Release picks the queue up again)
	end
	local item = table.remove(queue, 1)
	if not item then
		showing = false
		flushToasts()
		return
	end
	showing = true
	title.Text, subtitle.Text = item.title, item.subtitle or ""
	title.TextColor3 = item.color or Color3.new(1, 1, 1)
	bigFrame.Visible = true
	local cleanUp = nil
	if item.decorate then
		local ok, result = pcall(item.decorate, bigFrame)
		cleanUp = if ok and type(result) == "function" then result else nil
	end
	-- (never wider than the screen, and on a narrow screen never over the HUD's menu column: it moves into the
	-- space beside it and shrinks to fit there)
	local screen = UIKit.ScreenSize()
	local full = bigFrame.Size.X.Offset
	local menu = math.min(UIKit.MenuScale(), (screen.X - 24) / full)
	local left = 12
	local hud = Players.LocalPlayer.PlayerGui:FindFirstChild("HUD")
	local column = hud and hud:FindFirstChild("Menu", true)
	if column and column:IsA("GuiObject") and column.AbsoluteSize.X > 0 and column.AbsolutePosition.X < screen.X * 0.3 then
		left = column.AbsolutePosition.X + column.AbsoluteSize.X + 8 - root.AbsolutePosition.X
	end
	if (screen.X - full * menu) / 2 < left then
		local width = math.max(200, screen.X - left - 12)
		menu = math.min(menu, width / full)
		bigFrame.Position = UDim2.new(0, left + width / 2, 0.34, 0)
	else
		bigFrame.Position = UDim2.fromScale(0.5, 0.34)
	end
	bigScale.Scale = 0.2
	TweenService:Create(bigScale, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = menu }):Play()
	task.delay(item.seconds or 2.6, function()
		local out = TweenService:Create(bigScale, TweenInfo.new(0.2), { Scale = 0 })
		out:Play()
		out.Completed:Wait()
		bigFrame.Visible = false
		if cleanUp then
			pcall(cleanUp)
		end
		nextBig()
	end)
end

function Banners.Big(titleText: string, subtitleText: string?, color: Color3?, seconds: number?, decorate: ((Frame) -> (() -> ())?)?)
	table.insert(queue, { title = titleText, subtitle = subtitleText, color = color, seconds = seconds, decorate = decorate })
	if not showing then
		nextBig()
	end
end

function Banners.Busy(): boolean
	return showing or #queue > 0
end

function Banners.Hold()
	holds += 1
end

function Banners.Release()
	holds = math.max(0, holds - 1)
	if holds == 0 and not showing then
		nextBig() -- (the queued banners, then the waiting toasts)
	end
end

local toastList = Instance.new("Frame")
toastList.Name = "Toasts"
toastList.BackgroundTransparency = 1
toastList.AnchorPoint = Vector2.new(0.5, 0)
toastList.Position = UDim2.new(0.5, 0, 0, 120)
toastList.Size = UDim2.fromOffset(800, 200)
toastList.Parent = root
local toastLayout = Instance.new("UIListLayout")
toastLayout.HorizontalAlignment = Enum.HorizontalAlignment.Center
toastLayout.Padding = UDim.new(0, 4)
toastLayout.Parent = toastList
local toastScale = Instance.new("UIScale")
toastScale.Parent = toastList

function showToast(text: string, color: Color3?)
	local scale = UIKit.HudScale()
	toastScale.Scale = scale
	toastList.Size = UDim2.fromOffset(math.min(800, (UIKit.Viewport().X - 24) / scale), 200) -- (fits a small phone)
	local label = UIKit.Label(toastList, "Toast", text, 30, color)
	label.Size = UDim2.new(1, 0, 0, 36)
	label.TextXAlignment = Enum.TextXAlignment.Center
	label.TextScaled = true -- (a long line shrinks to fit rather than running off the screen)
	local limit = Instance.new("UITextSizeConstraint")
	limit.MaxTextSize = 30
	limit.Parent = label
	task.delay(4, function()
		local fade = TweenService:Create(label, TweenInfo.new(0.5), { TextTransparency = 1 })
		-- (the outline fades with the text: alone it left a dark, unreadable ghost of the line)
		local outline = label:FindFirstChildOfClass("UIStroke")
		if outline then
			TweenService:Create(outline, TweenInfo.new(0.5), { Transparency = 1 }):Play()
		end
		fade:Play()
		fade.Completed:Wait()
		label:Destroy()
	end)
end

function Banners.HoldToasts()
	toastHolds += 1
end

function Banners.ReleaseToasts()
	toastHolds = math.max(0, toastHolds - 1)
	flushToasts()
end

function Banners.Toast(text: string, color: Color3?)
	if showing or holds > 0 or toastHolds > 0 then
		table.insert(waitingToasts, { text = text, color = color })
	else
		showToast(text, color)
	end
end

return Banners
