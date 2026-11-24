# building_kit_fantasy.py - fantasy pieces for the building kit (load after building_kit.py):
# spoked brass gears and brass pipes, glowing crystals and coils, gems, rune rings, floating platforms,
# cartoon eyes, brows and mouths, and gold and aurora trim. Same rules as the base kit: each piece is
# built in its own frame facing +Z, returns [(bmesh, swatch, bevel, glow)], and glow pieces go to a
# separate glow mesh.
import bmesh, math
from mathutils import Vector, Matrix


def spoked_gear(radius=1.0, teeth=12, thickness=0.3, tooth=0.2, spokes=4, swatch="Brass", hub="Copper"):
    """A brass gear with an open rim and spokes (turns about Z, centred on its axis). Att: Axle."""
    root, rim_in = radius - tooth, radius - tooth - radius * 0.2
    outline = []
    for i in range(teeth):
        for frac, r in ((0.0, root), (0.22, radius), (0.52, radius), (0.74, root)):
            a = 2 * math.pi * (i + frac) / teeth
            outline.append((r * math.cos(a), r * math.sin(a)))
    n = len(outline)
    bm = bmesh.new()
    outer = [[bm.verts.new((x, y, z)) for x, y in outline] for z in (-thickness / 2, thickness / 2)]
    inner = [[bm.verts.new((rim_in * math.cos(2 * math.pi * k / n), rim_in * math.sin(2 * math.pi * k / n), z)) for k in range(n)]
             for z in (-thickness / 2, thickness / 2)]
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((outer[0][k], outer[0][j], outer[1][j], outer[1][k]))
        bm.faces.new((inner[1][k], inner[1][j], inner[0][j], inner[0][k]))
        bm.faces.new((outer[1][k], outer[1][j], inner[1][j], inner[1][k]))
        bm.faces.new((inner[0][k], inner[0][j], outer[0][j], outer[0][k]))
    pieces = [(bm, swatch, 0.04, False)]
    for s in range(spokes):
        spoke = bmesh.new()
        rounded_block(spoke, (radius * 0.18, rim_in * 2 - 0.05, thickness * 0.8), M((0, 0, 0), (0, 0, s * math.pi / spokes)),
                      corner=0.05, edge=0.04, corner_seg=2, edge_seg=1)
        pieces.append((spoke, swatch, 0.0, False))
    h = bmesh.new()
    cylinder(h, (0, 0, -thickness * 0.75), radius * 0.26, thickness * 1.5, 12)
    pieces.append((h, hub, 0.04, False))
    return pieces


def crystal(height=1.6, radius=0.32, swatch="CrystalCyan", tilt=(0, 0), sides=6, glow=True):
    """A glowing hexagonal crystal standing on z = 0 with a pointed top. Att: Base."""
    bm = bmesh.new()
    lathe(bm, [(0, -0.1), (radius * 0.8, -0.1), (radius, height * 0.15), (radius, height * 0.72), (0, height)], sides)
    bm.transform(Matrix.Rotation(tilt[0], 4, "X") @ Matrix.Rotation(tilt[1], 4, "Y"))
    return [(bm, swatch, 0.0, glow)]


def crystal_cluster(scale=1.0, swatch="CrystalCyan", base="Stone"):
    """Three to five crystals leaning out of a rock. Att: Base."""
    pieces = []
    rock = bmesh.new()
    blob(rock, (0, 0, 0.12 * scale), (0.6 * scale, 0.5 * scale, 0.28 * scale), 1, floor=0.0)
    pieces.append((rock, base, 0.0, False))
    for h, r, tx, ty, ox, oy in ((1.5, 0.3, 0, 0, 0, 0), (1.0, 0.22, 0.45, 0.1, 0.3, 0.05),
                                 (0.9, 0.2, -0.4, 0.2, -0.28, 0.1), (0.7, 0.16, 0.1, -0.5, 0.05, -0.25)):
        c = crystal(h * scale, r * scale, swatch, (tx, ty))
        place(c, M((ox * scale, oy * scale, 0.1 * scale)))
        pieces += c
    return pieces


def coil(radius=0.5, height=2.0, turns=6, core="SteelDark", wire="Copper", top="AuroraCyan"):
    """A tesla-style coil: a core, a copper wire wound round it, and a glowing ball on top. Att: Base."""
    pieces = []
    c = bmesh.new()
    cylinder(c, (0, 0, 0), radius * 0.6, height, 12)
    pieces.append((c, core, 0.03, False))
    steps = turns * 8
    helix = [Vector((radius * 0.82 * math.cos(2 * math.pi * turns * t / steps), radius * 0.82 * math.sin(2 * math.pi * turns * t / steps),
                     0.2 + (height - 0.5) * t / steps)) for t in range(steps + 1)]
    w = bmesh.new()
    sweep(w, helix, radius * 0.16, 6)
    pieces.append((w, wire, 0.0, False))
    ring = bmesh.new()
    torus(ring, M((0, 0, height)), radius * 0.9, radius * 0.16, 16, 6)
    pieces.append((ring, core, 0.0, False))
    ball = bmesh.new()
    blob(ball, (0, 0, height + radius * 0.55), (radius * 0.55,) * 3, 2)
    pieces.append((ball, top, 0.0, True))
    return pieces


def gem(size=0.4, swatch="MagicPink", glow=True):
    """A faceted cut gem (point down, table up), centred on the origin. Att: Back."""
    bm = bmesh.new()
    lathe(bm, [(0, -size * 0.75), (size, 0), (size * 0.62, size * 0.38), (0, size * 0.42)], 8)
    return [(bm, swatch, 0.0, glow)]


def rune_ring(radius=1.6, swatch="RuneGlow", band="ArcaneDeep", glyphs=8):
    """A flat magic circle in the XY plane: a dark band with glowing rune glyphs on it. Att: Centre."""
    pieces = []
    b = bmesh.new()
    torus(b, Matrix.Diagonal((1, 1, 0.25, 1)), radius, radius * 0.08, 32, 6)
    pieces.append((b, band, 0.0, False))
    for k in range(glyphs):
        a = 2 * math.pi * k / glyphs
        g = bmesh.new()
        shape = k % 3
        size = (radius * 0.14, radius * 0.06, radius * 0.05) if shape == 0 else (radius * 0.06, radius * 0.16, radius * 0.05)
        rounded_block(g, size, M((radius * math.cos(a), radius * math.sin(a), radius * 0.03), (0, 0, a + shape * 0.7)),
                      corner=0.02, edge=0.01, corner_seg=1, edge_seg=1)
        pieces.append((g, swatch, 0.0, True))
    inner = bmesh.new()
    torus(inner, Matrix.Diagonal((1, 1, 0.2, 1)), radius * 0.84, radius * 0.03, 32, 4)
    pieces.append((inner, swatch, 0.0, True))
    return pieces


def floating_platform(radius=1.6, thickness=0.5, top="Moonstone", rock="StoneDark", trim="Gold", crystal_swatch="RuneViolet", tip=True):
    """A floating rock island: a rounded hexagonal slab with a gold rim and a crystal hanging below.
    Its top is at z = 0. Att: Top, Under."""
    pieces = []
    slab = bmesh.new()
    lathe(slab, [(0, -thickness), (radius * 0.86, -thickness), (radius, -thickness * 0.35), (radius, -0.05), (radius * 0.95, 0), (0, 0)], 6)
    pieces.append((slab, top, 0.05, False))
    under = bmesh.new()
    lathe(under, [(0, -thickness - radius * 1.1), (radius * 0.35, -thickness - radius * 0.6), (radius * 0.82, -thickness - 0.1), (0, -thickness - 0.05)], 6)
    pieces.append((under, rock, 0.03, False))
    rim = bmesh.new()
    torus(rim, M((0, 0, -thickness * 0.35)), radius * 1.0, 0.08, 6, 4)
    pieces.append((rim, trim, 0.0, False))
    if tip:
        hanging = crystal(radius * 0.7, radius * 0.16, crystal_swatch)
        place(hanging, Matrix.Translation((0, 0, -thickness - radius * 1.05)) @ Matrix.Rotation(math.pi, 4, "X"))
        pieces += hanging
    return pieces


def cartoon_eye(radius=0.5, glow_swatch=None, look=(0.12, -0.05), lid=None):
    """A big cartoon eye facing +Z: a white dome (or a glowing one), a dark pupil looking at `look`, and
    two highlight dots. lid: a swatch for a sleepy upper lid. Att: Back."""
    pieces = []
    ball = bmesh.new()
    lathe(ball, [(0, 0), (radius, 0), (radius * 0.92, radius * 0.3), (radius * 0.6, radius * 0.48), (0, radius * 0.55)], 16)
    pieces.append((ball, glow_swatch or "EyeWhite", 0.0, bool(glow_swatch)))
    px, py = look[0] * radius, look[1] * radius
    pupil = bmesh.new()
    lathe(pupil, [(0, 0), (radius * 0.42, 0), (radius * 0.36, radius * 0.1), (0, radius * 0.12)], 12, M((px, py, radius * 0.47)))
    pieces.append((pupil, "EyeDark", 0.0, False))
    for dx, dy, s in ((0.13, 0.15, 0.13), (-0.08, -0.12, 0.06)):
        shine = bmesh.new()
        blob(shine, (px + dx * radius, py + dy * radius, radius * 0.6), (s * radius, s * radius, s * radius * 0.4), 1)
        pieces.append((shine, "EyeWhite", 0.0, True))
    if lid:
        cap = bmesh.new()
        rounded_block(cap, (radius * 2.2, radius * 0.5, radius * 0.5), M((0, radius * 0.72, radius * 0.25), (0.35, 0, 0)), corner=0.15, edge=0.1, corner_seg=2, edge_seg=1)
        pieces.append((cap, lid, 0.0, False))
    return pieces


def brow(width=0.9, angle=0.25, swatch="EyeDark"):
    """A chunky eyebrow facing +Z, tilted by angle (radians; + = angry inner end down). Att: Back."""
    bm = bmesh.new()
    rounded_block(bm, (width, width * 0.24, 0.22), M((0, 0, 0.11), (0, 0, angle)), corner=0.1, edge=0.07, corner_seg=2, edge_seg=1)
    return [(bm, swatch, 0.0, False)]


def grin(width=1.4, depth=0.35, swatch="EyeDark", teeth="EyeWhite", tooth_count=4):
    """A wide toothy grin facing +Z: a curved mouth line with square teeth. Att: Back."""
    pieces = []
    points = [Vector((width / 2 * (2 * t / 10 - 1), -depth * (1 - (2 * t / 10 - 1) ** 2), 0.08)) for t in range(11)]
    m = bmesh.new()
    sweep(m, points, 0.1, 8)
    pieces.append((m, swatch, 0.0, False))
    for k in range(tooth_count):
        x = width / 2 * ((k + 0.5) / tooth_count * 1.2 - 0.6)
        y = -depth * (1 - (2 * x / width) ** 2)
        t = bmesh.new()
        rounded_block(t, (width * 0.14, 0.22, 0.12), M((x, y - 0.13, 0.08)), corner=0.04, edge=0.03, corner_seg=1, edge_seg=1)
        pieces.append((t, teeth, 0.0, False))
    return pieces


def trim_strip(p0, p1, width=0.18, swatch="Gold", glow=False):
    """A thin rounded trim strip between two points (gold trim, or glowing aurora trim)."""
    p0, p1 = Vector(p0), Vector(p1)
    bm = bmesh.new()
    rounded_block(bm, (width, width * 0.7, (p1 - p0).length), Matrix.Translation((p0 + p1) / 2) @ align_z(p1 - p0),
                  corner=width * 0.3, edge=width * 0.2, corner_seg=2, edge_seg=1)
    return [(bm, swatch, 0.0, glow)]


def trim_ring(radius, z=0.0, swatch="Gold", glow=False, minor=0.09, segments=24):
    """A trim band round a cylinder or dome (gold, or glowing aurora)."""
    bm = bmesh.new()
    torus(bm, M((0, 0, z)), radius, minor, segments, 6)
    return [(bm, swatch, 0.0, glow)]


def spiral_bit(length=2.4, radius=0.5, swatch="Brass", tip="SteelLight", turns=3.0, glow=False):
    """A drill nose / bit along +Z with a raised spiral flute (any swatch: brass, crystal, plasma).
    Built round its axis so it spins true. Att: Mount, Tip."""
    pieces = []
    body = bmesh.new()
    lathe(body, [(0, 0), (radius, 0), (radius * 0.95, length * 0.35), (radius * 0.55, length * 0.8), (0, length)], 12)
    pieces.append((body, tip, 0.0, False))  # the body stays solid so its shape reads; only the flute glows
    steps = int(turns * 14)
    helix = []
    for t in range(steps + 1):
        s = t / steps
        r = radius * (1 - 0.55 * s ** 1.4) + 0.02
        a = 2 * math.pi * turns * s
        helix.append(Vector((r * math.cos(a), r * math.sin(a), 0.05 + length * 0.85 * s)))
    f = bmesh.new()
    sweep(f, helix, radius * 0.17, 6, radius_end=radius * 0.06)
    pieces.append((f, swatch, 0.0, glow))
    return pieces


FANTASY_KIT = [
    ("SpokedGear", lambda: place(spoked_gear(0.9), frame((0, 0, 1.0), out=(0, -1, 0))), 2.1),
    ("BrassPipe", lambda: pipe(1.8, 0.22, "Brass", "Copper"), 0.9),
    ("BrassElbow", lambda: elbow(0.6, 0.22, "Brass", "Copper"), 1.4),
    ("Crystal", lambda: crystal(1.8, 0.36), 1.0),
    ("CrystalCluster", lambda: crystal_cluster(1.0, "RuneViolet"), 1.6),
    ("Coil", lambda: coil(0.45, 1.8), 1.2),
    ("Gem", lambda: place(gem(0.45), frame((0, 0, 0.7), out=(0, -1, 0))), 1.0),
    ("RuneRing", lambda: place(rune_ring(1.0), M((0, 0, 0.12))), 2.3),
    ("FloatingPlatform", lambda: place(floating_platform(1.0, 0.35), M((0, 0, 2.0))), 2.3),
    ("Eye", lambda: place(cartoon_eye(0.55), frame((0, 0, 0.8), out=(0, -1, 0))), 1.3),
    ("GlowEye", lambda: place(cartoon_eye(0.55, "CrystalCyan", lid="SteelDark"), frame((0, 0, 0.8), out=(0, -1, 0))), 1.3),
    ("Brow", lambda: place(brow(0.9), frame((0, 0, 0.6), out=(0, -1, 0))), 1.1),
    ("Grin", lambda: place(grin(1.4), frame((0, 0, 0.7), out=(0, -1, 0))), 1.6),
    ("GoldTrim", lambda: trim_strip((-0.9, 0, 0.2), (0.9, 0, 0.2), 0.22, "Gold"), 2.0),
    ("AuroraTrim", lambda: trim_strip((-0.9, 0, 0.2), (0.9, 0, 0.2), 0.22, "AuroraGreen", True), 2.0),
    ("SpiralBit", lambda: spiral_bit(2.0, 0.45, "Brass", "SteelLight"), 1.1),
]
