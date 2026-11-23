-- The debug menu's server side. Server only.
-- Access (DebugRules.HasAccess): every player in Studio; outside Studio only DebugConfig's
-- allowlist. It is checked on EVERY request, not just when the menu opens; refusals are logged.
-- Players with access get the DebugAccess attribute, which only tells their client to build the
-- menu; the server never reads it back.
--
-- One RemoteFunction, DebugRequest:
--   ("Catalog")                          -> the action list, or nil
--   ("Run", { Action, Target, Args, Confirmed }) -> { ok, message }
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local DebugActions = require(script.Parent.DebugActions)
local DebugConfig = require(script.Parent.DebugConfig)
local DebugRules = require(script.Parent.DebugRules)

local DebugService = {}

local lastRequestAt = {}

local function hasAccess(player: Player): boolean
	return DebugRules.HasAccess(player.UserId, RunService:IsStudio(), DebugConfig.AllowedUserIds)
end

local function log(text: string)
	if string.find(text, "REJECTED", 1, true) or string.find(text, "failed", 1, true) then
		warn(text)
	else
		print(text)
	end
end

local function findTarget(userId: number): Player?
	local player = Players:GetPlayerByUserId(userId)
	return if player and player.Parent == Players then player else nil
end

local function onRequest(player: Player, kind, payload)
	if kind == "Run" then
		local request = if type(payload) == "table" then payload else {}
		return DebugRules.Handle({
			player = player,
			actionId = request.Action,
			targetUserId = request.Target,
			args = request.Args,
			confirmed = request.Confirmed,
		}, {
			isStudio = RunService:IsStudio(),
			allowlist = DebugConfig.AllowedUserIds,
			actions = DebugActions.ById,
			now = os.clock(),
			lastRequestAt = lastRequestAt,
			cooldown = DebugConfig.RequestCooldownSeconds,
			findTarget = findTarget,
			log = log,
		})
	end
	if not hasAccess(player) then
		log(`[Debug] REJECTED {player.Name} ({player.UserId}): no debug access`)
		return nil
	end
	if kind == "Catalog" then
		return DebugActions.Catalog
	end
	return nil
end

function DebugService.Start()
	local remote = ReplicatedStorage:WaitForChild("DebugRequest") :: RemoteFunction
	remote.OnServerInvoke = onRequest

	local function onPlayerAdded(player: Player)
		if hasAccess(player) then
			player:SetAttribute("DebugAccess", true)
		end
	end
	Players.PlayerAdded:Connect(onPlayerAdded)
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		lastRequestAt[player] = nil
	end)
end

return DebugService
