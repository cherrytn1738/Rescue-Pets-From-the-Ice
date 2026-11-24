# SunMirrorTower.py - the Sun Mirror Tower's five tiers and upgrade sets, for
# tools/blender/buildings/framework.py (style reference: IceDrill.py).
#
# The working part in every tier is a mirror at the front, aimed at the ice (-Y, tilted a little down),
# with a converging glow beam stand-in ("Beam", a Neon mesh) from the mirror to the pad edge, where `Hit`
# sits. The game can hide that stand-in and draw a real Beam from `Work` along its +Z.
#   1 Scrappy     a polished round shield on a wooden pole, tilted by a rope crank
#   2 Workshop    an iron lattice tower with a brass telescope on a turntable and a brass-framed mirror
#   3 Frost-tech  a white tech column topped by a crystal prism that splits light into three rays
#   4 Enchanted   a column of light with rune rings, floating gold mirrors orbiting it
#   5 Legendary   the Celestial Observatory: an observatory drum and night-sky dome with brass rings,
#                 gears and a telescope, a calm sun disk with glowing eyes and a gold crown of rays,
#                 mini planets on brass orbit rings, a great gold mirror in a gimbal
import re

TIER_Q = {"Scrappy": {"round": 1.0}, "Workshop": {"round": 1.0}, "Frost-tech": {"round": 1.1},
          "Enchanted": {"round": 1.25, "minor": 1.25, "corner": 3}, "Legendary": {"round": 1.1, "minor": 1.0}}

BEAM_SLOPE = 0.35          # the beam leaves the mirror toward -Y, this much down per stud forward
PAD_EDGE = -7.6            # the beam stand-in ends here (the pad is 16: +-8)
MIRROR_R = {1: 1.35, 2: 1.45, 3: 1.6, 4: 1.45, 5: 2.1}
METAL = {1: ("Iron", "Steel"), 2: ("Brass", "Copper"), 3: ("SteelLight", "GlacierBlue"), 4: ("Gold", "Moonstone"), 5: ("Gold", "Brass")}
BEAM_SWATCH = {1: "LampYellow", 2: "LampYellow", 3: "Diamond", 4: "RuneGlow", 5: "FlameYellow"}


def aim(slope=BEAM_SLOPE):
    return Vector((0, -1, -slope)).normalized()


# ---------- pieces of this building ----------

def mirror_disc(radius, face="SteelLight", rim="Iron", back="Steel", sides=24, glints=1, rim_minor=None, depth=0.26):
    """A mirror facing +Z: a back shell, a rim, a slightly concave polished face and glow glints."""
    pieces = []
    shell = bmesh.new()
    lathe(shell, [(0, -depth), (radius * 0.72, -depth), (radius * 0.97, -depth * 0.45), (radius, 0.02), (0, 0.02)], sides)
    pieces.append((shell, back, 0.0, False))
    dish = bmesh.new()
    lathe(dish, [(0, 0.03), (radius * 0.5, 0.055), (radius * 0.93, 0.12), (radius * 0.93, 0.02), (0, 0.02)], sides)
    pieces.append((dish, face, 0.0, False))
    rim_bm = bmesh.new()
    torus(rim_bm, M((0, 0, 0.08)), radius * 0.97, rim_minor or max(0.06, radius * 0.07), sides, 6)
    pieces.append((rim_bm, rim, 0.0, False))
    for k in range(glints):  # diagonal highlight streaks: it reads as polished
        g = bmesh.new()
        length = radius * (0.95 - 0.3 * k)
        rounded_block(g, (radius * 0.07 * (1.2 - 0.3 * k), length, 0.02), M((radius * (-0.28 + 0.24 * k), radius * (0.16 + 0.12 * k), 0.13), (0, 0, 0.75)),
                      corner=0.02, edge=0.005, corner_seg=1, edge_seg=1)
        pieces.append((g, "EyeWhite", 0.0, True))
    return pieces


def light_beam(p0, p1, r0, r1, swatch="LampYellow", segments=12):
    """A tapering glow cone from p0 to p1 (beam and ray stand-ins)."""
    p0, p1 = Vector(p0), Vector(p1)
    bm = bmesh.new()
    cylinder(bm, p0, r0, (p1 - p0).length, segments, top=r1, direction=p1 - p0)
    return [(bm, swatch, 0.0, True)]


def beam_to_edge(b, centre, d, radius, swatch, role="Beam"):
    """The converging beam stand-in from the mirror to the pad edge; returns its end (the Hit point)."""
    t = (centre.y - PAD_EDGE) / -d.y
    end = centre + d * t
    b.add(role, light_beam(centre + d * 0.35, end, radius * 0.32, 0.08, swatch))
    return end


def four_star(size, swatch="LampYellow"):
    """A flat four-pointed twinkle star facing +Z (faceted)."""
    bm = bmesh.new()
    pts = []
    for k in range(8):
        a = k * math.pi / 4
        r = size if k % 2 == 0 else size * 0.3
        pts.append(Vector((r * math.cos(a), r * math.sin(a), 0)))
    loft(bm, [[p + Vector((0, 0, z)) for p in pts] for z in (-0.03, 0.03)])
    return [(faceted(bm), swatch, 0.0, True)]


def prism(height, radius, swatch="CrystalCyan", glow=True):
    """A triangular crystal prism standing on z = 0, cut facets, a pointed top."""
    bm = bmesh.new()
    lathe(bm, [(0, -0.05), (radius * 0.8, -0.05), (radius, height * 0.12), (radius, height * 0.75), (radius * 0.4, height * 0.94), (0, height)], 3)
    return [(faceted(bm), swatch, 0.0, glow)]


def rope(p0, p1, sag=0.3, radius=0.035, swatch="PineLight"):
    """A thin sagging rope (cheaper than the kit's cable: no sleeves)."""
    p0, p1 = Vector(p0), Vector(p1)
    pts = [p0.lerp(p1, t / 8) - Vector((0, 0, sag * 4 * (t / 8) * (1 - t / 8))) for t in range(9)]
    bm = bmesh.new()
    sweep(bm, pts, radius, 5)
    return [(bm, swatch, 0.0, False)]


def rope_wrap(p0, p1, radius, turns, swatch="PineLight"):
    """Rope wound round a beam between two points."""
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0)
    m = Matrix.Translation(p0) @ align_z(d)
    pts = [m @ Vector((radius * math.cos(2 * math.pi * turns * s / 16), radius * math.sin(2 * math.pi * turns * s / 16), d.length * s / 16)) for s in range(17)]
    bm = bmesh.new()
    sweep(bm, pts, 0.045, 5)
    return [(bm, swatch, 0.0, False)]


def tracker(t):
    """The 3rd upgrade: a small mirror that turns to track the sun, in tier t's look. Built on z = 0,
    turning about +Z; the mirror leans back to face the sky."""
    pieces = []
    tilt = frame((0, 0, 0), out=(0, -0.55, 0.85))
    if t == 1:
        pieces += grained_beam((0, 0, 0), (0, 0, 1.4), 0.24, "Pine", "PineDark", faces=(0, 2))
        pieces += place(cyl(0.3, 0.12, "Iron", 12), M((0, 0, 1.35)))
        pieces += place(mirror_disc(0.55, "SteelLight", "Iron", "Steel", 12, 1), Matrix.Translation((0, 0, 1.85)) @ tilt)
        pieces += rope_wrap((0, 0, 0.9), (0, 0, 1.2), 0.15, 2)
    elif t == 2:
        pieces += place(cyl(0.38, 0.25, "Brass", 14), M())
        pieces += place(cyl(0.11, 1.5, "Iron", 10), M((0, 0, 0.25)))
        pieces += place(gear(0.42, 8, 0.12, 0.09, "Brass", "Copper"), M((0, 0, 0.45)))
        for sx in (-1, 1):
            pieces += beam_between((sx * 0.62, 0, 1.6), (sx * 0.62, 0, 2.15), 0.1, swatch="Brass")
        pieces += beam_between((-0.62, 0, 1.6), (0.62, 0, 1.6), 0.12, swatch="Brass")
        pieces += place(mirror_disc(0.55, "SteelLight", "Brass", "Copper", 12, 1), Matrix.Translation((0, 0, 2.15)) @ tilt)
    elif t == 3:
        pieces += place(block((0.8, 0.8, 0.3), "SnowWhite", corner=0.2, edge=0.08), M())
        pieces += place(cyl(0.16, 1.5, "SteelLight", 12), M((0, 0, 0.3)))
        pieces += trim_ring(0.2, 1.0, "AuroraCyan", True, minor=0.05, segments=12)
        pieces += place(mirror_disc(0.62, "Diamond", "SteelLight", "GlacierBlue", 6, 1), Matrix.Translation((0, 0, 2.0)) @ tilt)
        pieces += place(trim_ring(0.62, 0, "AuroraCyan", True, minor=0.04, segments=6), Matrix.Translation((0, 0, 2.0)) @ tilt @ M((0, 0, 0.15)))
    elif t == 4:
        pieces += place(engraved_rune_ring(0.55, "RuneGlow", "ArcaneDeep", "RuneViolet", 6), M((0, 0, 0.05)))
        pieces += place(mirror_disc(0.6, "Diamond", "Gold", "Moonstone", 12, 1), Matrix.Translation((0, 0, 1.6)) @ tilt)
        pieces += place(cut_gem(0.14, "MagicPink"), Matrix.Translation((0, 0, 1.6)) @ tilt @ M((0, 0.72, 0.1)))
        hang = cut_crystal(0.5, 0.1, "RuneViolet", sides=6)
        pieces += place(hang, M((0, 0, 0.95), (math.pi, 0, 0)))
    else:
        pieces += place(cyl(0.45, 0.2, "Gold", 16), M())
        pieces += place(cyl(0.12, 1.6, "Brass", 12), M((0, 0, 0.2)))
        ring = bmesh.new()
        torus(ring, M((0, 0, 1.0), (math.pi / 2, 0, 0)), 0.5, 0.04, 12, 4)
        pieces.append((ring, "Brass", 0.0, False))
        pieces += place(mirror_disc(0.7, "Diamond", "Gold", "Gold", 12, 1), Matrix.Translation((0, 0, 2.2)) @ tilt)
        for k in range(6):  # a little ray crown on the mirror
            a = k * math.pi / 3
            ray = bmesh.new()
            lathe(ray, [(0, 0), (0.08, 0), (0, 0.3)], 4)
            ray.transform(Matrix.Translation((0, 0, 2.2)) @ tilt @ frame((0.78 * math.cos(a), 0.78 * math.sin(a), 0.0), out=(math.cos(a), math.sin(a), 0)))
            pieces.append((ray, "Gold", 0.0, False))
    return pieces


# ---------- tier 1: Scrappy - a polished shield on a pole ----------

def tier_scrappy(b):
    for L, W, swatch, grain, loc, turn, seed in ((4.4, 1.05, "PineDark", "RustDark", (-0.2, -1.15, 0), 0.08, 0.0),
                                                 (3.8, 1.0, "Pine", "PineDark", (0.3, 0.05, 0), -0.1, 1.3),
                                                 (3.3, 0.95, "PineLight", "Pine", (-0.15, 1.2, 0), 0.16, 2.1)):
        b.add("Planks", place(plank(L, W, 0.25, swatch, grain, True, seed), M(loc, (0, 0, turn))))
    pole = V(0, 0.5, 0.25)
    top = V(0, 0.5, 7.7)
    b.add("Pole", grained_beam(pole, top, 0.5, "PineDark", "RustDark"))
    b.add("Pole", place(cyl(0.34, 0.14, "Iron", 12), M(top)))
    feet = (V(-1.8, -0.7, 0.25), V(1.8, -0.5, 0.25), V(0.25, 2.2, 0.25))
    for k, foot in enumerate(feet):
        b.add("Pole", grained_beam(foot, V(0, 0.5, 2.7), 0.32, ("Pine", "PineLight", "Pine")[k], "PineDark", faces=(0, 2)))
        stone = bmesh.new()
        blob(stone, (foot.x, foot.y, 0.18), (0.4, 0.34, 0.2), 1, floor=0.0)
        b.add("Planks", [(stone, "StoneDark", 0.0, False)])
        b.add("Pole", place(rivet(0.06, "Iron"), frame(foot.lerp(V(0, 0.5, 2.7), 0.85) + V(0, -0.17, 0), out=(0, -1, 0))))
    b.add("Pole", rope_wrap((0, 0.5, 2.35), (0, 0.5, 2.95), 0.3, 4))
    # guy ropes to two stakes at the back
    for sx in (-1, 1):
        stake = V(sx * 2.6, 2.4, 0.0)
        b.add("Pole", beam_between(stake, stake + V(0, 0.1, 0.7), 0.16, swatch="PineDark"))
        b.add("Ropes", rope((0, 0.6, 7.2), stake + V(0, 0.1, 0.6), 0.35))
    # the yoke: a crossbar on the pole, iron straps up to the pivots
    P = V(0, -0.2, 6.3)
    D = aim()
    b.add("Yoke", beam_between((-1.75, 0.12, 5.35), (1.75, 0.12, 5.35), 0.28, swatch="Pine"))
    for sx in (-1, 1):
        b.add("Yoke", beam_between((sx * 1.62, 0.12, 5.2), (sx * 1.62, P.y, P.z + 0.15), 0.16, swatch="Iron"))
        b.add("Yoke", place(cyl(0.12, 0.12, "Iron", 6), frame((sx * 1.7, P.y, P.z), out=(sx, 0, 0))))
        b.add("Yoke", place(rivet(0.05, "SteelDark"), frame((sx * 1.62, 0.12 - 0.15, 5.35), out=(0, -1, 0))))
    b.add("Yoke", place(block((0.7, 0.6, 0.06), "PatchGreen", corner=0.08, edge=0.02), frame((0, -0.02, 5.05), out=(0, -1, 0))))
    for sx in (-1, 1):
        b.add("Yoke", place(rivet(0.05, "RustDark"), frame((sx * 0.24, -0.09, 5.35), out=(0, -1, 0))))
    # the shield: a dished steel face, an iron rim with rivets, boards and a strap on the back
    W = frame(P, out=D)
    R = MIRROR_R[1]
    b.add("Shield", place(mirror_disc(R, "SteelLight", "Iron", "Steel", 24, 1), W))
    b.add("Shield", place(rivet_ring(R * 0.84, 6, 0.05, "Iron"), W @ M((0, 0, 0.1))))
    for k, x in enumerate((-0.35, 0.35)):
        b.add("Shield", place(plank(2.0, 0.6, 0.12, "Pine", "PineDark", False, k), W @ M((x, 0, -0.42), (0, 0, math.pi / 2))))
    b.add("Shield", place(handle(0.7, 0.22, 0.05, "RustDark", "Iron"), W @ M((0, 0, -0.42), (math.pi, 0, 0))))
    b.add("Shield", place(block((0.45, 0.4, 0.04), "Copper", corner=0.06, edge=0.015), W @ M((-0.65, -0.55, 0.11), (0, 0, 0.3))))
    # the crank: a little wheel on the right pivot, a rope down to a cleat on the pole
    wheel_at = frame((1.95, P.y, P.z), out=(1, 0, 0))
    wheel = bmesh.new()
    torus(wheel, wheel_at, 0.42, 0.06, 12, 4)
    b.add("Crank", [(wheel, "Pine", 0.0, False)])
    for k in range(3):
        a = k * math.pi / 3
        b.add("Crank", place(beam_between((-0.4 * math.cos(a), -0.4 * math.sin(a), 0), (0.4 * math.cos(a), 0.4 * math.sin(a), 0), 0.07, swatch="PineDark"), wheel_at))
    b.add("Crank", place(cyl(0.1, 0.16, "Iron", 8), wheel_at @ M((0, 0, -0.08))))
    b.add("Crank", place(cyl(0.06, 0.35, "PineLight", 8), frame((2.05, P.y + 0.3, P.z + 0.15), out=(1, 0, 0))))
    b.add("Ropes", rope((1.95, P.y + 0.05, P.z - 0.4), (0.3, 0.45, 3.6), 0.15))
    b.add("Crank", place(block((0.15, 0.2, 0.5), "Iron", corner=0.04, edge=0.03), M((0.3, 0.45, 3.35))))
    # junk: a crate of polish tins, a bucket of rags, two stumps for the trackers
    b.add("Junk", place(block((1.0, 0.9, 0.8), "PineLight", corner=0.08, edge=0.05), M((2.0, 1.2, 0.0), (0, 0, 0.2))))
    for z in (0.4,):
        b.add("Junk", place(block((1.04, 0.94, 0.08), "PineDark", corner=0.08, edge=0.02), M((2.0, 1.2, z), (0, 0, 0.2))))
    for k in range(2):
        b.add("Junk", place(cyl(0.14, 0.2, "Copper" if k % 2 else "PatchGreen", 10), M((1.8 + 0.28 * k, 1.1 + 0.05 * k, 0.8))))
    bucket = bmesh.new()
    lathe(bucket, [(0, 0), (0.3, 0), (0.42, 0.6), (0.38, 0.6), (0.27, 0.06), (0, 0.06)], 14, M((-2.2, 0.8, 0)))
    rag = bmesh.new()
    blob(rag, (-2.2, 0.8, 0.62), (0.32, 0.3, 0.14), 1)
    b.add("Junk", [(bucket, "Steel", 0.0, False), (rag, "Cream", 0.0, False)])
    for sx in (-1, 1):
        stump = bmesh.new()
        lathe(stump, [(0, 0), (0.46, 0), (0.42, 0.2), (0.4, 0.75), (0, 0.75)], 12, M((sx * 2.5, -1.3, 0)))
        ring = bmesh.new()
        lathe(ring, [(0, 0.75), (0.38, 0.75), (0, 0.77)], 12, M((sx * 2.5, -1.3, 0)))
        b.add("Junk", [(stump, "PineDark", 0.0, False), (ring, "PineLight", 0.0, False)])
    hit = beam_to_edge(b, P, D, R, BEAM_SWATCH[1])
    return {"Work": frame(P + D * 0.15, out=D), "Lamp1": up_(top + V(0, 0, 0.14)), "Lamp2": up_((2.0, 1.2, 0.9)),
            "Gear1": up_((-2.5, -1.3, 0.77)), "Gear2": up_((2.5, -1.3, 0.77)), "Steam1": up_((-2.2, 0.8, 0.8)),
            "Hit": frame(hit, out=(0, -1, 0.6)), "Trail": frame(P + D * 0.15, out=D), "NamePlate": front((0, -1.7, 0.4)),
            "Aura": up_((0, 0, 0.3)), "Top": up_(top + V(0, 0, 0.14))}


# ---------- tier 2: Workshop - a brass telescope tower ----------

def tier_workshop(b):
    for k in range(5):
        y = -3.2 + 1.6 * k
        b.add("Deck", place(plank(8.0, 1.56, 0.5, "Pine" if k % 2 else "PineLight", "PineDark", k in (0, 4), k * 1.1), M((0, y, 0))))
    legs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            foot, head = V(sx * 3.0, sy * 3.0, 0.5), V(sx * 1.6, sy * 1.6, 7.4)
            legs.append((foot, head))
            b.add("Tower", beam_between(foot, head, 0.36, swatch="Iron"))
            b.add("Tower", place(cyl(0.42, 0.22, "Brass", 8), M(foot)))
            for t in (0.5,):
                p = foot.lerp(head, t)
                b.add("Tower", place(trim_ring(0.27, 0, "Brass", minor=0.06, segments=12), Matrix.Translation(p) @ align_z(head - foot)))
    # X braces on all four faces, two storeys
    faces = ((legs[0], legs[1]), (legs[2], legs[3]), (legs[0], legs[2]), (legs[1], legs[3]))
    for (fa, ha), (fb, hb) in faces:
        for t0, t1 in ((0.06, 0.94),):
            a0, a1, b0, b1 = fa.lerp(ha, t0), fa.lerp(ha, t1), fb.lerp(hb, t0), fb.lerp(hb, t1)
            b.add("Braces", beam_between(a0, b1, 0.14, swatch="SteelDark"))
            b.add("Braces", beam_between(b0, a1, 0.14, swatch="SteelDark"))
            mid = (a0 + b1) / 2
            n = (mid - V(0, 0, mid.z)).normalized()
            b.add("Braces", place(rivet(0.12, "Brass"), frame(mid + n * 0.08, out=n)))
    b.add("Tower", place(ladder(6.9, 0.8, "PineDark", "Pine"), M((0, 2.55, 0.5), (-0.2, 0, 0))))
    # the platform: a round wooden deck with a brass rim and a railing
    b.add("Platform", place(cyl(2.7, 0.32, "PineDark", 24), M((0, 0, 7.4))))
    b.add("Platform", place(trim_ring(2.72, 7.56, "Brass", minor=0.12, segments=24), M()))
    rail_posts = []
    for k in range(12):
        a = k * math.pi / 6 + math.pi / 12
        if abs(math.sin(a) + 1) < 0.2:  # leave the front open for the mirror
            continue
        p = V(2.5 * math.cos(a), 2.5 * math.sin(a), 7.72)
        rail_posts.append(p)
        b.add("Platform", place(cyl(0.06, 0.8, "Brass", 8), M(p)))
    rail = []
    for k in range(13):
        a = -math.pi / 2 + 0.55 + (2 * math.pi - 1.1) * k / 12
        rail.append(V(2.5 * math.cos(a), 2.5 * math.sin(a), 8.52))
    r = bmesh.new()
    sweep(r, rail, 0.07, 8)
    b.add("Platform", [(r, "Brass", 0.0, False)])
    # the telescope: a turntable, a fork, a banded brass tube aimed at the sky, a lens cap
    b.add("Telescope", place(cyl(1.2, 0.35, "Brass", 20), M((0, 0.3, 7.72))))
    b.add("Telescope", place(rivet_ring(1.0, 8, 0.06, "Copper"), M((0, 0.3, 8.07))))
    c = V(0, 0.3, 9.5)
    for sx in (-1, 1):
        b.add("Telescope", beam_between((sx * 0.95, 0.3, 8.0), (sx * 0.95, 0.3, 9.7), 0.24, swatch="Brass"))
        b.add("Telescope", place(cyl(0.16, 0.1, "Iron", 8), frame((sx * 1.07, 0.3, 9.5), out=(sx, 0, 0))))
    tdir = Vector((0, 0.75, 1)).normalized()
    tube = bmesh.new()
    lathe(tube, [(0, -1.1), (0.32, -1.1), (0.42, -0.9), (0.55, -0.6), (0.55, 2.6), (0.68, 2.7), (0.68, 3.3), (0.6, 3.3), (0, 3.2)], 20, Matrix.Translation(c) @ align_z(tdir))
    b.add("Telescope", [(tube, "Brass", 0.0, False)])
    for s in (0.2, 2.2):
        b.add("Telescope", place(trim_ring(0.57, 0, "Copper", minor=0.07, segments=20), Matrix.Translation(c + tdir * s) @ align_z(tdir)))
    lens = bmesh.new()
    lathe(lens, [(0, 3.22), (0.58, 3.22), (0.5, 3.3), (0, 3.34)], 20, Matrix.Translation(c) @ align_z(tdir))
    b.add("Telescope", [(lens, "Diamond", 0.0, True)])
    b.add("Telescope", place(cyl(0.16, 0.5, "Iron", 10), Matrix.Translation(c + tdir * -1.1) @ align_z(-tdir)))
    b.add("Telescope", place(cyl(0.22, 0.12, "Brass", 10), Matrix.Translation(c + tdir * -1.55) @ align_z(-tdir)))
    finder = c + Vector((0.62, 0, 0)) + tdir * 0.8
    b.add("Telescope", place(cyl(0.14, 1.1, "Copper", 10), Matrix.Translation(finder) @ align_z(tdir)))
    b.add("TelescopeGear", place(gear(0.75, 10, 0.18, 0.12, "Brass", "Copper"), frame((1.2, 0.3, 9.5), out=(1, 0, 0))))
    # the mirror on a brass fork at the front of the platform
    P = V(0, -2.75, 9.15)
    D = aim()
    R = MIRROR_R[2]
    W = frame(P, out=D)
    b.add("Mirror", place(mirror_disc(R, "SteelLight", "Brass", "Copper", 24, 1), W))
    b.add("Mirror", place(rivet_ring(R * 0.97, 8, 0.06, "Copper"), W @ M((0, 0, -0.1))))
    for sx in (-1, 1):
        b.add("MirrorFork", beam_between((sx * 1.62, -2.3, 7.72), (sx * 1.62, P.y, P.z + 0.2), 0.2, swatch="Brass"))
        b.add("MirrorFork", place(cyl(0.16, 0.25, "Copper", 12), frame((sx * 1.45, P.y, P.z), out=(sx, 0, 0))))
        b.add("MirrorFork", place(bolt(0.08, "Iron", "Brass"), frame((sx * 1.72, P.y, P.z), out=(sx, 0, 0))))
    b.add("MirrorFork", beam_between((-1.7, -2.3, 7.85), (1.7, -2.3, 7.85), 0.22, swatch="Brass"))
    # the steam winch at the foot of the tower that turns the telescope, with its drive belt
    b.add("Engine", place(block((1.6, 1.2, 0.95), "Copper", corner=0.18, edge=0.1), M((1.9, -1.7, 0.5))))
    b.add("Engine", place(block((1.68, 1.28, 0.25), "Brass", corner=0.2, edge=0.08), M((1.9, -1.7, 1.45))))
    b.add("Engine", place(dial(0.25, "Cream", "Brass", "WarnRed", 0.8), front((1.6, -2.32, 1.0))))
    b.add("Engine", place(cyl(0.16, 1.75, "Brass", 12), M((2.4, -1.5, 1.68))))
    b.add("Engine", place(trim_ring(0.18, 2.6, "Copper", minor=0.05, segments=12), M((2.4, -1.5, 0))))
    cap = bmesh.new()
    lathe(cap, [(0, 3.4), (0.26, 3.4), (0.3, 3.5), (0.2, 3.65), (0, 3.68)], 12, M((2.4, -1.5, 0)))
    b.add("Engine", [(cap, "Copper", 0.0, False)])
    b.add("Engine", trim_strip((1.5, -1.25, 1.75), (0.45, 0.2, 7.75), 0.1, "Rubber"))
    # a beacon mast at the back of the platform, a toolbox and a crate on the deck
    b.add("Platform", place(cyl(0.1, 2.6, "Iron", 10), M((-1.9, 1.3, 7.72))))
    b.add("Platform", place(cyl(0.22, 0.12, "Brass", 12), M((-1.9, 1.3, 10.3))))
    b.add("Deck", place(block((1.0, 0.6, 0.45), "WarnRed", corner=0.08, edge=0.05), M((-2.3, -3.2, 0.5), (0, 0, 0.15))))
    b.add("Deck", place(block((0.9, 0.9, 0.8), "PineLight", corner=0.08, edge=0.05), M((-3.2, 0.6, 0.5))))
    hit = beam_to_edge(b, P, D, R, BEAM_SWATCH[2])
    post = max(rail_posts, key=lambda p: p.x + p.y)
    return {"Work": frame(P + D * 0.15, out=D), "Lamp1": up_((-1.9, 1.3, 10.42)), "Lamp2": up_(post + V(0, 0, 0.82)),
            "Gear1": up_((-3.5, -1.6, 0.5)), "Gear2": up_((3.5, 1.0, 0.5)), "Steam1": up_((2.4, -1.5, 3.7)),
            "Hit": frame(hit, out=(0, -1, 0.6)), "Trail": frame(P + D * 0.15, out=D), "NamePlate": front((0, -4.0, 0.25)),
            "Aura": up_((0, 0, 0.5)), "Top": up_(c + tdir * 3.34)}


# ---------- tier 3: Frost-tech - a crystal prism tower splitting light ----------

def tier_frosttech(b):
    b.add("Deck", block((11.0, 11.0, 0.8), "SnowWhite", corner=1.6, edge=0.3))
    b.add("Deck", place(block((10.0, 10.0, 0.3), "IceBlue", corner=1.2, edge=0.12), M((0, 0, 0.8))))
    for x, y in ((-2.6, -3.3), (2.6, -3.3), (-3.3, 2.8), (3.3, 2.8)):
        b.add("Deck", place(inset_panel(1.8, 1.2, 0.05, "FrostLight", "GlacierBlue", True), M((x, y, 1.1))))
    for sx in (-1, 1):
        b.add("Deck", place(vent(1.6, 0.4, 5, "GlacierBlue", "SteelLight"), front((sx * 3.0, -5.49, 0.42))))
        for sy in (-1, 1):
            b.add("Deck", place(bolt(0.1, "SteelLight", "GlacierBlue"), M((sx * 4.6, sy * 4.6, 1.1))))
    for p0, p1 in (((-3.6, -5.53, 0.42), (3.6, -5.53, 0.42)), ((-3.6, 5.53, 0.42), (3.6, 5.53, 0.42)),
                   ((-5.53, -3.6, 0.42), (-5.53, 3.6, 0.42)), ((5.53, -3.6, 0.42), (5.53, 3.6, 0.42))):
        b.add("Deck", trim_strip(p0, p1, 0.16, "AuroraCyan", True))
    b.add("Deck", place(cyl(0.55, 0.12, "GlacierBlue", 6), front((0, -5.5, 0.42))))
    # the column: tapering white tower with panel bands, glowing coil rings, screens and vents
    col = bmesh.new()
    profile = [(0, 1.1), (2.1, 1.1), (2.1, 1.7), (1.75, 2.0), (1.5, 6.0), (1.22, 9.8), (1.55, 10.0), (1.55, 10.5), (0, 10.5)]
    lathe(col, profile, 24)
    b.add("Column", [(col, "SnowWhite", 0.0, False)])
    radius_at = lambda z: 1.75 + (1.5 - 1.75) * (z - 2.0) / 4.0 if z < 6 else 1.5 + (1.22 - 1.5) * (z - 6.0) / 3.8
    for z in (3.0, 5.2, 7.4, 9.2):
        b.add("Column", place(trim_ring(radius_at(z) + 0.02, 0, "GlacierBlue", minor=0.06, segments=24), M((0, 0, z))))
    for z in (4.1, 6.3, 8.3):
        b.add("ColumnGlow", place(trim_ring(radius_at(z) + 0.03, 0, "AuroraCyan", True, minor=0.08, segments=24), M((0, 0, z))))
    b.add("Column", place(screen(0.9, 0.55, "AuroraCyan", "NavyIce", 3), front((0, -radius_at(3.6) - 0.02, 3.6), 0.07)))
    for a in (math.radians(30), math.radians(150)):
        n = V(math.cos(a), math.sin(a), 0)
        b.add("Column", place(vent(0.8, 0.5, 4, "GlacierBlue", "SteelLight"), frame(n * (radius_at(4.6) + 0.01) + V(0, 0, 4.6), out=n)))
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 2
        fin = bmesh.new()
        rounded_block(fin, (0.18, 1.4, 2.4), M((2.0 * math.cos(a), 2.0 * math.sin(a), 2.3), (0, 0, a + math.pi / 2)), corner=0.06, edge=0.05, taper=0.55)
        line = bmesh.new()
        rounded_block(line, (0.2, 0.08, 1.8), M((2.0 * math.cos(a), 2.0 * math.sin(a), 2.2), (0, 0, a + math.pi / 2)), corner=0.02, edge=0.02, corner_seg=1, edge_seg=1)
        b.add("Column", [(fin, "GlacierBlue", 0.0, False), (line, "AuroraCyan", 0.0, True)])
    # the prism holder: a collar, three claw prongs, a halo ring; the prism and its three split rays
    b.add("Prism", place(cyl(1.25, 0.3, "SteelLight", 18), M((0, 0, 10.5))))
    b.add("Prism", place(trim_ring(1.27, 10.65, "AuroraCyan", True, minor=0.06, segments=18), M()))
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 2
        prong = bmesh.new()
        sweep(prong, [V(1.0 * math.cos(a), 1.0 * math.sin(a), 10.7), V(1.25 * math.cos(a), 1.25 * math.sin(a), 11.4), V(0.95 * math.cos(a), 0.95 * math.sin(a), 12.2)], 0.11, 8, radius_end=0.05)
        b.add("Prism", [(prong, "SteelLight", 0.0, False)])
    b.add("Prism", prism(3.4, 1.0, "CrystalCyan"), M((0, 0, 10.8), (0, 0, math.pi / 2)))
    halo = bmesh.new()
    torus(halo, M((0, 0, 12.4), (0.25, 0, 0)), 1.55, 0.05, 24, 4)
    b.add("Prism", [(halo, "AuroraCyan", 0.0, True)])
    # the main mirror on an arm from the column
    P = V(0, -3.6, 7.4)
    D = aim()
    R = MIRROR_R[3]
    W = frame(P, out=D)
    b.add("Mirror", place(mirror_disc(R, "Diamond", "SteelLight", "GlacierBlue", 6, 1, rim_minor=0.12), W))
    b.add("Mirror", place(trim_ring(R * 0.82, 0, "AuroraCyan", True, minor=0.05, segments=6), W @ M((0, 0, 0.12))))
    b.add("Mirror", place(cyl(0.45, 0.3, "SteelLight", 16), W @ M((0, 0, -0.55))))
    shoulder = V(0, -radius_at(7.0) + 0.1, 7.0)
    b.add("Arm", place(block((0.9, 0.7, 0.9), "SteelLight", corner=0.25, edge=0.12), M(shoulder + V(0, -0.2, -0.45))))
    b.add("Arm", piston(shoulder + V(0, -0.5, 0.0), P - D * 0.5, 0.18, "GlacierBlue", "SteelLight"))
    for sx in (-1, 1):
        b.add("Arm", cable(shoulder + V(sx * 0.4, -0.3, -0.3), P - D * 0.3 + V(sx * 0.4, 0, -0.3), 0.3, 0.06, "NavyIce", "GlacierBlue"))
    # the split rays: white to the mirror, pink and green out to crystal receivers on two coil pods
    top = V(0, 0, 11.6)
    b.add("Rays", light_beam(top + V(0, -0.5, -0.2), P + V(0, 0.35, 0.6), 0.22, 0.08, "Diamond", 8))
    for sx, swatch in ((-1, "MagicPink"), (1, "AuroraGreen")):
        pod = V(sx * 3.6, 1.8, 1.1)
        b.add("Pods", place(cyl(0.95, 0.4, "SteelLight", 16), M(pod)))
        b.add("Pods", place(coil(0.7, 2.6, 5, "GlacierBlue", "IceBlue", "AuroraCyan"), M(pod + V(0, 0, 0.4))))
        b.add("Pods", place(cut_crystal_cluster(0.7, swatch if swatch == "MagicPink" else "AuroraGreen", "SteelLight", 5), M(pod + V(0, 0, 3.75))))
        b.add("Pods", place(trim_ring(0.98, 0, "AuroraCyan", True, minor=0.05, segments=16), M(pod + V(0, 0, 0.42))))
        b.add("Rays", light_beam(top + V(sx * 0.6, 0.1, -0.3), pod + V(0, 0, 4.4), 0.18, 0.06, swatch, 8))
        b.add("Cables", cable(pod + V(-sx * 0.8, -0.2, 0.3), V(sx * 1.6, 0.6, 1.4), 0.35, 0.1, "NavyIce", "GlacierBlue", ribs=2))
    for x, y, a in ((-4.4, 0.4, 0.3), (4.4, -1.2, 1.9), (-1.6, 4.5, 2.6), (1.9, 4.4, 4.0)):
        b.add("DeckCrystals", place(cut_crystal_cluster(0.55, "IceBlue", "SnowWhite", 5), M((x, y, 1.1), (0, 0, a))))
    # tracker plinths at the front corners, a gem lamp at the back
    for sx in (-1, 1):
        b.add("Deck", place(cyl(0.6, 0.15, "GlacierBlue", 6), M((sx * 4.0, -3.9, 1.1))))
    hit = beam_to_edge(b, P, D, R, BEAM_SWATCH[3])
    return {"Work": frame(P + D * 0.15, out=D), "Lamp1": up_((0, 0, 14.2)), "Lamp2": up_((-4.3, 4.2, 1.1)),
            "Gear1": up_((-4.0, -3.9, 1.25)), "Gear2": up_((4.0, -3.9, 1.25)), "Steam1": up_((3.3, 4.3, 1.1)),
            "Hit": frame(hit, out=(0, -1, 0.6)), "Trail": frame(P + D * 0.15, out=D), "NamePlate": front((0, -5.55, 0.4)),
            "Aura": up_((0, 0, 1.1)), "Top": up_((0, 0, 14.2))}


# ---------- tier 4: Enchanted - mirrors orbiting a column of light ----------

def gold_mirror(b, role, at, radius, gem="MagicPink", sides=24, gems=6):
    """A floating mirror in a gold frame with a gem on top and a crystal hanging below."""
    b.add(role, place(mirror_disc(radius, "Diamond", "Gold", "Moonstone", sides, 1), at))
    b.add(role, place(gem_setting(radius * 0.14, gem, "Gold", 4), at @ frame((0, radius * 1.05, -0.05), out=(0, 1, 0))))
    b.add(role, place(cut_crystal(radius * 0.55, radius * 0.1, "RuneViolet", sides=6), at @ M((0, -radius * 1.0, -0.05), (math.pi / 2, 0, 0))))
    for k in range(gems):
        a = k * 2 * math.pi / gems + math.pi / 6
        b.add(role, place(cut_gem(radius * 0.06, "AuroraCyan"), at @ M((radius * 0.97 * math.cos(a), radius * 0.97 * math.sin(a), 0.16))))


def tier_enchanted(b):
    dais = bmesh.new()
    lathe(dais, [(0, 0), (5.2, 0), (5.2, 0.3), (5.0, 0.35), (5.0, 0.55), (4.75, 0.8), (0, 0.8)], 6)
    b.add("Dais", [(dais, "Moonstone", 0.04, False)])
    plinth = bmesh.new()
    lathe(plinth, [(0, -0.01), (5.35, -0.01), (5.35, 0.18), (0, 0.18)], 6)
    b.add("Dais", [(plinth, "StoneDark", 0.03, False)])
    b.add("Dais", place(trim_ring(4.87, 0, "RuneViolet", minor=0.08, segments=6), M((0, 0, 0.56))))
    b.add("Dais", place(engraved_rune_ring(3.6, "RuneGlow", "ArcaneDeep", "RuneViolet", 16), M((0, 0, 0.8))))
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        if k in (4,):  # the front corner stays clear for the beam
            continue
        b.add("DaisCrystals", place(cut_crystal_cluster(0.6, "CrystalCyan" if k % 2 else "RuneViolet", "Moonstone", 4), M((4.5 * math.cos(a), 4.5 * math.sin(a), 0.78), (0, 0, a))))
    for k in range(6):
        fa = k * math.pi / 3
        apothem = 5.2 * math.cos(math.pi / 6)
        b.add("Dais", place(gem_setting(0.15, "AuroraCyan", "Gold", 4), frame((apothem * math.cos(fa) * 0.99, apothem * math.sin(fa) * 0.99, 0.18), out=(math.cos(fa), math.sin(fa), 0))))
    # the pedestal and the column of light
    ped = bmesh.new()
    lathe(ped, [(0, 0.8), (1.6, 0.8), (1.5, 1.2), (1.1, 1.45), (0.9, 1.6), (0.9, 2.3), (1.25, 2.45), (1.25, 2.7), (0, 2.7)], 6)
    b.add("Pedestal", [(ped, "Moonstone", 0.03, False)])
    b.add("Pedestal", place(trim_ring(1.27, 2.58, "Gold", minor=0.07, segments=6), M()))
    b.add("Pedestal", place(trim_ring(1.55, 0.98, "Gold", minor=0.07, segments=6), M()))
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        b.add("Pedestal", place(rune_glyph(0.4, k, "RuneGlow", 0.04), frame((0.9 * math.cos(a) * 1.02, 0.9 * math.sin(a) * 1.02, 1.95), out=(math.cos(a), math.sin(a), 0))))
    light = bmesh.new()
    lathe(light, [(0, 2.6), (0.62, 2.6), (0.5, 3.6), (0.45, 9.0), (0.5, 14.6), (0.3, 15.2), (0, 15.3)], 16)
    b.add("Column", [(light, "RuneGlow", 0.0, True)])
    for k in range(18):  # motes spiralling up the column
        a = k * 1.1
        b.add("Column", place(cut_gem(0.09, "Moonstone" if k % 2 else "CrystalCyan"), M((0.75 * math.cos(a), 0.75 * math.sin(a), 3.2 + k * 0.65))))
    for z, r, role in ((5.0, 1.45, "RuneRingA"), (9.6, 1.2, "RuneRingB"), (13.6, 0.95, "RuneRingC")):
        b.add(role, place(engraved_rune_ring(r, "RuneGlow", "ArcaneDeep", "Gold", 6), M((0, 0, z))))
    # the crown on top: a crystal cluster on a floating gold cup, a gem, a halo
    cup = bmesh.new()
    lathe(cup, [(0, 15.5), (0.5, 15.5), (0.95, 15.8), (1.0, 15.95), (0, 15.9)], 16)
    b.add("Crown", [(cup, "Gold", 0.0, False)])
    b.add("Crown", place(cut_crystal_cluster(1.0, "CrystalCyan", "Moonstone", 6), M((0, 0, 15.8))))
    b.add("Crown", place(gem_setting(0.3, "MagicPink", "Gold", 6), M((0, 0, 17.4))))
    halo = bmesh.new()
    torus(halo, M((0, 0, 17.8), (math.pi / 2, 0, 0.5)), 0.62, 0.04, 24, 4)
    b.add("Crown", [(halo, "Gold", 0.0, False)])
    # the orbiting mirrors: three small ones facing the column on glowing orbit paths, the main one at the front
    for k, (ang, z, role, gem) in enumerate(((math.radians(25), 6.2, "MirrorB", "AuroraCyan"), (math.radians(150), 9.8, "MirrorC", "MagicPink"), (math.radians(270 + 180), 12.6, "MirrorD", "AuroraGreen"))):
        pos = V(3.0 * math.cos(ang), 3.0 * math.sin(ang), z)
        inward = (V(0, 0, z + 0.8) - pos).normalized()
        gold_mirror(b, role, frame(pos, out=inward), 0.8, gem, 16, 3)
        orbit = bmesh.new()
        torus(orbit, M((0, 0, z), (0.12 * (k - 1), 0.1, 0)), 3.0, 0.03, 24, 4)
        b.add("Orbits", [(orbit, "RuneViolet", 0.0, True)])
    P = V(0, -3.3, 7.6)
    D = aim()
    R = MIRROR_R[4]
    W = frame(P, out=D)
    gold_mirror(b, "Mirror", W, R, "MagicPink")
    b.add("MirrorRing", place(engraved_rune_ring(R * 1.22, "RuneGlow", "ArcaneDeep", "Gold", 8), W @ M((0, 0, -0.45))))
    # floating rune stones round the base
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        stone = cage_box((0.55, 0.4, 0.65), 1)
        stone = subsurf(stone, 1)
        stone.transform(M((3.4 * math.cos(a), 3.4 * math.sin(a), 2.4 + 0.4 * (k % 2)), (0.2, 0.1, a)))
        b.add("RuneStones", [(stone, "StoneDark", 0.0, False)])
        b.add("RuneStones", place(rune_glyph(0.36, k + 1, "RuneGlow", 0.03), frame((3.4 * math.cos(a), 3.4 * math.sin(a), 2.4 + 0.4 * (k % 2)), out=(math.cos(a), math.sin(a), 0)) @ M((0, 0, 0.2))))
    hit = beam_to_edge(b, P, D, R, BEAM_SWATCH[4])
    return {"Work": frame(P + D * 0.15, out=D), "Lamp1": up_((0, 0, 18.0)), "Lamp2": up_((3.0, 1.6, 0.8)),
            "Gear1": up_((-3.4, -2.7, 0.8)), "Gear2": up_((3.4, -2.7, 0.8)), "Steam1": up_((0, 0, 15.4)),
            "Hit": frame(hit, out=(0, -1, 0.6)), "Trail": frame(P + D * 0.15, out=D), "NamePlate": front((0, -4.55, 0.4)),
            "Aura": up_((0, 0, 0.8)), "Top": up_((0, 0, 18.0))}


# ---------- tier 5: Legendary - the Celestial Observatory ----------

SUN = V(0, 0.8, 16.4)
SUN_OUT = Vector((0, -1, -0.12)).normalized()
SUN_R = 3.0


def tier_observatory(b):
    # the plinth: gunmetal, gold trim, aurora strips, vents, gems, front steps
    b.add("Platform", block((14.4, 14.4, 0.9), "Gunmetal", corner=1.2, edge=0.25))
    b.add("Platform", place(block((13.8, 13.8, 0.3), "StoneLight", corner=1.0, edge=0.1), M((0, 0, 0.9))))
    b.add("Trim", place(block((14.5, 14.5, 0.16), "Gold", corner=1.22, edge=0.06), M((0, 0, 0.72))))
    for sx in (-1, 1):
        b.add("Platform", place(vent(2.2, 0.4, 5, "Gunmetal", "SteelDark"), front((sx * 4.6, -7.19, 0.45))))
        b.add("Trim", trim_strip((sx * 1.9, -7.22, 0.4), (sx * 3.2, -7.22, 0.4), 0.16, "AuroraGreen", True))
        for sy in (-1, 1):
            b.add("Platform", place(gem_setting(0.2, "AuroraCyan", "Gold", 4), M((sx * 6.5, sy * 6.5, 1.2))))
    for k in range(4):  # star inlays on the plinth top
        a = k * math.pi / 2 + math.pi / 4
        b.add("Platform", place(four_star(0.45, "Gold"), M((5.4 * math.cos(a), 5.4 * math.sin(a), 1.22))))
    # the observatory drum: a stepped base, white walls, brass bands, glowing arched windows, a gold cornice
    drum = bmesh.new()
    lathe(drum, [(0, 1.2), (4.5, 1.2), (4.5, 1.8), (4.1, 2.0), (3.65, 2.15), (3.5, 7.3), (0, 7.3)], 32)
    b.add("Drum", [(drum, "SnowWhite", 0.0, False)])
    b.add("Drum", place(trim_ring(4.52, 1.55, "Gold", minor=0.1, segments=32), M()))
    for z in (2.6, 6.5):
        b.add("Drum", place(trim_ring(3.56, z, "Brass", minor=0.14, segments=32), M()))
        b.add("Drum", place(rivet_ring(3.62, 10, 0.07, "Gold"), M((0, 0, z + 0.18))))
    cornice = bmesh.new()
    lathe(cornice, [(3.45, 7.2), (3.85, 7.25), (3.95, 7.5), (3.85, 7.75), (3.3, 7.75)], 32)
    b.add("Drum", [(cornice, "Gold", 0.0, False)])
    b.add("Drum", place(trim_ring(3.52, 7.05, "AuroraGreen", True, minor=0.08, segments=32), M()))
    for k in range(8):
        a = math.radians(-90 + 22.5) + k * math.pi / 4
        n = V(math.cos(a), math.sin(a), 0)
        if abs(a % (2 * math.pi) - math.radians(270)) < 0.3:
            continue
        at = frame(n * 3.47 + V(0, 0, 4.4), out=n)
        win = bmesh.new()
        rounded_block(win, (0.8, 1.5, 0.12), M((0, 0, 0.04)), corner=0.38, edge=0.03, corner_seg=3, edge_seg=1)
        b.add("Windows", place([(win, "LampYellow", 0.0, True)], at))
        frm = bmesh.new()
        rounded_block(frm, (1.05, 1.75, 0.1), M((0, 0, 0.0)), corner=0.5, edge=0.03, corner_seg=3, edge_seg=1)
        b.add("Windows", place([(frm, "Gold", 0.0, False)], at))
        mullion = bmesh.new()
        box(mullion, (0, -0.05, 0.12), (0.07, 1.4, 0.05))
        b.add("Windows", [(mullion, "Gold", 0.0, False)], at)
    # the front door with steps
    door = front((0, -3.64, 2.15))
    b.add("Door", place(block((1.6, 2.4, 0.12), "PineDark", corner=0.75, edge=0.04), door @ M((0, 1.2, 0))))
    for x in (-0.4, 0.4):
        b.add("Door", place(block((0.06, 2.0, 0.05), "Pine", corner=0.02, edge=0.01), door @ M((x, 1.0, 0.12))))
    arch = bmesh.new()
    sweep(arch, [V(-0.92, 0, 0), V(-0.92, 1.75, 0), V(-0.65, 2.35, 0), V(0, 2.62, 0), V(0.65, 2.35, 0), V(0.92, 1.75, 0), V(0.92, 0, 0)], 0.13, 10)
    b.add("Door", place([(arch, "Gold", 0.0, False)], door @ M((0, 0, 0.1))))
    b.add("Door", place(cyl(0.08, 0.1, "Gold", 10), door @ M((0.5, 1.1, 0.12))))
    b.add("Door", place(four_star(0.3, "LampYellow"), door @ M((0, 2.15, 0.16))))
    for k, (y, z) in enumerate(((-4.9, 1.2), (-4.55, 1.5))):
        b.add("Door", place(block((2.4 - 0.3 * k, 0.9, 0.3), "StoneLight", corner=0.1, edge=0.04), M((0, y, z))))
    # the night-sky dome with gold stars, a slit and a brass telescope aimed at the sun
    dome = bmesh.new()
    lathe(dome, [(3.45, 7.7)] + [(3.45 * math.cos(math.radians(a)), 7.7 + 3.45 * math.sin(math.radians(a))) for a in (15, 30, 45, 60, 75, 87)] + [(0, 11.15)], 32)
    b.add("Dome", [(dome, "NavyIce", 0.0, False)], organic=True)
    for k in range(14):
        a = k * 2.39996
        el = math.radians(18 + (k * 37) % 62)
        n = V(math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el))
        b.add("Dome", place(four_star(0.16 + 0.06 * (k % 3), "LampYellow"), frame(V(0, 0, 7.7) + n * 3.47, out=n)))
    slit_x = -1.7
    rs = math.sqrt(3.45 ** 2 - slit_x ** 2)
    slit = [V(slit_x, -rs * math.cos(math.radians(a)), 7.7 + rs * math.sin(math.radians(a))) for a in range(10, 101, 10)]
    for sx in (-1, 1):
        s = bmesh.new()
        sweep(s, [p + V(sx * 0.42, 0, 0) for p in slit], 0.09, 8)
        b.add("Dome", [(s, "Gold", 0.0, False)])
    opening = bmesh.new()
    sweep(opening, slit, 0.34, 8)
    b.add("Dome", [(opening, "Gunmetal", 0.0, False)])
    scope_at = V(slit_x, -1.7, 10.1)
    sdir = (SUN + V(-1.2, 0, -1.0) - scope_at).normalized()
    tube = bmesh.new()
    lathe(tube, [(0, -0.6), (0.38, -0.6), (0.46, 0), (0.46, 2.6), (0.58, 2.7), (0.58, 3.2), (0.5, 3.2), (0, 3.1)], 20, Matrix.Translation(scope_at) @ align_z(sdir))
    b.add("Telescope", [(tube, "Brass", 0.0, False)])
    for s in (0.4, 1.5, 2.5):
        b.add("Telescope", place(trim_ring(0.48, 0, "Gold", minor=0.07, segments=20), Matrix.Translation(scope_at + sdir * s) @ align_z(sdir)))
    lens = bmesh.new()
    lathe(lens, [(0, 3.12), (0.5, 3.12), (0, 3.2)], 20, Matrix.Translation(scope_at) @ align_z(sdir))
    b.add("Telescope", [(lens, "Diamond", 0.0, True)])
    # the side gears: a big brass gear and a small one on each side of the drum (they turn the dome)
    for sx in (-1, 1):
        b.add("Gears", place(spoked_gear(1.25, 10, 0.3, 0.16, 4, "Brass", "Gold"), frame((sx * 3.72, 0.6, 4.4), out=(sx, 0, 0))))
        b.add("Gears", place(gear(0.6, 8, 0.3, 0.12, "Gold", "Brass"), frame((sx * 3.62, -1.0, 5.75), out=(sx, 0, 0))))
        b.add("Gears", place(dial(0.35, "Cream", "Gold", "WarnRed", 0.4 * sx), frame((sx * 3.5 * 0.71, -3.5 * 0.71, 3.3), out=(sx * 0.71, -0.71, 0))))
    # the finial column from the dome up to the sun, with an armillary of brass rings
    b.add("Column", pipe_between((0, 0.6, 11.0), (0, 0.75, 13.6), 0.32, "Brass"))
    for z in (11.4, 12.6):
        b.add("Column", place(trim_ring(0.36, 0, "Gold", minor=0.08, segments=16), M((0, 0.65, z))))
    b.add("Column", place(gear(0.62, 10, 0.22, 0.12, "Gold", "Brass"), M((0, 0.68, 12.0))))
    Sm = frame(SUN, out=SUN_OUT)
    arm = bmesh.new()
    torus(arm, Sm @ M((0, 0, -0.25)), 3.55, 0.1, 40, 4)
    b.add("Armillary", [(arm, "Brass", 0.0, False)])
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        b.add("Armillary", place(rivet(0.1, "Gold"), Sm @ frame((3.55 * math.cos(a), 3.55 * math.sin(a), -0.15), out=(0, 0, 1))))
    # the sun: a puffed disk with a calm face, glowing eyes, a crown of rays and a glowing corona
    disk = bmesh.new()
    lathe(disk, [(0, -0.55), (2.4, -0.5), (2.9, -0.2), (SUN_R, 0.05), (2.75, 0.4), (1.6, 0.6), (0, 0.65)], 32)
    disk.transform(Sm)
    b.add("Sun", [(disk, "FlameYellow", 0.0, False)], organic=True)
    b.add("Sun", place(trim_ring(SUN_R - 0.02, 0.05, "Gold", minor=0.12, segments=32), Sm))
    for sx in (-1, 1):
        eye = Sm @ frame((sx * 0.95, 0.35, 0.5), out=(sx * 0.08, 0.05, 1), up=(0, 1, 0))
        b.add("Eyes", place(cartoon_eye(0.56, "CrystalCyan", look=(0.0, -0.22)), eye))
        lid = bmesh.new()  # a heavy, calm upper lid over the top half of the eye, with a dark lash line
        lathe(lid, [(0, 0.0), (0.62, 0.0), (0.6, 0.16), (0.45, 0.3), (0, 0.35)], 16)
        bmesh.ops.bisect_plane(lid, geom=lid.verts[:] + lid.edges[:] + lid.faces[:], plane_co=(0, 0.05, 0), plane_no=(0, -1, 0), clear_outer=True)
        b.add("Face", place([(lid, "Gold", 0.0, False)], eye @ M((0, 0, 0.02))))
        lash_line = bmesh.new()
        sweep(lash_line, [eye @ V(0.63 * math.cos(a), 0.05 - 0.06 * math.sin(a), 0.3 * math.sin(a) + 0.05) for a in [math.pi * k / 8 for k in range(9)]], 0.05, 6)
        b.add("Face", [(lash_line, "PineDark", 0.0, False)])
        lash = bmesh.new()
        sweep(lash, [Sm @ V(sx * (0.95 + dx), 0.35 + 0.8 - 0.3 * dx * dx, 0.64) for dx in (-0.5, -0.25, 0.0, 0.25, 0.5)], 0.045, 6)
        b.add("Face", [(lash, "PineDark", 0.0, False)])
        blush = bmesh.new()
        blob(blush, (sx * 1.75, -0.45, 0.48), (0.42, 0.26, 0.12), 2)
        blush.transform(Sm)
        b.add("Face", [(blush, "Blush", 0.0, False)])
    smile = bmesh.new()
    sweep(smile, [Sm @ V(x, -0.75 - 0.28 * (1 - (x / 0.7) ** 2), 0.6) for x in (-0.7, -0.45, -0.2, 0.0, 0.2, 0.45, 0.7)], 0.07, 8)
    b.add("Face", [(smile, "PineDark", 0.0, False)])
    nose = bmesh.new()
    blob(nose, (0, -0.15, 0.68), (0.2, 0.16, 0.1), 2)
    nose.transform(Sm)
    b.add("Face", [(nose, "Amber", 0.0, False)])
    for k in range(16):  # the crown of rays: long gold rays and short amber ones, gems at the long ones
        a = math.pi / 2 + k * math.pi / 8
        long_ray = k % 2 == 0
        length = (2.1 if k == 0 else 1.7) if long_ray else 1.05
        ray = bmesh.new()
        lathe(ray, [(0, 0), (0.48 if long_ray else 0.36, 0), (0.3 if long_ray else 0.2, length * 0.55), (0, length)], 4)
        ray.transform(Sm @ frame((2.75 * math.cos(a), 2.75 * math.sin(a), -0.05), out=(math.cos(a), math.sin(a), 0)) @ Matrix.Diagonal((1, 0.4, 1, 1)))
        b.add("Rays", [(faceted(ray), "Gold" if long_ray else "Amber", 0.0, False)])
        if long_ray:
            b.add("Rays", place(cut_gem(0.13, "AuroraCyan" if k % 4 else "MagicPink"), Sm @ M((3.35 * math.cos(a), 3.35 * math.sin(a), 0.22))))
    corona = bmesh.new()
    torus(corona, Sm @ M((0, 0, -0.35)), 3.15, 0.22, 40, 6)
    b.add("Corona", [(corona, "FlameOrange", 0.0, True)])
    # mini planets on brass orbit rings round the sun
    planets = ((5.4, (0.3, 0.0, 0.0), 0.9, 0.55, "DeepIce"), (6.0, (-0.25, 0.12, 0.0), 2.6, 0.7, "Copper"), (5.7, (0.1, -0.2, 0.0), 4.4, 0.45, "PolarTeal"))
    for k, (r, rot, phase, pr, swatch) in enumerate(planets):
        om = Matrix.Translation(SUN) @ align_z(Vector((0, -1, 0))) @ Euler(rot).to_matrix().to_4x4()
        ring = bmesh.new()
        torus(ring, om, r, 0.05, 40, 4)
        b.add("Orbits", [(ring, "Brass", 0.0, False)])
        p = om @ Vector((r * math.cos(phase), r * math.sin(phase), 0))
        ball = bmesh.new()
        blob(ball, p, (pr, pr, pr), 3)
        b.add("Planets", [(ball, swatch, 0.0, False)], organic=True)
        if k == 1:
            band = bmesh.new()
            torus(band, Matrix.Translation(p) @ Matrix.Rotation(0.5, 4, "X"), pr * 1.55, 0.06, 24, 4)
            b.add("Planets", [(band, "Cream", 0.0, False)])
        if k == 0:
            moon = bmesh.new()
            blob(moon, p + Vector((0.8, 0, 0.5)), (0.18, 0.18, 0.18), 2)
            b.add("Planets", [(moon, "StoneLight", 0.0, False)])
    # the great mirror: gold frame in a brass gimbal on struts from the cornice
    P = V(0, -5.0, 7.6)
    D = aim()
    R = MIRROR_R[5]
    W = frame(P, out=D)
    b.add("Mirror", place(mirror_disc(R, "Diamond", "Gold", "Gold", 28, 2, rim_minor=0.14), W))
    b.add("Mirror", place(rivet_ring(R * 0.97, 16, 0.07, "Gold"), W @ M((0, 0, -0.12))))
    for k in range(12):  # a frame of little rays round the mirror
        a = k * math.pi / 6
        ray = bmesh.new()
        lathe(ray, [(0, 0), (0.16, 0), (0, 0.45)], 4)
        ray.transform(W @ frame((R * 1.05 * math.cos(a), R * 1.05 * math.sin(a), -0.05), out=(math.cos(a), math.sin(a), 0)))
        b.add("Mirror", [(faceted(ray), "Gold", 0.0, False)])
    b.add("Mirror", place(crest(0.7, 0.85, 0.12, "Gold", "DeepIce", "SnowWhite", "AuroraCyan"), W @ M((0, 0, -0.3), (math.pi, 0, 0))))
    gimbal = bmesh.new()
    torus(gimbal, Matrix.Translation(P) @ Matrix.Rotation(math.pi / 2, 4, "Y") @ Matrix.Rotation(0, 4, "Z"), R + 0.35, 0.1, 40, 6)
    b.add("Gimbal", [(gimbal, "Brass", 0.0, False)])
    for sx in (-1, 1):
        b.add("Gimbal", place(cyl(0.18, 0.35, "Gold", 14), frame((sx * (R + 0.1), P.y, P.z), out=(sx, 0, 0))))
        b.add("Gimbal", beam_between((sx * 1.0, -3.3, 7.4), (sx * (R + 0.35), P.y + 0.1, P.z - 0.25), 0.26, swatch="Brass"))
        b.add("Gimbal", place(bolt(0.1, "Gold", "Brass"), frame((sx * 1.0, -3.55, 7.4), out=(0, -1, 0))))
    b.add("Gimbal", piston(V(0, -3.5, 5.2), P - D * 0.45 + V(0, 0, -0.6), 0.16, "Gunmetal", "SteelLight"))
    # sunlight from the sun's chin down to the mirror
    b.add("SunRay", light_beam(SUN + SUN_OUT * 0.3 + V(0, -0.2, -2.6), P + V(0, 0.4, 0.5), 0.35, 0.16, "LampYellow", 12))
    hit = beam_to_edge(b, P, D, R, BEAM_SWATCH[5])
    sun_top = SUN + V(0, 0, SUN_R + 2.1)
    return {"Work": frame(P + D * 0.15, out=D), "Lamp1": up_(sun_top + V(0, -0.1, 0.05)), "Lamp2": up_((0, 0, 11.15)),
            "Gear1": up_((-5.6, -5.2, 1.2)), "Gear2": up_((5.6, -5.2, 1.2)), "Steam1": up_(scope_at + sdir * 3.3),
            "Hit": frame(hit, out=(0, -1, 0.6)), "Trail": frame(P + D * 0.15, out=D), "NamePlate": front((0, -7.22, 0.45)),
            "Aura": up_((0, 0, 1.2)), "Top": up_(sun_top), "Crown": up_(SUN + V(0, 0, SUN_R)),
            "Eyes": frame(SUN + SUN_OUT * 0.6 + V(0, 0, 0.35), out=SUN_OUT)}


TIER_FNS = [tier_scrappy, tier_workshop, tier_frosttech, tier_enchanted, tier_observatory]


# ---------- upgrade sets ----------

RAINBOW = ("WarnRed", "Amber", "LampYellow", "AuroraGreen", "GlacierBlue", "RuneViolet")


def UPGRADES(u, t, atts, b, fx):
    work, hit = atts["Work"], atts["Hit"]
    R = MIRROR_R[t]
    rim, back = METAL[t]
    if u == 1:  # a polished mirror: a bright face, a heavier rim, more glints
        sides = 6 if t == 3 else 24
        b.add("PolishedMirror", place(mirror_disc(R * 1.03, "Diamond", rim, back, sides, 3, rim_minor=R * 0.09, depth=0.1), work @ M((0, 0, 0.08))))
        if t == 1:
            b.add("PolishedMirror", place(rivet_ring(R * 0.9, 12, 0.06, "Copper"), work @ M((0, 0, 0.2))))
        elif t == 2:
            b.add("PolishedMirror", place(rivet_ring(R * 0.9, 12, 0.06, "Copper"), work @ M((0, 0, 0.2))))
        elif t == 3:
            b.add("PolishedMirror", place(trim_ring(R * 0.92, 0, "AuroraCyan", True, minor=0.05, segments=6), work @ M((0, 0, 0.22))))
        else:
            for k in range(4):
                a = k * math.pi / 2 + math.pi / 4
                b.add("PolishedMirror", place(cut_gem(0.1 + 0.03 * (t == 5), "MagicPink" if k % 2 else "AuroraCyan"), work @ M((R * 0.92 * math.cos(a), R * 0.92 * math.sin(a), 0.26))))
    elif u == 2:  # a beacon on top (and a second light)
        b.add("Beacon1", place(tier_lamp(t), atts["Lamp1"]))
        if t >= 4:
            b.add("Beacon1", place(trim_ring(0.55, 0.05, "Gold", minor=0.05, segments=16), atts["Lamp1"]))
        if "Lamp2" in atts:
            b.add("Beacon2", place(tier_lamp(t), atts["Lamp2"]))
    elif u == 3:  # mirrors that turn to track the sun
        for key in ("Gear1", "Gear2"):
            if key in atts:
                b.add("Tracker" + key[-1], place(tracker(t), atts[key]))
        if t >= 4 and "Steam1" in atts:
            fx.add("Sparkle", place(tier_puff(t), atts["Steam1"]))
    elif u == 4:  # a brighter beam with heat glow (render-only stand-ins; particles and a Beam in game)
        p0 = work.to_translation()
        p1 = hit.to_translation()
        fx.add("HotBeam", light_beam(p0 + (p1 - p0).normalized() * 0.5, p1, R * 0.42, 0.18, "FlameOrange", 12))
        for k in range(3):
            ring = bmesh.new()
            torus(ring, hit @ M((0, 0, 0.15 + 0.3 * k)), 0.45 + 0.25 * k, 0.04, 20, 4)
            fx.add("Heat", [(ring, "FlameYellow" if k % 2 else "FlameOrange", 0.0, True)])
        fx.add("Hit", place(hit_standin(t, "FlameYellow"), hit))
    else:  # a rainbow beam: a prism lens on the mirror, rainbow ray stand-ins along the beam
        lens = []
        lens += trim_ring(0.42, 0, rim, False, minor=0.06, segments=16)
        for k in range(3):
            a = k * 2 * math.pi / 3
            lens += beam_between((0.42 * math.cos(a), 0.42 * math.sin(a), 0), (0.85 * R * math.cos(a), 0.85 * R * math.sin(a), -0.05), 0.07, swatch=rim)
        lens += place(prism(0.7, 0.34, "Diamond"), M((0, 0, -0.1)))
        b.add("RainbowLens", place(lens, work @ M((0, 0, 0.45))))
        p0 = work.to_translation() + (work.to_3x3() @ Vector((0, 0, 0.9)))
        p1 = hit.to_translation()
        side = work.to_3x3() @ Vector((1, 0, 0))
        for k, swatch in enumerate(RAINBOW):
            off = (k - 2.5) * 0.14
            fx.add("Rainbow", light_beam(p0 + side * off * 0.3, p1 + side * off * 2.2, 0.07, 0.1, swatch, 6))


# ---------- the Legendary's signature aura (render-only stand-ins) ----------

def AURA(atts, fx):
    """Twinkling stars, a slow aurora ribbon round the observatory and glowing mini planets orbiting the sun."""
    for k in range(16):
        a = k * 2.39996
        r = 5.0 + 1.6 * ((k * 7) % 5) / 4
        p = V(r * math.cos(a) * 0.95, r * math.sin(a) * 0.7, 9.0 + 12.0 * ((k * 5) % 16) / 16)
        fx.add("Stars", place(four_star(0.22 + 0.1 * (k % 3), "LampYellow" if k % 3 else "EyeWhite"), frame(p, out=(0, -1, 0.2))))
    for band, (swatch, z0, h) in enumerate((("AuroraGreen", 10.5, 1.3), ("AuroraViolet", 11.8, 0.9))):
        left, right = [], []
        for k in range(33):  # a waving curtain arc behind the observatory
            a = math.radians(15 + 150 * k / 32)
            r = 6.9 + 0.35 * math.sin(4 * a)
            z = z0 + 1.1 * math.sin(2.5 * a + 0.4)
            left.append(V(r * math.cos(a), r * math.sin(a), z))
            right.append(V(r * math.cos(a), r * math.sin(a), z + h))
        bm = bmesh.new()
        double_sided_strip(bm, left, right)
        fx.add("AuroraRibbon", [(bm, swatch, 0.0, True)])
    om = Matrix.Translation(SUN) @ align_z(Vector((0, -1, 0)))
    for k, (r, swatch) in enumerate(((7.0, "PolarTeal"), (7.0, "MagicPink"), (7.0, "AuroraCyan"))):
        a = 2.2 + k * 2.1
        p = om @ Vector((r * math.cos(a) * 0.95, r * math.sin(a) * 0.85, 0.6 * (k - 1)))
        ball = bmesh.new()
        blob(ball, p, (0.42, 0.42, 0.42), 2)
        fx.add("GlowPlanets", [(ball, swatch, 0.0, True)])
        halo = bmesh.new()
        torus(halo, Matrix.Translation(p) @ Matrix.Rotation(0.6, 4, "X"), 0.7, 0.04, 20, 4)
        fx.add("GlowPlanets", [(halo, swatch, 0.0, True)])
    ring = bmesh.new()
    torus(ring, M((0, 0, 1.25)), 6.4, 0.07, 48, 4)
    fx.add("AuraGround", [(ring, "AuroraGreen", 0.0, True)])
