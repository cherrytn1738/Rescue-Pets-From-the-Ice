# tools_ice_picks.py - the player's ice pick in six tiers (docs/GAME_DESIGN.md, "Upgrades in detail" and
# "How buildings, upgrades and pets look": wood, stone, iron, gold, diamond, cosmic), a hand-held tool about
# 3.5 studs long, on the building kit (same palette texture, bevels, weighted normals, glow meshes).
#   blender -b --factory-startup --python tools/blender/tools_ice_picks.py
# or in the Blender MCP: REPO = r"..."; exec(open(REPO + r"\tools\blender\tools_ice_picks.py").read())
# Writes store-assets/tools/: IcePicks_sheet.png (the six picks with the 3-stud pet and the 5.5-stud
# avatar), IcePicks_manifest.json (meshes, triangles, attachments), fbx/IcePick_T<n>.fbx.
# Each pick: the handle along +Z from the pommel (z = 0); the head across X at the top. Attachments: Grip
# (where the hand holds it), Tip (the striking point, for sparks), Trail (the head's centre).
import os, sys, math, json
if "REPO" not in globals():
    REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILDING = "IcePicks"
exec(open(os.path.join(REPO, "tools", "blender", "buildings", "framework.py"), encoding="utf-8").read())

LENGTH = 3.5
PICKS = [
    # name, handle, grip, band, head, head accent, glow accent
    ("Wooden pick", "Pine", "PineLight", "PineDark", "PineDark", "PineLight", None),
    ("Stone pick", "Pine", "Rubber", "PineDark", "Stone", "StoneDark", None),
    ("Iron pick", "PineDark", "Rubber", "Iron", "Iron", "SteelLight", None),
    ("Gold pick", "PineDark", "Rubber", "Brass", "Gold", "Brass", None),
    ("Diamond pick", "SteelLight", "NavyIce", "Gold", "Diamond", "CrystalCyan", "CrystalCyan"),
    ("Cosmic pick", "ArcaneDeep", "NavyIce", "Gold", "RuneViolet", "MagicPink", "RuneGlow"),
]


def pick_head(tier, swatch, accent, glow):
    """The double-ended pick head across X: a thick middle tapering to two curved points."""
    pieces = []
    top = LENGTH - 0.35
    for side in (-1, 1):
        points = []
        for k in range(7):
            s = k / 6
            x = side * (0.12 + 1.05 * s)
            z = top - 0.42 * s * s  # curving down toward the tip
            points.append(Vector((x, 0, z)))
        arm = bmesh.new()
        sweep(arm, points, 0.2 if tier > 1 else 0.17, 10, radius_end=0.03)
        if tier in (2, 5, 6):
            arm = faceted(arm)  # chipped stone and cut crystal read faceted
        pieces.append((arm, swatch, 0.0, bool(glow) and tier == 6))
    collar = bmesh.new()  # the eye where the head meets the handle
    rounded_block(collar, (0.46, 0.38, 0.5), M((0, 0, top)), corner=0.1, edge=0.06, corner_seg=2, edge_seg=2)
    pieces.append((collar, accent, 0.0, False))
    if tier == 1:  # rope lashing over the wooden head
        for dz in (-0.12, 0.12):
            ring = bmesh.new()
            torus(ring, M((0, 0, top + dz), (math.pi / 2, 0, 0)), 0.26, 0.04, 12, 4)
            pieces.append((ring, "PineLight", 0.0, False))
    if tier == 3:
        for sx in (-1, 1):
            pieces += place(rivet(0.06, "SteelDark"), frame((sx * 0.14, -0.2, top), out=(0, -1, 0)))
    if tier >= 4:  # a gem set in the collar
        gem_swatch = {4: "WarnRed", 5: "AuroraCyan", 6: "MagicPink"}[tier]
        pieces += place(gem_setting(0.11, gem_swatch, "Gold", 4), frame((0, -0.2, top), out=(0, -1, 0)))
    if glow:  # a glowing edge along the points (diamond) or a ring of runes (cosmic)
        if tier == 5:
            for side in (-1, 1):
                edge = bmesh.new()
                sweep(edge, [Vector((side * (0.3 + 0.75 * s), 0, top + 0.13 - 0.42 * s * s)) for s in (0, 0.33, 0.66, 1.0)], 0.045, 6, radius_end=0.015)
                pieces.append((edge, glow, 0.0, True))
        else:
            ring = bmesh.new()
            torus(ring, M((0, 0, top), (math.pi / 2, 0, 0.3)), 0.55, 0.035, 20, 4)
            pieces.append((ring, glow, 0.0, True))
            for k in range(3):
                a = k * 2 * math.pi / 3
                star = bmesh.new()
                lathe(star, [(0, -0.09), (0.05, 0), (0, 0.09)], 4, M((0.55 * math.cos(a), 0.55 * math.sin(a) * 0.3, top + 0.55 * math.sin(a) * 0.95)))
                pieces.append((faceted(star), "Gold", 0.0, True))
    return pieces


def pick(b, tier):
    name, handle, grip, band, head, accent, glow = PICKS[tier - 1]
    shaft = bmesh.new()
    lathe(shaft, [(0, 0.1), (0.13, 0.1), (0.15, 0.4), (0.12, LENGTH * 0.6), (0.14, LENGTH - 0.6), (0.15, LENGTH - 0.1), (0, LENGTH - 0.1)], 12)
    b.add("Handle", [(shaft, handle, 0.0, False)])
    if tier == 1:  # wood grain grooves down the handle
        for k in range(3):
            a = k * 2 * math.pi / 3 + 0.4
            g = bmesh.new()
            sweep(g, [Vector((0.135 * math.cos(a), 0.135 * math.sin(a), z)) for z in (0.6, 1.4, 2.2)], 0.012, 4)
            b.add("Handle", [(g, "PineDark", 0.0, False)])
    pommel = bmesh.new()
    lathe(pommel, [(0, 0), (0.17, 0), (0.2, 0.1), (0.16, 0.16), (0, 0.16)], 12)
    b.add("Handle", [(pommel, band, 0.0, False)])
    for k in range(5):  # the wrapped grip
        ring = bmesh.new()
        torus(ring, M((0, 0, 0.32 + k * 0.16), (0.2, 0, 0)), 0.15, 0.04, 12, 4)
        b.add("Handle", [(ring, grip, 0.0, False)])
    for z in (LENGTH * 0.55, LENGTH - 0.75):
        b.add("Handle", place(trim_ring(0.15, 0, band, minor=0.035, segments=12), M((0, 0, z))))
    if tier == 6:  # star gems up the cosmic handle
        for z in (1.4, 1.9, 2.4):
            b.add("Handle", place(cut_gem(0.06, "RuneGlow"), frame((0, -0.13, z), out=(0, -1, 0))))
    b.add("Head", pick_head(tier, head, accent, glow))
    return {"Grip": frame((0, 0, 0.55)), "Tip": frame((1.17, 0, LENGTH - 0.77), out=(1, 0, -0.6)),
            "Trail": frame((0, 0, LENGTH - 0.35), out=(0, 0, 1))}


def build_picks():
    global MATERIALS, SCENE_NAME
    SCENE_NAME = "B_IcePicks"
    scene = fresh_scene()
    path = os.path.join(REPO, "assets", "textures", "BuildingPalette.png")
    image = bpy.data.images.get("BuildingPalette") or bpy.data.images.load(path)
    MATERIALS = palette_materials(image)
    manifest = {"picks": []}
    for tier in range(1, 7):
        Q.update({"round": 1.0, "minor": 1.0, "corner": 2, "edge": 2, "bevel": 2, "tiny": 0.6})
        coll = coll_in(scene, "Pick %d" % tier)
        b = Builder("IcePickT%d" % tier, coll)
        atts = pick(b, tier)
        b.finish()
        attach(b, atts)
        manifest["picks"].append({"tier": tier, "name": PICKS[tier - 1][0], "meshes": counts(b.made),
                                  "attachments": {k: roblox_frame(m) for k, m in atts.items()}})
        print("IcePick T%d %-13s %d tris" % (tier, PICKS[tier - 1][0], sum(n for _, n in counts(b.made))))
    rig, avatar, _ = reference(coll_in(scene, "Reference"))
    out = os.path.join(REPO, "store-assets", "tools")
    os.makedirs(out, exist_ok=True)
    json.dump(manifest, open(os.path.join(out, "IcePicks_manifest.json"), "w", encoding="utf-8"), indent=1)
    # the sheet: six picks standing in a row, each turned three-quarter, labelled, with the pet and the avatar
    cam = stage(scene)
    labels = []
    for tier in range(1, 7):
        root = bpy.data.objects["IcePickT%d" % tier]
        root.location = ((tier - 1) * 3.0, 0, 0)
        root.rotation_euler = (0, 0, math.radians(-25))
        labels.append(label(scene, PICKS[tier - 1][0], ((tier - 1) * 3.0, -6.0, 0.4), 0.32))
    rig.location, avatar.location = (18.5, 0, 0), (22.0, 0, 0)
    labels.append(label(scene, "pet 3 studs", (18.5, -6.0, 0.4), 0.3))
    labels.append(label(scene, "avatar 5.5 studs", (22.0, -6.0, 0.4), 0.3))
    ortho(cam, (11.0, 0, 2.7), 10, 27)
    shoot(scene, os.path.join(out, "IcePicks_sheet.png"), 2600, 1000)
    for lab in labels:
        bpy.data.objects.remove(lab, do_unlink=True)
    for tier in range(1, 7):
        root = bpy.data.objects["IcePickT%d" % tier]
        root.location, root.rotation_euler = (0, 0, 0), (0, 0, 0)
        export_fbx([o for o in root.children if o.type == "MESH"], os.path.join(out, "fbx", "IcePick_T%d.fbx" % tier))


build_picks()
