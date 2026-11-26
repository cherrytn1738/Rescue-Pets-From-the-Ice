--[[
Announcements: a message panel on every player's screen (ServerNotices.client shows it). Server only.

  Announcements.Show(title, text, seconds?)   everyone in THIS server (GameEvent "ServerMessage")
  Announcements.Broadcast(title, text)        everyone in EVERY server of the game (MessagingService,
                                              topic "Announcement"); in Studio it shows here only and is
                                              never published, so a test can't reach live servers
Text from a person must be filtered before it gets here (AdminCommands does it). Used by the admin
window's announcement commands and by SoftShutdown's "update coming" warnings.
]]
local MessagingService = game:GetService("MessagingService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Announcements = {}

local TOPIC = "Announcement"
local MAX_TEXT = 200
local DEFAULT_SECONDS = 8

local gameEvent

function Announcements.Show(title: string, text: string, seconds: number?)
	gameEvent = gameEvent or ReplicatedStorage:WaitForChild("GameEvent")
	gameEvent:FireAllClients("ServerMessage", {
		Title = string.sub(tostring(title), 1, 40),
		Text = string.sub(tostring(text), 1, MAX_TEXT),
		Seconds = math.clamp(seconds or DEFAULT_SECONDS, 3, 30),
	})
end

-- Returns true once published (or, in Studio, shown here only), or false and Roblox's message.
function Announcements.Broadcast(title: string, text: string): (boolean, string?)
	if RunService:IsStudio() then
		Announcements.Show(title, text)
		return true, "Studio: shown in this server only (never published to live servers)"
	end
	local ok, problem = pcall(MessagingService.PublishAsync, MessagingService, TOPIC, {
		Title = string.sub(tostring(title), 1, 40),
		Text = string.sub(tostring(text), 1, MAX_TEXT),
	})
	if not ok then
		return false, tostring(problem)
	end
	return true, nil
end

function Announcements.Start()
	gameEvent = ReplicatedStorage:WaitForChild("GameEvent")
	if RunService:IsStudio() then
		return
	end
	local ok, problem = pcall(MessagingService.SubscribeAsync, MessagingService, TOPIC, function(message)
		local data = type(message) == "table" and message.Data
		if type(data) == "table" and type(data.Title) == "string" and type(data.Text) == "string" then
			Announcements.Show(data.Title, data.Text)
		end
	end)
	if not ok then
		warn(`[Announcements] can't receive announcements from other servers: {problem}`)
	end
end

return Announcements
