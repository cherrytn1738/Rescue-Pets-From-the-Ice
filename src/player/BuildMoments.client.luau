-- The building moments (docs/GAME_DESIGN.md, "How buildings, upgrades and pets look" and "Detail levels"), on
-- your own plot, from the server's GameEvent notices:
--  - "Built" with First: the station rises out of the snow with a puff, and the camera nudges;
--  - "Built" that reaches a new station milestone (10, 25, 50, 100 owned): the evolution moment: a white
--    glow, a puff, a shake and "Your Ice Drill evolved!";
--  - "Upgraded" (a building upgrade, a new detail point): the station flashes white with a puff and a nudge.
-- Display only: the server already changed the station (PlotService); this moves your copy of it for a
-- moment. Reduced effects: fewer puffs, no shake (Effects).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local BuildingConfig = require(ReplicatedStorage.BuildingConfig)
local UpgradeConfig = require(ReplicatedStorage.UpgradeConfig)
local Banners = require(script.Parent.Banners)
local ClientState = require(script.Parent.ClientState)
local Effects = require(script.Parent.Effects)

local player = Players.LocalPlayer
local RISE_SECONDS = 0.75

local function tierFor(owned: number): number
	local tier = 0
	for index, milestone in BuildingConfig.StationMilestones do
		if owned >= milestone then
			tier = index
		end
	end
	return tier
end

-- Your plot's station for a building, once the server's new copy is here (it is rebuilt on a new look).
local function stationOf(buildingId: string): Instance?
	local index = player:GetAttribute("PlotIndex")
	local plots = Workspace:FindFirstChild("Plots")
	local plot = type(index) == "number" and plots and plots:FindFirstChild("Plot" .. index)
	local folder = plot and plot:FindFirstChild("Buildings")
	return folder and folder:WaitForChild(buildingId, 2)
end

local function bounds(station: Instance): (CFrame, Vector3)
	if station:IsA("Model") then
		return station:GetBoundingBox()
	end
	return (station :: BasePart).CFrame, (station :: BasePart).Size
end

local function puff(at: Vector3, radius: number, count: number)
	for _ = 1, Effects.Count(count) do
		Effects.Debris({
			Size = Vector3.one * (0.8 + math.random() * 0.8),
			CFrame = CFrame.new(at + Vector3.new((math.random() - 0.5) * radius * 2, math.random() * 1.5, (math.random() - 0.5) * radius * 2)),
			Color = Color3.fromRGB(240, 248, 255),
			Material = Enum.Material.Snow,
			Transparency = 0.15,
			Velocity = Vector3.new((math.random() - 0.5) * 14, 8 + math.random() * 8, (math.random() - 0.5) * 14),
			Life = 1.1,
		})
	end
end

-- A white glow over the station that fades out.
local function flash(station: Instance, seconds: number)
	local glow = Instance.new("Highlight")
	glow.Name = "BuildFlash"
	glow.FillColor = Color3.new(1, 1, 1)
	glow.OutlineColor = Color3.new(1, 1, 1)
	glow.FillTransparency = 0.15
	glow.OutlineTransparency = 0
	glow.DepthMode = Enum.HighlightDepthMode.Occluded
	glow.Adornee = station
	glow.Parent = station
	TweenService:Create(glow, TweenInfo.new(seconds, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { FillTransparency = 1, OutlineTransparency = 1 }):Play()
	task.delay(seconds + 0.05, function()
		glow:Destroy()
	end)
end

-- The station rises out of the snow (your copy only: a server change to it ends the rise at once).
local function rise(station: Instance)
	if not station:IsA("Model") then
		return
	end
	local model = station :: Model
	local final = model:GetPivot()
	local _, size = model:GetBoundingBox()
	local depth = size.Y + 1
	local started = os.clock()
	local connection
	connection = RunService.RenderStepped:Connect(function()
		local t = math.clamp((os.clock() - started) / RISE_SECONDS, 0, 1)
		if not model.Parent or model:GetAttribute("Look") == nil then
			connection:Disconnect()
			return
		end
		local eased = 1 - (1 - t) ^ 3
		model:PivotTo(final * CFrame.new(0, -depth * (1 - eased), 0))
		if t >= 1 then
			connection:Disconnect()
		end
	end)
end

ClientState.Event("Built", function(payload)
	if type(payload) ~= "table" or type(payload.BuildingId) ~= "string" then
		return
	end
	local building = BuildingConfig.Get(payload.BuildingId)
	local owned = tonumber(payload.Owned) or 0
	local before = owned - (tonumber(payload.Count) or 0)
	local evolved = not payload.First and tierFor(owned) > tierFor(before)
	if not building or not (payload.First or evolved) then
		return
	end
	task.wait(0.1) -- (the server's new station arrives with or just after the notice)
	local station = stationOf(payload.BuildingId)
	if not station then
		return
	end
	local cf, size = bounds(station)
	local base = cf.Position - Vector3.new(0, size.Y / 2, 0)
	if payload.First then
		rise(station)
		puff(base, math.max(size.X, size.Z) / 2, 14)
		Effects.Shake(0.35, 0.3)
	else
		flash(station, 0.9)
		puff(base, math.max(size.X, size.Z) / 2, 18)
		Effects.Shake(0.7, 0.45)
		Banners.Big(`Your {building.Name} evolved!`, `{owned} owned`, Color3.fromRGB(255, 230, 140), 2.4)
	end
end)

ClientState.Event("Upgraded", function(payload)
	local upgrade = type(payload) == "table" and UpgradeConfig.Get(payload.UpgradeId)
	if not upgrade or upgrade.Kind ~= "Building" or not upgrade.Building then
		return
	end
	task.wait(0.1)
	local station = stationOf(upgrade.Building)
	if not station then
		return
	end
	local cf, size = bounds(station)
	flash(station, 0.6)
	puff(cf.Position - Vector3.new(0, size.Y / 2, 0), math.max(size.X, size.Z) / 2, 10)
	Effects.Shake(0.3, 0.25)
end)
