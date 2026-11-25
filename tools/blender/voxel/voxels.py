# voxels.py - stud-voxel buildings (the lihfolk-stud-voxel look, STYLE TEST): models on a fixed voxel grid,
# meshed into one mesh per colour with the Roblox stud tiled across every face.
#
# The grid: VOXEL = 0.5 studs, anchored at the pad centre (voxel edges on multiples of 0.5 studs), Blender axes
# (x right, y back: the front -Y faces the ice, z up). One Roblox stud (the pets' Studs surface: one stud per
# stud) covers 2 x 2 voxels: the stud texture's UVs run in world studs, so studs line up across every face and
# every model, like the skill's "one continuous model-wide grid" rule.
#
# Colours are the building palette's swatch names (building_kit.SWATCHES), so the test keeps the approved
# palette. Glowing voxels go to separate "...Glow" meshes (Neon in game, no studs).
#
# Load inside Blender after framework.py (it provides SWATCHES, swatch_rgb, bpy helpers):
#     exec(open(os.path.join(REPO, "tools", "blender", "voxel", "voxels.py"), encoding="utf-8").read())
import math, os, json
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

VOXEL = 0.5         # studs per voxel
STUD_TILE = 8       # the stud image (assets/textures/StudOverlay.png) holds 8 x 8 studs: UV = studs / 8
MESH_QUADS = 4800   # a colour mesh over this many quads is split (Roblox: 20k triangles a mesh; ours stay under 10k)
STUD_IMAGE = os.path.join(REPO, "assets", "textures", "StudOverlay.png")


# ---------- the grid ----------

class VGrid:
    """A box of voxels from lo to hi (studs). col: 0 = empty, else 1 + an index into names; glow: Neon."""

    def __init__(self, lo, hi, voxel=VOXEL):
        v = voxel
        self.v = v
        self.i0 = np.floor(np.array(lo, float) / v + 1e-6).astype(int) - 1  # (a free voxel all round)
        self.i1 = np.ceil(np.array(hi, float) / v - 1e-6).astype(int) + 1
        self.shape = tuple(int(n) for n in self.i1 - self.i0)
        self.col = np.zeros(self.shape, np.int16)
        self.glow = np.zeros(self.shape, bool)
        self.names = []
        axes = [(np.arange(self.i0[k], self.i1[k]) + 0.5) * v for k in range(3)]
        self.X, self.Y, self.Z = np.meshgrid(*axes, indexing="ij")

    def cid(self, name):
        if name not in self.names:
            SWATCH_INDEX[name]  # (a palette name, or KeyError)
            self.names.append(name)
        return self.names.index(name) + 1

    # -- writing --
    def put(self, mask, name, glow=False):
        self.col[mask] = self.cid(name)
        self.glow[mask] = glow
        return mask

    def cut(self, mask):
        self.col[mask] = 0
        self.glow[mask] = False

    def paint(self, mask, name, glow=False):
        """Recolours voxels already there (markings, stripes)."""
        m = mask & (self.col > 0)
        self.put(m, name, glow)
        return m

    def filled(self):
        return self.col > 0

    # -- shapes: each returns a mask of voxel centres inside it --
    def box(self, x0, x1, y0, y1, z0, z1):
        return (self.X >= x0) & (self.X < x1) & (self.Y >= y0) & (self.Y < y1) & (self.Z >= z0) & (self.Z < z1)

    def cbox(self, c, size):
        """A box centred at c (x, y, z) with full sizes (sx, sy, sz)."""
        return self.box(c[0] - size[0] / 2, c[0] + size[0] / 2, c[1] - size[1] / 2, c[1] + size[1] / 2, c[2] - size[2] / 2, c[2] + size[2] / 2)

    def obox(self, c, size, x_axis=(1, 0, 0), y_axis=(0, 1, 0)):
        """A turned box: centre c, full sizes along its own axes x_axis, y_axis and their cross."""
        ax = Vector(x_axis).normalized()
        ay = (Vector(y_axis) - ax * ax.dot(Vector(y_axis))).normalized()
        az = ax.cross(ay)
        dx, dy, dz = self.X - c[0], self.Y - c[1], self.Z - c[2]
        m = np.ones(self.shape, bool)
        for a, s in ((ax, size[0]), (ay, size[1]), (az, size[2])):
            m &= np.abs(dx * a.x + dy * a.y + dz * a.z) <= s / 2
        return m

    def oellipsoid(self, c, r, x_axis=(1, 0, 0), y_axis=(0, 1, 0)):
        """A turned ellipsoid: centre c, radii r along its own axes x_axis, y_axis and their cross."""
        ax = Vector(x_axis).normalized()
        ay = (Vector(y_axis) - ax * ax.dot(Vector(y_axis))).normalized()
        az = ax.cross(ay)
        dx, dy, dz = self.X - c[0], self.Y - c[1], self.Z - c[2]
        total = np.zeros(self.shape)
        for a, s in ((ax, r[0]), (ay, r[1]), (az, r[2])):
            total += ((dx * a.x + dy * a.y + dz * a.z) / s) ** 2
        return total <= 1.0

    def ellipsoid(self, c, r):
        return ((self.X - c[0]) / r[0]) ** 2 + ((self.Y - c[1]) / r[1]) ** 2 + ((self.Z - c[2]) / r[2]) ** 2 <= 1.0

    def sphere(self, c, r):
        return self.ellipsoid(c, (r, r, r))

    def _seg(self, p0, p1):
        p0, p1 = np.array(p0, float), np.array(p1, float)
        d = p1 - p0
        L2 = float(d @ d) or 1e-9
        t = ((self.X - p0[0]) * d[0] + (self.Y - p0[1]) * d[1] + (self.Z - p0[2]) * d[2]) / L2
        tc = np.clip(t, 0, 1)
        dist = np.sqrt((self.X - p0[0] - tc * d[0]) ** 2 + (self.Y - p0[1] - tc * d[1]) ** 2 + (self.Z - p0[2] - tc * d[2]) ** 2)
        return t, dist

    def cyl(self, p0, p1, r0, r1=None, caps=False):
        """A cylinder (or a cone/frustum: r0 at p0 to r1 at p1) between two points; flat ends unless caps."""
        r1 = r0 if r1 is None else r1
        t, dist = self._seg(p0, p1)
        r = r0 + (r1 - r0) * np.clip(t, 0, 1)
        inside = dist <= r
        return inside if caps else inside & (t >= 0) & (t <= 1)

    def zcyl(self, cx, cy, r, z0, z1, r1=None):
        return self.cyl((cx, cy, z0), (cx, cy, z1), r, r1)

    def tube(self, points, r, r_end=None):
        """A chain of capped cylinders through points (arms, hoses, necks, tails)."""
        m = np.zeros(self.shape, bool)
        n = len(points) - 1
        for i in range(n):
            ra = r + ((r_end if r_end is not None else r) - r) * i / n
            rb = r + ((r_end if r_end is not None else r) - r) * (i + 1) / n
            m |= self.cyl(points[i], points[i + 1], ra, rb, caps=True)
        return m

    def ring(self, c, axis, R, r):
        """A torus round axis."""
        a = np.array(axis, float) / np.linalg.norm(axis)
        dx, dy, dz = self.X - c[0], self.Y - c[1], self.Z - c[2]
        h = dx * a[0] + dy * a[1] + dz * a[2]
        rad = np.sqrt(np.maximum(dx * dx + dy * dy + dz * dz - h * h, 0))
        return (rad - R) ** 2 + h * h <= r * r

    def disc(self, c, axis, R, thick, r_in=0.0):
        """A flat disc (or washer from r_in) round axis, thick along it."""
        a = np.array(axis, float) / np.linalg.norm(axis)
        dx, dy, dz = self.X - c[0], self.Y - c[1], self.Z - c[2]
        h = dx * a[0] + dy * a[1] + dz * a[2]
        rad = np.sqrt(np.maximum(dx * dx + dy * dy + dz * dz - h * h, 0))
        return (np.abs(h) <= thick / 2) & (rad <= R) & (rad >= r_in)

    def lathe(self, cx, cy, profile):
        """Round about the z axis at (cx, cy): profile = [(r, z), ...] with rising z (radius by height)."""
        rs = np.array([p[0] for p in profile], float)
        zs = np.array([p[1] for p in profile], float)
        r = np.interp(self.Z, zs, rs, left=-1, right=-1)
        return np.hypot(self.X - cx, self.Y - cy) <= r

    def surface(self, mask):
        """The voxels of mask that touch empty space (the visible skin)."""
        inner = mask.copy()
        for axis in range(3):
            for s in (1, -1):
                inner &= np.roll(mask, s, axis)
        return mask & ~inner

    # -- characters --
    def front_y(self, x, z):
        """The front-most (lowest y) filled voxel centre at x, z (None if the column is empty)."""
        i = int(round(x / self.v - 0.5)) - self.i0[0]
        k = int(round(z / self.v - 0.5)) - self.i0[2]
        if not (0 <= i < self.shape[0] and 0 <= k < self.shape[2]):
            return None
        col = np.nonzero(self.col[i, :, k])[0]
        return None if len(col) == 0 else (col[0] + self.i0[1] + 0.5) * self.v

    def eye(self, x, z, r, iris="AuroraCyan", look=(0.0, 0.0), glow_iris=False, out=1):
        """A cartoon eye on the front face at (x, z), as on the pets: a dark outline, a big coloured iris, a
        dark pupil and two white shines (a big one upper left, a small one lower right), standing `out`
        voxels proud of the face."""
        y = self.front_y(x, z)
        if y is None:
            return
        v = self.v
        d = np.hypot(self.X - x, self.Z - z)
        disc = (d <= r) & (self.col > 0) & (self.Y < y + 3 * v)
        yf = float(self.Y[disc].min()) if disc.any() else y  # the most forward voxel over the whole disc
        y0 = yf - out * v - v * 0.5
        slab = (self.Y >= y0) & (self.Y < y + v * 0.5)
        front = slab & (self.Y < y0 + v)
        self.put(slab & (d <= r), "EyeDark")
        self.put(front & (d <= r * 0.78), iris, glow_iris)
        px, pz = x + look[0] * r * 0.3, z + look[1] * r * 0.3
        self.put(front & (np.hypot(self.X - px, self.Z - pz) <= r * 0.32), "EyeDark")
        big = max(v, round(r * 0.3 / v) * v)
        sx, sz = px - r * 0.22, pz + r * 0.22
        self.put(front & (self.X >= sx - big) & (self.X < sx) & (self.Z >= sz) & (self.Z < sz + big), "EyeWhite")
        self.put(front & (np.abs(self.X - (px + r * 0.3)) < v * 0.5) & (np.abs(self.Z - (pz - r * 0.3)) < v * 0.5), "EyeWhite")


# ---------- voxelizing existing meshes (style B) ----------

def swatch_at(u, v):
    col = min(PALETTE_COLUMNS - 1, max(0, int(u * PALETTE_COLUMNS)))
    row = min(PALETTE_ROWS - 1, max(0, int((1 - v) * PALETTE_ROWS)))
    return SWATCHES[row * PALETTE_COLUMNS + col][0]


def voxelize(objs, voxel=VOXEL, shell=0.5, grid=None):
    """A VGrid of the meshes objs (world space): voxels within shell*voxel of a surface take that surface's
    palette colour (and glow, from a "...Glow" mesh); voxels closed in by them are filled. With grid, the
    voxels are added to it."""
    bm = bmesh.new()
    info = []
    for o in objs:
        if o.type != "MESH" or not o.data.polygons:
            continue
        tmp = bmesh.new()
        tmp.from_mesh(o.data)
        tmp.transform(o.matrix_world)
        uv = tmp.loops.layers.uv.active
        glow = o.name.endswith("Glow")
        for f in tmp.faces:
            u, v = f.loops[0][uv].uv if uv else (0.5, 0.5)
            info.append((swatch_at(u, v), glow))
        me = bpy.data.meshes.new("_vox_tmp")
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    bm.faces.ensure_lookup_table()
    pts = [v.co for v in bm.verts]
    lo = [min(p[k] for p in pts) for k in range(3)]
    hi = [max(p[k] for p in pts) for k in range(3)]
    tree = BVHTree.FromBMesh(bm)
    g = grid or VGrid(lo, hi, voxel)
    near = np.zeros(g.shape, bool)
    reach = shell * voxel
    ii = np.nonzero((g.X >= lo[0] - voxel) & (g.X <= hi[0] + voxel) & (g.Y >= lo[1] - voxel) & (g.Y <= hi[1] + voxel)
                    & (g.Z >= lo[2] - voxel) & (g.Z <= hi[2] + voxel))
    cids, glows = {}, np.zeros(g.shape, bool)
    colour = np.zeros(g.shape, np.int16)
    for a, b, c in zip(*ii):
        hit = tree.find_nearest(Vector((g.X[a, b, c], g.Y[a, b, c], g.Z[a, b, c])), reach)
        if hit[0] is None:
            continue
        name, glow = info[hit[2]]
        near[a, b, c] = True
        colour[a, b, c] = g.cid(name)
        glows[a, b, c] = glow
    bm.free()
    # flood the empty space in from the grid's edge (6-connected): what it can't reach is inside a mesh
    outside = np.zeros(g.shape, bool)
    outside[0, :, :] = outside[-1, :, :] = outside[:, 0, :] = outside[:, -1, :] = outside[:, :, 0] = outside[:, :, -1] = True
    outside &= ~near
    while True:
        grown = outside.copy()
        for axis in range(3):
            for s in (1, -1):
                grown |= np.roll(outside, s, axis)
        grown &= ~near
        if grown.sum() == outside.sum():
            break
        outside = grown
    inside = ~outside & ~near
    filler = g.cid(info[0][0]) if info else 1
    g.col[near] = colour[near]
    g.glow[near] = glows[near]
    g.col[inside & (g.col == 0)] = filler  # (hidden: never meshed)
    return g


# ---------- meshing ----------

def _greedy(key):
    """Rectangles (i, j, h, w, k) covering the cells of key >= 0 with the same value."""
    H, W = key.shape
    done = np.zeros((H, W), bool)
    rows = key.tolist()
    rects = []
    for i in range(H):
        row = rows[i]
        for j in range(W):
            k = row[j]
            if k < 0 or done[i, j]:
                continue
            w = 1
            while j + w < W and row[j + w] == k and not done[i, j + w]:
                w += 1
            h = 1
            while i + h < H and (key[i + h, j:j + w] == k).all() and not done[i + h, j:j + w].any():
                h += 1
            done[i:i + h, j:j + w] = True
            rects.append((i, j, h, w, k))
    return rects


def mesh_quads(g):
    """{(colour name, glow): [quad, ...]}: the visible faces, greedily merged per colour; each quad is four
    world points in counter-clockwise order seen from outside."""
    occ = g.col > 0
    key3 = np.where(occ, g.col.astype(np.int32) * 2 + g.glow.astype(np.int32), -1)
    out = {}
    v = g.v
    for axis in range(3):
        b, c = [k for k in range(3) if k != axis]
        for sign in (-1, 1):
            nb = np.zeros_like(occ)
            src = [slice(None)] * 3
            dst = [slice(None)] * 3
            if sign > 0:
                dst[axis], src[axis] = slice(0, -1), slice(1, None)
            else:
                dst[axis], src[axis] = slice(1, None), slice(0, -1)
            nb[tuple(dst)] = occ[tuple(src)]
            vis = occ & ~nb
            for s in np.nonzero(vis.any(axis=tuple(k for k in range(3) if k != axis)))[0]:
                sl = [slice(None)] * 3
                sl[axis] = s
                key = np.where(vis[tuple(sl)], key3[tuple(sl)], -1)
                plane = (g.i0[axis] + s + (1 if sign > 0 else 0)) * v
                for i, j, h, w, k in _greedy(key):
                    u0, u1 = (g.i0[b] + i) * v, (g.i0[b] + i + h) * v
                    w0, w1 = (g.i0[c] + j) * v, (g.i0[c] + j + w) * v
                    corners = [(u0, w0), (u1, w0), (u1, w1), (u0, w1)]
                    quad = []
                    for uu, ww in corners:
                        p = [0.0, 0.0, 0.0]
                        p[axis], p[b], p[c] = plane, uu, ww
                        quad.append(tuple(p))
                    # (b, c, axis) is a right-handed cycle when axis is 0 or 2 ... check the winding
                    n = np.cross(np.subtract(quad[1], quad[0]), np.subtract(quad[3], quad[0]))
                    if (n[axis] > 0) != (sign > 0):
                        quad.reverse()
                    name = g.names[k // 2 - 1]
                    out.setdefault((name, bool(k % 2)), []).append((quad, axis))
    return out


def stud_uv(p, axis):
    a, b = [k for k in range(3) if k != axis]
    return (p[a] / STUD_TILE, p[b] / STUD_TILE)


VOXEL_MATERIALS = {}


def voxel_material(name, glow):
    key = name + ("Glow" if glow else "")
    if key in VOXEL_MATERIALS:
        return VOXEL_MATERIALS[key]
    mat = bpy.data.materials.new("Vox_" + key)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    r, gg, b = swatch_rgb(name)
    lin = tuple(srgb_to_linear(c) for c in (r, gg, b)) + (1.0,)
    if glow:
        bsdf.inputs["Base Color"].default_value = lin
        bsdf.inputs["Emission Color"].default_value = lin
        bsdf.inputs["Emission Strength"].default_value = 1.6
    else:
        image = bpy.data.images.get("StudOverlay") or bpy.data.images.load(STUD_IMAGE)
        image.name = "StudOverlay"
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = image
        mix = nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        sock = lambda group, name: next(x for x in group if x.name == name and x.type == "RGBA")
        sock(mix.inputs, "A").default_value = lin
        links.new(tex.outputs["Alpha"], next(x for x in mix.inputs if x.name == "Factor"))
        links.new(tex.outputs["Color"], sock(mix.inputs, "B"))
        links.new(sock(mix.outputs, "Result"), bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.45
    mat.diffuse_color = lin
    VOXEL_MATERIALS[key] = mat
    return mat


def make_objects(g, prefix, coll, parent=None):
    """One mesh object per colour (and per glow colour) named prefix + colour (+ "Glow"), split into
    numbered pieces when large. Returns [(object, (colour, glow), triangles)]."""
    made = []
    for (name, glow), quads in sorted(mesh_quads(g).items()):
        chunks = [quads[i:i + MESH_QUADS] for i in range(0, len(quads), MESH_QUADS)]
        for n, chunk in enumerate(chunks):
            label = prefix + name + ("Glow" if glow else "") + (str(n + 1) if n else "")
            verts, faces, uvs = [], [], []
            for quad, axis in chunk:
                base = len(verts)
                verts.extend(quad)
                faces.append((base, base + 1, base + 2, base + 3))
                uvs.extend(stud_uv(p, axis) for p in quad)
            me = bpy.data.meshes.new(label)
            me.from_pydata(verts, [], faces)
            uv = me.uv_layers.new(name="UVMap")
            for i, loop in enumerate(me.loops):
                uv.data[i].uv = uvs[loop.vertex_index]
            me.materials.append(voxel_material(name, glow))
            me.update()
            obj = bpy.data.objects.new(label, me)
            coll.objects.link(obj)
            if parent is not None:
                obj.parent = parent
            obj["voxColour"] = name
            obj["voxGlow"] = glow
            made.append((obj, (name, glow), len(faces) * 2))
    return made


def export_fbx_scaled(objs, path, scale=0.25):
    """FBX like the building pipeline's (a quarter scale: Studio imports it at 25x)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.hide_set(False)
        o.hide_viewport = False
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"}, use_mesh_modifiers=True,
                             apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", global_scale=scale,
                             axis_forward="-Z", axis_up="Y", add_leaf_bones=False, bake_anim=False, path_mode="STRIP")


# ---------- clean-up ----------

_N18 = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1) if 0 < abs(dx) + abs(dy) + abs(dz) <= 2]


def exposed(g):
    """Filled voxels with an empty face neighbour (the visible skin)."""
    occ = g.col > 0
    inner = occ.copy()
    for axis in range(3):
        for s in (1, -1):
            inner &= np.roll(occ, s, axis)
    return occ & ~inner


def despeckle(g, keep=("EyeDark", "EyeWhite"), passes=2):
    """Recolours lone voxels on the skin (fewer than 2 skin neighbours of the same colour among the 18 nearest):
    each takes the commonest colour of its skin neighbours. Rivets and trims thinner than a voxel otherwise
    come out as scattered specks. Lines and patches (2+ in a row) stay."""
    keep_ids = {g.names.index(n) + 1 for n in keep if n in g.names}
    for _ in range(passes):
        skin = exposed(g)
        key = np.where(skin, g.col.astype(np.int32) * 2 + g.glow, -1)
        same = np.zeros(g.shape, np.int8)
        for d in _N18:
            same += (np.roll(key, d, (0, 1, 2)) == key) & skin
        lone = skin & (same < 2) & ~np.isin(g.col, list(keep_ids))
        changed = 0
        for a, b, c in zip(*np.nonzero(lone)):
            votes = {}
            for dx, dy, dz in _N18:
                i, j, k = a + dx, b + dy, c + dz
                if 0 <= i < g.shape[0] and 0 <= j < g.shape[1] and 0 <= k < g.shape[2] and key[i, j, k] >= 0 and key[i, j, k] != key[a, b, c]:
                    votes[key[i, j, k]] = votes.get(key[i, j, k], 0) + 1
            if votes:
                best = max(votes, key=votes.get)
                g.col[a, b, c], g.glow[a, b, c] = best // 2, bool(best % 2)
                changed += 1
        if not changed:
            break
    return g
