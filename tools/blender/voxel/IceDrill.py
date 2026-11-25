# IceDrill.py (voxel STYLE TEST) - the Ice Drill on the 0.5-stud voxel grid (tools/blender/voxel/voxels.py):
#   FIX_B  hand fixes on the automatically voxelized approved models (style B)
#   A_TIERS the five tiers hand-built on the grid (style A), following the approved designs, heights, pad
#           (10 studs) and attachment points (store-assets/buildings/IceDrill/IceDrill_manifest.json)
# Blender axes: x right, y back (the front -Y faces the ice), z up; studs.
import numpy as np

NOSE = np.array((0.0, -0.789, -0.615))  # the Titan's drill direction (IceDrill.TITAN_NOSE_DIR)
TITAN_WORK = (0.0, -6.6, 18.5)          # where the bit is mounted (the Work attachment)
TITAN_EYES = [(-2.14, 21.8), (2.14, 21.8)]  # (x, z) of the eye centres on the face


def drill_bit(g, base, direction, length, r0, bands=3, body=("SteelLight", "Steel"), band="Gold", tip="Diamond", glow_tip=False):
    """A stepped voxel drill bit from base along direction: alternating tones, gold bands, a bright tip."""
    d = np.array(direction, float) / np.linalg.norm(direction)
    base = np.array(base, float)
    steps = bands * 2
    for k in range(steps):
        a, b = k / steps, (k + 1) / steps
        p0, p1 = base + d * length * a, base + d * length * b
        g.put(g.cyl(p0, p1, r0 * (1 - a * 0.85), r0 * (1 - b * 0.85)), body[k % 2])
    for k in range(1, bands + 1):  # gold bands: the bit's own skin painted, no collars
        f = k / (bands + 1) * 0.9
        c = base + d * length * f
        g.paint(g.cyl(c - d * 0.3, c + d * 0.3, r0 * (1 - f * 0.85) + 0.1), band)
    g.put(g.cyl(base + d * length * 0.86, base + d * length * 1.02, r0 * 0.2, 0.1, caps=True), tip, glow_tip)


def fix_titan(g):
    # the drill: the voxelized bit and its thin energy rings came out as a gold-and-white tangle; rebuild it
    w = np.array(TITAN_WORK)
    rel = np.stack([g.X - w[0], g.Y - w[1], g.Z - w[2]], -1)
    along = rel @ NOSE
    radial = np.linalg.norm(rel - along[..., None] * NOSE, axis=-1)
    old = (along > -0.2) & (radial < 3.6)
    length = float(along[old & (g.col > 0)].max()) if (old & (g.col > 0)).any() else 5.0
    g.cut(old)
    g.put(g.cyl(w - NOSE * 0.6, w + NOSE * 0.2, 2.3), "Gunmetal")  # the housing's lip
    g.put(g.ring(w - NOSE * 0.1, NOSE, 2.3, 0.45), "Gold")
    drill_bit(g, w, NOSE, max(length, 4.5), 1.8)
    # the eyes: the glowing voxel blobs become proper cartoon eyes (dark ring, cyan iris, two shines)
    for x, z in TITAN_EYES:
        blob = (np.abs(g.X - x) < 2.6) & (np.abs(g.Z - z) < 2.6) & (g.Y < 0)
        g.paint(blob & g.glow, "Gunmetal")
        g.glow[blob] = False
        g.put(g.ring((x, g.front_y(x, z) + 0.2, z), (0, 1, 0), 1.95, 0.4), "Gunmetal")
        g.eye(x, z, 1.55, iris="CrystalCyan", look=(0.0, 0.5), glow_iris=True)


def fix_titan_diamond(g):
    """The 1st upgrade on the Titan: the diamond bit over the station's bit (voxelized, it was a glowing
    blob): a clean crystal bit, a size up."""
    w = np.array(TITAN_WORK)
    rel = np.stack([g.X - w[0], g.Y - w[1], g.Z - w[2]], -1)
    along = rel @ NOSE
    radial = np.linalg.norm(rel - along[..., None] * NOSE, axis=-1)
    old = (along > -0.2) & (radial < 3.8) & (g.col > 0)
    length = float(along[old].max()) if old.any() else 5.5
    g.cut(old)
    drill_bit(g, w + NOSE * 0.3, NOSE, max(length, 5.0), 2.0, body=("Diamond", "CrystalCyan"), band="Gold", tip="Diamond", glow_tip=True)


FIX_B = {5: fix_titan}
FIX_B_UP = {(5, 1): fix_titan_diamond}
