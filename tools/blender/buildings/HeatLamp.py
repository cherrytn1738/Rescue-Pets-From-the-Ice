# HeatLamp.py - the Heat Lamp's five tiers and its upgrade sets, for tools/blender/buildings/framework.py.
# Pad 8: compact, growing tall. The working part is the lamp (or the sun's focusing lens on the higher
# tiers): it sits at the front and aims at the ice (-Y), tilted down.
#   1 Scrappy     a camping lantern hung from a wooden post, a tin pie-dish reflector behind it
#   2 Workshop    a brass street lamp: cast-iron column, a crook arm, a brass bell lamp aimed at the ice
#   3 Frost-tech  a crystal heat-coil tower: an orange-hot coil powered by four blue crystals, a heat head
#   4 Enchanted   a floating sun orb inside three spinning rune rings, a floating lens aiming it
#   5 Legendary   Captive Star: a cheeky little sun in a golden birdcage with a crown, clamps, rivets,
#                 aurora rings and a focusing lens aimed at the ice
# Upgrades: 1 brighter bulbs, 2 orange beacon, 3 turning reflector, 4 heat shimmer and sparks (fx),
# 5 white-hot sun bulb with light rays (rays are fx).
TIER_Q = {"Scrappy": {"round": 1.0}, "Workshop": {"round": 1.0}, "Frost-tech": {"round": 1.1},
          "Enchanted": {"round": 1.5, "minor": 1.25, "corner": 3}, "Legendary": {"round": 1.25, "minor": 1.0}}

AIM1 = Vector((0, -1, -0.55)).normalized()
AIM2 = Vector((0, -0.75, -1)).normalized()
AIM3 = Vector((0, -1, -0.5)).normalized()
AIM4 = Vector((0, -1, -0.85)).normalized()
AIM5 = Vector((0, -1, -0.6)).normalized()


# ---------- small helpers ----------

def hl_smooth(points, n=4):
    """Catmull-Rom through the points (Vectors), n steps per span: a smooth sweep path."""
    pts = [Vector(p) for p in points]
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(n):
            t = s / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return out


def hl_sphere(radius, swatch, glow=False, segments=20, rings=10, center=(0, 0, 0)):
    bm = bmesh.new()
    prof = [(radius * math.sin(math.pi * k / rings), -radius * math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    prof[0], prof[-1] = (0, -radius), (0, radius)
    lathe(bm, prof, segments, M(center))
    return [(bm, swatch, 0.0, glow)]


def hl_dish(radius, depth, swatch, rim=None, segments=16, rim_glow=False):
    """A reflector dish opening along +Z (back at z = 0), with a rolled rim."""
    bm = bmesh.new()
    lathe(bm, [(0, 0), (radius * 0.5, depth * 0.08), (radius * 0.85, depth * 0.5), (radius, depth), (radius * 0.93, depth * 1.04),
               (radius * 0.8, depth * 0.62), (radius * 0.45, depth * 0.22), (0, depth * 0.16)], segments)
    pieces = [(bm, swatch, 0.0, False)]
    if rim:
        pieces += trim_ring(radius * 0.98, depth, rim, rim_glow, minor=max(0.035, radius * 0.05), segments=segments)
    return pieces


def hl_bulb(size, glass="LampYellow", metal="Brass"):
    """A light bulb along +Z: a screw base and a glowing pear-shaped glass."""
    base, glass_bm = bmesh.new(), bmesh.new()
    lathe(base, [(0, 0), (size * 0.28, 0), (size * 0.34, size * 0.1), (size * 0.34, size * 0.32), (size * 0.3, size * 0.36), (0, size * 0.36)], 10)
    lathe(glass_bm, [(0, size * 0.34), (size * 0.3, size * 0.36), (size * 0.5, size * 0.62), (size * 0.56, size * 0.88),
                     (size * 0.48, size * 1.12), (size * 0.26, size * 1.26), (0, size * 1.3)], 10)
    ridge = bmesh.new()
    torus(ridge, M((0, 0, size * 0.2)), size * 0.34, size * 0.04, 10, 4)
    return [(base, metal, 0.0, False), (ridge, metal, 0.0, False), (glass_bm, glass, 0.0, True)]


def hl_cone(base, direction, length, radius, swatch, glow=True, segments=6):
    bm = bmesh.new()
    cylinder(bm, base, radius, length, segments, top=0.0, direction=direction)
    return [(bm, swatch, 0.0, glow)]


def hl_lens(radius, glass="Diamond", rim="Gold", rim_minor=0.08, segments=16):
    """A biconvex lens facing +Z, centred, in a rim."""
    bm = bmesh.new()
    t = radius * 0.16
    lathe(bm, [(0, -t), (radius * 0.6, -t * 0.7), (radius, 0), (radius * 0.6, t * 0.7), (0, t)], segments)
    return [(bm, glass, 0.0, True)] + trim_ring(radius, 0, rim, minor=rim_minor, segments=segments)


def hl_wavy_ring(radius, z, swatch, waves=5, amp=0.12, minor=0.035):
    pts = [Vector((radius * math.cos(2 * math.pi * k / 40), radius * math.sin(2 * math.pi * k / 40),
                   z + amp * math.sin(waves * 2 * math.pi * k / 40))) for k in range(41)]
    bm = bmesh.new()
    sweep(bm, pts, minor, 4, caps=False)
    return [(bm, swatch, 0.0, True)]


def on_sphere(center, radius, x, z, lift=0.0):
    """The frame on a sphere's front (-Y) at world x and z, +Z along the surface normal."""
    c = Vector(center)
    dy = math.sqrt(max(radius * radius - (x - c.x) ** 2 - (z - c.z) ** 2, 0.0))
    p = Vector((x, c.y - dy, z))
    n = (p - c).normalized()
    return frame(p + n * lift, out=n)


# ---------- tier 1: Scrappy, a camping lantern ----------

def camp_lantern(glass="LampYellow", body="PatchGreen", metal="Iron"):
    """A camping lantern standing on z = 0: fuel tank, glowing globe, wire guards, hood, bail handle
    (its top is at z = 1.7)."""
    pieces = []
    tank, globe, hood = bmesh.new(), bmesh.new(), bmesh.new()
    lathe(tank, [(0, 0), (0.42, 0), (0.47, 0.06), (0.47, 0.3), (0.4, 0.38), (0, 0.38)], 16)
    lathe(globe, [(0, 0.36), (0.26, 0.38), (0.36, 0.52), (0.39, 0.72), (0.35, 0.92), (0.25, 1.06), (0, 1.08)], 16)
    lathe(hood, [(0, 1.04), (0.45, 1.04), (0.43, 1.12), (0.27, 1.27), (0.14, 1.33), (0, 1.35)], 16)
    pieces += [(tank, body, 0.0, False), (globe, glass, 0.0, True), (hood, body, 0.0, False)]
    pieces += place(cyl(0.11, 0.12, metal, 10), M((0, 0, 1.31)))
    knob = bmesh.new()
    cylinder(knob, (0.44, 0, 0.19), 0.08, 0.14, 8, direction=(1, 0, 0))
    pieces.append((knob, "Brass", 0.0, False))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        g = bmesh.new()
        sweep(g, [V(0.41 * math.cos(a), 0.41 * math.sin(a), 0.36), V(0.45 * math.cos(a), 0.45 * math.sin(a), 0.72),
                  V(0.39 * math.cos(a), 0.39 * math.sin(a), 1.06)], 0.028, 5)
        pieces.append((g, metal, 0.0, False))
    bail = bmesh.new()
    sweep(bail, [V(0.47 * math.cos(math.pi * i / 10), 0, 1.12 + 0.58 * math.sin(math.pi * i / 10)) for i in range(11)], 0.03, 6)
    pieces.append((bail, metal, 0.0, False))
    for sx in (-1, 1):
        pv = bmesh.new()
        blob(pv, (sx * 0.47, 0, 1.12), (0.06, 0.06, 0.06), 1)
        pieces.append((pv, metal, 0.0, False))
    return pieces


def tier_scrappy(b):
    for L, W, swatch, grain, loc, turn, seed in ((3.4, 0.95, "PineDark", "RustDark", (0.1, -0.9, 0), 0.06, 0.0),
                                                 (3.0, 0.9, "Pine", "PineDark", (0.3, 0.1, 0), -0.08, 1.3),
                                                 (2.6, 0.85, "PineLight", "Pine", (0.2, 1.05, 0), 0.1, 2.1)):
        b.add("Planks", place(plank(L, W, 0.25, swatch, grain, True, seed), M(loc, (0, 0, turn))))
    px, py = 0.6, 0.6
    b.add("Post", grained_beam((px, py, 0.25), (px, py, 4.35), 0.42, "PineDark", "Pine"))
    b.add("Post", grained_beam((px - 1.1, py, 0.25), (px - 0.15, py, 1.6), 0.24, "Pine", "PineDark", faces=(0, 2)))
    b.add("Post", grained_beam((px, py + 0.95, 0.25), (px, py + 0.15, 1.5), 0.24, "Pine", "PineDark", faces=(1, 3)))
    # the arm reaching out over the ice side, with a strut, rope lashings and nails
    b.add("Post", grained_beam((px, py + 0.35, 4.05), (px, -1.35, 4.2), 0.3, "Pine", "PineDark", faces=(0, 1)))
    b.add("Post", beam_between((px, py - 0.15, 3.0), (px, -0.35, 4.02), 0.18, swatch="PineLight"))
    for z, tilt in ((1.45, 0.25), (3.95, -0.3), (4.12, 0.35)):
        ring = bmesh.new()
        torus(ring, M((px, py, z), (tilt, 0, 0)), 0.3, 0.055, 12, 4)
        b.add("Post", [(ring, "PineLight", 0.0, False)])
    for p in ((px + 0.16, -0.45, 4.12), (px - 0.16, -0.45, 4.12), (px + 0.22, py - 0.15, 3.0)):
        b.add("Post", place(bolt(0.045, "Iron", "RustDark"), frame(p, out=(1 if p[0] > px else -1, 0, 0))))
    # the hook and the lantern
    tip = V(px, -1.15, 4.06)
    hook = bmesh.new()
    sweep(hook, [tip, tip + V(0, 0, -0.25), tip + V(0, 0.05, -0.38), tip + V(0, 0.15, -0.32)], 0.035, 6)
    b.add("Post", [(hook, "Iron", 0.0, False)])
    lantern_base = V(px, -1.15, tip.z - 0.36 - 1.7)
    b.add("Lantern", place(camp_lantern(), M(lantern_base)))
    # a hand-made reflector: a dented tin pie dish nailed to the post, aimed at the ice
    glass_c = lantern_base + V(0, 0, 0.72)
    dish_at = frame(glass_c + V(0, 0.72, 0.1), out=AIM1)
    b.add("Reflector", place(hl_dish(0.95, 0.36, "SteelLight", "Steel", 16), dish_at))
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.3
        b.add("Reflector", place(rivet(0.04, "RustDark"), dish_at @ frame((0.9 * math.cos(a), 0.9 * math.sin(a), 0.35), out=(0, 0, 1))))
    b.add("Reflector", beam_between(dish_at @ V(0, 0, 0.0), (px, py - 0.21, glass_c.z + 0.2), 0.1, swatch="Iron"))
    b.add("Reflector", beam_between((px, py - 0.21, glass_c.z - 0.5), dish_at @ V(0, -0.5, 0.1), 0.08, swatch="RustDark"))
    # junk: a tree stump, a jerry can, a firewood pile with an axe, a coil of rope
    sx, sy = -2.1, -1.2
    stump, top = bmesh.new(), bmesh.new()
    lathe(stump, [(0, 0), (0.55, 0), (0.48, 0.12), (0.45, 0.78), (0, 0.78)], 14, M((sx, sy, 0)))
    lathe(top, [(0, 0.77), (0.43, 0.77), (0.43, 0.81), (0, 0.81)], 14, M((sx, sy, 0)))
    b.add("Junk", [(stump, "PineDark", 0.0, False), (top, "PineLight", 0.0, False)])
    for r in (0.14, 0.28):
        gr = bmesh.new()
        torus(gr, M((sx, sy, 0.81)), r, 0.018, 14, 3)
        b.add("Junk", [(gr, "Pine", 0.0, False)])
    can = bmesh.new()
    rounded_block(can, (0.36, 0.72, 0.85), M((-2.0, 1.1, 0.425)), corner=0.08, edge=0.06)
    b.add("Junk", [(can, "WarnRed", 0.0, False)])
    b.add("Junk", place(handle(0.36, 0.12, 0.03, "Iron"), M((-2.0, 1.0, 0.85))))
    b.add("Junk", place(cyl(0.08, 0.14, "Iron", 8), M((-2.0, 1.36, 0.85))))
    b.add("Junk", trim_strip((-1.81, 0.8, 0.55), (-1.81, 1.4, 0.55), 0.1, "WarnRedDark"))
    for k, (x, z) in enumerate(((1.95, 0.2), (2.45, 0.2), (2.2, 0.55))):
        log = bmesh.new()
        lathe(log, [(0, -0.6), (0.2, -0.6), (0.21, 0.6), (0, 0.6)], 10, frame((x, 1.3, z), out=(0, 1, 0)))
        b.add("Junk", [(log, "PineDark", 0.0, False)])
        for e in (-0.61, 0.61):
            end = bmesh.new()
            lathe(end, [(0, 0), (0.17, 0), (0.17, 0.02), (0, 0.02)], 10, frame((x, 1.3 + e, z), out=(0, 1, 0)))
            b.add("Junk", [(end, "PineLight", 0.0, False)])
    axe = bmesh.new()
    sweep(axe, [V(2.2, 1.0, 0.72), V(2.3, 0.75, 1.05), V(2.35, 0.55, 1.4)], 0.045, 6)
    b.add("Junk", [(axe, "PineLight", 0.0, False)])
    head = bmesh.new()
    rounded_block(head, (0.08, 0.36, 0.22), M((2.2, 1.02, 0.7), (0.5, 0, 0)), corner=0.03, edge=0.02, corner_seg=1, edge_seg=1)
    b.add("Junk", [(head, "Steel", 0.0, False)])
    for k in range(3):
        rope = bmesh.new()
        torus(rope, M((1.75, -2.0, 0.06 + 0.09 * k)), 0.38 - 0.03 * k, 0.05, 14, 4)
        b.add("Junk", [(rope, "PineLight", 0.0, False)])
    work = frame(glass_c, out=AIM1)
    atts = {"Work": work, "Lamp1": up_((sx, sy, 0.81)), "Gear1": frame((px - 0.22, py, 2.6), out=(-1, -0.25, 0)),
            "Steam1": up_(lantern_base + V(0, 0, 1.45)), "Hit": frame((px, -3.4, 0.3), out=(0, -1, 0.6)), "Trail": work,
            "NamePlate": front((0.1, -1.4, 0.3)), "Aura": up_((0, 0, 0.25)), "Top": up_((px, py, 4.4))}
    return atts


# ---------- tier 2: Workshop, a brass street lamp ----------

def street_lamp_head(b, role, H):
    """The brass bell lamp hanging from the crook, opening along H's +Z. Returns the glass centre frame."""
    shade = bmesh.new()
    lathe(shade, [(0, -0.15), (0.18, -0.15), (0.22, 0.05), (0.5, 0.38), (0.82, 0.72), (0.9, 0.84), (0.84, 0.88),
                  (0.74, 0.78), (0.44, 0.45), (0.14, 0.2), (0, 0.2)], 16)
    b.add(role, place([(shade, "Brass", 0.0, False)], H))
    b.add(role, place(trim_ring(0.2, -0.08, "Iron", minor=0.06, segments=12), H))
    b.add(role, place(trim_ring(0.87, 0.85, "Copper", minor=0.05, segments=16), H))
    glass = bmesh.new()
    lathe(glass, [(0, 0.25), (0.3, 0.3), (0.5, 0.55), (0.56, 0.8), (0.5, 1.05), (0.3, 1.22), (0, 1.26)], 16)
    b.add(role, place([(glass, "LampYellow", 0.0, True)], H))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        bar = bmesh.new()
        sweep(bar, [V(0.8 * math.cos(a), 0.8 * math.sin(a), 0.86), V(0.6 * math.cos(a), 0.6 * math.sin(a), 1.12), V(0, 0, 1.36)], 0.03, 5)
        b.add(role, place([(bar, "Brass", 0.0, False)], H))
    drop = bmesh.new()
    lathe(drop, [(0, 1.3), (0.1, 1.36), (0.08, 1.48), (0, 1.62)], 10)
    b.add(role, place([(drop, "Brass", 0.0, False)], H))
    for k in range(6):
        a = k * math.pi / 3
        b.add(role, place(rivet(0.04, "Copper"), H @ frame((0.6 * math.cos(a), 0.6 * math.sin(a), 0.5), out=(math.cos(a), math.sin(a), -0.85))))
    return H @ Matrix.Translation((0, 0, 0.78))


def tier_workshop(b):
    deck, cob = bmesh.new(), bmesh.new()
    lathe(deck, [(0, 0), (3.0, 0), (3.06, 0.12), (3.0, 0.26), (0, 0.26)], 24)
    lathe(cob, [(0, 0.25), (2.72, 0.25), (2.68, 0.33), (0, 0.33)], 24)
    b.add("Deck", [(deck, "Iron", 0.0, False), (cob, "StoneLight", 0.0, False)])
    b.add("Deck", place(trim_ring(2.86, 0.28, "Brass", minor=0.06, segments=24), Matrix()))
    b.add("Deck", place(rivet_ring(2.93, 16, 0.05, "Brass"), M((0, 0, 0.26))))
    for k in range(9):  # a few cobbles set into the paving
        a = k * 2.39 + 0.4
        r = 1.35 + 0.95 * ((k * 0.618) % 1)
        c = bmesh.new()
        blob(c, (r * math.cos(a), r * math.sin(a), 0.33), (0.3, 0.24, 0.07), 1, rotation=(0, 0, a))
        b.add("Deck", [(c, "Stone", 0.0, False)])
    # pedestal and the fluted cast-iron column with brass collars
    ped = bmesh.new()
    lathe(ped, [(0, 0.3), (1.05, 0.3), (1.05, 0.6), (0.95, 0.7), (0.7, 0.95), (0.55, 1.4), (0.5, 1.6), (0, 1.6)], 8)
    b.add("Column", [(ped, "Iron", 0.03, False)])
    b.add("Column", place(trim_ring(1.0, 0.65, "Brass", minor=0.06, segments=8), Matrix()))
    b.add("Column", place(riveted_plate(0.55, 0.45, 0.05, "Gunmetal", "Brass", 0.25), front((0, -0.82, 0.83), -0.45)))
    col = bmesh.new()
    lathe(col, [(0.42, 1.55), (0.32, 1.75), (0.27, 2.0), (0.24, 5.7), (0.3, 5.85), (0.38, 6.0), (0.3, 6.12), (0, 6.15)], 12)
    b.add("Column", [(col, "Iron", 0.0, False)])
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        b.add("Column", trim_strip((0.245 * math.cos(a), 0.245 * math.sin(a), 2.15), (0.235 * math.cos(a), 0.235 * math.sin(a), 5.55), 0.06, "SteelDark"))
    for z, r in ((2.05, 0.29), (4.25, 0.26), (5.75, 0.31)):
        b.add("Column", place(trim_ring(r, z, "Brass", minor=0.06, segments=12), Matrix()))
    # the ladder rest crossbar (the lamplighter's), with brass knobs
    b.add("Column", beam_between((-1.0, 0, 5.25), (1.0, 0, 5.25), 0.13, swatch="Iron"))
    for sx in (-1, 1):
        k = bmesh.new()
        blob(k, (sx * 1.02, 0, 5.25), (0.11, 0.11, 0.11), 1)
        b.add("Column", [(k, "Brass", 0.0, False)])
    # the crook arm with a brass scroll under it and a finial on top
    crook = bmesh.new()
    sweep(crook, hl_smooth([V(0, 0.05, 6.0), V(0, -0.05, 6.55), V(0, -0.4, 7.0), V(0, -0.95, 7.2), V(0, -1.55, 7.12), V(0, -2.0, 6.85), V(0, -2.1, 6.62)], 3), 0.1, 10)
    b.add("Arm", [(crook, "Iron", 0.0, False)])
    scroll = bmesh.new()
    sweep(scroll, [V(0, -0.78 + (0.5 - 0.022 * i) * math.cos(0.9 + i * 0.42), 6.42 + (0.5 - 0.022 * i) * math.sin(0.9 + i * 0.42)) for i in range(16)], 0.045, 6)
    b.add("Arm", [(scroll, "Brass", 0.0, False)])
    fin = bmesh.new()
    lathe(fin, [(0, 7.2), (0.14, 7.24), (0.17, 7.36), (0.1, 7.48), (0.05, 7.75), (0, 7.85)], 10, M((0, -0.95, 0.02)))
    b.add("Arm", [(fin, "Brass", 0.0, False)])
    H = frame((0, -2.12, 6.5), out=AIM2)
    work = street_lamp_head(b, "LampHead", H)
    # the gas tank on a cradle: brass, copper bands, a dial, a safety valve, a copper gas pipe up the column
    tank_at = frame((0.75, 1.35, 0.95), out=(1, 0, 0))
    tank = bmesh.new()
    lathe(tank, [(0, -0.1), (0.3, -0.07), (0.45, 0.05), (0.47, 0.15), (0.47, 1.35), (0.45, 1.45), (0.3, 1.57), (0, 1.6)], 14, tank_at)
    b.add("Tank", [(tank, "Brass", 0.0, False)])
    for z in (0.35, 1.15):
        b.add("Tank", place(trim_ring(0.48, z, "Copper", minor=0.06, segments=14), tank_at))
        b.add("Tank", place(rivet_ring(0.48, 5, 0.04, "Copper"), tank_at @ M((0, 0, z + 0.1))))
    for x in (1.05, 2.05):
        b.add("Tank", place(block((0.25, 0.85, 0.35), "Iron", corner=0.06, edge=0.04), M((x, 1.35, 0.3))))
    b.add("Tank", place(dial(0.2, "Cream", "Brass", "WarnRed", 0.5), front((1.55, 0.86, 0.98))))
    b.add("Tank", place(cyl(0.07, 0.32, "Copper", 10), M((1.9, 1.35, 1.38))))
    b.add("Tank", place(cyl(0.13, 0.08, "Brass", 12), M((1.9, 1.35, 1.68))))
    pipe = bmesh.new()
    sweep(pipe, hl_smooth([V(0.72, 1.35, 0.95), V(0.45, 1.0, 1.05), V(0.36, 0.45, 1.5), V(0.3, 0.12, 1.9), V(0.27, 0.1, 2.3), V(0.26, 0.1, 5.5)], 3), 0.055, 8)
    b.add("Tank", [(pipe, "Copper", 0.0, False)])
    for z in (2.9, 3.9, 4.9):
        clip = bmesh.new()
        torus(clip, M((0.26, 0.1, z)), 0.07, 0.025, 10, 4)
        b.add("Tank", [(clip, "Brass", 0.0, False)])
    wheel_at = frame((0.42, 0.72, 1.32), out=(0.6, -0.8, 0))
    b.add("Tank", place(trim_ring(0.14, 0, "WarnRed", minor=0.03, segments=12), wheel_at))
    for k in range(2):
        b.add("Tank", place(block((0.26, 0.035, 0.035), "WarnRed", corner=0.01, edge=0.01), wheel_at @ M((0, 0, -0.017), (0, 0, k * math.pi / 2))))
    # the lamplighter's clock: a lidded brass box on the column with a clock face
    b.add("Clock", place(lidded_box((0.8, 0.5, 0.8), "Brass", "Brass", "Copper"), M((0, -0.45, 2.75))))
    b.add("Clock", place(dial(0.27, "Cream", "Copper", "EyeDark", 1.2), front((0, -0.71, 3.18))))
    b.add("Clock", place(gear(0.28, 8, 0.1, 0.07, "Copper", "Brass"), frame((0.41, -0.45, 3.15), out=(1, 0, 0))))
    # a lamplighter's ladder leaning on the back of the column, and an oil can
    b.add("Ladder", place(ladder(4.3, 0.75, "PineDark", "Pine"), M((0, 1.52, 0.3), (0.3, 0, 0))))
    can = bmesh.new()
    lathe(can, [(0, 0), (0.22, 0), (0.22, 0.42), (0.12, 0.55), (0, 0.55)], 12, M((-1.7, 0.9, 0.33)))
    spout = bmesh.new()
    sweep(spout, [V(-1.6, 0.9, 0.8), V(-1.4, 0.8, 1.03), V(-1.15, 0.7, 1.12)], 0.035, 6, radius_end=0.02)
    b.add("Ladder", [(can, "Copper", 0.0, False), (spout, "Brass", 0.0, False)])
    atts = {"Work": work, "Lamp1": up_((1.0, 0, 5.36)), "Lamp2": up_((-1.0, 0, 5.36)),
            "Gear1": frame((0.48, -0.45, 2.98), out=(1, 0, 0)), "Gear2": frame((-0.42, -0.45, 3.15), out=(-1, 0, 0)),
            "Steam1": up_((1.9, 1.35, 1.78)), "Hit": frame((0, -3.6, 0.3), out=(0, -1, 0.6)), "Trail": work,
            "NamePlate": front((0, -3.08, 0.14)), "Aura": up_((0, 0, 0.34)), "Top": up_((0, -0.95, 7.85))}
    return atts


# ---------- tier 3: Frost-tech, a crystal heat-coil tower ----------

def tier_frosttech(b):
    b.add("Deck", block((7.4, 7.4, 0.7), "SnowWhite", corner=1.3, edge=0.28))
    b.add("Deck", place(block((6.6, 6.6, 0.25), "IceBlue", corner=1.0, edge=0.1), M((0, 0, 0.7))))
    for x in (-1.9, 1.9):
        b.add("Deck", place(inset_panel(1.4, 1.0, 0.05, "FrostLight", "GlacierBlue", True), M((x, -2.3, 0.95))))
    for p0, p1 in (((-1.6, -3.72, 0.36), (-0.7, -3.72, 0.36)), ((0.7, -3.72, 0.36), (1.6, -3.72, 0.36)), ((-2.6, 3.72, 0.36), (2.6, 3.72, 0.36)),
                   ((-3.72, -2.2, 0.36), (-3.72, 2.2, 0.36)), ((3.72, -2.2, 0.36), (3.72, 2.2, 0.36))):
        b.add("Deck", trim_strip(p0, p1, 0.15, "AuroraCyan", True))
    for sx in (-1, 1):
        b.add("Deck", place(vent(1.1, 0.35, 4, "GlacierBlue", "SteelLight"), front((sx * 2.4, -3.69, 0.36))))
        for sy in (-1, 1):
            b.add("Deck", place(bolt(0.1, "SteelLight", "GlacierBlue"), M((sx * 3.0, sy * 3.0, 0.95))))
    # the tower base: a white pod with a band, a screen and vents
    b.add("Base", place(block((2.4, 2.4, 1.7), "SnowWhite", corner=0.8, edge=0.4), M((0, 0.6, 0.95))))
    b.add("Base", place(block((2.46, 2.46, 0.07), "GlacierBlue", corner=0.83, edge=0.02), M((0, 0.6, 1.85))))
    b.add("Base", place(screen(0.9, 0.5, "AuroraCyan", "NavyIce", 3), front((0, -0.6, 2.25))))
    for sx in (-1, 1):
        b.add("Base", place(vent(0.9, 0.6, 4, "GlacierBlue", "SteelLight"), frame((sx * 1.2, 0.6, 1.5), out=(sx, 0, 0))))
    # the heat coil: a navy core, an orange-hot wire wound round it, insulator discs, three rails
    cx, cy = 0.0, 0.6
    b.add("Coil", place(cyl(1.0, 0.2, "GlacierBlue", 16), M((cx, cy, 2.65))))
    b.add("Coil", place(cyl(0.42, 4.25, "NavyIce", 14), M((cx, cy, 2.85))))
    helix = [V(cx + 0.62 * math.cos(2 * math.pi * 7 * t / 70), cy + 0.62 * math.sin(2 * math.pi * 7 * t / 70), 3.0 + 3.7 * t / 70) for t in range(71)]
    wire = bmesh.new()
    sweep(wire, helix, 0.09, 6)
    b.add("Coil", [(wire, "FlameOrange", 0.0, True)])
    for z in (2.85, 6.85):
        b.add("Coil", place(cyl(0.95, 0.16, "IceBlue", 16), M((cx, cy, z))))
        b.add("Coil", place(rivet_ring(0.82, 6, 0.05, "SteelDark"), M((cx, cy, z + 0.16))))
    for a in (math.pi / 2, math.pi / 2 + 2 * math.pi / 3, math.pi / 2 + 4 * math.pi / 3):
        b.add("Coil", beam_between((cx + 0.92 * math.cos(a), cy + 0.92 * math.sin(a), 2.9), (cx + 0.92 * math.cos(a), cy + 0.92 * math.sin(a), 7.0), 0.16, swatch="SteelLight"))
    b.add("Coil", place(cyl(1.05, 0.22, "SteelLight", 16), M((cx, cy, 7.0))))
    b.add("Coil", place(trim_ring(1.06, 7.11, "AuroraCyan", True, minor=0.05, segments=16), M((cx, cy, 0))))
    # the yoke and the heat head aimed at the ice
    Hc = V(0, 0.45, 8.0)
    for sx in (-1, 1):
        b.add("Yoke", beam_between((sx * 0.85, cy, 7.2), (sx * 1.32, Hc.y, Hc.z), 0.22, swatch="SteelLight"))
        b.add("Yoke", place(cyl(0.24, 0.2, "GlacierBlue", 12), frame((sx * 1.22, Hc.y, Hc.z), out=(sx, 0, 0))))
        b.add("Yoke", place(bolt(0.09, "SteelLight", "GlacierBlue"), frame((sx * 1.42, Hc.y, Hc.z), out=(sx, 0, 0))))
    H = frame(Hc, out=AIM3)
    house = bmesh.new()
    lathe(house, [(0, -0.85), (0.55, -0.82), (0.9, -0.6), (1.1, -0.25), (1.15, 0.15), (1.12, 0.35), (1.0, 0.42), (0.9, 0.3), (0, 0.3)], 16)
    b.add("Head", place([(house, "SnowWhite", 0.0, False)], H))
    b.add("Head", place(trim_ring(1.06, 0.4, "GlacierBlue", minor=0.08, segments=16), H))
    b.add("Head", place(trim_ring(1.16, 0.0, "AuroraCyan", True, minor=0.05, segments=16), H))
    spiral = [V((0.15 + 0.7 * t / 36) * math.cos(2 * math.pi * 3 * t / 36), (0.15 + 0.7 * t / 36) * math.sin(2 * math.pi * 3 * t / 36), 0.36) for t in range(37)]
    el = bmesh.new()
    sweep(el, spiral, 0.05, 5)
    b.add("Head", place([(el, "FlameOrange", 0.0, True)], H))
    b.add("Head", place(hl_sphere(0.2, "LampYellow", True, 12, 6, (0, 0, 0.38)), H))
    for k in range(2):
        b.add("Head", place(block((1.9, 0.05, 0.05), "SteelLight", corner=0.02, edge=0.015), H @ M((0, 0, 0.44), (0, 0, k * math.pi / 2 + math.pi / 4))))
    for k in range(6):
        a = k * math.pi / 3
        fin = bmesh.new()
        rounded_block(fin, (0.1, 0.42, 0.55), M((0.82 * math.cos(a), 0.82 * math.sin(a), -0.55), (0, 0, a + math.pi / 2)), corner=0.04, edge=0.03, taper=0.7)
        b.add("Head", place([(fin, "GlacierBlue", 0.0, False)], H))
    b.add("Head", place(cyl(0.25, 0.3, "SteelLight", 12), H @ M((0, 0, -1.1))))
    antenna_at = H @ V(0, 0.95, -0.35)
    b.add("Head", place(cut_crystal(1.1, 0.22, "CrystalCyan"), M(antenna_at)))
    b.add("Head", place(cyl(0.26, 0.15, "GlacierBlue", 6), M(antenna_at - V(0, 0, 0.1))))
    b.add("Cables", cable(H @ V(0.35, 0.1, -1.0), (0.55, cy + 0.6, 7.05), 0.3, 0.08, "NavyIce", "GlacierBlue"))
    # four blue power crystals in steel mounts, cabled to the tower
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 2.55, sy * 2.45
            b.add("Crystals", place(cyl(0.48, 0.22, "GlacierBlue", 6), M((x, y, 0.95))))
            b.add("Crystals", place(cyl(0.38, 0.14, "SteelLight", 6), M((x, y, 1.17))))
            b.add("Crystals", place(cut_crystal(1.9 if sy > 0 else 1.4, 0.34, "CrystalCyan", (0.05 * sy, -0.05 * sx)), M((x, y, 1.28))))
            for k in range(3):
                a = k * 2 * math.pi / 3 + 0.5
                b.add("Crystals", trim_strip((x + 0.36 * math.cos(a), y + 0.36 * math.sin(a), 1.25), (x + 0.3 * math.cos(a), y + 0.3 * math.sin(a), 1.75), 0.07, "SteelLight"))
            b.add("Cables", cable((x - sx * 0.4, y - sy * 0.3, 1.05), (sx * 1.05, cy + sy * 0.6, 1.15), 0.25, 0.08, "NavyIce", "GlacierBlue"))
    # a snowflake emblem on the deck front, a control desk and a coolant tank piped to the tower
    b.add("Deck", place(cyl(0.5, 0.12, "GlacierBlue", 6), front((0, -3.7, 0.36))))
    for k in range(3):
        b.add("Deck", place(block((0.11, 0.72, 0.08), "SnowWhite", corner=0.03, edge=0.02), front((0, -3.82, 0.36)) @ M((0, 0, 0), (0, 0, k * math.pi / 3))))
    desk = bmesh.new()
    rounded_block(desk, (1.1, 0.7, 0.75), M((2.0, -0.9, 1.32)), corner=0.2, edge=0.1)
    b.add("Desk", [(desk, "SnowWhite", 0.0, False)])
    panel = frame((2.0, -1.12, 1.78), out=(0, -0.6, 1))
    b.add("Desk", place(block((1.0, 0.55, 0.12), "GlacierBlue", corner=0.12, edge=0.04), panel @ M((0, 0, -0.08))))
    b.add("Desk", place(screen(0.55, 0.32, "AuroraCyan", "NavyIce", 3), panel @ M((-0.18, 0, 0.04))))
    b.add("Desk", place(dial(0.13, "FrostLight", "SteelLight", "FlameOrange", 0.9), panel @ M((0.3, 0.04, 0.04))))
    lever = bmesh.new()
    sweep(lever, [V(2.4, -0.75, 1.75), V(2.45, -0.8, 2.15)], 0.04, 6)
    knob = bmesh.new()
    blob(knob, (2.45, -0.8, 2.2), (0.09, 0.09, 0.09), 1)
    b.add("Desk", [(lever, "SteelLight", 0.0, False), (knob, "FlameOrange", 0.0, False)])
    tank_at = frame((-2.0, -0.9, 0.95), out=(0, 0, 1))
    tank = bmesh.new()
    lathe(tank, [(0, 0), (0.38, 0.02), (0.45, 0.2), (0.45, 1.3), (0.38, 1.48), (0.2, 1.55), (0, 1.56)], 14, tank_at)
    b.add("Desk", [(tank, "IceBlue", 0.0, False)])
    for z in (0.45, 1.05):
        b.add("Desk", place(trim_ring(0.46, z, "GlacierBlue", minor=0.05, segments=14), tank_at))
    b.add("Desk", place(trim_ring(0.47, 0.75, "AuroraCyan", True, minor=0.04, segments=14), tank_at))
    b.add("Cables", cable((-1.75, -0.7, 2.35), (-0.9, -0.1, 2.3), 0.2, 0.09, "SteelLight", "GlacierBlue", ribs=2))
    work = H @ Matrix.Translation((0, 0, 0.42))
    top = antenna_at + V(0, 0, 1.0)
    atts = {"Work": work, "Lamp1": up_((0.95, -0.38, 2.65)), "Lamp2": up_((-0.95, -0.38, 2.65)),
            "Gear1": frame((1.55, Hc.y, Hc.z), out=(1, 0, 0)), "Gear2": frame((-1.55, Hc.y, Hc.z), out=(-1, 0, 0)),
            "Steam1": up_(H @ V(0, 0.6, -1.0)), "Hit": frame((0, -3.9, 0.3), out=(0, -1, 0.6)), "Trail": work,
            "NamePlate": front((0, -3.72, 0.38)), "Aura": up_((0, 0, 0.95)), "Top": up_(top)}
    return atts


# ---------- tier 4: Enchanted, a floating sun orb in spinning rune rings ----------

def sun_orb(radius, core="LampYellow", spikes="FlameOrange", count=14):
    """A glowing orb with short flame spikes all round (fibonacci directions), centred."""
    pieces = hl_sphere(radius, core, True, 20, 10)
    for k in range(count):
        z = 1 - 2 * (k + 0.5) / count
        r = math.sqrt(1 - z * z)
        a = k * 2.39996
        d = Vector((r * math.cos(a), r * math.sin(a), z))
        pieces += hl_cone(d * radius * 0.85, d, radius * 0.55, radius * 0.16, spikes, True, 6)
    return pieces


def tier_enchanted(b):
    dais = bmesh.new()
    lathe(dais, [(0, 0), (3.7, 0), (3.7, 0.28), (3.55, 0.33), (3.55, 0.5), (3.35, 0.72), (0, 0.72)], 6)
    b.add("Dais", [(dais, "Moonstone", 0.04, False)])
    plinth = bmesh.new()
    lathe(plinth, [(0, -0.01), (3.85, -0.01), (3.85, 0.16), (0, 0.16)], 6)
    b.add("Dais", [(plinth, "StoneDark", 0.03, False)])
    b.add("Dais", place(trim_ring(3.42, 0.52, "RuneViolet", minor=0.07, segments=6), Matrix()))
    b.add("Dais", place(engraved_rune_ring(2.6, "RuneGlow", "ArcaneDeep", "RuneViolet", 12), M((0, 0, 0.72))))
    for k in range(6):
        a = k * math.pi / 3
        if k % 2 == 0:
            b.add("DaisCrystals", place(cut_crystal_cluster(0.62, "CrystalCyan" if k else "RuneViolet", "Moonstone", 5), M((3.0 * math.cos(a), 3.0 * math.sin(a), 0.6), (0, 0, a))))
        else:
            op = (3.0 * math.cos(a), 3.0 * math.sin(a))
            ob = bmesh.new()
            rounded_block(ob, (0.55, 0.55, 1.7), M((op[0], op[1], 0.72 + 0.85), (0, 0, a)), corner=0.08, edge=0.06, taper=0.65)
            b.add("Obelisks", [(ob, "StoneDark", 0.0, False)])
            b.add("Obelisks", place(trim_ring(0.4, 0.78, "Gold", minor=0.05, segments=4), M((op[0], op[1], 0), (0, 0, a + math.pi / 4))))
            b.add("Obelisks", place(rune_glyph(0.36, k, "RuneGlow", 0.03), frame((op[0] + 0.25 * math.cos(a), op[1] + 0.25 * math.sin(a), 1.55), out=(math.cos(a), math.sin(a), 0.12))))
            b.add("Obelisks", place(cut_gem(0.17, "MagicPink" if k == 3 else "AuroraCyan"), M((op[0], op[1], 2.85))))
            orbit = bmesh.new()
            torus(orbit, M((op[0], op[1], 2.85), (0.3, 0.2 * k, 0)), 0.3, 0.022, 16, 4)
            b.add("Obelisks", [(orbit, "Gold", 0.0, False)])
        fa = a + math.pi / 6
        ap = 3.7 * math.cos(math.pi / 6)
        b.add("Dais", place(gem_setting(0.13, "AuroraCyan", "Gold", 4), frame((ap * math.cos(fa), ap * math.sin(fa), 0.15), out=(math.cos(fa), math.sin(fa), 0))))
    # the cradle island under the orb, with three gold prongs reaching up toward it
    ic = 3.3
    b.add("Island", place(floating_platform(1.3, 0.45, "Moonstone", "StoneDark", "Gold", tip=False), M((0, 0.2, ic))))
    b.add("Island", place(trim_ring(0.95, 0.03, "Gold", minor=0.04, segments=6), M((0, 0.2, ic))))
    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.5
        b.add("IslandGlow", place(cut_crystal(0.65, 0.12, "RuneViolet", sides=6), Matrix.Translation((0.5 * math.cos(a), 0.2 + 0.5 * math.sin(a), ic - 0.75)) @ Matrix.Rotation(math.pi, 4, "X")))
        prong = bmesh.new()
        sweep(prong, hl_smooth([V(0.55 * math.cos(a), 0.2 + 0.55 * math.sin(a), ic), V(0.8 * math.cos(a), 0.2 + 0.8 * math.sin(a), ic + 0.7),
                                V(0.7 * math.cos(a), 0.2 + 0.7 * math.sin(a), ic + 1.35)], 3), 0.07, 8, radius_end=0.035)
        b.add("Island", [(prong, "Gold", 0.0, False)])
        b.add("Island", place(cut_gem(0.09, "MagicPink"), M((0.7 * math.cos(a), 0.2 + 0.7 * math.sin(a), ic + 1.42))))
    # the sun orb
    O = V(0, 0.2, 6.1)
    b.add("Orb", place(sun_orb(1.2), M(O)), organic=True)
    swirl = bmesh.new()
    torus(swirl, M(O, (0.4, 0.3, 0)), 1.28, 0.05, 32, 4)
    b.add("Orb", [(swirl, "FlameOrange", 0.0, True)])
    # three engraved rune rings round it (each spins)
    for role, radius, rot, glow in (("RingA", 1.85, (1.4, 0, 0.25), "RuneGlow"), ("RingB", 2.35, (0.35, 1.25, 0), "AuroraGreen"),
                                    ("RingC", 2.85, (0.22, -0.18, 0), "RuneGlow")):
        b.add(role, place(engraved_rune_ring(radius, glow, "ArcaneDeep", "Gold" if role == "RingB" else "RuneViolet", 12), M(O, rot)))
    # the floating lens that focuses the sun on the ice
    L = O + AIM4 * 3.45
    lens = frame(L, out=AIM4)
    b.add("Lens", place(hl_lens(0.85, "Diamond", "Gold", 0.09, 16), lens))
    b.add("Lens", place(trim_ring(1.12, 0, "RuneGlow", True, minor=0.035, segments=16), lens))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        b.add("Lens", place(cut_gem(0.09, "AuroraCyan"), lens @ M((1.0 * math.cos(a), 1.0 * math.sin(a), 0))))
    # two small floating islands for the lamps, floating rune stones, the crowning crystal
    for sx in (-1, 1):
        b.add("SideIslands", place(floating_platform(0.6, 0.28, "Moonstone", "StoneDark", "Gold", "CrystalCyan", tip=True), M((sx * 2.65, 1.3, 4.1))))
    for k, a in enumerate((0.5, 2.65, 4.0)):
        p = (2.95 * math.cos(a), 2.95 * math.sin(a), 1.9 + 0.35 * k)
        stone = subsurf(cage_box((0.7, 0.5, 0.9), 1), 1)
        stone.transform(M(p, (0.2, 0.1, a)))
        b.add("RuneStones", [(stone, "StoneDark", 0.0, False)])
        b.add("RuneStones", place(rune_glyph(0.48, k + 1, "RuneGlow", 0.03), frame(p, out=(math.cos(a), math.sin(a), 0)) @ M((0, 0, 0.24))))
    for k, a in enumerate((0.0, 1.57, 3.4, 5.9)):  # floating sun-shards, each with its own little orbit ring
        p = (3.15 * math.cos(a), 3.15 * math.sin(a), 2.3 + 0.5 * (k % 2))
        b.add("Shards", place(cut_crystal(0.95, 0.2, "FlameYellow" if k % 2 else "AuroraGreen", (0.3, 0.2)), M(p)))
        orbit = bmesh.new()
        torus(orbit, M((p[0], p[1], p[2] + 0.45), (1.2, 0.3 * k, 0)), 0.4, 0.025, 16, 4)
        b.add("Shards", [(orbit, "RuneGlow", 0.0, True)])
    crown_z = 9.55
    b.add("Crown", place(floating_platform(0.75, 0.3, "Moonstone", "StoneDark", "Gold", "RuneViolet", tip=True), M((0, 0.2, crown_z))))
    b.add("Crown", place(cut_crystal_cluster(0.8, "CrystalCyan", "Moonstone", 5), M((0, 0.2, crown_z - 0.05))))
    b.add("Crown", place(gem_setting(0.26, "FlameYellow", "Gold", 6), M((0, 0.2, crown_z + 1.4))))
    halo = bmesh.new()
    torus(halo, M((0, 0.2, crown_z + 1.75), (math.pi / 2, 0, 0.4)), 0.55, 0.035, 24, 4)
    b.add("Crown", [(halo, "Gold", 0.0, False)])
    atts = {"Work": lens, "Lamp1": up_((2.65, 1.3, 4.1)), "Lamp2": up_((-2.65, 1.3, 4.1)),
            "Gear1": frame((3.28, 1.3, 3.95), out=(1, 0, 0)), "Gear2": frame((-3.28, 1.3, 3.95), out=(-1, 0, 0)),
            "Steam1": up_((0, 0.2, crown_z + 2.3)), "Hit": frame((0, -3.7, 0.4), out=(0, -1, 0.6)), "Trail": lens,
            "NamePlate": front((0, -3.22, 0.36)), "Aura": up_((0, 0, 0.72)), "Top": up_((0, 0.2, crown_z + 2.3)), "Orb": up_(O)}
    return atts


# ---------- tier 5: Legendary, the Captive Star ----------

CAGE = [(2.45, 2.4), (2.85, 3.6), (3.0, 5.2), (3.0, 6.8), (2.75, 8.2), (2.15, 9.4), (1.3, 10.3), (0.45, 10.9)]


def cage_r(z):
    for (r0, z0), (r1, z1) in zip(CAGE, CAGE[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return CAGE[-1][0]


def crown_pieces(radius=0.8):
    pieces = trim_ring(radius, 0.1, "Gold", minor=0.15, segments=20) + trim_ring(radius, 0.42, "Gold", minor=0.07, segments=20)
    band = bmesh.new()
    lathe(band, [(radius * 0.95, 0.05), (radius, 0.05), (radius, 0.45), (radius * 0.95, 0.45)], 20)
    pieces.append((band, "Gold", 0.0, False))
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 2
        tall = k % 2 == 0
        spike = bmesh.new()
        h = 0.8 if tall else 0.55
        lathe(spike, [(0, 0), (0.2, 0), (0.18, h * 0.35), (0.07, h * 0.85), (0, h)], 8, M((radius * math.cos(a), radius * math.sin(a), 0.4)))
        pieces.append((spike, "Gold", 0.0, False))
        ball = bmesh.new()
        blob(ball, (radius * math.cos(a), radius * math.sin(a), 0.4 + h + 0.06), (0.08, 0.08, 0.08), 1)
        pieces.append((ball, "Gold", 0.0, False))
        gem_at = frame((radius * 1.05 * math.cos(a), radius * 1.05 * math.sin(a), 0.26), out=(math.cos(a), math.sin(a), 0))
        if tall:
            pieces += place(gem_setting(0.12, "MagicPink" if k == 0 else "AuroraCyan", "Gold", 4), gem_at)
        else:
            pieces += place(cut_gem(0.08, "AuroraGreen"), gem_at @ M((0, 0, 0.05)))
    pieces += place(cut_gem(0.22, "MagicPink"), M((0, 0, 0.85), (math.pi, 0, 0)))
    return pieces


def tier_legendary(b):
    # the plinth: gunmetal, a stone top, gold trim, aurora strips, vents, corner clamps
    b.add("Plinth", block((7.7, 7.7, 0.8), "Gunmetal", corner=0.9, edge=0.25))
    b.add("Plinth", place(block((7.1, 7.1, 0.25), "StoneLight", corner=0.7, edge=0.1), M((0, 0, 0.8))))
    b.add("Trim", place(block((7.8, 7.8, 0.16), "Gold", corner=0.94, edge=0.06), M((0, 0, 0.6))))
    b.add("Trim", trim_strip((-1.4, -3.86, 0.32), (1.4, -3.86, 0.32), 0.16, "AuroraGreen", True))
    for sx in (-1, 1):
        b.add("Plinth", place(vent(1.3, 0.35, 4, "Gunmetal", "SteelDark"), front((sx * 2.5, -3.85, 0.32))))
        b.add("Trim", trim_strip((sx * 3.86, -1.6, 0.32), (sx * 3.86, 1.6, 0.32), 0.16, "AuroraGreen", True))
        for sy in (-1, 1):
            if sy > 0:
                b.add("Plinth", place(gem_setting(0.17, "AuroraCyan", "Gold", 4), M((sx * 3.15, sy * 3.15, 1.05))))
            clamp = bmesh.new()
            rounded_block(clamp, (0.9, 0.22, 0.5), M((sx * 3.45, sy * 3.45, 0.85), (0, 0, sx * sy * math.pi / 4)), corner=0.08, edge=0.05)
            b.add("Plinth", [(clamp, "Gold", 0.0, False)])
            b.add("Plinth", place(bolt(0.07, "Gunmetal", "Gold"), frame((sx * 3.52, sy * 3.52, 0.95), out=(sx, sy, 0))))
    # the pedestal under the cage: aurora ring, gold bands, rivets
    ped = bmesh.new()
    lathe(ped, [(0, 1.05), (2.5, 1.05), (2.5, 1.3), (2.2, 1.45), (2.0, 1.9), (2.35, 2.05), (2.35, 2.3), (0, 2.3)], 20)
    b.add("Pedestal", [(ped, "Gunmetal", 0.0, False)])
    b.add("Pedestal", place(trim_ring(2.48, 1.3, "Gold", minor=0.08, segments=20), Matrix()))
    b.add("Pedestal", place(trim_ring(2.08, 1.68, "AuroraGreen", True, minor=0.07, segments=20), Matrix()))
    b.add("Pedestal", place(rivet_ring(2.25, 12, 0.07, "Gold"), M((0, 0, 2.3))))
    # side control boxes: a dial, a screen, exhaust vents
    for sx in (-1, 1):
        b.add("Controls", place(block((0.9, 0.8, 0.7), "Gunmetal", corner=0.15, edge=0.06), M((sx * 3.0, 1.0, 1.05))))
        b.add("Controls", place(block((0.96, 0.86, 0.12), "SteelDark", corner=0.17, edge=0.04), M((sx * 3.0, 1.0, 1.75))))
        b.add("Controls", trim_strip((sx * 3.0 - 0.45, 0.58, 1.75), (sx * 3.0 + 0.45, 0.58, 1.75), 0.08, "Gold"))
        b.add("Controls", place(dial(0.22, "Cream", "Gold", "WarnRed", 0.4 * sx) if sx < 0 else screen(0.6, 0.4, "AuroraGreen", "NavyIce", 3),
                                front((sx * 3.0, 0.59, 1.45))))
        b.add("Controls", place(cyl(0.12, 0.35, "SteelDark", 10), M((sx * 3.15, 1.25, 1.85))))
    # the golden birdcage: eight curved ribs, gold and aurora rings, clamp blocks at the feet, a domed cap
    for k in range(6):
        a = math.radians(60 * k)
        pts = hl_smooth([V(r * math.cos(a), r * math.sin(a), z) for r, z in CAGE], 3)
        rib = bmesh.new()
        sweep(rib, pts, 0.12, 8)
        b.add("CageRibs", [(rib, "Gold", 0.0, False)])
        foot = bmesh.new()
        rounded_block(foot, (0.34, 0.3, 0.5), M((2.45 * math.cos(a), 2.45 * math.sin(a), 2.45), (0, 0, a)), corner=0.07, edge=0.05)
        b.add("Cage", [(foot, "Gunmetal", 0.0, False)])
        b.add("Cage", place(rivet(0.06, "Gold"), frame((2.63 * math.cos(a), 2.63 * math.sin(a), 2.5), out=(math.cos(a), math.sin(a), 0))))
    for z, minor, swatch, glow in ((2.4, 0.15, "Gold", False), (3.05, 0.08, "AuroraGreen", True), (8.2, 0.1, "Gold", False), (9.4, 0.09, "Gold", False)):
        b.add("Cage", place(trim_ring(cage_r(z), z, swatch, glow, minor=minor, segments=28), Matrix()))
    for k in range(6):  # gold scroll curls between the ribs above the upper ring, with a gem in each
        a = math.radians(30 + 60 * k)
        out, side = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
        for sgn in (-1, 1):
            curl = [out * (cage_r(8.25 + 0.05 * i) + 0.02) + side * sgn * (0.55 - 0.32 * math.cos(i * 0.67)) * (1 - i / 17) + Vector((0, 0, 8.25 + 0.35 * math.sin(i * 0.67) + 0.05 * i)) for i in range(9)]
            sc = bmesh.new()
            sweep(sc, curl, 0.045, 5, radius_end=0.03)
            b.add("CageRibs", [(sc, "Gold", 0.0, False)])
        b.add("Cage", place(gem_setting(0.11, "AuroraCyan" if k % 2 else "MagicPink", "Gold", 4), frame(out * (cage_r(8.2) + 0.08) + Vector((0, 0, 8.2)), out=out)))
    for k in range(6):  # rivets on the upper ring, on the ribs
        a = math.radians(60 * k)
        r = cage_r(8.2) + 0.1
        b.add("Cage", place(rivet(0.06, "Gunmetal"), frame((r * math.cos(a), r * math.sin(a), 8.2), out=(math.cos(a), math.sin(a), 0))))
    cap = bmesh.new()
    lathe(cap, [(0.5, 10.75), (0.72, 10.85), (0.74, 11.0), (0.55, 11.22), (0.3, 11.34), (0, 11.38)], 16)
    b.add("Cage", [(cap, "Gold", 0.0, False)])
    b.add("Cage", place(trim_ring(0.72, 10.9, "Gunmetal", minor=0.06, segments=16), Matrix()))
    b.add("Crown", place(crown_pieces(0.62), M((0, 0, 11.25))))
    # the side hubs between the ribs (the turning reflectors sit here)
    for sx in (-1, 1):
        r = cage_r(6.3)
        b.add("Cage", place(cyl(0.32, 0.24, "Gunmetal", 12), frame((sx * (r + 0.02), 0, 6.3), out=(sx, 0, 0))))
        b.add("Cage", place(rivet_ring(0.24, 4, 0.045, "Gold"), frame((sx * (r + 0.26), 0, 6.3), out=(sx, 0, 0))))
    # the sun: a glowing ball with flame spikes round its rim and a cheeky face
    S, R = V(0, 0, 6.3), 2.0
    b.add("Sun", hl_sphere(R, "FlameYellow", True, 24, 12, S), organic=True)
    for k in range(12):
        th = math.radians(15 + 30 * k)
        d = Vector((math.cos(th), 0, math.sin(th)))
        long = k % 2 == 0
        b.add("SunRays", hl_cone(S + d * (R - 0.15), d, 0.85 if long else 0.6, 0.36 if long else 0.28, "FlameOrange", True, 10))
    for k in range(8):  # a second set of shorter spikes, back-tilted, so the sun is round from any side
        a = k * math.pi / 4 + math.pi / 8
        d = Vector((0.55 * math.cos(a), 0.85, 0.55 * math.sin(a))).normalized()
        b.add("SunRays", hl_cone(S + d * (R - 0.15), d, 0.55, 0.24, "FlameOrange", True, 8))
    ex, ez = 0.7, S.z + 0.42
    b.add("Face", place(cartoon_eye(0.52, None, look=(0.18, 0.12)), on_sphere(S, R, -ex, ez, -0.05)))
    wink = [on_sphere(S, R, ex + dx, ez + dz, 0.04).to_translation() for dx, dz in ((-0.34, -0.02), (-0.17, 0.15), (0.0, 0.2), (0.17, 0.15), (0.34, -0.02))]
    w = bmesh.new()
    sweep(w, hl_smooth(wink, 3), 0.075, 8)
    b.add("Face", [(w, "EyeDark", 0.0, False)])
    for k, (dx, dz) in enumerate(((0.34, -0.02), (0.42, 0.1))):  # lashes on the wink
        p0 = on_sphere(S, R, ex + dx, ez + dz, 0.04).to_translation()
        lash = bmesh.new()
        sweep(lash, [p0, p0 + V(0.12, -0.03, 0.06 + 0.06 * k)], 0.035, 5, radius_end=0.015)
        b.add("Face", [(lash, "EyeDark", 0.0, False)])
    b.add("Face", place(brow(0.62, -0.35, "EyeDark"), on_sphere(S, R, -ex, ez + 0.72, -0.04)))
    b.add("Face", place(brow(0.55, 0.2, "EyeDark"), on_sphere(S, R, ex, ez + 0.5, -0.04)))
    b.add("Face", place(grin(1.2, 0.3, "EyeDark", "EyeWhite", 4), on_sphere(S, R, 0.05, S.z - 0.55, -0.04)))
    tongue = bmesh.new()
    tp = on_sphere(S, R, 0.3, S.z - 0.98, 0.0).to_translation()
    blob(tongue, (tp.x, tp.y - 0.05, tp.z), (0.2, 0.12, 0.18), 2, rotation=(0.3, 0, 0.2))
    b.add("Face", [(tongue, "Blush", 0.0, False)])
    for sx in (-1, 1):
        cheek = bmesh.new()
        cp = on_sphere(S, R, sx * 1.18, S.z - 0.2, 0.0).to_translation()
        blob(cheek, cp, (0.28, 0.12, 0.2), 1, rotation=(0, 0, sx * 0.55))
        b.add("Face", [(cheek, "Blush", 0.0, False)])
    # machine clamps holding the sun: two arms from the back ribs and a cradle cup underneath
    for k in (1, 2):
        a = math.radians(60 * k)
        z = S.z + 0.35
        c0 = V(cage_r(z) * math.cos(a), cage_r(z) * math.sin(a), z)
        d = (c0 - S).normalized()
        c1 = S + d * (R + 0.18)
        b.add("Clamps", piston(c0, c1 + d * 0.15, 0.12, "Gunmetal", "SteelLight"))
        pad = frame(c1, out=d)
        b.add("Clamps", place(block((0.8, 0.8, 0.22), "Gunmetal", corner=0.2, edge=0.06), pad @ M((0, 0, -0.1))))
        b.add("Clamps", place(rivet_ring(0.3, 4, 0.05, "Gold"), pad @ M((0, 0, 0.12))))
        b.add("Clamps", place(block((0.3, 0.3, 0.4), "Gold", corner=0.06, edge=0.04), frame(c0, out=-d) @ M((0, 0, -0.1))))
    b.add("Clamps", place(cyl(0.28, S.z - R - 2.3 - 0.05, "Gunmetal", 12), M((0, 0, 2.3))))
    b.add("Clamps", place(trim_ring(0.3, 3.0, "Gold", minor=0.05, segments=12), Matrix()))
    cup = bmesh.new()
    lathe(cup, [(0, 0), (0.5, 0.03), (0.72, 0.22), (0.68, 0.3), (0.48, 0.14), (0, 0.1)], 16, M((0, 0, S.z - R - 0.12)))
    b.add("Clamps", [(cup, "Gold", 0.0, False)])
    # the focusing lens aimed at the ice, on a gold yoke from the pedestal, with a hose
    L = V(0, -3.28, 4.45)
    lens = frame(L, out=AIM5)
    b.add("Lens", place(hl_lens(0.82, "Diamond", "Gold", 0.1, 16), lens))
    b.add("Lens", place(trim_ring(0.92, -0.06, "Gunmetal", minor=0.07, segments=16), lens))
    for k in range(6):
        a = k * math.pi / 3
        b.add("Lens", place(rivet(0.045, "Gold"), lens @ frame((0.92 * math.cos(a), 0.92 * math.sin(a), 0.03), out=(0, 0, 1))))
    for sx in (-1, 1):
        pin = lens @ V(sx * 1.02, 0, 0)
        b.add("Lens", place(cyl(0.13, 0.16, "Gunmetal", 10), frame(pin, out=(sx, 0, 0))))
        b.add("Lens", beam_between((sx * 0.55, -2.15, 2.28), pin, 0.14, swatch="Gold"))
        b.add("Lens", place(bolt(0.07, "Gold", "Gunmetal"), frame(pin + V(sx * 0.16, 0, 0), out=(sx, 0, 0))))
    b.add("Lens", place(gem_setting(0.12, "AuroraGreen", "Gold", 4), lens @ frame((0, 0.95, 0.0), out=(0, 1, 0.3))))
    b.add("Lens", cable((0.9, -1.9, 2.28), lens @ V(0.6, -0.65, -0.1), 0.35, 0.07, "Rubber", "Gold"))
    eyes = frame(on_sphere(S, R, 0, ez, 0).to_translation(), out=(0, -1, 0))
    atts = {"Work": lens, "Lamp1": up_((3.1, -3.1, 1.05)), "Lamp2": up_((-3.1, -3.1, 1.05)),
            "Gear1": frame((cage_r(6.3) + 0.3, 0, 6.3), out=(1, 0, 0)), "Gear2": frame((-cage_r(6.3) - 0.3, 0, 6.3), out=(-1, 0, 0)),
            "Steam1": up_((3.15, 1.25, 2.2)), "Steam2": up_((-3.15, 1.25, 2.2)),
            "Hit": frame((0, -3.95, 1.05), out=(0, -1, 0.6)), "Trail": lens, "NamePlate": front((0, -3.88, 0.42)),
            "Aura": up_((0, 0, 1.05)), "Crown": up_((0, 0, 11.25)), "Eyes": eyes, "Sun": up_(S), "Top": up_((0, 0, 12.4))}
    return atts


TIER_FNS = [tier_scrappy, tier_workshop, tier_frosttech, tier_enchanted, tier_legendary]


# ---------- upgrade sets ----------

METAL = {1: "Iron", 2: "Brass", 3: "SteelLight", 4: "Gold", 5: "Gold"}
ACCENT = {1: "RustDark", 2: "Copper", 3: "GlacierBlue", 4: "Moonstone", 5: "Gunmetal"}
BULB_RING = {1: (0.66, -0.05), 2: (1.0, 0.08), 3: (1.3, -0.05), 4: (1.05, 0.0), 5: (1.15, 0.0)}  # (radius, offset) round Work
SUN_BULB = {1: (0.3, 0.62), 2: (0.4, 0.42), 3: (0.42, 0.3), 4: (0.42, 0.0), 5: (0.5, 0.05)}  # (radius, offset along Work)


def turning_reflector(t, radius=0.55):
    """The 3rd upgrade: a faceted mirror dish on a hub, turning about its +Z (built round the axis)."""
    metal, mirror = METAL[t], ("SteelLight" if t <= 2 else "Diamond")
    pieces = place(cyl(radius * 0.28, 0.22, ACCENT[t], 12), Matrix())
    pieces += place(hl_dish(radius, radius * 0.55, metal, None, 16), M((0, 0, 0.18)))
    facets = bmesh.new()
    lathe(facets, [(0, 0.3), (radius * 0.86, 0.18 + radius * 0.5), (radius * 0.82, 0.21 + radius * 0.5), (0, 0.33)], 8)
    pieces.append((faceted(facets), mirror, 0.0, False))
    pieces += trim_ring(radius * 0.97, 0.18 + radius * 0.55, "AuroraCyan" if t == 3 else "RuneGlow" if t == 4 else metal, t in (3, 4),
                        minor=0.045, segments=16)
    pieces += place(hl_bulb(0.3, "LampYellow" if t != 4 else "FlameYellow", metal), M((0, 0, 0.3)))
    for k in range(4):
        a = k * math.pi / 2
        pieces += place(rivet(0.04, ACCENT[t] if t != 5 else "Gold"), frame((radius * 0.6 * math.cos(a), radius * 0.6 * math.sin(a), 0.2), out=(0, 0, -1)))
    return pieces


def UPGRADES(u, t, atts, b, fx):
    work = atts["Work"]
    if u == 1:  # brighter bulbs: a ring of bright bulbs round the working part, aimed with it
        ring_r, off = BULB_RING[t]
        b.add("Bulbs", place(trim_ring(ring_r, off - 0.05, METAL[t], minor=0.05, segments=20), work))
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            at = work @ M((ring_r * math.cos(a), ring_r * math.sin(a), off))
            b.add("Bulbs", place(cyl(0.11, 0.08, ACCENT[t], 10), at @ M((0, 0, -0.08))))
            b.add("Bulbs", place(hl_bulb(0.32, "LampYellow" if t < 5 else "FlameYellow", METAL[t]), at))
    elif u == 2:  # an orange beacon on each lamp point, in the tier's look
        for key in ("Lamp1", "Lamp2"):
            if key not in atts:
                continue
            if t == 1:
                pieces = camp_lantern("FlameOrange", "Rust", "Iron")
                place(pieces, Matrix.Diagonal((0.5, 0.5, 0.5, 1)))
            elif t == 2:
                pieces = warning_lamp(0.3, "FlameOrange", "Brass", "Iron")
            elif t == 3:
                pieces = warning_lamp(0.3, "FlameOrange", "SteelLight", "GlacierBlue")
            else:
                pieces = tier_lamp(t, "FlameOrange")
            b.add("Beacon" + key[-1], place(pieces, atts[key]))
    elif u == 3:  # a turning reflector on each gear point
        for key in ("Gear1", "Gear2"):
            if key in atts:
                b.add("Reflector" + key[-1], place(turning_reflector(t, 0.5 if t <= 2 else 0.6), atts[key]))
    elif u == 4:  # heat shimmer and sparks on every hit (particles in game)
        pieces = hit_standin(t, "FlameOrange")
        for k in range(3):
            pieces += hl_wavy_ring(0.55 + 0.25 * k, 0.5 + 0.45 * k, "FlameYellow", 5 + k, 0.1, 0.03)
        fx.add("Hit", place(pieces, atts["Hit"]))
    else:  # the white-hot sun bulb with light rays (the rays are particles/beams in game)
        radius, off = SUN_BULB[t]
        at = work @ M((0, 0, off))
        b.add("SunBulb", place(hl_sphere(radius, "SnowWhite", True, 16, 8), at))
        b.add("SunBulb", place(trim_ring(radius * 1.15, -radius * 0.55, METAL[t], minor=0.06, segments=16), at))
        for k in range(6):
            a = k * math.pi / 3
            b.add("SunBulb", place(hl_cone((0, 0, 0), (0, 0, 1), radius * 0.6, radius * 0.18, "LampYellow", True, 6),
                                   at @ frame((radius * 0.95 * math.cos(a), radius * 0.95 * math.sin(a), 0), out=(math.cos(a), math.sin(a), 0.25))))
        if t == 1:  # a wire holder from the lantern
            holder = bmesh.new()
            sweep(holder, [work @ V(0, 0.35, 0.2), work @ V(0, 0.2, off - radius * 0.6)], 0.03, 5)
            b.add("SunBulb", [(holder, "Iron", 0.0, False)])
        if t == 5:  # a white-hot halo round the sun itself
            halo = bmesh.new()
            torus(halo, atts["Sun"] @ M((0, 0, 0), (math.pi / 2, 0, 0)), 2.8, 0.06, 40, 4)
            b.add("SunBulb", [(halo, "SnowWhite", 0.0, True)])
        rays = []
        for k in range(7):
            a = k * 2 * math.pi / 6
            spread = 0 if k == 6 else 0.28
            d = Vector((spread * math.cos(a), spread * math.sin(a), 1)).normalized()
            base = Vector((0.3 * math.cos(a), 0.3 * math.sin(a), 0)) if k < 6 else Vector()
            rays += hl_cone(base, d, 3.0 + 0.4 * (k % 2), 0.09, "LampYellow", True, 4)
        fx.add("Rays", place(rays, at))


def AURA(atts, fx):
    """Captive Star: sun rays turning slowly, heat shimmer above, embers orbiting the cage, a ground ring."""
    sun = atts["Sun"].to_translation()
    rays = []
    for k in range(16):
        th = 2 * math.pi * k / 16 + 0.1
        d = Vector((math.cos(th), 0, math.sin(th)))
        rays += hl_cone(sun + d * 3.2, d, 1.2 if k % 2 else 0.8, 0.12, "LampYellow", True, 4)
    fx.add("AuraRays", rays)
    for k in range(3):
        fx.add("AuraShimmer", place(hl_wavy_ring(0.9 + 0.35 * k, 12.6 + 0.5 * k, "FlameYellow", 5, 0.12, 0.035), Matrix()))
    embers = []
    for k in range(12):
        a = 2 * math.pi * k / 12
        p = sun + Vector((3.6 * math.cos(a), 3.6 * math.sin(a) * 0.9, 1.2 * math.sin(a + 0.8)))
        e = bmesh.new()
        blob(e, p, (0.12, 0.12, 0.12), 1)
        embers.append((e, "FlameOrange" if k % 2 else "FlameYellow", 0.0, True))
    fx.add("AuraEmbers", embers)
    ring = bmesh.new()
    torus(ring, M((0, 0, 1.08)), 3.4, 0.06, 40, 4)
    fx.add("AuraGround", [(ring, "FlameOrange", 0.0, True)])
