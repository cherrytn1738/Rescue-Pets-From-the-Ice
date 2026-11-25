--[[
SoundRules: when a game sound plays (pure rules, no Instances; settings in AudioConfig.Rules; spec
tests/SoundRules.spec.luau). The client scripts ask these, then play through Audio.

 * SoundRules.TapLimiter(settings)            limiter:Allow(now) -> boolean: your own tap sounds, capped
 * SoundRules.TapSpeed(streak, settings, r)   the playback speed of a tap (a fast streak sounds higher)
 * SoundRules.ChipGate(settings, random)      gate:Allow(now, isMine, lastTapAt) -> boolean: a building's hit
 * SoundRules.RescueCue(isMine, rarity, distance, settings) -> (cue name?, volume scale)
 * SoundRules.TickGate(settings, random)      gate:Allow(now, lastTapAt) -> boolean: the income tick
 * SoundRules.PickVariant(count, last, r)     a variant index, never `last` again when there is a choice
]]
local SoundRules = {}

-- At most settings.MaxOverlap tap sounds at once (each lasts settings.Length seconds), at least
-- settings.MinGap apart. An autoclicker at any rate gets the same few overlapping sounds.
function SoundRules.TapLimiter(settings)
	local limiter = { playing = {}, last = -math.huge }
	function limiter:Allow(now: number): boolean
		if now - self.last < settings.MinGap then
			return false
		end
		local still = {}
		for _, startedAt in self.playing do
			if now - startedAt < settings.Length then
				table.insert(still, startedAt)
			end
		end
		self.playing = still
		if #still >= settings.MaxOverlap then
			return false
		end
		table.insert(still, now)
		self.last = now
		return true
	end
	function limiter:Playing(now: number): number
		local count = 0
		for _, startedAt in self.playing do
			if now - startedAt < settings.Length then
				count += 1
			end
		end
		return count
	end
	return limiter
end

-- 1 + up to StreakPitch, by how long the fast streak is (Audio adds the entry's own random PitchJitter).
function SoundRules.TapSpeed(streak: number, settings): number
	local share = math.clamp(streak / settings.StreakMax, 0, 1)
	return 1 + settings.StreakPitch * share
end

-- A building's hit on a block: only your own block, at most every MinGap seconds, with Chance, and not
-- just after your own tap (the tap sound covers it). random() -> [0, 1).
function SoundRules.ChipGate(settings, random: () -> number)
	local gate = { last = -math.huge }
	function gate:Allow(now: number, isMine: boolean, lastTapAt: number?): boolean
		if not isMine or now - self.last < settings.MinGap then
			return false
		end
		if lastTapAt and now - lastTapAt < settings.QuietAfterTap then
			return false
		end
		if random() >= settings.Chance then
			self.last = now -- a skipped chance still waits a full gap, so chips stay occasional
			return false
		end
		self.last = now
		return true
	end
	return gate
end

-- Which rescue jingle plays for a shatter, and how loud (a share of the jingle's own volume). Your own:
-- always, full volume. Other players': only settings.Rarities, within settings.MaxDistance studs, quieter.
function SoundRules.RescueCue(isMine: boolean, rarity: string?, distance: number, settings): (string?, number)
	if type(rarity) ~= "string" then
		return nil, 0
	end
	if isMine then
		return "Rescue" .. rarity, 1
	end
	if settings.Rarities[rarity] and distance == distance and distance <= settings.MaxDistance then
		return "Rescue" .. rarity, settings.Volume
	end
	return nil, 0
end

-- The income tick: at most every MinGap seconds, each time with Chance (so it never ticks like a clock),
-- and quiet while you're tapping. random() -> [0, 1).
function SoundRules.TickGate(settings, random: () -> number)
	local gate = { last = -math.huge }
	function gate:Allow(now: number, lastTapAt: number?): boolean
		if now - self.last < settings.MinGap or (lastTapAt and now - lastTapAt < settings.QuietAfterTap) then
			return false
		end
		self.last = now
		return random() < settings.Chance
	end
	return gate
end

-- random(n) -> 1..n (math.random's shape).
function SoundRules.PickVariant(count: number, last: number?, random: (number) -> number): number
	if count <= 1 then
		return 1
	end
	if not last or last < 1 or last > count then
		return random(count)
	end
	local pick = random(count - 1)
	return if pick >= last then pick + 1 else pick
end

return SoundRules
