# plaza_boards.py - the plaza's leaderboard board in the buildings' smooth "toy" style (the shared
# BuildingPalette.png, weighted normals, every mesh under 10k triangles), one model used for all three boards:
#   LeaderboardBoard   two snow-capped log posts in snowy rock footings, a carved ice frame round a flat dark
#                      display panel, a blank wooden header sign (crown medallion) with snow on top, icicles
#                      under the frame's top bar, small ice crystals at the corners
# The rows and the title stay a SurfaceGui on the game's invisible "Face" part (PlazaService): 16 wide x 20 tall
# x 1 deep, its bottom 1 stud up, centred on the model's origin. So the mesh panel is 16 x 20, its bottom at
# z = 1, and its flat front face at Blender y = -0.45 (0.05 behind the Face part's front, so the GUI never
# z-fights). Origin on the ground under the panel's centre; front faces -Y (Roblox -Z, the Model's LookVector).
# Mesh names end in their colour role.
#   blender -b --factory-startup --python tools/blender/plaza_boards.py [-- render]
#   (or the Blender MCP: REPO = r"..."; exec(open(REPO + r"\tools\blender\plaza_boards.py", encoding="utf-8").read()))
# Out: store-assets/plaza/LeaderboardBoard.fbx, plaza_manifest.json (meshes, triangles, sizes), render/*.png
import math, os, sys, json, random
import bpy, bmesh
from mathutils import Vector, Matrix

if "REPO" not in globals():
    REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT_SCALE = 0.1  # as plot_parts.py: arrives at 10x, so build_templates.luau's plot path (PLOT_IMPORT = 10) loads it
exec(open(os.path.join(REPO, "tools", "blender", "model_helpers.py"), encoding="utf-8").read())
exec(open(os.path.join(REPO, "tools", "blender", "building_kit.py"), encoding="utf-8").read())
OUT = os.path.join(REPO, "store-assets", "plaza")
RENDER = "render" in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []) or globals().get("RENDER", False)
MAX_TRIS = 10000

# PlazaService's Face part (studs): keep in step with board() in src/server/PlazaService.luau
PANEL = {"Width": 16, "Height": 20, "Bottom": 1, "Front": -0.45}
LIP = 0.45         # the carved inner step of the frame, round the panel
FRAME = 1.4        # the chunky outer frame blocks
FRAME_FRONT = -1.3  # the frame's front face (it stands proud of the panel, so the panel reads inset)
FRAME_BACK = 0.95
POST_X, POST_Y, POST_R = 10.35, 0.45, 1.05
TOP = PANEL["Bottom"] + PANEL["Height"]  # 21: the panel's top edge
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


def snow_roll(part, length, depth, z, rng, height=0.75, centre=(0, 0)):
    """A pillowy snow layer along X from z up, with lumps on top and a few drips over the front and back."""
    box(part, (length, depth, height), (centre[0], centre[1], z + height / 2), "SnowWhite", corner=min(depth / 2 - 0.02, 0.6), edge=height / 2 - 0.02, seg=2)
    x = -length / 2 + rng.uniform(1.0, 2.0)
    while x < length / 2 - 1.0:
        w = rng.uniform(1.6, 3.0)
        lump(part, (centre[0] + x, centre[1] + rng.uniform(-0.12, 0.12) * depth, z + height * 0.75), (w / 2, depth * 0.45, rng.uniform(0.3, 0.55)))
        if rng.random() < 0.4:
            side = rng.choice((-1, 1)) * (depth / 2)
            lump(part, (centre[0] + x + rng.uniform(-0.5, 0.5), centre[1] + side, z + 0.1), (0.45, 0.4, rng.uniform(0.35, 0.6)))
        x += w * rng.uniform(0.9, 1.3)


def log(part, x, y, height, radius, rng):
    """A chunky round log standing on the ground: a slightly wobbly trunk, two bark bands, a cut top."""
    profile = [(0, 0), (radius * 1.08, 0)]
    rings = 7
    for k in range(1, rings + 1):
        profile.append((radius * rng.uniform(0.95, 1.03), height * k / (rings + 1)))
    profile += [(radius, height - 0.25), (radius * 0.9, height), (0, height)]
    bm = bmesh.new()
    lathe(bm, profile, 12)
    part.take(bm, "Pine", Matrix.Translation((x, y, 0)) @ Matrix.Rotation(rng.uniform(0, 1), 4, "Z"))
    for z in (height * 0.33, height * 0.72):  # bark bands
        ring = bmesh.new()
        torus(ring, Matrix.Translation((x, y, z)), radius * 0.98, 0.16, 12, 5)
        part.take(ring, "PineDark")
    top = bmesh.new()  # the cut end, lighter
    cylinder(top, (0, 0, 0), radius * 0.82, 0.08, 12)
    part.take(top, "PineLight", Matrix.Translation((x, y, height - 0.02)))


def crown(part, at, scale=1.0):
    """A small gold crown facing -Y: a band and five points with balls on the tips."""
    s = scale
    box(part, (2.2 * s, 0.35 * s, 0.55 * s), (at[0], at[1], at[2] - 0.45 * s), "Gold", corner=0.12 * s, edge=0.1 * s)
    for k, (dx, h) in enumerate(((-0.95, 0.85), (-0.48, 1.05), (0, 1.3), (0.48, 1.05), (0.95, 0.85))):
        bm = bmesh.new()
        lathe(bm, [(0, 0), (0.26 * s, 0), (0.12 * s, h * s * 0.75), (0, h * s)], 4)
        part.take(bm, "Gold", Matrix.Translation((at[0] + dx * s, at[1], at[2] - 0.25 * s)) @ Matrix.Rotation(math.pi / 4, 4, "Z"))
        lump(part, (at[0] + dx * s, at[1], at[2] - 0.25 * s + h * s), (0.17 * s, 0.17 * s, 0.17 * s), "Gold")


# ---------- the model ----------

def leaderboard(seed):
    rng = random.Random(seed)
    name = "LeaderboardBoard"
    panel, ice, wood, snow, stone, crystals, gold = (Part(name + r) for r in ("Panel", "Ice", "Wood", "Snow", "Stone", "Crystals", "Gold"))
    w, bottom = PANEL["Width"], PANEL["Bottom"]
    cz = bottom + PANEL["Height"] / 2

    # the display panel: one flat dark slab, its front exactly at PANEL["Front"]
    depth = 0.5
    box(panel, (w, depth, PANEL["Height"]), (0, PANEL["Front"] + depth / 2, cz), "NavyIce", corner=0.1, edge=0.1, seg=1)
    # the wooden back board behind it (seen from behind the board), with vertical planks on its back
    box(wood, (w + 2 * (LIP + FRAME) - 0.6, 0.7, PANEL["Height"] + 1.8), (0, 0.55, cz + 0.4), "PineDark", corner=0.3, edge=0.2)
    n = 6
    for z in (5.0, 17.0):  # two battens across the back, tying the posts together
        box(wood, (2 * POST_X, 0.55, 1.1), (0, 1.5, z), "PineDark", corner=0.2, edge=0.15)
    for i in range(n):
        pw = (w + 1.6) / n
        box(wood, (pw - 0.18, 0.4, PANEL["Height"] + 1.2), (-(w + 1.6) / 2 + pw * (i + 0.5), 1.05, cz + 0.3), ("Pine", "PineLight")[i % 2], corner=0.12, edge=0.1)

    # the carved inner step: a thin deeper-blue lip round the panel, set back from the frame's face
    lip_front = -0.8
    lip_d = FRAME_BACK - lip_front
    lip_y = (lip_front + FRAME_BACK) / 2
    box(ice, (w + 2 * LIP, lip_d, LIP + 0.2), (0, lip_y, TOP + LIP / 2 - 0.05), "GlacierBlue", corner=0.15, edge=0.15)
    box(ice, (w + 2 * LIP, lip_d, LIP + 0.2), (0, lip_y, bottom - LIP / 2 + 0.05), "GlacierBlue", corner=0.15, edge=0.15)
    for side in (-1, 1):
        box(ice, (LIP + 0.2, lip_d, PANEL["Height"] + 2 * LIP), (side * (w / 2 + LIP / 2 - 0.05), lip_y, cz), "GlacierBlue", corner=0.15, edge=0.15)

    # the chunky outer frame: rounded ice blocks, big corner blocks, a little jitter so it looks hand-carved
    fd = FRAME_BACK - FRAME_FRONT
    fy = (FRAME_FRONT + FRAME_BACK) / 2
    inner_x = w / 2 + LIP
    outer_x = inner_x + FRAME
    corner_size = FRAME + 0.7
    top_bar = (TOP + LIP, TOP + LIP + FRAME + 0.1)            # z range of the top bar
    bottom_bar = (0.0, bottom - LIP + 0.25)                   # the bottom bar sits on the ground
    for zr, along in ((top_bar, "top"), (bottom_bar, "bottom")):
        x = -inner_x
        while x < inner_x - 0.4:
            seg = min(rng.uniform(3.2, 4.4), inner_x - x)
            if inner_x - x - seg < 1.4:
                seg = inner_x - x
            h = zr[1] - zr[0]
            box(ice, (seg - 0.12, fd - rng.uniform(0, 0.12), h - 0.06), (x + seg / 2, fy + rng.uniform(-0.04, 0.04), (zr[0] + zr[1]) / 2),
                rng.choice(ICE_SWATCHES), corner=0.4, edge=min(0.4, h / 2 - 0.05), rot=math.radians(rng.uniform(-1.2, 1.2)))
            x += seg
    side_low, side_high = bottom_bar[1] + corner_size - 0.4, top_bar[0] - corner_size + 0.6
    for side in (-1, 1):
        z = side_low
        while z < side_high - 0.4:
            seg = min(rng.uniform(3.0, 4.2), side_high - z)
            if side_high - z - seg < 1.4:
                seg = side_high - z
            box(ice, (FRAME - 0.06, fd - rng.uniform(0, 0.12), seg - 0.12), (side * (inner_x + FRAME / 2), fy + rng.uniform(-0.04, 0.04), z + seg / 2),
                rng.choice(ICE_SWATCHES), corner=0.4, edge=0.4, rot=math.radians(rng.uniform(-1.2, 1.2)))
            z += seg
        # the corner blocks: bigger, standing a little proud, the top ones crowned with snow and crystals
        ccx = side * (inner_x + FRAME / 2 + 0.05)  # centred on the side bar, so it stays clear of the panel
        for zc in (corner_size / 2, top_bar[1] + 0.25 - corner_size / 2):
            box(ice, (corner_size, fd + 0.35, corner_size), (ccx, fy - 0.1, zc), "FrostLight", corner=0.55, edge=0.5, rot=math.radians(rng.uniform(-3, 3)))
            # a cut ice gem (a diamond shape) on the corner block's face
            gem = bmesh.new()
            cylinder(gem, (0, 0, 0), 0.62, 0.3, 4, top=0.3, direction=(0, -1, 0))
            crystals.take(gem, "CrystalCyan", Matrix.Translation((ccx, FRAME_FRONT - 0.27, zc)), bevel=0.06)

    # icicles under the top bar: short, hanging in front of the carved lip only, so they never cross the panel
    # (the GUI title sits just under it); the long ones hang under the corner blocks, outside the panel
    x = -inner_x + 0.4
    while x < inner_x - 0.3:
        length = rng.uniform(0.3, top_bar[0] - TOP - 0.08)
        cone(ice, (x + rng.uniform(-0.12, 0.12), FRAME_FRONT + 0.35, top_bar[0] + 0.02), rng.uniform(0.14, 0.2), length, rng.choice(("Diamond", "IceBlue", "FrostLight")))
        x += rng.uniform(0.7, 1.1)
    # and longer ones under the outer corners and the header's ends
    for side in (-1, 1):
        for k in range(3):
            ccx = side * (inner_x + FRAME / 2 + 0.05)
            cone(ice, (ccx + side * (k - 1) * 0.6, FRAME_FRONT + 0.15, top_bar[1] + 0.3 - corner_size), rng.uniform(0.2, 0.28), (1.9, 1.2, 1.5)[k] * rng.uniform(0.85, 1.1), ("Diamond", "IceBlue", "Diamond")[k])
        # snow heaped on the top corner blocks
        lump(snow, (side * (inner_x + FRAME / 2 + 0.05), fy - 0.1, top_bar[1] + 0.3), (1.25, 1.55, 0.6), subdivisions=2)

    # the posts: two chunky logs, the frame set into them
    post_h = top_bar[1] + 4.0
    for side in (-1, 1):
        log(wood, side * POST_X, POST_Y, post_h, POST_R, rng)
        # snow cap
        lump(snow, (side * POST_X, POST_Y, post_h + 0.1), (POST_R * 1.45, POST_R * 1.45, 0.95), subdivisions=2)
        lump(snow, (side * POST_X + side * 0.15, POST_Y + 0.1, post_h + 0.85), (POST_R * 0.9, POST_R * 0.9, 0.7), subdivisions=2)
        lump(snow, (side * (POST_X + POST_R * 0.7), POST_Y - 0.4, post_h - 0.35), (0.4, 0.4, 0.6))  # a drip over the side

    # the header sign: a wide blank wooden board between the posts, a crown medallion in its middle
    hz0, hh = top_bar[1] + 0.15, 3.3
    hy = 0.1
    hw = 2 * POST_X
    box(wood, (hw, 0.9, hh + 0.5), (0, hy + 0.15, hz0 + hh / 2), "PineDark", corner=0.35, edge=0.25)
    for row in range(3):
        rh = hh / 3
        box(wood, (hw - 2 * POST_R - 0.4, 0.9, rh - 0.12), (0, hy - 0.15, hz0 + 0.25 + rh * (row + 0.5) - 0.25), ("PineLight", "Pine", "PineLight")[row], corner=0.15, edge=0.1)
    for side in (-1, 1):  # wooden pegs at the plank ends
        for zz in (hz0 + 0.8, hz0 + hh - 0.6):
            peg = bmesh.new()
            cylinder(peg, (0, 0, 0), 0.2, 0.18, 8, direction=(0, -1, 0))
            wood.take(peg, "PineDark", Matrix.Translation((side * (hw / 2 - POST_R - 0.75), hy - 0.62, zz)), bevel=0.04)
    mz = hz0 + hh / 2 + 0.05
    disc = bmesh.new()
    cylinder(disc, (0, 0, 0), 1.75, 0.45, 24, direction=(0, -1, 0))
    ice.take(disc, "DeepIce", Matrix.Translation((0, hy - 0.5, mz)), bevel=0.1)
    ring = bmesh.new()
    torus(ring, Matrix.Translation((0, hy - 0.97, mz)) @ Matrix.Rotation(math.pi / 2, 4, "X"), 1.72, 0.22, 24, 6)
    ice.take(ring, "FrostLight")
    crown(gold, (0, hy - 1.05, mz - 0.25), 0.85)
    # snow on the header and on the frame's front ledge
    snow_roll(snow, hw - 1.4, 1.9, hz0 + hh + 0.1, rng, height=1.0, centre=(0, hy + 0.1))
    for k in range(6):
        lump(snow, (rng.uniform(-inner_x + 1, inner_x - 1), FRAME_FRONT + 0.55, top_bar[1] - 0.05), (rng.uniform(0.9, 1.5), 0.42, rng.uniform(0.22, 0.32)))

    # crystal clusters on the corners: on top of the top corner blocks and out of the snow at the feet
    for side in (-1, 1):
        base = Vector((side * (inner_x + FRAME / 2 + 0.3), fy - 0.5, top_bar[1] + 0.35))
        for k in range(3):
            off = Vector((side * (0.15 + 0.35 * k), rng.uniform(-0.3, 0.3), 0))
            lean = (math.radians(rng.uniform(-10, 10)), math.radians(side * (12 + 16 * k)))
            prism(crystals, base + off, (0.42, 0.34, 0.3)[k], (2.4, 1.7, 1.2)[k] * rng.uniform(0.9, 1.1), ("CrystalCyan", "Diamond", "IceBlue")[k], lean=lean, rot=rng.uniform(0, 1))
        base = Vector((side * (POST_X - 0.2), POST_Y - 2.0, 0.3))
        for k in range(4):
            off = Vector((side * rng.uniform(-0.6, 0.6), rng.uniform(-0.3, 0.3), 0))
            lean = (math.radians(-rng.uniform(10, 30)), math.radians(side * rng.uniform(0, 25)))
            prism(crystals, base + off, rng.uniform(0.3, 0.45), rng.uniform(1.0, 1.9) * (1.3 if k == 0 else 1.0), rng.choice(("CrystalCyan", "IceBlue", "Diamond")), lean=lean, rot=rng.uniform(0, 1))

    # the footings: snowy rocks round each post's foot, a chunk of ice, a snow drift
    for side in (-1, 1):
        fx = side * POST_X
        # a ring of chunky rocks round the post's foot, the biggest in front
        for k, (dx, dy, r) in enumerate(((-0.75, -1.25, 1.2), (0.75, -1.1, 1.15), (1.0, 0.6, 1.05), (-1.0, 0.7, 1.05), (0.0, 1.35, 0.95), (side * -1.25, -0.2, 0.9))):
            lump(stone, (fx + dx, POST_Y + dy, 0.3), (r * rng.uniform(0.95, 1.1), r * rng.uniform(0.85, 1.0), r * 0.85),
                 ("Stone", "StoneLight", "Stone", "StoneDark", "StoneLight", "Stone")[k], subdivisions=1, rot=rng.uniform(0, 3), floor=0.0)
        box(ice, (1.3, 1.1, 1.2), (fx - side * 1.6, POST_Y - 1.0, 0.55), "IceBlue", corner=0.4, edge=0.35, rot=math.radians(rng.uniform(-20, 20)), tilt=(0.15, 0.1))
        lump(snow, (fx, POST_Y - 0.1, 1.05), (1.7, 1.55, 0.6), subdivisions=2, floor=0.0)
        lump(snow, (fx - side * 0.9, POST_Y - 1.2, 0.2), (1.3, 1.0, 0.55), subdivisions=2, floor=0.0)
    # a low drift along the bottom bar's front (below the panel: its top stays under z = 1)
    for k in range(5):
        x = -w / 2 + 1.2 + k * (w - 2.4) / 4 + rng.uniform(-0.6, 0.6)
        lump(snow, (x, FRAME_FRONT - 0.35, 0.0), (rng.uniform(1.3, 2.0), 0.75, rng.uniform(0.55, 0.8)), floor=0.0)
    return [panel, ice, wood, snow, stone, crystals, gold]


# ---------- renders (preview only: never exported) ----------

def render_views(objects, out_dir):
    """EEVEE previews with a sun and a bright sky, roughly Roblox's daylight. Adds a snow floor, the stand-in GUI
    text and a camera to the scene (after the export, so none of them reaches the FBX)."""
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.view_settings.view_transform = "Standard"  # flat palette colours, as Roblox shows them
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    if world.node_tree is None:
        world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.62, 0.78, 0.95, 1)
    bg.inputs["Strength"].default_value = 0.9
    sun = bpy.data.objects.new("PreviewSun", bpy.data.lights.new("PreviewSun", "SUN"))
    sun.data.energy = 2.6
    sun.data.angle = math.radians(3)
    sun.rotation_euler = Vector((0.45, 0.65, -0.75)).to_track_quat("-Z", "Y").to_euler()  # from the front left, high
    scene.collection.objects.link(sun)
    extras = []
    ground = Part("PreviewGround")
    gbm = bmesh.new()
    rounded_block(gbm, (120, 120, 0.4), Matrix.Translation((0, 0, -0.22)), corner=1, edge=0.1, corner_seg=1, edge_seg=1)
    ground.take(gbm, "SnowWhite")
    g = ground.finish(scene.collection, materials)
    extras.append(g)
    # stand-in GUI text, as PlazaService draws it, on the Face part's front (y = -0.5)
    for body, size, z, colour in (("ALL-TIME CRYSTALS", 1.55, TOP - 1.9, (1.0, 0.72, 0.1)),
                                  ("1. FrostyFox  12.4M\n2. IcePrincess  9.1M\n3. Snowball99  7.7M\n4. Glacier  5.0M\n5. Penguin  3.2M", 1.15, TOP - 4.6, (1, 1, 1))):
        curve = bpy.data.curves.new("PreviewText", "FONT")
        curve.body = body
        curve.size = size
        curve.align_x = "CENTER" if size > 1.3 else "LEFT"
        curve.extrude = 0.01
        t = bpy.data.objects.new("PreviewText", curve)
        t.location = (0 if size > 1.3 else -7.3, -0.5, z)
        t.rotation_euler = (math.pi / 2, 0, 0)
        bpy.context.scene.collection.objects.link(t)
        mat = bpy.data.materials.new("PreviewTextMat")
        if mat.node_tree is None:
            mat.use_nodes = True
        b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")  # unlit, like LightInfluence 0
        b.inputs["Base Color"].default_value = (0, 0, 0, 1)
        b.inputs["Emission Color"].default_value = (*colour, 1)
        b.inputs["Emission Strength"].default_value = 1.0
        curve.materials.append(mat)
        extras.append(t)
    cam = bpy.data.objects.new("ShotCamera", bpy.data.cameras.new("ShotCamera"))
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 900, 900, 100
    views = {
        "front": ((0, -55, 13.5), (0, 0, 13.5), 50),
        "three_quarter": ((-30, -38, 20), (0, 0, 12.5), 45),
        "eye_30": ((0, -30, 5), (0, 0, 13), 26),
        "eye_30_side": ((-17, -25, 5), (0, 0, 13), 26),
        "back": ((22, 40, 16), (0, 0, 12), 45),
    }
    os.makedirs(out_dir, exist_ok=True)
    for name, (eye, target, lens) in views.items():
        cam.data.lens = lens
        cam.location = Vector(eye)
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(out_dir, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)


# ---------- build, check, export ----------

coll = begin("PlazaBoards")
image = bpy.data.images.get("BuildingPalette") or bpy.data.images.load(os.path.join(REPO, "assets", "textures", "BuildingPalette.png"))
image.name = "BuildingPalette"
materials = palette_materials(image)
models = {"LeaderboardBoard": leaderboard(21)}
manifest = {"exportScale": EXPORT_SCALE, "models": {}}
problems = []
os.makedirs(OUT, exist_ok=True)
for name, parts in models.items():
    objs = [p.finish(coll, materials) for p in parts]
    lo, hi = bounds(objs)
    info = {"meshes": {o.name: tris_of(o) for o in objs}, "size": [round(hi.x - lo.x, 2), round(hi.z - lo.z, 2), round(hi.y - lo.y, 2)],
            "top": round(hi.z, 2), "bounds": {"x": [round(lo.x, 2), round(hi.x, 2)], "y": [round(lo.y, 2), round(hi.y, 2)], "z": [round(lo.z, 2), round(hi.z, 2)]}}
    info["triangles"] = sum(info["meshes"].values())
    panel = next(o for o in objs if o.name.endswith("Panel"))
    plo, phi = bounds([panel])
    info["panel"] = {"front": round(plo.y, 3), "width": round(phi.x - plo.x, 3), "bottom": round(plo.z, 3), "top": round(phi.z, 3)}
    # nothing may stand in front of the panel's face inside its rectangle
    for o in objs:
        if o is panel:
            continue
        for v in o.data.vertices:
            p = o.matrix_world @ v.co
            if abs(p.x) < PANEL["Width"] / 2 - 0.05 and PANEL["Bottom"] + 0.05 < p.z < TOP - 0.05 and p.y < PANEL["Front"]:
                problems.append("%s has a vertex in front of the panel at %s" % (o.name, tuple(round(c, 2) for c in p)))
                break
    for o in objs:
        if info["meshes"][o.name] > MAX_TRIS:
            problems.append("%s has %d triangles" % (o.name, info["meshes"][o.name]))
    problems += check(objs)
    manifest["models"][name] = info
    print(name, json.dumps(info))
    export_fbx(objs, os.path.join(OUT, name + ".fbx"))
    if RENDER:
        render_views(objs, os.path.join(OUT, "render"))
with open(os.path.join(OUT, "plaza_manifest.json"), "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=1, sort_keys=True)
for p in problems:
    print("PROBLEM:", p)
print("PLAZA_BOARDS_DONE", "problems:", len(problems))
