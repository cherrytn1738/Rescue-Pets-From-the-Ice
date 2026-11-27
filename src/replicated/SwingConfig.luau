--[[
SwingConfig: how each family of tools is held and swung (docs/GAME_DESIGN.md, "Tools"). PickSwing.client plays it on
every tap; PickService holds the tool with its family's Grip.

Families (UpgradeConfig.Tools[tier].Family), each with its own variants that take turns:
 * Pick: the overhead strike and its two diagonals (Overhead, FromLeft, FromRight).
 * Hammer: a slower wind-up that hangs at the top, a heavy slam, a bigger impact (a stronger camera nudge, a
   chunkier chip burst): Slam, then SlamRight (down from over the right shoulder).
 * Axe: diagonal chops, alternating ChopLeft (down from over the left shoulder) and ChopRight.
 * Sword: quick slashes in a 3-hit combo, SlashRight (sweeping in from the right), SlashLeft (back across from the
   left), SlashOverhead, with a trail during the slash.
 * Spear (the spears and the Ice Drill): a forward thrust, Thrust and ThrustLow in turn, with a lunge; a drill's
   bit spins on the hit.
Each swing is a wind-up, the strike (ImpactAt: the camera nudge), a small recoil, a follow-through and the recovery
back to the hold. The tap's effects and sound fire on the click itself; tapping faster plays the swing faster (up to
MaxSpeed) and cuts into the next one, never queueing. The knees' dip (the family's Dip animation) plays only while
standing still, so a swing while walking doesn't stiffen the legs.

Grip: the Tool.Grip for the family. Every tool model has its handle along +Y from its butt and its striking side
toward -X (tools/blender/tools_tiers.py); the grip turns that into the swing: picks, hammers and axes lead with the
-X side, swords hold the edges to the sides, spears point forward along the arm.
Impact: the chip burst at the strike point (TapFeedback): Chips and Sparks scale the counts, ChipSize the chips.

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

SwingConfig.FadeIn = 0.06 -- the blend into a swing from the hold (or from the last swing)
SwingConfig.DipWhenSlowerThan = 0.5 -- studs/s: the knees dip only while (nearly) standing still
-- the swing trail (a sword's slash): mostly plain colour, the tier's spark colour (added light vanishes against snow)
SwingConfig.Trail = { Lifetime = 0.16, Transparency = { 0.1, 1 }, WidthScale = { 1, 0.3 }, LightEmission = 0.1, AfterImpact = 0.08 }
SwingConfig.BitSpin = { Speed = 40, Seconds = 0.45 } -- a drill bit's spin on the hit (radians/s, slowing to a stop)

SwingConfig.Families = {
	Pick = {
		Variants = { "Overhead", "FromLeft", "FromRight" },
		Length = 0.56, WindUpEnd = 0.1, ImpactAt = 0.17, MaxSpeed = 2.4,
		Nudge = { Strength = 0.12, Seconds = 0.09 },
		Dip = "Dip",
		Impact = { Chips = 1, ChipSize = 1, Sparks = 1 },
		Grip = CFrame.Angles(0, math.rad(90), 0),
	},
	Hammer = {
		Variants = { "Slam", "SlamRight" },
		Length = 0.78, WindUpEnd = 0.25, ImpactAt = 0.32, MaxSpeed = 3,
		Nudge = { Strength = 0.32, Seconds = 0.15 },
		Dip = "HammerDip",
		Impact = { Chips = 2, ChipSize = 1.5, Sparks = 1.3 },
		Grip = CFrame.Angles(0, math.rad(90), 0),
	},
	Axe = {
		Variants = { "ChopLeft", "ChopRight" },
		Length = 0.56, WindUpEnd = 0.11, ImpactAt = 0.18, MaxSpeed = 2.4,
		Nudge = { Strength = 0.15, Seconds = 0.1 },
		Dip = "Dip",
		Impact = { Chips = 1.4, ChipSize = 1.15, Sparks = 1 },
		Grip = CFrame.Angles(0, math.rad(90), 0),
	},
	Sword = {
		Variants = { "SlashRight", "SlashLeft", "SlashOverhead" },
		Length = 0.42, WindUpEnd = 0.07, ImpactAt = 0.13, MaxSpeed = 2.2,
		Nudge = { Strength = 0.08, Seconds = 0.07 },
		Dip = "Dip",
		Impact = { Chips = 0.75, ChipSize = 0.9, Sparks = 1.6 },
		Trail = true,
		Grip = CFrame.new(),
	},
	Spear = {
		Variants = { "Thrust", "ThrustLow" },
		Length = 0.5, WindUpEnd = 0.12, ImpactAt = 0.18, MaxSpeed = 2.4,
		Nudge = { Strength = 0.12, Seconds = 0.09 },
		Dip = "Lunge",
		Impact = { Chips = 1, ChipSize = 0.85, Sparks = 1.2 },
		Grip = CFrame.Angles(math.rad(90), 0, 0),
	},
}
SwingConfig.FamilyOrder = { "Pick", "Hammer", "Axe", "Sword", "Spear" }

-- The hold every swing starts and ends in (close to the default tool hold).
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

local LEGS = { "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot" }
local function legs(move, angles)
	local out = { LowerTorso = { 0, 0, 0, Move = move } }
	for i, part in LEGS do
		out[part] = angles[i] or { 0, 0, 0 }
	end
	return out
end

-- Easing of the stretch from a keyframe to the next: "Out" slows into the next pose, "In" speeds up into it.
SwingConfig.R15 = {
	-- Pick ----------------------------------------------------------------------------------------------------
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
	-- the knees: a quick dip with the wind-up, lowest at the strike, back up with the recovery (picks, axes, swords)
	Dip = {
		{ Time = 0, Ease = "Out", Poses = legs({ 0, 0, 0 }, {}) },
		{ Time = 0.17, Ease = "Out", Poses = legs({ 0, -0.32, 0 }, { { 22, 0, 0 }, { -40, 0, 0 }, { 18, 0, 0 }, { 18, 0, 0 }, { -34, 0, 0 }, { 16, 0, 0 } }) },
		{ Time = 0.56, Ease = "Out", Poses = legs({ 0, 0, 0 }, {}) },
	},

	-- Hammer: up high and back, a moment's hang at the top, then the slam ---------------------------------------
	Slam = {
		{ Time = 0, Ease = "Out", Poses = pose({}) },
		{ Time = 0.2, Ease = "Out", Poses = pose({ -- the heavy wind-up: the hammer high behind the head, leaning back
			RightUpperArm = { 150, 0, 10 }, RightLowerArm = { 16, 0, 0 }, RightHand = { -30, 0, 0 },
			LeftUpperArm = { 140, 0, -24 }, LeftLowerArm = { 40, 0, 0 },
			UpperTorso = { 12, -14, 0 }, Head = { -10, 12, 0 },
		}) },
		{ Time = 0.25, Ease = "In", Poses = pose({ -- the hang at the top
			RightUpperArm = { 156, 0, 10 }, RightLowerArm = { 20, 0, 0 }, RightHand = { -30, 0, 0 },
			LeftUpperArm = { 145, 0, -24 }, LeftLowerArm = { 42, 0, 0 },
			UpperTorso = { 15, -15, 0 }, Head = { -11, 13, 0 },
		}) },
		{ Time = 0.32, Ease = "Out", Poses = pose({ -- the slam, leaning right into it
			RightUpperArm = { 72, 0, 0 }, RightLowerArm = { 2, 0, 0 }, RightHand = { -44, 0, 0 },
			LeftUpperArm = { 44, 0, -10 }, LeftLowerArm = { 18, 0, 0 },
			UpperTorso = { -24, 8, 0 }, Head = { 14, -6, 0 },
		}) },
		{ Time = 0.4, Ease = "Out", Poses = pose({ -- the bounce off the ice
			RightUpperArm = { 80, 0, 0 }, RightLowerArm = { 10, 0, 0 }, RightHand = { -32, 0, 0 },
			LeftUpperArm = { 44, 0, -10 }, LeftLowerArm = { 20, 0, 0 },
			UpperTorso = { -16, 6, 0 }, Head = { 9, -4, 0 },
		}) },
		{ Time = 0.52, Ease = "Out", Poses = pose({
			RightUpperArm = { 66, 0, 0 }, RightLowerArm = { 4, 0, 0 }, RightHand = { -44, 0, 0 },
			LeftUpperArm = { 34, 0, -8 }, LeftLowerArm = { 16, 0, 0 },
			UpperTorso = { -19, 7, 0 }, Head = { 11, -5, 0 },
		}) },
		{ Time = 0.78, Ease = "Out", Poses = pose({}) },
	},
	SlamRight = {
		{ Time = 0, Ease = "Out", Poses = pose({}) },
		{ Time = 0.2, Ease = "Out", Poses = pose({ -- high over the right shoulder (the chest turned left)
			RightUpperArm = { 145, 0, 34 }, RightLowerArm = { 16, 0, 0 }, RightHand = { -26, 0, 0 },
			LeftUpperArm = { 125, 0, -10 }, LeftLowerArm = { 40, 0, 0 },
			UpperTorso = { 12, 30, 0 }, Head = { -8, -22, 0 },
		}) },
		{ Time = 0.25, Ease = "In", Poses = pose({
			RightUpperArm = { 151, 0, 36 }, RightLowerArm = { 20, 0, 0 }, RightHand = { -26, 0, 0 },
			LeftUpperArm = { 130, 0, -10 }, LeftLowerArm = { 42, 0, 0 },
			UpperTorso = { 15, 32, 0 }, Head = { -9, -23, 0 },
		}) },
		{ Time = 0.32, Ease = "Out", Poses = pose({ -- down across to the left
			RightUpperArm = { 72, 0, -14 }, RightLowerArm = { 2, 0, 0 }, RightHand = { -44, 0, 0 },
			LeftUpperArm = { 40, 0, -8 }, LeftLowerArm = { 18, 0, 0 },
			UpperTorso = { -22, 20, 0 }, Head = { 13, -15, 0 },
		}) },
		{ Time = 0.4, Ease = "Out", Poses = pose({
			RightUpperArm = { 80, 0, -10 }, RightLowerArm = { 10, 0, 0 }, RightHand = { -32, 0, 0 },
			LeftUpperArm = { 38, 0, -8 }, LeftLowerArm = { 20, 0, 0 },
			UpperTorso = { -15, 15, 0 }, Head = { 8, -11, 0 },
		}) },
		{ Time = 0.52, Ease = "Out", Poses = pose({
			RightUpperArm = { 66, 0, -18 }, RightLowerArm = { 4, 0, 0 }, RightHand = { -44, 0, 0 },
			LeftUpperArm = { 28, 0, -6 }, LeftLowerArm = { 16, 0, 0 },
			UpperTorso = { -18, 22, 0 }, Head = { 10, -16, 0 },
		}) },
		{ Time = 0.78, Ease = "Out", Poses = pose({}) },
	},
	-- the hammer's knees: up on the wind-up, a deep dip with the slam
	HammerDip = {
		{ Time = 0, Ease = "Out", Poses = legs({ 0, 0, 0 }, {}) },
		{ Time = 0.22, Ease = "In", Poses = legs({ 0, 0.06, 0 }, { { -4, 0, 0 }, { 0, 0, 0 }, { -6, 0, 0 }, { -4, 0, 0 }, { 0, 0, 0 }, { -6, 0, 0 } }) },
		{ Time = 0.32, Ease = "Out", Poses = legs({ 0, -0.5, 0 }, { { 32, 0, 0 }, { -58, 0, 0 }, { 26, 0, 0 }, { 28, 0, 0 }, { -50, 0, 0 }, { 22, 0, 0 } }) },
		{ Time = 0.78, Ease = "Out", Poses = legs({ 0, 0, 0 }, {}) },
	},

	-- Axe: diagonal chops, the wrist snapping through ---------------------------------------------------------
	ChopLeft = {
		{ Time = 0, Ease = "Out", Poses = pose({}) },
		{ Time = 0.11, Ease = "In", Poses = pose({ -- up over the left shoulder (the chest turned right)
			RightUpperArm = { 158, 0, -34 }, RightLowerArm = { 22, 0, 0 }, RightHand = { -6, 0, 0 },
			LeftUpperArm = { 36, 0, -20 }, LeftLowerArm = { 38, 0, 0 },
			UpperTorso = { 6, -36, 0 }, Head = { -4, 28, 0 },
		}) },
		{ Time = 0.18, Ease = "Out", Poses = pose({ -- the chop, down to the right
			RightUpperArm = { 58, 0, 28 }, RightLowerArm = { 4, 0, 0 }, RightHand = { -26, 0, 0 },
			LeftUpperArm = { 22, 0, -6 }, LeftLowerArm = { 20, 0, 0 },
			UpperTorso = { -14, -16, 0 }, Head = { 9, 12, 0 },
		}) },
		{ Time = 0.24, Ease = "Out", Poses = pose({
			RightUpperArm = { 68, 0, 24 }, RightLowerArm = { 12, 0, 0 }, RightHand = { -12, 0, 0 },
			LeftUpperArm = { 26, 0, -6 }, LeftLowerArm = { 22, 0, 0 },
			UpperTorso = { -9, -11, 0 }, Head = { 6, 8, 0 },
		}) },
		{ Time = 0.34, Ease = "Out", Poses = pose({
			RightUpperArm = { 50, 0, 34 }, RightLowerArm = { 6, 0, 0 }, RightHand = { -28, 0, 0 },
			LeftUpperArm = { 16, 0, -6 }, LeftLowerArm = { 16, 0, 0 },
			UpperTorso = { -12, -20, 0 }, Head = { 8, 15, 0 },
		}) },
		{ Time = 0.56, Ease = "Out", Poses = pose({}) },
	},
	ChopRight = {
		{ Time = 0, Ease = "Out", Poses = pose({}) },
		{ Time = 0.11, Ease = "In", Poses = pose({ -- up and out over the right shoulder (the chest turned left)
			RightUpperArm = { 154, 0, 40 }, RightLowerArm = { 22, 0, 0 }, RightHand = { -6, 0, 0 },
			LeftUpperArm = { 48, 0, -16 }, LeftLowerArm = { 30, 0, 0 },
			UpperTorso = { 8, 36, 0 }, Head = { -4, -28, 0 },
		}) },
		{ Time = 0.18, Ease = "Out", Poses = pose({ -- the chop, down across to the left
			RightUpperArm = { 60, 0, -22 }, RightLowerArm = { 4, 0, 0 }, RightHand = { -26, 0, 0 },
			LeftUpperArm = { 22, 0, -4 }, LeftLowerArm = { 20, 0, 0 },
			UpperTorso = { -14, 24, 0 }, Head = { 9, -18, 0 },
		}) },
		{ Time = 0.24, Ease = "Out", Poses = pose({
			RightUpperArm = { 70, 0, -18 }, RightLowerArm = { 12, 0, 0 }, RightHand = { -12, 0, 0 },
			LeftUpperArm = { 26, 0, -4 }, LeftLowerArm = { 22, 0, 0 },
			UpperTorso = { -9, 17, 0 }, Head = { 6, -12, 0 },
		}) },
		{ Time = 0.34, Ease = "Out", Poses = pose({
			RightUpperArm = { 52, 0, -28 }, RightLowerArm = { 6, 0, 0 }, RightHand = { -28, 0, 0 },
			LeftUpperArm = { 16, 0, -4 }, LeftLowerArm = { 16, 0, 0 },
			UpperTorso = { -12, 26, 0 }, Head = { 8, -19, 0 },
		}) },
		{ Time = 0.56, Ease = "Out", Poses = pose({}) },
	},

	-- Sword: a quick 3-hit combo, the blade laid forward for the two sweeps ---------------------------------
	SlashRight = {
		{ Time = 0, Ease = "Out", Poses = pose({}) },
		{ Time = 0.07, Ease = "In", Poses = pose({ -- drawn back out to the right (the chest turned right)
			RightUpperArm = { 96, 0, 72 }, RightLowerArm = { 12, 0, 0 }, RightHand = { -76, 0, 0 },
			LeftUpperArm = { 34, 0, -20 }, LeftLowerArm = { 30, 0, 0 },
			UpperTorso = { 4, -30, 0 }, Head = { 0, 22, 0 },
		}) },
		{ Time = 0.13, Ease = "Out", Poses = pose({ -- swept across to the left
			RightUpperArm = { 92, 0, -24 }, RightLowerArm = { 6, 0, 0 }, RightHand = { -80, 0, 0 },
			LeftUpperArm = { 22, 0, -6 }, LeftLowerArm = { 22, 0, 0 },
			UpperTorso = { -6, 24, 0 }, Head = { 4, -16, 0 },
		}) },
		{ Time = 0.2, Ease = "Out", Poses = pose({ -- the follow-through
			RightUpperArm = { 86, 0, -44 }, RightLowerArm = { 10, 0, 0 }, RightHand = { -74, 0, 0 },
			LeftUpperArm = { 18, 0, -6 }, LeftLowerArm = { 18, 0, 0 },
			UpperTorso = { -4, 30, 0 }, Head = { 3, -20, 0 },
		}) },
		{ Time = 0.42, Ease = "Out", Poses = pose({}) },
	},
	SlashLeft = {
		{ Time = 0, Ease = "Out", Poses = pose({}) },
		{ Time = 0.07, Ease = "In", Poses = pose({ -- drawn across the body to the left (the chest turned left)
			RightUpperArm = { 78, 0, -62 }, RightLowerArm = { 30, 0, 0 }, RightHand = { -95, 0, 0 },
			LeftUpperArm = { 22, 0, -10 }, LeftLowerArm = { 26, 0, 0 },
			UpperTorso = { 2, 32, 0 }, Head = { 0, -22, 0 },
		}) },
		{ Time = 0.13, Ease = "Out", Poses = pose({ -- the backhand, swept out to the right
			RightUpperArm = { 92, 0, 32 }, RightLowerArm = { 8, 0, 0 }, RightHand = { -80, 0, 0 },
			LeftUpperArm = { 26, 0, -14 }, LeftLowerArm = { 24, 0, 0 },
			UpperTorso = { -6, -22, 0 }, Head = { 4, 16, 0 },
		}) },
		{ Time = 0.2, Ease = "Out", Poses = pose({
			RightUpperArm = { 88, 0, 54 }, RightLowerArm = { 12, 0, 0 }, RightHand = { -74, 0, 0 },
			LeftUpperArm = { 28, 0, -16 }, LeftLowerArm = { 24, 0, 0 },
			UpperTorso = { -4, -30, 0 }, Head = { 3, 20, 0 },
		}) },
		{ Time = 0.42, Ease = "Out", Poses = pose({}) },
	},
	SlashOverhead = {
		{ Time = 0, Ease = "Out", Poses = pose({}) },
		{ Time = 0.07, Ease = "In", Poses = pose({ -- the blade up over the head
			RightUpperArm = { 160, 0, 8 }, RightLowerArm = { 16, 0, 0 }, RightHand = { -20, 0, 0 },
			LeftUpperArm = { 50, 0, -10 }, LeftLowerArm = { 30, 0, 0 },
			UpperTorso = { 6, -16, 0 }, Head = { -6, 12, 0 },
		}) },
		{ Time = 0.13, Ease = "Out", Poses = pose({ -- straight down
			RightUpperArm = { 70, 0, 0 }, RightLowerArm = { 4, 0, 0 }, RightHand = { -48, 0, 0 },
			LeftUpperArm = { 24, 0, -4 }, LeftLowerArm = { 20, 0, 0 },
			UpperTorso = { -14, 10, 0 }, Head = { 10, -8, 0 },
		}) },
		{ Time = 0.2, Ease = "Out", Poses = pose({
			RightUpperArm = { 62, 0, 0 }, RightLowerArm = { 6, 0, 0 }, RightHand = { -52, 0, 0 },
			LeftUpperArm = { 18, 0, -4 }, LeftLowerArm = { 16, 0, 0 },
			UpperTorso = { -12, 10, 0 }, Head = { 8, -8, 0 },
		}) },
		{ Time = 0.42, Ease = "Out", Poses = pose({}) },
	},

	-- Spear: drawn back to the chest, then a straight thrust with the right shoulder driving forward ------------
	Thrust = {
		{ Time = 0, Ease = "Out", Poses = pose({}) },
		{ Time = 0.12, Ease = "In", Poses = pose({ -- drawn back, the point still on the ice (the chest turned right)
			RightUpperArm = { 58, 0, -12 }, RightLowerArm = { 62, 0, 0 }, RightHand = { -30, 0, 0 },
			LeftUpperArm = { 62, 0, -30 }, LeftLowerArm = { 30, 0, 0 },
			UpperTorso = { 4, -14, 0 }, Head = { 0, 12, 0 },
		}) },
		{ Time = 0.18, Ease = "Out", Poses = pose({ -- the thrust
			RightUpperArm = { 92, 0, -6 }, RightLowerArm = { 0, 0, 0 }, RightHand = { 6, 0, 0 },
			LeftUpperArm = { 22, 0, -12 }, LeftLowerArm = { 20, 0, 0 },
			UpperTorso = { -12, 22, 0 }, Head = { 6, -16, 0 },
		}) },
		{ Time = 0.25, Ease = "Out", Poses = pose({ -- the recoil
			RightUpperArm = { 86, 0, -4 }, RightLowerArm = { 14, 0, 0 }, RightHand = { -10, 0, 0 },
			LeftUpperArm = { 26, 0, -14 }, LeftLowerArm = { 22, 0, 0 },
			UpperTorso = { -8, 16, 0 }, Head = { 4, -12, 0 },
		}) },
		{ Time = 0.5, Ease = "Out", Poses = pose({}) },
	},
	ThrustLow = {
		{ Time = 0, Ease = "Out", Poses = pose({}) },
		{ Time = 0.12, Ease = "In", Poses = pose({
			RightUpperArm = { 52, 0, -12 }, RightLowerArm = { 62, 0, 0 }, RightHand = { -34, 0, 0 },
			LeftUpperArm = { 58, 0, -28 }, LeftLowerArm = { 32, 0, 0 },
			UpperTorso = { 6, -12, 0 }, Head = { 2, 10, 0 },
		}) },
		{ Time = 0.18, Ease = "Out", Poses = pose({ -- the thrust, aimed a little lower
			RightUpperArm = { 86, 0, -4 }, RightLowerArm = { 0, 0, 0 }, RightHand = { 0, 0, 0 },
			LeftUpperArm = { 20, 0, -12 }, LeftLowerArm = { 20, 0, 0 },
			UpperTorso = { -16, 20, 0 }, Head = { 9, -14, 0 },
		}) },
		{ Time = 0.25, Ease = "Out", Poses = pose({
			RightUpperArm = { 82, 0, -2 }, RightLowerArm = { 12, 0, 0 }, RightHand = { -6, 0, 0 },
			LeftUpperArm = { 24, 0, -14 }, LeftLowerArm = { 22, 0, 0 },
			UpperTorso = { -11, 14, 0 }, Head = { 6, -10, 0 },
		}) },
		{ Time = 0.5, Ease = "Out", Poses = pose({}) },
	},
	-- the spear's legs: a short lunge, the front knee bending and the body going forward and down
	Lunge = {
		{ Time = 0, Ease = "Out", Poses = legs({ 0, 0, 0 }, {}) },
		{ Time = 0.18, Ease = "Out", Poses = legs({ 0, -0.28, -0.3 }, { { -10, 0, 0 }, { -18, 0, 0 }, { 14, 0, 0 }, { 30, 0, 0 }, { -40, 0, 0 }, { 12, 0, 0 } }) },
		{ Time = 0.5, Ease = "Out", Poses = legs({ 0, 0, 0 }, {}) },
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
	R15 = {
		Overhead = 106668462275845, FromLeft = 110464574897720, FromRight = 111143080137346, Dip = 127243049876513,
		Slam = 112147726668578, SlamRight = 82847729121210, HammerDip = 123411023403962,
		ChopLeft = 80435661491688, ChopRight = 98358725240018,
		SlashRight = 88181411707133, SlashLeft = 119961855935717, SlashOverhead = 125195537816817,
		Thrust = 76853346354718, ThrustLow = 73611655188843, Lunge = 86353792297686,
	},
}

-- A family's swing (UpgradeConfig.Tools[tier].Family), the Pick for an unknown one.
function SwingConfig.Family(name: string?)
	return SwingConfig.Families[name or "Pick"] or SwingConfig.Families.Pick
end

-- The length of the animation `name` (its last keyframe).
function SwingConfig.LengthOf(name: string): number
	local frames = SwingConfig.R15[name]
	return if frames then frames[#frames].Time else 0
end

-- A CFrame for one pose entry ({ X, Y, Z, Move = { X, Y, Z }? } in degrees and studs).
function SwingConfig.PoseCFrame(entry): CFrame
	local move = entry.Move or { 0, 0, 0 }
	return CFrame.new(move[1], move[2], move[3]) * CFrame.Angles(math.rad(entry[1]), math.rad(entry[2]), math.rad(entry[3]))
end

-- The family's next variant after `previous` (they take turns in order; never the same one twice running).
function SwingConfig.NextVariant(family, previous: string?): string
	local variants = family.Variants
	local index = previous and table.find(variants, previous) or 0
	return variants[(index % #variants) + 1]
end

-- How fast to play a swing that starts `sinceLast` seconds after the previous one began: normal speed for an
-- unhurried tap, faster (up to the family's MaxSpeed) when taps come quicker than a full swing.
function SwingConfig.SpeedFor(family, sinceLast: number?): number
	if not sinceLast or sinceLast >= family.Length then
		return 1
	end
	return math.clamp(family.Length / math.max(sinceLast, 0.01), 1, family.MaxSpeed)
end

return SwingConfig
