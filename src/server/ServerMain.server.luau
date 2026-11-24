-- ServerMain: starts every server system, in order (docs/GAME_DESIGN.md).
-- Everything that reacts to a player's data loading (PlayerData.OnLoaded, OnGiftsArrived) must
-- register before PlayerData.Start(), which loads the players already here.
local AdminService = require(script.Parent.AdminService)
local Analytics = require(script.Parent.Analytics)
local CodeService = require(script.Parent.CodeService)
local DebugService = require(script.Parent.DebugService)
local Economy = require(script.Parent.Economy)
local GamePasses = require(script.Parent.GamePasses)
local GameConfig = require(game:GetService("ReplicatedStorage").GameConfig)
local GoldenGlacierService = require(script.Parent.GoldenGlacierService)
local IceBlockService = require(script.Parent.IceBlockService)
local LeaderboardService = require(script.Parent.LeaderboardService)
local OfflineEarnings = require(script.Parent.OfflineEarnings)
local PaidRandomPolicy = require(script.Parent.PaidRandomPolicy)
local PetService = require(script.Parent.PetService)
local PlayerData = require(script.Parent.PlayerData)
local PlayerEffects = require(script.Parent.PlayerEffects)
local PlazaService = require(script.Parent.PlazaService)
local PlotService = require(script.Parent.PlotService)
local RankService = require(script.Parent.RankService)
local RebirthService = require(script.Parent.RebirthService)
local Receipts = require(script.Parent.Receipts)
local RewardService = require(script.Parent.RewardService)
local RobuxShop = require(script.Parent.RobuxShop)
local SettingsService = require(script.Parent.SettingsService)
local ShopService = require(script.Parent.ShopService)
local TapService = require(script.Parent.TapService)
local TutorialService = require(script.Parent.TutorialService)

-- Robux: pass ownership, paid-random-item rules, the one ProcessReceipt handler (and gifts), the shop.
PaidRandomPolicy.Start()
GamePasses.Start()
Receipts.Start() -- (also starts Gifting)
RobuxShop.Start()

OfflineEarnings.Start() -- pays for the time away (the earner is Economy's building income)
Analytics.Start() -- Roblox funnels (AnalyticsConfig); nothing is sent from Studio
CodeService.Start() -- promo codes (CodesConfig, server only)

-- Gameplay: plots, the crystal economy and its 4-a-second tick, the ice block, tapping, buying, pets.
PlotService.Start()
Economy.Start()
IceBlockService.Start()
TapService.Start()
ShopService.Start()
PetService.Start()
RebirthService.Start()
RankService.Start()
TutorialService.Start()
SettingsService.Start()

-- The map: the plaza (boards, chests, the codes board, the Golden Glacier ring), leaderboards, the rush,
-- the daily and group rewards (and the Crystals reward kind for codes).
PlazaService.Start(GameConfig.Leaderboards.Boards)
LeaderboardService.Start()
GoldenGlacierService.Start()
RewardService.Start()

-- Developer tools: the F2 debug menu (everyone in Studio, allowlist live) and the F3 admin window.
PlayerEffects.Start()
DebugService.Start()
AdminService.Start()

PlayerData.Start()
print("[Server] started")
