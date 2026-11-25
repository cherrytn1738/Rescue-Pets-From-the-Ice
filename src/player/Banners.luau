--[[
Banners (client): the big moments on screen, in the house style (UIKit labels).
  Banners.Big(title, subtitle, color, seconds?)   a big centre banner (rarity reveal, new layer)
  Banners.Toast(text, color?)                     a short line at the top (announcements, notices)
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local UIKit = require(ReplicatedStorage.UIKit)

local Banners = {}

local _, root = UIKit.Screen("Banners", 30)
local queue = {}
local showing = false

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

local function nextBig()
	local item = table.remove(queue, 1)
	if not item then
		showing = false
		return
	end
	showing = true
	title.Text, subtitle.Text = item.title, item.subtitle or ""
	title.TextColor3 = item.color or Color3.new(1, 1, 1)
	bigFrame.Visible = true
	-- (never wider than the screen: a small phone shrinks it a little more)
	local menu = math.min(UIKit.MenuScale(), (UIKit.Viewport().X - 24) / bigFrame.Size.X.Offset)
	bigScale.Scale = 0.2
	TweenService:Create(bigScale, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = menu }):Play()
	task.delay(item.seconds or 2.6, function()
		local out = TweenService:Create(bigScale, TweenInfo.new(0.2), { Scale = 0 })
		out:Play()
		out.Completed:Wait()
		bigFrame.Visible = false
		nextBig()
	end)
end

function Banners.Big(titleText: string, subtitleText: string?, color: Color3?, seconds: number?)
	table.insert(queue, { title = titleText, subtitle = subtitleText, color = color, seconds = seconds })
	if not showing then
		nextBig()
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

function Banners.Toast(text: string, color: Color3?)
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
		fade:Play()
		fade.Completed:Wait()
		label:Destroy()
	end)
end

return Banners
