# Ice Drill v3: import notes

For when these models are exported and brought into Roblox (not done yet: nothing has been uploaded).
Source: `tools/blender/ice_drill_tiers_v3.py` (scene `StyleTestV3`, saved copy `IceDrillTiersV3.blend`).

## Every MeshPart

| Property | Value | Why |
| --- | --- | --- |
| RenderFidelity | **Automatic** | Roblox lowers the mesh's detail at a distance, so the extra geometry costs little across a plot or from the plaza |
| TextureID | the uploaded `assets/textures/BuildingPalette.png` | one palette texture for every building mesh; UVs sit in the middle of each colour swatch |
| Color | white (255, 255, 255) | the texture carries the colour; a tint would change every swatch |
| Material | SmoothPlastic | the toy look; glow meshes are the exception (below) |
| DoubleSided | false | every mesh is closed |
| CastShadow | true, except glow meshes | |

## Glow meshes (names ending in `Glow`)

Material **Neon**. They hold only the glowing parts (lamp glass, screens, aurora trim, runes, crystals,
eyes), so the game can blink, pulse or dim them without touching the rest. Neon ignores the texture's
shading: keep the palette texture on them so each glow keeps its own colour. They cast no shadow.

## Collision

| Mesh | CollisionFidelity | CanCollide |
| --- | --- | --- |
| The base of each station (Planks, Deck, Platform, Dais) | Box | true |
| Big body parts players could walk into (Posts, Pods, Tower, Body, Legs) | Hull | true |
| Everything else (trim, glow, bits, gears, cables, hoses, crowns, small details) | Box | false |

Spinning parts (`Bit*`, `Gear*`, the flywheel and wheel) are separate meshes built around their axle,
so a MeshPart turning about its bounding-box centre spins true.

## Export

FBX per tier, with the shared settings in `tools/blender/model_helpers.py` (`export_fbx`). Every mesh
is under 10,000 triangles (the largest is the Titan's head at 5,236), safe for FBX import. Uploads
always go to group 921449746 (`tools/upload_models.py`).

## Attachment points

Empties named `<Station>_Att_<Name>` (Bit, Lamp1/2, Gear1/2, Steam1/2, Hit, Trail, NamePlate, Crown on
the Titan). Export them as Attachments (or read their positions into a config) so upgrade part sets
and particle emitters snap onto them in game.
