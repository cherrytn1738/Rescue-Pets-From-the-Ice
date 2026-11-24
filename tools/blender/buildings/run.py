# run.py - builds, renders and exports one building with the framework.
#   blender -b --factory-startup --python tools/blender/buildings/run.py -- IceDrill build render export
# (inside the Blender MCP: set REPO, BUILDING and STEPS, then exec this file)
import os, sys
if "REPO" not in globals():
    REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if "BUILDING" not in globals():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    BUILDING = argv[0]
    STEPS = tuple(argv[1:]) or ("build", "render", "export")
exec(open(os.path.join(REPO, "tools", "blender", "buildings", "framework.py"), encoding="utf-8").read())
MODULE = dict(globals())
exec(open(os.path.join(REPO, "tools", "blender", "buildings", BUILDING + ".py"), encoding="utf-8").read(), MODULE)
OUT_B = os.path.join(OUT_ROOT, BUILDING)
if "build" in STEPS:
    build_building(MODULE, BUILDING)
    os.makedirs(OUT_B, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_B, BUILDING + ".blend"), copy=True)
if "render" in STEPS:
    render_lineup(BUILDING, os.path.join(OUT_B, BUILDING + "_lineup.png"))
    render_masterwork(BUILDING, os.path.join(OUT_B, BUILDING + "_Masterwork.png"))
if "export" in STEPS:
    export_building(BUILDING)
print("RUN_DONE", BUILDING, STEPS)
