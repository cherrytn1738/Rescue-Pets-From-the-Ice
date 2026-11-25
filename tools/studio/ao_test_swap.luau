--[[
ao_test_swap.luau: the baked-AO TEST, in a play test only (run on the Server through MCP execute_luau while
Studio is in Play mode; everything it changes is thrown away when the play test stops).
MODE = "AO" | "Real": puts ServerStorage.AOTest.IceDrill.T5 (built by ao_test.luau) or the real Mecha Mole Titan
in BuildingTemplates and clears the Ice Drill stations from every plot. The plot rebuilds them on its next
refresh (buy one more Ice Drill).
]]
local MODE = "%MODE%"
local ServerStorage = game:GetService("ServerStorage")
local slot = ServerStorage.BuildingTemplates.IceDrill
local test = ServerStorage.AOTest.IceDrill
local keep = test:FindFirstChild("Real")
if not keep then
	keep = slot.T5:Clone()
	keep.Name = "Real"
	keep.Parent = test
end
slot.T5:Destroy()
local copy = (if MODE == "AO" then test.T5 else keep):Clone()
copy.Name = "T5"
copy.Parent = slot
for _, plot in workspace.Plots:GetChildren() do
	local station = plot.Buildings:FindFirstChild("IceDrill")
	if station then
		station:Destroy()
	end
end
return MODE .. ": IceDrill.T5 swapped"
