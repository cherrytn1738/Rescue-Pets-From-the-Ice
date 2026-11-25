-- The VIP lounge's door (docs/GAME_DESIGN.md, "Monetization"; PlazaService builds the lounge once the VIP
-- pass is in MonetizationConfig). The door is a solid invisible wall; for an owner of its pass (the door's
-- Pass attribute; the Owns_<Key> player attribute the server sets) this client turns its collision off, so
-- they walk in. Your own character's physics runs on your client, so this is all it takes; the lounge is a
-- hangout with no gameplay advantage. Anyone else who walks into it is told how to get in.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local Banners = require(script.Parent.Banners)

local player = Players.LocalPlayer
local plaza = Workspace:WaitForChild("Plaza", 60)
local gate = plaza and plaza:WaitForChild("VipGate", 30)
local door = gate and gate:WaitForChild("VipDoor", 10)
if not door then
	return -- no VIP pass in the config yet: no lounge
end

local passKey = door:GetAttribute("Pass") or "VIP"
local function owns(): boolean
	return player:GetAttribute("Owns_" .. passKey) == true
end
local function apply()
	door.CanCollide = not owns()
end
apply()
player:GetAttributeChangedSignal("Owns_" .. passKey):Connect(apply)

local toldAt = -math.huge
door.Touched:Connect(function(hit)
	local character = player.Character
	if owns() or not character or not hit:IsDescendantOf(character) or os.clock() - toldAt < 6 then
		return
	end
	toldAt = os.clock()
	Banners.Toast("The VIP lounge is for VIP owners: VIP is in the SHOP.", Color3.fromRGB(255, 210, 80))
end)
