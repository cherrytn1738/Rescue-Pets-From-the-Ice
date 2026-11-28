--[[
PickSwing (client): the swing of the tool you hold, on every tap (SwingConfig: its family's variants take turns,
Pick, Hammer, Axe, Sword or Spear). Played with the local character's Animator, so every player sees it (a
character's animations replicate from its owner).
 * The tap's own effects and sound fire on the click (TapFeedback); the swing is the show.
 * Taps faster than a full swing never queue: the next swing cuts in (blending over SwingConfig.FadeIn, starting
   part way into its wind-up so its strike comes sooner) and plays faster (SwingConfig.SpeedFor, up to the family's
   MaxSpeed).
 * The knees (the family's Dip: a dip, the hammer's deeper one, the spear's lunge) only while the character is
   (nearly) standing still, so walking legs stay free.
 * At the strike: the family's camera nudge (Effects.Nudge: none with reduced effects) and a drill's bit spinning
   (ToolFX.SpinBit).
 * Swords and the magical tools draw a trail during the slash (ToolFX.Trail: the tool's SwingTrail, in the tier's
   spark colour; not with reduced effects). Other players see both through ToolFX too.
 * An R6 avatar, or a variant with no uploaded animation, gets the default tool slash instead.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local SwingConfig = require(ReplicatedStorage.SwingConfig)
local Effects = require(script.Parent.Effects)
local ToolFX = require(script.Parent.ToolFX)

local PickSwing = {}

PickSwing.ToolName = "IceTool" -- (PickService's name for the held tool)

local player = Players.LocalPlayer
local loaded = nil -- { character, tracks = { [name] = AnimationTrack } }
local lastVariant: string? = nil
local lastFamily: string? = nil
local lastStart: number? = nil

local function tracksFor(character: Model)
	if loaded and loaded.character == character then
		return loaded.tracks
	end
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	local animator = humanoid and humanoid:FindFirstChildOfClass("Animator")
	if not animator or humanoid.RigType ~= Enum.HumanoidRigType.R15 then
		return nil
	end
	local tracks = {}
	for name, id in SwingConfig.AnimationIds.R15 do
		if id > 0 then
			local animation = Instance.new("Animation")
			animation.AnimationId = "rbxassetid://" .. id
			local ok, track = pcall(animator.LoadAnimation, animator, animation)
			if ok and track then
				track.Priority = Enum.AnimationPriority.Action
				track.Looped = false
				tracks[name] = track
			end
		end
	end
	loaded = { character = character, tracks = tracks }
	return tracks
end

-- The old swing: the default Animate script's tool slash.
local function defaultSlash(tool: Tool)
	if not tool:FindFirstChild("toolanim") then
		local anim = Instance.new("StringValue")
		anim.Name = "toolanim"
		anim.Value = "Slash"
		anim.Parent = tool
	end
end

function PickSwing.Swing()
	local character = player.Character
	local tool = character and character:FindFirstChild(PickSwing.ToolName)
	if not tool or not tool:IsA("Tool") then
		return
	end
	local familyName = tool:GetAttribute("Family") or "Pick"
	local family = SwingConfig.Family(familyName)
	local tracks = tracksFor(character)
	local now = os.clock()
	local sameFamily = lastFamily == familyName
	local variant = SwingConfig.NextVariant(family, if sameFamily then lastVariant else nil)
	local track = tracks and tracks[variant]
	if not track then
		defaultSlash(tool)
		return
	end
	local since = if lastStart and sameFamily then now - lastStart else nil
	local speed = SwingConfig.SpeedFor(family, since)
	-- cutting into a swing still going: start at the middle of the wind-up, so the strike comes sooner
	local startAt = if since and since < family.Length then family.WindUpEnd * 0.5 else 0
	for name, other in tracks do
		if name ~= variant and other.IsPlaying then
			other:Stop(SwingConfig.FadeIn)
		end
	end
	track:Play(SwingConfig.FadeIn, 1, speed)
	track.TimePosition = startAt
	local root = character:FindFirstChild("HumanoidRootPart")
	local dip = tracks[family.Dip]
	if dip and root and (root.AssemblyLinearVelocity * Vector3.new(1, 0, 1)).Magnitude < SwingConfig.DipWhenSlowerThan then
		dip:Play(SwingConfig.FadeIn, 1, speed)
		dip.TimePosition = startAt
	end
	lastVariant, lastFamily, lastStart = variant, familyName, now
	local function current()
		return lastStart == now -- (not when the next swing already cut in)
	end
	if ToolFX.HasTrail(tool, family) then
		ToolFX.Trail(tool, family, startAt, speed, current)
	end
	task.delay(math.max(0, family.ImpactAt - startAt) / speed, function()
		if current() then
			Effects.Nudge(family.Nudge.Strength, family.Nudge.Seconds)
			ToolFX.SpinBit(tool)
		end
	end)
end

-- The variant last played (the visual review's swing shots).
function PickSwing.LastVariant(): string?
	return lastVariant
end

return PickSwing
