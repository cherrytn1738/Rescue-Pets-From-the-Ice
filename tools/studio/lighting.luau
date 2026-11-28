--[[
lighting.luau: the place's lighting in Edit mode (the command bar or MCP execute_luau), so Studio shows the game's
fixed look (LightingConfig.Default, the pink dusk) while editing; then save the place. In a Play each client runs the
day-night cycle itself (DayNight.client). Every value is in src/replicated/LightingConfig.luau, and the
game applies the same at the start of every server (LightingService), so the place file is never the only copy.

Lighting.Technology can't be set from a script without plugin access: if the report says so, set
Lighting > Technology = Future in the Properties window by hand.
]]
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local report = {}
local ok = pcall(function()
	Lighting.Technology = Enum.Technology.Future
end)
table.insert(report, if ok then "Technology = Future" else "Technology: SET BY HAND (Lighting > Technology = Future)")

-- a fresh copy of LightingConfig (Studio's require keeps the first copy it loaded in a session)
local fresh = ReplicatedStorage.LightingConfig:Clone()
fresh.Parent = ServerStorage
local LightingConfig = require(fresh)
fresh:Destroy()

table.insert(report, LightingConfig.Apply(Lighting))
table.insert(report, "save the place")
return table.concat(report, "\n")
