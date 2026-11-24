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

## Milestone 2: gameplay Days 1 and 2 (greybox) (done)

**Done:**
- **Plot:** the ice block on its mound, the pads at the doc's positions, border, owner sign.
- **Ice block:** HP from `LayerConfig.BlockHp`, the creature rolled when the block spawns and saved
  with its HP (a rejoin finds the same block), layers by level, the rescue at 0 HP and the sled.
- **Taps:** 0.25 s batches; the server caps them at 20/s (a bucket holding 1 s of taps) and logs
  players who keep going over.
- **Crystals:** crystals per damage times the multiplier, a 4-per-second server tick, offline
  earnings (building income at 50%, capped at 2 hours).
- **Buying:** buildings x1/x10/x100/Max on the 1.15 curve; every upgrade with its unlock rule (ice
  pick tiers, Frost Touch, building upgrades, ice upgrades).
- **UI:** HUD crystals and crystals/s (counting smoothly), the overhead HP bar with crack % and
  level, and the Build and Upgrades panels built from UIKit/ShowcaseKit.
- **Playtests:**
  - A NEW player: level 1 with 100 HP, the first Ice Pick Post at 0.8 s, the first rescue at 5.2 s.
  - Tap batches, buying and the unlock rules ("Buy the Iron pick first").
  - A forced Mini Yeti rescue: pet, Book, New! badge and the next block after the sled ride.
  - A rejoin restored the same block (creature and HP), the level, the pets, the buildings and the
    upgrades.

**Economy simulation** (`python tools/economy_sim.py`; real configs and rules, a greedy buyer,
fixed-seed pet rolls; the tutorial's Ice Pick Post bought first):

| Taps/s | First building | First rescue | Rebirth unlocked (level 21) | 1 / 3 / 5 Frost Cores | Rescue pace L1-10 / 11-20 / 21-30 / 31-40 |
| --- | --- | --- | --- | --- | --- |
| 2 | 0:07 | 0:48 | 17:11 | 17:11 / 29:34 / 39:06 | 0.6 / 1.0 / 2.3 / 5.6 min |
| 4 | 0:03 | 0:24 | 13:56 | 13:56 / 25:50 / 35:10 | 0.4 / 1.0 / 2.2 / 5.4 min |
| 7 | 0:02 | 0:14 | 11:35 | 11:35 / 22:45 / 31:46 | 0.3 / 0.8 / 2.1 / 5.0 min |
| 20 (cap) | 0:00 | 0:05 | 7:14 | 7:14 / 15:39 / 22:44 | 0.2 / 0.6 / 1.7 / 3.8 min |

- Targets met: the first building (30 s) and the first rescue (60 s), at every tap rate.
- **Target missed: the first rebirth.** Level 21 comes at 12-17 minutes, not 45-60. I didn't change
  any config (the specs tie the configs to the doc). What-if runs at 4 taps/s:

| Block HP growth | Rebirth unlocked | 5 cores | Rescue pace L11-20 / L21-30 |
| --- | --- | --- | --- |
| 1.5 (doc) | 13:56 | 35:10 | 1.0 / 2.2 min |
| 1.6 | 19:19 | 40:20 | 1.4 / 4.1 min |
| 1.65 | 22:51 | 43:21 | 1.7 / 5.5 min |
| 1.7 | 26:36 | 44:56 | 2.0 / 7.5 min |

  **Proposal** (yours to choose; each needs a doc change):
  1. **Keep HP growth at 1.5 and move the rebirth requirement to Layer 4 (level 31).** Level 31 comes
     at about 31-39 min for 2-7 taps/s (35 min at 4/s), and the rescue pace stays inside 1-3 min up to
     level 30. This is the smallest change that gets close to the target.
  2. **Or keep level 21 and make the first rebirth worth waiting for.** For example, require 5 Frost
     Cores' worth of crystals (125M this run) before the button lights; that lands at 31-39 min.
  3. Raising HP growth alone doesn't work: 1.65+ pushes rescues in Layer 3 to 5+ minutes, past the
     doc's 1-3 minutes.
  4. Separately: past level 30, rescues take 4-6 minutes with any setting. Later layers may need a
     gentler HP curve (for example 1.45 from Layer 4), or stronger late buildings.

## Milestone 3: the ice look, pets and the Creature Book (done, with gaps below)

**Done:**
- **The ice block** (`src/player/IceBlocks.luau`, look tuning in `src/replicated/IceLooks.luau`):
  - The creature's own voxel model sits inside in the Silhouette look, at 60% of the block's height.
  - The rarity glow shows from the moment the block arrives. A light and a soft aura: Rare soft blue,
    Epic purple, Legendary pulsing gold, Mythic cycling through the rainbow.
  - The five crack stages:
    - 20%: hairline cracks.
    - 40%: chunks fall off and the overhead shows the rarity.
    - 60%: the eyes show and blink.
    - 80%: the creature wiggles, the glow brightens and a heartbeat plays.
    - The frost thins at every stage.
  - Per hit: the block shudders and "+N" floats up. Building hits make a small shudder.
  - The rescue moment:
    - The block shatters into shards with a crystal fountain (everyone sees it).
    - The owner gets the rarity banner (+ "NEW!" and the fountain's crystals).
    - The creature shakes off the frost, shrinks from its size in the ice to pet size and runs to you.
    - The next block slides in on its sled.
  - Ice for the six layers:
    - Fresh Snow: snow.
    - Blue Ice: clear pale blue.
    - Ancient Ice: deep blue with bubbles.
    - Crystal Ice: sparkles.
    - Primordial Ice: dark teal with glowing veins.
    - Frozen Core: black ice with an inner light.
  - The new-layer moment: a banner ("Layer 2: Blue Ice / Rarer creatures ahead") and a ground shake,
    and the next block comes in the new ice.
  - Legendary and Mythic blocks are announced to the whole server.
- **Pets** (`PetService`, `PetRules`, `PetFollow.client`, `PetsWindow.client`):
  - The inventory (50) and equipping.
  - Slots: 1, then rebirth 3, 6 and 10. Plus the Extra Pet Slot and Pet Squad passes, read from
    `MonetizationConfig` with no ids yet; in Studio, give them from the debug menu.
  - Locked slots show "Rebirth 3" or the pass name and price.
  - Equip Best, delete (asks "SURE?"), combine 5 into Golden (the new pet takes the equipped slot),
    and the crystal bonuses.
  - Equipped pets follow their owner for every client, playing Idle and Hop, a hop when you tap and a
    cheer on a rescue.
- **The Creature Book** (`BookWindow.client`):
  - Pages for each rarity, plus the Golden page.
  - Silhouettes with "Found in Ancient Ice or deeper" until found, rescue counts and "New!" badges
    until viewed.
  - Each page's reward and whether it's earned, and the completion % (also on the HUD's BOOK button).
  - On a first rescue the book flies open on that page and the silhouette fills in with colour.
- **Playtested:**
  - A Mythic block from level 2 up: cracks, eyes, glow and rarity label at the right stages; the
    banner; the book opening.
  - Equip Best, the slot limit, the Golden combine, Pet Squad's slots, the followers.
  - A rejoin keeps the pets, the Golden pet, the Golden page and the New! badges.
- **Specs:** `tests/Pets.spec.luau` (new, 49 checks); all 16 specs pass (2,640 checks).

**Not done or simplified:**
- **No sounds.** `AudioConfig` is still empty, so the crunch, crack, heartbeat, shatter, jingle and
  new-layer sounds are silent. The code already calls them by name (`Crack`, `Heartbeat`,
  `Shatter`, `RescueJingle`, `BigFanfare`, `NewLayer`, `BookReveal`): add ids to `AudioConfig` and
  they play. The crunch pitch rising during fast tapping needs a pitch parameter in `Audio` too.
- **No pick swing.** There is no ice pick model yet (it's art), and the pick's spark colours depend
  on it.
- **The camera "dip" on a new layer** is a shake for now.
- **No 3D previews on the Build cards** (they wait for the building models).
