--[[
EffectsRules: the effects performance rules as pure functions (docs/GAME_DESIGN.md, "Effects and auras":
"Performance rules"), used by BuildingEffects.client and tests/Effects.spec.luau.

  AmbientScale(isOwnPlot, distance, reduced)  0..1: how much of an emitter's Rate runs. Your own plot: 1;
                                    another plot: OtherPlotRate within OtherPlotDistance studs, 0 beyond;
                                    the reduced-effects setting halves it.
  HitsAllowed(isOwnPlot, distance, reduced)   whether hit bursts play at all (never with reduced effects,
                                    never on a plot beyond OtherPlotDistance).
  TierFor(owned)                    the station tier (1-5) for a number owned (0 = none).
  HitInterval(owned)                seconds between a building's visible hits (faster with more owned).
  NewHitBucket(perSecond) -> bucket; bucket:Take(now) -> boolean   the global hit cap per second.
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local BuildingConfig = require(ReplicatedStorage.BuildingConfig)
local EffectsConfig = require(ReplicatedStorage.EffectsConfig)

local EffectsRules = {}
local RULES = EffectsConfig.Rules

function EffectsRules.AmbientScale(isOwnPlot: boolean, distance: number, reduced: boolean): number
	local scale
	if isOwnPlot then
		scale = 1
	elseif distance <= RULES.OtherPlotDistance then
		scale = RULES.OtherPlotRate
	else
		scale = 0
	end
	if reduced then
		scale *= RULES.ReducedAmbient
	end
	return scale
end

function EffectsRules.HitsAllowed(isOwnPlot: boolean, distance: number, reduced: boolean): boolean
	if reduced and not RULES.ReducedHits then
		return false
	end
	return isOwnPlot or distance <= RULES.OtherPlotDistance
end

function EffectsRules.TierFor(owned: number): number
	local tier = 0
	for index, milestone in BuildingConfig.StationMilestones do
		if owned >= milestone then
			tier = index
		end
	end
	return tier
end

function EffectsRules.HitInterval(owned: number): number
	local slow, fast = RULES.HitIntervalSeconds[1], RULES.HitIntervalSeconds[2]
	local t = math.clamp(math.log10(math.max(1, owned)) / 2, 0, 1) -- 1 copy: slow; 100 copies: fast
	return slow + (fast - slow) * t
end

local Bucket = {}
Bucket.__index = Bucket

function EffectsRules.NewHitBucket(perSecond: number?)
	local rate = perSecond or RULES.HitEffectsPerSecond
	return setmetatable({ rate = rate, tokens = rate, at = nil }, Bucket)
end

function Bucket:Take(now: number): boolean
	if self.at then
		self.tokens = math.min(self.rate, self.tokens + (now - self.at) * self.rate)
	end
	self.at = now
	if self.tokens >= 1 then
		self.tokens -= 1
		return true
	end
	return false
end

return EffectsRules
