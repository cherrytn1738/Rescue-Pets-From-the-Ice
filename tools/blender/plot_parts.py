# plot_parts.py - the plot's own parts in the buildings' smooth "toy" style (the shared BuildingPalette.png,
# weighted normals, every mesh under 10k triangles). Four models, each its own FBX with its pivot at the origin
# on the ground (Blender X = plot X, Blender Y = plot Z, front -Y):
#   PlotWallLong   the 100-stud border wall (Back, Left, Right): rounded ice blocks on a plinth, snow on top
#   PlotWallShort  the 28-stud front wall sections (FrontLeft, FrontRight)
#   PlotArch       the entrance gate: chunky ice pillars with snow caps, a frosted lintel with icicles, and two
#                  wooden name boards on the front walls beside it (the owner's name is a SurfaceGui in game)
#   PlotStage      the frozen stage under the ice block: cracked ice tiles on a snowy rim, small crystals
# Mesh names end in their colour role. "...Trim" meshes are untextured in game and take the owner's rebirth
# colour (RankService). The collision stays the plot's own invisible Parts (PlotService), so every size here
# follows MapConfig: the walls, the arch's posts and beam, the mound (Mound 30 x 3, its top 24 x 1).
#   blender -b --factory-startup --python tools/blender/plot_parts.py [-- render]
#   (or the Blender MCP: REPO = r"..."; exec(open(REPO + r"\tools\blender\plot_parts.py", encoding="utf-8").read()))
# Out: store-assets/plot/<Model>.fbx, plot_manifest.json (meshes, triangles, sizes), render/*.png
import math, os, sys, json, random
import bpy, bmesh
from mathutils import Vector, Matrix

if "REPO" not in globals():
    REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT_SCALE = 0.1  # the 100-stud wall would pass Roblox's 2048-stud part cap at the usual 25x import; this arrives at 10x
exec(open(os.path.join(REPO, "tools", "blender", "model_helpers.py"), encoding="utf-8").read())
exec(open(os.path.join(REPO, "tools", "blender", "building_kit.py"), encoding="utf-8").read())
OUT = os.path.join(REPO, "store-assets", "plot")
RENDER = "render" in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []) or globals().get("RENDER", False)
MAX_TRIS = 10000

# MapConfig (studs): keep in step with src/replicated/MapConfig.luau
PLOT = 100
WALL = {"Height": 3, "Thickness": 2, "FrontGap": 44}
SHORT = (PLOT - WALL["FrontGap"]) / 2  # 28
ARCH = {"ClearHeight": 20, "BeamHeight": 3, "BeamDepth": 2, "PostSize": 3}
BOARD = {"Width": 12.8, "Height": 3.8, "Bottom": 7.2, "CentreX": 36.0}  # MapConfig.Arch.Board
MOUND = {"Size": 30, "Height": 3}
ICE_SWATCHES = ["IceBlue", "FrostLight", "IceBlue", "GlacierBlue", "IceBlue"]


def tris_of(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def box(part, size, at, swatch, corner=0.3, edge=0.2, rot=0.0, tilt=(0.0, 0.0), taper=1.0, seg=2):
    bm = bmesh.new()
    rounded_block(bm, size, Matrix(), corner=corner, edge=edge, corner_seg=seg, edge_seg=seg, taper=taper)
    m = Matrix.Translation(Vector(at)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Rotation(tilt[0], 4, "X") @ Matrix.Rotation(tilt[1], 4, "Y")
    part.take(bm, swatch, m)


def lump(part, at, size, swatch="SnowWhite", subdivisions=1, rot=0.0, floor=None):
    bm = bmesh.new()
    blob(bm, (0, 0, 0), size, subdivisions=subdivisions, rotation=(0, 0, rot), floor=None if floor is None else floor - at[2])
    part.take(bm, swatch, Matrix.Translation(Vector(at)))


def cone(part, base, radius, length, swatch, segments=6, down=True, lean=(0.0, 0.0)):
    """An icicle (down) or a crystal spike (up): a cone from `base`."""
    bm = bmesh.new()
    lathe(bm, [(0, 0), (radius, 0), (radius * 0.55, length * 0.45), (0, length)], segments)
    m = Matrix.Translation(Vector(base)) @ Matrix.Rotation(lean[0], 4, "X") @ Matrix.Rotation(lean[1], 4, "Y")
    if down:
        m = m @ Matrix.Rotation(math.pi, 4, "X")
    part.take(bm, swatch, m)


def prism(part, base, radius, height, swatch, sides=6, lean=(0.0, 0.0), rot=0.0):
    """A crystal: a hexagonal prism with a pointed top."""
    bm = bmesh.new()
    lathe(bm, [(0, 0), (radius, 0), (radius, height * 0.7), (0, height)], sides)
    m = Matrix.Translation(Vector(base)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Rotation(lean[0], 4, "X") @ Matrix.Rotation(lean[1], 4, "Y")
    part.take(bm, swatch, m)


def snow_roll(part, length, depth, z, rng, height=0.75, lumps=True, along="X"):
    """A pillowy snow layer along X (or Y) from z up, with lumps on top and a few drips over the sides."""
    size = (length, depth, height) if along == "X" else (depth, length, height)
    box(part, size, (0, 0, z + height / 2), "SnowWhite", corner=min(depth / 2 - 0.02, 0.6), edge=height / 2 - 0.02, seg=2)
    if not lumps:
        return
    x = -length / 2 + rng.uniform(1.0, 3.0)
    while x < length / 2 - 1.0:
        w = rng.uniform(1.6, 3.2)
        p = (x, rng.uniform(-0.15, 0.15) * depth) if along == "X" else (rng.uniform(-0.15, 0.15) * depth, x)
        lump(part, (p[0], p[1], z + height * 0.75), (w / 2 if along == "X" else depth * 0.45, depth * 0.45 if along == "X" else w / 2, rng.uniform(0.28, 0.5)))
        if rng.random() < 0.35:  # a drip over the front or back edge
            side = rng.choice((-1, 1)) * (depth / 2)
            q = (x + rng.uniform(-0.5, 0.5), side) if along == "X" else (side, x + rng.uniform(-0.5, 0.5))
            lump(part, (q[0], q[1], z + 0.1), (0.45, 0.45, rng.uniform(0.35, 0.6)) if along == "X" else (0.45, 0.45, rng.uniform(0.35, 0.6)))
        x += w * rng.uniform(0.9, 1.4)


# ---------- the models ----------

def wall(name, length, seed):
    rng = random.Random(seed)
    ice, snow, trim = Part(name + "Ice"), Part(name + "Snow"), Part(name + "Trim")
    depth = WALL["Thickness"] + 0.5
    box(trim, (length + 0.4, depth + 0.4, 0.5), (0, 0, 0.25), "SteelLight", corner=0.35, edge=0.2)
    x = -length / 2
    while x < length / 2 - 0.5:
        w = min(rng.uniform(3.6, 5.0), length / 2 - x)
        if length / 2 - x - w < 1.5:
            w = length / 2 - x
        h = rng.uniform(2.25, 2.55)
        box(ice, (w - 0.14, depth - rng.uniform(0, 0.2), h), (x + w / 2, rng.uniform(-0.06, 0.06), 0.45 + h / 2),
            rng.choice(ICE_SWATCHES), corner=0.4, edge=0.32, rot=math.radians(rng.uniform(-1.5, 1.5)))
        x += w
    snow_roll(snow, length + 0.3, depth + 0.25, 2.72, rng)
    return [ice, snow, trim]


def arch(seed):
    rng = random.Random(seed)
    ice, snow, wood, trim = Part("PlotArchIce"), Part("PlotArchSnow"), Part("PlotArchWood"), Part("PlotArchTrim")
    half_gap = WALL["FrontGap"] / 2
    beam_bottom, beam_top = ARCH["ClearHeight"], ARCH["ClearHeight"] + ARCH["BeamHeight"]
    width = 6.0
    lintel_top = beam_top + 1.2  # the visible lintel stands a little above the collision beam
    for side in (-1, 1):
        cx = side * (half_gap + width / 2)  # the pillar's inner face on the opening's edge
        box(trim, (width + 1.4, width + 1.4, 0.8), (cx, 0, 0.4), "SteelLight", corner=0.9, edge=0.3)
        z = 0.7
        tiers = [(5.2, 6.6), (4.8, 6.2), (4.6, 5.9), (4.9, 5.7)]
        for i, (h, w) in enumerate(tiers):
            box(ice, (w, w, h - 0.14), (cx + rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), z + h / 2),
                ("IceBlue", "FrostLight", "GlacierBlue", "IceBlue")[i], corner=0.9, edge=0.55, rot=math.radians(rng.uniform(-3, 3)))
            for corner_x, corner_y in ((-1, -1), (1, -1), (-1, 1), (1, 1)):  # snow caught on the ledges
                if rng.random() < 0.6:
                    lump(snow, (cx + corner_x * (w / 2 - 0.9), corner_y * (w / 2 - 0.9), z + h - 0.05), (rng.uniform(0.7, 1.1), rng.uniform(0.7, 1.1), 0.35))
            z += h
        # the crown above the lintel, its snow cap and the icicles under its rim
        box(ice, (width + 1.4, width + 1.4, 1.8), (cx, 0, lintel_top + 0.9), "FrostLight", corner=1.0, edge=0.55)
        lump(snow, (cx, 0, lintel_top + 1.75), ((width + 1.2) * 0.55, (width + 1.2) * 0.55, 1.3), subdivisions=2)
        lump(snow, (cx + 0.4, 0.3, lintel_top + 2.7), (width * 0.33, width * 0.33, 0.85), subdivisions=2)
        for k in range(12):
            a = k / 12 * 2 * math.pi + rng.uniform(-0.1, 0.1)
            r = (width + 1.4) / 2 - 0.2
            cone(ice, (cx + math.cos(a) * r, math.sin(a) * r, lintel_top + 0.05), 0.24, rng.uniform(0.6, 1.4), "Diamond")
        # snow drifted against the pillar's foot
        lump(snow, (cx, 0, 0.5), (width * 0.72, width * 0.72, 1.0), subdivisions=2)
    # the frosted lintel: a frosted beam on an ice lip, snow along its top, icicles hanging under it (short in the
    # middle, so the ice stays in view under the beam from the plaza: tests/World.spec.luau)
    span = WALL["FrontGap"] + 2 * width
    depth = ARCH["BeamDepth"] + 1.6
    box(ice, (span, depth, lintel_top - beam_bottom - 0.6), (0, 0, beam_bottom + 0.3 + (lintel_top - beam_bottom - 0.6) / 2), "FrostLight", corner=0.7, edge=0.6)
    box(ice, (span - 1.0, depth + 0.3, 0.8), (0, 0, beam_bottom + 0.4), "GlacierBlue", corner=0.5, edge=0.35)
    box(ice, (span - 2.0, depth + 0.25, 0.6), (0, 0, lintel_top - 0.9), "IceBlue", corner=0.4, edge=0.25)
    snow_roll(snow, span - 1.0, depth + 0.4, lintel_top - 0.35, rng, height=1.0)
    # a snowflake medallion on the lintel's middle, front and back
    for face in (-1, 1):
        y = face * (depth / 2 + 0.25)
        disc = bmesh.new()
        cylinder(disc, (0, 0, 0), 3.1, 0.5, 24, direction=(0, face, 0))
        ice.take(disc, "DeepIce", Matrix.Translation((0, y - face * 0.25, lintel_top - 0.4)), bevel=0.12)
        ring = bmesh.new()
        torus(ring, Matrix.Translation((0, y + face * 0.25, lintel_top - 0.4)) @ Matrix.Rotation(math.pi / 2, 4, "X"), 3.0, 0.28, 24, 8)
        ice.take(ring, "FrostLight")
        for k in range(3):  # three bars make the six arms
            a = k * math.pi / 3
            bar = bmesh.new()
            rounded_block(bar, (4.6, 0.3, 0.55), Matrix(), corner=0.12, edge=0.1, corner_seg=1, edge_seg=1)
            snow.take(bar, "SnowWhite", Matrix.Translation((0, y + face * 0.3, lintel_top - 0.4)) @ Matrix.Rotation(a, 4, "Y"))
            for end in (-1, 1):  # little chevrons near each arm's tip
                tip = Vector((math.cos(a) * 1.5 * end, 0, -math.sin(a) * 1.5 * end))
                for turn in (-0.6, 0.6):
                    twig = bmesh.new()
                    rounded_block(twig, (1.1, 0.28, 0.35), Matrix(), corner=0.1, edge=0.08, corner_seg=1, edge_seg=1)
                    snow.take(twig, "SnowWhite", Matrix.Translation(tip + Vector((0, y + face * 0.32, lintel_top - 0.4))) @ Matrix.Rotation(a + turn * end, 4, "Y"))
    x = -half_gap + 0.6
    while x < half_gap - 0.6:
        middle = abs(x) < half_gap - 10
        length = rng.uniform(0.5, 1.0) if middle else rng.uniform(1.0, 2.6)
        for y in (-depth / 2 + 0.4, depth / 2 - 0.4):
            if rng.random() < 0.8:
                cone(ice, (x + rng.uniform(-0.2, 0.2), y, beam_bottom - 0.05), rng.uniform(0.16, 0.26), length, rng.choice(("Diamond", "IceBlue")))
        x += rng.uniform(1.0, 1.7)
    # the name boards: wooden boards on two posts, standing on the front walls beside the gate
    for side in (-1, 1):
        bx = side * BOARD["CentreX"]
        bottom, top = BOARD["Bottom"], BOARD["Bottom"] + BOARD["Height"]
        for px in (-BOARD["Width"] / 2 + 1.6, BOARD["Width"] / 2 - 1.6):
            box(wood, (0.7, 0.7, bottom - WALL["Height"] + 0.4), (bx + px, 0, WALL["Height"] + (bottom - WALL["Height"]) / 2), "PineDark", corner=0.15, edge=0.1)
        box(wood, (BOARD["Width"] + 0.8, 0.7, BOARD["Height"] + 0.8), (bx, 0, (bottom + top) / 2), "PineDark", corner=0.3, edge=0.2)
        for row in range(3):  # three planks, the name goes over them
            h = BOARD["Height"] / 3
            box(wood, (BOARD["Width"], 0.8, h - 0.1), (bx, 0, bottom + h * (row + 0.5)), ("PineLight", "Pine", "PineLight")[row], corner=0.12, edge=0.08)
        snow_roll(snow, BOARD["Width"] + 1.0, 1.0, top + 0.35, rng, height=0.5)
    return [ice, snow, wood, trim]


def stage(seed):
    rng = random.Random(seed)
    snow, ice, cracks, crystals = Part("PlotStageSnow"), Part("PlotStageIce"), Part("PlotStageCracks"), Part("PlotStageCrystals")
    size, height = MOUND["Size"], MOUND["Height"]
    top_size = size - 6
    # the snowy rim: a rounded snow slab (its top at the mound's height) with drifts round its edge
    box(snow, (size + 0.6, size + 0.6, height), (0, 0, height / 2), "SnowWhite", corner=2.6, edge=0.9, seg=3)
    for k in range(20):
        a = k / 20 * 2 * math.pi + rng.uniform(-0.08, 0.08)
        r = size / 2 + 0.1
        x, y = max(-r, min(r, math.cos(a) * r * 1.4)), max(-r, min(r, math.sin(a) * r * 1.4))
        if y > r - 0.01 and abs(x) < 7:
            continue  # the front (Blender +Y is the plot's +Z), where the footpath arrives
        lump(snow, (x, y, height - 0.6), (rng.uniform(1.4, 2.4), rng.uniform(1.4, 2.4), rng.uniform(0.7, 1.1)))
    # the deck: a dark under-layer (the cracks) and cracked ice tiles on it, their tops at the mound top (height + 1)
    box(cracks, (top_size + 0.2, top_size + 0.2, 0.9), (0, 0, height + 0.45), "DeepIce", corner=1.4, edge=0.3)
    n = 5
    step = top_size / n
    jitter = {}
    for i in range(n + 1):
        for j in range(n + 1):
            edge_i, edge_j = i in (0, n), j in (0, n)
            jx = 0 if edge_i else rng.uniform(-0.28, 0.28) * step
            jy = 0 if edge_j else rng.uniform(-0.28, 0.28) * step
            jitter[i, j] = Vector((-top_size / 2 + i * step + jx, -top_size / 2 + j * step + jy))
    for i in range(n):
        for j in range(n):
            quad = [jitter[i, j], jitter[i + 1, j], jitter[i + 1, j + 1], jitter[i, j + 1]]
            pieces = [quad]
            if rng.random() < 0.45:  # a crack across the tile
                if rng.random() < 0.5:
                    pieces = [[quad[0], quad[1], quad[2]], [quad[0], quad[2], quad[3]]]
                else:
                    pieces = [[quad[0], quad[1], quad[3]], [quad[1], quad[2], quad[3]]]
            for poly in pieces:
                centre = sum(poly, Vector((0, 0))) / len(poly)
                shrunk = [centre + (p - centre) * 0.93 - (p - centre).normalized() * 0.08 for p in poly]
                bm = bmesh.new()
                bottom = [bm.verts.new((p.x, p.y, height + 0.55)) for p in shrunk]
                topv = [bm.verts.new((p.x, p.y, height + 1.0)) for p in shrunk]
                bm.faces.new(topv)
                bm.faces.new(list(reversed(bottom)))
                for k in range(len(shrunk)):
                    a, b = k, (k + 1) % len(shrunk)
                    bm.faces.new((bottom[a], bottom[b], topv[b], topv[a]))
                bm.normal_update()
                bevel_edges(bm, 0.12, segments=2, angle=40)
                ice.take(bm, rng.choice(("IceBlue", "FrostLight", "IceBlue", "Diamond")))
    # small crystal clusters on the rim's corners
    for cx, cy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        base = Vector((cx * (size / 2 - 2.4), cy * (size / 2 - 2.4), height - 0.1))
        for k in range(4):
            off = Vector((rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9), 0))
            lean = (math.radians(rng.uniform(-22, 22)), math.radians(rng.uniform(-22, 22)))
            prism(crystals, base + off, rng.uniform(0.4, 0.6), rng.uniform(1.6, 2.6) * (1.3 if k == 0 else 1.0), rng.choice(("CrystalCyan", "IceBlue", "Diamond")), lean=lean, rot=rng.uniform(0, 1))
    return [snow, ice, cracks, crystals]


# ---------- build, check, export ----------

coll = begin("PlotParts")
image = bpy.data.images.get("BuildingPalette") or bpy.data.images.load(os.path.join(REPO, "assets", "textures", "BuildingPalette.png"))
image.name = "BuildingPalette"
materials = palette_materials(image)
models = {
    "PlotWallLong": wall("PlotWallLong", PLOT, 11),
    "PlotWallShort": wall("PlotWallShort", SHORT, 12),
    "PlotArch": arch(13),
    "PlotStage": stage(14),
}
manifest = {"exportScale": EXPORT_SCALE, "models": {}}
problems = []
os.makedirs(OUT, exist_ok=True)
for name, parts in models.items():
    objs = [p.finish(coll, materials) for p in parts]
    for o in objs:
        if o.name.endswith("Trim"):
            set_material(o, o.name, (0.79, 0.83, 0.87))  # preview only: in game the rebirth colour
    lo, hi = bounds(objs)
    info = {"meshes": {o.name: tris_of(o) for o in objs}, "size": [round(hi.x - lo.x, 2), round(hi.z - lo.z, 2), round(hi.y - lo.y, 2)],
            "top": round(hi.z, 2)}
    for o in objs:
        if info["meshes"][o.name] > MAX_TRIS:
            problems.append("%s has %d triangles" % (o.name, info["meshes"][o.name]))
    manifest["models"][name] = info
    print(name, info)
    export_fbx(objs, os.path.join(OUT, name + ".fbx"))
with open(os.path.join(OUT, "plot_manifest.json"), "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=1, sort_keys=True)
for p in problems:
    print("PROBLEM:", p)
print("PLOT_PARTS_DONE", "problems:", len(problems))
