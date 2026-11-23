-- ServerMain: starts every server system, in order (docs/GAME_DESIGN.md).
-- Everything that reacts to a player's data loading (PlayerData.OnLoaded, OnGiftsArrived) must
-- register before PlayerData.Start(), which loads the players already here.
local AdminService = require(script.Parent.AdminService)
local Analytics = require(script.Parent.Analytics)
local CodeService = require(script.Parent.CodeService)
local DebugService = require(script.Parent.DebugService)
local Economy = require(script.Parent.Economy)
local GamePasses = require(script.Parent.GamePasses)
local IceBlockService = require(script.Parent.IceBlockService)
local OfflineEarnings = require(script.Parent.OfflineEarnings)
local PaidRandomPolicy = require(script.Parent.PaidRandomPolicy)
local PetService = require(script.Parent.PetService)
local PlayerData = require(script.Parent.PlayerData)
local PlayerEffects = require(script.Parent.PlayerEffects)
local PlotService = require(script.Parent.PlotService)
local Receipts = require(script.Parent.Receipts)
local RobuxShop = require(script.Parent.RobuxShop)
local ShopService = require(script.Parent.ShopService)
local TapService = require(script.Parent.TapService)

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

-- Developer tools: the F2 debug menu (everyone in Studio, allowlist live) and the F3 admin window.
PlayerEffects.Start()
DebugService.Start()
AdminService.Start()

PlayerData.Start()
print("[Server] started")
