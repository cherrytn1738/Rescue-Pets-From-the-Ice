-- The Golden Glacier (docs/GAME_DESIGN.md, "Social and events"), drawn from Workspace.GoldenGlacier's
-- attributes (GoldenGlacierService): during the countdown a golden block hangs high over the plaza ring
-- with the seconds left, then crashes down (shake, shards); while it stands, its label shows the taps
-- left. Taps near it go to the server on GoldenTap (TapInput). Messages show as toasts.
-- Its look is the ice block's, in gold: see-through golden ice, a glowing crystal core turning inside,
-- sparkles, and white-gold cracks that spread in four stages (20, 40, 60, 80% of its HP gone).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage.GameConfig)
local UITheme = require(ReplicatedStorage.UITheme)
local Banners = require(script.Parent:WaitForChild("Banners"))
local ClientState = require(script.Parent:WaitForChild("ClientState"))
local Effects = require(script.Parent:WaitForChild("Effects"))

local player = Players.LocalPlayer
local state = Workspace:WaitForChild("GoldenGlacier")
local SIZE = Vector3.new(11, 13, 11)

local GOLD_ICE = Color3.fromRGB(255, 176, 40)
local CORE = Color3.fromRGB(255, 205, 90)
local CRACK = Color3.fromRGB(255, 250, 225)
local CRACKS_PER_STAGE = { 6, 9, 10, 12 }

local model = Instance.new("Model")
model.Name = "GoldenGlacier"

local function piece(name: string, size: Vector3, color: Color3, material: Enum.Material, transparency: number): Part
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
	p.CastShadow = false
	p.Size = size
	p.Color = color
	p.Material = material
	p.Transparency = transparency
	p.Parent = model
	return p
end

-- the golden ice: see-through, so the core shows (a near-solid gold block read as a flat yellow cube)
local block = piece("GoldenGlacierBlock", SIZE, GOLD_ICE, Enum.Material.Ice, 0.5)
block.Reflectance = 0.08
block.CastShadow = true
model.PrimaryPart = block
-- a frosted cap on top, like the ice blocks' snowy tops
local cap = piece("FrostCap", Vector3.new(SIZE.X + 0.3, 0.6, SIZE.Z + 0.3), Color3.fromRGB(255, 240, 200), Enum.Material.Snow, 0.15)
-- the crystal core: a cluster of glowing crystals round a hot centre, turning slowly (one neon cube on its
-- point read as a flat yellow diamond)
local CORE_CRYSTALS = { -- { length, tilt (degrees), turn (degrees) }
	{ 5.2, 0, 0 }, { 4.2, 32, 20 }, { 4, 30, 140 }, { 3.6, 34, 255 }, { 3, 60, 75 }, { 3, 58, 200 },
}
local crystals = {}
for index, spec in CORE_CRYSTALS do
	local crystal = piece("Core" .. index, Vector3.new(1.1, spec[1], 1.1), CORE, Enum.Material.Neon, 0.5)
	crystals[crystal] = CFrame.Angles(0, math.rad(spec[3]), 0) * CFrame.Angles(math.rad(spec[2]), 0, 0)
		* CFrame.new(0, spec[1] / 2 - 0.6, 0) * CFrame.Angles(0, math.rad(45), 0)
end
local heart = piece("Heart", Vector3.one * 1.5, Color3.fromRGB(255, 160, 30), Enum.Material.Neon, 0)
heart.Shape = Enum.PartType.Ball
local light = Instance.new("PointLight")
light.Color = Color3.fromRGB(255, 205, 100)
light.Range = 16
light.Brightness = 0.7
light.Shadows = false
light.Parent = heart
local sparkles = Instance.new("ParticleEmitter")
sparkles.Name = "Sparkles"
sparkles.Texture = "rbxasset://textures/particles/sparkles_main.dds"
sparkles.Rate = 10
sparkles.Lifetime = NumberRange.new(0.6, 1.3)
sparkles.Speed = NumberRange.new(0.5, 1.5)
sparkles.SpreadAngle = Vector2.new(180, 180)
sparkles.Size = NumberSequence.new(0.9, 0)
sparkles.LightEmission = 1
sparkles.Color = ColorSequence.new(Color3.fromRGB(255, 235, 140))
sparkles.Parent = block

-- cracks: thin lines on the sides, four groups (one per stage), always in the same places
local cracks = {}
local crackOffsets = {} -- [part] = its CFrame in the block's space
do
	local rng = Random.new(2024)
	local faces = {
		{ normal = Vector3.zAxis, right = Vector3.xAxis, half = SIZE.Z / 2, w = SIZE.X },
		{ normal = -Vector3.zAxis, right = -Vector3.xAxis, half = SIZE.Z / 2, w = SIZE.X },
		{ normal = Vector3.xAxis, right = -Vector3.zAxis, half = SIZE.X / 2, w = SIZE.Z },
		{ normal = -Vector3.xAxis, right = Vector3.zAxis, half = SIZE.X / 2, w = SIZE.Z },
	}
	for stage, count in CRACKS_PER_STAGE do
		cracks[stage] = {}
		for _ = 1, count do
			local face = faces[rng:NextInteger(1, #faces)]
			local length = SIZE.Y * (0.12 + 0.05 * stage) * (0.6 + rng:NextNumber() * 0.8)
			local centre = face.normal * (face.half + 0.04) + face.right * (rng:NextNumber(-0.42, 0.42) * face.w)
				+ Vector3.yAxis * (rng:NextNumber(-0.42, 0.42) * SIZE.Y)
			local p = piece("Crack", Vector3.new(0.1 + 0.05 * stage, length, 0.06), CRACK, Enum.Material.Neon, 1)
			crackOffsets[p] = CFrame.fromMatrix(centre, face.right, Vector3.yAxis) * CFrame.Angles(0, 0, rng:NextNumber(-1.2, 1.2))
			table.insert(cracks[stage], p)
		end
	end
end
local shownStage = 0

-- Puts the whole glacier at cf (the block's centre); the core turns on its own.
local function place(cf: CFrame, now: number)
	block.CFrame = cf
	cap.CFrame = cf * CFrame.new(0, SIZE.Y / 2 + 0.25, 0)
	local centre = cf * CFrame.new(0, -1 + 0.3 * math.sin(now * 2), 0) * CFrame.Angles(0, now * 0.8, 0)
	for crystal, offset in crystals do
		crystal.CFrame = centre * offset
	end
	heart.CFrame = centre * CFrame.new(0, 0.6, 0)
	for p, offset in crackOffsets do
		p.CFrame = cf * offset
	end
end

-- Shows the cracks up to `stage` (0-4); a new stage pops with a crack sound for players close by.
local function setStage(stage: number, near: boolean)
	if stage > shownStage and stage > 0 and near then
		Effects.Sound("Crack" .. math.clamp(stage, 1, 4))
	end
	shownStage = stage
	for index, group in cracks do
		for _, p in group do
			p.Transparency = if index <= stage then 0.15 else 1
		end
	end
	-- the core burns brighter as the ice breaks
	heart.Size = Vector3.one * (1.5 + 0.3 * stage)
	light.Brightness = 0.7 + 0.3 * stage
	sparkles.Rate = Effects.Count(10 + 5 * stage)
end
local gui = Instance.new("BillboardGui")
gui.Size = UDim2.fromScale(13, 2.2)
-- at the foot of the block, pushed toward the camera (so the block never hides it): it never covers the block
-- or climbs into the HUD's crystal counter
gui.StudsOffsetWorldSpace = Vector3.new(0, -SIZE.Y / 2 + 1.4, 0)
gui.StudsOffset = Vector3.new(0, 0, SIZE.X / 2 + 2.5)
gui.LightInfluence = 0
gui.MaxDistance = 400
gui.Parent = block
local label = Instance.new("TextLabel")
-- white on a dark plate: readable against the gold block and the snow
label.BackgroundColor3 = Color3.fromRGB(40, 28, 6)
label.BackgroundTransparency = 0.3
label.Size = UDim2.fromScale(1, 1)
label.Font = UITheme.Font
label.TextScaled = true
label.TextColor3 = Color3.new(1, 1, 1)
label.TextStrokeTransparency = 0
local labelCorner = Instance.new("UICorner")
labelCorner.CornerRadius = UDim.new(0.3, 0)
labelCorner.Parent = label
label.Parent = gui

local landed = false
local lastState = "Idle"

local function nearPlayer(point: Vector3, distance: number): boolean
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	return root ~= nil and (root.Position - point).Magnitude < distance
end

local function spot(): Vector3
	return state:GetAttribute("Spot") or Vector3.new(0, 0, -34)
end

RunService.RenderStepped:Connect(function()
	local current = state:GetAttribute("State") or "Idle"
	local now = Workspace:GetServerTimeNow()
	local ground = spot() + Vector3.new(0, SIZE.Y / 2, 0)
	if current == "Countdown" then
		if lastState ~= "Countdown" then
			Effects.Sound("GoldenAlarm") -- (everyone: the race is about to start)
		end
		local left = math.max(0, (state:GetAttribute("LandsAt") or now) - now)
		local fall = math.clamp(1 - left / GameConfig.GoldenGlacier.CountdownSeconds, 0, 1)
		local height = 140 * (1 - fall ^ 6)
		place(CFrame.new(ground + Vector3.new(0, height, 0)) * CFrame.Angles(0, now % (math.pi * 2), 0), now)
		label.Text = `GOLDEN GLACIER in {math.ceil(left)}`
		if shownStage ~= 0 then
			setStage(0, false)
		end
		model.Parent = Workspace
		landed = false
	elseif current == "Active" then
		if not landed then
			landed = true
			if nearPlayer(ground, 150) then
				Effects.Shake(1.2, 0.8)
			end
			Effects.Sound("GoldenCrash")
		end
		place(CFrame.new(ground), now)
		local hp, hpMax = state:GetAttribute("Hp") or 0, state:GetAttribute("HpMax") or 1
		local left = math.max(0, (state:GetAttribute("EndsAt") or now) - now)
		label.Text = `TAP IT! {hp}/{hpMax}  ·  {math.ceil(left)}s`
		local broken = 1 - math.clamp(hp / math.max(hpMax, 1), 0, 1)
		local stage = math.clamp(math.floor(broken * 5), 0, 4) -- 20% -> 1 ... 80% -> 4
		if stage ~= shownStage then
			setStage(stage, nearPlayer(ground, GameConfig.GoldenGlacier.Radius + 20))
		end
		model.Parent = Workspace
	else
		if lastState == "Active" then
			for _ = 1, Effects.Count(24) do
				Effects.Debris({
					Size = Vector3.one * (0.8 + math.random()),
					CFrame = CFrame.new(ground + Vector3.new((math.random() - 0.5) * 8, (math.random() - 0.5) * 10, (math.random() - 0.5) * 8)),
					Color = if math.random() < 0.5 then GOLD_ICE else CORE,
					Material = if math.random() < 0.5 then Enum.Material.Neon else Enum.Material.Ice,
					Velocity = Vector3.new((math.random() - 0.5) * 40, 20 + math.random() * 25, (math.random() - 0.5) * 40),
					CanCollide = true,
					Life = 2,
				})
			end
		end
		model.Parent = nil
	end
	lastState = current
end)

ClientState.Event("Golden", function(payload)
	Banners.Toast(payload.Text, Color3.fromRGB(255, 220, 100))
end)
