# scenery_pines.py - the snowy pine trees round the map (scenery, not gameplay). Two models:
#   PineTall (about 34 studs) and PineShort (about 22 studs), each three meshes named for their colour role:
#   <Model>Trunk, <Model>Needles, <Model>Snow. tools/studio/build_world.luau colours them by name and scatters
#   them beyond the plot ring.
#   blender -b --factory-startup --python tools/blender/scenery_pines.py
# Out: store-assets/scenery/Pines.fbx and Pines_manifest.json (exported at a quarter scale: the import arrives
# at 25x, so the tall tree stays under Roblox's 2048-stud part cap).
import math, os, random
import bpy, bmesh
from mathutils import Vector

EXPORT_SCALE = 0.25
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
exec(open(os.path.join(REPO, "tools", "blender", "model_helpers.py"), encoding="utf-8").read())
OUT = os.path.join(REPO, "store-assets", "scenery")

TRUNK = (0.37, 0.27, 0.2)
NEEDLES = (0.18, 0.36, 0.31)
SNOW = (0.94, 0.96, 0.99)
SEGMENTS = 9  # a chunky, faceted round


def tier(bm, z0, radius, height, rng):
    """One needle tier: a squat cone with a slight lip underneath, its rim a little ragged."""
    rings = []
    for k, (r, z) in enumerate([(radius * 0.35, z0 + 0.9), (radius, z0), (radius * 0.92, z0 + 0.45)]):
        ring = []
        for i in range(SEGMENTS):
            a = 2 * math.pi * (i + 0.5 * (k == 1)) / SEGMENTS
            wobble = 1 + (rng.uniform(-0.07, 0.07) if k else 0)
            ring.append(bm.verts.new((r * wobble * math.cos(a), r * wobble * math.sin(a), z + (rng.uniform(-0.25, 0.1) if k == 1 else 0))))
        rings.append(ring)
    apex = bm.verts.new((0, 0, z0 + height))
    for a, b in zip(rings, rings[1:]):
        for i in range(SEGMENTS):
            j = (i + 1) % SEGMENTS
            bm.faces.new((a[i], a[j], b[j], b[i]))
    top = rings[-1]
    for i in range(SEGMENTS):
        bm.faces.new((top[i], top[(i + 1) % SEGMENTS], apex))
    bottom = rings[0]
    bm.faces.new(list(reversed(bottom)))


def snow_cap(bm, z0, radius, height, top, rng):
    """Snow on a tier's visible shoulder: a shell just outside the needles from part-way up the exposed band
    to `top` (tucked under the next tier, or the apex for the top tier), its lower edge hanging in scallops,
    closed underneath."""
    rim_z, rim_r = z0 + 0.45, radius * 0.92

    def surface(z):  # the needles' radius at height z
        return rim_r * max(0.0, 1 - (z - rim_z) / (height - 0.45))

    low = rim_z + (top - rim_z) * 0.62
    n = SEGMENTS * 2
    edge, inner, upper = [], [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        c, s_ = math.cos(a), math.sin(a)
        droop = (0.8 if i % 2 == 0 else 0.0) + rng.uniform(0, 0.3)
        z = max(rim_z - 0.1, low - droop)
        r = surface(z) + 0.28
        edge.append(bm.verts.new((r * c, r * s_, z)))
        inner.append(bm.verts.new(((r - 0.5) * c, (r - 0.5) * s_, z + 0.15)))
        rt = surface(top) + 0.22
        upper.append(bm.verts.new((rt * c, rt * s_, top)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((edge[i], edge[j], upper[j], upper[i]))
        bm.faces.new((inner[j], inner[i], edge[i], edge[j]))
    if surface(top) < 0.05:
        apex = bm.verts.new((0, 0, top + 0.2))
        for i in range(n):
            bm.faces.new((upper[i], upper[(i + 1) % n], apex))
    else:
        bm.faces.new(upper)
    bm.faces.new(list(reversed(inner)))


def pine(name, height, tiers, seed):
    rng = random.Random(seed)
    meshes = {name + "Trunk": bmesh.new(), name + "Needles": bmesh.new(), name + "Snow": bmesh.new()}
    trunk_h = height * 0.3
    lathe(meshes[name + "Trunk"], [(0, 0), (height * 0.06, 0), (height * 0.045, 0.6), (height * 0.032, trunk_h), (0, trunk_h)], 7)
    z = height * 0.16
    radius = height * 0.3
    step = (height - z) / (tiers + 0.6)
    for t in range(tiers):
        h = step * 1.9 if t < tiers - 1 else height - z
        tier(meshes[name + "Needles"], z, radius, h, rng)
        snow_cap(meshes[name + "Snow"], z, radius, h, z + step + 0.6 if t < tiers - 1 else z + h, rng)
        z += step
        radius *= 0.74
    looks = {name + "Trunk": (TRUNK, "hard"), name + "Needles": (NEEDLES, "hard"), name + "Snow": (SNOW, "smooth")}
    return build_looks(COLL, meshes, looks)


COLL = begin("Pines")
groups = {"PineTall": pine("PineTall", 34, 5, 7), "PineShort": pine("PineShort", 22, 4, 11)}
sizes = rest_and_place(groups, spacing=(30, 30))
objects = [o for objs in groups.values() for o in objs]
check(objects)
for o in objects:
    print(o.name, triangles(o))
fbx = os.path.join(OUT, "Pines.fbx")
export_fbx(objects, fbx)
write_manifest(os.path.join(OUT, "Pines_manifest.json"), fbx, groups, sizes)
shots(objects, {"front": (0, -1, 0.25), "three_quarter": (1, -1, 0.6)}, os.path.join(OUT, "render"), size=640)
print("PINES_DONE")
