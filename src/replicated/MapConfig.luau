--[[
MapConfig: where things are in the world (docs/GAME_DESIGN.md, "Plot and map layout"). Studs.

 * Plots: PlotCount plots in a ring around the plaza, each a PlotSize square (BuildingConfig.PlotSize)
   whose centre is RingRadius from the plaza's centre, with its open front (+Z in plot space)
   facing the plaza. Pads and the ice block are placed in plot space (BuildingConfig pads: X, Z from
   the centre of the ice).
 * The ice block stands on a raised snow mound in the middle of the plot.
 * A player can tap their ice while standing inside their own plot (TapMargin studs of slack).
]]
local MapConfig = {}

MapConfig.Ground = 0 -- the top of the baseplate
MapConfig.PlotCount = 8
MapConfig.PlotSize = 100
MapConfig.RingRadius = 175 -- plaza centre to plot centre
MapConfig.PlazaRadius = 70
MapConfig.TapMargin = 6 -- studs outside the plot square that still count as "in your plot"

MapConfig.Mound = { Size = 30, Height = 3 } -- the snow mound under the ice (square, rounded later)
MapConfig.Border = { Height = 3, Thickness = 2, FrontGap = 44 } -- the low snow wall, open at the front
-- The name sign is an arch over the open front: two posts on the wall ends and a beam high enough that the
-- tallest ice (23 studs with its mound, 50 studs behind the arch) stays in view beneath it from the plaza
-- and the path (tests/World.spec.luau checks the line of sight).
MapConfig.Arch = { ClearHeight = 20, BeamHeight = 3, BeamDepth = 2, PostSize = 3 }
MapConfig.TapSpot = { X = 0, Z = 24 } -- where a player arrives in their plot: in front of the ice

-- The plot ring: plot i's centre and facing. Returns a CFrame whose LookVector points AWAY from the
-- plaza, so +Z (the open front) faces the plaza.
function MapConfig.PlotCFrame(index: number): CFrame
	local angle = (index - 1) / MapConfig.PlotCount * math.pi * 2
	local centre = Vector3.new(math.sin(angle) * MapConfig.RingRadius, MapConfig.Ground, math.cos(angle) * MapConfig.RingRadius)
	local outward = Vector3.new(centre.X, 0, centre.Z).Unit
	return CFrame.lookAt(centre, centre + outward)
end

-- Where the ice block stands: the middle of the mound's top, in plot index's frame.
function MapConfig.BlockBase(index: number): CFrame
	return MapConfig.PlotCFrame(index) * CFrame.new(0, MapConfig.Mound.Height + 1, 0)
end

-- A point in plot space (x, z from the centre of the ice; +Z toward the plaza) in the world.
function MapConfig.PlotPoint(index: number, x: number, z: number, y: number?): Vector3
	return (MapConfig.PlotCFrame(index) * CFrame.new(x, y or 0, z)).Position
end

return MapConfig
