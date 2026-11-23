# Overnight run report

Branch `overnight-milestones` (pushed after each milestone; merge it into `main` when you're happy).
Nothing was uploaded to Roblox. Building art stays greybox. The earlier style-test files
(`assets/`, `store-assets/style-test/`, `tools/blender/`) are still uncommitted, as you asked.

## Look at these first

1. `store-assets/creatures/RosterSheet.png`: all 18 creatures, each with its silhouette and Golden version
2. `store-assets/creatures/<Id>/sheet.png` and `loop.gif`: each creature's views and idle loop

## Milestone 1: the 18 creatures (done)

- All 18 creatures from the roster are built with the voxel skill's box rig: `tools/pets/creatures/<Id>.py`.
  Six builder agents worked in parallel from one brief, and I built the Snow Bunny first as the reference.
- **Size:** 3 studs (Legendary and Mythic 3.6). `tools/pets/build_pet.py` measures each model and
  sets its stud scale so its biggest dimension (height or length) hits the target. So a long, low
  pet (Seal Pup 1.54 tall, Glacier Otter 2.26 tall) is 3 studs long, not 3 studs tall.
- **Animations:** every pet has `Idle` (the idle animation), `Hop` (moving and following) and `Cheer`
  (a rescue celebration).
- **Silhouette:** the same model in one dark shade (`PetLooks.Apply(model, data, "Silhouette")`;
  `ShowEyes` lights the eyes for the 60% crack stage). It is rendered for every creature
  (`render/variant_silhouette_ol.png`).
- **Golden:** a material swap. Each part turns gold, shaded by its normal brightness, in Foil; the
  eyes keep their colour and glow stays Neon (`render/variant_golden_ol.png`). In Studio I built all
  18 in Normal, Golden and Silhouette and checked the properties: Golden is Foil with the eyes kept,
  Silhouette is one dark SmoothPlastic. Studio screenshots stopped working during the run (below),
  so check them by eye in Studio.
- **In game:** each pet is built from Parts by `PetBuild` (the skill's ModelBuild) from its generated
  `<Id>Data`/`<Id>Clips` modules, so nothing needs uploading.
- **Parts per pet:** 68 (Seal Pup) to 131 (Mini Yeti).

## Milestone 2: gameplay Days 1 and 2 (greybox)

(see below; filled in as the run goes)
