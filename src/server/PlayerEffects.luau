--[[
PlayerEffects: the short, harmless things the admin window does to a player (Launch, Rocket, Jail).
Server only.

 * No damage, ever.
 * One effect at a time: Busy(target) says what the target is going through, until it ends.
 * When the game gets its own movement checks (an anti-cheat), every push here must tell them, or
   they will take a launched player for a speed hack.
]]
local Debris = game:GetService("Debris")
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local AdminConfig = require(script.Parent.AdminConfig)

local PlayerEffects = {}

local busy = {} -- [player] = { name = "jailed", untilClock = os.clock() it ends }

local CAGE_SIZE = Vector3.new(7, 9, 7) -- studs, around the target's feet
local BAR_THICKNESS = 0.4
local BARS_PER_SIDE = 4
local CAGE_COLOR = Color3.fromRGB(70, 70, 80)
local PUSH_NAME = "AdminPush"

local function rootOf(target: Player): BasePart
	local root = target.Character and target.Character:FindFirstChild("HumanoidRootPart")
	if not root then
		error(`{target.Name} has no character`, 0)
	end
	return root
end

local function mark(target: Player, name: string, seconds: number)
	busy[target] = { name = name, untilClock = os.clock() + seconds }
end

-- Pushes a character for a moment. A LinearVelocity made by the server is simulated by whoever owns
-- the character (the player's own client), so this works on players' characters too.
local function push(root: BasePart, velocity: Vector3, seconds: number)
	local attachment = root:FindFirstChild("RootAttachment")
	if not attachment then
		attachment = Instance.new("Attachment")
		attachment.Name = "RootAttachment"
		attachment.Parent = root
	end
	-- A newer push replaces one still running (two pushes with endless force would fight).
	for _, old in root:GetChildren() do
		if old.Name == PUSH_NAME and old:IsA("LinearVelocity") then
			old:Destroy()
		end
	end
	local force = Instance.new("LinearVelocity")
	force.Name = PUSH_NAME
	force.Attachment0 = attachment
	force.RelativeTo = Enum.ActuatorRelativeTo.World
	force.VelocityConstraintMode = Enum.VelocityConstraintMode.Vector
	force.MaxForce = math.huge
	force.VectorVelocity = velocity
	force.Parent = root
	Debris:AddItem(force, seconds)
end

-- What the target is going through right now ("being launched", "jailed"...), or nil.
function PlayerEffects.Busy(target: Player): string?
	local entry = busy[target]
	if entry and os.clock() < entry.untilClock then
		return entry.name
	end
	busy[target] = nil
	return nil
end

-- Straight up, plus a little sideways in a random direction.
function PlayerEffects.Launch(target: Player)
	local root = rootOf(target)
	local angle = math.random() * math.pi * 2
	local side = Vector3.new(math.cos(angle), 0, math.sin(angle)) * AdminConfig.LaunchSideSpeed
	push(root, side + Vector3.new(0, AdminConfig.LaunchUpSpeed, 0), AdminConfig.LaunchPushSeconds)
	mark(target, "being launched", AdminConfig.LaunchBusySeconds)
end

local function bar(cage: Model, size: Vector3, cframe: CFrame)
	local part = Instance.new("Part")
	part.Name = "Bar"
	part.Anchored = true
	part.CanCollide = true
	part.CanQuery = false
	part.CastShadow = false
	part.Material = Enum.Material.Metal
	part.Color = CAGE_COLOR
	part.Size = size
	part.CFrame = cframe
	part.Parent = cage
end

-- A cage of bars around the target for JailSeconds.
function PlayerEffects.Jail(target: Player)
	local root = rootOf(target)
	local humanoid = target.Character:FindFirstChildOfClass("Humanoid")
	local feet = root.Position - Vector3.new(0, (humanoid and humanoid.HipHeight or 2) + root.Size.Y / 2, 0)
	local base = CFrame.new(feet) * CFrame.Angles(0, select(2, root.CFrame:ToOrientation()), 0)

	local cage = Instance.new("Model")
	cage.Name = "JailCage_" .. target.Name
	local half = CAGE_SIZE / 2
	-- Upright bars along each side, a frame at the bottom, and a roof so they can't jump out.
	for side = 0, 3 do
		local turn = base * CFrame.Angles(0, side * math.pi / 2, 0)
		for index = 0, BARS_PER_SIDE - 1 do
			local x = -half.X + (index + 0.5) * CAGE_SIZE.X / BARS_PER_SIDE
			bar(cage, Vector3.new(BAR_THICKNESS, CAGE_SIZE.Y, BAR_THICKNESS), turn * CFrame.new(x, half.Y, -half.Z))
		end
		bar(cage, Vector3.new(CAGE_SIZE.X, BAR_THICKNESS, BAR_THICKNESS), turn * CFrame.new(0, 0.2, -half.Z))
	end
	bar(cage, Vector3.new(CAGE_SIZE.X + BAR_THICKNESS, BAR_THICKNESS * 2, CAGE_SIZE.Z + BAR_THICKNESS), base * CFrame.new(0, CAGE_SIZE.Y, 0))
	cage.Parent = Workspace
	Debris:AddItem(cage, AdminConfig.JailSeconds)
	mark(target, "jailed", AdminConfig.JailSeconds)
end

-- Up like a rocket (a flame under them), then gravity brings them back down. No damage.
function PlayerEffects.Rocket(target: Player)
	local root = rootOf(target)
	local flame = Instance.new("Fire")
	flame.Name = "RocketFlame"
	flame.Size = 6
	flame.Heat = 18
	flame.Parent = root
	local smoke = Instance.new("Smoke")
	smoke.Name = "RocketSmoke"
	smoke.RiseVelocity = -4
	smoke.Size = 2
	smoke.Parent = root
	Debris:AddItem(flame, AdminConfig.RocketPushSeconds + 0.6)
	Debris:AddItem(smoke, AdminConfig.RocketPushSeconds + 1.5)
	push(root, Vector3.new(0, AdminConfig.RocketUpSpeed, 0), AdminConfig.RocketPushSeconds)
	mark(target, "flying", AdminConfig.RocketPushSeconds + 3)
end

function PlayerEffects.Start()
	Players.PlayerRemoving:Connect(function(player)
		busy[player] = nil
	end)
end

return PlayerEffects
