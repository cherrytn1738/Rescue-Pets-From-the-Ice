-- The Codes window, opened from the HUD's CODES button: type a promo code, press REDEEM.
-- The window only sends what was typed (RedeemCode); the server checks the code, gives the reward
-- and answers with the message shown here (CodeService).
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)

local remote = ReplicatedStorage:WaitForChild("RedeemCode") :: RemoteFunction
local Colors = UIKit.Colors
local icons = UIKit.Theme.Icons or {}

local subtitle, box, redeem, feedback, hint

local window = ShowcaseKit.Window("CodesWindow", "Codes", {
	cornerIcon = icons.Codes, -- (no picture until this game uploads its own icons)
	width = 580,
	height = 380,
	onLayout = function(width, height)
		local compact = height < 240
		subtitle.Position, subtitle.Size = UDim2.fromOffset(0, 4), UDim2.fromOffset(width, 28)
		box.Position, box.Size = UDim2.fromOffset(0, 40), UDim2.fromOffset(width, 60)
		redeem.Position = UDim2.fromOffset(width / 2, 112)
		redeem.Size = UDim2.fromOffset(math.min(260, width), 60)
		feedback.Position, feedback.Size = UDim2.fromOffset(0, 180), UDim2.fromOffset(width, 30)
		hint.Visible = not compact
		hint.Position, hint.Size = UDim2.fromOffset(0, height - 26), UDim2.fromOffset(width, 24)
	end,
	onOpen = function()
		feedback.Text = ""
	end,
})
local content = window.content

subtitle = UIKit.Label(content, "Subtitle", "Enter a code to get free rewards!", 24, Colors.Muted)
subtitle.TextXAlignment = Enum.TextXAlignment.Center
box = UIKit.TextBox(content, "CodeBox", "Type a code here")
redeem = UIKit.Button(content, "RedeemButton", "REDEEM", "Go", 32)
redeem.AnchorPoint = Vector2.new(0.5, 0)
feedback = UIKit.Label(content, "Feedback", "", 24, Colors.Gold, true)
feedback.TextXAlignment = Enum.TextXAlignment.Center
hint = UIKit.Label(content, "Hint", "Codes aren't case-sensitive. Each one works once.", 18, Colors.Muted)
hint.TextXAlignment = Enum.TextXAlignment.Center

local busy = false
local function send()
	if busy then
		return
	end
	if string.match(box.Text, "^%s*$") then
		feedback.Text = "Type a code first."
		feedback.TextColor3 = Colors.Error
		return
	end
	busy = true
	UIKit.SetButton(redeem, "...", "Done", false)
	local ok, reply = pcall(function()
		return remote:InvokeServer(box.Text)
	end)
	busy = false
	UIKit.SetButton(redeem, "REDEEM", "Go", true)
	if not ok or type(reply) ~= "table" then
		feedback.Text = "The server didn't answer. Try again."
		feedback.TextColor3 = Colors.Error
		return
	end
	feedback.Text = tostring(reply.message or "")
	feedback.TextColor3 = if reply.ok then Colors.Good else Colors.Error
	UIKit.PlaySound(if reply.ok then "CodeRedeem" else "Invalid")
	if reply.ok then
		box.Text = ""
	end
end
redeem.Activated:Connect(send)
box.FocusLost:Connect(function(enterPressed)
	if enterPressed then
		send()
	end
end)

UIKit.MenuButton("Codes").Activated:Connect(window.Toggle)
