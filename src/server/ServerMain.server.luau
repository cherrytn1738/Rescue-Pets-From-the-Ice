-- ServerMain: starts every server system, in order. No gameplay yet (docs/GAME_DESIGN.md).
-- Everything that reacts to a player's data loading (PlayerData.OnLoaded, OnGiftsArrived) must
-- register before PlayerData.Start(), which loads the players already here.
local AdminService = require(script.Parent.AdminService)
local Analytics = require(script.Parent.Analytics)
local CodeService = require(script.Parent.CodeService)
local DebugService = require(script.Parent.DebugService)
local GamePasses = require(script.Parent.GamePasses)
local OfflineEarnings = require(script.Parent.OfflineEarnings)
local PaidRandomPolicy = require(script.Parent.PaidRandomPolicy)
local PlayerData = require(script.Parent.PlayerData)
local PlayerEffects = require(script.Parent.PlayerEffects)
local Receipts = require(script.Parent.Receipts)
local RobuxShop = require(script.Parent.RobuxShop)

-- Robux: pass ownership, paid-random-item rules, the one ProcessReceipt handler (and gifts), the shop.
PaidRandomPolicy.Start()
GamePasses.Start()
Receipts.Start() -- (also starts Gifting)
RobuxShop.Start()

OfflineEarnings.Start() -- pays for the time away once the game registers an earner (OfflineEarnings.SetEarner)
Analytics.Start() -- Roblox funnels (AnalyticsConfig); nothing is sent from Studio
CodeService.Start() -- promo codes (CodesConfig, server only)

-- Developer tools: the F2 debug menu (everyone in Studio, allowlist live) and the F3 admin window.
PlayerEffects.Start()
DebugService.Start()
AdminService.Start()

PlayerData.Start()
print("[Server] started")
