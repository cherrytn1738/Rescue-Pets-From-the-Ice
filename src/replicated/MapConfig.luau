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
MapConfig.Arch = {
	ClearHeight = 20,
	BeamHeight = 3,
	BeamDepth = 2,
	PostSize = 3,
	-- The owner's name: two wooden boards standing on the front walls beside the gate (low and to the side, so
	-- from the plaza they never sit behind the HUD's crystal counter at the top centre). Studs, plot space.
	Board = { Width = 12.8, Height = 3.8, Bottom = 7.2, CentreX = 36 },
}
-- The plot's own parts in the buildings' style (tools/blender/plot_parts.py, store-assets/plot/; uploaded as group
-- 921449746). tools/studio/build_templates.luau (ONLY = "Plot") builds ServerStorage.PlotTemplates from them;
-- PlotService shows them over the plot's invisible collision Parts, or the plain Parts while one is missing.
MapConfig.PlotModels = {
	PlotArch = 95072979923759,
	PlotStage = 127069362987945,
	PlotWallLong = 84064124507568,
	PlotWallShort = 128971708238167,
}
-- The plaza's own models (tools/blender/plaza_boards.py and plaza_props.py, uploaded as the group; built into
-- ServerStorage.PlazaTemplates by tools/studio/build_templates.luau with ONLY = "Plaza").
MapConfig.PlazaModels = {
	LeaderboardBoard = 105555700752777,
	DailyChestStand = 125874282900680,
	CodesKiosk = 99536553992465,
}
MapConfig.TapSpot = { X = 0, Z = 24 } -- where a player arrives in their plot: in front of the ice
-- The light column over your own plot's entrance while you're outside it (PlotGuide.client): it starts above the
-- gate's snow (the gate's top is about 26 studs up) and fades out as it rises.
MapConfig.HomeMarker = { Bottom = 28, Height = 55, Width = 3.5 }

-- The ground inside every plot (plot space, as the pads). The floor is the place's snow terrain, shaped by
-- tools/studio/build_world.luau from this table (re-run it after changing it, then save the place); the plot's
-- own Base part is an invisible floor above it. The footpath is a part (PlotService). Everything stays clear
-- of the pads, the mound and the open front.
MapConfig.PlotGround = {
	Footpath = { Width = 12, FromZ = 16, Color = Color3.fromRGB(198, 216, 238) }, -- from the mound to the open front
	Drifts = { -- low snow drifts against the walls: centre, radius, height above the ground
		{ X = 45, Z = 21, Radius = 7, Height = 3 },
		{ X = 46, Z = 12, Radius = 5, Height = 2 },
		{ X = -46, Z = 3, Radius = 4, Height = 2 },
		{ X = -45, Z = -45, Radius = 7, Height = 3.5 },
		{ X = 45, Z = -45, Radius = 7, Height = 3.5 },
		{ X = -42, Z = 45, Radius = 6, Height = 2.5 },
		{ X = 42, Z = 45, Radius = 6, Height = 2.5 },
	},
	IcePatches = { -- flat ice in the snow: centre, radius
		{ X = -29, Z = 3, Radius = 5 },
		{ X = 34, Z = 21, Radius = 4 },
		{ X = 13, Z = -29, Radius = 4 },
		{ X = -14, Z = 27, Radius = 4 },
	},
}

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
