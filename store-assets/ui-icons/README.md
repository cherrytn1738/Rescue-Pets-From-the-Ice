# UI icons

The in-game button and window icons: 256x256 PNG, transparent background, no text, a thick dark outline (about
7 px) so they read at 48 px on a coloured button. Not uploaded anywhere. Made by `tools/icons/render_icons.py`
(headless Blender, `ui` mode: the game's own creature models, the tier-1 building stations from
`store-assets/buildings/<Id>/<Id>.blend`, the ice pick tiers and simple props) and `tools/icons/compose_icons.py --ui`
(Pillow: outline, soft glow, shadow, sparkles, small 2D extras). Regenerate with
`python tools/icons/compose_icons.py --ui --render` (or name some: `--ui --render Pets Home`; `--ui` alone composes
again from the last renders). `contact_sheet.png` shows each icon on its card colour at 96 px and 48 px, plus a copy
on a checkerboard.

| File | Used for | What it shows |
|---|---|---|
| `Build.png` | Build menu button (orange) | The tier-1 Ice Pick Post station with a chunky hammer |
| `Upgrades.png` | Upgrades menu button (green) | The gold ice pick in front of a big green up-arrow |
| `Pets.png` | Pets menu button (pink) | Snow Bunny, cheering |
| `Book.png` | Creature Book menu button (teal) | A chunky icy-blue book with a gold paw on the cover, Penguin Chick peeking over the top |
| `Rebirth.png` | Rebirth menu button (purple) | A glowing faceted Frost Core inside two gold circular arrows |
| `Home.png` | Home menu button (ice blue) | A cosy ice-brick igloo with a snow cap and a warm glowing doorway (reads better at 48 px than the wide plot gate) |
| `Shop.png` | Shop menu button (glacier blue) | An open wooden treasure chest heaped with cyan crystals |
| `Codes.png` | Codes menu button (slate) | A gold ticket with a blue snowflake and a tear line |
| `Building_IcePickPost.png` | Build window | The tier-1 Ice Pick Post station, three-quarter view |
| `Building_ChiselMill.png` | Build window | The tier-1 Chisel Mill station, same camera |
| `Building_IceDrill.png` | Build window | The tier-1 Ice Drill station, same camera |
| `Building_HeatLamp.png` | Build window | The tier-1 Heat Lamp station, same camera |
| `Building_WreckingCrane.png` | Build window | The tier-1 Wrecking Crane station, same camera |
| `Building_FlamethrowerTurret.png` | Build window | The tier-1 Flamethrower Turret station, same camera |
| `Building_LavaPump.png` | Build window | The tier-1 Lava Pump station, same camera |
| `Building_SunMirrorTower.png` | Build window | The tier-1 Sun Mirror Tower station, same camera |
| `Pick1.png` ... `Pick6.png` | Upgrades window, ice pick tiers | The wooden, stone, iron, gold, diamond and cosmic picks, all at the same angle |
| `FrostTouch.png` | Upgrades window, Frost Touch | The iron pick with ice on its head inside a glowing cyan frost swirl, snowflakes |
| `BiggerBurst.png` | Upgrades window, ice upgrade | A fountain of cyan crystals bursting up out of a shattered ice block |
| `CrystalYield.png` | Upgrades window, ice upgrade | A crystal pile with a green 3D plus |
| `FastSled.png` | Upgrades window, ice upgrade | A wooden sled on metal runners carrying an ice block (a pet silhouette inside), speed streaks |
| `UpgradeBadge.png` | Overlay on a building icon (building upgrades) | A green up-arrow |
