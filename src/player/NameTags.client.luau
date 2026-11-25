-- The stations' name tags ("Ice Drill ×100 ★"; PlotService makes them small and hidden). Every frame:
--  - a station's tag shows while your character is near it (BuildingConfig.NameTags.NearDistance), and your own
--    plot's tags show while you're in your plot or the camera looks at it (LookAngle, LookDistance);
--  - any tag (the plots' owner signs too) hides while its rectangle on screen reaches into the top centre,
--    where the HUD's crystal counter is (TopCentre, grown to cover the counter if it is bigger).
local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local BuildingConfig = require(ReplicatedStorage.BuildingConfig)
local MapConfig = require(ReplicatedStorage.MapConfig)

local SETTINGS = BuildingConfig.NameTags
local player = Players.LocalPlayer

-- The top-centre area kept clear, in viewport pixels.
local function clearArea(camera: Camera): (Vector2, Vector2)
	local viewport = camera.ViewportSize
	local half = viewport.X * SETTINGS.TopCentre.X / 2
	local low = Vector2.new(viewport.X / 2 - half, 0)
	local high = Vector2.new(viewport.X / 2 + half, viewport.Y * SETTINGS.TopCentre.Y)
	local hud = player.PlayerGui:FindFirstChild("HUD")
	local counter = hud and hud:FindFirstChild("Counter", true)
	if counter and counter:IsA("GuiObject") and counter.Visible then
		local inset = if hud.IgnoreGuiInset then Vector2.zero else GuiService:GetGuiInset()
		local topLeft = counter.AbsolutePosition + inset
		local bottomRight = topLeft + counter.AbsoluteSize
		low = Vector2.new(math.min(low.X, topLeft.X), 0)
		high = Vector2.new(math.max(high.X, bottomRight.X), math.max(high.Y, bottomRight.Y))
	end
	return low, high
end

-- Does the tag's rectangle on screen overlap the area?
local function overlaps(gui: BillboardGui, camera: Camera, low: Vector2, high: Vector2): boolean
	local adornee = gui.Adornee or gui.Parent
	if not adornee or not adornee:IsA("BasePart") then
		return false
	end
	local centre = adornee.Position + gui.StudsOffsetWorldSpace
	local point = camera:WorldToViewportPoint(centre)
	if point.Z <= 0 then
		return false -- behind the camera
	end
	local right = camera:WorldToViewportPoint(centre + camera.CFrame.RightVector * gui.Size.X.Scale / 2)
	local up = camera:WorldToViewportPoint(centre + camera.CFrame.UpVector * gui.Size.Y.Scale / 2)
	local halfWidth, halfHeight = math.abs(right.X - point.X), math.abs(up.Y - point.Y)
	return point.X + halfWidth > low.X and point.X - halfWidth < high.X and point.Y + halfHeight > low.Y and point.Y - halfHeight < high.Y
end

-- Is the player in their own plot, or is the camera looking at it?
local function watchingOwnPlot(camera: Camera, root: BasePart?): boolean
	local index = player:GetAttribute("PlotIndex")
	if typeof(index) ~= "number" then
		return false
	end
	local plot = MapConfig.PlotCFrame(index)
	if root then
		local at = plot:PointToObjectSpace(root.Position)
		local half = MapConfig.PlotSize / 2 + MapConfig.TapMargin
		if math.abs(at.X) <= half and math.abs(at.Z) <= half then
			return true
		end
	end
	local toPlot = plot.Position - camera.CFrame.Position
	if toPlot.Magnitude > SETTINGS.LookDistance then
		return false
	end
	return math.deg(math.acos(math.clamp(toPlot.Unit:Dot(camera.CFrame.LookVector), -1, 1))) <= SETTINGS.LookAngle
end

RunService:BindToRenderStep("NameTags", Enum.RenderPriority.Camera.Value + 1, function()
	local plots = Workspace:FindFirstChild("Plots")
	local camera = Workspace.CurrentCamera
	if not plots or not camera then
		return
	end
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	local low, high = clearArea(camera)
	local watching = watchingOwnPlot(camera, root)
	for _, plot in plots:GetChildren() do
		local own = plot:GetAttribute("Owner") == player.UserId
		local sign = plot:FindFirstChild("Sign")
		local ownerLabel = sign and sign:FindFirstChild("OwnerLabel")
		if ownerLabel then
			ownerLabel.Enabled = not overlaps(ownerLabel, camera, low, high)
		end
		local buildings = plot:FindFirstChild("Buildings")
		if not buildings then
			continue
		end
		for _, station in buildings:GetChildren() do
			local holder = if station:IsA("Model") then station.PrimaryPart else station
			local tag = holder and holder:FindFirstChild("Label")
			if not tag or not tag:GetAttribute("NameTag") then
				continue
			end
			local near = root ~= nil and (holder.Position - root.Position).Magnitude <= SETTINGS.NearDistance
			tag.Enabled = (near or (own and watching)) and not overlaps(tag, camera, low, high)
		end
	end
end)
