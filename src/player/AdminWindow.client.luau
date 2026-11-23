-- The admin window (developer only): live-server commands such as server info, kicking, and the
-- harmless player effects (launch, rocket, jail). Built ONLY
-- when the server marked this player with the AdminAccess attribute (the AdminConfig allowlist in
-- live servers, everyone in Studio). The server checks access again on every command, so this UI
-- decides nothing. F3 or the ADMIN button toggles it. The commands come from the server
-- (src/server/AdminCommands.luau); the window itself is ActionMenu.
local Players = game:GetService("Players")

local ActionMenu = require(script.Parent:WaitForChild("ActionMenu"))

local localPlayer = Players.LocalPlayer

local function build()
	ActionMenu.Build({
		guiName = "AdminWindow",
		title = "ADMIN",
		remoteName = "AdminRequest",
		toggleKey = Enum.KeyCode.F3,
		buttonName = "AdminButton",
		buttonText = "ADMIN",
		buttonColor = Color3.fromRGB(210, 60, 60),
		buttonY = 0.42,
		accent = Color3.fromRGB(230, 80, 80),
		displayOrder = 31,
		noAccessText = "No admin access",
	})
end

if localPlayer:GetAttribute("AdminAccess") == true then
	build()
else
	local connection
	connection = localPlayer:GetAttributeChangedSignal("AdminAccess"):Connect(function()
		if localPlayer:GetAttribute("AdminAccess") == true then
			connection:Disconnect()
			build()
		end
	end)
end
