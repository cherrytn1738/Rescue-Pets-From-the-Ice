# Overnight run 2: buildings, upgrade parts, picks, effects

## Look at these first

1. `store-assets/buildings/Legendary_sheet.png`: the eight Legendary forms together, with their aura
   stand-ins, the 3-stud Snow Bunny and the 5.5-stud avatar.
2. `store-assets/style-test/v4/IceDrill_v4_lineup.png` (and `IceDrill_v4_Titan_Masterwork_threequarter.png`).
3. `store-assets/buildings/<BuildingId>/<BuildingId>_lineup.png` and `_Masterwork.png` for each building.
4. `store-assets/tools/IcePicks_sheet.png`: the six ice picks.

## Summary

| Step | State |
| --- | --- |
| 0 Sync with the doc | Done. BuildingConfig and its spec follow the new tables. |
| 1 Ice Drill fixes | Done. v4 renders in `store-assets/style-test/v4/`. |
| 2 The other seven buildings | Done. 35 new tiers; every tier fits its pad. |
| 3 Upgrade parts and the ice pick | Done. Five upgrade sets for every tier of every building (200 sets), and six picks. |
| 4 Renders and export | Done. Line-ups, the Legendary sheet, the pick sheet, TRIANGLE_COUNTS.md, IMPORT_NOTES.md, 80 FBX files (40 stations + 40 upgrade files) and 6 pick FBX files. |
| 5 Effects and auras | Done. Play-tested after the Rojo reconnect (see "Play test, after the run"). |

**Specs: 18, all passing, 3,899 checks.** New spec: Effects. Changed: BuildingConfig.
Nothing was uploaded to Roblox.

## Step 0: sync with the design doc (done)

- `BuildingConfig` follows the new doc tables:
  - `Tiers`: the five tier themes.
  - `Stations`: each building's five tier forms.
  - `UpgradeParts`: now a list of five, one per upgrade.
  - `LegendaryForm` and `SignatureAura`: each Legendary's name and aura.
- `tests/BuildingConfig.spec.luau` reads all four of those doc tables.

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

## Steps 2-4: the other seven buildings, upgrade sets, picks, renders, export (done)

- **How they were built:**
  - Seven builder agents worked in parallel, one per building, from one brief (`tools/blender/buildings/`).
  - They used the same kit, palette texture, bevels, glow meshes and attachment names as the Ice Drill.
  - I re-ran all eight on the final framework so the renders and manifests are consistent.
- **Legendary forms** (each mixes creature and machine details):
  - **Frost Golem:** an icy rock golem with glowing eyes, an ice-crystal crown, a raised fist pounding
    the ice, gold-banded machine joints, a frost-core porthole and a back engine.
  - **Captive Star:** a winking sun with a grin in a golden birdcage, with a jewelled crown, piston
    clamps and a focusing lens aimed at the ice.
  - **Kraken Mill:** a violet kraken with goggle eyes and a crown. Its tentacles hold brass chisels and
    swing mallets, with brass head bands, a gear hub, a dial and a water wheel.
  - **Mecha Mole Titan:** from Step 1.
  - **Titan Arm:** a stone-and-metal golem arm swinging a meteor on a chain. A golem head with glowing
    eyes peeks out of the ground. It has pistons, riveted plates and runes.
  - **Dragon Turret:** a red dragon on an armoured turret drum, with glowing eyes, horns and a crown.
    Fire comes from a nozzle in its throat; it has fuel tanks and hoses.
  - **Volcano Forge:** a volcano with a face and a crown of obsidian and gold. It has a lava heart in a
    forge cage, pistons, bellows, an anvil and a lava cannon on a piston arm.
  - **Celestial Observatory:** a calm sun face with a crown of rays, mini planets on brass orbits, a
    domed observatory with a telescope and gears, and a great gold mirror.
- **Working parts:** in every tier the working part (pick, lamp, chisels, ball, nozzle, lava hose,
  mirror) is at the front and points at the ice (-Y, tilted down).
- **Growth:** every tier changes its silhouette, materials and glow, and grows taller rather than wider.
- **Upgrade sets:**
  - Each building has five sets per tier, in that tier's look, snapping onto the tier's attachment
    points.
  - The 4th upgrade (the hit effect) is particles only, so it has no meshes, just stand-ins in the
    renders.
- **Ice picks:**
  - Six tiers (wood, stone, iron, gold, diamond, cosmic), each 3.5 studs long.
  - The diamond and cosmic picks have glow meshes.
  - Attachments: Grip, Tip and Trail.
- **Files:**
  - FBX: `store-assets/buildings/<Id>/fbx/` (`<Id>_T1..T5.fbx` plus `_Upgrades.fbx` per tier) and
    `store-assets/tools/fbx/`.
  - Import notes: `store-assets/buildings/IMPORT_NOTES.md` (RenderFidelity Automatic, the palette, Neon
    glow meshes, collision, pivots and facing, attachments, the upload command).
  - Triangle tables: `store-assets/buildings/TRIANGLE_COUNTS.md`, written by
    `python tools/blender/triangle_table.py --buildings`.

**Triangles.** Each tier is the station without upgrades; Legendary is shown as the station alone and
then with all five upgrade sets (the budget counts the second number):

| Building | Pad | Scrappy (~6k) | Workshop (~10k) | Frost-tech (~15k) | Enchanted (~20k) | Legendary (~30k with Masterwork) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ice Pick Post | 8 | 6,384 | 10,738 | 15,136 | 18,952 | 27,328 / 32,352 |
| Heat Lamp | 8 | 5,584 | 9,700 | 14,930 | 18,664 | 23,094 / 29,026 |
| Chisel Mill | 10 | 6,334 | 10,680 | 14,202 | 19,470 | 24,424 / 28,232 |
| Ice Drill | 10 | 6,200 | 10,592 | 16,012 | 20,726 | 27,120 / 33,064 |
| Wrecking Crane | 12 | 6,536 | 10,980 | 14,052 | 19,142 | 24,380 / 32,080 |
| Flamethrower Turret | 12 | 6,544 | 10,792 | 14,308 | 18,120 | 24,644 / 31,388 |
| Lava Pump | 14 | 6,486 | 10,684 | 15,412 | 20,376 | 23,396 / 28,840 |
| Sun Mirror Tower | 16 | 6,528 | 10,260 | 14,780 | 21,060 | 26,277 / 31,333 |

- **More than 10% over budget:** only the Ice Drill's Legendary with its Masterwork parts, at 33,064
  (+10.2%). Everything else is within +-10%.
- **Mesh size:** the largest single mesh is about 5,000 triangles, so every mesh is under 10,000.

## Step 5: effects and auras (done)

- **Particle textures** in `assets/textures/particles/`:
  - soft glow, sparkle, snowflake, ember, smoke puff, star, water droplet, and four rune glyphs.
  - All white on transparent, made by `tools/make_particle_textures.py`.
- **`src/replicated/EffectsConfig.luau`:**
  - **Tier layers** (from the doc's table, each tier keeping the ones below it):
    - Scrappy: dust on hits.
    - Workshop: steam, a lantern light, sparks on hits.
    - Frost-tech: cold mist, ice sparkles, a coil pulse, ice chips on hits.
    - Enchanted: an aura ring in the building's colour, crystal motes, orbiting runes, a gem beam, and
      a rune flash with a sparkle burst on hits.
    - Legendary: a ground ring, a slow light pulse, and a shockwave on hits.
  - **Signature auras:** one per Legendary.
  - **Masterwork:** gold sparkles and motes, and gold sparks in every hit.
  - **Each emitter spec:** attachment, texture, colours, rate or burst, sizes, lifetimes, speeds,
    spread, light emission and transparency.
  - **Performance rules:** in `EffectsConfig.Rules` and `EffectsRules.luau`.
- **`src/player/BuildingEffects.client.luau`:** builds the emitters, lights and beams on each
  station's attachment points (the greybox stand-ins for now, mapped by model size) and applies the
  rules:
  - your own plot shows everything;
  - other plots run at half rate within 60 studs and none beyond (lights stay on);
  - at most 2 lights per building;
  - a global cap of 8 hit bursts a second;
  - reduced effects: no hit effects and half the ambient particles.
- **`src/replicated/BuildingModels.luau`:** generated from the Blender manifests by
  `tools/make_building_models.py`. `tests/Effects.spec.luau` checks that every attachment
  EffectsConfig names exists on its model, every building and tier fits its pad, every Legendary has
  a signature, and the rules hold.
- **Aura stand-ins** are in the Legendary renders: the Masterwork renders and the Legendary sheet.
- **Studio test** (Edit mode, the repo's `BuildingEffects` run on real stand-in parts with Roblox's
  built-in particle texture; Ice Drill, owned 1, 10, 25, 50, 100 and then Masterwork):

  | Stage | Emitters | Ambient rate/s | Lights | Beams |
  | --- | ---: | ---: | ---: | ---: |
  | 1 owned | 1 (hit dust) | 0 | 0 | 0 |
  | 10 owned | 3 | 2 | 1 | 0 |
  | 25 owned | 11 | 8 | 2 | 0 |
  | 50 owned | 29 | 19.5 | 2 | 1 |
  | 100 owned | 45 | 54.5 | 2 | 1 |
  | Masterwork | 53 | 65.5 | 2 | 1 |

  - Another player's plot ran at scale 0.5 at 40 studs, and its emitters switched off at 120 studs.
  - Reduced effects halved the ambient rate and showed no hits in 5 s.
  - With 31 buildings hitting at once, 41 bursts in 5 s (the cap is 8 a second).
  - The test found a real bug, now fixed: rebuilding a station for a new tier left the old tier's
    emitters behind.

## Play test, after the run

After you reconnected Rojo, Studio had every module. In a Play test I used a throwaway fresh save, added
crystals with the debug action and bought buildings through the real `BuyBuilding` remote:

| Station | Owned | Tier | Emitters (on) | Lights | Beams | Hit bursts in 3 s |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| Ice Pick Post | 100 | 5 | 48 (44) | 2 | 1 | 5 |
| Ice Drill | 100 | 5 | 45 (41) | 2 | 1 | 4 |
| Lava Pump | 100 | 5 | 39 (35) | 2 | 1 | 5 |
| Heat Lamp | 50 | 4 | 29 (26) | 2 | 1 | 4 |
| Chisel Mill | 25 | 3 | 11 (8) | 2 | 0 | 3 |
| Wrecking Crane | 10 | 2 | 3 (1) | 1 | 0 | 2 |
| Flamethrower Turret | 1 | 1 | 1 (0) | 0 | 0 | 2 |

"On" counts the ambient emitters; the rest are hit emitters, which fire bursts instead of a steady rate.

- **Reduced effects** (set through the real `SaveSettings` remote): the Ice Drill's ambient rate went from
  54.5 to 27.25, its hits from 5 to 0, and both came back when it was switched off.
- **Masterwork:** buying the Ice Drill's five upgrades took it to Detail 10, which added the gold layer
  (GoldMotes, GoldAura, GoldSparks). It still had 2 lights.
- **Output:** no errors from the game. `rbxassetid://203785492` fails to load a few times each session,
  but that id isn't in the repo or the place, and it also failed before this test, so it's probably a
  Studio plugin.
- **The look:** the particles render, but with the built-in sparkle texture and pale icy colours they
  barely show against snow and sky. Judge the look again once the real textures and models are
  uploaded.
- **Not tested:** the other-plot distance rule in Play (it needs a 2-player test; it passed in Edit mode).
- **Cleanup:** the `StudioFreshSave` switch was removed afterwards and the place wasn't saved.

## Not done, and why

- **Effects that need uploads before they can be checked:**
  - **The particle textures:** emitters use the built-in sparkle until the PNGs are uploaded and their
    ids are in `EffectsConfig.Textures`.
  - **The look of each layer and signature aura in game:** colours on the real textures, Neon bloom,
    and how the orbit rings and beams read.
  - **Placement on the real models:** emitters sit on the stand-ins' boxes now, and on the real
    attachment points once the FBX models are uploaded.
  - **Performance on a phone** with eight plots.
  - **Hit timing:** hit bursts follow each building's own client-side pace, not a server event,
    because the server ticks damage 4 times a second for all buildings together.
- **Animation:** moving parts (bits, gears, wheels, the wrecking ball, the golem fist) are separate
  meshes built round their axis or pivot attachment, but nothing animates them yet.
- **Not uploaded, as asked.**

## Decisions I made on my own

1. **One build pipeline for all eight buildings** (`tools/blender/buildings/`): it runs headless, so
   seven buildings were built in parallel by agents from one brief. The approved v3 script stays as
   the reference.
2. **Front = -Y faces the ice;** the game turns each station to face the ice on its pad. "Pointed at
   the ice" means forward and a little down.
3. **The Ice Drill's Scrappy hand drill still drills straight down.** A hand drill on an A-frame works
   that way, and your list of fixes named only Workshop, Frost-tech and Enchanted. Every other
   working part points forward at the ice.
4. **The Titan:**
   - It stands 1.1 studs back on a narrower plinth, and its snout points steeper (about 38 degrees
     down), so the bit stays over the 10-stud pad.
   - To fit the budget, the elbow, knee and snout gears are plain gears, and the platform lost its
     inset panels and some crystals.
   - Round segments went back to the v2 level.
5. **Budgets:** each tier is counted without its upgrades, and the Legendary with all five upgrade
   sets, as for v3.
6. **Upgrade sets:** each tier has its own five sets, modelled in the station's space at its
   attachment points (no separate rigging per combination). The 4th upgrade (hit effect) is
   particles only.
7. **Extra attachment names some builders added:**
   - Pivot and Counter on the Wrecking Crane, Gauge1/Gauge2 on the Flamethrower Turret, and Sun on
     the Heat Lamp.
   - HoseA-C and Fountain on the Lava Pump, Hit2 on the Kraken, and Eyes/Eyes2 on Legendaries.
   - I added a Steam1 point at the Titan Arm's elbow so the steam layer has a place to go.
8. **Lava Pump:** Scrappy and Workshop use one bevel segment instead of two (`TIER_Q`) to stay in
   budget. It's the only exception to the two-segment rule.
9. **Effects:**
   - **Hit bursts:**
     - Every tier shows its hit effects from the doc's tier table, whether or not the 4th upgrade is
       bought. The 4th upgrade adds the building's own hit stand-in.
     - A building's hits come every 1.6 s with one copy, down to 0.6 s at 100.
     - The global cap is 8 bursts a second.
   - **Rings:** "orbit" emitters (rings, motes, auras) are a turning ring of 6 attachments, since
     Roblox emitters can't orbit on their own.
   - **Placeholder:** emitters use the built-in sparkle texture until the textures are uploaded.
   - **Colours:** each building's aura colour is my pick (`EffectsConfig.BuildingColours`).
10. **The Effects spec** also checks that every tier fits its pad, from the manifests.

## Anything more than 10% over budget

The Ice Drill's Legendary with its five Masterwork upgrade sets: 33,064 triangles (+10.2%). Every other
tier and every Legendary is within 10%.

## What you need to do by hand

1. Done: Rojo reconnected and the effects were Play-tested (above).
2. **Look at the renders** above and pick any building that needs another pass.
3. **When you're happy, upload** the FBX files and the particle textures with the group tool, then:
   - put the station ids in `BuildingConfig.StationModelIds`;
   - put the texture ids in `EffectsConfig.Textures`;
   - create the attachment points on the uploaded stations (positions in `BuildingModels.luau`).
