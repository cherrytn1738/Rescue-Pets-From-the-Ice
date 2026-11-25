# FlamethrowerTurret.py - the Flamethrower Turret's five tiers and upgrade sets, for
# tools/blender/buildings/framework.py (style reference: IceDrill.py).
# Working part: the nozzle, aimed at the ice (-Y, tilted down), with a flame stand-in (role "Flame",
# a glow mesh that flickers in game). Tiers: a torch on a stand, a brass flamethrower cart, a blue-flame
# crystal cannon, an enchanted brazier with fire spirits, and the Dragon Turret.
# Attachments: Work, Lamp1/2, Gear1 (Gear2 on the Legendary: spinning turret gears), Gauge1/2 (fuel
# gauges, upgrade 3), Steam1/2 (smoke), Hit, Trail, NamePlate, Aura, Top; Crown and Eyes on the Legendary.
TIER_Q = {"Scrappy": {"round": 1.0}, "Workshop": {"round": 1.0}, "Frost-tech": {"round": 1.1},
          "Enchanted": {"round": 1.25, "minor": 1.25}, "Legendary": {"round": 1.0}}

T1_DIR = Vector((0, -1, -0.4)).normalized()
T2_DIR = Vector((0, -1, -0.3)).normalized()
T3_DIR = Vector((0, -1, -0.32)).normalized()
T4_DIR = Vector((0, -1, -0.5)).normalized()
HEAD_PITCH = 0.5            # the dragon's head bends down this much toward the ice (radians)
JAW_OPEN = 0.72             # and its lower jaw hangs wide open round the nozzle
FLAME = {1: (0.3, 1.3, "FlameOrange", "FlameYellow"), 2: (0.36, 1.6, "FlameOrange", "FlameYellow"),
         3: (0.4, 1.8, "GlacierBlue", "CrystalCyan"), 4: (0.42, 1.9, "MagicPink", "FlameYellow"),
         5: (0.55, 2.4, "FlameOrange", "FlameYellow")}
NOZZLE_R = {1: 0.14, 2: 0.3, 3: 0.46, 4: 0.4, 5: 0.42}
HIT = frame((0, -5.5, 0.5), out=(0, -1, 0.6))


# ---------- small pieces of this building ----------

def spline(points, steps=4):
    """A smooth Catmull-Rom curve through the points (for necks, tails, horns)."""
    P = [Vector(p) for p in points]
    out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for k in range(steps):
            t = k / steps
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(P[-1])
    return out


def cone(r, h, swatch, segs=8, glow=False):
    bm = bmesh.new()
    lathe(bm, [(0, 0), (r, 0), (r * 0.55, h * 0.55), (0, h)], segs)
    return [(bm, swatch, 0.0, glow)]


def tube(points, r0, r1, swatch, segs=10, glow=False):
    bm = bmesh.new()
    sweep(bm, [Vector(p) for p in points], r0, segs, radius_end=r1)
    return [(bm, swatch, 0.0, glow)]


def ball(center, size, swatch, subdiv=2, glow=False, rotation=(0, 0, 0)):
    bm = bmesh.new()
    blob(bm, center, size, subdiv, rotation)
    return [(bm, swatch, 0.0, glow)]


def ring(matrix, radius, minor, swatch, segs=16, glow=False):
    bm = bmesh.new()
    torus(bm, matrix, radius, minor, segs, 4)
    return [(bm, swatch, 0.0, glow)]


def flare(profile, swatch, segs=16):
    bm = bmesh.new()
    lathe(bm, profile, segs)
    return [(bm, swatch, 0.0, False)]


def the_flame(t, scale=1.0, outer=None, inner=None, length=None):
    r, h, o, i = FLAME[t]
    return flame(r * scale, h * (length or scale), outer or o, inner or i)


def stave_barrel(x, y, z0, swatch="Rust", r=0.56, h=1.2):
    pieces = []
    barrel = bmesh.new()
    lathe(barrel, [(0, 0), (r * 0.86, 0), (r, h * 0.25), (r * 1.07, h * 0.5), (r, h * 0.75), (r * 0.86, h), (0, h)], 16, M((x, y, z0)))
    pieces.append((barrel, swatch, 0.0, False))
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.3
        pts = [V(x + (r * 0.87 + r * 0.2 * math.sin(math.pi * zz / h)) * math.cos(a), y + (r * 0.87 + r * 0.2 * math.sin(math.pi * zz / h)) * math.sin(a), z0 + zz) for zz in (0.05, h * 0.25, h * 0.5, h * 0.75, h - 0.05)]
        s = bmesh.new()
        sweep(s, pts, 0.015, 4)
        pieces.append((s, "RustDark", 0.0, False))
    for zz in (0.22, 0.78):
        pieces += ring(M((x, y, z0 + h * zz)), r * 1.01, 0.04, "Iron", 16)
    pieces += place(cyl(r * 0.84, 0.08, "PineDark", 16), M((x, y, z0 + h - 0.02)))
    return pieces


def dragon_eye(r):
    """A glowing dragon eye facing +Z: a gold-yellow glowing dome, a slit pupil, a shine, a steel rim."""
    pieces = []
    dome = bmesh.new()
    lathe(dome, [(0, 0), (r, 0), (r * 0.93, r * 0.3), (r * 0.62, r * 0.5), (0, r * 0.56)], 16)
    pieces.append((dome, "LampYellow", 0.0, True))
    pieces += ball((0, 0, r * 0.5), (r * 0.14, r * 0.5, r * 0.1), "EyeDark", 2)
    pieces += ball((r * 0.3, r * 0.28, r * 0.48), (r * 0.12, r * 0.12, r * 0.06), "EyeWhite", 1, glow=True)
    pieces += ring(M((0, 0, 0.04)), r * 1.04, r * 0.12, "Gunmetal", 16)
    return pieces


def fire_spirit(s=1.0):
    """A cute fire spirit facing -Y: a flame body (glow) with big eyes and a smile."""
    pieces = flame(0.42 * s, 1.25 * s, "FlameOrange", "FlameYellow")
    for sx in (-1, 1):
        pieces += place(cartoon_eye(0.13 * s, None, look=(0.0, -0.1)), frame((sx * 0.15 * s, -0.5 * s, 0.5 * s), out=(sx * 0.25, -1, 0.1)))
    smile = bmesh.new()
    sweep(smile, [V(-0.1 * s, -0.5 * s, 0.33 * s), V(0, -0.53 * s, 0.29 * s), V(0.1 * s, -0.5 * s, 0.33 * s)], 0.025 * s, 6)
    pieces.append((smile, "EyeDark", 0.0, False))
    return pieces


def cart_wheel(r):
    """An iron-rimmed cart wheel facing +Z (turns about Z): rim, six spokes, a brass hub."""
    pieces = ring(Matrix(), r - 0.06, 0.08, "Iron", 20)
    for k in range(3):
        spoke = bmesh.new()
        rounded_block(spoke, (0.09, 2 * r - 0.15, 0.08), M((0, 0, 0), (0, 0, k * math.pi / 3)), corner=0.03, edge=0.02, corner_seg=1, edge_seg=1)
        pieces.append((spoke, "PineDark", 0.0, False))
    pieces += place(cyl(0.16, 0.26, "Brass", 10, bevel=0.0), M((0, 0, -0.13)))
    return pieces


def smoke(t, size=1.0):
    """A smoke puff stand-in (particles in game): grey smoke, magic sparkles on the Enchanted tier."""
    if t == 4:
        return tier_puff(4, 0.3 * size)
    pieces = []
    for k, (dx, dz, r) in enumerate(((0.0, 0.3, 0.2), (0.15, 0.7, 0.27), (-0.1, 1.15, 0.34))):
        pieces += ball((dx * size, 0, dz * size), (r * size,) * 3, "StoneLight" if k % 2 else "Stone", 2)
    return pieces


def ember_diamond(p, size, swatch):
    s = bmesh.new()
    lathe(s, [(0, -size), (size * 0.45, 0), (0, size)], 4, M(p, (0.3, 0.2, 0.7)))
    return [(faceted(s), swatch, 0.0, True)]


# ---------- tier 1: Scrappy, a torch on a stand ----------

def tier_scrappy(b):
    for L, W, sw, gr, loc, turn, seed in ((4.6, 1.0, "PineDark", "RustDark", (-0.1, -1.15, 0), 0.05, 0.0),
                                          (5.0, 1.0, "Pine", "PineDark", (0.1, -0.05, 0), -0.03, 1.3),
                                          (4.4, 0.95, "PineLight", "Pine", (0, 1.05, 0), 0.06, 2.1),
                                          (3.4, 0.9, "Pine", "PineDark", (0.5, 2.05, 0), -0.05, 0.7)):
        b.add("Planks", place(plank(L, W, 0.25, sw, gr, True, seed), M(loc, (0, 0, turn))))
    py = 0.5
    P = V(0, py, 3.3)
    D = T1_DIR
    b.add("Stand", grained_beam((0, py, 0.25), (0, py, 2.95), 0.46, "PineDark", "RustDark"))
    for foot in ((-1.35, py - 0.1, 0.25), (1.35, py + 0.1, 0.25), (0.0, py + 1.45, 0.25)):
        top = (foot[0] * 0.15, py + (foot[1] - py) * 0.15, 1.6)
        b.add("Stand", grained_beam(foot, top, 0.28, "Pine", "PineDark", faces=(1, 3)))
    b.add("Stand", place(block((0.42, 0.04, 0.5), "PatchGreen", corner=0.04, edge=0.02), M((0.02, py - 0.25, 1.95), (0, 0.15, 0))))
    for z in (2.05, 2.35):
        b.add("Stand", place(rivet(0.04, "RustDark"), front((0.02, py - 0.27, z))))
    for sx in (-1, 1):  # the iron fork the torch pivots in
        b.add("Stand", place(block((0.1, 0.4, 0.95), "Iron", corner=0.04, edge=0.03), M((sx * 0.27, py, 2.55))))
        b.add("Stand", place(rivet(0.1, "Iron"), frame((sx * 0.33, py, 3.3), out=(sx, 0, 0))))
    b.add("Stand", place(cyl(0.07, 0.66, "SteelDark", 8), frame((-0.33, py, 3.3), out=(1, 0, 0))))
    for z in (2.62, 2.9):  # rope lashing round the fork
        b.add("Stand", ring(M((0, py, z)), 0.36, 0.06, "PineLight", 12))
    # the torch: a long wooden shaft with rope lashings, a stone counterweight, a tin heat shield
    back, tip = P - D * 1.5, P + D * 1.9
    tm = frame(back, out=D)
    b.add("Torch", place(cyl(0.15, 3.4, "PineLight", 12), tm))
    for t in (0.4, 2.6):
        b.add("Torch", ring(tm @ M((0, 0, t)), 0.17, 0.05, "Cream", 12))
    b.add("Torch", ball(back + V(0, 0.05, -0.32), (0.32, 0.3, 0.26), "StoneDark", 1))
    b.add("Torch", tube([back + V(0, 0, 0.05), back + V(0, 0.05, -0.2)], 0.035, 0.035, "PineLight", 6))
    shield = frame(P + D * 0.95, out=D)
    b.add("Torch", place(cyl(0.62, 0.06, "Steel", 16), shield))
    b.add("Torch", place(rivet_ring(0.5, 6, 0.045, "RustDark"), shield @ M((0, 0, 0.06))))
    b.add("Torch", place(riveted_plate(0.36, 0.3, 0.03, "Rust", "RustDark", 0.5), shield @ M((0.22, 0.2, 0.06), (0, 0, 0.3))))
    # the head: an iron basket of oily rags with a rusty spout poking out (the nozzle)
    hm = frame(tip, out=D)
    b.add("Head", flare([(0, 0), (0.2, 0), (0.44, 0.5), (0.48, 0.62), (0.42, 0.62), (0.18, 0.08), (0, 0.08)], "Iron", 12), hm)
    for z in (0.25, 0.5):
        b.add("Head", ring(hm @ M((0, 0, z)), 0.3 + 0.28 * z, 0.035, "SteelDark", 12))
    b.add("Head", ball((0, 0, 0.4), (0.36, 0.36, 0.24), "Cream", 1), hm)
    b.add("Head", ball((0.12, 0.08, 0.5), (0.22, 0.2, 0.15), "PatchGreen", 1), hm)
    b.add("Head", place(cyl(0.09, 0.55, "Rust", 10), hm @ M((0, 0, 0.2))))
    b.add("Head", place(cyl(0.12, 0.08, "RustDark", 10), hm @ M((0, 0, 0.7))))
    # the fuel: a stave barrel with a hand pump, a hose up to a rusty pipe along the shaft
    bx, by = 1.95, 1.35
    b.add("Barrel", stave_barrel(bx, by, 0.25))
    b.add("Barrel", place(cyl(0.08, 0.7, "Iron", 8), M((bx + 0.2, by + 0.18, 1.45))))
    b.add("Barrel", tube([V(bx + 0.2, by + 0.18, 2.15), V(bx + 0.45, by + 0.18, 2.2), V(bx + 0.75, by + 0.18, 2.1)], 0.04, 0.04, "Iron", 6))
    b.add("Barrel", place(cyl(0.06, 0.3, "PineLight", 8), frame((bx + 0.75, by + 0.03, 2.1), out=(0, 1, 0))))
    under = tm.to_3x3() @ Vector((0, -0.21, 0))
    pipe_from, pipe_to = P - D * 0.8 + under, tip + D * 0.15 + under * 0.6
    b.add("Barrel", tube([pipe_from, pipe_to], 0.05, 0.05, "Rust", 8))
    for t in (0.2, 0.7):
        b.add("Barrel", ring(Matrix.Translation(pipe_from.lerp(pipe_to, t)) @ align_z(D), 0.07, 0.025, "Iron", 8))
    b.add("Barrel", cable((bx + 0.2, by + 0.18, 1.6), pipe_from, 0.35, 0.06, "Rubber", "RustDark"))
    # junk: a crate (the lamp stands on it), a sand bucket, a coil of rope
    b.add("Junk", place(block((0.9, 0.9, 0.75), "PineDark", corner=0.06, edge=0.05), M((-1.85, -0.9, 0.25))))
    b.add("Junk", trim_strip((-2.31, -1.36, 0.35), (-1.39, -1.36, 0.95), 0.06, "Pine"))
    bucket = bmesh.new()
    lathe(bucket, [(0, 0), (0.28, 0), (0.38, 0.5), (0.34, 0.5), (0.25, 0.06), (0, 0.06)], 12, M((-1.9, 1.2, 0.25)))
    b.add("Junk", [(bucket, "Steel", 0.0, False)])
    b.add("Junk", ball((-1.9, 1.2, 0.68), (0.32, 0.32, 0.08), "Cream", 1))
    b.add("Junk", tube([V(-2.26, 1.2, 0.73), V(-2.2, 1.2, 1.0), V(-1.9, 1.2, 1.12), V(-1.6, 1.2, 1.0), V(-1.54, 1.2, 0.73)], 0.022, 0.022, "Iron", 6))
    b.add("Junk", ring(M((1.5, -1.05, 0.31)), 0.32, 0.06, "PineLight", 12))
    work = frame(tip + D * 0.78, out=D)
    b.add("Flame", the_flame(1), work)
    return {"Work": work, "Lamp1": up_((-1.85, -0.9, 1.0)), "Lamp2": up_((bx - 0.2, by - 0.18, 1.45)),
            "Gear1": frame((0.42, py, 3.3), out=(1, 0, 0)), "Gauge1": front((bx, by - 0.61, 0.75)),
            "Steam1": up_(tip + V(0, 0, 0.55)), "Steam2": up_((bx + 0.2, by + 0.18, 2.25)),
            "Hit": HIT, "Trail": work, "NamePlate": front((0, -1.75, 0.3)), "Aura": up_((0, 0, 0.3)),
            "Top": up_(back + V(0, 0, 0.2))}


# ---------- tier 2: Workshop, a brass flamethrower on an iron-wheeled cart ----------

def tier_workshop(b):
    for k, y in enumerate((-2.2, -1.1, 0.0, 1.1, 2.2)):
        b.add("Deck", place(plank(6.6, 1.06, 0.26, "Pine", "PineDark", k in (0, 4), k * 1.1), M((0, y, 1.0))))
    for sy in (-1, 1):
        b.add("Frame", beam_between((-3.35, sy * 2.35, 0.86), (3.35, sy * 2.35, 0.86), 0.3, swatch="Iron"))
        b.add("Frame", place(cyl(0.12, 7.3, "SteelDark", 10), frame((-3.65, sy * 1.85, 0.65), out=(1, 0, 0))))
        for sx in (-1, 1):
            b.add("Frame", place(cyl(0.22, 0.12, "Brass", 12, bevel=0.0), frame((sx * 3.3, sy * 2.35, 0.86), out=(sx, 0, 0))))
            wheel = frame((sx * 3.5, sy * 1.85, 0.65), out=(sx, 0, 0))
            b.add("Wheel" + ("L" if sx < 0 else "R"), cart_wheel(0.65), wheel)
    for sx in (-1, 1):
        b.add("Frame", beam_between((sx * 3.2, -2.35, 0.86), (sx * 3.2, 2.35, 0.86), 0.28, swatch="Iron"))
    # two riveted fuel tanks at the back with copper bands, valves and a manifold
    for sx, sw in ((-1, "Brass"), (1, "Copper")):
        x, y, z0 = sx * 1.35, 1.5, 1.26
        tank = bmesh.new()
        lathe(tank, [(0, 0), (0.6, 0), (0.72, 0.15), (0.72, 2.6), (0.6, 2.9), (0.3, 3.05), (0, 3.08)], 16, M((x, y, z0)))
        b.add("Tanks", [(tank, sw, 0.0, False)])
        for z in (0.55,):
            b.add("Tanks", ring(M((x, y, z0 + z)), 0.74, 0.07, "Copper" if sw == "Brass" else "Brass", 16))
        b.add("Tanks", place(cyl(0.09, 0.3, "Iron", 8), M((x, y, z0 + 3.0))))
        b.add("Tanks", ring(M((x, y, z0 + 3.3)), 0.2, 0.04, "WarnRed", 12))
        for a in (0, math.pi / 2):
            b.add("Tanks", place(block((0.4, 0.05, 0.04), "WarnRed", corner=0.01, edge=0.01), M((x, y, z0 + 3.28), (0, 0, a))))
        b.add("Tanks", cable((x - sx * 0.3, y - 0.62, z0 + 1.2), (sx * 0.3, 0.8, 3.65), 0.25, 0.1, "Rubber", "Brass"))
    b.add("Tanks", pipe_between((-1.35, 1.5, 4.05), (1.35, 1.5, 4.05), 0.1, "Copper"))
    # a small pump-house and a chimney with bands and a spark cap
    b.add("Pump", place(block((1.3, 0.9, 0.8), "Iron", corner=0.15, edge=0.08), M((0, 2.25, 1.26))))
    b.add("Pump", place(block((1.38, 0.98, 0.22), "SteelDark", corner=0.17, edge=0.08), M((0, 2.25, 2.06))))
    b.add("Pump", pipe_between((0, 2.25, 2.3), (0, 2.25, 5.8), 0.2, "Brass"))
    for z in (4.6,):
        b.add("Pump", ring(M((0, 2.25, z)), 0.22, 0.05, "Copper", 12))
    b.add("Pump", flare([(0, 0), (0.32, 0), (0.38, 0.14), (0.26, 0.32), (0, 0.36)], "Copper", 14), M((0, 2.25, 5.8)))
    # the gun mount: an iron flange, a brass column, a swivel plate and a yoke on a trunnion
    P, D = V(0, -0.7, 3.35), T2_DIR
    b.add("Mount", flare([(0, 0), (0.75, 0), (0.75, 0.12), (0.45, 0.3), (0, 0.3)], "Iron", 16), M((0, -0.7, 1.26)))
    b.add("Mount", place(rivet_ring(0.6, 6, 0.06, "Iron"), M((0, -0.7, 1.38))))
    b.add("Mount", place(cyl(0.34, 1.4, "Brass", 14), M((0, -0.7, 1.5))))
    b.add("Mount", place(cyl(0.62, 0.16, "Brass", 16), M((0, -0.7, 2.75))))
    for sx in (-1, 1):
        b.add("Mount", place(block((0.14, 0.62, 0.85), "Brass", corner=0.05, edge=0.04), M((sx * 0.5, -0.7, 2.85))))
        b.add("Mount", place(bolt(0.09, "Iron"), frame((sx * 0.58, -0.7, 3.35), out=(sx, 0, 0))))
    # the brass flamethrower: a breech with a dial and a grip, cooling fins, a gun shield, a flared nozzle
    gm = frame(P, out=D)
    b.add("Gun", place(cyl(0.26, 3.4, "Brass", 14), gm @ M((0, 0, -1.2))))
    b.add("Gun", place(block((0.8, 0.75, 1.1), "Copper", corner=0.15, edge=0.08), gm @ M((0, 0, -1.55))))
    b.add("Gun", place(rivet_ring(0.3, 6, 0.05, "Brass"), gm @ M((0, 0, -1.56), (math.pi, 0, 0))))
    b.add("Gun", place(dial(0.22, "Cream", "Brass", "WarnRed", 0.4), gm @ M((0.41, 0, -0.95)) @ Matrix.Rotation(math.pi / 2, 4, "Y")))
    b.add("Gun", place(handle(0.5, 0.24, 0.045, "SteelDark", "Iron"), gm @ M((0, 0.38, -1.0)) @ Matrix.Rotation(-math.pi / 2, 4, "X")))
    b.add("Gun", place(cyl(0.07, 0.6, "PineDark", 8), gm @ M((0, -0.3, -0.8)) @ Matrix.Rotation(math.pi / 2 + 0.3, 4, "X")))
    for t in (0.9, 1.2, 1.5):
        b.add("Gun", ring(gm @ M((0, 0, t)), 0.3, 0.06, "Iron", 14))
    b.add("Gun", place(block((1.7, 1.2, 0.08), "Iron", corner=0.2, edge=0.03), gm @ M((0, 0.2, 0.3))))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add("Gun", place(rivet(0.06, "Brass"), gm @ M((sx * 0.7, 0.2 + sy * 0.45, 0.38))))
    b.add("Gun", flare([(0, 0), (0.3, 0), (0.3, 0.12), (0.42, 0.42), (0.48, 0.55), (0.4, 0.56), (0.22, 0.32), (0, 0.3)], "Brass", 16), gm @ M((0, 0, 2.2)))
    b.add("Gun", ring(gm @ M((0, 0, 2.27)), 0.31, 0.05, "Copper", 14))
    # a toolbox and two lamp posts at the front corners
    for sx in (-1, 1):
        b.add("Deck", place(cyl(0.08, 0.9, "Iron", 8), M((sx * 2.9, -2.3, 1.26))))
        b.add("Deck", place(cyl(0.2, 0.08, "Brass", 12), M((sx * 2.9, -2.3, 2.12))))
    work = gm @ M((0, 0, 2.76))
    b.add("Flame", the_flame(2), work)
    return {"Work": work, "Lamp1": up_((2.9, -2.3, 2.2)), "Lamp2": up_((-2.9, -2.3, 2.2)),
            "Gear1": up_((0, -0.7, 2.2)), "Gauge1": front((-1.35, 0.77, 3.25)), "Gauge2": front((1.35, 0.77, 3.25)),
            "Steam1": up_((0, 2.25, 6.2)), "Steam2": up_((1.35, 1.5, 4.6)), "Hit": HIT, "Trail": work,
            "NamePlate": front((0, -2.52, 0.86)), "Aura": up_((0, 0, 1.26)), "Top": up_((0, 2.25, 6.2))}


# ---------- tier 3: Frost-tech, a blue-flame crystal cannon ----------

def tier_frosttech(b):
    b.add("Deck", block((9.6, 8.6, 0.8), "SnowWhite", corner=1.4, edge=0.3))
    b.add("Deck", place(block((8.6, 7.6, 0.3), "IceBlue", corner=1.1, edge=0.12), M((0, 0, 0.8))))
    for x in (-2.4, 2.4):
        b.add("Deck", place(inset_panel(1.8, 1.2, 0.05, "FrostLight", "GlacierBlue", True), M((x, -2.4, 1.1))))
    for sx in (-1, 1):
        b.add("Deck", place(vent(1.4, 0.4, 5, "GlacierBlue", "SteelLight"), front((sx * 2.7, -4.29, 0.42))))
        for sy in (-1, 1):
            b.add("Deck", place(bolt(0.1, "SteelLight", "GlacierBlue"), M((sx * 4.0, sy * 3.5, 1.1))))
    for p0, p1 in (((-3.4, -4.33, 0.42), (3.4, -4.33, 0.42)), ((-3.2, 4.33, 0.42), (3.2, 4.33, 0.42)),
                   ((-4.83, -2.6, 0.42), (-4.83, 2.6, 0.42)), ((4.83, -2.6, 0.42), (4.83, 2.6, 0.42))):
        b.add("Deck", trim_strip(p0, p1, 0.16, "AuroraCyan", True))
    # the pedestal: a white housing with a screen, a turntable, a rotating base and the yoke
    py = 0.3
    b.add("Pedestal", place(block((2.8, 2.8, 1.4), "SnowWhite", corner=0.9, edge=0.35), M((0, py, 1.1))))
    b.add("Pedestal", place(block((2.86, 2.86, 0.08), "GlacierBlue", corner=0.93, edge=0.03), M((0, py, 1.75))))
    b.add("Pedestal", place(screen(0.9, 0.5, "AuroraCyan", "NavyIce", 3), front((-0.45, py - 1.4, 1.95))))
    b.add("Pedestal", place(cyl(1.3, 0.25, "GlacierBlue", 20), M((0, py, 2.5))))
    b.add("Pedestal", ring(M((0, py, 2.62)), 1.3, 0.05, "AuroraCyan", 20, True))
    b.add("Turret", place(block((2.4, 2.0, 0.6), "SteelLight", corner=0.5, edge=0.15), M((0, py, 2.75))))
    for sx in (-1, 1):
        b.add("Turret", place(block((0.3, 0.9, 1.7), "SnowWhite", corner=0.14, edge=0.1), M((sx * 1.02, py, 3.3))))
        b.add("Turret", trim_strip((sx * 1.18, py - 0.25, 3.5), (sx * 1.18, py - 0.25, 4.8), 0.07, "AuroraCyan", True))
        b.add("Turret", place(cyl(0.2, 0.3, "SteelLight", 12), frame((sx * 0.82, py, 4.4), out=(sx, 0, 0))))
        b.add("Turret", place(cyl(0.12, 0.08, "AuroraCyan", 10), frame((sx * 1.17, py, 4.4), out=(sx, 0, 0))))
    # the cannon: a sleek white barrel with ice-blue bands, glowing coil rings and a steel muzzle
    P, D = V(0, py, 4.4), T3_DIR
    cm = frame(P - D * 2.0, out=D)
    b.add("Cannon", flare([(0, 0), (0.5, 0), (0.72, 0.3), (0.78, 1.4), (0.68, 2.4), (0.5, 3.4), (0.46, 4.3), (0, 4.3)], "SnowWhite", 20), cm)
    for z, r in ((0.45, 0.75), (2.2, 0.71)):
        b.add("Cannon", ring(cm @ M((0, 0, z)), r, 0.06, "GlacierBlue", 20))
    b.add("Cannon", place(vent(0.7, 0.4, 3, "GlacierBlue", "SteelLight"), cm @ M((0, -0.72, 1.4)) @ Matrix.Rotation(math.pi / 2, 4, "X")))
    b.add("CannonCoils", ring(cm @ M((0, 0, 2.9)), 0.6, 0.09, "AuroraCyan", 16, True))
    b.add("CannonCoils", ring(cm @ M((0, 0, 3.35)), 0.55, 0.09, "AuroraCyan", 16, True))
    b.add("CannonCoils", ring(cm @ M((0, 0, 3.8)), 0.52, 0.09, "AuroraCyan", 16, True))
    b.add("Cannon", flare([(0, 0), (0.5, 0), (0.56, 0.3), (0.62, 0.52), (0.5, 0.55), (0.34, 0.4), (0, 0.38)], "SteelLight", 16), cm @ M((0, 0, 4.28)))
    b.add("Cannon", ring(cm @ M((0, 0, 4.5)), 0.6, 0.05, "CrystalCyan", 16, True))
    b.add("Cannon", place(bolt_ring(0.62, 6, 0.06, "SteelLight"), cm @ M((0, 0, 0.02), (math.pi, 0, 0))))
    # the crystal chamber on the barrel's back: a steel cradle, cage bars, a cap and a big crystal
    ch = cm @ M((0, 0.62, 1.0)) @ Matrix.Rotation(-math.pi / 2, 4, "X")
    b.add("Chamber", place(cyl(0.55, 0.25, "SteelLight", 16), ch))
    b.add("Chamber", place(cut_crystal(1.5, 0.36, "CrystalCyan", sides=6), ch @ M((0, 0, 0.2))))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        b.add("Chamber", place(cyl(0.05, 1.45, "GlacierBlue", 6), ch @ M((0.48 * math.cos(a), 0.48 * math.sin(a), 0.22))))
    b.add("Chamber", place(cyl(0.55, 0.16, "SteelLight", 16), ch @ M((0, 0, 1.65))))
    b.add("Chamber", ring(ch @ M((0, 0, 1.0)), 0.5, 0.04, "AuroraCyan", 16, True))
    # two crystal pylons at the back power it, with cables to the pedestal
    for sx in (-1, 1):
        x, y = sx * 3.4, 2.6
        b.add("Pylons", place(block((1.5, 1.4, 0.6), "SteelLight", corner=0.35, edge=0.12), M((x, y, 1.1))))
        b.add("Pylons", place(coil(0.5, 3.2, 6, "SteelDark", "IceBlue", "AuroraCyan"), M((x, y, 1.7))))
        b.add("Pylons", place(cyl(0.6, 0.2, "GlacierBlue", 14), M((x, y, 5.35))))
        b.add("Pylons", place(cut_crystal(2.0, 0.42, "CrystalCyan", sides=6), M((x, y, 5.5))))
        for k in range(3):
            a = k * 2 * math.pi / 3 + 0.5
            b.add("Pylons", place(cut_crystal(0.8, 0.18, "IceBlue", (0.4 * math.cos(a), 0.4 * math.sin(a)), glow=False), M((x + 0.38 * math.cos(a), y + 0.38 * math.sin(a), 5.5))))
        b.add("Cables", cable((x - sx * 0.7, y - 0.3, 1.4), (sx * 1.35, py + 0.6, 1.5), 0.15, 0.1, "NavyIce", "GlacierBlue"))
    b.add("Cables", cable((-0.6, py + 1.0, 2.9), (0, P.y + 1.9 - 0.4, 5.0), 0.3, 0.09, "NavyIce", "GlacierBlue", ribs=3))
    for k in range(6):  # radial cooling fins round the breech
        a = k * math.pi / 3 + math.pi / 6
        fin = bmesh.new()
        rounded_block(fin, (0.1, 0.32, 0.8), M((0.82 * math.cos(a), 0.82 * math.sin(a), 0.7), (0, 0, a + math.pi / 2)), corner=0.04, edge=0.03, taper=0.8)
        b.add("CannonFins", [(fin, "GlacierBlue", 0.0, False)], cm)
    b.add("CannonFins", place(screen(0.5, 0.3, "AuroraCyan", "NavyIce", 2), cm @ M((0.55, 0.45, 1.75)) @ frame((0, 0, 0), out=(0.7, 0.7, 0))))
    for sx in (-1, 1):  # side vents on the pedestal, crystal clusters at the deck's front corners
        b.add("Pedestal", place(vent(1.2, 0.6, 4, "GlacierBlue", "SteelLight"), frame((sx * 1.41, py, 1.8), out=(sx, 0, 0))))
        b.add("DeckCrystals", place(cut_crystal_cluster(0.55, "CrystalCyan", "FrostLight", 5), M((sx * 3.7, -3.1, 1.1), (0, 0, sx * 0.6))))
        b.add("Pylons", place(inset_panel(0.9, 0.4, 0.04, "FrostLight", "GlacierBlue", False), frame((sx * 3.4, 2.6 - 0.71, 1.62), out=(0, -1, 0))))
    b.add("Deck", place(cyl(0.55, 0.12, "GlacierBlue", 6), front((0, -4.3, 0.42))))
    for k in range(3):
        b.add("Deck", place(block((0.12, 0.8, 0.08), "SnowWhite", corner=0.03, edge=0.02), front((0, -4.42, 0.42)) @ M((0, 0, 0), (0, 0, k * math.pi / 3))))
    work = cm @ M((0, 0, 4.82))
    b.add("Flame", the_flame(3), work)
    return {"Work": work, "Lamp1": up_((1.02, py, 5.0)), "Lamp2": up_((-1.02, py, 5.0)),
            "Gear1": front((0.65, py - 1.42, 1.85)), "Gauge1": front((-3.4, 1.89, 1.4)), "Gauge2": front((3.4, 1.89, 1.4)),
            "Steam1": up_((-3.4, 2.6, 7.5)), "Steam2": up_((3.4, 2.6, 7.5)), "Hit": HIT, "Trail": work,
            "NamePlate": front((-2.4, -4.32, 0.4)), "Aura": up_((0, 0, 1.1)), "Top": up_((3.4, 2.6, 7.5))}


# ---------- tier 4: Enchanted, a floating brazier with fire spirits ----------

def tier_enchanted(b):
    dais = bmesh.new()
    lathe(dais, [(0, 0), (5.1, 0), (5.1, 0.3), (4.9, 0.35), (4.9, 0.55), (4.6, 0.8), (0, 0.8)], 6)
    b.add("Dais", [(dais, "Moonstone", 0.04, False)])
    plinth = bmesh.new()
    lathe(plinth, [(0, -0.01), (5.25, -0.01), (5.25, 0.18), (0, 0.18)], 6)
    b.add("Dais", [(plinth, "StoneDark", 0.03, False)])
    b.add("Dais", place(trim_ring(4.77, 0, "RuneViolet", minor=0.08, segments=6), M((0, 0, 0.56))))
    b.add("DaisRunes", place(engraved_rune_ring(3.5, "RuneGlow", "ArcaneDeep", "RuneViolet", 14), M((0, 0, 0.8))))
    for k in range(6):
        a = k * math.pi / 3
        if k in (1, 2):  # the back corners carry the obelisks
            pass
        else:
            b.add("DaisCrystals", place(cut_crystal_cluster(0.5, "FlameOrange" if k % 2 else "MagicPink", "Moonstone", 4), M((4.5 * math.cos(a), 4.5 * math.sin(a) * 0.95, 0.78), (0, 0, a))))
        fa = a + math.pi / 6
        apothem = 5.1 * math.cos(math.pi / 6)
        b.add("Dais", place(gem_setting(0.14, "FlameOrange", "Gold", 4), frame((apothem * math.cos(fa), apothem * math.sin(fa), 0.18), out=(math.cos(fa), math.sin(fa), 0))))
    # the stone column with gold rings and runes
    cy = 1.0
    col = bmesh.new()
    lathe(col, [(0, 0.8), (1.15, 0.8), (1.15, 1.2), (0.85, 1.4), (0.66, 1.6), (0.58, 4.2), (0.85, 4.45), (0.92, 4.8), (0, 4.8)], 12, M((0, cy, 0)))
    b.add("Column", [(col, "Moonstone", 0.0, False)])
    for z, r in ((1.32, 0.98), (4.42, 0.82)):
        b.add("Column", place(trim_ring(r, 0, "Gold", minor=0.07, segments=16), M((0, cy, z))))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        b.add("ColumnGlow", place(rune_glyph(0.36, k + 1, "RuneGlow", 0.03), frame((0.62 * math.cos(a), cy + 0.62 * math.sin(a), 3.2), out=(math.cos(a), math.sin(a), 0))))
    # the floating golden brazier: a gem underneath, glowing coals, magic fire, a spinning rune ring
    bz = 5.6
    bowl = bmesh.new()
    lathe(bowl, [(0, 0), (0.4, 0), (0.7, 0.2), (1.5, 0.8), (1.9, 1.3), (1.98, 1.45), (1.82, 1.47), (1.4, 1.05), (0, 0.95)], 16, M((0, cy, bz)))
    b.add("Brazier", [(bowl, "Gold", 0.0, False)])
    b.add("Brazier", place(trim_ring(1.52, 0, "ArcaneDeep", minor=0.07, segments=16), M((0, cy, bz + 0.82))))
    for k in range(6):
        a = k * math.pi / 3 + math.pi / 6
        b.add("Brazier", place(gem_setting(0.13, "MagicPink" if k % 2 else "AuroraCyan", "Gold", 4), frame((1.62 * math.cos(a), cy + 1.62 * math.sin(a), bz + 0.95), out=(math.cos(a), math.sin(a), 0.6))))
    b.add("Brazier", place(cut_gem(0.42, "RuneViolet"), M((0, cy, bz - 0.35))))
    b.add("BrazierFire", ball((0, cy, bz + 1.05), (1.2, 1.2, 0.3), "FlameOrange", 2, glow=True))
    b.add("BrazierFire", flame(1.0, 2.6, "MagicPink", "FlameYellow"), M((0, cy, bz + 1.05)))
    b.add("Orbit", place(engraved_rune_ring(2.5, "RuneGlow", "ArcaneDeep", "Moonstone", 12), M((0, cy, bz + 0.3), (0.22, 0.1, 0))))
    # above it, a floating halo and a violet crystal
    b.add("Crown", place(cut_crystal(1.3, 0.3, "RuneViolet", sides=6), M((0, cy, 10.1))))
    b.add("Crown", ring(M((0, cy, 10.5), (math.pi / 2, 0, 0.4)), 0.7, 0.045, "Gold", 24))
    # the nozzle: a floating golden horn aimed at the ice, a gem collar and a rune ring round its bell
    D = T4_DIR
    horn = spline([(0, -0.9, 6.05), (0, -1.6, 5.75), (0, -2.3, 5.25), (0, -3.0, 4.9)], 4)
    b.add("Horn", tube(horn, 0.12, 0.32, "Gold", 12))
    end = horn[-1]
    hm = frame(end, out=D)
    b.add("Horn", flare([(0, -0.05), (0.3, -0.05), (0.45, 0.2), (0.62, 0.4), (0.56, 0.44), (0.32, 0.25), (0, 0.22)], "Gold", 16), hm)
    b.add("Horn", place(trim_ring(0.31, 0, "Moonstone", minor=0.08, segments=14), hm @ M((0, 0, -0.35))))
    for k in range(4):
        a = k * math.pi / 2
        b.add("Horn", place(cut_gem(0.08, "MagicPink"), hm @ M((0.38 * math.cos(a), 0.38 * math.sin(a), -0.35))))
    b.add("HornRing", place(engraved_rune_ring(0.9, "RuneGlow", "ArcaneDeep", "RuneViolet", 8), hm @ M((0, 0, 0.15))))
    # two obelisks at the back with glowing runes (the lamps sit on top)
    for sx in (-1, 1):
        x, y = sx * 3.4, 1.4
        ob = bmesh.new()
        rounded_block(ob, (0.9, 0.9, 2.4), M((x, y, 2.0)), corner=0.15, edge=0.1, taper=0.7)
        b.add("Obelisks", [(ob, "StoneDark", 0.0, False)])
        b.add("Obelisks", place(block((0.75, 0.75, 0.12), "Gold", corner=0.1, edge=0.04), M((x, y, 3.2))))
        b.add("ObelisksGlow", place(rune_glyph(0.4, 3 + sx, "RuneGlow", 0.03), frame((x, y - 0.4, 2.55), out=(0, -1, 0.06))))
    # the fire spirits, each its own mesh so it can bob and orbit
    for k, (p, yaw, s) in enumerate((((2.7, -1.0, 3.4), 0.5, 1.0), ((-2.8, -0.2, 5.0), -0.5, 0.9), ((2.0, 2.9, 7.4), 0.9, 0.8))):
        b.add("Spirit" + "ABC"[k], fire_spirit(s), M(p, (0, 0, yaw)))
    work = frame(end + D * 0.42, out=D)
    b.add("Flame", the_flame(4), work)
    return {"Work": work, "Lamp1": up_((3.4, 1.4, 3.26)), "Lamp2": up_((-3.4, 1.4, 3.26)),
            "Gear1": front((0, cy - 0.6, 2.6)), "Gauge1": front((-3.4, 0.99, 1.5)), "Gauge2": front((3.4, 0.99, 1.5)),
            "Steam1": up_((0, cy, 9.0)), "Steam2": up_((0, -3.0, 5.5)), "Hit": HIT, "Trail": work,
            "NamePlate": front((0, -4.45, 0.4)), "Aura": up_((0, 0, 0.8)), "Top": up_((0, cy, 11.45))}


# ---------- tier 5: Legendary, the Dragon Turret ----------

class Surface:
    """Measures a finished organic mesh so parts sit on its surface."""

    def __init__(self, bm):
        self.points = [v.co.copy() for v in bm.verts]

    def near(self, a, b, axes, reach):
        found = [p for p in self.points if abs(p[axes[0]] - a) < reach and abs(p[axes[1]] - b) < reach]
        while not found:
            reach *= 1.5
            found = [p for p in self.points if abs(p[axes[0]] - a) < reach and abs(p[axes[1]] - b) < reach]
        return found

    def front(self, x, z, reach=0.2):
        return min(p.y for p in self.near(x, z, (0, 2), reach))

    def top(self, x, y, reach=0.2):
        return max(p.z for p in self.near(x, y, (0, 1), reach))

    def bottom(self, x, y, reach=0.2):
        return min(p.z for p in self.near(x, y, (0, 1), reach))

    def side(self, y, z, reach=0.2):
        return max(p.x for p in self.near(y, z, (1, 2), reach))


def dragon_head():
    """The upper head in its own frame (front -Y, the neck socket near the origin): a round skull with a
    domed brow, narrowing and flattening into a snout with a flat underside where the mouth opens."""
    cage = cage_box((2.5, 3.9, 1.9), 2)
    radii = Vector((1.25, 1.95, 0.95))
    for v in cage.verts:
        unit = Vector((v.co.x / radii.x, v.co.y / radii.y, v.co.z / radii.z))
        if unit.length > 1e-6:
            unit.normalize()
            v.co = v.co.lerp(Vector((unit.x * radii.x, unit.y * radii.y, unit.z * radii.z)) * 1.04, 0.8)
    for v in cage.verts:
        x, y, z = v.co
        s = min(1.0, max(0.0, (-y - 0.1) / 1.85))
        v.co.x = x * (1 - 0.34 * s)
        if z > 0:
            v.co.z = z * (1 - 0.4 * s) + (0.2 if y > 0.3 else 0.0)
        else:
            v.co.z = z * (0.5 + 0.5 * min(1.0, max(0.0, (y + 0.2) / 1.0)))
    head = subsurf(cage, 2)
    head.transform(M((0, -1.25, 0.35)))
    return head


def dragon_jaw():
    """The lower jaw in its own frame: centred on the origin, front -Y, narrowing to the chin."""
    cage = cage_box((1.9, 3.0, 0.5), 1)
    for v in cage.verts:
        s = min(1.0, max(0.0, -v.co.y / 1.5))
        v.co.x *= 1 - 0.38 * s
        if v.co.z < 0:
            v.co.z -= 0.12 * (1 - s)
    return subsurf(cage, 2)


JAW_M = Matrix.Translation((0, 0.15, -0.3)) @ Matrix.Rotation(JAW_OPEN, 4, "X") @ Matrix.Translation((0, -1.45, 0))
MOUTH_DIR = Vector((0, -math.cos(JAW_OPEN / 2), -math.sin(JAW_OPEN / 2)))


def tier_dragon(b):
    # the plinth: gunmetal with gold trim, vents, gems and an aurora strip
    b.add("Platform", block((11.4, 11.4, 0.9), "Gunmetal", corner=1.0, edge=0.25))
    b.add("Platform", place(block((10.8, 10.8, 0.3), "StoneLight", corner=0.8, edge=0.1), M((0, 0, 0.9))))
    b.add("Trim", place(block((11.5, 11.5, 0.16), "Gold", corner=1.02, edge=0.06), M((0, 0, 0.72))))
    b.add("Trim", trim_strip((-2.4, -5.72, 0.4), (2.4, -5.72, 0.4), 0.16, "AuroraCyan", True))
    for sx in (-1, 1):
        b.add("Platform", place(vent(1.8, 0.4, 5, "Gunmetal", "SteelDark"), front((sx * 3.6, -5.69, 0.45))))
        for sy in (-1, 1):
            b.add("Platform", place(gem_setting(0.18, "AuroraCyan", "Gold", 4), M((sx * 5.1, sy * 5.1, 1.2))))
    # the turret drum: armour plates with rivets, a big turret gear ring, a crest at the front
    cx, cy = 0.0, 0.6
    drum = bmesh.new()
    lathe(drum, [(0, 1.2), (4.0, 1.2), (4.0, 1.5), (3.8, 1.62), (3.8, 3.6), (3.6, 3.9), (3.3, 4.0), (0, 4.0)], 24, M((cx, cy, 0)))
    b.add("Drum", [(drum, "Gunmetal", 0.0, False)])
    b.add("Drum", place(rivet_ring(3.9, 16, 0.07, "Gold"), M((cx, cy, 1.5))))
    b.add("Drum", place(trim_ring(3.82, 0, "Gold", minor=0.07, segments=24), M((cx, cy, 1.75))))
    b.add("TurretRing", place(gear(3.95, 40, 0.28, 0.16, "Brass", "Gold"), M((cx, cy, 3.62))))
    for deg in (30, 150, 210, 330):
        a = math.radians(deg)
        n = Vector((math.cos(a), math.sin(a), 0))
        b.add("Armour", place(riveted_plate(1.7, 1.5, 0.1, "SteelLight", "Gold", 0.75), frame((cx + 3.8 * n.x, cy + 3.8 * n.y, 2.6), out=n)))
    b.add("Drum", place(crest(1.4, 1.7, 0.2, "Gold", "NavyIce", "FlameYellow", "FlameOrange"), front((cx, cy - 3.83, 2.65), 0.0)))
    b.add("Drum", place(vent(1.2, 0.5, 4, "SteelDark", "Gunmetal"), frame((cx, cy + 3.83, 2.6), out=(0, 1, 0))))
    # fuel tanks at the back corners: copper with gold bands, valves and ribbed hoses into the dragon
    for sx in (-1, 1):
        x, y = sx * 4.2, 4.0
        tank = bmesh.new()
        lathe(tank, [(0, 0), (0.8, 0), (0.9, 0.2), (0.9, 3.4), (0.75, 3.85), (0.4, 4.1), (0, 4.15)], 16, M((x, y, 1.2)))
        b.add("Tanks", [(tank, "Copper", 0.0, False)])
        for z in (1.9, 3.9):
            b.add("Tanks", ring(M((x, y, z)), 0.92, 0.08, "Gold", 16))
        b.add("Tanks", place(riveted_plate(0.9, 0.6, 0.05, "Gunmetal", "Gold", 0.4), frame((x - sx * 0.62, y - 0.62, 2.9), out=(-sx, -1, 0))))
        b.add("Tanks", place(flare([(0, 0), (0.22, 0), (0.22, 0.25), (0, 0.25)], "Iron", 10), frame((x + sx * 0.88, y, 4.0), out=(sx, 0, 0))))
        b.add("Tanks", ring(frame((x + sx * 1.15, y, 4.0), out=(sx, 0, 0)), 0.2, 0.04, "WarnRed", 12))
    # the dragon: a crouching body on the drum, a long neck, the head, forelegs gripping the rim, a tail
    b.add("Drum", place(trim_ring(3.42, 0, "Gold", minor=0.07, segments=24), M((cx, cy, 3.97))))
    before = set(b.parts)  # everything added from here on is the dragon (scaled up at the end)
    body_cage = cage_box((2.9, 2.9, 2.6), 1)
    radii = Vector((1.45, 1.45, 1.3))
    for v in body_cage.verts:
        unit = Vector((v.co.x / radii.x, v.co.y / radii.y, v.co.z / radii.z))
        if unit.length > 1e-6:
            unit.normalize()
            v.co = v.co.lerp(Vector((unit.x * radii.x, unit.y * radii.y, unit.z * radii.z)) * 1.05, 0.75)
    body = subsurf(body_cage, 2)
    body.transform(M((0, 1.3, 5.15)))
    bs = Surface(body)
    b.add("Body", [(body, "WarnRedDark", 0.0, False)], organic=True)
    for k, z in enumerate((4.45, 4.95, 5.45, 5.95)):  # cream belly plates down the chest
        n = Vector((0, -1, (z - 5.15) * 0.8)).normalized()
        b.add("Body", ball((0, 0, 0), (0.95 - 0.08 * abs(k - 1.5), 0.26, 0.14), "Cream", 2), frame((0, bs.front(0, z) + 0.06, z), out=n, up=(0, 0, 1)))
    b.add("Body", place(riveted_plate(1.6, 1.3, 0.08, "Gunmetal", "Gold", 0.5), frame((0, 2.62, 5.75), out=(0, 1, 0.8))))
    head_m = Matrix.Translation((0, -0.35, 8.85)) @ Matrix.Rotation(HEAD_PITCH, 4, "X")
    neck_end = head_m @ Vector((0, 0.35, 0.15))
    neck = spline([(0, 1.15, 5.5), (0, 1.15, 6.7), (0, 0.85, 7.8), neck_end + V(0, 0.5, -0.3), neck_end], 4)
    b.add("Neck", tube(neck, 0.98, 0.66, "WarnRedDark", 16), organic=True)
    for i, p in enumerate(neck):
        t = i / (len(neck) - 1)
        r = 0.98 + (0.66 - 0.98) * t
        tangent = (neck[min(i + 1, len(neck) - 1)] - neck[max(i - 1, 0)]).normalized()
        fwd = Vector((1, 0, 0)).cross(tangent).normalized()  # the throat side
        if 1 <= i <= len(neck) - 3:  # cream throat scales and gold back spikes
            b.add("NeckScales", ball((0, 0, 0), (r * 0.72, 0.36, 0.16), "Cream", 2), frame(p + fwd * (r * 0.86), out=fwd, up=tangent))
            if i % 2 == 0:
                b.add("NeckSpikes", cone(0.2, 0.55, "Gold", 8), frame(p - fwd * (r * 0.9), out=-fwd - tangent * 0.5, up=tangent))
    for t in (0.3, 0.62):  # riveted armour collars on the neck
        i = int(t * (len(neck) - 1))
        p, r = neck[i], 0.98 + (0.66 - 0.98) * t
        axis = (neck[i + 1] - neck[i - 1]).normalized()
        cm = Matrix.Translation(p) @ align_z(axis)
        b.add("NeckArmour", ring(cm, r + 0.04, 0.12, "Gunmetal", 20))
        for k in range(6):
            a = k * math.pi / 3
            n = cm.to_3x3() @ Vector((math.cos(a), math.sin(a), 0))
            b.add("NeckArmour", place(rivet(0.07, "Gold"), frame(p + n * (r + 0.15), out=n)))
    # forelegs: shoulders, elbow guards, paws gripping the drum's front rim with curved claws
    for sx in (-1, 1):
        sh, el, wr = V(sx * 1.15, 0.5, 5.55), V(sx * 1.85, -0.45, 5.2), V(sx * 1.55, -1.55, 4.38)
        b.add("Legs", tube(spline([sh, el, wr], 3), 0.5, 0.32, "WarnRedDark", 12), organic=True)
        b.add("Legs", ball(el + V(sx * 0.15, 0, 0.05), (0.42, 0.42, 0.42), "Gunmetal", 2))
        b.add("Legs", place(rivet(0.07, "Gold"), frame(el + V(sx * 0.55, 0, 0.1), out=(sx, 0, 0.2))))
        paw = cage_box((0.8, 0.9, 0.45), 0)
        paw = subsurf(paw, 2)
        paw.transform(M(wr + V(0, -0.3, -0.12)))
        b.add("Legs", [(paw, "WarnRedDark", 0.0, False)], organic=True)
        for k in (-1, 0, 1):
            b.add("Legs", place(curved_claw(0.55, 0.11, 0.5, "Cream"), frame(wr + V(k * 0.26, -0.72, -0.15), out=(0, -0.5, -1), up=(0, 1, 0))))
    # the tail curls round the drum top and ends in a gold spade
    tail = spline([(0, 2.4, 4.6), (0.85, 2.85, 4.42), (1.8, 2.85, 4.25), (2.55, 2.0, 4.18), (2.75, 0.9, 4.15)], 4)
    b.add("Tail", tube(tail, 0.55, 0.12, "WarnRedDark", 12), organic=True)
    for i in range(2, len(tail) - 2, 3):
        b.add("Tail", cone(0.14, 0.38, "Gold", 8), M(tail[i] + V(0, 0, 0.42 - 0.025 * i)))
    spade = bmesh.new()
    lathe(spade, [(0, 0), (0.32, 0.2), (0.28, 0.45), (0, 0.75)], 4, frame(tail[-1] - V(0, 0.05, 0), out=(0.1, -1, 0)) @ Matrix.Diagonal((1, 0.35, 1, 1)))
    b.add("Tail", [(faceted(spade), "Gold", 0.0, False)])
    # the head: subdivided skull and jaw, glowing slit eyes, brows, horns, crown, teeth, nostrils
    head = dragon_head()
    hs = Surface(head)
    b.add("Head", [(head, "WarnRedDark", 0.0, False)], head_m, organic=True)
    jaw = dragon_jaw()
    js = Surface(jaw)
    b.add("Jaw", [(jaw, "WarnRedDark", 0.0, False)], head_m @ JAW_M, organic=True)
    b.add("Jaw", ball((0, -0.25, 0.22), (0.55, 1.05, 0.12), "Blush", 2), head_m @ JAW_M)
    b.add("Mouth", ball((0, -0.9, -0.45), (0.8, 1.15, 0.62), "Rubber", 2), head_m)
    for x, y, big in ((0.6, -2.75, True), (0.62, -2.25, False), (0.68, -1.75, False)):
        for sx in (-1, 1):
            zb = hs.bottom(sx * x, y)
            b.add("Teeth", cone(0.12 if big else 0.09, 0.42 if big else 0.26, "EyeWhite", 6), head_m @ frame((sx * x, y, zb + 0.05), out=(0, 0, -1)))
    for y in (-1.15, -0.5, 0.15):
        for sx in (-1, 1):
            x = js.side(y, 0.1) * 0.78 * sx
            b.add("Teeth", cone(0.09, 0.26, "EyeWhite", 6), head_m @ JAW_M @ frame((x, y, js.top(x, y) - 0.04), out=(0, 0, 1)))
    for sx in (-1, 1):  # riveted steel jaw plates
        y = -0.3
        b.add("Jaw", place(riveted_plate(1.4, 0.36, 0.06, "Gunmetal", "Gold", 0.45), head_m @ JAW_M @ frame((sx * (js.side(y, 0.0) - 0.02), y, 0.0), out=(sx, 0, 0), up=(0, 0, 1))))
    eyes = []
    for sx in (-1, 1):
        ez = 0.95
        ey = hs.front(sx * 0.72, ez) + 0.16
        em = frame((sx * 0.72, ey, ez), out=(sx * 0.5, -1, 0.3))
        eyes.append(head_m @ em)
        b.add("Eyes", dragon_eye(0.36), head_m @ em)
        brow_cage = cage_box((0.85, 0.32, 0.28), 0)
        brow = subsurf(brow_cage, 2)
        brow.transform(frame((sx * 0.72, ey + 0.12, ez + 0.42), out=(sx * 0.3, -1, 0.9)) @ M((0, 0, 0), (0, 0, -sx * 0.3)))
        b.add("Head", [(brow, "Gunmetal", 0.0, False)], head_m)
        b.add("Head", place(rivet(0.06, "Gold"), frame((sx * 0.98, ey + 0.2, ez + 0.5), out=(sx * 0.5, -0.6, 1))), head_m)
        hz = hs.top(sx * 0.55, 0.05)  # the big horns sweep back and up from the skull
        root = V(sx * 0.55, 0.05, hz - 0.12)
        b.add("Horns", tube(spline([root, root + V(sx * 0.15, 0.45, 0.45), root + V(sx * 0.35, 1.05, 0.75), root + V(sx * 0.45, 1.65, 0.8)], 3), 0.24, 0.03, "Cream", 10), head_m)
        b.add("Horns", ring(Matrix.Translation(root + V(sx * 0.05, 0.12, 0.15)) @ align_z(V(sx * 0.2, 0.6, 0.6)), 0.23, 0.06, "Gold", 12), head_m)
        side_root = V(sx * (hs.side(0.0, 0.3) - 0.1), 0.0, 0.3)
        b.add("Horns", tube(spline([side_root, side_root + V(sx * 0.35, 0.4, 0.05), side_root + V(sx * 0.55, 0.95, 0.2)], 3), 0.16, 0.02, "Cream", 8), head_m)
        for k in range(3):  # cheek frills
            b.add("Frills", cone(0.13, 0.65 - 0.1 * k, "Amber", 8), head_m @ frame((sx * (hs.side(0.3, 0.0) - 0.15), 0.2, -0.1 - 0.12 * k), out=(sx * 0.7, 1, -0.3 - 0.35 * k)))
        b.add("Head", ball((sx * 0.28, -2.95, hs.top(sx * 0.28, -2.95) - 0.02), (0.1, 0.12, 0.06), "EyeDark", 1), head_m)
    for k, y in enumerate((-0.05, 0.4)):
        b.add("Frills", cone(0.13, 0.4, "Gold", 8), head_m @ frame((0, y, hs.top(0, y) - 0.08), out=(0, 0.5, 1)))
    nostrils = [head_m @ Vector((sx * 0.28, -2.95, hs.top(sx * 0.28, -2.95) + 0.05)) for sx in (1, -1)]
    # the gold crown on top of the skull, between the horns
    crown_at = M((0, -0.55, hs.top(0, -0.55) - 0.1))
    crown = []
    crown += trim_ring(0.55, 0.06, "Gold", minor=0.09, segments=16)
    crown += trim_ring(0.55, 0.28, "Gold", minor=0.04, segments=16)
    for k in range(5):
        a = 2 * math.pi * k / 5 - math.pi / 2
        tall = 0.55 if k == 0 else 0.42
        crown += flare([(0, 0), (0.13, 0), (0.11, 0.18), (0.04, tall), (0, tall + 0.04)], "Gold", 6)
        place(crown[-1:], M((0.55 * math.cos(a), 0.55 * math.sin(a), 0.06)))
        crown += place(cut_gem(0.07, "MagicPink" if k == 0 else "AuroraCyan"), frame((0.6 * math.cos(a), 0.6 * math.sin(a), 0.2), out=(math.cos(a), math.sin(a), 0)))
    b.add("Crown", crown, head_m @ crown_at)
    # the nozzle inside the throat: a gunmetal barrel with a gold muzzle ring, aimed out of the mouth
    nm = frame(V(0, -0.55, -0.4), out=MOUTH_DIR)
    BARREL = 2.55
    b.add("Nozzle", flare([(0, -0.2), (0.44, -0.2), (0.44, BARREL - 0.55), (0.36, BARREL - 0.4), (0.36, BARREL - 0.2),
                           (0.56, BARREL), (0.62, BARREL + 0.18), (0.5, BARREL + 0.2), (0.3, BARREL + 0.02), (0, BARREL)], "Gunmetal", 18), head_m @ nm)
    for z, rr, sw in ((0.55, 0.5, "Gold"), (1.15, 0.5, "Gold"), (BARREL - 0.6, 0.49, "Brass"), (BARREL + 0.1, 0.62, "Gold")):
        b.add("Nozzle", ring(nm @ M((0, 0, z)), rr, 0.07, sw, 18), head_m)
    for k in range(6):  # rivets round the barrel
        a = k * math.pi / 3 + math.pi / 6
        b.add("Nozzle", place(rivet(0.05, "Gold"), nm @ frame((0.45 * math.cos(a), 0.45 * math.sin(a), 0.85), out=(math.cos(a), math.sin(a), 0))), head_m)
    b.add("NozzleGlow", ring(nm @ M((0, 0, BARREL + 0.05)), 0.4, 0.06, "FlameYellow", 16, True), head_m)  # the hot muzzle
    work = head_m @ nm @ M((0, 0, BARREL + 0.2))
    b.add("Flame", the_flame(5, 1.05, length=1.3), work)
    top = head_m @ Vector((0, -0.55, hs.top(0, -0.55) + 0.55))
    # the dragon statue is 15% bigger than it was modelled, grown from the drum top
    S = Matrix.Translation((0, cy, 4.0)) @ Matrix.Diagonal((1.15, 1.15, 1.15, 1)) @ Matrix.Translation((0, -cy, -4.0))
    for key, part in b.parts.items():
        if key not in before:
            part.bm.transform(S)

    def moved(m):
        m = m.copy()
        m.translation = S @ m.translation
        return m

    work, crown_m, top = moved(work), moved(head_m @ crown_at), S @ top
    eyes = [moved(e) for e in eyes]
    nostrils = [S @ n for n in nostrils]
    for sx in (-1, 1):
        b.add("Hoses", cable((sx * 3.5, 3.5, 4.3), S @ V(sx * 0.7, 2.3, 5.4), 0.4, 0.13, "Rubber", "Gold", ribs=2))
    return {"Work": work, "Lamp1": up_((4.2, 4.0, 5.35)), "Lamp2": up_((-4.2, 4.0, 5.35)),
            "Gear1": frame((cx + 3.83, cy, 2.6), out=(1, 0, 0)), "Gear2": frame((cx - 3.83, cy, 2.6), out=(-1, 0, 0)),
            "Gauge1": front((-4.2, 3.08, 3.3)), "Gauge2": front((4.2, 3.08, 3.3)),
            "Steam1": up_(nostrils[0]), "Steam2": up_(nostrils[1]), "Hit": frame((0, -5.5, 1.25), out=(0, -1, 0.6)), "Trail": work,
            "Crown": crown_m, "Eyes": eyes[0], "Eyes2": eyes[1], "NamePlate": front((0, -5.72, 0.45)),
            "Aura": up_((0, 0, 1.2)), "Top": up_(top)}


TIER_FNS = [tier_scrappy, tier_workshop, tier_frosttech, tier_enchanted, tier_dragon]


def PEDESTAL(t, b, info):
    """Dragon Turret (Legendary): no room to grow to its full height, so the turret (drum, fuel tanks and
    dragon, unchanged) stands on a tower of three stacked gunmetal drums: gold-trimmed joints, a crest, a
    glowing strip, and a flared collar under a deck that carries the drum and the tanks
    (framework.raise_on_pedestal)."""
    if t != 5:
        return
    m, z0 = info["matrix"], info["bottom"]
    s = m.to_scale().x
    foot = m @ V(0.0, 0.6, 1.2)  # the turret drum's foot, now
    deck_top = foot.z + 0.12
    deck_bottom = deck_top - 1.1
    outline = floor_outline(info["grown"], foot.z - 0.3, foot.z + 1.2)
    b.add("Deck", [(prism(outline, deck_bottom, deck_top, inset=0.15), "Gunmetal", 0.12, False)])
    b.add("DeckTrim", [(prism(outline, deck_bottom + 0.35, deck_bottom + 0.6, inset=0.05), "Gold", 0.0, False)])
    cx, cy = foot.x, min(foot.y, 5.7 - 3.9)
    R = 3.2  # the tower's drums: narrow next to the 15-stud turret
    collar_h = 2.2
    collar = bmesh.new()
    lathe(collar, [(0, deck_bottom - collar_h), (R + 0.1, deck_bottom - collar_h), (R + 0.6, deck_bottom - collar_h + 0.5),
                   (R + 2.2, deck_bottom - 0.25), (R + 2.4, deck_bottom + 0.05), (0, deck_bottom + 0.05)], 16, M((cx, cy, 0)))
    b.add("Tower", [(collar, "Gunmetal", 0.0, False)])
    b.add("TowerTrim", place(trim_ring(R + 0.55, 0, "Gold", minor=0.1, segments=16), M((cx, cy, deck_bottom - collar_h + 0.45))))
    zs = [z0 - 0.05 + (deck_bottom - collar_h - z0) * k / 3 for k in range(4)]
    for k in range(3):
        za, zb = zs[k], zs[k + 1]
        r = R * (1.12 - 0.05 * k)
        drum = bmesh.new()
        lathe(drum, [(0, za), (r, za), (r + 0.15, za + 0.3), (r + 0.15, zb - 0.3), (r, zb), (0, zb)], 16, M((cx, cy, 0)))
        b.add("Tower", [(drum, "Gunmetal" if k != 1 else "SteelDark", 0.0, False)])
        if k < 2:  # gold trim where the drums meet (the collar covers the top one)
            b.add("TowerTrim", place(trim_ring(r + 0.17, 0, "Gold", minor=0.1, segments=16), M((cx, cy, zb - 0.12))))
    b.add("Tower", place(crest(1.5, 1.8, 0.2, "Gold", "NavyIce", "FlameYellow", "FlameOrange"), front((cx, cy - R * 1.02 - 0.17, (zs[2] + zs[3]) / 2 + 0.2), 0.0)))
    b.add("TowerLights", trim_strip((cx - 1.2, cy - R * 1.12 - 0.17, zs[0] + 0.7), (cx + 1.2, cy - R * 1.12 - 0.17, zs[0] + 0.7), 0.16, "FlameOrange", True))



# ---------- the upgrade sets ----------

NOZZLE_LOOK = {  # metal, ring, ring glows
    1: ("Steel", "Iron", False), 2: ("SteelLight", "Brass", False), 3: ("SteelLight", "AuroraCyan", True),
    4: ("SteelLight", "RuneGlow", True), 5: ("SteelLight", "Gold", False)}


def steel_nozzle(t):
    """The 1st upgrade: a steel nozzle in tier t's look, its mouth just past the Work point (+Z)."""
    r = NOZZLE_R[t]
    metal, ring_swatch, ring_glow = NOZZLE_LOOK[t]
    L = 0.6 + 0.6 * r
    pieces = flare([(0, -L), (r * 1.05, -L), (r * 1.05, -L * 0.4), (r * 1.3, 0.1), (r * 1.4, 0.25), (r * 1.22, 0.26), (r * 0.8, 0.05), (0, 0.02)], metal, 16)
    pieces += ring(M((0, 0, -L * 0.55)), r * 1.12, 0.03 + r * 0.1, ring_swatch, 14, ring_glow)
    pieces += ring(M((0, 0, 0.2)), r * 1.42, 0.02 + r * 0.06, ring_swatch, 14, ring_glow)
    if t == 1:  # wired on with iron wire
        for z in (-0.5, -0.38):
            pieces += ring(M((0, 0, z)), r * 1.12, 0.02, "Iron", 10)
    elif t == 2:  # cooling fins
        for z in (-0.75, -0.6, -0.45):
            pieces += ring(M((0, 0, z)), r * 1.25, 0.04, "Iron", 14)
    elif t == 4:  # set with gems
        for k in range(4):
            a = k * math.pi / 2
            pieces += place(cut_gem(0.07, "MagicPink"), frame((r * 1.2 * math.cos(a), r * 1.2 * math.sin(a), -L * 0.3), out=(math.cos(a), math.sin(a), 0)))
    elif t == 5:
        pieces += place(rivet_ring(r * 1.1, 6, 0.05, "Gold"), M((0, 0, -L * 0.2)))
    return pieces


def gauge(t):
    """A fuel gauge facing +Z in tier t's look."""
    if t == 1:
        return dial(0.22, "Cream", "Iron", "WarnRed", 0.9)
    if t == 2:
        pieces = dial(0.26, "Cream", "Brass", "WarnRed", 0.5)
        return pieces + place(rivet_ring(0.3, 4, 0.04, "Copper"), M((0, 0, 0.02)))
    if t == 3:
        pieces = place(screen(0.7, 0.42, "AuroraCyan", "NavyIce", 3), M((0, 0.26, 0)))
        return pieces + place(dial(0.2, "FrostLight", "SteelLight", "WarnRed", 0.3), M((0, -0.26, 0)))
    if t == 4:
        pieces = dial(0.24, "Moonstone", "Gold", "RuneViolet", -0.4)
        return pieces + place(cut_gem(0.08, "MagicPink"), M((0, 0.36, 0.08)))
    pieces = dial(0.3, "Cream", "Gold", "WarnRed", 0.7)
    return pieces + place(rivet_ring(0.35, 6, 0.045, "Gold"), M((0, 0, 0.02)))


GEAR_LOOK = {1: ("Pine", "Iron"), 2: ("Brass", "Copper"), 3: ("SteelLight", "AuroraCyan"), 4: ("Moonstone", "Gold"), 5: ("Brass", "Gold")}


def UPGRADES(u, t, atts, b, fx):
    work = atts["Work"]
    r = NOZZLE_R[t]
    if u == 1:  # steel nozzles
        b.add("Nozzle", steel_nozzle(t), work)
    elif u == 2:  # pilot lights: lamps (glowing gems later) and a little blue pilot flame under the nozzle
        for key in ("Lamp1", "Lamp2"):
            if key in atts:
                b.add("Lamp" + key[-1], place(tier_lamp(t, "FlameOrange" if t in (2, 5) else None), atts[key]))
        pilot = work @ M((0, -(r * 1.45 + 0.08), -0.55))
        b.add("Pilot", place(cyl(0.05 + 0.03 * t / 5, 0.45, NOZZLE_LOOK[t][0], 8), pilot @ M((0, 0, -0.3))))
        b.add("Pilot", flame(0.07 + 0.02 * t, 0.28 + 0.05 * t, "GlacierBlue", "CrystalCyan"), pilot @ M((0, 0, 0.15)))
    elif u == 3:  # the rotating turret's gear(s) and fuel gauges; smoke puffs
        swatch, hub = GEAR_LOOK[t]
        for key in ("Gear1", "Gear2"):
            if key in atts:
                if t == 5:
                    b.add("Gear%sBig" % key[-1], place(gear(0.95, 12, 0.28, 0.16, swatch, hub), atts[key] @ M((0, 0, 0.15))))
                    b.add("Gear%sSmall" % key[-1], place(gear(0.5, 7, 0.28, 0.13, "Copper", "Gold"), atts[key] @ M((0.8, 0.8, 0.35))))
                elif t == 2:  # a turret ring round the column
                    b.add("Gear1", place(spoked_gear(0.75, 14, 0.18, 0.12, 4, swatch, hub), atts[key]))
                else:
                    b.add("Gear" + key[-1], place(spoked_gear(0.62 if t != 4 else 0.55, 10, 0.2, 0.12, 4, swatch, hub), atts[key] @ M((0, 0, 0.12))))
        for key in ("Gauge1", "Gauge2"):
            if key in atts:
                b.add("Gauges", place(gauge(t), atts[key]))
        for key in ("Steam1", "Steam2"):
            if key in atts:
                fx.add("Smoke" + key[-1], place(smoke(t, 0.5 if t == 5 else 1.0), atts[key] @ (M((0, -0.25, 0), (0.5, 0, 0)) if t == 5 else Matrix())))
    elif u == 4:  # blue-hot flame: a blue-white core in the flame and a blue burst where it hits
        fx.add("BlueFlame", the_flame(t, 0.75, "GlacierBlue", "Diamond"), work @ M((0, 0, 0.05)))
        fx.add("Hit", place(hit_standin(t, "CrystalCyan"), atts["Hit"]))
        fx.add("Hit", place(flame(0.5, 1.2, "GlacierBlue", "CrystalCyan"), atts["Hit"] @ M((0, 0, 0.1))))
    else:  # white-purple plasma flame: a plasma emitter collar, the plasma flame and a trail of sparks
        coll = work @ M((0, 0, -0.32))
        b.add("Plasma", ring(coll, r * 1.55, 0.04 + r * 0.08, "RuneViolet", 16, True))
        b.add("Plasma", ring(coll @ M((0, 0, 0.18)), r * 1.45, 0.03 + r * 0.06, "AuroraViolet", 16, True))
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            b.add("Plasma", place(block((0.08 + r * 0.12, 0.08 + r * 0.12, 0.45), NOZZLE_LOOK[t][0] if t != 5 else "Gold", corner=0.03, edge=0.02), coll @ M((r * 1.55 * math.cos(a), r * 1.55 * math.sin(a), -0.15))))
        fx.add("PlasmaFlame", the_flame(t, 1.12, "AuroraViolet", "EyeWhite", 1.45), work)
        trail = []
        for k in range(10):
            a = k * 0.9
            rr = (0.35 + r) * (1 - k / 16)
            trail += ember_diamond((rr * math.cos(a), rr * math.sin(a), 0.4 + k * 0.28), 0.08 + 0.02 * (k % 3), "RuneGlow" if k % 2 else "EyeWhite")
        fx.add("Trail", place(trail, atts["Trail"]))
        if t == 5:  # a plasma gem set into the front of the crown
            b.add("CrownGem", place(gem_setting(0.2, "AuroraViolet", "Gold", 4), atts["Crown"] @ frame((0, -0.7, 0.32), out=(0, -1, 0.2))))


def AURA(atts, fx):
    """Dragon Turret: drifting embers, curling smoke from the nostrils, an ember ring on the ground."""
    centre = atts["Aura"].to_translation()
    ember_ring = bmesh.new()
    torus(ember_ring, M(centre + V(0, 0, 0.03)), 5.0, 0.07, 48, 4)
    fx.add("AuraRing", [(ember_ring, "FlameOrange", 0.0, True)])
    for k in range(18):
        a = k * 2 * math.pi / 18 + 0.1 * (k % 3)
        fx.add("AuraRing", ember_diamond(centre + V(5.0 * math.cos(a), 5.0 * math.sin(a), 0.12 + 0.1 * (k % 3)), 0.08 + 0.03 * (k % 2), "Amber" if k % 2 else "FlameYellow"))
    for k in range(20):  # embers drifting up round the dragon
        a = k * 2.39
        rr = 3.0 + 1.6 * ((k * 7) % 5) / 5
        fx.add("AuraEmbers", ember_diamond(centre + V(rr * math.cos(a), rr * math.sin(a) + 0.3, 1.6 + 0.5 * k), 0.09 + 0.03 * (k % 3), ("FlameOrange", "Amber", "LampYellow")[k % 3]))
    for sx, key in ((1, "Steam1"), (-1, "Steam2")):  # smoke curling out of each nostril, forward and away from the eyes
        base = atts[key].to_translation()
        for k in range(6):
            a = k * 1.2
            r = 0.12 + 0.05 * k
            curl = V(sx * (0.2 * k + 0.2 * math.cos(a)), -0.3 * k + 0.2 * math.sin(a), 0.1 + 0.3 * k)
            fx.add("AuraSmoke", ball(base + curl, (r, r, r * 0.85), "StoneLight" if k % 2 else "Stone", 2))
