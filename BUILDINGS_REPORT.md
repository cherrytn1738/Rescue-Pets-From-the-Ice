# Overnight run 2: buildings, upgrade parts, picks, effects

(Filled in step by step; the final summary is at the end.)

## Step 0: sync with the design doc (done)

- `BuildingConfig` follows the new doc tables:
  - `Tiers`: the five tier themes.
  - `Stations`: each building's five tier forms.
  - `UpgradeParts`: now a list of five, one per upgrade.
  - `LegendaryForm` and `SignatureAura`: each Legendary's name and aura.
- `tests/BuildingConfig.spec.luau` reads all four of those doc tables.
- All 17 specs pass (2,801 checks).

## Step 1: Ice Drill fixes (done)

- **Pipeline:**
  - The Ice Drill moved into the new building pipeline (`tools/blender/buildings/framework.py`,
    `run.py`, `IceDrill.py`). It builds a building's five tiers and their upgrade sets on the v3 kit.
  - It checks pad fit and counts triangles, writes the attachment manifest, renders, and exports FBX.
  - It runs headless, so several buildings can build at once.
- **Workshop:** the bit comes out of the gearbox on an angled boom at the front, pointing down at the ice.
- **Frost-tech:** each pod's bit comes out of its front, through a steel collar with a glowing ring.
- **Enchanted:**
  - A violet spiral-crystal drill floats at the front inside its own rune ring, aimed at the ice.
  - The floating islands' cones have gold spiral flutes, so they read as drill bits.
- **Mecha Mole Titan:**
  - Riveted steel pauldrons and a riveted helmet plate over the fur.
  - Gears at the elbows and knees; pistons at the elbows and knees (the knees already had them).
  - Two exhaust pipes with flared tips, and chunky armoured gauntlets.
  - A bigger snout: a geared housing, a gold collar, hydraulic struts and a wider bit.
  - Fur and head use plain smooth normals, which fixes the blotchy shading; hard parts keep weighted
    normals.
  - It now stands back on a narrower plinth.
- **Pad:** every tier fits the Ice Drill's 10-stud pad.
- **Renders:** `store-assets/style-test/v4/IceDrill_v4_lineup.png` and
  `IceDrill_v4_Titan_Masterwork_threequarter.png`.
- **Triangles:**
  - Scrappy 6,200 (+3%), Workshop 10,592 (+6%), Frost-tech 16,012 (+7%), Enchanted 20,726 (+4%).
  - Legendary 27,120, or 33,064 (+10%) with its Masterwork parts.
