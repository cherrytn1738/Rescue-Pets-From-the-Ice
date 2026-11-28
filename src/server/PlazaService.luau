--[[
PlazaService: the plaza in the middle of the plot ring (docs/GAME_DESIGN.md, "Plot and map layout").
Server only. Greybox, built at start in Workspace.Plaza:
 - a round snow plaza around the spawn point, and a snow path from the plaza to each plot's open front;
 - three leaderboard boards (LeaderboardService fills them), the codes board (opens the Codes window),
   the daily chest and the group chest (RewardService), the Golden Glacier landing ring, and the VIP
   lounge behind a gate (built only once the VIP pass in MonetizationConfig has a real Id: hidden until then);
 - the PLOT button's request (GoHome): sends the player to their plot's tapping spot (TeleportRules decides,
   PlotService moves them), at most every GameConfig.Teleport.CooldownSeconds, and tells nearby clients to poof the
   snow where they left and arrived (GameEvent "Teleported").
Players spawn in the plaza (the place's SpawnLocation); a glowing guide line leads them home
(PlotGuide.client).
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage.GameConfig)
local MapConfig = require(ReplicatedStorage.MapConfig)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local PlayerEffects = require(script.Parent.PlayerEffects)
local PlotService = require(script.Parent.PlotService)
local TeleportRules = require(script.Parent.TeleportRules)

local PlazaService = {}

PlazaService.GoldenSpot = Vector3.new(0, MapConfig.Ground, -34)

local VIP_PASS = "VIP" -- the pass that opens the lounge (MonetizationConfig.Passes Key)
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

-- The plaza's own model (ServerStorage.PlazaTemplates.<name>, built by tools/studio/build_templates.luau),
-- standing on the ground at groundCFrame over a plain Part that turns invisible and keeps its prompt, collision
-- and SurfaceGui sign. Returns the model, or nil when the template is missing (the plain Part stays).
local function dressPart(target: BasePart, name: string, groundCFrame: CFrame): Model?
	local templates = ServerStorage:FindFirstChild("PlazaTemplates")
	local template = templates and templates:FindFirstChild(name)
	if not template then
		warn(`[Plaza] ServerStorage.PlazaTemplates.{name} is missing: a plain part stands in`)
		return nil
	end
	local look = template:Clone()
	look.Name = name
	look:PivotTo(groundCFrame)
	look.Parent = target.Parent
	target.Transparency = 1
	return look
end

-- A floating label over a prop (the daily chest's model has a blank sign of its own)
local function floatingLabel(target: BasePart, text: string, height: number)
	local gui = Instance.new("BillboardGui")
	gui.Name = "Label"
	gui.Size = UDim2.fromScale(6, 1.4)
	gui.StudsOffsetWorldSpace = Vector3.new(0, height, 0)
	gui.LightInfluence = 0
	gui.MaxDistance = 120
	gui.Parent = target
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Size = UDim2.fromScale(1, 1)
	label.Font = Enum.Font.FredokaOne
	label.TextScaled = true
	label.TextColor3 = Color3.fromRGB(150, 230, 255)
	label.TextStrokeTransparency = 0
	label.Text = text
	label.Parent = gui
end

-- A leaderboard: the carved ice-and-wood board (ServerStorage.PlazaTemplates.LeaderboardBoard, built by
-- tools/studio/build_templates.luau) with the invisible Face part carrying the SurfaceGui just in front of
-- its panel (and giving it collision). Without the template, the old navy slab and post stand in.
local function board(name: string, title: string, degrees: number)
	local model = Instance.new("Model")
	model.Name = name
	local face = part(model, "Face", Vector3.new(16, 20, 1), spot(58, degrees, 11), Color3.fromRGB(30, 60, 100), Enum.Material.SmoothPlastic)
	local templates = ServerStorage:FindFirstChild("PlazaTemplates")
	local template = templates and templates:FindFirstChild("LeaderboardBoard")
	if template then
		local look = template:Clone()
		look.Name = "Look"
		look:PivotTo(spot(58, degrees, 0))
		look.Parent = model
		face.Transparency = 1
	else
		warn("[Plaza] ServerStorage.PlazaTemplates.LeaderboardBoard is missing: a plain board stands in")
		part(model, "Post", Vector3.new(2, 2, 2), spot(58, degrees, 1), Color3.fromRGB(90, 110, 140), Enum.Material.Slate)
	end
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
	-- (a Persistent model: with streaming on, the plaza, its boards and chests stay loaded everywhere)
	folder = Instance.new("Model")
	folder.Name = "Plaza"
	folder.ModelStreamingMode = Enum.ModelStreamingMode.Persistent
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
	sign(codes, "CODES") -- (on the invisible Part, just in front of the kiosk's panel)
	prompt(codes, "CodesPrompt", "Enter a code", "Codes board")
	dressPart(codes, "CodesKiosk", spot(58, 22.5 + 45 * 6, 0))
	-- the chests
	local daily = part(folder, "DailyChest", Vector3.new(6, 4, 4), spot(50, 22.5 + 45 * 1, 2), Color3.fromRGB(120, 200, 255), Enum.Material.Ice)
	prompt(daily, "DailyPrompt", "Open", "Daily crystal chest")
	if dressPart(daily, "DailyChestStand", spot(50, 22.5 + 45 * 1, 0)) then
		floatingLabel(daily, "DAILY CHEST", 7)
	else
		sign(daily, "DAILY")
	end
	local group = part(folder, "GroupChest", Vector3.new(6, 4, 4), spot(50, 22.5 + 45 * 2, 2), Color3.fromRGB(255, 205, 80), Enum.Material.Foil)
	sign(group, "GROUP +10%")
	prompt(group, "GroupPrompt", "Check", "Group reward")
	-- the Golden Glacier landing ring
	local ring = part(folder, "GoldenRing", Vector3.new(0.3, 30, 30), CFrame.new(PlazaService.GoldenSpot + Vector3.new(0, 0.3, 0)) * CFrame.Angles(0, 0, math.rad(90)),
		Color3.fromRGB(255, 210, 80), Enum.Material.Neon, Enum.PartType.Cylinder)
	ring.Transparency = 0.6
	ring.CanCollide = false
	-- the VIP lounge behind its gate: only once a VIP pass is in MonetizationConfig (Key "VIP"); until then
	-- there is nothing to show, so the plaza has no lounge
	-- (only once the VIP pass exists on Roblox: a real Id, in Studio too)
	if MonetizationConfig.IsLive(MonetizationConfig.GetPass(VIP_PASS)) then
		local lounge = spot(62, 22.5 + 45 * 7, 0)
		-- (its top sits 0.15 above the plaza disc's: at the same height the two surfaces flickered)
		part(folder, "VipFloor", Vector3.new(18, 0.6, 14), lounge * CFrame.new(0, 0.45, 4), Color3.fromRGB(80, 50, 120), Enum.Material.Fabric)
		-- a gold rail fence round the floor, closed at the front, with the sign over the gate (a ForceField wall
		-- here only shimmered and read as something broken; a solid one was a big flat slab beside a plot's path)
		local gold = Color3.fromRGB(255, 205, 80)
		local gate = Instance.new("Model")
		gate.Name = "VipGate"
		gate.Parent = folder
		local posted = {} -- one post per corner (two identical posts in one spot flickered)
		local function rails(name: string, from: Vector3, to: Vector3)
			local length = (to - from).Magnitude
			local along = CFrame.lookAt((from + to) / 2, to)
			for _, y in { 1.6, 3.2 } do
				part(gate, name .. "Rail", Vector3.new(0.4, 0.4, length), lounge * along * CFrame.new(0, y, 0), gold, Enum.Material.SmoothPlastic)
			end
			for _, at in { from, to } do
				local key = tostring(at)
				if not posted[key] then
					posted[key] = true
					part(gate, name .. "Post", Vector3.new(0.8, 4.2, 0.8), lounge * CFrame.new(at + Vector3.new(0, 2.1, 0)), gold, Enum.Material.SmoothPlastic)
				end
			end
		end
		rails("FrontLeft", Vector3.new(-9, 0, -3), Vector3.new(-3, 0, -3))
		rails("FrontRight", Vector3.new(3, 0, -3), Vector3.new(9, 0, -3))
		rails("Left", Vector3.new(-9, 0, -3), Vector3.new(-9, 0, 11))
		rails("Right", Vector3.new(9, 0, -3), Vector3.new(9, 0, 11))
		rails("Back", Vector3.new(-9, 0, 11), Vector3.new(9, 0, 11))
		for _, x in { -3, 3 } do
			part(gate, "SignPost", Vector3.new(0.5, 6.5, 0.5), lounge * CFrame.new(x, 3.25, -3), gold, Enum.Material.SmoothPlastic)
		end
		-- Invisible walls, too high to jump, all round; the door between the sign posts lets VIP owners
		-- through (VipLounge.client turns its collision off for them: your own character's physics is your
		-- client's, and the lounge gives no gameplay advantage, so a client-side door is enough).
		for _, wall in {
			{ "WallFront", Vector3.new(6, 12, 1), Vector3.new(-6, 6, -3) },
			{ "WallFront", Vector3.new(6, 12, 1), Vector3.new(6, 6, -3) },
			{ "WallLeft", Vector3.new(1, 12, 14), Vector3.new(-9, 6, 4) },
			{ "WallRight", Vector3.new(1, 12, 14), Vector3.new(9, 6, 4) },
			{ "WallBack", Vector3.new(18, 12, 1), Vector3.new(0, 6, 11) },
		} do
			local blocker = part(gate, wall[1], wall[2], lounge * CFrame.new(wall[3]), gold, Enum.Material.SmoothPlastic)
			blocker.Transparency = 1
		end
		local door = part(gate, "VipDoor", Vector3.new(6, 12, 0.6), lounge * CFrame.new(0, 6, -3), gold, Enum.Material.SmoothPlastic)
		door.Transparency = 1
		local glow = part(gate, "VipDoorGlow", Vector3.new(5.6, 5, 0.2), lounge * CFrame.new(0, 2.5, -3), gold, Enum.Material.Neon)
		glow.Transparency = 0.75
		glow.CanCollide = false
		door:SetAttribute("Pass", VIP_PASS)
		local board = part(gate, "Sign", Vector3.new(9, 2, 0.4), lounge * CFrame.new(0, 6.2, -3), Color3.fromRGB(80, 50, 120), Enum.Material.SmoothPlastic)
		sign(board, "VIP LOUNGE")
	end
	-- a welcome sign over the spawn
	local welcome = part(folder, "Welcome", Vector3.new(20, 6, 1), spot(24, 0, 10), Color3.fromRGB(40, 90, 150), Enum.Material.SmoothPlastic)
	sign(welcome, "Rescue Pets From the Ice")

	local gameEvent = ReplicatedStorage:WaitForChild("GameEvent") :: RemoteEvent
	ReplicatedStorage:WaitForChild("GoHome").OnServerEvent:Connect(function(player)
		local character = player.Character
		local humanoid = character and character:FindFirstChildOfClass("Humanoid")
		local root = character and character:FindFirstChild("HumanoidRootPart")
		local now = os.clock()
		local ok = TeleportRules.Check({
			now = now,
			lastAt = lastHome[player],
			hasPlot = PlotService.IndexOf(player) ~= nil,
			alive = humanoid ~= nil and root ~= nil and humanoid.Health > 0,
			jailed = PlayerEffects.Busy(player) == "jailed", -- (PLOT doesn't let a player out of the admin's jail early)
		}, GameConfig.Teleport.CooldownSeconds)
		if not ok then
			return
		end
		lastHome[player] = now
		local from = (root :: BasePart).Position
		if PlotService.SendHome(player) and root and root.Parent then
			gameEvent:FireAllClients("Teleported", { UserId = player.UserId, From = from, To = root.Position })
		end
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
