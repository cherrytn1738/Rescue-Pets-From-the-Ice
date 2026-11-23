--[[
AdminCommands: everything the admin window (F3) can do. Server only. Developer only: AdminRules
checks who may run a command, and its inputs, on every request.

One entry per command:
	{
		Id = "UniqueId", Group = "Window section", Label = "Button text",
		Params = { ...input specs, see DebugRules... },   -- optional
		NoTarget = true,   -- the command doesn't apply to one player
		Confirm = true,    -- optional: the window asks "Sure?" before sending
		Run = function(target, args, caller) ... return "Short result message" end,
	}
Refuse with fail("message"). Commands go through the game's own systems; add the game's live-ops
commands (events, announcements...) here as those systems are built.
]]
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local AdminConfig = require(script.Parent.AdminConfig)
local PlayerEffects = require(script.Parent.PlayerEffects)

local function fail(message: string)
	error(message, 0)
end

-- One effect at a time: refuse while the target is still under another one.
local function notBusy(target: Player)
	local effect = PlayerEffects.Busy(target)
	if effect then
		fail(`{target.Name} is {effect} right now; try again in a moment`)
	end
end

local COMMANDS = {
	-- Server
	{
		Id = "ServerInfo", Group = "Server", Label = "Server info (players, uptime, version)",
		NoTarget = true,
		Run = function()
			local uptime = math.floor(Workspace.DistributedGameTime)
			local kind = if game.PrivateServerId ~= "" then "private" else "public"
			return `{#Players:GetPlayers()} / {Players.MaxPlayers} players, up {uptime // 60} min {uptime % 60} s, place version {game.PlaceVersion}, {kind} server {if game.JobId ~= "" then game.JobId else "(Studio)"}`
		end,
	},

	-- Players: short and harmless (PlayerEffects), one at a time per target.
	{
		Id = "Launch", Group = "Players", Label = "Launch the target player into the air",
		Run = function(target)
			notBusy(target)
			PlayerEffects.Launch(target)
			return `Launched {target.Name}`
		end,
	},
	{
		Id = "Rocket", Group = "Players", Label = "Rocket the target up (they come back down)",
		Run = function(target)
			notBusy(target)
			PlayerEffects.Rocket(target)
			return `Rocketed {target.Name}`
		end,
	},
	{
		Id = "Jail", Group = "Players", Label = `Jail the target ({AdminConfig.JailSeconds} s in a cage)`,
		Run = function(target)
			notBusy(target)
			PlayerEffects.Jail(target)
			return `Jailed {target.Name} for {AdminConfig.JailSeconds} s`
		end,
	},
	{
		Id = "Kick", Group = "Players", Label = "Kick the target from this server (they can rejoin)",
		Confirm = true,
		Run = function(target, _, caller)
			if target == caller then
				fail("Kicking yourself? Leave the game instead")
			end
			target:Kick("You were removed from this server by the developer.")
			return `Kicked {target.Name}`
		end,
	},
}

local byId = {}
for _, command in COMMANDS do
	assert(byId[command.Id] == nil, "duplicate admin command " .. command.Id)
	byId[command.Id] = command
end

return {
	List = COMMANDS,
	ById = byId,
}
