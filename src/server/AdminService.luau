-- The admin window's server side (F3, developer only). Server only.
--
-- One RemoteFunction, AdminRequest. Access: the AdminConfig allowlist in live servers, everyone in
-- Studio. The AdminAccess attribute only tells a client to build the window; the server never reads
-- it back. Access is checked on EVERY request; everyone else is rejected and logged
-- ("[Admin] REJECTED").
--   ("Catalog")                                    -> the commands this player may run, or nil
--   ("Run", { Action, Target, Args, Confirmed })   -> { ok, message }
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local AdminCommands = require(script.Parent.AdminCommands)
local AdminConfig = require(script.Parent.AdminConfig)
local AdminRules = require(script.Parent.AdminRules)

local AdminService = {}

local lastRequestAt = {} -- [player] = os.clock() of their last command

local function access(player: Player): string?
	return AdminRules.Access(player.UserId, RunService:IsStudio(), AdminConfig.AllowedUserIds)
end

-- A refused request is logged at most once a minute per user id, so someone spamming the remote can't flood
-- the server's log (they are refused every time all the same).
local REJECT_LOG_SECONDS = 60
local rejectLoggedAt = {} -- [user id text] = os.clock()
local function log(text: string)
	if string.find(text, "REJECTED", 1, true) then
		local userId = string.match(text, "%((%-?%d+)%)") or "?"
		local now = os.clock()
		if rejectLoggedAt[userId] and now - rejectLoggedAt[userId] < REJECT_LOG_SECONDS then
			return
		end
		rejectLoggedAt[userId] = now
		warn(text)
	elseif string.find(text, "failed", 1, true) then
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
		return AdminRules.Handle({
			player = player,
			commandId = request.Action,
			targetUserId = request.Target,
			args = request.Args,
			confirmed = request.Confirmed,
		}, {
			isStudio = RunService:IsStudio(),
			allowlist = AdminConfig.AllowedUserIds,
			commands = AdminCommands.ById,
			now = os.clock(),
			lastRequestAt = lastRequestAt,
			cooldown = AdminConfig.RequestCooldownSeconds,
			findTarget = findTarget,
			log = log,
		})
	end
	local level = access(player)
	if not level then
		log(`[Admin] REJECTED {player.Name} ({player.UserId}) asked for the admin window: not an admin`)
		return nil
	end
	if kind == "Catalog" then
		return AdminRules.Catalog(AdminCommands.List, level)
	end
	return nil
end

function AdminService.Start()
	local remote = ReplicatedStorage:WaitForChild("AdminRequest") :: RemoteFunction
	remote.OnServerInvoke = onRequest

	local function onPlayerAdded(player: Player)
		if access(player) then
			player:SetAttribute("AdminAccess", true)
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

return AdminService
