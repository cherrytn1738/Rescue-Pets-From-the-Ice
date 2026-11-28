# tools_tiers.py - the player's tools (docs/GAME_DESIGN.md, "Tools"): 18 tiers in five families (Pick, Hammer,
# Axe, Sword, Spear: the Ice Drill is a spear), on the building kit (same palette texture, bevels, weighted
# normals, glow meshes). About 20% bigger in the hand than the old ice picks (3.5 studs): picks and axes 4.2,
# hammers 4.0 with a chunkier head, swords 4.6 (the Starbreaker 4.8), the drill 4.2, spears 4.8.
#   blender -b --factory-startup --python tools/blender/tools_tiers.py
# or in the Blender MCP: REPO = r"..."; ONLY_TIERS = (4, 7); exec(open(REPO + r"\tools\blender\tools_tiers.py").read())
# Writes store-assets/tools/: Tools_sheet.png (the tools built, with the 3-stud pet and the 5.5-stud avatar),
# Tools_manifest.json (meshes, triangles, attachments; entries for tiers not rebuilt are kept), fbx/Tool_T<n>.fbx.
#
# Every tool: the handle along +Z from its butt (z = 0); the striking side toward +X (Roblox -X: the families' grips
# in SwingConfig turn it into the swing). Meshes: Tool<T>Handle, Tool<T>Head (or Blade), Tool<T>Bit (a drill's bit,
# its own mesh, round its axis: it spins), "...Glow" for glowing pieces. Attachments: Grip (where the hand holds
# it), Tip (the striking point), TrailA and TrailB (a swing trail runs between them), Bit (a drill bit's spin axis).
# Tiers 1-10 are real materials (no glow); tiers 11-18 are magical: their "magic" key adds glowing pieces (Neon in
# game), and the game adds their light, trail and hit effect (IceLooks.ToolMagic).
import os, sys, math, json
if "REPO" not in globals():
    REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILDING = "Tools"
exec(open(os.path.join(REPO, "tools", "blender", "buildings", "framework.py"), encoding="utf-8").read())

ONLY_TIERS = globals().get("ONLY_TIERS")  # e.g. (4, 7): just these (the rest of the manifest is kept)
EXPORT = globals().get("EXPORT", True)

# tier: name, family, looks (palette swatches) and shape options (each builder's defaults are the approved samples:
# the Iron Pick, Gold Hammer, Crystal Axe, Ice Drill and Diamond Sword)
TOOLS = {
    1: dict(name="Wooden Pick", family="Pick", wood="Pine", wrap="PineLight", band="PineDark", head="PineDark", edge="StoneLight",
            collar="PineLight", lash=True, rivet="PineLight", bend=0.62),
    2: dict(name="Stone Hammer", family="Hammer", wood="Pine", wrap="PineLight", band="PineDark", head="Stone", face="StoneLight",
            ring="PineLight", shape="stone"),
    3: dict(name="Copper Axe", family="Axe", wood="Pine", wrap="Rubber", band="Copper", blade="Copper", edge="PineLight", socket="Copper",
            back="poll"),
    4: dict(name="Iron Pick", family="Pick", wood="PineDark", wrap="Rubber", band="Iron", head="Iron", edge="SteelLight", collar="SteelLight"),
    5: dict(name="Steel Sword", family="Sword", wrap="Rubber", band="Steel", blade="SteelLight", ridge="Steel", guard="Steel", gem=None,
            curls=False, pommel_gem=False),
    6: dict(name="Frost Spear", family="Spear", wood="NavyIce", wrap="Rubber", band="SteelLight", head="IceBlue", edge="Diamond",
            socket="SteelLight", frost="FrostLight"),
    7: dict(name="Gold Hammer", family="Hammer", wood="PineDark", wrap="Rubber", band="Brass", head="Gold", face="Brass", ring="Brass", gem="WarnRed"),
    8: dict(name="Crystal Axe", family="Axe", wood="NavyIce", wrap="Rubber", band="SteelLight", blade="CrystalCyan", edge="Diamond", socket="SteelLight"),
    9: dict(name="Ice Drill", family="Drill", wrap="Rubber", core="SteelDark", body="IceBlue", cap="SteelLight", bit="SteelLight", tip="Diamond", stripe="SnowWhite"),
    10: dict(name="Diamond Sword", family="Sword", wrap="NavyIce", band="Gold", blade="Diamond", ridge="AuroraCyan", guard="Gold", gem="AuroraCyan"),
    # the magical tiers
    11: dict(name="Flame Pick", family="Pick", wood="Gunmetal", wrap="Rubber", band="Copper", head="Iron", edge="FlameOrange", collar="Gunmetal",
             magic="flame", glow_edge=True),
    12: dict(name="Thunder Hammer", family="Hammer", wood="Gunmetal", wrap="Rubber", band="SteelLight", head="SteelDark", face="SteelLight",
             ring="LampYellow", gem=None, magic="thunder"),
    13: dict(name="Aurora Blade", family="Sword", wrap="ArcaneDeep", band="Moonstone", blade="AuroraCyan", ridge="AuroraGreen", guard="Moonstone",
             gem="AuroraViolet", magic="aurora"),
    14: dict(name="Lava Axe", family="Axe", wood="Gunmetal", wrap="Rubber", band="Iron", blade="Gunmetal", edge="FlameOrange", socket="Iron",
             magic="lava", back="blade"),
    15: dict(name="Starfall Spear", family="Spear", wood="ArcaneDeep", wrap="Rubber", band="Gold", head="Moonstone", edge="LampYellow",
             socket="Gold", magic="star"),
    16: dict(name="Comet Hammer", family="Hammer", wood="ArcaneDeep", wrap="Rubber", band="Moonstone", head="ArcaneDeep", face="CrystalCyan",
             ring="Moonstone", gem="CrystalCyan", magic="comet"),
    17: dict(name="Cosmic Pick", family="Pick", wood="ArcaneDeep", wrap="Rubber", band="RuneViolet", head="ArcaneDeep", edge="RuneGlow",
             collar="RuneViolet", magic="cosmic", glow_edge=True),
    18: dict(name="Starbreaker", family="Sword", wrap="Gunmetal", band="Gold", blade="ArcaneDeep", ridge="LampYellow", guard="Gold",
             gem=None, magic="starbreaker", length=4.8, width=1.2),
}


def ring(z, radius, minor, swatch, tilt=0.0, segments=14, glow=False):
    bm = bmesh.new()
    torus(bm, M((0, 0, z), (tilt, 0, 0)), radius, minor, segments, 4)
    return (bm, swatch, 0.0, glow)


def shaft(b, top, radius, wood, wrap, band, grip=(0.25, 1.15), bands=(), wraps=6, pommel=None, glow=False):
    """The handle: a slightly waisted shaft from z = 0 to top, wrapped grip, trim bands, a pommel."""
    bm = bmesh.new()
    lathe(bm, [(0, 0.06), (radius * 0.9, 0.06), (radius, 0.35), (radius * 0.86, top * 0.55), (radius * 0.95, top - 0.35),
               (radius * 1.04, top), (0, top)], 14)
    b.add("Handle", [(bm, wood, 0.0, False)])
    p = bmesh.new()
    lathe(p, [(0, -0.04), (radius * 1.2, -0.04), (radius * 1.38, 0.08), (radius * 1.2, 0.2), (0, 0.2)], 14)
    b.add("Handle", [(p, pommel or band, 0.0, False)])
    step = (grip[1] - grip[0]) / max(1, wraps - 1)
    for k in range(wraps):
        b.add("Handle", [ring(grip[0] + k * step, radius * 1.02, 0.05, wrap, 0.22)])
    for z in bands:
        b.add("Handle", [ring(z, radius * 1.05, 0.045, band, 0.0, 16)])


def star_points(centre, normal, outer, inner, points=4, depth=0.12, swatch="Gold", glow=False, spin=0.0):
    """A flat faceted star facing `normal`: `points` diamond rays from the centre (a 4-point star by default)."""
    pieces = []
    m = frame(centre, out=normal)
    for k in range(points):
        a = spin + 2 * math.pi * k / points
        ray = bmesh.new()
        tip = Vector((outer * math.cos(a), outer * math.sin(a), 0))
        side = Vector((-math.sin(a), math.cos(a), 0)) * inner
        verts = [ray.verts.new(v) for v in (Vector((0, 0, depth)), side, tip, -side, Vector((0, 0, -depth)))]
        top, s1, t, s2, bot = verts
        for f in ((top, s1, t), (top, t, s2), (bot, t, s1), (bot, s2, t)):
            ray.faces.new(f)
        bmesh.ops.recalc_face_normals(ray, faces=ray.faces)
        ray.transform(m)
        pieces.append((faceted(ray), swatch, 0.0, glow))
    return pieces


def zigzag(points, radius, swatch, glow=True):
    """A crack or a lightning bolt: a thin tube through (x, y, z) points."""
    bm = bmesh.new()
    sweep(bm, [Vector(p) for p in points], radius, 6, radius_end=radius * 0.5)
    return (bm, swatch, 0.0, glow)


def pick(b, t, look):
    length = 4.2
    top = length - 0.42
    shaft(b, top + 0.1, 0.17, look["wood"], look["wrap"], look["band"], grip=(0.28, 1.2), bands=(1.45, length * 0.62, top - 0.45))
    pieces = []
    bend = look.get("bend", 0.5)
    glow_edge = look.get("glow_edge", False)
    for side in (-1, 1):  # the double-ended head: a thick middle tapering to two curved points
        points = [Vector((side * (0.14 + 1.24 * s), 0, top - bend * s * s)) for s in [k / 8 for k in range(9)]]
        arm = bmesh.new()
        sweep(arm, points[:7], 0.27, 12, radius_end=0.11)
        pieces.append((arm, look["head"], 0.0, False))
        point = bmesh.new()  # the bright steel point
        sweep(point, points[6:], 0.11, 12, radius_end=0.025)
        pieces.append((point, look["edge"], 0.0, glow_edge))
    if look.get("lash"):  # a wooden head lashed on with rope, crossed over where the handle goes through
        for x, lean in ((-0.24, 0.0), (-0.1, 0.35), (0.1, -0.35), (0.24, 0.0)):
            lash = bmesh.new()
            torus(lash, M((x, 0, top), (0, math.pi / 2, lean)), 0.3, 0.055, 12, 4)
            pieces.append((lash, look["collar"], 0.0, False))
    else:
        collar = bmesh.new()
        rounded_block(collar, (0.58, 0.48, 0.66), M((0, 0, top)), corner=0.12, edge=0.08, corner_seg=2, edge_seg=2)
        pieces.append((collar, look["collar"], 0.0, False))
        for sx in (-1, 1):
            for sy in (-1, 1):
                pieces += place(rivet(0.07, look.get("rivet", "SteelDark")), frame((sx * 0.16, sy * 0.24, top + 0.12), out=(0, sy, 0)))
    magic = look.get("magic")
    if magic == "flame":  # a flame burning on top of the head, and glowing cracks along both sides of both arms
        pieces += place(flame(0.2, 0.75), M((0, 0, top + 0.3)))
        for side in (-1, 1):
            for sy in (-1, 1):
                crack = []
                for k, s in enumerate((0.16, 0.3, 0.44, 0.58)):
                    r = 0.27 - 0.16 * s / 0.75  # the arm's radius there
                    crack.append((side * (0.14 + 1.24 * s), sy * (r - 0.01), top - bend * s * s + (0.06 if k % 2 else -0.05)))
                pieces.append(zigzag(crack, 0.035, "FlameYellow"))
    elif magic == "cosmic":  # a glowing orbit ring round the head, with small stars riding it, and a star gem
        pieces += place([ring(0.0, 0.62, 0.035, "RuneGlow", 0.0, 24, glow=True)], M((0, 0, top), (math.radians(70), 0, math.radians(20))))
        orbit = M((0, 0, top), (math.radians(70), 0, math.radians(20)))
        for k, a in enumerate((0.4, 2.5, 4.4)):
            pieces += star_points(orbit @ Vector((0.62 * math.cos(a), 0.62 * math.sin(a), 0)), (0, -1, 0), 0.16, 0.05, 4, 0.04, "Moonstone", True, spin=k)
        for sy in (-1, 1):
            pieces += place(gem_setting(0.13, "MagicPink", look["collar"], 4), frame((0, sy * 0.25, top), out=(0, sy, 0)))
    b.add("Head", pieces)
    tip = Vector((1.38, 0, top - bend))
    return {"Grip": frame((0, 0, 0.7)), "Tip": frame(tip, out=(0.86, 0, -0.51)),
            "TrailA": frame((0.3, 0, top)), "TrailB": frame(tip)}


def hammer(b, t, look):
    length = 4.0
    top = length - 0.5
    shaft(b, top + 0.1, 0.18, look["wood"], look["wrap"], look["band"], grip=(0.28, 1.2), bands=(1.45, length * 0.6))
    pieces = []
    shape = look.get("shape", "barrel")
    magic = look.get("magic")
    if shape == "stone":  # a rough stone block lashed on with rope
        body = bmesh.new()
        rounded_block(body, (1.84, 0.9, 0.98), M((0, 0, top)), corner=0.34, edge=0.22, corner_seg=2, edge_seg=1)
        for v in body.verts:  # knock the block about a little: a hand-shaped stone
            v.co.x += 0.05 * math.sin(v.co.z * 7 + v.co.y * 3)
            v.co.z += 0.04 * math.sin(v.co.x * 5)
        pieces.append((faceted(body), look["head"], 0.0, False))
        for side in (-1, 1):
            face = bmesh.new()
            rounded_block(face, (0.16, 0.74, 0.8), M((side * 0.9, 0, top)), corner=0.12, edge=0.06, corner_seg=1, edge_seg=1)
            pieces.append((faceted(face), look["face"], 0.0, False))
        for x in (-0.24, 0.0, 0.24):  # the rope lashing round the head, where the handle goes through
            lash = bmesh.new()
            torus(lash, M((x, 0, top), (0, math.pi / 2, 0)), 0.55, 0.07, 12, 4)
            pieces.append((lash, look["ring"], 0.0, False))
    else:
        body = bmesh.new()  # the chunky head, a barrel across X with flared striking faces
        lathe(body, [(0, -0.92), (0.47, -0.92), (0.53, -0.83), (0.47, -0.68), (0.41, -0.36), (0.39, 0.0), (0.41, 0.36), (0.47, 0.68),
                     (0.53, 0.83), (0.47, 0.92), (0, 0.92)], 20, M((0, 0, top), (0, math.pi / 2, 0)))
        pieces.append((body, look["head"], 0.0, False))
        for side in (-1, 1):
            face = bmesh.new()
            cylinder(face, (side * 0.92, 0, top), 0.45, 0.12 * side, 20, direction=(1, 0, 0))
            pieces.append((face, look["face"], 0.03, magic == "comet" and side == 1))
            r = bmesh.new()
            torus(r, M((side * 0.57, 0, top), (0, math.pi / 2, 0)), 0.43, 0.065, 20, 5)
            pieces.append((r, look["ring"], 0.0, magic == "thunder"))
        socket = bmesh.new()
        rounded_block(socket, (0.5, 0.62, 1.12), M((0, 0, top)), corner=0.14, edge=0.1, corner_seg=2, edge_seg=2)
        pieces.append((socket, look["ring"] if magic != "thunder" else look["band"], 0.0, False))
        if look.get("gem"):
            for sy in (-1, 1):
                pieces += place(gem_setting(0.15, look["gem"], look["ring"] if magic != "thunder" else look["band"], 4),
                                frame((0, sy * 0.31, top), out=(0, sy, 0)))
    if magic == "thunder":  # lightning bolts on both sides of the barrel, hugging it
        def barrel(x):  # the barrel's radius along it (its lathe profile)
            x = abs(x)
            return 0.39 + 0.02 * min(1, x / 0.36) + 0.06 * max(0, min(1, (x - 0.36) / 0.32))
        for sy in (-1, 1):
            bolt = [(x, 0, dz) for x, dz in ((-0.72, 0.16), (-0.36, -0.1), (-0.06, 0.14), (0.3, -0.12), (0.7, 0.1))]
            points = []
            for x, _, dz in bolt:
                r = barrel(x) + 0.02
                y = math.sqrt(max(0.0, r * r - dz * dz))
                points.append((x, sy * y, top + dz))
            pieces.append(zigzag(points, 0.05, "LampYellow"))
    elif magic == "comet":  # the comet: its glowing face up front, a swept tail of glowing fins behind
        for k, (dz, dy) in enumerate(((0.0, 0.0), (0.28, 0.18), (-0.28, -0.18), (0.22, -0.26), (-0.22, 0.26))):
            fin = bmesh.new()
            sweep(fin, [Vector((-0.95, dy * 0.6, top + dz * 0.6)), Vector((-1.25, dy, top + dz)), Vector((-1.55 - 0.1 * (k == 0), dy * 1.3, top + dz * 1.3))],
                  0.16 if k == 0 else 0.1, 8, radius_end=0.02)
            pieces.append((fin, "CrystalCyan" if k == 0 else "AuroraCyan", 0.0, True))
    b.add("Head", pieces)
    return {"Grip": frame((0, 0, 0.7)), "Tip": frame((1.04, 0, top), out=(1, 0, 0)),
            "TrailA": frame((0.5, 0, top)), "TrailB": frame((1.04, 0, top))}


def slab(outline, thickness_at, swatch, edge_y=0.0, glow=False):
    """A flat blade from an outline in the XZ plane (convex, counter-clockwise), thickness per point; faceted."""
    bm = bmesh.new()
    front = [bm.verts.new((x, -thickness_at(x, z) / 2 - edge_y, z)) for x, z in outline]
    back = [bm.verts.new((x, thickness_at(x, z) / 2 + edge_y, z)) for x, z in outline]
    n = len(outline)
    bm.faces.new(front[::-1])
    bm.faces.new(back)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return (faceted(bm), swatch, 0.0, glow)


def mirror_x(piece):
    bm = piece[0]
    bm.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    return piece


def axe(b, t, look):
    length = 4.2
    top = length - 0.45
    shaft(b, top + 0.15, 0.17, look["wood"], look["wrap"], look["band"], grip=(0.28, 1.2), bands=(1.45, length * 0.62))
    pieces = []
    head_z = top - 0.25
    magic = look.get("magic")
    # the blade: a fan from the socket to a curved edge, thick at the spine, thin at the edge
    edge = [(1.36 + 0.22 * math.sin(math.pi * k / 10), head_z - 0.86 + 1.72 * k / 10 + 0.12 * math.sin(math.pi * k / 10)) for k in range(11)]
    outline = [(0.24, head_z - 0.3)] + edge + [(0.24, head_z + 0.42)]
    outline = [(x, z) for x, z in outline]
    # counter-clockwise seen from -Y: bottom-left, along the edge upward, top-left
    pieces.append(slab(outline, lambda x, z: 0.32 - 0.24 * min(1, max(0, (x - 0.24) / 1.3)), look["blade"]))
    # the bright cut edge: a thin facet band along the curve
    inner = [(x - 0.2, z) for x, z in reversed(edge)]
    band = edge + inner
    pieces.append(slab(band, lambda x, z: 0.08, look["edge"], edge_y=0.012, glow=magic == "lava"))
    socket = bmesh.new()
    rounded_block(socket, (0.52, 0.5, 1.05), M((0, 0, head_z + 0.05)), corner=0.13, edge=0.09, corner_seg=2, edge_seg=2)
    pieces.append((socket, look["socket"], 0.0, False))
    for z in (head_z - 0.38, head_z + 0.48):
        pieces.append(ring(z, 0.27, 0.05, look["band"], 0.0, 16))
    back = look.get("back", "spike")
    if back == "spike":
        spike = cut_crystal(0.62, 0.17, look["blade"], tilt=(0, 0), sides=6, glow=False)  # a crystal spike out the back
        pieces += place(spike, frame((-0.2, 0, head_z + 0.05), out=(-1, 0, 0.15)))
    elif back == "poll":  # a flat hammer poll out the back
        poll = bmesh.new()
        rounded_block(poll, (0.42, 0.42, 0.5), M((-0.38, 0, head_z + 0.05)), corner=0.1, edge=0.06, corner_seg=2, edge_seg=1)
        pieces.append((poll, look["blade"], 0.0, False))
    elif back == "blade":  # a double-bit axe: a smaller blade out the back
        small = [(0.24 + (x - 0.24) * 0.62, head_z + (z - head_z) * 0.7) for x, z in outline]
        pieces.append(mirror_x(slab(small, lambda x, z: 0.3 - 0.22 * min(1, max(0, (x - 0.24) / 0.8)), look["blade"])))
        small_edge = [(0.24 + (x - 0.24) * 0.62, head_z + (z - head_z) * 0.7) for x, z in edge]
        small_band = small_edge + [(x - 0.14, z) for x, z in reversed(small_edge)]
        pieces.append(mirror_x(slab(small_band, lambda x, z: 0.07, look["edge"], edge_y=0.012, glow=magic == "lava")))
    if magic == "lava":  # glowing cracks of lava across both faces of the blade
        for sy in (-1, 1):
            for crack in ([(0.4, head_z + 0.2), (0.7, head_z + 0.05), (0.95, head_z + 0.28), (1.25, head_z + 0.12)],
                          [(0.45, head_z - 0.15), (0.75, head_z - 0.32), (1.05, head_z - 0.2), (1.3, head_z - 0.45)]):
                pieces.append(zigzag([(x, sy * (0.32 - 0.24 * min(1, max(0, (x - 0.24) / 1.3))) / 2 * 1.04, z) for x, z in crack], 0.032, "FlameYellow"))
    b.add("Head", pieces)
    tip = Vector((1.58, 0, head_z))
    return {"Grip": frame((0, 0, 0.7)), "Tip": frame(tip, out=(1, 0, 0)),
            "TrailA": frame((0.4, 0, head_z)), "TrailB": frame(tip)}


def loft_rhombus(sections, swatch, glow=False):
    """A faceted rhombus-section solid along Z: sections of (z, half width along X, half thickness along Y)."""
    bm = bmesh.new()
    loops = []
    for z, w, th in sections:
        loops.append([Vector((w, 0, z)), Vector((0, th, z)), Vector((-w, 0, z)), Vector((0, -th, z))])
    loft(bm, loops)
    return (faceted(bm), swatch, 0.0, glow)


def sword(b, t, look):
    length = look.get("length", 4.6)
    big = look.get("width", 1.0)  # the Starbreaker's blade is longer and wider
    guard_z = 1.12
    magic = look.get("magic")
    # grip and pommel
    g = bmesh.new()
    lathe(g, [(0, 0.12), (0.15, 0.12), (0.16, 0.5), (0.15, guard_z - 0.05), (0, guard_z - 0.05)], 14)
    b.add("Handle", [(g, look["wrap"], 0.0, False)])
    for k in range(5):
        b.add("Handle", [ring(0.24 + k * 0.18, 0.155, 0.035, look["band"], 0.25)])
    pommel = bmesh.new()
    lathe(pommel, [(0, -0.02), (0.2, -0.02), (0.24, 0.07), (0.2, 0.16), (0, 0.16)], 14)
    b.add("Handle", [(pommel, look["band"], 0.0, False)])
    if look.get("pommel_gem", True):
        b.add("Handle", place(cut_gem(0.14, look["blade"], glow=magic is not None), M((0, 0, -0.05), (math.pi, 0, 0))))
    # the crossguard with curled ends and a gem on each face
    guard = []
    bar = bmesh.new()
    rounded_block(bar, (1.4, 0.34, 0.26), M((0, 0, guard_z)), corner=0.12, edge=0.09, corner_seg=2, edge_seg=2)
    guard.append((bar, look["guard"], 0.0, False))
    if look.get("curls", True):
        for side in (-1, 1):
            curl = bmesh.new()
            sweep(curl, [Vector((side * (0.62 + 0.12 * math.sin(a)), 0, guard_z + 0.12 * (1 - math.cos(a)))) for a in [k * 0.45 for k in range(6)]], 0.11, 10, radius_end=0.07)
            guard.append((curl, look["guard"], 0.0, False))
    else:  # plain square quillon ends
        for side in (-1, 1):
            end = bmesh.new()
            rounded_block(end, (0.16, 0.4, 0.36), M((side * 0.72, 0, guard_z)), corner=0.06, edge=0.04, corner_seg=1, edge_seg=1)
            guard.append((end, look["guard"], 0.0, False))
    if look.get("gem"):
        for sy in (-1, 1):
            guard += place(gem_setting(0.11, look["gem"], look["guard"], 4), frame((0, sy * 0.17, guard_z), out=(0, sy, 0)))
    if magic == "aurora":  # swept wings rising from the guard, like aurora curtains
        for side in (-1, 1):
            wing = bmesh.new()
            sweep(wing, [Vector((side * 0.45, 0, guard_z + 0.05)), Vector((side * 0.62, 0, guard_z + 0.35)), Vector((side * 0.58, 0, guard_z + 0.7))],
                  0.09, 8, radius_end=0.02)
            guard.append((wing, "AuroraViolet", 0.0, True))
    elif magic == "starbreaker":  # a gold four-point star round the guard, a glowing star at its heart
        for sy in (-1, 1):
            guard += star_points((0, sy * 0.2, guard_z + 0.05), (0, sy, 0), 0.62, 0.13, 4, 0.06, look["guard"], False, spin=math.pi / 4)
            guard += star_points((0, sy * 0.27, guard_z + 0.05), (0, sy, 0), 0.3, 0.08, 4, 0.04, "LampYellow", True)
    b.add("Head", guard)
    # the blade: a faceted diamond blade, its edges toward +X and -X, with a raised ridge down the middle
    z0 = guard_z + 0.12
    blade = [(z0, 0.34 * big, 0.13), (z0 + 0.7, 0.37 * big, 0.13), (length - 1.2, 0.33 * big, 0.115), (length - 0.55, 0.25 * big, 0.09), (length, 0.0, 0.0)]
    b.add("Blade", [loft_rhombus(blade, look["blade"])])
    ridge = [(z0 + 0.05, 0.11, 0.145), (length - 1.0, 0.09, 0.128), (length - 0.5, 0.0, 0.098)]
    b.add("Blade", [loft_rhombus(ridge, look["ridge"], glow=magic in ("aurora", "starbreaker"))])
    if magic == "starbreaker":  # star gems set down the blade
        for k, z in enumerate((z0 + 0.6, z0 + 1.35, z0 + 2.1)):
            for sy in (-1, 1):
                b.add("Blade", star_points((0, sy * 0.15, z), (0, sy, 0), 0.14 - 0.02 * k, 0.045, 4, 0.03, "Moonstone", True))
    tip_z = length - 1.0
    return {"Grip": frame((0, 0, 0.62)), "Tip": frame((0.33 * big, 0, tip_z), out=(1, 0, 0)),
            "TrailA": frame((0, 0, z0 + 0.4)), "TrailB": frame((0, 0, length - 0.05))}


def spear(b, t, look):
    """A spear held like the drill: the grip at the back, a long shaft, the head pointing along +Z."""
    length = 4.8
    socket_z = length - 1.8
    magic = look.get("magic")
    shaft(b, socket_z + 0.05, 0.15, look["wood"], look["wrap"], look["band"], grip=(0.3, 1.25), bands=(1.5, 2.55))
    pieces = []
    socket = bmesh.new()
    lathe(socket, [(0, socket_z - 0.05), (0.2, socket_z - 0.05), (0.23, socket_z + 0.1), (0.17, socket_z + 0.34), (0.11, socket_z + 0.42),
                   (0, socket_z + 0.42)], 14)
    pieces.append((socket, look["socket"], 0.0, False))
    pieces.append(ring(socket_z + 0.04, 0.22, 0.05, look["band"], 0.0, 14))
    # the head: a long faceted leaf blade with a bright cutting edge and a raised spine
    h0 = socket_z + 0.38
    head = [(h0, 0.1, 0.09), (h0 + 0.32, 0.3, 0.1), (h0 + 0.75, 0.3, 0.095), (length - 0.32, 0.17, 0.07), (length, 0.0, 0.0)]
    pieces.append(loft_rhombus(head, look["head"]))
    spine = [(h0 + 0.05, 0.08, 0.125), (length - 0.4, 0.06, 0.095), (length - 0.1, 0.0, 0.035)]
    pieces.append(loft_rhombus(spine, look["edge"], glow=magic == "star"))
    if look.get("frost"):  # frost crystals round the socket
        for k in range(5):
            a = 2 * math.pi * k / 5 + 0.3
            pieces += place(cut_crystal(0.42 - 0.06 * (k % 2), 0.08, look["frost"], sides=5, glow=False),
                            frame((0.16 * math.cos(a), 0.16 * math.sin(a), socket_z + 0.12), out=(math.cos(a), math.sin(a), 1.4)))
    if magic == "star":  # a star blazing where the head meets the socket, and two wings below it
        for sy in (-1, 1):
            pieces += star_points((0, sy * 0.13, h0 + 0.05), (0, sy, 0), 0.5, 0.11, 4, 0.05, "Gold", False, spin=math.pi / 4)
            pieces += star_points((0, sy * 0.19, h0 + 0.05), (0, sy, 0), 0.24, 0.07, 4, 0.035, "LampYellow", True)
        for side in (-1, 1):
            wing = bmesh.new()
            sweep(wing, [Vector((side * 0.15, 0, socket_z + 0.1)), Vector((side * 0.42, 0, socket_z - 0.05)), Vector((side * 0.55, 0, socket_z - 0.32))],
                  0.07, 8, radius_end=0.02)
            pieces.append((wing, "Moonstone", 0.0, True))
    b.add("Head", pieces)
    return {"Grip": frame((0, 0, 0.75)), "Tip": frame((0, 0, length), out=(0, 0, 1)),
            "TrailA": frame((0, 0, h0)), "TrailB": frame((0, 0, length))}


def drill(b, t, look):
    """A hand ice drill held like a spear: a rear grip, the motor housing, and a two-flute bit that spins."""
    length = 4.2
    grip = bmesh.new()
    lathe(grip, [(0, 0.06), (0.17, 0.06), (0.18, 0.35), (0.17, 1.3), (0.2, 1.42), (0, 1.42)], 14)
    b.add("Handle", [(grip, look["core"], 0.0, False)])
    knob = bmesh.new()
    lathe(knob, [(0, -0.05), (0.22, -0.05), (0.26, 0.07), (0.22, 0.2), (0, 0.2)], 14)
    b.add("Handle", [(knob, look["cap"], 0.0, False)])
    for k in range(6):
        b.add("Handle", [ring(0.3 + k * 0.18, 0.175, 0.05, look["wrap"], 0.22)])
    body = []
    housing = bmesh.new()
    lathe(housing, [(0, 1.38), (0.38, 1.38), (0.52, 1.5), (0.56, 1.75), (0.56, 2.2), (0.5, 2.42), (0.34, 2.52), (0, 2.52)], 20)
    body.append((housing, look["body"], 0.0, False))
    for z in (1.5, 2.4):
        body.append(ring(z, 0.52, 0.065, look["cap"], 0.0, 20))
    stripe = bmesh.new()
    torus(stripe, M((0, 0, 1.96)), 0.56, 0.055, 20, 4)
    body.append((stripe, look["stripe"], 0.0, False))
    for k in range(4):  # cooling vents round the housing
        a = k * math.pi / 2 + math.pi / 4
        vent_bm = bmesh.new()
        rounded_block(vent_bm, (0.18, 0.1, 0.34), frame((0.55 * math.cos(a), 0.55 * math.sin(a), 1.78), out=(math.cos(a), math.sin(a), 0), up=(0, 0, 1)),
                      corner=0.05, edge=0.03, corner_seg=1, edge_seg=1)
        body.append((vent_bm, look["core"], 0.0, False))
    chuck = bmesh.new()
    lathe(chuck, [(0, 2.48), (0.34, 2.48), (0.3, 2.64), (0.2, 2.76), (0, 2.76)], 16)
    body.append((chuck, look["core"], 0.0, False))
    b.add("Head", body)
    # the bit: a thick core and two broad flutes winding up it, symmetric round its axis (it spins about its
    # bounding box), ending in a cut point
    bit = []
    core = bmesh.new()
    lathe(core, [(0, 2.7), (0.15, 2.7), (0.13, length - 0.5), (0, length - 0.4)], 12)
    bit.append((core, look["cap"], 0.0, False))
    for start in (0, math.pi):
        steps = 26
        points = []
        for k in range(steps + 1):
            s = k / steps
            r = 0.27 * (1 - 0.6 * s ** 1.5)
            a = start + 2 * math.pi * 1.25 * s
            points.append(Vector((r * math.cos(a), r * math.sin(a), 2.8 + (length - 0.55 - 2.8) * s)))
        flute = bmesh.new()
        sweep(flute, points, 0.11, 8, radius_end=0.06)
        bit.append((flute, look["bit"], 0.0, False))
    point = bmesh.new()
    lathe(point, [(0, length - 0.62), (0.17, length - 0.62), (0, length)], 6)
    bit.append((faceted(point), look["tip"], 0.0, False))
    b.add("Bit", bit)
    return {"Grip": frame((0, 0, 0.75)), "Tip": frame((0, 0, length), out=(0, 0, 1)),
            "TrailA": frame((0, 0, 2.6)), "TrailB": frame((0, 0, length)), "Bit": frame((0, 0, 2.7))}


FAMILY_BUILD = {"Pick": pick, "Hammer": hammer, "Axe": axe, "Sword": sword, "Drill": drill, "Spear": spear}
# the game's family name (UpgradeConfig.Tools: the drill swings as a spear)
GAME_FAMILY = {"Drill": "Spear"}


def build_tools():
    global MATERIALS, SCENE_NAME
    SCENE_NAME = "B_Tools"
    scene = fresh_scene()
    path = os.path.join(REPO, "assets", "textures", "BuildingPalette.png")
    image = bpy.data.images.get("BuildingPalette") or bpy.data.images.load(path)
    MATERIALS = palette_materials(image)
    out = os.path.join(REPO, "store-assets", "tools")
    os.makedirs(os.path.join(out, "fbx"), exist_ok=True)
    manifest_path = os.path.join(out, "Tools_manifest.json")
    manifest = json.load(open(manifest_path, encoding="utf-8")) if os.path.exists(manifest_path) else {"tools": []}
    kept = {entry["tier"]: entry for entry in manifest["tools"]}
    tiers = [t for t in sorted(TOOLS) if not ONLY_TIERS or t in ONLY_TIERS]
    for tier in tiers:
        look = TOOLS[tier]
        Q.update({"round": 1.0, "minor": 1.0, "corner": 2, "edge": 2, "bevel": 2, "tiny": 0.6})
        coll = coll_in(scene, "Tool %d" % tier)
        b = Builder("ToolT%d" % tier, coll)
        atts = FAMILY_BUILD[look["family"]](b, tier, look)
        b.finish()
        attach(b, atts)
        meshes = counts(b.made)
        kept[tier] = {"tier": tier, "name": look["name"], "family": look["family"], "meshes": meshes,
                      "triangles": sum(n for _, n in meshes),
                      "attachments": {k: roblox_frame(m) for k, m in atts.items()}}
        print("Tool T%d %-15s %d tris" % (tier, look["name"], kept[tier]["triangles"]))
    manifest["tools"] = [kept[t] for t in sorted(kept)]
    json.dump(manifest, open(manifest_path, "w", encoding="utf-8"), indent=1)
    # the sheets: six tools at a time standing in a row, each turned three-quarter, labelled, with the pet and the
    # avatar (Tools_sheet.png, then Tools_sheet_2.png, Tools_sheet_3.png for more)
    rig, avatar, _ = reference(coll_in(scene, "Reference"))
    cam = stage(scene)
    per_row = 6
    for row in range((len(tiers) + per_row - 1) // per_row):
        labels = []
        chunk = tiers[row * per_row:(row + 1) * per_row]
        for tier in tiers:
            bpy.data.objects["ToolT%d" % tier].hide_render = tier not in chunk
            for child in bpy.data.objects["ToolT%d" % tier].children_recursive:
                child.hide_render = tier not in chunk
        for i, tier in enumerate(chunk):
            root = bpy.data.objects["ToolT%d" % tier]
            root.location = (i * 3.2, 0, 0)
            root.rotation_euler = (0, 0, math.radians(-25))
            labels.append(label(scene, "T%d %s" % (tier, TOOLS[tier]["name"]), (i * 3.2, -6.0, 0.4), 0.3))
        x = len(chunk) * 3.2 + 0.5
        rig.location, avatar.location = (x, 0, 0), (x + 3.5, 0, 0)
        labels.append(label(scene, "pet 3 studs", (x, -6.0, 0.4), 0.3))
        labels.append(label(scene, "avatar 5.5 studs", (x + 3.5, -6.0, 0.4), 0.3))
        ortho(cam, ((x + 3.5) / 2, 0, 2.9), 10, x + 7)
        shoot(scene, os.path.join(out, "Tools_sheet.png" if row == 0 else "Tools_sheet_%d.png" % (row + 1)), 2600, 1000)
        for lab in labels:
            bpy.data.objects.remove(lab, do_unlink=True)
    for tier in tiers:
        for obj in [bpy.data.objects["ToolT%d" % tier]] + list(bpy.data.objects["ToolT%d" % tier].children_recursive):
            obj.hide_render = False
    if EXPORT:
        for tier in tiers:
            root = bpy.data.objects["ToolT%d" % tier]
            root.location, root.rotation_euler = (0, 0, 0), (0, 0, 0)
            export_fbx([o for o in root.children if o.type == "MESH"], os.path.join(out, "fbx", "Tool_T%d.fbx" % tier))
    return kept


build_tools()
