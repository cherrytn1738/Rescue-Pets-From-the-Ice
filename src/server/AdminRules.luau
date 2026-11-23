--[[
AdminRules: who may run admin commands, and the order every admin request goes through. Plain
values only, so tests/Admin.spec.luau can run every case. AdminService wires it to the real
RemoteFunction, players and commands (AdminCommands).

Access levels:
  "Developer"  every command: a user id on AdminConfig.AllowedUserIds, or anyone in Studio.
  nil          no admin commands at all; requests are rejected and logged.

A command: { Id, Group, Label, Params (DebugRules input specs), NoTarget?, Confirm?,
             Run(target, args, caller) -> message }
]]
local DebugRules = require(script.Parent.DebugRules)

local AdminRules = {}

function AdminRules.IsAllowlisted(userId, allowlist): boolean
	return type(userId) == "number" and type(allowlist) == "table" and table.find(allowlist, userId) ~= nil
end

-- The caller's access level: "Developer" or nil.
function AdminRules.Access(userId, isStudio: boolean, allowlist): string?
	if isStudio or AdminRules.IsAllowlisted(userId, allowlist) then
		return "Developer"
	end
	return nil
end

-- The commands an access level may see (for the window), in order, without their code.
function AdminRules.Catalog(commands, access: string?)
	local list = {}
	if access ~= "Developer" then
		return list
	end
	for _, command in commands do
		table.insert(list, {
			Id = command.Id,
			Group = command.Group,
			Label = command.Label,
			Params = command.Params or {},
			NoTarget = command.NoTarget == true,
			Confirm = command.Confirm == true,
		})
	end
	return list
end

--[[
Runs one request through every check, in order: access, rate, command, target, inputs,
confirmation. Returns { ok, message }.
request = { player, commandId, targetUserId, args, confirmed }
env = {
	isStudio, allowlist, commands ([id] = command), now, lastRequestAt ([player] = time), cooldown,
	findTarget(userId) -> player or nil, log(text)
}
]]
function AdminRules.Handle(request, env)
	local player = request.player
	local access = AdminRules.Access(player.UserId, env.isStudio, env.allowlist)
	local commandName = if type(request.commandId) == "string" then string.sub(request.commandId, 1, 40) else "?"
	if not access then
		env.log(`[Admin] REJECTED {player.Name} ({player.UserId}) tried {commandName}: not an admin`)
		return { ok = false, message = "No access" }
	end
	local last = env.lastRequestAt[player]
	if last and env.now - last < env.cooldown then
		return { ok = false, message = "Too fast" }
	end
	env.lastRequestAt[player] = env.now

	local command = type(request.commandId) == "string" and env.commands[request.commandId] or nil
	if not command then
		return { ok = false, message = "Unknown command" }
	end
	local target = nil
	if not command.NoTarget then
		local id = request.targetUserId
		target = type(id) == "number" and id % 1 == 0 and env.findTarget(id) or nil
		if not target then
			return { ok = false, message = "That player isn't in the server" }
		end
	end
	local args, problem = DebugRules.ValidateArgs(command.Params, request.args)
	if not args then
		return { ok = false, message = problem }
	end
	if command.Confirm and request.confirmed ~= true then
		return { ok = false, message = "Needs confirming" }
	end

	local ran, result = pcall(command.Run, target, args, player)
	if not ran then
		local text = tostring(result):match(":%d+: (.+)$") or tostring(result)
		env.log(`[Admin] {player.Name} {command.Id} failed: {tostring(result)}`)
		return { ok = false, message = text }
	end
	env.log(`[Admin] {player.Name} ran {command.Id}{if target then " on " .. target.Name else ""}: {result}`)
	return { ok = true, message = tostring(result) }
end

return AdminRules
