--[[
TeleportRules: whether a "take me to my plot" request (the HUD's PLOT button, the GoHome remote) goes ahead. Pure, so
tests/Teleport.spec.luau can check it; PlazaService gathers the facts and PlotService does the move.
Refused: too soon after the last one (GameConfig.Teleport.CooldownSeconds), no plot, no character or a dead one,
jailed by an admin. A refused request is ignored quietly (the client only asked).
]]
local TeleportRules = {}

export type Request = {
	now: number,
	lastAt: number?, -- the last teleport that went ahead (os.clock), if any
	hasPlot: boolean,
	alive: boolean, -- a character with a HumanoidRootPart and a Humanoid above 0 health
	jailed: boolean,
}

function TeleportRules.Check(request: Request, cooldownSeconds: number): (boolean, string?)
	if request.lastAt and request.now - request.lastAt < cooldownSeconds then
		return false, "cooldown"
	end
	if not request.hasPlot then
		return false, "no plot"
	end
	if not request.alive then
		return false, "no character"
	end
	if request.jailed then
		return false, "jailed"
	end
	return true, nil
end

return TeleportRules
