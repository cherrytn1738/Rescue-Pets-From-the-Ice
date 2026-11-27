"""make_swing_animations.py - the tools' swing Animation files (every family's variants and dips), from SwingConfig's poses.

    python tools/make_swing_animations.py

Studio open on the place in Edit mode (Rojo synced, "Enable Studio as MCP server" on). Runs
tools/studio/build_swing_animations.luau, which builds a KeyframeSequence per variant (and each family's dip) and
serializes it, and writes store-assets/animations/PickSwing<Name>.rbxm. Then upload them as the group:

    python tools/upload_models.py store-assets/animations/*.rbxm

and paste the ids into SwingConfig.AnimationIds (a changed animation is a NEW asset: swap its id in).
Only a file whose content changed is rewritten (the serializer's output is stable for the same poses).
"""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from run_specs import StudioMcp  # noqa: E402

OUT = os.path.join(REPO, "store-assets", "animations")


def main():
    mcp = StudioMcp()
    studios = []
    for _ in range(15):  # (Studio's MCP server finds an open Studio only after a few seconds)
        studios = json.loads(mcp.call("list_roblox_studios", {}, 60) or "{}").get("studios", [])
        if studios:
            break
        time.sleep(2)
    edit = [s for s in studios if s.get("mode") == "Edit"]
    if not edit:
        sys.exit("No Studio in Edit mode found (stop any Play first).")
    code = open(os.path.join(HERE, "studio", "build_swing_animations.luau"), encoding="utf8").read()
    result = mcp.call("execute_luau", {"code": code, "datamodel_type": "Edit", "studio_id": edit[0]["id"]}, 120)
    start = result.find("{")
    files = json.loads(result[start:result.rfind("}") + 1])
    os.makedirs(OUT, exist_ok=True)
    for name, data in sorted(files.items()):
        path = os.path.join(OUT, name + ".rbxm")
        content = bytes.fromhex(data)
        if os.path.exists(path) and open(path, "rb").read() == content:
            print("%-22s unchanged" % name)
            continue
        open(path, "wb").write(content)
        print("%-22s %6d bytes  %s" % (name, len(content), os.path.relpath(path, REPO)))


if __name__ == "__main__":
    main()
