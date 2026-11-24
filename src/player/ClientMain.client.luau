-- ClientMain: starts the client systems that are modules (the windows and the HUD start themselves).
local IceBlocks = require(script.Parent.IceBlocks)
local RescueMoment = require(script.Parent.RescueMoment)

IceBlocks.Start() -- every plot's ice block, drawn from the server's attributes
RescueMoment.Start() -- your rescues: the banner, the creature running to you; new layers; announcements

print("[Client] started")
