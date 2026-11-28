--[[
IceBlockService: each player's ice block (docs/GAME_DESIGN.md, "The ice block", "Glacier depth" and
"Technical design"). Server only.

 - A block has a level (the save's BlockLevel), HP (LayerConfig.BlockHp) and a creature inside,
   rolled when the block arrives (BlockRules, from the layer's odds; Lucky Ice doubles Legendary and
   Mythic; a Mythic Block bought and waiting (data.MythicBlocks) rolls from that product's own odds
   instead) and saved as CurrentBlock, so a rejoin finds the same block with the same HP left. The roll
   is final. On the first run (0 rebirths), the block for rescue CreatureConfig.FirstRunGuarantee.ByRescue
   holds at least a Rare if none has been rescued yet.
 - Damage(player, data, amount): taps and buildings hit the block; every point of damage pays one
   crystal times the multiplier (Economy). Nothing is hit while the next block is still on its sled.
 - At 0 HP the creature is rescued (PetService.Rescue), a crystal fountain worth BurstSeconds of
   income is paid, the level goes up, and the next block arrives after the sled ride
   (EconomyRules.SledSeconds).
 - The block's state is copied to the plot's Block folder as attributes (every client draws it):
   Present, Level, CreatureId, Rarity, Layer, Hp, HpMax, Stage (0-4 crack stages), ArriveAt, MythicBlock (a Mythic
   Block bought with Robux: CurrentBlock.Mythic).
   Player attributes BlockLevel, BlockHp, BlockHpMax for the HUD.
 - Events to the owner on GameEvent: "Rescue", "NewLayer"; to everyone: "Announce" (a Legendary or
   Mythic block arrived, with its PlotIndex, so others can come and watch: RareWatch.client; and again
   with Freed = true when it breaks).
]]
local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

local BlockRules = require(ReplicatedStorage.BlockRules)
local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local EconomyRules = require(ReplicatedStorage.EconomyRules)
local LayerConfig = require(ReplicatedStorage.LayerConfig)
local MapConfig = require(ReplicatedStorage.MapConfig)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)
local Economy = require(script.Parent.Economy)
local PetService = require(script.Parent.PetService)
local PlayerData = require(script.Parent.PlayerData)
local PlotService = require(script.Parent.PlotService)

local IceBlockService = {}

local gameEvent = ReplicatedStorage:WaitForChild("GameEvent") :: RemoteEvent
local random = Random.new()
local states = {} -- [player] = { arriveAt = os.clock() time or nil, layer = number }
local rollOverride = {} -- [player] = creature id (debug: "pick the creature inside")
local luckSources = {} -- { function(player) -> boolean } (Lucky Ice)
local rescueListeners = {}

local function layerFor(data)
	return LayerConfig.LayerForLevel(data.BlockLevel, data.MaxLayerOpened)
end

local function isLucky(player: Player): boolean
	for _, callback in luckSources do
		local ok, lucky = pcall(callback, player)
		if ok and lucky then
			return true
		end
	end
	return false
end

-- callback(player) -> true when the player's blocks roll with Lucky Ice.
function IceBlockService.AddLuck(callback)
	table.insert(luckSources, callback)
end

-- callback(player, data, creatureId, pet, first) after every rescue.
function IceBlockService.OnRescue(callback)
	table.insert(rescueListeners, callback)
end

-- Copies the block's state to the plot (for every client) and to the player's HUD attributes.
local function publish(player: Player, data)
	local plot = PlotService.PlotOf(player)
	local state = states[player]
	if not plot or not state then
		return
	end
	local folder = plot.Block
	local block = data.CurrentBlock
	local present = block ~= nil and state.arriveAt == nil
	local hpMax = LayerConfig.BlockHp(data.BlockLevel)
	folder:SetAttribute("Present", present)
	folder:SetAttribute("Level", data.BlockLevel)
	folder:SetAttribute("Layer", layerFor(data).Number)
	folder:SetAttribute("HpMax", hpMax)
	if block then
		local creature = CreatureConfig.Get(block.CreatureId)
		folder:SetAttribute("CreatureId", block.CreatureId)
		folder:SetAttribute("Rarity", creature.Rarity)
		folder:SetAttribute("Hp", block.HpLeft)
		folder:SetAttribute("Stage", BlockRules.CrackStage(block.HpLeft, hpMax))
		folder:SetAttribute("MythicBlock", block.Mythic == true)
	end
	folder:SetAttribute("ArriveAt", if state.arriveAt then Workspace:GetServerTimeNow() + (state.arriveAt - os.clock()) else 0)
	player:SetAttribute("BlockLevel", data.BlockLevel)
	player:SetAttribute("BlockHp", if block then block.HpLeft else hpMax)
	player:SetAttribute("BlockHpMax", hpMax)
end

-- Rolls the creature for a new block at the player's current level.
local function rollBlock(player: Player, data)
	local layer = layerFor(data)
	local creature
	local forced = rollOverride[player]
	local mythicBlock = MonetizationConfig.GetProduct("MythicBlock")
	local fromMythicBlock = false
	if forced and CreatureConfig.Get(forced) then
		creature = CreatureConfig.Get(forced)
		rollOverride[player] = nil
	elseif (data.MythicBlocks or 0) > 0 and mythicBlock and mythicBlock.Odds then
		creature = BlockRules.RollMythicBlock(mythicBlock.Odds, random:NextNumber(), random:NextNumber())
		data.MythicBlocks -= 1
		fromMythicBlock = true -- (the block looks the part: IceBlockLook's glowing corner crystals)
		PlayerData.MarkImportant(player)
		PlayerData.Publish(player)
		gameEvent:FireClient(player, "Notice", { Text = `Your Mythic Block arrived: a {creature.Rarity} creature is inside!` })
	else
		local atLeast = BlockRules.NeedsFirstRunGuarantee(data.Rebirths, data.CreaturesRescued, data.BookSeen, CreatureConfig.FirstRunGuarantee)
		creature = BlockRules.RollCreature(layer.Number, random:NextNumber(0, 100), random:NextNumber(), isLucky(player), atLeast)
	end
	data.CurrentBlock = { CreatureId = creature.Id, HpLeft = LayerConfig.BlockHp(data.BlockLevel), Mythic = if fromMythicBlock then true else nil }
	local rarity = CreatureConfig.GetRarity(creature.Rarity)
	if rarity.Announce then
		gameEvent:FireAllClients("Announce", {
			Text = `{player.DisplayName}'s ice holds a {creature.Rarity} creature! Follow the beam to watch it break.`,
			Rarity = creature.Rarity,
			PlotIndex = PlotService.IndexOf(player),
		})
	end
	local state = states[player]
	if state.layer and layer.Number ~= state.layer then
		gameEvent:FireClient(player, "NewLayer", { Layer = layer.Number, Name = layer.Name })
	end
	state.layer = layer.Number
end

-- The block in progress: restored from the save, or rolled.
local function setUp(player: Player, data)
	states[player] = { arriveAt = nil, layer = layerFor(data).Number }
	local block = data.CurrentBlock
	local hpMax = LayerConfig.BlockHp(data.BlockLevel)
	if block and block.HpLeft > 0 and block.HpLeft <= hpMax then
		-- the saved block comes back
	else
		rollBlock(player, data)
	end
	publish(player, data)
end

local function rescue(player: Player, data)
	local block = data.CurrentBlock
	local creature = CreatureConfig.Get(block.CreatureId)
	-- the fountain: BurstSeconds of income (crystals/s as the HUD shows it), paid before the level rises
	local burst = EconomyRules.BurstSeconds(data) * Economy.CrystalsPerSecond(player, data)
	local first = (data.BookSeen[creature.Id] or 0) == 0
	local pet = PetService.Rescue(player, data, creature.Id)
	Economy.Grant(player, data, burst, "Rescue")
	data.BlockLevel += 1
	data.CurrentBlock = nil
	local state = states[player]
	state.arriveAt = os.clock() + EconomyRules.SledSeconds(data)
	PlayerData.MarkImportant(player)
	PlayerData.Publish(player)
	gameEvent:FireClient(player, "Rescue", {
		CreatureId = creature.Id,
		Rarity = creature.Rarity,
		Burst = burst,
		First = first,
		Uid = pet and pet.Uid,
		InventoryFull = pet == nil,
		Level = data.BlockLevel - 1,
	})
	for _, callback in rescueListeners do
		task.spawn(callback, player, data, creature.Id, pet, first)
	end
	-- a rare rescue: the whole server hears it was freed (and their beacons over this plot go out)
	if CreatureConfig.GetRarity(creature.Rarity).Announce then
		gameEvent:FireAllClients("Announce", {
			Text = `{player.DisplayName} freed a {creature.Rarity} {creature.Name}!`,
			Rarity = creature.Rarity,
			PlotIndex = PlotService.IndexOf(player),
			Freed = true,
		})
	end
	-- every client plays the shatter for this plot (the owner also gets the reveal from "Rescue")
	local plot = PlotService.PlotOf(player)
	if plot then
		plot.Block:SetAttribute("Rescued", creature.Id)
		plot.Block:SetAttribute("RescueCount", (plot.Block:GetAttribute("RescueCount") or 0) + 1)
	end
	publish(player, data)
end

-- Hits the player's block for `amount` damage and pays the crystals. Returns the damage dealt (0 when
-- there's no block on the mound). source: who hit it, for analytics ("Taps", "AutoPick", "Buildings").
function IceBlockService.Damage(player: Player, data, amount: number, source: string?): number
	local state = states[player]
	local block = data.CurrentBlock
	if not state or not block or state.arriveAt or type(amount) ~= "number" or amount ~= amount or amount <= 0 then
		return 0
	end
	Economy.Grant(player, data, amount * Economy.Multiplier(player, data), source or "Taps")
	block.HpLeft = math.max(0, block.HpLeft - amount)
	if block.HpLeft <= 0 then
		rescue(player, data)
	end
	return amount
end

-- Debug: the next block to roll holds this creature.
function IceBlockService.ForceNextCreature(player: Player, creatureId: string)
	rollOverride[player] = creatureId
end

-- Whether there is a block on the mound to shatter now (not on its sled).
function IceBlockService.CanShatter(player: Player): boolean
	local data = PlayerData.Get(player)
	local state = states[player]
	return data ~= nil and state ~= nil and data.CurrentBlock ~= nil and state.arriveAt == nil
end

-- Debug and Shatter Now: breaks the current block at once (the normal rescue).
function IceBlockService.Shatter(player: Player): boolean
	local data = PlayerData.Edit(player)
	local state = states[player]
	if not data or not state or not data.CurrentBlock or state.arriveAt then
		return false
	end
	data.CurrentBlock.HpLeft = 0
	rescue(player, data)
	return true
end

-- After something outside the block changed it (debug level set, rebirth): roll a new block now.
function IceBlockService.Reroll(player: Player)
	local data = PlayerData.Edit(player)
	if not data or not states[player] then
		return
	end
	states[player].arriveAt = nil
	rollBlock(player, data)
	publish(player, data)
end

function IceBlockService.Rarity(player: Player): string?
	local data = PlayerData.Get(player)
	local block = data and data.CurrentBlock
	local creature = block and CreatureConfig.Get(block.CreatureId)
	return creature and creature.Rarity
end

-- The ring round the ice (MapConfig.BlockRing, built by each client in IceBlocks) stops characters but lets flying
-- pieces through: two collision groups that don't collide (registered here, they replicate to every client).
local function registerRingGroups()
	local ring = MapConfig.BlockRing
	for _, name in { ring.Group, ring.DebrisGroup } do
		if not PhysicsService:IsCollisionGroupRegistered(name) then
			PhysicsService:RegisterCollisionGroup(name)
		end
	end
	PhysicsService:CollisionGroupSetCollidable(ring.Group, ring.DebrisGroup, false)
end

function IceBlockService.Start()
	registerRingGroups()
	-- the ice block's looks (ServerStorage.IceTemplates, tools/studio/build_templates.luau ONLY = "Ice") go where
	-- every client can clone them: the clients draw the blocks (IceBlocks, IceBlockLook)
	local templates = ServerStorage:FindFirstChild("IceTemplates")
	if templates and not ReplicatedStorage:FindFirstChild("IceTemplates") then
		templates:Clone().Parent = ReplicatedStorage
	end
	PlayerData.OnLoaded(function(player, data)
		if not PlotService.IndexOf(player) then
			PlotService.Assign(player)
		end
		setUp(player, data)
	end)
	Players.PlayerRemoving:Connect(function(player)
		states[player] = nil
		rollOverride[player] = nil
	end)
	Economy.OnTick(function(player, data, dt)
		local state = states[player]
		if not state then
			return
		end
		if state.arriveAt and os.clock() >= state.arriveAt then
			state.arriveAt = nil
		end
		-- the sled has arrived, or something else cleared the block (the debug menu, a rebirth)
		if not state.arriveAt and not data.CurrentBlock then
			rollBlock(player, data)
		end
		IceBlockService.Damage(player, data, EconomyRules.TotalBuildingDps(data) * dt, "Buildings")
		publish(player, data)
	end)
end

return IceBlockService
