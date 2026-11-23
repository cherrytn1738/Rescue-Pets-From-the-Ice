--[[
DebugRules: who may use the debug menu, how a request's inputs are checked, and the order every
request goes through. Plain values only, so tests/Debug.spec.luau can run every case.
DebugService wires it to the real RemoteFunction, players and actions.

An action's Params is a list of input specs:
	{ Name, Label, Kind = "number", Min, Max, Integer?, Default? }
	{ Name, Label, Kind = "choice", Choices = { { Value, Label } }, Default? }
	{ Name, Label, Kind = "text", MaxLength, Pattern, Optional? }
]]
local DebugRules = {}

-- Studio: everyone in the test. Anywhere else: only user ids on the allowlist.
function DebugRules.HasAccess(userId, isStudio: boolean, allowlist): boolean
	if isStudio then
		return true
	end
	return type(userId) == "number" and type(allowlist) == "table" and table.find(allowlist, userId) ~= nil
end

local function isFinite(value): boolean
	return type(value) == "number" and value == value and value > -math.huge and value < math.huge
end

-- Checks one input. Returns the clean value, or nil and why.
local function checkParam(param, value)
	if param.Kind == "number" then
		if value == nil and param.Default ~= nil then
			return param.Default
		end
		if not isFinite(value) then
			return nil, `{param.Label} must be a number`
		end
		if param.Integer and value % 1 ~= 0 then
			return nil, `{param.Label} must be a whole number`
		end
		if value < param.Min or value > param.Max then
			return nil, `{param.Label} must be {param.Min} to {param.Max}`
		end
		return value
	elseif param.Kind == "choice" then
		if value == nil and param.Default ~= nil then
			value = param.Default
		end
		for _, choice in param.Choices do
			if choice.Value == value then
				return value
			end
		end
		return nil, `Unknown {param.Label}`
	elseif param.Kind == "text" then
		if value == nil or value == "" then
			if param.Optional then
				return ""
			end
			return nil, `{param.Label} is required`
		end
		if type(value) ~= "string" or #value > param.MaxLength or not string.match(value, param.Pattern) then
			return nil, `{param.Label} has characters or a length that isn't allowed`
		end
		return value
	end
	return nil, "Bad input definition"
end

-- Checks every input an action takes. Extra keys are ignored. Returns the clean args, or nil and why.
function DebugRules.ValidateArgs(params, raw)
	if raw ~= nil and type(raw) ~= "table" then
		return nil, "Bad request"
	end
	raw = raw or {}
	local args = {}
	for _, param in params or {} do
		local value, problem = checkParam(param, raw[param.Name])
		if value == nil then
			return nil, problem
		end
		args[param.Name] = value
	end
	return args, nil
end

--[[
Runs one request through every check, in order. Returns { ok, message }.
request = { player, actionId, targetUserId, args, confirmed }
env = {
	isStudio, allowlist, actions ([id] = action), now, lastRequestAt ([player] = time),
	cooldown, findTarget(userId) -> player or nil, log(text)
}
An action: { Id, Label, Params, NoTarget?, Confirm?, Run(target, args, player) -> message }
Run may error with a message ("X's data isn't ready"); that becomes a refusal.
]]
function DebugRules.Handle(request, env)
	local player = request.player
	if not DebugRules.HasAccess(player.UserId, env.isStudio, env.allowlist) then
		env.log(`[Debug] REJECTED {player.Name} ({player.UserId}): no debug access`)
		return { ok = false, message = "No access" }
	end
	local last = env.lastRequestAt[player]
	if last and env.now - last < env.cooldown then
		return { ok = false, message = "Too fast" }
	end
	env.lastRequestAt[player] = env.now

	local action = type(request.actionId) == "string" and env.actions[request.actionId] or nil
	if not action then
		return { ok = false, message = "Unknown action" }
	end
	local target = nil
	if not action.NoTarget then
		local id = request.targetUserId
		target = type(id) == "number" and id % 1 == 0 and env.findTarget(id) or nil
		if not target then
			return { ok = false, message = "That player isn't in the server" }
		end
	end
	local args, problem = DebugRules.ValidateArgs(action.Params, request.args)
	if not args then
		return { ok = false, message = problem }
	end
	if action.Confirm and request.confirmed ~= true then
		return { ok = false, message = "Needs confirming" }
	end

	local ran, result = pcall(action.Run, target, args, player)
	if not ran then
		-- An error() with a plain message from an action is a refusal; anything else is a bug.
		local text = tostring(result):match(":%d+: (.+)$") or tostring(result)
		env.log(`[Debug] {player.Name} {action.Id} failed: {tostring(result)}`)
		return { ok = false, message = text }
	end
	env.log(`[Debug] {player.Name} ran {action.Id}{if target then " on " .. target.Name else ""}: {result}`)
	return { ok = true, message = tostring(result) }
end

return DebugRules
