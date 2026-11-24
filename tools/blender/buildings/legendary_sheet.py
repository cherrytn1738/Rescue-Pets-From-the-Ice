# legendary_sheet.py - one sheet with all eight Legendary forms together, each with its signature aura
# stand-in, plus the 3-stud Snow Bunny and the 5.5-stud avatar for scale.
#   blender -b --factory-startup --python tools/blender/buildings/legendary_sheet.py
# Writes store-assets/buildings/Legendary_sheet.png.
import os
if "REPO" not in globals():
    REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BUILDING = "Legendaries"
exec(open(os.path.join(REPO, "tools", "blender", "buildings", "framework.py"), encoding="utf-8").read())

ORDER = ["IcePickPost", "HeatLamp", "ChiselMill", "IceDrill", "WreckingCrane", "FlamethrowerTurret", "LavaPump", "SunMirrorTower"]


def legendary_sheet():
    global MATERIALS, SCENE_NAME
    SCENE_NAME = "B_Legendaries"
    scene = fresh_scene()
    path = os.path.join(REPO, "assets", "textures", "BuildingPalette.png")
    image = bpy.data.images.get("BuildingPalette") or bpy.data.images.load(path)
    MATERIALS = palette_materials(image)
    roots = []
    for bid in ORDER:
        file = os.path.join(REPO, "tools", "blender", "buildings", bid + ".py")
        if not os.path.exists(file):
            print("missing", bid)
            continue
        module = dict(globals())
        exec(open(file, encoding="utf-8").read(), module)
        Q.update({"round": 1.0, "minor": 1.0, "corner": 2, "edge": 2, "bevel": 2, "tiny": 0.6})
        Q.update(module.get("TIER_Q", {}).get("Legendary", {}))
        coll = coll_in(scene, bid)
        b = Builder(bid + "Legend", coll)
        atts = module["TIER_FNS"][4](b)
        b.finish()
        fx = Builder(bid + "LegendFx", coll)
        module["AURA"](atts, fx)
        fx.finish()
        fx.root.parent = b.root
        roots.append((bid, b.root))
    rig, avatar, _ = reference(coll_in(scene, "Reference"))
    cam = stage(scene)
    x, labels = 0.0, []
    for bid, root in roots:
        root.rotation_euler = (0, 0, math.radians(-20))
        bpy.context.view_layer.update()
        lo, hi = bounds_of([o for o in tree(root) if o.type == "MESH"])
        root.location = (x - lo.x, 0, 0)
        labels.append(label(scene, CONFIG[bid]["Legendary"], (x + (hi.x - lo.x) / 2, -18.0, 0.9), 0.75))
        x += (hi.x - lo.x) + 3.0
    rig.location, avatar.location = (x + 0.8, 0, 0), (x + 4.4, 0, 0)
    labels.append(label(scene, "pet 3 studs", (x + 0.8, -18.0, 0.7), 0.5))
    labels.append(label(scene, "avatar 5.5 studs", (x + 4.4, -18.0, 0.7), 0.5))
    bpy.context.view_layer.update()
    lo, hi = bounds_of([o for _, r in roots for o in tree(r) if o.type == "MESH"])
    width = x + 6.0
    ortho(cam, (width / 2 - 0.8, 0, hi.z * 0.45 + 0.6), 12, max(width + 2.0, hi.z * 3.1 + 2))
    out = os.path.join(REPO, "store-assets", "buildings")
    os.makedirs(out, exist_ok=True)
    shoot(scene, os.path.join(out, "Legendary_sheet.png"), 4000, 1300)


legendary_sheet()
