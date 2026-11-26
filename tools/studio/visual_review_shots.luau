--[[
visual_review_shots.luau: every shot of the visual review set (store-assets/visual-review/), as setups
that put the game in the right state, hold the camera and stage the UI. Client side, in Play (solo
Play as the developer: the debug menu works and every pass is owned).

Normally run by `python tools/visual_review.py` (it substitutes SHOT and SIZE, clicks what a shot
asks for, takes the screenshot, crops it and saves it as JPG). By hand, in the command bar on the
CLIENT: set SHOT to a shot name (e.g. "buildings/HeatLamp_T3") and SIZE to "desktop", "844x390" or
"667x375", run it, then look or take a screenshot. SHOT = "?list" returns every shot (JSON);
"?prepare:<category>" sets up a category's starting state; "?cleanup" gives the camera and UI back.

Each shot: Name ("<category>/<file name>"), Sizes (default desktop only), Run(ctx) which sets the scene
and may return { Clicks = { instance paths under the player's PlayerGui, clicked in order },
Close = { paths clicked after the shot }, Wait = seconds before the capture }.
The desktop shot lays the UI out in a 16:9 region at the top left of the viewport (StudioScreenSize)
and turns the camera so its target sits in the middle of that region; the helper crops and scales it
to 1920x1080. Phone sizes lay the UI out at exactly that size at the top left.
]]
local SHOT = "%SHOT%"
local SIZE = "%SIZE%"

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")

local BuildingConfig = require(ReplicatedStorage.BuildingConfig)
local CreatureConfig = require(ReplicatedStorage.CreatureConfig)
local MapConfig = require(ReplicatedStorage.MapConfig)

local me = Players.LocalPlayer
local camera = workspace.CurrentCamera

-- Helpers ----------------------------------------------------------------------------------------

local function dbg(action: string, args)
	-- the debug menu refuses requests closer than DebugConfig.RequestCooldownSeconds (0.1 s): keep a gap
	local last = me:GetAttribute("VisualReviewDebugAt") or 0
	local gap = 0.25 - (os.clock() - last)
	if gap > 0 then
		task.wait(gap)
	end
	me:SetAttribute("VisualReviewDebugAt", os.clock())
	local ok, result = pcall(function()
		return ReplicatedStorage.DebugRequest:InvokeServer("Run", { Action = action, Target = me.UserId, Args = args or {}, Confirmed = true })
	end)
	if not ok or type(result) ~= "table" or result.ok == false then
		warn(`[VisualReview] {action} failed: {if ok and type(result) == "table" then tostring(result.message) else tostring(result)}`)
	end
	return result
end

local function plotIndex(): number
	return me:GetAttribute("PlotIndex") or 1
end
local function plotPoint(x: number, z: number, y: number?): Vector3
	return MapConfig.PlotPoint(plotIndex(), x, z, y)
end
local function root(): BasePart?
	return me.Character and me.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
end
local function waitFor(check: () -> boolean, seconds: number)
	local deadline = os.clock() + seconds
	while os.clock() < deadline and not check() do
		task.wait(0.1)
	end
	return check()
end

local function regionSize(): Vector2
	local vp = camera.ViewportSize
	if SIZE == "844x390" then
		return Vector2.new(844, 390)
	elseif SIZE == "667x375" then
		return Vector2.new(667, 375)
	end
	return Vector2.new(math.floor(vp.Y * 16 / 9), vp.Y)
end

-- Hides name tags, the debug and admin buttons, the Studio screen edge (and the tutorial, the HUD
-- when asked) every frame, so nothing new sneaks back in.
local staging = { hud = true, tutorial = false, banners = true }
local function stage()
	workspace:SetAttribute("StudioScreenSize", regionSize())
	pcall(function()
		RunService:UnbindFromRenderStep("VisualReviewStage")
	end)
	RunService:BindToRenderStep("VisualReviewStage", Enum.RenderPriority.Last.Value, function()
		for _, player in Players:GetPlayers() do
			local character = player.Character
			if character then
				for _, d in character:GetDescendants() do
					if d:IsA("BillboardGui") and (d.Name == "NameTag" or d.Name == "RankTag") then
						d.Enabled = false
					end
				end
			end
		end
		for _, gui in me.PlayerGui:GetChildren() do
			if gui:IsA("ScreenGui") then
				local name = gui.Name
				if string.find(name, "Debug") or string.find(name, "Admin") then
					gui.Enabled = false
				elseif string.find(name, "Tutorial") then
					gui.Enabled = staging.tutorial
				elseif not staging.hud and (name ~= "Banners" or not staging.banners) then
					-- model shots: nothing on screen but the big moments (marked so cleanup turns it back on)
					if gui.Enabled then
						gui:SetAttribute("VisualReviewHidden", true)
					end
					gui.Enabled = false
				elseif gui:GetAttribute("VisualReviewHidden") then
					gui.Enabled = true
					gui:SetAttribute("VisualReviewHidden", nil)
				end
				local edge = gui:FindFirstChild("StudioScreenEdge", true)
				if edge then
					edge.Visible = false
				end
			end
		end
	end)
end

-- Holds the camera at `from` looking at `at`, turned so `at` sits in the middle of the shot's region.
local function hold(from: Vector3, at: Vector3, fov: number?)
	fov = fov or 55
	pcall(function()
		RunService:UnbindFromRenderStep("VisualReviewCamera")
	end)
	RunService:BindToRenderStep("VisualReviewCamera", Enum.RenderPriority.Last.Value, function()
		local vp = camera.ViewportSize
		local region = regionSize()
		local focal = (vp.Y / 2) / math.tan(math.rad(fov) / 2)
		local yaw = -math.atan((vp.X / 2 - region.X / 2) / focal)
		local pitch = math.atan((vp.Y / 2 - region.Y / 2) / focal)
		camera.CameraType = Enum.CameraType.Scriptable
		camera.FieldOfView = fov
		camera.CFrame = CFrame.lookAt(from, at) * CFrame.Angles(pitch, yaw, 0)
	end)
end

-- Follows the character: offset in the root's space, looking at a point in the root's space.
local function follow(offset: Vector3, lookOffset: Vector3, fov: number?)
	fov = fov or 50
	pcall(function()
		RunService:UnbindFromRenderStep("VisualReviewCamera")
	end)
	RunService:BindToRenderStep("VisualReviewCamera", Enum.RenderPriority.Last.Value, function()
		local r = root()
		if not r then
			return
		end
		local vp = camera.ViewportSize
		local region = regionSize()
		local focal = (vp.Y / 2) / math.tan(math.rad(fov) / 2)
		local yaw = -math.atan((vp.X / 2 - region.X / 2) / focal)
		local pitch = math.atan((vp.Y / 2 - region.Y / 2) / focal)
		local base = CFrame.new(r.Position) * CFrame.Angles(0, select(2, r.CFrame:ToOrientation()), 0)
		camera.CameraType = Enum.CameraType.Scriptable
		camera.FieldOfView = fov
		camera.CFrame = CFrame.lookAt(base:PointToWorldSpace(offset), base:PointToWorldSpace(lookOffset)) * CFrame.Angles(pitch, yaw, 0)
	end)
end

local function freeCamera()
	pcall(function()
		RunService:UnbindFromRenderStep("VisualReviewCamera")
	end)
	camera.CameraType = Enum.CameraType.Custom
end

-- Stands the character somewhere, facing a point (it stays: the character is anchored by the root).
local function standAt(position: Vector3, facing: Vector3)
	local r = root()
	if r then
		r.Anchored = false
		r.CFrame = CFrame.lookAt(position, Vector3.new(facing.X, position.Y, facing.Z))
		r.AssemblyLinearVelocity = Vector3.zero
		task.wait(0.3)
		r.Anchored = true
	end
end
local function release()
	local r = root()
	if r then
		r.Anchored = false
	end
end

local function home()
	release()
	ReplicatedStorage.GoHome:FireServer()
	task.wait(1.5)
end

-- The UI shots' background: the player's own plot from behind the tapping spot, as in play.
local function uiCamera()
	hold(MapConfig.PlotPoint(me:GetAttribute("PlotIndex") or 1, 6, 46, 15), MapConfig.PlotPoint(me:GetAttribute("PlotIndex") or 1, 0, 2, 5), 60)
end

local function progress()
	local ok, data = pcall(HttpService.JSONDecode, HttpService, me:GetAttribute("Progress") or "")
	return if ok and type(data) == "table" then data else {}
end

local function pets(): { any }
	return progress().Pets or {}
end

-- Equips exactly these pet uids (in order).
local function equipOnly(uids: { string })
	local data = progress()
	for _, uid in data.Equipped or {} do
		ReplicatedStorage.PetRequest:InvokeServer("Unequip", uid)
		task.wait(0.2)
	end
	for _, uid in uids do
		ReplicatedStorage.PetRequest:InvokeServer("Equip", uid)
		task.wait(0.2)
	end
end

local function petOf(creatureId: string, golden: boolean)
	for _, pet in pets() do
		if pet.CreatureId == creatureId and (pet.Golden == true) == golden then
			return pet
		end
	end
	dbg("GivePet", { Creature = creatureId, Golden = if golden then "On" else "Off" })
	task.wait(0.6)
	for _, pet in pets() do
		if pet.CreatureId == creatureId and (pet.Golden == true) == golden then
			return pet
		end
	end
	return nil
end

local function guiPath(relative: string): string
	return `game.Players.{me.Name}.PlayerGui.{relative}`
end
local function menu(name: string): string
	return guiPath(`HUD.Root.Menu.Grid.{name}Button`)
end
local function closeOf(window: string): string
	return guiPath(`{window}Window.Root.Panel.Close`)
end
-- The tab buttons of a window, as paths (UIKit.Tabs names them "<Id>Tab").
local function tabsOf(window: string): { string }
	local list = {}
	local gui = me.PlayerGui:FindFirstChild(window .. "Window")
	local strip = gui and gui:FindFirstChild("Tabs", true)
	if strip then
		local buttons = {}
		for _, b in strip:GetChildren() do
			if b:IsA("GuiButton") and string.sub(b.Name, -3) == "Tab" then
				table.insert(buttons, b)
			end
		end
		table.sort(buttons, function(a, b)
			return a.LayoutOrder < b.LayoutOrder
		end)
		for _, b in buttons do
			table.insert(list, (string.gsub(b:GetFullName(), "^Players%.", "game.Players.")))
		end
	end
	return list
end

-- Every window that is open now, as close-button paths (the helper clicks them before a shot).
local function openWindows(): { string }
	local list = {}
	for _, gui in me.PlayerGui:GetChildren() do
		if gui:IsA("ScreenGui") and string.sub(gui.Name, -6) == "Window" and gui.Enabled then
			local panel = gui:FindFirstChild("Root") and gui.Root:FindFirstChild("Panel")
			local close = panel and panel:FindFirstChild("Close")
			if panel and panel.Visible and close then
				table.insert(list, guiPath(`{gui.Name}.Root.Panel.Close`))
			end
		end
	end
	return list
end

-- The spot in front of a building's pad, looking at it.
local function padShot(buildingId: string, zoom: number?)
	local pad = BuildingConfig.Get(buildingId).Pad
	local center = plotPoint(pad.X, pad.Z, 0)
	local plotCenter = plotPoint(0, 0, 0)
	local out = Vector3.new(center.X - plotCenter.X, 0, center.Z - plotCenter.Z)
	out = if out.Magnitude > 0 then out.Unit else Vector3.zAxis
	local size = pad.Size * (zoom or 1.25)
	-- from the plot's middle side of the pad (stations face the ice), a little to the side
	local side = out:Cross(Vector3.yAxis)
	local from = center - out * (size * 2.4 + 8) + side * size * 0.6 + Vector3.new(0, size * 1.3 + 6, 0)
	hold(from, center + Vector3.new(0, size * 0.75, 0), 55)
end

local function rarityCreature(rarity: string): string
	for _, creature in CreatureConfig.Creatures do
		if creature.Rarity == rarity then
			return creature.Id
		end
	end
	return CreatureConfig.Creatures[1].Id
end

local function blockShot(close: boolean?)
	if close then
		hold(plotPoint(12, 30, 11), plotPoint(0, 0, 6), 50)
	else
		hold(plotPoint(14, 34, 14), plotPoint(0, 0, 6), 55)
	end
end

local function freshBlock(level: number, creatureId: string)
	dbg("SetBlockLevel", { Level = level })
	task.wait(0.5)
	dbg("PickCreature", { Creature = creatureId })
	waitFor(function()
		local plot = workspace.Plots:FindFirstChild("Plot" .. plotIndex())
		return plot ~= nil and plot.Block:GetAttribute("CreatureId") == creatureId and plot.Block:GetAttribute("Present") == true
	end, 8)
end

local function plazaThing(name: string): BasePart?
	local plaza = workspace:FindFirstChild("Plaza")
	local found = plaza and plaza:FindFirstChild(name, true)
	if found and found:IsA("Model") then
		return found.PrimaryPart or found:FindFirstChildWhichIsA("BasePart", true)
	end
	return found
end

-- A shot of a plaza object from the plaza's middle side.
local function plazaShot(name: string, distance: number, height: number, lift: number?)
	local part = plazaThing(name)
	if not part then
		warn("[VisualReview] no plaza part " .. name)
		return
	end
	local pos = part.Position
	local inward = Vector3.new(-pos.X, 0, -pos.Z)
	inward = if inward.Magnitude > 0 then inward.Unit else Vector3.zAxis
	standAt(pos + inward * (distance + 6) + Vector3.new(0, 4, 0), pos)
	hold(pos + inward * distance + Vector3.new(0, height, 0), pos + Vector3.new(0, lift or 3, 0), 55)
end

-- Only these buildings on the plot (every other one set to 0), so a shot shows one station on its own.
local function onlyBuildings(keep: { [string]: boolean })
	local owned = progress().Buildings or {}
	for _, building in BuildingConfig.Buildings do
		if not keep[building.Id] and (owned[building.Id] or 0) > 0 then
			dbg("SetBuilding", { Building = building.Id, Count = 0, Upgrades = 0 })
		end
	end
end

local LAYER_LEVELS = { 5, 15, 25, 35, 45, 55 }
local RARITIES = { "Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic" }
local PHONES = { "desktop", "844x390", "667x375" }
local WINDOWS = { "Build", "Upgrades", "Pets", "Book", "Rebirth", "Shop", "Codes" }

-- The shots ---------------------------------------------------------------------------------------

local SHOTS = {}
local TIER_ZOOM = { 0.8, 0.95, 1.1, 1.3, 1.6 } -- (bigger tiers need the camera further back)
local function shot(name: string, run, sizes)
	table.insert(SHOTS, { Name = name, Run = run, Sizes = sizes or { "desktop" } })
end

-- Starting states per category.
local PREPARE = {
	buildings = function()
		dbg("ResetSave")
		task.wait(3)
		dbg("SetBlockLevel", { Level = 400 })
		home()
	end,
	picks = function()
		dbg("ResetSave") -- (no Golden page yet, so the tiers show their own look; the golden skin is last)
		task.wait(3)
		dbg("SetBlockLevel", { Level = 400 }) -- (no rescue banners: the developer's Auto Pick taps in the plot)
		home()
	end,
	ice = function()
		dbg("SetRebirths", { Rebirths = 3 }) -- layer 6 open
		home()
	end,
	pets = function()
		dbg("SetRebirths", { Rebirths = 10 }) -- every rank slot
		home()
	end,
	rescue = function()
		dbg("SetBuilding", { Building = "HeatLamp", Count = 25, Upgrades = 2 }) -- (some income, so the burst isn't +0)
		-- every creature seen once, so a rescue isn't "new" (a new one opens the Book); new_badge is the exception
		for _, creature in CreatureConfig.Creatures do
			petOf(creature.Id, false)
		end
		home()
	end,
	world = function()
		home()
	end,
	ui = function()
		-- a calm screen: no rescues (no buildings, high block level), no creature new (a new one opens the Book)
		onlyBuildings({})
		dbg("SetBlockLevel", { Level = 400 })
		for _, creature in CreatureConfig.Creatures do
			petOf(creature.Id, false)
		end
		home()
	end,
	effects = function()
		onlyBuildings({})
		dbg("SetBlockLevel", { Level = 400 })
		for _, creature in CreatureConfig.Creatures do
			petOf(creature.Id, false)
		end
		task.wait(3)
		home()
	end,
}

-- Buildings: every tier, Masterwork, each upgrade at 100 owned, the fence ring, the build moments.
for _, building in BuildingConfig.Buildings do
	local id = building.Id
	for tier, owned in BuildingConfig.StationMilestones do
		shot(`buildings/{id}_T{tier}`, function()
			onlyBuildings({ [id] = true })
			dbg("SetBuilding", { Building = id, Count = owned, Upgrades = 0 })
			padShot(id, TIER_ZOOM[tier])
			return { Wait = 3 }
		end)
	end
	for upgrades = 1, 4 do
		shot(`buildings/{id}_T5_U{upgrades}`, function()
			dbg("SetBuilding", { Building = id, Count = 100, Upgrades = upgrades })
			padShot(id, TIER_ZOOM[5])
			return { Wait = 3 }
		end)
	end
	shot(`buildings/{id}_Masterwork`, function()
		dbg("SetBuilding", { Building = id, Count = 100, Upgrades = 5 })
		padShot(id, TIER_ZOOM[5])
		return { Wait = 3 }
	end)
	shot(`buildings/{id}_Masterwork_close`, function()
		dbg("SetBuilding", { Building = id, Count = 100, Upgrades = 5 })
		padShot(id, 1.0)
		return { Wait = 3 }
	end)
end
shot("buildings/fence_ring", function()
	-- a faded Ice Pick Post becomes the fence once the next building up is owned
	onlyBuildings({ IcePickPost = true, HeatLamp = true })
	dbg("SetBuilding", { Building = "IcePickPost", Count = 100, Upgrades = 5 })
	dbg("SetBuilding", { Building = "HeatLamp", Count = 10, Upgrades = 0 })
	hold(plotPoint(-46, 64, 46), plotPoint(0, 0, 2), 60)
	return { Wait = 3 }
end)
shot("buildings/overview_all_masterwork", function()
	for _, building in BuildingConfig.Buildings do
		dbg("SetBuilding", { Building = building.Id, Count = 100, Upgrades = 5 })
	end
	hold(plotPoint(-30, 75, 55), plotPoint(0, -5, 4), 60)
	return { Wait = 4 }
end)
shot("buildings/moment_rise", function()
	onlyBuildings({})
	dbg("AddCrystals", { Amount = 1e6 })
	padShot("HeatLamp")
	task.wait(1.5)
	ReplicatedStorage.BuyBuilding:InvokeServer("HeatLamp", 1)
	return { Wait = 0.5 }
end)
shot("buildings/moment_evolved", function()
	onlyBuildings({ ChiselMill = true })
	dbg("SetBuilding", { Building = "ChiselMill", Count = 9, Upgrades = 0 })
	dbg("AddCrystals", { Amount = 1e7 })
	padShot("ChiselMill")
	task.wait(1.5)
	ReplicatedStorage.BuyBuilding:InvokeServer("ChiselMill", 1)
	return { Wait = 0.35 }
end)

-- Picks: each tier in the hand, and the golden skin.
for tier = 1, 6 do
	shot(`picks/pick_tier{tier}`, function()
		dbg("SetPickTier", { Tier = tier })
		task.wait(1)
		standAt(plotPoint(0, 26, 4), plotPoint(0, 0, 4))
		follow(Vector3.new(4.6, 3.0, -6.8), Vector3.new(0.9, 2.4, -0.2), 42)
		return { Wait = 1.5 }
	end)
end
shot("picks/pick_golden_skin", function()
	-- the Creature Book's Golden page: every creature Golden
	for _, creature in CreatureConfig.Creatures do
		petOf(creature.Id, true)
	end
	dbg("SetPickTier", { Tier = 6 })
	dbg("Respawn")
	task.wait(4)
	standAt(plotPoint(0, 26, 4), plotPoint(0, 0, 4))
	follow(Vector3.new(4.6, 3.0, -6.8), Vector3.new(0.9, 2.4, -0.2), 42)
	return { Wait = 1.5 }
end)

-- Ice: every layer with every rarity, the crack stages, the shatter, the sled, the Mythic Block.
for layer, level in LAYER_LEVELS do
	for _, rarity in RARITIES do
		shot(`ice/layer{layer}_{rarity}`, function()
			freshBlock(level, rarityCreature(rarity))
			blockShot(true)
			return { Wait = 2 }
		end)
	end
end
for stage, percent in { 100, 79, 59, 39, 19 } do
	shot(`ice/crack_stage{stage - 1}`, function()
		freshBlock(15, "GlacierOtter")
		dbg("SetBlockHp", { Percent = percent })
		blockShot(true)
		return { Wait = 1.5 }
	end)
end
shot("ice/shatter", function()
	freshBlock(15, "GlacierOtter")
	blockShot(false)
	task.wait(1)
	dbg("ForceRescue")
	return { Wait = 0.25 }
end)
shot("ice/sled_arrival", function()
	freshBlock(15, "GlacierOtter")
	blockShot(false)
	task.wait(1)
	dbg("ForceRescue")
	return { Wait = 2.6 }
end)
shot("ice/mythic_block", function()
	freshBlock(15, "SnowBunny")
	dbg("SimulateReceipt", { Product = "MythicBlock", GiftTo = 0 })
	task.wait(0.5)
	dbg("ForceRescue")
	blockShot(true)
	return { Wait = 5 }
end)

-- Pets: each creature following, Golden too, the slot layouts, the aurora trail.
for _, creature in CreatureConfig.Creatures do
	for _, golden in { false, true } do
		shot(`pets/{creature.Id}{if golden then "_golden" else ""}`, function()
			local pet = petOf(creature.Id, golden)
			if pet then
				equipOnly({ pet.Uid })
			end
			standAt(plotPoint(0, 30, 4), plotPoint(0, 60, 4))
			-- a close-up of the pet itself (its model is Workspace.ClientEffects.Pet_<player>_<creature>)
			local model
			waitFor(function()
				local folder = workspace:FindFirstChild("ClientEffects")
				model = folder and folder:FindFirstChild(`Pet_{me.Name}_{creature.Id}`)
				return model ~= nil
			end, 6)
			task.wait(2)
			local r = root()
			if model and r then
				local at = model:GetPivot().Position
				local size = model:GetExtentsSize().Magnitude
				-- pets face the way the player faces: film the face from the front, on the pet's own side, so
				-- the character isn't in between
				local right = r.CFrame.RightVector
				local side = if (at - r.Position):Dot(right) < 0 then -right else right
				local dir = (side + r.CFrame.LookVector * 0.55).Unit
				hold(at + dir * (size * 1.7 + 2) + Vector3.new(0, size * 0.45, 0), at + Vector3.new(0, size * 0.1, 0), 40)
			else
				follow(Vector3.new(-7, 4, -9), Vector3.new(0, 1, 4), 45)
			end
			return { Wait = 1.5 }
		end)
	end
end
for count = 1, 7 do
	shot(`pets/slots_{count}`, function()
		local uids = {}
		for index = 1, count do
			local creature = CreatureConfig.Creatures[index * 2]
			local pet = petOf(creature.Id, false)
			if pet then
				table.insert(uids, pet.Uid)
			end
		end
		equipOnly(uids)
		standAt(plotPoint(0, 30, 4), plotPoint(0, 60, 4))
		follow(Vector3.new(-9, 10, -12), Vector3.new(0, 0, 5), 50)
		return { Wait = 3 }
	end)
end
shot("pets/aurora_trail", function()
	for _, creature in CreatureConfig.Creatures do
		if creature.Rarity == "Mythic" then
			petOf(creature.Id, false)
		end
	end
	dbg("Respawn")
	task.wait(4)
	release()
	local r = root()
	local hum = me.Character and me.Character:FindFirstChildOfClass("Humanoid")
	if r and hum then
		hum:MoveTo(r.Position + r.CFrame.LookVector * 40)
	end
	follow(Vector3.new(-8, 5, 6), Vector3.new(0, 1, 3), 50)
	return { Wait = 1.2 }
end)

-- Rescue moments: each rarity's banner and confetti, the NEW badge, the server announcement.
for _, rarity in RARITIES do
	shot(`rescue/{rarity}`, function()
		freshBlock(15, rarityCreature(rarity))
		blockShot(false)
		task.wait(1)
		dbg("ForceRescue")
		return { Wait = 0.7 }
	end)
end
shot("rescue/server_announcement", function()
	freshBlock(45, "SpiritWhale")
	blockShot(false)
	return { Wait = 0.8 }
end)
shot("rescue/new_badge", function()
	dbg("ResetSave")
	task.wait(3)
	home()
	freshBlock(3, "SnowBunny")
	blockShot(false)
	task.wait(1)
	dbg("ForceRescue")
	return { Wait = 1.6, Close = { closeOf("Book") }, After = 3 } -- (a new creature opens the Book a moment later)
end)

-- World: the plot parts, the plaza, the Golden Glacier, the terrain and the overall views.
shot("world/plot_gate_and_name_boards", function()
	staging.hud = false
	hold(plotPoint(10, 92, 16), plotPoint(0, 50, 9), 55)
	return { Wait = 2 }
end)
shot("world/plot_walls_and_stage", function()
	staging.hud = false
	hold(plotPoint(-72, 78, 40), plotPoint(-10, 0, 2), 60)
	return { Wait = 2 }
end)
shot("world/plot_ice_stage", function()
	staging.hud = false
	hold(plotPoint(20, 30, 8), plotPoint(0, 0, 2), 55)
	return { Wait = 2 }
end)
for _, rebirths in { 1, 2, 3, 6, 10 } do
	shot(`world/rank_trim_{rebirths}_rebirths`, function()
		staging.hud = false
		dbg("SetRebirths", { Rebirths = rebirths })
		dbg("Respawn")
		task.wait(4)
		hold(plotPoint(16, 80, 14), plotPoint(0, 50, 7), 50)
		return { Wait = 2 }
	end)
end
shot("world/plaza_leaderboards", function()
	standAt(Vector3.new(6, 6, 6), Vector3.new(-20, 6, -40))
	hold(Vector3.new(14, 24, 14), Vector3.new(-18, 10, -42), 70)
	return { Wait = 3 }
end)
for _, board in { "BoardCrystals", "BoardRebirths", "BoardRescued" } do
	shot(`world/plaza_{string.lower(board)}`, function()
		plazaShot(board, 30, 6, 12)
		return { Wait = 3 }
	end)
end
shot("world/plaza_daily_chest", function()
	staging.hud = false
	plazaShot("DailyChest", 18, 7, 3)
	return { Wait = 3 }
end)
shot("world/plaza_codes_kiosk", function()
	staging.hud = false
	plazaShot("CodesBoard", 22, 8, 6)
	return { Wait = 3 }
end)
shot("world/plaza_vip_lounge", function()
	staging.hud = false
	plazaShot("VipFloor", 30, 14, 3)
	return { Wait = 3 }
end)
shot("world/home_beacon", function()
	staging.hud = false
	standAt(Vector3.new(0, 6, 0), plotPoint(0, 0, 0))
	local target = plotPoint(0, 0, 40)
	hold(Vector3.new(0, 18, 0) - (target - Vector3.new(0, 18, 0)).Unit * 20, target, 55)
	return { Wait = 3 }
end)
for stage, hpShare in { 1, 0.7, 0.5, 0.3, 0.1 } do
	shot(`world/golden_glacier_stage{stage - 1}`, function()
		staging.hud = false
		local state = workspace:FindFirstChild("GoldenGlacier")
		if state and state:GetAttribute("State") == "Idle" then
			dbg("SpawnGolden")
		end
		waitFor(function()
			return state ~= nil and state:GetAttribute("State") == "Active"
		end, 20)
		-- (the helper sets the glacier's HP on the server: it reads GlacierHpShare from the shot)
		local spot = state and state:GetAttribute("Spot") or Vector3.zero
		standAt(spot + Vector3.new(0, 4, 30), spot)
		hold(spot + Vector3.new(9, 9, 20), spot + Vector3.new(0, 5, 0), 50)
		return { Wait = 1.5, GlacierHpShare = hpShare }
	end)
end
shot("world/terrain_pines_sky", function()
	staging.hud = false
	hold(Vector3.new(120, 80, 260), Vector3.new(0, 20, 0), 70)
	return { Wait = 4 }
end)
shot("world/overview_plaza", function()
	staging.hud = false
	standAt(Vector3.new(0, 6, 30), Vector3.zero)
	hold(Vector3.new(0, 55, 95), Vector3.new(0, 4, 0), 65)
	return { Wait = 4 }
end)
shot("world/overview_ring", function()
	staging.hud = false
	hold(Vector3.new(0, 260, 330), Vector3.new(0, 0, 0), 60)
	return { Wait = 5 }
end)
shot("world/overview_tapping_spot", function()
	home()
	follow(Vector3.new(4, 7, 12), Vector3.new(0, 3, -16), 60)
	return { Wait = 3 }
end)

-- UI: the HUD, every window and tab (desktop and both phone sizes), popups and moments.
shot("ui/hud", function()
	home()
	uiCamera()
	return { Wait = 2 }
end, PHONES)
shot("ui/hud_rebirth_goal", function()
	dbg("SetBlockLevel", { Level = 27 })
	home()
	uiCamera()
	return { Wait = 2 }
end, PHONES)
for _, window in WINDOWS do
	shot(`ui/window_{string.lower(window)}`, function()
		home()
		uiCamera()
		return { Clicks = { menu(window) }, Close = { closeOf(window) }, Wait = 1.5, Tabs = window }
	end, PHONES)
end
shot("ui/window_settings", function()
	home()
	uiCamera()
	return { Clicks = { guiPath("HUD.Root.SettingsButton") }, Close = { closeOf("Settings") }, Wait = 1.5 }
end, PHONES)
shot("ui/offline_earnings_popup", function()
	home()
	uiCamera()
	dbg("SetBuilding", { Building = "HeatLamp", Count = 25, Upgrades = 2 }) -- (income to earn while away)
	dbg("OfflineEarningsNow", { Seconds = 5400 })
	return { Wait = 1.5, Close = { closeOf("OfflineEarnings") } }
end, PHONES)
shot("ui/shatter_offer_normal", function()
	freshBlock(15, "SnowBunny")
	uiCamera()
	return { Wait = 3.5 } -- (the new-layer banner passes first)
end, PHONES)
shot("ui/shatter_offer_rare", function()
	freshBlock(15, "AuroraFox")
	uiCamera()
	return { Wait = 1.5 }
end, PHONES)
shot("ui/golden_glacier_tap_bar", function()
	local state = workspace:FindFirstChild("GoldenGlacier")
	if state and state:GetAttribute("State") == "Idle" then
		dbg("SpawnGolden")
	end
	waitFor(function()
		return state ~= nil and state:GetAttribute("State") == "Active"
	end, 20)
	local spot = state and state:GetAttribute("Spot") or Vector3.zero
	standAt(spot + Vector3.new(0, 4, 22), spot)
	hold(spot + Vector3.new(5, 11, 40), spot + Vector3.new(0, 5, 0), 60)
	return { Wait = 1.5 }
end, PHONES)


shot("ui/toast_notice", function()
	home()
	uiCamera()
	ReplicatedStorage.RedeemCode:InvokeServer("NOTACODE")
	dbg("SimulateReceipt", { Product = "CrystalPouch", GiftTo = 0 })
	return { Wait = 0.8 }
end, PHONES)
shot("ui/server_frost_rush", function()
	home()
	uiCamera()
	dbg("SimulateReceipt", { Product = "ServerFrostRush", GiftTo = 0 })
	return { Wait = 1 }
end, PHONES)
shot("ui/update_screen", function()
	home()
	uiCamera()
	dbg("PreviewUpdateScreen")
	return { Wait = 1.2 }
end, PHONES)




shot("ui/rebirth_frost_over", function()
	dbg("SetBlockLevel", { Level = 31 })
	home()
	uiCamera()
	task.wait(1)
	ReplicatedStorage.RebirthRequest:InvokeServer("Rebirth")
	return { Wait = 0.6 }
end, PHONES)

shot("ui/tutorial_pointer_step1", function()
	staging.tutorial = true
	dbg("ResetSave")
	task.wait(3)
	home()
	uiCamera()
	return { Wait = 5 } -- (banners from earlier shots finish first)
end, PHONES)

shot("ui/server_message", function()
	home()
	uiCamera()
	dbg("PreviewRestartWarning")
	return { Wait = 1.2 }
end, PHONES)

-- Effects: tapping, crystals flying, the rushes, reduced effects on and off.
shot("effects/tap_feedback", function()
	freshBlock(400, "SnowBunny")
	follow(Vector3.new(4, 6, 10), Vector3.new(0, 3, -14), 55)
	for _ = 1, 6 do
		ReplicatedStorage.TapBatch:FireServer(1)
		task.wait(0.12)
	end
	return { Wait = 0.1, TapWhileShooting = true }
end)
shot("effects/crystals_flying", function()
	freshBlock(15, "GlacierOtter")
	blockShot(false)
	task.wait(3) -- (the new-layer banner passes first)
	dbg("ForceRescue")
	return { Wait = 1.1 }
end)
shot("effects/server_frost_rush", function()
	home()
	uiCamera()
	dbg("SimulateReceipt", { Product = "ServerFrostRush", GiftTo = 0 })
	return { Wait = 2.5 }
end)
for _, reduced in { false, true } do
	shot(`effects/reduced_effects_{if reduced then "on" else "off"}`, function()
		staging.hud, staging.banners = false, false -- (the world's effects only)
		ReplicatedStorage.SaveSettings:FireServer({ ReducedEffects = reduced })
		for _, building in BuildingConfig.Buildings do
			dbg("SetBuilding", { Building = building.Id, Count = 100, Upgrades = 5 })
		end
		hold(plotPoint(-30, 75, 55), plotPoint(0, -5, 4), 60)
		return { Wait = 3 }
	end)
end

-- Running --------------------------------------------------------------------------------------------

if SHOT == "?list" then
	local list = {}
	for _, entry in SHOTS do
		table.insert(list, { Name = entry.Name, Sizes = entry.Sizes })
	end
	return HttpService:JSONEncode(list)
elseif string.sub(SHOT, 1, 9) == "?prepare:" then
	local category = string.sub(SHOT, 10)
	-- the developer owns Auto Pick, which would tap the block between setup and screenshot
	dbg("RemovePass", { Pass = "AutoPick" })
	if PREPARE[category] then
		PREPARE[category]()
	end
	return "prepared " .. category
elseif SHOT == "?cleanup" then
	ReplicatedStorage.SaveSettings:FireServer({ ReducedEffects = false }) -- (the effects shots turn it on)
	for _, name in { "VisualReviewCamera", "VisualReviewStage" } do
		pcall(function()
			RunService:UnbindFromRenderStep(name)
		end)
	end
	release()
	camera.CameraType = Enum.CameraType.Custom
	workspace:SetAttribute("StudioScreenSize", nil)
	for _, gui in me.PlayerGui:GetChildren() do
		if gui:IsA("ScreenGui") and (gui:GetAttribute("VisualReviewHidden") or gui.Name == "HUD" or string.find(gui.Name, "Debug") or string.find(gui.Name, "Admin") or string.find(gui.Name, "Tutorial")) then
			gui.Enabled = true
			gui:SetAttribute("VisualReviewHidden", nil)
		end
	end
	return "cleaned up"
end

for _, entry in SHOTS do
	if entry.Name == SHOT then
		-- model shots hide the HUD; UI, rescue moments and effects keep it
		local category = string.split(SHOT, "/")[1]
		staging.hud = not (category == "buildings" or category == "picks" or category == "ice" or category == "pets" or category == "world")
		staging.tutorial = false
		-- the big moments only where they're the subject (building moments, rescues, UI, effects)
		staging.banners = not (category == "picks" or category == "ice" or category == "pets" or category == "world")
		stage()
		local preClose = openWindows()
		local result = entry.Run() or {}
		result.PreClose = preClose
		stage() -- (a shot may have changed what's hidden)
		local vp = camera.ViewportSize
		local region = regionSize()
		result.Viewport = { vp.X, vp.Y }
		result.Region = { region.X, region.Y }
		if result.Tabs then
			result.TabPaths = tabsOf(result.Tabs)
		end
		return HttpService:JSONEncode(result)
	end
end
return HttpService:JSONEncode({ Error = "no shot named " .. SHOT })
