--[[
SoftShutdown: when this server closes for an update, everyone's save is written first, they see
"Updating the game, back in a moment" and they come straight back on a new server. Server only.

How a server gets closed, and what happens (game:BindToClose's CloseReason, SoftShutdown.Plan):
  * DeveloperUpdate: "Restart Servers" on the Creator Hub (the game > Configurations > Server
    management; tick "Restart only servers with outdated versions"). Roblox itself teleports everyone
    on this server to one new server running the latest version. We show the update screen and save
    everyone first ("Message").
  * RobloxMaintenance: the same, when Roblox restarts servers for its own reasons.
  * DeveloperShutdown: "Shut Down All Servers". Roblox would only disconnect everyone, so we save,
    show the update screen and teleport everyone to a temporary reserved server (the holding server),
    which sends them back to a new public server a few seconds later ("Hop"). In Studio (pressing
    Stop is a DeveloperShutdown) nothing can teleport, so it only logs what it would do ("StudioLog").
  * Anything else (ServerEmpty, OutOfMemory, Moderation, Unknown): nothing extra; PlayerData saves.
A delayed restart ("Delay server restart" on the Hub) fires DataModel.ServerRestartScheduled first:
everyone is told how many minutes are left (again at one minute), and every save is marked important.

The holding server is a reserved server (PrivateServerId set, no owner). This game reserves servers
for nothing else, so ServerMain checks IsHoldingServer() before anything and runs only
RunHoldingServer() there: no gameplay and no save loaded (the old server has just released them), only
the update screen and the way back. Clients show the screen while Workspace's "SoftShutdown"
attribute holds a message (ServerNotices.client).
]]
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TeleportService = game:GetService("TeleportService")
local Workspace = game:GetService("Workspace")

local Announcements = require(script.Parent.Announcements)
local PlayerData = require(script.Parent.PlayerData)

local SoftShutdown = {}

SoftShutdown.Attribute = "SoftShutdown" -- Workspace attribute: the update screen's text while it shows
SoftShutdown.Message = "Updating the game, back in a moment!"
local SAVE_SECONDS = 15 -- for everyone's save before the teleport (BindToClose allows about 30 s)
local HOLD_SECONDS = 5 -- in the holding server, before going back (the old servers are closing)
local RETRY_SECONDS = 5

local function log(text: string)
	print("[SoftShutdown] " .. text)
end

-- What to do when the server closes (pure, for the spec). reasonName: the CloseReason's Name.
function SoftShutdown.Plan(reasonName: string, isStudio: boolean, playerCount: number): string
	if playerCount <= 0 then
		return "None"
	end
	if reasonName == "DeveloperShutdown" then
		return if isStudio then "StudioLog" else "Hop"
	end
	if reasonName == "DeveloperUpdate" or reasonName == "RobloxMaintenance" then
		return "Message"
	end
	return "None"
end

-- A reserved server with no owner: in this game, only the holding server (pure, for the spec).
function SoftShutdown.IsHolding(privateServerId: string, privateServerOwnerId: number): boolean
	return privateServerId ~= "" and privateServerOwnerId == 0
end

function SoftShutdown.IsHoldingServer(): boolean
	return SoftShutdown.IsHolding(game.PrivateServerId, game.PrivateServerOwnerId)
end

-- The text for a scheduled restart, minutes away (pure, for the spec).
function SoftShutdown.ScheduledText(secondsLeft: number): string
	local minutes = math.max(1, math.ceil(secondsLeft / 60))
	return `This server restarts for an update in {minutes} minute{if minutes == 1 then "" else "s"}. Your progress is saved, and you'll come straight back.`
end

-- The holding server: show the update screen and send each arrival back to a public server.
function SoftShutdown.RunHoldingServer()
	Workspace:SetAttribute(SoftShutdown.Attribute, SoftShutdown.Message)
	local waiting = {} -- [player] = os.clock() when they may go
	local function arrive(player: Player)
		waiting[player] = os.clock() + HOLD_SECONDS
	end
	Players.PlayerAdded:Connect(arrive)
	for _, player in Players:GetPlayers() do
		arrive(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		waiting[player] = nil
	end)
	log("holding server: sending everyone back to a new server")
	task.spawn(function()
		while true do
			task.wait(1)
			local ready = {}
			for player, at in waiting do
				if os.clock() >= at then
					table.insert(ready, player)
					waiting[player] = os.clock() + RETRY_SECONDS -- (if the teleport fails, try again)
				end
			end
			if #ready > 0 then
				local ok, problem = pcall(TeleportService.TeleportAsync, TeleportService, game.PlaceId, ready)
				if not ok then
					warn(`[SoftShutdown] teleport back failed, trying again: {problem}`)
				end
			end
		end
	end)
end

-- Everyone's save, written and released (PlayerData.CloseAll), then everyone to a new reserved server.
local function hop()
	PlayerData.CloseAll(SAVE_SECONDS)
	local options = Instance.new("TeleportOptions")
	options.ShouldReserveServer = true
	options:SetTeleportData({ SoftShutdown = true })
	for attempt = 1, 3 do
		local list = Players:GetPlayers()
		if #list == 0 then
			return
		end
		local ok, problem = pcall(TeleportService.TeleportAsync, TeleportService, game.PlaceId, list, options)
		if ok then
			log(`sent {#list} player(s) to a holding server`)
			break
		end
		warn(`[SoftShutdown] teleport to a holding server failed (try {attempt}): {problem}`)
		task.wait(2)
	end
	local deadline = os.clock() + 12
	while #Players:GetPlayers() > 0 and os.clock() < deadline do
		task.wait(0.5)
	end
end

local function onClose(reason)
	local reasonName = if typeof(reason) == "EnumItem" then reason.Name else "Unknown"
	local count = #Players:GetPlayers()
	local plan = SoftShutdown.Plan(reasonName, RunService:IsStudio(), count)
	if plan == "None" then
		return
	end
	Workspace:SetAttribute(SoftShutdown.Attribute, SoftShutdown.Message)
	if plan == "Hop" then
		hop()
	elseif plan == "Message" then
		log(`{reasonName}: saving {count} player(s); Roblox moves them to the new server`)
		PlayerData.CloseAll(SAVE_SECONDS)
	elseif plan == "StudioLog" then
		local saved = PlayerData.CloseAll(SAVE_SECONDS)
		log(`(Studio) {reasonName}: {count} player(s) saved{if saved then "" else " (not all in time)"}; live, they would now go to a holding server and come straight back`)
	end
end

local function onRestartScheduled(restartTime, source, preview: boolean?)
	local secondsLeft = if typeof(restartTime) == "DateTime" then restartTime.UnixTimestamp - os.time() else 60
	local sourceName = if typeof(source) == "EnumItem" then source.Name else "Unknown"
	log(`restart scheduled ({sourceName}) in {secondsLeft} s`)
	for _, player in Players:GetPlayers() do
		PlayerData.MarkImportant(player)
	end
	Announcements.Show("UPDATE COMING", SoftShutdown.ScheduledText(secondsLeft), 10)
	if secondsLeft > 90 and not preview then
		task.delay(secondsLeft - 60, function()
			Announcements.Show("UPDATE COMING", SoftShutdown.ScheduledText(60), 10)
		end)
	end
end

-- Debug and admin: what players see when a restart is scheduled, and the update screen, without closing.
function SoftShutdown.PreviewScheduled(secondsLeft: number)
	onRestartScheduled(DateTime.fromUnixTimestamp(os.time() + secondsLeft), Enum.CloseReason.DeveloperUpdate, true)
end

function SoftShutdown.PreviewScreen(seconds: number)
	Workspace:SetAttribute(SoftShutdown.Attribute, SoftShutdown.Message)
	task.delay(seconds, function()
		Workspace:SetAttribute(SoftShutdown.Attribute, nil)
	end)
end

function SoftShutdown.Start()
	game:BindToClose(onClose)
	local ok, problem = pcall(function()
		game.ServerRestartScheduled:Connect(onRestartScheduled)
	end)
	if not ok then
		warn(`[SoftShutdown] can't watch for scheduled restarts: {problem}`)
	end
end

return SoftShutdown
