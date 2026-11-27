-- The hover tick: a very short, very quiet sound (AudioConfig.Ui.Hover, through Audio so the Sound effects
-- volume applies) when the mouse moves ONTO something clickable, never while it stays there:
--  * any button on screen (every UI kit button, card and tab): the topmost one under the cursor that would take
--    the click. A button with the NoHover attribute (a window's click-catching scrim) or one that can't be
--    interacted with (Interactable off: the tutorial's darkened buttons) counts as nothing;
--  * in the world, when no window is open and no UI is under the cursor: your own ice block (while it's there
--    to tap) and anything with a ProximityPrompt or ClickDetector (the daily chest, the codes kiosk, the chests).
-- Desktop only: touch screens have no hover, and a gamepad moves a selection instead. At most one tick every
-- AudioConfig.Rules.Hover.MinGap seconds.
local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Audio = require(ReplicatedStorage.Audio)
local AudioConfig = require(ReplicatedStorage.AudioConfig)
local UIKit = require(ReplicatedStorage.UIKit)
local IceBlocks = require(script.Parent:WaitForChild("IceBlocks"))

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local RULES = AudioConfig.Rules.Hover
local CHECK_EVERY = 1 / 30 -- seconds between looks at what's under the cursor

local MOUSE_INPUTS = {
	[Enum.UserInputType.MouseMovement] = true,
	[Enum.UserInputType.MouseButton1] = true,
	[Enum.UserInputType.MouseButton2] = true,
	[Enum.UserInputType.MouseButton3] = true,
	[Enum.UserInputType.MouseWheel] = true,
}

local function usingMouse(): boolean
	return UserInputService.MouseEnabled and MOUSE_INPUTS[UserInputService:GetLastInputType()] == true
end

local function canClick(object: GuiObject): boolean
	-- (a greyed-out kit button is still clickable: it answers with the "locked" thunk)
	return object.Interactable and object:GetAttribute("NoHover") ~= true
end

-- The button that would take a click at this point (nil if none), and whether any UI is under it at all.
local function buttonAt(point: Vector2): (GuiObject?, boolean)
	local objects = playerGui:GetGuiObjectsAtPosition(point.X, point.Y)
	for _, object in objects do
		if object:IsA("GuiButton") or object:IsA("TextBox") then
			return if canClick(object) then object else nil, true
		end
		if object.Active then
			return nil, true -- a panel that takes the click itself
		end
	end
	return nil, false -- (labels and pictures let the click through to the world)
end

local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Exclude

-- What clickable thing in the world is under this point (the thing itself, so moving across its parts doesn't tick).
local function worldAt(point: Vector2): Instance?
	local camera = Workspace.CurrentCamera
	local ray = camera:ViewportPointToRay(point.X, point.Y)
	params.FilterDescendantsInstances = { player.Character }
	local hit = Workspace:Raycast(ray.Origin, ray.Direction * 400, params)
	if not hit then
		return nil
	end
	local index = player:GetAttribute("PlotIndex")
	local view = type(index) == "number" and IceBlocks.View(index) or nil
	if view and view.present and (hit.Instance == view.block or hit.Instance:IsDescendantOf(view.folder)) then
		return view.block
	end
	local node: Instance? = hit.Instance
	while node and node ~= Workspace do
		if node:FindFirstChildOfClass("ProximityPrompt") or node:FindFirstChildOfClass("ClickDetector") then
			return node
		end
		node = node.Parent
	end
	return nil
end

local current: Instance? = nil
local lastTick = -math.huge
local lastCheck = 0

RunService.RenderStepped:Connect(function()
	local now = os.clock()
	if now - lastCheck < CHECK_EVERY then
		return
	end
	lastCheck = now
	if not usingMouse() then
		current = nil
		return
	end
	local mouse = UserInputService:GetMouseLocation() -- (the full screen; GUI positions start below the top bar)
	local guiPoint = mouse - GuiService:GetGuiInset()
	local target, overUi = buttonAt(guiPoint)
	if not target and not overUi and not UIKit.AnyWindowOpen() then
		target = worldAt(mouse)
	end
	if target ~= current then
		current = target
		if target and now - lastTick >= RULES.MinGap then
			lastTick = now
			Audio.Play("Hover")
		end
	end
end)
