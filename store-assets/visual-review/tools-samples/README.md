# Tools, part 1: the tier table and five sample tools

(The part 1 record. Part 2 retuned the table for the 10-taps-a-second cap and the slower Auto Pick: every tool now
unlocks at a block level too. The current numbers are in docs/GAME_DESIGN.md, "Tools", and
docs/economy_sim_2026-11-27.txt; all 18 tools are in store-assets/visual-review/tools/.)

One sample of each family, made at the new size, with its swing and hit effects: Iron Pick (Pick), Gold Hammer
(Hammer), Crystal Axe (Axe), Ice Drill (Spear family) and Diamond Sword (Sword). The other 13 tiers already work
in game and hold the nearest sample of their family until their own model is made in part 2.

## The pictures

| Picture | What it shows |
| --- | --- |
| `all_five_samples_blender.jpg` | The five samples next to the 3-stud pet and the 5.5-stud avatar |
| `T..._vs_old_iron_pick.jpg` | Each sample at the wind-up and the strike, next to the old Iron Pick in the same moment, from the side at the tap spot |
| `T..._swings.jpg` | Every variant of the family's swing, wind-up and strike, from the front |
| `T..._avatar_sizes.jpg` | The wind-up and the strike on the smallest avatar (90% height, 70% width), the default one, and the largest (105%, full Rthro body type) |
| `all_strike_play_camera.jpg` | Each sample's strike from the play camera, as a player sees it |
| `T07_gold_hammer_impact_vs_pick.jpg` | The chip burst of a real click: the Iron Pick and the Gold Hammer |
| `T10_diamond_sword_trail.jpg` | The sword's slash trail. Its lifetime was stretched for this still: in play it is a quick 0.16 s streak. |

## The tiers

From the economy simulation: `python tools/economy_sim.py`, three seeds at 4 taps a second, eight to ten runs each.
The full output is in `docs/economy_sim_2026-11-27.txt`.

| Tier | Tool | Family | Tap damage | Cost | Unlocks | First bought (sim) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Wooden Pick | Pick | 1 | start | | |
| 2 | Stone Hammer | Hammer | 2 | 60 | | 0:18 |
| 3 | Copper Axe | Axe | 6 | 2,000 | | 2:15 |
| 4 | Iron Pick | Pick | 20 | 10,000 | | 4:40 |
| 5 | Steel Sword | Sword | 60 | 40,000 | | 7:30 |
| 6 | Frost Spear | Spear | 120 | 100,000 | | 10:05 |
| 7 | Gold Hammer | Hammer | 250 | 250,000 | | 12:25 |
| 8 | Crystal Axe | Axe | 500 | 500,000 | | 14:50 |
| 9 | Ice Drill | Spear | 800 | 750,000 | | 17:55 |
| 10 | Diamond Sword | Sword | 1,200 | 1.5M | | 21:35 |
| 11 | Flame Pick | Pick | 2,000 | 3M | | 23:30 |
| 12 | Thunder Hammer | Hammer | 3,000 | 5M | | 28:15 |
| 13 | Aurora Blade | Sword | 4,000 | 7.5M | | 31:30 |
| 14 | Lava Axe | Axe | 50,000 | 100M | level 33 | run 2 |
| 15 | Starfall Spear | Spear | 250,000 | 2B | level 37 | run 4 |
| 16 | Comet Hammer | Hammer | 1.5M | 20B | level 41 | run 4 |
| 17 | Cosmic Pick | Pick | 6M | 200B | level 45 | runs 5-6 |
| 18 | Starbreaker | Sword | 25M | 2T | level 48 | run 7 |

**First run.** A new tool comes about every 2.5 minutes, 12 of them by the rebirth. The longest wait is 4–5 minutes.
The rebirth level is reached at 33.6, 34.7 and 37.2 minutes (it was 35.2 before the tools).

**Tap share.** Taps deal 29–36% of the damage at every layer of the first run: 35% in Layer 1, 29% in Layer 2,
29–34% in Layer 3. Frost Touch adds up to 6 points on top; the simulated player still buys Frost Touch I
at about 12–14 minutes.

**Later runs.** Taps stay at 28–37% in Layer 4 and 30–50% in Layer 5. The early layers of later runs fly by on
buildings.

**Why the deep tools wait for a block level.** Each rebirth multiplies crystals, but not block HP. A tool with only a
price would therefore be affordable earlier in every run, and the top tools would end up in Layer 4. With the level
gate, they arrive where intended:

- the Lava Axe in run 2;
- the Starfall Spear and the Comet Hammer in run 4;
- the Cosmic Pick in runs 5–6;
- the Starbreaker in run 7.

## How each swing feels

- **Iron Pick (Pick):** the familiar overhead strike, then diagonals from the left and the right in turn (0.56 s,
  the strike at 0.17 s), a small camera nudge and a knee dip. It is the old pick swing, now with a pick 20% longer.
- **Gold Hammer (Hammer):** slow and heavy (0.78 s). The hammer goes up high behind the head, hangs there for a
  moment, then slams down at 0.32 s. The body leans into the slam and the knees dip deep, then it bounces off the ice.
  It has the strongest camera jolt (almost three times the pick's), twice the chips at one and a half times the size,
  and gold sparks. An overhead slam and a slam from over the right shoulder take turns. Fast tapping plays it up to 3x
  faster.
- **Crystal Axe (Axe):** snappy diagonal chops, from over the left shoulder, then the right, the wrist snapping through
  (0.56 s, the strike at 0.18 s). Its chips and nudge are a little bigger than the pick's.
- **Ice Drill (Spear family):** drawn back to the chest with the point still on the ice, then a straight thrust with a
  short lunge: the front knee bends and the body goes forward (0.5 s, the strike at 0.18 s). A level thrust and a
  slightly lower one take turns. The bit spins on the hit and winds down in about half a second.
- **Diamond Sword (Sword):** the quickest (0.42 s, the strike at 0.13 s). It is a 3-hit combo: a sweep in from the
  right, a backhand from the left, then an overhead. A cyan trail streaks along each slash. It throws more sparks and
  fewer, smaller chips, with the smallest nudge.

Every family keeps the existing rules:

- the tap's effects and sound fire on the click;
- fast tapping speeds the swing up (to 2.2–3x) and cuts into it, never queueing;
- the knees bend only while standing;
- the animations are group-owned (`store-assets/animations/`).

## Size and fit

**Lengths.** The old picks were 3.5 studs. The new tools are:

- the Iron Pick and the Crystal Axe, 4.2 studs (+20%);
- the Gold Hammer, 4.0 studs, with a 2.1-stud head;
- the Ice Drill, 4.2 studs;
- the Diamond Sword, 4.6 studs.

They run 1.7–2.8k triangles each.

**Body and head.** No tool passes through the body or the head at the wind-up or the strike, on the smallest, the
default or the largest avatar.

**Reach into the ice.** From the tap spot, where players arrive, every strike stops 12–15 studs short of the ice.
Standing right against the block, the strike's end goes into the face:

| Tool | Depth into the face |
| --- | --- |
| Diamond Sword | 1.0–3.6 studs |
| Crystal Axe | 2.0 studs |
| Iron Pick | 2.2–3.6 studs |
| Gold Hammer | 3.6 studs |
| Ice Drill | 4.4 studs |
| Old Iron Pick (for comparison) | 3.2 studs |
