# framework.py - the building pipeline: every building is a module with five tier builders and five
# upgrade sets per tier, built on the approved v3 kit (same palette texture, bevels, detail pieces,
# weighted normals, separate glow meshes, named attachment points).
#
# Run headless (one building per Blender, so several can build in parallel):
#   blender -b --factory-startup --python tools/blender/buildings/run.py -- <BuildingId> [build] [render] [export]
# or inside the Blender MCP:
#   REPO = r"..."; BUILDING = "IceDrill"; STEPS = ("build", "render"); exec(open(REPO + r"\tools\blender\buildings\run.py").read())
#
# A building module (tools/blender/buildings/<BuildingId>.py) defines:
#   TIER_FNS = [scrappy, workshop, frosttech, enchanted, legendary]   each fn(b) -> atts
#       b is a Builder named <Id>T<n>; atts maps attachment names to 4x4 matrices (+Z = out)
#   UPGRADES(u, t, atts, b, fx)   adds upgrade u (1-5) in tier t's look (1-5) to Builder b, placed at the
#       tier's attachment points; fx gets particle stand-ins (render only)
#   AURA(atts, fx)                the Legendary's signature aura stand-in (render only)
#   TIER_Q (optional)             per-tier quality overrides like v3's
#
# Conventions (studs; Blender front -Y faces the ice; the game turns each station so its front faces the
# ice): the model stands on z = 0 centred on its pad; its footprint stays inside the pad (BuildingConfig
# Pad.Size); higher tiers grow taller, not wider. Standard attachment names: Work (the working part's
# mount, +Z pointing where it hits: toward the ice), Work2, Lamp1, Lamp2, Gear1, Gear2, Steam1, Steam2,
# Hit (where hit effects start), Trail, NamePlate, Aura (ground centre, +Z up), Top (the highest point),
# Crown (Legendary). Organic surfaces (Builder.add(..., organic=True)) get plain smooth normals; hard
# surfaces get weighted normals.
import os, math, json, re
import bpy, bmesh
from mathutils import Vector, Matrix

TOOLS = os.path.join(REPO, "tools", "blender")
OUT_ROOT = os.path.join(REPO, "store-assets", "buildings")
OUT = OUT_ROOT  # (v2/v3 code reads OUT)
BUNNY_BLEND = ""
_keep_mode = globals().get("MODE")
MODE = "none"
RENDER_TAG = "v4"
exec(open(os.path.join(TOOLS, "ice_drill_tiers_v3.py"), encoding="utf-8").read())
MODE = _keep_mode

THEMES = ["Scrappy", "Workshop", "Frost-tech", "Enchanted", "Legendary"]
BUDGET = {"Scrappy": 6000, "Workshop": 10000, "Frost-tech": 15000, "Enchanted": 20000, "Legendary": 30000}
MESH_LIMIT = 10000
STANDARD_ATTS = ("Work", "Lamp1", "Gear1", "Hit", "Trail", "NamePlate", "Aura", "Top")


# ---------- scenes: headless Blender has no window, so it builds in the default scene ----------

_fresh_scene_v2 = fresh_scene


def fresh_scene():
    if bpy.context.window:
        return _fresh_scene_v2()
    scene = bpy.context.scene
    scene.name = SCENE_NAME
    for obj in list(scene.collection.all_objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in list(scene.collection.children_recursive):
        bpy.data.collections.remove(coll)
    return scene


# ---------- the config the game uses (pads, names, forms) ----------

def building_config():
    text = open(os.path.join(REPO, "src", "replicated", "BuildingConfig.luau"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'\{ Id = "(\w+)", Name = "([^"]+)".*?Pad = \{ Index = (\d+), X = (-?\d+), Z = (-?\d+), Size = (\d+) \},\s*'
                         r'Stations = \{ (.*?) \},.*?LegendaryForm = "([^"]+)", SignatureAura = "([^"]+)"', text, re.S):
        out[m.group(1)] = {"Name": m.group(2), "Pad": int(m.group(6)), "Stations": re.findall(r'"([^"]*)"', m.group(7)),
                           "Legendary": m.group(8), "Aura": m.group(9)}
    return out


CONFIG = building_config()


# ---------- organic vs hard surfaces ----------

_part_init, _part_take, _part_finish = Part.__init__, Part.take, Part.finish


def _init(self, name, glow=False):
    _part_init(self, name, glow)
    self.organic = set()


def _take(self, piece, swatch, matrix=Matrix(), bevel=0.0, organic=False):
    before = len(self.bm.verts)
    _part_take(self, piece, swatch, matrix, bevel)
    if organic:
        self.organic.update(range(before, len(self.bm.verts)))


def _add(self, pieces, matrix=Matrix(), organic=False):
    for bm, swatch, bevel, glow in pieces:
        if glow and not self.glow:
            raise ValueError("glow piece added to a non-glow part %s: use split()" % self.name)
        self.take(bm, swatch, matrix, bevel, organic)


def _finish(self, coll, materials):
    total = len(self.bm.verts)
    organic = set(self.organic)
    obj = _part_finish(self, coll, materials)
    if organic:
        hard = [i for i in range(total) if i not in organic]
        group = obj.vertex_groups.new(name="Hard")
        if hard:
            group.add(hard, 1.0, "REPLACE")
        mod = obj.modifiers.get("WeightedNormal")
        if mod:
            mod.vertex_group = "Hard"  # organic vertices keep plain smooth normals
    return obj


Part.__init__, Part.take, Part.add, Part.finish = _init, _take, _add, _finish
_builder_add = Builder.add


def _builder_add_organic(self, role, pieces, matrix=Matrix(), organic=False):
    solid, glow = split(pieces)
    for group, is_glow in ((solid, False), (glow, True)):
        if group:
            key = self.name + role + ("Glow" if is_glow else "")
            self.parts.setdefault(key, Part(key, is_glow)).add(group, matrix, organic)


Builder.add = _builder_add_organic


# ---------- shared upgrade pieces in each tier's look ----------

def tier_lamp(t, glow_swatch=None):
    """The 2nd upgrade's light in tier t's look: a lantern, a brass warning lamp, a glowing gem in a
    setting, a floating gem in a rune ring, an aurora beacon in gold."""
    if t == 1:
        return lantern_v3("LampYellow", "Iron")
    if t == 2:
        return warning_lamp(0.32, glow_swatch or "Amber", "Brass", "Iron")
    if t == 3:
        return gem_setting(0.22, glow_swatch or "AuroraCyan", "SteelLight", 6)
    if t == 4:
        pieces = cut_gem(0.26, glow_swatch or "MagicPink")
        for bm, *_ in pieces:
            bm.transform(M((0, 0, 0.45)))
        pieces += trim_ring(0.4, 0.45, "RuneViolet", True, minor=0.04, segments=16)
        return pieces
    return warning_lamp(0.4, glow_swatch or "AuroraGreen", "Gold", "Gunmetal")


def tier_puff(t, radius=0.35):
    """A steam or sparkle puff stand-in (particles in game) for renders."""
    pieces = []
    swatch = {1: "StoneLight", 2: "SnowWhite", 3: "FrostLight", 4: "MagicPink", 5: "Gold"}[t]
    for dx, dz, r in ((0.0, 0.4, 0.3), (0.2, 0.95, 0.42), (-0.15, 1.6, 0.55)):
        puff = bmesh.new()
        blob(puff, (dx, 0, dz), (r * radius / 0.35,) * 3, 1)
        pieces.append((puff, swatch, 0.0, t >= 4))
    return pieces


def hit_standin(t, swatch=None):
    """The 4th upgrade's hit burst stand-in (particles in game): chips and sparks."""
    pieces = []
    chip = {1: "PineLight", 2: "IceBlue", 3: "IceBlue", 4: "RuneGlow", 5: "Gold"}[t]
    for k in range(7):
        a = k * 2.4
        c = bmesh.new()
        blob(c, (0.6 * math.cos(a), 0.6 * math.sin(a), 0.3 + 0.2 * k), (0.16, 0.12, 0.2), 1, rotation=(a, 0.5 * k, 0))
        pieces.append((c, chip, 0.0, False))
    for k in range(5):
        a = k * 1.2 + 0.4
        s = bmesh.new()
        cylinder(s, (0.35 * math.cos(a), 0.35 * math.sin(a), 0.2), 0.05, 0.6, 4, direction=(math.cos(a), math.sin(a), 1.3), top=0.0)
        pieces.append((s, swatch or ("CrystalCyan" if t >= 3 else "LampYellow"), 0.0, True))
    return pieces


def masterwork_extras(atts, b, fx):
    """Every Masterwork: the name plate, and a golden sparkle aura stand-in."""
    if "NamePlate" in atts:
        b.add("NamePlate", place(name_plate(2.6, 0.55, "PineLight", "Gold"), atts["NamePlate"]))
    sparkles = []
    centre = atts.get("Aura", Matrix()).to_translation()
    for k in range(10):
        a = k * 2.2
        s = bmesh.new()
        lathe(s, [(0, -0.2), (0.08, 0), (0, 0.2)], 4, M((centre.x + 3.2 * math.cos(a), centre.y + 3.2 * math.sin(a), 2.0 + 0.8 * (k % 5))))
        sparkles.append((faceted(s), "LampYellow", 0.0, True))
    fx.add("Sparkles", sparkles)


# ---------- building one station ----------

def counts(objs):
    return [(o.name, sum(len(p.vertices) - 2 for p in o.data.polygons)) for o in objs if o.type == "MESH"]


def footprint(objs):
    lo, hi = bounds_of(objs)
    return lo, hi


def build_building(module, bid):
    """Builds the five tiers, their upgrade sets and the Legendary aura stand-in into scene B_<Id>.
    Returns the manifest dict (also written to store-assets/buildings/<Id>/<Id>_manifest.json)."""
    global MATERIALS, SCENE_NAME
    SCENE_NAME = "B_" + bid
    scene = fresh_scene()
    palette_path = os.path.join(REPO, "assets", "textures", "BuildingPalette.png")
    image = bpy.data.images.get("BuildingPalette")
    if image is None:
        image = bpy.data.images.load(palette_path) if os.path.exists(palette_path) else write_palette(palette_path)
        image.name = "BuildingPalette"
    MATERIALS = palette_materials(image)
    pad = CONFIG[bid]["Pad"]
    manifest = {"id": bid, "name": CONFIG[bid]["Name"], "pad": pad, "tiers": []}
    tier_q = module.get("TIER_Q", {})
    fns = module["TIER_FNS"]
    for t, fn in enumerate(fns, start=1):
        theme = THEMES[t - 1]
        Q.update({"round": 1.0, "minor": 1.0, "corner": 2, "edge": 2, "bevel": 2, "tiny": 0.6})
        Q.update(tier_q.get(theme, {}))
        coll = coll_in(scene, "%s %s" % (bid, theme))
        b = Builder("%sT%d" % (bid, t), coll)
        atts = fn(b)
        b.finish()
        for name in STANDARD_ATTS:
            if name not in atts:
                print("WARNING %s tier %d has no %s attachment" % (bid, t, name))
        attach(b, atts)
        bpy.context.view_layer.update()
        lo, hi = bounds_of(b.made)
        half = pad / 2 + 0.01
        fits = -half <= lo.x and hi.x <= half and -half <= lo.y and hi.y <= half
        # the upgrade sets: one Builder per upgrade, in this tier's look
        ucoll = coll_in(scene, "%s %s Upgrades" % (bid, theme))
        fx = Builder("%sT%dFx" % (bid, t), ucoll)
        upgrades = []
        for u in range(1, 6):
            ub = Builder("%sT%dU%d" % (bid, t, u), ucoll)
            module["UPGRADES"](u, t, atts, ub, fx)
            if u == 5 and t == 5:
                masterwork_extras(atts, ub, fx)
            ub.finish()
            upgrades.append({"upgrade": u, "meshes": counts(ub.made)})
            ub.root.parent = b.root
        if t == 5:
            module["AURA"](atts, fx)
        fx.finish()
        fx.root.parent = b.root
        for obj in fx.made:
            obj["fx"] = True
        manifest["tiers"].append({
            "tier": t, "theme": theme, "form": CONFIG[bid]["Stations"][t - 1],
            "meshes": counts(b.made), "upgrades": upgrades, "fx": counts(fx.made),
            "size": [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)],
            "fitsPad": fits, "attachments": {name: roblox_frame(m) for name, m in atts.items()},
        })
        total = sum(n for _, n in counts(b.made))
        biggest = max(counts(b.made), key=lambda m: m[1])
        print("%s T%d %-10s %3d meshes %6d tris (budget %d) largest %s %d  size %.1f x %.1f x %.1f  pad %d %s" % (
            bid, t, theme, len(b.made), total, BUDGET[theme], biggest[0], biggest[1], hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, pad,
            "fits" if fits else "DOES NOT FIT"))
        for name, tris in counts(b.made) + [m for up in upgrades for m in up["meshes"]]:
            if tris > MESH_LIMIT:
                print("WARNING mesh over %d: %s %d" % (MESH_LIMIT, name, tris))
    rig, avatar, _ = reference(coll_in(scene, "Reference"))
    REFERENCE[bid] = (rig, avatar)
    out = os.path.join(OUT_ROOT, bid)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, bid + "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    return manifest


def roblox_frame(m):
    """An attachment as the game reads it: position and its +Z (out) and +Y axes, on Roblox's axes
    (Blender x, y, z -> Roblox -x, z, y), relative to the model's pivot (the pad centre on the ground)."""
    p, z, y = m.to_translation(), m.to_3x3().col[2], m.to_3x3().col[1]
    r = lambda v: [round(-v.x, 3), round(v.z, 3), round(v.y, 3)]
    return {"position": r(p), "out": r(z), "up": r(y)}


# ---------- renders ----------

REFERENCE = {}  # [building id] = (pet rig, avatar root), the objects this build made


def reference_of(bid):
    if bid in REFERENCE:
        return REFERENCE[bid]
    scene = bpy.data.scenes["B_" + bid]
    objs = list(scene.collection.all_objects)
    rig = next(o for o in objs if o.type == "ARMATURE")
    avatar = next(o for o in objs if o.name.startswith("AvatarStandIn") and o.parent is None)
    return rig, avatar


def roots_of(bid):
    return [bpy.data.objects["%sT%d" % (bid, t)] for t in range(1, 6)]


def show_tier(root, upgrades=False, fx=False):
    for o in tree(root):
        is_upgrade = re.search(r"T\dU\d", o.name) is not None
        is_fx = "Fx" in o.name or o.get("fx")
        on = (not is_upgrade or upgrades) and (not is_fx or fx)
        o.hide_render = not on
        o.hide_set(not on)


def render_lineup(bid, path, aura=True):
    scene = bpy.data.scenes["B_" + bid]
    if bpy.context.window:
        bpy.context.window.scene = scene
    cam = scene.camera if scene.camera and scene.camera.name.startswith("StyleCam") else stage(scene)
    roots = roots_of(bid)
    rig, avatar = reference_of(bid)
    x, gap, labels = 0.0, 2.2, []
    for t, root in enumerate(roots, start=1):
        show_tier(root, fx=(aura and t == 5))
        root.location = (0, 0, 0)
        root.rotation_euler = (0, 0, math.radians(-22))
        bpy.context.view_layer.update()
        lo, hi = bounds_of([o for o in tree(root) if o.type == "MESH" and not o.hide_render])
        root.location = (x - lo.x, 0, 0)
        labels.append(label(scene, THEMES[t - 1], (x + (hi.x - lo.x) / 2, -15.0, 0.95), 0.62))
        x += (hi.x - lo.x) + gap
    rig.location, avatar.location = (x + 0.8, 0, 0), (x + 4.4, 0, 0)
    labels.append(label(scene, "pet 3 studs", (x + 0.8, -15.0, 0.6), 0.45))
    labels.append(label(scene, "avatar 5.5 studs", (x + 4.4, -15.0, 0.6), 0.45))
    bpy.context.view_layer.update()
    vis = [o for r in roots for o in tree(r) if o.type == "MESH" and not o.hide_render]
    lo, hi = bounds_of(vis)
    width = x + 6.0
    height = hi.z
    ortho(cam, (width / 2 - 0.8, 0, height * 0.42 + 0.6), 14, max(width + 2.0, height * 2.75 + 2))
    shoot(scene, path, 3000, 1100)
    for lab in labels:
        bpy.data.objects.remove(lab, do_unlink=True)
    for root in roots:
        root.location, root.rotation_euler = (0, 0, 0), (0, 0, 0)
        show_tier(root, upgrades=True, fx=True)


def render_masterwork(bid, path, eye=(0.78, -1.0, 0.5), lens=50):
    """The Legendary tier with every upgrade (the Masterwork), three-quarter, with the pet and avatar."""
    scene = bpy.data.scenes["B_" + bid]
    cam = scene.camera
    roots = roots_of(bid)
    for root in roots:
        visible(tree(root), False)
    root = roots[4]
    visible(tree(root), True)
    show_tier(root, upgrades=True, fx=True)
    root.location, root.rotation_euler = (0, 0, 0), (0, 0, 0)
    bpy.context.view_layer.update()
    lo, hi = bounds_of([o for o in tree(root) if o.type == "MESH" and not o.hide_render])
    rig, avatar = reference_of(bid)
    rig.location, avatar.location = (hi.x + 1.8, -0.5, 0), (hi.x + 4.4, 0.5, 0)
    hi = Vector((hi.x + 5.8, hi.y, max(hi.z, 5.5)))
    centre = (lo + hi) / 2
    size = max(hi.x - lo.x, hi.z - lo.z, hi.y - lo.y)
    persp(cam, centre + Vector((0.4, 0, -0.6)), centre + Vector(eye).normalized() * size * 2.25, lens)
    shoot(scene, path, 1800, 1400)
    for r in roots:
        visible(tree(r), True)


# ---------- export ----------

def export_building(bid):
    """FBX per tier (the station) and per tier's upgrade sets, ready for tools/upload_models.py."""
    out = os.path.join(OUT_ROOT, bid, "fbx")
    for t in range(1, 6):
        root = bpy.data.objects["%sT%d" % (bid, t)]
        station = [o for o in root.children if o.type == "MESH"]
        ups = [o for u in range(1, 6) for ur in [bpy.data.objects.get("%sT%dU%d" % (bid, t, u))] if ur for o in ur.children if o.type == "MESH"]
        for objs, path in ((station, os.path.join(out, "%s_T%d.fbx" % (bid, t))), (ups, os.path.join(out, "%s_T%d_Upgrades.fbx" % (bid, t)))):
            if objs:
                visible(objs, True)
                export_fbx(objs, path)
