-- Rare rescues are events (docs/GAME_DESIGN.md, "Social and events": "when a Legendary or Mythic block
-- arrives, the whole server is told, and other players can come and watch it break"). The server's
-- "Announce" notice (IceBlockService) carries the plot; over another player's plot holding one, this puts a
-- tall beam in the rarity's colour (Mythic: shifting rainbow) so you can find it from anywhere, until the
-- creature is freed (the "Freed" announce) or MaxSeconds pass. The toast itself is RescueMoment's.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local IceLooks = require(ReplicatedStorage.IceLooks)
local MapConfig = require(ReplicatedStorage.MapConfig)
local ClientState = require(script.Parent.ClientState)

local SETTINGS = { Height = 90, Width = 6, MaxSeconds = 180 }
local player = Players.LocalPlayer
local beacons = {} -- [plot index] = { part, beam, rarity, endsAt }

local function remove(index: number)
	local beacon = beacons[index]
	if beacon then
		beacon.part:Destroy()
		beacons[index] = nil
	end
end

local function add(index: number, rarity: string)
	remove(index)
	local plots = Workspace:FindFirstChild("Plots")
	local plot = plots and plots:FindFirstChild("Plot" .. index)
	local anchor = plot and plot:FindFirstChild("BlockAnchor", true)
	local base = if anchor and anchor:IsA("BasePart") then anchor.Position else MapConfig.PlotCFrame(index).Position
	local part = Instance.new("Part")
	part.Name = "RareBeacon" .. index
	part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch = true, false, false, false
	part.Transparency = 1
	part.Size = Vector3.one
	part.CFrame = CFrame.new(base + Vector3.new(0, 24, 0))
	local bottom = Instance.new("Attachment")
	bottom.Parent = part
	local top = Instance.new("Attachment")
	top.Position = Vector3.new(0, SETTINGS.Height, 0)
	top.Parent = part
	local beam = Instance.new("Beam")
	beam.Attachment0, beam.Attachment1 = bottom, top
	beam.Color = ColorSequence.new(IceLooks.RarityColors[rarity] or Color3.new(1, 1, 1))
	beam.LightEmission = 1
	beam.FaceCamera = true
	beam.Width0, beam.Width1 = SETTINGS.Width, SETTINGS.Width * 0.4
	beam.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.2),
		NumberSequenceKeypoint.new(0.7, 0.6),
		NumberSequenceKeypoint.new(1, 1),
	})
	beam.Parent = part
	part.Parent = Workspace
	beacons[index] = { part = part, beam = beam, rarity = rarity, endsAt = os.clock() + SETTINGS.MaxSeconds }
end

ClientState.Event("Announce", function(payload)
	if type(payload) ~= "table" or type(payload.PlotIndex) ~= "number" then
		return
	end
	if payload.Freed then
		remove(payload.PlotIndex)
	elseif payload.PlotIndex ~= player:GetAttribute("PlotIndex") and IceLooks.RarityColors[payload.Rarity] then
		add(payload.PlotIndex, payload.Rarity)
	end
end)

RunService.Heartbeat:Connect(function()
	local now = os.clock()
	for index, beacon in beacons do
		if now >= beacon.endsAt then
			remove(index)
		elseif beacon.rarity == "Mythic" then
			beacon.beam.Color = ColorSequence.new(Color3.fromHSV((now * 0.15) % 1, 0.75, 1))
		end
	end
end)
