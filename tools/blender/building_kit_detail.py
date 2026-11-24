# building_kit_detail.py - the high-detail layer of the building kit (load after building_kit.py and
# building_kit_fantasy.py). Same toy style, same palette, more geometry:
#   * Q: quality settings. Round shapes (cylinders, domes, rings, tubes: 10+ segments) get Q["round"] times
#     the segments; faceted shapes (hex bolts, 6-sided crystals, 8-sided gems) keep theirs. Rounded blocks
#     and bevels get Q["corner"] / Q["edge"] / Q["bevel"] segments (tiny blocks stay cheap).
#   * subsurf(): Catmull-Clark subdivision of a low cage, for organic, characterful shapes.
#   * faceted(): marks a piece's faces flat-shaded (cut crystal and gem facets).
#   * Detail pieces: planks with wood grain grooves, riveted plates, inset panels, bolt rings, sagging
#     cables and ribbed hoses, handles, vents, screens, dials, hinges and lids, gems in settings,
#     engraved rune rings, faceted crystals, curved claws, pistons.
import bpy, bmesh, math
from mathutils import Vector, Matrix

Q = {"round": 1.5, "minor": 1.25, "corner": 3, "edge": 2, "bevel": 2, "tiny": 0.6}
Q.update(globals().get("Q_OVERRIDE") or {})

# Wrap the shared helpers once per namespace (model_helpers.py is re-read on every run, which resets them).
if not globals().get("_DETAIL_WRAPPED_FOR") is lathe:
    _lathe0, _torus0, _sweep0, _rb0, _bevel0 = lathe, torus, sweep, rounded_block, bevel_edges

    def _round_segments(n):
        return int(round(n * Q["round"])) if n >= 12 else n

    def lathe(bm, profile, segments, matrix=Matrix()):
        _lathe0(bm, profile, _round_segments(segments), matrix)

    def torus(bm, matrix, radius, minor, segments=24, minor_segments=8):
        _torus0(bm, matrix, radius, minor, _round_segments(segments), max(minor_segments, int(round(minor_segments * Q["minor"]))))

    def sweep(bm, points, radius, segments=10, radius_end=None, caps=True):
        _sweep0(bm, points, radius, min(24, int(round(segments * Q["round"]))) if segments >= 10 else segments, radius_end, caps)

    def rounded_block(bm, size, matrix=Matrix(), corner=0.3, edge=0.1, corner_seg=3, edge_seg=2, taper=1.0):
        if max(size) >= Q["tiny"]:
            corner_seg, edge_seg = max(corner_seg, Q["corner"]), max(edge_seg, Q["edge"])
        _rb0(bm, size, matrix, corner, edge, corner_seg, edge_seg, taper)

    def bevel_edges(bm, width, segments=2, angle=50):
        _bevel0(bm, width, max(segments, Q["bevel"]), angle)

    _DETAIL_WRAPPED_FOR = lathe


# ---------- shading and subdivision ----------

def faceted(bm):
    """Mark every face of this piece flat-shaded (Part keeps it flat): cut facets."""
    layer = bm.faces.layers.int.get("flat") or bm.faces.layers.int.new("flat")
    for f in bm.faces:
        f[layer] = 1
    return bm


def subsurf(bm, levels=2):
    """Catmull-Clark subdivision of a cage bmesh (consumed); returns the smooth result as a new bmesh."""
    mesh = bpy.data.meshes.new("_cage")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("_cage", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mod = obj.modifiers.new("Sub", "SUBSURF")
    mod.levels = mod.render_levels = levels
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    out = bmesh.new()
    out.from_mesh(obj.evaluated_get(deps).to_mesh())
    obj.evaluated_get(deps).to_mesh_clear()
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return out


def cage_box(size, cuts=2):
    """A box cage with `cuts` loops per side, centred, ready to be shaped and subdivided."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    return bm


# ---------- gears with rounded teeth ----------

def _tooth_outline(radius, teeth, tooth):
    root = radius - tooth
    steps = 2 if Q["round"] >= 1.25 else 1
    outline = []
    for i in range(teeth):
        pts = [(0.0, root)]
        for k in range(steps + 1):  # rounded rise, flat-ish tip, rounded fall
            u = k / steps
            pts.append((0.18 + 0.08 * u, root + tooth * math.sin(u * math.pi / 2)))
        for k in range(steps + 1):
            u = k / steps
            pts.append((0.5 + 0.08 * u, radius - tooth * (1 - math.cos(u * math.pi / 2))))
        pts.append((0.76, root))
        for frac, r in pts:
            a = 2 * math.pi * (i + frac) / teeth
            outline.append((r * math.cos(a), r * math.sin(a)))
    return outline


def gear(radius=1.0, teeth=10, thickness=0.35, tooth=0.22, swatch="Brass", hub="SteelDark"):
    """A chunky gear with rounded teeth, centred on its axle (spins true). Att: Axle."""
    outline = _tooth_outline(radius, teeth, tooth)
    bm = bmesh.new()
    loft(bm, [[Vector((x, y, z)) for x, y in outline] for z in (-thickness / 2, thickness / 2)])
    pieces = [(bm, swatch, 0.03, False)]
    hub_bm = bmesh.new()
    cylinder(hub_bm, (0, 0, -thickness * 0.8), radius * 0.32, thickness * 1.6, 16)
    pieces.append((hub_bm, hub, 0.03, False))
    nut = bmesh.new()
    cylinder(nut, (0, 0, thickness * 0.8), radius * 0.16, thickness * 0.25, 6)
    pieces.append((nut, "Iron", 0.02, False))
    for k in range(6):  # bolts round the hub
        a = k * math.pi / 3
        pieces += place(rivet(radius * 0.045, "SteelLight"), M((radius * 0.24 * math.cos(a), radius * 0.24 * math.sin(a), thickness * 0.8)))
    return pieces


def spoked_gear(radius=1.0, teeth=12, thickness=0.3, tooth=0.2, spokes=4, swatch="Brass", hub="Copper"):
    """An open-rim gear with rounded teeth, curved-edged spokes and a riveted hub. Att: Axle."""
    rim_in = radius - tooth - radius * 0.2
    outline = _tooth_outline(radius, teeth, tooth)
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
    pieces = [(bm, swatch, 0.0, False)]
    for s in range(spokes):  # bevelled bars: rounded edges, few triangles
        spoke = bmesh.new()
        box(spoke, (0, 0, 0), (radius * 0.16, rim_in * 2 - 0.05, thickness * 0.7), (0, 0, s * math.pi / spokes))
        pieces.append((spoke, swatch, min(0.04, radius * 0.03), False))
    h = bmesh.new()
    cylinder(h, (0, 0, -thickness * 0.75), radius * 0.26, thickness * 1.5, 16)
    pieces.append((h, hub, 0.03, False))
    for k in range(spokes):
        a = (k + 0.5) * 2 * math.pi / spokes
        pieces += place(rivet(radius * 0.04, "Gold"), M((radius * 0.18 * math.cos(a), radius * 0.18 * math.sin(a), thickness * 0.75)))
    return pieces


# ---------- wood ----------

def plank(length, width=0.9, thick=0.22, swatch="Pine", grain="PineDark", nails=True, seed=0.0):
    """A board along X sitting on z = 0: rounded edges, three wavy grain grooves on top, nail heads."""
    pieces = []
    board = bmesh.new()
    rounded_block(board, (length, width, thick), M((0, 0, thick / 2)), corner=0.06, edge=0.05, corner_seg=2, edge_seg=2)
    pieces.append((board, swatch, 0.0, False))
    for k, off in enumerate((-0.22, 0.24)):
        y0 = off * width
        pts = [Vector((length * (t / 6 - 0.5) * 0.92, y0 + 0.035 * width * math.sin(t * 1.5 + seed + k * 1.7), thick + 0.002)) for t in range(7)]
        g = bmesh.new()
        sweep(g, pts, 0.02, 3, caps=True)
        pieces.append((g, grain, 0.0, False))
    if nails:
        for x in (-length / 2 + 0.16, length / 2 - 0.16):
            pieces += place(rivet(0.04, "Iron"), M((x, 0, thick)))
    return pieces


def grained_beam(p0, p1, width=0.45, swatch="Pine", grain="PineDark", faces=(0, 1, 2, 3)):
    """A beam between two points with grain grooves running along its four faces."""
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    pieces = beam(L, width, None, swatch, corner=0.08, edge=0.06)
    for k in faces:
        a = k * math.pi / 2
        n = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-n.y, n.x, 0))
        off = 0.15 * (1 if k % 2 else -1)
        pts = [n * (width / 2 + 0.002) + side * (off * width + 0.025 * math.sin(t * 1.6 + k)) + Vector((0, 0, L * (0.08 + 0.84 * t / 6))) for t in range(7)]
        g = bmesh.new()
        sweep(g, pts, 0.02, 3)
        pieces.append((g, grain, 0.0, False))
    return place(pieces, Matrix.Translation(p0) @ align_z(p1 - p0))


# ---------- metalwork ----------

def riveted_plate(w, h, t=0.08, swatch="SteelLight", rivet_swatch="SteelDark", spacing=0.4):
    """A plate in the XY plane facing +Z with a row of rivets round its edge. Att: Back."""
    pieces = []
    plate = bmesh.new()
    rounded_block(plate, (w, h, t), M((0, 0, t / 2)), corner=min(w, h) * 0.12, edge=t * 0.4, corner_seg=3, edge_seg=2)
    pieces.append((plate, swatch, 0.0, False))
    inset = 0.12
    nx, ny = max(1, int(w / spacing)), max(1, int(h / spacing))
    seen = set()
    for i in range(nx + 1):
        for y in (-h / 2 + inset, h / 2 - inset):
            seen.add((round(-w / 2 + inset + (w - 2 * inset) * i / nx, 3), round(y, 3)))
    for j in range(ny + 1):
        for x in (-w / 2 + inset, w / 2 - inset):
            seen.add((round(x, 3), round(-h / 2 + inset + (h - 2 * inset) * j / ny, 3)))
    for x, y in seen:
        pieces += place(rivet(0.045, rivet_swatch), M((x, y, t)))
    return pieces


def rivet_ring(radius, count=8, size=0.06, swatch="Gold"):
    """Rivets in a circle in the XY plane facing +Z (cheaper than a bolt ring)."""
    pieces = []
    for k in range(count):
        a = 2 * math.pi * k / count
        pieces += place(rivet(size, swatch), M((radius * math.cos(a), radius * math.sin(a), 0)))
    return pieces


def inset_panel(w, h, depth=0.06, plate="SteelLight", frame_swatch="SteelDark", bolts=True):
    """A panel facing +Z: a dark recessed frame (the panel line) with a plate set into it."""
    pieces = []
    border = 0.07
    for x, y, sw, sh in ((0, h / 2 - border / 2, w, border), (0, -h / 2 + border / 2, w, border),
                         (w / 2 - border / 2, 0, border, h), (-w / 2 + border / 2, 0, border, h)):
        b = bmesh.new()
        box(b, (x, y, depth / 2), (sw, sh, depth))
        pieces.append((b, frame_swatch, 0.0, False))
    p = bmesh.new()
    rounded_block(p, (w - 2 * border - 0.03, h - 2 * border - 0.03, depth * 0.6), M((0, 0, depth * 0.3)), corner=0.05, edge=0.02, corner_seg=2, edge_seg=2)
    pieces.append((p, plate, 0.0, False))
    if bolts:
        for sx in (-1, 1):
            for sy in (-1, 1):
                pieces += place(rivet(0.05, "Iron"), M((sx * (w / 2 - border / 2), sy * (h / 2 - border / 2), depth)))
    return pieces


def bolt_ring(radius, count=8, size=0.07, swatch="Iron"):
    """Bolts in a circle in the XY plane facing +Z (a flange or a joint)."""
    pieces = []
    for k in range(count):
        a = 2 * math.pi * k / count
        pieces += place(bolt(size, swatch, "SteelLight"), M((radius * math.cos(a), radius * math.sin(a), 0), (0, 0, a)))
    return pieces


def cable(p0, p1, sag=0.6, radius=0.07, swatch="Rubber", sleeve="SteelDark", ribs=0):
    """A cable or hose hanging between two points with a natural sag, sleeves at both ends; ribs > 0
    adds rings along it (a ribbed hose)."""
    p0, p1 = Vector(p0), Vector(p1)
    pts = [p0.lerp(p1, t / 16) - Vector((0, 0, sag * 4 * (t / 16) * (1 - t / 16))) for t in range(17)]
    c = bmesh.new()
    sweep(c, pts, radius, 8)
    pieces = [(c, swatch, 0.0, False)]
    for end, nxt in ((pts[0], pts[1]), (pts[-1], pts[-2])):
        s = bmesh.new()
        cylinder(s, end, radius * 1.6, 0.18, 12, direction=nxt - end)
        pieces.append((s, sleeve, 0.02, False))
    for k in range(1, ribs + 1):
        i = int(16 * k / (ribs + 1))
        r = bmesh.new()
        torus(r, Matrix.Translation(pts[i]) @ align_z(pts[i + 1] - pts[i - 1]), radius * 1.05, radius * 0.25, 8, 4)
        pieces.append((r, swatch, 0.0, False))
    return pieces


def handle(width=0.6, height=0.25, radius=0.05, swatch="SteelDark", mounts="Iron"):
    """A U-shaped grab handle on the XY plane, sticking out along +Z. Att: Back."""
    pts = [Vector((-width / 2, 0, 0)), Vector((-width / 2, 0, height * 0.7)), Vector((-width * 0.4, 0, height)),
           Vector((width * 0.4, 0, height)), Vector((width / 2, 0, height * 0.7)), Vector((width / 2, 0, 0))]
    h = bmesh.new()
    sweep(h, pts, radius, 8)
    pieces = [(h, swatch, 0.0, False)]
    for x in (-width / 2, width / 2):
        m = bmesh.new()
        cylinder(m, (x, 0, 0), radius * 2.0, 0.06, 10)
        pieces.append((m, mounts, 0.01, False))
    return pieces


def vent(w=1.0, h=0.6, slats=5, swatch="SteelDark", frame_swatch="Iron"):
    """A louvred vent facing +Z: a frame with angled slats. Att: Back."""
    pieces = []
    f = bmesh.new()
    rounded_block(f, (w, h, 0.08), M((0, 0, 0.04)), corner=0.06, edge=0.03, corner_seg=2, edge_seg=2)
    pieces.append((f, frame_swatch, 0.0, False))
    for k in range(slats):
        y = -h / 2 + 0.08 + (h - 0.16) * (k + 0.5) / slats
        s = bmesh.new()
        box(s, (0, y, 0.1), (w - 0.14, (h - 0.16) / slats * 0.75, 0.04), (-0.5, 0, 0))
        pieces.append((s, swatch, 0.0, False))
    return pieces


def screen(w=0.8, h=0.5, glow="AuroraCyan", bezel="NavyIce", bars=3):
    """A small glowing screen facing +Z: a bezel, a lit pane and a little bar readout. Att: Back."""
    pieces = []
    b = bmesh.new()
    rounded_block(b, (w, h, 0.1), M((0, 0, 0.05)), corner=0.08, edge=0.04, corner_seg=3, edge_seg=2)
    pieces.append((b, bezel, 0.0, False))
    p = bmesh.new()
    rounded_block(p, (w - 0.14, h - 0.14, 0.03), M((0, 0, 0.1)), corner=0.05, edge=0.01, corner_seg=2, edge_seg=1)
    pieces.append((p, glow, 0.0, True))
    for k in range(bars):
        bar = bmesh.new()
        bh = (h - 0.24) * (0.4 + 0.25 * ((k * 7) % 3))
        rounded_block(bar, ((w - 0.3) / bars * 0.6, bh, 0.02), M((-w / 2 + 0.15 + (w - 0.3) * (k + 0.5) / bars, -h / 2 + 0.12 + bh / 2, 0.125)), corner=0.01, edge=0.005, corner_seg=1, edge_seg=1)
        pieces.append((bar, bezel, 0.0, False))
    return pieces


def dial(radius=0.25, face="Cream", rim="Brass", needle="WarnRed", angle=0.6):
    """A pressure dial facing +Z: a rim, a face with tick marks and a needle. Att: Back."""
    pieces = []
    r = bmesh.new()
    cylinder(r, (0, 0, 0), radius, 0.1, 16)
    pieces.append((r, rim, 0.02, False))
    f = bmesh.new()
    cylinder(f, (0, 0, 0.1), radius * 0.82, 0.02, 16)
    pieces.append((f, face, 0.0, False))
    for k in range(7):
        a = math.pi * 1.25 - k * math.pi * 1.5 / 6
        t = bmesh.new()
        box(t, (radius * 0.66 * math.cos(a), radius * 0.66 * math.sin(a), 0.125), (0.02, radius * 0.16, 0.01), (0, 0, a - math.pi / 2))
        pieces.append((t, "EyeDark", 0.0, False))
    n = bmesh.new()
    rounded_block(n, (0.03, radius * 0.66, 0.015), M((0.33 * radius * math.cos(angle + math.pi / 2), 0.33 * radius * math.sin(angle + math.pi / 2), 0.135), (0, 0, angle)), corner=0.008, edge=0.004, corner_seg=1, edge_seg=1)
    pieces.append((n, needle, 0.0, False))
    pieces += place(cyl(0.035, 0.03, "Iron", 8), M((0, 0, 0.12)))
    return pieces


def hinge(length=0.6, radius=0.06, knuckles=3, swatch="SteelDark", pin="Brass"):
    """A hinge along X at the origin: alternating knuckles on a pin."""
    pieces = []
    for k in range(knuckles):
        seg = length / knuckles
        h = bmesh.new()
        cylinder(h, (-length / 2 + k * seg + 0.01, 0, 0), radius, seg - 0.02, 12, direction=(1, 0, 0))
        pieces.append((h, swatch, 0.01, False))
    for x in (-length / 2 - 0.03, length / 2 + 0.03):
        c = bmesh.new()
        cylinder(c, (x - 0.02 if x < 0 else x - 0.01, 0, 0), radius * 0.6, 0.03, 8, direction=(1, 0, 0))
        pieces.append((c, pin, 0.0, False))
    return pieces


def lidded_box(size, swatch="Copper", lid="Copper", trim="Brass", hinge_swatch="SteelDark"):
    """A housing sitting on z = 0 with a separate lid (a seam line), a hinge along the back, a latch at
    the front and bolts round the base."""
    w, d, h = size
    lid_h = h * 0.22
    pieces = block((w, d, h - lid_h), swatch, corner=0.18, edge=0.1)
    pieces += place(block((w + 0.08, d + 0.08, lid_h), lid, corner=0.2, edge=0.1), M((0, 0, h - lid_h + 0.02)))
    pieces += place(block((w + 0.12, d + 0.12, 0.1), trim, corner=0.22, edge=0.04), M((0, 0, 0)))
    pieces += place(hinge(w * 0.6, 0.07, 3, hinge_swatch), M((0, d / 2 + 0.06, h - lid_h + 0.02)))
    latch = bmesh.new()
    rounded_block(latch, (0.22, 0.08, 0.3), M((0, -d / 2 - 0.05, h - lid_h - 0.05)), corner=0.04, edge=0.02, corner_seg=2, edge_seg=1)
    pieces.append((latch, trim, 0.0, False))
    for sx in (-1, 1):
        for sy in (-1, 1):
            pieces += place(rivet(0.07, "Iron"), M((sx * (w / 2 - 0.12), sy * (d / 2 - 0.12), 0.1)))
    return pieces


def piston(p0, p1, radius=0.14, body="SteelDark", rod="SteelLight"):
    """A hydraulic piston between two points: a fat cylinder, a shiny rod and eye mounts."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    pieces = []
    b = bmesh.new()
    cylinder(b, p0, radius, d.length * 0.55, 12, direction=d)
    pieces.append((b, body, 0.02, False))
    r = bmesh.new()
    cylinder(r, p0 + d * 0.5, radius * 0.45, d.length * 0.5, 10, direction=d)
    pieces.append((r, rod, 0.0, False))
    for p in (p0, p1):
        e = bmesh.new()
        blob(e, p, (radius * 1.1,) * 3, 2)
        pieces.append((e, body, 0.0, False))
    return pieces


# ---------- crystals and gems ----------

def cut_crystal(height=1.6, radius=0.32, swatch="CrystalCyan", tilt=(0, 0), sides=6, glow=True):
    """A crystal with cut facets: a bevelled base, slightly tapering sides, a two-step faceted point."""
    bm = bmesh.new()
    lathe(bm, [(0, -0.05), (radius * 0.78, -0.05), (radius, height * 0.1), (radius * 0.94, height * 0.6),
               (radius * 0.6, height * 0.82), (0, height)], sides)
    bm.transform(Matrix.Rotation(tilt[0], 4, "X") @ Matrix.Rotation(tilt[1], 4, "Y"))
    return [(faceted(bm), swatch, 0.0, glow)]


def cut_crystal_cluster(scale=1.0, swatch="CrystalCyan", base="Stone", count=6):
    pieces = []
    rock = bmesh.new()
    blob(rock, (0, 0, 0.12 * scale), (0.7 * scale, 0.6 * scale, 0.3 * scale), 2, floor=0.0)
    pieces.append((rock, base, 0.0, False))
    layout = ((1.5, 0.3, 0, 0, 0, 0), (1.0, 0.22, 0.45, 0.1, 0.3, 0.05), (0.9, 0.2, -0.4, 0.2, -0.28, 0.1),
              (0.7, 0.16, 0.1, -0.5, 0.05, -0.25), (0.55, 0.13, -0.3, -0.45, -0.2, -0.2), (0.6, 0.14, 0.5, 0.45, 0.25, 0.25))
    for h, r, tx, ty, ox, oy in layout[:count]:
        pieces += place(cut_crystal(h * scale, r * scale, swatch, (tx, ty)), M((ox * scale, oy * scale, 0.1 * scale)))
    return pieces


def cut_gem(size=0.4, swatch="MagicPink", glow=True):
    """A brilliant-cut gem (table up, point down), faceted, centred on the origin."""
    bm = bmesh.new()
    lathe(bm, [(0, -size * 0.75), (size * 0.55, -size * 0.3), (size, 0), (size * 0.92, size * 0.18), (size * 0.6, size * 0.38), (0, size * 0.42)], 8)
    return [(faceted(bm), swatch, 0.0, glow)]


def gem_setting(size=0.3, swatch="MagicPink", metal="Gold", prongs=4):
    """A gem in a setting facing +Z: a gold bezel cup, prongs over the girdle, the gem on top."""
    pieces = []
    cup = bmesh.new()
    lathe(cup, [(0, 0), (size * 0.7, 0), (size * 1.15, size * 0.35), (size * 1.1, size * 0.5), (0, size * 0.45)], 16)
    pieces.append((cup, metal, 0.0, False))
    pieces += place(cut_gem(size, swatch), M((0, 0, size * 0.85)))
    for k in range(prongs):
        a = 2 * math.pi * k / prongs + math.pi / 4
        pr = bmesh.new()
        sweep(pr, [Vector((size * 1.05 * math.cos(a), size * 1.05 * math.sin(a), size * 0.4)),
                   Vector((size * 1.08 * math.cos(a), size * 1.08 * math.sin(a), size * 0.85)),
                   Vector((size * 0.8 * math.cos(a), size * 0.8 * math.sin(a), size * 1.08))], size * 0.1, 6)
        pieces.append((pr, metal, 0.0, False))
    return pieces


# ---------- magic ----------

_RUNE_STROKES = [  # little glyphs, each a few strokes (x0, y0, x1, y1) in a unit box
    ((0, -1, 0, 1), (0, 0.2, 0.7, 0.9), (0, -0.2, 0.7, -0.9)),
    ((-0.6, -1, 0, 1), (0, 1, 0.6, -1), (-0.35, -0.1, 0.35, -0.1)),
    ((0, -1, 0, 1), (-0.7, 0.6, 0.7, 0.6)),
    ((-0.6, 1, 0.6, -1), (-0.6, -1, 0.6, 1)),
    ((0, -1, 0, 0.3), (0, 0.3, -0.6, 1), (0, 0.3, 0.6, 1)),
    ((-0.5, -1, -0.5, 1), (-0.5, 1, 0.5, 0.3), (0.5, 0.3, -0.5, -0.3)),
]


def rune_glyph(size, k, swatch="RuneGlow", depth=0.05):
    """One rune glyph in the XY plane (k picks the glyph)."""
    pieces = []
    for x0, y0, x1, y1 in _RUNE_STROKES[k % len(_RUNE_STROKES)]:
        a, b = Vector((x0 * size * 0.5, y0 * size * 0.5, 0)), Vector((x1 * size * 0.5, y1 * size * 0.5, 0))
        s = bmesh.new()
        L = (b - a).length
        box(s, (0, 0, 0), (size * 0.14, L + size * 0.14, depth))
        s.transform(Matrix.Translation((a + b) / 2) @ Matrix.Rotation(math.atan2(-(b - a).x, (b - a).y), 4, "Z"))
        pieces.append((s, swatch, 0.0, True))
    return pieces


def engraved_rune_ring(radius=1.6, swatch="RuneGlow", band="ArcaneDeep", rim="RuneViolet", glyphs=12):
    """A magic circle in the XY plane: a broad dark band with raised rims, glowing runes set into it
    (engraved: their tops sit just under the rims), and a thin glowing inner circle."""
    pieces = []
    w = radius * 0.22
    b = bmesh.new()
    lathe(b, [(radius - w / 2, 0), (radius + w / 2, 0), (radius + w / 2, 0.06), (radius - w / 2, 0.06), (radius - w / 2, 0)], 32)
    pieces.append((b, band, 0.0, False))
    for r in (radius - w / 2, radius + w / 2):
        rr = bmesh.new()
        torus(rr, M((0, 0, 0.08)), r, 0.045, 24, 4)
        pieces.append((rr, rim, 0.0, False))
    for k in range(glyphs):
        a = 2 * math.pi * k / glyphs
        pieces += place(rune_glyph(w * 0.62, k, swatch, 0.04), M((radius * math.cos(a), radius * math.sin(a), 0.06), (0, 0, a - math.pi / 2)))
    inner = bmesh.new()
    torus(inner, M((0, 0, 0.04)), radius * 0.78, 0.03, 24, 3)
    pieces.append((inner, swatch, 0.0, True))
    return pieces


# ---------- creature parts ----------

def curved_claw(length=0.9, radius=0.2, curl=0.45, swatch="SteelLight"):
    """A curved, tapering claw along +Z that hooks toward -Y (smooth, many rings)."""
    pts = [Vector((0, -curl * length * (t / 8) ** 2, length * t / 8)) for t in range(9)]
    c = bmesh.new()
    sweep(c, pts, radius, 8, radius_end=radius * 0.08)
    tip = bmesh.new()
    blob(tip, pts[-1], (radius * 0.1,) * 3, 1)
    return [(c, swatch, 0.0, False), (tip, swatch, 0.0, False)]


DETAIL_KIT = [
    ("Plank", lambda: plank(2.0, 0.6), 2.1),
    ("RivetedPlate", lambda: place(riveted_plate(1.2, 0.9), frame((0, 0, 0.6), out=(0, -1, 0))), 1.4),
    ("InsetPanel", lambda: place(inset_panel(1.2, 0.9), frame((0, 0, 0.6), out=(0, -1, 0))), 1.4),
    ("Vent", lambda: place(vent(1.0, 0.6), frame((0, 0, 0.5), out=(0, -1, 0))), 1.2),
    ("Screen", lambda: place(screen(0.9, 0.6), frame((0, 0, 0.5), out=(0, -1, 0))), 1.1),
    ("Dial", lambda: place(dial(0.35), frame((0, 0, 0.45), out=(0, -1, 0))), 0.9),
    ("Handle", lambda: place(handle(0.7, 0.3), frame((0, 0, 0.35), out=(0, -1, 0))), 0.9),
    ("Hinge", lambda: place(hinge(0.8, 0.08), M((0, 0, 0.1))), 1.0),
    ("LiddedBox", lambda: lidded_box((1.2, 1.0, 0.9)), 1.4),
    ("Cable", lambda: cable((-0.9, 0, 1.0), (0.9, 0, 1.0), 0.5, 0.07), 2.0),
    ("Hose", lambda: cable((-0.9, 0, 1.0), (0.9, 0, 1.0), 0.4, 0.12, "Rubber", "Brass", ribs=6), 2.0),
    ("Piston", lambda: piston((0, 0, 0.15), (0, 0, 1.5)), 0.6),
    ("CutCrystal", lambda: cut_crystal(1.6, 0.35), 0.9),
    ("GemSetting", lambda: place(gem_setting(0.32), frame((0, 0, 0.5), out=(0, -1, 0))), 0.9),
    ("EngravedRuneRing", lambda: place(engraved_rune_ring(1.0), M((0, 0, 0.05))), 2.4),
    ("CurvedClaw", lambda: place(curved_claw(1.0, 0.2), M((0, 0, 0))), 0.6),
]
