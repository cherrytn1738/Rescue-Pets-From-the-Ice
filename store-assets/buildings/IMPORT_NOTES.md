# Buildings: import notes

How these models are uploaded and brought into Roblox. All of them are uploaded (ids in `ASSET_IDS.md`).
Source: `tools/blender/buildings/<BuildingId>.py` on `framework.py`. Rebuild one building with:
`blender -b --factory-startup --python tools/blender/buildings/run.py -- <BuildingId> build render export`.

## Files

Per building, in `store-assets/buildings/<BuildingId>/`:
- `fbx/<Id>_T<n>.fbx`: the station for tier n (1 Scrappy, 2 Workshop, 3 Frost-tech, 4 Enchanted,
  5 Legendary). One model per tier, so 40 stations in all.
- `fbx/<Id>_T<n>_Upgrades.fbx`: that tier's five upgrade sets, modelled in the station's own space.
  Meshes are named `<Id>T<n>U<u>...` (u = 1 better part, 2 lights, 3 moving extra, 4 hit effect,
  5 signature). The 4th upgrade is particles only, so it has no meshes.
- `<Id>_manifest.json`: every mesh with its triangles, the tier's size, whether it fits its pad, and its
  attachment points.
- `<Id>_lineup.png` and `<Id>_Masterwork.png`: the renders.

Upload with the group tool, which uploads as group 921449746:
`python tools/upload_models.py --manifest store-assets/buildings/upload_manifest.json store-assets/buildings/<Id>/fbx/*.fbx`.
Then `python tools/write_asset_ids.py` writes the ids into `BuildingConfig.ModelIds` (and `ASSET_IDS.md`), and
`tools/studio/build_templates.luau` (Edit mode) rebuilds the Studio templates with every setting below. Save the place.

## Every MeshPart

| Property | Value | Why |
| --- | --- | --- |
| RenderFidelity | **Automatic** | Roblox lowers a mesh's detail at a distance, so the extra geometry costs little across a plot or from the plaza |
| TextureID | the uploaded `assets/textures/BuildingPalette.png` | one palette texture for every building mesh; UVs sit in the middle of each colour swatch |
| Color | white (255, 255, 255) | the texture carries the colour |
| Material | SmoothPlastic | the toy look; glow meshes are the exception |
| CastShadow | true, except glow meshes | |

**Glow meshes** (names ending in `Glow`): Material **Neon**, with the palette texture kept so each glow
keeps its colour. They cast no shadow. Keeping them separate lets the game pulse or dim them.

**Organic surfaces** (faces, tentacles, golem bodies, the dragon, the mole's fur and head) are exported
with plain smooth normals. Hard surfaces use weighted normals. FBX keeps both, so don't recalculate
normals on import.

## Collision

| Mesh | CollisionFidelity | CanCollide |
| --- | --- | --- |
| The station's base or platform | Box | true |
| Big body parts players could walk into | Hull | true |
| Everything else (trim, glow, working parts, gears, cables, upgrade sets) | Box | false |

## Placement and attachment points

- **Pivot and facing:** each station's pivot is the centre of its pad on the ground. Its front (-Z in
  Roblox, -Y in Blender) faces the ice, so turn the station to face the ice when you place it on its pad.
- **Size and height:** each tier is grown to its height from `BuildingConfig.TierHeights` (docs: "Height grows
  fast with each tier") by `tools/blender/buildings/heights.py`. Everything above the base scales uniformly
  about the base's top centre; the base keeps its pad size. The scale is capped so the structure stays in its
  room: short of the half-way line to every other pad, off the fence ring round the ice and inside the plot.
  The manifest's `growth` records the scale, the height reached and whether it fell short. `fitsPad` means
  the base is on its pad and the rest is in its room.
- **Import scale:** building FBX files are exported at a quarter scale, so Studio's import arrives at 25x
  (not 100x). A grown tier has meshes over 20 studs, and Roblox caps a part at 2048 studs on each axis.
  `tools/studio/build_templates.luau` detects the factor. The ice picks still arrive at 100x.
- **Attachment points:**
  - **Names:** Work and Work2 (the working part), Lamp1, Lamp2, Gear1, Gear2, Steam1, Steam2, Hit,
    Trail, NamePlate, Aura and Top, plus Crown (and Eyes where there is one) on the Legendary.
  - **Where they are recorded:** the manifests hold them, and `src/replicated/BuildingModels.luau` is
    generated from them by `python tools/make_building_models.py`.
  - **In game:** create them as Attachments on the uploaded stations. EffectsConfig puts its emitters,
    lights and beams on them (`BuildingEffects.client`), and `tests/Effects.spec.luau` checks that every
    name it uses exists.
- **Upgrade sets** are modelled where they attach. Give each set the same pivot as its station and it
  sits on the right attachment points.
- **Moving parts** (bits, gears, wheels, reflectors, mirrors, wrecking balls) are separate meshes built
  round their own axis, so they spin true.

## Effects

Particles, beams and lights come from `EffectsConfig`. The FX meshes in the renders (aura stand-ins,
puffs, sparks, trails) are only for judging the look and are not exported. The particle textures are in
`assets/textures/particles/` (white on transparent). After uploading them as group 921449746, put their
ids in `EffectsConfig.Textures`; until then emitters use Roblox's built-in sparkle texture.

## Ice picks

`store-assets/tools/fbx/IcePick_T1..T6.fbx` (wood, stone, iron, gold, diamond, cosmic):
- Each is about 3.5 studs long, with the handle along +Y and the pommel at the pivot.
- Attachments are Grip (the hand), Tip (the striking point, for sparks) and Trail. They're listed in
  `store-assets/tools/IcePicks_manifest.json` and `BuildingModels.Picks`.
- The diamond and cosmic picks have a glow mesh (Neon).
- Weld the pick to the character's RightHand at Grip.
