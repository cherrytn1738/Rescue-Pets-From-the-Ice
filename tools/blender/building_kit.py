# building_kit.py - the building kit for Rescue Pets From the Ice: chunky, hand-made, low-poly "toy"
# pieces (bevelled beams and boxes, cylinders, gears, pipes and elbows, rivets and bolts, a warning
# lamp, a crest, a chain, a flame, auger bits, a ladder, a name plate) that every building is built from.
#
# The approved smooth style. The stud-voxel style for buildings (lihfolk-stud-voxel) is being tried out in
# tools/blender/voxel/ (a style test, not in the game).
#
# Load after model_helpers.py, at the top level of a script:
#     exec(open(HELPERS, encoding="utf-8").read()); exec(open(KIT, encoding="utf-8").read())
#
# Conventions (on top of model_helpers.py):
#   * 1 unit = 1 stud, +Z up, a building's front faces -Y.
#   * Colour comes from ONE palette texture (BuildingPalette.png: a grid of flat swatches). Every face's
#     UVs sit in the middle of its swatch, so a mesh can hold several colours and still be one
#     MeshPart with one TextureID. Colours are picked by swatch name (SWATCHES).
#   * Glowing parts (lamp glass, flames) go in a separate "glow" mesh, so the game can give them Neon
#     and blink or flicker them without touching the rest.
#   * Every piece is built in its own frame, facing +Z ("out"): a lamp stands on +Z, a gear turns
#     about Z, a crest faces +Z, a bit points along +Z. Attachment points (Att) are frames with the
#     same rule, so placing a piece is: piece matrix = attachment matrix.
#   * Bevels are small and rounded (rounded_block edges, bevel_edges on cylinders); objects are shaded
#     smooth with a Weighted Normal modifier, so flat faces stay flat and only the bevels shade.
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

# ---------- the palette ----------

PALETTE_COLUMNS, PALETTE_ROWS, SWATCH_PIXELS = 8, 6, 16
GLOW_STRENGTH = globals().get("GLOW_STRENGTH", 1.1)  # preview only: in game, glow meshes are Neon
# Icy theme (docs/GAME_DESIGN.md: snow, see-through ice, icy blues and white, cartoon UI) plus the warm
# and signal colours a toy machine needs. Several match the UI theme (Accent, Gold, Error, Good).
SWATCHES = [
    # snow and ice
    ("SnowWhite", "F4FAFF"), ("FrostLight", "D6ECFF"), ("IceBlue", "9FD6F5"), ("GlacierBlue", "5AB4E6"),
    ("DeepIce", "2F7FC0"), ("NavyIce", "1C3F6E"), ("PolarTeal", "3FC1C9"), ("AuroraCyan", "6EE6FF"),
    # metals
    ("SteelLight", "C9D3DE"), ("Steel", "98A6B5"), ("SteelDark", "5F6C7B"), ("Iron", "3B4350"),
    ("Gunmetal", "262C36"), ("Brass", "E0B54A"), ("Gold", "FFD640"), ("Copper", "D27D4A"),
    # wood, stone, rubber
    ("PineLight", "E8B57A"), ("Pine", "C98A4E"), ("PineDark", "8E5A2E"), ("StoneLight", "BFC3C9"),
    ("Stone", "8D939C"), ("StoneDark", "646A73"), ("Rubber", "22262E"), ("Cream", "FFF0D6"),
    # signals and effects
    ("WarnRed", "FF5468"), ("WarnRedDark", "C2304A"), ("Amber", "FFB23E"), ("LampYellow", "FFE45C"),
    ("FlameOrange", "FF8A2A"), ("FlameYellow", "FFD24A"), ("Diamond", "C8F4FF"), ("Mint", "82FFC8"),
    # fantasy: runes, aurora, crystals
    ("RuneViolet", "8E6BFF"), ("RuneGlow", "C9B6FF"), ("AuroraGreen", "5CFFB0"), ("AuroraViolet", "B48CFF"),
    ("MagicPink", "FF7AD9"), ("CrystalCyan", "7FF5FF"), ("ArcaneDeep", "3A2A7A"), ("Moonstone", "E6E0FF"),
    # scrap and characters
    ("Rust", "B8673A"), ("RustDark", "7A3F22"), ("PatchGreen", "6E8B5A"), ("EyeWhite", "FFFFFF"),
    ("EyeDark", "141820"), ("Blush", "FF9AAE"), ("MoleFur", "7A5A48"), ("MoleFurLight", "A8836A"),
]
SWATCH_INDEX = {name: i for i, (name, _) in enumerate(SWATCHES)}


def swatch_rgb(name):
    hexcode = SWATCHES[SWATCH_INDEX[name]][1]
    return tuple(int(hexcode[i:i + 2], 16) / 255 for i in (0, 2, 4))


def swatch_uv(name):
    """The middle of a swatch, in UV space (V up; row 0 is the top row of the image)."""
    i = SWATCH_INDEX[name]
    col, row = i % PALETTE_COLUMNS, i // PALETTE_COLUMNS
    return ((col + 0.5) / PALETTE_COLUMNS, 1 - (row + 0.5) / PALETTE_ROWS)


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def write_palette(path):
    """BuildingPalette.png: PALETTE_COLUMNS x PALETTE_ROWS flat swatches, SWATCH_PIXELS each."""
    w, h = PALETTE_COLUMNS * SWATCH_PIXELS, PALETTE_ROWS * SWATCH_PIXELS
    image = bpy.data.images.get("BuildingPalette") or bpy.data.images.new("BuildingPalette", w, h, alpha=False)
    pixels = [0.0] * (w * h * 4)
    for y in range(h):
        row = (h - 1 - y) // SWATCH_PIXELS  # Blender's pixel rows start at the bottom
        for x in range(w):
            col = x // SWATCH_PIXELS
            r, g, b = swatch_rgb(SWATCHES[row * PALETTE_COLUMNS + col][0])
            k = (y * w + x) * 4
            pixels[k:k + 4] = (r, g, b, 1.0)  # an 8-bit sRGB image stores display values
    image.pixels = pixels
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.filepath_raw = path
    image.file_format = "PNG"
    image.save()
    return image


def palette_materials(image):
    """Two shared materials: the palette (lit), and the palette glowing (lamp glass, flames)."""
    made = {}
    for name, glow in (("BuildingPalette", False), ("BuildingPaletteGlow", True)):
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        if mat.node_tree is None:
            mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
        tex = next((n for n in nodes if n.type == "TEX_IMAGE"), None) or nodes.new("ShaderNodeTexImage")
        tex.image = image
        tex.interpolation = "Closest"  # flat swatches, no blending between neighbours
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.5
        if glow:
            links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = GLOW_STRENGTH
        made[name] = mat
    return made


# ---------- frames ----------

def frame(origin, out=(0, 0, 1), up=(0, 0, 1)):
    """A 4x4 frame at origin whose +Z points `out` and whose +Y leans toward `up`."""
    z = Vector(out).normalized()
    y = Vector(up) - z * Vector(up).dot(z)
    if y.length < 1e-4:
        y = Vector((0, 1, 0)) - z * z.y
    y.normalize()
    x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


# ---------- a mesh being assembled from kit pieces ----------

class Part:
    """One output mesh (one MeshPart). Kit pieces are dropped into it with a swatch and a matrix."""

    def __init__(self, name, glow=False):
        self.name, self.glow = name, glow
        self.bm = bmesh.new()
        self.bm.loops.layers.uv.verify()
        self.flat = set()  # face indices that stay flat-shaded (cut facets on crystals and gems)

    def take(self, piece, swatch, matrix=Matrix(), bevel=0.0):
        """piece: a bmesh in its own frame (consumed). Bevel its hard edges, colour it, place it."""
        if bevel:
            bevel_edges(piece, bevel, segments=2, angle=40)
        piece.transform(matrix)
        bmesh.ops.recalc_face_normals(piece, faces=piece.faces[:])
        uv_layer = piece.loops.layers.uv.verify()
        u, v = swatch_uv(swatch)
        for face in piece.faces:
            for loop in face.loops:
                loop[uv_layer].uv = (u, v)
        flat_layer = piece.faces.layers.int.get("flat")
        flags = [face[flat_layer] for face in piece.faces] if flat_layer else None
        before = len(self.bm.faces)
        temp = bpy.data.meshes.new("_kit_temp")
        piece.to_mesh(temp)
        piece.free()
        self.bm.from_mesh(temp)  # appends to what is already there, in the same face order
        bpy.data.meshes.remove(temp)
        if flags:
            self.flat.update(before + i for i, flag in enumerate(flags) if flag)

    def add(self, pieces, matrix=Matrix()):
        """pieces: what a kit function returns, [(bmesh, swatch, bevel, glow)]. Glow pieces are skipped
        here; use split() to send them to a glow Part."""
        for bm, swatch, bevel, glow in pieces:
            if glow and not self.glow:
                raise ValueError("glow piece added to a non-glow part %s: use split()" % self.name)
            self.take(bm, swatch, matrix, bevel)

    def finish(self, coll, materials):
        bm = self.bm
        bm.faces.ensure_lookup_table()
        for f in bm.faces:  # before triangulating: new triangles keep their face's flag
            f.smooth = f.index not in self.flat
        ngons = [f for f in bm.faces if len(f.verts) > 4]
        if ngons:
            bmesh.ops.triangulate(bm, faces=ngons)
        mesh = bpy.data.meshes.new(self.name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(self.name, mesh)
        coll.objects.link(obj)
        obj.data.materials.append(materials["BuildingPaletteGlow" if self.glow else "BuildingPalette"])
        mod = obj.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
        mod.mode = "FACE_AREA"
        mod.weight = 50
        mod.keep_sharp = True
        return obj


def split(pieces):
    """(solid pieces, glow pieces) of a kit function's result."""
    return [p for p in pieces if not p[3]], [p for p in pieces if p[3]]


def place(pieces, matrix):
    """The same pieces, moved by matrix (for building a piece out of pieces)."""
    for bm, *_ in pieces:
        bm.transform(matrix)
    return pieces


def _bm():
    return bmesh.new()


# ---------- the kit ----------
# Each returns [(bmesh, swatch, bevel, glow)] in its own frame. ATTACH lists each piece's attachment
# points in that frame (name: (origin, out)), shown on the kit sheet.

ATTACH = {}


def beam(length, width=0.5, depth=None, swatch="Pine", corner=0.1, edge=0.07):
    """A bevelled square beam standing on z = 0, `length` tall. Att: Bottom, Top."""
    bm = _bm()
    rounded_block(bm, (width, depth or width, length), M((0, 0, length / 2)), corner=corner, edge=edge, corner_seg=2, edge_seg=1)
    return [(bm, swatch, 0.0, False)]


ATTACH["Beam"] = {"Bottom": ((0, 0, 0), (0, 0, -1)), "Top": ((0, 0, 1), (0, 0, 1))}


def beam_between(p0, p1, width=0.5, depth=None, swatch="Pine"):
    """A beam from p0 to p1 (world points)."""
    p0, p1 = Vector(p0), Vector(p1)
    pieces = beam((p1 - p0).length, width, depth, swatch)
    return place(pieces, Matrix.Translation(p0) @ align_z(p1 - p0))


def block(size, swatch="SteelLight", corner=0.2, edge=0.14):
    """A rounded box sitting on z = 0. Att: Top, Bottom, Front."""
    bm = _bm()
    rounded_block(bm, size, M((0, 0, size[2] / 2)), corner=corner, edge=edge, corner_seg=2, edge_seg=2)
    return [(bm, swatch, 0.0, False)]


ATTACH["Block"] = {"Top": ((0, 0, 1), (0, 0, 1)), "Bottom": ((0, 0, 0), (0, 0, -1)), "Front": ((0, -0.5, 0.5), (0, -1, 0))}


def cyl(radius, height, swatch="Steel", segments=16, top=None, bevel=0.05):
    """A capped cylinder standing on z = 0 with softly bevelled rims. Att: Bottom, Top."""
    bm = _bm()
    cylinder(bm, (0, 0, 0), radius, height, segments, top)
    return [(bm, swatch, bevel, False)]


ATTACH["Cylinder"] = {"Bottom": ((0, 0, 0), (0, 0, -1)), "Top": ((0, 0, 1), (0, 0, 1))}


def gear(radius=1.0, teeth=10, thickness=0.35, tooth=0.22, swatch="Brass", hub="SteelDark"):
    """A chunky toothed gear turning about Z, centred on its axis (so it spins true as a MeshPart).
    Att: Axle (the centre of its back face)."""
    root = radius - tooth
    outline = []
    for i in range(teeth):
        for frac, r in ((0.0, root), (0.22, radius), (0.52, radius), (0.74, root)):
            a = 2 * math.pi * (i + frac) / teeth
            outline.append((r * math.cos(a), r * math.sin(a)))
    bm = _bm()
    loft(bm, [[Vector((x, y, z)) for x, y in outline] for z in (-thickness / 2, thickness / 2)])
    hub_bm = _bm()
    cylinder(hub_bm, (0, 0, -thickness * 0.8), radius * 0.32, thickness * 1.6, 12)
    cap = _bm()
    cylinder(cap, (0, 0, thickness * 0.8), radius * 0.16, thickness * 0.25, 6)  # a hex nut
    return [(bm, swatch, 0.045, False), (hub_bm, hub, 0.04, False), (cap, "Iron", 0.02, False)]


ATTACH["Gear"] = {"Axle": ((0, 0, -0.2), (0, 0, -1))}


def pipe(length, radius=0.22, swatch="Copper", flange="SteelDark"):
    """A straight pipe along +Z from z = 0, with a flange at each end. Att: EndA, EndB."""
    body = _bm()
    cylinder(body, (0, 0, 0), radius, length, 12)
    pieces = [(body, swatch, 0.03, False)]
    for z in (0.0, length - 0.16):
        ring = _bm()
        cylinder(ring, (0, 0, z), radius * 1.4, 0.16, 12)
        pieces.append((ring, flange, 0.03, False))
    return pieces


ATTACH["Pipe"] = {"EndA": ((0, 0, 0), (0, 0, -1)), "EndB": ((0, 0, 1), (0, 0, 1))}


def pipe_between(p0, p1, radius=0.22, swatch="Copper"):
    p0, p1 = Vector(p0), Vector(p1)
    return place(pipe((p1 - p0).length, radius, swatch), Matrix.Translation(p0) @ align_z(p1 - p0))


def elbow(bend=0.6, radius=0.22, swatch="Copper", flange="SteelDark"):
    """A 90-degree pipe elbow: in along +Z from the origin, out along +X. Att: EndA, EndB."""
    points = [Vector((bend - bend * math.cos(a), 0, bend * math.sin(a)))
              for a in (math.pi / 2 * k / 8 for k in range(9))]
    body = _bm()
    sweep(body, points, radius, 12)
    pieces = [(body, swatch, 0.0, False)]
    for base, direction in (((0, 0, 0), (0, 0, 1)), ((bend - 0.16, 0, bend), (1, 0, 0))):
        ring = _bm()
        cylinder(ring, base, radius * 1.4, 0.16, 12, direction=direction)
        pieces.append((ring, flange, 0.03, False))
    return pieces


ATTACH["PipeElbow"] = {"EndA": ((0, 0, 0), (0, 0, -1)), "EndB": ((0.6, 0, 0.6), (1, 0, 0))}


def rivet(radius=0.12, swatch="SteelDark"):
    """A domed rivet head on z = 0. Att: Base."""
    bm = _bm()
    lathe(bm, [(0, 0), (radius, 0), (radius * 0.85, radius * 0.55), (0, radius)], 8)
    return [(bm, swatch, 0.0, False)]


ATTACH["Rivet"] = {"Base": ((0, 0, 0), (0, 0, -1))}


def bolt(radius=0.16, swatch="Iron", washer="SteelLight"):
    """A hex bolt head on a washer, on z = 0. Att: Base."""
    w = _bm()
    cylinder(w, (0, 0, 0), radius * 1.35, radius * 0.25, 8)
    h = _bm()
    cylinder(h, (0, 0, radius * 0.25), radius, radius * 0.65, 6)
    return [(w, washer, 0.015, False), (h, swatch, 0.03, False)]


ATTACH["Bolt"] = {"Base": ((0, 0, 0), (0, 0, -1))}


def warning_lamp(radius=0.32, glass="WarnRed", metal="Iron", cage="SteelDark"):
    """A caged warning lamp on z = 0; the glass dome is a glow piece (it blinks in game). Att: Base."""
    base = _bm()
    cylinder(base, (0, 0, 0), radius * 1.15, radius * 0.7, 12)
    dome = _bm()
    lathe(dome, [(0, 0), (radius, 0), (radius, radius * 0.6), (radius * 0.86, radius * 1.1),
                 (radius * 0.5, radius * 1.42), (0, radius * 1.55)], 12, M((0, 0, radius * 0.7)))
    pieces = [(base, metal, 0.03, False), (dome, glass, 0.0, True)]
    top = radius * 0.7 + radius * 1.6
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        bar = _bm()
        sweep(bar, [Vector((radius * 1.08 * math.cos(a), radius * 1.08 * math.sin(a), radius * 0.6)),
                    Vector((radius * 1.08 * math.cos(a), radius * 1.08 * math.sin(a), radius * 1.6)),
                    Vector((radius * 0.45 * math.cos(a), radius * 0.45 * math.sin(a), top))], radius * 0.09, 6)
        pieces.append((bar, cage, 0.0, False))
    ring = _bm()
    torus(ring, M((0, 0, radius * 1.6)), radius * 1.08, radius * 0.1, 16, 6)
    cap = _bm()
    cylinder(cap, (0, 0, top - 0.02), radius * 0.5, radius * 0.25, 10)
    pieces += [(ring, cage, 0.0, False), (cap, metal, 0.02, False)]
    return pieces


ATTACH["WarningLamp"] = {"Base": ((0, 0, 0), (0, 0, -1))}


def _shield_outline(w, h, n=8):
    """(x, y) outline of a crest shield, centred, pointed at the bottom (-y): down the right side to
    the point, up the left side, then across a slightly arched top."""
    right = [(w / 2 * (1 - (s / n) ** 2.2), h / 2 - (s / n) * h) for s in range(n + 1)]
    left = [(-x, y) for x, y in reversed(right[:-1])]
    top = [(-w / 2 + w * t / 6, h / 2 + 0.06 * h * math.sin(math.pi * t / 6)) for t in range(1, 6)]
    return right + left + top


def crest(width=2.0, height=2.4, depth=0.22, rim="Gold", plate="DeepIce", emblem="SnowWhite", gem="AuroraCyan"):
    """A shield crest facing +Z (up is +Y) with a gold rim, an ice-blue plate and a snowflake.
    Att: Back."""
    outline = _shield_outline(width, height)
    pieces = []
    rim_bm = _bm()
    loft(rim_bm, [[Vector((x, y, z)) for x, y in outline] for z in (0, depth)])
    pieces.append((rim_bm, rim, 0.05, False))
    inner = [(x * 0.8, y * 0.8 - 0.04 * height) for x, y in outline]
    plate_bm = _bm()
    loft(plate_bm, [[Vector((x, y, z)) for x, y in inner] for z in (depth * 0.5, depth * 1.45)])
    pieces.append((plate_bm, plate, 0.03, False))
    for k in range(3):
        arm = _bm()
        rounded_block(arm, (width * 0.1, height * 0.5, depth * 0.5),
                      M((0, height * 0.04, depth * 1.6), (0, 0, k * math.pi / 3)), corner=0.04, edge=0.03, corner_seg=2, edge_seg=1)
        pieces.append((arm, emblem, 0.0, False))
    centre = _bm()
    cylinder(centre, (0, height * 0.04, depth * 1.6), width * 0.11, depth * 0.55, 6)
    pieces.append((centre, gem, 0.02, False))
    return pieces


ATTACH["Crest"] = {"Back": ((0, 0, 0), (0, 0, -1))}


def chain(links=6, size=0.22, swatch="SteelDark"):
    """A hanging chain going down -Z from the origin, links alternating by 90 degrees. Att: Top, Bottom."""
    pieces = []
    pitch = size * 2.3
    for i in range(links):
        bm = _bm()
        matrix = (Matrix.Translation((0, 0, -size * 1.4 - i * pitch)) @ Matrix.Rotation(i * math.pi / 2, 4, "Z")
                  @ Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Diagonal((1.0, 1.6, 1.0, 1.0)))
        torus(bm, matrix, size, size * 0.32, 12, 6)
        pieces.append((bm, swatch, 0.0, False))
    return pieces


ATTACH["Chain"] = {"Top": ((0, 0, 0), (0, 0, 1)), "Bottom": ((0, 0, -3.0), (0, 0, -1))}


def _flame_shape(bm, radius, height, twist, rings=9, segments=10, offset=(0, 0, 0)):
    """A lumpy, twisting teardrop along +Z (hand-made, not a perfect cone)."""
    ox, oy, oz = offset
    bottom = bm.verts.new((ox, oy, oz))
    top = bm.verts.new((ox, oy, oz + height))
    loops = []
    for k in range(1, rings):
        s = k / rings
        r = radius * math.sin(math.pi * s ** 0.55)
        loops.append([bm.verts.new((ox + r * (1 + 0.2 * math.cos(3 * a + twist * s)) * math.cos(a + twist * s * 0.6),
                                    oy + r * (1 + 0.2 * math.cos(3 * a + twist * s)) * math.sin(a + twist * s * 0.6),
                                    oz + s * height))
                      for a in (2 * math.pi * i / segments for i in range(segments))])
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((bottom, loops[0][j], loops[0][i]))
        bm.faces.new((loops[-1][i], loops[-1][j], top))
    for a, b in zip(loops, loops[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new((a[i], a[j], b[j], b[i]))


def flame(radius=0.55, height=1.8, outer="FlameOrange", inner="FlameYellow"):
    """A chunky stylised flame on z = 0: a twisting main tongue, two leaning side tongues and a yellow
    core (all glow: it flickers in game). Att: Base."""
    pieces = []
    a = _bm()
    _flame_shape(a, radius, height, 2.2)
    pieces.append((a, outer, 0.0, True))
    for side, lean in ((-1, 0.45), (1, 0.35)):
        tongue = _bm()
        _flame_shape(tongue, radius * 0.55, height * 0.62, -2.0 * side)
        tongue.transform(Matrix.Translation((side * radius * 0.55, 0, 0)) @ Matrix.Rotation(side * lean, 4, "Y"))
        pieces.append((tongue, outer, 0.0, True))
    core = _bm()
    _flame_shape(core, radius * 0.6, height * 0.6, -1.8, offset=(0, -radius * 0.35, 0.05))
    pieces.append((core, inner, 0.0, True))
    return pieces


ATTACH["Flame"] = {"Base": ((0, 0, 0), (0, 0, -1))}


BIT_KINDS = {  # length, radius, turns, flute, shaft, tip, collar
    "Iron": (2.0, 0.42, 2.0, "Iron", "SteelDark", "Iron", "SteelDark"),
    "Steel": (2.6, 0.5, 2.6, "SteelLight", "Steel", "SteelLight", "Iron"),
    "Diamond": (3.0, 0.58, 3.0, "Diamond", "SteelLight", "Diamond", "Gold"),
}


def auger(kind="Steel"):
    """A drill bit pointing along +Z from its mount (spins about Z; built round the axis). Att: Mount."""
    length, radius, turns, flute, shaft, tip, collar = BIT_KINDS[kind]
    pieces = []
    c = _bm()
    cylinder(c, (0, 0, 0), radius * 0.62, 0.32, 12)
    pieces.append((c, collar, 0.04, False))
    s = _bm()
    cylinder(s, (0, 0, 0.3), radius * 0.32, length * 0.72, 10)
    pieces.append((s, shaft, 0.0, False))
    steps = int(turns * 14)
    helix = [Vector((radius * (1 - 0.3 * t / steps) * math.cos(2 * math.pi * turns * t / steps),
                     radius * (1 - 0.3 * t / steps) * math.sin(2 * math.pi * turns * t / steps),
                     0.4 + (length * 0.74 - 0.4) * t / steps)) for t in range(steps + 1)]
    f = _bm()
    sweep(f, helix, radius * 0.27, 8, radius_end=radius * 0.2)
    pieces.append((f, flute, 0.0, False))
    t = _bm()
    cylinder(t, (0, 0, length * 0.72), radius * 0.55, length * 0.28, 6 if kind == "Diamond" else 10, top=0.0)
    pieces.append((t, tip, 0.0 if kind == "Diamond" else 0.03, False))
    return pieces


ATTACH["Auger"] = {"Mount": ((0, 0, 0), (0, 0, -1)), "Tip": ((0, 0, 3.0), (0, 0, 1))}


def ladder(height, width=1.0, rail="SteelDark", rung="Steel"):
    """A ladder standing on z = 0 in the XZ plane. Att: Bottom, Top."""
    pieces = []
    for x in (-width / 2, width / 2):
        pieces += place(beam(height, 0.16, 0.2, rail, corner=0.05, edge=0.04), M((x, 0, 0)))
    z = 0.6
    while z < height - 0.2:
        r = _bm()
        cylinder(r, (-width / 2, 0, z), 0.07, width, 6, direction=(1, 0, 0))
        pieces.append((r, rung, 0.0, False))
        z += 0.8
    return pieces


ATTACH["Ladder"] = {"Bottom": ((0, 0, 0), (0, 0, -1)), "Top": ((0, 0, 1), (0, 0, 1))}


def name_plate(width=3.0, height=0.9, board="PineLight", frame_swatch="Gold"):
    """A board for the owner's name (a SurfaceGui in game), facing +Z, gold frame. Att: Back."""
    back = _bm()
    rounded_block(back, (width + 0.24, height + 0.24, 0.12), M((0, 0, 0.06)), corner=0.14, edge=0.05, corner_seg=2, edge_seg=1)
    front = _bm()
    rounded_block(front, (width, height, 0.12), M((0, 0, 0.16)), corner=0.1, edge=0.05, corner_seg=2, edge_seg=1)
    pieces = [(back, frame_swatch, 0.0, False), (front, board, 0.0, False)]
    for x in (-width / 2 + 0.18, width / 2 - 0.18):
        pieces += place(rivet(0.07, "Gold"), M((x, 0, 0.22)))
    return pieces


ATTACH["NamePlate"] = {"Back": ((0, 0, 0), (0, 0, -1))}

# The kit, for the kit sheet: name -> (builder, display matrix, footprint width).
KIT = [
    ("Beam", lambda: beam(2.4), 1.2),
    ("Block", lambda: block((1.6, 1.4, 1.2)), 2.0),
    ("Cylinder", lambda: cyl(0.6, 1.4), 1.6),
    ("Gear", lambda: place(gear(0.9, 10), frame((0, 0, 1.0), out=(0, -1, 0))), 2.2),
    ("Pipe", lambda: pipe(2.0), 1.0),
    ("PipeElbow", lambda: elbow(), 1.6),
    ("Rivet (x2)", lambda: place(rivet(0.4), M()), 0.9),
    ("Bolt (x2)", lambda: bolt(0.5), 1.4),
    ("WarningLamp", lambda: warning_lamp(0.4), 1.3),
    ("Crest", lambda: place(crest(1.6, 2.0), frame((0, 0, 1.25), out=(0, -1, 0))), 2.0),
    ("Chain", lambda: place(chain(6, 0.2), M((0, 0, 2.6))), 0.9),
    ("Flame", lambda: flame(), 1.4),
    ("IronBit", lambda: place(auger("Iron"), frame((0, 0, 2.05), out=(0, 0, -1), up=(0, 1, 0))), 1.2),
    ("SteelBit", lambda: place(auger("Steel"), frame((0, 0, 2.65), out=(0, 0, -1), up=(0, 1, 0))), 1.3),
    ("DiamondBit", lambda: place(auger("Diamond"), frame((0, 0, 3.05), out=(0, 0, -1), up=(0, 1, 0))), 1.5),
    ("Ladder", lambda: ladder(2.6), 1.4),
    ("NamePlate", lambda: place(name_plate(2.2, 0.7), frame((0, 0, 0.6), out=(0, -1, 0))), 2.6),
]
