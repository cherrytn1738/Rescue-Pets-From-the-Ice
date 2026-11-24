--[[
TutorialService: the five-step tutorial and the onboarding funnel (docs/GAME_DESIGN.md, "UI and
controls" and "Technical design"). Server only. The step is saved (TutorialStep); the client's
TutorialGuide shows the arrow and the words.
  1 Tap the ice              -> 2 once the player has 15 crystals (or a building)
  2 Build an Ice Pick Post   -> 3 on the first building
  3 Free the first creature  -> 4 on the first rescue
  4 Equip your new pet       -> 5 once a pet is equipped
  5 Done: the tutorial code is shown (GameEvent "TutorialDone")
Funnel steps (Analytics.Onboarding): FirstTap, FirstBuilding, FirstRescue, FirstPetEquipped,
TutorialDone (Joined is Analytics' own; FirstRebirth is RebirthService's).
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local BuildingConfig = require(ReplicatedStorage.BuildingConfig)
local Analytics = require(script.Parent.Analytics)
local Economy = require(script.Parent.Economy)
local IceBlockService = require(script.Parent.IceBlockService)
local PetService = require(script.Parent.PetService)
local PlayerData = require(script.Parent.PlayerData)
local ShopService = require(script.Parent.ShopService)
local TapService = require(script.Parent.TapService)

local TutorialService = {}

TutorialService.Code = "THAWED" -- the tutorial-completion code (CodesConfig)
TutorialService.CrystalsForStep2 = BuildingConfig.Get("IcePickPost").BaseCost

local gameEvent

local function hasBuilding(data): boolean
	return next(data.Buildings) ~= nil
end

-- Moves the player on as far as their save allows. Returns whether the step changed.
function TutorialService.Advance(player: Player, data): boolean
	local before = data.TutorialStep
	if data.TutorialStep == 1 and (data.Crystals >= TutorialService.CrystalsForStep2 or hasBuilding(data)) then
		data.TutorialStep = 2
	end
	if data.TutorialStep == 2 and hasBuilding(data) then
		data.TutorialStep = 3
	end
	if data.TutorialStep == 3 and data.CreaturesRescued > 0 then
		data.TutorialStep = 4
	end
	if data.TutorialStep == 4 and #data.Equipped > 0 then
		data.TutorialStep = 5
		Analytics.Onboarding(player, "TutorialDone")
		gameEvent:FireClient(player, "TutorialDone", { Code = TutorialService.Code })
	end
	if data.TutorialStep ~= before then
		PlayerData.MarkImportant(player)
		PlayerData.Publish(player)
		return true
	end
	return false
end

function TutorialService.Start()
	gameEvent = ReplicatedStorage:WaitForChild("GameEvent")
	TapService.OnTaps(function(player)
		Analytics.Onboarding(player, "FirstTap")
	end)
	ShopService.OnBought(function(player, data, kind)
		if kind == "Building" then
			Analytics.Onboarding(player, "FirstBuilding")
		end
		TutorialService.Advance(player, data)
	end)
	IceBlockService.OnRescue(function(player, data)
		Analytics.Onboarding(player, "FirstRescue")
		TutorialService.Advance(player, data)
	end)
	PetService.OnEquipChanged(function(player, data)
		if #data.Equipped > 0 then
			Analytics.Onboarding(player, "FirstPetEquipped")
		end
		TutorialService.Advance(player, data)
	end)
	Economy.OnTick(function(player, data)
		if data.TutorialStep == 1 then
			TutorialService.Advance(player, data)
		end
	end)
	PlayerData.OnLoaded(function(player, data)
		TutorialService.Advance(player, data)
	end)
end

return TutorialService
