--[[
ServerNotices (client): what the server tells everyone.
  * The update screen: while Workspace's "SoftShutdown" attribute holds a message (SoftShutdown on the
    server: the server is closing for an update, or this is the holding server on the way back), a
    full-screen panel says so. It sits above everything else.
  * Server messages: a panel near the top with a title and a line of text for a few seconds
    (GameEvent "ServerMessage": admin announcements, "update coming" warnings). One at a time, queued.
Built from the UI kit (ShowcaseKit.Panel, UIKit labels).
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)
local UITheme = require(ReplicatedStorage.UITheme)
local ClientState = require(script.Parent:WaitForChild("ClientState"))

local ATTRIBUTE = "SoftShutdown"
local TITLE_COLOUR = UITheme.Windows.Polar.title

-- The update screen ------------------------------------------------------------------------------

local _, updateRoot = UIKit.Screen("UpdateScreen", 1000)
updateRoot.Parent.IgnoreGuiInset = true
local shade = Instance.new("Frame")
shade.Name = "Shade"
shade.BackgroundColor3 = UITheme.Windows.Polar.bottom
shade.BackgroundTransparency = 0.15
shade.BorderSizePixel = 0
shade.Size = UDim2.fromScale(1, 1)
shade.Visible = false
shade.Active = true -- (taps don't reach the game behind it)
shade.Parent = updateRoot
local updatePanel = ShowcaseKit.Panel(shade, "Panel")
updatePanel.AnchorPoint = Vector2.new(0.5, 0.5)
updatePanel.Position = UDim2.fromScale(0.5, 0.5)
updatePanel.Size = UDim2.fromOffset(640, 230)
local updateScale = Instance.new("UIScale")
updateScale.Parent = updatePanel
local updateTitle = UIKit.Label(updatePanel, "Title", "", 56, TITLE_COLOUR)
updateTitle.TextXAlignment = Enum.TextXAlignment.Center
updateTitle.Position = UDim2.fromOffset(20, 28)
updateTitle.Size = UDim2.fromOffset(600, 70) -- (an offset width: FitOneLine measures it)
UIKit.FitOneLine(updateTitle, 56)
local updateText = UIKit.Label(updatePanel, "Text", "Your progress is saved.", 30, nil, true)
updateText.TextXAlignment = Enum.TextXAlignment.Center
updateText.Position = UDim2.fromOffset(30, 110)
updateText.Size = UDim2.new(1, -60, 0, 90)

local function fitPanels()
	local viewport = UIKit.Viewport()
	updateScale.Scale = math.min(UIKit.MenuScale(), (viewport.X - 24) / 640, (viewport.Y - 24) / 230)
end

local pulse
local function showUpdate()
	local message = Workspace:GetAttribute(ATTRIBUTE)
	local on = type(message) == "string" and message ~= ""
	shade.Visible = on
	if pulse then
		pulse:Cancel()
		pulse = nil
	end
	if on then
		fitPanels()
		updateTitle.Text = message
		pulse = TweenService:Create(updateText, TweenInfo.new(0.9, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { TextTransparency = 0.45 })
		pulse:Play()
	end
end
Workspace:GetAttributeChangedSignal(ATTRIBUTE):Connect(showUpdate)
showUpdate()

-- Server messages --------------------------------------------------------------------------------

local _, messageRoot = UIKit.Screen("ServerMessage", 40)
local messagePanel = ShowcaseKit.Panel(messageRoot, "Panel")
messagePanel.AnchorPoint = Vector2.new(0.5, 0)
messagePanel.Position = UDim2.new(0.5, 0, 0.18, 0)
messagePanel.Size = UDim2.fromOffset(620, 170)
messagePanel.Visible = false
local messageScale = Instance.new("UIScale")
messageScale.Parent = messagePanel
local messageTitle = UIKit.Label(messagePanel, "Title", "", 40, UITheme.Buttons.Gold[1])
messageTitle.TextXAlignment = Enum.TextXAlignment.Center
messageTitle.Position = UDim2.fromOffset(20, 14)
messageTitle.Size = UDim2.new(1, -40, 0, 48)
local messageText = UIKit.Label(messagePanel, "Text", "", 28, nil, true)
messageText.TextXAlignment = Enum.TextXAlignment.Center
messageText.TextYAlignment = Enum.TextYAlignment.Top
messageText.Position = UDim2.fromOffset(24, 66)
messageText.Size = UDim2.new(1, -48, 0, 92)
local textLimit = Instance.new("UITextSizeConstraint")
textLimit.MaxTextSize = 28
textLimit.MinTextSize = 14
textLimit.Parent = messageText
messageText.TextScaled = true

local queue, showing = {}, false
local function nextMessage()
	local item = table.remove(queue, 1)
	if not item then
		showing = false
		messagePanel.Visible = false
		return
	end
	showing = true
	messageTitle.Text, messageText.Text = item.Title, item.Text
	local viewport = UIKit.Viewport()
	local target = math.min(UIKit.HudScale() * 1.15, (viewport.X - 24) / 620)
	messageScale.Scale = 0.2
	messagePanel.Visible = true
	TweenService:Create(messageScale, TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = target }):Play()
	task.delay(item.Seconds, function()
		local out = TweenService:Create(messageScale, TweenInfo.new(0.2), { Scale = 0 })
		out:Play()
		out.Completed:Wait()
		nextMessage()
	end)
end

ClientState.Event("ServerMessage", function(payload)
	if type(payload) ~= "table" or type(payload.Text) ~= "string" then
		return
	end
	table.insert(queue, {
		Title = tostring(payload.Title or "ANNOUNCEMENT"),
		Text = payload.Text,
		Seconds = if type(payload.Seconds) == "number" then math.clamp(payload.Seconds, 3, 30) else 8,
	})
	if not showing then
		nextMessage()
	end
end)

UIKit.OnScreenChanged(fitPanels)
