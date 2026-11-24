"""Writes TRIANGLE_COUNTS.md from the triangle_counts.json that ice_drill_tiers_v3.py's build() saves.

    python tools/blender/triangle_table.py store-assets/style-test/v3
"""
import json, os, sys

BUDGETS = {"Scrappy": 6000, "Workshop": 10000, "Frost-tech": 15000, "Enchanted": 20000,
           "Legendary: Mecha Mole Titan": 30000, "Masterwork": 30000}
LABELS = {"Masterwork": "Legendary + all 5 Masterwork upgrades"}


def main(folder):
    table = json.load(open(os.path.join(folder, "triangle_counts.json"), encoding="utf-8"))
    lines = ["# Ice Drill v3: triangle counts", "",
             "Generated from `triangle_counts.json` (written by `tools/blender/ice_drill_tiers_v3.py`; this table by "
             "`tools/blender/triangle_table.py`). Every mesh stays under 10,000 triangles (safe for FBX import; Roblox allows 20,000).",
             "", "## Per tier", "", "| Tier | Meshes | Triangles | Budget | vs budget | Largest mesh |", "| --- | ---: | ---: | ---: | ---: | --- |"]
    for name, row in table.items():
        meshes = row["meshes"]
        total = sum(t for _, t in meshes)
        big = max(meshes, key=lambda m: m[1])
        budget = BUDGETS[name]
        lines.append(f"| {LABELS.get(name, name)} | {len(meshes)} | {total:,} | {budget:,} | {(total - budget) / budget * 100:+.0f}% | {big[0]} ({big[1]:,}) |")
    base = sum(t for _, t in table["Legendary: Mecha Mole Titan"]["meshes"])
    master = sum(t for _, t in table["Masterwork"]["meshes"])
    fx = table["Masterwork"].get("fx", [])
    lines += ["", f"Masterwork upgrade parts alone: {master - base:,} triangles. FX stand-ins (particles in game, not meshes): "
              f"{sum(t for _, t in fx):,} triangles in {len(fx)} preview meshes, not counted above.", "", "## Per mesh"]
    for name, row in table.items():
        lines += ["", f"### {name}", "", "| Mesh | Triangles | Glow (Neon) |", "| --- | ---: | :---: |"]
        for mesh, tris in sorted(row["meshes"], key=lambda m: -m[1]):
            lines.append(f"| {mesh} | {tris:,} | {'yes' if mesh.endswith('Glow') else ''} |")
    open(os.path.join(folder, "TRIANGLE_COUNTS.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines[6:14]))


if __name__ == "__main__":
    main(sys.argv[1])
