# ice_drill_style_test.py - style test: the Ice Drill at detail levels 1, 5 and 10 (docs/GAME_DESIGN.md,
# "Detail levels"), built from the building kit, rendered as turnarounds beside a voxel pet.
#
# Run headless (nothing is uploaded or exported to Roblox):
#   blender -b --factory-startup --python tools/blender/ice_drill_style_test.py -- <bunny.blend> <out dir>
#
# How the detail levels are made (the plan for every building):
#   * Structure: one station model per count milestone (1, 10, 25, 50, 100 owned). Each station has
#     named attachment points (Att_<Name>): Bit1/Bit2, Lamp1/Lamp2, Gear1/Gear2, Steam1/Steam2, Hit1/Hit2,
#     Trail1/Trail2, NamePlate (and Smoke where there is a stack).
#   * Upgrades: one small part set per upgrade, built once in its attachment's frame and snapped onto
#     every attachment of that name the station has. Order doesn't matter; the model shows what's earned.
#       Ice Drill: 1st steel bits (Bit), 2nd warning lamps (Lamp), 3rd gears + steam (Gear, Steam),
#       4th ice chips and sparks on hits (Hit), 5th diamond bits + crystal trail (Bit, Trail) and the
#       Masterwork name plate (NamePlate).
#   * Effects (steam, chips, sparks, the trail) are particles in game; here they are FX stand-ins
#     (FxPreview_*), only so the renders show where they come from.
#   Detail 1 = station 1. Detail 5 = station 25 + upgrades 1 and 2. Detail 10 = station 100 + all five.
import bpy, sys, os, math
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "model_helpers.py"), encoding="utf-8").read())
exec(open(os.path.join(HERE, "building_kit.py"), encoding="utf-8").read())

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BUNNY_BLEND = ARGS[0]
OUT = ARGS[1]
REPO = os.path.dirname(os.path.dirname(HERE))
PALETTE_PNG = os.path.join(REPO, "assets", "textures", "BuildingPalette.png")
MESH_BUDGET = 5000  # triangles per mesh: well under Roblox's 20,000 (and the 10k some import paths use)

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
palette = write_palette(PALETTE_PNG)
MATERIALS = palette_materials(palette)
ALL_MESHES = []


def collection(name):
    coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    return coll


class Builder:
    """Collects Parts (solid and glow) for one model and finishes them under a root empty."""

    def __init__(self, name, coll):
        self.name, self.coll, self.parts = name, coll, {}
        self.root = bpy.data.objects.new(name, None)
        coll.objects.link(self.root)

    def part(self, role, glow=False):
        key = self.name + role + ("Glow" if glow else "")
        if key not in self.parts:
            self.parts[key] = Part(key, glow)
        return self.parts[key]

    def add(self, role, pieces, matrix=Matrix()):
        solid, glow = split(pieces)
        if solid:
            self.part(role).add(solid, matrix)
        if glow:
            self.part(role, True).add(glow, matrix)

    def finish(self):
        made = []
        for part in self.parts.values():
            obj = part.finish(self.coll, MATERIALS)
            obj.parent = self.root
            made.append(obj)
            ALL_MESHES.append(obj)
        self.parts = {}
        return made


def attach_empties(builder, atts):
    for name, matrix in atts.items():
        empty = bpy.data.objects.new(builder.name + "_Att_" + name, None)
        empty.empty_display_type = "ARROWS"
        empty.empty_display_size = 0.6
        empty.matrix_world = matrix
        builder.coll.objects.link(empty)
        empty.parent = builder.root


def down(p):
    return frame(p, out=(0, 0, -1), up=(0, 1, 0))


def up_(p):
    return frame(p, out=(0, 0, 1), up=(0, 1, 0))


def front(p):
    return frame(p, out=(0, -1, 0))


# ---------- stations (the structure track) ----------

def drill_rig(b, role, X, base_z, top_z, motor_z):
    """A twin-post steel-and-pine drill frame with a motor housing on top, centred on x = X."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add(role, beam_between((X + sx * 1.0, sy * 0.9, base_z), (X + sx * 1.0, sy * 0.9, top_z), 0.42, swatch="Steel"))
    for z, swatch, width in ((top_z - 0.18, "Steel", 0.36), ((base_z + top_z) / 2, "Pine", 0.3)):
        for sy in (-1, 1):
            b.add(role, beam_between((X - 1.0, sy * 0.9, z), (X + 1.0, sy * 0.9, z), width, swatch=swatch))
        for sx in (-1, 1):
            b.add(role, beam_between((X + sx * 1.0, -0.9, z), (X + sx * 1.0, 0.9, z), width, swatch=swatch))
    for sx in (-1, 1):  # side braces
        b.add(role, beam_between((X + sx * 1.0, -0.9, base_z + 0.2), (X + sx * 1.0, 0.9, (base_z + top_z) / 2 - 0.2), 0.26, swatch="PineDark"))
    b.add(role, beam_between((X - 1.0, -0.9, (base_z + top_z) / 2 + 0.2), (X + 1.0, -0.9, top_z - 0.4), 0.26, swatch="PineDark"))
    motor(b, role, X, motor_z)
    b.add(role, place(cyl(0.2, motor_z - base_z - 1.0, "Steel"), M((X, 0, base_z + 1.0))))


def motor(b, role, X, z, exhaust=True):
    """A motor housing (steel box, ice-blue band, rivets) sitting at height z."""
    b.add(role, place(block((2.4, 2.2, 1.6), "SteelLight"), M((X, 0, z))))
    b.add(role, place(block((2.52, 2.32, 0.32), "DeepIce", corner=0.22, edge=0.08), M((X, 0, z + 0.45))))
    for sx in (-1, 1):
        for dz in (0.25, 1.3):
            b.add(role, place(rivet(0.09), front((X + sx * 0.95, -1.1, z + dz))))
    for k in range(3):  # vents on the back
        b.add(role, place(block((1.4, 0.12, 0.16), "SteelDark", corner=0.05, edge=0.04), M((X, 1.12, z + 0.95 + k * 0.22))))
    if exhaust:
        b.add(role, place(cyl(0.2, 0.6, "SteelDark", 10), M((X + 0.6, 0.6, z + 1.6))))
        b.add(role, place(cyl(0.28, 0.14, "Iron", 10), M((X + 0.6, 0.6, z + 2.2))))


def collar(b, role, X, z):
    ring = bmesh.new()
    torus(ring, M((X, 0, z)), 0.78, 0.22, 16, 6)
    b.add(role, [(ring, "StoneDark", 0.0, False)])


def station_1(coll):
    """1 owned: a hand drill on a small frame."""
    b = Builder("IceDrillStation1", coll)
    for x in (-1.8, 1.8):
        for sy in (-1, 1):
            b.add("Frame", beam_between((x, sy * 1.5, 0.25), (x, sy * 0.15, 5.0), 0.45, swatch="Pine"))
            b.add("Frame", place(block((0.8, 0.8, 0.3), "StoneDark", corner=0.2, edge=0.1), M((x, sy * 1.5, 0))))
        b.add("Frame", beam_between((x, -0.95, 2.2), (x, 0.95, 2.2), 0.32, swatch="PineDark"))
    b.add("Frame", beam_between((-2.3, 0, 5.0), (2.3, 0, 5.0), 0.55, swatch="PineLight"))
    b.add("Frame", place(block((0.9, 0.9, 0.7), "SteelDark"), M((0, 0, 4.65))))
    for x in (-0.28, 0.28):
        b.add("Frame", place(rivet(0.08), front((x, -0.45, 5.15))))
    for x in (-1.8, 1.8):
        b.add("Frame", place(bolt(0.14), front((x, -0.28, 5.0))))
    b.add("Frame", place(cyl(0.16, 3.1, "Steel"), M((0, 0, 1.6))))
    b.add("Frame", place(cyl(0.55, 0.18, "Brass", 14), M((0, 0, 5.35))))  # the crank wheel
    b.add("Frame", beam_between((0, 0, 5.6), (0.95, 0, 5.6), 0.18, swatch="Iron"))
    b.add("Frame", place(cyl(0.12, 0.6, "PineLight", 8), M((0.95, 0, 5.6))))
    collar(b, "Frame", 0, 0.15)
    atts = {"Bit1": down((0, 0, 1.6)), "Lamp1": up_((2.05, 0, 5.28)), "Gear1": front((-1.15, -0.28, 5.0)),
            "Steam1": up_((0, 0.3, 5.6)), "Hit1": frame((0, -0.7, 0.35), out=(0, -1, 0.6)),
            "Trail1": down((0, 0, -0.4)), "NamePlate": front((0, -2.0, 0.55))}
    return b, atts


def platform(b, size, trim=False):
    w, d = size
    b.add("Platform", block((w, d, 0.9), "Stone", corner=0.45, edge=0.2))
    b.add("Platform", place(block((w - 0.6, d - 0.6, 0.3), "StoneLight", corner=0.3, edge=0.1), M((0, 0, 0.9))))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add("Platform", place(bolt(0.2), up_((sx * (w / 2 - 0.65), sy * (d / 2 - 0.65), 1.2))))
    if trim:  # 100 owned: gold trim round the platform
        b.add("Trim", place(block((w + 0.1, d + 0.1, 0.16), "Gold", corner=0.47, edge=0.06), M((0, 0, 0.72))))


def station_25(coll):
    """25 owned: a stone base platform and a second drill (with 10 owned's motor housing and taller frame)."""
    b = Builder("IceDrillStation25", coll)
    platform(b, (9.0, 7.0))
    for X, role in ((-2.2, "RigA"), (2.2, "RigB")):
        collar(b, "Platform", X, 1.3)
        drill_rig(b, role, X, 1.2, 7.0, 7.0)
    b.add("Pipes", pipe_between((-1.0, 0.4, 8.0), (1.0, 0.4, 8.0)))
    atts = {}
    for n, X in ((1, -2.2), (2, 2.2)):
        atts["Bit%d" % n] = down((X, 0, 2.3))
        atts["Lamp%d" % n] = up_((X - 0.6, -0.4, 8.6))
        atts["Gear%d" % n] = front((X, -1.1, 7.8))
        atts["Steam%d" % n] = up_((X + 0.6, 0.6, 8.95))
        atts["Hit%d" % n] = frame((X, -0.9, 1.4), out=(0, -1, 0.6))
        atts["Trail%d" % n] = down((X, 0, 1.4))
    atts["NamePlate"] = front((0, -3.55, 0.45))
    return b, atts


def station_100(coll):
    """100 owned: the lattice drill tower (50 owned: tower, smoke stack, ladder) with gold trim and a crest."""
    b = Builder("IceDrillStation100", coll)
    XA, XB = -1.8, 2.6
    platform(b, (9.6, 8.0), trim=True)
    collar(b, "Platform", XA, 1.3)
    collar(b, "Platform", XB, 1.3)
    base, top = 1.2, 14.0

    def leg(sx, sy, z):
        f = (z - base) / (top - base)
        return Vector((XA + sx * (1.8 - 1.1 * f), sy * (1.6 - 1.0 * f), z))

    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for sx, sy in corners:
        b.add("Tower", beam_between(leg(sx, sy, base), leg(sx, sy, top), 0.45, swatch="SteelLight"))
        b.add("Tower", place(block((0.8, 0.8, 0.3), "StoneDark", corner=0.2, edge=0.1), M(leg(sx, sy, base))))
    rings = [base + 0.2, 4.6, 8.0, 11.0, top - 0.2]
    for z in rings[1:]:
        for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
            b.add("Tower", beam_between(leg(ax, ay, z), leg(bx, by, z), 0.3, swatch="Steel"))
    for z0, z1 in zip(rings, rings[1:]):  # the lattice: an X on every face of every bay
        for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
            b.add("TowerBraces", beam_between(leg(ax, ay, z0 + 0.15), leg(bx, by, z1 - 0.15), 0.2, swatch="PineDark"))
            b.add("TowerBraces", beam_between(leg(bx, by, z0 + 0.15), leg(ax, ay, z1 - 0.15), 0.2, swatch="PineDark"))
    b.add("Tower", place(block((2.2, 2.0, 0.6), "SteelDark"), M((XA, 0, top))))
    b.add("Trim", place(block((2.4, 2.2, 0.18), "Gold", corner=0.25, edge=0.06), M((XA, 0, top + 0.6))))
    for sx, sy in corners:
        b.add("Trim", place(cyl(0.14, 0.45, "Gold", 8), M((XA + sx * 0.95, sy * 0.85, top + 0.78))))
        b.add("Trim", place(rivet(0.16, "Gold"), M((XA + sx * 0.95, sy * 0.85, top + 1.23))))
    motor(b, "Tower", XA, 5.0, exhaust=False)
    b.add("Tower", place(cyl(0.22, top - 2.5, "Steel"), M((XA, 0, 2.5))))
    # the crest on a bracket across the tower's front
    b.add("Tower", beam_between(leg(-1, -1, 9.6) + Vector((0, -0.25, 0)), leg(1, -1, 9.6) + Vector((0, -0.25, 0)), 0.3, swatch="Steel"))
    b.add("Crest", place(crest(1.9, 2.3, 0.24), front((XA, -1.38, 9.7))))
    # ladder up the right face, following the leg's slope
    tilt = math.atan2(1.1, top - base)
    b.add("Ladder", place(ladder(top - base - 0.8, 0.9), Matrix.Translation((XA + 2.15, 0, base)) @ Matrix.Rotation(-tilt, 4, "Y") @ Matrix.Rotation(math.pi / 2, 4, "Z")))
    # the second drill and the smoke stack
    drill_rig(b, "RigB", XB, 1.2, 7.0, 7.0)
    b.add("Stack", place(cyl(0.6, 10.0, "SteelDark", 16), M((XB, 2.7, 1.2))))
    for z in (3.2, 6.2, 9.2):
        ring = bmesh.new()
        torus(ring, M((XB, 2.7, z)), 0.62, 0.12, 16, 6)
        b.add("Stack", [(ring, "Iron", 0.0, False)])
    b.add("Stack", place(cyl(0.78, 0.4, "Gunmetal", 16), M((XB, 2.7, 11.2))))
    ring = bmesh.new()
    torus(ring, M((XB, 2.7, 10.9)), 0.64, 0.13, 16, 6)
    b.add("Trim", [(ring, "Gold", 0.0, False)])
    b.add("Pipes", pipe_between((XB, 1.1, 8.0), (XB, 2.15, 8.0)))
    for p0, p1 in (((XA + 1.2, 0.4, 5.8), (0.9, 0.4, 5.8)), ((0.9, 0.4, 5.8), (0.9, 0.4, 7.8)), ((0.9, 0.4, 7.8), (XB - 1.2, 0.4, 7.8))):
        b.add("Pipes", pipe_between(p0, p1))
    for p in ((0.9, 0.4, 5.8), (0.9, 0.4, 7.8)):
        b.add("Pipes", place(block((0.62, 0.62, 0.62), "Copper", corner=0.2, edge=0.15), M((p[0], p[1], p[2] - 0.31))))
    atts = {"Bit1": down((XA, 0, 2.5)), "Bit2": down((XB, 0, 2.3)),
            "Lamp1": up_((XA, 0, top + 0.78)), "Lamp2": up_((XB - 0.6, -0.4, 8.6)),
            "Gear1": front((XA, -1.0, top + 0.3)), "Gear2": front((XB, -1.1, 7.8)),
            "Steam1": up_((XA - 1.05, 0.0, 6.6)), "Steam2": up_((XB + 0.6, 0.6, 8.95)),
            "Smoke": up_((XB, 2.7, 11.6)),
            "Hit1": frame((XA, -0.9, 1.4), out=(0, -1, 0.6)), "Hit2": frame((XB, -0.9, 1.4), out=(0, -1, 0.6)),
            "Trail1": down((XA, 0, 1.0)), "Trail2": down((XB, 0, 1.2)),
            "NamePlate": front((0, -4.05, 0.45))}
    return b, atts


# ---------- upgrade part sets (snap onto attachments) ----------

LETTERS = "ABCD"


def numbered(atts, prefix):
    return [(atts[k], LETTERS[i]) for i, k in enumerate(sorted(k for k in atts if k.startswith(prefix) and k[len(prefix):].isdigit()))]


def bits(b, atts, kind):
    for matrix, letter in numbered(atts, "Bit"):
        b.add("Bit" + letter, place(auger(kind), matrix))  # one mesh per bit: it spins about its own axis


def lamps(b, atts):
    for matrix, letter in numbered(atts, "Lamp"):
        b.add("Lamp" + letter, place(warning_lamp(0.34), matrix))


def gears(b, atts):
    for matrix, letter in numbered(atts, "Gear"):
        b.add("Gear%s1" % letter, place(gear(0.72, 12, 0.3, 0.2), matrix @ M((0, 0, 0.18))))
        b.add("Gear%s2" % letter, place(gear(0.42, 8, 0.3, 0.16, "Copper"), matrix @ M((0.62, 0.62, 0.42))))


def masterwork_plate(b, atts):
    b.add("NamePlate", place(name_plate(2.8, 0.7), atts["NamePlate"]))


# ---------- FX stand-ins (particles in game) ----------

def fx_steam(b, atts):
    for matrix, letter in numbered(atts, "Steam"):
        for k, (dx, dz, r) in enumerate(((0.0, 0.5, 0.32), (0.25, 1.05, 0.42), (-0.1, 1.7, 0.52))):
            puff = bmesh.new()
            blob(puff, (dx, 0, dz), (r, r, r * 0.85), 1)
            b.add("Steam" + letter, place([(puff, "SnowWhite", 0.0, False)], matrix))


def fx_hits(b, atts):
    for matrix, letter in numbered(atts, "Hit"):
        pieces = []
        for k in range(7):
            a = k * 2.4
            chip = bmesh.new()
            blob(chip, (0.55 * math.cos(a), 0.55 * math.sin(a), 0.3 + 0.18 * k), (0.16, 0.11, 0.2), 1, rotation=(a, 0.5 * k, 0))
            pieces.append((chip, "IceBlue" if k % 2 else "Diamond", 0.0, False))
        for k in range(5):
            a = k * 1.3 + 0.4
            spark = bmesh.new()
            cylinder(spark, (0.35 * math.cos(a), 0.35 * math.sin(a), 0.2), 0.04, 0.5, 4,
                     direction=(math.cos(a), math.sin(a), 1.2), top=0.0)
            pieces.append((spark, "LampYellow", 0.0, True))
        b.add("Hit" + letter, place(pieces, matrix))


def fx_trail(b, atts):
    for matrix, letter in numbered(atts, "Trail"):
        pieces = []
        for k in range(9):
            a = k * 0.9
            gem = bmesh.new()
            blob(gem, (0.75 * math.cos(a), 0.75 * math.sin(a), -2.6 + k * 0.38), (0.11, 0.11, 0.16), 1)
            pieces.append((gem, "Diamond", 0.0, True))
        b.add("Trail" + letter, place(pieces, matrix))


# ---------- the three detail levels ----------

def detail(level):
    coll = collection("IceDrillD%d" % level)
    station = {1: station_1, 5: station_25, 10: station_100}[level]
    s, atts = station(coll)
    s.name = "IceDrillD%d" % level  # unique part names per detail model in this file
    s.root.name = s.name
    attach_empties(s, atts)
    u = s  # upgrade sets are separate meshes in the same model
    if level == 1:
        bits(u, atts, "Iron")
    elif level == 5:
        bits(u, atts, "Steel")
        lamps(u, atts)
    else:
        bits(u, atts, "Diamond")
        lamps(u, atts)
        gears(u, atts)
        masterwork_plate(u, atts)
    meshes = s.finish()
    fx = Builder("FxPreviewD%d" % level, coll)
    if level == 10:
        fx_steam(fx, atts)
        fx_hits(fx, atts)
        fx_trail(fx, atts)
    fx_meshes = fx.finish()
    fx.root.parent = s.root
    return s.root, meshes, fx_meshes


def reference_figures():
    """The Snow Bunny voxel pet at the pet pipeline's own scale (Scale = 5: 1 m = 5 studs), and a plain
    5.5-stud avatar stand-in."""
    coll = collection("Reference")
    with bpy.data.libraries.load(BUNNY_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in ("Bunny", "BunnyRig")]
    for obj in dst.objects:
        coll.objects.link(obj)
    rig = next(o for o in dst.objects if o.type == "ARMATURE")
    rig.scale = (5, 5, 5)
    rig.location = (10.8, 0.5, 0)
    av = Builder("AvatarStandIn", coll)
    av.add("Body", place(block((0.9, 0.9, 2.0), "SteelDark", corner=0.15, edge=0.1), M((-0.5, 0, 0))))
    av.add("Body", place(block((0.9, 0.9, 2.0), "SteelDark", corner=0.15, edge=0.1), M((0.5, 0, 0))))
    av.add("Body", place(block((2.0, 1.0, 2.0), "Steel", corner=0.2, edge=0.12), M((0, 0, 2.0))))
    for sx in (-1, 1):
        av.add("Body", place(block((0.85, 0.85, 2.0), "Steel", corner=0.15, edge=0.1), M((sx * 1.45, 0, 2.0))))
    av.add("Body", place(block((1.15, 1.15, 1.15), "StoneLight", corner=0.3, edge=0.25), M((0, 0, 4.0))))
    av.finish()
    av.root.location = (16.5, 0, 0)
    return coll


# ---------- render setup ----------

def setup_render():
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 1100, 1000
    scene.render.film_transparent = False
    try:
        scene.eevee.taa_render_samples = 48
    except AttributeError:
        pass
    world = bpy.data.worlds.new("Sky")
    scene.world = world
    if world.node_tree is None:
        world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.42, 0.62, 0.84, 1)
    bg.inputs["Strength"].default_value = 0.55
    coll = collection("Stage")
    ground_mesh = bpy.data.meshes.new("Ground")
    gbm = bmesh.new()
    bmesh.ops.create_grid(gbm, x_segments=1, y_segments=1, size=200)
    gbm.to_mesh(ground_mesh)
    gbm.free()
    ground = bpy.data.objects.new("Ground", ground_mesh)
    coll.objects.link(ground)
    snow = bpy.data.materials.new("Snow")
    if snow.node_tree is None:
        snow.use_nodes = True
    sb = next(n for n in snow.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    sb.inputs["Base Color"].default_value = (0.55, 0.66, 0.78, 1)
    sb.inputs["Roughness"].default_value = 0.9
    ground.data.materials.append(snow)
    for name, rotation, energy in (("Key", (math.radians(50), 0, math.radians(-35)), 2.3),
                                    ("Fill", (math.radians(65), 0, math.radians(120)), 0.6),
                                    ("Rim", (math.radians(35), 0, math.radians(190)), 1.0)):
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
        light.data.energy = energy
        light.data.angle = math.radians(4)
        light.rotation_euler = rotation
        coll.objects.link(light)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.type = "ORTHO"
    coll.objects.link(cam)
    scene.camera = cam
    return cam


def aim(cam, target, elevation_deg, ortho):
    target = Vector(target)
    e = math.radians(elevation_deg)
    eye = target + Vector((0, -80 * math.cos(e), 80 * math.sin(e)))
    cam.location = eye
    cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = ortho
    cam.data.clip_end = 400


def label(text, location, size=0.9, coll=None):
    curve = bpy.data.curves.new("Label", "FONT")
    curve.body = text
    curve.size = size
    curve.align_x = "CENTER"
    obj = bpy.data.objects.new("Label_" + text, curve)
    obj.location = location
    obj.rotation_euler = (math.radians(90), 0, 0)
    mat = bpy.data.materials.get("LabelInk") or bpy.data.materials.new("LabelInk")
    mat.diffuse_color = (0.05, 0.1, 0.2, 1)
    if mat.node_tree is None:
        mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.03, 0.07, 0.16, 1)
    obj.data.materials.append(mat)
    (coll or collection("Labels")).objects.link(obj)
    return obj


def set_visible(objects, visible):
    for obj in objects:
        obj.hide_render = not visible
        obj.hide_viewport = not visible


def tree(root):
    out, frontier = [root], [root]
    while frontier:
        nxt = [o for o in bpy.data.objects if o.parent in frontier]
        out += nxt
        frontier = nxt
    return out


# ---------- build everything ----------

cam = setup_render()
models = {level: detail(level) for level in (1, 5, 10)}
reference_figures()

problems = []
print("TRIANGLES per mesh:")
for obj in ALL_MESHES:
    deps = bpy.context.evaluated_depsgraph_get()
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    flag = "  <-- OVER %d" % MESH_BUDGET if tris > MESH_BUDGET else ""
    print("  %-34s %6d%s" % (obj.name, tris, flag))
    if tris > MESH_BUDGET:
        problems.append(obj.name)
    if "." in obj.name:
        problems.append("renamed: " + obj.name)
for level, (root, meshes, fx) in models.items():
    print("MODEL IceDrillD%d: %d meshes, %d triangles (+%d FX stand-in meshes)" % (
        level, len(meshes), sum(sum(len(p.vertices) - 2 for p in m.data.polygons) for m in meshes), len(fx)))
spins = {}
for level, (root, meshes, fx) in models.items():
    for m in meshes:
        if "Bit" in m.name or "Gear" in m.name:
            spins[m.name] = m
print("PROBLEMS:", problems or "none")

# ---------- turnarounds ----------

os.makedirs(OUT, exist_ok=True)
VIEWS = [("front", 0.0, 12), ("side", -90.0, 12), ("back", 180.0, 12), ("threequarter", -40.0, 26)]
labels = collection("Labels")
names = {1: "Detail 1: 1 owned", 5: "Detail 5: 25 owned + 2 upgrades", 10: "Detail 10: Masterwork"}
pet_label = label("voxel pet: the pet kit's bunny, at pipeline scale", (10.8, -7.5, 0.25), 0.5)
avatar_label = label("avatar 5.5 studs", (16.5, -7.5, 1.0), 0.5)
for level, (root, meshes, fx) in models.items():
    for other, (oroot, *_rest) in models.items():
        set_visible(tree(oroot), other == level)
    title = label(names[level], (0, -7.5, 0.25), 0.62)
    for view, angle, elevation in VIEWS:
        root.rotation_euler = (0, 0, math.radians(angle))
        aim(cam, (5.3, 0, 8.2), elevation, 28)
        bpy.context.scene.render.filepath = os.path.join(OUT, "IceDrill_D%d_%s.png" % (level, view))
        bpy.ops.render.render(write_still=True)
        print("RENDERED", bpy.context.scene.render.filepath)
    root.rotation_euler = (0, 0, 0)
    bpy.data.objects.remove(title, do_unlink=True)

# ---------- attachment map: station 100 with its attachment points ----------

root100 = models[10][0]
set_visible(tree(root100), True)
for other in (1, 5):
    set_visible(tree(models[other][0]), False)
set_visible([o for o in tree(root100) if o.name.startswith("FxPreview") or any(k in o.name for k in ("Bit", "Lamp", "Gear", "NamePlate"))], False)
markers = []
for empty in [o for o in tree(root100) if o.type == "EMPTY" and "_Att_" in o.name]:
    cone = bmesh.new()
    cylinder(cone, (0, 0, 0), 0.22, 0.7, 8, top=0.0)
    mesh = bpy.data.meshes.new("Marker")
    cone.to_mesh(mesh)
    cone.free()
    marker = bpy.data.objects.new("Marker_" + empty.name, mesh)
    marker.matrix_world = empty.matrix_world
    marker.data.materials.append(MATERIALS["BuildingPaletteGlow"])
    uv = mesh.uv_layers.new()
    for loop in uv.data:
        loop.uv = swatch_uv("WarnRed")
    labels.objects.link(marker)
    markers.append(marker)
    tag = label(empty.name.split("_Att_")[1], empty.matrix_world.translation + Vector((0, -0.8, 0.45)), 0.38)
    markers.append(tag)
set_visible(tree(models[1][0]) + tree(models[5][0]), False)
bpy.context.view_layer.update()  # the labels' matrix_world must exist before it is turned below
set_visible([pet_label, avatar_label] + [o for o in collection("Reference").all_objects], False)
aim(cam, (0.3, 0, 7.6), 18, 21)
root100.rotation_euler = (0, 0, math.radians(-25))
for m in markers:
    m.matrix_world = Matrix.Rotation(math.radians(-25), 4, "Z") @ m.matrix_world
bpy.context.scene.render.filepath = os.path.join(OUT, "IceDrill_D10_attachments.png")
bpy.ops.render.render(write_still=True)
for m in markers:
    bpy.data.objects.remove(m, do_unlink=True)
root100.rotation_euler = (0, 0, 0)
set_visible([o for o in bpy.data.objects], True)

# ---------- the kit sheet ----------

for level in (1, 5, 10):
    set_visible(tree(models[level][0]), False)
set_visible([o for o in collection("Reference").all_objects] + [pet_label, avatar_label], False)
kit_coll = collection("Kit")
x, row_y = 0.0, 0
rows = [KIT[:9], KIT[9:]]
for r, row in enumerate(rows):
    x = 0.0
    width_total = sum(w for _, _, w in row) + 1.1 * (len(row) - 1)
    x = -width_total / 2
    for name, build, width in row:
        b = Builder("Kit" + name.split(" ")[0], kit_coll)
        b.add("", build())
        objs = b.finish()
        b.root.location = (x + width / 2, 0, 0 if r == 0 else 0)
        b.root.location.z = 0
        b.root.location.y = r * 7.0
        label(name, (x + width / 2, -1.6 + r * 7.0, 0.1), 0.42, kit_coll)
        x += width + 1.1
bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 1800, 1000
aim(cam, (0, 3.5, 1.6), 30, 26)
bpy.context.scene.render.filepath = os.path.join(OUT, "Kit_sheet.png")
bpy.ops.render.render(write_still=True)
set_visible([o for o in bpy.data.objects], True)
set_visible([o for o in kit_coll.all_objects], False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "IceDrillStyleTest.blend"))
print("DONE")
