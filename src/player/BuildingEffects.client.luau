-- BuildingEffects: every building's particles, beams and lights (docs/GAME_DESIGN.md, "Effects and auras"),
-- client only, from EffectsConfig on the stations' named attachment points (BuildingModels).
--
-- Until the building models are uploaded, the stations are PlotService's greybox stand-ins (a Part named
-- by building id, with Owned and Detail attributes): the attachment points are mapped from the model's
-- size onto the stand-in's box, so the logic (which effects, where, how much) is the real one.
--
-- Performance rules (EffectsRules): your own plot shows everything; another plot shows ambient effects at
-- half rate within 60 studs and none beyond (lights stay); at most 2 lights per building; hit bursts are
-- capped per second across all buildings; the reduced-effects setting turns hit effects off and halves
-- the ambient particles. "Orbit" emitters ride a slowly turning ring of attachments.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local BuildingModels = require(ReplicatedStorage.BuildingModels)
local EffectsConfig = require(ReplicatedStorage.EffectsConfig)
local EffectsRules = require(ReplicatedStorage.EffectsRules)

local player = Players.LocalPlayer
local RULES = EffectsConfig.Rules
local ORBIT_POINTS = 6
local stations = {} -- [stand-in part] = station
local hitBucket = EffectsRules.NewHitBucket()

local function numberRange(pair)
	return NumberRange.new(pair[1], pair[2] or pair[1])
end

-- A model's attachment as a CFrame inside the stand-in box (or the real model, once it exists).
local function attachmentCFrame(part: BasePart, modelSize: Vector3, a)
	local size = part.Size
	local p = a.Position
	local scaled = Vector3.new(p.X * size.X / math.max(modelSize.X, 0.1), p.Y * size.Y / math.max(modelSize.Y, 0.1) - size.Y / 2, p.Z * size.Z / math.max(modelSize.Z, 0.1))
	local up = a.Out.Magnitude > 0 and a.Out.Unit or Vector3.yAxis
	local look = a.Up.Magnitude > 0 and a.Up.Unit or Vector3.zAxis
	local right = look:Cross(up)
	if right.Magnitude < 1e-3 then
		return CFrame.new(scaled)
	end
	return CFrame.fromMatrix(scaled, right.Unit, up) -- the attachment's +Y (an emitter's Top) points out
end

local function makeEmitter(spec, parent: Instance)
	local emitter = Instance.new("ParticleEmitter")
	emitter.Name = spec.Name
	emitter.Texture = EffectsConfig.Texture(spec.Texture)
	emitter.Color = ColorSequence.new(spec.Color[1], spec.Color[2] or spec.Color[1])
	emitter.Size = NumberSequence.new(spec.Size[1], spec.Size[2] or spec.Size[1])
	emitter.Lifetime = numberRange(spec.Lifetime)
	emitter.Speed = numberRange(spec.Speed or { 1, 2 })
	emitter.SpreadAngle = Vector2.new(spec.Spread or 0, spec.Spread or 0)
	emitter.LightEmission = spec.LightEmission or 0
	local transparency = spec.Transparency or { 0, 1 }
	emitter.Transparency = NumberSequence.new(transparency[1], transparency[2])
	emitter.Acceleration = spec.Acceleration or Vector3.zero
	emitter.RotSpeed = NumberRange.new(-(spec.Spin or 0), spec.Spin or 0)
	emitter.Drag = spec.Drag or 0
	emitter.EmissionDirection = Enum.NormalId.Top
	emitter.Rate = 0
	emitter:SetAttribute("BaseRate", spec.Rate or 0)
	emitter:SetAttribute("Burst", spec.Burst or 0)
	emitter.Parent = parent
	return emitter
end

local function clear(station)
	if station.folder then
		station.folder:Destroy()
	end
	for _, att in station.attachments or {} do
		att:Destroy() -- (attachments must sit on the part itself, so they're tracked, not foldered)
	end
	station.folder, station.attachments = nil, {}
	station.emitters, station.hits, station.lights, station.beams, station.orbits = {}, {}, {}, {}, {}
end

-- (Re)builds a station's effects for its current tier and Masterwork state.
local function build(station)
	clear(station)
	local part, id = station.part, station.id
	local owned = part:GetAttribute("Owned") or 0
	local detail = part:GetAttribute("Detail") or 0
	local tier = EffectsRules.TierFor(owned)
	local model = BuildingModels.Buildings[id] and BuildingModels.Buildings[id][tier]
	station.tier, station.owned = tier, owned
	if tier == 0 or not model then
		return
	end
	local set = EffectsConfig.For(id, tier, detail >= 10)
	local folder = Instance.new("Folder")
	folder.Name = "Effects"
	folder.Parent = part
	station.folder = folder
	local points = {}
	local function point(name)
		if points[name] == nil then
			local a = model.Attachments[name]
			if a then
				local att = Instance.new("Attachment")
				att.Name = name
				att.CFrame = attachmentCFrame(part, model.Size, a)
				att.Parent = part
				att:SetAttribute("Effects", true)
				table.insert(station.attachments, att)
				points[name] = att
			else
				warn(`[Effects] {id} tier {tier} has no attachment {name}`)
				points[name] = false
			end
		end
		return points[name] or nil
	end
	local function attachFor(spec)
		local base = point(spec.Attachment)
		if not base then
			return {}
		end
		if not spec.Orbit then
			return { base }
		end
		local ring = {}
		local radius = (spec.R or 2) * math.min(part.Size.X, part.Size.Z) / math.max(model.Size.X, model.Size.Z, 0.1)
		for k = 1, ORBIT_POINTS do
			local att = Instance.new("Attachment")
			att.Name = spec.Name .. "Orbit" .. k
			att.Parent = part
			table.insert(station.attachments, att)
			table.insert(ring, att)
			table.insert(station.orbits, { att = att, base = base, radius = radius, angle = (k - 1) / ORBIT_POINTS * math.pi * 2 })
		end
		return ring
	end
	for _, spec in set.Ambient do
		for _, att in attachFor(spec) do
			local emitter = makeEmitter(spec, att)
			emitter:SetAttribute("BaseRate", (spec.Rate or 0) / (if spec.Orbit then ORBIT_POINTS else 1))
			table.insert(station.emitters, emitter)
		end
	end
	for _, spec in set.Hit do
		local att = point(spec.Attachment)
		if att then
			table.insert(station.hits, makeEmitter(spec, att))
		end
	end
	for index, spec in set.Lights do
		local att = point(spec.Attachment)
		if att and index <= RULES.MaxLightsPerBuilding then
			local light = Instance.new("PointLight")
			light.Name = spec.Name
			light.Color, light.Brightness, light.Range, light.Shadows = spec.Color, spec.Brightness, spec.Range, false
			light:SetAttribute("BaseBrightness", spec.Brightness)
			light:SetAttribute("Pulse", spec.Pulse or 0)
			light.Parent = att
			table.insert(station.lights, light)
		end
	end
	for _, spec in set.Beams do
		local a0, a1 = point(spec.From), point(spec.To)
		if a0 and a1 then
			local beam = Instance.new("Beam")
			beam.Name = spec.Name
			beam.Attachment0, beam.Attachment1 = a0, a1
			beam.Texture = EffectsConfig.Texture(spec.Texture)
			beam.Color = ColorSequence.new(spec.Color)
			beam.Width0, beam.Width1 = spec.Width, spec.Width * 0.4
			beam.LightEmission = 1
			beam.TextureSpeed = spec.Speed or 0
			beam.FaceCamera = true
			beam.Transparency = NumberSequence.new(0.4, 0.9)
			beam.Parent = folder
			table.insert(station.beams, beam)
		end
	end
	folder:SetAttribute("Tier", tier)
	folder:SetAttribute("Masterwork", detail >= 10)
end

local function watchStation(part: BasePart, plot: Model)
	if stations[part] then
		return
	end
	local station = { part = part, id = part.Name, plot = plot, nextHit = os.clock() + math.random() }
	stations[part] = station
	clear(station)
	local function rebuild()
		if part.Parent then
			build(station)
		end
	end
	part:GetAttributeChangedSignal("Owned"):Connect(function()
		if EffectsRules.TierFor(part:GetAttribute("Owned") or 0) ~= station.tier then
			rebuild()
		end
	end)
	part:GetAttributeChangedSignal("Detail"):Connect(rebuild)
	part.AncestryChanged:Connect(function()
		if not part.Parent then
			stations[part] = nil
		end
	end)
	rebuild()
end

local function watchPlot(plot: Model)
	local buildings = plot:WaitForChild("Buildings", 10)
	if not buildings then
		return
	end
	buildings.ChildAdded:Connect(function(child)
		if child:IsA("BasePart") then
			task.defer(watchStation, child, plot)
		end
	end)
	for _, child in buildings:GetChildren() do
		if child:IsA("BasePart") then
			watchStation(child, plot)
		end
	end
end

local plots = Workspace:WaitForChild("Plots")
plots.ChildAdded:Connect(watchPlot)
for _, plot in plots:GetChildren() do
	task.spawn(watchPlot, plot)
end

local function reduced(): boolean
	return player:GetAttribute("ReducedEffects") == true
end

-- The rules: every CheckSeconds, each station's ambient rate from where it is and whose plot it's on.
local checkAt = 0
RunService.Heartbeat:Connect(function(dt)
	local now = os.clock()
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	local here = if root then root.Position else Workspace.CurrentCamera.CFrame.Position
	local recheck = now >= checkAt
	if recheck then
		checkAt = now + RULES.CheckSeconds
	end
	for part, station in stations do
		if not station.folder then
			continue
		end
		local mine = station.plot:GetAttribute("Owner") == player.UserId
		if recheck then
			local distance = (part.Position - here).Magnitude
			local scale = EffectsRules.AmbientScale(mine, distance, reduced())
			station.scale = scale
			station.hitsOn = EffectsRules.HitsAllowed(mine, distance, reduced())
			for _, emitter in station.emitters do
				emitter.Rate = (emitter:GetAttribute("BaseRate") or 0) * scale
				emitter.Enabled = scale > 0
			end
			for _, beam in station.beams do
				beam.Enabled = scale > 0
			end
			station.folder:SetAttribute("Scale", scale)
		end
		-- orbiting emitters turn slowly round their centre
		for _, orbit in station.orbits do
			orbit.angle += dt * 0.6
			orbit.att.CFrame = orbit.base.CFrame * CFrame.new(math.cos(orbit.angle) * orbit.radius, 0, math.sin(orbit.angle) * orbit.radius)
		end
		-- pulsing lights
		for _, light in station.lights do
			local pulse = light:GetAttribute("Pulse")
			if pulse and pulse > 0 then
				light.Brightness = light:GetAttribute("BaseBrightness") * (0.6 + 0.4 * math.sin(now * 2 * math.pi / pulse))
			end
		end
		-- hit bursts, at the building's pace, within the global cap
		if station.hitsOn and #station.hits > 0 and now >= station.nextHit then
			station.nextHit = now + EffectsRules.HitInterval(station.owned)
			if hitBucket:Take(now) then
				for _, emitter in station.hits do
					emitter:Emit(math.max(1, math.floor((emitter:GetAttribute("Burst") or 1) * (if mine then 1 else RULES.OtherPlotRate))))
				end
				station.part:SetAttribute("HitsShown", (station.part:GetAttribute("HitsShown") or 0) + 1)
			end
		end
	end
end)
