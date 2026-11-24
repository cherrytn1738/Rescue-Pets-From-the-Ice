# ice_drill_tiers_v2.py - building style test v2: the Ice Drill's five tiers, built from the building kit
# (building_kit.py + building_kit_fantasy.py). NOT the voxel style: that one is for pets only.
#
#   Scrappy (1 owned)          junk-built crooked tripod, rusty and patched; no glow
#   Workshop (10)              timber shed with a copper roof, brass boiler, flywheel and belt; warm glow
#   Frost-tech (25)            sleek white twin pods on a rounded deck, a frost coil spire; cyan glow
#   Enchanted (50)             floating rock islands over a rune circle, a crystal drill; violet glow
#   Legendary (100)            the Mecha Mole Titan: a robot mole with a drill nose, digging claws and
#                              glowing eyes; gold and aurora trim
#
# Every tier is a station model with the same named attachment points (Bit, Lamp1/2, Gear1/2, Steam1/2,
# Hit, Trail, NamePlate, and Crown on the Titan), so the five upgrade part sets snap onto any tier. Each
# tier gets its own look for those sets; this test builds the Legendary look:
#   1 a better working part (a diamond drill nose), 2 lights (aurora shoulder beacons), 3 moving extras
#   (brass shoulder gears, steam from the back stacks), 4 hit particles (chips and sparks),
#   5 the signature flourish (a crystal trail round the nose, a jewelled crown, the name plate, a
#   sparkle aura). Particles are FX stand-ins (FxPreview_*) in these renders.
#
# Run it through the Blender MCP (execute_blender_code, at the top level) or headless:
#   REPO = r"...\RescuePetsFromTheIce"; BUNNY_BLEND = r"...\Bunny.blend"; OUT = r"...\store-assets\style-test\v2"
#   MODE = "build" | "render"
#   exec(open(REPO + r"\tools\blender\ice_drill_tiers_v2.py", encoding="utf-8").read())
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

TOOLS = os.path.join(REPO, "tools", "blender")
GLOW_STRENGTH = 2.0
exec(open(os.path.join(TOOLS, "model_helpers.py"), encoding="utf-8").read())
exec(open(os.path.join(TOOLS, "building_kit.py"), encoding="utf-8").read())
exec(open(os.path.join(TOOLS, "building_kit_fantasy.py"), encoding="utf-8").read())

SCENE_NAME = "StyleTestV2"
MESH_BUDGET = 5000
PET_STUDS = 3.0  # the pet size asked for (about 3 studs)
AVATAR_STUDS = 5.5


# ---------- scene ----------

def fresh_scene():
    """A separate scene, so the user's own scene is never touched. Everything in it is rebuilt."""
    scene = bpy.data.scenes.get(SCENE_NAME) or bpy.data.scenes.new(SCENE_NAME)
    for obj in list(scene.collection.all_objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(scene.collection.children_recursive):
        bpy.data.collections.remove(coll)
    for mesh in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(mesh)
    for curve in [c for c in bpy.data.curves if c.users == 0]:
        bpy.data.curves.remove(curve)
    if bpy.context.window:
        bpy.context.window.scene = scene
    return scene


def coll_in(scene, name):
    coll = bpy.data.collections.new(name)
    scene.collection.children.link(coll)
    return coll


class Builder:
    """The Parts (solid and glow meshes) of one model, finished under a root empty."""

    def __init__(self, name, coll):
        self.name, self.coll, self.parts, self.made = name, coll, {}, []
        self.root = bpy.data.objects.new(name, None)
        coll.objects.link(self.root)

    def add(self, role, pieces, matrix=Matrix()):
        solid, glow = split(pieces)
        for group, is_glow in ((solid, False), (glow, True)):
            if group:
                key = self.name + role + ("Glow" if is_glow else "")
                self.parts.setdefault(key, Part(key, is_glow)).add(group, matrix)

    def finish(self):
        for part in self.parts.values():
            obj = part.finish(self.coll, MATERIALS)
            obj.parent = self.root
            self.made.append(obj)
        self.parts = {}
        return self.made


def attach(builder, atts):
    for name, matrix in atts.items():
        empty = bpy.data.objects.new(builder.name + "_Att_" + name, None)
        empty.empty_display_type, empty.empty_display_size = "ARROWS", 0.6
        empty.matrix_world = matrix
        builder.coll.objects.link(empty)
        empty.parent = builder.root


def down(p):
    return frame(p, out=(0, 0, -1), up=(0, 1, 0))


def up_(p):
    return frame(p, out=(0, 0, 1), up=(0, 1, 0))


def front(p, tilt=0.0):
    return frame(p, out=(0, -1, tilt))


def V(*a):
    return Vector(a)


# ---------- tier 1: Scrappy ----------

def tier_scrappy(coll):
    b = Builder("IceDrillScrappy", coll)
    for size, swatch, loc, turn in (((3.6, 1.0, 0.25), "PineDark", (-0.3, -1.0, 0), 0.12), ((3.0, 0.9, 0.25), "Pine", (0.4, 0.3, 0), -0.18),
                                    ((2.6, 0.8, 0.22), "PineLight", (-0.2, 1.3, 0), 0.25)):
        b.add("Frame", place(block(size, swatch, corner=0.1, edge=0.06), M(loc, (0, 0, turn))))
    apex = V(0.15, 0.05, 4.6)
    b.add("Frame", beam_between((-1.9, -1.4, 0.2), apex + V(-0.1, -0.05, 0.6), 0.42, swatch="PineDark"))
    b.add("Frame", pipe_between((1.8, -1.1, 0.2), apex + V(0.12, 0, 0.45), 0.16, "Rust"))
    b.add("Frame", beam_between((0.1, 1.9, 0.2), apex + V(0, 0.1, 0.55), 0.36, swatch="PineLight"))
    for tilt in (0.3, -0.5):
        ring = bmesh.new()
        torus(ring, Matrix.Translation(apex + V(0, 0, 0.25)) @ Matrix.Rotation(tilt, 4, "X"), 0.38, 0.08, 12, 5)
        b.add("Frame", [(ring, "RustDark", 0.0, False)])
    # a patch plate bolted onto the dark leg
    mid = (V(-1.9, -1.4, 0.2) + apex) / 2
    b.add("Frame", place(block((0.6, 0.7, 0.1), "PatchGreen", corner=0.05, edge=0.03), front(mid + V(0, -0.22, 0), 0.2)))
    b.add("Frame", place(bolt(0.07, "RustDark"), front(mid + V(0.18, -0.3, 0.15))))
    b.add("Frame", place(bolt(0.07, "RustDark"), front(mid + V(-0.2, -0.3, -0.2))))
    # the crank: an old rusty cart wheel with a handle
    hub = apex + V(0.5, 0, -0.35)
    b.add("Wheel", place(spoked_gear(0.75, 10, 0.2, 0.12, 4, "Rust", "RustDark"), frame(hub, out=(1, 0, 0))))
    b.add("Frame", beam_between(hub + V(0.2, 0, 0.55), hub + V(0.55, 0, 0.55), 0.12, swatch="Iron"))
    b.add("Frame", place(cyl(0.1, 0.4, "PineLight", 8), frame(hub + V(0.55, 0, 0.55), out=(1, 0, 0))))
    b.add("Frame", place(cyl(0.14, apex.z - 1.4, "Iron", 10), M((apex.x, apex.y, 1.4))))
    # junk round it: a rusty barrel and a dented bucket
    b.add("Junk", place(cyl(0.55, 1.2, "Rust", 12), M((2.3, 0.9, 0))))
    for z in (0.25, 0.95):
        b.add("Junk", place(trim_ring(0.56, 0, "RustDark", minor=0.06, segments=12), M((2.3, 0.9, z))))
    b.add("Junk", place(cyl(0.5, 0.08, "PineDark", 12), M((2.3, 0.9, 1.2))))
    b.add("Junk", place(cyl(0.3, 0.6, "Steel", 10, top=0.42), M((-2.1, 0.7, 0), (0.12, 0, 0))))
    atts = {"Bit": down((apex.x, apex.y, 1.4)), "Lamp1": up_((2.3, 0.9, 1.28)), "Gear1": front((apex.x, -0.42, apex.z - 0.9)),
            "Steam1": up_(apex + V(0, 0, 0.7)), "Hit": frame((apex.x, -0.7, 0.3), out=(0, -1, 0.6)),
            "Trail": down((apex.x, apex.y, -0.6)), "NamePlate": front((0, -1.9, 0.45))}
    return b, atts, ("Iron", None)


# ---------- tier 2: Workshop ----------

def lantern(glass="LampYellow", metal="Brass"):
    g = bmesh.new()
    cylinder(g, (0, 0, 0.12), 0.22, 0.42, 10)
    top, bottom = bmesh.new(), bmesh.new()
    cylinder(top, (0, 0, 0.54), 0.3, 0.12, 10, top=0.16)
    cylinder(bottom, (0, 0, 0), 0.28, 0.12, 10)
    return [(g, glass, 0.0, True), (top, metal, 0.02, False), (bottom, metal, 0.02, False)]


def tier_workshop(coll):
    b = Builder("IceDrillWorkshop", coll)
    b.add("Shed", block((6.0, 5.0, 0.5), "Pine", corner=0.3, edge=0.12))
    for y in (-1.5, -0.5, 0.5, 1.5):
        b.add("Shed", place(block((5.7, 0.07, 0.05), "PineDark", corner=0.02, edge=0.01), M((0, y, 0.5))))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.add("Shed", beam_between((sx * 2.4, sy * 1.9, 0.5), (sx * 2.4, sy * 1.9, 6.0), 0.5, swatch="PineLight"))
            b.add("Shed", place(cyl(0.32, 0.18, "Brass", 8), M((sx * 2.4, sy * 1.9, 0.5))))
    for sy in (-1, 1):
        b.add("Shed", beam_between((-2.7, sy * 1.9, 5.85), (2.7, sy * 1.9, 5.85), 0.42, swatch="PineDark"))
    for sx in (-1, 1):
        b.add("Shed", beam_between((sx * 2.4, -2.2, 5.85), (sx * 2.4, 2.2, 5.85), 0.42, swatch="PineDark"))
    # gable roof: two copper slabs and a brass ridge
    for side in (-1, 1):
        slab = bmesh.new()
        rounded_block(slab, (6.6, 3.0, 0.3), M((0, side * 1.25, 6.85), (side * -math.radians(32), 0, 0)), corner=0.15, edge=0.08, corner_seg=2, edge_seg=1)
        b.add("Roof", [(slab, "Copper", 0.0, False)])
    b.add("Roof", place(cyl(0.2, 6.8, "Brass", 10), frame((-3.4, 0, 7.62), out=(1, 0, 0))))
    # the brass boiler, its firebox and chimney
    b.add("Boiler", place(cyl(0.85, 2.6, "Brass", 16), frame((-2.0, 0.9, 1.6), out=(1, 0, 0))))
    for x in (-1.5, -0.4):
        b.add("Boiler", place(trim_ring(0.87, 0, "Copper", minor=0.08, segments=16), frame((x, 0.9, 1.6), out=(1, 0, 0))))
    b.add("Boiler", place(block((1.2, 1.0, 0.75), "Iron", corner=0.15, edge=0.08), M((-0.7, 0.2, 0.5))))
    window = bmesh.new()
    rounded_block(window, (0.7, 0.1, 0.32), M((-0.7, -0.33, 0.85)), corner=0.08, edge=0.03, corner_seg=2, edge_seg=1)
    b.add("Boiler", [(window, "FlameOrange", 0.0, True)])
    b.add("Boiler", place(cyl(0.26, 0.12, "Brass", 12), frame((-1.0, 0.04, 1.75), out=(0, -1, 0))))
    b.add("Boiler", place(cyl(0.2, 0.06, "Cream", 12), frame((-1.0, -0.06, 1.75), out=(0, -1, 0))))
    b.add("Boiler", pipe_between((-1.4, 0.9, 2.4), (-1.4, 0.9, 8.4), 0.24, "Brass"))
    b.add("Boiler", place(cyl(0.36, 0.3, "Copper", 12, top=0.26), M((-1.4, 0.9, 8.4))))
    # the drill head: a copper gearbox, a flywheel and its belt
    b.add("Drill", place(block((1.3, 1.2, 1.1), "Copper", corner=0.2, edge=0.1), M((1.3, -0.4, 4.3))))
    b.add("Drill", place(cyl(0.16, 2.9, "Steel", 10), M((1.3, -0.4, 1.4))))
    collar = bmesh.new()
    torus(collar, M((1.3, -0.4, 0.55)), 0.5, 0.14, 12, 5)
    b.add("Drill", [(collar, "PineDark", 0.0, False)])
    b.add("Flywheel", place(spoked_gear(1.0, 14, 0.24, 0.12, 5, "Brass", "Copper"), front((-0.9, -0.55, 4.4))))
    for z0, z1 in ((5.38, 5.15), (3.42, 3.95)):
        b.add("Drill", trim_strip((-0.9, -0.72, z0), (1.3, -0.72, z1), 0.12, "Rubber"))
    # a hanging lantern under the front eave
    b.add("Lantern", chain(3, 0.09, "Brass"), M((2.4, -2.35, 5.7)))
    b.add("Lantern", lantern(), M((2.4, -2.35, 4.4)))
    atts = {"Bit": down((1.3, -0.4, 1.4)), "Lamp1": up_((1.0, -0.4, 5.4)), "Gear1": front((1.3, -1.0, 4.85)),
            "Steam1": up_((-1.4, 0.9, 8.7)), "Hit": frame((1.3, -1.2, 0.6), out=(0, -1, 0.6)),
            "Trail": down((1.3, -0.4, -0.6)), "NamePlate": front((0, -2.52, 0.25))}
    return b, atts, ("Brass", None)


# ---------- tier 3: Frost-tech ----------

def tier_frosttech(coll):
    b = Builder("IceDrillFrostTech", coll)
    b.add("Deck", block((9.0, 7.0, 0.8), "SnowWhite", corner=1.4, edge=0.3))
    b.add("Deck", place(block((8.0, 6.0, 0.3), "IceBlue", corner=1.1, edge=0.12), M((0, 0, 0.8))))
    for p0, p1 in (((-3.0, -3.53, 0.42), (3.0, -3.53, 0.42)), ((-3.0, 3.53, 0.42), (3.0, 3.53, 0.42)),
                   ((-4.53, -2.0, 0.42), (-4.53, 2.0, 0.42)), ((4.53, -2.0, 0.42), (4.53, 2.0, 0.42))):
        b.add("Deck", trim_strip(p0, p1, 0.16, "AuroraCyan", True))
    for X, letter in ((-2.6, "A"), (2.6, "B")):
        pod = "Pod" + letter
        for sx in (-1, 1):
            b.add(pod, beam_between((X + sx * 0.85, 0, 1.1), (X + sx * 0.5, 0, 3.4), 0.26, swatch="SteelLight"))
        b.add(pod, place(block((2.2, 2.0, 3.6), "SnowWhite", corner=0.95, edge=0.6), M((X, 0, 3.0))))
        b.add(pod, place(block((1.7, 0.3, 0.55), "NavyIce", corner=0.25, edge=0.1), M((X, -0.92, 5.3))))
        b.add(pod, trim_strip((X - 0.7, -1.04, 5.15), (X + 0.7, -1.04, 5.15), 0.08, "AuroraCyan", True))
        b.add(pod, trim_strip((X - 0.7, -1.04, 5.75), (X + 0.7, -1.04, 5.75), 0.08, "AuroraCyan", True))
        b.add(pod, place(cyl(0.95, 0.25, "SteelLight", 16), M((X, 0, 6.6))))
        for sx in (-1, 1):  # frost fins
            fin = bmesh.new()
            rounded_block(fin, (0.14, 1.2, 1.8), M((X + sx * 1.15, 0.2, 4.4), (0, sx * 0.25, 0)), corner=0.06, edge=0.05, corner_seg=2, edge_seg=1, taper=0.6)
            b.add(pod, [(fin, "GlacierBlue", 0.0, False)])
        ring = bmesh.new()
        torus(ring, M((X, 0, 1.15)), 0.62, 0.1, 16, 5)
        b.add("Deck", [(ring, "AuroraCyan", 0.0, True)])
        b.add("Conduits", pipe_between((X - math.copysign(1.1, X), 0.2, 5.0), (math.copysign(0.65, X), 0.6, 5.0), 0.16, "SteelLight"))
    b.add("Coil", place(coil(0.62, 6.4, turns=8, core="SteelDark", wire="IceBlue", top="AuroraCyan"), M((0, 0.6, 1.1))))
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 2
        fin = bmesh.new()
        rounded_block(fin, (0.14, 0.9, 1.4), M((0.85 * math.cos(a), 0.6 + 0.85 * math.sin(a), 1.8), (0, 0, a)), corner=0.05, edge=0.04, corner_seg=2, edge_seg=1, taper=0.5)
        b.add("Coil", [(fin, "GlacierBlue", 0.0, False)])
    b.add("Deck", place(cyl(0.55, 0.12, "GlacierBlue", 6), front((0, -3.5, 0.42))))
    for k in range(3):
        b.add("Deck", place(block((0.12, 0.8, 0.08), "SnowWhite", corner=0.03, edge=0.02), front((0, -3.62, 0.42)) @ M((0, 0, 0), (0, 0, k * math.pi / 3))))
    atts = {"Bit": down((-2.6, 0, 3.0)), "Bit2": down((2.6, 0, 3.0)), "Lamp1": up_((-2.6, 0, 6.85)), "Lamp2": up_((2.6, 0, 6.85)),
            "Gear1": front((-2.6, -1.0, 4.0)), "Gear2": front((2.6, -1.0, 4.0)), "Steam1": up_((0, 0.6, 8.3)),
            "Hit": frame((-2.6, -0.9, 1.2), out=(0, -1, 0.6)), "Trail": down((-2.6, 0, 0.6)), "NamePlate": front((0, -3.55, 0.4))}
    return b, atts, ("FrostTech", None)


# ---------- tier 4: Enchanted ----------

def tier_enchanted(coll):
    b = Builder("IceDrillEnchanted", coll)
    dais = bmesh.new()
    lathe(dais, [(0, 0), (4.2, 0), (4.2, 0.5), (3.9, 0.8), (0, 0.8)], 6)
    b.add("Dais", [(dais, "Moonstone", 0.05, False)])
    b.add("Dais", place(trim_ring(4.05, 0, "RuneViolet", minor=0.08, segments=6), M((0, 0, 0.55))))
    b.add("Dais", place(rune_ring(3.1), M((0, 0, 0.82))))
    for top, radius, thick, role in ((5.2, 2.3, 0.5, "IslandA"), (8.0, 1.8, 0.45, "IslandB"), (10.6, 1.3, 0.4, "IslandC")):
        b.add(role, place(floating_platform(radius, thick, "Moonstone", "StoneDark", "Gold", tip=False), M((0, 0, top), (0, 0, top * 0.3))))
    b.add("Orbit", place(rune_ring(2.7, "AuroraGreen"), M((0, 0, 6.4), (0.32, 0.12, 0))))
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        b.add("Orbit", place(crystal(1.0, 0.18, "AuroraGreen", (0.3, 0.2)), M((3.3 * math.cos(a), 3.3 * math.sin(a), 2.2 + 0.6 * (k % 2)))))
    b.add("Crown", place(crystal_cluster(1.25, "CrystalCyan", "Moonstone"), M((0, 0, 10.6))))
    b.add("Crown", place(gem(0.42, "MagicPink"), M((0, 0, 13.3), (0, 0, 0.3))))
    atts = {"Bit": down((0, 0, 2.15)), "Lamp1": up_((1.75, 0, 5.2)), "Lamp2": up_((-1.3, 0, 8.0)), "Gear1": front((0, -2.05, 4.85)),
            "Steam1": up_((0, 0, 13.0)), "Hit": frame((0, -1.0, 0.9), out=(0, -1, 0.6)), "Trail": down((0, 0, 0.3)),
            "NamePlate": front((0, -3.7, 0.4))}
    return b, atts, ("Crystal", None)


# ---------- tier 5: Legendary, the Mecha Mole Titan ----------

def paw(b, role, wrist, direction, side):
    """A big mole paw at `wrist`, its three claws pointing along `direction`."""
    d = Vector(direction).normalized()
    lateral = d.cross(Vector((0, 0, 1)))
    if lateral.length < 1e-3:
        lateral = Vector((1, 0, 0))
    lateral.normalize()
    b.add(role, place(block((1.5, 0.75, 1.2), "MoleFurLight", corner=0.35, edge=0.3), Matrix.Translation(wrist) @ align_z(d) @ M((0, 0, -0.2))))
    for k in (-1, 0, 1):
        base = wrist + d * 0.9 + lateral * (k * 0.45)
        b.add(role, place(cyl(0.2, 0.9, "SteelLight", 8, top=0.0, bevel=0.0), Matrix.Translation(base) @ align_z(d + Vector((0, 0, -0.15)))))


def tier_titan(coll, name="IceDrillTitan"):
    b = Builder(name, coll)
    b.add("Platform", block((10.4, 9.0, 0.9), "Gunmetal", corner=0.9, edge=0.25))
    b.add("Platform", place(block((9.8, 8.4, 0.3), "StoneLight", corner=0.7, edge=0.1), M((0, 0, 0.9))))
    b.add("Trim", place(block((10.5, 9.1, 0.16), "Gold", corner=0.92, edge=0.06), M((0, 0, 0.72))))
    b.add("Trim", trim_strip((-3.6, -4.52, 0.4), (3.6, -4.52, 0.4), 0.16, "AuroraGreen", True))
    crater = bmesh.new()
    torus(crater, Matrix.Translation((0, -2.7, 1.2)) @ Matrix.Diagonal((1.3, 1, 0.45, 1)), 1.2, 0.35, 16, 6)
    b.add("Platform", [(crater, "StoneDark", 0.0, False)])
    for k in range(5):  # broken ice round the dig
        a = k * 1.25
        b.add("Platform", place(crystal(0.55, 0.22, "IceBlue", (0.5 * math.cos(a), 0.5 * math.sin(a)), glow=False), M((1.6 * math.cos(a) * 1.2, -2.7 + 1.0 * math.sin(a), 1.15))))
    # legs and feet
    for sx in (-1, 1):
        b.add("Legs", place(cyl(0.75, 1.9, "Gunmetal", 14), M((sx * 1.5, 0.7, 1.1))))
        b.add("Legs", place(block((1.8, 2.5, 0.8), "SteelDark", corner=0.6, edge=0.3), M((sx * 1.6, 0.2, 1.1))))
        for k in (-1, 0, 1):
            b.add("Legs", place(cyl(0.18, 0.6, "Gold", 8, top=0.0, bevel=0.0), frame((sx * 1.6 + k * 0.5, -1.0, 1.4), out=(0, -1, -0.2))))
    # the body: a round egg of mole-brown plates, a pale belly, gold and aurora bands, the crest
    body = bmesh.new()
    lathe(body, [(0, 2.5), (2.3, 2.6), (3.1, 3.8), (3.3, 5.2), (3.0, 6.8), (2.2, 7.9), (0, 8.3)], 20)
    b.add("Body", [(body, "MoleFur", 0.0, False)])
    belly = bmesh.new()
    lathe(belly, [(0, 0), (1.9, 0), (1.6, 0.35), (0, 0.45)], 16, frame((0, -2.85, 4.9), out=(0, -1, 0.05)))
    b.add("Body", [(belly, "MoleFurLight", 0.0, False)])
    for z, radius in ((2.85, 2.55), (7.35, 2.6)):
        b.add("Trim", place(trim_ring(radius, 0, "Gold", minor=0.13, segments=20), M((0, 0, z))))
    b.add("Trim", place(trim_ring(3.27, 0, "AuroraGreen", True, minor=0.1, segments=20), M((0, 0, 5.6))))
    b.add("Body", place(crest(1.5, 1.8, 0.2, "Gold", "DeepIce", "SnowWhite", "AuroraCyan"), front((0, -3.2, 6.45), 0.15)))
    for k in range(8):
        a = math.pi + k * math.pi / 7  # round the front half
        b.add("Body", place(rivet(0.11, "Gold"), frame((3.2 * math.cos(a), 3.2 * math.sin(a), 4.2), out=(math.cos(a), math.sin(a), 0))))
    # back exhaust stacks
    for sx in (-1, 1):
        b.add("Stacks", place(cyl(0.42, 2.6, "Gunmetal", 12), Matrix.Translation((sx * 1.2, 2.5, 6.2)) @ Matrix.Rotation(-0.3, 4, "X")))
        b.add("Stacks", place(trim_ring(0.44, 0, "Gold", minor=0.08, segments=12), Matrix.Translation((sx * 1.2, 2.5, 6.2)) @ Matrix.Rotation(-0.3, 4, "X") @ M((0, 0, 2.5))))
    # the head: round, leaning forward, with ears, big glowing eyes, brows, blush and buck teeth
    head = (0, -1.0, 10.0)
    hb = bmesh.new()
    blob(hb, head, (2.7, 2.4, 2.3), 3)
    b.add("Head", [(hb, "MoleFur", 0.0, False)])
    visor = bmesh.new()
    blob(visor, (0, -1.95, 10.65), (2.15, 1.45, 1.0), 2)
    b.add("Head", [(visor, "Gunmetal", 0.0, False)])
    for sx in (-1, 1):
        b.add("Head", place(cyl(0.72, 0.4, "MoleFurLight", 14), frame((sx * 2.35, -0.6, 11.4), out=(sx, 0, 0.45))))
        b.add("Head", place(trim_ring(0.74, 0, "Gold", minor=0.09, segments=14), frame((sx * 2.35, -0.6, 11.4), out=(sx, 0, 0.45)) @ M((0, 0, 0.34))))
        b.add("Eyes", place(cartoon_eye(0.8, "CrystalCyan", look=(0.0, 0.18), lid=None), frame((sx * 1.0, -2.95, 10.7), out=(0, -1, 0.12))))
        # determined brows: the inner ends tip down
        b.add("Head", place(brow(1.15, sx * 0.28, "Gunmetal"), frame((sx * 1.05, -3.0, 11.75), out=(0, -1, 0.18))))
        blush = bmesh.new()
        blob(blush, (sx * 1.9, -2.5, 9.6), (0.48, 0.22, 0.3), 1)
        b.add("Head", [(blush, "Blush", 0.0, False)])
    b.add("Head", place(grin(1.4, 0.3, "EyeDark", "EyeWhite", 2), frame((0, -2.75, 8.35), out=(0, -1, -0.35))))
    b.add("Head", place(trim_ring(0.95, 0, "Gold", minor=0.14, segments=16), frame((0, -3.15, 9.65), out=(0, -1, -0.3))))
    # arms: the left digs into the crater, the right waves
    for side, sx, elbow_at, hand_at in (("ArmL", -1, (-4.1, -1.7, 5.1), (-3.0, -3.1, 3.4)), ("ArmR", 1, (4.3, -1.3, 7.6), (4.6, -1.9, 9.4))):
        shoulder = Vector((sx * 3.15, -0.4, 6.3))
        b.add(side, place(cyl(1.1, 0.9, "Gunmetal", 14), frame(shoulder - Vector((sx * 0.25, 0, 0)), out=(sx, 0, 0))))
        upper = bmesh.new()
        sweep(upper, [shoulder, Vector(elbow_at)], 0.72, 12)
        lower = bmesh.new()
        sweep(lower, [Vector(elbow_at), Vector(hand_at)], 0.65, 12)
        joint = bmesh.new()
        blob(joint, elbow_at, (0.82, 0.82, 0.82), 2)
        b.add(side, [(upper, "SteelDark", 0.0, False), (lower, "SteelDark", 0.0, False), (joint, "Gunmetal", 0.0, False)])
        paw(b, side, Vector(hand_at), Vector(hand_at) - Vector(elbow_at), sx)
    nose_dir = Vector((0, -1, -0.3)).normalized()
    atts = {"Bit": frame((0, -3.2, 9.6), out=nose_dir), "Lamp1": up_((3.1, -0.4, 7.15)), "Lamp2": up_((-3.1, -0.4, 7.15)),
            "Gear1": frame((3.85, -0.4, 6.3), out=(1, 0, 0)), "Gear2": frame((-3.85, -0.4, 6.3), out=(-1, 0, 0)),
            "Steam1": up_((1.2, 3.25, 8.65)), "Steam2": up_((-1.2, 3.25, 8.65)),
            "Hit": frame((0, -3.7, 1.25), out=(0, -1, 0.6)), "Trail": frame((0, -3.2, 9.6), out=nose_dir),
            "Crown": up_((0, -1.0, 12.2)), "NamePlate": front((0, -4.52, 0.45))}
    return b, atts, ("TitanNose", None)


# ---------- working parts (each tier's own, on Bit) and the Legendary upgrade sets ----------

def working_part(b, atts, kind):
    bits = [atts[k] for k in sorted(atts) if k.startswith("Bit")]
    for i, matrix in enumerate(bits):
        role = "Bit" + "AB"[i]
        if kind == "Iron":
            b.add(role, place(auger("Iron"), matrix))
        elif kind == "Brass":
            b.add(role, place(spiral_bit(2.2, 0.5, "Brass", "SteelLight"), matrix))
        elif kind == "FrostTech":
            b.add(role, place(spiral_bit(2.2, 0.55, "DeepIce", "SnowWhite", 3.5), matrix))
        elif kind == "Crystal":
            b.add(role, place(crystal(2.4, 0.78, "RuneViolet"), matrix))
        elif kind == "TitanNose":
            b.add(role, place(spiral_bit(2.8, 0.92, "Brass", "SteelLight", 3.0), matrix))
        elif kind == "TitanDiamond":  # upgrade 1, Legendary look: a glowing diamond nose
            b.add(role, place(spiral_bit(3.0, 0.95, "CrystalCyan", "Diamond", 3.0, glow=True), matrix))


def legendary_upgrades(b, fx, atts):
    working_part(b, atts, "TitanDiamond")  # 1st: the better working part
    for key in ("Lamp1", "Lamp2"):  # 2nd: aurora beacons on the shoulders
        b.add("Beacon" + key[-1], place(warning_lamp(0.42, "AuroraGreen", "Gold", "Gunmetal"), atts[key]))
    for key in ("Gear1", "Gear2"):  # 3rd: spinning brass shoulder gears (each its own mesh) and steam
        b.add("Gear%sBig" % key[-1], place(spoked_gear(0.95, 14, 0.28, 0.16, 5, "Brass", "Gold"), atts[key] @ M((0, 0, 0.15))))
        b.add("Gear%sSmall" % key[-1], place(spoked_gear(0.5, 9, 0.28, 0.13, 3, "Copper", "Gold"), atts[key] @ M((0.85, 0.85, 0.35))))
    for key in ("Steam1", "Steam2"):
        for k, (dx, dz, r) in enumerate(((0.0, 0.4, 0.3), (0.2, 0.95, 0.42), (-0.15, 1.6, 0.55))):
            puff = bmesh.new()
            blob(puff, (dx, 0, dz), (r, r, r * 0.85), 1)
            fx.add("Steam" + key[-1], place([(puff, "SnowWhite", 0.0, False)], atts[key]))
    # 4th: chips and sparks on every hit
    pieces = []
    for k in range(9):
        a = k * 2.4
        chip = bmesh.new()
        blob(chip, (0.7 * math.cos(a), 0.7 * math.sin(a), 0.3 + 0.2 * k), (0.2, 0.14, 0.25), 1, rotation=(a, 0.5 * k, 0))
        pieces.append((chip, "IceBlue" if k % 2 else "Diamond", 0.0, False))
    for k in range(6):
        a = k * 1.1 + 0.4
        spark = bmesh.new()
        cylinder(spark, (0.4 * math.cos(a), 0.4 * math.sin(a), 0.2), 0.05, 0.7, 4, direction=(math.cos(a), math.sin(a), 1.3), top=0.0)
        pieces.append((spark, "LampYellow", 0.0, True))
    fx.add("Hit", place(pieces, atts["Hit"]))
    # 5th, the signature flourish: a jewelled crown, a crystal trail round the nose, the name plate, sparkles
    crown = []
    crown += trim_ring(1.0, 0.1, "Gold", minor=0.16, segments=20)
    for k in range(5):
        a = math.pi / 2 + (k - 2) * 0.55
        spike = bmesh.new()
        cylinder(spike, (math.cos(a), math.sin(a) - 0.0, 0.1), 0.22, 0.75 + (0.25 if k == 2 else 0), 6, top=0.0)
        crown.append((spike, "Gold", 0.0, False))
        crown += place(gem(0.16, "MagicPink" if k == 2 else "AuroraCyan"), frame((math.cos(a) * 1.05, math.sin(a) * 1.05 - 0.05, 0.35), out=(math.cos(a), math.sin(a), 0)))
    b.add("Crown", place(crown, atts["Crown"] @ M((0, 0, -0.35), (0.25, 0, 0))))
    trail = []
    for k in range(12):
        a = k * 0.85
        g = bmesh.new()
        blob(g, (1.0 * math.cos(a) * (1 - k / 20), 1.0 * math.sin(a) * (1 - k / 20), 0.3 + k * 0.28), (0.13, 0.13, 0.19), 1)
        trail.append((g, "CrystalCyan" if k % 2 else "Diamond", 0.0, True))
    fx.add("Trail", place(trail, atts["Trail"]))
    b.add("NamePlate", place(name_plate(3.2, 0.62, "PineLight", "Gold"), atts["NamePlate"]))
    sparkles = []
    for k in range(10):
        a = k * 2.2
        s = bmesh.new()
        lathe(s, [(0, -0.22), (0.09, 0), (0, 0.22)], 4, M((4.6 * math.cos(a), 1.0 + 3.6 * math.sin(a), 3.5 + 0.9 * (k % 5))))
        sparkles.append((s, "LampYellow", 0.0, True))
    fx.add("Sparkles", sparkles)


# ---------- reference figures ----------

def reference(coll):
    with bpy.data.libraries.load(BUNNY_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in ("Bunny", "BunnyRig")]
    for obj in dst.objects:
        coll.objects.link(obj)
    rig = next(o for o in dst.objects if o.type == "ARMATURE")
    bunny = next(o for o in dst.objects if o.type == "MESH")
    bpy.context.view_layer.update()
    height = max((bunny.matrix_world @ v.co).z for v in bunny.data.vertices) - min((bunny.matrix_world @ v.co).z for v in bunny.data.vertices)
    s = PET_STUDS / height
    rig.scale = (s, s, s)
    av = Builder("AvatarStandIn", coll)
    for sx in (-0.5, 0.5):
        av.add("Body", place(block((0.9, 0.9, 2.0), "SteelDark", corner=0.15, edge=0.1), M((sx, 0, 0))))
    av.add("Body", place(block((2.0, 1.0, 2.0), "Steel", corner=0.2, edge=0.12), M((0, 0, 2.0))))
    for sx in (-1, 1):
        av.add("Body", place(block((0.85, 0.85, 2.0), "Steel", corner=0.15, edge=0.1), M((sx * 1.45, 0, 2.0))))
    av.add("Body", place(block((1.15, 1.15, 1.5), "StoneLight", corner=0.3, edge=0.25), M((0, 0, 4.0))))
    av.finish()
    return rig, av.root, s


# ---------- build ----------

TIERS = [("Scrappy", "1 owned", tier_scrappy), ("Workshop", "10 owned", tier_workshop), ("Frost-tech", "25 owned", tier_frosttech),
         ("Enchanted", "50 owned", tier_enchanted), ("Legendary: Mecha Mole Titan", "100 owned", tier_titan)]


def build():
    global MATERIALS
    scene = fresh_scene()
    palette = write_palette(os.path.join(REPO, "assets", "textures", "BuildingPalette.png"))
    MATERIALS = palette_materials(palette)
    built = {}
    for name, owned, fn in TIERS:
        coll = coll_in(scene, "Tier " + name.split(":")[0])
        b, atts, (working, _) = fn(coll)
        working_part(b, atts, working)
        attach(b, atts)
        b.finish()
        built[name] = (b, atts)
    # the Titan's Masterwork: a second copy of the Titan with all five upgrades in their Legendary look
    coll = coll_in(scene, "Titan Masterwork")
    mb, matts = tier_titan(coll, "IceDrillTitanMW")[:2]
    fx = Builder("FxPreviewTitanMW", coll)
    legendary_upgrades(mb, fx, matts)
    mb.finish()
    fx.finish()
    fx.root.parent = mb.root
    built["Masterwork"] = (mb, matts)
    rig, avatar, pet_scale = reference(coll_in(scene, "Reference"))
    print("pet scale %.3f (bunny %.1f studs tall)" % (pet_scale, PET_STUDS))
    report = []
    for name, (b, _) in built.items():
        tris = [(o.name, sum(len(p.vertices) - 2 for p in o.data.polygons)) for o in b.made]
        over = [t for t in tris if t[1] > MESH_BUDGET]
        report.append("%-30s %2d meshes %6d tris, largest %s %d%s" % (name, len(tris), sum(t for _, t in tris),
                      *max(tris, key=lambda t: t[1]), "  OVER: %s" % over if over else ""))
    print("\n".join(report))
    return built, rig, avatar


# ---------- staging and rendering ----------

def visible(objs, on):
    for o in objs:
        o.hide_render = not on
        o.hide_set(not on)


def tree(root):
    out, frontier = [root], [root]
    while frontier:
        frontier = [o for o in bpy.data.objects if o.parent in frontier]
        out += frontier
    return out


def stage(scene):
    """Sky, snow, three suns, a camera, Standard colours, and a bloom pass for the glow meshes."""
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            pass
    scene.view_settings.view_transform = "Standard"
    try:
        scene.eevee.taa_render_samples = 48
    except AttributeError:
        pass
    world = bpy.data.worlds.get("StyleSky") or bpy.data.worlds.new("StyleSky")
    scene.world = world
    if world.node_tree is None:
        world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.42, 0.62, 0.84, 1)
    bg.inputs["Strength"].default_value = 0.55
    coll = coll_in(scene, "Stage")
    gm = bpy.data.meshes.new("Snow")
    gbm = bmesh.new()
    bmesh.ops.create_grid(gbm, x_segments=1, y_segments=1, size=300)
    gbm.to_mesh(gm)
    gbm.free()
    ground = bpy.data.objects.new("Snow", gm)
    coll.objects.link(ground)
    snow = bpy.data.materials.get("Snow") or bpy.data.materials.new("Snow")
    if snow.node_tree is None:
        snow.use_nodes = True
    sb = next(n for n in snow.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    sb.inputs["Base Color"].default_value = (0.55, 0.66, 0.78, 1)
    sb.inputs["Roughness"].default_value = 0.9
    ground.data.materials.append(snow)
    for name, rot, energy in (("Key", (50, 0, -35), 2.3), ("Fill", (65, 0, 120), 0.6), ("Rim", (35, 0, 190), 1.0)):
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
        light.data.energy, light.data.angle = energy, math.radians(4)
        light.rotation_euler = tuple(math.radians(r) for r in rot)
        coll.objects.link(light)
    cam = bpy.data.objects.new("StyleCam", bpy.data.cameras.new("StyleCam"))
    coll.objects.link(cam)
    scene.camera = cam
    bloom = False
    try:  # Blender 5: the compositor is a node group on the scene
        tree_ = bpy.data.node_groups.get("StyleBloom") or bpy.data.node_groups.new("StyleBloom", "CompositorNodeTree")
        tree_.nodes.clear()
        if not tree_.interface.items_tree:
            tree_.interface.new_socket("Image", in_out="INPUT", socket_type="NodeSocketColor")
            tree_.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        rl = tree_.nodes.new("CompositorNodeRLayers")
        glare = tree_.nodes.new("CompositorNodeGlare")
        out = tree_.nodes.new("NodeGroupOutput")
        for name, value in (("glare_type", "BLOOM"), ("quality", "HIGH")):
            if hasattr(glare, name):
                setattr(glare, name, value)
        if "Type" in glare.inputs:
            glare.inputs["Type"].default_value = "Bloom"
        if "Threshold" in glare.inputs:
            glare.inputs["Threshold"].default_value = 1.0
        elif hasattr(glare, "threshold"):
            glare.threshold = 1.0
        if "Strength" in glare.inputs:
            glare.inputs["Strength"].default_value = 0.6
        tree_.links.new(rl.outputs["Image"], glare.inputs["Image"])
        tree_.links.new(glare.outputs["Image"], out.inputs[0])
        scene.compositing_node_group = tree_
        bloom = True
    except Exception as error:  # bloom is a nicety: render without it
        print("bloom off:", error)
    print("bloom", bloom)
    return cam


def label(scene, text, location, size=0.8):
    curve = bpy.data.curves.new("Label", "FONT")
    curve.body, curve.size, curve.align_x = text, size, "CENTER"
    obj = bpy.data.objects.new("Label_" + text, curve)
    obj.location, obj.rotation_euler = location, (math.radians(90), 0, 0)
    ink = bpy.data.materials.get("LabelInk") or bpy.data.materials.new("LabelInk")
    if ink.node_tree is None:
        ink.use_nodes = True
    next(n for n in ink.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.03, 0.07, 0.16, 1)
    obj.data.materials.append(ink)
    scene.collection.objects.link(obj)
    return obj


def ortho(cam, target, elevation, scale, yaw=0.0, distance=120):
    target = Vector(target)
    e, y = math.radians(elevation), math.radians(yaw)
    eye = target + Vector((math.sin(y) * math.cos(e), -math.cos(y) * math.cos(e), math.sin(e))) * distance
    cam.data.type, cam.data.ortho_scale, cam.data.clip_end = "ORTHO", scale, 500
    cam.location = eye
    cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()


def persp(cam, target, eye, lens=50):
    cam.data.type, cam.data.lens, cam.data.clip_end = "PERSP", lens, 500
    cam.location = Vector(eye)
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()


def shoot(scene, path, x, y):
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = x, y, 100
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True, scene=scene.name)
    print("RENDERED", path)


def bounds_of(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


ROOT_NAMES = {"Scrappy": "IceDrillScrappy", "Workshop": "IceDrillWorkshop", "Frost-tech": "IceDrillFrostTech",
              "Enchanted": "IceDrillEnchanted", "Legendary: Mecha Mole Titan": "IceDrillTitan", "Masterwork": "IceDrillTitanMW"}


def render_all(which=("lineup", "closeups", "masterwork")):
    """Renders from what build() left in the scene (found by name, so it can run in a later call)."""
    scene = bpy.data.scenes[SCENE_NAME]
    if bpy.context.window:
        bpy.context.window.scene = scene
    cam = scene.camera if scene.camera and scene.camera.name == "StyleCam" else stage(scene)
    os.makedirs(OUT, exist_ok=True)
    roots = {name: bpy.data.objects[obj] for name, obj in ROOT_NAMES.items()}
    rig, avatar = bpy.data.objects["BunnyRig"], bpy.data.objects["AvatarStandIn"]
    bunny_objs = [rig] + list(rig.children)
    everything = [o for r in roots.values() for o in tree(r)]
    # 1) the line-up: five tiers, no upgrades, plus the pet and the avatar
    if "lineup" in which:
        lineup(scene, cam, roots, rig, avatar, everything)
    if "closeups" in which:
        closeups(scene, cam, roots, rig, everything)
    if "masterwork" in which:
        masterwork(scene, cam, roots, rig, avatar, everything)
    visible(everything, True)


def lineup(scene, cam, roots, rig, avatar, everything):
    visible(everything, False)
    x, gap, labels = 0.0, 2.6, []
    for name, owned, _ in TIERS:
        root = roots[name]
        visible(tree(root), True)
        root.rotation_euler = (0, 0, math.radians(-22))
        root.location = (0, 0, 0)
        bpy.context.view_layer.update()
        lo, hi = bounds_of(tree(root))
        root.location = (x - lo.x, 0, 0)
        labels.append(label(scene, name.split(":")[0], (x + (hi.x - lo.x) / 2, -15.0, 0.95), 0.62))
        labels.append(label(scene, owned, (x + (hi.x - lo.x) / 2, -15.0, 0.2), 0.45))
        x += (hi.x - lo.x) + gap
    rig.location = (x + 0.8, 0, 0)
    avatar.location = (x + 4.4, 0, 0)
    labels.append(label(scene, "pet 3 studs", (x + 0.8, -15.0, 0.6), 0.45))
    labels.append(label(scene, "avatar 5.5 studs", (x + 4.4, -15.0, 0.6), 0.45))
    width = x + 6.0
    ortho(cam, (width / 2 - 0.8, 0, 5.6), 14, width + 2.0)
    shoot(scene, os.path.join(OUT, "IceDrill_v2_lineup.png"), 3000, 1100)
    for lab in labels:
        bpy.data.objects.remove(lab, do_unlink=True)
    for name, *_ in TIERS:
        roots[name].location, roots[name].rotation_euler = (0, 0, 0), (0, 0, 0)


def closeups(scene, cam, roots, rig, everything):
    """Each tier from three-quarter, perspective, with the pet beside it for scale."""
    for name, owned, _ in TIERS:
        visible(everything, False)
        root = roots[name]
        visible(tree(root), True)
        root.location, root.rotation_euler = (0, 0, 0), (0, 0, 0)
        bpy.context.view_layer.update()
        lo, hi = bounds_of(tree(root))
        rig.location = (hi.x + 1.4, lo.y + 1.2, 0)
        centre = (lo + hi) / 2
        size = max(hi.x - lo.x + 2.5, hi.z - lo.z, hi.y - lo.y)
        eye = centre + Vector((0.72, -1.0, 0.55)).normalized() * size * 2.35
        persp(cam, centre + Vector((0.6, 0, -0.4)), eye, 50)
        slug = name.split(":")[0].replace("-", "").replace(" ", "")
        shoot(scene, os.path.join(OUT, "IceDrill_v2_%s_closeup.png" % slug), 1400, 1400)


def masterwork(scene, cam, roots, rig, avatar, everything):
    """The Mecha Mole Titan as a full Masterwork, three-quarter and front, with the pet and the avatar."""
    visible(everything, False)
    root = roots["Masterwork"]
    visible(tree(root), True)
    root.location, root.rotation_euler = (0, 0, 0), (0, 0, 0)
    rig.location, avatar.location = (7.6, -1.5, 0), (11.2, -1.0, 0)
    bpy.context.view_layer.update()
    persp(cam, (2.6, -0.5, 6.0), (2.6 + 21, -0.5 - 27, 6.0 + 15), 50)
    shoot(scene, os.path.join(OUT, "IceDrill_v2_Titan_Masterwork_threequarter.png"), 1800, 1400)
    ortho(cam, (3.2, 0, 7.0), 8, 21)
    shoot(scene, os.path.join(OUT, "IceDrill_v2_Titan_Masterwork_front.png"), 1500, 1300)


if MODE == "build":
    build()
elif MODE == "render":
    render_all(globals().get("WHICH", ("lineup", "closeups", "masterwork")))
