"""Writes tools/studio/build_voxel_test.luau (voxel STYLE TEST) from the test models' manifests
(store-assets/voxel-test/<style>/<Id>/<Id>_voxel.json: every mesh's colour and glow) and their upload
manifest (store-assets/voxel-test/upload_manifest.json: the asset ids). Run it in Studio in Edit mode; it
builds ServerStorage.VoxelTest.<style>.<Id>.T<tier> next to the real templates and never touches them.

    python tools/make_voxel_test_builder.py
"""
import glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST = os.path.join(ROOT, "store-assets", "voxel-test")


def stud_image():
    m = json.load(open(os.path.join(ROOT, "assets", "textures", "upload_manifest.json"), encoding="utf-8"))
    return m["assets"]["StudOverlay.png"]["assetId"]


def main():
    ids = {k: v["assetId"] for k, v in json.load(open(os.path.join(TEST, "upload_manifest.json"), encoding="utf-8"))["assets"].items()}
    rows = []
    for path in sorted(glob.glob(os.path.join(TEST, "*", "*", "*_voxel.json"))):
        m = json.load(open(path, encoding="utf-8"))
        style, bid = m["style"], m["id"]
        for tier, entry in sorted(m["tiers"].items()):
            key = "%s/%s/fbx/%s_%s_T%s" % (style, bid, bid, style, tier)
            parts = {**entry["station"], **entry["upgrades"]}
            colours = ", ".join('%s = { "%s", %s }' % (name, p["colour"], "true" if p["glow"] else "false") for name, p in sorted(parts.items()))
            rows.append('\t{ Style = "%s", Id = "%s", Tier = %s, Height = %g, Station = %s, Upgrades = %s, Parts = { %s } },' % (
                style, bid, tier, entry["size"][2], ids[key + ".fbx"], ids.get(key + "_Upgrades.fbx", "nil"), colours))
    body = open(os.path.join(ROOT, "tools", "studio", "build_voxel_test.template.luau"), encoding="utf-8").read()
    out = body.replace("--MODELS--", "\n".join(rows)).replace("--STUDS--", str(stud_image()))
    path = os.path.join(ROOT, "tools", "studio", "build_voxel_test.luau")
    open(path, "w", encoding="utf-8", newline="\n").write(out)
    print("wrote", path, "with", len(rows), "models")


if __name__ == "__main__":
    main()
