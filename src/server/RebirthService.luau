--[[
RebirthService: rebirths and ranks (docs/GAME_DESIGN.md, "Rebirth"). Server only.

 - RebirthRequest (RemoteFunction): ("Rebirth") -> { ok, message, cores }. Needs block level
   RebirthConfig.RequiredLevel (Layer 4). Grants Frost Cores = FrostCoresFor(crystals this run), resets
   RebirthConfig.ResetOnRebirth (crystals, buildings, upgrades, the block level and block) and keeps the
   rest (pets, the book, Frost Cores, rank, Robux items). Rebirth ranks open pet slots (PetService) and
   layers (MaxLayerOpened). A rebirth worth 0 Frost Cores is allowed; the Rebirth screen warns first.
 - A Mythic Block bought with Robux and still on the mound is paid for: it stays through the rebirth (the same
   creature, at the new level's HP) instead of being rolled away with the block.
 - Ranks show as a title and colour on the player's name tag and their plot's border (RankService).
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local LayerConfig = require(ReplicatedStorage.LayerConfig)
local RebirthConfig = require(ReplicatedStorage.RebirthConfig)
local Analytics = require(script.Parent.Analytics)
local IceBlockService = require(script.Parent.IceBlockService)
local PetService = require(script.Parent.PetService)
local PlayerData = require(script.Parent.PlayerData)
local PlotService = require(script.Parent.PlotService)

local RebirthService = {}

local DEFAULTS = {
	Crystals = 0,
	CrystalsThisRun = 0,
	BlockLevel = 1,
	CurrentBlock = nil,
	Buildings = {},
	Upgrades = {},
}
local listeners = {}
local lastRequest = {}

-- callback(player, data) after every rebirth.
function RebirthService.OnRebirth(callback)
	table.insert(listeners, callback)
end

-- Applies a rebirth to a save (pure: used by the server and the spec). Returns the Frost Cores earned,
-- or nil and a reason.
function RebirthService.Apply(data)
	if data.BlockLevel < RebirthConfig.RequiredLevel then
		return nil, `Reach level {RebirthConfig.RequiredLevel} (Layer 4: Crystal Ice) to rebirth.`
	end
	local cores = RebirthConfig.FrostCoresFor(data.CrystalsThisRun)
	local block = data.CurrentBlock
	local paidBlock = if type(block) == "table" and block.Mythic == true then block.CreatureId else nil
	for _, field in RebirthConfig.ResetOnRebirth do
		local default = DEFAULTS[field]
		data[field] = if type(default) == "table" then {} else default
	end
	if paidBlock then
		data.CurrentBlock = { CreatureId = paidBlock, HpLeft = LayerConfig.BlockHp(data.BlockLevel), Mythic = true }
	end
	data.FrostCores += cores
	data.Rebirths += 1
	data.MaxLayerOpened = math.max(data.MaxLayerOpened, RebirthConfig.MaxLayerFor(data.Rebirths, LayerConfig.FloorLayer, #LayerConfig.Layers))
	return cores
end

function RebirthService.Handle(player: Player, action)
	if action ~= "Rebirth" then
		return { ok = false, message = "Unknown request." }
	end
	local now = os.clock()
	if lastRequest[player] and now - lastRequest[player] < 2 then
		return { ok = false, message = "Slow down a little." }
	end
	lastRequest[player] = now
	local data = PlayerData.Edit(player)
	if not data then
		return { ok = false, message = "Your data isn't ready yet." }
	end
	local cores, reason = RebirthService.Apply(data)
	if not cores then
		return { ok = false, message = reason }
	end
	PlayerData.MarkImportant(player)
	if data.CurrentBlock then
		IceBlockService.Refresh(player) -- (a paid Mythic Block stays on the mound)
	else
		IceBlockService.Reroll(player)
	end
	PlotService.RefreshBuildings(player, data)
	PetService.Publish(player, data)
	Analytics.Onboarding(player, "FirstRebirth")
	local rank = RebirthConfig.RankFor(data.Rebirths)
	ReplicatedStorage.GameEvent:FireClient(player, "Rebirth", { Cores = cores, Rebirths = data.Rebirths, Title = rank and rank.Title })
	for _, callback in listeners do
		task.spawn(callback, player, data)
	end
	return { ok = true, message = `Reborn! +{cores} Frost Cores`, cores = cores }
end

function RebirthService.Start()
	ReplicatedStorage:WaitForChild("RebirthRequest").OnServerInvoke = RebirthService.Handle
	game:GetService("Players").PlayerRemoving:Connect(function(player)
		lastRequest[player] = nil
	end)
end

return RebirthService
