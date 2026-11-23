-- ClientMain: starts the client systems that are modules (the windows and the HUD start themselves).
local IceBlocks = require(script.Parent.IceBlocks)

IceBlocks.Start() -- every plot's ice block, drawn from the server's attributes

print("[Client] started")
