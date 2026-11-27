--[[
build_swing_animations.luau: turns SwingConfig's poses (every family's variants and dips) into KeyframeSequences and returns each one serialized as an
.rbxm file (hex), for tools/make_swing_animations.py (which writes store-assets/animations/PickSwing<Name>.rbxm for
tools/upload_models.py to upload as group Animations). Run in Edit mode with Rojo synced. Nothing is left in the
place.
]]
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SerializationService = game:GetService("SerializationService")

-- (a fresh copy: Studio's require keeps the first copy it loaded in a session, which may be older than Rojo's)
local fresh = ReplicatedStorage.SwingConfig:Clone()
local SwingConfig = require(fresh)
fresh:Destroy()

local function build(name: string, frames, parents): KeyframeSequence
	local sequence = Instance.new("KeyframeSequence")
	sequence.Name = "PickSwing" .. name
	sequence.Loop = false
	sequence.Priority = Enum.AnimationPriority.Action
	for _, frame in frames do
		local keyframe = Instance.new("Keyframe")
		keyframe.Time = frame.Time
		local poses = {}
		local function poseFor(part: string): Pose
			if poses[part] then
				return poses[part]
			end
			local pose = Instance.new("Pose")
			pose.Name = part
			local entry = frame.Poses[part]
			if entry then
				pose.CFrame = SwingConfig.PoseCFrame(entry)
				pose.Weight = 1
				pose.EasingStyle = Enum.PoseEasingStyle.Cubic
				pose.EasingDirection = if frame.Ease == "In" then Enum.PoseEasingDirection.In else Enum.PoseEasingDirection.Out
			else
				pose.Weight = 0 -- (a joint on the way to an animated one: not animated itself)
			end
			local parent = parents[part]
			pose.Parent = if parent then poseFor(parent) else keyframe
			poses[part] = pose
			return pose
		end
		for part in frame.Poses do
			poseFor(part)
		end
		keyframe.Parent = sequence
	end
	return sequence
end

local function hex(data: buffer): string
	local parts = table.create(buffer.len(data))
	for i = 0, buffer.len(data) - 1 do
		parts[i + 1] = string.format("%02x", buffer.readu8(data, i))
	end
	return table.concat(parts)
end

local out = {}
for name, frames in SwingConfig.R15 do
	local sequence = build(name, frames, SwingConfig.R15Parents)
	out["PickSwing" .. name] = hex(SerializationService:SerializeInstancesAsync({ sequence }))
	sequence:Destroy()
end
return HttpService:JSONEncode(out)
