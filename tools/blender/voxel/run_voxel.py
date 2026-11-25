# run_voxel.py - the voxel VSTYLE TEST for buildings: builds one building's voxel tiers in headless Blender.
#   blender -b --factory-startup --python tools/blender/voxel/run_voxel.py -- <BuildingId> <A|B> [tiers] [render] [export]
#     A: the stations hand-built on the voxel grid (tools/blender/voxel/<BuildingId>.py: A_TIERS)
#     B: the approved models voxelized automatically (voxels.voxelize), then hand-fixed (FIX_B)
#     tiers: e.g. 12345 (default) or 5
# Upgrade sets are voxelized from the approved ones in both (the test is about the stations).
# Out: store-assets/voxel-test/<style>/<BuildingId>/ (renders, fbx/, <BuildingId>_voxel.json with every
# mesh's colour, glow and triangles: the Studio test builder colours the parts from it).
import os, sys, json, re, time
if "REPO" not in globals():
    REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BID, VSTYLE = argv[0], argv[1]
VTIERS = [int(c) for c in next((a for a in argv[2:] if a.isdigit()), "12345")]
VSTEPS = [a for a in argv[2:] if not a.isdigit()] or ["render", "export"]
BUILDING = BID
exec(open(os.path.join(REPO, "tools", "blender", "buildings", "framework.py"), encoding="utf-8").read())
exec(open(os.path.join(REPO, "tools", "blender", "voxel", "voxels.py"), encoding="utf-8").read())
OUT_V = os.path.join(REPO, "store-assets", "voxel-test", VSTYLE, BID)
os.makedirs(OUT_V, exist_ok=True)

# 1. the approved building (its manifest goes to a scratch folder: the real one stays as it is)
MODULE = dict(globals())
exec(open(os.path.join(REPO, "tools", "blender", "buildings", BID + ".py"), encoding="utf-8").read(), MODULE)
OUT_ROOT = os.path.join(REPO, "tmp", "voxel_scratch")
build_building(MODULE, BID)
VMOD = dict(globals())
vfile = os.path.join(REPO, "tools", "blender", "voxel", BID + ".py")
for f in (vfile, vfile[:-3] + "_A.py"):  # the B fixes, then the hand-built A tiers
    if os.path.exists(f):
        exec(open(f, encoding="utf-8").read(), VMOD)
GRID_LO, GRID_HI = (-13, -13, 0), (13, 13, 36)

# 2. the voxel grids
t0 = time.time()
grids = {}
for t in VTIERS:
    root = bpy.data.objects["%sT%d" % (BID, t)]
    station = [o for o in root.children if o.type == "MESH"]
    if VSTYLE == "B":
        g = despeckle(voxelize(station, grid=VGrid(GRID_LO, GRID_HI)))
        fix = VMOD.get("FIX_B", {}).get(t)
        if fix:
            fix(g)
    else:
        g = VGrid(GRID_LO, GRID_HI)
        VMOD["A_TIERS"][t](g)
    ups = {}
    for u in range(1, 6):
        ur = bpy.data.objects.get("%sT%dU%d" % (BID, t, u))
        objs = [o for o in (ur.children if ur else []) if o.type == "MESH"]
        if objs:
            ups[u] = despeckle(voxelize(objs, grid=VGrid(GRID_LO, GRID_HI)))
            fixu = VMOD.get("FIX_B_UP", {}).get((t, u))
            if fixu:
                fixu(ups[u])
    grids[t] = (g, ups)
    print("voxel %s %s T%d: %d voxels, %.0f s" % (VSTYLE, BID, t, int((g.col > 0).sum()), time.time() - t0))

# 3. swap the approved meshes for the voxel ones, under the same names (so the line-up renders work)
scene = bpy.data.scenes["B_" + BID]
for coll in list(scene.collection.children):
    if coll.name.startswith(BID):
        for o in list(coll.all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(coll)
for me in list(bpy.data.meshes):
    if me.users == 0:
        bpy.data.meshes.remove(me)
vcoll = coll_in(scene, "Voxel " + BID)
manifest = {"id": BID, "style": VSTYLE, "voxel": VOXEL, "tiers": {}}
for t in range(1, 6):
    root = bpy.data.objects.new("%sT%d" % (BID, t), None)
    vcoll.objects.link(root)
    if t not in grids:
        continue
    g, ups = grids[t]
    made = make_objects(g, "%sT%d" % (BID, t), vcoll, root)
    entry = {"station": {o.name: {"colour": SWATCHES[SWATCH_INDEX[c]][1], "swatch": c, "glow": gl, "tris": n} for o, (c, gl), n in made},
             "upgrades": {}}
    for u, ug in ups.items():
        uroot = bpy.data.objects.new("%sT%dU%d" % (BID, t, u), None)
        vcoll.objects.link(uroot)
        uroot.parent = root
        for o, (c, gl), n in make_objects(ug, "%sT%dU%d" % (BID, t, u), vcoll, uroot):
            entry["upgrades"][o.name] = {"colour": SWATCHES[SWATCH_INDEX[c]][1], "swatch": c, "glow": gl, "tris": n}
    bpy.context.view_layer.update()
    lo, hi = bounds_of([o for o, _, _ in made])
    entry["size"] = [round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2)]
    entry["stationTris"] = sum(m["tris"] for m in entry["station"].values())
    entry["upgradeTris"] = sum(m["tris"] for m in entry["upgrades"].values())
    manifest["tiers"][str(t)] = entry
    print("%s %s T%d: %d meshes, %d tris (+ %d in upgrade sets), size %.1f x %.1f x %.1f" % (
        VSTYLE, BID, t, len(made), entry["stationTris"], entry["upgradeTris"], *entry["size"]))
with open(os.path.join(OUT_V, BID + "_voxel.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=1)


# 4. renders
def render_one(t, path, eye=(0.78, -1.0, 0.5), lens=50, upgrades=True):
    cam = scene.camera if scene.camera else stage(scene)
    for r in [bpy.data.objects["%sT%d" % (BID, k)] for k in range(1, 6)]:
        visible(tree(r), False)
    root = bpy.data.objects["%sT%d" % (BID, t)]
    visible(tree(root), True)
    show_tier(root, upgrades=upgrades)
    bpy.context.view_layer.update()
    lo, hi = bounds_of([o for o in tree(root) if o.type == "MESH" and not o.hide_render])
    rig, avatar = reference_of(BID)
    rig.location, avatar.location = (hi.x + 1.8, -0.5, 0), (hi.x + 4.4, 0.5, 0)
    hi = Vector((hi.x + 5.8, hi.y, max(hi.z, 5.5)))
    centre = (lo + hi) / 2
    size = max(hi.x - lo.x, hi.z - lo.z, hi.y - lo.y)
    persp(cam, centre + Vector((0.4, 0, -0.6)), centre + Vector(eye).normalized() * size * 2.25, lens)
    shoot(scene, path, 1800, 1400)
    for r in [bpy.data.objects["%sT%d" % (BID, k)] for k in range(1, 6)]:
        visible(tree(r), True)


if "render" in VSTEPS:
    if len(VTIERS) == 5:
        render_lineup(BID, os.path.join(OUT_V, "%s_%s_lineup.png" % (BID, VSTYLE)), aura=False)
    for t in VTIERS:
        render_one(t, os.path.join(OUT_V, "%s_%s_T%d.png" % (BID, VSTYLE, t)))
        if t == 5:
            render_one(t, os.path.join(OUT_V, "%s_%s_T5_front.png" % (BID, VSTYLE)), eye=(0.15, -1.0, 0.28), lens=60)
            render_one(t, os.path.join(OUT_V, "%s_%s_T5_station.png" % (BID, VSTYLE)), eye=(0.35, -1.0, 0.3), lens=60, upgrades=False)

# 5. FBX files
if "export" in VSTEPS:
    for t in VTIERS:
        root = bpy.data.objects["%sT%d" % (BID, t)]
        station = [o for o in root.children if o.type == "MESH"]
        export_fbx_scaled(station, os.path.join(OUT_V, "fbx", "%s_%s_T%d.fbx" % (BID, VSTYLE, t)))
        ups = [o for u in range(1, 6) for ur in [bpy.data.objects.get("%sT%dU%d" % (BID, t, u))] if ur for o in ur.children if o.type == "MESH"]
        if ups:
            export_fbx_scaled(ups, os.path.join(OUT_V, "fbx", "%s_%s_T%d_Upgrades.fbx" % (BID, VSTYLE, t)))
print("VOXEL_DONE", BID, VSTYLE, VTIERS, VSTEPS)
