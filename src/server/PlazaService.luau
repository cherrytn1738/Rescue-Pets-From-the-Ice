--[[
PlazaService: the plaza in the middle of the plot ring (docs/GAME_DESIGN.md, "Plot and map layout").
Server only. Greybox, built at start in Workspace.Plaza:
 - a round snow plaza around the spawn point, and a snow path from the plaza to each plot's open front;
 - three leaderboard boards (LeaderboardService fills them), the codes board (opens the Codes window),
   the daily chest and the group chest (RewardService), the Golden Glacier landing ring, and the VIP
   lounge behind a gate (closed: there is no VIP pass yet);
 - the Home button's request (GoHome): sends the player to their plot, at most every 2 seconds.
Players spawn in the plaza (the place's SpawnLocation); a glowing guide line leads them home
(PlotGuide.client).
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local MapConfig = require(ReplicatedStorage.MapConfig)
local PlotService = require(script.Parent.PlotService)

local PlazaService = {}

PlazaService.GoldenSpot = Vector3.new(0, MapConfig.Ground, -34)

local SNOW = Color3.fromRGB(236, 244, 252)
local PATH = Color3.fromRGB(205, 225, 245)
local folder
local lastHome = {}

local function part(parent, name, size, cframe, color, material, shape)
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.Size = size
	p.CFrame = cframe
	p.Color = color
	p.Material = material or Enum.Material.Snow
	p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	if shape then
		p.Shape = shape
	end
	p.Parent = parent
	return p
end

local function sign(target: BasePart, text: string, face: Enum.NormalId?)
	local gui = Instance.new("SurfaceGui")
	gui.Name = "Sign"
	gui.Face = face or Enum.NormalId.Front
	gui.CanvasSize = Vector2.new(400, 400 * target.Size.Y / math.max(target.Size.X, 0.1))
	gui.LightInfluence = 0
	gui.Parent = target
	local label = Instance.new("TextLabel")
	label.Name = "Text"
	label.BackgroundTransparency = 1
	label.Size = UDim2.fromScale(1, 1)
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextStrokeTransparency = 0
	label.Text = text
	label.Parent = gui
	return label
end

-- A spot on the plaza: radius from the centre, angle in degrees (0 = +Z), facing the centre.
local function spot(radius: number, degrees: number, height: number): CFrame
	local a = math.rad(degrees)
	local position = Vector3.new(math.sin(a) * radius, MapConfig.Ground + height, math.cos(a) * radius)
	return CFrame.lookAt(position, Vector3.new(0, position.Y, 0))
end

local function board(name: string, title: string, degrees: number)
	local model = Instance.new("Model")
	model.Name = name
	local face = part(model, "Face", Vector3.new(16, 20, 1), spot(58, degrees, 11), Color3.fromRGB(30, 60, 100), Enum.Material.SmoothPlastic)
	part(model, "Post", Vector3.new(2, 2, 2), spot(58, degrees, 1), Color3.fromRGB(90, 110, 140), Enum.Material.Slate)
	local gui = Instance.new("SurfaceGui")
	gui.Name = "Board"
	gui.CanvasSize = Vector2.new(480, 600)
	gui.LightInfluence = 0
	gui.Parent = face
	local heading = Instance.new("TextLabel")
	heading.Name = "Title"
	heading.BackgroundTransparency = 1
	heading.Size = UDim2.new(1, 0, 0, 70)
	heading.Font = Enum.Font.FredokaOne
	heading.TextScaled = true
	heading.TextColor3 = Color3.fromRGB(255, 220, 90)
	heading.TextStrokeTransparency = 0
	heading.Text = title
	heading.Parent = gui
	local rows = Instance.new("TextLabel")
	rows.Name = "Rows"
	rows.BackgroundTransparency = 1
	rows.Position = UDim2.fromOffset(16, 80)
	rows.Size = UDim2.new(1, -32, 1, -90)
	rows.Font = Enum.Font.FredokaOne
	rows.TextSize = 38
	rows.TextXAlignment = Enum.TextXAlignment.Left
	rows.TextYAlignment = Enum.TextYAlignment.Top
	rows.TextColor3 = Color3.new(1, 1, 1)
	rows.TextStrokeTransparency = 0
	rows.Text = "Loading..."
	rows.Parent = gui
	model.Parent = folder
	return rows
end

local function prompt(parent: BasePart, name: string, action: string, objectText: string)
	local p = Instance.new("ProximityPrompt")
	p.Name = name
	p.ActionText = action
	p.ObjectText = objectText
	p.MaxActivationDistance = 12
	p.RequiresLineOfSight = false
	p.Parent = parent
	return p
end

PlazaService.Boards = {} -- [board id] = the TextLabel its rows go in

function PlazaService.Start(boards)
	folder = Instance.new("Folder")
	folder.Name = "Plaza"
	folder.Parent = Workspace
	part(folder, "Ground", Vector3.new(1, MapConfig.PlazaRadius * 2, MapConfig.PlazaRadius * 2),
		CFrame.new(0, MapConfig.Ground + 0.1, 0) * CFrame.Angles(0, 0, math.rad(90)), SNOW, Enum.Material.Snow, Enum.PartType.Cylinder)
	-- paths to every plot's open front
	for index = 1, MapConfig.PlotCount do
		local plotFront = MapConfig.PlotPoint(index, 0, MapConfig.PlotSize / 2, 0)
		local direction = Vector3.new(plotFront.X, 0, plotFront.Z).Unit
		local from = direction * (MapConfig.PlazaRadius - 2)
		local to = Vector3.new(plotFront.X, 0, plotFront.Z)
		local length = (to - from).Magnitude
		part(folder, "Path" .. index, Vector3.new(12, 0.4, length), CFrame.lookAt((from + to) / 2 + Vector3.new(0, MapConfig.Ground + 0.2, 0), to + Vector3.new(0, MapConfig.Ground + 0.2, 0)), PATH)
	end
	-- the leaderboards, between the paths
	for i, spec in boards do
		PlazaService.Boards[spec.Id] = board("Board" .. spec.Id, spec.Title, 157.5 + 45 * (i - 1))
	end
	-- the codes board
	local codes = part(folder, "CodesBoard", Vector3.new(12, 9, 1), spot(58, 22.5 + 45 * 6, 6), Color3.fromRGB(110, 70, 200), Enum.Material.SmoothPlastic)
	sign(codes, "CODES")
	prompt(codes, "CodesPrompt", "Enter a code", "Codes board")
	-- the chests
	local daily = part(folder, "DailyChest", Vector3.new(6, 4, 4), spot(50, 22.5 + 45 * 1, 2), Color3.fromRGB(120, 200, 255), Enum.Material.Ice)
	sign(daily, "DAILY")
	prompt(daily, "DailyPrompt", "Open", "Daily crystal chest")
	local group = part(folder, "GroupChest", Vector3.new(6, 4, 4), spot(50, 22.5 + 45 * 2, 2), Color3.fromRGB(255, 205, 80), Enum.Material.Foil)
	sign(group, "GROUP +10%")
	prompt(group, "GroupPrompt", "Check", "Group reward")
	-- the Golden Glacier landing ring
	local ring = part(folder, "GoldenRing", Vector3.new(0.3, 30, 30), CFrame.new(PlazaService.GoldenSpot + Vector3.new(0, 0.3, 0)) * CFrame.Angles(0, 0, math.rad(90)),
		Color3.fromRGB(255, 210, 80), Enum.Material.Neon, Enum.PartType.Cylinder)
	ring.Transparency = 0.6
	ring.CanCollide = false
	-- the VIP lounge behind its gate (closed until a VIP pass exists)
	local lounge = spot(62, 22.5 + 45 * 7, 0)
	part(folder, "VipFloor", Vector3.new(18, 0.6, 14), lounge * CFrame.new(0, 0.3, 4), Color3.fromRGB(80, 50, 120), Enum.Material.Fabric)
	-- a gold rail fence round the floor, closed at the front, with the sign over the gate (a ForceField wall
	-- here only shimmered and read as something broken; a solid one was a big flat slab beside a plot's path)
	local gold = Color3.fromRGB(255, 205, 80)
	local gate = Instance.new("Model")
	gate.Name = "VipGate"
	gate.Parent = folder
	local function rails(name: string, from: Vector3, to: Vector3)
		local length = (to - from).Magnitude
		local along = CFrame.lookAt((from + to) / 2, to)
		for _, y in { 1.6, 3.2 } do
			part(gate, name .. "Rail", Vector3.new(0.4, 0.4, length), lounge * along * CFrame.new(0, y, 0), gold, Enum.Material.SmoothPlastic)
		end
		for _, at in { from, to } do
			part(gate, name .. "Post", Vector3.new(0.8, 4.2, 0.8), lounge * CFrame.new(at + Vector3.new(0, 2.1, 0)), gold, Enum.Material.SmoothPlastic)
		end
	end
	rails("Front", Vector3.new(-9, 0, -3), Vector3.new(9, 0, -3))
	rails("Left", Vector3.new(-9, 0, -3), Vector3.new(-9, 0, 11))
	rails("Right", Vector3.new(9, 0, -3), Vector3.new(9, 0, 11))
	for _, x in { -3, 3 } do
		part(gate, "SignPost", Vector3.new(0.5, 6.5, 0.5), lounge * CFrame.new(x, 3.25, -3), gold, Enum.Material.SmoothPlastic)
	end
	local board = part(gate, "Sign", Vector3.new(9, 2, 0.4), lounge * CFrame.new(0, 6.2, -3), Color3.fromRGB(80, 50, 120), Enum.Material.SmoothPlastic)
	sign(board, "VIP LOUNGE")
	-- a welcome sign over the spawn
	local welcome = part(folder, "Welcome", Vector3.new(20, 6, 1), spot(24, 0, 10), Color3.fromRGB(40, 90, 150), Enum.Material.SmoothPlastic)
	sign(welcome, "Rescue Pets From the Ice")

	ReplicatedStorage:WaitForChild("GoHome").OnServerEvent:Connect(function(player)
		local now = os.clock()
		if lastHome[player] and now - lastHome[player] < 2 then
			return
		end
		lastHome[player] = now
		PlotService.SendHome(player)
	end)
	Players.PlayerRemoving:Connect(function(player)
		lastHome[player] = nil
	end)
end

function PlazaService.Prompt(name: string): ProximityPrompt?
	local found = folder and folder:FindFirstChild(name, true)
	return found
end

return PlazaService
