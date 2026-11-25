# heights.py - the tier heights (docs/GAME_DESIGN.md, "Height grows fast with each tier") and the room each
# station has on the plot, for framework.py (which grows each tier) and for checks.
#
# A tier grows by scaling everything above its base uniformly about the base's top centre: the base keeps
# its pad size. The base is the widest flat mesh standing on the ground, plus every mesh that stays within
# BASE_SLACK of its top (plinth trim, gems, rubble). The scale is the one that brings the station's top to
# its target height (BuildingConfig.TierHeights), capped so its footprint (with the upgrade sets) stays in
# its room: short of the half-way line to every other pad, off the fence ring round the ice and inside the
# plot (plus a little over the low wall).
import math, os, re

BASE_SLACK = 0.7            # a mesh whose top is within this of the base top stays (plinth trim, gems, rubble)
NEIGHBOUR_MARGIN = 0.5      # studs kept clear of the half-way line to another pad
FENCE_CLEAR = 26.0          # stations stay this far from the ice centre: the fence ring (BuildingConfig.Fence, radius 23) and its posts
PLOT_LIMIT = 51.5           # |x|, |z| in plot space: the plot is 100 square; the low wall is at 49-51


def from_config(repo):
    """(pads {index: {X, Z, Size}}, {building id: pad index}, {pad index: [5 heights]}) from
    src/replicated/BuildingConfig.luau (Pad, TierHeights, PadGroups), so the doc's numbers live in one place."""
    text = open(os.path.join(repo, "src", "replicated", "BuildingConfig.luau"), encoding="utf-8").read()
    pads, index_of = {}, {}
    for m in re.finditer(r'\{ Id = "(\w+)".*?Pad = \{ Index = (\d+), X = (-?\d+), Z = (-?\d+), Size = (\d+) \}', text, re.S):
        pads[int(m.group(2))] = {"X": int(m.group(3)), "Z": int(m.group(4)), "Size": int(m.group(5))}
        index_of[m.group(1)] = int(m.group(2))
    groups = re.findall(r'"(\w+)"', re.search(r"BuildingConfig\.PadGroups = \{(.*?)\}", text).group(1))
    block = re.search(r"BuildingConfig\.TierHeights = \{(.*?)\n\}", text, re.S).group(1)
    table = {g: [float(x) for x in re.findall(r"[\d.]+", v)] for g, v in re.findall(r"(\w+) = \{ ([\d., ]+) \}", block)}
    return pads, index_of, {i: table[groups[i - 1]] for i in pads}


def pad_frame(pad):
    """(position, forward, right) of a station on its pad in plot space (Roblox x, z): its front faces the ice."""
    px, pz = pad["X"], pad["Z"]
    d = math.hypot(px, pz)
    f = (-px / d, -pz / d)
    return (px, pz), f, (-f[1], f[0])


def to_plot(pad, x_b, y_b):
    """A Blender station-space point (x, y) -> plot space (x, z)."""
    (px, pz), f, right = pad_frame(pad)
    # Blender (x, y) -> Roblox local (-x, y), and local -Z faces the ice: world = pad - x*right - y*forward
    return (px - x_b * right[0] - y_b * f[0], pz - x_b * right[1] - y_b * f[1])


def blocked_by(pad, others, points):
    """What plot-space points (x, z) run into: a set of names (empty = they stay in the station's room)."""
    (px, pz), _, _ = pad_frame(pad)
    hits = set()
    for x, z in points:
        if math.hypot(x, z) < FENCE_CLEAR:
            hits.add("the fence ring")
        if abs(x) > PLOT_LIMIT or abs(z) > PLOT_LIMIT:
            hits.add("the plot edge")
        for o in others:
            ux, uz = o["X"] - px, o["Z"] - pz
            d = math.hypot(ux, uz)
            if ((x - px) * ux + (z - pz) * uz) / d > d / 2 - NEIGHBOUR_MARGIN:
                hits.add("pad (%d, %d)" % (o["X"], o["Z"]))
    return hits


def room_ok(pad, others, points):
    return not blocked_by(pad, others, points)


def neighbours(pads, index):
    """Every other pad (far ones never limit anything)."""
    return [p for i, p in pads.items() if i != index]


def hull(points):
    """2D convex hull (monotone chain) of (x, y) points."""
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def best_scale(pad, others, base_top, top, target, outline, centre):
    """(scale, reached height): the scale that reaches the target (below 1 shrinks a tier that is already too
    tall), capped by the room. outline: the Blender (x, y) hull of everything above the base; centre: the
    base's top centre (x, y)."""
    want = (target - base_top) / max(top - base_top, 0.1)
    cx, cy = centre

    def fits(s):
        return room_ok(pad, others, [to_plot(pad, cx + s * (x - cx), cy + s * (y - cy)) for x, y in outline])

    if fits(want):
        return want, target
    lo, hi = min(1.0, want), want
    if not fits(lo):
        return lo, base_top + lo * (top - base_top)
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if fits(mid) else (lo, mid)
    lo *= 0.995  # (a hair inside the limit, so rounding never tips it over)
    return lo, base_top + lo * (top - base_top)


def split_base(meshes):
    """meshes: {name: [(x, y, z), ...]} of one tier's station. Returns (base_top, centre (x, y), base names):
    the base is the widest flat mesh standing on the ground plus every mesh that stays within BASE_SLACK of
    its top (plinth trim, gems, rubble, cracks); everything else is the structure that grows."""
    widest, area = None, -1.0
    for name, vs in meshes.items():
        if not vs or name.endswith("Glow"):
            continue
        if min(v[2] for v in vs) < 0.15 and max(v[2] for v in vs) < 1.8:  # (a flat deck, plinth or platform)
            xs, ys = [v[0] for v in vs], [v[1] for v in vs]
            a = (max(xs) - min(xs)) * (max(ys) - min(ys))
            if a > area:
                widest, area = name, a
    vs = meshes[widest]
    base_top = max(v[2] for v in vs)
    centre = ((max(v[0] for v in vs) + min(v[0] for v in vs)) / 2, (max(v[1] for v in vs) + min(v[1] for v in vs)) / 2)
    base = {n for n, vs in meshes.items() if vs and max(v[2] for v in vs) <= base_top + BASE_SLACK}
    return base_top, centre, base
