--[[
PickSwing (client): the ice pick's swing on every tap (SwingConfig). The variants take turns (Overhead, FromLeft,
FromRight). Played with the local character's Animator, so every player sees it (a character's animations
replicate from its owner).
 * The tap's own effects and sound fire on the click (TapFeedback); the swing is the show.
 * Taps faster than a full swing never queue: the next swing cuts in (blending over SwingConfig.FadeIn, starting
   part way into its wind-up so its strike comes sooner) and plays faster (SwingConfig.SpeedFor, up to MaxSpeed).
 * The knees dip (the Dip animation) only while the character is (nearly) standing still, so walking legs stay
   free.
 * A tiny camera nudge on the strike (Effects.Nudge: none with reduced effects).
 * An R6 avatar, or a variant with no uploaded animation, gets the default tool slash instead.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local SwingConfig = require(ReplicatedStorage.SwingConfig)
local Effects = require(script.Parent.Effects)

local PickSwing = {}

local player = Players.LocalPlayer
local loaded = nil -- { character, tracks = { [name] = AnimationTrack } }
local lastVariant: string? = nil
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
	local tool = character and character:FindFirstChild("IcePick")
	if not tool or not tool:IsA("Tool") then
		return
	end
	local tracks = tracksFor(character)
	local now = os.clock()
	local variant = SwingConfig.NextVariant(lastVariant)
	local track = tracks and tracks[variant]
	if not track then
		defaultSlash(tool)
		return
	end
	local since = if lastStart then now - lastStart else nil
	local speed = SwingConfig.SpeedFor(since)
	-- cutting into a swing still going: start at the middle of the wind-up, so the strike comes sooner
	local startAt = if since and since < SwingConfig.Length then SwingConfig.WindUpEnd * 0.5 else 0
	for name, other in tracks do
		if name ~= variant and name ~= "Dip" and other.IsPlaying then
			other:Stop(SwingConfig.FadeIn)
		end
	end
	track:Play(SwingConfig.FadeIn, 1, speed)
	track.TimePosition = startAt
	local root = character:FindFirstChild("HumanoidRootPart")
	local dip = tracks.Dip
	if dip and root and (root.AssemblyLinearVelocity * Vector3.new(1, 0, 1)).Magnitude < SwingConfig.DipWhenSlowerThan then
		dip:Play(SwingConfig.FadeIn, 1, speed)
		dip.TimePosition = startAt
	end
	lastVariant, lastStart = variant, now
	task.delay(math.max(0, SwingConfig.ImpactAt - startAt) / speed, function()
		if lastStart == now then -- (not when the next swing already cut in)
			Effects.Nudge(SwingConfig.Nudge.Strength, SwingConfig.Nudge.Seconds)
		end
	end)
end

-- The variant last played (the visual review's swing shots).
function PickSwing.LastVariant(): string?
	return lastVariant
end

return PickSwing
