-- A plain tool window built from a server catalogue of actions: the debug menu (F2) and the admin
-- window (F3) are both made with it. Each action is a card with its inputs and a RUN button; a
-- target picker at the top chooses the player actions apply to. The server checks everything on
-- every request (DebugRules / AdminRules), so this UI decides nothing.
--
-- ActionMenu.Build({
--	guiName, title, remoteName,       -- the ScreenGui's name, the window title, the RemoteFunction
--	toggleKey (optional), buttonName, buttonText, buttonColor, buttonY (0-1 down the right edge), accent,
--	displayOrder, noAccessText,
--	side = "Left" (optional: the button at buttonPosition and the window on the left instead),
--	buttonPosition, buttonSize (optional, with side = "Left"),
-- }) -> { gui, Destroy() }
-- The remote answers ("Catalog") with the action list, and ("Run", { Action, Target, Args,
-- Confirmed }) with { ok, message }.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local localPlayer = Players.LocalPlayer

local FONT = Enum.Font.BuilderSansBold
local BG = Color3.fromRGB(22, 24, 32)
local CARD = Color3.fromRGB(38, 42, 56)
local FIELD = Color3.fromRGB(58, 64, 82)
local GOOD = Color3.fromRGB(130, 230, 120)
local BAD = Color3.fromRGB(255, 110, 110)
local TEXT = Color3.fromRGB(235, 238, 245)
local MUTED = Color3.fromRGB(160, 168, 190)
local CONFIRM_SECONDS = 4

local ActionMenu = {}

-- Every menu built on this client (the debug menu and the admin window share this module). The
-- right-edge toggle buttons slide left of whichever right-side window is open, so a button never
-- sits on top of an open window; on a screen too narrow for that, they hide until it closes.
local EDGE_MARGIN = 8
local BUTTON_WIDTH = 64
local menus = {}

local function placeEdgeButtons()
	local openWidth = nil
	for _, menu in menus do
		if not menu.left and menu.panel.Visible then
			openWidth = math.max(openWidth or 0, menu.panel.Size.X.Offset) -- (layout() sizes it in pixels)
		end
	end
	local camera = Workspace.CurrentCamera
	local viewportWidth = if camera then camera.ViewportSize.X else 1280
	for _, menu in menus do
		if not menu.left then
			local shift = if openWidth then openWidth + EDGE_MARGIN else 0
			local fits = viewportWidth - EDGE_MARGIN - shift - BUTTON_WIDTH >= 0
			menu.toggleButton.Visible = fits
			menu.toggleButton.Position = UDim2.new(1, -EDGE_MARGIN - shift, menu.buttonY, 0)
		end
	end
end

function ActionMenu.Build(options)
	local TOGGLE_KEY = options.toggleKey
	local ACCENT = options.accent
	local remote = ReplicatedStorage:WaitForChild(options.remoteName) :: RemoteFunction

	local function corner(parent: Instance, radius: number?)
		local c = Instance.new("UICorner")
		c.CornerRadius = UDim.new(0, radius or 6)
		c.Parent = parent
	end

	local function text(class: string, props): any
		local item = Instance.new(class)
		item.BackgroundTransparency = 1
		item.Font = FONT
		item.TextColor3 = TEXT
		item.TextSize = 16
		item.TextXAlignment = Enum.TextXAlignment.Left
		item.TextTruncate = Enum.TextTruncate.AtEnd
		for key, value in props do
			item[key] = value
		end
		return item
	end

	local function button(label: string, color: Color3, parent: Instance): TextButton
		local b = text("TextButton", { Text = label, BackgroundTransparency = 0, BackgroundColor3 = color, TextXAlignment = Enum.TextXAlignment.Center, AutoButtonColor = true, Parent = parent })
		corner(b)
		return b
	end

	local gui = Instance.new("ScreenGui")
	gui.Name = options.guiName
	gui.ResetOnSpawn = false
	gui.DisplayOrder = options.displayOrder or 30
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = localPlayer:WaitForChild("PlayerGui")

	-- The small toggle button on the right edge (for touch screens; the toggle key on a keyboard).
	local toggleButton = button(options.buttonText, options.buttonColor, gui)
	toggleButton.Name = options.buttonName
	local left = options.side == "Left"
	if left then
		toggleButton.AnchorPoint = Vector2.new(0, 0)
		toggleButton.Position = options.buttonPosition or UDim2.fromOffset(8, 8)
		toggleButton.Size = options.buttonSize or UDim2.fromOffset(64, 30)
	else
		toggleButton.AnchorPoint = Vector2.new(1, 0.5)
		toggleButton.Position = UDim2.new(1, -EDGE_MARGIN, options.buttonY, 0)
		toggleButton.Size = UDim2.fromOffset(BUTTON_WIDTH, 30)
	end
	toggleButton.TextSize = 14

	local panel = Instance.new("Frame")
	panel.Name = "Panel"
	panel.AnchorPoint = if left then Vector2.new(0, 0) else Vector2.new(1, 0)
	panel.Position = if left then UDim2.fromOffset(8, 44) else UDim2.new(1, -8, 0, 8)
	panel.BackgroundColor3 = BG
	panel.BackgroundTransparency = 0.05
	panel.Visible = false
	panel.Parent = gui
	corner(panel, 10)

	local title = text("TextLabel", { Text = options.title, TextSize = 20, Position = UDim2.fromOffset(10, 6), Size = UDim2.new(1, -60, 0, 28), Parent = panel })
	title.Name = "Title"
	local closeButton = button("X", BAD, panel)
	closeButton.Name = "Close"
	closeButton.AnchorPoint = Vector2.new(1, 0)
	closeButton.Position = UDim2.new(1, -8, 0, 6)
	closeButton.Size = UDim2.fromOffset(32, 28)

	text("TextLabel", { Text = "Target:", TextColor3 = MUTED, Position = UDim2.fromOffset(10, 42), Size = UDim2.fromOffset(60, 30), Parent = panel })
	local targetButton = button("", FIELD, panel)
	targetButton.Name = "TargetButton"
	targetButton.Position = UDim2.fromOffset(70, 42)
	targetButton.Size = UDim2.new(1, -80, 0, 30)

	local result = text("TextLabel", { Name = "Result", Text = "Pick an action.", TextColor3 = MUTED, TextWrapped = true, TextTruncate = Enum.TextTruncate.None, TextYAlignment = Enum.TextYAlignment.Top, Position = UDim2.fromOffset(10, 78), Size = UDim2.new(1, -20, 0, 40), Parent = panel })

	local list = Instance.new("ScrollingFrame")
	list.Name = "Actions"
	list.Position = UDim2.fromOffset(6, 122)
	list.Size = UDim2.new(1, -12, 1, -128)
	list.BackgroundTransparency = 1
	list.BorderSizePixel = 0
	list.ScrollBarThickness = 6
	list.AutomaticCanvasSize = Enum.AutomaticSize.Y
	list.CanvasSize = UDim2.new()
	list.Parent = panel
	local listLayout = Instance.new("UIListLayout")
	listLayout.Padding = UDim.new(0, 6)
	listLayout.SortOrder = Enum.SortOrder.LayoutOrder
	listLayout.Parent = list

	-- A pop-up list for choosing a player or an option, over the action list.
	local picker = Instance.new("Frame")
	picker.Name = "Picker"
	picker.Position = list.Position
	picker.Size = list.Size
	picker.BackgroundColor3 = BG
	picker.Visible = false
	picker.ZIndex = 5
	picker.Parent = panel
	local pickerTitle = text("TextLabel", { Text = "", TextColor3 = MUTED, Position = UDim2.fromOffset(4, 0), Size = UDim2.new(1, -90, 0, 30), ZIndex = 5, Parent = picker })
	local pickerCancel = button("Cancel", FIELD, picker)
	pickerCancel.AnchorPoint = Vector2.new(1, 0)
	pickerCancel.Position = UDim2.new(1, -4, 0, 0)
	pickerCancel.Size = UDim2.fromOffset(80, 28)
	pickerCancel.ZIndex = 5
	local pickerList = Instance.new("ScrollingFrame")
	pickerList.Position = UDim2.fromOffset(0, 34)
	pickerList.Size = UDim2.new(1, 0, 1, -34)
	pickerList.BackgroundTransparency = 1
	pickerList.BorderSizePixel = 0
	pickerList.ScrollBarThickness = 6
	pickerList.AutomaticCanvasSize = Enum.AutomaticSize.Y
	pickerList.CanvasSize = UDim2.new()
	pickerList.ZIndex = 5
	pickerList.Parent = picker
	local pickerLayout = Instance.new("UIListLayout")
	pickerLayout.Padding = UDim.new(0, 4)
	pickerLayout.Parent = pickerList

	local function closePicker()
		picker.Visible = false
	end
	pickerCancel.Activated:Connect(closePicker)

	-- options: { { Value, Label } }
	local function openPicker(heading: string, options, onPick)
		for _, child in pickerList:GetChildren() do
			if child:IsA("GuiObject") then
				child:Destroy()
			end
		end
		pickerTitle.Text = heading
		for _, option in options do
			local b = button(option.Label, CARD, pickerList)
			b.Size = UDim2.new(1, -10, 0, 30)
			b.ZIndex = 5
			b.Activated:Connect(function()
				closePicker()
				onPick(option)
			end)
		end
		pickerList.CanvasPosition = Vector2.zero
		picker.Visible = true
	end

	-- Target -------------------------------------------------------------------------------------
	local target = localPlayer
	local function showTarget()
		targetButton.Text = target.Name .. (if target == localPlayer then " (you)" else "") .. "  v"
	end
	showTarget()
	targetButton.Activated:Connect(function()
		local options = {}
		for _, player in Players:GetPlayers() do
			table.insert(options, { Value = player, Label = player.Name .. (if player == localPlayer then " (you)" else "") })
		end
		openPicker("Target player", options, function(option)
			target = option.Value
			showTarget()
		end)
	end)
	Players.PlayerRemoving:Connect(function(player)
		if player == target then
			target = localPlayer
			showTarget()
		end
	end)

	local function showResult(ok: boolean, message: string)
		result.Text = message
		result.TextColor3 = if ok then GOOD else BAD
	end

	-- Action cards -------------------------------------------------------------------------------
	local busy = false
	local function send(action, args, confirmed: boolean)
		if busy then
			return
		end
		busy = true
		local ok, reply = pcall(function()
			return remote:InvokeServer("Run", { Action = action.Id, Target = target.UserId, Args = args, Confirmed = confirmed })
		end)
		busy = false
		if ok and type(reply) == "table" then
			showResult(reply.ok == true, tostring(reply.message))
		else
			showResult(false, "No reply from the server")
		end
	end

	local function labelFor(param, value): string
		for _, choice in param.Choices do
			if choice.Value == value then
				return choice.Label
			end
		end
		return tostring(value)
	end

	local function addCard(action, order: number)
		local card = Instance.new("Frame")
		card.Name = action.Id
		card.LayoutOrder = order
		card.BackgroundColor3 = CARD
		card.Size = UDim2.new(1, -8, 0, 0)
		card.AutomaticSize = Enum.AutomaticSize.Y
		card.Parent = list
		corner(card)
		local layout = Instance.new("UIListLayout")
		layout.Padding = UDim.new(0, 4)
		layout.SortOrder = Enum.SortOrder.LayoutOrder
		layout.Parent = card
		local padding = Instance.new("UIPadding")
		padding.PaddingTop, padding.PaddingBottom = UDim.new(0, 6), UDim.new(0, 6)
		padding.PaddingLeft, padding.PaddingRight = UDim.new(0, 8), UDim.new(0, 8)
		padding.Parent = card

		text("TextLabel", { Text = action.Label .. (if action.NoTarget then "  (everyone)" else ""), LayoutOrder = 0, Size = UDim2.new(1, 0, 0, 22), Parent = card })

		local readers = {} -- [param name] = function() -> value
		for index, param in action.Params do
			local row = Instance.new("Frame")
			row.BackgroundTransparency = 1
			row.LayoutOrder = index
			row.Size = UDim2.new(1, 0, 0, 30)
			row.Parent = card
			text("TextLabel", { Text = param.Label, TextColor3 = MUTED, TextSize = 14, Size = UDim2.new(0.45, -4, 1, 0), Parent = row })
			if param.Kind == "choice" then
				local value = param.Default or param.Choices[1].Value
				local choose = button(labelFor(param, value) .. "  v", FIELD, row)
				choose.Name = param.Name
				choose.Position = UDim2.fromScale(0.45, 0)
				choose.Size = UDim2.fromScale(0.55, 1)
				choose.Activated:Connect(function()
					openPicker(param.Label, param.Choices, function(option)
						value = option.Value
						choose.Text = option.Label .. "  v"
					end)
				end)
				readers[param.Name] = function()
					return value
				end
			else
				local box = text("TextBox", {
					Name = param.Name,
					BackgroundTransparency = 0,
					BackgroundColor3 = FIELD,
					ClearTextOnFocus = false,
					Text = if param.Kind == "number" and param.Default ~= nil then tostring(param.Default) else "",
					PlaceholderText = if param.Kind == "number" then `{param.Min} - {param.Max}` else "",
					Position = UDim2.fromScale(0.45, 0),
					Size = UDim2.fromScale(0.55, 1),
					Parent = row,
				})
				corner(box)
				readers[param.Name] = function()
					if param.Kind == "number" then
						return tonumber(box.Text)
					end
					return box.Text
				end
			end
		end

		local run = button(if action.Confirm then "RUN (asks first)" else "RUN", ACCENT, card)
		run.Name = "Run"
		run.LayoutOrder = 100
		run.Size = UDim2.new(1, 0, 0, 32)
		local armedUntil = 0
		run.Activated:Connect(function()
			local args = {}
			for name, read in readers do
				args[name] = read()
			end
			if action.Confirm and os.clock() > armedUntil then
				armedUntil = os.clock() + CONFIRM_SECONDS
				run.Text = `SURE? Tap again ({target.Name})`
				run.BackgroundColor3 = BAD
				task.delay(CONFIRM_SECONDS, function()
					if os.clock() >= armedUntil then
						run.Text = "RUN (asks first)"
						run.BackgroundColor3 = ACCENT
					end
				end)
				return
			end
			local confirmed = action.Confirm and os.clock() <= armedUntil
			armedUntil = 0
			run.Text = if action.Confirm then "RUN (asks first)" else "RUN"
			run.BackgroundColor3 = ACCENT
			send(action, args, confirmed)
		end)
	end

	local loaded = false
	local function loadCatalog()
		local ok, catalog = pcall(function()
			return remote:InvokeServer("Catalog")
		end)
		if not ok or type(catalog) ~= "table" then
			showResult(false, options.noAccessText or "No access")
			return
		end
		loaded = true
		local order, lastGroup = 0, nil
		for _, action in catalog do
			if action.Group ~= lastGroup then
				lastGroup = action.Group
				order += 1
				text("TextLabel", { Text = string.upper(action.Group), TextColor3 = ACCENT, TextSize = 15, LayoutOrder = order, Size = UDim2.new(1, -8, 0, 22), Parent = list })
			end
			order += 1
			addCard(action, order)
		end
	end

	-- Size: a column on the right; full width (minus margins) on a narrow phone.
	local function layout()
		local camera = Workspace.CurrentCamera
		local viewport = if camera then camera.ViewportSize else Vector2.new(1280, 720)
		panel.Size = UDim2.fromOffset(math.min(380, viewport.X - 16), math.max(240, viewport.Y - 70))
	end

	local function setOpen(open: boolean)
		if open and not loaded then
			loadCatalog()
		end
		layout()
		closePicker()
		panel.Visible = open
		placeEdgeButtons()
	end

	toggleButton.Activated:Connect(function()
		setOpen(not panel.Visible)
	end)
	closeButton.Activated:Connect(function()
		setOpen(false)
	end)
	local connections = {}
	if TOGGLE_KEY then
		table.insert(connections, UserInputService.InputBegan:Connect(function(input)
			if input.KeyCode == TOGGLE_KEY then
				setOpen(not panel.Visible)
			end
		end))
	end
	if Workspace.CurrentCamera then
		table.insert(connections, Workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(function()
			layout()
			placeEdgeButtons()
		end))
	end

	local menu = { panel = panel, toggleButton = toggleButton, left = left, buttonY = options.buttonY }
	table.insert(menus, menu)

	return {
		gui = gui,
		Destroy = function()
			for _, connection in connections do
				connection:Disconnect()
			end
			table.remove(menus, table.find(menus, menu))
			gui:Destroy()
		end,
	}
end


return ActionMenu
