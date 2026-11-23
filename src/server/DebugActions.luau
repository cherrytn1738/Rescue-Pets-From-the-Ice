--[[
DebugActions: everything the debug menu (F2) can do. Server only.

To add an action (every new system adds its own), add ONE entry to ACTIONS:
	{
		Id = "UniqueId", Group = "Menu section", Label = "Button text",
		Params = { ...input specs, see DebugRules... },   -- optional
		NoTarget = true,   -- optional: the action doesn't apply to a player (switches)
		Confirm = true,    -- optional: the menu asks "Sure?" before sending
		Run = function(target, args, caller) ... return "Short result message" end,
	}
Run gets a validated target Player (still in the server) and validated args. Refuse with
fail("message"). Always go through the game's own systems (PlayerData, Receipts, CodeService...)
so debug changes behave and save exactly like real ones.

A choice list built from a config that is still empty (no game passes or products yet) gets one
placeholder choice, so the menu still draws; running the action then says what is missing.
]]
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local CodeService = require(script.Parent.CodeService)
local IceBlockService = require(script.Parent.IceBlockService)
local PetService = require(script.Parent.PetService)
local PlotService = require(script.Parent.PlotService)
local GamePasses = require(script.Parent.GamePasses)
local Gifting = require(script.Parent.Gifting)
local OfflineEarnings = require(script.Parent.OfflineEarnings)
local PlayerData = require(script.Parent.PlayerData)
local Receipts = require(script.Parent.Receipts)
local AnalyticsConfig = require(ReplicatedStorage.AnalyticsConfig)
local AnalyticsRules = require(ReplicatedStorage.AnalyticsRules)
local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local MonetizationConfig = require(ReplicatedStorage.MonetizationConfig)

local NONE = "__none" -- the placeholder choice of an empty list
local SHOW_SAVE_CHARACTERS = 400 -- how much of the save the menu shows (Output gets all of it)

local function fail(message: string)
	error(message, 0)
end

-- Choice lists ---------------------------------------------------------------------------------

local onOff = { { Value = "On", Label = "On" }, { Value = "Off", Label = "Off" } }

-- A choice list, or one placeholder when the config has nothing in it yet.
local function choicesOr(list, emptyLabel: string)
	if #list == 0 then
		return { { Value = NONE, Label = emptyLabel } }
	end
	return list
end

local passChoices, productChoices = {}, {}
for _, pass in MonetizationConfig.Passes do
	table.insert(passChoices, { Value = pass.Key, Label = pass.Name .. (if MonetizationConfig.IsLive(pass) then "" else " (no id yet)") })
end
for _, product in MonetizationConfig.Products do
	table.insert(productChoices, { Value = product.Key, Label = product.Name .. (if MonetizationConfig.IsLive(product) then "" else " (no id yet)") })
end
passChoices = choicesOr(passChoices, "(no game passes in MonetizationConfig yet)")
productChoices = choicesOr(productChoices, "(no products in MonetizationConfig yet)")

local creatureChoices = {}
for _, creature in CreatureConfig.Creatures do
	table.insert(creatureChoices, { Value = creature.Id, Label = `{creature.Name} ({creature.Rarity})` })
end
creatureChoices = choicesOr(creatureChoices, "(no creatures)")

local lastSimulated = {} -- [buyer] = { product, gift, purchaseId }: the "duplicate receipt" action replays it

local function amountParam(name: string, label: string, min: number, max: number, default: number?)
	return { Name = name, Label = label, Kind = "number", Min = min, Max = max, Integer = true, Default = default }
end
local function passParam()
	return { Name = "Pass", Label = "Pass", Kind = "choice", Choices = passChoices, Default = passChoices[1].Value }
end
local function productParam(label: string?)
	return { Name = "Product", Label = label or "Product", Kind = "choice", Choices = productChoices, Default = productChoices[1].Value }
end
local function stateParam()
	return { Name = "State", Label = "State", Kind = "choice", Choices = onOff, Default = "On" }
end

-- Helpers -------------------------------------------------------------------------------------------

local function dataOf(target: Player)
	local data = PlayerData.Edit(target)
	if not data then
		fail(`{target.Name}'s data isn't ready`)
	end
	return data
end

local function humanoidOf(target: Player): Humanoid
	local humanoid = target.Character and target.Character:FindFirstChildOfClass("Humanoid")
	if not humanoid then
		fail(`{target.Name} has no character`)
	end
	return humanoid
end

local function rootOf(player: Player): BasePart
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not root then
		fail(`{player.Name} has no character`)
	end
	return root
end

local function studioOnly()
	if not RunService:IsStudio() then
		fail("Studio only")
	end
end

local function passOf(key: string)
	if key == NONE then
		fail("There are no game passes yet: add them to MonetizationConfig.Passes")
	end
	return MonetizationConfig.GetPass(key)
end

local function productOf(key: string)
	if key == NONE then
		fail("There are no products yet: add them to MonetizationConfig.Products")
	end
	return MonetizationConfig.GetProduct(key)
end

-- "PurchaseGranted: gave ... (PurchaseId Studio-1A2B...)" from a simulated receipt.
local function receiptResult(decision, note: string, purchaseId: string): string
	return `{if decision == Enum.ProductPurchaseDecision.PurchaseGranted then "PurchaseGranted" else "NotProcessedYet"}: {note} (PurchaseId {purchaseId})`
end

-- A Studio-only Workspace attribute switch (read only when RunService:IsStudio(), never saved).
local function studioSwitch(attribute: string, label: string, state: string): string
	studioOnly()
	Workspace:SetAttribute(attribute, if state == "On" then true else nil)
	return `{label} {string.lower(state)}`
end

-- The actions, in menu order -------------------------------------------------------------------

local ACTIONS = {
	-- Save
	{
		Id = "SaveNow", Group = "Save", Label = "Force a save now",
		Run = function(target)
			dataOf(target)
			if not PlayerData.SaveNow(target) then
				fail(`Save failed for {target.Name} (see Output)`)
			end
			return `Saved {target.Name}`
		end,
	},
	{
		Id = "AddCrystals", Group = "Save", Label = "Add crystals (this run and all time too)",
		Params = { amountParam("Amount", "Crystals", 1, 1e15, 1000) },
		Run = function(target, args)
			local data = dataOf(target)
			data.Crystals += args.Amount
			data.CrystalsThisRun += args.Amount
			data.CrystalsAllTime += args.Amount
			PlayerData.Publish(target)
			PlayerData.MarkImportant(target)
			return `{target.Name} now has {data.Crystals} crystals`
		end,
	},
	{
		Id = "SetBlockLevel", Group = "Save", Label = "Set block level (the next block rolls again)",
		Params = { amountParam("Level", "Block level", 1, 1000, 21) },
		Run = function(target, args)
			local data = dataOf(target)
			data.BlockLevel = args.Level
			data.CurrentBlock = nil
			PlayerData.Publish(target)
			PlayerData.MarkImportant(target)
			return `{target.Name} is at block level {args.Level}`
		end,
	},
	-- Ice block and pets
	{
		Id = "ForceRescue", Group = "Ice block", Label = "Force a rescue (break the current block now)",
		Run = function(target)
			dataOf(target)
			if not IceBlockService.Shatter(target) then
				fail("No block on the mound right now (the sled is still bringing it)")
			end
			return `{target.Name}'s block broke`
		end,
	},
	{
		Id = "PickCreature", Group = "Ice block", Label = "Pick the creature inside (a new block rolls with it now)",
		Params = { { Name = "Creature", Label = "Creature", Kind = "choice", Choices = creatureChoices, Default = creatureChoices[1].Value } },
		Run = function(target, args)
			dataOf(target)
			IceBlockService.ForceNextCreature(target, args.Creature)
			IceBlockService.Reroll(target)
			return `{target.Name}'s block now holds a {args.Creature}`
		end,
	},
	{
		Id = "GivePet", Group = "Ice block", Label = "Give a pet",
		Params = {
			{ Name = "Creature", Label = "Creature", Kind = "choice", Choices = creatureChoices, Default = creatureChoices[1].Value },
			{ Name = "Golden", Label = "Golden", Kind = "choice", Choices = onOff, Default = "Off" },
		},
		Run = function(target, args)
			dataOf(target)
			if not PetService.Give(target, args.Creature, args.Golden == "On") then
				fail("Couldn't give it (inventory full?)")
			end
			return `{target.Name} got a {if args.Golden == "On" then "Golden " else ""}{args.Creature}`
		end,
	},
	{
		Id = "SendHome", Group = "Player", Label = "Send to their plot",
		Run = function(target)
			if not PlotService.SendHome(target) then
				fail(`{target.Name} has no plot or no character`)
			end
			return `{target.Name} is home`
		end,
	},
	{
		Id = "ShowSave", Group = "Save", Label = "Show the save (all of it goes to Output)",
		Run = function(target)
			dataOf(target)
			local json = HttpService:JSONEncode(PlayerData.Get(target))
			print(`[Debug] {target.Name}'s save: {json}`)
			if #json > SHOW_SAVE_CHARACTERS then
				return string.sub(json, 1, SHOW_SAVE_CHARACTERS) .. "... (the rest is in Output)"
			end
			return json
		end,
	},
	{
		-- Receipts and gifts survive the reset (they stop a purchase paying twice).
		Id = "ResetSave", Group = "Save", Label = "Reset to a fresh save (keeps Robux receipts)",
		Confirm = true,
		Run = function(target)
			dataOf(target)
			if not PlayerData.ResetToNew(target) then
				fail(`Couldn't reset {target.Name}`)
			end
			return `Reset {target.Name} to a fresh save`
		end,
	},

	-- Progress
	{
		-- The real payout (OfflineEarnings.Pay) as if the target had just come back after N seconds.
		Id = "OfflineEarningsNow", Group = "Progress", Label = "Offline earnings now (as if away N seconds)",
		Params = { amountParam("Seconds", "Seconds away", 1, 30 * 86400, 600) },
		Run = function(target, args)
			dataOf(target)
			local paid = OfflineEarnings.Pay(target, args.Seconds)
			return `{target.Name} earned {tostring(paid or 0)} for {args.Seconds} s away`
		end,
	},
	{
		Id = "AnalyticsProgress", Group = "Progress", Label = "Analytics funnels: how far they are logged",
		Run = function(target)
			local funnels = dataOf(target).Funnels or {}
			local waiting = if type(funnels.Waiting) == "table" and #funnels.Waiting > 0 then ` (waiting: {table.concat(funnels.Waiting, ", ")})` else ""
			return `{target.Name}: onboarding {tostring(funnels.Onboarding)} of {#AnalyticsConfig.Onboarding}{waiting}`
		end,
	},
	{
		Id = "AnalyticsRestart", Group = "Progress", Label = "Analytics funnels: start again (log every step afresh)",
		Run = function(target)
			local data = dataOf(target)
			data.Funnels = AnalyticsRules.New()
			PlayerData.MarkImportant(target)
			return `{target.Name}'s funnels start again (the first step logs on their next join)`
		end,
	},

	-- Codes
	{
		Id = "ResetCodes", Group = "Codes", Label = "Reset redeemed codes (every code works again)",
		Run = function(target)
			local count = CodeService.ResetRedeemed(target)
			return `Forgot {count} redeemed code{if count == 1 then "" else "s"} for {target.Name}`
		end,
	},

	-- Robux (Studio only: passes and receipts here never touch Roblox or a live save)
	{
		Id = "GivePass", Group = "Robux", Label = "Give a game pass (Studio, this session)",
		Params = { passParam() },
		Run = function(target, args)
			studioOnly()
			local pass = passOf(args.Pass)
			GamePasses.SetStudioOverride(target, args.Pass, true)
			return `{target.Name} owns {pass.Name} (this session)`
		end,
	},
	{
		Id = "RemovePass", Group = "Robux", Label = "Remove a game pass (Studio, this session)",
		Params = { passParam() },
		Run = function(target, args)
			studioOnly()
			local pass = passOf(args.Pass)
			GamePasses.SetStudioOverride(target, args.Pass, false)
			return `{target.Name} doesn't own {pass.Name} (this session)`
		end,
	},
	{
		Id = "SimulateReceipt", Group = "Robux", Label = "Simulate a receipt (the target is the buyer)",
		Params = {
			productParam(),
			{ Name = "GiftTo", Label = "Gift to user id (0 = for themselves; Studio test players are -1, -2...)", Kind = "number", Min = -1e12, Max = 1e12, Integer = true, Default = 0 },
		},
		Run = function(target, args)
			studioOnly()
			local product = productOf(args.Product)
			local gift = args.GiftTo ~= 0
			if gift then
				-- As the shop does: the recipient is saved in the buyer's record before the "prompt".
				local ok, problem = Gifting.Prepare(target, product, Players:GetPlayerByUserId(args.GiftTo))
				if not ok then
					fail(problem or "The gift couldn't be started")
				end
				Gifting.PromptFinished(target, product, true)
			end
			local decision, note, purchaseId = Receipts.Simulate(target, product, { gift = gift })
			lastSimulated[target] = { product = product, gift = gift, purchaseId = purchaseId }
			return receiptResult(decision, note, purchaseId)
		end,
	},
	{
		Id = "DuplicateReceipt", Group = "Robux", Label = "Simulate a duplicate receipt (the same PurchaseId again)",
		Params = {
			{ Name = "PurchaseId", Label = "PurchaseId (blank = the target's last simulated one)", Kind = "text", MaxLength = 64, Pattern = "^[%w%-]*$", Optional = true },
			productParam("Product (only used with a typed PurchaseId)"),
			{ Name = "Gift", Label = "A gift receipt? (only used with a typed PurchaseId)", Kind = "choice", Choices = onOff, Default = "Off" },
		},
		Run = function(target, args)
			studioOnly()
			local replay = lastSimulated[target]
			if args.PurchaseId ~= "" then
				replay = { product = productOf(args.Product), gift = args.Gift == "On", purchaseId = args.PurchaseId }
			end
			if not replay then
				fail(`{target.Name} has no simulated receipt yet; simulate one first (or type its PurchaseId)`)
			end
			local decision, note, purchaseId = Receipts.Simulate(target, replay.product, { gift = replay.gift, purchaseId = replay.purchaseId })
			return receiptResult(decision, note, purchaseId)
		end,
	},

	-- Testing switches (Studio only: Workspace attributes, never saved). Set during Play they last until
	-- Stop; set them in Edit (Workspace > Attributes) to have them from the start of a Play.
	{
		Id = "FreshSave", Group = "Testing switches", Label = "Fresh save: the next join plays as a brand-new player (throwaway record)",
		NoTarget = true,
		Params = { stateParam() },
		Run = function(_, args)
			return studioSwitch("StudioFreshSave", "Fresh save on the next join", args.State)
		end,
	},
	{
		Id = "UseLiveSaves", Group = "Testing switches", Label = "Use LIVE saves on the next join (only on purpose!)",
		NoTarget = true, Confirm = true,
		Params = { { Name = "State", Label = "State", Kind = "choice", Choices = onOff, Default = "Off" } },
		Run = function(_, args)
			return studioSwitch("StudioUseLiveSaves", "Live saves on the next join", args.State)
		end,
	},
	{
		-- Studio: the next join of a save that has a leave time counts as away this long (0 = off).
		Id = "FakeTimeAway", Group = "Testing switches", Label = "Fake time away on the next join (seconds, 0 = off)",
		NoTarget = true,
		Params = { amountParam("Seconds", "Seconds away", 0, 30 * 86400, 3600) },
		Run = function(_, args)
			studioOnly()
			Workspace:SetAttribute("StudioTimeAway", if args.Seconds > 0 then args.Seconds else nil)
			return if args.Seconds > 0 then `The next join counts as {args.Seconds} s away` else "Fake time away off"
		end,
	},
	{
		-- Everyone counts as living where paid random items are restricted (PaidRandomPolicy).
		Id = "PaidRandomRestricted", Group = "Testing switches", Label = "Paid random items restricted (region)",
		NoTarget = true,
		Params = { stateParam() },
		Run = function(_, args)
			return studioSwitch("StudioPaidRandomRestricted", "Paid random items restricted", args.State)
		end,
	},

	-- Player
	{
		Id = "TeleportToPlayer", Group = "Player", Label = "Teleport the target next to another player",
		Params = { { Name = "To", Label = "The other player's user id (Studio test players are -1, -2...)", Kind = "number", Min = -1e12, Max = 1e12, Integer = true, Default = -1 } },
		Run = function(target, args)
			local other = Players:GetPlayerByUserId(args.To)
			if not other or other == target then
				fail("Pick another player who is in this server")
			end
			local destination = rootOf(other).CFrame * CFrame.new(0, 0, -4)
			rootOf(target)
			target.Character:PivotTo(destination)
			return `Teleported {target.Name} to {other.Name}`
		end,
	},
	{
		Id = "SetWalkSpeed", Group = "Player", Label = "Set walk speed (until respawn)",
		Params = { amountParam("Speed", "Speed", 1, 200, 16) },
		Run = function(target, args)
			humanoidOf(target).WalkSpeed = args.Speed
			return `{target.Name}'s walk speed is {args.Speed}`
		end,
	},
	{
		Id = "Respawn", Group = "Player", Label = "Respawn",
		Run = function(target)
			humanoidOf(target)
			target:LoadCharacter()
			return `Respawned {target.Name}`
		end,
	},
}

-- Lookup by id, and the catalogue the menu draws from (everything but Run).
local byId, catalog = {}, {}
for _, action in ACTIONS do
	assert(byId[action.Id] == nil, "duplicate debug action " .. action.Id)
	byId[action.Id] = action
	table.insert(catalog, {
		Id = action.Id,
		Group = action.Group,
		Label = action.Label,
		Params = action.Params or {},
		NoTarget = action.NoTarget == true,
		Confirm = action.Confirm == true,
	})
end

return {
	ById = byId,
	Catalog = catalog,
}
