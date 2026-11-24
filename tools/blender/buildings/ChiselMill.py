# ChiselMill.py - the Chisel Mill's five tiers and upgrade sets, for tools/blender/buildings/framework.py.
# A water wheel turns an axle and the axle drives a row of chisels that strike the ice (front, -Y).
#   1 Scrappy: a wooden overshot water wheel fed by a plank flume, a trestle axle, a chisel bar.
#   2 Workshop: a brass gear mill: a brass bucket wheel in a stone mill race, a copper cistern and pipe,
#      a gearbox with a big drive gear, a brass crosshead on guide columns.
#   3 Frost-tech: a crystal turbine in a white shroud, fed by a tank of glowing water.
#   4 Enchanted: a waterwheel floating in mid-air under a waterfall pouring out of a rune portal.
#   5 Legendary: the Kraken Mill: a crowned kraken whose tentacles grip chisels and swing mallets, with
#      brass bands, a gear hub and a water wheel on its side.
# (Run: blender -b --factory-startup --python tools/blender/buildings/run.py -- ChiselMill build render export)

TIER_Q = {"Scrappy": {"round": 1.0}, "Workshop": {"round": 1.0}, "Frost-tech": {"round": 1.1},
          "Enchanted": {"round": 1.5, "minor": 1.25, "corner": 3}, "Legendary": {"round": 1.0}}

T1_DIR = Vector((0, -1, -0.6)).normalized()
T2_DIR = Vector((0, -1, -0.65)).normalized()
T3_DIR = Vector((0, -1, -0.55)).normalized()
T4_DIR = Vector((0, -1, -0.75)).normalized()
T5_DIR = Vector((0, -1, -0.7)).normalized()

# the chisel row at each tier (count, spacing, length, width) and its three looks: base, steel (1st
# upgrade), crystal (5th upgrade)
ROW = {1: dict(n=3, spacing=1.25, length=1.7, width=0.4), 2: dict(n=4, spacing=0.9, length=1.7, width=0.38),
       3: dict(n=4, spacing=1.0, length=1.75, width=0.42), 4: dict(n=4, spacing=1.15, length=1.8, width=0.44),
       5: dict(n=1, spacing=0.0, length=2.1, width=0.56)}
LOOKS = {
    1: (dict(handle="PineDark", blade="Iron", ferrule="Rust"),
        dict(handle="PineLight", blade="SteelLight", ferrule="Steel", cap="Steel"),
        dict(handle="PineLight", blade="CrystalCyan", ferrule="Brass", cap="Brass", glow=True)),
    2: (dict(handle="Pine", blade="Iron", ferrule="Brass", cap="Brass"),
        dict(handle="Pine", blade="SteelLight", ferrule="Brass", cap="Copper"),
        dict(handle="Brass", blade="CrystalCyan", ferrule="Gold", cap="Gold", glow=True)),
    3: (dict(handle="SnowWhite", blade="GlacierBlue", ferrule="SteelLight", cap="NavyIce"),
        dict(handle="SteelLight", blade="SteelLight", ferrule="GlacierBlue", cap="NavyIce"),
        dict(handle="SnowWhite", blade="CrystalCyan", ferrule="AuroraCyan", cap="NavyIce", glow=True)),
    4: (dict(handle="ArcaneDeep", blade="Moonstone", ferrule="Gold", cap="Gold"),
        dict(handle="ArcaneDeep", blade="SteelLight", ferrule="Gold", cap="Gold"),
        dict(handle="Moonstone", blade="CrystalCyan", ferrule="Gold", cap="Gold", glow=True)),
    5: (dict(handle="Gunmetal", blade="Brass", ferrule="Gold", cap="Gold"),
        dict(handle="Gold", blade="SteelLight", ferrule="Gold", cap="Gold"),
        dict(handle="Gold", blade="CrystalCyan", ferrule="Gold", cap="Gold", glow=True)),
}
GEAR_LOOK = {1: (0.6, "Pine", "Iron"), 2: (0.75, "Brass", "Copper"), 3: (0.75, "SteelLight", "AuroraCyan"),
             4: (0.8, "Moonstone", "Gold"), 5: (0.95, "Brass", "Gold")}
GLOW_WATER = {}  # [tier] = [function() -> pieces]: that tier's water, glowing (the 5th upgrade)
_raw_block = globals().get("_rb0", rounded_block)  # the kit's rounded_block without the quality floor


# ---------- cheap shapes (one segment per rounded edge) ----------

def low_block(size, swatch, matrix=Matrix(), corner=0.06, edge=0.04, glow=False):
    """A rounded box centred on the matrix with single-segment rounding (about 60 triangles)."""
    bm = bmesh.new()
    _raw_block(bm, size, matrix, corner=corner, edge=edge, corner_seg=1, edge_seg=1)
    return [(bm, swatch, 0.0, glow)]


def low_beam(p0, p1, width, swatch, depth=None):
    p0, p1 = Vector(p0), Vector(p1)
    return low_block((width, depth or width, (p1 - p0).length), swatch, Matrix.Translation((p0 + p1) / 2) @ align_z(p1 - p0), corner=width * 0.18, edge=width * 0.12)


def wood_beam(p0, p1, width, swatch="Pine", grain="PineDark", faces=(1,)):
    """A cheap wooden beam with grain grooves on the faces you see."""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    pieces = low_block((width, width, L), swatch, M((0, 0, L / 2)), corner=width * 0.18, edge=width * 0.12)
    for k in faces:
        a = k * math.pi / 2
        n = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-n.y, n.x, 0))
        for off in (-0.18, 0.2):
            pts = [n * (width / 2 + 0.003) + side * (off * width + 0.025 * math.sin(t * 1.6 + k + off * 9)) + Vector((0, 0, L * (0.08 + 0.84 * t / 5))) for t in range(6)]
            g = bmesh.new()
            sweep(g, pts, 0.018, 3)
            pieces.append((g, grain, 0.0, False))
    return place(pieces, Matrix.Translation(p0) @ align_z(p1 - p0))


def band(radius, minor, matrix, swatch, segments=16, glow=False):
    """A thin ring (a strap, a hoop, a glowing trim) with a 4-sided section."""
    bm = bmesh.new()
    torus(bm, matrix, radius, minor, segments, 4)
    return [(bm, swatch, 0.0, glow)]


def low_gear(radius, teeth, thick, swatch, hub_swatch):
    """A cheap solid gear turning about Z, centred on its axle: square-ish teeth, a raised hub, spoke ribs."""
    root = radius * 0.82
    outline = []
    for i in range(teeth):
        for frac, r in ((0.0, root), (0.2, radius), (0.5, radius), (0.7, root)):
            a = 2 * math.pi * (i + frac) / teeth
            outline.append(Vector((r * math.cos(a), r * math.sin(a), 0)))
    g = bmesh.new()
    loft(g, [[p + Vector((0, 0, z)) for p in outline] for z in (-thick / 2, thick / 2)])
    pieces = [(g, swatch, 0.0, False)]
    h = bmesh.new()
    cylinder(h, (0, 0, -thick * 0.8), radius * 0.28, thick * 1.6, 10)
    pieces.append((h, hub_swatch, 0.0, False))
    for k in range(3):
        pieces += low_block((radius * 1.3, radius * 0.12, thick * 0.4), hub_swatch, M((0, 0, thick / 2 + 0.02), (0, 0, k * math.pi / 3)), corner=0.02, edge=0.01)
    return pieces


# ---------- shared pieces ----------

def chisel(length=1.7, width=0.4, handle="PineDark", blade="Iron", ferrule="Iron", cap=None, glow=False):
    """A chisel along +Z: a turned handle from z = 0, a ferrule, a flat blade ground to an edge at
    z = length (the edge runs along X, so a row of chisels lines up across the ice)."""
    pieces = []
    hl = length * 0.46
    h = bmesh.new()
    lathe(h, [(0, 0), (width * 0.3, 0), (width * 0.34, hl * 0.35), (width * 0.29, hl), (0, hl)], 10)
    pieces.append((h, handle, 0.0, False))
    f = bmesh.new()
    cylinder(f, (0, 0, hl - 0.08), width * 0.37, 0.18, 10)
    pieces.append((f, ferrule, 0.0, False))
    if cap:  # a strike cap on the butt
        c = bmesh.new()
        cylinder(c, (0, 0, -0.12), width * 0.4, 0.16, 10, top=width * 0.33)
        pieces.append((c, cap, 0.0, False))
    sections = []
    for z, w, d in ((hl + 0.08, width * 0.42, width * 0.42), (hl + 0.3, width * 0.8, width * 0.3),
                    (length * 0.84, width, width * 0.24), (length, width * 1.04, 0.04)):
        sections.append([Vector((x, y, z)) for x, y in rounded_rect(w, d, min(w, d) * 0.3, 1)])
    bl = bmesh.new()
    loft(bl, sections)
    if glow:
        faceted(bl)  # crystal chisels: cut facets
    pieces.append((bl, blade, 0.0, glow))
    return pieces


def chisel_row(n, spacing, length, width, **look):
    pieces = []
    for i in range(n):
        pieces += place(chisel(length, width, **look), M(((i - (n - 1) / 2) * spacing, 0, 0)))
    return pieces


def water_wheel(radius, width, paddles=10, rim="Pine", board="PineLight", spoke="PineDark", hub="Iron",
                bars=3, buckets=None, segments=20):
    """A water wheel turning about Z, centred on its axle so it spins true: two rims, paddles (or L-shaped
    buckets) between them, spoke bars across each rim and a hub."""
    pieces = []
    rw, t = radius * 0.13, 0.1
    for s in (-1, 1):
        z = s * (width / 2 - t / 2)
        ring = bmesh.new()
        lathe(ring, [(radius - rw, z - t / 2), (radius, z - t / 2), (radius, z + t / 2), (radius - rw, z + t / 2), (radius - rw, z - t / 2)], segments)
        pieces.append((ring, rim, 0.0, False))
        for k in range(bars):
            sp = bmesh.new()
            box(sp, (0, 0, z), (radius * 2 - rw, rw * 0.55, t * 0.8), (0, 0, k * math.pi / bars + 0.2))
            pieces.append((sp, spoke, 0.0, False))
    pd = radius * 0.34
    for k in range(paddles):
        a = 2 * math.pi * k / paddles
        pieces += low_block((pd, 0.09, width - 0.04), board, M(((radius - pd / 2 + 0.06) * math.cos(a), (radius - pd / 2 + 0.06) * math.sin(a), 0), (0, 0, a)), corner=0.03, edge=0.03)
        if buckets:  # the bucket's lip: a short plate across the paddle's outer end
            pieces += low_block((0.08, pd * 0.6, width - 0.06), buckets, M(((radius - 0.02) * math.cos(a) - pd * 0.25 * math.sin(a), (radius - 0.02) * math.sin(a) + pd * 0.25 * math.cos(a), 0), (0, 0, a)), corner=0.03, edge=0.03)
    h = bmesh.new()
    cylinder(h, (0, 0, -width / 2 - 0.14), radius * 0.17, width + 0.28, 12)
    pieces.append((h, hub, 0.02, False))
    return pieces


def stream(points, radius, swatch, glow=False, end=1.2, segments=10):
    """Falling water: a tube along the points, widening as it falls."""
    s = bmesh.new()
    sweep(s, [Vector(p) for p in points], radius, segments, radius_end=radius * end)
    return [(s, swatch, 0.0, glow)]


def water_slab(size, centre, swatch="GlacierBlue", glow=False, turn=0.0):
    return low_block(size, swatch, M(centre, (0, 0, turn)), corner=min(size[0], size[1]) * 0.15, edge=min(0.03, size[2] * 0.4), glow=glow)


def water_disc(radius, z, swatch="GlacierBlue", glow=False, centre=(0, 0), segments=24):
    bm = bmesh.new()
    lathe(bm, [(0, z - 0.05), (radius, z - 0.05), (radius, z), (0, z)], segments, M((centre[0], centre[1], 0)))
    return [(bm, swatch, 0.0, glow)]


def teardrop(size, swatch, glow=False):
    d = bmesh.new()
    lathe(d, [(0, -size), (size * 0.75, -size * 0.45), (size * 0.6, size * 0.3), (0, size * 1.3)], 8)
    return [(d, swatch, 0.0, glow)]


def splash_standin(t, scale=1.0):
    """The 3rd upgrade's splash stand-in (particles in game): a foam ring and droplets thrown up."""
    water = {1: "IceBlue", 2: "IceBlue", 3: "AuroraCyan", 4: "PolarTeal", 5: "IceBlue"}[t]
    pieces = band(0.55, 0.1, Matrix.Diagonal((scale, scale, 0.5, 1)) @ M((0, 0, 0.1)), "SnowWhite", 16)
    for k in range(9):
        a = k * 2.4
        r = (0.35 + 0.15 * (k % 3)) * scale
        out = Vector((math.cos(a), math.sin(a), 1.6)).normalized()
        pieces += place(teardrop(0.11 * scale, water, t >= 3), Matrix.Translation((r * math.cos(a), r * math.sin(a), (0.35 + 0.28 * (k % 4)) * scale)) @ align_z(out))
    return pieces


def rope_wrap(p, axis, radius, turns=2, swatch="PineLight"):
    pieces = []
    for k in range(turns):
        pieces += band(radius, 0.055, Matrix.Translation(Vector(p) + Vector(axis).normalized() * (k * 0.11 - 0.05)) @ align_z(axis), swatch, 10)
    return pieces


def smooth_path(ctrl, per=5):
    """Catmull-Rom points through the control points (organic curves for tentacles and pipes)."""
    P = [Vector(c) for c in ctrl]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out


def tier_water(t, fn):
    """Record a glowing copy of a tier's water for its 5th upgrade."""
    GLOW_WATER.setdefault(t, []).append(fn)


def ring4(radius, z=0.0, swatch="Gold", glow=False, minor=0.09, segments=24):
    """A trim band with a 4-sided section (half the triangles of the kit's trim ring)."""
    return band(radius, minor, M((0, 0, z)), swatch, segments, glow)


def flip_if(s):
    return Matrix.Rotation(math.pi, 4, "X") if s < 0 else Matrix()


# ---------- tier 1: Scrappy, the wooden water wheel ----------

def scrappy(b):
    GLOW_WATER[1] = []
    top = 0.5
    for x in (-3.3, 1.8):  # runners on stones, a plank deck on top
        b.add("Deck", low_beam((x, -2.2, 0.12), (x, 2.0, 0.12), 0.24, "PineDark"))
        for y in (-1.9, 1.7):
            stone = bmesh.new()
            blob(stone, (x, y, 0.06), (0.36, 0.3, 0.14), 1, floor=0.0)
            b.add("Deck", [(stone, "StoneDark", 0.0, False)])
    for k, (y, sw, gr) in enumerate(((-1.47, "Pine", "PineDark"), (-0.08, "PineLight", "Pine"), (1.31, "PineDark", "RustDark"))):
        b.add("Deck", place(plank(6.3 - 0.3 * (k % 2), 1.36, 0.26, sw, gr, k == 0, k * 1.3), M((-0.75 - 0.15 * (k % 2), y, 0.24), (0, 0, (-1) ** k * 0.015))))
    # the tub under the wheel: board walls with iron straps, water inside
    tx, ty = 3.3, 0.3
    for sx in (-1, 1):
        b.add("Tub", low_block((0.14, 3.64, 0.78), "Pine", M((tx + sx * 0.66, ty, 0.39))))
    for sy in (-1, 1):
        b.add("Tub", low_block((1.46, 0.14, 0.78), "PineDark", M((tx, ty + sy * 1.75, 0.39))))
    b.add("Tub", low_block((1.2, 3.4, 0.1), "PineDark", M((tx, ty, 0.05))))
    b.add("Tub", band(1.0, 0.04, Matrix.Translation((tx, ty, 0.55)) @ Matrix.Diagonal((0.76, 1.86, 1, 1)), "Iron", 16))
    b.add("Water", water_slab((1.2, 3.38, 0.08), (tx, ty, 0.6)))
    tier_water(1, lambda: water_slab((1.22, 3.4, 0.09), (tx, ty, 0.61), "AuroraCyan", True))
    # the wheel (spins about X)
    wheel_at = frame((tx, ty, 2.35), out=(1, 0, 0))
    b.add("Wheel", place(water_wheel(1.85, 0.8, 8, "Pine", "PineLight", "PineDark", "Iron", 2), wheel_at))
    # posts: the outer bearing post and the flume post, both outside the tub
    for y, z1 in ((ty, 2.75), (1.4, 4.3)):
        b.add("Frame", wood_beam((4.25, y, 0.0), (4.25, y, z1), 0.34, "PineDark", "RustDark", (0,)))
        stone = bmesh.new()
        blob(stone, (4.25, y, 0.06), (0.36, 0.32, 0.14), 1, floor=0.0)
        b.add("Frame", [(stone, "StoneDark", 0.0, False)])
    b.add("Frame", low_block((0.46, 0.56, 0.4), "Iron", M((4.25, ty, 2.35))))
    # the two trestles holding the axle, rope-lashed, with iron bearing blocks
    for x in (2.25, -3.35):
        for sy in (-1, 1):
            b.add("Frame", wood_beam((x, ty + sy * 1.2, top), (x, ty + sy * 0.1, 2.55), 0.3, "Pine", "PineDark", (3,) if x > 0 else ()))
        b.add("Frame", low_beam((x, ty - 0.82, 1.3), (x, ty + 0.82, 1.3), 0.2, "PineDark"))
        b.add("Frame", low_block((0.44, 0.56, 0.38), "Iron", M((x, ty, 2.34))))
        b.add("Frame", rope_wrap((x, ty, 1.3), (0, 1, 0), 0.16, 1))
    # the axle (turns with the wheel): cranks drive the chisel bar's connecting rods
    b.add("Axle", place(cyl(0.16, 8.2, "PineDark", 10, bevel=0.0), frame((-3.75, ty, 2.35), out=(1, 0, 0))))
    for x in (-1.55, 0.15):
        b.add("Axle", low_block((0.16, 0.36, 0.62), "PineLight", M((x, ty, 2.56))))
        b.add("Axle", place(cyl(0.07, 0.42, "Iron", 8, bevel=0.0), frame((x - 0.21, ty, 2.78), out=(1, 0, 0))))
    # the front guide frame and the chisel bar
    for x in (-3.0, 1.6):
        b.add("Frame", wood_beam((x, -1.75, top), (x, -1.75, 3.3), 0.34, "PineLight", "Pine", (3,)))
        b.add("Frame", low_beam((x, -1.75, 2.9), (x, -0.2, top + 0.02), 0.2, "PineDark"))
        b.add("Frame", low_block((0.48, 0.5, 0.12), "Iron", M((x, -1.75, 2.42))))
    b.add("Frame", low_beam((-3.3, -1.75, 3.4), (1.9, -1.75, 3.4), 0.3, "PineDark"))
    for x in (-3.0, 1.6):
        b.add("Frame", place(rivet(0.06, "Iron"), front((x, -1.91, 3.4))))
    b.add("Frame", low_block((0.5, 0.06, 0.4), "PatchGreen", M((-0.7, -1.92, 3.4), (0, 0, 0.1))))
    b.add("Hammer", low_beam((-2.82, -1.75, 2.15), (1.42, -1.75, 2.15), 0.4, "PineDark"))
    for x in (-1.55, 0.15):
        b.add("Hammer", low_beam((x - 0.21, ty - 0.02, 2.78), (x - 0.21, -1.55, 2.2), 0.16, "PineLight"))
        b.add("Hammer", rope_wrap((x - 0.21, -1.4, 2.25), (0, 1, -0.3), 0.13, 1, "Rust"))
    work = frame((-0.7, -1.85, 2.15), out=T1_DIR)
    # the flume: a plank trough on legs, water running in it and pouring onto the wheel
    fy0, fy1, fz = 0.75, 4.75, 4.32
    L, cy = fy1 - fy0, (fy0 + fy1) / 2
    b.add("Flume", place(plank(L, 0.8, 0.12, "Pine", "PineDark", False, 0.7), M((tx, cy, fz), (0, 0, math.pi / 2))))
    for sx in (-1, 1):
        b.add("Flume", low_block((0.1, L, 0.36), "PineLight", M((tx + sx * 0.42, cy, fz + 0.18))))
        b.add("Flume", low_beam((tx + sx * 0.4, 3.9, 0), (tx + sx * 0.4, 3.9, fz), 0.24, "PineDark"))
    b.add("Flume", low_beam((tx - 0.62, 3.9, fz - 0.1), (tx + 0.62, 3.9, fz - 0.1), 0.2, "Pine"))
    b.add("Flume", low_beam((2.45, 1.4, fz - 0.12), (4.45, 1.4, fz - 0.12), 0.22, "PineDark"))
    b.add("Flume", low_beam((2.6, 1.4, 0.0), (2.6, 1.4, fz - 0.2), 0.26, "PineDark"))
    b.add("Water", water_slab((0.7, L - 0.1, 0.06), (tx, cy, fz + 0.2)))
    pour = [(tx, 0.82, fz + 0.24), (tx, 0.62, fz + 0.16), (tx, 0.5, 4.3)]
    b.add("Water", stream(pour, 0.2, "IceBlue"))
    tier_water(1, lambda: water_slab((0.72, L - 0.08, 0.07), (tx, cy, fz + 0.205), "AuroraCyan", True) + stream(pour, 0.22, "AuroraCyan", True))
    # junk: a bucket, a rope coil, a crate
    bucket = bmesh.new()
    lathe(bucket, [(0, 0), (0.28, 0), (0.38, 0.55), (0.34, 0.55), (0.25, 0.06), (0, 0.06)], 12, M((-3.0, 1.35, top), (0.1, 0, 0)))
    wire = bmesh.new()
    sweep(wire, [V(-3.38, 1.4, top + 0.55), V(-3.3, 1.42, top + 0.85), V(-3.0, 1.45, top + 0.98), V(-2.7, 1.42, top + 0.85), V(-2.62, 1.4, top + 0.55)], 0.025, 5)
    b.add("Junk", [(bucket, "Steel", 0.0, False), (wire, "Iron", 0.0, False)])
    for k in range(2):
        b.add("Junk", band(0.34 - 0.04 * k, 0.07, M((-1.4, 1.35, top + 0.07 + 0.12 * k)), "PineLight", 12))
    b.add("Junk", low_block((0.8, 0.7, 0.6), "Pine", M((0.6, 1.4, top + 0.3), (0, 0, 0.2))))
    b.add("Junk", low_beam((0.22, 1.1, top + 0.3), (1.0, 1.26, top + 0.3), 0.08, "PineDark"))
    atts = {"Work": work, "Trail": work, "Hit": frame((-0.7, -3.8, 0.9), out=(0, -1, 0.6)),
            "Lamp1": up_((-3.0, -1.75, 3.56)), "Lamp2": up_((1.6, -1.75, 3.56)),
            "Gear1": frame((-3.82, ty, 2.35), out=(-1, 0, 0)), "Gear2": frame((4.45, ty, 2.35), out=(1, 0, 0)),
            "Steam1": up_((tx, -0.9, 0.66)), "Steam2": up_((tx, 0.5, 4.3)),
            "NamePlate": front((-0.75, -2.22, 0.25)), "Aura": up_((0, 0, 0.5)), "Top": up_((tx, 2.7, 4.7))}
    return atts


# ---------- tier 2: Workshop, the brass gear mill ----------

def workshop(b):
    GLOW_WATER[2] = []
    base = 0.4
    b.add("Base", low_block((9.0, 7.2, base), "Iron", M((0, 0, base / 2)), corner=0.5, edge=0.1))
    b.add("Base", low_block((9.1, 7.3, 0.1), "Brass", M((0, 0, base - 0.07)), corner=0.52, edge=0.03))
    for k in range(5):
        b.add("Base", place(rivet(0.06, "Brass"), front((-4.0 + k * 2.0, -3.61, 0.18))))
    top = base + 0.22
    for k, y in enumerate((-2.7, -1.15, 0.4, 1.95)):  # the plank floor of the mill
        b.add("Floor", place(plank(6.0, 1.5, 0.22, "Pine" if k % 2 else "PineLight", "PineDark", k == 0, k * 0.9), M((-1.25, y, base))))
    # the mill race: stone walls, water running under the wheel
    wx, wy = 3.25, 0.2
    for x in (2.2, 4.3):
        b.add("Race", low_block((0.36, 7.0, 0.62), "StoneLight", M((x, 0, base + 0.31)), corner=0.1, edge=0.06))
    b.add("Water", water_slab((1.74, 7.0, 0.1), (wx, 0, 0.72)))
    tier_water(2, lambda: water_slab((1.76, 7.02, 0.11), (wx, 0, 0.73), "AuroraCyan", True))
    # the brass bucket wheel (spins about X) and its bearing pedestals
    wheel_at = frame((wx, wy, 3.0), out=(1, 0, 0))
    b.add("Wheel", place(water_wheel(2.15, 0.95, 10, "Brass", "Copper", "Iron", "SteelDark", 3, buckets="Copper", segments=24), wheel_at))
    for x in (2.2, 4.3):
        b.add("Pedestal", low_block((0.5, 0.9, 2.05), "SteelDark", M((x, wy, 2.04)), corner=0.12, edge=0.06))
        b.add("Pedestal", low_block((0.6, 1.0, 0.28), "Brass", M((x, wy, 3.0)), corner=0.12, edge=0.05))
    b.add("Axle", place(cyl(0.2, 3.0, "Steel", 12, bevel=0.0), frame((1.7, wy, 3.0), out=(1, 0, 0))))
    # the copper gearbox with its big brass drive gear and a dial
    b.add("Gearbox", place(lidded_box((1.4, 1.8, 3.1), "Copper", "Copper", "Brass"), M((1.0, wy, top))))
    b.add("Gearbox", place(dial(0.24, "Cream", "Brass", "WarnRed", 0.4), frame((1.0, wy - 0.92, 3.3), out=(0, -1, 0))))
    b.add("DriveGear", place(spoked_gear(1.0, 10, 0.22, 0.16, 4, "Brass", "Copper"), frame((1.0, wy - 1.0, 2.0), out=(0, -1, 0))))
    # the cam housing: a long riveted iron case; pistons drive the brass crosshead
    b.add("CamHousing", low_block((4.0, 1.2, 2.6), "SteelDark", M((-1.85, -0.1, top + 1.3)), corner=0.25, edge=0.1))
    b.add("CamHousing", low_block((4.06, 1.26, 0.12), "Brass", M((-1.85, -0.1, top + 2.5)), corner=0.27, edge=0.04))
    for x in (-3.0, -0.9):
        b.add("CamHousing", place(inset_panel(1.5, 1.3, 0.05, "Steel", "Iron", False), front((x, -0.72, 1.85))))
    b.add("CamHousing", place(vent(0.9, 0.5, 4, "Iron", "Brass"), frame((-1.85, 0.51, 2.0), out=(0, 1, 0))))
    b.add("CamGear", place(gear(0.5, 7, 0.2, 0.12, "Brass", "Iron"), frame((-0.4, -0.77, 2.6), out=(0, -1, 0))))
    for x in (-3.0, -0.7):
        b.add("Pistons", piston((x, -0.75, 2.9), (x, -2.05, 2.55), 0.16, "Iron", "SteelLight"))
    for x in (-3.85, 0.25):  # guide columns with brass caps
        b.add("Columns", place(cyl(0.17, 3.8, "Iron", 12, bevel=0.0), M((x, -2.3, top))))
        b.add("Columns", place(cyl(0.28, 0.2, "Brass", 12), M((x, -2.3, top))))
        b.add("Columns", place(cyl(0.27, 0.22, "Brass", 12), M((x, -2.3, top + 3.8))))
    b.add("Columns", low_beam((-4.1, -2.3, top + 3.9), (0.5, -2.3, top + 3.9), 0.26, "SteelDark"))
    b.add("Crosshead", low_block((3.8, 0.62, 0.66), "Brass", M((-1.8, -2.3, 2.23)), corner=0.14, edge=0.07))
    b.add("Crosshead", low_block((3.86, 0.66, 0.1), "Iron", M((-1.8, -2.3, 2.55)), corner=0.15, edge=0.03))
    for x in (-3.85, 0.25):
        b.add("Crosshead", band(0.24, 0.07, M((x, -2.3, 2.23)), "Iron", 12))
    for k in range(3):
        b.add("Crosshead", place(rivet(0.05, "Copper"), front((-3.2 + k * 1.4, -2.62, 2.4))))
    work = frame((-1.8, -2.5, 2.15), out=T2_DIR)
    # the copper cistern on iron legs, the pipe to the wheel and its valve
    cx, cy = -2.6, 2.05
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add("Cistern", low_beam((cx + sx * 0.8, cy + sy * 0.75, top), (cx + sx * 0.75, cy + sy * 0.7, 4.7), 0.22, "Iron"))
        b.add("Cistern", low_beam((cx + sx * 0.8, cy - 0.75, 1.6), (cx + sx * 0.8, cy + 0.75, 1.6), 0.12, "SteelDark"))
    b.add("Cistern", low_beam((cx - 0.8, cy - 0.75, 2.4), (cx + 0.8, cy - 0.75, 3.6), 0.12, "SteelDark"))
    tank = bmesh.new()
    lathe(tank, [(0, 4.6), (0.9, 4.6), (1.12, 4.8), (1.15, 6.6), (1.0, 6.95), (0.6, 7.2), (0, 7.28)], 16, M((cx, cy, 0)))
    b.add("Cistern", [(tank, "Copper", 0.0, False)])
    for z in (4.95, 6.55):
        b.add("Cistern", band(1.17, 0.07, M((cx, cy, z)), "Brass", 16))
    b.add("Cistern", place(cyl(0.28, 0.25, "Brass", 10), M((cx, cy, 7.15))))
    b.add("Cistern", place(handle(0.36, 0.14, 0.03, "Iron"), M((cx, cy, 7.4))))
    b.add("Pipe", pipe_between((cx + 1.1, cy, 6.0), (4.3, cy, 6.0), 0.2, "Copper"))
    b.add("Pipe", pipe_between((wx, cy + 0.1, 6.0), (wx, 1.05, 5.5), 0.2, "Copper"))
    spout = bmesh.new()
    lathe(spout, [(0.12, -0.1), (0.24, -0.1), (0.32, 0.25), (0.26, 0.28), (0.12, 0.05)], 12, frame((wx, 1.05, 5.5), out=(0, -0.7, -1)))
    b.add("Pipe", [(spout, "Brass", 0.0, False)])
    b.add("Pipe", place(cyl(0.27, 0.12, "Brass", 12), frame((0.0, cy, 6.0), out=(1, 0, 0))))
    b.add("Pipe", place(cyl(0.12, 5.4, "Iron", 8, bevel=0.0), M((0.8, cy, top))))
    b.add("Pipe", place(cyl(0.14, 5.0, "Iron", 8, bevel=0.0), M((4.3, cy, base + 0.62))))
    b.add("Pipe", band(0.32, 0.05, M((-0.6, cy, 6.55)), "WarnRed", 14))  # the valve handwheel
    for a in (0.0, math.pi / 2):
        b.add("Pipe", low_block((0.62, 0.06, 0.05), "WarnRed", M((-0.6, cy, 6.55), (0, 0, a))))
    b.add("Pipe", place(cyl(0.06, 0.35, "Brass", 8, bevel=0.0), M((-0.6, cy, 6.2))))
    pour = [(wx, 0.98, 5.4), (wx, 0.85, 5.25), (wx, 0.7, 5.12)]
    b.add("Water", stream(pour, 0.16, "IceBlue", end=1.4))
    tier_water(2, lambda: stream(pour, 0.18, "AuroraCyan", True, end=1.4))
    atts = {"Work": work, "Trail": work, "Hit": frame((-1.8, -4.3, 0.9), out=(0, -1, 0.6)),
            "Lamp1": up_((-3.85, -2.3, top + 4.03)), "Lamp2": up_((0.25, -2.3, top + 4.03)),
            "Gear1": frame((4.56, wy, 3.0), out=(1, 0, 0)), "Gear2": frame((-3.88, -0.1, 1.9), out=(-1, 0, 0)),
            "Steam1": up_((wx, -1.6, 0.78)), "Steam2": up_((wx, 0.7, 5.1)),
            "NamePlate": front((-1.0, -3.62, 0.2)), "Aura": up_((0, 0, base)), "Top": up_((cx, cy, 7.5))}
    return atts


# ---------- tier 3: Frost-tech, the crystal turbine ----------

def frosttech(b):
    GLOW_WATER[3] = []
    b.add("Deck", block((9.2, 7.6, 0.7), "SnowWhite", corner=2.0, edge=0.3))
    b.add("Deck", place(block((8.4, 6.8, 0.25), "IceBlue", corner=1.7, edge=0.1), M((0, 0, 0.7))))
    top = 0.95
    for sx in (-1, 1):
        b.add("Deck", place(vent(1.2, 0.4, 5, "GlacierBlue", "SteelLight"), front((sx * 1.75, -3.79, 0.36))))
        b.add("Deck", trim_strip((sx * 4.63, -1.4, 0.36), (sx * 4.63, 1.4, 0.36), 0.16, "AuroraCyan", True))
        for sy in (-1, 1):
            b.add("Deck", place(bolt(0.1, "SteelLight", "GlacierBlue"), M((sx * 3.2, sy * 2.7, top))))
    b.add("Deck", trim_strip((-0.9, -3.83, 0.36), (0.9, -3.83, 0.36), 0.16, "AuroraCyan", True))
    for x, y in ((-1.1, 2.6), (0.9, 2.6)):
        b.add("Deck", place(inset_panel(1.4, 0.9, 0.05, "FrostLight", "GlacierBlue", True), M((x, y, top))))
    # the turbine: a white shroud standing on a cradle, crystal blades turning inside it (about X)
    tx, ty, tz = 2.9, -0.3, 3.5
    S = frame((tx, ty, tz), out=(1, 0, 0))
    shroud = bmesh.new()
    lathe(shroud, [(1.92, -0.62), (2.2, -0.66), (2.34, -0.5), (2.34, 0.5), (2.2, 0.66), (1.92, 0.62), (1.86, 0.0), (1.92, -0.62)], 32, S)
    b.add("Shroud", [(shroud, "SnowWhite", 0.0, False)])
    for s in (-1, 1):
        flip = Matrix.Rotation(math.pi, 4, "X") if s < 0 else Matrix()
        b.add("Shroud", place(ring4(2.06, 0, "AuroraCyan", True, minor=0.05, segments=32), S @ M((0, 0, s * 0.66))))
        b.add("Shroud", place(ring4(2.35, 0, "GlacierBlue", minor=0.045, segments=32), S @ M((0, 0, s * 0.28))))
        b.add("Shroud", place(rivet_ring(2.1, 6, 0.05, "SteelLight"), S @ M((0, 0, s * 0.67)) @ flip))
    b.add("Shroud", place(block((1.5, 1.7, 0.5), "SteelLight", corner=0.35, edge=0.12), M((tx, ty, top))))
    b.add("Shroud", place(block((1.56, 1.76, 0.08), "GlacierBlue", corner=0.36, edge=0.03), M((tx, ty, top + 0.42))))
    for sy in (-1, 1):
        b.add("Shroud", low_beam((tx, ty + sy * 1.6, top), (tx, ty + sy * 2.1, 2.5), 0.3, "SnowWhite"))
        b.add("Shroud", place(cyl(0.26, 0.1, "GlacierBlue", 12), M((tx, ty + sy * 1.6, top))))
    funnel = bmesh.new()
    lathe(funnel, [(0.2, -0.2), (0.34, -0.2), (0.5, 0.25), (0.44, 0.3), (0.26, 0.0)], 16, M((tx, ty, tz + 2.3)))
    b.add("Shroud", [(funnel, "SnowWhite", 0.0, False)])
    hub = bmesh.new()
    lathe(hub, [(0, -0.6), (0.42, -0.6), (0.48, -0.3), (0.48, 0.3), (0.36, 0.7), (0, 0.95)], 16, S)
    b.add("Turbine", [(hub, "SteelLight", 0.0, False)])
    b.add("Turbine", place(ring4(0.49, 0, "AuroraCyan", True, minor=0.05, segments=16), S @ M((0, 0, 0.1))))
    for k in range(8):
        a = 2 * math.pi * k / 8
        blade = S @ Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((0.36, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Y") @ Matrix.Rotation(0.6, 4, "Z") @ Matrix.Diagonal((1.0, 0.42, 1.0, 1.0))
        b.add("Turbine", place(cut_crystal(1.45, 0.3, "CrystalCyan" if k % 2 else "IceBlue", sides=6), blade))
    # the glowing pool in front of the turbine and the water spilling into it
    b.add("Pool", place(block((1.9, 1.6, 0.1), "SteelLight", corner=0.3, edge=0.04), M((tx, -3.0, top))))
    b.add("Water", water_slab((1.6, 1.3, 0.06), (tx, -3.0, top + 0.1), "PolarTeal", True))
    spill = [(tx, -2.2, 2.25), (tx, -2.6, 1.7), (tx, -2.85, 1.1)]
    b.add("Water", stream(spill, 0.14, "PolarTeal", True, end=1.5))
    tier_water(3, lambda: water_slab((1.64, 1.34, 0.07), (tx, -3.0, top + 0.105), "AuroraCyan", True) + stream(spill, 0.16, "AuroraCyan", True, end=1.5))
    # the chisel engine: a white housing on legs, the turbine shaft into its side
    hx, hy = -1.1, -1.1
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add("EngineLegs", low_beam((hx + sx * 2.0, hy + sy * 0.8, top), (hx + sx * 1.9, hy + sy * 0.75, 1.75), 0.3, "GlacierBlue"))
    b.add("Engine", place(block((5.0, 2.4, 2.3), "SnowWhite", corner=0.8, edge=0.5), M((hx, hy, 1.6))))
    for z in (2.35, 3.2):
        b.add("Engine", place(block((5.06, 2.46, 0.07), "GlacierBlue", corner=0.82, edge=0.02), M((hx, hy, z))))
    b.add("Engine", place(screen(1.1, 0.5, "AuroraCyan", "NavyIce", 4), front((hx - 1.2, hy - 1.21, 3.45))))
    b.add("Engine", place(dial(0.22, "FrostLight", "SteelLight", "AuroraCyan", 0.5), front((hx + 0.6, hy - 1.21, 3.5))))
    b.add("Engine", place(vent(1.2, 0.6, 4, "GlacierBlue", "SteelLight"), frame((hx - 2.51, hy, 3.0), out=(-1, 0, 0))))
    b.add("Engine", place(block((4.2, 0.3, 0.45), "NavyIce", corner=0.12, edge=0.08), M((hx, hy - 1.12, 1.85))))
    for sx in (-1, 1):  # frost fins on the lid
        fin = bmesh.new()
        rounded_block(fin, (0.14, 1.6, 0.9), M((hx + sx * 1.6, hy + 0.1, 4.1), (0, sx * 0.2, 0)), corner=0.06, edge=0.05, taper=0.6)
        line = bmesh.new()
        rounded_block(line, (0.16, 0.06, 0.7), M((hx + sx * 1.61, hy + 0.1, 4.05), (0, sx * 0.2, 0)), corner=0.02, edge=0.02, corner_seg=1, edge_seg=1)
        b.add("Engine", [(fin, "GlacierBlue", 0.0, False), (line, "AuroraCyan", 0.0, True)])
    b.add("Engine", place(handle(0.7, 0.2, 0.05, "GlacierBlue"), M((hx, hy + 0.4, 3.9))))
    work = frame((hx, hy - 1.1, 2.1), out=T3_DIR)
    for i in range(4):
        b.add("Engine", place(cyl(0.3, 0.2, "NavyIce", 12), work @ M(((i - 1.5) * 1.0, 0, 0.02))))
        b.add("Engine", place(ring4(0.27, 0, "AuroraCyan", True, minor=0.045, segments=12), work @ M(((i - 1.5) * 1.0, 0, 0.23))))
    b.add("Shaft", pipe_between((tx - 0.6, ty, tz), (hx + 2.45, ty, tz), 0.2, "SteelLight"))
    for x in (1.75, 2.05):
        b.add("Shaft", place(ring4(0.24, 0, "AuroraCyan", True, minor=0.05, segments=12), frame((x, ty, tz), out=(1, 0, 0))))
    # the tank of glowing water: ribs and rings round a glowing core, a coil on its cap
    cx, cy = -2.6, 1.9
    b.add("Tank", place(block((2.0, 2.0, 0.55), "SteelLight", corner=0.6, edge=0.15), M((cx, cy, top))))
    b.add("Tank", place(ring4(1.0, 0, "AuroraCyan", True, minor=0.05, segments=20), M((cx, cy, top + 0.58))))
    core = cyl(0.85, 5.2, "PolarTeal", 20)
    b.add("TankGlass", [(bm, sw, bev, True) for bm, sw, bev, _ in place(core, M((cx, cy, 1.45)))])
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        b.add("Tank", low_beam((cx + 0.93 * math.cos(a), cy + 0.93 * math.sin(a), 1.45), (cx + 0.93 * math.cos(a), cy + 0.93 * math.sin(a), 6.6), 0.13, "SnowWhite"))
    for z in (1.55, 3.3, 5.0, 6.55):
        b.add("Tank", place(ring4(0.96, 0, "SteelLight", minor=0.08, segments=20), M((cx, cy, z))))
    for k in range(5):  # bubbles rising on the glass
        a = k * 2.1
        bub = bmesh.new()
        blob(bub, (cx + 0.86 * math.cos(a), cy + 0.86 * math.sin(a), 1.9 + k * 0.9), (0.1 + 0.03 * (k % 2),) * 3, 1)
        b.add("Tank", [(bub, "FrostLight", 0.0, False)])
    cap = bmesh.new()
    lathe(cap, [(0, 6.5), (1.05, 6.5), (1.05, 6.8), (0.8, 7.25), (0.35, 7.45), (0, 7.5)], 20, M((cx, cy, 0)))
    b.add("Tank", [(cap, "SnowWhite", 0.0, False)])
    b.add("Tank", place(coil(0.32, 1.0, 4, "SteelDark", "IceBlue", "AuroraCyan"), M((cx, cy, 7.4))))
    tier_water(3, lambda: [(bm, sw, bev, True) for bm, sw, bev, _ in place(cyl(0.87, 5.22, "AuroraCyan", 20), M((cx, cy, 1.44)))])
    # the glowing water main from the tank to the turbine's intake, on a pylon
    main = smooth_path([(cx + 0.9, cy, 6.0), (0.0, cy, 6.25), (2.0, cy, 6.25), (tx, 0.9, 6.15), (tx, ty, 5.95)], 4)
    b.add("Main", stream(main, 0.17, "PolarTeal", True, end=1.0))
    tier_water(3, lambda: stream(main, 0.19, "AuroraCyan", True, end=1.0))
    for k in (2, 6, 10, 13):
        p, q = main[k], main[k + 1]
        b.add("MainCollars", place(cyl(0.25, 0.22, "SnowWhite", 12), Matrix.Translation(p) @ align_z(q - p)))
    b.add("MainCollars", place(block((0.5, 0.5, 5.2), "SnowWhite", corner=0.15, edge=0.1), M((0.3, cy, top))))
    b.add("MainCollars", trim_strip((0.3, cy - 0.26, 1.5), (0.3, cy - 0.26, 5.6), 0.12, "AuroraCyan", True))
    b.add("Coils", place(coil(0.35, 1.6, 5, "SteelDark", "IceBlue", "AuroraCyan"), M((-0.9, 2.55, top))))
    atts = {"Work": work, "Trail": work, "Hit": frame((hx, -4.2, 1.0), out=(0, -1, 0.6)),
            "Lamp1": up_((hx - 2.0, hy - 0.5, 3.88)), "Lamp2": up_((hx + 1.9, hy - 0.5, 3.88)),
            "Gear1": frame((tx + 1.05, ty, tz), out=(1, 0, 0)), "Gear2": frame((hx - 2.56, hy, 2.3), out=(-1, 0, 0)),
            "Steam1": up_((tx, -3.0, top + 0.12)), "Steam2": up_((cx, cy, 8.85)),
            "NamePlate": front((0, -3.82, 0.36)), "Aura": up_((0, 0, top)), "Top": up_((cx, cy, 8.85))}
    return atts


# ---------- tier 4: Enchanted, the waterwheel in mid-air under a waterfall from nowhere ----------

def waterfall(x, y, z_top, z_bottom, w0, d0, w1, d1, swatch, glow, wobble=0.08, rings=8):
    """A falling column of water: rounded sections lofted from z_bottom up to z_top, widening as it falls."""
    sections = []
    for k in range(rings + 1):
        s = k / rings
        z = z_top + (z_bottom - z_top) * s
        w, d = w0 + (w1 - w0) * s, d0 + (d1 - d0) * s
        ox = wobble * math.sin(k * 1.7)
        sections.append([Vector((x + ox + px, y + py, z)) for px, py in rounded_rect(w, d, min(w, d) * 0.45, 2)])
    bm = bmesh.new()
    loft(bm, list(reversed(sections)))
    return [(bm, swatch, 0.0, glow)]


def enchanted(b):
    GLOW_WATER[4] = []
    dais = bmesh.new()
    lathe(dais, [(0, 0), (4.4, 0), (4.4, 0.3), (4.2, 0.35), (4.2, 0.55), (3.95, 0.8), (0, 0.8)], 6)
    b.add("Dais", [(dais, "Moonstone", 0.04, False)])
    plinth = bmesh.new()
    lathe(plinth, [(0, -0.01), (4.55, -0.01), (4.55, 0.18), (0, 0.18)], 6)
    b.add("Dais", [(plinth, "StoneDark", 0.03, False)])
    b.add("Dais", place(ring4(4.07, 0, "RuneViolet", minor=0.08, segments=6), M((0, 0, 0.56))))
    b.add("DaisRunes", place(engraved_rune_ring(3.25, "RuneGlow", "ArcaneDeep", "RuneViolet", 16), M((0, 0, 0.8))))
    for k in range(6):
        a = k * math.pi / 3
        b.add("DaisCrystals", place(cut_crystal_cluster(0.5, "CrystalCyan" if k % 2 else "RuneViolet", "Moonstone", 4), M((3.9 * math.cos(a), 3.9 * math.sin(a), 0.78), (0, 0, a))))
        fa = a + math.pi / 6
        apothem = 4.4 * math.cos(math.pi / 6)
        b.add("Dais", place(gem_setting(0.14, "AuroraCyan", "Gold", 4), frame((apothem * math.cos(fa), apothem * math.sin(fa), 0.18), out=(math.cos(fa), math.sin(fa), 0))))
    top = 0.8
    # the pool the waterfall ends in
    px, py = 0.0, 0.9
    wall = bmesh.new()
    lathe(wall, [(2.0, top - 0.02), (2.35, top - 0.02), (2.4, top + 0.3), (2.28, top + 0.4), (2.05, top + 0.36), (2.0, top - 0.02)], 28, M((px, py, 0)))
    b.add("Pool", [(wall, "Moonstone", 0.0, False)])
    b.add("Pool", place(ring4(2.33, 0, "Gold", minor=0.06, segments=28), M((px, py, top + 0.38))))
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        b.add("Pool", place(rivet(0.06, "Gold"), frame((px + 2.39 * math.cos(a), py + 2.39 * math.sin(a), top + 0.18), out=(math.cos(a), math.sin(a), 0))))
    b.add("PoolWater", water_disc(2.02, top + 0.26, "PolarTeal", True, (px, py), 28))
    tier_water(4, lambda: water_disc(2.04, top + 0.27, "CrystalCyan", True, (px, py), 28))
    # the floating waterfall wheel (turns about Y), its rune ring, sparkling crystals round it
    wx, wy, wz = 0.0, 0.9, 6.0
    W = frame((wx, wy, wz), out=(0, 1, 0))
    b.add("Wheel", place(water_wheel(2.4, 0.9, 12, "Moonstone", "ArcaneDeep", "Gold", "Gold", 3, buckets="Gold", segments=24), W))
    for s in (-1, 1):
        flip = Matrix.Rotation(math.pi, 4, "X") if s < 0 else Matrix()
        b.add("WheelGems", place(gem_setting(0.28, "MagicPink", "Gold", 4), W @ M((0, 0, s * 0.62)) @ flip))
    b.add("RuneRing", place(engraved_rune_ring(3.0, "RuneGlow", "ArcaneDeep", "RuneViolet", 14), frame((wx, wy - 0.1, wz), out=(0, -1, 0.12))))
    b.add("RuneRing", place(ring4(3.45, 0, "Gold", minor=0.05, segments=40), frame((wx, wy + 0.1, wz), out=(0.25, -1, -0.2))))
    for k in range(4):
        a = k * math.pi / 2 + 0.6
        p = (wx + 3.35 * math.cos(a), wy - 0.4, wz + 3.0 * math.sin(a))
        b.add("Orbit", place(cut_crystal(0.8, 0.17, "AuroraGreen" if k % 2 else "MagicPink", (0.3, 0.2)), M(p)))
    # the rune portal in mid-air: the waterfall pours out of it onto the wheel
    P = Vector((1.25, wy, 11.3))
    b.add("Portal", place(engraved_rune_ring(1.05, "RuneGlow", "ArcaneDeep", "RuneViolet", 8), frame(P, out=(0, 0, -1))))
    disc = bmesh.new()
    lathe(disc, [(0, 0), (0.9, 0), (0.9, 0.04), (0, 0.07)], 20, Matrix.Translation(P + Vector((0, 0, 0.02))) @ Matrix.Rotation(math.pi, 4, "X"))
    b.add("Portal", [(disc, "ArcaneDeep", 0.0, False)])
    swirl = [P + Vector((0.85 * (1 - s) * math.cos(s * 9.0), 0.85 * (1 - s) * math.sin(s * 9.0), -0.08)) for s in (k / 24 for k in range(25))]
    sw = bmesh.new()
    sweep(sw, swirl, 0.045, 5, radius_end=0.02)
    b.add("Portal", [(sw, "AuroraCyan", 0.0, True)])
    for k in range(3):
        a = k * 2 * math.pi / 3
        b.add("PortalCrown", place(cut_crystal(0.7, 0.15, "RuneViolet", (0.3 * math.cos(a), 0.3 * math.sin(a))), M((P.x + 0.55 * math.cos(a), P.y + 0.55 * math.sin(a), P.z + 0.35))))
    b.add("PortalCrown", place(gem_setting(0.24, "AuroraCyan", "Gold", 4), M((P.x, P.y, P.z + 0.45))))
    halo = bmesh.new()
    torus(halo, M((P.x, P.y, P.z + 1.25), (math.pi / 2, 0, 0.4)), 0.42, 0.035, 20, 4)
    b.add("PortalCrown", [(halo, "Gold", 0.0, False)])
    rim_z = wz + math.sqrt(2.4 ** 2 - (P.x - wx) ** 2)
    b.add("Waterfall", waterfall(P.x, wy, P.z - 0.05, rim_z - 0.05, 0.75, 0.55, 1.0, 0.85, "PolarTeal", True))
    drop_x = 1.0
    low_z = wz - math.sqrt(2.4 ** 2 - drop_x ** 2)
    b.add("Waterfall", waterfall(drop_x, wy, low_z, top + 0.27, 0.45, 0.4, 0.7, 0.55, "PolarTeal", True, rings=6))
    tier_water(4, lambda: waterfall(P.x, wy, P.z - 0.04, rim_z - 0.04, 0.82, 0.6, 1.08, 0.92, "CrystalCyan", True) + waterfall(drop_x, wy, low_z + 0.02, top + 0.28, 0.5, 0.45, 0.76, 0.6, "CrystalCyan", True, rings=6))
    for x, z, r in ((P.x, rim_z, 0.62), (drop_x, top + 0.3, 0.5)):
        foam = bmesh.new()
        torus(foam, Matrix.Translation((x, wy, z)) @ Matrix.Diagonal((1.0, 0.85, 0.5, 1)), r, 0.12, 16, 4)
        b.add("Foam", [(foam, "SnowWhite", 0.0, False)])
    # floating islands for the lamps
    for sx in (-1, 1):
        isl = M((sx * 3.3, -1.2, 4.6), (0, 0, 0.3 * sx))
        b.add("Islands", place(floating_platform(0.95, 0.35, "Moonstone", "StoneDark", "Gold", "RuneViolet"), isl))
        b.add("Islands", place(ring4(0.5, 0.01, "Gold", minor=0.04, segments=6), isl))
    # the floating chisel holder: a moonstone bar with gold trim and gems, rune rings round each chisel
    work = frame((0, -2.5, 3.0), out=T4_DIR)
    b.add("Holder", place(block((4.9, 0.55, 0.5), "Moonstone", corner=0.25, edge=0.12), work @ M((0, 0, -0.15))))
    for s in (-1, 1):
        b.add("Holder", place(trim_strip((-2.4, s * 0.3, 0.1), (2.4, s * 0.3, 0.1), 0.08, "Gold"), work))
        b.add("Holder", place(cut_gem(0.18, "MagicPink"), work @ M((s * 2.55, 0, 0.1), (0, math.pi / 2 * s, 0))))
    for i in range(4):
        b.add("ChiselRunes", place(ring4(0.34, 0, "RuneGlow", True, minor=0.04, segments=16), work @ M(((i - 1.5) * 1.15, 0, 0.62))))
    hover = bmesh.new()
    torus(hover, work @ M((0, 0, -0.45)) @ Matrix.Diagonal((2.6, 0.5, 1, 1)), 1.0, 0.03, 32, 4)
    b.add("ChiselRunes", [(hover, "RuneGlow", 0.0, True)])
    atts = {"Work": work, "Trail": work, "Hit": frame((0, -4.3, 0.9), out=(0, -1, 0.6)),
            "Lamp1": up_((-3.3, -1.2, 4.62)), "Lamp2": up_((3.3, -1.2, 4.62)),
            "Gear1": frame((wx, wy - 0.72, wz), out=(0, -1, 0)), "Gear2": frame((wx, wy + 0.72, wz), out=(0, 1, 0)),
            "Steam1": up_((drop_x, wy, top + 0.3)), "Steam2": up_((P.x, wy, P.z + 0.2)),
            "NamePlate": front((0, -3.85, 0.4)), "Aura": up_((0, 0, top)), "Top": up_((P.x, wy, P.z + 1.7))}
    return atts


# ---------- tier 5: Legendary, the Kraken Mill ----------

class Surface:
    """Measures a finished organic surface so the face parts sit on it."""

    def __init__(self, *bms):
        self.points = [v.co.copy() for bm in bms for v in bm.verts]

    def front(self, x, z, reach=0.35):
        while True:  # widen the search until it finds surface points
            ys = [p.y for p in self.points if abs(p.x - x) < reach and abs(p.z - z) < reach]
            if ys:
                return min(ys)
            reach *= 1.5

    def side(self, z, y, reach=0.4):
        return max(p.x for p in self.points if abs(p.z - z) < reach and abs(p.y - y) < reach)

    def band(self, z, reach=0.22):
        ring = [p for p in self.points if abs(p.z - z) < reach]
        return (max(p.x for p in ring) - min(p.x for p in ring)) / 2, (max(p.y for p in ring) - min(p.y for p in ring)) / 2, (max(p.y for p in ring) + min(p.y for p in ring)) / 2

    def toward(self, centre, direction):
        d = Vector(direction).normalized()
        return max(self.points, key=lambda p: (p - centre).normalized().dot(d))

    def top(self):
        return max(p.z for p in self.points)


def kraken_body():
    """The kraken in one piece: a soft skirt in the water, a waist where the face sits and a big round
    head on top (a revolved profile, the face pushed forward a little, then subdivided)."""
    profile = [(0, 0.7), (1.7, 0.75), (2.3, 1.3), (2.4, 2.1), (2.1, 3.0), (1.72, 3.9), (1.72, 4.7), (2.2, 5.6),
               (2.75, 6.7), (2.95, 7.9), (2.88, 9.0), (2.55, 9.95), (1.95, 10.7), (1.05, 11.15), (0, 11.3)]
    bm = bmesh.new()
    lathe(bm, profile, 20)
    for v in bm.verts:
        v.co.y *= 0.93
        if v.co.y < 0:  # the face: cheeks and muzzle a little forward
            v.co.y -= 0.35 * max(0.0, 1 - abs(v.co.z - 5.4) / 1.6) * max(0.0, -v.co.y / 2.0)
        v.co.y += 0.55
    return subsurf(bm, 1)


def kraken_mantle(radii):
    """The kraken's big round head: a box cage rounded to an ellipsoid, a little wider at the top and
    narrowing toward the neck, then subdivided."""
    cage = cage_box((2 * radii[0], 2 * radii[1], 2 * radii[2]), 2)
    R = Vector(radii)
    for v in cage.verts:
        unit = Vector((v.co.x / R.x, v.co.y / R.y, v.co.z / R.z))
        if unit.length > 1e-6:
            unit.normalize()
            v.co = v.co.lerp(Vector((unit.x * R.x, unit.y * R.y, unit.z * R.z)) * 1.04, 0.85)
    for v in cage.verts:
        t = v.co.z / R.z
        s = 1 + 0.06 * t if t > 0 else 1 + 0.12 * t
        v.co.x *= s
        v.co.y *= s
    return subsurf(cage, 2)


def tentacle(points, r0, r1, b, role, suckers=(0.12, 0.7), count=9, swatch="RuneViolet", sucker="Blush"):
    """A tapering tentacle along the points (organic), suckers on its underside."""
    pts = [Vector(p) for p in points]
    t = bmesh.new()
    sweep(t, pts, r0, 12, radius_end=r1)
    tip = bmesh.new()
    blob(tip, pts[-1], (r1 * 1.1,) * 3, 1)
    b.add(role, [(t, swatch, 0.0, False), (tip, swatch, 0.0, False)], organic=True)
    n = len(pts)
    discs = []
    for k in range(count):
        i = int(n * (suckers[0] + (suckers[1] - suckers[0]) * k / max(1, count - 1)))
        i = max(1, min(n - 2, i))
        tan = (pts[i + 1] - pts[i - 1]).normalized()
        under = Vector((0, 0, -1))
        under = under - tan * under.dot(tan)
        if under.length < 0.2:
            continue
        under.normalize()
        r = r0 + (r1 - r0) * i / (n - 1)
        rs = r * 0.42
        d = bmesh.new()
        lathe(d, [(0, 0), (rs, 0), (rs * 0.85, rs * 0.42), (rs * 0.45, rs * 0.32), (0, rs * 0.2)], 8, Matrix.Translation(pts[i] + under * r * 0.86) @ align_z(under))
        discs.append((d, sucker, 0.0, False))
    if discs:
        b.add(role, discs, organic=True)


def helix_round(m, radius, z0, z1, turns, start=math.pi / 2, sense=1, steps=14):
    """Points winding round the local Z axis of frame m (a tentacle gripping a handle)."""
    return [m @ Vector((radius * math.cos(start + sense * 2 * math.pi * turns * k / steps), radius * math.sin(start + sense * 2 * math.pi * turns * k / steps), z0 + (z1 - z0) * k / steps)) for k in range(steps + 1)]


def curl(end, travel, r0=0.45, turns=1.6, steps=16):
    """A fern-like curl at a tentacle's tip: forward, then rolling up and back over itself."""
    t = Vector(travel)
    t.z = 0
    t.normalize()
    up = Vector((0, 0, 1))
    c = Vector(end) + up * r0
    pts = []
    for k in range(1, steps + 1):
        th = 2 * math.pi * turns * k / steps
        r = r0 * (1 - 0.72 * k / steps)
        pts.append(c + (t * math.sin(th) - up * math.cos(th)) * r)
    return pts


def mallet(head_c, strike, grip):
    """A gold-banded brass mallet whose head faces `strike`; returns the pieces and the handle frame."""
    d = Vector(strike).normalized()
    g = Vector(grip) - d * Vector(grip).dot(d)
    g.normalize()
    hc = Vector(head_c)
    hd = Matrix.Translation(hc) @ align_z(d)
    pieces = []
    head = bmesh.new()
    lathe(head, [(0, -0.5), (0.3, -0.5), (0.38, -0.4), (0.38, 0.4), (0.3, 0.5), (0, 0.5)], 14, hd)
    pieces.append((head, "Brass", 0.0, False))
    for z in (-0.3, 0.3):
        pieces += place(ring4(0.39, 0, "Gold", minor=0.05, segments=14), hd @ M((0, 0, z)))
    for z in (-0.52, 0.52):
        pieces += place(cyl(0.26, 0.06, "Gunmetal", 12), hd @ M((0, 0, z - 0.03)))
    hm = Matrix.Translation(hc) @ align_z(g)
    pieces += place(cyl(0.1, 1.7, "PineDark", 10), hm)
    knob = bmesh.new()
    blob(knob, hm @ Vector((0, 0, 1.72)), (0.14, 0.14, 0.12), 1)
    pieces.append((knob, "Gold", 0.0, False))
    return pieces, hm


def kraken(b):
    GLOW_WATER[5] = []
    # the octagonal plinth, a pool of water on it, gold trim, aurora strips and gems
    turn = M((0, 0, 0), (0, 0, math.pi / 8))
    plat = bmesh.new()
    lathe(plat, [(0, 0), (5.0, 0), (5.0, 0.55), (4.85, 0.85), (0, 0.85)], 8, turn)
    b.add("Platform", [(plat, "Gunmetal", 0.04, False)])
    trim = bmesh.new()
    lathe(trim, [(0, 0.38), (5.06, 0.38), (5.06, 0.6), (0, 0.6)], 8, turn)
    b.add("PlatformTrim", [(trim, "Gold", 0.02, False)])
    ap = 5.0 * math.cos(math.pi / 8)
    for k in range(8):
        a = k * math.pi / 4
        out = Vector((math.cos(a), math.sin(a), 0))
        c = out * ap
        tang = Vector((-math.sin(a), math.cos(a), 0))
        if k in (5, 7):  # the two front diagonal faces: glowing aurora strips
            b.add("PlatformTrim", trim_strip(c - tang * 1.3 + out * 0.03 + Vector((0, 0, 0.2)), c + tang * 1.3 + out * 0.03 + Vector((0, 0, 0.2)), 0.15, "AuroraGreen", True))
        if k in (0, 2, 4):
            b.add("Platform", place(gem_setting(0.15, "AuroraCyan", "Gold", 4), frame(c + Vector((0, 0, 0.72)) - out * 0.06, out=(out.x, out.y, 0.25))))
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        b.add("Platform", place(rivet(0.07, "Gold"), M((4.35 * math.cos(a), 4.35 * math.sin(a), 0.85))))
    b.add("Water", water_disc(4.0, 0.92, "GlacierBlue", False, (0, 0), 32))
    b.add("Water", place(ring4(4.02, 0, "SnowWhite", minor=0.06, segments=32), M((0, 0, 0.9))))
    tier_water(5, lambda: water_disc(4.03, 0.93, "PolarTeal", True, (0, 0), 32))
    # the kraken: a big round head on a soft body, sitting in the pool
    centre = Vector((0, 0.55, 7.8))
    body = kraken_body()
    hs = face = Surface(body)
    b.add("Body", [(body, "RuneViolet", 0.0, False)], organic=True)
    foam = bmesh.new()
    torus(foam, Matrix.Translation((0, 0.55, 0.95)) @ Matrix.Diagonal((1.0, 0.93, 0.45, 1)), 2.0, 0.16, 24, 4)
    b.add("Water", [(foam, "SnowWhite", 0.0, False)])
    for k, d in enumerate(((0.5, 0.3, 0.8), (-0.6, 0.5, 0.6), (0.2, 0.8, 0.5), (-0.3, -0.25, 0.95), (0.85, 0.4, 0.2), (-0.85, 0.2, 0.35), (0.4, 0.9, -0.1))):
        p = hs.toward(centre, d)
        n = (p - centre).normalized()
        spot = bmesh.new()
        blob(spot, (0, 0, 0), (0.34 - 0.05 * (k % 3), 0.3, 0.07), 2)
        spot.transform(Matrix.Translation(p - n * 0.02) @ align_z(n))
        b.add("Spots", [(spot, "ArcaneDeep", 0.0, False)], organic=True)
    # the face: goggled eyes, cheeky brows, blush, a smile with two teeth
    eye_z, eye_y = 6.05, 0.0
    for sx in (-1, 1):
        ex = sx * 1.0
        eye_y = hs.front(ex, eye_z) + 0.16
        eye_at = frame((ex, eye_y, eye_z), out=(sx * 0.18, -1, 0.06))
        b.add("Eyes", place(cartoon_eye(0.8, None, look=(-sx * 0.08, -0.12)), eye_at))
        rim = bmesh.new()
        torus(rim, eye_at @ M((0, 0, 0.05)), 0.86, 0.12, 20, 4)
        b.add("Goggles", [(rim, "Gold", 0.0, False)])
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            b.add("Goggles", place(rivet(0.07, "Gunmetal"), eye_at @ M((0.86 * math.cos(a), 0.86 * math.sin(a), 0.15))))
        bz = 7.15
        b.add("Goggles", place(brow(0.95, -0.18 if sx < 0 else 0.3, "ArcaneDeep"), frame((sx * 1.05, hs.front(sx * 1.05, bz) + 0.02, bz), out=(0, -1, 0.35))))
        blush = bmesh.new()
        blob(blush, (sx * 1.85, face.front(sx * 1.85, 5.25) + 0.1, 5.25), (0.42, 0.2, 0.27), 1)
        b.add("Goggles", [(blush, "Blush", 0.0, False)])
    mz = 4.85
    my = face.front(0, mz, 0.3)
    smile = bmesh.new()
    sweep(smile, [V(-0.6, my + 0.14, mz + 0.14), V(-0.3, my + 0.02, mz), V(0.3, my + 0.02, mz), V(0.6, my + 0.14, mz + 0.14)], 0.07, 8)
    b.add("Goggles", [(smile, "EyeDark", 0.0, False)])
    for sx in (-1, 1):
        tooth = bmesh.new()
        rounded_block(tooth, (0.24, 0.12, 0.26), M((sx * 0.16, my + 0.02, mz - 0.14), (0.25, 0, 0)), corner=0.06, edge=0.05, corner_seg=2, edge_seg=1)
        b.add("Goggles", [(tooth, "EyeWhite", 0.0, False)])
    # mill machinery on the head: riveted brass bands, a gear hub on each temple, a porthole at the back
    for z in (7.75, 9.45):
        rx, ry, cy = hs.band(z)
        strap = bmesh.new()
        torus(strap, Matrix.Translation((0, cy, z)) @ Matrix.Diagonal((rx + 0.04, ry + 0.04, 1, 1)), 1.0, 0.13, 32, 4)
        b.add("Bands", [(strap, "Brass", 0.0, False)])
        for k in range(9):
            a = k * 2 * math.pi / 9 + 0.1
            b.add("Bands", place(rivet(0.075, "Gold"), frame(((rx + 0.12) * math.cos(a), cy + (ry + 0.12) * math.sin(a), z), out=(math.cos(a) / rx, math.sin(a) / ry, 0))))
    temple_z = 7.75
    gx = hs.side(temple_z, 0.6) + 0.05
    for sx in (-1, 1):
        hubm = frame((sx * gx, 0.6, temple_z), out=(sx, 0, 0))
        b.add("TempleHub", place(cyl(0.62, 0.22, "Gunmetal", 16), hubm @ M((0, 0, -0.08))))
        b.add("TempleHub", place(rivet_ring(0.5, 6, 0.06, "Gold"), hubm @ M((0, 0, 0.14))))
    b.add("GearHub", place(gear(0.75, 11, 0.22, 0.14, "Brass", "Gold"), frame((gx + 0.3, 0.6, temple_z), out=(1, 0, 0))))
    b.add("TempleHub", place(dial(0.3, "Cream", "Gold", "WarnRed", 0.7), frame((-gx - 0.17, 0.6, temple_z), out=(-1, 0, 0))))
    back = hs.toward(centre, (0, 1, 0.15))
    b.add("TempleHub", place(ring4(0.5, 0, "Gold", minor=0.1, segments=16), frame(back + Vector((0, 0.05, 0)), out=(0, 1, 0.15))))
    port = bmesh.new()
    lathe(port, [(0, 0.12), (0.44, 0.0), (0, 0.0)], 16, frame(back, out=(0, 1, 0.15)))
    b.add("TempleHub", [(port, "IceBlue", 0.0, False)])
    # the gold crown, tilted at a jaunty angle
    crown_at = frame((0.1, 0.55, hs.top() - 0.3), out=(0.12, -0.06, 1))
    crown = []
    crown += ring4(1.15, 0.12, "Gold", minor=0.17, segments=20)
    crown += ring4(1.15, 0.5, "Gold", minor=0.07, segments=20)
    for k in range(7):
        a = 2 * math.pi * k / 7 - math.pi / 2
        tall = 0.35 if k == 0 else 0.0
        spike = bmesh.new()
        lathe(spike, [(0, 0), (0.24, 0), (0.22, 0.3), (0.09, 0.75 + tall), (0, 0.85 + tall)], 8, M((1.15 * math.cos(a), 1.15 * math.sin(a), 0.1)))
        crown.append((spike, "Gold", 0.0, False))
        ball = bmesh.new()
        blob(ball, (1.15 * math.cos(a), 1.15 * math.sin(a), 1.0 + tall), (0.1, 0.1, 0.1), 1)
        crown.append((ball, "Gold", 0.0, False))
        gem_at = frame((1.29 * math.cos(a), 1.29 * math.sin(a), 0.3), out=(math.cos(a), math.sin(a), 0))
        if k == 0:
            crown += place(gem_setting(0.18, "MagicPink", "Gold", 4), gem_at)
        else:
            crown += place(cut_gem(0.12, "AuroraCyan" if k % 2 else "AuroraGreen"), gem_at @ M((0, 0, 0.06)))
    b.add("Crown", place(crown, crown_at))
    # the side water wheel, its post, the inner bearing pillar, a belt up to the gear hub
    wx, wy, wz = 3.35, 1.8, 2.75
    WH = frame((wx, wy, wz), out=(1, 0, 0))
    b.add("Wheel", place(water_wheel(1.95, 0.7, 12, "Gold", "Gunmetal", "Gunmetal", "Gold", 3, buckets="Brass", segments=24), WH))
    b.add("Axle", place(cyl(0.17, 2.15, "Steel", 12), frame((2.55, wy, wz), out=(1, 0, 0))))
    b.add("Axle", place(cyl(0.42, 0.2, "Brass", 16), frame((2.82, wy, wz), out=(1, 0, 0))))
    b.add("MillFrame", place(block((0.42, 0.6, 2.2), "Gunmetal", corner=0.12, edge=0.08), M((4.45, wy, 0.85))))
    b.add("MillFrame", place(block((0.56, 0.74, 0.22), "Gold", corner=0.14, edge=0.05), M((4.45, wy, 3.02))))
    b.add("MillFrame", beam_between((4.45, wy + 1.5, 0.85), (4.45, wy + 0.2, 2.6), 0.2, swatch="Gunmetal"))
    b.add("MillFrame", place(bolt_ring(0.24, 4, 0.06, "Gold"), frame((4.67, wy, wz), out=(1, 0, 0))))
    b.add("MillFrame", place(cyl(0.28, 2.0, "Gunmetal", 14), M((2.55, wy, 0.75))))
    b.add("MillFrame", place(block((0.5, 0.6, 0.4), "Gold", corner=0.1, edge=0.05), M((2.55, wy, 2.55))))
    for s in (-1, 1):
        b.add("Belt", trim_strip((gx + 0.32, 0.6 + s * 0.68, temple_z), (2.84, wy + s * 0.42, wz), 0.13, "Rubber"))
    # a brass siphon from the back of the head pours onto the wheel
    pipe = smooth_path([(0.9, 2.65, 8.7), (1.9, 3.35, 8.4), (3.0, 3.3, 7.0), (wx, 2.8, 5.7), (wx, 2.35, 5.15)], 5)
    sp = bmesh.new()
    sweep(sp, pipe, 0.2, 12)
    b.add("Siphon", [(sp, "Brass", 0.0, False)])
    for k in (3, 9, 15):
        p, q = pipe[k], pipe[k + 1]
        b.add("Siphon", place(ring4(0.23, 0, "Gold", minor=0.06, segments=12), Matrix.Translation(p) @ align_z(q - p)))
    spout = bmesh.new()
    lathe(spout, [(0.14, -0.05), (0.24, -0.05), (0.34, 0.25), (0.28, 0.28), (0.15, 0.03)], 14, Matrix.Translation(pipe[-1]) @ align_z(pipe[-1] - pipe[-2]))
    b.add("Siphon", [(spout, "Gold", 0.0, False)])
    pour = [pipe[-1] + Vector((0, -0.05, -0.2)), Vector((wx, 2.15, 4.85)), Vector((wx, 2.05, 4.62))]
    b.add("Water", stream(pour, 0.17, "IceBlue", end=1.3))
    tier_water(5, lambda: stream(pour, 0.19, "AuroraCyan", True, end=1.3))
    # a brass lamp post at the front left (the 2nd upgrade's lamp sits on it)
    lp = Vector((-3.25, -3.15, 0.85))
    b.add("LampPost", place(cyl(0.12, 2.4, "Brass", 12), M(lp)))
    b.add("LampPost", place(cyl(0.26, 0.18, "Gold", 12), M(lp)))
    b.add("LampPost", place(cyl(0.22, 0.12, "Gold", 12), M(lp + Vector((0, 0, 2.4)))))
    for z in (0.9, 1.7):
        b.add("LampPost", place(ring4(0.13, 0, "Gold", minor=0.04, segments=12), M(lp + Vector((0, 0, z)))))
    # tentacles: two grip chisels, two swing mallets, one winds round the mill pillar, three curl in the pool
    works = {}
    for sx, key in ((-1, "Work"), (1, "Work2")):
        W = frame((sx * 1.25, -3.0, 2.95), out=T5_DIR)
        works[key] = W
        grip = helix_round(W, 0.36, 0.18, 0.72, 1.35, start=math.pi / 2 + sx * 0.6, sense=-sx)
        approach = W @ Vector((sx * 0.25, 0.75, 0.0))
        path = smooth_path([(sx * 1.15, -1.15, 2.6), (sx * 1.75, -2.0, 2.55), approach], 5) + grip
        tentacle(path, 0.5, 0.11, b, "TentacleF" + ("L" if sx < 0 else "R"), (0.08, 0.55), 8)
        # the mallet, raised above the chisel's butt, ready to strike
        head_c = Vector((sx * 2.05, -2.55, 4.75))
        butt = W @ Vector((0, 0, -0.15))
        pieces, hm = mallet(head_c, butt - head_c, (sx * 1.0, 0.55, 0.35))
        b.add("Mallets", pieces)
        mgrip = helix_round(hm, 0.27, 1.0, 1.55, 1.25, sense=sx, steps=12)
        mpath = smooth_path([(sx * 1.85, -0.35, 3.3), (sx * 2.75, -0.55, 4.3), (sx * 3.1, -0.7, 5.3), mgrip[0] + Vector((sx * 0.25, 0.2, 0.25))], 5) + mgrip
        tentacle(mpath, 0.46, 0.11, b, "TentacleM" + ("L" if sx < 0 else "R"), (0.08, 0.6), 8)
    pillar = M((2.55, wy, 0))
    pgrip = helix_round(pillar, 0.5, 1.25, 2.15, 1.3, start=math.pi, sense=1, steps=14)
    tentacle(smooth_path([(1.65, 1.55, 2.0), (2.0, 1.25, 1.45), pgrip[0] + Vector((-0.2, -0.05, 0.0))], 5) + pgrip, 0.44, 0.12, b, "TentacleSide", (0.1, 0.5), 7)
    for role, ctrl in (("TentacleBack", [(-1.95, 0.9, 2.1), (-3.0, 0.35, 1.3), (-3.55, -0.55, 1.05)]),
                       ("TentacleBack", [(-1.3, 2.3, 1.9), (-2.05, 3.2, 1.25), (-2.55, 3.65, 1.02)]),
                       ("TentacleBack2", [(0.8, 2.45, 1.9), (1.15, 3.45, 1.25), (1.9, 3.85, 1.02)])):
        main = smooth_path(ctrl, 5)
        tentacle(main + curl(main[-1], main[-1] - main[-3], 0.42), 0.46, 0.1, b, role, (0.15, 0.72), 7)
    atts = {"Work": works["Work"], "Work2": works["Work2"], "Trail": works["Work"],
            "Hit": frame((-1.25, -4.85, 1.3), out=(0, -1, 0.6)), "Hit2": frame((1.25, -4.85, 1.3), out=(0, -1, 0.6)),
            "Lamp1": up_((4.45, wy, 3.24)), "Lamp2": up_((lp.x, lp.y, lp.z + 2.52)),
            "Gear1": frame((gx + 0.45, 0.6, temple_z), out=(1, 0, 0)), "Gear2": frame((-gx - 0.3, 0.6, temple_z), out=(-1, 0, 0)),
            "Steam1": up_((wx, 0.9, 0.95)), "Steam2": up_((wx, 2.1, 4.7)),
            "Eyes": frame((0, eye_y, eye_z), out=(0, -1, 0)), "Crown": crown_at,
            "NamePlate": front((0, -ap - 0.02, 0.42)), "Aura": up_((0, 0, 0.9)), "Top": up_((0.1, 0.55, hs.top() + 1.0))}
    return atts


def _station(t, tier_fn):
    """A tier builder plus its base chisel row at the Work attachment(s)."""
    def build(b):
        atts = tier_fn(b)
        for key in ("Work", "Work2"):
            if key in atts:
                b.add("Chisels" + key[4:], place(chisel_row(**ROW[t], **LOOKS[t][0]), atts[key]))
        return atts
    return build


TIER_FNS = [_station(t, f) for t, f in enumerate((scrappy, workshop, frosttech, enchanted, kraken), start=1)]


# ---------- the upgrade sets ----------

def UPGRADES(u, t, atts, b, fx):
    works = [(k, atts[k]) for k in ("Work", "Work2") if k in atts]
    if u in (1, 5):  # steel chisels, then crystal chisels and glowing water
        look = LOOKS[t][1 if u == 1 else 2]
        for k, m in works:
            b.add("Chisels" + k[4:], place(chisel_row(**ROW[t], **look), m))
        if u == 5:
            for fn in GLOW_WATER.get(t, []):
                b.add("GlowWater", fn())
    elif u == 2:  # lamps on the frame (glowing gems from Frost-tech on)
        for key in ("Lamp1", "Lamp2"):
            if key in atts:
                b.add("Lamp" + key[-1], place(tier_lamp(t), atts[key]))
    elif u == 3:  # a faster wheel: a step-up gear pair on the drive, splashing water (particles in game)
        r, rim, hub = GEAR_LOOK[t]
        for key in ("Gear1", "Gear2"):
            if key in atts:
                b.add("Gear" + key[-1], place(low_gear(r, 12, 0.22, rim, hub), atts[key] @ M((0, 0, 0.13))))
                b.add("Pinion" + key[-1], place(low_gear(r * 0.5, 7, 0.2, rim, hub), atts[key] @ M((0, r * 1.32, 0.13), (0, 0, 0.2))))
        for key in ("Steam1", "Steam2"):
            if key in atts:
                fx.add("Splash" + key[-1], place(splash_standin(t), atts[key]))
    elif u == 4:  # chips and sparks where the chisels bite (particles in game)
        for key in ("Hit", "Hit2"):
            if key in atts:
                fx.add(key, place(hit_standin(t), atts[key]))


def AURA(atts, fx):
    """Kraken Mill: water droplets and bubbles spiralling round it in a teal mist."""
    c = atts["Aura"].to_translation()
    for k in range(28):
        s = k / 27
        a = s * 2 * math.pi * 2.3
        r = 4.4 - 0.9 * s
        p = Vector((c.x + r * math.cos(a), c.y + 0.4 + r * math.sin(a), c.z + 0.5 + 10.8 * s))
        if k % 2:
            tangent = Vector((-math.sin(a), math.cos(a), 0.35))
            fx.add("AuraDrops", place(teardrop(0.13, "IceBlue"), Matrix.Translation(p) @ align_z(-tangent)))
        else:
            r_b = 0.13 + 0.05 * (k % 3)
            bub = bmesh.new()
            blob(bub, p, (r_b,) * 3, 2)
            shine = bmesh.new()
            blob(shine, p + Vector((0.4, -0.55, 0.5)) * r_b, (0.3 * r_b, 0.3 * r_b, 0.22 * r_b), 1)
            fx.add("AuraBubbles", [(bub, "FrostLight", 0.0, False), (shine, "EyeWhite", 0.0, True)])
        if k % 4 == 1 and math.sin(a) > -0.5:  # teal mist drifting along the spiral (kept off the face)
            for d, r_m in ((Vector((0, 0, -0.35)), 0.3), (Vector((0.3, 0.1, -0.25)), 0.22), (Vector((-0.25, -0.1, -0.2)), 0.2)):
                mist = bmesh.new()
                blob(mist, p + d, (r_m, r_m, r_m * 0.8), 2)
                fx.add("AuraMist", [(mist, "PolarTeal", 0.0, True)])
    for k in range(10):  # and a low mist round the plinth
        a = k * 2 * math.pi / 10 + 0.3
        for j, r_m in enumerate((0.38, 0.28)):
            mist = bmesh.new()
            blob(mist, (c.x + (5.0 + 0.3 * j) * math.cos(a + 0.12 * j), c.y + (5.0 + 0.3 * j) * math.sin(a + 0.12 * j), c.z - 0.2 + 0.25 * j), (r_m, r_m, r_m * 0.75), 2)
            fx.add("AuraMist", [(mist, "PolarTeal", 0.0, True)])
