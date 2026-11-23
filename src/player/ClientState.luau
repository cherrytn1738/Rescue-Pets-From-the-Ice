--[[
ClientState: the local player's progress as the panels see it: the server's display copies (player
attributes Progress (JSON), Crystals, CrystalsPerSecond...), decoded into a table shaped like the save
so the panels can use the same rules as the server (EconomyRules, PetRules). Display only: the
server checks every request.

  ClientState.Data()            the latest copy (Crystals included), or nil before the save loads
  ClientState.Changed(callback) callback(data) on every change (Progress, or Crystals ~4 times a second)
  ClientState.Event(kind, callback)  the server's GameEvent notices ("Rescue", "Built", ...)
]]
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local ClientState = {}

local player = Players.LocalPlayer
local listeners = {}
local eventListeners = {}
local data = nil

local function decode()
	local text = player:GetAttribute("Progress")
	if type(text) ~= "string" then
		return
	end
	local ok, decoded = pcall(HttpService.JSONDecode, HttpService, text)
	if not ok or type(decoded) ~= "table" then
		return
	end
	-- JSON arrays come back for empty maps; that's fine for every reader
	decoded.Buildings = decoded.Buildings or {}
	decoded.Upgrades = decoded.Upgrades or {}
	decoded.Pets = decoded.Pets or {}
	decoded.Equipped = decoded.Equipped or {}
	decoded.BookSeen = decoded.BookSeen or {}
	decoded.BookNew = decoded.BookNew or {}
	decoded.BookGolden = decoded.BookGolden or {}
	decoded.Settings = decoded.Settings or {}
	data = decoded
end

local function fire()
	if not data then
		return
	end
	data.Crystals = player:GetAttribute("Crystals") or 0
	for _, callback in listeners do
		task.spawn(callback, data)
	end
end

function ClientState.Data()
	if data then
		data.Crystals = player:GetAttribute("Crystals") or 0
	end
	return data
end

function ClientState.Changed(callback)
	table.insert(listeners, callback)
	if data then
		task.spawn(callback, ClientState.Data())
	end
end

function ClientState.Event(kind: string, callback)
	eventListeners[kind] = eventListeners[kind] or {}
	table.insert(eventListeners[kind], callback)
end

player:GetAttributeChangedSignal("Progress"):Connect(function()
	decode()
	fire()
end)
player:GetAttributeChangedSignal("Crystals"):Connect(fire)
decode()

local gameEvent = ReplicatedStorage:WaitForChild("GameEvent") :: RemoteEvent
gameEvent.OnClientEvent:Connect(function(kind, payload)
	for _, callback in eventListeners[kind] or {} do
		task.spawn(callback, payload)
	end
end)

return ClientState
