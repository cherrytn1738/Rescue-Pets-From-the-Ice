# IcePickPost.py - the Ice Pick Post's five tiers and upgrade sets, for tools/blender/buildings/framework.py.
# Pad 8 (the smallest): compact footprints that grow tall. The working part is the ice pick, swinging at
# the ice in front (-Y): a pick on a wooden post, a brass clockwork hammer arm, two crystal-tipped piston
# picks, enchanted picks floating round a rune pillar, and the Frost Golem's raised fist.
# Upgrade sets (docs/GAME_DESIGN.md): 1 steel pick heads, 2 lantern on the post, 3 a spring that bounces
# with each swing, 4 ice chips (hit effect), 5 diamond picks with a frost trail.
import re

TIER_Q = {"Scrappy": {"round": 0.8}, "Workshop": {"round": 0.75}, "Frost-tech": {"round": 1.0},
          "Enchanted": {"round": 1.15}, "Legendary": {"round": 0.9}}

PICK_DIR_T1 = Vector((0, -1, -0.2)).normalized()
PICK_DIR_T2 = Vector((0, -1, -0.25)).normalized()
RAM_DIR_T3 = Vector((0, -0.6, -0.8)).normalized()
PICK_DIR_T4 = Vector((0, -1, -0.3)).normalized()
FIST_DIR_T5 = Vector((0.15, -1, -0.45)).normalized()
PICK_LEN = {1: 3.0, 2: 2.9, 3: 1.75, 4: 2.4, 5: 3.75}  # mount to the business end, per tier
GOLEM_RAISE = 1.3  # how much taller the golem stands than its first draft, so the Legendary is the tallest tier
GOLEM_X = 0.3  # the golem stands a little right, so its raised left fist stays over the pad


# ---------- pieces of this building ----------

def pickaxe(L, handle_sw, head_sw, spike_sw, back_sw, r=0.13, spike=1.2, hw=0.3, back="adze",
            spike_glow=False, crystal_spike=False, bands=(), gem=None):
    """An ice pick along +Z from its mount (the pivot): the handle, a socket at z = L, a spike toward -Y
    (down at the ice when the handle points at it) curving a little forward, and an adze blade or a hammer
    face toward +Y."""
    pieces = []
    h = bmesh.new()
    lathe(h, [(0, -0.12), (r * 1.08, -0.12), (r, 0.02), (r * 0.86, L * 0.5), (r, L - 0.25), (r * 0.92, L + hw * 0.9), (0, L + hw * 0.98)], 12)
    pieces.append((h, handle_sw, 0.0, False))
    s = bmesh.new()
    rounded_block(s, (hw * 1.3, hw * 1.45, hw * 1.9), M((0, 0, L)), corner=hw * 0.22, edge=hw * 0.14)
    pieces.append((s, head_sw, 0.0, False))
    if crystal_spike:
        pieces += place(cut_crystal(spike, hw * 0.5, spike_sw, glow=spike_glow), frame((0, -hw * 0.62, L), out=(0, -1, 0.2)))
    else:
        pts = [Vector((0, -hw * 0.6 - spike * u, L + 0.2 * spike * u * u)) for u in (0, 0.25, 0.5, 0.75, 1.0)]
        sp = bmesh.new()
        sweep(sp, pts, hw * 0.42, 8, radius_end=0.03)
        pieces.append((sp, spike_sw, 0.0, spike_glow))
    if back == "adze":
        a = bmesh.new()
        rounded_block(a, (hw * 1.9, spike * 0.5, hw * 0.32), M((0, hw * 0.6 + spike * 0.22, L - 0.05), (0.18, 0, 0)), corner=0.05, edge=0.04)
        pieces.append((a, back_sw, 0.0, False))
    else:  # a hammer face
        hm = bmesh.new()
        lathe(hm, [(0, 0), (hw * 0.62, 0), (hw * 0.62, spike * 0.38), (hw * 0.78, spike * 0.42), (hw * 0.78, spike * 0.54), (hw * 0.6, spike * 0.57), (0, spike * 0.57)], 12,
              frame((0, hw * 0.55, L), out=(0, 1, 0)))
        pieces.append((hm, back_sw, 0.0, False))
    for z, sw in bands:
        ring = bmesh.new()
        torus(ring, M((0, 0, z)), r * 1.05, 0.035, 12, 4)
        pieces.append((ring, sw, 0.0, False))
    if gem:  # a glowing gem set into each side of the socket
        for sx in (-1, 1):
            pieces += place(cut_gem(hw * 0.28, gem), frame((sx * hw * 0.66, 0, L), out=(sx, 0, 0)))
    return pieces


def piston_ram(tip_sw, tip_glow, fin_sw, shaft_sw="SteelLight", diamond=False):
    """Tier 3's piston pick along +Z from the rod end: a collar, a cross head with swept-back fins and a
    long cut-crystal point."""
    pieces = []
    c = bmesh.new()
    lathe(c, [(0, -0.05), (0.26, -0.05), (0.3, 0.1), (0.3, 0.32), (0.22, 0.4), (0, 0.4)], 14)
    pieces.append((c, shaft_sw, 0.0, False))
    pieces += trim_ring(0.31, 0.2, "AuroraCyan", True, minor=0.04, segments=14)
    head = bmesh.new()
    rounded_block(head, (0.42, 1.25, 0.36), M((0, 0, 0.55)), corner=0.12, edge=0.08)
    pieces.append((head, shaft_sw, 0.0, False))
    for sy in (-1, 1):  # fins swept back from the cross head
        fin = bmesh.new()
        rounded_block(fin, (0.12, 0.45, 0.6), M((0, sy * 0.68, 0.32), (sy * 0.45, 0, 0)), corner=0.04, edge=0.03, taper=0.5)
        pieces.append((fin, fin_sw, 0.0, False))
    pieces += place(cut_crystal(1.25, 0.24, tip_sw, glow=tip_glow), M((0, 0, 0.62)))
    if diamond:
        pieces += place(cut_gem(0.12, "CrystalCyan"), frame((0.22, 0, 0.55), out=(1, 0, 0)))
        pieces += place(cut_gem(0.12, "CrystalCyan"), frame((-0.22, 0, 0.55), out=(-1, 0, 0)))
    return pieces


def pick_look(t, kind):
    """The working part of tier t in its own frame: kind is "base", "steel" (1st upgrade) or "diamond" (5th)."""
    L = PICK_LEN[t]
    if t == 1:
        head, spike, back = {"base": ("Iron", "Rust", "Iron"), "steel": ("SteelDark", "SteelLight", "Steel"), "diamond": ("SteelLight", "Diamond", "Diamond")}[kind]
        pieces = pickaxe(L, "PineLight", head, spike, back, r=0.13, spike=1.25, hw=0.32, crystal_spike=(kind == "diamond"),
                         bands=((0.25, "Iron"), (2.55, "Iron")), gem="CrystalCyan" if kind == "diamond" else None)
        for k in range(3):  # a rope grip wound round the handle by the pivot
            ring = bmesh.new()
            torus(ring, M((0, 0, 0.5 + 0.09 * k)), 0.14, 0.04, 10, 4)
            pieces.append((ring, "Pine", 0.0, False))
        return pieces
    if t == 2:
        head, spike, back = {"base": ("Brass", "SteelDark", "Iron"), "steel": ("Brass", "SteelLight", "SteelLight"), "diamond": ("Gold", "Diamond", "SteelLight")}[kind]
        pieces = pickaxe(L, "Iron", head, spike, back, r=0.16, spike=1.2, hw=0.36, back="hammer", crystal_spike=(kind == "diamond"),
                         bands=((0.35, "Brass"), (1.3, "Brass"), (2.3, "Brass")), gem="CrystalCyan" if kind == "diamond" else None)
        pieces += place(gear(0.3, 8, 0.1, 0.08, "Brass", "Copper"), frame((0.19, 0, 1.0), out=(1, 0, 0)))
        return pieces
    if t == 3:
        if kind == "base":
            return piston_ram("CrystalCyan", True, "GlacierBlue")
        if kind == "steel":
            return piston_ram("SteelLight", False, "IceBlue", "Steel")
        return piston_ram("Diamond", False, "CrystalCyan", "SteelLight", diamond=True)
    if t == 4:
        head, spike, glow = {"base": ("Gold", "RuneViolet", True), "steel": ("Gold", "SteelLight", False), "diamond": ("Gold", "Diamond", False)}[kind]
        pieces = pickaxe(L, "Moonstone", head, spike, "Moonstone" if kind != "steel" else "SteelLight", r=0.15, spike=1.45, hw=0.4,
                         spike_glow=glow, crystal_spike=True, bands=((0.3, "Gold"), (1.3, "Gold"), (2.1, "Gold")),
                         gem="AuroraCyan" if kind == "diamond" else "MagicPink")
        pieces += trim_ring(0.34, 0.8, "RuneGlow", True, minor=0.035, segments=16)  # floating rune bands on the handle
        pieces += trim_ring(0.3, 1.6, "RuneGlow", True, minor=0.03, segments=16)
        return pieces
    # t == 5: the knuckle picks on the golem's fist (the fist itself is the tier's working part)
    pieces = []
    for k in range(4):
        x = -0.6 + 0.4 * k
        base = M((x, 0.1, L - 0.15))
        if kind == "steel":
            cone = bmesh.new()
            lathe(cone, [(0, 0), (0.17, 0), (0.15, 0.25), (0.05, 0.75), (0, 0.82)], 8, base)
            pieces.append((cone, "SteelLight", 0.0, False))
            pieces += place(trim_ring(0.18, 0.02, "Gold", minor=0.04, segments=12), base)
        else:
            pieces += place(cut_crystal(0.95, 0.17, "Diamond", glow=False), base)
            pieces += place(trim_ring(0.19, 0.04, "Gold", minor=0.04, segments=12), base)
            pieces += place(cut_gem(0.07, "CrystalCyan"), base @ M((0, -0.2, 0.05)))
    return pieces


def spring(length, radius, wire, cap, turns=6, wire_r=None, cap_glow=False, wire_glow=False):
    """A coil spring along +Z from its base: a wound wire and a washer at each end."""
    n = turns * 10
    pts = [Vector((radius * math.cos(2 * math.pi * i / 10), radius * math.sin(2 * math.pi * i / 10), 0.15 + (length - 0.3) * i / n)) for i in range(n + 1)]
    s = bmesh.new()
    sweep(s, pts, wire_r or radius * 0.15, 6)
    pieces = [(s, wire, 0.0, wire_glow)]
    pieces += place(cyl(radius * 1.25, 0.14, cap, 14), M((0, 0, 0)))
    pieces += place(cyl(radius * 1.25, 0.14, cap, 14), M((0, 0, length - 0.14)))
    if cap_glow:
        pieces += trim_ring(radius * 1.3, 0.07, cap_glow, True, minor=0.035, segments=14)
        pieces += trim_ring(radius * 1.3, length - 0.07, cap_glow, True, minor=0.035, segments=14)
    return pieces


SPRING_LOOK = {  # (length, radius, wire, cap, glow ring, turns)
    1: (1.35, 0.17, "Rust", "Iron", None, 6),
    2: (1.3, 0.2, "Brass", "Copper", None, 6),
    3: (0.95, 0.27, "SteelLight", "GlacierBlue", "AuroraCyan", 5),
    4: (1.45, 0.2, "Gold", "Moonstone", "RuneGlow", 6),
    5: (1.7, 0.3, "Gold", "Gunmetal", "AuroraGreen", 5),
}


def snowflake(size, swatch="Diamond", glow=True):
    """A flat six-armed snowflake in the XY plane (a flurry stand-in)."""
    pieces = []
    for k in range(3):
        a = k * math.pi / 3
        arm = bmesh.new()
        box(arm, (0, 0, 0), (size * 0.12, size * 2, size * 0.06), rotation=(0, 0, a))
        pieces.append((arm, swatch, 0.0, glow))
    for k in range(6):
        a = k * math.pi / 3
        for side in (-1, 1):
            twig = bmesh.new()
            p = Vector((-math.sin(a), math.cos(a), 0)) * size * 0.6
            box(twig, p, (size * 0.08, size * 0.45, size * 0.05), rotation=(0, 0, a + side * 0.7))
            pieces.append((twig, swatch, 0.0, glow))
    return pieces


def ice_chips(t):
    """The 4th upgrade's hit effect stand-in (particles in game): ice shards and a snow puff bursting out
    along +Z, with sparks in the tier's colour."""
    pieces = []
    for k in range(9):
        a = k * 2.3
        sw = ("IceBlue", "Diamond", "FrostLight")[k % 3]
        pieces += place(cut_crystal(0.3 + 0.06 * (k % 3), 0.1 + 0.025 * (k % 2), sw, glow=False),
                        M((0.6 * math.cos(a), 0.6 * math.sin(a), 0.25 + 0.17 * k), (a, 0.6 * k, 0)))
    for dx, dz, r in ((0.0, 0.15, 0.3), (0.3, 0.35, 0.22), (-0.3, 0.3, 0.25)):
        puff = bmesh.new()
        blob(puff, (dx, 0, dz), (r, r, r * 0.8), 1)
        pieces.append((puff, "SnowWhite", 0.0, False))
    spark = {1: "FrostLight", 2: "LampYellow", 3: "CrystalCyan", 4: "RuneGlow", 5: "Gold"}[t]
    for k in range(5):
        a = k * 1.25 + 0.4
        s = bmesh.new()
        cylinder(s, (0.35 * math.cos(a), 0.35 * math.sin(a), 0.2), 0.05, 0.6, 4, direction=(math.cos(a), math.sin(a), 1.3), top=0.0)
        pieces.append((s, spark, 0.0, True))
    return pieces


def frost_trail(points, size=0.13):
    """The 5th upgrade's frost trail stand-in: glittering ice and snowflakes along the swing."""
    pieces = []
    n = len(points)
    for k, p in enumerate(points):
        s = size * (1 - 0.5 * k / n)
        pieces += place(cut_gem(s, "CrystalCyan" if k % 2 else "Diamond"), M(p, (k, 0.7 * k, 0)))
        if k % 3 == 1:
            pieces += place(snowflake(s * 1.8, "Diamond"), M(p + Vector((0.25, 0, 0)), (0.5 * k, 0.3, 0)))
    return pieces


def swing_arc(L, start=0.15, end=1.1, count=10):
    """Where a pick's head was just before it struck: an arc round its pivot, back up the swing (+Y)."""
    return [Vector((0, L * math.sin(a), L * math.cos(a))) for a in (start + (end - start) * k / (count - 1) for k in range(count))]


def pennant(length=0.8, height=0.45, thick=0.04):
    """A triangular cloth pennant in the YZ plane, flying toward -Y from its pole at the origin."""
    bm = bmesh.new()
    pts = [(0, 0), (-length, -height * 0.45 + 0.05), (-length * 0.55, -height * 0.5), (0, -height)]
    a = [bm.verts.new((-thick / 2, y, z)) for y, z in pts]
    b2 = [bm.verts.new((thick / 2, y, z)) for y, z in pts]
    bm.faces.new(a[::-1])
    bm.faces.new(b2)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((a[i], a[j], b2[j], b2[i]))
    return bm


class Surface:
    """Measures a finished organic mesh so face parts sit on it, not in front of it or inside it."""

    def __init__(self, bm):
        self.points = [v.co.copy() for v in bm.verts]

    def front(self, x, z, reach=0.3):
        return min(p.y for p in self.points if abs(p.x - x) < reach and abs(p.z - z) < reach)

    def top(self, x=None, reach=0.4):
        return max(p.z for p in self.points if x is None or abs(p.x - x) < reach)

    def band(self, z, reach=0.2):
        ring = [p for p in self.points if abs(p.z - z) < reach]
        return ((max(p.x for p in ring) - min(p.x for p in ring)) / 2, (max(p.y for p in ring) - min(p.y for p in ring)) / 2,
                (max(p.x for p in ring) + min(p.x for p in ring)) / 2, (max(p.y for p in ring) + min(p.y for p in ring)) / 2)


def rock(size, cuts=1, levels=2, roundness=0.6, shape=None, lump=0.06, seed=0.0):
    """An icy rock: a box cage pulled toward an ellipsoid, shaped by shape(v), a little lumpy, subdivided."""
    cage = cage_box(size, cuts)
    radii = Vector(size) / 2
    for v in cage.verts:
        unit = Vector((v.co.x / radii.x, v.co.y / radii.y, v.co.z / radii.z))
        if unit.length > 1e-6:
            unit.normalize()
            v.co = v.co.lerp(Vector((unit.x * radii.x, unit.y * radii.y, unit.z * radii.z)), roundness)
        n = math.sin(v.co.x * 3.1 + seed) * math.cos(v.co.y * 2.7 + seed * 1.7) * math.sin(v.co.z * 2.3 + seed * 0.5)
        v.co *= 1 + lump * n
        if shape:
            shape(v)
    return subsurf(cage, levels)


def limb(p0, p1, r0, r1, swatch, seed=0.0, cuts=1):
    """A rock limb from p0 to p1 tapering from r0 to r1."""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length

    def taper(v):
        s = 0.5 + v.co.z / L
        k = (r0 + (r1 - r0) * s) / max(r0, r1)
        v.co.x *= k
        v.co.y *= k
    bm = rock((2 * max(r0, r1), 2 * max(r0, r1) * 0.92, L + max(r0, r1) * 0.8), cuts, 2, 0.45, taper, 0.07, seed)
    bm.transform(Matrix.Translation(p0) @ align_z(p1 - p0) @ M((0, 0, L / 2)))
    return [(bm, swatch, 0.0, False)]


# ---------- tier 1: Scrappy, a wooden post with a pick ----------

def t1_scrappy(b):
    for k, (sw, grain, y, L, turn) in enumerate((("PineDark", "RustDark", -1.0, 4.3, 0.03), ("Pine", "PineDark", 0.02, 3.9, -0.04), ("PineLight", "Pine", 1.04, 4.1, 0.05))):
        b.add("Base", place(plank(L, 0.98, 0.25, sw, grain, k != 1, k * 1.3), M((0.05 * k, y, 0), (0, 0, turn))))
    for sx in (-1, 1):  # battens nailed across the boards
        b.add("Base", place(plank(3.0, 0.42, 0.14, "PineDark", "RustDark", False, 3 + sx), M((sx * 1.7, 0, 0.25), (0, 0, math.pi / 2))))
    post_y = 0.9
    b.add("Post", place(block((0.95, 0.95, 0.42), "PineDark", corner=0.1, edge=0.06), M((0, post_y, 0.25))))
    b.add("Post", grained_beam((0, post_y, 0.6), (0, post_y, 4.75), 0.55, "Pine", "PineDark"))
    b.add("Post", place(block((0.72, 0.72, 0.16), "PineDark", corner=0.08, edge=0.05), M((0, post_y, 4.72))))
    b.add("Braces", grained_beam((-1.75, post_y, 0.32), (-0.27, post_y, 2.5), 0.3, "PineDark", "RustDark"))
    b.add("Braces", grained_beam((0, 2.6, 0.32), (0, 1.17, 2.6), 0.3, "PineDark", "RustDark"))
    for p in ((-1.75, post_y, 0.4), (0, 2.6, 0.4)):
        b.add("Braces", place(cyl(0.24, 0.12, "StoneDark", 10), M((p[0], p[1], 0.25))))
    for z, tilt in ((2.35, 0.25), (2.55, -0.3)):  # rope lashing where the braces meet the post
        ring = bmesh.new()
        torus(ring, M((0, post_y, z), (tilt, tilt * 0.5, 0)), 0.42, 0.055, 12, 4)
        b.add("Braces", [(ring, "PineLight", 0.0, False)])
    for z in (1.3, 3.3):  # iron straps nailed round the post
        b.add("Post", trim_strip((-0.3, post_y - 0.29, z), (0.3, post_y - 0.29, z), 0.2, "Iron"))
    # the pivot: two oak cheeks out of the post front, an iron axle and bolts
    for sx in (-1, 1):
        b.add("Pivot", place(block((0.14, 0.9, 0.75), "PineDark", corner=0.05, edge=0.04), M((sx * 0.25, 0.27, 3.72))))
        b.add("Pivot", place(bolt(0.09, "Iron", "SteelDark"), frame((sx * 0.32, 0.25, 4.1), out=(sx, 0, 0))))
        b.add("Pivot", place(rivet(0.05, "Iron"), frame((sx * 0.32, 0.5, 3.85), out=(sx, 0, 0))))
    b.add("Pivot", place(cyl(0.08, 0.7, "Iron", 12), frame((-0.35, 0.25, 4.1), out=(1, 0, 0))))
    b.add("Pivot", trim_strip((-0.33, 0.62, 3.6), (0.33, 0.62, 3.6), 0.12, "Iron"))
    # the winch on the post's side: a drum with rope, end boards and an iron crank
    b.add("Winch", place(cyl(0.26, 0.55, "PineDark", 14), frame((0.3, post_y, 1.75), out=(1, 0, 0))))
    for x in (0.3, 0.8):
        b.add("Winch", place(cyl(0.4, 0.06, "Pine", 14), frame((x, post_y, 1.75), out=(1, 0, 0))))
    for k in range(2):
        ring = bmesh.new()
        torus(ring, frame((0.48 + 0.2 * k, post_y, 1.75), out=(1, 0, 0)), 0.28, 0.05, 12, 4)
        b.add("Winch", [(ring, "PineLight", 0.0, False)])
    crank = bmesh.new()
    sweep(crank, [V(0.85, post_y, 1.75), V(1.0, post_y, 1.75), V(1.02, post_y - 0.05, 1.42), V(1.02, post_y - 0.1, 1.2)], 0.045, 6)
    b.add("Winch", [(crank, "Iron", 0.0, False)])
    b.add("Winch", place(cyl(0.07, 0.32, "PineLight", 10), frame((1.02, post_y - 0.1, 1.2), out=(1, 0, 0))))
    b.add("Winch", cable((0.55, post_y - 0.25, 1.95), (0.2, post_y - 0.2, 4.6), 0.12, 0.035, "PineLight", "Iron"))
    # the lantern hook arm on the left of the post
    hook = bmesh.new()
    sweep(hook, [V(-0.25, post_y, 4.4), V(-0.7, post_y, 4.45), V(-1.0, post_y, 4.38), V(-1.0, post_y, 4.2)], 0.045, 6)
    b.add("Post", [(hook, "Iron", 0.0, False)])
    b.add("Post", place(block((0.3, 0.3, 0.04), "Iron", corner=0.04, edge=0.015), frame((-0.28, post_y, 4.4), out=(-1, 0, 0))))
    # the spring bracket on the post front (the 3rd upgrade's spring stands on it)
    b.add("Post", place(block((0.6, 0.38, 0.22), "PineDark", corner=0.06, edge=0.04), M((0, 0.55, 2.5))))
    b.add("Post", place(rivet_ring(0.15, 4, 0.04, "Iron"), M((0, 0.55, 2.72))))
    # a pennant on the post top
    b.add("Post", place(cyl(0.04, 1.0, "PineLight", 8), M((0, post_y, 4.85))))
    b.add("Post", [(pennant(0.75, 0.42), "WarnRed", 0.0, False)], M((0, post_y, 5.82), (0, 0, math.pi / 2 + 0.25)))
    # junk: a wooden bucket of ice chunks, a nailed crate, a rope coil
    bucket = bmesh.new()
    lathe(bucket, [(0, 0), (0.32, 0), (0.42, 0.55), (0.37, 0.55), (0.28, 0.06), (0, 0.06)], 14, M((-1.55, -1.05, 0.25)))
    b.add("Junk", [(bucket, "Pine", 0.0, False)])
    for z, r in ((0.45, 0.41),):
        hoop = bmesh.new()
        torus(hoop, M((-1.55, -1.05, 0.25 + z)), r, 0.03, 14, 4)
        b.add("Junk", [(hoop, "Iron", 0.0, False)])
    for k in range(2):
        a = k * 3.0
        b.add("Junk", place(cut_crystal(0.45 + 0.1 * (k % 2), 0.13, "IceBlue", (0.3 * math.cos(a), 0.3 * math.sin(a)), glow=False), M((-1.55 + 0.15 * math.cos(a), -1.05 + 0.15 * math.sin(a), 0.6))))
    b.add("Junk", place(block((1.0, 0.85, 0.75), "Pine", corner=0.06, edge=0.05), M((1.55, 1.3, 0.25), (0, 0, 0.15))))
    for z in (0.45, 0.8):
        b.add("Junk", place(trim_strip((-0.5, -0.44, 0), (0.5, -0.44, 0), 0.1, "PineDark"), M((1.55, 1.3, z), (0, 0, 0.15))))
    work = frame((0, 0.25, 4.1), out=PICK_DIR_T1)
    b.add("Pick", pick_look(1, "base"), work)
    return {"Work": work, "Lamp1": up_((-1.0, post_y, 3.37)), "Gear1": frame((0, 0.55, 2.72), out=(0, -0.48, 0.88)),
            "Hit": frame((0, -3.3, 0.3), out=(0, -1, 0.6)), "Trail": work, "NamePlate": front((0, -1.55, 0.45)),
            "Aura": up_((0, 0, 0.25)), "Top": up_((0, post_y, 5.85))}


# ---------- tier 2: Workshop, a brass clockwork hammer arm ----------

def t2_workshop(b):
    for k in range(6):
        b.add("Deck", place(plank(6.8, 1.0, 0.45, "Pine", "PineDark", k in (0, 5), k * 0.9), M((0, -2.65 + k * 1.06, 0))))
    rail_tops = {}
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = (sx * 3.05, sy * 2.85)
            b.add("Rail", beam_between((p[0], p[1], 0.45), (p[0], p[1], 1.95), 0.3, swatch="PineDark"))
            b.add("Rail", place(cyl(0.22, 0.12, "Brass", 8), M((p[0], p[1], 1.95))))
            rail_tops[(sx, sy)] = Vector((p[0], p[1], 1.75))
    for a, c in (((-1, 1), (1, 1)), ((-1, -1), (-1, 1)), ((1, -1), (1, 1))):
        b.add("Rail", pipe_between(rail_tops[a], rail_tops[c], 0.06, "Brass"))
    # the clockwork housing: iron with a brass lid, a riveted brass plate and a pressure dial
    b.add("Housing", place(lidded_box((2.8, 2.3, 2.6), "Iron", "Brass", "Brass"), M((0, 1.15, 0.45))))
    b.add("Housing", place(riveted_plate(1.6, 0.9, 0.06, "Brass", "Copper", 0.5), front((0, -0.02, 1.25))))
    b.add("Housing", place(vent(1.0, 0.6, 4, "Iron", "Brass"), frame((-1.42, 1.15, 1.5), out=(-1, 0, 0))))
    b.add("Housing", place(dial(0.25, "Cream", "Brass", "WarnRed", 0.4), frame((-1.42, 0.45, 2.45), out=(-1, 0, 0))))
    # the clock tower: a brass box with a big clock face, copper corner trims, a cornice and a pyramid roof
    b.add("Tower", place(block((2.1, 1.9, 2.3), "Brass", corner=0.25, edge=0.12), M((0, 1.15, 3.05))))
    b.add("Tower", place(dial(0.78, "Cream", "Brass", "Iron", 0.9), front((0, 0.19, 4.25))))
    b.add("Tower", place(trim_ring(0.84, 0, "Copper", minor=0.07, segments=24), front((0, 0.18, 4.25))))
    for k in range(4):  # hour studs
        a = k * math.pi / 2
        b.add("Tower", place(rivet(0.05, "Iron"), front((0.66 * math.cos(a), 0.16, 4.25 + 0.66 * math.sin(a)))))
    for sx in (-1, 1):
        for y in (0.22,):
            b.add("Tower", trim_strip((sx * 1.04, y, 3.1), (sx * 1.04, y, 5.3), 0.16, "Copper"))
    b.add("Tower", place(block((2.45, 2.25, 0.22), "Copper", corner=0.25, edge=0.06), M((0, 1.15, 5.33))))
    roof = bmesh.new()
    lathe(roof, [(0, 5.55), (1.72, 5.55), (1.6, 5.72), (0.3, 6.95), (0, 7.05)], 4, M((0, 1.15, 0), (0, 0, math.pi / 4)))
    b.add("Tower", [(roof, "Copper", 0.0, False)])
    b.add("Tower", place(cyl(0.1, 0.55, "Brass", 10), M((0, 1.15, 6.95))))
    ball = bmesh.new()
    blob(ball, (0, 1.15, 7.6), (0.17, 0.17, 0.17), 2)
    b.add("Tower", [(ball, "Brass", 0.0, False)])
    b.add("Tower", place(cut_crystal(0.4, 0.08, "Brass", glow=False, sides=4), M((0, 1.15, 7.72))))
    # the wind-up key on the back
    b.add("Key", place(cyl(0.1, 0.65, "Brass", 10), frame((0, 2.1, 4.25), out=(0, 1, 0))))
    for sx in (-1, 1):
        loop = bmesh.new()
        torus(loop, frame((sx * 0.34, 2.8, 4.25), out=(0, 1, 0)), 0.28, 0.08, 14, 4)
        b.add("Key", [(loop, "Brass", 0.0, False)])
    hub = bmesh.new()
    blob(hub, (0, 2.8, 4.25), (0.16, 0.12, 0.16), 1)
    b.add("Key", [(hub, "Brass", 0.0, False)])
    # gears on the sides: a big spoked gear meshing with a small one, an escapement wheel on the tower
    b.add("Gears", place(spoked_gear(1.0, 10, 0.24, 0.14, 4, "Brass", "Copper"), frame((1.52, 1.15, 1.75), out=(1, 0, 0))))
    b.add("Gears", place(gear(0.5, 8, 0.22, 0.12, "Copper", "Brass"), frame((1.52, 2.05, 2.85), out=(1, 0, 0))))
    b.add("Gears", place(gear(0.55, 10, 0.16, 0.1, "Brass", "Iron"), frame((-1.1, 1.15, 4.3), out=(-1, 0, 0))))
    # the steam pipe with copper bands and a whistle
    b.add("Pipe", pipe_between((-1.3, 2.0, 3.05), (-1.3, 2.0, 6.3), 0.16, "Brass"))
    for z in (4.0, 5.4):
        b.add("Pipe", place(trim_ring(0.18, 0, "Copper", minor=0.04, segments=12), M((-1.3, 2.0, z))))
    whistle = bmesh.new()
    lathe(whistle, [(0, 6.3), (0.2, 6.3), (0.24, 6.45), (0.18, 6.6), (0.22, 6.72), (0, 6.78)], 12, M((-1.3, 2.0, 0)))
    b.add("Pipe", [(whistle, "Copper", 0.0, False)])
    # the arm's mount: brass cheek plates, an iron axle with bolts, a ratchet wheel
    for sx in (-1, 1):
        b.add("Mount", place(block((0.14, 0.8, 0.85), "Brass", corner=0.06, edge=0.04), M((sx * 0.32, -0.3, 2.88))))
        b.add("Mount", place(bolt(0.1, "Iron", "Brass"), frame((sx * 0.4, -0.35, 3.3), out=(sx, 0, 0))))
    b.add("Mount", place(cyl(0.09, 0.84, "Iron", 12), frame((-0.42, -0.35, 3.3), out=(1, 0, 0))))
    b.add("Mount", place(block((0.7, 0.4, 0.25), "Iron", corner=0.06, edge=0.04), M((0, -0.15, 1.7))))
    # deck clutter: a toolbox, an oil can, a coal scuttle
    b.add("Clutter", place(lidded_box((0.9, 0.5, 0.45), "WarnRedDark", "WarnRed", "Brass"), M((2.2, 1.6, 0.45), (0, 0, -0.2))))
    can = bmesh.new()
    lathe(can, [(0, 0), (0.2, 0), (0.2, 0.38), (0.11, 0.5), (0, 0.5)], 12, M((-2.3, -1.7, 0.45)))
    spout = bmesh.new()
    sweep(spout, [V(-2.2, -1.7, 0.88), V(-2.0, -1.8, 1.08), V(-1.8, -1.9, 1.15)], 0.03, 6, radius_end=0.02)
    b.add("Clutter", [(can, "Brass", 0.0, False), (spout, "Copper", 0.0, False)])
    work = frame((0, -0.35, 3.3), out=PICK_DIR_T2)
    b.add("Arm", pick_look(2, "base"), work)
    return {"Work": work, "Lamp1": up_((-3.05, -2.85, 2.02)), "Lamp2": up_((3.05, -2.85, 2.02)),
            "Gear1": frame((0, -0.15, 1.95), out=(0, -0.42, 0.91)), "Steam1": up_((-1.3, 2.0, 6.8)),
            "Hit": frame((0, -3.4, 0.3), out=(0, -1, 0.6)), "Trail": work, "NamePlate": front((0, -3.17, 0.25)),
            "Aura": up_((0, 0, 0.45)), "Top": up_((0, 1.15, 8.1))}


# ---------- tier 3: Frost-tech, crystal-tipped piston picks with blue coils ----------

def t3_frosttech(b):
    b.add("Deck", block((7.7, 7.7, 0.75), "SnowWhite", corner=1.2, edge=0.28))
    b.add("Deck", place(block((6.9, 6.9, 0.25), "IceBlue", corner=0.95, edge=0.1), M((0, 0, 0.75))))
    for sx in (-1, 1):
        b.add("Deck", place(inset_panel(1.3, 1.0, 0.05, "FrostLight", "GlacierBlue", True), M((sx * 2.6, -2.5, 1.0))))
        b.add("Deck", place(vent(1.2, 0.36, 4, "GlacierBlue", "SteelLight"), front((sx * 2.5, -3.84, 0.38))))
        for sy in (-1, 1):
            b.add("Deck", place(bolt(0.1, "SteelLight", "GlacierBlue"), M((sx * 3.1, sy * 3.1, 1.0))))
    for p0, p1 in (((-1.5, -3.87, 0.4), (1.5, -3.87, 0.4)), ((-2.6, 3.87, 0.4), (2.6, 3.87, 0.4)),
                   ((-3.87, -2.6, 0.4), (-3.87, 2.6, 0.4)), ((3.87, -2.6, 0.4), (3.87, 2.6, 0.4))):
        b.add("Deck", trim_strip(p0, p1, 0.16, "AuroraCyan", True))
    # the core tower: banded white shell, a visor, a screen, a back vent, a hinged lid
    ty = 1.2
    b.add("Tower", place(block((2.8, 2.3, 4.3), "SnowWhite", corner=0.9, edge=0.55), M((0, ty, 1.0))))
    for z in (2.3, 3.75):
        b.add("Tower", place(block((2.86, 2.36, 0.07), "GlacierBlue", corner=0.92, edge=0.02), M((0, ty, z))))
    b.add("Tower", place(block((2.1, 0.3, 0.6), "NavyIce", corner=0.25, edge=0.1), M((0, ty - 1.12, 4.25))))
    for z in (4.12, 4.95):
        b.add("Tower", trim_strip((-0.9, ty - 1.28, z), (0.9, ty - 1.28, z), 0.07, "AuroraCyan", True))
    b.add("Tower", place(screen(0.9, 0.5, "AuroraCyan", "NavyIce", 3), front((0, ty - 1.15, 3.05))))
    b.add("Tower", place(vent(1.2, 0.6, 5, "GlacierBlue", "SteelLight"), frame((0, ty + 1.16, 3.0), out=(0, 1, 0))))
    b.add("Tower", place(block((2.4, 1.9, 0.3), "SteelLight", corner=0.7, edge=0.12), M((0, ty, 5.3))))
    b.add("Tower", place(hinge(1.2, 0.07, 4, "GlacierBlue"), M((0, ty + 0.95, 5.38))))
    b.add("Tower", place(handle(0.5, 0.18, 0.04, "GlacierBlue"), front((0, ty - 0.93, 5.45))))
    # the coil spire: insulators, the wound coil and its glowing top
    b.add("Coil", place(cyl(0.7, 0.3, "GlacierBlue", 16), M((0, ty, 5.6))))
    b.add("Coil", place(coil(0.5, 3.2, turns=6, core="SteelDark", wire="IceBlue", top="AuroraCyan"), M((0, ty, 5.9))))
    for z in (6.2, 6.8):
        b.add("Coil", place(cyl(0.82, 0.12, "IceBlue", 16), M((0, ty, z))))
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 2
        fin = bmesh.new()
        rounded_block(fin, (0.12, 0.7, 1.1), M((0.72 * math.cos(a), ty + 0.72 * math.sin(a), 6.5), (0, 0, a)), corner=0.05, edge=0.04, taper=0.5)
        b.add("Coil", [(fin, "GlacierBlue", 0.0, False)])
    # back coils on the deck corners, hoses to the tower
    for sx in (-1, 1):
        b.add("BackCoils", place(block((1.0, 1.0, 0.5), "SteelLight", corner=0.25, edge=0.1), M((sx * 2.65, 2.65, 1.0))))
        b.add("BackCoils", place(coil(0.3, 2.0, turns=5, core="SteelDark", wire="GlacierBlue", top="AuroraCyan"), M((sx * 2.65, 2.65, 1.5))))
        b.add("BackCoils", cable((sx * 1.4, ty + 0.6, 2.0), (sx * 2.2, 2.65, 1.35), 0.25, 0.1, "NavyIce", "GlacierBlue", ribs=2))
        b.add("BackCoils", place(cut_crystal_cluster(0.4, "CrystalCyan", "SteelLight", 4), M((sx * 3.0, -1.0, 1.0), (0, 0, sx))))
    # the two piston picks: a mount on each side of the tower, a piston wound with a glowing coil, a rod
    atts = {}
    D = RAM_DIR_T3
    for i, sx in enumerate((-1, 1)):
        side = "PistonA" if sx < 0 else "PistonB"
        b.add(side, place(block((0.8, 1.2, 1.2), "SteelLight", corner=0.3, edge=0.15), M((sx * 1.75, 0.7, 3.8))))
        b.add(side, place(inset_panel(0.6, 0.6, 0.04, "FrostLight", "GlacierBlue", False), frame((sx * 2.16, 0.7, 4.4), out=(sx, 0, 0))))
        p0 = Vector((sx * 1.75, 0.15, 4.3))
        b.add(side, place(cyl(0.3, 0.5, "GlacierBlue", 14), frame(p0 - D * 0.35, out=D)))
        b.add(side, place(cyl(0.34, 1.5, "SteelLight", 16), frame(p0, out=D)))
        for s in (0.05, 1.45):
            b.add(side, place(trim_ring(0.35, 0, "GlacierBlue", minor=0.06, segments=16), frame(p0 + D * s, out=D)))
        helix = [Vector((0.39 * math.cos(2 * math.pi * k / 10), 0.39 * math.sin(2 * math.pi * k / 10), 0.25 + 1.0 * k / 50)) for k in range(51)]
        wire = bmesh.new()
        sweep(wire, helix, 0.05, 6)
        b.add(side + "Coil", [(wire, "AuroraCyan", 0.0, True)], frame(p0, out=D))
        p1 = p0 + D * 1.5
        b.add(side, place(cyl(0.14, 1.0, "Steel", 12), frame(p1, out=D)))
        b.add(side, beam_between((sx * 1.75, -0.45, 1.0), (sx * 1.75, -0.45, 3.45), 0.24, swatch="SteelLight"))
        b.add(side, place(cyl(0.28, 0.12, "GlacierBlue", 12), M((sx * 1.75, -0.45, 1.0))))
        b.add(side, cable((sx * 1.4, ty - 0.6, 2.2), (sx * 1.75, -0.75, 3.15), 0.3, 0.07, "NavyIce", "GlacierBlue"))
        work = frame(p1 + D * 1.0, out=D)
        b.add("Pick" + "AB"[i], pick_look(3, "base"), work)
        suffix = "" if i == 0 else "2"
        atts["Work" + suffix] = work
        atts["Trail" + suffix] = work
        atts["Lamp" + str(i + 1)] = up_((sx * 1.75, 0.7, 5.0))
        atts["Gear" + str(i + 1)] = frame(p1 + D * 0.02, out=D)
    atts.update({"Hit": frame((0, -3.4, 0.3), out=(0, -1, 0.6)), "NamePlate": front((0, -3.86, 0.38)),
                 "Aura": up_((0, 0, 1.0)), "Top": up_((0, ty, 9.6)), "Steam1": up_((0, ty, 9.6))})
    return atts


# ---------- tier 4: Enchanted, picks orbiting a rune pillar ----------

PILLAR_Y = 0.6


def pillar_radius(z):
    return 0.95 + (0.78 - 0.95) * (z - 2.0) / 6.4


def t4_enchanted(b):
    dais = bmesh.new()
    lathe(dais, [(0, 0), (3.75, 0), (3.75, 0.3), (3.55, 0.35), (3.55, 0.55), (3.3, 0.8), (0, 0.8)], 6)
    b.add("Dais", [(dais, "Moonstone", 0.04, False)])
    plinth = bmesh.new()
    lathe(plinth, [(0, -0.01), (3.9, -0.01), (3.9, 0.18), (0, 0.18)], 6)
    b.add("Dais", [(plinth, "StoneDark", 0.03, False)])
    b.add("Dais", place(trim_ring(3.5, 0, "RuneViolet", minor=0.08, segments=6), M((0, 0, 0.56))))
    b.add("Dais", place(engraved_rune_ring(2.6, "RuneGlow", "ArcaneDeep", "RuneViolet", 14), M((0, 0, 0.8))))
    for k in range(6):
        a = k * math.pi / 3
        if k not in (4, 5):  # the two front corners stay clear for the lamps' pedestals
            b.add("DaisCrystals", place(cut_crystal_cluster(0.45, "CrystalCyan" if k % 2 else "RuneViolet", "Moonstone", 4), M((3.25 * math.cos(a), 3.25 * math.sin(a), 0.78), (0, 0, a))))
        fa = a + math.pi / 6
        ap = 3.75 * math.cos(math.pi / 6)
        b.add("Dais", place(gem_setting(0.13, "AuroraCyan", "Gold", 4), frame((ap * math.cos(fa), ap * math.sin(fa), 0.18), out=(math.cos(fa), math.sin(fa), 0))))
    # the rune pillar: a tapering obelisk on a plinth, gold bands, glowing runes and gems on its faces
    py = PILLAR_Y
    b.add("Pillar", place(block((2.0, 2.0, 0.6), "StoneDark", corner=0.15, edge=0.08), M((0, py, 0.8))))
    b.add("Pillar", place(block((1.75, 1.75, 0.2), "Gold", corner=0.12, edge=0.05), M((0, py, 1.3))))
    obelisk = bmesh.new()
    lathe(obelisk, [(0, 1.4), (1.35, 1.4), (1.34, 2.0), (pillar_radius(8.4) * 1.414, 8.4), (1.2, 8.55), (1.2, 8.8), (0, 9.5)], 4,
          M((0, py, 0), (0, 0, math.pi / 4)))
    b.add("Pillar", [(obelisk, "Moonstone", 0.04, False)])
    for z in (2.05, 8.45):
        band = bmesh.new()
        torus(band, M((0, py, z), (0, 0, math.pi / 4)), pillar_radius(z) * 1.414 + 0.05, 0.08, 4, 4)
        b.add("Pillar", [(band, "Gold", 0.0, False)])
    for f in range(4):
        a = f * math.pi / 2
        n = Vector((math.cos(a), math.sin(a), 0))
        for j, z in enumerate((3.0, 4.6, 6.2)):
            p = Vector((0, py, z)) + n * (pillar_radius(z) * 0.99 + 0.02)
            b.add("Runes", place(rune_glyph(0.55, f * 3 + j, "RuneGlow", 0.05), frame(p, out=n)))
        p = Vector((0, py, 7.55)) + n * (pillar_radius(7.55) * 0.99)
        b.add("Pillar", place(gem_setting(0.17, "MagicPink" if f % 2 else "AuroraCyan", "Gold", 4), frame(p, out=n)))
    # the floating crown crystal with a gold halo and orbiting gems
    b.add("Crown", place(cut_crystal(2.3, 0.55, "CrystalCyan"), M((0, py, 10.0))))
    b.add("Crown", place(cut_crystal(0.7, 0.55, "CrystalCyan"), Matrix.Translation((0, py, 10.08)) @ Matrix.Rotation(math.pi, 4, "X")))
    halo = bmesh.new()
    torus(halo, M((0, py, 10.7), (0.35, 0.2, 0)), 0.95, 0.05, 24, 4)
    b.add("Crown", [(halo, "Gold", 0.0, False)])
    for k in range(3):
        a = k * 2 * math.pi / 3
        b.add("Crown", place(cut_gem(0.13, "MagicPink"), M((1.0 * math.cos(a), py + 1.0 * math.sin(a), 10.7 + 0.3 * math.sin(a)))))
    # rune rings orbiting the pillar
    b.add("Orbit", place(engraved_rune_ring(1.9, "AuroraGreen", "ArcaneDeep", "Moonstone", 12), M((0, py, 5.1), (0.22, 0.1, 0))))
    b.add("Orbit", place(engraved_rune_ring(1.55, "RuneGlow", "ArcaneDeep", "RuneViolet", 10), M((0, py, 8.0), (-0.18, 0.15, 0.4))))
    # two more enchanted picks orbiting behind (decoration), floating rune stones
    b.add("OrbitPicks", pick_look(4, "base"), frame((-0.5, py + 1.0, 7.2), out=(-1, 0.35, 0.2)))
    b.add("OrbitPicks", pick_look(4, "base"), frame((0.5, py + 1.0, 3.4), out=(1, 0.45, -0.15)))
    for f in range(4):  # gold strips down the obelisk's corners
        a = f * math.pi / 2 + math.pi / 4
        c = Vector((math.cos(a), math.sin(a), 0))
        b.add("Pillar", trim_strip(Vector((0, py, 2.15)) + c * pillar_radius(2.15) * 1.414, Vector((0, py, 8.35)) + c * pillar_radius(8.35) * 1.414, 0.14, "Gold"))
        b.add("Pillar", place(cut_crystal_cluster(0.32, "RuneViolet" if f % 2 else "CrystalCyan", "Moonstone", 3), M((1.15 * math.cos(a), py + 1.15 * math.sin(a), 0.8), (0, 0, a))))
    for k in range(4):  # crystal shards floating round the crown
        a = k * math.pi / 2 + 0.5
        b.add("Crown", place(cut_crystal(0.6, 0.12, "RuneViolet" if k % 2 else "CrystalCyan"), M((1.45 * math.cos(a), py + 1.3 * math.sin(a), 9.3 + 0.35 * k), (0.3 * math.sin(a), 0.3 * math.cos(a), 0))))
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.9
        stone = rock((0.5, 0.35, 0.6), 1, 1, 0.3, seed=k)
        stone.transform(M((2.75 * math.cos(a), py + 2.4 * math.sin(a) * 0.9, 3.3 + 0.6 * k), (0.2, 0.1, a)))  # inside the pad
        b.add("RuneStones", [(stone, "StoneDark", 0.0, False)])
        n = Vector((math.cos(a), math.sin(a), 0))
        b.add("RuneStones", place(rune_glyph(0.32, k + 1, "RuneGlow", 0.03), frame(Vector((2.75 * math.cos(a), py + 2.4 * math.sin(a) * 0.9, 3.3 + 0.6 * k)) + n * 0.18, out=n)))
    # moonstone pedestals for the lamps, floating rune discs under the picks' pivots
    for sx in (-1, 1):
        ped = bmesh.new()
        lathe(ped, [(0, 0), (0.42, 0), (0.42, 0.12), (0.22, 0.25), (0.18, 0.65), (0.32, 0.75), (0.3, 0.8), (0, 0.8)], 6, M((sx * 2.5, -1.9, 0.8)))
        b.add("Pedestals", [(ped, "Moonstone", 0.0, False)])
        b.add("Pedestals", place(trim_ring(0.31, 0.75, "Gold", minor=0.04, segments=6), M((sx * 2.5, -1.9, 0.8))))
    work_at = {1: Vector((-1.15, -0.9, 4.3)), 2: Vector((1.15, -0.9, 6.4))}
    atts = {}
    for i in (1, 2):
        p = work_at[i]
        disc = bmesh.new()
        lathe(disc, [(0, -0.08), (0.42, -0.08), (0.46, 0.0), (0.42, 0.08), (0, 0.08)], 6)
        b.add("Pedestals", [(disc, "Moonstone", 0.0, False)], M((p.x, p.y, p.z - 1.95)))
        b.add("Pedestals", place(trim_ring(0.46, 0, "RuneGlow", True, minor=0.03, segments=6), M((p.x, p.y, p.z - 1.95))))
        work = frame(p, out=PICK_DIR_T4)
        b.add("Pick" + "AB"[i - 1], pick_look(4, "base"), work)
        b.add("Pick" + "AB"[i - 1], trim_ring(0.3, 0, "RuneGlow", True, minor=0.04, segments=16), frame(p, out=(1, 0, 0)))
        suffix = "" if i == 1 else "2"
        atts["Work" + suffix], atts["Trail" + suffix] = work, work
        atts["Gear" + str(i)] = up_((p.x, p.y, p.z - 1.87))
    atts.update({"Lamp1": up_((-2.5, -1.9, 1.6)), "Lamp2": up_((2.5, -1.9, 1.6)), "Steam1": up_((0, py, 12.4)),
                 "Hit": frame((0, -3.4, 0.3), out=(0, -1, 0.6)), "NamePlate": front((0, -3.27, 0.4)),
                 "Aura": up_((0, 0, 0.8)), "Top": up_((0, py, 12.4))})
    return atts


# ---------- tier 5: Legendary, the Frost Golem ----------

def golem_fist(kind="base"):
    """The raised forearm and fist along +Z from the elbow (the working part)."""
    pieces = []
    pieces += limb((0, 0, 0.2), (0, 0, 2.0), 0.62, 0.7, "DeepIce", seed=4.0)
    pieces += trim_ring(0.78, 1.95, "Gold", minor=0.13, segments=18)
    pieces += place(rivet_ring(0.82, 6, 0.07, "Gold"), M((0, 0, 1.75)))
    pieces += trim_ring(0.72, 0.65, "Gunmetal", minor=0.08, segments=18)

    def fist_shape(v):
        if v.co.z > 0.2:  # the knuckle end is broader and flatter
            v.co.x *= 1.1
    fist = rock((1.75, 1.45, 1.55), 1, 2, 0.35, fist_shape, 0.05, 2.0)
    fist.transform(M((0, 0, 2.85)))
    pieces.append((fist, "NavyIce", 0.0, False))
    for k in range(4):  # finger rolls over the front of the fist
        roll = bmesh.new()
        blob(roll, (-0.6 + 0.4 * k, 0.05, 3.55), (0.2, 0.55, 0.22), 2)
        pieces.append((roll, "Iron", 0.0, False))
    thumb = bmesh.new()
    blob(thumb, (0.88, -0.2, 3.05), (0.24, 0.42, 0.45), 2, rotation=(0.4, 0, 0))
    pieces.append((thumb, "Iron", 0.0, False))
    pieces += place(trim_strip((-0.85, 0.55, 3.0), (0.85, 0.55, 3.0), 0.16, "Gold"), Matrix())  # a gold knuckle band
    for x in (-0.6, 0.0, 0.6):
        pieces += place(rivet(0.06, "Gunmetal"), frame((x, 0.64, 3.0), out=(0, 1, 0)))
    return pieces


def t5_golem(b):
    # the plinth: gunmetal base, a stone top, gold trim, an aurora strip, vents, gems and a cracked crater
    b.add("Plinth", block((7.8, 7.8, 0.8), "Gunmetal", corner=0.8, edge=0.22))
    b.add("Plinth", place(block((7.2, 7.2, 0.25), "StoneLight", corner=0.6, edge=0.1), M((0, 0, 0.8))))
    b.add("PlinthTrim", place(block((7.9, 7.9, 0.14), "Gold", corner=0.82, edge=0.05), M((0, 0, 0.6))))
    b.add("PlinthTrim", trim_strip((-1.8, -3.92, 0.32), (1.8, -3.92, 0.32), 0.16, "AuroraGreen", True))
    for sx in (-1, 1):
        b.add("Plinth", place(vent(1.3, 0.36, 4, "Gunmetal", "SteelDark"), front((sx * 2.75, -3.86, 0.32))))
        b.add("Plinth", place(gem_setting(0.16, "AuroraCyan", "Gold", 4), M((sx * 3.3, 3.3, 1.05))))
        b.add("Plinth", place(cyl(0.34, 0.12, "Gold", 12), M((sx * 3.15, -3.15, 1.05))))  # the lamps' sockets
    crater = bmesh.new()
    torus(crater, Matrix.Translation((-1.55, -2.6, 1.05)) @ Matrix.Diagonal((1.1, 0.75, 0.35, 1)), 0.85, 0.3, 14, 6)
    b.add("Plinth", [(crater, "StoneDark", 0.0, False)])
    for k in range(5):
        a = k * 1.3 + 0.2
        b.add("Plinth", place(cut_crystal(0.45 + 0.1 * (k % 2), 0.16, "IceBlue", (0.5 * math.cos(a), 0.5 * math.sin(a)), glow=False), M((-1.55 + 1.0 * math.cos(a), -2.6 + 0.7 * math.sin(a), 1.0))))
    cx, cy, H = GOLEM_X, 0.75, GOLEM_RAISE
    # legs: rock thighs, gold-banded knee joints with gears, big rock feet with stone toes
    for sx in (-1, 1):
        x = cx + sx * 1.2
        b.add("Legs", limb((x, cy, 1.7), (x, cy, 3.4 + H), 0.86, 0.8, "DeepIce", seed=sx), organic=True)
        foot = rock((1.95, 2.3, 0.8), 1, 2, 0.5, None, 0.05, sx * 2.0)
        foot.transform(M((x, cy - 0.15, 1.42)))
        b.add("Legs", [(foot, "NavyIce", 0.0, False)], organic=True)
        for k in (-1, 0, 1):
            toe = bmesh.new()
            blob(toe, (x + k * 0.55, cy - 1.25, 1.32), (0.28, 0.27, 0.24), 1)
            b.add("Legs", [(toe, "Iron", 0.0, False)])
        knee = 2.55 + H / 2
        b.add("Joints", place(cyl(0.9, 0.5, "Gunmetal", 16), M((x, cy, knee - 0.25))))
        for dz in (-0.25, 0.25):
            b.add("Joints", place(trim_ring(0.93, 0, "Gold", minor=0.08, segments=18), M((x, cy, knee + dz))))
        for k in range(5):
            a = -math.pi / 2 + (k - 2) * 0.5
            b.add("Joints", place(rivet(0.06, "Gunmetal"), frame((x + 1.03 * math.cos(a), cy + 1.03 * math.sin(a), knee), out=(math.cos(a), math.sin(a), 0))))
        b.add("Joints", place(gear(0.42, 8, 0.18, 0.1, "Brass", "Gold"), frame((x + sx * 0.88, cy, knee - 0.1), out=(sx, 0, 0))))
    # the waist: a gunmetal machine joint between gold bands
    b.add("Waist", place(cyl(1.45, 0.75, "Gunmetal", 20), M((cx, cy, 3.1 + H))))
    for z in (3.12, 3.82):
        b.add("Waist", place(trim_ring(1.48, z + H, "Gold", minor=0.11, segments=20), M((cx, cy, 0))))
    for k in range(10):
        a = k * math.pi / 5
        b.add("Waist", place(rivet(0.07, "Gold"), frame((cx + 1.45 * math.cos(a), cy + 1.45 * math.sin(a), 3.47 + H), out=(math.cos(a), math.sin(a), 0))))
    # the torso: a broad-shouldered ice rock with stone plates, snow on the shoulders, a glowing frost core

    def torso_shape(v):
        if v.co.z > 0:
            v.co.x *= 1 + 0.18 * v.co.z / 2
        else:
            v.co.x *= 1 + 0.06 * v.co.z / 2
        if v.co.y < 0:
            v.co.y *= 0.9
    torso = rock((3.9, 2.9, 4.0), 2, 2, 0.55, torso_shape, 0.05, 1.0)
    torso.transform(M((cx, cy, 5.6 + H)))
    ts = Surface(torso)
    b.add("Torso", [(torso, "GlacierBlue", 0.0, False)], organic=True)
    for sx in (-1, 1):
        plate = bmesh.new()
        blob(plate, (cx + sx * 0.95, ts.front(cx + sx * 0.95, 6.4 + H) + 0.18, 6.4 + H), (0.75, 0.28, 0.65), 2, rotation=(0.1, 0, sx * 0.25))
        b.add("TorsoRock", [(plate, "NavyIce", 0.0, False)])
        belly = bmesh.new()
        blob(belly, (cx + sx * 0.7, ts.front(cx + sx * 0.7, 4.6 + H) + 0.2, 4.6 + H), (0.6, 0.25, 0.5), 1, rotation=(0, 0, sx * 0.3))
        b.add("TorsoRock", [(belly, "DeepIce", 0.0, False)])
        snow = bmesh.new()
        blob(snow, (cx + sx * 1.55, cy + 0.1, 7.45 + H), (0.85, 0.85, 0.28), 2)
        b.add("TorsoRock", [(snow, "SnowWhite", 0.0, False)])
    core_y = ts.front(cx, 5.9 + H)
    core = frame((cx, core_y + 0.05, 5.9 + H), out=(0, -1, 0.05))
    b.add("Core", place(gem_setting(0.5, "CrystalCyan", "Gold", 6), core))
    halo = bmesh.new()
    torus(halo, core @ M((0, 0, 0.02)), 0.9, 0.09, 24, 4)
    b.add("Core", [(halo, "AuroraCyan", 0.0, True)])
    for k in range(6):  # glowing frost cracks from the core across the chest
        a = k * math.pi / 3 + 0.35
        pts = []
        for j in range(5):
            rr = 0.95 + 0.2 * j
            aa = a + 0.18 * math.sin(j * 2.1 + k)
            x = cx + rr * math.cos(aa)
            z = 5.9 + H + rr * math.sin(aa) * 0.85
            pts.append(Vector((x, ts.front(x, z, 0.3) + 0.03, z)))
        crack = bmesh.new()
        sweep(crack, pts, 0.06, 4, radius_end=0.02)
        b.add("Core", [(crack, "AuroraCyan", 0.0, True)])
    b.add("Core", place(trim_ring(0.72, 0, "Gold", minor=0.1, segments=20), core @ M((0, 0, 0.08))))
    b.add("Core", place(rivet_ring(0.68, 6, 0.06, "Gunmetal"), core @ M((0, 0, 0.16))))
    b.add("Core", place(snowflake(0.35, "Diamond"), core @ M((0, 0, 0.62))))
    # crystals growing out of the back and shoulders
    for k, (dx, dz, out, h) in enumerate(((-0.9, 7.0, (-0.3, 1, 0.6), 1.4), (0.2, 7.3, (0.1, 1, 0.9), 1.8), (1.1, 6.6, (0.4, 1, 0.5), 1.2),
                                         (-0.3, 5.6, (-0.1, 1, 0.3), 1.0), (-1.9, 7.6, (-0.6, 0.4, 1), 1.0), (1.6, 7.7, (0.6, 0.5, 1), 0.9))):
        p = Vector((cx + dx, cy + 1.2, dz + H))
        glow = k % 2 == 1
        b.add("Shards", place(cut_crystal(h, 0.26, "CrystalCyan" if glow else "IceBlue", glow=glow), frame(p, out=out)))
    # the back: a frost engine with gold trim, two short vent stacks
    b.add("Back", place(lidded_box((1.9, 0.8, 1.6), "Gunmetal", "SteelDark", "Gold"), M((cx, cy + 1.55, 4.3 + H))))
    stack_tops = {}
    for sx in (-1, 1):
        b.add("Back", place(vent(0.6, 0.5, 3, "SteelDark", "Gunmetal"), frame((cx + sx * 0.45, cy + 1.96, 5.0 + H), out=(0, 1, 0))))
        stack = frame((cx + sx * 0.55, cy + 1.75, 5.9 + H), out=(sx * 0.15, 0.3, 1))
        b.add("Back", place(cyl(0.22, 1.1, "Gunmetal", 12), stack))
        b.add("Back", place(trim_ring(0.24, 1.0, "Gold", minor=0.05, segments=12), stack))
        stack_tops[sx] = (stack @ Vector((0, 0, 1.15, 1))).to_3d()
    # shoulders: gold-banded gunmetal ball joints with gears and rivets
    shoulders = {}
    for sx in (-1, 1):
        s = Vector((cx + sx * 2.35, cy, 7.0 + H))
        shoulders[sx] = s
        ball = bmesh.new()
        blob(ball, s, (0.72, 0.72, 0.72), 2)
        b.add("Joints", [(ball, "Gunmetal", 0.0, False)])
        out = frame(s + Vector((sx * 0.35, 0, 0)), out=(sx, 0, 0))
        b.add("Joints", place(trim_ring(0.66, 0, "Gold", minor=0.12, segments=18), out))
        b.add("Joints", place(rivet_ring(0.5, 6, 0.06, "Gold"), out @ M((0, 0, 0.3))))
        b.add("Joints", place(gear(0.38, 8, 0.16, 0.09, "Brass", "Gold"), out @ M((0, 0, 0.32))))
    # the right arm leans on its knuckles on the plinth
    sL, eL, wL = shoulders[1], Vector((cx + 2.8, cy - 0.3, 4.75 + H * 0.6)), Vector((cx + 2.6, cy - 1.15, 2.9))
    b.add("ArmRest", limb(sL, eL, 0.7, 0.62, "GlacierBlue", seed=5.0), organic=True)
    b.add("ArmRest", limb(eL, wL, 0.62, 0.72, "DeepIce", seed=6.0), organic=True)
    elbow = bmesh.new()
    blob(elbow, eL, (0.6, 0.6, 0.6), 2)
    b.add("ArmRest", [(elbow, "Gunmetal", 0.0, False)])
    b.add("ArmRest", place(trim_ring(0.66, 0, "Gold", minor=0.1, segments=16), Matrix.Translation(eL + (wL - eL).normalized() * 0.4) @ align_z(wL - eL)))
    b.add("ArmRest", place(trim_ring(0.72, 0, "Gold", minor=0.11, segments=16), Matrix.Translation(wL) @ align_z(wL - eL)))
    fistL = rock((1.5, 1.35, 1.3), 1, 2, 0.4, None, 0.05, 3.0)
    fistL.transform(M((wL.x + 0.05, wL.y - 0.35, 1.72)))
    b.add("ArmRest", [(fistL, "NavyIce", 0.0, False)], organic=True)
    for k in range(4):
        roll = bmesh.new()
        blob(roll, (wL.x - 0.5 + 0.33 * k, wL.y - 0.95, 1.45), (0.17, 0.2, 0.3), 1)
        b.add("ArmRest", [(roll, "Iron", 0.0, False)])
    # the left arm: the upper arm raised high, a hydraulic piston along it
    sR, eR = shoulders[-1], Vector((cx - 3.0, cy + 0.5, 11.6))
    b.add("ArmRaised", limb(sR, eR, 0.66, 0.58, "GlacierBlue", seed=7.0), organic=True)
    elbow = bmesh.new()
    blob(elbow, eR, (0.64, 0.64, 0.64), 2)
    b.add("ArmRaised", [(elbow, "Gunmetal", 0.0, False)])
    b.add("ArmRaised", place(trim_ring(0.64, 0, "Gold", minor=0.11, segments=16), Matrix.Translation(eR + Vector((-0.18, 0, 0))) @ align_z(Vector((1, 0, 0)))))
    b.add("ArmRaised", place(gear(0.42, 8, 0.16, 0.09, "Brass", "Gold"), frame(eR + Vector((-0.6, 0, 0)), out=(-1, 0, 0))))
    b.add("ArmRaised", piston(sR + Vector((-0.15, 0.66, 0.2)), eR + Vector((0.0, 0.6, -0.35)), 0.12, "Gunmetal", "SteelLight"))
    b.add("ArmRaised", place(trim_ring(0.68, 0, "Gold", minor=0.1, segments=16), Matrix.Translation(sR.lerp(eR, 0.45)) @ align_z(eR - sR)))
    # the head: an icy rock face with a heavy brow, glowing eyes in dark sockets, an icicle grin

    def head_shape(v):
        if v.co.z < -0.2 and v.co.y < 0:  # a jutting jaw
            v.co.y -= 0.22
            v.co.x *= 1.06
        if v.co.z > 0.6:
            v.co.z -= 0.1 * (v.co.z - 0.6)
    hz = 9.0 + H
    head = rock((2.7, 2.3, 2.35), 2, 2, 0.6, head_shape, 0.05, 9.0)
    head.transform(M((cx, cy - 0.3, hz)))
    hs = Surface(head)
    b.add("Head", [(head, "GlacierBlue", 0.0, False)], organic=True)
    b.add("Neck", place(cyl(0.85, 0.6, "Gunmetal", 16), M((cx, cy - 0.1, 7.35 + H))))
    b.add("Neck", place(trim_ring(0.88, 7.62 + H, "Gold", minor=0.1, segments=18), M((cx, cy - 0.1, 0))))
    eye_z = hz + 0.25
    for sx in (-1, 1):
        ex = cx + sx * 0.56
        ey = hs.front(ex, eye_z)
        socket = bmesh.new()
        blob(socket, (ex, ey + 0.08, eye_z), (0.5, 0.14, 0.44), 2)
        b.add("Head", [(socket, "EyeDark", 0.0, False)])
        eye_m = frame((ex, ey - 0.02, eye_z), out=(0, -1, 0.05))
        b.add("Eyes", place(cartoon_eye(0.4, "AuroraCyan", look=(-sx * 0.08, -0.12)), eye_m))
        glow_ring = bmesh.new()
        torus(glow_ring, eye_m @ M((0, 0, 0.04)), 0.45, 0.075, 16, 4)
        b.add("Eyes", [(glow_ring, "AuroraCyan", 0.0, True)])
        brow_rock = bmesh.new()
        blob(brow_rock, (cx + sx * 0.6, hs.front(cx + sx * 0.6, hz + 0.75) - 0.02, hz + 0.72), (0.55, 0.24, 0.17), 2, rotation=(0, -sx * 0.3, 0))
        b.add("Head", [(brow_rock, "NavyIce", 0.0, False)])
        cheek = bmesh.new()
        blob(cheek, (cx + sx * 1.05, hs.front(cx + sx * 1.05, hz - 0.3) + 0.12, hz - 0.3), (0.35, 0.18, 0.25), 1)
        b.add("Head", [(cheek, "IceBlue", 0.0, False)])
    nose = bmesh.new()
    blob(nose, (cx, hs.front(cx, hz) - 0.05, hz - 0.05), (0.24, 0.22, 0.3), 2)
    b.add("Head", [(nose, "DeepIce", 0.0, False)])
    mouth_z = hz - 0.6
    b.add("Head", place(grin(1.05, 0.16, "NavyIce", "FrostLight", 4), frame((cx, hs.front(cx, mouth_z) + 0.02, mouth_z), out=(0, -1, -0.15))))
    for k, dx in enumerate((-0.45, 0.0, 0.42)):  # icicles hanging from the chin
        chin_y = hs.front(cx + dx, hz - 1.0) + 0.15
        b.add("Head", place(cut_crystal(0.4 + 0.12 * (k % 2), 0.09, "IceBlue", glow=False), Matrix.Translation((cx + dx, chin_y, hz - 0.95)) @ Matrix.Rotation(math.pi, 4, "X")))
    # the crown of ice crystals on a gold circlet
    top = hs.top()
    crown_z = top - 0.45
    rx, ry, mx, my = hs.band(crown_z)
    circlet = bmesh.new()
    torus(circlet, Matrix.Translation((mx, my, crown_z)) @ Matrix.Diagonal((rx + 0.05, ry + 0.05, 1, 1)), 1.0, 0.12, 28, 4)
    b.add("Crown", [(circlet, "Gold", 0.0, False)])
    for k in range(7):
        a = -math.pi / 2 + (k - 3) * 0.55
        h = (1.6, 1.15, 1.35, 2.0, 1.35, 1.15, 1.6)[k]
        p = Vector((mx + rx * 0.92 * math.cos(a), my + ry * 0.92 * math.sin(a), crown_z + 0.05))
        b.add("Crown", place(cut_crystal(h, 0.22, "CrystalCyan" if k % 2 == 0 else "IceBlue", glow=(k % 2 == 0)), frame(p, out=(0.3 * math.cos(a), 0.3 * math.sin(a), 1))))
        if k % 2 == 0:
            b.add("Crown", place(gem_setting(0.09, "MagicPink" if k == 3 else "AuroraCyan", "Gold", 4), frame(p + Vector((0.14 * math.cos(a), 0.14 * math.sin(a), -0.12)), out=(math.cos(a), math.sin(a), 0))))
    for k in range(3):  # crystals behind, so the crown reads from every side
        a = math.pi / 2 + (k - 1) * 0.8
        p = Vector((mx + rx * 0.8 * math.cos(a), my + ry * 0.8 * math.sin(a), crown_z + 0.05))
        b.add("Crown", place(cut_crystal(1.4, 0.24, "IceBlue", glow=False), frame(p, out=(0.3 * math.cos(a), 0.3 * math.sin(a), 1))))
    # the raised fist (the working part)
    work = frame(eR, out=FIST_DIR_T5)
    b.add("Fist", golem_fist(), work, organic=True)
    springR = frame(sR + Vector((-0.62, 0.5, 0.3)), out=eR - sR)
    springL = frame(sL + Vector((0.55, 0.45, -0.25)), out=eL - sL)
    return {"Work": work, "Trail": work, "Lamp1": up_((-3.15, -3.15, 1.17)), "Lamp2": up_((3.15, -3.15, 1.17)),
            "Gear1": springR, "Gear2": springL, "Steam1": up_(stack_tops[1]), "Steam2": up_(stack_tops[-1]),
            "Hit": frame((-1.55, -3.4, 1.1), out=(0, -1, 0.6)), "NamePlate": front((0, -3.92, 0.45)),
            "Aura": up_((0, 0, 1.05)), "Crown": up_((mx, my, top)), "Eyes": frame((cx, hs.front(cx, eye_z), eye_z), out=(0, -1, 0)),
            "Top": up_((mx, my, crown_z + 2.0))}


# ---------- the framework's interface ----------

TIER_FNS = [t1_scrappy, t2_workshop, t3_frosttech, t4_enchanted, t5_golem]


def _works(atts):
    return [(k, atts[k]) for k in sorted(atts) if re.fullmatch(r"Work\d*", k)]


def UPGRADES(u, t, atts, b, fx):
    works = _works(atts)
    if u in (1, 5):  # steel pick heads, then diamond picks with a frost trail
        for i, (key, m) in enumerate(works):
            b.add(("Spikes" if t == 5 else "Pick") + "AB"[i], pick_look(t, "steel" if u == 1 else "diamond"), m)
        if u == 5:
            for i, (key, m) in enumerate(works):
                if t == 3:
                    points = [Vector((0, 0.0, 1.2 - 0.3 * k)) for k in range(9)]
                elif t == 5:
                    points = swing_arc(3.2, 0.2, 1.2, 12)
                else:
                    points = swing_arc(PICK_LEN[t], 0.15, 1.1, 10)
                fx.add("Trail" + "AB"[i], place(frost_trail(points), m))
    elif u == 2:  # the lantern on the post (warning lamps, then glowing gems from Frost-tech on)
        for key in ("Lamp1", "Lamp2"):
            if key in atts:
                b.add("Lamp" + key[-1], place(tier_lamp(t), atts[key]))
    elif u == 3:  # the spring that bounces with each swing
        length, radius, wire, cap, ring, turns = SPRING_LOOK[t]
        for key in ("Gear1", "Gear2"):
            if key in atts:
                b.add("Spring" + key[-1], place(spring(length, radius, wire, cap, turns, cap_glow=ring), atts[key]))
    else:  # ice chips
        fx.add("Hit", place(ice_chips(t), atts["Hit"]))


def AURA(atts, fx):
    """Frost Golem: swirling snow flurries round the golem and a frost ring creeping across the ground."""
    centre = atts["Aura"].to_translation()
    for k in range(22):  # flurries spiralling up round the golem
        a = k * 0.95
        r = 3.3 - 0.05 * k
        p = Vector((centre.x + GOLEM_X + r * math.cos(a), centre.y + 0.6 + r * math.sin(a) * 0.95, centre.z + 0.8 + 0.5 * k))
        if k % 2:
            fx.add("AuraFlurries", place(snowflake(0.22 + 0.04 * (k % 3), "SnowWhite"), M(p, (a, 0.4 * k, a))))
        else:
            flake = bmesh.new()
            blob(flake, p, (0.12, 0.12, 0.12), 1)
            fx.add("AuraFlurries", [(flake, "SnowWhite", 0.0, False)])
        if k % 4 == 0:  # streaks that show the swirl
            streak = bmesh.new()
            pts = [Vector((centre.x + GOLEM_X + r * math.cos(a - 0.12 * j), centre.y + 0.6 + r * 0.95 * math.sin(a - 0.12 * j), p.z - 0.06 * j)) for j in range(6)]
            sweep(streak, pts, 0.035, 4, radius_end=0.01)
            fx.add("AuraFlurries", [(streak, "FrostLight", 0.0, True)])
    ring = bmesh.new()
    torus(ring, M((centre.x, centre.y, centre.z + 0.03)), 3.45, 0.06, 40, 4)
    fx.add("AuraFrost", [(ring, "AuroraCyan", 0.0, True)])
    inner = bmesh.new()
    torus(inner, M((centre.x, centre.y, centre.z + 0.02)), 2.9, 0.035, 40, 4)
    fx.add("AuraFrost", [(inner, "FrostLight", 0.0, True)])
    for k in range(16):  # frost spikes creeping out round the ring
        a = k * 2 * math.pi / 16 + 0.1
        p = Vector((centre.x + 3.2 * math.cos(a), centre.y + 3.2 * math.sin(a), centre.z))
        fx.add("AuraFrost", place(cut_crystal(0.35 + 0.15 * (k % 3), 0.1, "IceBlue" if k % 2 else "Diamond", glow=False),
                                  frame(p, out=(0.9 * math.cos(a), 0.9 * math.sin(a), 1))))
    for k in range(8):  # frost lines branching out from the golem's feet
        a = k * math.pi / 4 + 0.3
        pts = [Vector((centre.x + GOLEM_X * (1 - s) + (1.2 + 2.0 * s) * math.cos(a + 0.25 * math.sin(6 * s)),
                       centre.y + 0.4 * (1 - s) + (1.2 + 2.0 * s) * math.sin(a + 0.25 * math.sin(6 * s)), centre.z + 0.03)) for s in (0, 0.25, 0.5, 0.75, 1.0)]
        line = bmesh.new()
        sweep(line, pts, 0.045, 4, radius_end=0.015)
        fx.add("AuraFrost", [(line, "FrostLight", 0.0, True)])
