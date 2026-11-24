-- Pets following their owners (docs/GAME_DESIGN.md, "How buildings, upgrades and pets look"): every
-- client draws every player's equipped pets from their EquippedPets attribute (PetService), built from
-- the voxel models (PetLooks; Golden ones with the gold material swap). They walk in an arc behind the
-- owner, play Idle standing and Hop moving; your own pets also hop when you tap and cheer when you
-- free a creature. Display only.
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local PetAnimator = require(ReplicatedStorage.Pets.PetAnimator)
local PetLooks = require(ReplicatedStorage.Pets.PetLooks)
local ClientState = require(script.Parent:WaitForChild("ClientState"))
local Effects = require(script.Parent:WaitForChild("Effects"))

local localPlayer = Players.LocalPlayer
local owners = {} -- [player] = { pets = { [uid] = pet }, key = json }
local FOLLOW_DISTANCE = 6
local SPREAD = math.rad(34)
local MAX_DRAW_DISTANCE = 220 -- far players' pets aren't animated

local function clear(state)
	for _, pet in state.pets do
		pet.model:Destroy()
	end
	table.clear(state.pets)
end

local function refresh(owner: Player)
	local state = owners[owner]
	if not state then
		state = { pets = {}, key = nil, order = {} }
		owners[owner] = state
	end
	local text = owner:GetAttribute("EquippedPets") or "[]"
	if text == state.key then
		return
	end
	state.key = text
	local ok, list = pcall(HttpService.JSONDecode, HttpService, text)
	if not ok or type(list) ~= "table" then
		list = {}
	end
	local keep = {}
	state.order = {}
	for _, entry in list do
		if type(entry) == "table" and type(entry.Uid) == "string" then
			keep[entry.Uid] = true
			table.insert(state.order, entry.Uid)
			if not state.pets[entry.Uid] then
				local data, clips = PetLooks.Data(entry.CreatureId), PetLooks.Clips(entry.CreatureId)
				local root = owner.Character and owner.Character:FindFirstChild("HumanoidRootPart")
				local start = if root then root.CFrame * CFrame.new(0, -2.8, 4) else CFrame.new(0, -500, 0)
				local model = data and PetLooks.Build(entry.CreatureId, start, if entry.Golden then "Golden" else "Normal")
				if model then
					model.Name = "Pet_" .. owner.Name .. "_" .. entry.CreatureId
					model.Parent = Effects.Folder()
					local animator = clips and PetAnimator.new(model, data, clips)
					if animator then
						animator:Play("Idle", true, 0)
						animator.Time = math.random() * 2
					end
					state.pets[entry.Uid] = { model = model, animator = animator, clip = "Idle", oneShotUntil = 0, at = start }
				end
			end
		end
	end
	for uid, pet in state.pets do
		if not keep[uid] then
			pet.model:Destroy()
			state.pets[uid] = nil
		end
	end
end

local function watch(owner: Player)
	owner:GetAttributeChangedSignal("EquippedPets"):Connect(function()
		refresh(owner)
	end)
	refresh(owner)
end

-- A one-shot clip on your own pets (Hop on a tap, Cheer on a rescue), then back to walking/idling.
local function oneShot(clip: string, seconds: number)
	local state = owners[localPlayer]
	if not state then
		return
	end
	for _, pet in state.pets do
		if pet.animator and os.clock() >= pet.oneShotUntil then
			pet.animator:Play(clip, false, 0.08)
			pet.clip = clip
			pet.oneShotUntil = os.clock() + seconds
		end
	end
end

Players.PlayerAdded:Connect(watch)
for _, owner in Players:GetPlayers() do
	watch(owner)
end
Players.PlayerRemoving:Connect(function(owner)
	local state = owners[owner]
	if state then
		clear(state)
		owners[owner] = nil
	end
end)

UserInputService.InputBegan:Connect(function(input, processed)
	if not processed and (input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch) then
		if math.random() < 0.5 then
			oneShot("Hop", 0.8)
		end
	end
end)
ClientState.Event("Rescue", function()
	oneShot("Cheer", 1.4)
end)

RunService.RenderStepped:Connect(function(dt)
	local camera = workspace.CurrentCamera
	for owner, state in owners do
		local character = owner.Character
		local root = character and character:FindFirstChild("HumanoidRootPart")
		local humanoid = character and character:FindFirstChildOfClass("Humanoid")
		if not root or not humanoid then
			continue
		end
		local far = (root.Position - camera.CFrame.Position).Magnitude > MAX_DRAW_DISTANCE
		local moving = root.AssemblyLinearVelocity.Magnitude > 2
		local ground = root.Position.Y - humanoid.HipHeight - root.Size.Y / 2
		local count = #state.order
		for slot, uid in state.order do
			local pet = state.pets[uid]
			if not pet then
				continue
			end
			-- an arc behind the owner
			local angle = (slot - (count + 1) / 2) * SPREAD
			local offset = CFrame.Angles(0, angle, 0) * Vector3.new(0, 0, FOLLOW_DISTANCE + math.floor((slot - 1) / 4) * 3)
			local flatLook = Vector3.new(root.CFrame.LookVector.X, 0, root.CFrame.LookVector.Z)
			if flatLook.Magnitude < 1e-3 then
				flatLook = Vector3.zAxis
			end
			local facing = CFrame.lookAt(root.Position, root.Position + flatLook)
			local target = (facing * CFrame.new(offset)).Position
			target = Vector3.new(target.X, ground, target.Z)
			local here = pet.at.Position
			local nextPos = here:Lerp(target, math.min(1, dt * 8))
			if (target - here).Magnitude > 60 then
				nextPos = target -- teleported owner: catch up at once
			end
			local lookAt = if moving then target + flatLook * 4 else root.Position
			lookAt = Vector3.new(lookAt.X, nextPos.Y, lookAt.Z)
			pet.at = if (lookAt - nextPos).Magnitude > 0.1 then CFrame.lookAt(nextPos, lookAt) else CFrame.new(nextPos) * pet.at.Rotation
			pet.model:PivotTo(pet.at)
			if pet.animator and not far then
				if os.clock() >= pet.oneShotUntil then
					local want = if moving then "Hop" else "Idle"
					if pet.clip ~= want then
						pet.animator:Play(want, true, 0.2)
						pet.clip = want
					end
				end
				pcall(pet.animator.Step, pet.animator, dt)
			end
		end
	end
end)
