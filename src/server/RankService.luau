--[[
RankService: what shows a player's standing in the world (docs/GAME_DESIGN.md, "Rebirth" and "The
Creature Book"). Server only.
 - A name tag over every character (hidden from its own player): the display name, the rebirth rank ("Rebirth 7 · Frost Finder") in
   the rank's colour, the Creature Book's "Ice Keeper" title, and the book's frosty or golden border. A VIP
   pass owner's name is gold, with "VIP" in front (MonetizationConfig GoldNameTag).
 - The plot's border wall in the rank's colour (Rainbow: a hue per wall).
Refreshed on spawn, on load, after a rebirth and after any book change.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EconomyRules = require(ReplicatedStorage.EconomyRules)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local RebirthConfig = require(ReplicatedStorage.RebirthConfig)
local GamePasses = require(script.Parent.GamePasses)
local PlayerData = require(script.Parent.PlayerData)
local PlotService = require(script.Parent.PlotService)
local IceBlockService = require(script.Parent.IceBlockService)
local PetService = require(script.Parent.PetService)
local RebirthService = require(script.Parent.RebirthService)

local RankService = {}

local DEFAULT_BORDER = Color3.fromRGB(205, 222, 240)
local BORDER_COLOURS = { Frosty = Color3.fromRGB(150, 230, 255), Golden = Color3.fromRGB(255, 205, 60) }
local VIP_GOLD = Color3.fromRGB(255, 210, 80)

-- Whether the player owns a pass that gives a gold name tag (VIP).
local function goldTag(player: Player): boolean
	for _, pass in MonetizationConfig.Passes do
		if pass.GoldNameTag and GamePasses.Owns(player, pass.Key) then
			return true
		end
	end
	return false
end

local function bookRewards(data)
	local title, border = nil, nil
	for _, page in EconomyRules.BookPages(data) do
		if page.Complete then
			title = page.Reward.Title or title
			border = page.Reward.NameTagBorder or border
		end
	end
	return title, border
end

local function tag(player: Player, data)
	local character = player.Character
	local head = character and character:FindFirstChild("Head")
	if not head then
		return
	end
	local gui = head:FindFirstChild("NameTag")
	if not gui then
		gui = Instance.new("BillboardGui")
		gui.Name = "NameTag"
		gui.Size = UDim2.fromScale(7, 1.9)
		gui.StudsOffset = Vector3.new(0, 2.6, 0)
		gui.MaxDistance = 120
		gui.PlayerToHideFrom = player -- your own tag would cover the ice from the tapping spot; others still see it
		gui.Parent = head
		local frame = Instance.new("Frame")
		frame.Name = "Tag"
		frame.BackgroundColor3 = Color3.fromRGB(10, 20, 36)
		frame.BackgroundTransparency = 0.45
		frame.Size = UDim2.fromScale(1, 1)
		frame.Parent = gui
		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0.25, 0)
		corner.Parent = frame
		local stroke = Instance.new("UIStroke")
		stroke.Name = "Border"
		stroke.Thickness = 3
		stroke.Parent = frame
		for _, spec in { { "NameLine", 0.02, 0.5 }, { "RankLine", 0.52, 0.44 } } do
			local label = Instance.new("TextLabel")
			label.Name = spec[1]
			label.BackgroundTransparency = 1
			label.Position = UDim2.fromScale(0.04, spec[2])
			label.Size = UDim2.fromScale(0.92, spec[3])
			label.Font = Enum.Font.FredokaOne
			label.TextScaled = true
			label.TextColor3 = Color3.new(1, 1, 1)
			label.TextStrokeTransparency = 0
			label.Parent = frame
		end
		-- (the default Roblox name above the head would repeat the name)
		local humanoid = character:FindFirstChildOfClass("Humanoid")
		if humanoid then
			humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		end
	end
	local rank = RebirthConfig.RankFor(data.Rebirths)
	local title, border = bookRewards(data)
	local frame = gui.Tag
	local vip = goldTag(player)
	frame.NameLine.Text = (if vip then "VIP · " else "") .. player.DisplayName .. (if title then ` · {title}` else "")
	frame.NameLine.TextColor3 = if vip then VIP_GOLD else Color3.new(1, 1, 1)
	if rank then
		frame.RankLine.Text = `Rebirth {data.Rebirths} · {rank.Title}`
		frame.RankLine.TextColor3 = RebirthConfig.ColourValues[rank.Colour] or Color3.new(1, 1, 1)
	else
		frame.RankLine.Text = "Ice Breaker in training"
		frame.RankLine.TextColor3 = Color3.fromRGB(200, 215, 235)
	end
	frame.RankLine:SetAttribute("Rainbow", rank ~= nil and rank.Colour == "Rainbow")
	frame.Border.Color = if border then BORDER_COLOURS[border] elseif vip then VIP_GOLD else Color3.fromRGB(12, 20, 36)
	frame.Border.Thickness = if border or vip then 4 else 2
end

local function border(player: Player, data)
	local plot = PlotService.PlotOf(player)
	if not plot then
		return
	end
	local rank = RebirthConfig.RankFor(data.Rebirths)
	-- the border's rank-coloured parts: the trims of the plot's models, or the plain walls while there are none
	local walls = {}
	for _, d in plot.Border:GetDescendants() do
		if d:IsA("BasePart") and d:GetAttribute("RankColour") then
			table.insert(walls, d)
		end
	end
	for index, wall in walls do
		if not rank then
			wall.Color = DEFAULT_BORDER
		elseif rank.Colour == "Rainbow" then
			wall.Color = Color3.fromHSV((index - 1) / #walls, 0.6, 1)
		else
			wall.Color = RebirthConfig.ColourValues[rank.Colour] or DEFAULT_BORDER
		end
	end
	plot:SetAttribute("RankColour", if rank then rank.Colour else "")
end

function RankService.Refresh(player: Player)
	local data = PlayerData.Get(player)
	if data then
		tag(player, data)
		border(player, data)
	end
end

function RankService.Start()
	local function watch(player: Player)
		player.CharacterAdded:Connect(function(character)
			character:WaitForChild("Head", 10)
			RankService.Refresh(player)
		end)
	end
	Players.PlayerAdded:Connect(watch)
	for _, player in Players:GetPlayers() do
		watch(player)
	end
	PlayerData.OnLoaded(function(player)
		for _ = 1, 40 do -- the plot is assigned as the data loads
			if PlotService.IndexOf(player) then
				break
			end
			task.wait(0.1)
		end
		RankService.Refresh(player)
	end)
	PlotService.OnAssigned(function(player)
		RankService.Refresh(player)
	end)
	-- a new rank, or a Creature Book page completed (a rescue, a Golden combine)
	RebirthService.OnRebirth(RankService.Refresh)
	IceBlockService.OnRescue(RankService.Refresh)
	PetService.OnEquipChanged(RankService.Refresh)
	-- a VIP pass bought, gifted or given in Studio: the gold name tag at once
	GamePasses.OnChanged(function(player)
		RankService.Refresh(player)
	end)
end

return RankService
