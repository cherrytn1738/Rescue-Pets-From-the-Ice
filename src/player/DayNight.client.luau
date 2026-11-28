-- The day-night cycle on this client (LightingConfig: Day -> PinkDusk -> Night, each look fixed while it lasts).
-- The server only publishes when the cycle started and how fast it runs (Workspace attributes DayCycleStart,
-- DayCycleSpeed, and DayCycleLook when the debug menu forces a look: LightingService); this script works out the look
-- from the server time (LightingConfig.LookFor), so everyone in a server switches together with no network traffic.
-- A player who turned "Day/night cycle" off in Settings stays on the fixed look (LightingConfig.Default, pink dusk).
-- At a switch the screen dims and comes back over Cycle.FadeSeconds, the new look (lighting, effects, skybox) applied
-- in the middle. The lamps (Workspace.Lamps, placed by the server) are on for the looks with Lamps; the northern lights
-- (Beams with the aurora texture, LightingConfig.Aurora) move across the sky in the looks with Aurora.
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local LightingConfig = require(ReplicatedStorage.LightingConfig)
local ClientState = require(script.Parent.ClientState)
local Effects = require(script.Parent.Effects)

local CYCLE = LightingConfig.Cycle
local AURORA = LightingConfig.Aurora
local CHECK_SECONDS = 0.25

local current: string? = nil
local switching = false
local lampsOn = true

-- The lamps -------------------------------------------------------------------------------------------------------

local function setLamp(light: Instance)
	if light:IsA("Light") then
		light.Enabled = lampsOn
	end
end

local function setLamps(on: boolean)
	lampsOn = on
	local folder = Workspace:FindFirstChild("Lamps")
	if folder then
		for _, light in folder:GetDescendants() do
			setLamp(light)
		end
	end
end

-- (with streaming, lamps come and go: each one that arrives gets the current state)
task.spawn(function()
	local folder = Workspace:WaitForChild("Lamps", 60)
	if folder then
		folder.DescendantAdded:Connect(setLamp)
		setLamps(lampsOn)
	end
end)

-- The northern lights ---------------------------------------------------------------------------------------------

local aurora: Folder? = nil
local curtains = {}

local function buildAurora()
	if aurora then
		return
	end
	local folder = Instance.new("Folder")
	folder.Name = "Aurora"
	for index, spec in AURORA.Curtains do
		local angle = math.rad(spec.Angle)
		local centre = Vector3.new(math.sin(angle) * spec.Distance, spec.Height, math.cos(angle) * spec.Distance)
		local along = Vector3.new(math.cos(angle), 0, -math.sin(angle))
		local anchor = Instance.new("Part")
		anchor.Name = "Curtain" .. index
		anchor.Anchored = true
		anchor.CanCollide, anchor.CanQuery, anchor.CanTouch = false, false, false
		anchor.Transparency = 1
		anchor.Size = Vector3.one
		anchor.CFrame = CFrame.new(centre)
		anchor.Parent = folder
		local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
		-- (the curve bends each end along its attachment's X axis: up, so the curtain ripples in the sky)
		a0.CFrame = CFrame.lookAt(-along * spec.Length / 2, -along * spec.Length / 2 + Vector3.yAxis)
		a1.CFrame = CFrame.lookAt(along * spec.Length / 2, along * spec.Length / 2 + Vector3.yAxis)
		a0.Parent, a1.Parent = anchor, anchor
		local beam = Instance.new("Beam")
		beam.Attachment0, beam.Attachment1 = a0, a1
		beam.Texture = "rbxassetid://" .. AURORA.Texture
		beam.TextureMode = Enum.TextureMode.Wrap
		beam.TextureLength = spec.Length / 3
		beam.TextureSpeed = AURORA.Scroll
		beam.Width0, beam.Width1 = spec.Width, spec.Width * 0.8
		beam.Color = ColorSequence.new(spec.Colour)
		beam.LightEmission = AURORA.LightEmission
		beam.Brightness = AURORA.Brightness
		beam.LightInfluence = 0
		beam.FaceCamera = true
		beam.Segments = AURORA.Segments
		beam.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(0.2, AURORA.Transparency),
			NumberSequenceKeypoint.new(0.8, AURORA.Transparency),
			NumberSequenceKeypoint.new(1, 1),
		})
		beam.Parent = anchor
		table.insert(curtains, { beam = beam, phase = index * 1.7 })
	end
	folder.Parent = Workspace
	aurora = folder
end

local function removeAurora()
	if aurora then
		aurora:Destroy()
		aurora = nil
		table.clear(curtains)
	end
end

-- the ripple: each curtain's ends swing slowly (none with reduced effects: the curtains just scroll)
local rippleAt = 0
RunService.Heartbeat:Connect(function()
	if not aurora then
		return
	end
	local now = os.clock()
	if now - rippleAt < 0.1 then
		return
	end
	rippleAt = now
	local reduced = Effects.Reduced()
	for _, curtain in curtains do
		local swing = if reduced then 0 else math.sin(now * 2 * math.pi / AURORA.Ripple.Seconds + curtain.phase)
		curtain.beam.CurveSize0 = AURORA.Ripple.Size * swing
		curtain.beam.CurveSize1 = -AURORA.Ripple.Size * swing
	end
end)

-- Switching -------------------------------------------------------------------------------------------------------

local function apply(look: string)
	LightingConfig.Apply(Lighting, look)
	local preset = LightingConfig.Presets[look]
	setLamps(preset.Lamps == true)
	if preset.Aurora then
		buildAurora()
	else
		removeAurora()
	end
	current = look
end

local fade: ColorCorrectionEffect? = nil
local function fadeTo(brightness: number, seconds: number)
	if not fade or not fade.Parent then
		fade = Instance.new("ColorCorrectionEffect")
		fade.Name = "LookFade"
		fade.Parent = Lighting
	end
	local tween = TweenService:Create(fade :: ColorCorrectionEffect, TweenInfo.new(seconds, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { Brightness = brightness })
	tween:Play()
	tween.Completed:Wait()
end

local function switchTo(look: string)
	if current == nil or CYCLE.FadeSeconds <= 0 then
		apply(look)
		return
	end
	switching = true
	fadeTo(-CYCLE.FadeDepth, CYCLE.FadeSeconds / 2)
	apply(look)
	fadeTo(0, CYCLE.FadeSeconds / 2)
	switching = false
end

local function wanted(): string
	local data = ClientState.Data()
	local cycleOn = not (data and data.Settings and data.Settings.DayNight == false)
	return LightingConfig.LookFor(Workspace:GetServerTimeNow(), Workspace:GetAttribute("DayCycleStart"),
		Workspace:GetAttribute("DayCycleSpeed"), Workspace:GetAttribute("DayCycleLook"), cycleOn)
end

task.spawn(function()
	while true do
		if not switching then
			local look = wanted()
			if look ~= current then
				switchTo(look)
			end
		end
		task.wait(CHECK_SECONDS)
	end
end)
