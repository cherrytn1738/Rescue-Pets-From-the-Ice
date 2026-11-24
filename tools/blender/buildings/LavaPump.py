# LavaPump.py - the Lava Pump's five tiers and its upgrade sets, for tools/blender/buildings/framework.py.
#   1 Scrappy     a cast-iron hand pump over a lava pit, a bucket under its spout, a patched leather hose
#                 to a tin nozzle lashed on a sawhorse
#   2 Workshop    a steam beam-engine pump: a walking beam on timber posts, a brass boiler and chimney, a
#                 riveted lava tank, brass pipes and a brass nozzle turret
#   3 Frost-tech  crystal-cooled lava pipes: a glass lava reactor wound with coolant coils, crystal
#                 cooling towers, glowing lava pipes in crystal collars, a white nozzle turret
#   4 Enchanted   a volcano altar on a rune dais with floating lava orbs, floating islands and a floating
#                 moonstone horn that sprays lava
#   5 Legendary   the Volcano Forge: a mini volcano with a face (glowing eyes, a lava grin), a crown of
#                 obsidian and gold, a lava heart in a forge cage, pistons, pipes, gauges, an anvil, a
#                 bellows, smoke stacks and a big lava hose aimed at the ice
# The working part (the lava nozzle) sits at Work, +Z toward the ice (-Y, tilted down), in every tier.
# Extra attachments: HoseA/B/C (along the lava hose, +Z along it) and Fountain (the 5th upgrade's spot).
LAVA, LAVA_HOT = "FlameOrange", "FlameYellow"
TIER_Q = {"Scrappy": {"round": 0.75, "corner": 1, "edge": 1}, "Workshop": {"round": 0.75, "corner": 1, "edge": 1}, "Frost-tech": {"round": 1.1},
          "Enchanted": {"round": 1.25, "minor": 1.25, "corner": 3}, "Legendary": {"round": 1.0}}


# ---------- small helpers ----------

def lp_noise(x, y, z, seed):
    return 0.5 * (math.sin(x * 3.1 + seed * 1.7) * math.cos(y * 2.7 - seed) + math.sin(z * 3.7 + x * 1.3 + seed * 2.3))


def lp_rock(center, size, swatch="StoneDark", seed=0.0, glow=False, sub=1, floor=None):
    """A lumpy faceted rock (an icosphere pushed about by a little noise)."""
    bm = bmesh.new()
    blob(bm, (0, 0, 0), (1, 1, 1), sub)
    for v in bm.verts:
        n = lp_noise(v.co.x, v.co.y, v.co.z, seed)
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) * (1 + 0.22 * n)
    bm.transform(M(center, (seed * 0.7, seed * 1.3, seed * 2.1)))
    if floor is not None:
        for v in bm.verts:
            v.co.z = max(v.co.z, floor)
    return [(faceted(bm), swatch, 0.0, glow)]


def lp_glow_rock(center, s, seed, crust="Gunmetal"):
    """A cooling lava rock: a dark crust with a molten core breaking out of it."""
    c = Vector(center)
    pieces = lp_rock(c, (s, s * 0.85, s * 0.7), crust, seed)
    pieces += lp_rock(c + Vector((0.2 * s, -0.25 * s, 0.3 * s)), (s * 0.62, s * 0.58, s * 0.5), LAVA, seed + 3, glow=True)
    return pieces


def lp_pool(radius, segments=16, bubbles=3, seed=0.0):
    """A glowing lava surface (a low dome) with brighter bubbles, its top near z = 0.08."""
    pool = bmesh.new()
    lathe(pool, [(0, -0.05), (radius, -0.05), (radius, 0.02), (radius * 0.6, 0.07), (0, 0.08)], segments)
    pieces = [(pool, LAVA, 0.0, True)]
    for k in range(bubbles):
        a = seed + k * 2.3
        b = bmesh.new()
        blob(b, (radius * 0.5 * math.cos(a), radius * 0.5 * math.sin(a), 0.07), (radius * 0.15, radius * 0.15, radius * 0.09), 1)
        pieces.append((b, LAVA_HOT, 0.0, True))
    return pieces


def lp_spline(ctrl, per=5):
    """A smooth Catmull-Rom curve through the control points."""
    P = [Vector(p) for p in ctrl]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2 * p1) + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out


def lp_hose(ctrl, radius, swatch, sleeve=None, rib=None, ribs=0, per=5, segments=10):
    """A hose along a smooth curve, with end sleeves and rings. Returns (pieces, curve points)."""
    pts = lp_spline(ctrl, per)
    h = bmesh.new()
    sweep(h, pts, radius, segments)
    pieces = [(h, swatch, 0.0, False)]
    if sleeve:
        for end, nxt in ((pts[0], pts[1]), (pts[-1], pts[-2])):
            d = (nxt - end).normalized()
            s = bmesh.new()
            cylinder(s, end - d * 0.02, radius * 1.4, 0.24, 12, direction=d)
            pieces.append((s, sleeve, 0.02, False))
    for k in range(1, ribs + 1):
        i = int((len(pts) - 1) * k / (ribs + 1))
        r = bmesh.new()
        torus(r, Matrix.Translation(pts[i]) @ align_z(pts[i + 1] - pts[i - 1]), radius * 1.03, radius * 0.22, 10, 4)
        pieces.append((r, rib or swatch, 0.0, False))
    return pieces, pts


def lp_along(pts, f):
    i = max(1, min(len(pts) - 2, int(round(f * (len(pts) - 1)))))
    return frame(pts[i], out=pts[i + 1] - pts[i - 1])


def lp_hose_atts(atts, pts):
    for name, f in (("HoseA", 0.3), ("HoseB", 0.55), ("HoseC", 0.8)):
        atts[name] = lp_along(pts, f)


def lp_stream(ctrl, r0, r1, swatch=LAVA, per=4, segments=8):
    """A glowing lava stream or drip along a curve, tapering from r0 to r1."""
    s = bmesh.new()
    sweep(s, lp_spline(ctrl, per), r0, segments, radius_end=r1)
    return [(s, swatch, 0.0, True)]


def lp_ring(matrix, radius, minor, swatch, glow=False, segments=16, minor_segments=4):
    r = bmesh.new()
    torus(r, matrix, radius, minor, segments, minor_segments)
    return [(r, swatch, 0.0, glow)]


def lp_mouth_glow(radius, z):
    """Lava glowing in a nozzle's mouth, and a drip hanging under its lip (local +Y is up)."""
    g = bmesh.new()
    blob(g, (0, 0, z), (radius, radius, radius * 0.45), 1)
    d = bmesh.new()
    cylinder(d, (0, -radius * 0.75, z - 0.05), radius * 0.28, radius * 0.9, 6, top=0.0, direction=(0, -1, 0.35))
    return [(g, LAVA, 0.0, True), (d, LAVA, 0.0, True)]


# ---------- the lava nozzles (the working part), one per tier, built along +Z ----------
# NOZ_BANDS: (z, radius) of each nozzle's body, so the 1st upgrade's armour bands wrap it.
NOZ_BANDS = {1: [(0.45, 0.15), (0.78, 0.14)], 2: [(0.45, 0.25), (0.72, 0.25)], 3: [(0.75, 0.34), (1.05, 0.33)],
             4: [(0.55, 0.33), (0.95, 0.34)], 5: [(0.75, 0.4), (1.1, 0.39)]}
NOZ_LEN = {1: 1.05, 2: 1.5, 3: 1.6, 4: 1.62, 5: 1.8}
NOZ_SCALE = {4: 1.45}  # the Enchanted horn is built small and scaled up
HOSE_R = {1: 0.13, 2: 0.14, 3: 0.17, 4: 0.12, 5: 0.32}


def nozzle(t):
    pieces = []
    body = bmesh.new()
    if t == 1:  # a dented tin funnel lashed with rope
        lathe(body, [(0, -0.05), (0.2, -0.05), (0.21, 0.12), (0.16, 0.2), (0.13, 0.85), (0.16, 0.92), (0.16, 1.02), (0.1, 1.05), (0, 1.0)], 12)
        pieces.append((body, "Steel", 0.0, False))
        pieces += lp_ring(M((0, 0, 0.15)), 0.22, 0.045, "PineLight", segments=12)
        pieces += lp_ring(M((0, 0, 0.6)), 0.15, 0.035, "PineLight", segments=12)
        pieces += place(block((0.18, 0.22, 0.03), "PatchGreen", corner=0.03, edge=0.01), frame((0.14, 0, 0.5), out=(1, 0, 0.1)))
        pieces += lp_mouth_glow(0.1, 1.04)
    elif t == 2:  # a brass barrel with a copper band, rivets and a valve wheel
        lathe(body, [(0, -0.1), (0.34, -0.1), (0.34, 0.12), (0.26, 0.16), (0.24, 0.9), (0.3, 0.95), (0.3, 1.1), (0.2, 1.14),
                     (0.17, 1.35), (0.22, 1.4), (0.22, 1.5), (0.12, 1.5), (0, 1.46)], 14)
        pieces.append((body, "Brass", 0.0, False))
        pieces += lp_ring(M((0, 0, 0.55)), 0.25, 0.05, "Copper", segments=14)
        pieces += place(rivet_ring(0.3, 6, 0.04, "Copper"), M((0, 0, 0.12)))
        stem = bmesh.new()
        cylinder(stem, (0, 0.22, 0.6), 0.04, 0.3, 8, direction=(0, 1, 0))
        pieces.append((stem, "Iron", 0.0, False))
        wheel = frame((0, 0.52, 0.6), out=(0, 1, 0))
        pieces += lp_ring(wheel, 0.18, 0.03, "WarnRedDark", segments=12)
        for k in range(3):
            sp = bmesh.new()
            box(sp, (0, 0, 0), (0.36, 0.035, 0.03), (0, 0, k * math.pi / 3))
            sp.transform(wheel)
            pieces.append((sp, "WarnRedDark", 0.0, False))
        pieces += lp_mouth_glow(0.15, 1.5)
    elif t == 3:  # a sleek white barrel with frost fins and cyan rings
        lathe(body, [(0, -0.1), (0.42, -0.1), (0.45, 0.2), (0.36, 0.3), (0.32, 1.3), (0.38, 1.38), (0.38, 1.55), (0.26, 1.6), (0, 1.55)], 16)
        pieces.append((body, "SnowWhite", 0.0, False))
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            fin = bmesh.new()
            rounded_block(fin, (0.08, 0.26, 0.8), M((0.4 * math.cos(a), 0.4 * math.sin(a), 0.75), (0, 0, a + math.pi / 2)), corner=0.03, edge=0.03, corner_seg=1, edge_seg=1)
            pieces.append((fin, "GlacierBlue", 0.0, False))
        for z in (0.32, 1.32):
            pieces += lp_ring(M((0, 0, z)), 0.36, 0.04, "AuroraCyan", True, 16)
        core = bmesh.new()
        cylinder(core, (0, 0, 1.45), 0.22, 0.17, 12)
        pieces.append((core, LAVA, 0.0, True))
        pieces += lp_mouth_glow(0.14, 1.62)
    elif t == 4:  # a moonstone horn with gold bands, a glowing rune band and gems round the flare
        lathe(body, [(0, -0.1), (0.3, -0.1), (0.34, 0.3), (0.3, 0.8), (0.36, 1.2), (0.55, 1.55), (0.6, 1.62), (0.45, 1.6), (0.3, 1.45), (0, 1.4)], 16)
        pieces.append((body, "Moonstone", 0.0, False))
        for z, r in ((0.3, 0.35), (1.2, 0.37)):
            pieces += lp_ring(M((0, 0, z)), r, 0.05, "Gold", segments=16)
        for k in range(6):
            a = k * math.pi / 3
            pieces += place(rune_glyph(0.16, k, "RuneGlow", 0.03), frame((0.32 * math.cos(a), 0.32 * math.sin(a), 0.7), out=(math.cos(a), math.sin(a), 0)))
        for k in range(6):
            a = k * math.pi / 3 + math.pi / 6
            pieces += place(cut_gem(0.07, "MagicPink" if k % 2 else LAVA_HOT), frame((0.58 * math.cos(a), 0.58 * math.sin(a), 1.5), out=(math.cos(a), math.sin(a), 0.6)))
        orb = bmesh.new()
        blob(orb, (0, 0, 1.45), (0.33, 0.33, 0.25), 2)
        pieces.append((orb, LAVA, 0.0, True))
    else:  # a gunmetal cannon with gold rings, fins, a bolt ring and a flared muzzle
        lathe(body, [(0, -0.15), (0.5, -0.15), (0.52, 0.3), (0.42, 0.4), (0.38, 1.4), (0.46, 1.5), (0.55, 1.75), (0.38, 1.8), (0, 1.7)], 18)
        pieces.append((body, "Gunmetal", 0.0, False))
        for z, r in ((0.32, 0.47), (1.45, 0.43)):
            pieces += lp_ring(M((0, 0, z)), r, 0.07, "Gold", segments=18)
        pieces += place(rivet_ring(0.47, 8, 0.05, "Gold"), M((0, 0, 0.18)))
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            fin = bmesh.new()
            rounded_block(fin, (0.08, 0.3, 0.9), M((0.44 * math.cos(a), 0.44 * math.sin(a), 0.9), (0, 0, a + math.pi / 2)), corner=0.03, edge=0.03, corner_seg=1, edge_seg=1, taper=0.7)
            pieces.append((fin, "Gold", 0.0, False))
        pieces += lp_mouth_glow(0.24, 1.76)
    return pieces


# ---------- tier 1: Scrappy - hand pump and bucket ----------

def lp_scrappy(b):
    for x in (-0.3, 2.7):  # pallet battens and planks
        b.add("Pallet", beam_between((x, -2.3, 0.15), (x, 1.45, 0.15), 0.3, swatch="PineDark"))
    for k, (y, L, turn, sw) in enumerate(((-1.85, 3.9, 0.03, "Pine"), (-0.92, 3.6, -0.04, "PineLight"), (0.0, 3.8, 0.02, "Pine"), (0.92, 3.5, -0.03, "PineDark"))):
        b.add("Pallet", place(plank(L, 0.86, 0.24, sw, "PineDark" if sw != "PineDark" else "RustDark", False, k * 1.3), M((1.2, y, 0.3), (0, 0, turn))))
    # the lava pit: a ring of rough stones round a glowing pool, crossed by two beams the pump stands on
    P = V(-1.7, 0.9, 0)
    b.add("PitLava", place(lp_pool(0.82, 16, 3, 0.4), M((P.x, P.y, 0.1))))
    for k in range(7):
        a = k * 2 * math.pi / 7 + 0.2
        b.add("Pit", lp_rock((P.x + 0.9 * math.cos(a), P.y + 0.9 * math.sin(a), 0.16), (0.38, 0.3, 0.24), "StoneDark" if k % 3 else "Stone", k, floor=0.0))
    for dy in (-0.32, 0.32):
        b.add("Pit", grained_beam((P.x - 1.15, P.y + dy, 0.48), (P.x + 1.15, P.y + dy, 0.48), 0.28, "PineDark", "RustDark", faces=(0, 2)))
    # the cast-iron pitcher pump: a flanged barrel, a band, a rust patch, a long spout and a lever
    pump = bmesh.new()
    lathe(pump, [(0, 0.6), (0.45, 0.6), (0.45, 0.76), (0.32, 0.82), (0.3, 1.9), (0.38, 1.96), (0.38, 2.12), (0.26, 2.18),
                 (0.26, 2.4), (0.34, 2.46), (0.34, 2.56), (0, 2.6)], 14, M((P.x, P.y, 0)))
    b.add("Pump", [(pump, "Iron", 0.0, False)])
    b.add("Pump", lp_ring(M((P.x, P.y, 1.4)), 0.31, 0.05, "Rust", segments=14))
    b.add("Pump", place(rivet_ring(0.37, 4, 0.05, "RustDark"), M((P.x, P.y, 0.76))))
    b.add("Pump", place(block((0.36, 0.42, 0.04), "PatchGreen", corner=0.05, edge=0.015), frame((P.x + 0.3, P.y - 0.05, 1.15), out=(1, -0.2, 0))))
    for dz in (-0.14, 0.14):
        b.add("Pump", place(rivet(0.04, "RustDark"), frame((P.x + 0.34, P.y - 0.05, 1.15 + dz), out=(1, -0.2, 0))))
    b.add("Pump", place(cyl(0.11, 0.62, "Rust", 10), M((P.x, P.y, 0.0))))
    spout_pts = [V(P.x, P.y - 0.25, 1.95), V(P.x, P.y - 0.8, 2.0), V(P.x, P.y - 1.35, 1.85), V(P.x, P.y - 1.62, 1.5)]
    spout = bmesh.new()
    sweep(spout, lp_spline(spout_pts, 4), 0.11, 10)
    b.add("Pump", [(spout, "Iron", 0.0, False)])
    b.add("Pump", lp_ring(Matrix.Translation(spout_pts[-1]) @ align_z(spout_pts[-1] - spout_pts[-2]), 0.12, 0.035, "Rust", segments=10))
    b.add("Pump", beam_between((P.x + 0.08, P.y - 1.3, 0.55), (P.x + 0.08, P.y - 1.3, 1.8), 0.14, swatch="PineLight"))  # a stick propping the spout
    lever_a, lever_b = V(P.x, P.y - 0.35, 3.0), V(P.x, P.y + 1.55, 3.6)
    b.add("Lever", place(cyl(0.06, 0.4, "SteelLight", 8), M((P.x, P.y, 2.6))))
    b.add("Lever", beam_between(V(P.x, P.y + 0.3, 2.5), V(P.x, P.y + 0.36, 3.15), 0.1, swatch="Iron"))
    lever = bmesh.new()
    sweep(lever, [lever_a, lever_a.lerp(lever_b, 0.5) + V(0, 0, 0.08), lever_b], 0.07, 8)
    b.add("Lever", [(lever, "Iron", 0.0, False)])
    b.add("Lever", place(cyl(0.12, 0.55, "PineLight", 10), Matrix.Translation(lever_b) @ align_z(lever_b - lever_a) @ M((0, 0, -0.35))))
    for p in (V(P.x, P.y + 0.33, 3.12), V(P.x, P.y - 0.05, 3.03)):
        b.add("Lever", place(cyl(0.05, 0.3, "SteelDark", 8), frame(p + V(-0.15, 0, 0), out=(1, 0, 0))))
    # the bucket under the spout, full of lava, with hoops and a wire handle; a drip falls into it
    B = V(P.x, P.y - 1.68, 0)
    bucket = bmesh.new()
    lathe(bucket, [(0, 0), (0.34, 0), (0.46, 0.75), (0.42, 0.75), (0.31, 0.06), (0, 0.06)], 14, M(B))
    b.add("Bucket", [(bucket, "Steel", 0.0, False)])
    for z, r in ((0.2, 0.37), (0.55, 0.43)):
        b.add("Bucket", lp_ring(M(B + V(0, 0, z)), r, 0.035, "RustDark", segments=14))
    b.add("Bucket", lp_ring(M(B + V(0, 0, 0.75)), 0.44, 0.035, "SteelDark", segments=14))
    wire = bmesh.new()
    sweep(wire, [B + V(-0.45, 0, 0.72), B + V(-0.38, 0.05, 1.05), B + V(0, 0.08, 1.2), B + V(0.38, 0.05, 1.05), B + V(0.45, 0, 0.72)], 0.025, 6)
    b.add("Bucket", [(wire, "Iron", 0.0, False)])
    b.add("BucketLava", place(lp_pool(0.41, 14, 2, 1.0), M(B + V(0, 0, 0.62))))
    b.add("BucketLava", lp_stream([spout_pts[-1] + V(0, -0.02, -0.05), B + V(0, 0.06, 1.05), B + V(0, 0.04, 0.7)], 0.07, 0.035))
    # the patched leather hose from the bucket to the tin nozzle lashed on a sawhorse
    D = V(0, -1, -0.42).normalized()
    N = V(1.1, -1.75, 1.6)
    hose, pts = lp_hose([B + V(0.44, -0.05, 0.2), V(-0.6, -1.0, 0.62), V(0.2, -0.85, 0.8), V(0.85, -1.0, 1.5), N - D * 0.55, N - D * 0.05],
                        HOSE_R[1], "PineDark", "Iron", "PineLight", 3, per=4, segments=8)
    b.add("Hose", hose)
    b.add("Hose", place(block((0.3, 0.06, 0.32), "Rust", corner=0.04, edge=0.02), lp_along(pts, 0.42) @ M((0, 0.12, -0.16))))
    for x0 in (0.35, 1.85):
        for sy in (-1, 1):
            b.add("Sawhorse", beam_between((x0, -1.75 + sy * 0.42, 0.54), (x0 + (0.12 if x0 < 1 else -0.12), -1.75, 1.3), 0.17, swatch="PineLight"))
    b.add("Sawhorse", grained_beam((0.2, -1.75, 1.32), (2.0, -1.75, 1.32), 0.24, "Pine", "PineDark", faces=(1, 3)))
    b.add("Sawhorse", place(block((0.35, 0.4, 0.2), "PineDark", corner=0.05, edge=0.04), M((1.1, -1.55, 1.42))))
    work = frame(N, out=D)
    for z in (0.12, 0.35):
        b.add("Sawhorse", lp_ring(work @ M((0, 0, z), (0.5, 0, 0)), 0.2, 0.04, "PineLight", segments=12))
    b.add("Nozzle", place(nozzle(1), work))
    # the junk: a crate, a leaning shovel, a coal sack, a coil of rope, a few spare stones
    b.add("Junk", place(block((1.1, 1.0, 0.9), "Pine", corner=0.06, edge=0.05), M((2.3, 0.55, 0.54))))
    for z in (0.75, 1.15):
        b.add("Junk", trim_strip((1.78, 0.04, z), (2.82, 0.04, z), 0.06, "PineDark"))
    for sx in (-1, 1):
        b.add("Junk", trim_strip((2.3 + sx * 0.5, 0.04, 0.6), (2.3 + sx * 0.5, 0.04, 1.4), 0.07, "PineDark"))
    b.add("Junk", beam_between((1.55, 0.25, 0.6), (1.72, 0.9, 2.35), 0.09, swatch="PineLight"))
    blade = bmesh.new()
    rounded_block(blade, (0.36, 0.06, 0.42), Matrix.Translation((1.53, 0.18, 0.62)) @ align_z(V(0.17, 0.65, 1.75)), corner=0.08, edge=0.02, corner_seg=2, edge_seg=1)
    b.add("Junk", [(blade, "SteelDark", 0.0, False)])
    for k, (x, z) in enumerate(((-0.22, 0.0), (0.22, 0.0), (0.0, 0.33))):  # a little stack of firewood
        log = frame((2.3 + x - 0.55, -0.8, 0.72 + z), out=(1, 0.05 * k, 0))
        b.add("Junk", place(cyl(0.17, 1.1, "PineDark", 8, bevel=0.0), log))
    for k, (x, y) in enumerate(((-3.0, -0.6), (0.0, 1.9))):
        b.add("Pit", lp_glow_rock((x, y, 0.15), 0.2, k + 5))
    atts = {"Work": work, "Lamp1": up_((2.3, 0.55, 1.44)), "Lamp2": up_((1.95, -1.75, 1.45)),
            "Gear1": frame((P.x - 0.33, P.y, 1.35), out=(-1, 0, 0)), "Gear2": frame((P.x + 0.33, P.y + 0.15, 1.6), out=(1, 0.3, 0)),
            "Steam1": up_((P.x - 0.7, P.y + 0.6, 0.3)), "Steam2": up_(B + V(0, 0, 0.75)),
            "Hit": frame((N.x, -4.4, 0.3), out=(0, -1, 0.6)), "Trail": work, "Fountain": up_((-3.1, -1.9, 0.0)),
            "NamePlate": frame((1.2, -2.33, 0.4), out=(0, -1, 0)), "Aura": up_((0, 0, 0.2)), "Top": up_(lever_b + V(0, 0, 0.15))}
    lp_hose_atts(atts, pts)
    return atts


# ---------- tier 2: Workshop - steam pump and pipes ----------

def lp_workshop(b):
    for k in range(6):  # the deck
        y = -2.8 + k * 1.12
        b.add("Deck", place(plank(8.0, 1.1, 0.45, "Pine" if k % 2 else "PineLight", "PineDark", False, k * 1.1), M((0, y, 0))))
    for sy in (-1, 1):
        b.add("Deck", beam_between((-4.05, sy * 3.25, 0.22), (4.05, sy * 3.25, 0.22), 0.3, swatch="PineDark"))
        for sx in (-1, 1):
            b.add("Deck", place(cyl(0.26, 0.55, "Brass", 12), M((sx * 4.0, sy * 3.25, 0))))
    # the lava well: a stone ring round a glowing pool, the pump barrel standing in it
    W = V(0.8, 2.2, 0.45)
    well = bmesh.new()
    lathe(well, [(0.62, 0.55), (0.62, 0), (0.95, 0), (0.98, 0.5), (0.9, 0.62), (0.62, 0.55)], 14, M(W))
    b.add("Well", [(well, "Stone", 0.0, False)])
    b.add("Well", lp_ring(M(W + V(0, 0, 0.35)), 0.97, 0.05, "Iron", segments=14))
    b.add("WellLava", place(lp_pool(0.62, 14, 2, 0.3), M(W + V(0, 0, 0.42))))
    b.add("Well", place(cyl(0.4, 2.4, "Iron", 14), M(W + V(0, 0, 0.5))))
    for z in (1.1, 2.3):
        b.add("Well", lp_ring(M(W + V(0, 0, z)), 0.42, 0.06, "Copper", segments=14))
    b.add("Well", place(cyl(0.48, 0.25, "Brass", 14), M(W + V(0, 0, 2.9))))
    # the Samson posts: two timber A-frames carrying the walking beam's pivot
    piv = V(0.8, 0.4, 5.45)
    for sx in (-1, 1):
        x = piv.x + sx * 0.6
        for y0 in (-0.7, 1.5):
            b.add("Posts", grained_beam((x, y0, 0.45), (x, piv.y, piv.z - 0.2), 0.34, "PineLight", "Pine", faces=(1,) if sx < 0 else (3,)))
        b.add("Posts", beam_between((x, -0.4, 2.0), (x, 1.2, 2.0), 0.22, swatch="PineDark"))
        b.add("Posts", place(block((0.5, 0.6, 0.45), "Brass", corner=0.1, edge=0.06), M((x, piv.y, piv.z - 0.35))))
    b.add("Posts", place(cyl(0.1, 1.5, "SteelLight", 10), frame((piv.x - 0.75, piv.y, piv.z - 0.1), out=(1, 0, 0))))
    # the walking beam with iron straps, the horsehead over the well and the pump rod
    b.add("Beam", place(block((0.42, 4.3, 0.55), "PineDark", corner=0.08, edge=0.06), M((piv.x, 0.15, piv.z - 0.1))))
    for y in (-1.6, 0.4, 2.0):
        b.add("Beam", place(block((0.5, 0.14, 0.63), "Iron", corner=0.03, edge=0.02), M((piv.x, y, piv.z - 0.14))))
    hc = V(piv.x, 1.1, piv.z + 0.1)  # the horsehead: a thick curved sector whose face hangs over the well
    arc = [math.radians(-55 + 110 * k / 10) for k in range(11)]
    outline = [(1.15 * math.cos(a), 1.15 * math.sin(a)) for a in arc] + [(0.65 * math.cos(a), 0.65 * math.sin(a)) for a in reversed(arc)]
    head = bmesh.new()
    loft(head, [[hc + V(x, oy, oz) for oy, oz in outline] for x in (-0.24, 0.24)])
    b.add("Beam", [(head, "Iron", 0.0, False)])
    for a in arc[1::3]:
        b.add("Beam", place(rivet(0.05, "Brass"), frame(hc + V(0.25, 0.9 * math.cos(a), 0.9 * math.sin(a)), out=(1, 0, 0))))
    b.add("Beam", place(cyl(0.05, piv.z - 0.05 - (W.z + 3.15), "SteelLight", 8), M(W + V(0, 0, 3.15))))
    # the crank: a brass flywheel on a bearing stand, the pitman rod up to the beam's front end
    F = V(1.75, -1.9, 2.05)
    b.add("Flywheel", place(spoked_gear(1.2, 9, 0.24, 0.16, 4, "Brass", "Copper"), frame(F, out=(1, 0, 0))))
    b.add("Crank", place(block((0.35, 0.7, F.z - 0.45), "Iron", corner=0.1, edge=0.05), M((F.x + 0.3, F.y, 0.45))))
    b.add("Crank", place(block((0.5, 0.9, 0.15), "Brass", corner=0.1, edge=0.04), M((F.x + 0.3, F.y, 0.45))))
    b.add("Crank", place(cyl(0.09, 0.6, "SteelLight", 10), frame(F + V(-0.2, 0, 0), out=(1, 0, 0))))
    pin = F + V(-0.22, 0, 0.75)
    b.add("Crank", beam_between(pin, V(piv.x + 0.25, -1.8, piv.z - 0.3), 0.14, swatch="Steel"))
    # the steam engine cylinder beside it, driving the crank
    E = V(3.0, -0.4, 1.3)
    b.add("Engine", place(cyl(0.48, 1.7, "Brass", 14), frame(E, out=(0, 1, 0))))
    for y in (0.15, 1.55):
        b.add("Engine", lp_ring(frame(E + V(0, y, 0), out=(0, 1, 0)), 0.5, 0.06, "Copper", segments=14))
    b.add("Engine", place(block((1.0, 1.9, 0.45), "PineDark", corner=0.08, edge=0.05), M((E.x, E.y + 0.85, 0.45))))
    b.add("Engine", beam_between(E, F + V(0.3, 0, 0.0), 0.08, swatch="SteelLight"))
    # the boiler: a vertical brass drum, a firebox door glowing, the chimney with bands and a cap
    Bo = V(-2.7, 1.7, 0.45)
    boiler = bmesh.new()
    lathe(boiler, [(0, 0), (1.0, 0), (1.05, 0.2), (1.05, 2.4), (0.85, 2.85), (0.5, 3.05), (0, 3.1)], 14, M(Bo))
    b.add("Boiler", [(boiler, "Brass", 0.0, False)])
    for z in (0.6, 1.6):
        b.add("Boiler", lp_ring(M(Bo + V(0, 0, z)), 1.06, 0.07, "Copper", segments=14))
        for k in range(3):
            a = k * math.pi / 4 - math.pi / 2
            b.add("Boiler", place(rivet(0.06, "Copper"), frame(Bo + V(1.08 * math.cos(a), 1.08 * math.sin(a), z + 0.16), out=(math.cos(a), math.sin(a), 0))))
    door = frame(Bo + V(0.15, -1.03, 0.5), out=(0, -1, 0))
    b.add("Boiler", place(block((0.75, 0.55, 0.06), "Iron", corner=0.06, edge=0.02), door @ M((0, 0.3, 0))))
    glow = bmesh.new()
    rounded_block(glow, (0.5, 0.2, 0.04), door @ M((0, 0.3, 0.07)), corner=0.04, edge=0.01, corner_seg=2, edge_seg=1)
    b.add("Firebox", [(glow, LAVA, 0.0, True)])
    b.add("Boiler", place(hinge(0.4, 0.04, 2, "SteelDark"), door @ M((-0.4, 0.3, 0.03), (0, 0, math.pi / 2))))
    b.add("Boiler", place(dial(0.25, "Cream", "Brass", "WarnRed", 0.8), frame(Bo + V(0.75, -0.75, 1.25), out=(0.7, -0.7, 0))))
    b.add("Chimney", pipe_between(Bo + V(0.2, 0.2, 2.9), Bo + V(0.2, 0.2, 7.6), 0.26, "Iron"))
    for z in (4.6, 6.6):
        b.add("Chimney", lp_ring(M(Bo + V(0.2, 0.2, z)), 0.28, 0.05, "Brass", segments=12))
    cap = bmesh.new()
    lathe(cap, [(0, 7.6), (0.38, 7.6), (0.44, 7.75), (0.3, 7.95), (0, 8.0)], 14, M(Bo + V(0.2, 0.2, 0)))
    b.add("Chimney", [(cap, "Copper", 0.0, False)])
    b.add("Boiler", place(cyl(0.1, 0.35, "Copper", 10), M(Bo + V(-0.4, -0.3, 3.0))))
    b.add("Boiler", place(cyl(0.16, 0.1, "Brass", 12), M(Bo + V(-0.4, -0.3, 3.35))))
    # the lava tank: a riveted copper drum with a sight glass and a gauge
    T = V(-2.7, -1.0, 0.45)
    tank = bmesh.new()
    lathe(tank, [(0, 0), (0.8, 0), (0.85, 0.15), (0.85, 1.8), (0.65, 2.1), (0, 2.2)], 14, M(T))
    b.add("Tank", [(tank, "Copper", 0.0, False)])
    for z in (0.4, 1.5):
        b.add("Tank", lp_ring(M(T + V(0, 0, z)), 0.86, 0.06, "Iron", segments=14))
    b.add("SightGlass", trim_strip(T + V(0.4, -0.76, 0.5), T + V(0.4, -0.76, 1.4), 0.14, LAVA, True))
    b.add("Tank", place(dial(0.2, "Cream", "Brass", "WarnRed", -0.3), frame(T + V(-0.35, -0.8, 1.0), out=(-0.4, -1, 0))))
    # brass pipes: pump to tank (lava), boiler to engine (steam), tank to the nozzle; valve wheels
    lava_pipe, _ = lp_hose([W + V(-0.42, 0, 1.8), W + V(-1.3, -0.2, 2.2), V(-1.5, 0.2, 2.6), T + V(0.3, 0.1, 2.3), T + V(0.1, 0, 2.15)], 0.13, "Brass", "Copper", "Copper", 1, per=4, segments=8)
    b.add("Pipes", lava_pipe)
    steam_pipe, _ = lp_hose([Bo + V(0.9, -0.45, 1.6), V(-0.8, 0.4, 1.2), V(0.8, 0.4, 0.95), V(2.2, 0.4, 1.0), E + V(-0.4, 0.6, 0.1)], 0.11, "Copper", "Brass", "Brass", 1, per=4, segments=8)
    b.add("Pipes", steam_pipe)
    # the nozzle turret: a swivel base, a brass yoke, the barrel aimed at the ice
    S = V(-1.0, -2.35, 0.45)
    D = V(0, -1, -0.45).normalized()
    N = V(-1.0, -2.55, 1.55)
    b.add("Turret", place(cyl(0.6, 0.3, "Iron", 14), M(S)))
    b.add("Turret", place(rivet_ring(0.48, 6, 0.05, "Brass"), M(S + V(0, 0, 0.3))))
    b.add("Turret", place(cyl(0.3, 0.6, "Brass", 12), M(S + V(0, 0, 0.3))))
    for sx in (-1, 1):
        b.add("Turret", place(block((0.12, 0.5, 0.75), "Brass", corner=0.05, edge=0.04), M(S + V(sx * 0.38, -0.15, 0.85))))
        b.add("Turret", place(bolt(0.07, "Iron"), frame(N + V(sx * 0.45, 0.35, -0.05), out=(sx, 0, 0))))
    work = frame(N, out=D)
    b.add("Nozzle", place(nozzle(2), work))
    out_pipe, pts = lp_hose([T + V(0.6, -0.55, 0.6), V(-1.6, -1.3, 0.9), V(-1.0, -1.5, 1.6), N - D * 0.6, N - D * 0.1], HOSE_R[2], "Rubber", "Brass", "Brass", 3, per=4, segments=8)
    b.add("Hose", out_pipe)
    atts = {"Work": work, "Lamp1": up_(T + V(0, 0, 2.2)), "Lamp2": up_(E + V(0, 1.2, 0.48)),
            "Gear1": frame((piv.x + 0.8, 0.4, 3.2), out=(1, 0, 0)), "Gear2": frame((piv.x - 0.8, 0.4, 3.2), out=(-1, 0, 0)),
            "Steam1": up_(Bo + V(0.2, 0.2, 8.0)), "Steam2": up_(Bo + V(-0.4, -0.3, 3.45)),
            "Hit": frame((N.x, -5.8, 0.3), out=(0, -1, 0.6)), "Trail": work, "Fountain": up_((3.0, 2.3, 0.45)),
            "NamePlate": frame((0.8, -3.4, 0.25), out=(0, -1, 0)), "Aura": up_((0, 0, 0.45)), "Top": up_(Bo + V(0.2, 0.2, 8.0))}
    lp_hose_atts(atts, pts)
    return atts


# ---------- tier 3: Frost-tech - crystal-cooled lava pipes ----------

def lp_crystal_pipe(b, role, p0, p1, r=0.17):
    """A lava pipe: a glowing lava core in white sleeves, cyan rings and a collar of cooling crystals."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    m = Matrix.Translation(p0) @ align_z(d)
    L = d.length
    b.add(role + "Lava", place(cyl(r * 0.8, L, LAVA, 10, bevel=0.0), m.copy()))
    for z0, z1 in ((0.0, 0.3 * L), (0.62 * L, L)):
        b.add(role, place(cyl(r, z1 - z0, "SnowWhite", 12), m @ M((0, 0, z0))))
        for z in (z0, z1):
            b.add(role + "Rings", lp_ring(m @ M((0, 0, z)), r * 1.05, 0.03, "AuroraCyan", True, 12))
    for k in range(5):
        a = k * 2 * math.pi / 5
        b.add(role + "Crystals", place(cut_crystal(0.42, 0.08, "CrystalCyan"), m @ M((0, 0, 0.46 * L)) @ frame((r * math.cos(a), r * math.sin(a), 0), out=(math.cos(a), math.sin(a), 0.4))))
    b.add(role, lp_ring(m @ M((0, 0, 0.46 * L)), r * 1.15, 0.05, "SteelLight", segments=12))


def lp_frosttech(b):
    b.add("Deck", block((10.0, 9.0, 0.8), "SnowWhite", corner=1.4, edge=0.3))
    b.add("Deck", place(block((9.0, 8.0, 0.3), "IceBlue", corner=1.1, edge=0.12), M((0, 0, 0.8))))
    for sx in (-1, 1):
        b.add("Deck", place(vent(1.5, 0.4, 5, "GlacierBlue", "SteelLight"), frame((sx * 3.0, -4.49, 0.42), out=(0, -1, 0))))
        b.add("Deck", place(inset_panel(1.6, 1.2, 0.05, "FrostLight", "GlacierBlue", True), M((sx * 2.4, -2.9, 1.1))))
        for sy in (-1, 1):
            b.add("Deck", place(bolt(0.1, "SteelLight", "GlacierBlue"), M((sx * 4.2, sy * 3.7, 1.1))))
    for p0, p1 in (((-3.6, -4.53, 0.42), (3.6, -4.53, 0.42)), ((-3.6, 4.53, 0.42), (3.6, 4.53, 0.42)),
                   ((-5.03, -2.6, 0.42), (-5.03, 2.6, 0.42)), ((5.03, -2.6, 0.42), (5.03, 2.6, 0.42))):
        b.add("DeckLights", trim_strip(p0, p1, 0.16, "AuroraCyan", True))
    b.add("DeckLights", trim_strip((-1.0, -4.55, 0.62), (1.0, -4.55, 0.62), 0.12, LAVA, True))
    # the reactor: a vented base, a glass column of lava in a white cage wound with a coolant coil
    R = V(0, 1.3, 1.1)
    b.add("ReactorBase", place(block((2.8, 2.8, 1.0), "SteelLight", corner=0.5, edge=0.15), M(R)))
    b.add("ReactorBase", place(block((2.9, 2.9, 0.1), "GlacierBlue", corner=0.52, edge=0.04), M(R + V(0, 0, 0.7))))
    b.add("ReactorBase", place(vent(1.4, 0.45, 4, "GlacierBlue", "SteelLight"), frame(R + V(0, -1.41, 0.45), out=(0, -1, 0))))
    b.add("ReactorCore", place(cyl(0.72, 4.6, LAVA, 16, bevel=0.0), M(R + V(0, 0, 1.0))))
    for k in range(5):
        a = k * 1.3
        bub = bmesh.new()
        blob(bub, R + V(0.62 * math.cos(a), 0.62 * math.sin(a), 1.5 + 0.8 * k), (0.15, 0.15, 0.15), 1)
        b.add("ReactorCore", [(bub, LAVA_HOT, 0.0, True)])
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        b.add("Reactor", place(block((0.28, 0.28, 4.6), "SnowWhite", corner=0.1, edge=0.06), M(R + V(0.86 * math.cos(a), 0.86 * math.sin(a), 1.0), (0, 0, a))))
    for z in (1.1, 3.3, 5.5):
        b.add("Reactor", place(cyl(1.08, 0.3, "SnowWhite", 18), M(R + V(0, 0, z))))
        b.add("ReactorCore", lp_ring(M(R + V(0, 0, z + 0.15)), 1.1, 0.04, "AuroraCyan", True, 18))
    helix = []
    for k in range(73):
        s = k / 72
        a = 2 * math.pi * 5 * s
        helix.append(R + V(0.85 * math.cos(a), 0.85 * math.sin(a), 1.45 + 3.9 * s))
    coil_bm = bmesh.new()
    sweep(coil_bm, helix, 0.07, 6)
    b.add("Reactor", [(coil_bm, "IceBlue", 0.0, False)])
    dome = bmesh.new()
    lathe(dome, [(0, 5.75), (1.1, 5.75), (1.0, 6.1), (0.7, 6.45), (0, 6.55)], 18, M((R.x, R.y, R.z)))
    b.add("Reactor", [(dome, "SnowWhite", 0.0, False)])
    b.add("ReactorCrystals", place(cut_crystal_cluster(1.15, "CrystalCyan", "SteelLight", 6), M(R + V(0, 0, 6.45))))
    # the cooling towers: white housings with frost fins, a screen, and a big crystal in a setting on top
    for sx in (-1, 1):
        X = V(sx * 3.3, 1.4, 1.1)
        role = "Tower" + ("A" if sx < 0 else "B")
        b.add(role, place(block((1.7, 1.7, 3.4), "SnowWhite", corner=0.6, edge=0.3), M(X)))
        for k in range(5):
            b.add(role, place(block((1.85, 1.85, 0.1), "GlacierBlue", corner=0.65, edge=0.03), M(X + V(0, 0, 1.2 + 0.4 * k))))
        b.add(role, place(screen(0.8, 0.45, "AuroraCyan", "NavyIce", 3), frame(X + V(0, -0.86, 0.6), out=(0, -1, 0))))
        b.add(role, place(cyl(0.6, 0.25, "SteelLight", 12), M(X + V(0, 0, 3.4))))
        b.add(role, place(gem_setting(0.32, "CrystalCyan", "SteelLight", 6), M(X + V(0, 0, 3.65))))
        b.add(role + "Crystal", place(cut_crystal(1.5, 0.3, "CrystalCyan"), M(X + V(0, 0, 3.9))))
        coolant, _ = lp_hose([X + V(-sx * 0.86, -0.3, 2.6), V(sx * 1.6, 1.0, 3.6), R + V(sx * 1.0, -0.2, 3.6)], 0.14, "SteelLight", "GlacierBlue", "AuroraCyan", 2)
        b.add("Cables", coolant)
        b.add("Cables", cable(X + V(-sx * 0.5, 0.86, 0.8), R + V(sx * 0.9, 1.0, 0.4), 0.3, 0.09, "NavyIce", "GlacierBlue"))
    # crystal-cooled lava pipes from the reactor down to the nozzle turret
    for sx in (-1, 1):
        lp_crystal_pipe(b, "LavaPipe" + ("A" if sx < 0 else "B"), R + V(sx * 0.55, -0.9, 1.7), V(sx * 0.5, -1.65, 1.55))
    # the nozzle turret: a turntable, a white housing, the finned white barrel aimed at the ice
    S = V(0, -2.2, 1.1)
    D = V(0, -1, -0.35).normalized()
    N = V(0, -2.95, 2.05)
    b.add("Turret", place(cyl(0.95, 0.3, "SteelLight", 18), M(S)))
    b.add("TurretRing", lp_ring(M(S + V(0, 0, 0.32)), 0.85, 0.04, "AuroraCyan", True, 18))
    b.add("Turret", place(block((1.6, 1.5, 1.1), "SnowWhite", corner=0.5, edge=0.25), M(S + V(0, 0, 0.3))))
    b.add("Turret", place(block((1.66, 1.56, 0.08), "GlacierBlue", corner=0.52, edge=0.03), M(S + V(0, 0, 0.95))))
    b.add("Turret", place(dial(0.2, "FrostLight", "SteelLight", "WarnRed", 0.5), frame(S + V(0.81, 0, 0.85), out=(1, 0, 0))))
    work = frame(N, out=D)
    b.add("Nozzle", place(nozzle(3), work))
    feed, pts = lp_hose([R + V(0, -1.3, 0.9), V(0, -0.5, 3.3), V(0, -1.3, 3.4), V(0, -1.95, 2.55)], HOSE_R[3], "SteelLight", "GlacierBlue", "AuroraCyan", 3)
    b.add("Hose", feed)
    atts = {"Work": work, "Lamp1": up_((-4.1, -3.6, 1.1)), "Lamp2": up_((4.1, -3.6, 1.1)),
            "Gear1": frame((-4.15, 1.4, 2.8), out=(-1, 0, 0)), "Gear2": frame((4.15, 1.4, 2.8), out=(1, 0, 0)),
            "Steam1": up_((-3.3, 2.0, 4.6)), "Steam2": up_((3.3, 2.0, 4.6)),
            "Hit": frame((0, -6.2, 0.3), out=(0, -1, 0.6)), "Trail": work, "Fountain": up_((2.7, -2.7, 1.1)),
            "NamePlate": frame((0, -4.55, 0.35), out=(0, -1, 0)), "Aura": up_((0, 0, 1.1)), "Top": up_(R + V(0, 0, 8.3))}
    lp_hose_atts(atts, pts)
    return atts


# ---------- tier 4: Enchanted - volcano altar with floating lava orbs ----------

def lp_orb(radius, ring_swatch="Gold", tilt=(0.4, 0.2, 0)):
    """A floating lava orb in two crossed gold rings with a gem: centred on the origin."""
    pieces = []
    orb = bmesh.new()
    blob(orb, (0, 0, 0), (radius, radius, radius), 2)
    pieces.append((orb, LAVA, 0.0, True))
    core = bmesh.new()
    blob(core, (radius * 0.3, -radius * 0.35, radius * 0.3), (radius * 0.4,) * 3, 1)
    pieces.append((core, LAVA_HOT, 0.0, True))
    for k in range(2):
        pieces += lp_ring(M((0, 0, 0), (tilt[0] + k * math.pi / 2, tilt[1], k * 0.8)), radius * 1.25, radius * 0.07, ring_swatch, segments=20)
    pieces += place(cut_gem(radius * 0.22, "MagicPink"), M((0, 0, radius * 1.45)))
    return pieces


def lp_enchanted(b):
    dais = bmesh.new()
    lathe(dais, [(0, 0), (5.0, 0), (5.0, 0.3), (4.8, 0.35), (4.8, 0.55), (4.55, 0.8), (0, 0.8)], 6)
    b.add("Dais", [(dais, "Moonstone", 0.04, False)])
    plinth = bmesh.new()
    lathe(plinth, [(0, -0.01), (5.15, -0.01), (5.15, 0.18), (0, 0.18)], 6)
    b.add("Dais", [(plinth, "StoneDark", 0.03, False)])
    b.add("Dais", place(trim_ring(4.67, 0, "RuneViolet", minor=0.08, segments=6), M((0, 0, 0.56))))
    b.add("DaisRunes", place(engraved_rune_ring(3.7, "RuneGlow", "ArcaneDeep", "RuneViolet", 16), M((0, 0, 0.8))))
    for k in range(6):
        a = k * math.pi / 3
        b.add("DaisCrystals", place(cut_crystal_cluster(0.55, LAVA if k % 2 else "RuneViolet", "StoneDark", 4), M((4.5 * math.cos(a), 4.5 * math.sin(a), 0.78), (0, 0, a))))
        fa = a + math.pi / 6
        ap = 5.0 * math.cos(math.pi / 6)
        b.add("Dais", place(gem_setting(0.15, LAVA_HOT, "Gold", 4), frame((ap * math.cos(fa), ap * math.sin(fa), 0.18), out=(math.cos(fa), math.sin(fa), 0))))
    # the altar: a stepped hexagonal base and a little volcano with a lava crater and runnels
    A = V(0, 0.7, 0.8)
    step = bmesh.new()
    lathe(step, [(0, 0), (2.4, 0), (2.4, 0.45), (2.25, 0.5), (1.9, 0.5), (1.9, 1.0), (0, 1.0)], 6, M(A, (0, 0, math.pi / 6)))
    b.add("Altar", [(step, "Moonstone", 0.04, False)])
    b.add("Altar", place(trim_ring(2.42, 0.25, "Gold", minor=0.06, segments=6), M(A, (0, 0, math.pi / 6))))
    for k in range(6):
        a = k * math.pi / 3
        b.add("Altar", place(rune_glyph(0.4, k, "RuneGlow", 0.04), frame(A + V(1.92 * math.cos(a), 1.92 * math.sin(a), 0.75), out=(math.cos(a), math.sin(a), 0))))
    prof = [(0, 1.0), (1.75, 1.0), (1.55, 1.7), (1.1, 2.8), (0.8, 3.5), (0.62, 3.62), (0.48, 3.4), (0, 3.35)]
    cone = bmesh.new()
    lathe(cone, prof, 16, M(A))
    for v in cone.verts:
        r = math.hypot(v.co.x - A.x, v.co.y - A.y)
        if 0.3 < r and 1.1 < v.co.z - A.z < 3.5:
            v.co.x = A.x + (v.co.x - A.x) * (1 + 0.06 * lp_noise(v.co.x, v.co.y, v.co.z, 2))
            v.co.y = A.y + (v.co.y - A.y) * (1 + 0.06 * lp_noise(v.co.x, v.co.y, v.co.z, 2))
    b.add("Volcano", [(subsurf(cone, 1), "StoneDark", 0.0, False)], organic=True)
    b.add("Volcano", place(trim_ring(1.62, 0, "Gold", minor=0.08, segments=16), M(A + V(0, 0, 1.35))))
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        b.add("Volcano", place(gem_setting(0.1, "MagicPink" if k % 2 else LAVA_HOT, "Gold", 4), frame(A + V(1.66 * math.cos(a), 1.66 * math.sin(a), 1.35), out=(math.cos(a), math.sin(a), 0))))
    b.add("VolcanoLava", place(lp_pool(0.5, 14, 2, 0.7), M(A + V(0, 0, 3.4))))
    for k, a in enumerate((0.9, 2.3, 3.7, 5.2)):
        pts = []
        for z, r in ((3.55, 0.7), (3.0, 0.98), (2.4, 1.28), (1.85, 1.52), (1.4, 1.64)):
            aa = a + 0.12 * math.sin(z * 3 + k)
            pts.append(A + V((r + 0.04) * math.cos(aa), (r + 0.04) * math.sin(aa), z))
        b.add("VolcanoLava", lp_stream(pts, 0.11, 0.06))
    # the great lava orb over the crater in a turning rune ring, and smaller orbs orbiting the altar
    G = A + V(0, 0, 5.9)
    b.add("GreatOrb", place(lp_orb(0.75), M(G)))
    b.add("OrbRing", place(engraved_rune_ring(1.45, "RuneGlow", "ArcaneDeep", "Gold", 10), M(G, (0.35, 0.15, 0))))
    for k in range(4):
        a = k * math.pi / 2 + 0.75
        p = V(3.0 * math.cos(a), 0.4 + 3.0 * math.sin(a), 3.0 + 0.9 * (k % 2))
        b.add("Orbs", place(lp_orb(0.36, "Gold", (0.3 * k, 0.5, 0)), M(p)))
    # floating islands: two with crystals (lamps sit on them), a high one with the crowning gem
    for sx, top, role in ((-1, 6.4, "IslandA"), (1, 7.4, "IslandB")):
        isl = M((sx * 3.1, 1.6, top), (0, 0, top))
        b.add(role, place(floating_platform(1.25, 0.4, "Moonstone", "StoneDark", "Gold", LAVA, tip=False), isl))
        b.add(role, place(trim_ring(0.9, 0.03, "Gold", minor=0.04, segments=6), isl))
        for k in range(3):
            a = k * 2 * math.pi / 3 + 0.4
            hang = cut_crystal(0.55, 0.12, "RuneViolet", sides=6)
            b.add(role + "Crystals", place(hang, isl @ Matrix.Translation((0.55 * math.cos(a), 0.55 * math.sin(a), -0.75)) @ Matrix.Rotation(math.pi, 4, "X")))
        b.add(role, lp_rock((sx * 3.1, 1.6, top - 1.15), (0.5, 0.5, 0.45), "StoneDark", 3 + sx))
    crown = M((0, 0.9, 9.4), (0, 0, 0.5))
    b.add("Crown", place(floating_platform(1.0, 0.35, "Moonstone", "StoneDark", "Gold", LAVA, tip=True), crown))
    b.add("Crown", place(gem_setting(0.38, LAVA, "Gold", 6), crown))
    b.add("Crown", lp_ring(M((0, 0.9, 10.15), (math.pi / 2, 0, 0.4)), 0.7, 0.04, "Gold", segments=24))
    for k in range(4):  # floating rune stones round the dais
        a = k * math.pi / 2 + 1.2
        stone = subsurf(cage_box((0.5, 0.35, 0.6), 1), 1)
        stone.transform(M((3.9 * math.cos(a), 3.9 * math.sin(a), 2.0 + 0.4 * (k % 2)), (0.2, 0.1, a)))
        b.add("RuneStones", [(stone, "StoneDark", 0.0, False)])
        b.add("RuneStones", place(rune_glyph(0.34, k + 2, "RuneGlow", 0.03), frame((3.9 * math.cos(a), 3.9 * math.sin(a), 2.0 + 0.4 * (k % 2)), out=(math.cos(a), math.sin(a), 0)) @ M((0, 0, 0.17))))
    # the floating moonstone horn spraying lava, fed by a chain of floating lava drops from the crater
    D = V(0, -1, -0.62).normalized()
    N = V(0, -2.85, 3.9)
    work = frame(N, out=D)
    big = work @ Matrix.Scale(NOZ_SCALE[4], 4)
    b.add("Horn", place(nozzle(4), big))
    b.add("HornRing", place(engraved_rune_ring(0.75, "RuneGlow", "ArcaneDeep", "Gold", 8), big @ M((0, 0, 0.35))))
    arc = lp_spline([A + V(0, -0.2, 3.9), A + V(0, -1.4, 4.9), N - D * 1.0 + V(0, 0, 0.4), N - D * 0.5], 4)
    pts = arc
    for k, p in enumerate(arc[1:-1:2]):
        drop = bmesh.new()
        r = 0.2 - 0.012 * k
        blob(drop, p, (r, r, r * 1.15), 1)
        b.add("LavaDrops", [(drop, LAVA, 0.0, True)])
    atts = {"Work": work, "Lamp1": up_((-3.1, 1.6, 6.45)), "Lamp2": up_((3.1, 1.6, 7.45)),
            "Gear1": frame((-2.6, -0.3, 2.6), out=(-1, 0, 0)), "Gear2": frame((2.6, -0.3, 2.6), out=(1, 0, 0)),
            "Steam1": up_(A + V(0, 0, 3.6)), "Steam2": up_((0, 0.9, 10.3)),
            "Hit": frame((0, -6.0, 0.3), out=(0, -1, 0.6)), "Trail": work, "Fountain": up_((2.4, -2.9, 0.8)),
            "NamePlate": frame((0, -4.37, 0.4), out=(0, -1, 0)), "Aura": up_((0, 0, 0.8)), "Top": up_((0, 0.9, 10.9))}
    lp_hose_atts(atts, pts)
    return atts


# ---------- tier 5: Legendary - the Volcano Forge ----------

VC = V(0, 0.9, 0)  # the volcano's axis
VOLCANO_PROFILE = [(0, 1.15), (4.75, 1.15), (4.65, 1.5), (4.15, 2.4), (3.55, 3.6), (3.1, 5.0), (2.75, 6.6), (2.45, 8.2),
                   (2.2, 9.5), (2.05, 10.25), (1.8, 10.55), (1.5, 10.45), (1.28, 9.95), (0.0, 9.8)]


def vol_r(z):
    """The volcano's outside radius at height z (the profile, before the noise)."""
    outer = VOLCANO_PROFILE[1:-3]
    for (r0, z0), (r1, z1) in zip(outer, outer[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return outer[-1][0]


def vol_point(a, z, lift=0.0):
    """A point on the volcano's skin at angle a (0 = +X, -90 deg = the face) and height z, and its normal."""
    r = vol_r(z) - 0.06 + lift
    slope = (vol_r(z + 0.1) - vol_r(z - 0.1)) / 0.2
    n = V(math.cos(a), math.sin(a), -slope).normalized()
    return VC + V(r * math.cos(a), r * math.sin(a), z), n


def vol_face(x, z, lift=0.0):
    """A point on the front of the volcano at x, height z, and the outward normal there."""
    r = vol_r(z)
    a = -math.pi / 2 + math.asin(max(-0.95, min(0.95, x / r)))
    return vol_point(a, z, lift)


def lp_heart():
    """A glowing lava heart, centred, facing +Z (+Y up)."""
    pieces = []
    for sx in (-1, 1):
        lobe = bmesh.new()
        blob(lobe, (sx * 0.3, 0.15, 0), (0.38, 0.38, 0.26), 2)
        pieces.append((lobe, LAVA, 0.0, True))
    tip = bmesh.new()
    lathe(tip, [(0, 0.0), (0.6, 0.0), (0.0, 0.85)], 12, Matrix.Translation((0, 0.1, 0)) @ Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Diagonal((1, 0.45, 1, 1)))
    pieces.append((tip, LAVA, 0.0, True))
    core = bmesh.new()
    blob(core, (0, 0.0, 0.18), (0.25, 0.25, 0.18), 1)
    pieces.append((core, LAVA_HOT, 0.0, True))
    return pieces


def lp_legendary(b):
    # the forge floor: a dark plinth with gold trim, vents, aurora strips and lava cracks
    b.add("Plinth", block((11.6, 11.6, 0.9), "Gunmetal", corner=1.2, edge=0.25))
    b.add("Plinth", place(block((11.0, 11.0, 0.3), "StoneDark", corner=1.0, edge=0.1), M((0, 0, 0.9))))
    b.add("Trim", place(block((11.7, 11.7, 0.16), "Gold", corner=1.22, edge=0.06), M((0, 0, 0.72))))
    for sx in (-1, 1):
        b.add("Plinth", place(vent(1.8, 0.4, 5, "Gunmetal", "SteelDark"), frame((sx * 3.4, -5.79, 0.42), out=(0, -1, 0))))
        b.add("TrimLights", trim_strip((sx * 5.83, -2.6, 0.4), (sx * 5.83, 2.6, 0.4), 0.14, "AuroraGreen", True))
    b.add("TrimLights", trim_strip((-2.0, -5.83, 0.4), (2.0, -5.83, 0.4), 0.14, "AuroraGreen", True))
    for k, (p0, p1, p2) in enumerate((((-1.2, -4.0), (-2.2, -4.8), (-2.6, -5.3)), ((1.3, -3.7), (2.0, -4.3), (1.8, -5.1)),
                                       ((-4.0, -2.0), (-4.7, -2.9), (-5.2, -3.1)), ((4.3, 3.4), (4.9, 4.2), (5.2, 4.3)))):
        b.add("LavaCracks", lp_stream([(p0[0], p0[1], 1.2), (p1[0], p1[1], 1.21), (p2[0], p2[1], 1.2)], 0.07, 0.03, segments=6))
    # the volcano: a rocky cone (organic), a crater of lava, lava running down its sides, rock ledges
    cone = bmesh.new()
    lathe(cone, VOLCANO_PROFILE, 32, M(VC))
    for v in cone.verts:
        d = V(v.co.x - VC.x, v.co.y - VC.y, 0)
        if d.length > 0.5 and 1.6 < v.co.z < 10.3:
            front_face = max(0.0, -d.normalized().y - 0.55) * 2.2  # keep the face smooth
            a = math.atan2(d.y, d.x)
            bump = 0.3 * lp_noise(v.co.x * 0.6, v.co.y * 0.6, v.co.z * 0.55, 4) + 0.22 * math.sin(7 * a + 0.8 * v.co.z) * min(1.0, (v.co.z - 1.6) / 2.0)
            v.co += d.normalized() * bump * (1 - min(1.0, front_face))
    b.add("Volcano", [(subsurf(cone, 1), "StoneDark", 0.0, False)], organic=True)
    b.add("CraterLava", place(lp_pool(1.4, 18, 4, 0.2), M(VC + V(0, 0, 9.85))))
    for k, a in enumerate((0.35, 1.25, 2.2, 2.9, 3.7, 5.55)):
        pts = []
        for z in (10.35, 9.4, 8.3, 7.0, 5.8, 4.6 - 0.5 * (k % 2)):
            p, _ = vol_point(a + 0.1 * math.sin(z * 2 + k), z, 0.1)
            pts.append(p)
        b.add("LavaFlows", lp_stream(pts, 0.2, 0.1, segments=6))
        b.add("LavaFlows", lp_stream([p + (p - VC - V(0, 0, p.z)).normalized() * 0.14 for p in pts[:4]], 0.08, 0.04, LAVA_HOT, segments=6))
    for k in range(9):
        a = k * 2 * math.pi / 9 + 0.5
        if -2.1 < a - 2 * math.pi < -1.0 or -2.1 < a < -1.0:
            continue
        p, n = vol_point(a, 1.6 + 0.35 * (k % 3), 0.1)
        b.add("Ledges", lp_rock(p, (0.7, 0.55, 0.45), "Stone" if k % 2 else "StoneDark", k, floor=1.2))
    for k, (a, z, s) in enumerate(((-0.4, 5.6, 0.6), (0.6, 7.6, 0.5), (1.4, 4.4, 0.7), (2.0, 7.0, 0.55), (2.8, 5.2, 0.65),
                                   (3.4, 8.0, 0.45), (4.0, 3.4, 0.6), (-2.5, 2.4, 0.5), (-0.75, 2.6, 0.55))):  # boulders on the flanks
        p, n = vol_point(a, z, -0.1)
        b.add("Boulders", lp_rock(p, (s * 1.2, s, s * 0.75), "Gunmetal" if k % 3 == 0 else "StoneDark", k + 20, sub=2))
    for k in range(16):  # basalt columns round the foot, leaving the face and the hose clear
        a = math.pi / 2 + (k - 7.5) * 0.3
        h = 0.8 + 0.55 * ((k * 7) % 4)
        p = VC + V(4.5 * math.cos(a), 4.5 * math.sin(a), 1.1)
        if p.y > 5.6:
            p.y = 5.6
        col = bmesh.new()
        lathe(col, [(0, 0), (0.42, 0), (0.42, h), (0.3, h + 0.08), (0, h + 0.08)], 6, M(p, (0, 0, k)))
        b.add("Basalt", [(faceted(col), "Gunmetal" if k % 2 else "StoneDark", 0.0, False)])
    for k, (a, z) in enumerate(((-0.9, 2.2), (-2.3, 2.0), (0.3, 3.8), (2.4, 3.0), (-2.6, 6.2))):  # glowing cracks in the rock
        pts = []
        for i in range(4):
            q, _ = vol_point(a + 0.12 * (i % 2) - 0.06, z + 0.45 * i, 0.02)
            pts.append(q)
        b.add("LavaCracks", lp_stream(pts, 0.08, 0.03, LAVA, per=2, segments=6))
    # the crown on the crater rim: a gold band, obsidian and gold spikes, lava gems
    rim_z = 10.3
    b.add("Crown", lp_ring(M(VC + V(0, 0, rim_z - 0.15)), 2.02, 0.17, "Gold", segments=26, minor_segments=6))
    b.add("Crown", lp_ring(M(VC + V(0, 0, rim_z + 0.2)), 1.92, 0.08, "Gold", segments=26))
    for k in range(10):
        a = k * 2 * math.pi / 10 - math.pi / 2
        base = VC + V(1.95 * math.cos(a), 1.95 * math.sin(a), rim_z)
        out_d = V(math.cos(a) * 0.35, math.sin(a) * 0.35, 1)
        if k % 2 == 0:
            tall = 1.6 if k == 0 else 1.2
            b.add("CrownSpikes", place(cut_crystal(tall, 0.26, "Gunmetal", glow=False, sides=5), Matrix.Translation(base) @ align_z(out_d)))
        else:
            spike = bmesh.new()
            lathe(spike, [(0, 0), (0.2, 0), (0.17, 0.35), (0.06, 0.8), (0, 0.9)], 8, Matrix.Translation(base) @ align_z(out_d))
            b.add("CrownSpikes", [(spike, "Gold", 0.0, False)])
    for k in range(5):
        a = -math.pi / 2 + (k - 2) * 0.62
        b.add("Crown", place(gem_setting(0.14 if k != 2 else 0.2, LAVA if k != 2 else "MagicPink", "Gold", 4),
                             frame(VC + V(2.2 * math.cos(a), 2.2 * math.sin(a), rim_z - 0.15), out=(math.cos(a), math.sin(a), 0.1))))
    # the face: glowing eyes in iron-rimmed sockets, heavy rock brows, a wide grin full of lava
    for sx in (-1, 1):
        p, n = vol_face(sx * 1.05, 7.25, 0.0)
        eye_at = frame(p, out=n)
        b.add("Face", lp_ring(eye_at @ M((0, 0, 0.06)), 0.72, 0.13, "Gunmetal", segments=20))
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            b.add("Face", place(rivet(0.07, "Gold"), eye_at @ M((0.72 * math.cos(a), 0.72 * math.sin(a), 0.16))))
        b.add("Eyes", place(cartoon_eye(0.62, LAVA_HOT, look=(-sx * 0.05, -0.08), lid=None), eye_at))
        bp, bn = vol_face(sx * 1.1, 8.25, 0.05)
        brow_bm = subsurf(cage_box((1.35, 0.4, 0.34), 0), 2)
        brow_bm.transform(frame(bp, out=bn) @ M((0, 0, 0.12), (0, 0, sx * 0.22)))
        b.add("Face", [(brow_bm, "Gunmetal", 0.0, False)], organic=True)
    mp, mn = vol_face(0, 5.45, 0.0)
    mouth_at = frame(mp, out=mn)
    cavity = bmesh.new()
    blob(cavity, (0, 0, 0.02), (1.25, 0.55, 0.22), 2)
    for v in cavity.verts:  # a smile: the corners lifted
        v.co.y += 0.22 * (v.co.x / 1.25) ** 2
    cavity.transform(mouth_at)
    b.add("Mouth", [(cavity, "EyeDark", 0.0, False)])
    tongue = bmesh.new()
    blob(tongue, (0, -0.15, 0.1), (0.95, 0.3, 0.18), 2)
    for v in tongue.verts:
        v.co.y += 0.2 * (v.co.x / 0.95) ** 2
    tongue.transform(mouth_at)
    b.add("MouthLava", [(tongue, LAVA, 0.0, True)])
    lip = bmesh.new()
    sweep(lip, [mouth_at @ V(1.35 * (t / 8 - 0.5) * 2, 0.5 + 0.3 * (2 * t / 8 - 1) ** 2, 0.1) for t in range(9)], 0.17, 10)
    b.add("Mouth", [(lip, "StoneDark", 0.0, False)])
    for k in (-1, 1):
        fang = cut_crystal(0.42, 0.13, "StoneLight", glow=False, sides=5)
        b.add("Mouth", place(fang, mouth_at @ Matrix.Translation((k * 0.55, 0.42, 0.18)) @ Matrix.Rotation(math.pi / 2 + 0.15, 4, "X")))
    # the lava heart in its forge cage, under the grin
    hp, hn = vol_face(0, 3.15, 0.0)
    cage_at = frame(hp, out=hn)
    b.add("Cage", place(cyl(1.05, 0.25, "Iron", 18), cage_at @ M((0, 0, -0.1))))
    b.add("Cage", lp_ring(cage_at @ M((0, 0, 0.15)), 1.05, 0.12, "Gold", segments=20))
    b.add("Cage", place(bolt_ring(1.05, 8, 0.07, "Iron"), cage_at @ M((0, 0, 0.27))))
    b.add("LavaHeart", place(lp_heart(), cage_at @ M((0, 0, 0.55))))
    for k in range(4):
        x = (k - 1.5) * 0.46
        h = math.sqrt(max(0.0, 1.0 - x * x))
        bar = bmesh.new()
        sweep(bar, [cage_at @ V(x, -h * 0.95, 0.15), cage_at @ V(x, -h * 0.6, 0.95), cage_at @ V(x, 0, 1.15), cage_at @ V(x, h * 0.6, 0.95), cage_at @ V(x, h * 0.95, 0.15)], 0.05, 8)
        b.add("Cage", [(bar, "Iron", 0.0, False)])
    b.add("Cage", lp_ring(cage_at @ M((0, 0, 0.98)), 0.62, 0.05, "Gold", segments=16))
    # pistons from the floor to the volcano's flanks, with gold mounts
    for sx in (-1, 1):
        a = math.pi / 2 - sx * 1.05
        top, n = vol_point(a, 6.0, 0.15)
        foot = VC + V(sx * 4.8, 1.8, 1.2)
        b.add("Pistons", piston(foot, top, 0.3, "Gunmetal", "SteelLight"))
        b.add("Pistons", place(block((0.9, 0.9, 0.3), "Gold", corner=0.15, edge=0.06), M(foot + V(0, 0, -0.05))))
        b.add("Pistons", place(cyl(0.45, 0.25, "Gold", 14), frame(top, out=n)))
    # the smoke stacks up the back, with bands and flared tips
    for sx in (-1, 1):
        a0 = math.pi / 2 + sx * 0.45
        lo, _ = vol_point(a0, 1.9, 0.4)
        hi, _ = vol_point(a0 - sx * 0.1, 8.9, 0.4)
        b.add("Stacks", pipe_between(lo, hi, 0.32, "Gunmetal"))
        for f in (0.35, 0.7):
            p = lo.lerp(hi, f)
            b.add("Stacks", lp_ring(Matrix.Translation(p) @ align_z(hi - lo), 0.36, 0.06, "Gold", segments=14))
        flare = bmesh.new()
        lathe(flare, [(0.25, -0.1), (0.36, 0.0), (0.5, 0.4), (0.42, 0.45), (0.26, 0.1)], 14, Matrix.Translation(hi) @ align_z(hi - lo))
        b.add("Stacks", [(flare, "Iron", 0.0, False)])
    # the bellows at the back left, puffing air into the forge through a copper pipe
    Bw = V(-4.3, 3.5, 1.2)
    for s in (-1, 1):
        board = bmesh.new()
        rounded_block(board, (1.5, 2.0, 0.12), M(Bw + V(0, 0, 0.75 + s * 0.42), (s * 0.22, 0, 0)), corner=0.45, edge=0.05, corner_seg=2, edge_seg=1, taper=1.0)
        b.add("Bellows", [(board, "PineDark", 0.0, False)])
    for k in range(3):
        fold = bmesh.new()
        rounded_block(fold, (1.35, 1.7 - 0.3 * k, 0.14), M(Bw + V(0, 0.15 * k - 0.1, 0.55 + 0.2 * k)), corner=0.35, edge=0.06, corner_seg=2, edge_seg=1)
        b.add("Bellows", [(fold, "Rubber", 0.0, False)])
    b.add("Bellows", place(block((1.6, 0.6, 0.3), "Iron", corner=0.1, edge=0.05), M(Bw + V(0, -0.9, 0.0))))
    b.add("Bellows", place(handle(0.7, 0.4, 0.06, "Gold", "Iron"), frame(Bw + V(0, 1.05, 1.2), out=(0, 1, 0.4))))
    nozzle_from = Bw + V(0, -1.2, 0.75)
    pipe_to, _ = vol_point(math.pi * 0.83, 2.6, -0.1)
    bel, _ = lp_hose([nozzle_from, nozzle_from + V(0.3, -0.5, 0.5), pipe_to], 0.16, "Copper", "Gold", "Gold", 1)
    b.add("Bellows", bel)
    # the anvil on a stump at the front left, a glowing ingot on it, a hammer leaning on the stump
    Av = V(-3.9, -4.2, 1.2)
    b.add("Anvil", place(cyl(0.7, 0.75, "PineDark", 14), M(Av)))
    b.add("Anvil", lp_ring(M(Av + V(0, 0, 0.6)), 0.71, 0.05, "Iron", segments=14))
    b.add("Anvil", place(block((0.7, 0.55, 0.25), "Iron", corner=0.06, edge=0.04), M(Av + V(0, 0, 0.75))))
    b.add("Anvil", place(block((0.4, 0.35, 0.35), "Iron", corner=0.04, edge=0.03), M(Av + V(0, 0, 0.98))))
    b.add("Anvil", place(block((1.1, 0.5, 0.3), "Gunmetal", corner=0.08, edge=0.05), M(Av + V(0.05, 0, 1.3))))
    horn = bmesh.new()
    lathe(horn, [(0, 0), (0.22, 0), (0.0, 0.65)], 10, frame(Av + V(0.58, 0, 1.47), out=(1, 0, 0.1)))
    b.add("Anvil", [(horn, "Gunmetal", 0.0, False)])
    ingot = bmesh.new()
    rounded_block(ingot, (0.5, 0.2, 0.12), M(Av + V(-0.1, 0, 1.66)), corner=0.05, edge=0.03, corner_seg=2, edge_seg=1)
    b.add("Ingot", [(ingot, LAVA, 0.0, True)])
    b.add("Anvil", beam_between(Av + V(-0.6, -0.55, 0.0), Av + V(-0.68, -0.05, 1.05), 0.1, swatch="PineLight"))
    b.add("Anvil", place(block((0.45, 0.25, 0.25), "Iron", corner=0.05, edge=0.03), Matrix.Translation(Av + V(-0.68, -0.05, 1.05)) @ align_z(V(-0.08, 0.5, 1.05))))
    # the gauge manifold at the right: a gold-trimmed box, two dials, pipes into the volcano
    Mf = V(5.0, -0.6, 1.2)
    b.add("Manifold", place(block((0.9, 1.6, 1.3), "Gunmetal", corner=0.15, edge=0.08), M(Mf)))
    b.add("Manifold", place(block((0.98, 1.68, 0.1), "Gold", corner=0.17, edge=0.03), M(Mf + V(0, 0, 1.25))))
    for k, y in enumerate((-0.4, 0.4)):
        b.add("Manifold", place(dial(0.28, "Cream", "Gold", "WarnRed", 0.6 - k), frame(Mf + V(0.46, y, 0.8), out=(1, 0, 0))))
    for z in (0.5, 1.05):
        to, _ = vol_point(-0.1, z + 2.2, -0.1)
        b.add("Manifold", pipe_between(Mf + V(-0.4, 0.3, z + 0.1), to, 0.14, "Brass"))
    # the lava hose: from a gold port on the right flank to the big nozzle on an arm at the front right
    port, pn = vol_point(-0.62, 3.4, 0.0)
    b.add("Port", place(cyl(0.5, 0.35, "Gold", 16), frame(port, out=pn)))
    b.add("Port", place(bolt_ring(0.42, 6, 0.06, "Iron"), frame(port + pn * 0.35, out=pn)))
    Ar = V(3.7, -4.0, 1.2)
    D = V(0, -1, -0.5).normalized()
    N = V(3.5, -4.5, 3.5)
    b.add("Arm", place(cyl(0.6, 0.3, "Gold", 16), M(Ar)))
    b.add("Arm", place(cyl(0.35, 1.6, "Gunmetal", 14), M(Ar + V(0, 0, 0.3))))
    b.add("Arm", piston(Ar + V(0, 0, 1.6), N + V(0, 0.35, -0.55), 0.22, "Gunmetal", "SteelLight"))
    joint = bmesh.new()
    blob(joint, N + V(0, 0.35, -0.55), (0.35, 0.35, 0.35), 2)
    b.add("Arm", [(joint, "Gold", 0.0, False)])
    work = frame(N, out=D)
    b.add("Nozzle", place(nozzle(5), work))
    hose, pts = lp_hose([port + pn * 0.3, port + pn * 1.0 + V(0, 0, -0.4), V(4.6, -3.0, 3.4), N - D * 0.9 + V(0, 0, 0.25), N - D * 0.12],
                        HOSE_R[5], "Rubber", "Gold", "Gold", 6)
    b.add("Hose", hose)
    atts = {"Work": work, "Lamp1": up_((-5.0, -5.0, 1.2)), "Lamp2": up_((5.0, -5.0, 1.2)),
            "Gear1": frame(vol_face(-3.1, 5.4, 0.0)[0], out=(-1, -0.4, 0.2)),
            "Gear2": frame(vol_face(3.1, 5.4, 0.0)[0], out=(1, -0.4, 0.2)),
            "Steam1": None, "Steam2": None,
            "Hit": frame((N.x, -6.5, 0.3), out=(0, -1, 0.6)), "Trail": work, "Fountain": up_(VC + V(0, 0, 9.95)),
            "Crown": up_(VC + V(0, 0, rim_z + 0.2)), "Eyes": frame(vol_face(0, 7.25)[0], out=vol_face(0, 7.25)[1]),
            "NamePlate": frame((0, -5.85, 0.45), out=(0, -1, 0)), "Aura": up_((0, 0, 1.2)), "Top": up_(VC + V(0, 0, rim_z + 1.75))}
    for sx, key in ((-1, "Steam1"), (1, "Steam2")):
        a0 = math.pi / 2 + sx * 0.45
        hi, _ = vol_point(a0 - sx * 0.1, 8.9, 0.4)
        lo, _ = vol_point(a0, 1.9, 0.4)
        atts[key] = frame(hi + (hi - lo).normalized() * 0.45, out=(0, 0, 1), up=(0, 1, 0))
    lp_hose_atts(atts, pts)
    return atts


TIER_FNS = [lp_scrappy, lp_workshop, lp_frosttech, lp_enchanted, lp_legendary]


# ---------- the upgrade sets ----------

LOOK = {  # metal, accent, glow, piston body, piston rod
    1: ("Iron", "Rust", "LampYellow", "PineDark", "PineLight"),
    2: ("Brass", "Copper", "Amber", "Brass", "SteelLight"),
    3: ("SteelLight", "GlacierBlue", "AuroraCyan", "SnowWhite", "SteelLight"),
    4: ("Gold", "Moonstone", "RuneGlow", "Moonstone", "Gold"),
    5: ("Gold", "Gunmetal", LAVA_HOT, "Gunmetal", "Gold"),
}
LAMP_GLOW = {1: "LampYellow", 2: "WarnRed", 3: LAVA, 4: LAVA, 5: "Amber"}


def lp_clamp(t, r):
    """A hose clamp in tier t's look round a hose of radius r (in the XY plane, the hose along Z)."""
    metal, accent, glow, _, _ = LOOK[t]
    pieces = lp_ring(M((0, 0, 0)), r * 1.12, r * 0.28 + 0.02, metal, segments=14)
    pieces += lp_ring(M((0, 0, 0.18 + r * 0.3)), r * 1.12, r * 0.18 + 0.015, accent, glow=(t == 3), segments=14)
    pieces += lp_ring(M((0, 0, -0.18 - r * 0.3)), r * 1.12, r * 0.18 + 0.015, accent, glow=(t == 3), segments=14)
    pieces += place(bolt(0.05 + r * 0.15, "Iron" if t < 4 else metal, "SteelLight"), frame((0, r * 1.3, 0), out=(0, 1, 0)))
    if t == 4:
        pieces += place(cut_gem(0.06 + r * 0.2, "MagicPink"), frame((0, -r * 1.35, 0), out=(0, -1, 0)))
    if t == 5:
        pieces += place(cut_gem(0.1, LAVA), frame((0, -r * 1.42, 0), out=(0, -1, 0)))
    return pieces


def lp_reinforce(t):
    """The 1st upgrade's armour on the nozzle, in its own frame (+Z along the nozzle)."""
    metal, accent, glow, _, _ = LOOK[t]
    pieces = []
    for z, r in NOZ_BANDS[t]:
        pieces += lp_ring(M((0, 0, z)), r + 0.05, 0.06 + 0.012 * t, metal, segments=16)
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            pieces += place(rivet(0.04 + 0.01 * t, accent if t != 3 else "SteelDark"), frame(((r + 0.1) * math.cos(a), (r + 0.1) * math.sin(a), z), out=(math.cos(a), math.sin(a), 0)))
    z0, r0 = NOZ_BANDS[t][0]
    z1, r1 = NOZ_BANDS[t][-1]
    for k in range(3):  # armour strips joining the bands
        a = k * 2 * math.pi / 3 + 0.5
        strip = bmesh.new()
        rounded_block(strip, (0.12 + 0.02 * t, 0.06, z1 - z0 + 0.1), M(((r0 + 0.07) * math.cos(a), (r0 + 0.07) * math.sin(a), (z0 + z1) / 2), (0, 0, a + math.pi / 2)), corner=0.02, edge=0.02, corner_seg=1, edge_seg=1)
        pieces.append((strip, accent if t in (1, 2) else metal, 0.0, False))
    L = NOZ_LEN[t]
    rim = bmesh.new()  # a reinforced muzzle ring
    r_tip = {1: 0.16, 2: 0.22, 3: 0.38, 4: 0.6, 5: 0.55}[t]
    lathe(rim, [(r_tip + 0.02, L - 0.12), (r_tip + 0.1, L - 0.1), (r_tip + 0.1, L + 0.04), (r_tip + 0.02, L + 0.06)], 16)
    pieces.append((rim, metal, 0.0, False))
    if t >= 3:
        pieces += lp_ring(M((0, 0, L - 0.04)), r_tip + 0.11, 0.025, glow, True, 16)
    return pieces


def lp_piston_set(t):
    """The 3rd upgrade's pumping piston in tier t's look, in a Gear frame (+Z out, +Y up)."""
    _, accent, glow, body, rod = LOOK[t]
    pieces = []
    size = {1: 0.6, 2: 0.8, 3: 0.85, 4: 0.8, 5: 1.0}[t]
    p0, p1 = V(0, -1.0 * size, 0.4), V(0, 1.1 * size, 0.4)
    if t == 1:  # a wooden plunger in an iron sleeve
        pieces += place(cyl(0.16, 1.1 * size, "Iron", 10), Matrix.Translation(p0) @ align_z(p1 - p0))
        pieces += place(cyl(0.08, 2.1 * size, "PineLight", 8), Matrix.Translation(p0) @ align_z(p1 - p0))
        pieces += place(block((0.5, 0.3, 0.12), "PineDark", corner=0.05, edge=0.03), Matrix.Translation(p1) @ align_z(p1 - p0))
        pieces += lp_ring(Matrix.Translation(p0.lerp(p1, 0.25)) @ align_z(p1 - p0), 0.17, 0.035, "Rust", segments=10)
    else:
        pieces += piston(p0, p1, 0.13 + 0.03 * t, body, rod)
        for p in (p0, p1):
            pieces += place(block((0.5, 0.35, 0.45), accent, corner=0.08, edge=0.04), M((0, p.y, 0.0)))
        if t >= 3:
            pieces += lp_ring(Matrix.Translation(p0.lerp(p1, 0.52)) @ align_z(p1 - p0), 0.17 + 0.03 * t, 0.035, glow if t != 5 else LAVA, True, 12)
        if t == 4:
            pieces += place(rune_glyph(0.25, 3, "RuneGlow", 0.03), M((0, p0.y + 0.4, 0.62)))
    return pieces


def lp_splash(t):
    """The 4th upgrade's hit stand-in (particles in game): a crown of lava splashes, drops, steam off the ice."""
    pieces = []
    for k in range(7):
        a = k * 2 * math.pi / 7
        tongue = bmesh.new()
        cylinder(tongue, (0.25 * math.cos(a), 0.25 * math.sin(a), 0.0), 0.14, 0.7 + 0.15 * (k % 3), 6, top=0.02, direction=(math.cos(a), math.sin(a), 1.4))
        pieces.append((tongue, LAVA, 0.0, True))
    for k in range(6):
        a = k * 2.4 + 0.3
        drop = bmesh.new()
        blob(drop, (0.8 * math.cos(a), 0.8 * math.sin(a), 0.5 + 0.25 * k), (0.1, 0.1, 0.13), 1)
        pieces.append((drop, LAVA_HOT if k % 2 else LAVA, 0.0, True))
    pool = lp_pool(0.45, 12, 1, 0.5)
    pieces += pool
    for k, (dx, dz, r) in enumerate(((-0.5, 0.9, 0.3), (0.45, 1.3, 0.38), (0.0, 1.9, 0.45))):
        puff = bmesh.new()
        blob(puff, (dx, 0.2, dz), (r, r, r * 0.85), 1)
        pieces.append((puff, "SnowWhite", 0.0, False))
    extra = {3: ("CrystalCyan", True), 4: ("MagicPink", True), 5: ("Gold", True)}.get(t)
    if extra:
        for k in range(5):
            a = k * 1.25 + 0.6
            s = bmesh.new()
            cylinder(s, (0.4 * math.cos(a), 0.4 * math.sin(a), 0.3), 0.05, 0.6, 4, direction=(math.cos(a), math.sin(a), 1.3), top=0.0)
            pieces.append((s, extra[0], 0.0, extra[1]))
    return pieces


def lp_fountain_jet(height):
    """The 5th upgrade's fountain stand-in (particles in game): a lava column and arcs falling back."""
    pieces = lp_stream([(0, 0, 0.05), (0, 0, height * 0.5), (0, 0, height)], 0.18, 0.1)
    top = bmesh.new()
    blob(top, (0, 0, height), (0.3, 0.3, 0.25), 1)
    pieces.append((top, LAVA_HOT, 0.0, True))
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.3
        c, s = math.cos(a), math.sin(a)
        pieces += lp_stream([(0.1 * c, 0.1 * s, height * 0.95), (0.55 * c, 0.55 * s, height * 1.05), (0.95 * c, 0.95 * s, height * 0.6), (1.1 * c, 1.1 * s, 0.2)], 0.09, 0.04)
    return pieces


def lp_fountain_basin(t):
    """The 5th upgrade's basin in tier t's look (none on the Legendary: its crater is the basin)."""
    pieces = []
    if t == 1:  # half a barrel
        tub = bmesh.new()
        lathe(tub, [(0, 0), (0.6, 0), (0.7, 0.5), (0.62, 0.5), (0.52, 0.08), (0, 0.08)], 14)
        pieces.append((tub, "PineDark", 0.0, False))
        pieces += lp_ring(M((0, 0, 0.2)), 0.65, 0.04, "Iron", segments=14)
        pieces += lp_ring(M((0, 0, 0.45)), 0.69, 0.04, "Iron", segments=14)
        pieces += place(lp_pool(0.62, 14, 2, 0.2), M((0, 0, 0.4)))
    elif t == 2:  # a brass basin with a spout pipe
        bowl = bmesh.new()
        lathe(bowl, [(0, 0), (0.5, 0), (0.55, 0.15), (0.8, 0.45), (0.85, 0.6), (0.75, 0.6), (0.45, 0.25), (0, 0.25)], 14)
        pieces.append((bowl, "Brass", 0.0, False))
        pieces += lp_ring(M((0, 0, 0.6)), 0.82, 0.05, "Copper", segments=14)
        pieces += place(lp_pool(0.72, 14, 2, 0.6), M((0, 0, 0.45)))
        pieces += place(cyl(0.12, 0.7, "Copper", 10), M((0, 0, 0.2)))
    elif t == 3:  # a white ring basin with a cyan ring and cooling crystals
        bowl = bmesh.new()
        lathe(bowl, [(0, 0), (0.85, 0), (0.9, 0.3), (0.8, 0.4), (0, 0.35)], 16)
        pieces.append((bowl, "SnowWhite", 0.0, False))
        pieces += lp_ring(M((0, 0, 0.36)), 0.84, 0.04, "AuroraCyan", True, 16)
        pieces += place(lp_pool(0.72, 16, 2, 1.2), M((0, 0, 0.32)))
        for k in range(3):
            a = k * 2 * math.pi / 3 + 0.5
            pieces += place(cut_crystal(0.7, 0.14, "CrystalCyan", (0.3 * math.cos(a), 0.3 * math.sin(a))), M((0.95 * math.cos(a), 0.95 * math.sin(a), 0.0)))
    elif t == 4:  # a moonstone hexagon with a gold rim and runes
        bowl = bmesh.new()
        lathe(bowl, [(0, 0), (0.9, 0), (0.95, 0.4), (0.82, 0.45), (0, 0.4)], 6)
        pieces.append((bowl, "Moonstone", 0.03, False))
        pieces += place(trim_ring(0.9, 0.44, "Gold", minor=0.05, segments=6), M())
        pieces += place(lp_pool(0.72, 12, 2, 0.9), M((0, 0, 0.38)))
        for k in range(6):
            a = k * math.pi / 3 + math.pi / 6
            pieces += place(rune_glyph(0.22, k, "RuneGlow", 0.03), frame((0.83 * math.cos(a), 0.83 * math.sin(a), 0.22), out=(math.cos(a), math.sin(a), 0)))
    else:  # a gold spout ring set in the crater
        pieces += lp_ring(M((0, 0, 0.1)), 0.45, 0.1, "Gold", segments=16)
        pieces += place(rivet_ring(0.45, 6, 0.06, "Gunmetal"), M((0, 0, 0.2)))
    return pieces


ROCK_SPOTS = {  # where the 5th upgrade's glowing rocks lie, per tier (world points)
    1: [(-2.5, -2.4, 0.15), (-3.8, -1.3, 0.15), (-2.4, -1.2, 0.15)],
    2: [(2.2, 2.7, 0.6), (3.8, 1.4, 0.6), (3.6, 2.9, 0.6), (-3.4, -2.9, 0.6)],
    3: [(1.9, -3.4, 1.25), (3.6, -2.2, 1.25), (3.8, -3.7, 1.25), (-2.9, -3.7, 1.25)],
    4: [(1.7, -3.6, 0.95), (3.3, -2.2, 0.95), (3.4, -3.4, 0.95), (-2.6, -3.4, 0.95)],
    5: [(-1.6, -4.6, 1.35), (1.6, -5.0, 1.35), (-5.0, -1.6, 1.35), (5.0, 2.2, 1.35), (-2.8, 4.6, 1.35), (2.6, 4.9, 1.35)],
}


def UPGRADES(u, t, atts, b, fx):
    metal, accent, glow, _, _ = LOOK[t]
    if u == 1:  # reinforced hoses: an armoured nozzle and clamps along the hose
        b.add("Reinforce", place(lp_reinforce(t), atts["Work"] @ Matrix.Scale(NOZ_SCALE.get(t, 1.0), 4)))
        for key in ("HoseA", "HoseB", "HoseC"):
            b.add("Clamps", place(lp_clamp(t, HOSE_R[t]), atts[key]))
    elif u == 2:  # warning lamps
        for key in ("Lamp1", "Lamp2"):
            b.add("Lamp" + key[-1], place(tier_lamp(t, LAMP_GLOW[t]), atts[key]))
    elif u == 3:  # pumping pistons, and steam (sparkles from Enchanted on)
        for key in ("Gear1", "Gear2"):
            b.add("Piston" + key[-1], place(lp_piston_set(t), atts[key]))
        for key in ("Steam1", "Steam2"):
            fx.add("Steam" + key[-1], place(tier_puff(t), atts[key]))
    elif u == 4:  # lava splashes where the spray hits the ice
        fx.add("Hit", place(lp_splash(t), atts["Hit"]))
    else:  # a lava fountain with glowing rocks; lava drops trail from the nozzle
        basin = lp_fountain_basin(t)
        b.add("Fountain", place(basin, atts["Fountain"]))
        rocks = []
        for k, p in enumerate(ROCK_SPOTS[t]):
            rocks += lp_glow_rock(p, 0.22 + 0.04 * (k % 3) + (0.1 if t == 5 else 0.0), k + 11 * t, "Gunmetal" if t != 4 else "StoneDark")
        b.add("GlowRocks", rocks)
        height = {1: 1.8, 2: 2.2, 3: 2.4, 4: 2.6, 5: 3.4}[t]
        lift = {1: 0.4, 2: 0.55, 3: 0.4, 4: 0.45, 5: 0.0}[t]
        fx.add("Fountain", place(lp_fountain_jet(height), atts["Fountain"] @ M((0, 0, lift))))
        trail = []
        L = NOZ_LEN[t] * NOZ_SCALE.get(t, 1.0)
        for k in range(6):
            drop = bmesh.new()
            blob(drop, (0.12 * math.sin(k * 1.7), -0.08 * k * k * 0.15, L + 0.3 + k * 0.4), (0.1 - 0.008 * k,) * 3, 1)
            trail.append((drop, LAVA if k % 2 else LAVA_HOT, 0.0, True))
        fx.add("Trail", place(trail, atts["Trail"]))


def AURA(atts, fx):
    """Volcano Forge: lava sparks shooting up from the crater, heat haze over it, glowing smoke from the stacks."""
    crater = atts["Fountain"].to_translation()
    for k in range(12):
        a = k * 2.4
        r = 0.4 + 0.12 * (k % 4)
        s = bmesh.new()
        base = crater + V(r * math.cos(a), r * math.sin(a), 1.0 + 0.9 * (k % 5))
        cylinder(s, base, 0.05, 0.6, 4, direction=(0.25 * math.cos(a), 0.25 * math.sin(a), 1), top=0.0)
        fx.add("AuraSparks", [(s, LAVA_HOT if k % 2 else "Amber", 0.0, True)])
    for k in range(3):  # heat haze: wavy rings over the crater
        pts = []
        for i in range(25):
            a = 2 * math.pi * i / 24
            pts.append(crater + V((1.3 + 0.3 * k) * math.cos(a), (1.3 + 0.3 * k) * math.sin(a), 1.6 + 0.9 * k + 0.12 * math.sin(5 * a + k)))
        haze = bmesh.new()
        sweep(haze, pts, 0.035, 4)
        fx.add("AuraHaze", [(haze, "Cream", 0.0, False)])
    for key in ("Steam1", "Steam2"):  # glowing smoke from the stacks
        m = atts[key]
        for k, (dx, dz, r) in enumerate(((0.0, 0.4, 0.35), (0.25, 1.1, 0.5), (-0.1, 1.95, 0.62))):
            puff = bmesh.new()
            blob(puff, (dx, 0, dz), (r, r, r * 0.85), 2)
            fx.add("AuraSmoke", place([(puff, "Stone", 0.0, False)], m.copy()))
            ember = bmesh.new()
            blob(ember, (dx, -r * 0.45, dz - r * 0.45), (r * 0.5, r * 0.4, r * 0.3), 1)
            fx.add("AuraSmoke", place([(ember, "Amber", 0.0, True)], m.copy()))
