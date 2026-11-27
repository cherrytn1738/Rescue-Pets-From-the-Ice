# ice_block.py - the ice block's look (the carved block, option B of the redesign), in the buildings' smooth toy
# style: a rounded, bevelled block with frosty edges and glints, colour deepening from the top down, a snow cap with
# icicles, small crystals and snow round the base. One kit for every layer and block:
#   IceShell, IceCrack1-4          the body (transparent through the atlas's alpha) and its crack lines per stage
#   IceV<1-3>Snow/Crystals/Inner   three shape variants (snow cap and drips; icicles and base crystals; bubbles and
#                                  frost streaks), picked at random per block
#   IceDrifts                      Fresh Snow: snow banked round the base (instead of crystals)
#   IceDenseBubbles                Ancient Ice: many trapped bubbles (instead of the variant's inner)
#   IceCrystalClusters             Crystal Ice: faceted clusters on the corners
#   IceVeins                       Primordial Ice and the Frozen Core: glowing veins (Neon, coloured in game)
#   IceMythicGlass/Glow            the Mythic Block (bought with Robux): glowing crystal clusters out of the corners
#   IcePiece01-11                  the pre-cut shatter pieces;  IceChunk1-3  chunks that break off at the crack stages
# Built at the level-1 size (14 studs tall, 11.2 wide and deep; the game scales it with the level), pivot on the
# ground at the middle, front -Y (Roblox -Z). Every mesh uses the same UVs on a per-layer atlas
# (tools/make_ice_textures.py: keep the regions below in step with it), so a layer is a texture swap. A block shows
# under 5k triangles (checked per combination below; the plaza can show 8).
#   blender -b --factory-startup --python tools/blender/ice_block.py
#   (or the Blender MCP: REPO = r"..."; exec(open(REPO + r"\tools\blender\ice_block.py", encoding="utf-8").read()))
# Out: store-assets/ice-block/IceBlockKit.fbx, ice_manifest.json (meshes, triangles, per-block totals)
import ast, json, math, os, random, sys
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

if "REPO" not in globals():
    REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT_SCALE = 0.1  # arrives in Studio at 10x, like the plot parts (build_templates.luau scales it back)
exec(open(os.path.join(REPO, "tools", "blender", "model_helpers.py"), encoding="utf-8").read())
OUT = os.path.join(REPO, "store-assets", "ice-block")
ATLAS_PATH = os.path.join(REPO, "assets", "textures", "ice", "IceBlueIceAtlas.png")  # (Blender preview only)
H, W = 14.0, 11.2  # the level-1 block (LayerConfig.Block.HeightAtFirstLevel, IceLooks.BlockWidthShare)
MAX_BLOCK_TRIS = 5000
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
    image = bpy.data.images.get("IceBlueIceAtlas") or bpy.data.images.load(ATLAS_PATH)
    image.name = "IceBlueIceAtlas"
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


# ---------- the kit: look B for every layer ----------

CORNER, EDGE = 1.4, 1.1  # the body's rounded corners and edges


def inside_body(p, margin):
    return max(abs(p.x), abs(p.y)) < W / 2 - margin and margin < p.z < H - margin


def body_bm():
    return rounded_body((W, W, H), CORNER, EDGE, H / 2)


BODY_UV = body_uv(W / 2 - CORNER, W / 2 - CORNER, EDGE, H - EDGE)


def snow_cap(snow, rng, kind):
    """Three snow caps: 1 a thick slab with lumps, 2 a cap drifted to one side with long drips, 3 a two-tier pillow."""
    cap_z = H - 0.25
    if kind == 1:
        snow.add(rounded_body((W + 1.0, W + 1.0, 1.9), CORNER + 0.4, 0.85, cap_z + 0.7), snow_uv)
        for k in range(7):
            a = k / 7 * 2 * math.pi + rng.uniform(-0.2, 0.2)
            r = rng.uniform(1.0, W * 0.3)
            snow.add(lump((math.cos(a) * r, math.sin(a) * r, cap_z + 1.5), (rng.uniform(1.5, 2.4), rng.uniform(1.5, 2.4), rng.uniform(0.6, 0.9)), 2, rng.uniform(0, 3)), snow_uv)
        snow.add(lump((0.3, -0.2, cap_z + 1.9), (2.8, 2.6, 1.0), 2), snow_uv)
        drips, length = 3, (1.2, 2.2)
    elif kind == 2:
        snow.add(rounded_body((W + 0.8, W + 0.8, 1.5), CORNER + 0.3, 0.7, cap_z + 0.55), snow_uv)
        snow.add(lump((-W * 0.22, W * 0.12, cap_z + 1.5), (3.6, 3.2, 1.5), 2, 0.4), snow_uv)  # the drift piled on one side
        snow.add(lump((-W * 0.05, W * 0.2, cap_z + 2.2), (2.2, 2.0, 0.9), 2, 1.1), snow_uv)
        for k in range(3):
            a = rng.uniform(-1.0, 1.0)
            snow.add(lump((math.cos(a) * 2.8, math.sin(a) * 2.8 - 1.0, cap_z + 1.2), (1.6, 1.5, 0.6), 2, rng.uniform(0, 3)), snow_uv)
        drips, length = 4, (1.4, 2.8)
    else:
        snow.add(rounded_body((W + 0.9, W + 0.9, 1.4), CORNER + 0.4, 0.65, cap_z + 0.5), snow_uv)
        snow.add(rounded_body((W - 2.4, W - 2.6, 1.3), CORNER, 0.6, cap_z + 1.6), snow_uv)  # a second, smaller pillow on top
        for k in range(4):
            a = k / 4 * 2 * math.pi + rng.uniform(-0.3, 0.3)
            snow.add(lump((math.cos(a) * 2.0, math.sin(a) * 2.0, cap_z + 2.3), (1.4, 1.3, 0.55), 2, rng.uniform(0, 3)), snow_uv)
        drips, length = 2, (1.0, 1.8)
    for side, (normal, right, up) in FACES.items():
        for k in range(drips):
            if kind == 2 and rng.random() < 0.35:
                continue
            along = rng.uniform(-0.75, 0.75) * (W / 2 - 1)
            at = normal * (W / 2 + 0.45) + right * along + Vector((0, 0, cap_z - 0.05))
            snow.add(drip(at, normal, rng.uniform(*length), rng.uniform(0.42, 0.6)), snow_uv)


def icicles(crystals, rng, kind):
    """Icicles under the cap's edge: 1 even, 2 fewer and longer, 3 short and dense."""
    cap_z = H - 0.25
    spacing, lengths, chance = {1: ((1.1, 1.8), (0.8, 2.2), 0.75), 2: ((1.6, 2.4), (1.2, 2.8), 0.7), 3: ((0.8, 1.2), (0.5, 1.3), 0.85)}[kind]
    for side, (normal, right, up) in FACES.items():
        x = -W / 2 + 1.6
        while x < W / 2 - 1.4:
            if rng.random() < chance:
                base = normal * (W / 2 + 0.05) + right * (x + rng.uniform(-0.3, 0.3)) + Vector((0, 0, cap_z - 0.1))
                crystals.add(cone_down(base, rng.uniform(0.2, 0.32), rng.uniform(*lengths)), rng.choice(("CrystalPale", "IceBlue", "CrystalPale")), flat=True)
            x += rng.uniform(*spacing)


def base_decor(crystals, snow, rng, kind):
    """Small crystals and snow chunks round the base (never in front of the middle, where you tap)."""
    corners = {1: ((-1, 1, 3), (1, 1, 2), (1, -1, 3), (-1, -1, 2)), 2: ((1, 1, 4), (-1, -1, 4)), 3: ((-1, 1, 2), (1, 1, 3), (1, -1, 2))}[kind]
    for (cx, cy, count) in corners:
        base = Vector((cx * (W / 2 + 0.2), cy * (W / 2 + 0.2), 0.1))
        for k in range(count):
            off = Vector((rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), 0))
            out = Vector((cx * rng.uniform(0.3, 0.8), cy * rng.uniform(0.3, 0.8), 1.0))
            crystals.add(crystal(base + off, out, rng.uniform(0.32, 0.55), rng.uniform(1.4, 2.8) * (1.25 if k == 0 else 1.0), twist=rng.uniform(0, 1)), crystal_uv, flat=True)
    lumps = {1: ((-W / 2 - 0.6, -1.5, 1.1), (W / 2 + 0.5, 1.8, 1.0), (-1.8, W / 2 + 0.7, 1.2), (W / 2 + 0.2, -W / 2 - 0.4, 0.8), (-W / 2 - 0.2, W / 2 + 0.1, 0.9)),
             2: ((-W / 2 - 0.7, 0.5, 1.5), (-W / 2 - 0.3, 2.6, 1.0), (W / 2 + 0.4, -2.0, 0.9)),
             3: ((W / 2 + 0.6, 0.0, 1.2), (1.5, W / 2 + 0.6, 1.0), (-W / 2 - 0.4, -2.8, 0.9), (-2.5, W / 2 + 0.4, 0.8))}[kind]
    for (x, y, s) in lumps:
        snow.add(lump((x, y, 0.05), (s * 1.3, s * 1.1, s * 0.7), 2, rng.uniform(0, 3), floor=-0.4), snow_uv)


def drifts(snow, rng):
    """Fresh Snow: soft drifts banked round the whole base instead of crystals."""
    for side, (normal, right, up) in FACES.items():
        for k in range(3):
            along = (k - 1) * (W / 3) + rng.uniform(-0.6, 0.6)
            at = normal * (W / 2 + 0.3) + right * along
            snow.add(lump((at.x, at.y, 0.1), (rng.uniform(1.6, 2.2) if abs(normal.x) < 0.5 else 1.4, rng.uniform(1.6, 2.2) if abs(normal.y) < 0.5 else 1.4, rng.uniform(0.9, 1.4)), 2, rng.uniform(0, 3), floor=-0.4), snow_uv)


def dense_bubbles(inner, rng):
    """Ancient Ice: many trapped bubbles in rising strings, round the creature's column."""
    add_inner(inner, rng, inside_body, count=24, streaks=2)


def crystal_clusters(crystals, rng):
    """Crystal Ice: faceted crystal clusters on the top corners and the back of the base (never over the front)."""
    for (cx, cy, z, out, count, scale) in ((-1, -1, H - 0.4, (-0.8, -0.6, 0.9), 4, 1.0), (1, 1, H - 0.4, (0.8, 0.8, 0.9), 4, 1.0),
                                           (-1, 1, H - 0.4, (-0.7, 0.8, 1.0), 3, 0.85), (1, -1, H - 0.6, (0.9, -0.4, 0.8), 3, 0.8),
                                           (1, 1, 0.4, (0.8, 0.7, 0.35), 3, 0.8), (-1, 1, 0.4, (-0.8, 0.7, 0.35), 3, 0.75)):
        base = Vector((cx * (W / 2 - 0.6), cy * (W / 2 - 0.6), z))
        out = Vector(out).normalized()
        for k in range(count):
            spread = Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(-0.2, 0.4)))
            direction = (out + spread * (0.4 if k == 0 else 1.0)).normalized()
            crystals.add(crystal(base + Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 0)), direction,
                                 rng.uniform(0.45, 0.75) * scale * (1.3 if k == 0 else 1.0), rng.uniform(1.4, 2.4) * scale * (1.4 if k == 0 else 1.0),
                                 twist=rng.uniform(0, 1), sink=1.0), crystal_uv, flat=True)


def veins(glow, rng):
    """Primordial Ice and the Frozen Core: glowing veins inside, along the walls and corners (the front's middle stays
    clear for the creature). Neon in game, coloured by the layer."""
    for k in range(9):
        side = ("left", "right", "back", "left", "right", "back", "front", "front", "back")[k]
        normal, right, up = FACES[side]
        u = rng.uniform(-0.85, 0.85) if side != "front" else rng.choice((-1, 1)) * rng.uniform(0.62, 0.86)
        p = normal * (W / 2 - rng.uniform(0.7, 1.4)) + right * (u * W / 2) + Vector((0, 0, rng.uniform(0.1, 0.4) * H))
        points = [p.copy()]
        heading = rng.uniform(-0.6, 0.6)
        for _ in range(rng.randint(7, 11)):
            heading += rng.uniform(-0.5, 0.5)
            step = right * math.sin(heading) * 0.9 + Vector((0, 0, math.cos(heading) * 0.9))
            q = points[-1] + step
            q.x = max(-W / 2 + 0.6, min(W / 2 - 0.6, q.x))
            q.y = max(-W / 2 + 0.6, min(W / 2 - 0.6, q.y))
            if q.z > H - 0.8:
                break
            points.append(q)
        if len(points) >= 3:
            bm = new_bm()
            sweep(bm, points, rng.uniform(0.08, 0.13), segments=4, radius_end=0.03)
            glow.add(bm, "White")
            # a branch or two
            for _ in range(rng.randint(0, 2)):
                start = points[rng.randint(1, len(points) - 2)]
                branch = [start, start + right * rng.uniform(-1, 1) + Vector((0, 0, rng.uniform(0.6, 1.2))),
                          start + right * rng.uniform(-1.6, 1.6) + Vector((0, 0, rng.uniform(1.2, 2.2)))]
                bm = new_bm()
                sweep(bm, branch, 0.06, segments=4, radius_end=0.025)
                glow.add(bm, "White")


def mythic_clusters(glass, glow, rng):
    """The Mythic Block (bought with Robux): option C's glowing crystal clusters bursting out of the corners."""
    clusters = []
    for cx in (-1, 1):
        for cy in (-1, 1):
            clusters.append((Vector((cx * (W / 2 - 0.8), cy * (W / 2 - 0.8), H - 0.7)), Vector((cx * 0.9, cy * 0.9, 0.5)), 5, 0.95))
            clusters.append((Vector((cx * (W / 2 - 0.5), cy * (W / 2 - 0.5), 0.6)), Vector((cx * 0.9, cy * 0.9, 0.3)), 3, 0.7))
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


def shatter_pieces(coll, material, rng, count=11):
    """The block cut into its own pieces (Voronoi cells of random seeds, each cut out of the convex body): the outer
    faces keep the shell's look, the broken faces are frosty. Each piece is its own mesh, flung apart on a rescue."""
    seeds = []
    while len(seeds) < count:
        p = Vector((rng.uniform(-0.4, 0.4) * W, rng.uniform(-0.4, 0.4) * W, rng.uniform(0.08, 0.92) * H))
        if all((p - q).length > 3.2 for q in seeds):
            seeds.append(p)
    source = body_bm()
    bvh = BVHTree.FromBMesh(source)
    objs = []
    for i, s in enumerate(seeds):
        bm = source.copy()
        for j, t in enumerate(seeds):
            if i == j:
                continue
            n = (t - s).normalized()
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(s + t) / 2, plane_no=n, clear_outer=True)
        points = [v.co.copy() for v in bm.verts]
        bm.free()
        if len(points) < 4:
            continue
        piece = new_bm()
        for p in points:
            piece.verts.new(p)
        result = bmesh.ops.convex_hull(piece, input=piece.verts[:])
        bmesh.ops.delete(piece, geom=[v for v in result["geom_interior"] if isinstance(v, bmesh.types.BMVert)], context="VERTS")
        bmesh.ops.dissolve_limit(piece, angle_limit=math.radians(2), verts=piece.verts[:], edges=piece.edges[:])

        def piece_uv(face, co, bvh=bvh):
            c = face.calc_center_median()
            loc, normal, _, dist = bvh.find_nearest(c)
            if loc is not None and dist < 0.05 and normal.dot(face.normal) > 0.8:
                return BODY_UV(face, co)  # an outer face: the shell
            return swatch_uv("Fracture" if face.normal.z > 0 else "FractureDeep")  # a broken face

        m = IceMesh("IcePiece%02d" % (len(objs) + 1))
        m.add(piece, piece_uv, flat=True)
        obj = m.finish(coll, material)
        if obj:
            objs.append(obj)
    source.free()
    return objs


def chunks(coll, material, rng):
    """Three small chunks at the top edges: one or two break off and fall at each crack stage."""
    objs = []
    for i, at in enumerate((Vector((-W / 2 + 1.6, -W / 2 + 0.4, H - 0.9)), Vector((W / 2 - 0.4, 1.4, H - 1.4)), Vector((1.2, -W / 2 + 0.4, H - 1.1)))):
        bm = new_bm()
        for _ in range(12):
            d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
            if d.length > 0:
                bm.verts.new(at + d.normalized() * rng.uniform(0.55, 0.95))
        result = bmesh.ops.convex_hull(bm, input=bm.verts[:])
        bmesh.ops.delete(bm, geom=[v for v in result["geom_interior"] if isinstance(v, bmesh.types.BMVert)], context="VERTS")
        m = IceMesh("IceChunk%d" % (i + 1))
        m.add(bm, lambda f, co: swatch_uv("Fracture" if f.normal.z > 0.2 else ("RimFrost" if f.normal.z > -0.3 else "FractureDeep")), flat=True)
        objs.append(m.finish(coll, material))
    return objs


# ---------- build, check, export ----------

coll = begin("IceBlock")
material = preview_material()
rng = random.Random(22)
shell = IceMesh("IceShell")
shell.add(body_bm(), BODY_UV)
parts = [shell]
for kind in (1, 2, 3):
    snow, crystals, inner = IceMesh("IceV%dSnow" % kind), IceMesh("IceV%dCrystals" % kind), IceMesh("IceV%dInner" % kind)
    vr = random.Random(100 + kind)
    snow_cap(snow, vr, kind)
    icicles(crystals, vr, kind)
    base_decor(crystals, snow, vr, kind)
    add_inner(inner, vr, inside_body, count=12, streaks=4)
    parts += [snow, crystals, inner]
extras = {"Drifts": IceMesh("IceDrifts"), "DenseBubbles": IceMesh("IceDenseBubbles"), "CrystalClusters": IceMesh("IceCrystalClusters"),
          "Veins": IceMesh("IceVeins"), "MythicGlass": IceMesh("IceMythicGlass"), "MythicGlow": IceMesh("IceMythicGlow")}
drifts(extras["Drifts"], random.Random(201))
dense_bubbles(extras["DenseBubbles"], random.Random(202))
crystal_clusters(extras["CrystalClusters"], random.Random(203))
veins(extras["Veins"], random.Random(204))
mythic_clusters(extras["MythicGlass"], extras["MythicGlow"], random.Random(33))
parts += list(extras.values())
objs = [o for o in (p.finish(coll, material) for p in parts) if o]
shell_obj = next(o for o in objs if o.name == "IceShell")
objs += add_cracks("Ice", shell_obj, 202, coll, material)
objs += shatter_pieces(coll, material, random.Random(7))
objs += chunks(coll, material, random.Random(8))
bpy.context.view_layer.update()
tris = {o.name: triangles(o) for o in objs}


def block_total(names):
    return sum(tris.get(n, 0) for n in names)


body = ["IceShell", "IceCrack1", "IceCrack2", "IceCrack3", "IceCrack4"]
totals = {}
for kind in (1, 2, 3):
    v = ["IceV%dSnow" % kind, "IceV%dCrystals" % kind, "IceV%dInner" % kind]
    totals["V%d" % kind] = block_total(body + v)
    totals["V%d+Veins" % kind] = block_total(body + v + ["IceVeins"])
    totals["V%d+Clusters" % kind] = block_total(body + v + ["IceCrystalClusters"])
    totals["V%d+Bubbles" % kind] = block_total(body + ["IceV%dSnow" % kind, "IceV%dCrystals" % kind, "IceDenseBubbles"])
    totals["V%dMythic" % kind] = block_total(body + ["IceV%dSnow" % kind, "IceV%dInner" % kind, "IceMythicGlass", "IceMythicGlow"])
problems = check(objs)
for name, total in totals.items():
    if total > MAX_BLOCK_TRIS:
        problems.append("a %s block has %d triangles (budget %d)" % (name, total, MAX_BLOCK_TRIS))
lo, hi = bounds(objs)
manifest = {"exportScale": EXPORT_SCALE, "height": H, "width": W, "meshes": tris, "blockTotals": totals,
            "pieces": sum(1 for n in tris if n.startswith("IcePiece")), "top": round(hi.z, 2)}
print(json.dumps({"blockTotals": totals, "pieces": manifest["pieces"]}))
if EXPORT and not problems:
    os.makedirs(OUT, exist_ok=True)
    export_fbx(objs, os.path.join(OUT, "IceBlockKit.fbx"))
    with open(os.path.join(OUT, "ice_manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=1, sort_keys=True)
for p in problems:
    print("PROBLEM:", p)
print("ICE_BLOCK_DONE", "problems:", len(problems))
