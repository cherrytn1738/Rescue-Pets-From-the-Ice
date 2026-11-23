--[[
PaidRandomPolicy: whether a player may buy paid random items. Server only.

Roblox's rules (create.roblox.com/docs/production/monetization/paid-random-items): in some
regions players can't buy random items with Robux, or with currency bought with Robux.
PolicyService:GetPolicyInfoForPlayerAsync says so per player (ArePaidRandomItemsRestricted). It
covers every MonetizationConfig product with PaidRandom = true: hidden in the shop, refused by the
shop's requests, by gifts (buyer and recipient), and by receipts. Anything the game later sells for
a currency that Robux can buy must check IsAllowed too.

IsAllowed is true only once Roblox has said "not restricted". Until then (still asking, or every
attempt failed) the player is treated as restricted: fail closed, then ask again a little later.
The player attribute PaidRandomItems ("Allowed" / "Restricted") is a display copy for the UI;
the server never reads it back.

Studio: the Workspace attribute StudioPaidRandomRestricted (true) treats everyone as restricted,
to test the restricted shop. Read only in Studio.
]]
local Players = game:GetService("Players")
local PolicyService = game:GetService("PolicyService")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local PaidRandomPolicy = {}

local ATTEMPTS = 3
local RETRY_SECONDS = 2
local ASK_AGAIN_SECONDS = 60 -- after every attempt failed

local allowed = {} -- [player] = true once Roblox said "not restricted"
local answered = {} -- [player] = true once Roblox answered at all

PaidRandomPolicy.REFUSED = "Random items bought with Robux aren't available in your region."

local function studioRestricted(): boolean
	return RunService:IsStudio() and Workspace:GetAttribute("StudioPaidRandomRestricted") == true
end

function PaidRandomPolicy.IsAllowed(player: Player): boolean
	return allowed[player] == true and not studioRestricted()
end

-- Waits (up to `seconds`) until Roblox has answered for this player, then IsAllowed. A receipt
-- retried at join arrives before the answer; it waits here rather than being refused.
function PaidRandomPolicy.WaitForAnswer(player: Player, seconds: number): boolean
	local deadline = os.clock() + seconds
	while not answered[player] and os.clock() < deadline and player.Parent == Players do
		task.wait(0.2)
	end
	return PaidRandomPolicy.IsAllowed(player)
end

local function publish(player: Player)
	if player.Parent == Players then
		player:SetAttribute("PaidRandomItems", if PaidRandomPolicy.IsAllowed(player) then "Allowed" else "Restricted")
	end
end

-- Asks Roblox. Returns true (restricted), false (allowed) or nil (couldn't find out).
local function ask(player: Player): boolean?
	for attempt = 1, ATTEMPTS do
		local ok, info = pcall(PolicyService.GetPolicyInfoForPlayerAsync, PolicyService, player)
		if ok and type(info) == "table" and type(info.ArePaidRandomItemsRestricted) == "boolean" then
			return info.ArePaidRandomItemsRestricted
		end
		if attempt < ATTEMPTS then
			task.wait(RETRY_SECONDS * attempt)
		end
	end
	return nil
end

local function check(player: Player)
	while player.Parent == Players do
		local restricted = ask(player)
		if restricted ~= nil then
			allowed[player] = not restricted or nil
			answered[player] = true
			publish(player)
			return
		end
		warn(`[PaidRandom] couldn't read {player.Name}'s policy; treated as restricted, asking again soon`)
		publish(player)
		task.wait(ASK_AGAIN_SECONDS)
	end
end

function PaidRandomPolicy.Start()
	local function added(player: Player)
		publish(player) -- "Restricted" until Roblox answers
		task.spawn(check, player)
	end
	Players.PlayerAdded:Connect(added)
	for _, player in Players:GetPlayers() do
		added(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		allowed[player], answered[player] = nil, nil
	end)
	if RunService:IsStudio() then
		Workspace:GetAttributeChangedSignal("StudioPaidRandomRestricted"):Connect(function()
			for _, player in Players:GetPlayers() do
				publish(player)
			end
		end)
	end
end

return PaidRandomPolicy
