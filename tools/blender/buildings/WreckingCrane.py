# WreckingCrane.py - the Wrecking Crane's five tiers and its upgrade sets, for
# tools/blender/buildings/framework.py (style reference: IceDrill.py).
#
# Every tier: a boom (or arm) reaching toward -Y (the ice), and the wrecking ball hanging from its tip on
# a rope or chain. The ball and its rope/chain are one mesh per tier ("Ball", plus "BallGlow" for its
# glowing bits) so the game can swing them about the "Pivot" attachment (the hang point, +Z down).
# "Work" is the ball's centre, +Z toward the ice; "Counter" is where the 3rd upgrade's counterweight
# hangs from (+Z points back, away from the ice).
import math, bmesh
from mathutils import Vector, Matrix, Euler

TIER_Q = {"Scrappy": {"round": 1.0}, "Workshop": {"round": 1.0}, "Frost-tech": {"round": 1.1},
          "Enchanted": {"round": 1.25, "minor": 1.0, "corner": 2}, "Legendary": {"round": 1.0}}

BALL_R = {1: 0.9, 2: 1.05, 3: 1.15, 4: 1.3, 5: 1.5}
SWING_DIR = (0, -1, -0.25)  # the ball's +Z: toward the ice, a little down


# ---------- small helpers of this building ----------

def _hash(i, k=0):
    x = math.sin(i * 12.9898 + k * 78.233) * 43758.5453
    return x - math.floor(x) - 0.5


def _noise(d, seed, freq=2.4):
    """Smooth value noise on a unit direction, roughly -1..1."""
    total = 0.0
    for k in range(4):
        a = Vector((_hash(seed + k, 1), _hash(seed + k, 2), _hash(seed + k, 3)))
        a = a.normalized() if a.length > 1e-4 else Vector((0, 0, 1))
        total += math.sin(d.dot(a) * freq * (1 + 0.7 * k) + seed * 1.7 + k * 2.1) / (1 + 0.45 * k)
    return total / 2.0


def sphere(r, swatch, center=(0, 0, 0), segs=16, rings=10, glow=False):
    bm = bmesh.new()
    prof = [(r * math.sin(math.pi * i / rings), -r * math.cos(math.pi * i / rings)) for i in range(rings + 1)]
    lathe(bm, prof, segs, M(center))
    return [(bm, swatch, 0.0, glow)]


def lumpy_ball(r, swatch, center=(0, 0, 0), seed=1, subdiv=3, amp=0.1, crack=None, crack_depth=0.86, flat=False):
    """A rock ball: an icosphere pushed in and out by smooth noise. Where the noise drops under `crack`
    the surface sinks to crack_depth * r (a glowing core inside shows through there)."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    for v in bm.verts:
        d = v.co.normalized()
        n = _noise(d, seed)
        rad = r * (1 + amp * n)
        if crack is not None and n < crack:
            rad = r * crack_depth
        v.co = Vector(center) + d * rad
    if flat:
        faceted(bm)
    return [(bm, swatch, 0.0, False)]


def rock(size, center, seed, swatch="StoneDark", rotation=(0, 0, 0)):
    """A faceted low-poly rock (rubble)."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    turn = Euler(rotation).to_matrix()
    for i, v in enumerate(bm.verts):
        j = 1 + 0.22 * _hash(seed * 7 + i, 4)
        v.co = Vector(center) + turn @ Vector((v.co.x * size[0] * j, v.co.y * size[1] * j, v.co.z * size[2] * j))
    return [(faceted(bm), swatch, 0.0, False)]


def chain_between(p0, p1, size, swatch, glow=False):
    """A chain of links from p0 to p1 (cheaper links than the kit's chain())."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    pitch = size * 2.3
    n = max(1, int(round((d.length - size * 0.6) / pitch)))
    base = Matrix.Translation(p0) @ align_z(-d)
    pieces = []
    for i in range(n):
        bm = bmesh.new()
        m = (Matrix.Translation((0, 0, -size * 1.4 - i * pitch)) @ Matrix.Rotation(i * math.pi / 2, 4, "Z")
             @ Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Diagonal((1.0, 1.6, 1.0, 1.0)))
        torus(bm, base @ m, size, size * 0.32, 10, 4)
        pieces.append((bm, swatch, 0.0, glow))
    return pieces


def glowing(pieces):
    return [(bm, sw, bev, True) for bm, sw, bev, _ in pieces]


def rope(points, radius=0.06, swatch="PineLight", segs=6):
    bm = bmesh.new()
    sweep(bm, [Vector(p) for p in points], radius, segs)
    return [(bm, swatch, 0.0, False)]


def ring_at(matrix, radius, minor, swatch, glow=False, segs=16, minor_segs=4):
    bm = bmesh.new()
    torus(bm, matrix, radius, minor, segs, minor_segs)
    return [(bm, swatch, 0.0, glow)]


def fib_dirs(n):
    out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(max(0.0, 1 - z * z))
        a = i * 2.39996
        out.append(Vector((rr * math.cos(a), rr * math.sin(a), z)))
    return out


def spikes(center, r, n, length, base, swatch, top_gap=0.8):
    """Cone spikes all over a ball, leaving the top free for the chain's lug."""
    pieces = []
    c = Vector(center)
    for d in fib_dirs(n):
        if d.z > top_gap:
            continue
        bm = bmesh.new()
        cylinder(bm, c + d * (r * 0.85), base, length + r * 0.15, 8, top=0.0, direction=d)
        pieces.append((bm, swatch, 0.0, False))
    return pieces


def lug(top, swatch, size=0.18):
    """A shackle lug on top of a ball: a collar and an upright ring."""
    top = Vector(top)
    pieces = place(cyl(size * 1.3, size * 1.2, swatch, 10), M(top - Vector((0, 0, size * 0.6))))
    pieces += ring_at(Matrix.Translation(top + Vector((0, 0, size * 1.3))) @ Matrix.Rotation(math.pi / 2, 4, "X"), size * 1.1, size * 0.35, swatch, segs=10)
    return pieces


def hewn(size, matrix, swatch, seed, cuts=1, levels=2, rough=0.08):
    """A hewn stone block: a jittered cage, subdivided. Returns (pieces, local bmesh points before the move)."""
    cage = cage_box(size, cuts)
    for i, v in enumerate(cage.verts):
        v.co += Vector((_hash(seed + i, 1), _hash(seed + i, 2), _hash(seed + i, 3))) * rough * min(size)
    bm = subsurf(cage, levels)
    local = [v.co.copy() for v in bm.verts]
    bm.transform(matrix)
    return [(bm, swatch, 0.0, False)], local


def half_extent(points, z, reach=0.3):
    ring = [p for p in points if abs(p.z - z) < reach]
    return max(abs(p.x) for p in ring), max(abs(p.y) for p in ring)


def band(points, z, height, swatch, grow=0.06):
    """A band hugging a hewn block at local height z (built in the block's local frame)."""
    hx, hy = half_extent(points, z)
    bm = bmesh.new()
    rounded_block(bm, (2 * hx + grow * 2, 2 * hy + grow * 2, height), M((0, 0, z)), corner=min(hx, hy) * 0.6, edge=0.05, corner_seg=3, edge_seg=1)
    return [(bm, swatch, 0.0, False)]


def lattice(p0, p1, w0, w1, h0, h1, bays, rail="Iron", brace="Steel", rail_r=0.09, brace_r=0.05):
    """A lattice boom from p0 to p1: four rails and zigzag braces on all four faces."""
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0).normalized()
    side = Vector((1, 0, 0))
    up = d.cross(side).normalized()

    def c(s, i, j):
        return p0 + (p1 - p0) * s + side * (i * (w0 + (w1 - w0) * s) / 2) + up * (j * (h0 + (h1 - h0) * s) / 2)

    pieces = []
    for i in (-1, 1):
        for j in (-1, 1):
            pieces += rope([c(0, i, j), c(1, i, j)], rail_r, rail, 8)
    for k in range(bays):
        s0, s1 = k / bays, (k + 1) / bays
        for i in (-1, 1):  # side faces
            a, bb = (-1, 1) if k % 2 else (1, -1)
            pieces += rope([c(s0, i, a), c(s1, i, bb)], brace_r, brace, 6)
        for j in (-1, 1):  # top and bottom faces
            a, bb = (-1, 1) if k % 2 else (1, -1)
            pieces += rope([c(s0, a, j), c(s1, bb, j)], brace_r, brace, 6)
    return pieces


def along(p0, p1):
    """A frame at p0 whose +Z runs to p1."""
    p0, p1 = Vector(p0), Vector(p1)
    return Matrix.Translation(p0) @ align_z(p1 - p0)


def flag(p, length=0.9, height=0.55, swatch="WarnRed"):
    """A little triangular pennant flying toward +X from p (its top corner)."""
    p = Vector(p)
    bm = bmesh.new()
    t = 0.03
    pts = [p, p + Vector((0, 0, -height)), p + Vector((length, 0, -height * 0.45))]
    front_v = [bm.verts.new(q + Vector((0, -t, 0))) for q in pts]
    back_v = [bm.verts.new(q + Vector((0, t, 0))) for q in pts]
    bm.faces.new(front_v)
    bm.faces.new(list(reversed(back_v)))
    for k in range(3):
        j = (k + 1) % 3
        bm.faces.new((front_v[k], back_v[k], back_v[j], front_v[j]))
    return [(bm, swatch, 0.0, False)]


def zigzag_bolt(p0, direction, length, swatch="LampYellow", width=0.08):
    """A little lightning bolt (glow) from p0 along direction."""
    p0, d = Vector(p0), Vector(direction).normalized()
    side = d.cross(Vector((0, 0, 1)))
    side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
    pts = [p0, p0 + d * length * 0.35 + side * 0.18, p0 + d * length * 0.6 - side * 0.12, p0 + d * length]
    bm = bmesh.new()
    sweep(bm, pts, width, 5, radius_end=0.015)
    return [(bm, swatch, 0.0, True)]


def sheave(r, thick, rim="Brass", hub="Copper", holes=4):
    """A grooved pulley wheel about Z: a rim with a rope groove, a thinner web with holes, a hub."""
    h = thick / 2
    bm = bmesh.new()
    lathe(bm, [(0, -h * 0.45), (r * 0.78, -h * 0.45), (r * 0.84, -h), (r, -h), (r * 0.86, 0), (r, h), (r * 0.84, h), (r * 0.78, h * 0.45), (0, h * 0.45)], 16)
    pieces = [(bm, rim, 0.0, False)]
    pieces += place(cyl(r * 0.24, thick * 1.3, hub, 10), M((0, 0, -thick * 0.65)))
    for k in range(holes):
        a = k * 2 * math.pi / holes + math.pi / 4
        pieces += place(cyl(r * 0.14, 0.04, "Gunmetal", 8), M((r * 0.52 * math.cos(a), r * 0.52 * math.sin(a), h * 0.45)))
    return pieces


def cart_wheel(r, swatch="Rust", hub="RustDark", spokes=4):
    pieces = ring_at(Matrix(), r, 0.07, swatch, segs=14)
    for k in range(spokes):
        a = k * 2 * math.pi / spokes
        pieces += rope([(0, 0, 0), (r * math.cos(a), r * math.sin(a), 0)], 0.04, swatch, 5)
    pieces += place(cyl(r * 0.22, 0.2, hub, 10), M((0, 0, -0.1)))
    return pieces


def standard_atts(work, pivot, hit, trail_r, extra):
    atts = {"Work": frame(work, out=SWING_DIR), "Pivot": frame(pivot, out=(0, 0, -1), up=(0, -1, 0)),
            "Hit": frame(hit, out=(0, -1, 0.6)), "Trail": frame(Vector(work) + Vector((0, trail_r, 0)), out=(0, 1, 0.35))}
    atts.update(extra)
    return atts


# ---------- tier 1: Scrappy, a small wooden crane ----------

def tier_scrappy(b):
    for k, (y, sw, gr) in enumerate(((-1.0, "Pine", "PineDark"), (0.0, "PineLight", "Pine"), (1.0, "PineDark", "RustDark"), (2.0, "Pine", "PineDark"))):
        b.add("Deck", place(plank(5.2, 0.95, 0.25, sw, gr, True, k * 1.3), M((0.12 * _hash(k), y, 0), (0, 0, 0.04 * _hash(k, 2)))))
    # the mast: a post, two back braces on stone feet, rope lashings
    post = V(0, 1.7, 0.25)
    b.add("Mast", grained_beam(post, (0, 1.7, 6.0), 0.5, "Pine", "PineDark"))
    for sx, sw, gr in ((-1, "PineLight", "Pine"), (1, "PineDark", "RustDark")):
        foot = V(sx * 1.7, 2.45, 0.35)
        b.add("Mast", grained_beam(foot, (sx * 0.18, 1.85, 4.3), 0.3, sw, gr))
        stone = bmesh.new()
        blob(stone, (foot.x, foot.y, 0.35), (0.32, 0.28, 0.16), 1, floor=0.25)
        b.add("Mast", [(stone, "StoneDark", 0.0, False)])
    for z, tilt in ((4.3, 0.2), (5.75, -0.25)):
        b.add("Mast", ring_at(Matrix.Translation((0, 1.7, z)) @ Matrix.Rotation(tilt, 4, "X"), 0.36, 0.06, "PineLight", segs=12))
    b.add("Mast", place(block((0.6, 0.45, 0.09), "PineDark", corner=0.05, edge=0.03), M((0, 1.25, 2.95))))  # lantern shelf
    b.add("Mast", rope([(0, 1.45, 2.6), (0, 1.1, 2.92)], 0.04, "Iron", 5))
    b.add("Mast", pipe_between((0, 2.0, 5.0), (0, 2.0, 7.0), 0.05, "PineDark"))  # flag pole on the back
    b.add("Mast", flag((0, 2.0, 6.95), 0.85, 0.5, "WarnRed"))
    # the boom: heel on an iron hinge at the post, tip with a pulley block
    heel, tip = V(0, 1.15, 1.7), V(0, -3.9, 5.5)
    b.add("Boom", grained_beam(heel, tip, 0.42, "PineLight", "Pine"))
    b.add("Boom", place(block((0.5, 0.42, 0.05), "PatchGreen", corner=0.05, edge=0.02), frame(heel.lerp(tip, 0.45) + V(0.2, 0, 0), out=(1, 0, 0))))
    for k in range(4):
        b.add("Boom", place(rivet(0.035, "Iron"), frame(heel.lerp(tip, 0.45) + V(0.26, 0.17 * (1 if k % 2 else -1), 0.14 * (1 if k // 2 else -1)), out=(1, 0, 0))))
    for sx in (-1, 1):
        b.add("Boom", place(block((0.06, 0.75, 0.32), "Iron", corner=0.03, edge=0.02), M((sx * 0.27, 1.35, 1.55))))
        b.add("Boom", place(block((0.07, 0.36, 0.8), "Pine", corner=0.03, edge=0.02), M((sx * 0.2, -4.0, 4.75))))  # pulley cheeks
    b.add("Boom", place(cyl(0.07, 0.62, "Iron", 8), frame((-0.31, 1.35, 1.7), out=(1, 0, 0))))
    b.add("Boom", place(cyl(0.06, 0.52, "Iron", 8), frame((-0.26, -4.0, 5.1), out=(1, 0, 0))))
    wheel = bmesh.new()
    lathe(wheel, [(0, -0.12), (0.34, -0.12), (0.27, 0.0), (0.34, 0.12), (0, 0.12)], 12, frame((0, -4.0, 5.1), out=(1, 0, 0)))
    b.add("Boom", [(wheel, "PineDark", 0.0, False)])
    b.add("Boom", ring_at(Matrix.Translation(tip.lerp(heel, 0.04)) @ align_z(tip - heel), 0.27, 0.05, "Iron", segs=12))
    # the stay rope from the post top to the tip, and the hoist rope from the winch to the pulley
    b.add("Ropes", cable((0, 1.6, 5.95), (0, -3.85, 5.72), 0.25, 0.05, "PineLight", "Iron"))
    b.add("Ropes", rope([(0, 0.5, 1.3), (0, -3.72, 5.0)], 0.05))
    # the winch: a drum on two trestles, a cart-wheel crank with a worn grip
    for sx in (-1, 1):
        for y0 in (0.05, 0.95):
            b.add("Winch", rope([(sx * 0.75, y0, 0.25), (sx * 0.75, 0.5, 1.1)], 0.08, "PineDark", 6))
    b.add("Winch", place(cyl(0.3, 1.36, "PineLight", 12), frame((-0.68, 0.5, 1.0), out=(1, 0, 0))))
    for x in (-0.35, 0.2):
        b.add("Winch", ring_at(frame((x, 0.5, 1.0), out=(1, 0, 0)), 0.31, 0.045, "Pine", segs=12))
    b.add("Winch", place(cart_wheel(0.42), frame((0.82, 0.5, 1.0), out=(1, 0, 0))))
    b.add("Winch", rope([(0.88, 0.5, 1.0), (0.98, 0.5, 1.3), (1.05, 0.5, 1.45)], 0.04, "Iron"))
    b.add("Winch", place(cyl(0.07, 0.35, "PineLight", 10), frame((1.05, 0.5, 1.45), out=(1, 0, 0))))
    # junk: a crate of stones (the counterweight), a barrel, a coil of rope
    b.add("Junk", place(block((1.2, 1.0, 0.65), "PineDark", corner=0.06, edge=0.04), M((1.5, 1.95, 0.25))))
    b.add("Junk", trim_strip((0.9, 1.44, 0.6), (2.1, 1.44, 0.6), 0.05, "RustDark"))
    for k in range(5):
        b.add("Junk", rock((0.28, 0.24, 0.2), (1.2 + 0.3 * (k % 3), 1.75 + 0.35 * (k // 3), 0.95), k + 3, "Stone" if k % 2 else "StoneDark"))
    bx, by = -1.85, 1.9
    barrel = bmesh.new()
    lathe(barrel, [(0, 0), (0.42, 0), (0.5, 0.3), (0.52, 0.55), (0.5, 0.8), (0.42, 1.1), (0, 1.1)], 14, M((bx, by, 0.25)))
    b.add("Junk", [(barrel, "Rust", 0.0, False)])
    for z in (0.45, 1.1):
        b.add("Junk", ring_at(M((bx, by, z)), 0.5, 0.035, "Iron", segs=14))
    b.add("Junk", place(cyl(0.4, 0.06, "PineDark", 14), M((bx, by, 1.33))))
    # the ball: a rusty iron ball with iron bands, a patch, a lug, on a rope from the pulley
    r = BALL_R[1]
    pivot, ball = V(0, -4.3, 5.1), V(0, -4.3, 2.15)
    b.add("Ball", rope([pivot, ball + V(0, 0, r + 0.45)], 0.06))
    b.add("Ball", ring_at(Matrix.Translation(ball + V(0, 0, r + 0.42)) @ Matrix.Rotation(math.pi / 2, 4, "Y"), 0.13, 0.04, "Iron", segs=10))
    b.add("Ball", sphere(r, "SteelDark", ball, 14, 9))
    b.add("Ball", ring_at(M(ball), r + 0.02, 0.06, "Rust", segs=14))
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.3
        b.add("Ball", place(rivet(0.05, "RustDark"), frame(ball + V((r + 0.05) * math.cos(a), (r + 0.05) * math.sin(a), 0), out=(math.cos(a), math.sin(a), 0))))
    b.add("Ball", place(block((0.42, 0.42, 0.06), "PatchGreen", corner=0.06, edge=0.02), frame(ball + V(0.43, -0.7, 0.24), out=(0.5, -0.8, 0.28))))
    b.add("Ball", lug(ball + V(0, 0, r), "Iron", 0.12))
    return standard_atts(ball, pivot, (0, -5.4, 0.9), r, {
        "Lamp1": up_((0, 1.25, 3.04)), "Lamp2": up_((0, 1.7, 6.0)),
        "Gear1": frame((0.25, -4.0, 5.1), out=(1, 0, 0)), "Gear2": frame((0.26, 1.7, 5.1), out=(1, 0, 0)),
        "Counter": frame((0, 1.96, 5.4), out=(0, 1, 0)), "NamePlate": front((0, -1.5, 0.14)),
        "Aura": up_((0, 0, 0.25)), "Top": up_((0, 2.0, 7.05))})


# ---------- tier 2: Workshop, a steampunk crane ----------

def tier_workshop(b):
    for k, y in enumerate((-1.6, -0.6, 0.4, 1.4, 2.4)):
        b.add("Deck", place(plank(6.4, 0.96, 0.5, "Pine", "PineDark", k in (0, 4), k * 1.1), M((0, y, 0))))
    # the turntable: an iron drum with a brass slewing gear
    b.add("Turntable", place(cyl(2.0, 0.22, "Iron", 20), M((0, 1.0, 0.5))))
    b.add("Turntable", place(gear(2.05, 20, 0.18, 0.14, "Brass", "Iron"), M((0, 1.0, 0.8))))
    # the cab: a copper housing with portholes, a door, a dial, a vent and an arched brass roof
    b.add("Cab", place(lidded_box((2.8, 2.4, 2.1), "Copper", "Copper", "Brass"), M((0, 1.1, 0.9))))
    roof = bmesh.new()
    rounded_block(roof, (3.2, 2.8, 0.32), M((0, 1.1, 3.18)), corner=0.5, edge=0.14, taper=0.92)
    b.add("Cab", [(roof, "Brass", 0.0, False)])
    for sx in (-1, 1):
        at = front((sx * 0.7, -0.12, 2.15))
        b.add("Cab", place(ring_at(Matrix(), 0.32, 0.08, "Brass", segs=14), at))
        b.add("Cab", glowing(place(cyl(0.27, 0.04, "LampYellow", 14), at)))
    b.add("Cab", place(inset_panel(0.9, 1.4, 0.05, "Copper", "RustDark", True), frame((1.42, 1.3, 1.75), out=(1, 0, 0))))
    b.add("Cab", place(dial(0.3, "Cream", "Brass", "WarnRed", 0.6), frame((-1.42, 0.9, 2.1), out=(-1, 0, 0))))
    b.add("Cab", place(vent(1.2, 0.5, 4, "RustDark", "Brass"), frame((0.4, 2.32, 2.2), out=(0, 1, 0))))
    # the boiler and its chimney at the back
    boiler = bmesh.new()
    lathe(boiler, [(0, 0), (0.5, 0), (0.55, 0.1), (0.55, 2.1), (0.45, 2.35), (0.2, 2.45), (0, 2.45)], 14, M((-0.9, 2.55, 0.9)))
    b.add("Boiler", [(boiler, "Brass", 0.0, False)])
    for z in (1.3, 2.4):
        b.add("Boiler", place(trim_ring(0.57, 0, "Copper", minor=0.06, segments=14), M((-0.9, 2.55, z))))
    b.add("Boiler", pipe_between((-0.9, 2.55, 3.3), (-0.9, 2.55, 6.0), 0.18, "Iron"))
    cap = bmesh.new()
    lathe(cap, [(0.14, 6.0), (0.32, 6.05), (0.36, 6.2), (0.24, 6.35), (0, 6.38)], 12, M((-0.9, 2.55, 0)))
    b.add("Boiler", [(cap, "Copper", 0.0, False)])
    b.add("Boiler", place(trim_ring(0.2, 0, "Brass", minor=0.05, segments=12), M((-0.9, 2.55, 4.8))))
    b.add("Boiler", cable((-0.5, 2.6, 2.6), (0.6, 2.35, 2.9), 0.25, 0.07, "Copper", "Brass"))
    # a riveted iron counterweight on the back of the turntable
    b.add("Counterweight", place(block((1.3, 0.8, 1.5), "Iron", corner=0.15, edge=0.08), M((0.75, 2.6, 0.9))))
    b.add("Counterweight", place(riveted_plate(1.1, 1.2, 0.05, "SteelDark", "Brass", 0.35), frame((0.75, 3.01, 1.65), out=(0, 1, 0))))
    # the A-frame gantry on the roof with pendant cables to the boom tip
    apex = V(0, 2.0, 7.6)
    for sx in (-1, 1):
        b.add("Gantry", beam_between((sx * 1.2, 1.9, 3.3), apex + V(sx * 0.12, 0, 0), 0.22, swatch="Iron"))
        b.add("Gantry", place(bolt(0.09, "Brass", "Iron"), frame((sx * 1.2, 1.9, 3.36))))
    b.add("Gantry", beam_between((-0.7, 1.93, 5.6), (0.7, 1.93, 5.6), 0.16, swatch="SteelDark"))
    b.add("Gantry", place(cyl(0.3, 0.3, "Brass", 12), M(apex + V(0, 0, -0.1))))
    b.add("Gantry", place(rivet_ring(0.24, 5, 0.04, "Copper"), M(apex + V(0, 0, 0.2))))
    heel, tip = V(0, -0.3, 2.9), V(0, -4.2, 8.4)
    for sx in (-1, 1):
        b.add("Cables", cable(apex + V(sx * 0.1, -0.1, 0), tip + V(sx * 0.16, 0, 0.1), 0.15, 0.04, "SteelDark", "Brass"))
    # the lattice boom with brass collars at both ends, a heel pin and a sheave at the tip
    b.add("Boom", lattice(heel, tip, 0.9, 0.45, 0.7, 0.42, 6, "Iron", "SteelDark", 0.08, 0.045))
    b.add("BoomTrim", place(block((1.0, 0.8, 0.35), "Brass", corner=0.12, edge=0.06), along(heel, tip) @ M((0, 0, 0.05))))
    b.add("BoomTrim", place(cyl(0.12, 1.3, "Copper", 10), frame((-0.65, -0.3, 2.9), out=(1, 0, 0))))
    for sx in (-1, 1):
        b.add("BoomTrim", place(block((0.08, 0.7, 0.9), "Brass", corner=0.05, edge=0.03), M((sx * 0.3, -4.25, 7.9))))
        b.add("BoomTrim", place(rivet_ring(0.25, 4, 0.04, "Copper"), frame((sx * 0.34, -4.25, 8.35), out=(sx, 0, 0))))
    b.add("Sheave", place(sheave(0.5, 0.22, "Brass", "Copper"), frame((0, -4.25, 8.35), out=(1, 0, 0))))
    # the ball: a dark steel ball with a riveted brass band and a copper cap, on an iron chain
    r = BALL_R[2]
    pivot, ball = V(0, -4.6, 8.05), V(0, -4.6, 2.3)
    b.add("Ball", chain_between(pivot, ball + V(0, 0, r + 0.3), 0.17, "Iron"))
    b.add("Ball", sphere(r, "SteelDark", ball, 16, 10))
    b.add("Ball", ring_at(M(ball), r + 0.02, 0.09, "Brass", segs=16))
    for k in range(6):
        a = k * math.pi / 3
        b.add("Ball", place(rivet(0.06, "Copper"), frame(ball + V((r + 0.1) * math.cos(a), (r + 0.1) * math.sin(a), 0), out=(math.cos(a), math.sin(a), 0))))
    capm = bmesh.new()
    lathe(capm, [(0, r * 0.82), (0.5, r * 0.82), (0.46, r * 0.94), (0, r * 1.02)], 14, M(ball))
    b.add("Ball", [(capm, "Copper", 0.0, False)])
    b.add("Ball", lug(ball + V(0, 0, r), "Brass", 0.14))
    return standard_atts(ball, pivot, (0, -5.6, 1.1), r, {
        "Lamp1": up_((1.05, -0.05, 3.34)), "Lamp2": up_((0, 2.0, 7.9)),
        "Gear1": frame((0.4, -4.25, 8.35), out=(1, 0, 0)), "Gear2": frame((1.45, 1.6, 2.9), out=(1, 0, 0)),
        "Steam1": up_((-0.9, 2.55, 6.4)), "Counter": frame((0, 2.3, 7.3), out=(0, 1, 0)),
        "NamePlate": front((0, -2.1, 0.25)), "Aura": up_((0, 0, 0.5)), "Top": up_((0, -4.25, 8.9))})


# ---------- tier 3: Frost-tech, a crystal magnet crane on an energy chain ----------

def tier_frosttech(b):
    b.add("Deck", place(block((9.2, 7.6, 0.8), "SnowWhite", corner=1.4, edge=0.3), M((0, 1.0, 0))))
    b.add("Deck", place(block((8.2, 6.6, 0.3), "IceBlue", corner=1.1, edge=0.12), M((0, 1.0, 0.8))))
    for sx in (-1, 1):
        b.add("Deck", place(vent(1.4, 0.4, 5, "GlacierBlue", "SteelLight"), front((sx * 2.5, -2.79, 0.42))))
        b.add("Deck", place(inset_panel(1.6, 1.1, 0.05, "FrostLight", "GlacierBlue", True), M((sx * 2.6, -1.4, 1.1))))
        for sy in (-1, 1):
            b.add("Deck", place(bolt(0.1, "SteelLight", "GlacierBlue"), M((sx * 3.7, 1.0 + sy * 2.7, 1.1))))
    for p0, p1 in (((-3.0, -2.83, 0.42), (3.0, -2.83, 0.42)), ((-3.0, 4.83, 0.42), (3.0, 4.83, 0.42)),
                   ((-4.63, -1.0, 0.42), (-4.63, 3.0, 0.42)), ((4.63, -1.0, 0.42), (4.63, 3.0, 0.42))):
        b.add("Deck", trim_strip(p0, p1, 0.16, "AuroraCyan", True))
    # the turntable and the tower
    b.add("Tower", place(cyl(2.0, 0.3, "SteelLight", 20), M((0, 1.5, 1.1))))
    b.add("Tower", ring_at(M((0, 1.5, 1.25)), 2.05, 0.08, "AuroraCyan", True, 24))
    b.add("Tower", place(block((2.4, 2.2, 5.6), "SnowWhite", corner=0.8, edge=0.4), M((0, 1.6, 1.4))))
    for z in (3.0, 5.0):
        b.add("Tower", place(block((2.46, 2.26, 0.08), "GlacierBlue", corner=0.82, edge=0.02), M((0, 1.6, z))))
    b.add("Tower", place(screen(0.9, 0.55, "AuroraCyan", "NavyIce", 3), front((0, 0.49, 4.0))))
    b.add("Tower", place(vent(0.9, 0.6, 4, "GlacierBlue", "SteelLight"), frame((0, 2.71, 4.0), out=(0, 1, 0))))
    b.add("Tower", trim_strip((0, 0.47, 1.8), (0, 0.47, 3.4), 0.1, "AuroraCyan", True))
    # the cab on top with a dark visor
    b.add("Cab", place(block((2.6, 2.5, 1.6), "SteelLight", corner=0.7, edge=0.35), M((0, 1.4, 7.0))))
    b.add("Cab", place(block((2.2, 2.1, 0.2), "GlacierBlue", corner=0.6, edge=0.08), M((0, 1.4, 8.58))))
    visor = bmesh.new()
    rounded_block(visor, (2.0, 0.3, 0.7), M((0, 0.2, 7.85)), corner=0.25, edge=0.1)
    b.add("Cab", [(visor, "NavyIce", 0.0, False)])
    b.add("Cab", trim_strip((-0.85, 0.05, 7.42), (0.85, 0.05, 7.42), 0.07, "AuroraCyan", True))
    b.add("Cab", place(handle(0.5, 0.15, 0.04, "GlacierBlue"), frame((1.31, 1.4, 7.8), out=(1, 0, 0))))
    b.add("Cab", place(cyl(0.12, 1.6, "SteelLight", 8), M((0, 2.3, 8.7))))  # the stay mast
    b.add("Cab", place(cyl(0.2, 0.14, "GlacierBlue", 10), M((0, 2.3, 10.2))))
    for x in (-0.12, 0.12):  # glowing stays to the tip and the jib
        b.add("Cab", trim_strip((x, 2.2, 10.25), (x * 2, -4.45, 10.62), 0.06, "AuroraCyan", True))
    b.add("Cab", trim_strip((0, 2.4, 10.25), (0, 4.25, 8.7), 0.06, "AuroraCyan", True))
    # two crystal coils power it, and a crystal core at the back
    for sx in (-1, 1):
        b.add("Coils", place(cyl(0.55, 0.3, "GlacierBlue", 12), M((sx * 1.95, 2.4, 1.1))))
        b.add("Coils", place(coil(0.4, 3.0, turns=6, core="SteelDark", wire="IceBlue", top="AuroraCyan"), M((sx * 1.95, 2.4, 1.4))))
        b.add("Coils", cable((sx * 1.95, 2.75, 1.6), (sx * 1.2, 2.2, 2.2), 0.2, 0.07, "NavyIce", "GlacierBlue"))
    b.add("Core", place(cut_crystal_cluster(0.9, "CrystalCyan", "SteelLight", 5), M((0, 3.95, 1.1))))
    b.add("Core", ring_at(M((0, 3.95, 1.2)), 0.85, 0.07, "AuroraCyan", True, 16))
    # the boom: a tapered white box girder with glowing strips and panel bands, and a rear jib
    heel, tip = V(0, 0.4, 8.1), V(0, -4.55, 10.4)
    L = (tip - heel).length
    gm = along(heel, tip)
    boom = bmesh.new()
    rounded_block(boom, (0.85, 0.7, L), M((0, 0, L / 2)), corner=0.3, edge=0.12, taper=0.65)
    b.add("Boom", place([(boom, "SnowWhite", 0.0, False)], gm))
    for s in (0.25, 0.5, 0.75):
        w = 1 - 0.35 * s
        b.add("Boom", place(block((0.89 * w, 0.74 * w, 0.06), "GlacierBlue", corner=0.3 * w, edge=0.02), gm @ M((0, 0, s * L))))
    for sx in (-1, 1):
        b.add("Boom", trim_strip(heel + V(sx * 0.43, 0, 0.0), tip + V(sx * 0.28, 0, 0.0), 0.07, "AuroraCyan", True))
    b.add("Boom", place(cyl(0.3, 1.0, "SteelLight", 14), frame((-0.5, -4.55, 10.4), out=(1, 0, 0))))
    jib0, jib1 = V(0, 2.6, 8.2), V(0, 4.3, 8.45)
    b.add("Boom", place(block((0.7, 0.6, (jib1 - jib0).length), "SteelLight", corner=0.25, edge=0.1), along(jib0, jib1)))
    b.add("Boom", place(block((1.2, 1.0, 1.0), "NavyIce", corner=0.3, edge=0.15), M((0, 4.1, 7.15))))
    b.add("Boom", place(cut_crystal(0.8, 0.22, "CrystalCyan", (0.15, 0.1)), M((0, 4.1, 8.12))))
    b.add("Boom", place(screen(0.6, 0.35, "AuroraCyan", "NavyIce", 2), frame((0, 4.61, 7.65), out=(0, 1, 0))))
    # the crystal magnet under the tip: a housing, a glowing pad and crystals round its rim
    mag = V(0, -4.6, 9.8)
    b.add("Magnet", beam_between((0, -4.55, 10.4), mag + V(0, 0, 0.4), 0.3, swatch="SteelDark"))
    b.add("Magnet", place(cyl(0.75, 0.45, "SteelLight", 16), M(mag)))
    b.add("Magnet", place(trim_ring(0.77, 0.3, "GlacierBlue", minor=0.06, segments=16), M(mag)))
    b.add("Magnet", glowing(place(cyl(0.6, 0.06, "AuroraCyan", 16), M(mag + V(0, 0, -0.05)))))
    for k in range(6):
        a = k * math.pi / 3
        b.add("Magnet", place(cut_crystal(0.45, 0.1, "CrystalCyan", sides=6), frame(mag + V(0.68 * math.cos(a), 0.68 * math.sin(a), 0.05), out=(0.4 * math.cos(a), 0.4 * math.sin(a), -1))))
    # the ball: a polished steel ball with a glowing band and crystal studs, on an energy chain
    r = BALL_R[3]
    pivot, ball = V(0, -4.6, 9.72), V(0, -4.6, 2.5)
    b.add("Ball", chain_between(pivot, ball + V(0, 0, r + 0.25), 0.16, "AuroraCyan", glow=True))
    b.add("Ball", sphere(r, "SteelLight", ball, 18, 11))
    b.add("Ball", ring_at(M(ball), r + 0.01, 0.08, "AuroraCyan", True, 18))
    for z in (-0.45, 0.45):
        rr = math.sqrt(r * r - z * z)
        b.add("Ball", ring_at(M(ball + V(0, 0, z)), rr + 0.01, 0.05, "GlacierBlue", segs=18))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        d = V(math.cos(a), math.sin(a), 0.45).normalized()
        b.add("Ball", place(gem_setting(0.16, "CrystalCyan", "SteelLight", 4), frame(ball + d * (r - 0.02), out=d)))
    capm = bmesh.new()
    lathe(capm, [(0, r * 0.85), (0.55, r * 0.85), (0.5, r * 0.97), (0, r * 1.03)], 14, M(ball))
    b.add("Ball", [(capm, "NavyIce", 0.0, False)])
    b.add("Ball", lug(ball + V(0, 0, r), "SteelLight", 0.15))
    return standard_atts(ball, pivot, (0, -5.7, 1.2), r, {
        "Lamp1": up_((0.85, 0.75, 8.68)), "Lamp2": up_((0, 2.3, 10.34)),
        "Gear1": frame((0.5, -4.55, 10.4), out=(1, 0, 0)), "Gear2": frame((1.21, 1.6, 6.0), out=(1, 0, 0)),
        "Steam1": up_((1.95, 2.4, 4.9)), "Steam2": up_((-1.95, 2.4, 4.9)), "Counter": frame((0, 4.4, 8.5), out=(0, 1, 0)),
        "NamePlate": front((0, -2.82, 0.4)), "Aura": up_((0, 0, 1.1)), "Top": up_((0, -4.55, 10.8))})


# ---------- tier 4: Enchanted, a floating crane arm swinging a storm-cloud ball ----------

def hex_column(r0, r1, z0, z1, swatch="Moonstone"):
    bm = bmesh.new()
    lathe(bm, [(0, z0), (r0, z0), (r0 * 1.02, z0 + 0.15), (r1 * 1.02, z1 - 0.15), (r1, z1), (0, z1)], 6, M((0, 0, 0), (0, 0, math.pi / 6)))
    return [(bm, swatch, 0.03, False)]


def storm_cloud(center, r, seed=3):
    c = Vector(center)
    pieces = sphere(r * 0.62, "AuroraViolet", c, 12, 8, glow=True)
    for k, d in enumerate(fib_dirs(9)):
        s = r * (0.55 + 0.12 * _hash(seed + k, 5))
        p = c + d * (r * 0.5)
        bm = bmesh.new()
        blob(bm, p, (s * 1.1, s, s * 0.85), 3)
        pieces.append((bm, "StoneDark" if d.z < -0.1 else ("Stone" if d.z < 0.5 else "StoneLight"), 0.0, False))
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.3
        d = V(math.cos(a), math.sin(a), -0.6)
        pieces += zigzag_bolt(c + d.normalized() * r * 0.75, d, 1.1, "LampYellow" if k % 2 else "Diamond", 0.1)
    return pieces


def tier_enchanted(b):
    dais = bmesh.new()
    lathe(dais, [(0, 0), (5.0, 0), (5.0, 0.3), (4.8, 0.35), (4.8, 0.55), (4.55, 0.8), (0, 0.8)], 6)
    b.add("Dais", [(dais, "Moonstone", 0.04, False)])
    plinth = bmesh.new()
    lathe(plinth, [(0, -0.01), (5.12, -0.01), (5.12, 0.18), (0, 0.18)], 6)
    b.add("Dais", [(plinth, "StoneDark", 0.03, False)])
    b.add("Dais", place(trim_ring(4.67, 0, "RuneViolet", minor=0.08, segments=6), M((0, 0, 0.56))))
    b.add("Dais", place(engraved_rune_ring(3.4, "RuneGlow", "ArcaneDeep", "RuneViolet", 14), M((0, 0, 0.8))))
    for k in range(6):
        fa = k * math.pi / 3 + math.pi / 6
        apothem = 5.0 * math.cos(math.pi / 6)
        b.add("Dais", place(gem_setting(0.15, "AuroraCyan", "Gold", 4), frame((apothem * math.cos(fa), apothem * math.sin(fa), 0.2), out=(math.cos(fa), math.sin(fa), 0))))
    for k in (0, 1, 2, 3):  # crystal clusters on the back and side corners (the front stays clear for the ball)
        a = (0, math.pi / 3, 2 * math.pi / 3, math.pi)[k]
        b.add("DaisCrystals", place(cut_crystal_cluster(0.6, "CrystalCyan" if k % 2 else "RuneViolet", "Moonstone", 4), M((4.4 * math.cos(a), 4.4 * math.sin(a), 0.78), (0, 0, a))))
    # the floating mast: a pedestal and two floating hex columns with rune rings spinning in the gaps
    mx, my = 0.0, 2.3
    mast = M((mx, my, 0))
    b.add("Mast", place(hex_column(1.0, 0.85, 0.8, 2.0), mast))
    b.add("Mast", place(trim_ring(0.92, 1.95, "Gold", minor=0.08, segments=6), mast @ M((0, 0, 0), (0, 0, math.pi / 6))))
    for z0, z1, role in ((2.7, 5.8, "ColumnA"), (6.5, 9.5, "ColumnB")):
        b.add(role, place(hex_column(0.8, 0.68, z0, z1), mast))
        for z in (z0 + 0.12, z1 - 0.12):
            b.add(role, place(trim_ring(0.83 if z < z0 + 1 else 0.71, z, "Gold", minor=0.07, segments=6), mast @ M((0, 0, 0), (0, 0, math.pi / 6))))
        b.add(role, place(gem_setting(0.18, "MagicPink", "Gold", 4), frame((mx, my - 0.72, (z0 + z1) / 2), out=(0, -1, 0))))
        for k in range(3):
            a = k * 2 * math.pi / 3 + 0.5
            b.add(role, place(rune_glyph(0.3, k + (2 if role == "ColumnA" else 5), "RuneGlow", 0.03), frame((mx + 0.7 * math.cos(a), my + 0.7 * math.sin(a), (z0 + z1) / 2 + 0.6), out=(math.cos(a), math.sin(a), 0))))
        hang = cut_crystal(0.5, 0.12, "RuneViolet", sides=6)
        b.add(role, place(hang, Matrix.Translation((mx, my, z0 - 0.05)) @ Matrix.Rotation(math.pi, 4, "X")))
    for z, rr in ((2.35, 1.25), (6.15, 1.1)):
        b.add("RuneRings", place(engraved_rune_ring(rr, "AuroraGreen", "ArcaneDeep", "Moonstone", 8), M((mx, my, z), (0.12, 0.0, 0))))
    # the floating arm: an orb shoulder and three floating segments with small rune rings in the gaps
    orb = V(mx, my, 10.45)
    b.add("Shoulder", sphere(0.95, "Moonstone", orb, 16, 10))
    b.add("Shoulder", ring_at(Matrix.Translation(orb) @ Matrix.Rotation(math.pi / 2, 4, "Y"), 0.98, 0.08, "Gold", segs=18))
    b.add("Shoulder", ring_at(M(orb), 0.98, 0.08, "Gold", segs=18))
    rear, tip = V(0, 4.0, 10.0), V(0, -4.3, 12.6)
    for s0, s1, role in ((0.0, 0.13, "ArmRear"), (0.27, 0.52, "ArmA"), (0.58, 0.8, "ArmB"), (0.86, 1.0, "ArmTip")):
        p0, p1 = rear.lerp(tip, s0), rear.lerp(tip, s1)
        Lseg = (p1 - p0).length
        seg = bmesh.new()
        w = 0.95 - 0.3 * s0
        rounded_block(seg, (w, w, Lseg), M((0, 0, Lseg / 2)), corner=w * 0.4, edge=0.1, taper=0.88)
        b.add(role, place([(seg, "Moonstone", 0.0, False)], along(p0, p1)))
        for z in (0.12, Lseg - 0.12):
            ws = w * (1 - 0.12 * z / Lseg)
            b.add(role, place(block((ws + 0.08, ws + 0.08, 0.14), "Gold", corner=ws * 0.42, edge=0.03), along(p0, p1) @ M((0, 0, z - 0.07))))
        b.add(role, place(gem_setting(0.11, "AuroraCyan", "Gold", 4), along(p0, p1) @ frame((w / 2, 0, Lseg / 2), out=(1, 0, 0))))
        b.add(role, place(gem_setting(0.11, "AuroraCyan", "Gold", 4), along(p0, p1) @ frame((-w / 2, 0, Lseg / 2), out=(-1, 0, 0))))
    for s in (0.2, 0.55, 0.83):
        p = rear.lerp(tip, s)
        b.add("ArmRings", ring_at(Matrix.Translation(p) @ align_z(tip - rear), 0.72 - 0.15 * s, 0.06, "RuneGlow", True, 18))
    b.add("ArmRear", place(cut_crystal(0.9, 0.28, "RuneViolet", sides=6, glow=False), Matrix.Translation(rear + V(0, 0, -0.2)) @ Matrix.Rotation(math.pi, 4, "X")))
    # the tip: a gold ring and a crystal pointing down, the hang point
    b.add("ArmTip", ring_at(Matrix.Translation(tip + V(0, -0.05, -0.1)) @ Matrix.Rotation(math.pi / 2, 4, "Y"), 0.5, 0.08, "Gold", segs=18))
    b.add("ArmTip", place(cut_gem(0.28, "MagicPink"), M(tip + V(0, 0, 0.55))))
    # the ball: a storm cloud with a violet glow inside and lightning, on a glowing rune chain
    r = BALL_R[4]
    pivot, ball = V(0, -4.35, 12.1), V(0, -4.35, 3.4)
    b.add("Ball", chain_between(pivot, ball + V(0, 0, r * 0.95), 0.17, "RuneGlow", glow=True))
    b.add("Ball", storm_cloud(ball, r))
    return standard_atts(ball, pivot, (0, -5.8, 1.3), r, {
        "Lamp1": up_((mx, my - 0.25, 9.5)), "Lamp2": up_((0, 2.3, 11.2)),
        "Gear1": frame((0.5, -4.3, 12.55), out=(1, 0, 0)), "Gear2": frame((0.72, my, 8.0), out=(1, 0, 0)),
        "Steam1": up_((0, -4.3, 13.2)), "Counter": frame((0, 4.05, 9.85), out=(0, 1, 0)),
        "NamePlate": front((0, -4.35, 0.4)), "Aura": up_((0, 0, 0.8)), "Top": up_((0, -4.3, 13.2))})


# ---------- tier 5: Legendary, the Titan Arm ----------

def golem_head(b, center, turn):
    """A stone golem head peeking out of the ground: glowing eyes, heavy brows, a grin, a gold circlet."""
    cage = cage_box((3.5, 3.0, 3.1), 2)
    radii = Vector((1.75, 1.5, 1.55))
    for i, v in enumerate(cage.verts):
        unit = Vector((v.co.x / radii.x, v.co.y / radii.y, v.co.z / radii.z))
        if unit.length > 1e-6:
            unit.normalize()
            v.co = v.co.lerp(Vector((unit.x * radii.x, unit.y * radii.y, unit.z * radii.z)) * 1.05, 0.55)
        v.co += Vector((_hash(i, 7), _hash(i, 8), _hash(i, 9))) * 0.12
        if v.co.y < -0.6 and v.co.z < -0.2:  # a jutting jaw
            v.co.y -= 0.18
    head = subsurf(cage, 2)
    pts = [v.co.copy() for v in head.verts]
    H = M(center, (0, 0, turn))

    def fy(x, z, reach=0.3):
        return min(p.y for p in pts if abs(p.x - x) < reach and abs(p.z - z) < reach)

    b.add("Head", place([(head, "StoneLight", 0.0, False)], H), organic=True)
    for sx in (-1, 1):
        eye = frame((sx * 0.62, fy(sx * 0.62, 0.3) + 0.12, 0.3), out=(sx * 0.1, -1, 0.05))
        b.add("Head", place(ring_at(Matrix(), 0.46, 0.1, "StoneDark", segs=14), H @ eye @ M((0, 0, 0.02))))
        b.add("Eyes", place(cartoon_eye(0.46, "AuroraCyan", look=(-0.3, 0.05)), H @ eye))
        b.add("Head", place(stone_cube((1.05, 0.34, 0.5), "StoneDark"), H @ frame((sx * 0.64, fy(sx * 0.64, 1.0) + 0.05, 1.0), out=(0, -1, 0.25)) @ M((0, 0, 0), (0, 0, sx * 0.28))))
        b.add("Head", place(riveted_plate(0.55, 0.7, 0.05, "Gunmetal", "Gold", 0.3), H @ frame((sx * 1.45, -0.3, 0.0), out=(sx, -0.25, 0))))
    nose_p, _ = hewn((0.45, 0.4, 0.55), Matrix(), "StoneDark", 50, cuts=0, levels=2, rough=0.1)
    b.add("Head", place(nose_p, H @ M((0, fy(0, -0.15) - 0.05, -0.15))), organic=True)
    b.add("Head", place(grin(1.3, 0.28, "EyeDark", "StoneLight", 4), H @ frame((0, fy(0, -0.65) + 0.05, -0.65), out=(0, -1, 0.1))))
    b.add("Head", place(rune_glyph(0.4, 3, "AuroraCyan", 0.03), H @ frame((0, fy(0, 1.3) + 0.02, 1.3), out=(0, -1, 0.35))))
    # the gold circlet with a gem at the front
    ring = [p for p in pts if abs(p.z - 1.0) < 0.15]
    rx, ry = max(abs(p.x) for p in ring), max(abs(p.y) for p in ring)
    b.add("Circlet", place(ring_at(Matrix.Diagonal((rx + 0.05, ry + 0.05, 1, 1)), 1.0, 0.1, "Gold", segs=28), H @ M((0, 0, 1.0))))
    b.add("Circlet", place(gem_setting(0.18, "MagicPink", "Gold", 4), H @ frame((0, -ry - 0.08, 1.05), out=(0, -1, 0.2))))
    top = max(p.z for p in pts)
    return H, top, fy(0, 0.3)


def stone_cube(size, swatch):
    """A chunky bevelled stone block centred on the origin (knuckles, fingers)."""
    bm = bmesh.new()
    rounded_block(bm, size, Matrix(), corner=min(size[:2]) * 0.3, edge=min(size) * 0.22)
    return [(bm, swatch, 0.0, False)]


def golem_block(b, role, p0, p1, size, seed, swatch="Stone", rune=None, plate=True):
    """One hewn stone segment of the arm from p0 to p1 (+Y of its frame leans to the back): a gold band
    at its top end, a riveted plate on the front and a glowing rune on the outer side."""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    m = frame((p0 + p1) / 2, out=p1 - p0, up=(0, 1, 0))
    pieces, local = hewn((size[0], size[1], L), Matrix(), swatch, seed, cuts=1, levels=2, rough=0.13)
    b.add(role, place(pieces, m), organic=True)
    b.add(role + "Trim", place(band(local, L / 2 - 0.4, 0.3, "Gold"), m))
    hx, hy = half_extent(local, 0.0)
    if plate:
        b.add(role + "Trim", place(riveted_plate(size[0] * 0.5, L * 0.36, 0.05, "Gunmetal", "Gold", 0.35), m @ frame((0, -hy - 0.01, -L * 0.08), out=(0, -1, 0), up=(0, 0, 1))))
    if rune is not None:
        b.add(role + "Trim", place(rune_glyph(0.5, rune, "AuroraCyan", 0.04), m @ frame((hx, 0, -L * 0.1), out=(1, 0, 0), up=(0, 0, 1))))
    return m, local


def tier_titan(b):
    # the stone plinth: a gold trim, glowing runes on the front, gems on the corners, cracks and rubble
    b.add("Plinth", block((10.8, 10.8, 0.9), "StoneDark", corner=1.0, edge=0.25))
    b.add("Plinth", place(block((10.2, 10.2, 0.25), "Stone", corner=0.8, edge=0.1), M((0, 0, 0.9))))
    b.add("PlinthTrim", place(block((10.9, 10.9, 0.16), "Gold", corner=1.02, edge=0.06), M((0, 0, 0.62))))
    b.add("PlinthTrim", trim_strip((-3.6, -5.42, 0.32), (3.6, -5.42, 0.32), 0.12, "AuroraGreen", True))
    for k, x in enumerate((-3.0, -1.8, 1.8, 3.0)):
        b.add("PlinthTrim", place(rune_glyph(0.38, k + 1, "AuroraCyan", 0.04), front((x, -5.4, 0.72))))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add("PlinthTrim", place(gem_setting(0.2, "AuroraCyan", "Gold", 4), M((sx * 4.65, sy * 4.65, 1.15))))
    sh = V(1.3, 2.7, 1.5)
    for k in range(5):  # cracks across the top, running out from the shoulder
        a = 1.2 + k * 0.62
        p0 = V(sh.x + 2.0 * math.cos(a), sh.y + 1.7 * math.sin(a), 1.16)
        pts = [p0, p0 + V(math.cos(a) * 0.8, math.sin(a) * 0.8, 0) + V(0.2 * _hash(k), 0.2 * _hash(k, 1), 0),
               p0 + V(math.cos(a + 0.3) * 1.6, math.sin(a + 0.3) * 1.6, 0)]
        b.add("Plinth", rope(pts, 0.05, "Gunmetal", 4))
    for k in range(9):
        a = k * 2 * math.pi / 9 + 0.2
        b.add("Rubble", rock((0.42, 0.36, 0.3), (sh.x + 2.35 * math.cos(a), sh.y + 1.9 * math.sin(a), 1.25), k + 20, "StoneDark" if k % 2 else "Stone", (0, 0, a)))
    # the shoulder: a great boulder breaking out of the ground, with a riveted steel pauldron
    sp, _ = hewn((4.4, 3.8, 3.6), M(sh), "Stone", 11, cuts=2, levels=2, rough=0.1)
    b.add("Shoulder", sp, organic=True)
    paul = frame((sh.x, sh.y - 0.15, 2.85), out=(0, -0.15, 1))
    pauldron = bmesh.new()
    lathe(pauldron, [(0, 0), (1.95, 0), (1.9, 0.3), (1.55, 0.75), (0.9, 1.05), (0, 1.1)], 18, paul)
    b.add("Pauldron", [(pauldron, "Gunmetal", 0.0, False)])
    b.add("Pauldron", place(trim_ring(1.93, 0.12, "Gold", minor=0.1, segments=18), paul))
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        b.add("Pauldron", place(rivet(0.09, "Gold"), paul @ frame((1.6 * math.cos(a), 1.6 * math.sin(a), 0.62), out=(math.cos(a), math.sin(a), 1.2))))
    b.add("Pauldron", place(riveted_plate(1.1, 1.1, 0.06, "Gunmetal", "Gold", 0.35), frame((sh.x - 1.75, sh.y - 0.6, 1.85), out=(-1, -0.5, 0.1))))
    # the arm: hewn stone blocks to the elbow and on to the wrist, gold bands, plates, runes and pistons
    S, E, W = V(1.3, 2.5, 3.3), V(1.5, 1.8, 9.2), V(0.6, -2.4, 12.2)
    u = (E - S).normalized()
    mid_u = S.lerp(E, 0.5)
    golem_block(b, "UpperArmA", S, mid_u + u * 0.15, (2.4, 2.2), 61, "Stone", 2)
    golem_block(b, "UpperArmB", mid_u - u * 0.05, E - u * 0.5, (2.2, 2.05), 62, "StoneLight", 5)
    b.add("Elbow", sphere(1.15, "Gunmetal", E, 18, 12))
    for sx in (-1, 1):
        b.add("Elbow", place(rivet_ring(0.85, 8, 0.07, "Gold"), frame(E + V(sx * 0.85, 0, 0), out=(sx, 0, 0))))
    d = (W - E).normalized()
    mid_f = E.lerp(W, 0.5)
    golem_block(b, "ForearmA", E + d * 0.55, mid_f + d * 0.15, (2.2, 2.05), 63, "StoneLight", 3)
    golem_block(b, "ForearmB", mid_f - d * 0.05, W, (2.05, 1.95), 64, "Stone", 6)
    back_u, back_f = V(0, 1.2, 0), V(0, 0.15, 1.05)
    for p0, p1 in ((S + back_u + V(0, 0, 0.6), E + back_u - u * 1.0), (E + back_f + d * 0.4, E.lerp(W, 0.78) + back_f)):
        b.add("Pistons", piston(p0, p1, 0.17, "Gunmetal", "SteelLight"))
        for p in (p0, p1):
            b.add("Pistons", place(cyl(0.22, 0.34, "Gold", 10), frame(p - V(0.17, 0, 0), out=(1, 0, 0))))
    # the fist, its fingers curled round a gold shackle; the meteor's chain hangs from it
    F = W + d * 1.0
    fm = frame(F, out=d, up=(0, 0, -1))  # local +Y points down toward the chain
    fp, flocal = hewn((2.4, 2.2, 1.9), Matrix(), "Stone", 70, cuts=1, levels=2, rough=0.1)
    b.add("Fist", place(fp, fm), organic=True)
    hx, hy = half_extent(flocal, 0.0)
    for k in range(4):  # knuckles over the front, fingers curled under
        x = -0.78 + k * 0.52
        kp = stone_cube((0.5, 0.62, 0.6), "StoneLight")
        b.add("Fist", place(kp, fm @ M((x, 0.15, 1.0))), organic=True)
        fp2 = stone_cube((0.46, 0.5, 0.95), "StoneLight")
        b.add("Fist", place(fp2, fm @ M((x, hy + 0.1, 0.45), (0.5, 0, 0))), organic=True)
    tp, _ = hewn((0.55, 0.6, 1.1), Matrix(), "StoneLight", 90, cuts=0, levels=2, rough=0.1)
    b.add("Fist", place(tp, fm @ M((hx + 0.1, 0.4, 0.3), (0.3, -0.4, 0))), organic=True)
    b.add("FistTrim", place(riveted_plate(1.4, 0.9, 0.05, "Gunmetal", "Gold", 0.35), fm @ frame((0, -hy - 0.02, -0.1), out=(0, -1, 0), up=(0, 0, 1))))
    pivot = fm @ Vector((0, hy + 0.45, 0.15))
    # the meteor: a cratered rock with hot cracks and gold straps, on a heavy chain
    r = BALL_R[5]
    ball = V(pivot.x, pivot.y, 3.7)
    b.add("Ball", ring_at(Matrix.Translation(pivot + V(0, 0, 0.15)) @ Matrix.Rotation(math.pi / 2, 4, "Y"), 0.36, 0.1, "Gold", segs=12))
    b.add("Ball", chain_between(pivot, ball + V(0, 0, r + 0.35), 0.21, "Gunmetal"))
    b.add("Ball", lumpy_ball(r, "StoneDark", ball, seed=5, subdiv=4, amp=0.1, crack=-0.3, crack_depth=0.88), organic=True)
    b.add("Ball", sphere(r * 0.93, "FlameOrange", ball, 14, 9, glow=True))
    for turn in (0.0, math.pi / 2):
        b.add("Ball", ring_at(Matrix.Translation(ball) @ Matrix.Rotation(turn, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X"), r * 1.07, 0.1, "Gold", segs=20))
    b.add("Ball", lug(ball + V(0, 0, r * 1.05), "Gold", 0.2))
    # the crater under the meteor where it hits, with broken ice
    crater = bmesh.new()
    torus(crater, Matrix.Translation((ball.x, ball.y, 1.15)) @ Matrix.Diagonal((1.2, 0.75, 0.45, 1)), 1.3, 0.32, 16, 6)
    b.add("Plinth", [(crater, "StoneDark", 0.0, False)])
    for k in range(4):
        a = k * 1.6 + 0.4
        b.add("Plinth", place(cut_crystal(0.55, 0.2, "IceBlue", (0.5 * math.cos(a), 0.5 * math.sin(a)), glow=False), M((ball.x + 1.7 * math.cos(a), ball.y + 0.85 * math.sin(a), 1.15))))
    # the golem's head peeking out of the ground in front of its shoulder, watching its meteor,
    # and the fingertips of its other hand breaking through on the far side
    H, head_top, face_y = golem_head(b, (3.15, -1.5, 2.0), 0.12)
    for k in range(5):
        a = k * 1.25 + 4.0
        b.add("Rubble", rock((0.3, 0.26, 0.22), (3.15 + 1.95 * math.cos(a), -1.5 + 1.75 * math.sin(a), 1.2), k + 40, "Stone"))
    for k in range(3):
        fp3, _ = hewn((0.45, 0.48, 0.9), Matrix(), "Stone", 100 + k, cuts=0, levels=2, rough=0.1)
        b.add("Fingers", place(fp3, M((-3.9 + k * 0.55, -1.2 - 0.2 * k, 1.35), (0.5, 0.1 * k, 0))), organic=True)
        b.add("Fingers", place(cyl(0.26, 0.12, "Gold", 10), M((-3.9 + k * 0.55, -1.05 - 0.2 * k, 1.5), (0.5, 0.1 * k, 0))))
    eyes = H @ frame((0, face_y, 0.3), out=(0, -1, 0.05))
    crown = H @ up_((0, -0.1, head_top))
    return standard_atts(ball, pivot, (ball.x, -5.6, 1.4), r, {
        "Lamp1": paul @ frame((1.3, -0.7, 0.75), out=(0.3, -0.3, 1)), "Lamp2": up_(E + V(0, 0, 1.12)),
        "Gear1": frame(E + V(1.12, 0, 0), out=(1, 0, 0)), "Gear2": frame(E + V(-1.12, 0, 0), out=(-1, 0, 0)),
        "Counter": frame(E + V(0, 1.1, 0), out=(0, 1, 0)), "Crown": crown, "Eyes": eyes,
        "Steam1": up_(E + V(0, 0.6, 0.9)),  # (the elbow joint vents: Workshop-and-up steam rises from here)
        "NamePlate": front((0, -5.42, 0.45)), "Aura": up_((0, 0, 1.15)), "Top": up_(F + V(0, 0, 1.3))})


TIER_FNS = [tier_scrappy, tier_workshop, tier_frosttech, tier_enchanted, tier_titan]


# ---------- upgrade sets ----------

def spiked_ball(t, c, r):
    """The 1st upgrade: a spiked steel ball in tier t's look."""
    if t == 1:
        p = sphere(r, "Steel", c, 14, 9)
        p += ring_at(M(c), r + 0.02, 0.05, "Iron", segs=14)
        p += spikes(c, r, 14, 0.45, 0.13, "Iron")
        p += lug(c + V(0, 0, r), "Iron", 0.12)
    elif t == 2:
        p = sphere(r, "Steel", c, 16, 10)
        p += ring_at(M(c), r + 0.02, 0.1, "Brass", segs=16)
        p += spikes(c, r, 18, 0.5, 0.15, "SteelLight")
        p += lug(c + V(0, 0, r), "Brass", 0.14)
    elif t == 3:
        p = sphere(r, "SteelLight", c, 18, 11)
        p += ring_at(M(c), r + 0.01, 0.08, "AuroraCyan", True, 18)
        for d in fib_dirs(14):
            if d.z < 0.75:
                p += place(cut_crystal(0.7, 0.16, "IceBlue", sides=6, glow=False), frame(c + d * (r * 0.85), out=d))
        p += lug(c + V(0, 0, r), "SteelLight", 0.15)
    elif t == 4:
        p = sphere(r * 0.85, "Moonstone", c, 18, 11)
        p += ring_at(M(c), r * 0.85 + 0.02, 0.09, "Gold", segs=18)
        for d in fib_dirs(14):
            if d.z < 0.75:
                p += place(cut_crystal(0.75, 0.16, "RuneViolet", sides=6, glow=False), frame(c + d * (r * 0.72), out=d))
        for k in range(4):
            a = k * math.pi / 2 + 0.4
            puff = bmesh.new()
            blob(puff, c + V(r * 0.9 * math.cos(a), r * 0.9 * math.sin(a), -0.2), (0.45, 0.4, 0.32), 2)
            p.append((puff, "StoneDark", 0.0, False))
        p += zigzag_bolt(c + V(0, -r * 0.8, -0.4), (0.2, -0.4, -1), 0.8, "LampYellow", 0.07)
    else:
        p = lumpy_ball(r, "StoneDark", c, seed=5, subdiv=4, amp=0.1, crack=-0.5, crack_depth=0.88)
        p += sphere(r * 0.93, "FlameOrange", c, 14, 9, glow=True)
        p += spikes(c, r, 16, 0.65, 0.2, "SteelLight", 0.7)
        p += lug(c + V(0, 0, r * 1.05), "Gold", 0.2)
    return p


def molten_ball(t, c, r):
    """The 5th upgrade: a molten ball (a glowing core under a cracked crust) in tier t's look."""
    p = sphere(r * 0.96, "FlameOrange", c, 16, 10, glow=True)
    crust = {1: "RustDark", 2: "RustDark", 3: "Gunmetal", 4: "ArcaneDeep", 5: "StoneDark"}[t]
    p += lumpy_ball(r * 1.02, crust, c, seed=9 + t, subdiv=4 if t >= 3 else 3, amp=0.08, crack=-0.12, crack_depth=0.9, flat=t <= 2)
    trim = {1: "Iron", 2: "Brass", 3: "SteelLight", 4: "Gold", 5: "Gold"}[t]
    p += ring_at(M(c), r * 1.08, 0.08, trim, segs=18)
    if t >= 4:
        p += ring_at(Matrix.Translation(c) @ Matrix.Rotation(math.pi / 2, 4, "X"), r * 1.08, 0.08, trim, segs=18)
    for k in range(3):  # glowing drips under it
        a = k * 2.1
        drip = bmesh.new()
        blob(drip, c + V(r * 0.4 * math.cos(a), r * 0.4 * math.sin(a), -r * 0.98), (0.14, 0.14, 0.24), 1)
        p.append((drip, "FlameYellow", 0.0, True))
    p += lug(c + V(0, 0, r * 1.05), trim, 0.12 + 0.02 * t)
    return p


WEIGHT_LOOK = {  # beam, rope or chain, chain glows, pulley (rim, hub)
    1: ("PineDark", "PineLight", False, ("Pine", "Iron")),
    2: ("Iron", "Iron", False, ("Brass", "Copper")),
    3: ("SteelLight", "AuroraCyan", True, ("SteelLight", "AuroraCyan")),
    4: ("Moonstone", "RuneGlow", True, ("Moonstone", "Gold")),
    5: ("Gunmetal", "Gunmetal", False, ("Brass", "Gold")),
}


def counterweight(t, cw, b):
    """The 3rd upgrade's swinging counterweight: a bracket out the back, a pulley and a hanging weight."""
    beam_sw, line_sw, line_glow, (rim, hub) = WEIGHT_LOOK[t]
    start, end = cw.to_translation(), cw @ Vector((0, 0, 0.95))
    b.add("Counterweight", beam_between(start, end, 0.2 if t > 1 else 0.24, swatch=beam_sw))
    b.add("Counterweight", place(sheave(0.3, 0.16, rim, hub, 0), frame(end, out=(1, 0, 0))))
    top = end - Vector((0, 0, 0.3))
    hang = top - Vector((0, 0, 1.4))
    if t == 1:
        b.add("Counterweight", rope([top, hang], 0.05))
        b.add("Counterweight", place(block((0.75, 0.65, 0.6), "PineDark", corner=0.05, edge=0.03), M(hang - Vector((0, 0, 0.6)))))
        for k in range(3):
            b.add("Counterweight", rock((0.2, 0.18, 0.15), hang + Vector((-0.2 + 0.2 * k, 0.05 * k, -0.02)), 60 + k, "Stone"))
    elif t == 2:
        b.add("Counterweight", chain_between(top, hang, 0.1, line_sw))
        b.add("Counterweight", place(block((0.8, 0.7, 0.8), "Iron", corner=0.12, edge=0.06), M(hang - Vector((0, 0, 0.8)))))
        b.add("Counterweight", place(riveted_plate(0.6, 0.6, 0.04, "SteelDark", "Brass", 0.25), frame(hang + Vector((0, 0.36, -0.4)), out=(0, 1, 0))))
    elif t == 3:
        b.add("Counterweight", chain_between(top, hang, 0.1, line_sw, glow=True))
        b.add("Counterweight", place(block((0.8, 0.7, 0.8), "NavyIce", corner=0.22, edge=0.1), M(hang - Vector((0, 0, 0.8)))))
        b.add("Counterweight", trim_strip(hang + Vector((-0.38, -0.36, -0.4)), hang + Vector((0.38, -0.36, -0.4)), 0.07, "AuroraCyan", True))
        b.add("Counterweight", place(cut_crystal(0.5, 0.14, "CrystalCyan"), M(hang - Vector((0, 0, 0.02)))))
    elif t == 4:
        b.add("Counterweight", chain_between(top, hang, 0.1, line_sw, glow=True))
        b.add("Counterweight", place(cut_crystal(1.0, 0.3, "RuneViolet", sides=6), Matrix.Translation(hang + Vector((0, 0, -0.05))) @ Matrix.Rotation(math.pi, 4, "X")))
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            b.add("Counterweight", rope([hang + Vector((0, 0, 0.05)), hang + Vector((0.38 * math.cos(a), 0.38 * math.sin(a), -0.5)), hang + Vector((0, 0, -1.15))], 0.035, "Gold", 5))
    else:
        b.add("Counterweight", chain_between(top, hang, 0.14, line_sw))
        bp, blocal = hewn((1.0, 0.9, 0.95), M(hang - Vector((0, 0, 0.5))), "StoneDark", 120, cuts=1, levels=2, rough=0.1)
        b.add("Counterweight", bp, organic=True)
        b.add("Counterweight", place(band(blocal, 0.0, 0.22, "Gold"), M(hang - Vector((0, 0, 0.5)))))


def shockwave(t, hit, fx):
    """The 4th upgrade's stand-in: impact chips and sparks, and shockwave rings."""
    fx.add("Hit", place(hit_standin(t), hit))
    swatch, glow = {1: ("StoneLight", False), 2: ("SnowWhite", False), 3: ("AuroraCyan", True), 4: ("RuneGlow", True), 5: ("FlameYellow", True)}[t]
    p = hit.to_translation()
    face = frame(p + Vector((0, -0.2, 0.4)), out=(0, -1, 0))
    for k, (rad, minor) in enumerate(((0.7, 0.07), (1.3, 0.05), (1.9, 0.035))):
        fx.add("Shockwave", ring_at(face @ M((0, 0, -0.25 * k)), rad, minor, swatch, glow, 24))
    fx.add("Shockwave", ring_at(M((p.x, p.y + 0.6, max(0.15, p.z - 0.6))), 1.6, 0.06, swatch, glow, 28))


def lava_trail(t, trail, fx):
    pieces = []
    for k in range(9):
        s = 0.28 * (1 - k / 11)
        bm = bmesh.new()
        blob(bm, (0.12 * math.sin(k * 1.7), 0.1 * math.cos(k * 1.3), 0.3 + k * 0.38), (s, s, s * 1.3), 1)
        pieces.append((bm, "FlameYellow" if k % 3 == 0 else "FlameOrange", 0.0, True))
    fx.add("Trail", place(pieces, trail))


def UPGRADES(u, t, atts, b, fx):
    work = atts["Work"].to_translation()
    r = BALL_R[t] * 1.05
    if u == 1:
        b.add("Ball", spiked_ball(t, work, r))
    elif u == 2:  # a cab light and a beacon on top
        lamp1 = {1: tier_lamp(1), 2: tier_lamp(2), 3: tier_lamp(3), 4: tier_lamp(4, "MagicPink"), 5: tier_lamp(5, "FlameOrange")}[t]
        beacon = {1: lambda: warning_lamp(0.26, "Amber", "Iron", "RustDark"), 2: lambda: warning_lamp(0.34, "WarnRed", "Brass", "Iron"),
                  3: lambda: warning_lamp(0.34, "AuroraCyan", "SteelLight", "GlacierBlue"), 4: lambda: tier_lamp(4, "AuroraCyan"),
                  5: lambda: tier_lamp(5, "AuroraGreen")}[t]()
        b.add("Lamp1", place(lamp1, atts["Lamp1"]))
        b.add("Lamp2", place(beacon, atts["Lamp2"]))
    elif u == 3:  # a swinging counterweight and pulleys (and steam or sparkles where the tier vents)
        counterweight(t, atts["Counter"], b)
        rim, hub = WEIGHT_LOOK[t][3]
        for key in ("Gear1", "Gear2"):
            b.add("Pulley" + key[-1], place(sheave(0.48, 0.2, rim, hub), atts[key] @ M((0, 0, 0.12))))
        for key in ("Steam1", "Steam2"):
            if key in atts:
                fx.add("Steam" + key[-1], place(tier_puff(t), atts[key]))
    elif u == 4:
        shockwave(t, atts["Hit"], fx)
    else:
        b.add("Ball", molten_ball(t, work, BALL_R[t] * 1.12))
        lava_trail(t, atts["Trail"], fx)


def AURA(atts, fx):
    """Titan Arm: small rocks orbiting the meteor, and a dust storm swirling at its base."""
    c = atts["Work"].to_translation()
    orbit = Matrix.Translation(c) @ Matrix.Rotation(0.35, 4, "X") @ Matrix.Rotation(0.2, 4, "Y")
    fx.add("AuraOrbit", ring_at(orbit, 2.4, 0.03, "FlameOrange", True, 32))
    for k in range(9):
        a = k * 2 * math.pi / 9
        p = orbit @ Vector((2.4 * math.cos(a), 2.4 * math.sin(a), 0.15 * math.sin(3 * a)))
        fx.add("AuraRocks", rock((0.24, 0.2, 0.18), p, 200 + k, "StoneDark" if k % 2 else "Stone", (a, k, 0)))
        if k % 3 == 0:
            ember = bmesh.new()
            blob(ember, p + Vector((0, 0, 0.3)), (0.08, 0.08, 0.08), 1)
            fx.add("AuraOrbit", [(ember, "FlameYellow", 0.0, True)])
    base = atts["Aura"].to_translation()
    for k in range(14):
        a = k * 2 * math.pi / 14
        rad = 4.2 + 0.5 * math.sin(k * 1.9)
        s = 0.35 + 0.15 * (k % 3)
        puff = bmesh.new()
        blob(puff, base + Vector((rad * math.cos(a), rad * math.sin(a), 0.3 + 0.25 * (k % 4))), (s * 1.3, s, s * 0.8), 1)
        fx.add("AuraDust", [(puff, "StoneLight", 0.0, False)])
    for z, rad in ((0.35, 4.6), (0.95, 4.2), (1.6, 3.7)):
        fx.add("AuraDust", ring_at(Matrix.Translation(base + Vector((0, 0, z))) @ Matrix.Rotation(0.06, 4, "X"), rad, 0.04, "Cream", False, 32))
