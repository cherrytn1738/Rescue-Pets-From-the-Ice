-- ServerMain: starts every server system, in order (docs/GAME_DESIGN.md).
-- Everything that reacts to a player's data loading (PlayerData.OnLoaded, OnGiftsArrived) must
-- register before PlayerData.Start(), which loads the players already here.

-- A soft shutdown's holding server (a reserved server on the way back from an update) runs nothing
-- else: no gameplay, no saves (SoftShutdown).
local SoftShutdown = require(script.Parent.SoftShutdown)
if SoftShutdown.IsHoldingServer() then
	SoftShutdown.RunHoldingServer()
	return
end

local AdminService = require(script.Parent.AdminService)
local Analytics = require(script.Parent.Analytics)
local Announcements = require(script.Parent.Announcements)
local CodeService = require(script.Parent.CodeService)
local DebugService = require(script.Parent.DebugService)
local Economy = require(script.Parent.Economy)
local GamePasses = require(script.Parent.GamePasses)
local GameConfig = require(game:GetService("ReplicatedStorage").GameConfig)
local GoldenGlacierService = require(script.Parent.GoldenGlacierService)
local IceBlockService = require(script.Parent.IceBlockService)
local LeaderboardService = require(script.Parent.LeaderboardService)
local LightingService = require(script.Parent.LightingService)
local OfflineEarnings = require(script.Parent.OfflineEarnings)
local PaidRandomPolicy = require(script.Parent.PaidRandomPolicy)
local PetService = require(script.Parent.PetService)
local PickService = require(script.Parent.PickService)
local PlayerData = require(script.Parent.PlayerData)
local PlayerEffects = require(script.Parent.PlayerEffects)
local PlazaService = require(script.Parent.PlazaService)
local PlotService = require(script.Parent.PlotService)
local RankService = require(script.Parent.RankService)
local RebirthService = require(script.Parent.RebirthService)
local Receipts = require(script.Parent.Receipts)
local RewardService = require(script.Parent.RewardService)
local RobuxPerks = require(script.Parent.RobuxPerks)
local RobuxShop = require(script.Parent.RobuxShop)
local SettingsService = require(script.Parent.SettingsService)
local ShopService = require(script.Parent.ShopService)
local TapService = require(script.Parent.TapService)
local TutorialService = require(script.Parent.TutorialService)
local WelcomeBack = require(script.Parent.WelcomeBack)

-- Robux: pass ownership, paid-random-item rules, the one ProcessReceipt handler (and gifts), the shop.
PaidRandomPolicy.Start()
GamePasses.Start()
Receipts.Start() -- (also starts Gifting)
RobuxShop.Start()

OfflineEarnings.Start() -- pays for the time away (the earner is Economy's building income)
WelcomeBack.Start() -- the Welcome Back screen's x2 offer (Double Welcome Back), made at each payout
Analytics.Start() -- Roblox funnels (AnalyticsConfig); nothing is sent from Studio
CodeService.Start() -- promo codes (CodesConfig, server only)

-- Gameplay: plots, the crystal economy and its 4-a-second tick, the ice block, tapping, buying, pets.
PlotService.Start()
Economy.Start()
IceBlockService.Start()
TapService.Start()
ShopService.Start()
PetService.Start()
PickService.Start() -- the ice pick each player carries, for their pick tier
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
RobuxPerks.Start() -- what each pass and product does (reward kinds, pass perks, Auto Pick, Server Frost Rush)
LightingService.Start() -- the warm winter sunset (LightingConfig) and the lamps at the gates, boards and plaza

-- Live ops: server-wide messages (admin announcements, every server via MessagingService) and the soft
-- shutdown (saves, an update screen and straight back on a new server when servers restart).
Announcements.Start()
SoftShutdown.Start()

-- Developer tools: the F2 debug menu (everyone in Studio, allowlist live) and the F3 admin window.
PlayerEffects.Start()
DebugService.Start()
AdminService.Start()

-- Server-to-client remotes: a client firing them at the server is ignored (a handler, so Roblox doesn't
-- queue the calls and warn about it).
for _, name in { "GameEvent", "PurchaseNotice" } do
	game:GetService("ReplicatedStorage"):WaitForChild(name).OnServerEvent:Connect(function() end)
end

-- Analytics hooks (AnalyticsConfig): every crystal earned and spent, and the progression funnels after
-- anything that can raise a layer or a rank.
Economy.OnGrant(Analytics.CrystalsEarned)
ShopService.OnBought(function(player, data, kind, id, _, cost)
	Analytics.CrystalsSpent(player, kind, cost, data.Crystals, id)
end)
IceBlockService.OnRescue(Analytics.Progress)
RebirthService.OnRebirth(Analytics.Progress)

PlayerData.Start()
print("[Server] started")
