--[[
SwingConfig: the ice pick swing (docs/GAME_DESIGN.md, "The ice pick"). PickSwing.client plays it on every tap.

Three variants alternate so fast tapping doesn't look robotic: Overhead, FromLeft (a diagonal from up over the left
shoulder down to the right) and FromRight (up over the right shoulder down across to the left). Each is a quick
wind-up (the pick back over the shoulder, the torso twisting, the knees bending), a fast strike down into the ice,
a small recoil bounce on impact, then a follow-through and recovery back to the hold.

The arms and torso are one animation per variant; the knees' dip is its own animation (Dip), played only while
standing still, so a swing while walking doesn't stiffen the legs.

Poses: per keyframe, per body part (the joint's Part1: RightUpperArm is the RightShoulder joint), { X, Y, Z }
rotation in degrees and an optional Move = { X, Y, Z } in studs (LowerTorso only: the body dipping). These are the
joint's Transform, so they work for the classic Motor6D joints and the new AnimationConstraint ones alike.
R15 joints: X rotation raises an arm or a leg forward, Y twists, Z swings a right arm out to the side (a left one
across the body); Waist +Y turns the chest left, Waist -X leans it forward; knees bend with -X.

AnimationIds: the uploaded Animation assets (group 921449746), made from these poses by
tools/make_swing_animations.py and uploaded with tools/upload_models.py; 0 = not uploaded yet. An R6 avatar (if the
game's avatar settings allow one) or a missing id plays the default tool slash instead.
]]
local SwingConfig = {}

SwingConfig.Variants = { "Overhead", "FromLeft", "FromRight" }

SwingConfig.Length = 0.56 -- seconds, a full swing at normal speed
SwingConfig.ImpactAt = 0.17 -- the strike lands (the camera nudge)
SwingConfig.WindUpEnd = 0.1 -- the top of the wind-up: a fast tap cuts into the next swing here
SwingConfig.FadeIn = 0.06 -- the blend into a swing from the hold (or from the last swing)
SwingConfig.MaxSpeed = 2.4 -- fast tapping plays the swing up to this fast instead of queueing swings
SwingConfig.Nudge = { Strength = 0.12, Seconds = 0.09 } -- the camera's jolt on impact (none with reduced effects)
SwingConfig.DipWhenSlowerThan = 0.5 -- studs/s: the knees dip only while (nearly) standing still

-- The hold the swing starts and ends in (close to the default tool hold).
local HOLD = {
	RightUpperArm = { 80, 0, 0 },
	RightLowerArm = { 10, 0, 0 },
	RightHand = { 0, 0, 0 },
	LeftUpperArm = { 0, 0, 0 },
	LeftLowerArm = { 0, 0, 0 },
	UpperTorso = { 0, 0, 0 },
	Head = { 0, 0, 0 },
}

local function pose(overrides)
	local out = {}
	for part, angles in HOLD do
		out[part] = angles
	end
	for part, angles in overrides do
		out[part] = angles
	end
	return out
end

-- Easing of the stretch from a keyframe to the next: "Out" slows into the next pose, "In" speeds up into it.
SwingConfig.R15 = {
	Overhead = {
		{ Time = 0, Ease = "Out", Poses = pose({}) },
		{ Time = 0.1, Ease = "In", Poses = pose({ -- the wind-up: the pick back over the shoulder
			RightUpperArm = { 175, 0, 10 }, RightLowerArm = { 25, 0, 0 }, RightHand = { 10, 0, 0 },
			LeftUpperArm = { 55, 0, -8 }, LeftLowerArm = { 30, 0, 0 },
			UpperTorso = { 10, -22, 0 }, Head = { -6, 18, 0 },
		}) },
		{ Time = 0.17, Ease = "Out", Poses = pose({ -- the strike
			RightUpperArm = { 62, 0, 0 }, RightLowerArm = { 6, 0, 0 }, RightHand = { -22, 0, 0 },
			LeftUpperArm = { 25, 0, -4 }, LeftLowerArm = { 20, 0, 0 },
			UpperTorso = { -14, 14, 0 }, Head = { 10, -10, 0 },
		}) },
		{ Time = 0.23, Ease = "Out", Poses = pose({ -- the recoil bounce
			RightUpperArm = { 72, 0, 0 }, RightLowerArm = { 12, 0, 0 }, RightHand = { -10, 0, 0 },
			LeftUpperArm = { 28, 0, -4 }, LeftLowerArm = { 22, 0, 0 },
			UpperTorso = { -8, 10, 0 }, Head = { 6, -7, 0 },
		}) },
		{ Time = 0.33, Ease = "Out", Poses = pose({ -- the follow-through
			RightUpperArm = { 52, 0, 0 }, RightLowerArm = { 6, 0, 0 }, RightHand = { -26, 0, 0 },
			LeftUpperArm = { 18, 0, -4 }, LeftLowerArm = { 16, 0, 0 },
			UpperTorso = { -11, 12, 0 }, Head = { 8, -8, 0 },
		}) },
		{ Time = 0.56, Ease = "Out", Poses = pose({}) },
	},
	FromLeft = {
		{ Time = 0, Ease = "Out", Poses = pose({}) },
		{ Time = 0.1, Ease = "In", Poses = pose({ -- the pick up over the left shoulder (the chest turned right)
			RightUpperArm = { 168, 0, -18 }, RightLowerArm = { 25, 0, 0 }, RightHand = { 10, 0, 0 },
			LeftUpperArm = { 40, 0, -18 }, LeftLowerArm = { 35, 0, 0 },
			UpperTorso = { 6, -30, 0 }, Head = { -4, 24, 0 },
		}) },
		{ Time = 0.17, Ease = "Out", Poses = pose({ -- down to the right
			RightUpperArm = { 60, 0, 18 }, RightLowerArm = { 6, 0, 0 }, RightHand = { -22, 0, 0 },
			LeftUpperArm = { 22, 0, -6 }, LeftLowerArm = { 20, 0, 0 },
			UpperTorso = { -12, -18, 0 }, Head = { 8, 14, 0 },
		}) },
		{ Time = 0.23, Ease = "Out", Poses = pose({
			RightUpperArm = { 70, 0, 14 }, RightLowerArm = { 12, 0, 0 }, RightHand = { -10, 0, 0 },
			LeftUpperArm = { 26, 0, -6 }, LeftLowerArm = { 22, 0, 0 },
			UpperTorso = { -7, -12, 0 }, Head = { 5, 9, 0 },
		}) },
		{ Time = 0.33, Ease = "Out", Poses = pose({
			RightUpperArm = { 52, 0, 22 }, RightLowerArm = { 6, 0, 0 }, RightHand = { -26, 0, 0 },
			LeftUpperArm = { 16, 0, -6 }, LeftLowerArm = { 16, 0, 0 },
			UpperTorso = { -10, -20, 0 }, Head = { 7, 15, 0 },
		}) },
		{ Time = 0.56, Ease = "Out", Poses = pose({}) },
	},
	FromRight = {
		{ Time = 0, Ease = "Out", Poses = pose({}) },
		{ Time = 0.1, Ease = "In", Poses = pose({ -- the pick up and out over the right shoulder (the chest turned left)
			RightUpperArm = { 162, 0, 30 }, RightLowerArm = { 25, 0, 0 }, RightHand = { 10, 0, 0 },
			LeftUpperArm = { 50, 0, -14 }, LeftLowerArm = { 30, 0, 0 },
			UpperTorso = { 8, 32, 0 }, Head = { -4, -26, 0 },
		}) },
		{ Time = 0.17, Ease = "Out", Poses = pose({ -- down across to the left
			RightUpperArm = { 62, 0, -12 }, RightLowerArm = { 6, 0, 0 }, RightHand = { -22, 0, 0 },
			LeftUpperArm = { 22, 0, -4 }, LeftLowerArm = { 20, 0, 0 },
			UpperTorso = { -12, 22, 0 }, Head = { 8, -18, 0 },
		}) },
		{ Time = 0.23, Ease = "Out", Poses = pose({
			RightUpperArm = { 72, 0, -8 }, RightLowerArm = { 12, 0, 0 }, RightHand = { -10, 0, 0 },
			LeftUpperArm = { 26, 0, -4 }, LeftLowerArm = { 22, 0, 0 },
			UpperTorso = { -7, 15, 0 }, Head = { 5, -11, 0 },
		}) },
		{ Time = 0.33, Ease = "Out", Poses = pose({
			RightUpperArm = { 54, 0, -16 }, RightLowerArm = { 6, 0, 0 }, RightHand = { -26, 0, 0 },
			LeftUpperArm = { 16, 0, -4 }, LeftLowerArm = { 16, 0, 0 },
			UpperTorso = { -10, 24, 0 }, Head = { 7, -18, 0 },
		}) },
		{ Time = 0.56, Ease = "Out", Poses = pose({}) },
	},
	-- the knees: a quick dip with the wind-up, lowest at the strike, back up with the recovery
	Dip = {
		{ Time = 0, Ease = "Out", Poses = { LowerTorso = { 0, 0, 0, Move = { 0, 0, 0 } },
			LeftUpperLeg = { 0, 0, 0 }, LeftLowerLeg = { 0, 0, 0 }, LeftFoot = { 0, 0, 0 },
			RightUpperLeg = { 0, 0, 0 }, RightLowerLeg = { 0, 0, 0 }, RightFoot = { 0, 0, 0 } } },
		{ Time = 0.17, Ease = "Out", Poses = { LowerTorso = { 0, 0, 0, Move = { 0, -0.32, 0 } },
			LeftUpperLeg = { 22, 0, 0 }, LeftLowerLeg = { -40, 0, 0 }, LeftFoot = { 18, 0, 0 },
			RightUpperLeg = { 18, 0, 0 }, RightLowerLeg = { -34, 0, 0 }, RightFoot = { 16, 0, 0 } } },
		{ Time = 0.56, Ease = "Out", Poses = { LowerTorso = { 0, 0, 0, Move = { 0, 0, 0 } },
			LeftUpperLeg = { 0, 0, 0 }, LeftLowerLeg = { 0, 0, 0 }, LeftFoot = { 0, 0, 0 },
			RightUpperLeg = { 0, 0, 0 }, RightLowerLeg = { 0, 0, 0 }, RightFoot = { 0, 0, 0 } } },
	},
}

-- The Pose tree an Animation needs (each part under its joint's Part0), R15.
SwingConfig.R15Parents = {
	LowerTorso = "HumanoidRootPart",
	UpperTorso = "LowerTorso",
	Head = "UpperTorso",
	RightUpperArm = "UpperTorso",
	RightLowerArm = "RightUpperArm",
	RightHand = "RightLowerArm",
	LeftUpperArm = "UpperTorso",
	LeftLowerArm = "LeftUpperArm",
	LeftHand = "LeftLowerArm",
	RightUpperLeg = "LowerTorso",
	RightLowerLeg = "RightUpperLeg",
	RightFoot = "RightLowerLeg",
	LeftUpperLeg = "LowerTorso",
	LeftLowerLeg = "LeftUpperLeg",
	LeftFoot = "LeftLowerLeg",
}

SwingConfig.AnimationIds = {
	-- store-assets/animations/upload_manifest.json (group 921449746)
	R15 = { Overhead = 106668462275845, FromLeft = 110464574897720, FromRight = 111143080137346, Dip = 127243049876513 },
}

-- A CFrame for one pose entry ({ X, Y, Z, Move = { X, Y, Z }? } in degrees and studs).
function SwingConfig.PoseCFrame(entry): CFrame
	local move = entry.Move or { 0, 0, 0 }
	return CFrame.new(move[1], move[2], move[3]) * CFrame.Angles(math.rad(entry[1]), math.rad(entry[2]), math.rad(entry[3]))
end

-- The next variant after `previous` (they take turns; never the same one twice running).
function SwingConfig.NextVariant(previous: string?): string
	local index = previous and table.find(SwingConfig.Variants, previous) or 0
	return SwingConfig.Variants[(index % #SwingConfig.Variants) + 1]
end

-- How fast to play a swing that starts `sinceLast` seconds after the previous one began: normal speed for an
-- unhurried tap, faster (up to MaxSpeed) when taps come quicker than a full swing.
function SwingConfig.SpeedFor(sinceLast: number?): number
	if not sinceLast or sinceLast >= SwingConfig.Length then
		return 1
	end
	return math.clamp(SwingConfig.Length / math.max(sinceLast, 0.01), 1, SwingConfig.MaxSpeed)
end

return SwingConfig
