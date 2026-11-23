-- Temporary debug menu (testing only). Built ONLY when the server marked this player with the
-- DebugAccess attribute (everyone in Studio; the DebugConfig allowlist elsewhere). The server checks
-- access again on every request, so this UI decides nothing. F2 or the DEBUG button toggles it.
-- The actions come from the server's catalogue (src/server/DebugActions.luau); the window itself
-- is ActionMenu.
local Players = game:GetService("Players")

local ActionMenu = require(script.Parent:WaitForChild("ActionMenu"))

local localPlayer = Players.LocalPlayer

local function build()
	ActionMenu.Build({
		guiName = "DebugMenu",
		title = "DEBUG MENU",
		remoteName = "DebugRequest",
		toggleKey = Enum.KeyCode.F2,
		buttonName = "DebugButton",
		buttonText = "DEBUG",
		buttonColor = Color3.fromRGB(150, 60, 200),
		buttonY = 0.35,
		accent = Color3.fromRGB(80, 150, 255),
		displayOrder = 30,
		noAccessText = "No debug access",
	})
end

-- No access: nothing is built at all.
if localPlayer:GetAttribute("DebugAccess") == true then
	build()
else
	local connection
	connection = localPlayer:GetAttributeChangedSignal("DebugAccess"):Connect(function()
		if localPlayer:GetAttribute("DebugAccess") == true then
			connection:Disconnect()
			build()
		end
	end)
end
