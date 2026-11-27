--[[
TapService: tapping the ice (docs/GAME_DESIGN.md, "Technical design" and "UI and controls"). Server
only.

The client counts taps and sends the total every GameConfig.Taps.BatchSeconds on TapBatch. The
server:
 - accepts a whole number only, and only while the player stands in their own plot;
 - allows at most MaxPerSecond taps a second: a bucket that refills at that rate and holds at most
   BurstSeconds' worth, so a late batch isn't punished but an autoclicker can't beat the cap. Taps
   over the cap are dropped, and a player who keeps going over is logged ([Taps]) now and then;
 - hits the block with taps x EconomyRules.TapDamage (IceBlockService pays the crystals).
AddTaps(player, count) is the same path for taps the server makes itself; AutoTaps(player, count) lands the
Auto Pick pass's taps through the same bucket (so with your own taps they never pass the cap), quietly.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local EconomyRules = require(ReplicatedStorage.EconomyRules)
local GameConfig = require(ReplicatedStorage.GameConfig)
local Economy = require(script.Parent.Economy)
local IceBlockService = require(script.Parent.IceBlockService)
local PlayerData = require(script.Parent.PlayerData)
local PlotService = require(script.Parent.PlotService)

local TapService = {}

local TAPS = GameConfig.Taps
local MAX_BATCH = 1000 -- anything bigger isn't a tap count
local buckets = {} -- [player] = { tokens, at, over, loggedAt }
local tapListeners = {}

-- callback(player, taps) after taps land (the tutorial and analytics watch the first one).
function TapService.OnTaps(callback)
	table.insert(tapListeners, callback)
end

local function bucketOf(player: Player)
	local bucket = buckets[player]
	if not bucket then
		bucket = { tokens = TAPS.MaxPerSecond * TAPS.BurstSeconds, at = os.clock(), over = 0, loggedAt = -math.huge }
		buckets[player] = bucket
	end
	local now = os.clock()
	bucket.tokens = math.min(TAPS.MaxPerSecond * TAPS.BurstSeconds, bucket.tokens + (now - bucket.at) * TAPS.MaxPerSecond)
	bucket.at = now
	return bucket
end

-- How many of `count` taps are allowed now (and takes them from the bucket).
function TapService.Allow(player: Player, count: number): number
	local bucket = bucketOf(player)
	local allowed = math.min(count, math.floor(bucket.tokens))
	bucket.tokens -= allowed
	if allowed < count then
		bucket.over += count - allowed
		if os.clock() - bucket.loggedAt >= TAPS.OverLimitLogSeconds then
			bucket.loggedAt = os.clock()
			warn(`[Taps] {player.Name} ({player.UserId}) is tapping faster than {TAPS.MaxPerSecond}/s: {bucket.over} taps dropped so far`)
		end
	end
	return allowed
end

-- The Auto Pick pass's taps: taken from the same bucket as the player's own (never logged as too fast).
function TapService.AutoTaps(player: Player, count: number): number
	local bucket = bucketOf(player)
	local allowed = math.min(count, math.floor(bucket.tokens))
	if allowed <= 0 then
		return 0
	end
	bucket.tokens -= allowed
	return TapService.AddTaps(player, allowed, "AutoPick")
end

-- Lands `count` taps on the player's block. Returns the damage dealt. source: analytics ("Taps" or
-- "AutoPick").
function TapService.AddTaps(player: Player, count: number, source: string?): number
	local data = PlayerData.Edit(player)
	if not data or count <= 0 then
		return 0
	end
	local damage = IceBlockService.Damage(player, data, count * EconomyRules.TapDamage(data), source or "Taps")
	if damage > 0 then
		Economy.RecordTaps(player, count)
		for _, callback in tapListeners do
			task.spawn(callback, player, count)
		end
	end
	return damage
end

local function onBatch(player: Player, count)
	if type(count) ~= "number" or count ~= count or count % 1 ~= 0 or count < 1 or count > MAX_BATCH then
		return
	end
	if not PlotService.InOwnPlot(player) then
		return
	end
	local allowed = TapService.Allow(player, count)
	if allowed > 0 then
		TapService.AddTaps(player, allowed)
	end
end

function TapService.Start()
	local remote = ReplicatedStorage:WaitForChild("TapBatch") :: RemoteEvent
	remote.OnServerEvent:Connect(onBatch)
	Players.PlayerRemoving:Connect(function(player)
		buckets[player] = nil
	end)
end

return TapService
