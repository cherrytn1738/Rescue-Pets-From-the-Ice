--[[
ao_test.luau: the baked-AO TEST template (Edit mode, then save the place). Builds ServerStorage.AOTest.IceDrill.T5:
a copy of the real Mecha Mole Titan template (its Root, attachments and upgrade sets) whose station meshes come
from the AO test model (store-assets/ao-test/IceDrill/: tools/blender/ao_bake.py). Each baked mesh shows the
station's own AO texture; glow meshes keep the palette. Every other setting is copied from the real part of the
same name. The real template is never changed: tools/studio/ao_test_swap.luau swaps the test one in for a play
test only.
]]
local InsertService = game:GetService("InsertService")
local ServerStorage = game:GetService("ServerStorage")

local MODEL = 99932455112348 -- store-assets/ao-test/upload_manifest.json: IceDrill/fbx/IceDrill_T5_AO.fbx
local TEXTURE = "rbxassetid://127282647089686" -- IceDrill/IceDrill_T5_AO.png
local FACTOR = 25 -- exported at a quarter scale

local real = ServerStorage.BuildingTemplates.IceDrill.T5
local folder = ServerStorage:FindFirstChild("AOTest") or Instance.new("Folder")
folder.Name = "AOTest"
folder.Parent = ServerStorage
local set = folder:FindFirstChild("IceDrill") or Instance.new("Folder")
set.Name = "IceDrill"
set.Parent = folder
local old = set:FindFirstChild("T5")
if old then
	old:Destroy()
end

local model = real:Clone()
for _, p in model:GetChildren() do
	if p:IsA("MeshPart") then
		p:Destroy()
	end
end
local container = InsertService:LoadAsset(MODEL)
local loaded, baked, missing = 0, 0, {}
for _, p in container:GetDescendants() do
	if p:IsA("MeshPart") then
		local twin = real:FindFirstChild(p.Name)
		if not twin then
			table.insert(missing, p.Name)
			continue
		end
		p.Size /= FACTOR
		p.CFrame = CFrame.new(p.Position / FACTOR) * p.CFrame.Rotation
		local glow = string.sub(p.Name, -4) == "Glow"
		p.TextureID = if glow then twin.TextureID else TEXTURE
		p.Color = twin.Color
		p.Material = twin.Material
		p.CastShadow = twin.CastShadow
		p.RenderFidelity = twin.RenderFidelity
		p.CollisionFidelity = twin.CollisionFidelity
		p.CanCollide, p.CanQuery, p.CanTouch = twin.CanCollide, twin.CanQuery, twin.CanTouch
		p.DoubleSided = twin.DoubleSided
		p.Anchored = true
		p.Parent = model
		loaded += 1
		if not glow then
			baked += 1
		end
	end
end
container:Destroy()
model:SetAttribute("AOTest", true)
model.Parent = set
local realCount = 0
for _, p in real:GetChildren() do
	if p:IsA("MeshPart") then
		realCount += 1
	end
end
return string.format("AOTest.IceDrill.T5: %d meshes (%d with the AO texture) of the real %d; height %.1f (real %.1f)%s",
	loaded, baked, realCount, model:GetExtentsSize().Y, real:GetExtentsSize().Y,
	if #missing > 0 then " | NO TWIN: " .. table.concat(missing, ", ") else "")
