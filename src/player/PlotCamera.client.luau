-- Puts the camera behind the character whenever the server moves it to its plot (on spawn, and with
-- the Home button), so the player looks at their ice, not back at the plaza.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local player = Players.LocalPlayer

local function behind(root: BasePart)
	local camera = Workspace.CurrentCamera
	local look = root.CFrame.LookVector
	camera.CFrame = CFrame.lookAt(root.Position - look * 16 + Vector3.new(0, 7, 0), root.Position + look * 6)
end

local function watch(character: Model)
	local root = character:WaitForChild("HumanoidRootPart", 10) :: BasePart?
	if not root then
		return
	end
	-- a jump of more than 30 studs in one step is the server moving us (spawn, Home)
	local last = root.Position
	task.spawn(function()
		while character.Parent do
			local now = root.Position
			if (now - last).Magnitude > 30 then
				behind(root)
			end
			last = now
			task.wait()
		end
	end)
end

player.CharacterAdded:Connect(watch)
if player.Character then
	task.spawn(watch, player.Character)
end
