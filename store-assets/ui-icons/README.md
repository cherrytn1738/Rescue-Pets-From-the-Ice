# UI icons

The in-game button and window icons: 256x256 PNG, transparent background, no text (except the pick tiers' numeral
badge), a thick dark outline (about 7 px) so they read at 48 px on a coloured button. Uploaded as group 921449746
(`upload_manifest.json`; ids in `UITheme.Icons`). Made by `tools/icons/render_icons.py`
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
| `Tool1.png` ... `Tool18.png` | Upgrades window and its Tools tab, the 18 tools | Each tool leaning right with its head at the top (its own model from tools/blender/tools_tiers.py), a glow of its spark colour (IceLooks.ToolSparks) behind the head, and a round tier badge (bold white 1-18, dark outline) in that colour bottom right; the magical tiers 11-18 get a sparkle. `Pick1.png` ... `Pick6.png` are the retired ice picks' icons (no longer used) |
| `FrostTouch.png` | Upgrades window, Frost Touch | The iron pick with ice on its head inside a glowing cyan frost swirl, snowflakes |
| `BiggerBurst.png` | Upgrades window, ice upgrade | A fountain of cyan crystals bursting up out of a shattered ice block |
| `CrystalYield.png` | Upgrades window, ice upgrade | A crystal pile with a green 3D plus |
| `FastSled.png` | Upgrades window, ice upgrade | A wooden sled on metal runners carrying an ice block (a pet silhouette inside), speed streaks |
| `UpgradeBadge.png` | Overlay on a building icon (building upgrades) | A green up-arrow |
| `RebirthBadge.png` | Rebirth window, big corner picture (~170 px) | Two glossy ice circular arrows (pale cyan to white) chasing round a glowing faceted Frost Core |
| `FrostCore.png` | Frost Cores (Rebirth window, rewards; reads at 40-90 px) | The faceted glowing ice-blue Frost Core with three tiny ice shards floating round it |
| `Rank0.png` | Rebirth rank badge: no rank yet | A chunky slate grey-blue shield with a light rim and a pale snowflake, no stars |
| `Rank1.png` | Rebirth rank badge: rank 1 | The same shield in light blue, one gold star, a small white snowflake by the point |
| `Rank2.png` | Rebirth rank badge: rank 2 | Teal, two gold stars |
| `Rank3.png` | Rebirth rank badge: rank 3 | Purple, three gold stars |
| `Rank6.png` | Rebirth rank badge: rank 6 | Gold, four white stars, a sparkle |
| `Rank10.png` | Rebirth rank badge: rank 10 | A rainbow shield (the hue runs across it), five white stars, sparkles |
| `UnlockPetSlot.png` | Rebirth window: what a rank opens (a pet slot) | Arctic Fox Kit on a round glowing ice pedestal, a green 3D plus at the upper right |
| `UnlockLayer.png` | Rebirth window: what a rank opens (an ice layer) | A stack of three ice layers (pale blue, deep blue, black ice with glowing orange veins: the Frozen Core) and a green down-arrow |
| `IceBlock.png` | Block level | A rounded ice block with a Snow Bunny silhouette and a soft glow inside |
| `CrystalPile.png` | Welcome Back screen, the hero picture (~200 px), and small in a row | A big heap of cyan crystals with a big crystal on top |
| `RobuxItems.png` | Rebirth window: "your Robux purchases are kept" | A purple gift box with a gold ribbon and bow |
| `WelcomeClock.png` | Welcome Back screen, big corner badge (~170 px) | An ice-blue alarm clock (white face, dark hands at 10:10, gold bells, little feet) with a cyan snowflake badge over its lower right |
| `Sunburst.png` | Welcome Back screen, behind the crystal pile (tinted gold and turned slowly) | 512x512, 16 white rays, long and short in turn, fading out to the edges and a little at the centre; no outline (2D) |
| `Tick.png` | Before/After and checklist ticks | A chunky green tick with a lighter top, thick dark outline (2D) |
| `ArrowRight.png` | Between the "Before" and "After" cards | A chunky white to light blue arrow pointing right, thick dark outline (2D) |

`Sunburst`, `Tick` and `ArrowRight` are drawn in Pillow (`UI_FLAT` in `compose_icons.py`, no Blender):
`python tools/icons/compose_icons.py --ui Sunburst Tick ArrowRight`.
