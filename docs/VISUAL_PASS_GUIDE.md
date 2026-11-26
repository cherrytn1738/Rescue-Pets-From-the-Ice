# Visual pass guide

Your checklist for the full visual pass: every model, all the UI and every effect.
- **Known issues:** first, so you can start with what's already known to be wrong.
- **Retaking the screenshots:** how to retake the screenshot set and compare before and after.
- **The route:** goes through the game in order, with the F2 debug steps to set up each stop.
- **The map:** says where each visual lives, so you can point Claude Code at the right file, and what to re-run after a change.

Screenshots of everything, taken 2026-11-26 before the pass: `store-assets/visual-review/`. Open `store-assets/visual-review/index.html` in a browser (it works from disk).

## Known visual issues

Already known:
- [ ] **VIP lounge:** still a plain fence, floor and sign (`PlazaService`, `VipLounge.client`). Not remodelled.
- [ ] **Golden Glacier:** a flat box with a cardboard-looking wedge (`src/player/GoldenGlacier.client.luau`).
- [ ] **Frozen Core glow:** a hard flat disc inside the black ice (`IceLooks`, `src/player/IceBlocks.luau`).
- [ ] **DAILY CHEST label:** can sit behind the HUD's crystal counter (`PlazaService` `floatingLabel`, a BillboardGui).

Noticed tonight:
- [ ] **Light ice layers with a Legendary or Mythic inside:** the glow washes the whole block milky white, and the creature's silhouette almost disappears (`ice/layer1_Mythic`, `layer2_Mythic`, `layer1_Legendary`). `IceLooks` (rarity glow colours and strength), `src/player/IceBlocks.luau`.
- [ ] **Layer 4, Crystal Ice:** the ice hardly shows, so the creature reads as a flat black cut-out, and the rarity glow only tints the floor (`ice/layer4_*`). `IceLooks` layer looks.
- [ ] **Golden pets** are one flat yellow, and markings disappear (the Polar Bear Cub's scarf, the Puffin's beak) (`pets/*_golden`). How a Golden pet is coloured: `src/player/PetFollow.client.luau` and the pet build modules.
- [ ] **Legendary and Mythic rescues:** the server announcement toast lands on top of the big rescue title, so both are hard to read (`rescue/Legendary`, `rescue/Mythic`). `Banners.luau` (toast position) and `RescueMoment.luau`.
- [ ] **Heat Lamp at T5 and Masterwork:** a big white bloom at its base, and the "Masterwork" plate partly hidden behind the model (`buildings/HeatLamp_T5`, `HeatLamp_Masterwork`). `EffectsConfig` (the Legendary ring and glow), `PlotService` (`MasterworkPlate`).
- [ ] **The rebirth frost-over** covers the whole screen in near-white at its peak (`ui/rebirth_frost_over`). Intended? `RebirthWindow.client` / the frost effect.
- [ ] **New tonight (built from the UI kit, so restyle with the rest):** the "Updating the game, back in a moment!" screen (`ui/update_screen`) and the server message panel (`ui/server_message`, used for "update coming" and admin announcements). The panel draws over open windows on purpose (players must see it), and it sits at 18% from the top. `src/player/ServerNotices.client.luau`.
- [ ] **Pets window on phones:** with a full inventory it holds 50 live 3D previews (about 12K Instances). Consider pictures, or building a preview only when its card scrolls into view. `src/player/PetsWindow.client.luau`, `PetViewport.luau`.
- [ ] **From the code (not seen on screen):**
  - The Mythic Block has no look of its own: it's a normal block with better odds.
  - Shop cards have no pictures (`UITheme.ShopIcons` is empty and no code reads it).
  - The Frost Rush shows only as HUD text and banners, with no effect in the world.
  - `IceLooks.Particles.Chips` and `.Sparkles` are defined but unused.
- [ ] **Text, not look (a question in the report):** the welcome-back popup says "You earn for up to 1h while you're away", but the rule is half your building income for up to 2 hours away.

Can't be screenshotted, so check by hand: Roblox's own purchase prompt (Studio's test prompt doesn't show in a screen capture), and the rare-block beam over another player's plot (needs a second player).

## Retaking the screenshots

1. **Set up Studio:** open the place with Rojo connected and "Enable Studio as MCP server" on. Maximize Studio and keep it in front (a screen capture of a background window comes back grey, and a sleeping display makes captures time out).
2. **Start a solo Play** (Test > Play). Some categories reset the save, so it plays as a throwaway Studio save. Your real saves are never touched (Studio uses the Studio stores).
3. **Run** `python tools/visual_review.py` for the whole set (318 pictures, about 25 minutes). Other forms:
   - `python tools/visual_review.py buildings ui` for some categories;
   - `--only ice/crack_stage2` for one shot (repeatable);
   - `--size desktop` for one size;
   - `--list` for every shot name.
4. **What it saves:**
   - JPG at quality 90 into `store-assets/visual-review/<category>/` with the same names every time;
   - desktop shots at 1920x1080;
   - UI shots also at 844x390 and 667x375 (`_844x390`, `_667x375` in the name).
5. **Before and after:** the first time a run replaces a picture, the old one is kept in `store-assets/visual-review-before/`, and the gallery shows the pair side by side (tick "Before / after"). Delete that folder to start a fresh comparison.
6. **Where the shots are defined:** `tools/studio/visual_review_shots.luau`, with what each sets up, the camera and the UI to open. You can also run one shot by hand: paste the file into the command bar on the Client, set `SHOT` and `SIZE` at the top, and run. `SHOT = "?cleanup"` gives the camera back.

The helper runs on the debug menu's actions, so a shot looks exactly like the game.

## The route

Play solo in Studio (Test > Play). You'll be the developer, who owns every pass, so your name tag is gold (VIP) and you have extra pet slots. To see the game as a normal player, use Test > Clients and Servers with 1 player.

**Before you start:**
- The debug menu is **F2** (or the purple DEBUG button on the right edge). Pick an action, fill in its inputs, press Run; the target is you unless you pick someone else.
- Set the block level high before judging the ice block: **F2 > Save > Set block level** (e.g. 400), so a strong plot doesn't break every block the moment it arrives.
- **Photo booth:** `python tools/visual_review.py <category>` retakes a category, and `--only <shot>` retakes one shot (see "Retaking the screenshots" below).

### 1. A new player's first minute
- **Set up:** F2 > Testing switches > **Fresh save: On**, then Stop and Play again. Every Play is now a brand-new player until you turn it off.
- **Look for:**
  - the first view of your plot: gate, name boards, walls, the frozen stage, the block on its mound;
  - the HUD at zero;
  - the tutorial arrow.
- [ ] Checked
- Notes:

### 2. The tutorial (5 steps)
- **Set up:** the fresh save above. Then tap the ice, build an Ice Pick Post, free the first creature, and equip it (PETS).
- **Look for:**
  - the arrow and words at each step;
  - the first building rising out of the snow;
  - the first rescue's banner, confetti and NEW badge;
  - the "THAWED" code at the end.
- [ ] Checked
- Notes:

### 3. The first buildings and their tiers
- **Set up:** F2 > Save > **Set one building's count and upgrades**: Building, Count (1 = T1, 10 = T2, 25 = T3, 50 = T4, 100 = T5), Upgrades (5 at 100 owned = Masterwork). Do every building at 1, 10, 25, 50 and 100, then 100 + 5 upgrades.
- **Look for:**
  - each tier's theme: Scrappy, Workshop, Frost-tech, Enchanted, Legendary;
  - the upgrade parts U1-U5;
  - the stars on the station badge and the "<name>'s Masterwork" plate;
  - the T5 ground rings, auras and particles;
  - the fence ring (a faded Ice Pick Post once the Heat Lamp is owned).
- **Moments:** set a building to 9, then buy 1 in the Build window ("Your X evolved!" and the white flash). Set it to 0 and buy 1 for the rise.
- [ ] Checked
- Notes:

### 4. Every layer, 1 to 6
- **Set up:** F2 > Ice block > **Set rebirths** = 3 (opens layer 6). Then F2 > Save > **Set block level** = 5, 15, 25, 35, 45, 55 in turn.
- **Look for:**
  - each layer's ice look: Fresh Snow, Blue Ice, Ancient Ice, Crystal Ice, Primordial Ice, Frozen Core;
  - the creature's silhouette through the ice;
  - the camera dip on a new layer (break a block to see it);
  - the crack stages: F2 > Ice block > **Set the current block's HP left** = 100, 79, 59, 39, 19.
- [ ] Checked
- Notes:

### 5. A rescue of each rarity
- **Set up:** F2 > Ice block > **Pick the creature inside**, choosing one of each rarity (Snow Bunny Common, Arctic Fox Kit Uncommon, Polar Bear Cub Rare, Mini Yeti Epic, Frost Dragon Hatchling Legendary, Aurora Fox Mythic). Then F2 > Ice block > **Force a rescue**.
- **Look for:**
  - the glow colour in the ice before the break;
  - the shatter;
  - the rarity banner and confetti colour;
  - crystals flying;
  - the sled bringing the next block;
  - for Legendary and Mythic, the server announcement toast.
- **Mythic Block:** F2 > Robux > **Simulate a receipt** > Mythic Block, then break the current block.
- [ ] Checked
- Notes:

### 6. Pets and Golden pets
- **Set up:**
  - F2 > Ice block > **Give a pet** (Golden: On for the golden version).
  - Equip them in PETS.
  - **Set rebirths** = 10 for every rank slot; with your passes you can equip up to 7.
- **Look for:**
  - each creature following you, walking and idle;
  - the Golden versions;
  - how 1 to 7 pets arrange around you;
  - the Pets window cards, Lock, and "Delete all below".
- [ ] Checked
- Notes:

### 7. The Creature Book
- **Set up:** give a few pets (normal and Golden) as above. Open BOOK.
- **Look for:**
  - every page and tab, on a phone size too;
  - seen and unseen silhouettes;
  - the page rewards.
- **Rewards:**
  - all 18 Golden gives the golden pick skin (F2 > Ice block > Respawn to see it);
  - both Mythics give the aurora trail (walk to see it).
- [ ] Checked
- Notes:

### 8. Rebirth
- **Set up:** F2 > Save > **Set block level** = 31. Open REBIRTH and rebirth (two presses).
- **Look for:**
  - the Rebirth window;
  - the frost-over effect;
  - the rank title and colour on your name tag and plot trim. F2 > **Set rebirths** = 1, 2, 3, 6 and 10 shows each rank colour (respawn after each).
- **HUD:** the rebirth goal line appears from level 25.
- [ ] Checked
- Notes:

### 9. A Golden Glacier rush
- **Set up:** F2 > Ice block > **Drop a Golden Glacier in the plaza now**. Walk to the plaza and tap it.
- **Look for:**
  - the countdown;
  - the landing;
  - the gold block and its gem;
  - the four crack stages;
  - the tap bar on your HUD in range, and the sign above it from further away;
  - the break, and the Frost Rush on your HUD.
- **Known issue:** a flat box with a cardboard-looking wedge.
- [ ] Checked
- Notes:

### 10. The plaza
- **Set up:** F2 > Player > **Send to their plot**, then walk out through your gate to the plaza.
- **Look for:**
  - the three leaderboards;
  - the daily chest and its label;
  - the codes kiosk;
  - the home beacon over your plot;
  - the pines, terrain and sky;
  - the other plots around the ring.
- **Rare beams:** a beam over another player's plot holding a Legendary or Mythic needs a second player (Test > Clients and Servers, 2 players).
- [ ] Checked
- Notes:

### 11. The VIP lounge
- **Set up:** walk to the lounge in the plaza. You own VIP as the developer; a test player doesn't, and gets a toast at the door.
- **Look for:** the fence, floor, sign and gold door.
- **Known issue:** still the plain fence, floor and sign.
- [ ] Checked
- Notes:

### 12. The shop and each purchase prompt
- **Set up:** open SHOP. As the developer, the passes show OWNED. Use Test > Clients and Servers (1 player) to see them for sale.
- **Look for:**
  - both tabs and every card;
  - the INFO odds on the Mythic Block;
  - gift mode;
  - Roblox's test purchase prompt when you press a buy button (Studio's own prompt; cancel it);
  - "Thanks! You got ..." after a purchase, which you can trigger with F2 > Robux > **Simulate a receipt**;
  - the Shatter Now button on the right edge: blue normally, gold and pulsing with a Rare or better inside.
- [ ] Checked
- Notes:

### 13. Settings, offline earnings and other popups
- **Set up:**
  - Open SETTINGS. Try Reduced effects on and off while looking at a maxed plot.
  - F2 > Progress > **Offline earnings now** (e.g. 5400 s) for the welcome-back popup.
  - F2 > Progress > **Soft shutdown: show everyone the update screen** and **the 'update coming' warning**.
  - Redeem a wrong code for the error toast.
- [ ] Checked
- Notes:

### 14. Phone layouts
- **Set up:** in Play, in the command bar with the **Client** selected, run `workspace:SetAttribute("StudioScreenSize", Vector2.new(844, 390))`, then the same with `667, 375`. Set it back with `nil`.
- **Look for:**
  - the HUD;
  - every window and tab;
  - banners and toasts fitting;
  - buttons big enough to tap.
- [ ] Checked
- Notes:

## Where each visual lives

What makes each model, screen and effect, and what to re-run after changing it. Point Claude Code at the file in the "Controlled by" column.

### Pipeline shorthand (used in the "After a change" column)

| Tag | Meaning |
|---|---|
| **SYNC** | A `.luau` edit only. Rojo syncs it, so nothing else needs re-running. Run the specs named in the row if it has any. |
| **UPLOAD-M** `<manifest> <files>` | `python tools/upload_models.py --manifest <manifest> <files>` uploads as group 921449746. A changed `.fbx` Model is **updated in place and keeps its id**. |
| **UPLOAD-P** `<files>` | The same tool for `.png` and `.ogg` files. A changed picture or sound becomes a **NEW asset with a NEW id**, which you swap into the config named in the row. |
| **IDS** | `python tools/write_asset_ids.py`. It covers only the buildings, the picks, the particle textures and `BuildingPalette.png`, writing to `BuildingConfig.ModelIds` / `PaletteTextureId`, `UpgradeConfig.PickModelIds`, `EffectsConfig.Textures` and `ASSET_IDS.md`. It does **not** cover MapConfig, UITheme.Icons, AudioConfig, the sky or the pines; you paste those ids by hand. |
| **TPL(x)** | Run `tools/studio/build_templates.luau` in Studio **Edit** mode. Line 29 reads `local ONLY = ONLY_OVERRIDE`: change it in the pasted copy to `local ONLY = "x"`, where x is a building id, `"Picks"`, `"Plot"` or `"Plaza"`. With nil it builds all 8 buildings and the picks, but **not** Plot or Plaza. `tmp/build_one.sh <ONLY>` makes that substitution and runs it through `tmp/mcp.py`. |
| **WORLD** | Run `tools/studio/build_world.luau` in Edit mode. It replaces the terrain, `Workspace.Scenery` and `Lighting.Sky`. |
| **SAVE** | Save the place and back it up. Templates, terrain, sky and lighting live in the place file, not in Git. |
| **SPECS** `<names>` | `python tools/run_specs.py <names>`. It needs Studio in Edit mode with the MCP server on. |

Design text for every visual is in `docs/GAME_DESIGN.md`, in these sections: "The ice block", "Detail levels", "Effects and auras", "Creature roster", "How buildings, upgrades and pets look", "Plot and map layout", "UI and controls", "Screens" and "Sound and effects".


### Building models (8 buildings x 5 tiers)

| Visual | Controlled by | Source art | After a change |
|---|---|---|---|
| Station model per tier (Scrappy, Workshop, Frost-tech, Enchanted, Legendary at 1/10/25/50/100 owned) | `src/server/PlotService.luau` `RefreshBuildings` clones `ServerStorage.BuildingTemplates.<Id>.T<tier>` (`tierFor`, `template`, `realStation`, `padCFrame`). Numbers are in `src/replicated/BuildingConfig.luau`: `Tiers`, `StationMilestones`, `TierHeights` (Back/Side/Front), `PadGroups`, `Buildings[].Pad`. Ids are in `BuildingConfig.ModelIds` (generated block). Sizes and attachments are in `src/replicated/BuildingModels.luau` (GENERATED, don't hand-edit). | `tools/blender/buildings/<Id>.py` (TIER_FNS) on `framework.py` + `tools/blender/building_kit.py` (+ `building_kit_detail.py`, `building_kit_fantasy.py`, `model_helpers.py`), with heights from `tools/blender/buildings/heights.py`. Output goes to `store-assets/buildings/<Id>/fbx/<Id>_T<n>.fbx`, `<Id>_manifest.json` and `<Id>_lineup.png`. | 1. `blender -b --factory-startup --python tools/blender/buildings/run.py -- <Id> build render export`<br>2. `python tools/make_building_models.py`<br>3. UPLOAD-M `store-assets/buildings/upload_manifest.json store-assets/buildings/<Id>/fbx/*.fbx`<br>4. IDS<br>5. TPL("<Id>")<br>6. SAVE<br>If tier 1 changed, also re-render the `Building_<Id>` icon (and `Build`, which is IcePickPost T1). See A12. |
| Upgrade part sets U1..U5 per tier (better part, lights, moving extra, hit effect, signature) | The template's `Upgrades.U1..U5`, shown by `PlotService.ownedUpgrades` / `realStation`. Unlocks and costs are in `src/replicated/UpgradeConfig.luau` `BuildingUpgrades` (`UnlockAtOwned` {1,10,25,50,100}). `BuildingConfig.Buildings[].UpgradeParts` is descriptive text only. | The same building file, its `UPGRADES(u, t, ...)`, writes `fbx/<Id>_T<n>_Upgrades.fbx`. U4 is particles only, with no meshes. | Same as the station row. |
| Faded station (shrunk to 60%, Neon off, no ambient FX) and the Ice Pick Post fence ring | `PlotService.RefreshBuildings` (`topOrder`: every building below the highest one owned fades), `realStation(faded)` and `fenceStation`. Numbers are in `BuildingConfig.FadedScale` 0.6 and `BuildingConfig.Fence` {Radius 23, Slots 12, FrontGap 1, Scale 0.75, Parts}. `src/player/BuildingEffects.client.luau` reads the `Faded` attribute and turns ambient off and lights off. | The fence uses the IcePickPost T1 meshes named in `Fence.Parts`. | Config: SYNC. Model: as in the station row. |
| Greybox stand-ins (only while a template is missing) | `PlotService` `STAND_IN_COLOURS`, `standInSize` | none | SYNC |
| Station badge "Ice Drill ×37 ★★ MASTERWORK" and its visibility | `PlotService.label` / `nameTag` (BillboardGui, FredokaOne, white, MaxDistance 160). Stars come from `EconomyRules.BuildingUpgradeCount`. Show/hide is `src/player/NameTags.client.luau` with `BuildingConfig.NameTags` {Size 7x1.4, NearDistance 28, LookAngle 30, LookDistance 150, TopCentre 0.4x0.25}. | none | SYNC |
| Masterwork (detail level 10 = all 5 tiers + all 5 upgrades) | The gold plate is `MasterworkPlate` in `PlotService.RefreshBuildings` (back (120,80,10), text (255,220,110)). The gold FX are `EffectsConfig.Masterwork` {Ambient GoldAura, GoldMotes; Hit GoldSparks}. Rules: `EconomyRules.DetailLevel` / `IsMasterwork`, `BuildingConfig.MaxDetailLevel` 10. | A render only: `store-assets/buildings/<Id>/<Id>_Masterwork.png` (run.py render) | SYNC |
| Palette texture (the colour of every building, pick, plot and plaza mesh) | `BuildingConfig.PaletteTextureId` (generated). `build_templates.luau` applies it to every MeshPart (Color white, SmoothPlastic, RenderFidelity Automatic). Meshes whose names end in `Glow` become Neon with no shadow. | `building_kit.py` palette (8x6 swatches, `SWATCHES`) writes `assets/textures/BuildingPalette.png` | 1. Re-export<br>2. UPLOAD-P `--manifest assets/textures/upload_manifest.json assets/textures/BuildingPalette.png` (new id)<br>3. IDS<br>4. TPL(nil), TPL("Plot"), TPL("Plaza")<br>5. SAVE |

### Building effects (particles, lights, beams, rings)

| Visual | Controlled by | Source art | After a change |
|---|---|---|---|
| Per-tier layers (each tier keeps the ones below) | `src/replicated/EffectsConfig.luau`, local `tierLayers(tier, colour)`:<br>T1 Dust hit.<br>T2 Steam, Lantern light, Sparks hit.<br>T3 ColdMist, IceSparkles, CoilPulse light, IceChips hit.<br>T4 AuraRing, Motes, Runes, GemBeam, RuneFlash and SparkleBurst hits.<br>T5 GroundRing, LegendPulse light, Shockwave hit.<br>Shared colour locals: WHITE, GOLD, ICE, ICE_DEEP, STEAM. Per-building colour: `EffectsConfig.BuildingColours`. Entry point: `EffectsConfig.For(id, tier, masterwork)`. | none | SYNC; SPECS `Effects` (every attachment named must exist in BuildingModels) |
| Legendary signature auras | `EffectsConfig.Signatures[<Id>]` (Flurries/FrostRing, SunRays/HeatShimmer/OrbitEmbers, Droplets/Bubbles/TealMist, BackSteam/ClawSparks/DrillRings, OrbitRocks/DustStorm/MeteorTrail, Embers/CurlingSmoke/EmberRing, LavaSparks/HeatHaze/GlowingSmoke, Twinkles/AuroraRibbon/MiniPlanets) | Concept sheet: `store-assets/buildings/Legendary_sheet.png` (`tools/blender/buildings/legendary_sheet.py`) | SYNC |
| Legendary ground ring (Neon segments, seen at any distance) | `EffectsConfig.LegendRing` {Attachment "Aura", Segments 24, PadShare 0.42, Width 0.6, Height 0.25, Lift 0.1}, in `BuildingColours` | none | SYNC |
| Performance and visibility rules | `EffectsConfig.Rules` {OtherPlotRate 0.5, OtherPlotDistance 60, MaxLightsPerBuilding 2, HitEffectsPerSecond 8, ReducedAmbient 0.5, ReducedHits false, HitIntervalSeconds {1.6, 0.6}, CheckSeconds 0.5}. `src/replicated/EffectsRules.luau`: `AmbientScale`, `HitsAllowed`, `TierFor`, `HitInterval`, `NewHitBucket`. | none | SYNC; SPECS `Effects` |
| Emitter placement and scale | `src/player/BuildingEffects.client.luau`: `makeEmitter` scales by the tier's `Grow`, `ORBIT_POINTS` 6, `attachmentCFrame` for stand-ins. The points are the template Root's attachments, from `BuildingModels`. | The attachment points in the building files (Work, Work2, Lamp1/2, Gear1/2, Steam1/2, Hit, Trail, NamePlate, Aura, Top, Crown) | Moving points: `python tools/make_building_models.py`, then TPL("<Id>"), then SAVE |
| Particle textures | `EffectsConfig.Textures` (generated), `EffectsConfig.Placeholder`, `TextureFiles`. White textures, tinted by the emitter. | `python tools/make_particle_textures.py` writes `assets/textures/particles/*.png` | UPLOAD-P `--manifest assets/textures/upload_manifest.json assets/textures/particles/<file>.png` (new ids), then IDS. No template rebuild: the client applies textures. |
| Build, evolve and upgrade moments | `src/player/BuildMoments.client.luau`: `RISE_SECONDS` 0.75, white Highlight flash, snow puffs, `Effects.Shake` (0.35 / 0.7 / 0.3), `Banners.Big("Your X evolved!")` in (255,230,140) | none | SYNC |

### Ice picks

| Visual | Controlled by | Source art | After a change |
|---|---|---|---|
| Pick models, 6 tiers, held in hand | `src/server/PickService.luau` clones `ServerStorage.PickTemplates.Pick<tier>`. `UpgradeConfig.PickModelIds` (generated), `UpgradeConfig.PickGrip`, `BuildingModels.Picks[n]` (Grip/Tip/Trail). | `tools/blender/tools_ice_picks.py` (`PICKS` table: handle/band/head swatches) writes `store-assets/tools/fbx/IcePick_T<n>.fbx`, `IcePicks_manifest.json` and `IcePicks_sheet.png` | 1. `blender -b --factory-startup --python tools/blender/tools_ice_picks.py`<br>2. `python tools/make_building_models.py`<br>3. UPLOAD-M `store-assets/tools/upload_manifest.json store-assets/tools/fbx/*.fbx`<br>4. IDS<br>5. TPL("Picks")<br>6. SAVE<br>Also re-render icons Pick1..6, Upgrades and FrostTouch, plus the AutoPick and ShatterNow store icons. |
| Golden pick skin (Creature Book Golden page) | `PickService.applySkin`: `GOLD` (255,200,60), Foil, TextureID cleared. Unlocked by `CreatureConfig.Book` Golden `PickSkin`. | none | SYNC |
| Tap sparks per tier | `src/replicated/IceLooks.luau` `PickSparks[1..6]`, used by `src/player/TapFeedback.luau` `chips` | none | SYNC |
| Swing on tap | `src/player/TapInput.client.luau` `swingPick` (Roblox's default Animate "toolanim") | none | SYNC |

### Ice block (client-drawn from `Workspace.Plots.PlotN.Block` attributes)

| Visual | Controlled by | Source art | After a change |
|---|---|---|---|
| Look per layer (6 layers) | `IceLooks.Layers[n]` {Color, Material, Transparency (frosty start), Clear (at crack stage 4), Extra, VeinColor}, drawn by `src/player/IceBlocks.luau` `update` / `makeExtras`. The extras: Bubbles = 14 glass balls; Veins = 8 Neon sticks; InnerLight = PointLight Brightness 2, Range 16; Crystal Ice Sparkles = emitter Rate 7 (3 reduced) with the built-in sparkles texture. Names and level ranges are in `LayerConfig.Layers`. `IceLookId` there is nil and unused. | none (parts made in code) | SYNC; SPECS `Pets` (every layer needs a look) |
| Block size | `BlockRules.Height(level)` from `LayerConfig.Block.HeightAtFirstLevel` 14 / `HeightAtLevel50` 20; `IceLooks.BlockWidthShare` 0.8 | none | SYNC |
| Rarity glow (PointLight + Neon aura ball) | `IceLooks.Glow` {Rare, Epic, Legendary Mode "Pulse", Mythic Mode "Rainbow"}: Color, Brightness, Range. `IceLooks.GlowBoostAtStage4` 1.8. Aura size (height x 0.55) and transparency are in `IceBlocks.update`. `CreatureConfig.Rarities[].Glow` strings are descriptive only; the spec requires a glow exactly where that string isn't "None". | none | SYNC; SPECS `Pets` |
| Creature silhouette inside | `IceBlocks.buildSilhouette`. `PetLooks.SilhouetteColor` (27,36,51), `PetLooks.Apply("Silhouette")`, `ShowEyes`. `IceLooks.SilhouetteShare` 0.6 is pinned by SPECS `Pets`. | The pet's voxel model (A5) | SYNC |
| Crack stages 0-4 | Thresholds: `LayerConfig.Block.CrackStages` {20,40,60,80,100}, read through `BlockRules.CrackStage`. Lines: `IceBlocks.makeCracks`, local `CRACKS_PER_STAGE` {6,9,10,12}, colour (240,252,255). Frost clears through `Transparency → Clear`. Stage 2: chunks fall and the HUD shows the rarity. Stage 3: eyes blink. Stage 4: wiggle, glow boost and heartbeat. | none | SYNC |
| Shatter (shards + crystal fountain) | `IceBlocks.shatter`: `IceLooks.Particles.Shards` 26, `.Fountain` 40. Crystal colour is the owner's `IceLooks.CrystalColours` (by ice-upgrade tiers 0/3/6: white, blue, gold). Built with `Effects.Debris`. | none | SYNC |
| Sled under an arriving block | `IceBlocks.makeView`: Deck in WoodPlanks (150,100,60), runners in Metal (205,215,230). `IceLooks.SledDistance` 46, `SledSeconds` 0.9. The gameplay wait is `LayerConfig.Block.ArriveSeconds` 4, minus Fast Sled. | none | SYNC |
| Building-hit shudder and crystal pops | `IceBlocks.update` (shake 0.08, 2 Neon crystals), `IceLooks.HitCrystalSeconds` 0.6 | none | SYNC |
| Mythic Block (Robux product) | Has **no look of its own**. `src/server/IceBlockService.luau` `rollBlock` rolls the next block from `MonetizationConfig` MythicBlock `Odds`, and it looks like any block of that layer and rarity. A toast says it arrived. | Store icon `store-assets/icons/MythicBlock.png` | n/a |
| Note | `IceLooks.Particles.Chips` / `.Sparkles` are unused: `TapFeedback.chips` hard-codes 4 chips, 2 crystals and 3 sparks. | | |

### Pets and creatures

| Visual | Controlled by | Source art | After a change |
|---|---|---|---|
| 18 voxel creatures (built at runtime, never uploaded) | `src/replicated/Pets/PetBuild.luau` builds from `src/replicated/Pets/Models/<Id>Data.luau`; animations come from `<Id>Clips.luau` (`PetAnimator.luau`: Idle, Hop, Cheer). `CreatureConfig.Creatures[].ModelId` is nil and unused. | `tools/pets/creatures/<Id>.py` on `tools/pets/voxel/studlib.py` + `post.py` (the lihfolk-stud-voxel rig). `SIZE` in `tools/pets/build_pet.py` sets 3 studs, or 3.6 for Legendary and Mythic. Outputs: `store-assets/creatures/<Id>/` (.blend, sheet.png, loop.gif, render/). Roster sheet: `tools/pets/roster_sheet.py` writes `store-assets/creatures/RosterSheet.png`. `tmp/pets` is scratch. | `python tools/pets/build_pet.py <Id>` (or `all`; `--quick` skips renders). It writes the two .luau modules, then SYNC. **No upload, no id, no template, no place save.** Then re-render the icons that show the creature (A12). |
| Normal / Golden / Silhouette looks | `src/replicated/Pets/PetLooks.luau` `Apply`:<br>Normal: palette colours, Plastic + studs, Neon glow keys.<br>Golden: `GoldColor` (255,197,49), shade 0.5 + 0.65 x luminance, Foil; eyes keep their colour.<br>Silhouette: one dark shade, no studs. | none | SYNC |
| Follow layout behind the owner | `src/player/PetFollow.client.luau`: `FOLLOW_DISTANCE` 6, `SPREAD` 34°, 4 per row (+3 studs per row), `MAX_DRAW_DISTANCE` 220. Hops on your taps, cheers on rescue. | none | SYNC |
| Pets in UI tiles | `src/player/PetViewport.luau` (ViewportFrame, Ambient (170,180,200)), used by the Pets and Book windows | none | SYNC |
| Aurora trail (Book Mythic page) | `src/server/RankService.luau` `auroraTrail`: Trail Lifetime 0.9, LightEmission 0.8, colours (120,255,200) → (110,170,255) → (220,130,255), attachments AuroraTop/AuroraBottom on the HumanoidRootPart | none | SYNC |

### Rescue moments, banners, popups, rushes

| Visual | Controlled by | Source art | After a change |
|---|---|---|---|
| Rescue reveal (owner only) | `src/player/RescueMoment.luau` `play`. A frost puff (10 snow bits). The creature starts at ice size, shrinks to pet size between 0.35 and 0.95 s, then runs to you at 26 studs/s until 3 s. Confetti: `IceLooks.Confetti` 36 in `IceLooks.RarityColors`, every 3rd piece white. | none | SYNC |
| Rescue, layer, rush and notice banners | `RescueMoment.Start` uses:<br>Rescue: `Banners.Big(name, rarity, 2.8 s)`.<br>New layer: `Banners.Big` in (150,225,255), `Effects.Shake(1.1,1.2)`, `Effects.Dip(1.6,1.4)`.<br>Server Frost Rush: banner in (140,230,255).<br>Notice: toast (200,240,255).<br>Announce: toast in the rarity colour.<br>The rarity colours are `IceLooks.RarityColors` (also the Book's colours). | none | SYNC; SPECS `Pets` (each rarity needs a colour) |
| Big banner / toast | `src/player/Banners.luau`: Screen "Banners" (order 30), Big at 0.34 screen height, 900x190, title 84, subtitle 40; `Toast` | none | SYNC |
| Beam over another plot's Legendary/Mythic block | `src/player/RareWatch.client.luau` `SETTINGS` {Height 90, Width 6, MaxSeconds 180}, colour `IceLooks.RarityColors` (Mythic shifts through the rainbow) | none | SYNC |
| Frost Rush / Server Frost Rush | **HUD text only** (A11 `FrostRush` label) plus banners and toasts. No world effect. The rush values live in `GameConfig.GoldenGlacier` (RushSeconds 60, x3, top tapper x5) and `MonetizationConfig` ServerFrostRush (x2, 900 s). | none | SYNC |
| Rebirth flash | `src/player/RebirthWindow.client.luau`: "RebirthFrost" screen (frost (225,245,255), tweens 0.6 / 1.2 s) and `Banners.Big` in (190,150,255). The HUD REBIRTH button turns gold (255,220,90) when ready. | none | SYNC |
| "While you were away" popup | `src/player/OfflineEarningsPopup.client.luau`: ShowcaseKit.Window 600x340, `COUNT_UP_SECONDS` 0.9. It asks for corner icon `Icons.OfflineEarnings`, which isn't in UITheme.Icons, so none shows. | none | SYNC |
| Shatter Now offer | `src/player/ShatterOffer.client.luau`: right edge (1,-14 / 0.62), 210x74. `BIG_FROM` "Rare" or rarer gives a bigger Gold pulsing button; otherwise it's Neutral. | none | SYNC |
| Tutorial arrow and bubble | `src/player/TutorialGuide.client.luau`: `STEPS` text, bubble (255,240,150) at y 170, Screen "Tutorial" (order 8) | none | SYNC |
| Guide line home and home marker | `src/player/PlotGuide.client.luau`: Beam (120,230,255) → (255,235,120) with the built-in sparkles texture; `MapConfig.HomeMarker` {Bottom 28, Height 55, Width 3.5} | none | SYNC |
| Update screen and server messages | `src/player/ServerNotices.client.luau` (`UITheme.Windows.Polar`, full-screen panel at order 1000) | none | SYNC |

### Name and rank tags

| Visual | Controlled by | Source art | After a change |
|---|---|---|---|
| Player name tag (built on the server) | `RankService.tag`: BillboardGui 7x1.9 studs, offset 2.6, MaxDistance 120; frame (10,20,36) at 45% transparency.<br>`NameLine`: VIP gold `VIP_GOLD` (255,210,80), plus the "Ice Keeper" title.<br>`RankLine`: `RebirthConfig.Ranks` titles in `RebirthConfig.ColourValues`.<br>Border: `BORDER_COLOURS` Frosty/Golden (Book Epic/Legendary pages). | none | SYNC |
| Rainbow rank line (rebirth 10) | `src/player/RankTags.client.luau` (hue cycle 0.2/s, saturation 0.6) | none | SYNC |
| Plot owner name on the gate boards | `PlotService.nameText` (SurfaceGui 40 px/stud, white, stroke (70,40,20)); placement in `MapConfig.Arch.Board` | The boards are meshes in PlotArch (A8) | SYNC |

### Plot, plaza, Golden Glacier, world

| Visual | Controlled by | Source art | After a change |
|---|---|---|---|
| Plot parts: ice stage, ice-block walls, gate with name boards | `PlotService` (`buildPlot`, `look`, `dress`, `hide`, `streamLook`) shows `ServerStorage.PlotTemplates.*` over invisible collision Parts. Greybox colours: `SNOW`, `SNOW_SHADE`, `PAD`, `SIGN`. Sizes: `MapConfig.Mound`, `.Border`, `.Arch`. Ids: `MapConfig.PlotModels`. | `tools/blender/plot_parts.py` writes `store-assets/plot/<Model>.fbx`, `plot_manifest.json` and `render/` | 1. `blender -b --factory-startup --python tools/blender/plot_parts.py -- render`<br>2. UPLOAD-M `store-assets/plot/upload_manifest.json store-assets/plot/*.fbx` (same ids; a NEW model's id goes into `MapConfig.PlotModels` by hand)<br>3. TPL("Plot")<br>4. SAVE |
| Rank-coloured trim on the plot | `RankService.border` colours meshes carrying the `RankColour` attribute: `DEFAULT_BORDER` (205,222,240), `RebirthConfig.ColourValues`, Rainbow = one hue per wall. `build_templates.luau` makes `...Trim` meshes untextured (`TRIM_COLOUR`). | Mesh names ending `Trim` in `plot_parts.py` | Colours: SYNC. Meshes: as the plot-parts row. |
| Footpath, drifts, ice patches in plots | `MapConfig.PlotGround`: the Footpath {Width 12, FromZ 16, Color} is a Part made by PlotService; Drifts and IcePatches are terrain made by build_world | none | Footpath: SYNC. Drifts/patches: WORLD, then SAVE. |
| Plaza: ground, paths, signs, leaderboards, chests, codes kiosk, golden landing ring, VIP lounge, welcome sign | `src/server/PlazaService.luau` `Start`.<br>Colours: `SNOW`, `PATH`. Text: `sign`, `floatingLabel`.<br>`board()`: SurfaceGui heading (255,220,90), rows at 38 px; `LeaderboardService` fills the rows.<br>`dressPart` puts the models on the invisible Parts. GoldenRing: Neon (255,210,80) at 0.6, at `PlazaService.GoldenSpot`.<br>VIP rails: gold (255,205,80), floor (80,50,120). `src/player/VipLounge.client.luau` only toggles the door.<br>Ids: `MapConfig.PlazaModels`. | `tools/blender/plaza_boards.py` (LeaderboardBoard) and `tools/blender/plaza_props.py` (DailyChestStand, CodesKiosk) write `store-assets/plaza/*.fbx` and `render/` | Models:<br>1. Run the Blender script<br>2. UPLOAD-M `store-assets/plaza/upload_manifest.json store-assets/plaza/*.fbx`<br>3. A new model's id goes into `MapConfig.PlazaModels` by hand<br>4. TPL("Plaza")<br>5. SAVE<br>Code edits: SYNC. |
| Golden Glacier (falls into the plaza) | `src/player/GoldenGlacier.client.luau`: `SIZE` 11x13x11, `RIM` 0.55, `GOLD_GLASS` (235,135,0), `GOLD_RIM` (255,196,60), `GEM` (255,196,45), `CRACK` (255,250,225), `CRACKS_PER_STAGE`. The "TAP IT!" readout moves to the HUD within Radius+6. Timings and HP are in `GameConfig.GoldenGlacier`; the server side is `src/server/GoldenGlacierService.luau`. | none | SYNC |
| Terrain, ponds, hills, mountains | `tools/studio/build_world.luau`: terrain material colours (Snow (232,240,250), Ice, Glacier), `GROUND_HALF` 900, `CLEAR_RADIUS` 255, `SEED` | none | WORLD, then SAVE |
| Snowy pines | `build_world.luau` `PINES` id (hard-coded 138595808045459) and `LOOKS` {Trunk, Needles, Snow} colours | `tools/blender/scenery_pines.py` writes `store-assets/scenery/Pines.fbx` | 1. Blender script<br>2. UPLOAD-M `store-assets/scenery/upload_manifest.json store-assets/scenery/Pines.fbx` (same id)<br>3. WORLD<br>4. SAVE |
| Sky | `build_world.luau` `SKY` table (6 ids, hard-coded) | `python tools/make_skybox.py` (`ZENITH`, `MIDDLE`, `HORIZON`, clouds) writes `assets/textures/sky/Sky*.png` | 1. UPLOAD-P `assets/textures/sky/Sky*.png` (new ids; manifest `assets/textures/sky/upload_manifest.json`)<br>2. Paste the ids into `SKY`<br>3. WORLD<br>4. SAVE |
| Lighting | `tools/studio/lighting.luau` (ClockTime 14.8, Brightness 2.6, ambients, Atmosphere, Bloom, ColorCorrection). `Lighting.Technology = Future` is set by hand; MCP can't read or set it. | none | Run in Edit, then SAVE |
| Thumbnails | `store-assets/launch/thumb_*.png`; camera spots in `tools/studio/thumbnail_cameras.luau` | | Upload by hand on the Creator Hub |

### UI theme and kit (every screen is built from these)

| Visual | Controlled by | After a change |
|---|---|---|
| All UI tokens | `src/replicated/UITheme.luau`:<br>`Font` (FredokaOne; the spec pins it).<br>`Colors` (Outline, Text, Muted, Gold, Error, Good, Accent, Card, Well, ...).<br>`Windows` (Ice, Polar, Showcase).<br>`Buttons` (Go, Buy, Done, Locked, Neutral, Gift, Gold, Close, Frost).<br>`CardPalettes` (Ice, Glacier, Aurora, Green, Teal, Blue, Purple, Pink, Gold, Orange, Crimson, Slate, Locked).<br>`Progress`, `Assets` (checker, Robux), `Icons`, `Sheets`, `ShopIcons`.<br>`Showcase` (TitleSize 92, CornerIcon 170, CloseSize 78, ...), `Sizes`, `Scale` (Baseline 1050x620, Min 0.52, Max 1.18, Menu 0.95, MenuFloor 0.75, Hud 0.75), `Motion`, `Blur`, `WindowTransparency`. | SYNC; SPECS `UITheme`. The spec enforces:<br>• Window tops stay "cool" (B ≥ R).<br>• Go/Buy/Done/Neutral/Frost button faces stay cool (B ≥ R or G ≥ R).<br>• Contrast minimums (text on Card/Well/Showcase, Gold/Error on Well, CaptionOutline on every button).<br>• `ShopIcons` and `Sheets.Groups` stay empty.<br>• UITheme/UIKit/ShowcaseKit/Audio/AudioConfig/NumberFormat/HUD use no image ids except `Assets` and `Icons`.<br>A restyle that breaks these needs the spec updated in the same change. |
| Building blocks | `src/replicated/UIKit.luau`: Label, Card, Button/SetButton, CloseButton, HudButton, Tabs, ProgressBar, Slider, TextBox, Icon/IconImage, Screen, Window (options: theme, width, height, cornerIcon...), MenuScale/HudScale, Viewport, SelectionRim (gamepad gold rim) | SYNC |
| Showcase pieces | `src/replicated/ShowcaseKit.luau`: Window (defaults to theme "Showcase"), Panel, SectionHeader, Card/SetCardPalette, CardPicture, CardTitle, CardText, BuyButton, InfoButton, Sticker, SheetPicture, HudButton | SYNC |
| Debug / admin windows | `src/player/ActionMenu.luau`: a plain tool look **on purpose**; don't restyle | n/a |

### Screens

| Window | Script | Look specifics |
|---|---|---|
| Build | `src/player/BuildWindow.client.luau` | ShowcaseKit.Window. Card palettes: Locked (hidden "???"), Gold (best affordable), Blue (owned), Slate; flashes Ice. Icon `UIKit.IconImage("Building_<Id>")`. |
| Upgrades | `src/player/UpgradesWindow.client.luau` | Kinds: IcePick Teal ⛏️, FrostTouch Aurora ❄️, Building Orange 🏗️, Ice Purple 💎; Locked when unaffordable. Icons: Pick<n>, FrostTouch, Building_<Id> + UpgradeBadge, BiggerBurst/CrystalYield/FastSled. |
| Pets | `src/player/PetsWindow.client.luau` | Cards Gold (Golden pet) / Slate; bonus text in the rarity colour; "GOLDEN (5)" button Gold/Done; PetViewport |
| Creature Book | `src/player/BookWindow.client.luau` | Cards Gold (golden) / Blue (found) / Locked; PetViewport in Silhouette until rescued; rarity colours |
| Rebirth | `src/player/RebirthWindow.client.luau` | Plus the frost flash (A6) |
| Shop | `src/player/ShopWindow.client.luau` | `PASS_PALETTE` Purple, `PRODUCT_PALETTE` Blue, BuyButton, InfoButton (paid random odds). Card picture comes from the item's `Icon` field in `MonetizationConfig`; **none is set**, so the cards are text only. `UITheme.ShopIcons` is not read by any code. |
| Codes | `src/player/CodesWindow.client.luau` | Corner icon `UITheme.Icons.Codes` (the only window with a corner icon) |
| Settings | `src/player/SettingsWindow.client.luau` | Volume sliders; "Reduced effects" and "Auto equip" toggle buttons (Go = on, Done = off) |
| Offline earnings popup | A6 | |

### HUD and tap feedback

| Visual | Controlled by | After a change |
|---|---|---|
| Menu buttons | `src/player/HUD.client.luau` `MENU` {Name, Icon, Text, Palette}: Build Orange, Upgrades Green, Pets Pink, Book Teal, Rebirth Purple, Home Ice, Shop Glacier, Codes Slate. `BUTTON` 104, `GAP` 14, `TOP_ROOM` 20, `COLUMNS` 2. Left edge on desktop; top left on touch and pretend phone screens. | SYNC |
| Crystal counter block (top centre, 420x230, hidden while a window is open) | `HUD.client`: Crystals label (56, "💎"), Rate (30, `Colors.Gold`), Badge (24, `Colors.Muted`; rarity in `RarityColors` from crack stage 2), IceBar (`UIKit.ProgressBar` 340x28, only in your own plot), FrostRush label (28, (140,230,255)), RebirthGoal ((205,160,255); when ready it pulses gold ↔ purple). Settings gear: `UIKit.Button(..., "Frost")`. Scale: `UIKit.HudScale()`. | SYNC |
| "+N" float on tap | `TapFeedback.Float`: `UITheme.Font`, (190,240,255), 160x44, rises 90 px in 0.7 s | SYNC |
| Ice chips, crystal spray, sparks on tap | `TapFeedback.chips` (4 chips in the block colour, 2 Neon crystals in `IceLooks.CrystalColour`, 3 sparks in `PickSparks`) through `src/player/Effects.luau` `Debris` | SYNC |

### Icons and pictures

| Visual | Controlled by | Source art | After a change |
|---|---|---|---|
| In-game UI icons (HUD menu, Build/Upgrades tiles, pick tiers, UpgradeBadge) | `UITheme.Icons` | `tools/icons/render_icons.py` (headless Blender, `ui` mode: creature .blends, tier-1 station .blends, picks, props) and `tools/icons/compose_icons.py --ui` (`UI_SPECS`, `CARDS`, `PICK_TIERS`) write `store-assets/ui-icons/<Key>.png` and `contact_sheet.png` | 1. `python tools/icons/compose_icons.py --ui --render <Key...>`<br>2. UPLOAD-P `store-assets/ui-icons/<Key>.png` (new id)<br>3. Paste into `UITheme.Icons.<Key>`<br>4. SPECS `UITheme` |
| Robux item icons (Creator Hub pages, not shown in game) | Roblox's pass and product pages | `compose_icons.py` (no `--ui`) writes `store-assets/icons/<Key>.png` and `contact_sheet.png`. Game icon concepts: `store-assets/launch/icon_concept_<n>.png`. | Re-render. `tools/create_products.py` attaches an icon only when it **creates** an item (it matches existing items by name), so a changed icon for an existing pass or product must be replaced by hand on the Creator Hub. |
| Which icons show which creature (re-render after a pet change) | UI: Pets = Snow Bunny, Book = Penguin Chick.<br>Store: VIP = Snow Bunny, ExtraPetSlot = Arctic Fox Kit, PetSquad = Polar Bear Cub + Penguin Chick + Puffin Pal, LuckyIce = Frost Dragon Hatchling, ShatterNow = Mini Yeti, ServerFrostRush = Penguin Chick + Ice Wolf Pup + Seal Pup, MythicBlock = Spirit Whale.<br>From `store-assets/icons/README.md` and `store-assets/ui-icons/README.md`. | | |

### Audio-visual feedback

| Visual | Controlled by | Source | After a change |
|---|---|---|---|
| Sounds tied to visuals (Tap, Crack1-4, Shatter, Heartbeat, Rescue<Rarity>, BuildingChip, BookNew, BookReveal, NewLayer, GoldenAlarm, GoldenCrash, GoldenSparkle, Rebirth, Buy*, UI Click/Open/Close...) | `src/replicated/AudioConfig.luau` (`Files`, `Ui`, `Sfx`, `Rules`, `Music` with empty Plaza/Plot ids), `src/replicated/SoundRules.luau`, `src/replicated/Audio.luau`, `src/player/GameSounds.client.luau`, `src/player/MusicPlayer.client.luau` | `python tools/make_sfx.py` writes `store-assets/audio/<Name>.ogg` (`sources.json`) | 1. Re-run<br>2. UPLOAD-P `store-assets/audio/<Name>.ogg` (new id)<br>3. Paste into `AudioConfig.Files`<br>4. SPECS `SoundRules UITheme` |
| Camera shake and dip | `Effects.Shake` / `Effects.Dip` (skipped with reduced effects). Callers: IceBlocks (crack: 0.35, 0.25), RescueMoment (new layer), BuildMoments. | | SYNC |

### Reduced effects (Settings)

`Effects.Reduced()` reads the saved `Settings.ReducedEffects` (through `ClientState`). When it's on:
- `Effects.Count(n)` halves particle and debris counts (minimum 1).
- `Shake` and `Dip` are skipped.
- BuildingEffects: ambient rate x `Rules.ReducedAmbient` 0.5, and no hit bursts (`EffectsRules.HitsAllowed`).
- Crystal Ice sparkles drop from 7 to 3.

## The debug menu (F2) for visual checks

Open it with **F2** or the purple **DEBUG** button on the right edge. Everyone can use it in Studio. Pick the target player at the top. The table is `ACTIONS` in `src/server/DebugActions.luau`, in menu order. "Studio" means the action refuses outside Studio. "No target" means the action ignores the picked player.

| Id | Group | Label | Params (name: kind, range or choices, default) | Flags |
|---|---|---|---|---|
| SaveNow | Save | Force a save now | none | |
| AddCrystals | Save | Add crystals (this run and all time too) | Amount: int 1–1e15, 1000 | |
| SetCrystals | Save | Set crystals to an amount (spendable only) | Amount: int 0–1e15, 5,000,000 | |
| SetBlockLevel | Save | Set block level (the next block rolls again) | Level: int 1–1000, 21 | |
| SetBuilding | Save | Set one building's count and upgrades (tiers, Masterwork: visual checks) | Building: the 8 buildings; Count: int 0–1000, 100 (tiers at 1, 10, 25, 50, 100); Upgrades: int 0–5, 0 (5 at 100 owned = Masterwork) | Redraws the plot at once |
| SetPickTier | Save | Set ice pick tier (owns exactly the picks up to it) | Tier: int 1–6, 6 | |
| ForceRescue | Ice block | Force a rescue (break the current block now) | none | Fails while the sled is bringing the block |
| PickCreature | Ice block | Pick the creature inside (a new block rolls with it now) | Creature: choice of the 18 creatures ("Snow Bunny (Common)" ...), default Snow Bunny | |
| GivePet | Ice block | Give a pet | Creature: 18 choices, Snow Bunny; Golden: On/Off, Off | Also marks BookSeen (and BookGolden when Golden) |
| SetBlockHp | Ice block | Set the current block's HP left (crack stages: visual checks) | Percent: int 1–100, 50 | Fails while the sled is bringing the block |
| SpawnGolden | Ice block | Drop a Golden Glacier in the plaza now | none | No target; fails if one is already falling or standing |
| AddFrostCores | Ice block | Add Frost Cores | Amount: int 1–1000, 5 | |
| SetRebirths | Ice block | Set rebirths (rank, slots, layers) | Rebirths: int 0–100, 3 | Raises MaxLayerOpened |
| PlaySound | Sound | Play a sound (on their client, full volume) | Sound: every `AudioConfig.Sfx` and `.Ui` key, sorted | |
| FillDummyPlots | Testing switches | Fill every empty plot with a maxed dummy plot (performance tests) | Creature: 18 choices (sets the dummies' block creature and rarity) | No target, Studio |
| ClearDummyPlots | Testing switches | Free the dummy plots again | none | No target, Studio |
| SendHome | Player | Send to their plot | none | |
| ShowSave | Save | Show the save (all of it goes to Output) | none | |
| ResetSave | Save | Reset to a fresh save (keeps Robux receipts) | none | Confirm. Also refreshes stations, rerolls the block and republishes pets. Keeps Receipts, PendingGifts, ReceivedGifts, GiftedPasses, MythicBlocks. |
| OfflineEarningsNow | Progress | Offline earnings now (as if away N seconds) | Seconds: int 1–2,592,000, 600 | |
| AnalyticsProgress | Progress | Analytics funnels: how far they are logged | none | |
| DailyChestYesterday | Progress | Daily chest: last opened yesterday (it can be opened again) | none | |
| PreviewUpdateScreen | Progress | Soft shutdown: show everyone the update screen for 10 s | none | Ignores the target |
| PreviewRestartWarning | Progress | Soft shutdown: the 'update coming' warning (as if in 5 min) | none | Ignores the target |
| AnalyticsFlush | Progress | Analytics: send the target's batched crystal events now | none | |
| AnalyticsRestart | Progress | Analytics funnels: start again (log every step afresh) | none | |
| ResetCodes | Codes | Reset redeemed codes (every code works again) | none | |
| GivePass | Robux | Give a game pass (Studio, this session) | Pass: DoubleCrystals, AutoPick, VIP, ExtraPetSlot, PetSquad, LuckyIce; default 2x Crystals | Studio; a Studio override that wins over real ownership |
| RemovePass | Robux | Remove a game pass (Studio, this session) | Pass: as above | Studio; also hides passes the developer account owns |
| SimulateReceipt | Robux | Simulate a receipt (the target is the buyer) | Product: CrystalPouch, CrystalSack, CrystalChest, ShatterNow, ServerFrostRush, MythicBlock, plus "<pass> pass, as a gift" for each pass; default Crystal Pouch. GiftTo: int user id −1e12–1e12, 0 = for themselves (test players are −1, −2...). | Studio |
| RobuxPerks | Robux | Show the target's Robux perks and every crystal multiplier | none | |
| DuplicateReceipt | Robux | Simulate a duplicate receipt (the same PurchaseId again) | PurchaseId: text ≤64, `^[%w%-]*$`, optional (blank = the last one); Product: as above; Gift: On/Off, Off | Studio |
| FreshSave | Testing switches | Fresh save: the next join plays as a brand-new player (throwaway record) | State: On/Off, On | No target, Studio; sets the Workspace attribute `StudioFreshSave` |
| UseLiveSaves | Testing switches | Use LIVE saves on the next join (only on purpose!) | State: On/Off, Off | No target, Confirm, Studio. **Don't use it for visual checks.** |
| FakeTimeAway | Testing switches | Fake time away on the next join (seconds, 0 = off) | Seconds: int 0–2,592,000, 3600 | No target, Studio; sets `StudioTimeAway` |
| PaidRandomRestricted | Testing switches | Paid random items restricted (region) | State: On/Off, On | No target, Studio |
| TeleportToPlayer | Player | Teleport the target next to another player | To: int user id, −1 | |
| SetWalkSpeed | Player | Set walk speed (until respawn) | Speed: int 1–200, 16 | |
| Respawn | Player | Respawn | none | |

Not in F2: buying pick or ice upgrades (use the Upgrades window after SetCrystals), starting a Frost Rush directly (break a Golden Glacier), toggling reduced effects (the Settings window) and the screen size (the client's `StudioScreenSize` attribute). Buildings at any count and upgrade level: **SetBuilding**. Crack stages: **SetBlockHp** (100, 79, 59, 39, 19 % for stages 0-4).

### Recipes

Layer by block level:

| Levels | Layer |
|---|---|
| 1–10 | Fresh Snow |
| 11–20 | Blue Ice |
| 21–30 | Ancient Ice |
| 31–40 | Crystal Ice |
| 41–50 | Primordial Ice |
| 51–60 | Frozen Core (needs rebirths ≥ 3) |

Past an opened layer's range, the block stays in the deepest layer opened (`LayerConfig.LayerForLevel`).

**A given layer and rarity in your own block.**
1. For Frozen Core only, run `SetRebirths` 3 first. That opens layer 6.
2. Run `SetBlockLevel` with a level in the layer.
3. Run `PickCreature` with the creature you want. It rerolls at once, the rarity follows the creature, and any creature works on any layer.

A layer change also plays the "Layer N" banner with the shake and dip.

**Crack stages.** `SetBlockHp` with 100, 79, 59, 39 and 19 (% of HP left) shows stages 0 to 4. A stage starts at each 20% of damage. Do it while the block is on the mound, not on its sled.

**Buildings at a given tier or count.** `SetBuilding` sets one building's count and upgrades at once:
- Counts 1, 10, 25, 50 and 100 give tiers 1-5.
- Upgrades 0-5 show the parts U1-U5.
- 100 with 5 upgrades is Masterwork.
- Count 0 removes it.

Every building below your highest-ordered owned building is drawn faded (60%, no ambient FX). Order: IcePickPost < HeatLamp < ChiselMill < IceDrill < WreckingCrane < FlamethrowerTurret < LavaPump < SunMirrorTower. A faded Ice Pick Post turns into the fence ring. To judge one building at full size, own nothing above it.

Upgrade parts, stars and Masterwork: `SetBuilding`'s Upgrades input (or the Upgrades window). Masterwork needs all 5 tiers plus all 5 upgrades.

Before owning a lot of DPS, run `SetBlockLevel` 400 (the AGENTS.md tip), or blocks shatter the tick they arrive.

**A maxed plot.**
- Your own: run `SetBlockLevel` 400, then `SetBuilding` each of the 8 buildings to 100 with 5 upgrades.
- Others: `FillDummyPlots` (Studio) fills every **empty** plot with a dummy. Each dummy has 100 of every building and all upgrades (all Masterworks, so only Sun Mirror Tower shows unfaded) and a block at level 400, Layer 5, crack stage 2, holding the chosen creature. Use it for glow and silhouette comparisons. `ClearDummyPlots` frees them.
- With streaming on, move the character near a plot before judging a far view.

**Golden Glacier now.** Run `SpawnGolden`.
1. A 10 s countdown runs while the block hangs over the plaza.
2. It lands at `PlazaService.GoldenSpot` (0, 0, −34).
3. Tap within 40 studs. It takes 100 taps per player in the server and melts after 60 s.

**Frost Rush (the player's own).** There's no direct action: break the Golden Glacier (`SpawnGolden`, then about 100 taps solo; Auto Pick doesn't count). Solo, you are the top tapper, so you get x5 for 60 s. It shows only as the HUD's "❄ FROST RUSH" line plus toasts.

**Server Frost Rush.** Run `SimulateReceipt` with Product "Server Frost Rush" and GiftTo 0.
- You get the "SERVER FROST RUSH!" banner and the HUD "❄ SERVER RUSH x2 15:00" line.
- Running it again shows the "added 15 minutes" banner.

**Other Robux visuals.**
- `SimulateReceipt` "Shatter Now" breaks the block with a full rescue moment.
- `SimulateReceipt` "Mythic Block" changes the *next* block: `ForceRescue` the current one, then wait for the sled. A `PickCreature` override takes precedence over it.
- `GivePass` VIP gives the gold name tag and opens the lounge door. The developer account owns every pass, so use `RemovePass` to see the plain look.
- The Shatter Now offer button turns big and gold when `PickCreature` puts a Rare or better creature inside.

**Rescue moment per rarity.** Run `PickCreature`, then `ForceRescue`. The banner and confetti are in the rarity colour. A first rescue adds "NEW!" and the book opens on its page. Use `ResetSave` to see "first" again.

**Golden pets.**
1. `GivePet` with Golden On.
2. Equip it in the Pets window (EQUIP or Equip Best). Auto-equip only acts after a rescue.

Golden pets show gold cards in the Pets and Book windows and follow you in gold.

To fill the follow arc: `SetRebirths` 10 (4 slots), then `GivePass` ExtraPetSlot (+1) and PetSquad (+2) for 7 slots. Then `GivePet` x7 and Equip Best.

**Aurora trail.** `GivePet` Aurora Fox and Spirit Whale (Golden is not needed). That completes the Book's Mythic page, and the trail appears at once (GivePet triggers `RankService.Refresh`).

**Golden pick, Ice Keeper title, tag borders.** `GivePet` with Golden On for all 18 creatures (18 runs; the inventory holds 50). PickService swaps in the gold pick within 1 s. The same pages also give the Frosty and Golden tag borders and the "Ice Keeper" title.

**Rebirth ranks.** `SetRebirths` N:
- 1: Ice Breaker, light blue
- 2: Teal
- 3: Purple, and opens Frozen Core
- 6: Gold
- 10: Rainbow

Then run `Respawn`: the name tag and plot trim change only after a respawn or a rescue.

The rebirth moment itself (white frost flash and banner) needs a real rebirth: `SetBlockLevel` 31, then press REBIRTH in the Rebirth window. That resets crystals, buildings and upgrades.

**Ice pick tiers and spark colours.** `SetPickTier` 1–6.

**Crystal colours (white, blue, gold).** Buy ice-upgrade tiers (Bigger Burst, Crystal Yield, Fast Sled) in the Upgrades window after `SetCrystals`. 3 tiers turn them blue, 6 gold. There is no F2 action for this.

**Offline earnings popup.** Own at least one building first: offline pay is building income only, 50%, capped at 3600 s of income, and the popup shows only when the amount is above 0. Then either:
- run `OfflineEarningsNow` (Seconds, for example 600), which pays now and shows the popup; or
- set `StudioTimeAway` on Workspace in **Edit** mode (or `FakeTimeAway`), then Play.

**Tutorial from the start.** Either:
- run `ResetSave` (it asks to confirm) to go back to step 1, with the arrow over the ice; or
- for a brand-new player, set the Workspace attribute `StudioFreshSave` = true in **Edit** mode, then Play.

The `FreshSave` action only affects the *next join*, and a single-client test has none before Stop. Remove the attribute before saving the place.

**Phone screen sizes.** Not in F2. During Play, set the Workspace attribute `StudioScreenSize` = `Vector2.new(844, 390)` **on the client** (the client's command bar or execute_luau on the client instance). The UI lays out at that size in the top-left corner, with a red edge and the touch layout. Remove it after. `StudioGamepad` = true (also on the client) makes the UI act as if a gamepad is in use.

**Reduced effects.** Not in F2.
1. Open Settings with the gear (`PlayerGui.HUD.Root.SettingsButton`).
2. Toggle "Reduced effects" (the `ReducedEffects` button).

The setting is saved in the player's (Studio) save, so turn it off again afterwards.

**Rare beam over another plot and announce toasts.** This needs 2 players: from Edit, run `StudioTestService:ExecuteMultiplayerTestAsync(2, {})`.
1. In F2, pick Player2 (user id −2) as the target and run `PickCreature` with a Legendary or Mythic creature.
2. Player1 sees the beam over Player2's plot and the toast.
3. `ForceRescue` on Player2 clears the beam with a "freed" toast.

**Soft-shutdown screens.** `PreviewUpdateScreen` shows the update screen for 10 s; `PreviewRestartWarning` shows the warning message.

**Screenshot balance.** `SetCrystals` changes the spendable crystals only; the run and all-time totals stay.

### Not checked when this map was written

- The templates are all in place: the 2026-11-26 screenshots show every building tier, pick, plot part and plaza prop as its real model, with no greybox stand-ins.
- Whether `Lighting.Technology` is Future. No tool can read it.
- Exact control paths inside the Settings window, beyond the `ReducedEffects` button name.
