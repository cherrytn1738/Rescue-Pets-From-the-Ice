--[[
CodeService: redeeming promo codes (the Codes window). Server only.

One RemoteFunction, RedeemCode: (text) -> { ok, message }. The client sends only what was typed.
The server normalizes it, rate-limits the player, checks the code (CodesConfig, CodeRules) against
the player's save, and grants the reward through PurchaseRewards (the same path a Robux product
uses). The grant and the code going into the save's Codes list happen together, with no yield in
between, so a code can't pay twice; then an important save is asked for.

Studio: [Codes] lines in Output say what each attempt did (redeemed, or why not).
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local CodeRules = require(script.Parent.CodeRules)
local CodesConfig = require(script.Parent.CodesConfig)
local PlayerData = require(script.Parent.PlayerData)
local PurchaseRewards = require(script.Parent.PurchaseRewards)

local CodeService = {}

CodeRules.Validate(CodesConfig)

local attempts = {} -- [player] = { os.clock() of recent attempts }

local function log(text: string)
	if RunService:IsStudio() then
		print("[Codes] " .. text)
	end
end

-- The code's reward as a product PurchaseRewards understands. Name: how the reward reads in
-- messages; a code can set its own (entry.Name), otherwise it is a plain "reward".
local function asProduct(code: string, entry)
	return { Key = "Code_" .. code, Name = entry.Name or "reward", Reward = entry.Reward }
end

-- Redeems one code for a player. Returns { ok, message }. Public for the spec and debug menu.
function CodeService.Redeem(player: Player, text): { ok: boolean, message: string }
	local history = attempts[player]
	if not history then
		history = {}
		attempts[player] = history
	end
	if not CodeRules.AllowAttempt(history, os.clock(), CodesConfig.RateLimit) then
		return { ok = false, message = CodeRules.Messages.TooFast }
	end
	if type(text) ~= "string" or string.match(text, "^%s*$") then
		return { ok = false, message = CodeRules.Messages.Empty }
	end
	local data = PlayerData.Edit(player)
	if not data then
		return { ok = false, message = CodeRules.Messages.DataNotReady }
	end
	local code = CodeRules.Normalize(string.sub(text, 1, 64))
	local entry = CodeRules.Find(CodesConfig, code)
	local ok, why = CodeRules.Check(entry, code, data.Codes, os.time())
	if not ok then
		log(`{player.Name} tried "{string.sub(text, 1, 32)}": {why}`)
		return { ok = false, message = CodeRules.Messages[why] }
	end
	-- Grant and record together (Give never yields). A reward that can't apply now records nothing,
	-- so the code still works once it can.
	local given, problem = PurchaseRewards.Give(player, asProduct(code :: string, entry))
	if not given then
		log(`{player.Name} redeemed {code}: refused ({problem})`)
		return { ok = false, message = problem or "That code can't be used right now." }
	end
	table.insert(data.Codes, code)
	PlayerData.MarkImportant(player)
	PlayerData.Publish(player)
	log(`{player.Name} redeemed {code}: {given}`)
	return { ok = true, message = `Code redeemed: {given}!` }
end

-- Debug menu: forget every code this player redeemed. Returns how many there were.
function CodeService.ResetRedeemed(player: Player): number
	local data = PlayerData.Edit(player)
	if not data then
		error(`{player.Name}'s data isn't ready`, 0)
	end
	local count = #data.Codes
	table.clear(data.Codes)
	PlayerData.MarkImportant(player)
	return count
end

function CodeService.Start()
	local remote = ReplicatedStorage:WaitForChild("RedeemCode") :: RemoteFunction
	remote.OnServerInvoke = function(player, text)
		return CodeService.Redeem(player, text)
	end
	Players.PlayerRemoving:Connect(function(player)
		attempts[player] = nil
	end)
end

return CodeService
