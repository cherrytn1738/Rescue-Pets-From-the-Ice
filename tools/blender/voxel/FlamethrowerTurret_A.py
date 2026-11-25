# FlamethrowerTurret_A.py (voxel STYLE TEST, style A) - the Dragon Turret (Legendary) hand-built on the 0.5-stud
# voxel grid in the pets' style, following the approved design (tools/blender/buildings/FlamethrowerTurret.py,
# tier_dragon and PEDESTAL): the same drum, tanks and dragon, grown x1.88 and lifted onto its stacked drum
# tower (11.7 studs), the 12-stud pad, the attachment points (Work at the nozzle, Eyes, Crown).
import math
import numpy as np

SCALE, CENTRE, LIFT = 1.8802, np.array((0.0, -0.058, 1.408)), 11.708
STATUE = 1.15          # the dragon is 15% bigger than modelled, grown from the drum top (0, 0.6, 4.0)
HEAD_PITCH, JAW_OPEN = 0.5, 0.72


def G(p):
    """Design point (drum, tanks) -> where it stands now."""
    return CENTRE + SCALE * (np.array(p, float) - CENTRE) + (0, 0, LIFT)


def F(p):
    """Design point of the dragon itself -> where it stands now."""
    s = np.array((0, 0.6, 4.0)) + STATUE * (np.array(p, float) - np.array((0, 0.6, 4.0)))
    return G(s)


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array(((1, 0, 0), (0, c, -s), (0, s, c)))


HEAD_R = rot_x(HEAD_PITCH)
HEAD_T = np.array((0, -0.35, 8.85))
JAW_R = HEAD_R @ rot_x(JAW_OPEN)


def H(p):
    """A point in the head's own frame (front -Y) -> design."""
    return HEAD_T + HEAD_R @ np.array(p, float)


def J(p):
    """A point in the lower jaw's frame -> design."""
    return HEAD_T + HEAD_R @ (np.array((0, 0.15, -0.3)) + rot_x(JAW_OPEN) @ (np.array((0, -1.45, 0)) + np.array(p, float)))


def a_dragon(g):
    rs, rd = SCALE, SCALE * STATUE  # radii: the drum and tanks grow by rs, the dragon by rd
    # the plinth (the base keeps its pad size)
    g.put(g.cbox((0, 0, 0.45), (11.4, 11.4, 0.9)), "Gunmetal")
    g.put(g.cbox((0, 0, 0.75), (11.6, 11.6, 0.3)), "Gold")
    g.put(g.cbox((0, 0, 1.15), (10.8, 10.8, 0.5)), "StoneLight")
    g.put(g.cbox((0, -5.75, 0.4), (4.8, 0.3, 0.3)), "AuroraCyan", True)
    for sx in (-1, 1):
        g.put(g.cbox((sx * 3.6, -5.75, 0.45), (1.8, 0.4, 0.5)), "SteelDark")
        for sy in (-1, 1):
            g.put(g.cbox((sx * 5.1, sy * 5.1, 1.6), (0.5, 0.5, 0.5)), "AuroraCyan", True)
    # the tower: three stacked gunmetal drums with gold joints, a crest, a glowing strip, a flared collar
    foot = G((0, 0.6, 1.2))
    deck_top = foot[2] + 0.12
    deck_bottom = deck_top - 1.1
    cx, cy = foot[0], min(foot[1], 5.7 - 3.9)
    R = 3.2
    zs = [1.35 + (deck_bottom - 2.2 - 1.35) * k / 3 for k in range(4)]
    for k in range(3):
        r = R * (1.12 - 0.05 * k) + 0.15
        g.put(g.zcyl(cx, cy, r, zs[k], zs[k + 1]), "Gunmetal" if k != 1 else "SteelDark")
        if k < 2:
            g.put(g.zcyl(cx, cy, r + 0.4, zs[k + 1] - 0.5, zs[k + 1]), "Gold")
    g.put(g.lathe(cx, cy, [(R + 0.1, deck_bottom - 2.2), (R + 0.6, deck_bottom - 1.7), (R + 2.4, deck_bottom + 0.1)]), "Gunmetal")
    g.put(g.zcyl(cx, cy, R + 0.95, deck_bottom - 1.75, deck_bottom - 1.25), "Gold")
    tc = (cx, cy - R * 1.02 - 0.4, (zs[2] + zs[3]) / 2)
    for i, w in enumerate((2.6, 2.6, 2.2, 1.6, 0.8)):  # the crest on the tower
        g.put(g.cbox((tc[0], tc[1], tc[2] + 1.0 - i * 0.5), (w, 0.6, 0.5)), "Gold")
        g.put(g.cbox((tc[0], tc[1] - 0.2, tc[2] + 1.0 - i * 0.5), (max(w - 1.0, 0.5), 0.6, 0.5)), "NavyIce")
    g.put(g.cbox((tc[0], tc[1] - 0.4, tc[2] + 0.4), (0.6, 0.5, 0.6)), "FlameOrange", True)
    g.put(g.cbox((cx, cy - R * 1.12 - 0.35, zs[0] + 0.7), (2.4, 0.4, 0.5)), "FlameOrange", True)
    # the deck: a round plate under the drum and a plate under each fuel tank
    dc = G((0, 0.6, 1.2))
    deck = g.zcyl(dc[0], dc[1], 4.0 * rs + 0.4, deck_bottom, deck_top)
    for sx in (-1, 1):
        t = G((sx * 4.2, 4.0, 1.2))
        deck |= g.zcyl(t[0], t[1], 0.9 * rs + 0.6, deck_bottom, deck_top)
        deck |= g.box(min(t[0], dc[0]), max(t[0], dc[0]), t[1] - 1.5, t[1] + 1.5, deck_bottom, deck_top)
    g.put(deck, "Gunmetal")
    g.paint(deck & (g.Z >= deck_bottom + 0.3) & (g.Z < deck_bottom + 0.8) & g.surface(deck), "Gold")
    # the turret drum: armour, a gold gear ring on top, rivets, a crest at the front
    prof = [(4.0, 1.2), (4.0, 1.5), (3.8, 1.62), (3.8, 3.6), (3.6, 3.9), (3.3, 4.0)]
    drum = g.put(g.lathe(dc[0], dc[1], [(r * rs, G((0, 0, z))[2]) for r, z in prof]), "Gunmetal")
    skin = g.surface(drum)
    g.paint(skin & (np.abs(g.Z - G((0, 0, 1.75))[2]) < 0.3), "Gold")
    top = G((0, 0.6, 3.62))
    gear = g.zcyl(top[0], top[1], 3.95 * rs + 0.4, top[2] - 0.3, top[2] + 0.5) & ~g.zcyl(top[0], top[1], 3.3 * rs, top[2] - 0.4, top[2] + 0.6)
    teeth = np.sin(np.arctan2(g.Y - top[1], g.X - top[0]) * 20) > 0
    g.put(gear & (teeth | (g.Z < top[2] + 0.2)), "Gold")
    g.put(gear & ~teeth & (g.Z >= top[2] + 0.2), "Brass")
    for deg in (30, 150, 210, 330):  # steel armour plates
        a = math.radians(deg)
        n = np.array((math.cos(a), math.sin(a), 0))
        c = G((3.8 * n[0], 0.6 + 3.8 * n[1], 2.6))
        g.put(g.obox(c, (1.7 * rs, 0.7, 1.5 * rs), (-n[1], n[0], 0), (0, 0, 1)), "SteelLight")
    cc = G((0, 0.6 - 3.83, 2.65))
    for i, w in enumerate((2.6, 2.6, 2.4, 2.0, 1.4, 0.8)):
        g.put(g.cbox((cc[0], cc[1] - 0.3, cc[2] + 1.4 - i * 0.55), (w, 0.6, 0.55)), "Gold")
        g.put(g.cbox((cc[0], cc[1] - 0.5, cc[2] + 1.4 - i * 0.55), (max(w - 1.0, 0.5), 0.6, 0.55)), "NavyIce")
    g.put(g.cbox((cc[0], cc[1] - 0.7, cc[2] + 0.7), (0.6, 0.5, 1.6)), "FlameYellow")
    g.put(g.cbox((cc[0], cc[1] - 0.7, cc[2] + 0.7), (1.6, 0.5, 0.6)), "FlameOrange")
    # the fuel tanks: copper with gold bands, a gauge, a valve
    for sx in (-1, 1):
        t = G((sx * 4.2, 4.0, 0))
        tank = g.lathe(t[0], t[1], [(0.85 * rs, G((0, 0, 1.2))[2]), (0.9 * rs, G((0, 0, 1.4))[2]), (0.9 * rs, G((0, 0, 4.6))[2]), (0.55 * rs, G((0, 0, 5.1))[2]), (0.2 * rs, G((0, 0, 5.35))[2])])
        g.put(tank, "Copper")
        for z in (1.9, 3.9):
            g.paint(g.zcyl(t[0], t[1], 0.95 * rs + 0.5, G((0, 0, z))[2] - 0.3, G((0, 0, z))[2] + 0.3), "Gold")
        gp = G((sx * 4.2 - sx * 0.62, 4.0 - 0.62, 2.9))
        g.put(g.cbox(gp, (1.1, 1.1, 1.1)), "Cream")
        g.put(g.ring(gp, (-sx, -1, 0), 0.65, 0.3), "Gold")
        g.put(g.cyl(G((sx * 4.2, 4.0, 4.0)), G((sx * 5.3, 4.0, 4.0)), 0.5), "WarnRed")
    # the dragon: body, belly plates, neck with cream throat and gold spikes, forelegs on the rim, a tail
    body = g.put(g.ellipsoid(F((0, 1.3, 5.15)), (1.5 * rd, 1.5 * rd, 1.35 * rd)), "WarnRedDark")
    for k, z in enumerate((4.45, 4.95, 5.45, 5.95)):
        c = F((0, -0.1, z))
        g.paint(g.cbox(c, ((1.9 - 0.16 * abs(k - 1.5)) * rd * 0.5, 1.4, 0.4 * rd)) & g.surface(body), "Cream")
    neck_pts = [F(p) for p in ((0, 1.15, 5.5), (0, 1.15, 6.7), (0, 0.85, 7.8), H((0, 0.35, 0.15)) + (0, 0.5, -0.3), H((0, 0.35, 0.15)))]
    neck = g.put(g.tube(neck_pts, 0.98 * rd, 0.7 * rd), "WarnRedDark")
    g.paint(neck & (g.Y < np.interp(g.Z, [p[2] for p in neck_pts], [p[1] for p in neck_pts]) - 0.55 * rd), "Cream")
    for i in range(1, 4):  # gold spikes down the back of the neck
        a, b = np.array(neck_pts[i - 1]), np.array(neck_pts[i])
        m = (a + b) / 2 + (0, 0.95 * rd * 0.9, 0)
        g.put(g.cyl(m, m + (0, 0.9, 0.5), 0.5, 0.1, caps=True), "Gold")
    for sx in (-1, 1):
        sh, el, wr = F((sx * 1.15, 0.5, 5.55)), F((sx * 1.85, -0.45, 5.2)), F((sx * 1.55, -1.55, 4.38))
        g.put(g.tube([sh, el, wr], 0.5 * rd, 0.34 * rd), "WarnRedDark")
        g.put(g.sphere(el + (sx * 0.3, 0, 0), 0.42 * rd), "Gunmetal")
        paw = np.array(F((sx * 1.55, -1.85, 4.26)))
        g.put(g.ellipsoid(paw, (0.42 * rd, 0.5 * rd, 0.3 * rd)), "WarnRedDark")
        for k in (-1, 0, 1):
            cb = paw + (k * 0.26 * rd, -0.5 * rd, -0.1)
            g.put(g.cyl(cb, cb + (0, -0.6, -0.9), 0.4, 0.1, caps=True), "Cream")
    tail = [F(p) for p in ((0, 2.4, 4.6), (0.85, 2.85, 4.42), (1.8, 2.85, 4.25), (2.55, 2.0, 4.18), (2.75, 0.9, 4.15))]
    g.put(g.tube(tail, 0.55 * rd, 0.18 * rd), "WarnRedDark")
    sp = np.array(tail[-1])
    g.put(g.obox(sp + (0, -0.6, 0.1), (1.2, 1.4, 0.5), (1, 0, 0), (0, 1, 0)) & (np.abs(g.X - sp[0]) + np.abs(g.Y - sp[1] + 0.6) < 1.0), "Gold")
    for sx in (-1, 1):  # hoses from the tanks into the dragon's back
        g.put(g.tube([G((sx * 3.5, 3.5, 4.3)), F((sx * 1.3, 2.6, 5.3)), F((sx * 0.7, 2.3, 5.4))], 0.45), "Rubber")
    # the head: a round skull bent toward the ice, a snout, the open lower jaw, teeth, horns, frills, crown
    ax, ay = HEAD_R @ (1, 0, 0), HEAD_R @ (0, 1, 0)
    skull = g.oellipsoid(F(H((0, -0.75, 0.45))), (1.3 * rd, 1.4 * rd, 1.0 * rd), ax, ay)
    snout = g.oellipsoid(F(H((0, -2.4, 0.25))), (0.88 * rd, 1.25 * rd, 0.55 * rd), ax, ay)
    g.put(skull | snout, "WarnRedDark")
    jx, jy = JAW_R @ (1, 0, 0), JAW_R @ (0, 1, 0)
    g.put(g.oellipsoid(F(J((0, 0, 0))), (0.92 * rd, 1.5 * rd, 0.3 * rd), jx, jy), "WarnRedDark")
    g.put(g.oellipsoid(F(J((0, -0.25, 0.25))), (0.55 * rd, 1.05 * rd, 0.2 * rd), jx, jy), "Blush")
    g.put(g.oellipsoid(F(H((0, -1.0, -0.4))), (0.75 * rd, 1.1 * rd, 0.5 * rd), ax, ay) & ~(skull | snout), "Rubber")
    for y in (-2.75, -2.25, -1.75):  # teeth: upper fangs and lower teeth
        for sx in (-1, 1):
            p = F(H((sx * 0.6, y, -0.15)))
            g.put(g.cyl(p, np.array(p) - HEAD_R @ (0, 0, 1) * (0.9 if y < -2.5 else 0.6), 0.4, 0.1, caps=True), "EyeWhite")
    for y in (-1.15, -0.5):
        for sx in (-1, 1):
            p = F(J((sx * 0.55, y, 0.2)))
            g.put(g.cyl(p, np.array(p) + JAW_R @ (0, 0, 1) * 0.6, 0.35, 0.1, caps=True), "EyeWhite")
    for sx in (-1, 1):  # big horns sweeping back, side horns, cheek frills
        root = H((sx * 0.55, 0.05, 1.05))
        g.put(g.tube([F(root), F(root + HEAD_R @ (sx * 0.15, 0.45, 0.45)), F(root + HEAD_R @ (sx * 0.35, 1.05, 0.75)), F(root + HEAD_R @ (sx * 0.45, 1.65, 0.8))], 0.26 * rd, 0.06 * rd), "Cream")
        g.paint(g.sphere(F(root + HEAD_R @ (sx * 0.05, 0.12, 0.15)), 0.3 * rd), "Gold")
        sr = H((sx * 1.05, 0.0, 0.3))
        g.put(g.tube([F(sr), F(sr + HEAD_R @ (sx * 0.35, 0.4, 0.05)), F(sr + HEAD_R @ (sx * 0.55, 0.95, 0.2))], 0.18 * rd, 0.05 * rd), "Cream")
        for k in range(3):
            c = F(H((sx * 1.1, 0.2, -0.1 - 0.12 * k)))
            g.put(g.cyl(c, np.array(c) + HEAD_R @ np.array((sx * 0.7, 1, -0.3 - 0.35 * k)) * 0.6, 0.4, 0.1, caps=True), "Amber")
    crown_c = np.array(F(H((0, -0.55, 1.45))))
    g.put(g.oellipsoid(crown_c, (0.62 * rd, 0.62 * rd, 0.18 * rd), ax, ay) & ~g.oellipsoid(crown_c, (0.42 * rd, 0.42 * rd, 0.4 * rd), ax, ay), "Gold")
    for k in range(5):
        a = 2 * math.pi * k / 5 - math.pi / 2
        base = crown_c + (HEAD_R @ (0.55 * math.cos(a), 0.55 * math.sin(a), 0)) * rd
        g.put(g.cyl(base, base + HEAD_R @ (0, 0, 1) * (1.1 if k == 0 else 0.8), 0.35, 0.1, caps=True), "Gold")
        g.put(g.sphere(base + HEAD_R @ (0, 0, 1) * 0.3, 0.3), "MagicPink" if k == 0 else "AuroraCyan", True)
    # the eyes: glowing amber discs with slit pupils in gunmetal rims, looking at the ice
    for sx in (-1, 1):
        out = unit(HEAD_R @ (sx * 0.5, -1, 0.3))
        c = np.array(F(H((sx * 0.72, -1.45, 0.95))))
        g.put(g.disc(c, out, 0.36 * rd * 1.25 + 0.4, 0.9), "Gunmetal")
        g.put(g.disc(c + out * 0.35, out, 0.36 * rd * 1.25, 0.6), "LampYellow", True)
        up = unit(HEAD_R @ (0, 0, 1))
        g.put(g.obox(c + out * 0.55, (0.5, 0.5, 0.36 * rd * 1.6), np.cross(up, out), up), "EyeDark")
        g.put(g.cbox(c + out * 0.6 + up * 0.5 - np.cross(up, out) * 0.5 * sx, (0.5, 0.5, 0.5)), "EyeWhite")
        brow = c + up * 0.9 + out * 0.2
        g.put(g.obox(brow, (0.95 * rd, 0.6, 0.55), np.cross(up, out), up), "Gunmetal")
    # the nozzle in the throat and the flame
    md = HEAD_R @ np.array((0, -math.cos(JAW_OPEN / 2), -math.sin(JAW_OPEN / 2)))
    n0 = np.array(F(H((0, -0.55, -0.4))))
    n1 = n0 + md * 2.55 * rd
    g.put(g.cyl(n0, n1, 0.44 * rd), "Gunmetal")
    for f in (0.25, 0.5):
        g.paint(g.cyl(n0 + md * 2.55 * rd * f, n0 + md * (2.55 * rd * f + 0.5), 0.5 * rd), "Gold")
    g.put(g.cyl(n1, n1 + md * 0.5, 0.62 * rd), "Gold")
    g.put(g.cyl(n1 + md * 0.2, n1 + md * 0.55, 0.4 * rd), "FlameYellow", True)
    flame = g.cyl(n1 + md * 0.5, n1 + md * 4.2, 1.1, 0.2, caps=True)
    g.put(flame, "FlameOrange", True)
    g.put(flame & g.cyl(n1 + md * 0.5, n1 + md * 3.2, 0.7, 0.1, caps=True), "FlameYellow", True)


def unit(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


A_TIERS = {5: a_dragon}
