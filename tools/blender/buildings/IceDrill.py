import re
WORKSHOP_BIT_DIR = Vector((0, -1, -0.8)).normalized()
FROST_BIT_DIR = Vector((0, -1, -0.55)).normalized()
ENCHANTED_BIT_AT, ENCHANTED_BIT_DIR = (0, -2.3, 3.4), Vector((0, -1, -0.75)).normalized()
TITAN_NOSE_DIR = Vector((0, -1, -0.78)).normalized()
TITAN_SHIFT = 1.1  # the Titan stands this far back on its plinth, so the drill snout stays over the pad

# IceDrill.py - the Ice Drill's five tiers (v4: the approved v3 style with the Step 1 fixes) and its
# upgrade sets, for tools/blender/buildings/framework.py. Copied from ice_drill_tiers_v3.py (kept as the
# approved v3 reference) and changed here.
TIER_Q = {"Scrappy": {"round": 1.0}, "Workshop": {"round": 1.0}, "Frost-tech": {"round": 1.1},
          "Enchanted": {"round": 1.5, "minor": 1.25, "corner": 3}, "Legendary": {"round": 1.0}}

# ---------- tier 1: Scrappy ----------

def tier_scrappy(b):
    for L, W, swatch, grain, loc, turn, seed in ((3.6, 1.0, "PineDark", "RustDark", (-0.3, -1.0, 0), 0.12, 0.0),
                                                 (3.0, 0.9, "Pine", "PineDark", (0.4, 0.3, 0), -0.18, 1.3),
                                                 (2.6, 0.8, "PineLight", "Pine", (-0.2, 1.3, 0), 0.25, 2.1)):
        b.add("Planks", place(plank(L, W, 0.25, swatch, grain, True, seed), M(loc, (0, 0, turn))))
    apex = V(0.15, 0.05, 4.6)
    dark_foot, pipe_foot, light_foot = V(-1.9, -1.4, 0.2), V(1.8, -1.1, 0.2), V(0.1, 1.9, 0.2)
    b.add("Legs", grained_beam(dark_foot, apex + V(-0.1, -0.05, 0.6), 0.42, "PineDark", "RustDark"))
    b.add("Legs", grained_beam(light_foot, apex + V(0, 0.1, 0.55), 0.36, "PineLight", "Pine"))
    b.add("Legs", pipe_between(pipe_foot, apex + V(0.12, 0, 0.45), 0.16, "Rust"))
    for t in (0.25, 0.6):  # hose clamps on the rusty pipe
        p = pipe_foot.lerp(apex + V(0.12, 0, 0.45), t)
        clamp = bmesh.new()
        torus(clamp, Matrix.Translation(p) @ align_z(apex - pipe_foot), 0.18, 0.04, 12, 4)
        b.add("Legs", [(clamp, "SteelDark", 0.0, False)])
        b.add("Legs", place(bolt(0.05, "Iron"), Matrix.Translation(p) @ align_z(apex - pipe_foot) @ M((0.2, 0, 0), (0, math.pi / 2, 0))))
    for foot in (dark_foot, pipe_foot, light_foot):  # stone feet
        stone = bmesh.new()
        blob(stone, (foot.x, foot.y, 0.12), (0.42, 0.36, 0.2), 1, floor=0.0)
        b.add("Planks", [(stone, "StoneDark", 0.0, False)])
    # rope lashing and an iron bracket at the apex
    for k, tilt in enumerate((0.3, -0.4)):
        ring = bmesh.new()
        torus(ring, Matrix.Translation(apex + V(0, 0, 0.12 + 0.12 * k)) @ Matrix.Rotation(tilt, 4, "X"), 0.4, 0.07, 12, 4)
        b.add("Legs", [(ring, "PineLight", 0.0, False)])
    mid = (dark_foot + apex) / 2
    b.add("Legs", place(riveted_plate(0.6, 0.7, 0.06, "PatchGreen", "RustDark", 0.6), front(mid + V(0, -0.24, 0), 0.2)))
    # the crank: an old rusty cart wheel, a bent arm and a worn wooden grip
    hub = apex + V(0.5, 0, -0.35)
    b.add("Wheel", place(spoked_gear(0.75, 10, 0.2, 0.12, 4, "Rust", "RustDark"), frame(hub, out=(1, 0, 0))))
    arm = bmesh.new()
    sweep(arm, [hub + V(0.25, 0, 0), hub + V(0.35, 0, 0.3), hub + V(0.45, 0, 0.55)], 0.06, 8)
    b.add("Wheel", [(arm, "Iron", 0.0, False)])
    b.add("Wheel", place(cyl(0.11, 0.42, "PineLight", 12), frame(hub + V(0.45, 0, 0.55), out=(1, 0, 0))))
    b.add("Wheel", place(cyl(0.13, 0.06, "Iron", 12), frame(hub + V(0.87, 0, 0.55), out=(1, 0, 0))))
    b.add("Legs", place(cyl(0.14, apex.z - 1.4, "Iron", 12), M((apex.x, apex.y, 1.4))))
    b.add("Legs", place(cyl(0.26, 0.3, "Iron", 12), M((apex.x, apex.y, 1.4))))
    b.add("Legs", place(rivet_ring(0.2, 4, 0.05, "RustDark"), M((apex.x, apex.y, 1.7))))
    # junk: a stave barrel with hoops and a planked lid, a bucket with a wire handle, an oil can, a rope
    bx, by = 2.3, 0.9
    barrel = bmesh.new()
    lathe(barrel, [(0, 0), (0.48, 0), (0.56, 0.3), (0.6, 0.6), (0.56, 0.9), (0.48, 1.2), (0, 1.2)], 16, M((bx, by, 0)))
    b.add("Junk", [(barrel, "Rust", 0.0, False)])
    for k in range(6):  # stave lines
        a = 2 * math.pi * k / 6 + 0.3
        pts = [V(bx + (0.485 + 0.11 * math.sin(math.pi * z / 1.2)) * math.cos(a), by + (0.485 + 0.11 * math.sin(math.pi * z / 1.2)) * math.sin(a), z) for z in (0.05, 0.3, 0.6, 0.9, 1.15)]
        s = bmesh.new()
        sweep(s, pts, 0.015, 4)
        b.add("Junk", [(s, "RustDark", 0.0, False)])
    for z, r in ((0.25, 0.56), (0.95, 0.56)):
        hoop = bmesh.new()
        torus(hoop, M((bx, by, z)), r, 0.04, 16, 4)
        b.add("Junk", [(hoop, "Iron", 0.0, False)])
    b.add("Junk", place(cyl(0.46, 0.08, "PineDark", 16), M((bx, by, 1.18))))
    for off in (-0.16, 0.16):
        b.add("Junk", trim_strip((bx - 0.38, by + off, 1.27), (bx + 0.38, by + off, 1.27), 0.03, "RustDark"))
    bucket = bmesh.new()
    lathe(bucket, [(0, 0), (0.3, 0), (0.42, 0.6), (0.38, 0.6), (0.27, 0.06), (0, 0.06)], 14, M((-2.1, 0.7, 0), (0.12, 0, 0)))
    b.add("Junk", [(bucket, "Steel", 0.0, False)])
    rim = bmesh.new()
    torus(rim, M((-2.1, 0.77, 0.6), (0.12, 0, 0)), 0.42, 0.035, 14, 4)
    wire = bmesh.new()
    sweep(wire, [V(-2.52, 0.77, 0.6), V(-2.45, 0.8, 0.95), V(-2.1, 0.82, 1.1), V(-1.75, 0.8, 0.95), V(-1.68, 0.77, 0.6)], 0.025, 6)
    b.add("Junk", [(rim, "SteelDark", 0.0, False), (wire, "Iron", 0.0, False)])
    can = bmesh.new()
    lathe(can, [(0, 0), (0.22, 0), (0.22, 0.42), (0.12, 0.55), (0, 0.55)], 12, M((-0.9, -1.15, 0.25)))
    spout = bmesh.new()
    sweep(spout, [V(-0.8, -1.15, 0.72), V(-0.6, -1.25, 0.95), V(-0.35, -1.35, 1.05)], 0.035, 6, radius_end=0.02)
    b.add("Junk", [(can, "PatchGreen", 0.0, False), (spout, "Iron", 0.0, False)])
    b.add("Junk", cable(apex + V(0.3, 0.2, 0.1), (bx - 0.3, by, 1.3), 0.5, 0.045, "PineLight", "RustDark"))
    atts = {"Bit": down((apex.x, apex.y, 1.4)), "Lamp1": up_((bx, by, 1.32)), "Gear1": front((apex.x, -0.42, apex.z - 0.9)),
            "Steam1": up_(apex + V(0, 0, 0.7)), "Hit": frame((apex.x, -0.7, 0.3), out=(0, -1, 0.6)),
            "Trail": down((apex.x, apex.y, -0.6)), "NamePlate": front((0, -1.9, 0.45)), "Aura": up_((0, 0, 0.3)), "Top": up_(apex + V(0, 0, 0.7))}
    return b, atts, ("Iron", None)


# ---------- tier 2: Workshop ----------

def lantern_v3(glass="LampYellow", metal="Brass"):
    pieces = []
    g = bmesh.new()
    cylinder(g, (0, 0, 0.12), 0.2, 0.42, 12)
    pieces.append((g, glass, 0.0, True))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        bar = bmesh.new()
        cylinder(bar, (0.23 * math.cos(a), 0.23 * math.sin(a), 0.1), 0.03, 0.46, 6)
        pieces.append((bar, metal, 0.0, False))
    top, bottom = bmesh.new(), bmesh.new()
    lathe(top, [(0, 0.52), (0.3, 0.52), (0.26, 0.6), (0.12, 0.72), (0, 0.74)], 12)
    cylinder(bottom, (0, 0, 0), 0.28, 0.12, 12)
    ring = bmesh.new()
    torus(ring, M((0, 0, 0.82)), 0.08, 0.02, 10, 4)
    pieces += [(top, metal, 0.0, False), (bottom, metal, 0.02, False), (ring, metal, 0.0, False)]
    return pieces


def tier_workshop(b):
    for k, y in enumerate((-2.0, -1.0, 0.0, 1.0, 2.0)):
        b.add("Deck", place(plank(6.0, 0.96, 0.5, "Pine", "PineDark", k in (0, 4), k * 1.1), M((0, y, 0))))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add("Posts", grained_beam((sx * 2.4, sy * 1.9, 0.5), (sx * 2.4, sy * 1.9, 6.0), 0.5, "PineLight", "Pine", faces=(3,)))
            b.add("Posts", place(cyl(0.34, 0.2, "Brass", 12), M((sx * 2.4, sy * 1.9, 0.5))))
    for sy in (-1, 1):
        b.add("Posts", beam_between((-2.7, sy * 1.9, 5.85), (2.7, sy * 1.9, 5.85), 0.42, swatch="PineDark"))
    for sx in (-1, 1):
        b.add("Posts", beam_between((sx * 2.4, -2.2, 5.85), (sx * 2.4, 2.2, 5.85), 0.42, swatch="PineDark"))
    # copper gable roof with standing seams, a brass ridge with end caps, trim boards on the gables
    for side in (-1, 1):
        tilt = side * -math.radians(32)
        slab = bmesh.new()
        rounded_block(slab, (6.6, 3.0, 0.3), M((0, side * 1.25, 6.85), (tilt, 0, 0)), corner=0.15, edge=0.08)
        b.add("Roof", [(slab, "Copper", 0.0, False)])
        for k in range(5):
            x = -2.8 + k * 1.4
            seam = bmesh.new()
            box(seam, (0, 0, 0), (0.07, 2.9, 0.08))
            seam.transform(M((0, side * 1.25, 6.85), (tilt, 0, 0)) @ M((x, 0, 0.18)))
            b.add("Roof", [(seam, "RustDark", 0.0, False)])
    b.add("Roof", place(cyl(0.2, 6.8, "Brass", 14), frame((-3.4, 0, 7.62), out=(1, 0, 0))))
    for sx in (-1, 1):
        cap = bmesh.new()
        blob(cap, (sx * 3.42, 0, 7.62), (0.26, 0.26, 0.26), 1)
        b.add("Roof", [(cap, "Brass", 0.0, False)])
    # the boiler: domed ends, banded and riveted, a dial and a safety valve
    boiler = bmesh.new()
    lathe(boiler, [(0, -0.25), (0.5, -0.2), (0.78, -0.05), (0.85, 0.15), (0.85, 2.45), (0.78, 2.65), (0.5, 2.8), (0, 2.85)], 14, frame((-2.0, 0.9, 1.6), out=(1, 0, 0)))
    b.add("Boiler", [(boiler, "Brass", 0.0, False)])
    for x in (-1.5, -0.4):
        b.add("Boiler", place(trim_ring(0.87, 0, "Copper", minor=0.09, segments=14), frame((x, 0.9, 1.6), out=(1, 0, 0))))
        for k in range(5):
            a = 2 * math.pi * k / 5
            b.add("Boiler", place(rivet(0.05, "Copper"), frame((x + 0.16, 0.9 + 0.86 * math.cos(a), 1.6 + 0.86 * math.sin(a)), out=(0, math.cos(a), math.sin(a)))))
    b.add("Boiler", place(dial(0.27, "Cream", "Brass", "WarnRed", 0.5), frame((-1.0, 0.03, 1.8), out=(0, -1, 0))))
    b.add("Boiler", place(cyl(0.1, 0.35, "Copper", 10), M((-1.8, 0.9, 2.42))))
    b.add("Boiler", place(cyl(0.16, 0.1, "Brass", 12), M((-1.8, 0.9, 2.77))))
    b.add("Boiler", beam_between((-1.8, 0.9, 2.85), (-1.25, 0.9, 2.95), 0.06, swatch="Iron"))
    b.add("Boiler", place(cyl(0.6, 0.5, "PineDark", 14), frame((-1.95, 0.9, 1.6), out=(0, 0, -1))))  # cradle
    # firebox with a hinged door, a handle and a glowing grille window
    b.add("Firebox", place(block((1.2, 1.0, 0.75), "Iron", corner=0.15, edge=0.08), M((-0.7, 0.2, 0.5))))
    door = front((-0.7, -0.32, 0.88))
    b.add("Firebox", place(block((0.9, 0.55, 0.05), "SteelDark", corner=0.06, edge=0.02), door))
    window = bmesh.new()
    rounded_block(window, (0.55, 0.22, 0.04), M((0, 0, 0.06)), corner=0.05, edge=0.01, corner_seg=2, edge_seg=1)
    b.add("Firebox", place([(window, "FlameOrange", 0.0, True)], door))
    for k in range(4):
        b.add("Firebox", place(block((0.035, 0.24, 0.04), "Iron", corner=0.01, edge=0.01), door @ M((-0.2 + k * 0.13, 0, 0.06))))
    b.add("Firebox", place(hinge(0.45, 0.045, 2, "SteelDark"), door @ M((-0.48, 0, 0.03), (0, 0, math.pi / 2))))
    b.add("Firebox", place(cyl(0.05, 0.12, "Brass", 8), door @ M((0.36, 0, 0.05))))
    # chimney: banded brass pipe, a cap and a spark guard
    b.add("Chimney", pipe_between((-1.4, 0.9, 2.4), (-1.4, 0.9, 8.4), 0.24, "Brass"))
    for z in (4.5, 7.4):
        b.add("Chimney", place(trim_ring(0.26, 0, "Copper", minor=0.05, segments=12), M((-1.4, 0.9, z))))
    cap = bmesh.new()
    lathe(cap, [(0, 8.4), (0.36, 8.4), (0.4, 8.55), (0.28, 8.75), (0, 8.8)], 14, M((-1.4, 0.9, 0)))
    b.add("Chimney", [(cap, "Copper", 0.0, False)])
    # drill head: a lidded copper gearbox with a vent, the flywheel and its belt, a collar in the deck
    b.add("Gearbox", place(lidded_box((1.3, 1.2, 1.1), "Copper", "Copper", "Brass"), M((1.3, -0.4, 4.3))))
    b.add("Gearbox", place(vent(0.7, 0.5, 4, "RustDark", "Brass"), frame((1.97, -0.4, 4.75), out=(1, 0, 0))))
    # the drive boom: from under the gearbox, angled down and forward to the bit's chuck at the front
    boom_from, boom_to = V(1.3, -0.4, 3.75), V(1.3, -2.05, 2.1)
    b.add("Gearbox", place(cyl(0.17, (boom_to - boom_from).length, "Steel", 12), frame(boom_from, out=boom_to - boom_from)))
    chuck = frame(boom_to, out=WORKSHOP_BIT_DIR)
    b.add("Gearbox", place(cyl(0.36, 0.42, "Brass", 14), chuck @ M((0, 0, -0.3))))
    b.add("Gearbox", place(rivet_ring(0.3, 4, 0.06, "Copper"), chuck @ M((0, 0, 0.1))))
    b.add("Gearbox", beam_between((0.95, -2.0, 0.5), (1.2, -2.05, 1.95), 0.16, swatch="PineDark"))  # a strut under the chuck
    b.add("Gearbox", beam_between((1.65, -2.0, 0.5), (1.4, -2.05, 1.95), 0.16, swatch="PineDark"))
    b.add("Flywheel", place(spoked_gear(1.0, 10, 0.24, 0.12, 3, "Brass", "Copper"), front((-0.9, -0.55, 4.4))))
    for z0, z1 in ((5.38, 5.15), (3.42, 3.95)):
        b.add("Gearbox", trim_strip((-0.9, -0.72, z0), (1.3, -0.72, z1), 0.12, "Rubber"))
    # a hanging lantern and a toolbox on the deck
    b.add("Lantern", chain(3, 0.09, "Brass"), M((2.4, -2.35, 5.75)))
    b.add("Lantern", lantern_v3(), M((2.4, -2.35, 4.2)))
    b.add("Deck", place(handle(0.4, 0.14, 0.03, "SteelDark"), M((-1.9, -1.6, 0.96), (0, 0, 0.3))))
    atts = {"Bit": frame((1.3, -2.15, 2.0), out=WORKSHOP_BIT_DIR), "Lamp1": up_((1.0, -0.4, 5.45)), "Gear1": front((1.3, -1.04, 4.85)),
            "Steam1": up_((-1.4, 0.9, 8.85)), "Hit": frame((1.3, -3.6, 0.5), out=(0, -1, 0.6)),
            "Trail": frame((1.3, -2.15, 2.0), out=WORKSHOP_BIT_DIR), "NamePlate": front((0, -2.52, 0.25)), "Aura": up_((0, 0, 0.5)), "Top": up_((-1.4, 0.9, 8.85))}
    return b, atts, ("Brass", None)


# ---------- tier 3: Frost-tech ----------

def tier_frosttech(b):
    b.add("Deck", block((9.0, 7.0, 0.8), "SnowWhite", corner=1.4, edge=0.3))
    b.add("Deck", place(block((8.0, 6.0, 0.3), "IceBlue", corner=1.1, edge=0.12), M((0, 0, 0.8))))
    for x, y in ((-1.9, -2.2), (1.9, -2.2)):
        b.add("Deck", place(inset_panel(1.6, 1.1, 0.05, "FrostLight", "GlacierBlue", True), M((x, y, 1.1))))
    for sx in (-1, 1):
        b.add("Deck", place(vent(1.4, 0.4, 5, "GlacierBlue", "SteelLight"), front((sx * 2.6, -3.49, 0.42))))
        for sy in (-1, 1):
            b.add("Deck", place(bolt(0.1, "SteelLight", "GlacierBlue"), M((sx * 3.7, sy * 2.7, 1.1))))
    for p0, p1 in (((-3.0, -3.53, 0.42), (3.0, -3.53, 0.42)), ((-3.0, 3.53, 0.42), (3.0, 3.53, 0.42)),
                   ((-4.53, -2.0, 0.42), (-4.53, 2.0, 0.42)), ((4.53, -2.0, 0.42), (4.53, 2.0, 0.42))):
        b.add("Deck", trim_strip(p0, p1, 0.16, "AuroraCyan", True))
    b.add("Deck", place(cyl(0.55, 0.12, "GlacierBlue", 6), front((0, -3.5, 0.42))))
    for k in range(3):
        b.add("Deck", place(block((0.12, 0.8, 0.08), "SnowWhite", corner=0.03, edge=0.02), front((0, -3.62, 0.42)) @ M((0, 0, 0), (0, 0, k * math.pi / 3))))
    for X, letter in ((-2.6, "A"), (2.6, "B")):
        pod = "Pod" + letter
        for sx in (-1, 1):
            b.add(pod + "Legs", beam_between((X + sx * 0.85, 0, 1.1), (X + sx * 0.5, 0, 3.4), 0.26, swatch="SteelLight"))
            b.add(pod + "Legs", place(cyl(0.3, 0.12, "GlacierBlue", 12), M((X + sx * 0.85, 0, 1.1))))
            b.add(pod + "Legs", place(rivet_ring(0.22, 4, 0.05, "SteelDark"), M((X + sx * 0.85, 0, 1.22))))
        b.add(pod + "Legs", piston((X, 0.75, 1.2), (X, 0.75, 3.1), 0.12, "GlacierBlue", "SteelLight"))
        b.add(pod, place(block((2.2, 2.0, 3.6), "SnowWhite", corner=0.95, edge=0.6), M((X, 0, 3.0))))
        for z in (3.75, 4.75):  # panel line bands
            b.add(pod, place(block((2.26, 2.06, 0.07), "GlacierBlue", corner=0.98, edge=0.02), M((X, 0, z))))
        b.add(pod, place(block((1.7, 0.3, 0.55), "NavyIce", corner=0.25, edge=0.1), M((X, -0.92, 5.3))))
        b.add(pod, trim_strip((X - 0.7, -1.04, 5.15), (X + 0.7, -1.04, 5.15), 0.08, "AuroraCyan", True))
        b.add(pod, trim_strip((X - 0.7, -1.04, 5.75), (X + 0.7, -1.04, 5.75), 0.08, "AuroraCyan", True))
        b.add(pod, place(screen(0.8, 0.45, "AuroraCyan", "NavyIce", 3), front((X, -1.0, 4.3))))
        b.add(pod, place(vent(0.8, 0.5, 4, "GlacierBlue", "SteelLight"), frame((X, 1.0, 4.3), out=(0, 1, 0))))
        # the hinged lid on top, with a grab handle
        b.add(pod + "Lid", place(block((1.9, 1.7, 0.32), "SteelLight", corner=0.75, edge=0.12), M((X, 0, 6.6))))
        b.add(pod + "Lid", place(hinge(1.0, 0.07, 4, "GlacierBlue"), M((X, 0.88, 6.65))))
        b.add(pod + "Lid", place(handle(0.5, 0.18, 0.04, "GlacierBlue"), front((X, -0.86, 6.76))))
        for sx in (-1, 1):  # frost fins with a panel line
            fin = bmesh.new()
            rounded_block(fin, (0.14, 1.2, 1.8), M((X + sx * 1.15, 0.2, 4.4), (0, sx * 0.25, 0)), corner=0.06, edge=0.05, taper=0.6)
            line = bmesh.new()
            rounded_block(line, (0.16, 0.06, 1.4), M((X + sx * 1.16, 0.2, 4.3), (0, sx * 0.25, 0)), corner=0.02, edge=0.02, corner_seg=1, edge_seg=1)
            b.add(pod, [(fin, "GlacierBlue", 0.0, False), (line, "AuroraCyan", 0.0, True)])
        ring = bmesh.new()
        torus(ring, M((X, 0, 1.15)), 0.62, 0.1, 12, 4)
        b.add("Deck", [(ring, "AuroraCyan", 0.0, True)])
        inner = math.copysign(0.65, X)
        b.add("Cables", pipe_between((X - math.copysign(1.1, X), 0.2, 5.0), (inner, 0.6, 5.0), 0.16, "SteelLight"))
        b.add("Cables", cable((X - math.copysign(0.6, X), 0.95, 3.4), (math.copysign(0.75, X), 0.95, 1.6), 0.35, 0.08, "NavyIce", "GlacierBlue"))
        b.add("Cables", cable((X, 1.05, 3.6), (X + math.copysign(0.8, X), 2.6, 1.15), 0.4, 0.12, "SteelDark", "GlacierBlue", ribs=2))
    # the coil spire: a vented base, stacked insulators, the wound coil and the glowing top
    b.add("Coil", place(block((1.6, 1.6, 0.8), "SteelLight", corner=0.3, edge=0.12), M((0, 0.6, 1.1))))
    b.add("Coil", place(block((1.7, 1.7, 0.1), "GlacierBlue", corner=0.32, edge=0.04), M((0, 0.6, 1.1))))
    b.add("Coil", place(vent(0.9, 0.45, 4, "GlacierBlue", "SteelLight"), front((0, -0.21, 1.45))))
    b.add("Coil", place(coil(0.62, 5.6, turns=6, core="SteelDark", wire="IceBlue", top="AuroraCyan"), M((0, 0.6, 1.9))))
    for z in (2.2, 2.9):
        b.add("Coil", place(cyl(0.98, 0.14, "IceBlue", 16), M((0, 0.6, z))))
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 2
        fin = bmesh.new()
        rounded_block(fin, (0.14, 0.9, 1.4), M((0.85 * math.cos(a), 0.6 + 0.85 * math.sin(a), 2.5), (0, 0, a)), corner=0.05, edge=0.04, taper=0.5)
        b.add("Coil", [(fin, "GlacierBlue", 0.0, False)])
    for X in (-2.6, 2.6):  # the bit housings: a steel collar ring with a glowing ice band, on the pod's front
        mount = frame((X, -1.05, 2.25), out=FROST_BIT_DIR)
        b.add("Pod" + ("A" if X < 0 else "B"), place(cyl(0.62, 0.36, "SteelLight", 12), mount @ M((0, 0, -0.32))))
        b.add("Pod" + ("A" if X < 0 else "B"), place(trim_ring(0.64, 0, "AuroraCyan", True, minor=0.06, segments=12), mount @ M((0, 0, -0.05))))
    atts = {"Bit": frame((-2.6, -1.1, 2.25), out=FROST_BIT_DIR), "Bit2": frame((2.6, -1.1, 2.25), out=FROST_BIT_DIR),
            "Lamp1": up_((-2.6, -0.3, 6.92)), "Lamp2": up_((2.6, -0.3, 6.92)),
            "Gear1": front((-2.6, -1.0, 3.5)), "Gear2": front((2.6, -1.0, 3.5)), "Steam1": up_((0, 0.6, 8.6)),
            "Hit": frame((-2.6, -3.3, 1.2), out=(0, -1, 0.6)), "Trail": frame((-2.6, -1.1, 2.25), out=FROST_BIT_DIR),
            "NamePlate": front((0, -3.55, 0.4)), "Aura": up_((0, 0, 1.1)), "Top": up_((0, 0.6, 8.6))}
    return b, atts, ("FrostTech", None)


# ---------- tier 4: Enchanted ----------

def island_v3(b, role, top, radius, thick, spin):
    m = M((0, 0, top), (0, 0, spin))
    b.add(role, place(floating_platform(radius, thick, "Moonstone", "StoneDark", "Gold", tip=False), m))
    # a gold spiral flute round the cone under the rock, so each island reads as a floating drill bit
    helix, turns, top_z, tip_z = [], 2.5, -thick - 0.12, -thick - radius * 1.1
    for k in range(29):
        s = k / 28
        r = radius * 0.8 * (1 - s) ** 1.05 + 0.04
        a = 2 * math.pi * turns * s
        helix.append(Vector((r * math.cos(a), r * math.sin(a), top_z + (tip_z - top_z) * s * 0.96)))
    flute = bmesh.new()
    sweep(flute, helix, radius * 0.055, 5, radius_end=radius * 0.02)
    b.add(role, place([(flute, "Gold", 0.0, False)], m))
    inlay = bmesh.new()  # an inlaid hex tile on top with a gold inner rim
    lathe(inlay, [(0, 0), (radius * 0.72, 0), (radius * 0.72, 0.05), (0, 0.05)], 6)
    b.add(role, place([(inlay, "FrostLight", 0.0, False)], m))
    b.add(role, place(trim_ring(radius * 0.72, 0.04, "Gold", minor=0.035, segments=6), m))
    for k in range(6):  # gems set round the rim
        a = k * math.pi / 3 + math.pi / 6
        r = radius * 0.93
        b.add(role, place(gem_setting(0.11, "MagicPink" if k % 2 else "AuroraCyan", "Gold", 4), m @ frame((r * math.cos(a), r * math.sin(a), -thick * 0.35), out=(math.cos(a), math.sin(a), 0))))
    for k in range(3):  # small hanging crystals under the rock
        a = k * 2 * math.pi / 3 + 0.4
        hang = cut_crystal(radius * 0.42, radius * 0.09, "RuneViolet", sides=6)
        b.add(role + "Glow", place(hang, m @ Matrix.Translation((radius * 0.45 * math.cos(a), radius * 0.45 * math.sin(a), -thick - radius * 0.35)) @ Matrix.Rotation(math.pi, 4, "X")))


def tier_enchanted(b):
    dais = bmesh.new()
    lathe(dais, [(0, 0), (4.4, 0), (4.4, 0.3), (4.2, 0.35), (4.2, 0.55), (3.95, 0.8), (0, 0.8)], 6)
    b.add("Dais", [(dais, "Moonstone", 0.04, False)])
    plinth = bmesh.new()
    lathe(plinth, [(0, -0.01), (4.55, -0.01), (4.55, 0.18), (0, 0.18)], 6)
    b.add("Dais", [(plinth, "StoneDark", 0.03, False)])
    b.add("Dais", place(trim_ring(4.07, 0, "RuneViolet", minor=0.08, segments=6), M((0, 0, 0.56))))
    b.add("Dais", place(engraved_rune_ring(3.1, "RuneGlow", "ArcaneDeep", "RuneViolet", 14), M((0, 0, 0.8))))
    for k in range(6):  # crystal clusters on the corners, gems on the faces
        a = k * math.pi / 3
        b.add("DaisCrystals", place(cut_crystal_cluster(0.55, "CrystalCyan" if k % 2 else "RuneViolet", "Moonstone", 4), M((3.9 * math.cos(a), 3.9 * math.sin(a), 0.78), (0, 0, a))))
        fa = a + math.pi / 6
        apothem = 4.4 * math.cos(math.pi / 6)
        b.add("Dais", place(gem_setting(0.14, "AuroraCyan", "Gold", 4), frame((apothem * math.cos(fa), apothem * math.sin(fa), 0.18), out=(math.cos(fa), math.sin(fa), 0))))
    for top, radius, thick, role in ((5.2, 2.3, 0.5, "IslandA"), (8.0, 1.8, 0.45, "IslandB"), (10.6, 1.3, 0.4, "IslandC")):
        island_v3(b, role, top, radius, thick, top * 0.3)
    b.add("Orbit", place(engraved_rune_ring(2.7, "AuroraGreen", "ArcaneDeep", "Moonstone", 12), M((0, 0, 6.4), (0.32, 0.12, 0))))
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        p = (3.3 * math.cos(a), 3.3 * math.sin(a), 2.2 + 0.6 * (k % 2))
        b.add("Orbit", place(cut_crystal(1.0, 0.2, "AuroraGreen", (0.3, 0.2)), M(p)))
        orbit = bmesh.new()
        torus(orbit, M((p[0], p[1], p[2] + 0.45), (1.2, 0.3 * k, 0)), 0.42, 0.025, 16, 4)
        b.add("Orbit", [(orbit, "AuroraGreen", 0.0, True)])
    for k in range(4):  # floating rune stones
        a = k * math.pi / 2 + 1.2
        stone = cage_box((0.5, 0.35, 0.6), 1)
        stone = subsurf(stone, 1)
        stone.transform(M((3.0 * math.cos(a), 3.0 * math.sin(a), 4.6 + 0.5 * (k % 2)), (0.2, 0.1, a)))
        b.add("RuneStones", [(stone, "StoneDark", 0.0, False)])
        b.add("RuneStones", place(rune_glyph(0.34, k + 2, "RuneGlow", 0.03), frame((3.0 * math.cos(a), 3.0 * math.sin(a), 4.6 + 0.5 * (k % 2)), out=(math.cos(a), math.sin(a), 0)) @ M((0, 0, 0.17))))
    b.add("Crown", place(cut_crystal_cluster(1.25, "CrystalCyan", "Moonstone", 6), M((0, 0, 10.6))))
    b.add("Crown", place(gem_setting(0.36, "MagicPink", "Gold", 6), M((0, 0, 13.0))))
    halo = bmesh.new()
    torus(halo, M((0, 0, 13.4), (math.pi / 2, 0, 0.5)), 0.75, 0.04, 24, 4)
    b.add("Crown", [(halo, "Gold", 0.0, False)])
    drill = frame(ENCHANTED_BIT_AT, out=ENCHANTED_BIT_DIR)
    b.add("BitRing", place(trim_ring(1.05, 0, "Moonstone", minor=0.09, segments=18), drill @ M((0, 0, 0.25))))
    b.add("BitRing", place(trim_ring(1.05, 0, "RuneGlow", True, minor=0.035, segments=18), drill @ M((0, 0, 0.36))))
    atts = {"Bit": drill, "Lamp1": up_((1.75, 0, 5.2)), "Lamp2": up_((-1.3, 0, 8.0)), "Gear1": front((0, -2.05, 4.85)),
            "Steam1": up_((0, 0, 13.6)), "Hit": frame((0, -4.1, 0.9), out=(0, -1, 0.6)), "Trail": drill,
            "NamePlate": front((0, -3.85, 0.4)), "Aura": up_((0, 0, 0.8)), "Top": up_((0, 0, 13.6))}
    return b, atts, ("CrystalV3", None)


# ---------- tier 5: Legendary, the Mecha Mole Titan ----------

def mole_head():
    """The head: a subdivided cage (full size about 5.8 x 5.1 x 4.9 studs) with round cheeks, a
    narrower crown and a muzzle pushed forward."""
    cage = cage_box((5.8, 5.1, 4.9), 2)
    radii = Vector((2.75, 2.45, 2.35))
    for v in cage.verts:  # round the box cage toward an ellipsoid first: a round head, not a rounded cube
        unit = Vector((v.co.x / radii.x, v.co.y / radii.y, v.co.z / radii.z))
        if unit.length > 1e-6:
            unit.normalize()
            v.co = v.co.lerp(Vector((unit.x * radii.x, unit.y * radii.y, unit.z * radii.z)) * 1.04, 0.85)
    for v in cage.verts:
        x, y, z = v.co
        if y < -1.1:  # the face: push the lower middle forward into a muzzle, round the cheeks out
            v.co.y -= 0.75 * max(0, 1 - abs(x) / 3.1) * max(0, 1 - abs(z + 0.65) / 2.45)
            if abs(x) > 1.8 and z < 0.65:
                v.co.x *= 1.08
    return subsurf(cage, 2)


class HeadSurface:
    """Measures the finished head so the face parts sit on it, not in front of it or inside it."""

    def __init__(self, bm):
        self.points = [v.co.copy() for v in bm.verts]

    def front(self, x, z, reach=0.35):
        ys = [p.y for p in self.points if abs(p.x - x) < reach and abs(p.z - z) < reach]
        return min(ys)

    def side(self, z, reach=0.3):
        return max(p.x for p in self.points if abs(p.z - z) < reach)

    def band(self, z, reach=0.25):
        ring = [p for p in self.points if abs(p.z - z) < reach]
        return (max(p.x for p in ring) - min(p.x for p in ring)) / 2, (max(p.y for p in ring) - min(p.y for p in ring)) / 2, (max(p.y for p in ring) + min(p.y for p in ring)) / 2

    def top(self):
        return max(p.z for p in self.points)


def mole_paw(wrist, direction, b, role):
    d = Vector(direction).normalized()
    cage = cage_box((1.5, 0.8, 1.3), 1)
    for v in cage.verts:
        if v.co.z > 0.3:
            v.co.x *= 1.15
    paw = subsurf(cage, 2)
    paw.transform(Matrix.Translation(wrist) @ align_z(d) @ M((0, 0, 0.35)))
    b.add(role, [(paw, "MoleFurLight", 0.0, False)], organic=True)
    lateral = d.cross(Vector((0, 0, 1)))
    lateral = lateral.normalized() if lateral.length > 1e-3 else Vector((1, 0, 0))
    for k in (-1, 0, 1):
        base = wrist + d * 0.95 + lateral * (k * 0.45)
        b.add(role, place(curved_claw(0.95, 0.2, 0.4, "SteelLight"), Matrix.Translation(base) @ align_z(d + Vector((0, 0, -0.1)))))


def mole_foot(x, b):
    cage = cage_box((1.8, 2.5, 0.8), 0)
    foot = subsurf(cage, 2)
    foot.transform(M((x, 0.2, 1.5)))
    b.add("Legs", [(foot, "SteelDark", 0.0, False)])
    for k in (-1, 0, 1):
        b.add("Legs", place(curved_claw(0.55, 0.16, 0.25, "Gold"), frame((x + k * 0.5, -1.0, 1.45), out=(0, -1, -0.15), up=(0, 0, 1))))


def tier_titan(b):
    # the plinth: panels, vents, bolts, gold trim and aurora strips, the dig crater with broken ice
    b.add("Platform", block((9.7, 9.6, 0.9), "Gunmetal", corner=0.9, edge=0.25))
    b.add("Platform", place(block((9.1, 9.0, 0.3), "StoneLight", corner=0.7, edge=0.1), M((0, 0, 0.9))))
    for sx in (-1, 1):
        b.add("Platform", place(vent(1.6, 0.4, 5, "Gunmetal", "SteelDark"), front((sx * 3.2, -4.79, 0.45))))
        b.add("Platform", place(gem_setting(0.18, "AuroraCyan", "Gold", 4), M((sx * 4.45, -4.4, 1.2))))
    b.add("Trim", place(block((9.8, 9.7, 0.16), "Gold", corner=0.92, edge=0.06), M((0, 0, 0.72))))
    b.add("Trim", trim_strip((-2.4, -4.82, 0.4), (2.4, -4.82, 0.4), 0.16, "AuroraGreen", True))
    crater = bmesh.new()
    torus(crater, Matrix.Translation((0, -3.3, 1.2)) @ Matrix.Diagonal((1.3, 0.85, 0.45, 1)), 1.2, 0.35, 16, 6)
    b.add("Platform", [(crater, "StoneDark", 0.0, False)])
    for k in range(3):
        a = k * 2.0 + 0.3
        b.add("Platform", place(cut_crystal(0.6, 0.22, "IceBlue", (0.5 * math.cos(a), 0.5 * math.sin(a)), glow=False), M((1.85 * math.cos(a), -3.3 + 0.9 * math.sin(a), 1.15))))
    # legs: thighs with knee pads and pistons, subdivided feet with curved gold toe claws
    for sx in (-1, 1):
        b.add("Legs", place(cyl(0.75, 1.9, "Gunmetal", 16), M((sx * 1.5, 0.7, 1.1))))
        pad = bmesh.new()
        blob(pad, (sx * 1.5, 0.05, 2.3), (0.55, 0.35, 0.5), 1)
        b.add("Legs", [(pad, "SteelLight", 0.0, False)])
        b.add("Legs", piston((sx * 1.5, 1.45, 1.6), (sx * 1.5, 1.45, 2.9), 0.15, "SteelDark", "SteelLight"))
        mole_foot(sx * 1.6, b)
        b.add("Legs", place(gear(0.5, 8, 0.2, 0.11, "Brass", "Gold"), frame((sx * 2.28, 0.7, 2.25), out=(sx, 0, 0))))  # knee gears
    # the body: plates, panel bands, the belly, gold and aurora bands, the crest in a setting, rivets
    body = bmesh.new()
    lathe(body, [(0, 2.5), (2.3, 2.6), (3.1, 3.8), (3.3, 5.2), (3.0, 6.8), (2.2, 7.9), (0, 8.3)], 20)
    body = subsurf(body, 1)
    b.add("Fur", [(body, "MoleFur", 0.0, False)], organic=True)
    for z, r in ((4.2, 3.24), (6.5, 3.06)):
        band = bmesh.new()
        torus(band, M((0, 0, z)), r, 0.05, 24, 4)
        b.add("Body", [(band, "MoleFurLight", 0.0, False)])
    for sx in (-1, 1):  # armour over the fur: big riveted steel pauldrons over the shoulders
        pauldron = bmesh.new()
        lathe(pauldron, [(0, 0), (1.55, 0), (1.5, 0.35), (1.15, 0.75), (0.55, 0.95), (0, 1.0)], 12,
              frame((sx * 2.7, -0.4, 7.25), out=(sx * 0.75, 0, 1)))
        b.add("Armour", [(pauldron, "SteelLight", 0.0, False)])
        b.add("Armour", place(trim_ring(1.5, 0, "Gunmetal", minor=0.08, segments=16), frame((sx * 2.7, -0.4, 7.25), out=(sx * 0.75, 0, 1)) @ M((0, 0, 0.12))))
        for k in range(5):
            a = k * 2 * math.pi / 5
            b.add("Armour", place(rivet(0.09, "Gold"), frame((sx * 2.7, -0.4, 7.25), out=(sx * 0.75, 0, 1)) @ M((1.2 * math.cos(a), 1.2 * math.sin(a), 0.62))))
    for sx in (-1, 1):  # riveted side plates
        a = math.radians(90 + sx * 62)
        b.add("Body", place(riveted_plate(1.5, 1.7, 0.08, "MoleFurLight", "Gold", 0.7), frame((3.25 * math.cos(a), 3.25 * math.sin(a) - 0.3, 5.0), out=(math.cos(a), math.sin(a), 0.05))))
    belly = bmesh.new()
    lathe(belly, [(0, 0), (1.9, 0), (1.6, 0.35), (0, 0.45)], 16, frame((0, -2.85, 4.9), out=(0, -1, 0.05)))
    belly_rim = bmesh.new()
    torus(belly_rim, frame((0, -2.95, 4.9), out=(0, -1, 0.05)), 1.85, 0.07, 24, 4)
    b.add("Body", [(belly, "MoleFurLight", 0.0, False), (belly_rim, "Gold", 0.0, False)])
    for z, radius in ((2.85, 2.55), (7.35, 2.6)):
        b.add("BodyTrim", place(trim_ring(radius, 0, "Gold", minor=0.13, segments=20), M((0, 0, z))))
    b.add("BodyTrim", place(trim_ring(3.27, 0, "AuroraGreen", True, minor=0.1, segments=20), M((0, 0, 5.6))))
    b.add("Body", place(crest(1.5, 1.8, 0.2, "Gold", "DeepIce", "SnowWhite", "AuroraCyan"), front((0, -3.2, 6.45), 0.15)))
    for k in range(3):
        b.add("Body", place(gem_setting(0.1, "AuroraCyan", "Gold", 4), front((-0.4 + k * 0.4, -3.42, 7.55), 0.2)))
    for k in range(6):
        a = math.pi + (k + 0.5) * math.pi / 6
        b.add("Body", place(rivet(0.11, "Gold"), frame((3.2 * math.cos(a), 3.2 * math.sin(a), 4.2), out=(math.cos(a), math.sin(a), 0))))
    # back: a lidded backpack with vents, twin stacks with grilles, hoses to the shoulders
    b.add("Back", place(lidded_box((3.0, 1.4, 2.4), "Gunmetal", "SteelDark", "Gold"), M((0, 2.75, 4.6), (0, 0, 0))))
    for sx in (-1, 1):
        b.add("Back", place(vent(0.9, 0.7, 4, "SteelDark", "Gunmetal"), frame((sx * 0.8, 3.47, 5.6), out=(0, 1, 0))))
        stack = Matrix.Translation((sx * 1.2, 2.6, 6.6)) @ Matrix.Rotation(-0.3, 4, "X")
        b.add("Back", place(cyl(0.42, 2.4, "Gunmetal", 14), stack))
        b.add("Back", place(trim_ring(0.44, 0, "Gold", minor=0.08, segments=14), stack @ M((0, 0, 2.3))))
        b.add("Back", place(trim_ring(0.44, 0, "SteelDark", minor=0.06, segments=14), stack @ M((0, 0, 0.8))))
        grille = bmesh.new()
        lathe(grille, [(0, 0), (0.36, 0), (0.36, 0.05), (0, 0.05)], 6, stack @ M((0, 0, 2.38)))
        b.add("Back", [(grille, "Iron", 0.0, False)])
        b.add("Hoses", cable((sx * 1.3, 2.2, 6.4), (sx * 3.0, 0.3, 6.7), 0.55, 0.16, "Rubber", "Gold", ribs=0))
        # an exhaust pipe on each side of the backpack: up and out, with a flared, blackened tip
        exhaust = bmesh.new()
        sweep(exhaust, [V(sx * 1.55, 3.2, 4.2), V(sx * 2.1, 3.35, 5.0), V(sx * 2.35, 3.35, 7.6), V(sx * 2.45, 3.2, 8.9)], 0.24, 10)
        b.add("Back", [(exhaust, "Steel", 0.0, False)])
        tipm = frame((sx * 2.45, 3.2, 8.9), out=(sx * 0.1, -0.1, 1))
        flare = bmesh.new()
        lathe(flare, [(0.2, -0.1), (0.3, -0.05), (0.42, 0.3), (0.36, 0.34), (0.2, 0.05)], 14, tipm)
        b.add("Back", [(flare, "Iron", 0.0, False)])
    # the head: subdivided, with goggle rims, glowing eyes, brows, cheeks, ears, whiskers, buck teeth
    head = mole_head()
    head.transform(M((0, -1.0, 10.2)))
    hs = HeadSurface(head)
    b.add("Head", [(head, "MoleFur", 0.0, False)], organic=True)
    band_z = 12.05  # a headband above the eyes, hugging the head
    rx, ry, cy = hs.band(band_z)
    strap = bmesh.new()
    torus(strap, Matrix.Translation((0, cy, band_z)) @ Matrix.Diagonal((rx + 0.06, ry + 0.06, 1, 1)), 1.0, 0.14, 32, 4)
    b.add("Head", [(strap, "Gunmetal", 0.0, False)])
    helmet = bmesh.new()  # a riveted steel cap over the crown, its rim sitting on the headband
    lathe(helmet, [(0, hs.top() + 0.12), (rx * 0.55, hs.top() + 0.02), (rx * 0.92, band_z + 0.55), (rx + 0.1, band_z + 0.05), (rx + 0.04, band_z - 0.05), (0, band_z - 0.05)], 16,
          Matrix.Translation((0, cy, 0)) @ Matrix.Diagonal((1, ry / rx, 1, 1)))
    b.add("Helmet", [(helmet, "Steel", 0.0, False)])
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        b.add("Helmet", place(rivet(0.08, "Gold"), frame((rx * 0.98 * math.cos(a), cy + ry * 0.98 * math.sin(a), band_z + 0.32), out=(math.cos(a), math.sin(a), 0.6))))
    for sx in (-1, 1):
        eye_at = frame((sx * 0.98, hs.front(sx * 0.98, 10.9) + 0.18, 10.9), out=(0, -1, 0.12))
        rim = bmesh.new()
        torus(rim, eye_at @ M((0, 0, 0.05)), 0.88, 0.14, 20, 4)
        b.add("Head", [(rim, "Gunmetal", 0.0, False)])
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            b.add("Head", place(rivet(0.07, "Gold"), eye_at @ M((0.88 * math.cos(a), 0.88 * math.sin(a), 0.18))))
        b.add("Eyes", place(cartoon_eye(0.76, "CrystalCyan", look=(0.0, 0.18), lid=None), eye_at))
        brow_cage = cage_box((1.1, 0.3, 0.26), 0)
        brow = subsurf(brow_cage, 2)
        brow.transform(frame((sx * 1.0, hs.front(sx * 1.0, 11.75) + 0.05, 11.75), out=(0, -1, 0.25)) @ M((0, 0, 0.12), (0, 0, sx * 0.28)))
        b.add("Head", [(brow, "Gunmetal", 0.0, False)])
        blush = bmesh.new()
        blob(blush, (sx * 1.85, hs.front(sx * 1.85, 9.65) + 0.1, 9.65), (0.46, 0.22, 0.3), 1)
        b.add("Head", [(blush, "Blush", 0.0, False)])
        ear_at = frame((sx * (hs.side(11.5) - 0.35), -0.7, 11.5), out=(sx, -0.1, 0.45))
        ear = bmesh.new()
        lathe(ear, [(0, 0), (0.74, 0), (0.8, 0.2), (0.7, 0.42), (0, 0.45)], 16, ear_at)
        inner_ear = bmesh.new()
        lathe(inner_ear, [(0, 0), (0.48, 0), (0.42, 0.08), (0, 0.1)], 14, ear_at @ M((0, 0, 0.42)))
        b.add("Head", [(ear, "MoleFurLight", 0.0, False), (inner_ear, "Blush", 0.0, False)])
        b.add("Head", place(trim_ring(0.78, 0, "Gold", minor=0.08, segments=16), ear_at @ M((0, 0, 0.2))))
        for k in range(2):  # metal whiskers
            y0 = hs.front(sx * 0.95, 9.3 - 0.15 * k)
            w = bmesh.new()
            sweep(w, [V(sx * 0.95, y0 + 0.05, 9.3 - 0.15 * k), V(sx * 1.7, y0 - 0.15, 9.35 - 0.22 * k), V(sx * 2.4, y0 + 0.05, 9.5 - 0.35 * k)], 0.03, 6, radius_end=0.015)
            b.add("Head", [(w, "SteelLight", 0.0, False)])
    for sx in (-1, 1):
        tooth = bmesh.new()
        rounded_block(tooth, (0.32, 0.18, 0.42), M((sx * 0.18, hs.front(sx * 0.18, 8.55) + 0.02, 8.35), (0.3, 0, 0)), corner=0.08, edge=0.06, corner_seg=2, edge_seg=2)
        b.add("Head", [(tooth, "EyeWhite", 0.0, False)])
    mouth = bmesh.new()
    my = hs.front(0, 8.7)
    sweep(mouth, [V(-0.55, my + 0.1, 8.82), V(-0.25, my - 0.02, 8.7), V(0.25, my - 0.02, 8.7), V(0.55, my + 0.1, 8.82)], 0.06, 8)
    b.add("Head", [(mouth, "EyeDark", 0.0, False)])
    nose_y = hs.front(0, 9.85) + 0.1
    nose_at = frame((0, nose_y, 9.85), out=TITAN_NOSE_DIR)
    housing = bmesh.new()
    lathe(housing, [(0, -0.4), (1.25, -0.4), (1.35, 0.1), (1.2, 0.65), (1.05, 0.75), (0, 0.75)], 18, nose_at)
    b.add("Snout", [(housing, "Gunmetal", 0.0, False)])
    b.add("Snout", place(trim_ring(1.22, 0, "Gold", minor=0.14, segments=18), nose_at @ M((0, 0, 0.72))))
    b.add("Snout", place(gear(1.0, 12, 0.22, 0.12, "Brass", "Gold"), nose_at @ M((0, 0, 0.0))))
    for k in range(6):
        a = k * math.pi / 3
        b.add("Snout", place(rivet(0.08, "Gold"), nose_at @ M((1.27 * math.cos(a), 1.27 * math.sin(a), 0.4))))
    for sx in (-1, 1):  # hydraulic struts from the cheeks to the snout housing
        b.add("Snout", piston(V(sx * 1.6, nose_y + 0.9, 8.9), (nose_at @ Vector((sx * 0.95, -0.3, 0.45))), 0.11, "SteelDark", "SteelLight"))
    bit_at = nose_at @ M((0, 0, 0.72))  # the bit sits at the front of the housing
    # arms: shoulder housings with bolt rings, arms with elbow pistons, subdivided paws, curved claws
    for side, sx, elbow_at, hand_at in (("ArmL", -1, (-3.85, -1.7, 5.1), (-2.9, -3.0, 3.4)), ("ArmR", 1, (3.9, -1.3, 7.6), (4.0, -1.9, 9.4))):
        shoulder = Vector((sx * 3.15, -0.4, 6.3))
        housing = frame(shoulder - Vector((sx * 0.25, 0, 0)), out=(sx, 0, 0))
        b.add(side, place(cyl(1.1, 0.9, "Gunmetal", 16), housing))
        for k in range(8):
            a = k * math.pi / 4
            b.add(side, place(rivet(0.08, "Gold"), housing @ M((0.85 * math.cos(a), 0.85 * math.sin(a), 0.9))))
        upper, lower, joint = bmesh.new(), bmesh.new(), bmesh.new()
        sweep(upper, [shoulder, Vector(elbow_at)], 0.72, 12)
        sweep(lower, [Vector(elbow_at), Vector(hand_at)], 0.65, 12)
        blob(joint, elbow_at, (0.82, 0.82, 0.82), 2)
        b.add(side, [(upper, "SteelDark", 0.0, False), (lower, "SteelDark", 0.0, False), (joint, "Gunmetal", 0.0, False)])
        for t in (0.5,):
            p = shoulder.lerp(Vector(elbow_at), t)
            b.add(side, place(trim_ring(0.74, 0, "Gunmetal", minor=0.07, segments=16), Matrix.Translation(p) @ align_z(Vector(elbow_at) - shoulder)))
        out = Vector((0, 0.75, 0))
        b.add(side, piston(shoulder + out * 0.9 + Vector((0, 0, -0.4)), Vector(elbow_at) + out * 0.8, 0.13, "Gunmetal", "SteelLight"))
        # the elbow: a gear on the outside of the joint
        b.add(side + "Gear", place(gear(0.55, 9, 0.22, 0.12, "Brass", "Gold"), frame(Vector(elbow_at) + Vector((sx * 0.62, 0, 0)), out=(sx, 0, 0))))
        # the armoured gauntlet over the forearm: a chunky plated box with ridges and rivets
        fore = Vector(hand_at) - Vector(elbow_at)
        mid = Vector(elbow_at) + fore * 0.55
        gauntlet = Matrix.Translation(mid) @ align_z(fore)
        b.add(side, place(block((1.65, 1.5, fore.length * 0.72), "Gunmetal", corner=0.35, edge=0.16), gauntlet @ M((0, 0, -fore.length * 0.36))))
        b.add(side, place(block((1.72, 0.3, fore.length * 0.5), "SteelLight", corner=0.1, edge=0.06), gauntlet @ M((0, -0.65, -fore.length * 0.25))))
        b.add(side, place(rivet_ring(0.86, 6, 0.08, "Gold"), gauntlet @ M((0, 0, fore.length * 0.36))))
        mole_paw(Vector(hand_at), Vector(hand_at) - Vector(elbow_at), b, side)
    nose_dir = TITAN_NOSE_DIR
    atts = {"Bit": bit_at, "Lamp1": up_((3.1, -0.4, 7.15)), "Lamp2": up_((-3.1, -0.4, 7.15)),
            "Gear1": frame((3.85, -0.4, 6.3), out=(1, 0, 0)), "Gear2": frame((-3.85, -0.4, 6.3), out=(-1, 0, 0)),
            "Steam1": up_((1.2, 3.25, 8.95)), "Steam2": up_((-1.2, 3.25, 8.95)),
            "Hit": frame((0, -4.0, 1.25), out=(0, -1, 0.6)), "Trail": bit_at,
            "Crown": up_((0, -1.0, hs.top() - 0.15)), "NamePlate": front((0, -4.82, 0.45)), "Aura": up_((0, 0, 1.2)), "Top": up_((0, -1.0, hs.top()))}
    return b, atts, ("TitanNose", None)


# ---------- working parts and the Legendary upgrade sets, v3 ----------

_working_part_v2 = working_part


def working_part(b, atts, kind):
    if kind not in ("CrystalV3", "TitanNose", "TitanDiamond"):
        _working_part_v2(b, atts, kind)  # the v2 bits, one mesh per bit (each spins)
        return
    bits = [atts[k] for k in sorted(atts) if k.startswith("Bit")]
    for i, matrix in enumerate(bits):
        role = "Bit" + "AB"[i]
        if kind == "CrystalV3":  # a floating crystal drill: a violet spiral bit with a glowing flute
            b.add(role, place(spiral_bit(2.4, 0.72, "RuneGlow", "RuneViolet", 3.0, glow=True), matrix))
            collar = bmesh.new()
            lathe(collar, [(0, -0.05), (0.85, -0.05), (0.95, 0.15), (0.7, 0.35), (0, 0.3)], 16)
            b.add(role + "Collar", place([(collar, "Gold", 0.0, False)], matrix @ M((0, 0, -0.3))))
            for k in range(6):
                a = k * math.pi / 3
                b.add(role + "Collar", place(cut_gem(0.08, "AuroraCyan"), matrix @ M((0.88 * math.cos(a), 0.88 * math.sin(a), -0.1))))
        elif kind == "TitanNose":
            b.add(role, place(spiral_bit(2.35, 1.1, "Brass", "SteelLight", 3.5), matrix))
        elif kind == "TitanDiamond":
            b.add(role, place(spiral_bit(2.45, 1.14, "CrystalCyan", "Diamond", 3.5, glow=True), matrix))


def legendary_upgrades(b, fx, atts):
    working_part(b, atts, "TitanDiamond")
    for key in ("Lamp1", "Lamp2"):
        b.add("Beacon" + key[-1], place(warning_lamp(0.42, "AuroraGreen", "Gold", "Gunmetal"), atts[key]))
        b.add("Beacon" + key[-1], place(rivet_ring(0.42, 6, 0.05, "Gold"), atts[key] @ M((0, 0, 0.02))))
    for key in ("Gear1", "Gear2"):
        b.add("Gear%sBig" % key[-1], place(spoked_gear(0.95, 10, 0.28, 0.16, 4, "Brass", "Gold"), atts[key] @ M((0, 0, 0.15))))
        b.add("Gear%sSmall" % key[-1], place(spoked_gear(0.5, 7, 0.28, 0.13, 3, "Copper", "Gold"), atts[key] @ M((0.85, 0.85, 0.35))))
    for key in ("Steam1", "Steam2"):
        for k, (dx, dz, r) in enumerate(((0.0, 0.4, 0.3), (0.2, 0.95, 0.42), (-0.15, 1.6, 0.55))):
            puff = bmesh.new()
            blob(puff, (dx, 0, dz), (r, r, r * 0.85), 2)
            fx.add("Steam" + key[-1], place([(puff, "SnowWhite", 0.0, False)], atts[key]))
    pieces = []
    for k in range(9):
        a = k * 2.4
        pieces += place(cut_crystal(0.4, 0.12, "IceBlue" if k % 2 else "Diamond", (a, 0.5 * k), glow=False), M((0.7 * math.cos(a), 0.7 * math.sin(a), 0.2 + 0.2 * k)))
    for k in range(6):
        a = k * 1.1 + 0.4
        spark = bmesh.new()
        cylinder(spark, (0.4 * math.cos(a), 0.4 * math.sin(a), 0.2), 0.05, 0.7, 4, direction=(math.cos(a), math.sin(a), 1.3), top=0.0)
        pieces.append((spark, "LampYellow", 0.0, True))
    fx.add("Hit", place(pieces, atts["Hit"]))
    crown = []
    crown += trim_ring(1.0, 0.1, "Gold", minor=0.16, segments=18)
    crown += trim_ring(1.0, 0.45, "Gold", minor=0.07, segments=18)
    for k in range(5):
        a = math.pi / 2 + (k - 2) * 0.55
        spike = bmesh.new()
        lathe(spike, [(0, 0), (0.22, 0), (0.2, 0.3), (0.08, 0.7 + (0.25 if k == 2 else 0)), (0, 0.8 + (0.25 if k == 2 else 0))], 8, M((math.cos(a), math.sin(a), 0.1)))
        crown.append((spike, "Gold", 0.0, False))
        gem_at = frame((math.cos(a) * 1.06, math.sin(a) * 1.06, 0.32), out=(math.cos(a), math.sin(a), 0))
        if k in (0, 2, 4):
            crown += place(gem_setting(0.14 if k != 2 else 0.18, "MagicPink" if k == 2 else "AuroraCyan", "Gold", 4), gem_at)
        else:
            crown += place(cut_gem(0.1, "AuroraCyan"), gem_at @ M((0, 0, 0.08)))
    b.add("Crown", place(crown, atts["Crown"] @ M((0, 0, -0.35), (0.25, 0, 0))))
    trail = []
    for k in range(14):
        a = k * 0.8
        trail += place(cut_gem(0.14, "CrystalCyan" if k % 2 else "Diamond"), M((1.0 * math.cos(a) * (1 - k / 22), 1.0 * math.sin(a) * (1 - k / 22), 0.3 + k * 0.25), (a, k, 0)))
    fx.add("Trail", place(trail, atts["Trail"]))
    b.add("NamePlate", place(name_plate(3.2, 0.62, "PineLight", "Gold"), atts["NamePlate"]))
    sparkles = []
    for k in range(12):
        a = k * 2.2
        s = bmesh.new()
        lathe(s, [(0, -0.22), (0.09, 0), (0, 0.22)], 4, M((4.6 * math.cos(a), 1.0 + 3.6 * math.sin(a), 3.5 + 0.9 * (k % 5))))
        sparkles.append((faceted(s), "LampYellow", 0.0, True))
    fx.add("Sparkles", sparkles)




# ---------- the framework's interface ----------

def _station(tier_fn):
    def build(b):
        _, atts, (working, _) = tier_fn(b)
        working_part(b, atts, working)
        if tier_fn is tier_titan:  # stand the Titan back on its plinth so the snout stays over the pad
            shift = Matrix.Translation((0, TITAN_SHIFT, 0))
            for key, part in b.parts.items():
                if not re.search(r"(Platform|T5Trim)(Glow)?$", key):
                    part.bm.transform(shift)
            atts = {k: (m if k in ("Hit", "NamePlate", "Aura") else shift @ m) for k, m in atts.items()}
        return {("Work" + k[3:] if k.startswith("Bit") else k): m for k, m in atts.items()}
    return build


TIER_FNS = [_station(f) for f in (tier_scrappy, tier_workshop, tier_frosttech, tier_enchanted, tier_titan)]

BIT_LOOK = {  # the 1st upgrade (steel bits) and the 5th (diamond bits) in each tier's look
    1: (lambda: auger("Steel"), lambda: auger("Diamond")),
    2: (lambda: spiral_bit(2.3, 0.52, "SteelLight", "Steel"), lambda: spiral_bit(2.4, 0.55, "CrystalCyan", "Diamond", 3.5, glow=True)),
    3: (lambda: spiral_bit(2.3, 0.58, "SteelLight", "IceBlue", 3.5), lambda: spiral_bit(2.4, 0.6, "CrystalCyan", "Diamond", 3.5, glow=True)),
    4: (lambda: spiral_bit(2.5, 0.76, "SteelLight", "Moonstone", 3.0), lambda: spiral_bit(2.6, 0.8, "CrystalCyan", "Diamond", 3.0, glow=True)),
}


def UPGRADES(u, t, atts, b, fx):
    works = [atts[k] for k in sorted(atts) if k.startswith("Work")]
    if t == 5:  # the Mecha Mole Titan: the v3 Masterwork pieces, one upgrade at a time
        if u == 1:
            working_part(b, {"Bit": atts["Work"]}, "TitanDiamond")
        elif u == 2:
            for key in ("Lamp1", "Lamp2"):
                b.add("Beacon" + key[-1], place(warning_lamp(0.42, "AuroraGreen", "Gold", "Gunmetal"), atts[key]))
        elif u == 3:
            for key in ("Gear1", "Gear2"):
                b.add("Gear%sBig" % key[-1], place(gear(0.95, 12, 0.28, 0.16, "Brass", "Gold"), atts[key] @ M((0, 0, 0.15))))
                b.add("Gear%sSmall" % key[-1], place(gear(0.5, 6, 0.28, 0.13, "Copper", "Gold"), atts[key] @ M((0.85, 0.85, 0.35))))
            for key in ("Steam1", "Steam2"):
                fx.add("Steam" + key[-1], place(tier_puff(5), atts[key]))
        elif u == 4:
            fx.add("Hit", place(hit_standin(5), atts["Hit"]))
        else:  # the jewelled crown and the crystal trail (the name plate and sparkles come with every Masterwork)
            crown = []
            crown += trim_ring(1.0, 0.1, "Gold", minor=0.16, segments=14)
            crown += trim_ring(1.0, 0.45, "Gold", minor=0.07, segments=14)
            for k in range(5):
                a = math.pi / 2 + (k - 2) * 0.55
                spike = bmesh.new()
                lathe(spike, [(0, 0), (0.22, 0), (0.2, 0.3), (0.08, 0.7 + (0.25 if k == 2 else 0)), (0, 0.8 + (0.25 if k == 2 else 0))], 6, M((math.cos(a), math.sin(a), 0.1)))
                crown.append((spike, "Gold", 0.0, False))
                gem_at = frame((math.cos(a) * 1.06, math.sin(a) * 1.06, 0.32), out=(math.cos(a), math.sin(a), 0))
                crown += place(gem_setting(0.14 if k != 2 else 0.18, "MagicPink" if k == 2 else "AuroraCyan", "Gold", 4), gem_at)
            b.add("Crown", place(crown, atts["Crown"] @ M((0, 0, -0.35), (0.25, 0, 0))))
            trail = []
            for k in range(14):
                a = k * 0.8
                trail += place(cut_gem(0.14, "CrystalCyan" if k % 2 else "Diamond"), M((1.0 * math.cos(a) * (1 - k / 22), 1.0 * math.sin(a) * (1 - k / 22), 0.3 + k * 0.25), (a, k, 0)))
            fx.add("Trail", place(trail, atts["Trail"]))
        return
    if u in (1, 5):  # steel bits, then diamond bits with a crystal trail
        for i, m in enumerate(works):
            b.add("Bit" + "AB"[i], place(BIT_LOOK[t][0 if u == 1 else 1](), m))
        if u == 5:
            trail = []
            for k in range(8):
                a = k * 0.8
                trail += place(cut_gem(0.1, "CrystalCyan" if k % 2 else "Diamond"), M((0.6 * math.cos(a), 0.6 * math.sin(a), 0.3 + k * 0.25), (a, k, 0)))
            fx.add("Trail", place(trail, atts["Trail"]))
    elif u == 2:  # warning lamps (glowing gems from Frost-tech on)
        for key in ("Lamp1", "Lamp2"):
            if key in atts:
                b.add("Lamp" + key[-1], place(tier_lamp(t), atts[key]))
    elif u == 3:  # gears and steam (magic sparkles from Enchanted on)
        for key in ("Gear1", "Gear2"):
            if key in atts:
                gear_pieces = spoked_gear(0.7, 9, 0.22, 0.12, 4, *(("Pine", "Iron") if t == 1 else ("Brass", "Copper") if t == 2 else ("SteelLight", "AuroraCyan") if t == 3 else ("Moonstone", "Gold")))
                b.add("Gear" + key[-1], place(gear_pieces, atts[key] @ M((0, 0, 0.12))))
        for key in ("Steam1", "Steam2"):
            if key in atts:
                fx.add("Steam" + key[-1], place(tier_puff(t), atts[key]))
    elif u == 4:
        fx.add("Hit", place(hit_standin(t), atts["Hit"]))


def AURA(atts, fx):
    """Mecha Mole Titan: steam venting from its back, sparks from its claws, cyan energy rings round the drill."""
    for key in ("Steam1", "Steam2"):
        fx.add("AuraSteam", place(tier_puff(2, 0.5), atts[key] @ M((0, 0, 0.4))))
    for k in range(3):
        ring = bmesh.new()
        torus(ring, atts["Work"] @ M((0, 0, 0.6 + k * 0.9)), 1.5 - k * 0.3, 0.05, 24, 4)
        fx.add("AuraRings", [(ring, "AuroraCyan", 0.0, True)])
    for sx in (-1, 1):
        for k in range(4):
            s = bmesh.new()
            cylinder(s, (sx * (3.4 + 0.3 * k), -2.2 + 0.2 * k, 3.6 + 0.4 * k), 0.04, 0.5, 4, direction=(sx, -0.4, 1), top=0.0)
            fx.add("AuraSparks", [(s, "LampYellow", 0.0, True)])
    ring = bmesh.new()
    torus(ring, M((0, 0, 0.98)), 4.4, 0.06, 32, 4)
    fx.add("AuraGround", [(ring, "AuroraCyan", 0.0, True)])
