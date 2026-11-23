--[[
PetLooks: the three looks of a voxel pet (docs/GAME_DESIGN.md, "Creature roster"), all from the same
model, so there are no extra models:
  Normal      the creature's own colours (the <Id>Data palette).
  Silhouette  one dark shade, no studs, no glow: the shape seen inside the ice block. Eyes can be
              switched on separately (ShowEyes), for the crack stage where they become visible.
  Golden      a material swap: every part turns gold, darker or lighter by its normal colour's
              brightness so the markings still read, in Foil; the eyes (the Data's Eyes keys) keep their
              colour and glowing parts stay Neon.
Every part is named by its palette key (PetBuild), so a look is just a pass over the parts.

  PetLooks.Build(creatureId, cframe, look?)  builds the pet (PetBuild) and applies the look
  PetLooks.Apply(model, data, look)          re-colours a built pet
  PetLooks.Data(creatureId) / Clips(creatureId)  the generated modules
]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PetBuild = require(script.Parent.PetBuild)

local PetLooks = {}

PetLooks.SilhouetteColor = Color3.fromRGB(27, 36, 51)
PetLooks.GoldColor = Color3.fromRGB(255, 197, 49)

local models = script.Parent:WaitForChild("Models")
local cache = {}

local STUD_FACES = { "TopSurface", "BottomSurface", "FrontSurface", "BackSurface", "LeftSurface", "RightSurface" }
local DEFAULT_NOSTUD = { EY = true, IR = true, WH = true, SH = true, PU = true }

function PetLooks.Data(creatureId: string)
	local key = creatureId .. "Data"
	if cache[key] == nil then
		local module = models:FindFirstChild(key)
		cache[key] = if module then require(module) else false
	end
	return cache[key] or nil
end

function PetLooks.Clips(creatureId: string)
	local key = creatureId .. "Clips"
	if cache[key] == nil then
		local module = models:FindFirstChild(key)
		cache[key] = if module then require(module) else false
	end
	return cache[key] or nil
end

local function luminance(color: Color3): number
	return 0.2126 * color.R + 0.7152 * color.G + 0.0722 * color.B
end

local function setStuds(part: BasePart, on: boolean)
	for _, face in STUD_FACES do
		part[face] = if on then Enum.SurfaceType.Studs else Enum.SurfaceType.Smooth
	end
end

function PetLooks.Apply(model: Model, data, look: string)
	local eyes = data.Eyes or DEFAULT_NOSTUD
	local glow = data.Glow or {}
	local noStud = data.NoStud or DEFAULT_NOSTUD
	for _, part in model:GetChildren() do
		if not part:IsA("BasePart") or not data.Colors[part.Name] then
			continue
		end
		local key = part.Name
		local base = Color3.fromHex(data.Colors[key])
		if look == "Silhouette" then
			part.Color = PetLooks.SilhouetteColor
			part.Material = Enum.Material.SmoothPlastic
			setStuds(part, false)
		elseif look == "Golden" then
			if eyes[key] then
				part.Color = base
			else
				local shade = 0.5 + 0.65 * luminance(base)
				local gold = PetLooks.GoldColor
				part.Color = Color3.new(math.min(1, gold.R * shade), math.min(1, gold.G * shade), math.min(1, gold.B * shade))
			end
			if glow[key] then
				part.Material = Enum.Material.Neon
			elseif eyes[key] or noStud[key] then
				part.Material = Enum.Material.SmoothPlastic
			else
				part.Material = Enum.Material.Foil
				setStuds(part, true)
			end
		else -- Normal
			part.Color = base
			if glow[key] then
				part.Material = Enum.Material.Neon
			elseif noStud[key] then
				part.Material = Enum.Material.SmoothPlastic
			else
				part.Material = Enum.Material.Plastic
				setStuds(part, true)
			end
		end
	end
	model:SetAttribute("Look", look)
end

-- Silhouette only: the eyes show in their own colours (on) or dark again (off).
function PetLooks.ShowEyes(model: Model, data, on: boolean)
	local eyes = data.Eyes or DEFAULT_NOSTUD
	for _, part in model:GetChildren() do
		if part:IsA("BasePart") and eyes[part.Name] and data.Colors[part.Name] then
			part.Color = if on then Color3.fromHex(data.Colors[part.Name]) else PetLooks.SilhouetteColor
			part.Material = if on and (data.Glow or {})[part.Name] then Enum.Material.Neon else Enum.Material.SmoothPlastic
		end
	end
end

-- Builds the pet standing at cframe (its feet on cframe's position, facing its LookVector).
function PetLooks.Build(creatureId: string, cframe: CFrame, look: string?): Model?
	local data = PetLooks.Data(creatureId)
	if not data then
		warn("[Pets] no model for " .. tostring(creatureId))
		return nil
	end
	local model = PetBuild(data, cframe, creatureId)
	PetLooks.Apply(model, data, look or "Normal")
	return model
end

return PetLooks
