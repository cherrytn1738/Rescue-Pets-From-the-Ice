--[[
lighting.luau: the place's lighting in Edit mode (the command bar or MCP execute_luau), so Studio shows the game's
fixed look (LightingConfig.Default, the pink dusk) while editing; then save the place. In a Play each client runs the
day-night cycle itself (DayNight.client). Every value is in src/replicated/LightingConfig.luau, and the
game applies the same at the start of every server (LightingService), so the place file is never the only copy.

Unified Lighting: Apply also sets Lighting.LightingStyle (Realistic) and PrioritizeLightingQuality (off) from
LightingConfig.Style; Lighting.Technology no longer exists.
]]
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local report = {}

-- a fresh copy of LightingConfig (Studio's require keeps the first copy it loaded in a session)
local fresh = ReplicatedStorage.LightingConfig:Clone()
fresh.Parent = ServerStorage
local LightingConfig = require(fresh)
fresh:Destroy()

table.insert(report, LightingConfig.Apply(Lighting))
table.insert(report, `style: {Lighting.LightingStyle.Name}, PrioritizeLightingQuality {Lighting.PrioritizeLightingQuality}`)
table.insert(report, "save the place")
return table.concat(report, "\n")
