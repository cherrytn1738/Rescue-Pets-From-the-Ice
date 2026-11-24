-- Rainbow rank (Glacier Legend, rebirth 10): every client cycles the colour of rainbow rank lines on
-- name tags (RankService builds the tags on the server and marks those lines Rainbow).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local elapsed = 0
RunService.Heartbeat:Connect(function(dt)
	elapsed += dt
	if elapsed < 0.1 then
		return
	end
	elapsed = 0
	local color = Color3.fromHSV((os.clock() * 0.2) % 1, 0.6, 1)
	for _, player in Players:GetPlayers() do
		local head = player.Character and player.Character:FindFirstChild("Head")
		local tag = head and head:FindFirstChild("NameTag")
		local line = tag and tag:FindFirstChild("Tag") and tag.Tag:FindFirstChild("RankLine")
		if line and line:GetAttribute("Rainbow") then
			line.TextColor3 = color
		end
	end
end)
