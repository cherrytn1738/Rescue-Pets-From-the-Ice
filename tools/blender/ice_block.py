# ice_block.py - the ice block's look, in the buildings' smooth toy style. Part 1 of the redesign: three options
# for one test case (the Blue Ice layer), so the developer can choose:
#   IceBlockA  faceted iceberg: a chunky low-poly berg, flat-shaded facets in several blues (deep at the base, pale
#              at the top), jagged crystal spikes on top, a snow cap with soft drips over the edges
#   IceBlockB  carved block: a rounded, bevelled block, frosty white edges and glints, colour deepening from the top
#              down, a thick snow cap with icicles, small crystals and snow chunks round the base
#   IceBlockC  crystal geode: a block with clusters of glowing crystals bursting out of its corners, a clearer
#              window in a frosty frame on the front (and back), a snow cap
# Every option is built at the level-1 size (14 studs tall, 11.2 wide and deep; the game scales it with the level)
# with its pivot on the ground at the middle, front -Y (Roblox -Z). Meshes, by the suffix the game styles them by:
#   ...Shell     the ice: transparent through the atlas's alpha (frosty rims, a clear middle)
#   ...Inner     trapped bubbles and frost streaks (transparent)
#   ...Snow      the snow cap, lumps and drips (opaque)
#   ...Crystals  spikes, icicles, crystals (opaque);  ...Glass  see-through crystal shells (C)
#   ...Glow      the glowing crystal cores (C; Neon, coloured in game)
#   ...Crack1-4  the crack lines of each crack stage, lying on the shell's surface (opaque, shown by stage)
# Colours come from one texture, assets/textures/ice/IceBlueAtlas.png (tools/make_ice_textures.py: keep the regions
# below in step with it). Under 5k triangles per block (the plaza can show 8).
#   blender -b --factory-startup --python tools/blender/ice_block.py [-- render]
#   (or the Blender MCP: REPO = r"..."; exec(open(REPO + r"\tools\blender\ice_block.py", encoding="utf-8").read()))
# Out: store-assets/ice-block/IceBlock<A|B|C>.fbx, ice_manifest.json (meshes, triangles, sizes)
import ast, json, math, os, random, sys
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

if "REPO" not in globals():
    REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT_SCALE = 0.1  # arrives in Studio at 10x, like the plot parts (build_templates.luau scales it back)
exec(open(os.path.join(REPO, "tools", "blender", "model_helpers.py"), encoding="utf-8").read())
OUT = os.path.join(REPO, "store-assets", "ice-block")
ATLAS_PATH = os.path.join(REPO, "assets", "textures", "ice", "IceBlueAtlas.png")
H, W = 14.0, 11.2  # the level-1 block (LayerConfig.Block.HeightAtFirstLevel, IceLooks.BlockWidthShare)
MAX_BLOCK_TRIS = 5000
ONLY = globals().get("ONLY")  # e.g. ["IceBlockB"]
EXPORT = globals().get("EXPORT", True)

# ---------- the atlas (tools/make_ice_textures.py) ----------

_src = open(os.path.join(REPO, "tools", "make_ice_textures.py"), encoding="utf-8").read()
SWATCH_NAMES = [s[0] for s in next(ast.literal_eval(n.value) for n in ast.parse(_src).body
                                   if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SWATCHES")]
ATLAS = 512.0


def _px(x, y):
    return (x / ATLAS, 1 - y / ATLAS)


def clamp01(t):
    return max(0.0, min(1.0, t))


def swatch_uv(name):
    i = SWATCH_NAMES.index(name)
    return _px(256 + 32 * (i % 8) + 16, 256 + 32 * (i // 8) + 16)


def column_uv(col, t):
    """Gradient column col (0-7) at height share t (0 bottom, 1 top)."""
    return _px(256 + 32 * col + 16, 2 + (1 - clamp01(t)) * 252)


def side_uv(u, v):
    """Region S: a side face, u across it (0 left to 1 right, seen from outside), v up it."""
    return _px(1.5 + clamp01(u) * 253, 1.5 + (1 - clamp01(v)) * 509)


def crack_uv(u):
    return _px(258 + clamp01(u) * 252, 496)


def preview_material():
    mat = bpy.data.materials.get("IceAtlas") or bpy.data.materials.new("IceAtlas")
    if mat.node_tree is None:
        mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    tex = next((n for n in nodes if n.type == "TEX_IMAGE"), None) or nodes.new("ShaderNodeTexImage")
    image = bpy.data.images.get("IceBlueAtlas") or bpy.data.images.load(ATLAS_PATH)
    image.name = "IceBlueAtlas"
    image.reload()
    tex.image = image
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.25
    try:
        mat.surface_render_method = "BLENDED"
    except (AttributeError, TypeError):
        pass
    mat.diffuse_color = (0.7, 0.85, 1.0, 0.6)
    return mat


# ---------- a mesh assembled from pieces, each with its own UV rule ----------

class IceMesh:
    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.bm.loops.layers.uv.verify()
        self.flat = set()

    def add(self, piece, uv, matrix=None, flat=False, recalc=True):
        """piece: a bmesh (consumed). uv: a swatch name, or a function (face, vertex position) -> (u, v), called
        after the piece is placed. flat: flat-shaded facets."""
        if matrix is not None:
            piece.transform(matrix)
        if recalc:
            bmesh.ops.recalc_face_normals(piece, faces=piece.faces[:])
        piece.normal_update()
        layer = piece.loops.layers.uv.verify()
        for face in piece.faces:
            for loop in face.loops:
                loop[layer].uv = uv(face, loop.vert.co) if callable(uv) else swatch_uv(uv)
        before = len(self.bm.faces)
        temp = bpy.data.meshes.new("_ice_temp")
        piece.to_mesh(temp)
        piece.free()
        self.bm.from_mesh(temp)
        bpy.data.meshes.remove(temp)
        if flat:
            self.flat.update(range(before, len(self.bm.faces)))

    def finish(self, coll, material):
        if not self.bm.faces:
            self.bm.free()
            return None
        bm = self.bm
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            f.smooth = f.index not in self.flat
        ngons = [f for f in bm.faces if len(f.verts) > 4]
        if ngons:
            bmesh.ops.triangulate(bm, faces=ngons)
        mesh = bpy.data.meshes.new(self.name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(self.name, mesh)
        coll.objects.link(obj)
        obj.data.materials.append(material)
        if len(self.flat) < len(mesh.polygons):  # soft pieces: weighted normals keep flat faces flat
            mod = obj.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
            mod.mode = "FACE_AREA"
            mod.weight = 50
            mod.keep_sharp = True
        return obj


def new_bm():
    return bmesh.new()


# ---------- shapes ----------

def rounded_body(size, corner, edge, centre_z, seg=3):
    bm = new_bm()
    rounded_block(bm, size, Matrix.Translation((0, 0, centre_z)), corner=corner, edge=edge, corner_seg=seg, edge_seg=seg)
    return bm


def body_uv(hx, hy, z0, z1, sides="S", front_back="S"):
    """The rounded body's faces: flat sides box-projected onto region S (or a gradient column), the top frosty,
    the rounded corners and edges frosty white."""
    def uv(face, co):
        n = face.normal
        if n.z > 0.95:
            return swatch_uv("TopFrost")
        if n.z < -0.95:
            return swatch_uv("BaseDeep")
        if abs(n.z) < 0.05 and max(abs(n.x), abs(n.y)) > 0.995:
            front = abs(n.y) >= abs(n.x)
            rule = front_back if front else sides
            if rule != "S":
                return column_uv(rule, co.z / H)
            if front:
                u = (co.x + hx) / (2 * hx) if n.y < 0 else (hx - co.x) / (2 * hx)
            else:
                u = (co.y + hy) / (2 * hy) if n.x > 0 else (hy - co.y) / (2 * hy)
            return side_uv(u, (co.z - z0) / (z1 - z0))
        if n.z > 0.3:
            return column_uv(7, co.z / H)  # the top rounding: white frost
        return column_uv(0, co.z / H)  # the corners: frosty, deepening downwards
    return uv


def lump(at, size, subdivisions=2, rot=0.0, floor=None):
    bm = new_bm()
    blob(bm, (0, 0, 0), size, subdivisions=subdivisions, rotation=(0, 0, rot), floor=None if floor is None else floor - at[2])
    bm.transform(Matrix.Translation(Vector(at)))
    return bm


def snow_uv(face, co):
    return swatch_uv("SnowWhite" if face.normal.z > 0.35 else "SnowShade")


def drip(at, normal, length, radius):
    """A soft snow drip hanging over an edge: an elongated blob on the surface, pointing down."""
    bm = new_bm()
    blob(bm, (0, 0, 0), (radius, radius * 0.75, length / 2), subdivisions=1)
    n = Vector(normal)
    n.z = 0
    n = n.normalized() if n.length > 1e-3 else Vector((0, -1, 0))
    yaw = math.atan2(n.x, -n.y)
    bm.transform(Matrix.Translation(Vector(at) + n * radius * 0.35 + Vector((0, 0, -length * 0.35))) @ Matrix.Rotation(yaw, 4, "Z"))
    return bm


def cone_down(base, radius, length, segments=6, lean=(0.0, 0.0)):
    bm = new_bm()
    lathe(bm, [(0, 0), (radius, 0), (radius * 0.55, length * 0.45), (0, length)], segments)
    bm.transform(Matrix.Translation(Vector(base)) @ Matrix.Rotation(lean[0], 4, "X") @ Matrix.Rotation(lean[1], 4, "Y") @ Matrix.Rotation(math.pi, 4, "X"))
    return bm


def crystal(base, direction, radius, length, sides=6, twist=0.0, sink=0.6):
    """A crystal: a prism with a pointed tip, from base along direction (sunk a little into what it grows from)."""
    bm = new_bm()
    lathe(bm, [(0, -sink), (radius, -sink), (radius, length * 0.68), (radius * 0.35, length * 0.9), (0, length)], sides)
    bm.transform(Matrix.Translation(Vector(base)) @ align_z(direction) @ Matrix.Rotation(twist, 4, "Z"))
    return bm


def core(base, direction, radius, length, twist):
    """A crystal's glowing core: a plain pointed prism (fewer triangles than the crystal round it)."""
    bm = new_bm()
    lathe(bm, [(0, -1.0), (radius, -1.0), (radius, length * 0.7), (0, length)], 6)
    bm.transform(Matrix.Translation(Vector(base)) @ align_z(direction) @ Matrix.Rotation(twist, 4, "Z"))
    return bm


def facet_colour(index):
    """Crystals: alternate a light and a darker face, so the facets read."""
    return ("CrystalPale", "CrystalCyan", "IceBlue", "CrystalPale", "GlacierBlue", "CrystalCyan")[index % 6]


def crystal_uv(face, co):
    n = face.normal
    k = int((math.atan2(n.y, n.x) + math.pi) / (2 * math.pi) * 6 + 0.5) + (0 if n.z < 0.5 else 3)
    return swatch_uv(facet_colour(k))


def spike(base, direction, radius, length, rng, sides=5):
    """A jagged crystal spike: an irregular pyramid (flat facets)."""
    bm = new_bm()
    pts = []
    for k in range(sides):
        a = 2 * math.pi * k / sides + rng.uniform(-0.25, 0.25)
        r = radius * rng.uniform(0.75, 1.15)
        pts.append(Vector((math.cos(a) * r, math.sin(a) * r, 0)))
        pts.append(Vector((math.cos(a) * r * 0.9, math.sin(a) * r * 0.9, -0.9)))
    apex = Vector((rng.uniform(-0.15, 0.15) * radius, rng.uniform(-0.15, 0.15) * radius, length))
    shoulder = [Vector((p.x * 0.55, p.y * 0.55, length * rng.uniform(0.45, 0.6))) for p in pts[::2][:2]]
    verts = [bm.verts.new(p) for p in pts + [apex] + shoulder]
    result = bmesh.ops.convex_hull(bm, input=verts)
    bmesh.ops.delete(bm, geom=[v for v in result["geom_interior"] if isinstance(v, bmesh.types.BMVert)], context="VERTS")
    bm.transform(Matrix.Translation(Vector(base)) @ align_z(direction))
    return bm


def bubble(at, radius, subdivisions=1):
    bm = new_bm()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=radius, matrix=Matrix.Translation(Vector(at)))
    return bm


def streak(points, width, normal_hint):
    """A thin double-sided ribbon of frost inside the ice."""
    bm = new_bm()
    pts = [Vector(p) for p in points]
    left, right = [], []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        side = t.cross(Vector(normal_hint)).normalized()
        w = width * (0.35 + 0.65 * math.sin(math.pi * (i + 0.5) / len(pts)))
        left.append(p + side * w)
        right.append(p - side * w)
    double_sided_strip(bm, left, right)
    return bm


def window_ring(centre, w, h, corner, depth, thickness, normal_y=-1, seg=4, prof=5):
    """A raised frosty frame round a window on a face (normal -Y or +Y): a rounded-rect loop with a half-round
    profile standing `depth` off the face, `thickness` wide."""
    bm = new_bm()
    outline = rounded_rect(w, h, corner, seg)  # (x, z) round the window
    rings = []
    n = len(outline)
    cx, cy, cz = centre
    for i, (x, z) in enumerate(outline):
        x0, z0 = outline[i - 1]
        x1, z1 = outline[(i + 1) % n]
        tx, tz = x1 - x0, z1 - z0
        length = math.hypot(tx, tz) or 1.0
        ox, oz = tz / length, -tx / length  # outward in the face plane (the outline runs counter-clockwise)
        ring = []
        for k in range(prof + 1):
            a = math.pi * k / prof  # 0 = outer edge, pi = inner edge
            r = math.cos(a) * thickness / 2
            d = math.sin(a) * depth
            ring.append(bm.verts.new((cx + x + ox * r, cy + normal_y * d, cz + z + oz * r)))
        rings.append(ring)
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(prof):
            face = (a[k], b[k], b[k + 1], a[k + 1]) if normal_y < 0 else (a[k], a[k + 1], b[k + 1], b[k])
            bm.faces.new(face)
    return bm


# ---------- cracks: lines on the shell's surface, grown stage by stage ----------

FACES = {  # bounding-box faces: (normal, right, up) as seen from outside
    "front": (Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))),
    "back": (Vector((0, 1, 0)), Vector((-1, 0, 0)), Vector((0, 0, 1))),
    "right": (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))),
    "left": (Vector((-1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))),
}
CRACK_WIDTH = (0.07, 0.1, 0.13, 0.16)  # half-widths by stage
CRACK_SEEDS = {  # stage: [(face, u, v, branches)] in -1..1 face coordinates (cracks start where the pick lands)
    1: [("front", -0.42, 0.5, 3), ("front", 0.48, -0.32, 3)],
    2: [("right", -0.3, 0.35, 3), ("left", 0.35, -0.1, 3), ("front", 0.1, 0.78, 2)],
    3: [("back", 0.2, 0.3, 3), ("front", -0.55, -0.55, 3), ("right", 0.4, -0.5, 2)],
    4: [("left", -0.4, 0.6, 3), ("back", -0.4, -0.4, 3), ("front", 0.62, 0.62, 2)],
}


def project(bvh, face, u, v, half):
    normal, right, up = FACES[face]
    origin = normal * (half[0] + 6) + right * u * half[0] + up * (H / 2 + v * half[1])
    hit = bvh.ray_cast(origin, -normal, 30)
    if hit[0] is None or hit[1].dot(normal) < 0.15:
        return None
    return hit[0], hit[1]


def grow_cracks(bvh, seed, half):
    """{stage: [[(point, normal), ...], ...]}: each stage's new crack lines (a branch carries on in later stages from
    where it stopped, so the lines join up)."""
    rng = random.Random(seed)
    branches = []  # dicts: face, u, v, angle, alive
    out = {s: [] for s in CRACK_SEEDS}
    step = 0.1  # in face units (about 0.6 studs)
    for stage in sorted(CRACK_SEEDS):
        for face, u, v, count in CRACK_SEEDS[stage]:
            start = rng.uniform(0, 2 * math.pi)
            for k in range(count):
                branches.append({"face": face, "u": u, "v": v, "angle": start + 2 * math.pi * k / count + rng.uniform(-0.4, 0.4), "alive": True})
        for b in list(branches):
            if not b["alive"]:
                continue
            first = project(bvh, b["face"], b["u"], b["v"], half)
            if not first:
                b["alive"] = False
                continue
            line = [first]
            segments = rng.randint(1, 3) + (1 if stage >= 3 else 0)
            for _ in range(segments):
                b["angle"] += rng.uniform(-0.45, 0.45)
                b["u"] += math.cos(b["angle"]) * step * rng.uniform(0.7, 1.2)
                b["v"] += math.sin(b["angle"]) * step * rng.uniform(0.7, 1.2)
                if abs(b["u"]) > 0.93 or abs(b["v"]) > 0.93:
                    b["alive"] = False
                    break
                hit = project(bvh, b["face"], b["u"], b["v"], half)
                if not hit:
                    b["alive"] = False
                    break
                line.append(hit)
                if rng.random() < 0.14 and len(branches) < 40:  # a fork
                    branches.append({"face": b["face"], "u": b["u"], "v": b["v"], "angle": b["angle"] + rng.choice((-1, 1)) * rng.uniform(0.6, 1.1), "alive": True, "born": stage})
            if len(line) >= 2:
                out[stage].append(line)
    return out


def crack_ribbon(line, half_width, lift=0.06):
    """A ribbon along a crack line, lying on the surface, tapering to its ends; u runs across it."""
    bm = new_bm()
    layer = bm.loops.layers.uv.verify()
    left, right = [], []
    n = len(line)
    for i, (p, normal) in enumerate(line):
        t = (line[min(i + 1, n - 1)][0] - line[max(i - 1, 0)][0])
        t = t.normalized() if t.length > 1e-6 else Vector((1, 0, 0))
        side = t.cross(normal).normalized()
        taper = 0.35 + 0.65 * min(1.0, i / 1.5, (n - 1 - i) / 1.5 + 0.35)
        w = half_width * taper
        base = p + normal * lift
        left.append(bm.verts.new(base + side * w))
        right.append(bm.verts.new(base - side * w))
    for i in range(n - 1):
        face = bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
        face.normal_update()
        if face.normal.dot(line[i][1]) < 0:
            face.normal_flip()
        for loop in face.loops:
            loop[layer].uv = crack_uv(0.0 if loop.vert in left else 1.0)
    return bm


def add_cracks(model, shell_obj, seed, coll, material):
    bm = bmesh.new()
    bm.from_mesh(shell_obj.data)
    bm.transform(shell_obj.matrix_world)
    bvh = BVHTree.FromBMesh(bm)
    bm.free()
    half = (W / 2, H / 2 * 0.98)
    lines = grow_cracks(bvh, seed, half)
    objs = []
    for stage, stage_lines in lines.items():
        m = IceMesh("%sCrack%d" % (model, stage))
        for line in stage_lines:
            _add_keep_uv(m, crack_ribbon(line, CRACK_WIDTH[stage - 1]))  # (the ribbon sets its own UVs)
        obj = m.finish(coll, material)
        if obj:
            objs.append(obj)
    return objs


def _add_keep_uv(m, piece):
    """Append a piece that already has its UVs (flat-shaded)."""
    before = len(m.bm.faces)
    temp = bpy.data.meshes.new("_ice_temp")
    piece.to_mesh(temp)
    piece.free()
    m.bm.from_mesh(temp)
    bpy.data.meshes.remove(temp)
    m.flat.update(range(before, len(m.bm.faces)))


# ---------- inner bubbles and frost streaks (kept out of the middle, where the creature is) ----------

def add_inner(inner, rng, inside, count=12, streaks=4):
    placed = 0
    tries = 0
    while placed < count and tries < 400:
        tries += 1
        x, y = rng.uniform(-0.42, 0.42) * W, rng.uniform(-0.42, 0.42) * W
        z = rng.uniform(0.06, 0.85) * H
        if max(abs(x), abs(y)) < 0.3 * W:  # the creature's column
            continue
        r = rng.uniform(0.14, 0.42)
        if not inside(Vector((x, y, z)), r + 0.3):
            continue
        inner.add(bubble((x, y, z), r, 1 if r < 0.3 else 2), "BubbleWhite")
        placed += 1
        if rng.random() < 0.5:  # a little trail of smaller ones above
            for k in range(rng.randint(1, 3)):
                rr = r * (0.55 - 0.12 * k)
                p = Vector((x + rng.uniform(-0.2, 0.2), y + rng.uniform(-0.2, 0.2), z + r + 0.35 + k * 0.45))
                if inside(p, rr + 0.3):
                    inner.add(bubble(p, rr, 1), "BubbleWhite")
    for _ in range(streaks):
        side = rng.choice(list(FACES))
        normal, right, up = FACES[side]
        u0 = rng.choice((-1, 1)) * rng.uniform(0.45, 0.8)
        z0 = rng.uniform(0.2, 0.75) * H
        depth = W / 2 - rng.uniform(0.9, 1.6)
        pts = []
        angle = rng.uniform(-1.0, 1.0)
        for k in range(5):
            pts.append(normal * depth + right * (u0 * W / 2 + math.cos(angle) * k * 0.8) + up * (z0 + math.sin(angle) * k * 0.8 + rng.uniform(-0.15, 0.15)))
        if all(inside(p, 0.25) for p in pts):
            inner.add(streak(pts, rng.uniform(0.18, 0.32), normal), "StreakWhite", recalc=False)


# ---------- the three options ----------

def option_b(coll, material):
    """Carved block."""
    rng = random.Random(22)
    name = "IceBlockB"
    shell, inner, snow, crystals = IceMesh(name + "Shell"), IceMesh(name + "Inner"), IceMesh(name + "Snow"), IceMesh(name + "Crystals")
    corner, edge = 1.4, 1.1
    shell.add(rounded_body((W, W, H), corner, edge, H / 2), body_uv(W / 2 - corner, W / 2 - corner, edge, H - edge))
    # the thick snow cap: a rounded slab overhanging the top, lumps on it, drips over the edges, icicles under it
    cap_z = H - 0.25
    snow.add(rounded_body((W + 1.0, W + 1.0, 1.9), corner + 0.4, 0.85, cap_z + 0.7), snow_uv)
    for k in range(7):
        a = k / 7 * 2 * math.pi + rng.uniform(-0.2, 0.2)
        r = rng.uniform(1.0, W * 0.3)
        snow.add(lump((math.cos(a) * r, math.sin(a) * r, cap_z + 1.5), (rng.uniform(1.5, 2.4), rng.uniform(1.5, 2.4), rng.uniform(0.6, 0.9)), 2, rng.uniform(0, 3)), snow_uv)
    snow.add(lump((0.3, -0.2, cap_z + 1.9), (2.8, 2.6, 1.0), 2), snow_uv)
    for side, (normal, right, up) in FACES.items():
        for k in range(3):
            along = rng.uniform(-0.75, 0.75) * (W / 2 - 1)
            at = normal * (W / 2 + 0.45) + right * along + Vector((0, 0, cap_z - 0.05))
            snow.add(drip(at, normal, rng.uniform(1.2, 2.2), rng.uniform(0.42, 0.6)), snow_uv)
        x = -W / 2 + 1.6
        while x < W / 2 - 1.4:
            if rng.random() < 0.75:
                base = normal * (W / 2 + 0.05) + right * (x + rng.uniform(-0.3, 0.3)) + Vector((0, 0, cap_z - 0.1))
                crystals.add(cone_down(base, rng.uniform(0.2, 0.32), rng.uniform(0.8, 2.2)), rng.choice(("CrystalPale", "IceBlue", "CrystalPale")), flat=True)
            x += rng.uniform(1.1, 1.8)
    # small crystals and snow chunks round the base (not in front of the middle: that's where you tap)
    for (cx, cy, count) in ((-1, 1, 3), (1, 1, 2), (1, -1, 3), (-1, -1, 2)):
        base = Vector((cx * (W / 2 + 0.2), cy * (W / 2 + 0.2), 0.1))
        for k in range(count):
            off = Vector((rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), 0))
            out = Vector((cx * rng.uniform(0.3, 0.8), cy * rng.uniform(0.3, 0.8), 1.0))
            crystals.add(crystal(base + off, out, rng.uniform(0.32, 0.55), rng.uniform(1.4, 2.8) * (1.25 if k == 0 else 1.0), twist=rng.uniform(0, 1)), crystal_uv, flat=True)
    for (x, y, s) in ((-W / 2 - 0.6, -1.5, 1.1), (W / 2 + 0.5, 1.8, 1.0), (-1.8, W / 2 + 0.7, 1.2), (W / 2 + 0.2, -W / 2 - 0.4, 0.8), (-W / 2 - 0.2, W / 2 + 0.1, 0.9)):
        snow.add(lump((x, y, 0.05), (s * 1.3, s * 1.1, s * 0.7), 2, rng.uniform(0, 3), floor=-0.4), snow_uv)

    def inside(p, margin):
        return max(abs(p.x), abs(p.y)) < W / 2 - margin and margin < p.z < H - margin

    add_inner(inner, rng, inside)
    return name, [shell, inner, snow, crystals], 202


def option_c(coll, material):
    """Crystal geode."""
    rng = random.Random(33)
    name = "IceBlockC"
    shell, inner, snow, glass, glow = IceMesh(name + "Shell"), IceMesh(name + "Inner"), IceMesh(name + "Snow"), IceMesh(name + "Glass"), IceMesh(name + "Glow")
    corner, edge = 0.9, 0.7
    shell.add(rounded_body((W, W, H), corner, edge, H / 2), body_uv(W / 2 - corner, W / 2 - corner, edge, H - edge, sides=6, front_back="S"))
    for normal_y in (-1, 1):  # the window's frosty frame, front and back
        shell.add(window_ring((0, normal_y * (W / 2 - 0.05), H * 0.47), W - 2.4, H * 0.76, 1.6, 0.42, 0.9, normal_y=normal_y), "RimFrost", recalc=False)
    # crystal clusters bursting out of the corners
    clusters = []
    for cx in (-1, 1):
        for cy in (-1, 1):
            clusters.append((Vector((cx * (W / 2 - 0.8), cy * (W / 2 - 0.8), H - 0.7)), Vector((cx * 0.9, cy * 0.9, 0.5)), 7, 0.9))
            clusters.append((Vector((cx * (W / 2 - 0.5), cy * (W / 2 - 0.5), 0.6)), Vector((cx * 0.9, cy * 0.9, 0.3)), 4, 0.7))
    for base, out, count, scale in clusters:
        out = out.normalized()
        for k in range(count):
            spread = Vector((rng.uniform(-0.55, 0.55), rng.uniform(-0.55, 0.55), rng.uniform(-0.3, 0.45)))
            direction = (out + spread * (0.4 if k == 0 else 1.0)).normalized()
            radius = rng.uniform(0.65, 1.0) * scale * (1.35 if k == 0 else 1.0)
            length = rng.uniform(1.5, 2.6) * scale * (1.5 if k == 0 else 1.0)
            twist = rng.uniform(0, 1)
            at = base + Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), rng.uniform(-0.5, 0.4)))
            glass.add(crystal(at, direction, radius, length, twist=twist, sink=1.2), lambda f, co: swatch_uv("CrystalGlass" if f.normal.z > -0.2 else "CrystalGlassDeep"), flat=True)
            if k < 3:
                glow.add(core(at, direction, radius * 0.5, length * 0.85, twist), "CrystalCyan", flat=True)
    # the snow cap, between the corner crystals
    cap_z = H - 0.2
    snow.add(rounded_body((W - 2.2, W - 2.2, 1.2), 1.8, 0.55, cap_z + 0.4), snow_uv)
    for k in range(5):
        a = k / 5 * 2 * math.pi + rng.uniform(-0.2, 0.2)
        r = rng.uniform(0.6, 2.4)
        snow.add(lump((math.cos(a) * r, math.sin(a) * r, cap_z + 0.95), (rng.uniform(1.4, 2.0), rng.uniform(1.4, 2.0), rng.uniform(0.5, 0.75)), 2, rng.uniform(0, 3)), snow_uv)
    for side, (normal, right, up) in FACES.items():
        for k in range(2):
            along = rng.uniform(-0.45, 0.45) * (W / 2 - 1)
            at = normal * (W / 2 - 0.9) + right * along + Vector((0, 0, cap_z + 0.1))
            snow.add(drip(at, normal, rng.uniform(0.9, 1.5), rng.uniform(0.35, 0.5)), snow_uv)

    def inside(p, margin):
        return max(abs(p.x), abs(p.y)) < W / 2 - margin and margin < p.z < H - margin

    add_inner(inner, rng, inside, count=10, streaks=3)
    return name, [shell, inner, snow, glass, glow], 303


def option_a(coll, material):
    """Faceted iceberg."""
    rng = random.Random(11)
    name = "IceBlockA"
    shell, inner, snow, crystals = IceMesh(name + "Shell"), IceMesh(name + "Inner"), IceMesh(name + "Snow"), IceMesh(name + "Crystals")
    # the berg: a convex hull of irregular rings, wide at the base, narrowing to a ridge
    sides = 8
    levels = [(0.0, 0.46), (0.14 * H, 0.5), (0.42 * H, 0.49), (0.68 * H, 0.45), (0.86 * H, 0.38), (0.95 * H, 0.28)]
    points = []
    for li, (z, share) in enumerate(levels):
        offset = rng.uniform(0, 2 * math.pi / sides)
        for k in range(sides if li < len(levels) - 1 else 4):
            count = sides if li < len(levels) - 1 else 4
            a = 2 * math.pi * k / count + offset + rng.uniform(-0.18, 0.18)
            r = W * share * rng.uniform(0.8, 1.08)
            # a squarish footprint, so it fills the plot's ice spot like the block did
            sq = 1 / max(abs(math.cos(a)), abs(math.sin(a))) ** 0.25
            zz = z + (rng.uniform(-0.07, 0.07) * H if 0 < li < len(levels) - 1 else 0)
            lean = Vector((0.35, -0.2, 0)) * (zz / H)  # the top sits a little off-centre, like a real berg
            points.append(Vector((math.cos(a) * r * sq, math.sin(a) * r * sq, zz)) + lean)
    bm = new_bm()
    verts = [bm.verts.new(p) for p in points]
    result = bmesh.ops.convex_hull(bm, input=verts)
    bmesh.ops.delete(bm, geom=[v for v in result["geom_interior"] if isinstance(v, bmesh.types.BMVert)], context="VERTS")
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(6), verts=bm.verts[:], edges=bm.edges[:])
    hull_points = [v.co.copy() for v in bm.verts]

    def berg_uv(face, co):
        c = face.calc_center_median()
        n = face.normal
        t = co.z / H
        if n.z > 0.5 or c.z > 0.82 * H:
            return column_uv(4 if (face.index % 3) else 0, t)  # the top and shoulders: frosty cyan
        if c.z < 0.13 * H or n.z < -0.3:
            return column_uv(0, t)  # the base: frosty, deep blue at the bottom
        if n.y < -0.35:
            return column_uv(2, t)  # the front: one clear blue (the creature reads through it whole)
        if n.y < 0.35:
            return column_uv((3, 5)[face.index % 2], t)  # the sides: equally clear, in cyan and violet-blue
        return column_uv((1, 2, 3)[face.index % 3], t)  # the back: clear and semi

    bm.faces.index_update()
    shell.add(bm, berg_uv, flat=True)
    # the snow cap: a soft hull over the top, lumps, drips down the facets
    top = [p for p in hull_points if p.z > 0.9 * H]
    cap = new_bm()
    cap_pts = [Vector((p.x * 1.1, p.y * 1.1, p.z - 0.5)) for p in top] + [Vector((p.x * 0.75, p.y * 0.75, p.z + 0.9)) for p in top]
    cv = [cap.verts.new(p) for p in cap_pts]
    res = bmesh.ops.convex_hull(cap, input=cv)
    bmesh.ops.delete(cap, geom=[v for v in res["geom_interior"] if isinstance(v, bmesh.types.BMVert)], context="VERTS")
    bmesh.ops.subdivide_edges(cap, edges=cap.edges[:], cuts=1, use_grid_fill=True, smooth=0.6)
    snow.add(cap, snow_uv)
    for k in range(4):
        a = k / 4 * 2 * math.pi + rng.uniform(-0.3, 0.3)
        r = rng.uniform(0.8, 2.0)
        snow.add(lump((math.cos(a) * r, math.sin(a) * r, 0.95 * H + 0.5), (rng.uniform(1.1, 1.6), rng.uniform(1.1, 1.6), rng.uniform(0.45, 0.7)), 2, rng.uniform(0, 3)), snow_uv)
    for p in top:
        if rng.random() < 0.8:
            n = Vector((p.x, p.y, 0)).normalized()
            snow.add(drip(Vector((p.x * 1.08, p.y * 1.08, p.z - 0.6)), n, rng.uniform(1.2, 2.2), rng.uniform(0.4, 0.6)), snow_uv)
    # jagged crystal spikes on top, leaning out
    for k in range(6):
        a = k / 6 * 2 * math.pi + rng.uniform(-0.35, 0.35)
        r = rng.uniform(1.4, 2.6) if k else 0.4
        base = Vector((math.cos(a) * r, math.sin(a) * r, 0.93 * H))
        out = Vector((math.cos(a) * rng.uniform(0.25, 0.55), math.sin(a) * rng.uniform(0.25, 0.55), 1.0))
        crystals.add(spike(base, out, rng.uniform(0.9, 1.3), rng.uniform(2.6, 3.6) * (1.25 if k == 0 else 1.0), rng), crystal_uv, flat=True)
    # jagged spikes jutting from the shoulders
    for a in (0.9, 2.4, 4.0, 5.5):
        base = Vector((math.cos(a) * W * 0.36, math.sin(a) * W * 0.36, 0.78 * H))
        crystals.add(spike(base, Vector((math.cos(a), math.sin(a), 0.8)), 0.75, rng.uniform(2.0, 2.8), rng), crystal_uv, flat=True)

    hull = new_bm()
    for p in hull_points:
        hull.verts.new(p)
    bmesh.ops.convex_hull(hull, input=hull.verts[:])
    bvh = BVHTree.FromBMesh(hull)
    hull.free()

    def inside(p, margin):
        loc, normal, _, dist = bvh.find_nearest(p)
        return loc is not None and (p - loc).dot(normal) < -margin

    add_inner(inner, rng, inside, count=12, streaks=4)
    return name, [shell, inner, snow, crystals], 101


# ---------- build, check, export ----------

coll = begin("IceBlock")
material = preview_material()
manifest = {"exportScale": EXPORT_SCALE, "height": H, "width": W, "atlas": "assets/textures/ice/IceBlueAtlas.png", "models": {}}
problems = []
os.makedirs(OUT, exist_ok=True)
for index, build in enumerate((option_a, option_b, option_c)):
    name, parts, crack_seed = build(coll, material)
    if ONLY and name not in ONLY:
        continue
    objs = [o for o in (p.finish(coll, material) for p in parts) if o]
    shell_obj = next(o for o in objs if o.name.endswith("Shell"))
    objs += add_cracks(name, shell_obj, crack_seed, coll, material)
    for o in objs:
        o.location.x = (index - 1) * 26.0
    bpy.context.view_layer.update()
    lo, hi = bounds(objs)
    tris = {o.name: triangles(o) for o in objs}
    total = sum(tris.values())
    info = {"meshes": tris, "triangles": total, "size": [round(hi.x - lo.x, 2), round(hi.z - lo.z, 2), round(hi.y - lo.y, 2)], "top": round(hi.z, 2)}
    if total > MAX_BLOCK_TRIS:
        problems.append("%s has %d triangles (budget %d)" % (name, total, MAX_BLOCK_TRIS))
    problems += check(objs)
    manifest["models"][name] = info
    print(name, json.dumps(info))
    if EXPORT and not problems:
        for o in objs:
            o.location.x = 0
        bpy.context.view_layer.update()
        export_fbx(objs, os.path.join(OUT, name + ".fbx"))
        for o in objs:
            o.location.x = (index - 1) * 26.0
if EXPORT and not problems:
    with open(os.path.join(OUT, "ice_manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=1, sort_keys=True)
for p in problems:
    print("PROBLEM:", p)
print("ICE_BLOCK_DONE", "problems:", len(problems))
