# plaza_props.py - two more plaza props in the leaderboard board's smooth toy style (plaza_boards.py's helpers, the
# shared BuildingPalette.png, weighted normals, every mesh under 10k triangles, mesh names ending in their colour role):
#   DailyChestStand  a chunky wooden treasure chest with gold bands, corner caps and a gold lock, its carved ice lid
#                    half open (frost and snow on top, icicles off its front lip), glowing cyan crystals and a few
#                    gold coins heaped inside; on a snowy stone plinth, with a little wooden sign post at its front
#                    left. About 8 x 6 studs, 7 tall. The game's invisible DailyChest Part (6 x 4 x 4, centre 2 up)
#                    keeps the ProximityPrompt; this model only shows.
#   CodesKiosk       a little notice stand: two snow-capped log posts, a peaked wooden gable roof with snow, icicles,
#                    a gift box on the ridge and crystals at the eaves, a carved wood-and-ice frame round a flat deep
#                    violet display panel, a snowy ledge under it, rocky footings. The panel matches PlazaService's
#                    CodesBoard Part (12 wide x 9 tall x 1 deep, centre 6 up): bottom at z = 1.5, top 10.5, its flat
#                    front at Blender y = -0.45, 0.05 behind the Part's front (-0.5), so the "CODES" SurfaceGui stays
#                    on that invisible Part and never z-fights.
# Origin on the ground under each model's centre; front faces -Y (Roblox -Z, the Model's LookVector).
# "...Glow" meshes become Neon in Studio (build_templates.luau), so the chest's loot crystals are CrystalsGlow.
#   blender -b --factory-startup --python tools/blender/plaza_props.py [-- render]
# Out: store-assets/plaza/<Model>.fbx, the models' entries in plaza_manifest.json, render/<Model>_*.png
import math, os, sys, json, random
import bpy, bmesh
from mathutils import Vector, Matrix

if "REPO" not in globals():
    REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLAZA_HELPERS_ONLY = True  # plaza_boards.py: load its helpers (box, lump, cone, prism, log, snow_roll...) only
exec(open(os.path.join(REPO, "tools", "blender", "plaza_boards.py"), encoding="utf-8").read())
RENDER = "render" in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []) or globals().get("RENDER", False)

# PlazaService's CodesBoard part (studs): keep in step with PlazaService.Start
CODES_PANEL = {"Width": 12, "Height": 9, "Bottom": 1.5, "Front": -0.45}
CODES_TOP = CODES_PANEL["Bottom"] + CODES_PANEL["Height"]  # 10.5


def post(part, x, y, z0, height, radius, rng, swatch="Pine"):
    """A thin round wooden post standing on z0, with a cut top."""
    profile = [(0, 0), (radius * 1.06, 0)]
    for k in range(1, 4):
        profile.append((radius * rng.uniform(0.95, 1.03), height * k / 4))
    profile += [(radius * 0.9, height), (0, height)]
    bm = bmesh.new()
    lathe(bm, profile, 10)
    part.take(bm, swatch, Matrix.Translation((x, y, z0)))


def dome(part, width, depth, height, matrix, swatch, rows=10):
    """A chest lid: a half-round loaf along X, flat underneath, its ends softly rounded. Built round the
    middle of its flat underside (y in [-depth/2, depth/2], z in [0, height])."""
    bm = bmesh.new()
    sections = []
    for x, s in ((-width / 2, 0.86), (-width / 2 + 0.1, 0.96), (-width / 2 + 0.22, 1.0),
                 (width / 2 - 0.22, 1.0), (width / 2 - 0.1, 0.96), (width / 2, 0.86)):
        loop = []
        for k in range(rows + 1):
            t = math.pi * k / rows
            y, z = -depth / 2 * math.cos(t), height * math.sin(t)
            loop.append(matrix @ Vector((x, y * s, height * 0.3 + (z - height * 0.3) * s if k not in (0, rows) else z)))
        sections.append(loop)
    loft(bm, sections)
    part.take(bm, swatch)


def coin(part, at, tilt=(0.0, 0.0), r=0.32):
    bm = bmesh.new()
    cylinder(bm, (0, 0, 0), r, 0.1, 10)
    part.take(bm, "Gold", Matrix.Translation(Vector(at)) @ Matrix.Rotation(tilt[0], 4, "X") @ Matrix.Rotation(tilt[1], 4, "Y"), bevel=0.03)


def gift(part, at, size, body, rng, rot=0.0, ribbon="Gold"):
    """A wrapped gift box: a rounded box, a ribbon cross over its top and down its sides, a two-loop bow."""
    w, d, h = size
    base = Matrix.Translation(Vector(at)) @ Matrix.Rotation(rot, 4, "Z")
    for piece, sw in (((w, d, h), body), ((w * 0.2, d + 0.06, h + 0.04), ribbon), ((w + 0.06, d * 0.2, h + 0.04), ribbon)):
        bm = bmesh.new()
        rounded_block(bm, piece, Matrix.Translation((0, 0, h / 2)), corner=min(0.18, piece[0] / 2 - 0.02, piece[1] / 2 - 0.02), edge=0.08, corner_seg=2, edge_seg=2)
        part.take(bm, sw, base)
    for side in (-1, 1):
        bm = bmesh.new()
        blob(bm, (0, 0, 0), (w * 0.22, w * 0.1, w * 0.16), subdivisions=1)
        part.take(bm, ribbon, base @ Matrix.Translation((side * w * 0.17, 0, h + w * 0.08)) @ Matrix.Rotation(side * 0.5, 4, "Y"))
    bm = bmesh.new()
    blob(bm, (0, 0, 0), (w * 0.08, w * 0.08, w * 0.08), subdivisions=1)
    part.take(bm, ribbon, base @ Matrix.Translation((0, 0, h + w * 0.06)))


def ticket(part, at, rot_y, swatch="Amber", stripe="Cream"):
    """A golden ticket facing -Y: a flat rounded card with a pale band and a dark punched hole."""
    m = Matrix.Translation(Vector(at)) @ Matrix.Rotation(rot_y, 4, "Y")
    piece = bmesh.new()
    rounded_block(piece, (1.5, 0.85, 0.14), Matrix(), corner=0.2, edge=0.05, corner_seg=2, edge_seg=1)
    part.take(piece, swatch, m @ Matrix.Rotation(math.pi / 2, 4, "X"))
    band = bmesh.new()
    rounded_block(band, (0.95, 0.5, 0.06), Matrix(), corner=0.1, edge=0.02, corner_seg=2, edge_seg=1)
    part.take(band, stripe, m @ Matrix.Translation((0.12, -0.08, 0)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    hole = bmesh.new()
    cylinder(hole, (0, 0, 0), 0.1, 0.05, 8, direction=(0, -1, 0))
    part.take(hole, "Gunmetal", m @ Matrix.Translation((-0.52, -0.07, 0)))


# ---------- the daily chest ----------

def daily_chest(seed):
    rng = random.Random(seed)
    name = "DailyChestStand"
    wood, gold, ice, snow, stone, crystals = (Part(name + r) for r in ("Wood", "Gold", "Ice", "Snow", "Stone", "Crystals"))
    glow = Part(name + "CrystalsGlow", glow=True)

    # the plinth: a chunky stone base, a lighter cap slab overhanging it, rocks at the corners
    PZ = 1.2
    box(stone, (7.0, 5.0, 0.8), (0, 0, 0.4), "Stone", corner=0.5, edge=0.25)
    box(stone, (7.5, 5.5, 0.5), (0, 0, PZ - 0.25), "StoneLight", corner=0.6, edge=0.2)
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        lump(stone, (sx * 3.35, sy * 2.35, 0.35), (0.75 * rng.uniform(0.9, 1.1), 0.7 * rng.uniform(0.9, 1.1), 0.6), ("StoneDark", "Stone", "StoneDark", "Stone")[k], rot=rng.uniform(0, 3), floor=0.0)
    # carved stone blocks along the base's front and sides (joints read as a built plinth)
    for i in range(4):
        x = -3.5 + 7.0 * (i + 0.5) / 4
        box(stone, (7.0 / 4 - 0.14, 0.3, 0.62), (x, -2.42, 0.42), ("Stone", "StoneLight")[i % 2], corner=0.12, edge=0.1)
    for side in (-1, 1):
        for i in range(3):
            y = -2.5 + 5.0 * (i + 0.5) / 3
            box(stone, (0.3, 5.0 / 3 - 0.14, 0.62), (side * 3.42, y, 0.42), ("StoneLight", "Stone")[i % 2], corner=0.12, edge=0.1)

    # the chest body: a dark core, three planks wrapped round it, gold bands, gold corner caps
    W, D, H = 5.0, 3.4, 2.5
    Z0, ZT = PZ, PZ + H
    box(wood, (W - 0.16, D - 0.16, H), (0, 0, Z0 + H / 2), "PineDark", corner=0.2, edge=0.1)
    rows = 3
    rh = (H - 0.1) / rows
    for r in range(rows):
        box(wood, (W, D, rh - 0.1), (0, 0, Z0 + 0.05 + rh * (r + 0.5)), ("Pine", "PineLight", "Pine")[r], corner=0.22, edge=0.1, rot=math.radians(rng.uniform(-0.6, 0.6)))
    # the rim round the open top (dark wood) and the deep ice inside it
    for sy in (-1, 1):
        box(wood, (W + 0.1, 0.42, 0.3), (0, sy * (D / 2 - 0.15), ZT + 0.05), "PineDark", corner=0.12, edge=0.1)
    for sx in (-1, 1):
        box(wood, (0.42, D + 0.1, 0.3), (sx * (W / 2 - 0.15), 0, ZT + 0.05), "PineDark", corner=0.12, edge=0.1)
    box(ice, (W - 0.7, D - 0.7, 0.2), (0, 0, ZT - 0.15), "NavyIce", corner=0.15, edge=0.05, seg=1)
    for sx in (-1.55, 1.55):
        box(gold, (0.5, D + 0.18, H + 0.14), (sx, 0, Z0 + H / 2 + 0.03), "Gold", corner=0.12, edge=0.08)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(gold, (0.55, 0.55, H + 0.1), (sx * (W / 2 - 0.2), sy * (D / 2 - 0.2), Z0 + H / 2 + 0.02), "Brass", corner=0.14, edge=0.1)
            lump(gold, (sx * (W / 2 - 0.12), sy * (D / 2 - 0.12), ZT + 0.12), (0.2, 0.2, 0.16), "Gold")  # corner studs
    # the gold lock: a plate on the front's top middle, a round lock body, a dark keyhole
    box(gold, (1.15, 0.3, 1.25), (0, -D / 2 - 0.1, ZT - 0.55), "Gold", corner=0.25, edge=0.1)
    lock = bmesh.new()
    cylinder(lock, (0, 0, 0), 0.5, 0.3, 16, direction=(0, -1, 0))
    gold.take(lock, "Brass", Matrix.Translation((0, -D / 2 - 0.2, ZT - 0.75)), bevel=0.06)
    key = bmesh.new()
    cylinder(key, (0, 0, 0), 0.13, 0.08, 8, direction=(0, -1, 0))
    gold.take(key, "Gunmetal", Matrix.Translation((0, -D / 2 - 0.47, ZT - 0.68)))
    box(gold, (0.12, 0.08, 0.3), (0, -D / 2 - 0.51, ZT - 0.86), "Gunmetal", corner=0.04, edge=0.02, seg=1)
    # hinges at the back
    for sx in (-1.55, 1.55):
        hinge = bmesh.new()
        cylinder(hinge, (0, 0, 0), 0.2, 0.7, 10, direction=(1, 0, 0))
        gold.take(hinge, "Brass", Matrix.Translation((sx - 0.35, D / 2 + 0.12, ZT + 0.05)))

    # the carved ice lid, half open: hinged at the back top edge, swung up 42 degrees
    LD, LH, OPEN = D + 0.2, 1.25, math.radians(42)
    lid = Matrix.Translation((0, D / 2 + 0.1, ZT + 0.12)) @ Matrix.Rotation(-OPEN, 4, "X") @ Matrix.Translation((0, -LD / 2, 0))
    dome(ice, W + 0.2, LD, LH, lid, "IceBlue")
    under = bmesh.new()  # the lid's inside: a carved lighter rim round a deep blue middle, a backdrop for the crystals
    rounded_block(under, (W - 0.4, LD - 0.4, 0.12), Matrix.Translation((0, 0, -0.04)), corner=0.25, edge=0.04, corner_seg=2, edge_seg=1)
    ice.take(under, "GlacierBlue", lid)
    under = bmesh.new()
    rounded_block(under, (W - 1.2, LD - 1.2, 0.12), Matrix.Translation((0, 0, -0.1)), corner=0.3, edge=0.04, corner_seg=2, edge_seg=1)
    ice.take(under, "DeepIce", lid)
    for sx in (-1.55, 1.55):
        dome(gold, 0.5, LD + 0.14, LH + 0.08, lid @ Matrix.Translation((sx, 0, -0.01)), "Gold")
    lip = bmesh.new()  # the front lip, gold, with icicles under it
    rounded_block(lip, (W + 0.3, 0.32, 0.34), Matrix(), corner=0.12, edge=0.1, corner_seg=2, edge_seg=2)
    gold.take(lip, "Gold", lid @ Matrix.Translation((0, -LD / 2 + 0.1, 0.12)))
    for sx in (-1, 1):  # frosty ice end caps
        cap = bmesh.new()
        rounded_block(cap, (0.3, LD + 0.1, 0.5), Matrix(), corner=0.12, edge=0.1, corner_seg=2, edge_seg=2)
        ice.take(cap, "FrostLight", lid @ Matrix.Translation((sx * (W / 2 + 0.05), 0, 0.2)))
    for k, lx in enumerate((-1.95, -0.75, 0.45, 1.85)):  # snow and frost on top of the lid, between the gold bands
        t = math.pi * rng.uniform(0.4, 0.6)
        p = lid @ Vector((lx + rng.uniform(-0.2, 0.2), -LD / 2 * math.cos(t), LH * math.sin(t) - 0.12))
        lump(snow, tuple(p), (rng.uniform(0.55, 0.75), rng.uniform(0.9, 1.2), rng.uniform(0.4, 0.5)), "SnowWhite" if k % 2 else "FrostLight", subdivisions=2, rot=rng.uniform(-0.2, 0.2))
    x = -W / 2 + 0.3
    while x < W / 2 - 0.2:  # icicles off the lid's front lip, hanging straight down
        if abs(x) > 0.25:
            base = lid @ Vector((x, -LD / 2 + 0.12, -0.02))
            cone(ice, tuple(base), rng.uniform(0.1, 0.15), rng.uniform(0.35, 0.8), rng.choice(("Diamond", "IceBlue", "FrostLight")))
        x += rng.uniform(0.45, 0.7)

    # the loot: glowing crystals heaped in the chest, peeking out under the lid toward the front; coins
    heap = [(0.0, -0.1, 2.7, 0.5, 14), (-0.95, 0.3, 2.2, 0.44, 8), (1.0, 0.2, 2.3, 0.44, -4), (-1.8, -0.4, 1.6, 0.36, 20),
            (1.8, -0.35, 1.7, 0.36, 18), (-0.5, -0.85, 1.5, 0.34, 32), (0.6, -0.8, 1.55, 0.34, 30), (-1.35, 0.7, 1.4, 0.32, -10),
            (1.4, 0.75, 1.4, 0.32, -12), (0.15, 0.75, 1.8, 0.38, -15), (-1.25, -0.95, 1.1, 0.28, 40), (1.3, -0.95, 1.15, 0.28, 38)]
    for k, (hx, hy, hgt, r, lean) in enumerate(heap):
        side = math.radians(-hx * 11)
        prism(glow, (hx, hy, ZT - 0.2), r, hgt * rng.uniform(0.92, 1.08), ("CrystalCyan", "AuroraCyan", "CrystalCyan", "Diamond")[k % 4],
              lean=(math.radians(lean), side), rot=rng.uniform(0, 1))
    for k in range(7):
        a = rng.uniform(0, 2 * math.pi)
        coin(gold, (rng.uniform(-2.0, 2.0), rng.uniform(-1.2, 0.9), ZT + rng.uniform(0.0, 0.25)), (rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6)))
    for at in ((1.3, -2.25, PZ + 0.07), (1.9, -2.05, PZ + 0.06), (-0.9, -2.3, PZ + 0.07)):  # a few spilled on the plinth
        coin(gold, at, (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15)))

    # the sign post at the front left: a post, a little plank board with a crystal gem, snow on top
    sx, sy = -3.3, -1.85
    post(wood, sx, sy + 0.15, PZ - 0.05, 3.7, 0.2, rng, "PineDark")
    bz = PZ + 2.75
    board = Matrix.Translation((sx, sy, bz)) @ Matrix.Rotation(math.radians(-6), 4, "Y") @ Matrix.Rotation(math.radians(14), 4, "Z")
    for k in range(2):
        b = bmesh.new()
        rounded_block(b, (1.75, 0.28, 0.52), Matrix.Translation((0, 0, (k - 0.5) * 0.56)), corner=0.12, edge=0.08, corner_seg=2, edge_seg=2)
        wood.take(b, ("PineLight", "Pine")[k], board)
    gem = bmesh.new()
    cylinder(gem, (0, 0, 0), 0.34, 0.18, 4, top=0.18, direction=(0, -1, 0))
    crystals.take(gem, "CrystalCyan", board @ Matrix.Translation((0, -0.16, 0)), bevel=0.04)
    for zz in (-0.28, 0.28):  # nail heads
        for xx in (-0.7, 0.7):
            nail = bmesh.new()
            cylinder(nail, (0, 0, 0), 0.07, 0.06, 6, direction=(0, -1, 0))
            wood.take(nail, "Iron", board @ Matrix.Translation((xx, -0.15, zz)))
    lump(snow, tuple(board @ Vector((0, 0.02, 0.6))), (0.95, 0.24, 0.17), subdivisions=2)
    lump(snow, (sx, sy + 0.15, PZ + 3.68), (0.3, 0.3, 0.22), subdivisions=1)
    cone(ice, tuple(board @ Vector((0.45, -0.05, -0.58))), 0.08, 0.35, "Diamond")
    cone(ice, tuple(board @ Vector((-0.5, -0.05, -0.58))), 0.07, 0.25, "IceBlue")

    # snow: heaped on the plinth's corners and along its back, drifts on the ground round its foot
    for sxx, syy in ((-1, 1), (1, 1), (1, -1)):
        lump(snow, (sxx * 3.1, syy * 2.15, PZ + 0.05), (0.85, 0.75, 0.38), subdivisions=2)
    lump(snow, (-2.85, -2.2, PZ + 0.02), (0.55, 0.45, 0.25), subdivisions=2)
    for k in range(4):
        lump(snow, (-2.6 + k * 1.75 + rng.uniform(-0.3, 0.3), 2.25, PZ + 0.03), (0.8, 0.45, 0.26), subdivisions=1)
    for k, (gx, gy) in enumerate(((-2.2, -2.75), (0.4, -2.8), (2.5, -2.7), (3.6, 0.5), (-3.6, 0.8), (-1.0, 2.75), (2.0, 2.75))):
        lump(snow, (gx, gy, 0.0), (rng.uniform(0.9, 1.2), 0.5, rng.uniform(0.35, 0.5)), subdivisions=2, floor=0.0, rot=rng.uniform(-0.3, 0.3) + (math.pi / 2 if abs(gx) > 3.5 else 0))
    # little ice crystal clusters at two corners (not glowing: decoration, like the board's)
    for (cx, cy), side in (((3.45, -2.4), 1), ((-3.45, 2.3), -1)):
        for k in range(3):
            prism(crystals, (cx + side * 0.25 * k, cy + rng.uniform(-0.2, 0.2), 0.15), (0.32, 0.26, 0.22)[k], (1.3, 0.95, 0.7)[k],
                  ("CrystalCyan", "Diamond", "IceBlue")[k], lean=(math.radians(rng.uniform(-15, 5)), math.radians(side * (10 + 18 * k))), rot=rng.uniform(0, 1))
    return [wood, gold, ice, snow, stone, crystals, glow]


# ---------- the codes kiosk ----------

def codes_kiosk(seed):
    rng = random.Random(seed)
    name = "CodesKiosk"
    panel, wood, ice, snow, stone, crystals, gifts = (Part(name + r) for r in ("Panel", "Wood", "Ice", "Snow", "Stone", "Crystals", "Gifts"))
    w, bottom, top = CODES_PANEL["Width"], CODES_PANEL["Bottom"], CODES_TOP
    cz = bottom + CODES_PANEL["Height"] / 2
    front = CODES_PANEL["Front"]

    # the display panel: one flat deep violet slab, its front exactly at CODES_PANEL["Front"]
    depth = 0.5
    box(panel, (w, depth, CODES_PANEL["Height"]), (0, front + depth / 2, cz), "ArcaneDeep", corner=0.1, edge=0.1, seg=1)

    # the carved ice lip round it, then the chunky wooden frame
    LIP, FR = 0.38, 0.8
    lip_f, lip_b = -0.72, 0.45
    ly, ld = (lip_f + lip_b) / 2, lip_b - lip_f
    box(ice, (w + 2 * LIP, ld, LIP), (0, ly, top + LIP / 2), "GlacierBlue", corner=0.14, edge=0.13)
    box(ice, (w + 2 * LIP, ld, LIP), (0, ly, bottom - LIP / 2), "GlacierBlue", corner=0.14, edge=0.13)
    for side in (-1, 1):
        box(ice, (LIP, ld, CODES_PANEL["Height"] + 2 * LIP), (side * (w / 2 + LIP / 2), ly, cz), "IceBlue", corner=0.14, edge=0.13)
    fr_f, fr_b = -1.05, 0.6
    fy, fd = (fr_f + fr_b) / 2, fr_b - fr_f
    inner = w / 2 + LIP
    outer = inner + FR
    ftop = (top + LIP, top + LIP + FR)          # 10.88 .. 11.68
    fbot = (bottom - LIP - FR, bottom - LIP)    # 0.32 .. 1.12
    for zr in (ftop, fbot):
        x = -outer
        k = 0
        while x < outer - 0.3:  # planks of a few lengths, so the frame looks built
            seg = min(rng.uniform(3.6, 5.0), outer - x)
            if outer - x - seg < 1.5:
                seg = outer - x
            h = zr[1] - zr[0]
            box(wood, (seg - 0.08, fd - rng.uniform(0, 0.1), h - 0.05), (x + seg / 2, fy + rng.uniform(-0.03, 0.03), (zr[0] + zr[1]) / 2),
                ("Pine", "PineLight")[k % 2], corner=0.25, edge=0.22, rot=math.radians(rng.uniform(-0.8, 0.8)))
            x += seg
            k += 1
    for side in (-1, 1):
        box(wood, (FR - 0.05, fd - 0.05, ftop[0] - fbot[1] - 0.05), (side * (inner + FR / 2), fy, (ftop[0] + fbot[1]) / 2), "Pine", corner=0.25, edge=0.22)
        # dark pegs at the frame's corners
        for zz in ((fbot[0] + fbot[1]) / 2, (ftop[0] + ftop[1]) / 2):
            peg = bmesh.new()
            cylinder(peg, (0, 0, 0), 0.2, 0.14, 8, direction=(0, -1, 0))
            wood.take(peg, "PineDark", Matrix.Translation((side * (inner + FR / 2), fr_f + 0.02, zz)), bevel=0.04)
    # the snowy ledge under the panel (its snow stays below the panel's bottom edge)
    box(wood, (w + 1.6, 0.75, 0.26), (0, fr_f - 0.3, fbot[1] - 0.12), "PineDark", corner=0.15, edge=0.1)
    for k in range(6):
        x = -w / 2 + 0.6 + k * (w - 1.2) / 5 + rng.uniform(-0.3, 0.3)
        lump(snow, (x, fr_f - 0.38, fbot[1] + 0.02), (rng.uniform(0.8, 1.2), 0.38, rng.uniform(0.18, 0.28)), subdivisions=2)
    # the back board behind the panel, vertical planks and two battens on its back
    box(wood, (2 * outer - 0.2, 0.45, ftop[1] - fbot[0]), (0, 0.4, (ftop[1] + fbot[0]) / 2), "PineDark", corner=0.25, edge=0.15)
    n = 7
    for i in range(n):
        pw = (2 * outer - 0.6) / n
        box(wood, (pw - 0.14, 0.32, ftop[1] - fbot[0] - 0.5), (-(2 * outer - 0.6) / 2 + pw * (i + 0.5), 0.75, (ftop[1] + fbot[0]) / 2), ("Pine", "PineLight")[i % 2], corner=0.1, edge=0.08)
    for z in (2.6, 9.0):
        box(wood, (2 * 7.25, 0.45, 0.9), (0, 1.05, z), "PineDark", corner=0.18, edge=0.14)

    # the posts: chunky logs, the frame set into them, poking up through the roof with snow caps
    PX, PR = 7.25, 0.78
    post_h = 13.3
    for side in (-1, 1):
        log(wood, side * PX, 0.05, post_h, PR, rng)
        lump(snow, (side * PX, 0.05, post_h + 0.1), (PR * 1.4, PR * 1.4, 0.75), subdivisions=2)
        lump(snow, (side * PX + side * 0.12, 0.12, post_h + 0.68), (PR * 0.85, PR * 0.85, 0.55), subdivisions=2)

    # the gable roof: ridge along Y, eaves at the sides
    EX, EZ, RZ = 8.2, 11.2, 14.1   # eave half-width, eave underside height, ridge underside height
    RY0, RY1 = -2.05, 1.85          # roof front and back edge
    ry, rd = (RY0 + RY1) / 2, RY1 - RY0
    slope = math.atan2(RZ - EZ, EX)
    T = 0.5
    length = math.hypot(EX, RZ - EZ) + 0.35

    def under(x):  # the roof's underside height at x
        return RZ - abs(x) * math.tan(slope)

    for side in (-1, 1):
        mid = Vector((side * EX / 2, ry, (RZ + EZ) / 2))
        normal = Vector((side * math.sin(slope), 0, math.cos(slope)))
        c = mid + normal * (T / 2) + Vector((-side * 0.17 * math.cos(slope), 0, 0.17 * math.sin(slope)))
        box(wood, (length, rd, T), tuple(c), "PineDark", corner=0.2, edge=0.18, tilt=(0, side * slope))
        # shingle rows across the top (along Y), alternating colours, each overlapping the one below
        for k in range(7):
            t = (k + 0.5) / 7
            p = Vector((side * EX * (1 - t), ry, EZ + (RZ - EZ) * t)) + normal * (T + 0.08)
            box(wood, (length / 7 + 0.15, rd + 0.12, 0.2), tuple(p), ("Pine", "PineLight")[k % 2], corner=0.12, edge=0.08, tilt=(0, side * slope))
        # snow on the slope: a pillowy slab a little short of the edges, with lumps and a drip over the front
        sn = Vector((side * EX * 0.47, ry - 0.05, EZ + (RZ - EZ) * 0.53)) + normal * (T + 0.35)
        box(snow, (length - 1.3, rd - 0.2, 0.55), tuple(sn), "SnowWhite", corner=0.5, edge=0.26, tilt=(0, side * slope))
        for k in range(4):
            t = 0.15 + 0.22 * k + rng.uniform(-0.04, 0.04)
            p = Vector((side * EX * (1 - t), ry + rng.uniform(-0.6, 0.6), EZ + (RZ - EZ) * t)) + normal * (T + 0.55)
            lump(snow, tuple(p), (rng.uniform(0.9, 1.3), rng.uniform(1.0, 1.5), 0.3), subdivisions=2)
            q = Vector((side * EX * (1 - t + 0.04), RY0 + 0.15, EZ + (RZ - EZ) * (t - 0.04))) + normal * (T + 0.2)
            lump(snow, tuple(q), (0.55, 0.35, 0.42))
        # a thick roll of snow hanging over the slope's front edge
        roll = Vector((side * EX * 0.5, RY0 + 0.3, (RZ + EZ) / 2)) + normal * (T + 0.15)
        box(snow, (length - 0.9, 0.75, 0.6), tuple(roll), "SnowWhite", corner=0.36, edge=0.29, tilt=(0, side * slope))
        # icicles along the front edge of the slope (hanging straight down, all above the panel)
        x = 0.9
        while x < EX - 0.2:
            base = (side * x, RY0 + 0.35, under(x) - 0.02)
            longest = min(1.3, base[2] - top - 0.15) if x < w / 2 + 0.2 else 1.8
            cone(ice, base, rng.uniform(0.12, 0.18), rng.uniform(0.4, max(0.45, longest)), rng.choice(("Diamond", "IceBlue", "FrostLight")))
            x += rng.uniform(0.55, 0.85)
        # crystal clusters on the snow at the eave ends
        base = Vector((side * (EX - 0.9), ry - 0.6, EZ + 0.35 * math.tan(slope) + T + 0.35))
        for k in range(3):
            off = Vector((side * (0.1 + 0.3 * k), rng.uniform(-0.3, 0.3), -0.1 * k))
            prism(crystals, base + off, (0.38, 0.3, 0.26)[k], (1.7, 1.25, 0.9)[k], ("CrystalCyan", "Diamond", "IceBlue")[k],
                  lean=(math.radians(rng.uniform(-10, 10)), math.radians(side * (20 + 15 * k))), rot=rng.uniform(0, 1))
    # the ridge beam, and the gift on top of the ridge's front end
    beam = bmesh.new()
    cylinder(beam, (0, 0, 0), 0.42, rd + 0.3, 12, direction=(0, 1, 0))
    wood.take(beam, "Pine", Matrix.Translation((0, RY0 - 0.15, RZ + T + 0.05)), bevel=0.08)
    lump(snow, (0, ry + 0.4, RZ + T + 0.45), (0.7, 1.3, 0.35), subdivisions=2)
    gift(gifts, (0, RY0 + 0.75, RZ + T + 0.3), (1.25, 1.1, 1.0), "MagicPink", rng, rot=math.radians(8))
    # the gable: horizontal planks filling the triangle under the roof, set back from the roof's front
    gz0 = ftop[1] - 0.05
    gy_f = -0.85
    tri = bmesh.new()  # a dark backing triangle
    pts = [(-(RZ - gz0) / math.tan(slope) + 0.1, gz0), ((RZ - gz0) / math.tan(slope) - 0.1, gz0), (0, RZ - 0.05)]
    loft(tri, [[Vector((x, y, z)) for x, z in pts] for y in (gy_f + 0.2, 0.9)])
    wood.take(tri, "PineDark")
    rows_h = 0.62
    z = gz0
    k = 0
    while z + 0.25 < RZ - 0.2:
        zt = min(z + rows_h, RZ - 0.2)
        half = (RZ - zt) / math.tan(slope) - 0.12
        if half > 0.3:
            box(wood, (2 * half, 0.3, zt - z - 0.08), (0, gy_f + 0.15, (z + zt) / 2), ("PineLight", "Pine")[k % 2], corner=0.12, edge=0.08, seg=2)
        z = zt
        k += 1
    # the gable's medallion: a round ice badge with a little gift on it
    mz = gz0 + 1.25
    disc = bmesh.new()
    cylinder(disc, (0, 0, 0), 1.05, 0.35, 24, direction=(0, -1, 0))
    ice.take(disc, "DeepIce", Matrix.Translation((0, gy_f - 0.05, mz)), bevel=0.08)
    ring = bmesh.new()
    torus(ring, Matrix.Translation((0, gy_f - 0.4, mz)) @ Matrix.Rotation(math.pi / 2, 4, "X"), 1.02, 0.17, 24, 6)
    ice.take(ring, "FrostLight")
    gift(gifts, (0, gy_f - 0.45, mz - 0.5), (0.95, 0.3, 0.8), "RuneViolet", rng)
    # golden tickets tucked into the frame's top corners and one at the bottom right
    ticket(gifts, (-(inner + FR / 2) + 0.05, fr_f - 0.12, ftop[0] - 0.1), math.radians(-28))
    ticket(gifts, (inner + FR / 2 - 0.05, fr_f - 0.12, ftop[0] - 0.05), math.radians(24), swatch="Gold")
    ticket(gifts, (inner + FR / 2 + 0.25, fr_f - 0.12, fbot[1] + 0.3), math.radians(-14), swatch="MagicPink", stripe="Cream")

    # footings: snowy rocks round each post's foot, a chunk of ice, crystals, snow drifts
    for side in (-1, 1):
        fx = side * PX
        for k, (dx, dy, r) in enumerate(((-0.7, -1.1, 0.95), (0.7, -1.0, 0.9), (0.85, 0.6, 0.85), (-0.85, 0.7, 0.85), (side * 0.95, -0.1, 0.75))):
            lump(stone, (fx + dx, dy, 0.25), (r * rng.uniform(0.95, 1.1), r * rng.uniform(0.85, 1.0), r * 0.8),
                 ("Stone", "StoneLight", "StoneDark", "Stone", "StoneLight")[k], rot=rng.uniform(0, 3), floor=0.0)
        lump(snow, (fx, -0.05, 0.9), (1.45, 1.35, 0.5), subdivisions=2, floor=0.0)
        lump(snow, (fx - side * 0.9, -1.1, 0.15), (1.2, 0.9, 0.45), subdivisions=2, floor=0.0)
        box(ice, (1.0, 0.9, 1.0), (fx + side * 1.1, -1.25, 0.45), "IceBlue", corner=0.35, edge=0.3, rot=math.radians(rng.uniform(-20, 20)), tilt=(0.12, 0.1))
        base = Vector((fx + side * 0.3, -1.9, 0.2))
        for k in range(3):
            off = Vector((side * rng.uniform(-0.5, 0.5), rng.uniform(-0.25, 0.25), 0))
            lean = (math.radians(-rng.uniform(10, 28)), math.radians(side * rng.uniform(0, 25)))
            prism(crystals, base + off, rng.uniform(0.28, 0.4), rng.uniform(0.9, 1.6), rng.choice(("CrystalCyan", "IceBlue", "Diamond")), lean=lean, rot=rng.uniform(0, 1))
    for k in range(4):
        x = -w / 2 + 1.5 + k * (w - 3.0) / 3 + rng.uniform(-0.5, 0.5)
        lump(snow, (x, fr_f - 0.6, 0.0), (rng.uniform(1.2, 1.8), 0.65, rng.uniform(0.4, 0.6)), floor=0.0)
    return [panel, wood, ice, snow, stone, crystals, gifts]


# ---------- renders (preview only: never exported) ----------

def preview_setup():
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.view_settings.view_transform = "Standard"
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
    sun.rotation_euler = Vector((0.45, 0.65, -0.75)).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(sun)
    ground = Part("PreviewGround")
    gbm = bmesh.new()
    rounded_block(gbm, (120, 120, 0.4), Matrix.Translation((0, 0, -0.22)), corner=1, edge=0.1, corner_seg=1, edge_seg=1)
    ground.take(gbm, "SnowWhite")
    ground.finish(scene.collection, materials)
    cam = bpy.data.objects.new("ShotCamera", bpy.data.cameras.new("ShotCamera"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 900, 900, 100
    return cam


def preview_text(coll, body, size, at):
    """Stand-in GUI text (unlit white, as PlazaService draws it), in the model's collection but never exported."""
    curve = bpy.data.curves.new("PreviewText", "FONT")
    curve.body = body
    curve.size = size
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.extrude = 0.01
    t = bpy.data.objects.new("PreviewText", curve)
    t.location = at
    t.rotation_euler = (math.pi / 2, 0, 0)
    coll.objects.link(t)
    mat = bpy.data.materials.new("PreviewTextMat")
    if mat.node_tree is None:
        mat.use_nodes = True
    b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    b.inputs["Emission Strength"].default_value = 1.0
    curve.materials.append(mat)


def render_model(cam, name, views, out_dir):
    scene = bpy.context.scene
    os.makedirs(out_dir, exist_ok=True)
    for view, (eye, target, lens) in views.items():
        cam.data.lens = lens
        cam.location = Vector(eye)
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(out_dir, "%s_%s.png" % (name, view))
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)


VIEWS = {
    "DailyChestStand": {
        "front": ((0, -24, 3.6), (0, 0, 3.6), 50),
        "three_quarter": ((-14, -17, 9), (0, 0, 3.2), 50),
        "eye_25": ((0, -25, 5), (0, 0, 3.4), 35),
        "eye_25_side": ((-12, -22, 5), (0, 0, 3.4), 35),
        "back": ((12, 16, 8), (0, 0, 3.2), 50),
    },
    "CodesKiosk": {
        "front": ((0, -45, 8), (0, 0, 8), 50),
        "three_quarter": ((-26, -32, 15), (0, 0, 7.5), 45),
        "eye_25": ((0, -25, 5), (0, 0, 8), 30),
        "eye_25_side": ((-13, -21.5, 5), (0, 0, 8), 30),
        "back": ((20, 32, 13), (0, 0, 7.5), 45),
    },
}


# ---------- build, check, export ----------

image = bpy.data.images.get("BuildingPalette") or bpy.data.images.load(os.path.join(REPO, "assets", "textures", "BuildingPalette.png"))
image.name = "BuildingPalette"
materials = palette_materials(image)
cam = preview_setup() if RENDER else None
manifest = read_manifest()
problems = []
os.makedirs(OUT, exist_ok=True)
for name, build in (("DailyChestStand", lambda: daily_chest(7)), ("CodesKiosk", lambda: codes_kiosk(11))):
    coll = begin("Plaza" + name)
    objs = [p.finish(coll, materials) for p in build()]
    lo, hi = bounds(objs)
    info = {"meshes": {o.name: tris_of(o) for o in objs}, "size": [round(hi.x - lo.x, 2), round(hi.z - lo.z, 2), round(hi.y - lo.y, 2)],
            "top": round(hi.z, 2), "bounds": {"x": [round(lo.x, 2), round(hi.x, 2)], "y": [round(lo.y, 2), round(hi.y, 2)], "z": [round(lo.z, 2), round(hi.z, 2)]}}
    info["triangles"] = sum(info["meshes"].values())
    if name == "CodesKiosk":
        panel = next(o for o in objs if o.name.endswith("Panel"))
        plo, phi = bounds([panel])
        info["panel"] = {"front": round(plo.y, 3), "width": round(phi.x - plo.x, 3), "bottom": round(plo.z, 3), "top": round(phi.z, 3)}
        if abs(plo.y - CODES_PANEL["Front"]) > 1e-3 or abs(plo.z - CODES_PANEL["Bottom"]) > 1e-3 or abs(phi.z - CODES_TOP) > 1e-3:
            problems.append("CodesKiosk panel is off: %s" % info["panel"])
        for o in objs:  # nothing may stand in front of the panel's face inside its rectangle
            if o is panel:
                continue
            for v in o.data.vertices:
                p = o.matrix_world @ v.co
                if abs(p.x) < CODES_PANEL["Width"] / 2 - 0.05 and CODES_PANEL["Bottom"] + 0.05 < p.z < CODES_TOP - 0.05 and p.y < CODES_PANEL["Front"]:
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
        if name == "CodesKiosk":
            preview_text(coll, "CODES", 3.6, (0, -0.5, (CODES_PANEL["Bottom"] + CODES_TOP) / 2 - 0.4))
        render_model(cam, name, VIEWS[name], os.path.join(OUT, "render"))
with open(os.path.join(OUT, "plaza_manifest.json"), "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=1, sort_keys=True)
for p in problems:
    print("PROBLEM:", p)
print("PLAZA_PROPS_DONE", "problems:", len(problems))
