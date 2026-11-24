--[[
LeaderboardService: the three plaza boards: all-time crystals, rebirths, creatures rescued
(docs/GAME_DESIGN.md, "Social and events"; GameConfig.Leaderboards). Server only.
Every RefreshSeconds it writes each loaded player's values (LeaderboardRules.Encode; Studio's own
stores; never for a throwaway StudioFreshSave record) and reads the top entries into the boards
(PlazaService.Boards). Every request is in a pcall: a failed one waits for the next refresh.
]]
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local GameConfig = require(ReplicatedStorage.GameConfig)
local LeaderboardRules = require(ReplicatedStorage.LeaderboardRules)
local NumberFormat = require(ReplicatedStorage.NumberFormat)
local PlayerData = require(script.Parent.PlayerData)
local PlazaService = require(script.Parent.PlazaService)

local LeaderboardService = {}

local SETTINGS = GameConfig.Leaderboards
local stores = {}
local names = {} -- [user id] = display name, for players seen this server

local function storeOf(board)
	if not stores[board.Id] then
		stores[board.Id] = DataStoreService:GetOrderedDataStore(LeaderboardRules.StoreName(board.Id, RunService:IsStudio()))
	end
	return stores[board.Id]
end

local function nameOf(userId: number): string
	if names[userId] then
		return names[userId]
	end
	local ok, name = pcall(Players.GetNameFromUserIdAsync, Players, userId)
	names[userId] = if ok and name then name else ("Player " .. userId)
	return names[userId]
end

function LeaderboardService.Write(player: Player)
	local data = PlayerData.Get(player)
	if not data or PlayerData.IsThrowaway(player) then
		return
	end
	names[player.UserId] = player.DisplayName
	for _, board in SETTINGS.Boards do
		local value = LeaderboardRules.Encode(data[board.Field] or 0, board.Log)
		if value > 0 then
			local ok, err = pcall(function()
				storeOf(board):SetAsync(tostring(player.UserId), value)
			end)
			if not ok then
				warn(`[Leaderboards] write {board.Id} failed: {err}`)
			end
		end
	end
end

function LeaderboardService.Read()
	for _, board in SETTINGS.Boards do
		local label = PlazaService.Boards[board.Id]
		local ok, pages = pcall(function()
			return storeOf(board):GetSortedAsync(false, SETTINGS.Top)
		end)
		if ok and label then
			local lines = {}
			for rank, entry in pages:GetCurrentPage() do
				local value = LeaderboardRules.Decode(entry.value, board.Log)
				table.insert(lines, `{rank}. {nameOf(tonumber(entry.key) or 0)}  {NumberFormat.Short(value)}`)
			end
			label.Text = if #lines > 0 then table.concat(lines, "\n") else "Be the first!"
		elseif not ok then
			warn(`[Leaderboards] read {board.Id} failed: {pages}`)
		end
	end
end

function LeaderboardService.Refresh()
	for _, player in Players:GetPlayers() do
		LeaderboardService.Write(player)
	end
	LeaderboardService.Read()
end

function LeaderboardService.Start()
	PlayerData.OnLoaded(function(player)
		task.wait(3)
		LeaderboardService.Write(player)
		LeaderboardService.Read()
	end)
	Players.PlayerRemoving:Connect(LeaderboardService.Write)
	task.spawn(function()
		while true do
			task.wait(SETTINGS.RefreshSeconds)
			LeaderboardService.Refresh()
		end
	end)
end

return LeaderboardService
