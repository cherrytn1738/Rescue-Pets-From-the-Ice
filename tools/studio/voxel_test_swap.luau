--[[
voxel_test_swap.luau: the voxel STYLE TEST, in a play test only (run on the Server through MCP execute_luau
while Studio is in Play mode; everything it changes is thrown away when the play test stops).
STYLE = "A" | "B" | "Real": puts that style's templates (ServerStorage.VoxelTest.<style>, built by
build_voxel_test.luau) in place of the real ones for the buildings the test covers, and clears those
stations from every plot. The plot rebuilds them on its next refresh (buy one more of the building).
]]
local STYLE = "%STYLE%"
local ServerStorage = game:GetService("ServerStorage")
local test = ServerStorage.VoxelTest
local real = test:FindFirstChild("Real")
if not real then
	real = Instance.new("Folder")
	real.Name = "Real"
	real.Parent = test
end
local swapped = {}
for _, building in test.A:GetChildren() do
	local slot = ServerStorage.BuildingTemplates[building.Name]
	local keep = real:FindFirstChild(building.Name)
	if not keep then
		keep = Instance.new("Folder")
		keep.Name = building.Name
		keep.Parent = real
	end
	for _, tier in building:GetChildren() do
		if not keep:FindFirstChild(tier.Name) then
			slot[tier.Name]:Clone().Parent = keep
		end
		local source = if STYLE == "Real" then keep[tier.Name] else test[STYLE][building.Name][tier.Name]
		slot[tier.Name]:Destroy()
		local copy = source:Clone()
		copy.Name = tier.Name
		copy.Parent = slot
		table.insert(swapped, building.Name .. "." .. tier.Name)
	end
	for _, plot in workspace.Plots:GetChildren() do
		local station = plot.Buildings:FindFirstChild(building.Name)
		if station then
			station:Destroy()
		end
	end
end
return STYLE .. ": " .. table.concat(swapped, ", ")
