--[[
thumbnail_cameras.luau: camera presets for retaking the launch thumbnails at full resolution (the drafts in
store-assets/launch/ were captured from a small Studio test window and scaled up). Run in Play, in the
command bar on the CLIENT, with SCENE set; then take the screenshot (Studio: View > Screenshot, or run the
game full screen and press the Roblox screenshot key). Hides the debug and admin buttons and the tutorial;
set HUD = false to hide the HUD too. Stop the preset with STOP = true.
Scenes (your own plot = PlotIndex):
  "MaxedPlot"  across your maxed plot towards the ice (max it first: debug Add crystals, Build x100, upgrades;
               a Legendary in the block: debug "Pick the creature inside"; block level 400: debug SetBlockLevel)
  "Rescue"     your tapping spot looking at the ice (shatter a Mythic: debug "Pick the creature inside", then
               Shatter Now; the first moment is the shot)
  "Glacier"    the plaza looking at the Golden Glacier's landing spot (debug "Spawn a Golden Glacier", players
               tapping it)
  "FreshPlot"  a new plot from beside the tapping spot (debug "Reset to a fresh save")
]]
local SCENE = "MaxedPlot"
local HUD = true
local STOP = false

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local MapConfig = require(game:GetService("ReplicatedStorage").MapConfig)
local player = Players.LocalPlayer
local index = player:GetAttribute("PlotIndex") or 1
local SCENES = {
	MaxedPlot = { MapConfig.PlotPoint(index, -34, 40, 30), MapConfig.PlotPoint(index, 2, 0, 12), 55 },
	Rescue = { MapConfig.PlotPoint(index, 0, 40, 14), MapConfig.PlotPoint(index, 0, 0, 10), 60 },
	Glacier = { Vector3.new(-12, 10, -8), Vector3.new(0, 5, -34), 60 },
	FreshPlot = { MapConfig.PlotPoint(index, 10, 34, 9), MapConfig.PlotPoint(index, 0, 0, 7), 60 },
}
pcall(function()
	RunService:UnbindFromRenderStep("ThumbnailCamera")
end)
local camera = workspace.CurrentCamera
if STOP then
	camera.CameraType = Enum.CameraType.Custom
	return
end
for _, gui in player.PlayerGui:GetChildren() do
	if gui:IsA("ScreenGui") and (string.find(gui.Name, "Debug") or string.find(gui.Name, "Admin") or string.find(gui.Name, "Tutorial")) then
		gui.Enabled = false
	elseif gui.Name == "HUD" then
		gui.Enabled = HUD
	end
end
local scene = SCENES[SCENE]
RunService:BindToRenderStep("ThumbnailCamera", Enum.RenderPriority.Last.Value, function()
	camera.CameraType = Enum.CameraType.Scriptable
	camera.FieldOfView = scene[3]
	camera.CFrame = CFrame.lookAt(scene[1], scene[2])
end)
