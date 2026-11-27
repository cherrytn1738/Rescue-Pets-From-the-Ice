-- The Golden Glacier (docs/GAME_DESIGN.md, "Social and events"), drawn from Workspace.GoldenGlacier's
-- attributes (GoldenGlacierService): during the countdown a golden block hangs high over the plaza ring
-- with the seconds left, then crashes down (shake, shards); while it stands, the taps left show. Taps near
-- it go to the server on GoldenTap (TapInput). Messages show as toasts.
-- Its look is the ice block's, in gold: a rich gold glass block with glowing gold edges (the rim), a faceted
-- gold crystal core turning inside with a hot light, sparkles, and white-gold cracks that spread in four
-- stages (20, 40, 60, 80% of its HP gone).
-- The "TAP IT!" readout: on the HUD while you're within tap range (players standing round it can't cover
-- it), and as a sign above the glacier from further away.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage.GameConfig)
local UIKit = require(ReplicatedStorage.UIKit)
local UITheme = require(ReplicatedStorage.UITheme)
local Banners = require(script.Parent:WaitForChild("Banners"))
local ClientState = require(script.Parent:WaitForChild("ClientState"))
local Effects = require(script.Parent:WaitForChild("Effects"))

local player = Players.LocalPlayer
local state = Workspace:WaitForChild("GoldenGlacier")
local SIZE = Vector3.new(11, 13, 11)
local RIM = 0.55 -- the glowing gold edges' thickness
local HUD_RANGE = GameConfig.GoldenGlacier.Radius + 6 -- the readout moves onto your HUD within this

local GOLD_GLASS = Color3.fromRGB(235, 135, 0)
local GOLD_RIM = Color3.fromRGB(255, 196, 60)
local GEM = Color3.fromRGB(255, 196, 45)
local CRACK = Color3.fromRGB(255, 250, 225)
local CRACKS_PER_STAGE = { 6, 9, 10, 12 }

local model = Instance.new("Model")
model.Name = "GoldenGlacier"
local offsets = {} -- [part] = its CFrame from the block's centre (turning core parts are placed separately)

local function piece(name: string, size: Vector3, color: Color3, material: Enum.Material, transparency: number, offset: CFrame?): Part
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
	p.CastShadow = false
	p.Size = size
	p.Color = color
	p.Material = material
	p.Transparency = transparency
	p.Parent = model
	if offset then
		offsets[p] = offset
	end
	return p
end

-- The golden ice: deep amber-gold glass (Ice material read as pale sand), see-through so the core shows.
local block = piece("GoldenGlacierBlock", SIZE, GOLD_GLASS, Enum.Material.Glass, 0.3)
block.Reflectance = 0.25
block.CastShadow = true
model.PrimaryPart = block
-- The rim: twelve shiny gold (Foil) edge bars, so it reads as gold from any distance (Neon bloomed lemon yellow).
-- Only the X bars run the full length and fill the corners; the Y and Z bars stop at them, so no two bars
-- share a face (shared faces flickered).
do
	local h = SIZE / 2
	for _, axis in { "X", "Y", "Z" } do
		for _, a in { -1, 1 } do
			for _, b in { -1, 1 } do
				local size, at
				if axis == "X" then
					size, at = Vector3.new(SIZE.X + RIM, RIM, RIM), Vector3.new(0, a * h.Y, b * h.Z)
				elseif axis == "Y" then
					size, at = Vector3.new(RIM, SIZE.Y - RIM, RIM), Vector3.new(a * h.X, 0, b * h.Z)
				else
					size, at = Vector3.new(RIM, RIM, SIZE.Z - RIM), Vector3.new(a * h.X, b * h.Y, 0)
				end
				piece("Rim", size, GOLD_RIM, Enum.Material.Foil, 0, CFrame.new(at))
			end
		end
	end
end
-- a frosted gold cap on top, like the ice blocks' snowy tops
piece("FrostCap", Vector3.new(SIZE.X - 0.4, 0.5, SIZE.Z - 0.4), Color3.fromRGB(255, 236, 185), Enum.Material.Snow, 0.1,
	CFrame.new(0, SIZE.Y / 2 + 0.1, 0))

-- The core: a faceted gold gem (a cube stood on its point, shiny, so each face shades differently) ringed by
-- diamond-section crystals, round a small hot centre; it turns slowly. (Neon is flat: it read as a blob.)
local core = {} -- [part] = its CFrame from the core's turning centre
local gem = piece("Gem", Vector3.one * 3.4, GEM, Enum.Material.SmoothPlastic, 0)
gem.Reflectance = 0.35
core[gem] = CFrame.Angles(math.rad(45), 0, math.rad(35.26))
for index, spec in { { 3.6, 28, 0 }, { 3.2, 32, 90 }, { 3.4, 26, 180 }, { 3, 34, 270 }, { 2.4, 60, 45 }, { 2.4, 58, 225 } } do
	local length, tilt, turn = spec[1], spec[2], spec[3]
	local crystal = piece("Crystal" .. index, Vector3.new(1, length, 1), GEM:Lerp(Color3.new(1, 1, 1), 0.15), Enum.Material.SmoothPlastic, 0)
	crystal.Reflectance = 0.3
	core[crystal] = CFrame.Angles(0, math.rad(turn), 0) * CFrame.Angles(math.rad(tilt), 0, 0)
		* CFrame.new(0, 1.2 + length / 2, 0) * CFrame.Angles(0, math.rad(45), 0)
end
local heart = piece("Heart", Vector3.one * 1.2, Color3.fromRGB(255, 150, 20), Enum.Material.Neon, 0)
heart.Shape = Enum.PartType.Ball
core[heart] = CFrame.new()
local light = Instance.new("PointLight")
light.Color = Color3.fromRGB(255, 190, 80)
light.Range = 16
light.Brightness = 0.8
light.Shadows = false
light.Parent = heart
local sparkles = Instance.new("ParticleEmitter")
sparkles.Name = "Sparkles"
sparkles.Texture = "rbxasset://textures/particles/sparkles_main.dds"
sparkles.Rate = 14
sparkles.Lifetime = NumberRange.new(0.6, 1.3)
sparkles.Speed = NumberRange.new(0.5, 1.5)
sparkles.SpreadAngle = Vector2.new(180, 180)
sparkles.Size = NumberSequence.new(1.1, 0)
sparkles.LightEmission = 1
sparkles.Color = ColorSequence.new(Color3.fromRGB(255, 230, 120))
sparkles.Parent = block

-- cracks: thin lines on the sides, four groups (one per stage), always in the same places
local cracks = {}
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
			local p = piece("Crack", Vector3.new(0.1 + 0.05 * stage, length, 0.06), CRACK, Enum.Material.Neon, 1,
				CFrame.fromMatrix(centre, face.right, Vector3.yAxis) * CFrame.Angles(0, 0, rng:NextNumber(-1.2, 1.2)))
			table.insert(cracks[stage], p)
		end
	end
end
local shownStage = 0

-- Puts the whole glacier at cf (the block's centre); the core turns on its own.
local function place(cf: CFrame, now: number)
	block.CFrame = cf
	for p, offset in offsets do
		p.CFrame = cf * offset
	end
	local centre = cf * CFrame.new(0, -0.8 + 0.3 * math.sin(now * 2), 0) * CFrame.Angles(0, now * 0.7, 0)
	for p, offset in core do
		p.CFrame = centre * offset
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
	heart.Size = Vector3.one * (1.2 + 0.35 * stage)
	light.Brightness = 0.8 + 0.35 * stage
	sparkles.Rate = Effects.Count(14 + 6 * stage)
end

-- The sign above the glacier (seen from further away than tap range)
local sign = Instance.new("BillboardGui")
sign.Name = "GoldenSign"
sign.Size = UDim2.fromScale(14, 2.4)
sign.StudsOffsetWorldSpace = Vector3.new(0, SIZE.Y / 2 + 2.6, 0)
sign.LightInfluence = 0
sign.MaxDistance = 400
sign.Parent = block
local signLabel = Instance.new("TextLabel")
signLabel.BackgroundColor3 = Color3.fromRGB(40, 28, 6)
signLabel.BackgroundTransparency = 0.3
signLabel.Size = UDim2.fromScale(1, 1)
signLabel.Font = UITheme.Font
signLabel.TextScaled = true
signLabel.TextColor3 = Color3.fromRGB(255, 225, 120)
signLabel.TextStrokeTransparency = 0
local signCorner = Instance.new("UICorner")
signCorner.CornerRadius = UDim.new(0.3, 0)
signCorner.Parent = signLabel
signLabel.Parent = sign

-- The HUD readout while you're within tap range: a gold bar of the taps left and the seconds left, under the
-- crystal counter's lines (players round the glacier can't cover it)
local _, hudRoot = UIKit.Screen("GoldenGlacierHud", 7)
local hud = Instance.new("Frame")
hud.Name = "Readout"
hud.BackgroundTransparency = 1
hud.AnchorPoint = Vector2.new(0.5, 0)
hud.Size = UDim2.fromOffset(380, 64)
hud.Visible = false
hud.Parent = hudRoot
local hudScale = Instance.new("UIScale")
hudScale.Parent = hud
local hudTitle = UIKit.Label(hud, "Title", "TAP THE GOLDEN GLACIER!", 26, Color3.fromRGB(255, 220, 100))
hudTitle.Size = UDim2.new(1, 0, 0, 28)
hudTitle.TextXAlignment = Enum.TextXAlignment.Center
local hudBar, setHudBar = UIKit.ProgressBar(hud, "Taps")
hudBar.Position, hudBar.Size = UDim2.fromOffset(0, 32), UDim2.new(1, 0, 0, 30)
hudBar.Fill:FindFirstChildOfClass("UIGradient").Color = ColorSequence.new(Color3.fromRGB(255, 220, 90), Color3.fromRGB(235, 140, 0)) -- (gold, not the usual blue)
local function layoutHud()
	local scale = UIKit.HudScale()
	hudScale.Scale = scale
	-- below the HUD counter (crystals, rate, level line, HP bar, rush, rebirth goal: about 270 px in HUD units)
	hud.Position = UDim2.new(0.5, 0, 0, 6 + 272 * scale)
end
UIKit.OnScreenChanged(layoutHud)
layoutHud()

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
	local inRange = false
	if current == "Countdown" then
		if lastState ~= "Countdown" then
			Effects.Sound("GoldenAlarm") -- (everyone: the race is about to start)
		end
		local left = math.max(0, (state:GetAttribute("LandsAt") or now) - now)
		local fall = math.clamp(1 - left / GameConfig.GoldenGlacier.CountdownSeconds, 0, 1)
		local height = 140 * (1 - fall ^ 6)
		place(CFrame.new(ground + Vector3.new(0, height, 0)) * CFrame.Angles(0, now % (math.pi * 2), 0), now)
		signLabel.Text = `GOLDEN GLACIER in {math.ceil(left)}`
		sign.Enabled = true
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
		inRange = nearPlayer(ground, HUD_RANGE)
		sign.Enabled = not inRange
		signLabel.Text = `GOLDEN GLACIER · TAP IT! {math.ceil(left)}s`
		if inRange then
			setHudBar(math.clamp(hp / math.max(hpMax, 1), 0, 1), `{hp} / {hpMax} taps left  ·  {math.ceil(left)}s`)
		end
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
					Color = if math.random() < 0.5 then GOLD_GLASS else GEM,
					Material = if math.random() < 0.5 then Enum.Material.Neon else Enum.Material.Glass,
					Velocity = Vector3.new((math.random() - 0.5) * 40, 20 + math.random() * 25, (math.random() - 0.5) * 40),
					CanCollide = true,
					Life = 2,
				})
			end
		end
		model.Parent = nil
	end
	hud.Visible = inRange and not UIKit.AnyWindowOpen()
	lastState = current
end)

ClientState.Event("Golden", function(payload)
	Banners.Toast(payload.Text, Color3.fromRGB(255, 220, 100))
end)
