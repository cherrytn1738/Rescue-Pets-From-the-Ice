# IceDrill_A.py (voxel STYLE TEST, style A) - the Ice Drill's five tiers hand-built on the 0.5-stud voxel grid in
# the pets' style (bold stepped shapes, tone bands, studs, cartoon eyes), following the approved designs:
# their shapes are placed in each tier's design coordinates (tools/blender/buildings/IceDrill.py) and grown
# like the approved model (Design), so heights, the 10-stud pad and the attachment points all match.
# Loaded by run_voxel.py after IceDrill.py (drill_bit, NOSE, TITAN_WORK) and voxels.py.
import math
import numpy as np


class Design:
    """Places shapes given in a tier's design coordinates (the approved model's numbers) where the grown model
    has them: p -> centre + scale * (p + shift - centre) (framework.grow_tier: everything above the base grows
    about the base's top centre)."""

    def __init__(self, scale, centre, shift=(0.0, 0.0, 0.0)):
        self.s, self.c, self.shift = scale, np.array(centre, float), np.array(shift, float)

    def p(self, p):
        return tuple(self.c + self.s * (np.array(p, float) + self.shift - self.c))

    def r(self, r):
        return r * self.s


def tone_tops(g, pairs):
    """Pet shading: the skin voxels of a colour that face up (nothing above) take its light tone."""
    skin = exposed(g)
    above = np.roll(g.col > 0, -1, 2)
    for base, light in pairs.items():
        if base in g.names:
            g.paint(skin & ~above & (g.col == g.cid(base)), light)


def unit(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


def a_titan(g):
    D = Design(2.179, (0.0, -0.058, 1.678), (0.0, 1.1, 0.0))
    P, R = D.p, D.r
    # the plinth (the base keeps its pad size: real studs)
    g.put(g.cbox((0, 0, 0.45), (9.5, 9.5, 0.9)), "Gunmetal")
    g.put(g.cbox((0, 0, 0.75), (9.9, 9.9, 0.3)), "Gold")
    g.put(g.cbox((0, 0, 1.2), (9.0, 9.0, 0.6)), "StoneLight")
    for sx in (-1, 1):
        g.put(g.cbox((sx * 3.2, -4.9, 0.45), (1.6, 0.6, 0.5)), "SteelDark")
        g.put(g.cbox((sx * 4.2, -4.3, 1.75), (0.5, 0.5, 0.5)), "AuroraCyan", True)
    g.put(g.cbox((0, -4.95, 0.3), (4.5, 0.4, 0.3)), "AuroraGreen", True)
    g.put(g.ring((0, -3.4, 1.5), (0, 0, 1), 1.6, 0.5), "StoneDark")
    for k, (x, y) in enumerate(((-1.6, -3.8), (1.4, -2.9), (0.3, -4.4))):
        g.put(g.cyl((x, y, 1.4), (x + 0.2 * (k - 1), y - 0.2, 2.6), 0.5, 0.1, caps=True), "IceBlue")
    # legs and feet
    for sx in (-1, 1):
        lx, ly = P((sx * 1.5, 0.7, 0))[:2]
        g.put(g.zcyl(lx, ly, R(0.75), 1.7, P((0, 0, 3.0))[2]), "Gunmetal")
        g.put(g.ellipsoid(P((sx * 1.5, 0.0, 2.3)), (R(0.55), R(0.35), R(0.5))), "SteelLight")
        fx, fy = P((sx * 1.6, 0.2, 1.5))[:2]
        g.put(g.cbox((fx, fy, 2.3), (R(1.8), R(2.5), 1.4)), "SteelDark")
        toe_y = P((0, -1.0, 0))[1]
        for k in (-1, 0, 1):
            x = P((sx * 1.6 + k * 0.5, 0, 0))[0]
            g.put(g.cyl((x, toe_y, 2.1), (x, toe_y - 1.2, 1.7), 0.45, 0.15, caps=True), "Gold")
    # the body: a round fur barrel, gold bands, a glowing aurora band, the belly plate with a gold rim
    cx, cy = P((0, 0, 0))[:2]
    prof = [(0.1, 2.5), (2.3, 2.6), (3.1, 3.8), (3.3, 5.2), (3.0, 6.8), (2.2, 7.9), (0.1, 8.3)]
    body = g.put(g.lathe(cx, cy, [(R(r), P((0, 0, z))[2]) for r, z in prof]), "MoleFur")
    skin = g.surface(body)
    for z in (2.85, 7.35):  # gold bands painted flush round the body
        g.paint(skin & (np.abs(g.Z - P((0, 0, z))[2]) < 0.5), "Gold")
    g.paint(skin & (np.abs(g.Z - P((0, 0, 5.6))[2]) < 0.5), "AuroraGreen", True)
    bc = P((0, -2.9, 4.9))
    belly = g.put(g.disc(bc, (0, 1, 0), R(1.95), 1.0) & (g.Y < cy), "MoleFurLight")
    rim = belly & (np.hypot(g.X - bc[0], g.Z - bc[2]) > R(1.95) - 0.55)
    g.paint(rim, "Gold")
    # the crest: a gold-rimmed shield with a snowflake, on the chest
    sc = P((0, -3.3, 6.45))
    for i, w in enumerate((3.2, 3.2, 3.0, 2.6, 2.0, 1.2)):
        z = sc[2] + 1.6 - i * 0.6
        g.put(g.cbox((sc[0], sc[1], z), (w, 0.8, 0.6)), "Gold")
        g.put(g.cbox((sc[0], sc[1] - 0.25, z), (max(w - 1.0, 0.5), 0.6, 0.6)), "DeepIce")
    g.put(g.cbox((sc[0], sc[1] - 0.5, sc[2] + 0.4), (0.5, 0.4, 2.0)), "SnowWhite")
    g.put(g.cbox((sc[0], sc[1] - 0.5, sc[2] + 0.4), (2.0, 0.4, 0.5)), "SnowWhite")
    # shoulders: steel pauldrons with a gunmetal rim
    for sx in (-1, 1):
        pc = P((sx * 2.8, -0.4, 7.5))
        g.put(g.ellipsoid(pc, (R(1.45), R(1.45), R(0.85))) & (g.Z > pc[2] - R(0.4)), "SteelLight")
        g.put(g.ring((pc[0], pc[1], pc[2] - R(0.3)), (0, 0, 1), R(1.45), 0.5), "Gunmetal")
    # the back: a backpack, twin stacks, exhausts
    g.put(g.cbox(P((0, 2.75, 4.6)), (R(3.0), R(1.4), R(2.4))), "Gunmetal")
    g.put(g.cbox(P((0, 2.75, 5.85)), (R(3.1), R(1.5), 0.5)), "Gold")
    for sx in (-1, 1):
        b0 = np.array(P((sx * 1.2, 2.6, 6.6)))
        b1 = np.array(P((sx * 1.2, 2.6 + 0.72, 6.6 + 2.3)))
        g.put(g.cyl(b0, b1, R(0.42)), "Gunmetal")
        g.put(g.cyl(b1, b1 + (0, 0.2, 0.6), R(0.5)), "Gold")
        g.put(g.tube([P((sx * 1.55, 3.2, 4.2)), P((sx * 2.1, 3.35, 5.0)), P((sx * 2.35, 3.35, 7.6)), P((sx * 2.45, 3.2, 8.9))], R(0.24)), "Steel")
    # arms: shoulder housing, steel upper arm, elbow ball and gear, gunmetal gauntlet, paw, steel claws
    for sx, elbow, hand in ((-1, (-3.85, -1.7, 5.1), (-2.9, -3.0, 3.4)), (1, (3.9, -1.3, 7.6), (4.0, -1.9, 9.4))):
        sh = np.array(P((sx * 3.15, -0.4, 6.3)))
        el, ha = np.array(P(elbow)), np.array(P(hand))
        g.put(g.cyl(sh - (sx * R(0.3), 0, 0), sh + (sx * R(0.7), 0, 0), R(1.1)), "Gunmetal")
        g.put(g.cyl(sh + (sx * R(0.7), 0, 0), sh + (sx * R(0.8), 0, 0), R(0.85)), "Gold")
        g.put(g.cyl(sh, el, R(0.72), caps=True), "SteelDark")
        g.put(g.sphere(el, R(0.82)), "Gunmetal")
        g.put(g.disc(el + (sx * R(0.7), 0, 0), (1, 0, 0), R(0.55), 0.6), "Gold")
        d = unit(ha - el)
        mid = el + (ha - el) * 0.55
        side = np.cross(d, (0, 0, 1))
        side = side / np.linalg.norm(side) if np.linalg.norm(side) > 1e-3 else np.array((1.0, 0, 0))
        g.put(g.obox(mid, (R(1.6), R(1.5), float(np.linalg.norm(ha - el)) * 0.75), side, np.cross(d, side)), "Gunmetal")
        g.put(g.cyl(mid - d * 0.4, mid + d * 0.4, R(0.95)), "SteelLight")
        paw = ha + d * R(0.35)
        g.put(g.ellipsoid(paw, (R(0.8), R(0.8), R(0.8))), "MoleFurLight")
        for k in (-1, 0, 1):
            base = paw + d * R(0.55) + side * k * R(0.45)
            g.put(g.cyl(base, base + d * R(1.1) + (0, 0, -0.3), 0.55, 0.15, caps=True), "SteelLight")
    # the head: a round fur head with a pushed-out muzzle, a steel helmet and gunmetal band, a gold crown
    hc = P((0, -1.0, 10.2))
    head = g.ellipsoid(hc, (R(2.85), R(2.55), R(2.45)))
    head |= g.ellipsoid(P((0, -2.55, 9.55)), (R(1.9), R(1.2), R(1.45)))
    g.put(head, "MoleFur")
    band = P((0, 0, 12.05))[2]
    g.paint(head & (g.Z > band + 0.5), "Steel")
    g.paint(g.surface(head) & (np.abs(g.Z - band) < 0.5), "Gunmetal")  # the headband, flush
    top = float(g.Z[head].max())
    for k in range(5):
        a = k * 2 * math.pi / 5 - math.pi / 2
        x, y = 1.2 * math.cos(a), hc[1] + 0.3 + 1.2 * math.sin(a)
        g.put(g.box(x - 0.25, x + 0.25, y - 0.25, y + 0.25, top - 0.5, top + (1.6 if k == 0 else 1.1)), "Gold")
    g.put(g.zcyl(0, hc[1] + 0.3, 1.5, top - 0.25, top + 0.5) & ~g.zcyl(0, hc[1] + 0.3, 0.9, top - 0.25, top + 0.5), "Gold")
    for sx in (-1, 1):  # ears, pink inside
        ec = np.array(P((sx * 2.55, -0.7, 11.5)))
        out = unit((sx, -0.1, 0.45))
        g.put(g.cyl(ec, ec + out * R(0.45), R(0.78)), "MoleFurLight")
        g.put(g.cyl(ec + out * R(0.4), ec + out * R(0.55), R(0.48)), "Blush")
    # the face: goggle rims, big cyan eyes, stepped brows, blush, buck teeth, whiskers
    ez = P((0, 0, 10.9))[2]
    for sx in (-1, 1):
        x = sx * 2.14
        g.put(g.ring((x, g.front_y(x, ez) + 0.1, ez), (0, 1, 0), R(0.92), 0.5), "Gunmetal")
        g.eye(x, ez, R(0.74), iris="CrystalCyan", look=(0.0, 0.4), glow_iris=True)
        bz = P((0, 0, 11.9))[2]
        for i in range(4):  # a stepped brow, lower at the inside: determined
            bx = x + sx * (i - 1.5) * 0.5
            fy = g.front_y(bx, bz)
            g.put(g.cbox((bx, (fy if fy is not None else hc[1] - R(2.4)) - 0.3, bz + (i - 1.5) * 0.2), (0.6, 0.8, 0.6)), "Gunmetal")
        cz = P((0, 0, 9.65))[2]
        fy = g.front_y(sx * R(1.9), cz)
        if fy is not None:
            g.put(g.ellipsoid((sx * R(1.9), fy + 0.1, cz), (R(0.45), 0.6, R(0.3))), "Blush")
        for k in range(2):  # whiskers: thin steel lines out to the side
            wz = P((0, 0, 9.3 - 0.2 * k))[2]
            wy = g.front_y(sx * R(1.0), wz)
            g.put(g.cyl((sx * R(1.0), (wy if wy is not None else hc[1]) - 0.1, wz), (sx * R(2.6), hc[1] - R(1.6), wz + 0.4 - 0.6 * k), 0.26), "SteelLight")
    tz = P((0, 0, 8.35))[2]
    for sx in (-1, 1):
        ty = g.front_y(sx * 0.45, tz)
        g.put(g.cbox((sx * 0.45, (ty if ty is not None else hc[1]) - 0.2, tz), (0.8, 0.6, 1.0)), "EyeWhite")
    # the snout housing and the drill (the bit's mount is the Work attachment)
    w = np.array(TITAN_WORK)
    g.put(g.cyl(w - NOSE * R(1.15), w - NOSE * R(0.05), R(1.3)), "Gunmetal")
    g.put(g.ring(w - NOSE * R(0.25), NOSE, R(1.25), 0.5), "Gold")
    drill_bit(g, w, NOSE, 5.2, R(0.95))


def planks(g, x0, x1, y0, y1, z0, z1, tones=("Pine", "PineLight", "PineDark"), along="x", width=1.0):
    """A plank floor: boards along `along`, alternating tones."""
    m = g.box(x0, x1, y0, y1, z0, z1)
    across = g.Y if along == "x" else g.X
    start = y0 if along == "x" else x0
    k = np.floor((across - start) / width).astype(int)
    for i, tone in enumerate(tones):
        g.put(m & (k % len(tones) == i), tone)


def a_scrappy(g):
    D = Design(1.3442, (-0.05, 0.25, 0.32))
    P, R = D.p, D.r
    planks(g, -2.5, 2.5, -1.75, 1.75, 0, 0.5, ("PineDark", "Pine", "PineLight"))
    apex = np.array(P((0.15, 0.05, 4.6)))
    feet = [(P((-1.9, -1.4, 0.2)), "PineDark", R(0.24)), (P((1.8, -1.1, 0.2)), "Rust", R(0.17)), (P((0.1, 1.9, 0.2)), "PineLight", R(0.21))]
    for foot, tone, r in feet:  # the A-frame: two beams and a rusty pipe, on stone feet
        g.put(g.cyl(foot, apex + (0, 0, R(0.5)), max(r, 0.45), caps=True), tone)
        g.put(g.cbox((foot[0], foot[1], 0.55), (1.2, 1.0, 0.6)), "StoneDark")
    g.put(g.cbox(apex + (0, 0, R(0.25)), (1.4, 1.4, 1.0)), "PineLight")  # the rope lashing
    g.paint(g.cbox(apex + (0, 0, R(0.25)), (1.6, 1.6, 0.5)), "PineDark")
    hub = np.array(P((0.65, 0.05, 4.25)))  # the crank: an old cart wheel with a wooden grip
    wheel = g.disc(hub, (1, 0, 0), R(0.75), 0.6)
    g.put(wheel & ~g.disc(hub, (1, 0, 0), R(0.55), 0.6), "Rust")
    g.put(wheel & ((np.abs(g.Z - hub[2]) < 0.3) | (np.abs(g.Y - hub[1]) < 0.3)), "RustDark")
    g.put(g.cyl(hub + (0.4, 0, 0), hub + (0.6, 0, R(0.55)), 0.3), "Iron")
    g.put(g.cyl(hub + (0.6, 0, R(0.55)), hub + (1.2, 0, R(0.55)), 0.3), "PineLight")
    top = P((0.15, 0.05, 1.4))
    g.put(g.zcyl(apex[0], apex[1], 0.35, top[2], apex[2]), "Iron")  # the shaft and the auger
    drill_bit(g, top, (0, 0, -1), top[2] - 0.55, 0.75, bands=2, body=("Iron", "SteelDark"), band="RustDark", tip="SteelLight")
    bx, by = P((2.3, 0.9, 0))[:2]  # the barrel, with iron hoops and a lid
    g.put(g.lathe(bx, by, [(0.75, 0.5), (0.85, 1.0), (0.85, 1.7), (0.75, 2.2)]), "Rust")
    for z in (0.9, 1.8):
        g.paint(g.zcyl(bx, by, 1.0, z, z + 0.5), "Iron")
    g.put(g.zcyl(bx, by, 0.7, 2.2, 2.45), "PineDark")
    kx, ky = P((-2.1, 0.7, 0))[:2]  # the bucket and the oil can
    g.put(g.lathe(kx, ky, [(0.45, 0.5), (0.65, 1.3)]) & ~g.lathe(kx, ky, [(0.3, 0.75), (0.5, 1.4)]), "Steel")
    ox, oy = P((-0.9, -1.15, 0))[:2]
    g.put(g.zcyl(ox, oy, 0.4, 0.5, 1.25), "PatchGreen")
    g.put(g.cyl((ox, oy, 1.25), (ox + 0.6, oy - 0.3, 1.75), 0.2, caps=True), "Iron")
    g.put(g.tube([apex + (0.4, 0.2, 0.1), ((apex[0] + bx) / 2 + 0.2, by * 0.5, 3.4), (bx - 0.3, by, 2.4)], 0.25), "PineLight")


def a_workshop(g):
    D = Design(1.1564, (0.0, 0.0, 1.13))
    P, R = D.p, D.r
    planks(g, -3.5, 3.5, -2.75, 2.75, 0, 1.0, ("Pine", "PineLight", "PineDark"))
    g.put(g.cbox((-0.7, 0.2, 1.4), (1.5, 1.2, 0.9)), "Iron")  # the firebox, a glowing grille
    g.put(g.cbox((-0.7, -0.45, 1.4), (0.9, 0.3, 0.5)), "FlameOrange", True)
    for sx in (-1, 1):  # four posts with brass feet
        for sy in (-1, 1):
            x, y = P((sx * 2.4, sy * 1.9, 0))[:2]
            g.put(g.box(x - 0.5, x + 0.5, y - 0.5, y + 0.5, 1.0, P((0, 0, 6.0))[2]), "PineLight")
            g.put(g.box(x - 0.75, x + 0.75, y - 0.75, y + 0.75, 1.0, 1.5), "Brass")
    zb = P((0, 0, 5.85))[2]
    g.put(g.box(-3.3, 3.3, -2.6, 2.6, zb - 0.5, zb + 0.5) & ~g.box(-2.3, 2.3, -1.6, 1.6, zb - 0.6, zb + 0.6), "PineDark")
    for i in range(7):  # the copper gable roof, stepped, with dark seams and a brass ridge
        z = zb + 0.5 + i * 0.5
        half = 3.4 - i * 0.55
        if half <= 0.2:
            break
        step = g.box(-4.0, 4.0, -half, half, z, z + 0.5) & ~g.box(-3.8, 3.8, -half + 0.75, half - 0.75, z - 0.1, z + 0.6)
        g.put(step, "Copper")
        g.paint(step & (((g.X + 4.0) % 1.5) < 0.5), "RustDark")
    g.put(g.cyl((-4.1, 0, zb + 3.6), (4.1, 0, zb + 3.6), 0.45), "Brass")
    b0, b1 = P((-2.25, 0.9, 1.6)), P((0.85, 0.9, 1.6))  # the boiler: brass, copper bands, a dial
    g.put(g.cyl(b0, b1, R(0.85)), "Brass")
    for x in (-1.5, -0.4):
        g.paint(g.cyl(P((x, 0.9, 1.6)), P((x + 0.25, 0.9, 1.6)), R(0.95)), "Copper")
    dc = P((-1.0, 0.03, 1.8))
    g.put(g.disc((dc[0], dc[1] - 0.2, dc[2]), (0, 1, 0), 0.6, 0.5), "Cream")
    g.put(g.ring((dc[0], dc[1] - 0.2, dc[2]), (0, 1, 0), 0.65, 0.3), "Brass")
    g.put(g.cbox((dc[0] + 0.15, dc[1] - 0.5, dc[2] + 0.15), (0.5, 0.5, 0.5)), "WarnRed")
    cx_, cy_ = P((-1.4, 0.9, 0))[:2]  # the chimney
    g.put(g.zcyl(cx_, cy_, R(0.27), P((0, 0, 2.4))[2], P((0, 0, 8.4))[2]), "Brass")
    g.put(g.zcyl(cx_, cy_, R(0.42), P((0, 0, 8.4))[2], P((0, 0, 8.8))[2]), "Copper")
    g.put(g.cbox(P((1.3, -0.4, 4.85)), (R(1.3), R(1.2), R(1.1))), "Copper")  # the gearbox and boom
    g.put(g.cbox(P((1.3, -0.4, 5.45)), (R(1.45), R(1.35), 0.5)), "Brass")
    g.put(g.cyl(P((1.3, -0.4, 3.75)), P((1.3, -2.05, 2.1)), R(0.2)), "Steel")
    fw = np.array(P((-0.9, -0.55, 4.4)))  # the flywheel
    fc = fw - (0, 0.3, 0)
    g.put(g.disc(fc, (0, 1, 0), R(1.0), 0.6) & ~g.disc(fc, (0, 1, 0), R(0.7), 0.6), "Brass")
    for a in (0, 2.1, 4.2):
        g.put(g.cyl(fc, fc + (R(0.8) * math.cos(a), 0, R(0.8) * math.sin(a)), 0.3), "Copper")
    work = np.array(P((1.3, -2.15, 2.0)))  # the chuck and the drill
    bd = unit((0, -1, -0.8))
    g.put(g.cyl(work - bd * R(0.4), work, R(0.4)), "Brass")
    drill_bit(g, work, bd, 2.6, 0.8, bands=2, body=("SteelLight", "Steel"), band="Brass", tip="SteelLight")
    lc = P((2.4, -2.35, 4.2))  # the hanging lantern
    g.put(g.cbox((lc[0], lc[1], lc[2] + 0.5), (0.6, 0.6, 0.8)), "LampYellow", True)
    g.put(g.cbox((lc[0], lc[1], lc[2] + 1.05), (0.9, 0.9, 0.3)), "Brass")
    g.put(g.cbox((lc[0], lc[1], lc[2] + 0.05), (0.9, 0.9, 0.3)), "Brass")
    g.put(g.zcyl(lc[0], lc[1], 0.2, lc[2] + 1.2, zb - 0.4), "Brass")


def a_frosttech(g):
    D = Design(1.9765, (0.0, -0.1, 1.2))
    P, R = D.p, D.r
    g.put(g.cbox((0, 0, 0.4), (9.0, 7.0, 0.8)), "SnowWhite")  # the deck: white, an ice-blue top, glowing strips
    g.put(g.cbox((0, 0, 0.95), (8.0, 6.0, 0.4)), "IceBlue")
    for y in (-3.55, 3.55):
        g.put(g.cbox((0, y, 0.45), (6.0, 0.2, 0.3)), "AuroraCyan", True)
    z_lo, z_hi = P((0, 0, 3.0))[2], P((0, 0, 6.5))[2]
    for X in (-2.6, 2.6):  # the two pods: white capsules on legs, a navy visor, a screen, blue fins, a lid
        pc = np.array(P((X, 0, 4.8)))
        for sx in (-1, 1):
            g.put(g.cyl(P((X + sx * 0.85, 0, 1.1)), P((X + sx * 0.5, 0, 3.4)), R(0.15)), "SteelLight")
        g.put(g.zcyl(pc[0], pc[1], R(1.05), z_lo, z_hi), "SnowWhite")
        g.put(g.ellipsoid((pc[0], pc[1], z_lo), (R(1.05), R(1.05), R(0.5))), "SnowWhite")
        for z in (3.75, 4.75):
            g.paint(g.zcyl(pc[0], pc[1], R(1.2), P((0, 0, z))[2] - 0.25, P((0, 0, z))[2] + 0.25), "GlacierBlue")
        vz = P((0, 0, 5.3))[2]
        g.put(g.box(pc[0] - R(0.85), pc[0] + R(0.85), pc[1] - R(1.15), pc[1] - R(0.6), vz - R(0.28), vz + R(0.28)), "NavyIce")
        g.paint(g.box(pc[0] - R(0.7), pc[0] + R(0.7), pc[1] - R(1.2), pc[1] - R(1.0), vz - 0.25, vz + 0.25), "AuroraCyan", True)
        sz = P((0, 0, 4.3))[2]
        g.put(g.box(pc[0] - R(0.4), pc[0] + R(0.4), pc[1] - R(1.15), pc[1] - R(0.9), sz - R(0.23), sz + R(0.23)), "NavyIce")
        g.put(g.box(pc[0] - R(0.25), pc[0] + R(0.25), pc[1] - R(1.2), pc[1] - R(1.05), sz - 0.25, sz + 0.25), "AuroraCyan", True)
        g.put(g.zcyl(pc[0], pc[1], R(0.95), z_hi, P((0, 0, 6.85))[2]), "SteelLight")
        for sx in (-1, 1):
            fx = pc[0] + sx * R(1.05)
            g.put(g.box(fx - 0.25, fx + 0.25, pc[1] - R(0.5), pc[1] + R(0.8), P((0, 0, 3.6))[2], P((0, 0, 5.2))[2]), "GlacierBlue")
        work = np.array(P((X, -1.1, 2.25)))
        bd = unit((0, -1, -0.55))
        g.put(g.cyl(work - bd * R(0.35), work, R(0.62)), "SteelLight")
        g.paint(g.cyl(work - bd * 0.25, work, R(0.65)), "AuroraCyan", True)
        drill_bit(g, work, bd, 3.6, R(0.55), bands=3, body=("SnowWhite", "GlacierBlue"), band="DeepIce", tip="AuroraCyan", glow_tip=True)
        g.put(g.cyl(P((X - math.copysign(1.1, X), 0.2, 5.0)), P((math.copysign(0.65, X), 0.6, 5.0)), R(0.16)), "SteelLight")
    # the coil spire: a steel base, insulators, a dark core wound with an ice-blue coil, a glowing orb
    cx_, cy_ = P((0, 0.6, 0))[:2]
    g.put(g.cbox((cx_, cy_, P((0, 0, 1.5))[2]), (R(1.6), R(1.6), R(0.8))), "SteelLight")
    z0, z1 = P((0, 0, 1.9))[2], P((0, 0, 7.5))[2]
    g.put(g.zcyl(cx_, cy_, R(0.42), z0, z1), "SteelDark")
    turns = 6
    pts = [(cx_ + R(0.62) * math.cos(a), cy_ + R(0.62) * math.sin(a), z0 + (z1 - z0) * a / (2 * math.pi * turns)) for a in np.linspace(0, 2 * math.pi * turns, 120)]
    g.put(g.tube(pts, 0.4), "IceBlue")
    for z in (2.2, 2.9):
        g.put(g.zcyl(cx_, cy_, R(0.98), P((0, 0, z))[2], P((0, 0, z))[2] + 0.5), "IceBlue")
    g.put(g.sphere((cx_, cy_, z1 + R(0.5)), R(0.55)), "AuroraCyan", True)


def hexagon(g, r):
    """A hexagonal prism mask of radius r round the z axis (any height)."""
    return (np.abs(g.X) <= r) & (np.abs(g.X) * 0.5 + np.abs(g.Y) * 0.866 <= r * 0.866)


def a_enchanted(g):
    D = Design(1.5133, (0.0, 0.0, 0.923))
    P, R = D.p, D.r
    g.put(hexagon(g, 4.5) & (g.Z < 0.2), "StoneDark")  # the hex dais: moonstone, a violet trim, a glowing rune ring
    g.put(hexagon(g, 4.3) & (g.Z >= 0.2) & (g.Z < 0.85), "Moonstone")
    g.paint(hexagon(g, 4.3) & (g.Z >= 0.45) & (g.Z < 0.6) & ~hexagon(g, 4.0), "RuneViolet")
    g.put(g.ring((0, 0, 0.95), (0, 0, 1), 3.1, 0.3), "RuneGlow", True)
    for k in range(6):
        a = k * math.pi / 3
        x, y = 3.8 * math.cos(a), 3.8 * math.sin(a)
        g.put(g.cyl((x, y, 0.8), (x * 1.05, y * 1.05, 2.3), 0.45, 0.1, caps=True), "CrystalCyan" if k % 2 else "RuneViolet", True)
    # three floating islands: moonstone hexes over drill cones with gold studs spiralling down
    for top, radius, thick in ((5.2, 2.3, 0.5), (8.0, 1.8, 0.45), (10.6, 1.3, 0.4)):
        zt, rr, th = P((0, 0, top))[2], R(radius), R(thick)
        g.put(hexagon(g, rr) & (g.Z >= zt - th) & (g.Z < zt), "Moonstone")
        g.paint(hexagon(g, rr) & (g.Z >= zt - 0.5) & ~hexagon(g, rr * 0.72), "FrostLight")
        tip, top_ = zt - th - rr * 1.1, zt - th
        g.put(g.lathe(0, 0, [(0.2, tip), (rr * 0.8, top_)]), "StoneDark")
        for i in range(5):
            z = top_ - (top_ - tip) * (i + 0.5) / 5.5
            ang = i * 1.3
            r_here = rr * 0.8 * (z - tip) / (top_ - tip) + 0.2
            g.put(g.sphere((r_here * math.cos(ang), r_here * math.sin(ang), z), 0.5), "Gold")
    orbit = P((0, 0, 6.4))  # the tilted rune ring, glowing green glyphs on a deep band
    g.put(g.ring(orbit, (0.3, -0.1, 1), R(2.7), 0.45), "ArcaneDeep")
    g.paint(g.ring(orbit, (0.3, -0.1, 1), R(2.7), 0.5) & (np.sin(np.arctan2(g.Y, g.X) * 12) > 0.3), "AuroraGreen", True)
    for k in range(4):  # floating rune stones
        a = k * math.pi / 2 + 1.2
        c = P((3.0 * math.cos(a), 3.0 * math.sin(a), 4.6 + 0.5 * (k % 2)))
        g.put(g.cbox(c, (R(0.5), R(0.5), R(0.6))), "StoneDark")
        g.paint(g.cbox(c, (R(0.55), R(0.55), 0.5)), "RuneGlow", True)
    cr = P((0, 0, 10.6))  # the crown: a crystal cluster, a pink gem in a gold halo
    for dx, dy, h in ((0, 0, 2.6), (0.6, 0.2, 1.6), (-0.5, 0.4, 1.4), (0.1, -0.6, 1.5), (-0.3, -0.3, 1.2)):
        g.put(g.cyl((cr[0] + dx, cr[1] + dy, cr[2]), (cr[0] + dx * 1.4, cr[1] + dy * 1.4, cr[2] + R(h)), 0.6, 0.15, caps=True), "CrystalCyan", True)
    gc = P((0, 0, 13.0))
    g.put(g.sphere(gc, 0.7), "MagicPink", True)
    g.put(g.ring((gc[0], gc[1], gc[2] + 0.6), (0.4, -1, 0), R(0.75), 0.3), "Gold")
    work = np.array(P((0, -2.3, 3.4)))  # the violet spiral bit with a moonstone ring
    bd = unit((0, -1, -0.75))
    g.put(g.ring(work - bd * 0.3, bd, R(1.05), 0.45), "Moonstone")
    drill_bit(g, work, bd, 4.5, R(0.75), bands=3, body=("RuneViolet", "ArcaneDeep"), band="Moonstone", tip="MagicPink", glow_tip=True)


A_TIERS = {1: a_scrappy, 2: a_workshop, 3: a_frosttech, 4: a_enchanted, 5: a_titan}
