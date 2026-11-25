-- The Rebirth screen (docs/GAME_DESIGN.md, "Rebirth" and "Screens"): the Frost Cores you'd earn (and the
-- bonus they give), what resets and what's kept, the next rank and what it opens (pet slot, layer), and
-- REBIRTH. The button lights up at Layer 4 (level 31). The server does the rebirth (RebirthRequest).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local LayerConfig = require(ReplicatedStorage.LayerConfig)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local RebirthConfig = require(ReplicatedStorage.RebirthConfig)
local ShowcaseKit = require(ReplicatedStorage.ShowcaseKit)
local UIKit = require(ReplicatedStorage.UIKit)
local Banners = require(script.Parent.Banners)
local ClientState = require(script.Parent.ClientState)

local remote = ReplicatedStorage:WaitForChild("RebirthRequest") :: RemoteFunction
local Colors = UIKit.Colors

local coresLine, bonusLine, resetLine, keptLine, rankLine, confirm, feedback
local sure = false

local window
window = ShowcaseKit.Window("RebirthWindow", "Rebirth", {
	width = 760,
	height = 560,
	-- gamepad: start on the close button, so mashing A can't rebirth by accident (REBIRTH needs two presses)
	firstSelection = function()
		return window and window.panel:FindFirstChild("Close")
	end,
	onLayout = function(width, height)
		local y = 0
		for _, item in { coresLine, bonusLine, resetLine, keptLine, rankLine } do
			item.Position, item.Size = UDim2.fromOffset(0, y), UDim2.fromOffset(width, if item == coresLine then 64 else 54)
			y += if item == coresLine then 70 else 60
		end
		feedback.Position, feedback.Size = UDim2.fromOffset(0, height - 110), UDim2.fromOffset(width, 30)
		confirm.Position, confirm.Size = UDim2.fromOffset(width / 2, height - 76), UDim2.fromOffset(math.min(360, width), 72)
	end,
})
local content = window.content
coresLine = UIKit.Label(content, "Cores", "", 48, Color3.fromRGB(140, 230, 255))
bonusLine = UIKit.Label(content, "Bonus", "", 24, Colors.Gold, true)
resetLine = UIKit.Label(content, "Reset", "", 22, Colors.Error, true)
keptLine = UIKit.Label(content, "Kept", "", 22, Colors.Good, true)
rankLine = UIKit.Label(content, "Rank", "", 24, Colors.Muted, true)
for _, label in { coresLine, bonusLine, resetLine, keptLine, rankLine } do
	label.TextXAlignment = Enum.TextXAlignment.Center
end
feedback = UIKit.Label(content, "Feedback", "", 22, Colors.Gold)
feedback.TextXAlignment = Enum.TextXAlignment.Center
confirm = UIKit.Button(content, "Confirm", "REBIRTH", "Gift", 34)
confirm.AnchorPoint = Vector2.new(0.5, 0)

local function nextRank(rebirths: number)
	for _, rank in RebirthConfig.Ranks do
		if rank.Rank > rebirths then
			return rank
		end
	end
	return nil
end

local function refresh()
	local data = ClientState.Data()
	if not data or not window.IsOpen() then
		return
	end
	local cores = RebirthConfig.FrostCoresFor(data.CrystalsThisRun)
	local ready = data.BlockLevel >= RebirthConfig.RequiredLevel
	coresLine.Text = `+{cores} Frost Cores`
	bonusLine.Text = `Each Frost Core gives +{math.floor(RebirthConfig.FrostCoreBonus * 100)}% crystals forever. You have {data.FrostCores} (+{math.floor(data.FrostCores * RebirthConfig.FrostCoreBonus * 100)}%). This run: {NumberFormat.Short(data.CrystalsThisRun)} crystals.`
	resetLine.Text = "Resets: crystals, buildings, upgrades and the block level (back to 1)."
	keptLine.Text = "Kept: your pets, the Creature Book, Frost Cores, your rank and Robux items."
	local upcoming = nextRank(data.Rebirths + 1 - 1)
	local after = data.Rebirths + 1
	local reached = RebirthConfig.RankFor(after)
	local parts = { `Rebirth {after}: {reached and reached.Title or ""}` }
	if upcoming and upcoming.Rank == after then
		if upcoming.PetSlot then
			table.insert(parts, `opens pet slot {upcoming.PetSlot}`)
		end
		if upcoming.OpensLayer then
			local layer = LayerConfig.Get(upcoming.OpensLayer)
			table.insert(parts, if layer then `opens Layer {upcoming.OpensLayer}: {layer.Name}` else `opens Layer {upcoming.OpensLayer} (coming in an update)`)
		end
	elseif upcoming then
		table.insert(parts, `next unlock at Rebirth {upcoming.Rank}`)
	end
	rankLine.Text = table.concat(parts, " · ")
	if not ready then
		UIKit.SetButton(confirm, `REACH LEVEL {RebirthConfig.RequiredLevel}`, "Done", false)
	else
		UIKit.SetButton(confirm, if sure then (if cores == 0 then "0 CORES. SURE?" else "SURE?") else "REBIRTH", "Gift", true)
	end
end

confirm.Activated:Connect(function()
	if not confirm.Active then
		return
	end
	if not sure then
		sure = true
		refresh()
		return
	end
	sure = false
	local ok, reply = pcall(function()
		return remote:InvokeServer("Rebirth")
	end)
	if ok and type(reply) == "table" then
		feedback.Text = tostring(reply.message)
		feedback.TextColor3 = if reply.ok then Colors.Good else Colors.Error
		if reply.ok then
			window.Close()
		end
	end
	refresh()
end)

-- The rebirth moment: the screen frosts over and clears, then the new rank's banner.
local _, frostRoot = UIKit.Screen("RebirthFrost", 40)
local frost = Instance.new("Frame")
frost.BackgroundColor3 = Color3.fromRGB(225, 245, 255)
frost.BackgroundTransparency = 1
frost.Size = UDim2.fromScale(1, 1)
frost.Parent = frostRoot
ClientState.Event("Rebirth", function(payload)
	UIKit.PlaySound("Rebirth")
	TweenService:Create(frost, TweenInfo.new(0.6), { BackgroundTransparency = 0.05 }):Play()
	task.wait(0.9)
	TweenService:Create(frost, TweenInfo.new(1.2), { BackgroundTransparency = 1 }):Play()
	Banners.Big(`Rebirth {payload.Rebirths}!`, `{payload.Title or ""} · +{payload.Cores} Frost Cores`, Color3.fromRGB(190, 150, 255), 3)
end)

-- The HUD button lights up (gold) once a rebirth is possible.
local button = UIKit.MenuButton("Rebirth")
ClientState.Changed(function(data)
	refresh()
	local ready = data.BlockLevel >= RebirthConfig.RequiredLevel
	local visual = button:FindFirstChild("Visual")
	local gradient = visual and visual:FindFirstChildOfClass("UIGradient")
	if gradient then
		gradient.Enabled = true
	end
	button:SetAttribute("Ready", ready)
	if visual then
		visual.BackgroundColor3 = if ready then Color3.fromRGB(255, 220, 90) else Color3.new(1, 1, 1)
	end
end)
button.Activated:Connect(function()
	sure = false
	feedback.Text = ""
	window.Toggle()
	refresh()
end)
