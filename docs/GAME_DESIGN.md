# Rescue Pets From the Ice: Game Design Doc

Nov 21, 2026 · @Josh Lee

## Overview

Rescue Pets From the Ice is a Roblox clicker. A giant block of ice in your plot holds a frozen creature: you tap to crack the ice, collect the crystals that fly off, and free the creature, which becomes your pet.

|  |  |
| --- | --- |
| Genre | Simulator / clicker with idle income |
| Audience | Ages 8–14, phone first |
| Session | 10–20 minutes, with offline earnings to bring players back |
| References | Cookie Clicker (producers, prestige), Roblox clicker simulators (pets, rebirths) |
| Title | Rescue Pets From the Ice (all names and art are our own) |

**The hook: you can see what's inside.** The creature's blurry silhouette gets clearer as the ice cracks, and rare creatures glow through the ice from the moment the block arrives. Every block is a small mystery, and a glowing one is worth sticking around for.

Three pillars decide every feature:

- **Every tap feels good.** Ice chips fly, cracks spread, crystals spray out and a crunch plays on every hit.
- **Something is always about to happen.** The next crack stage, the next rescue, the next building is always seconds or minutes away.
- **Show off.** Your ice block and buildings fill your plot and your pets follow you around, where every player can see them.

## What it could look like

The concept renders in this doc show the intended look: chunky voxel shapes, bright snow, see-through ice with a creature silhouette and a rarity glow, and a bold cartoon UI. They're built from simple 3D blocks to show layout, scale and mood, not final art.

**Gameplay view.** A player at level 24 in Ancient Ice taps a block with a Legendary creature inside (gold glow, 68% cracked). Buildings ring the ice, three pets follow the player (a player with rebirths and a slot pass), and the HUD shows crystals per second, the layer, a Frost Rush timer and the Shatter Now offer.

&#91;image: Gameplay view: a player taps a glowing block of Ancient Ice with a Legendary creature inside, surrounded by buildings, pets and the HUD\]

## Core loop

Tapping the ice earns crystals, crystals build machines that crack it faster, and every block ends in a rescue whose pet makes the next block go faster still.

&#91;embedded content: core loop · tap, earn, build, hatch, rebirth\]

The short loop (tap, crystals, buildings) runs every few seconds; a rescue lands every 1–3 minutes; rebirth comes after about 30–40 minutes and restarts the run with a permanent bonus.

## Glacier depth: how players progress

Every block a player breaks takes them one level deeper into the glacier, and every 10 levels they reach a new ice layer with older ice, a new look and rarer creatures. Depth is the main goal: the next layer is always within reach, and it's always visibly better.

The player never leaves their plot. When a new layer starts, the ground shakes, the camera dips, a banner reads "Layer 2: Blue Ice", and the next block slides in made of the new ice.

| Layer | Block levels | Ice look | Common | Uncommon | Rare | Epic | Legendary | Mythic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1. Fresh Snow | 1–10 | Packed white snow, soft edges | 75% | 25% | – | – | – | – |
| 2. Blue Ice | 11–20 | Clear pale blue | 60% | 30% | 10% | – | – | – |
| 3. Ancient Ice | 21–30 | Deep blue with trapped bubbles | 50% | 30% | 15% | 5% | – | – |
| 4. Crystal Ice | 31–40 | Faceted, sparkling | 45% | 30% | 16% | 7% | 2% | – |
| 5. Primordial Ice | 41–50 | Dark teal with glowing veins | 40% | 30% | 18% | 8.5% | 3% | 0.5% |
| 6. Frozen Core | 51–60 (opened at rebirth 3) | Black ice lit from inside | 35% | 28% | 20% | 11% | 5% | 1% |

&#91;image: The five ice layers: Fresh Snow, Blue Ice, Ancient Ice, Crystal Ice and Primordial Ice\]

- **Layer 5 is the floor** until rebirths open deeper layers. Blocks past level 50 stay Primordial Ice, with HP still rising.
- **Each layer adds its own creatures** to the pool (see Creature roster), so a full Creature Book means going deep.
- **Lucky Ice** and the Mythic Block product raise these odds; the server always rolls from the current layer's table.
- Odds are starting values for the economy simulation; the shop's info button shows the live table.

## The ice block

Each block has HP, a creature frozen inside, and five crack stages. When its HP reaches zero the ice shatters, the creature is freed, and a new block slides in.

**Size and HP.** The block stands two to three times taller than an avatar in the middle of your plot. Each rescue raises the block level by one, and the next block has more HP:

```latex
\text{BlockHP}(L) = 100 \times 1.5^{\,L-1}
```

This is a starting value. The economy simulation tunes it so a rescue comes every 1–3 minutes at the intended pace.

**What's inside is rolled when the block arrives.** The server picks the creature as soon as a new block spawns, so its silhouette and glow can show from the first tap. Rare and better creatures glow through the ice in their rarity's colour:

| Rarity | Glow through the ice |
| --- | --- |
| Common, Uncommon | None, just a dark silhouette |
| Rare | Soft blue |
| Epic | Purple |
| Legendary | Pulsing gold, and the server is told |
| Mythic | Shifting rainbow, and the server is told |

**Crack stages.** The ice shows its damage in five steps, and the creature gets clearer at each one:

| Damage | What changes |
| --- | --- |
| 20% | Hairline cracks; the silhouette is a dark blur |
| 40% | Chunks fall off; the creature's shape is clear |
| 60% | Its eyes are visible and blink |
| 80% | It wiggles inside, the glow gets brighter, a heartbeat sound starts |
| 100% | The ice shatters and the creature breaks free |

&#91;image: Crack stages: an Epic Mini Yeti gets clearer at 20, 40, 60 and 80 percent, then breaks free at 100 percent\]

**Every hit.** Ice chips fly, a "+N" number floats up, crystals spray out, and a crunch plays. Its pitch rises slightly during fast tapping streaks.

**The rescue moment.** The ice explodes into shards with a crystal fountain worth about 30 seconds of the player's income. The creature shakes off the frost, a banner shows its rarity, and it runs to the player. A new, slightly bigger block then slides into the plot on a sled from the glacier.

## Economy

Crystals come from damage: every point of damage on the ice drops one crystal, times the player's multipliers. Taps and buildings both deal damage, so both earn crystals.

```latex
\text{Crystals/s} = (\text{tap damage} \times \text{taps/s} + \text{building damage/s}) \times \text{pet bonus} \times \text{upgrades} \times (1 + 0.05 \times \text{Frost Cores})
```

**Currencies.** Crystals are spent on buildings and upgrades. Frost Cores come from rebirths and give a permanent bonus. Robux buys passes and products.

**Buildings** are the producers. They stand on fixed pads around the ice and break it on their own, starting with simple tools and ending with heat and fire. Each copy costs 15% more than the last. Animals are kept for pets, so pets stay random and fun.

| Building | How it breaks the ice | Base cost (crystals) | Damage per second |
| --- | --- | --- | --- |
| Ice Pick Post | A spring-loaded ice pick on a post | 15 | 0.1 |
| Heat Lamp | Melts the surface | 120 | 1 |
| Chisel Mill | A water wheel drives a row of chisels | 1,300 | 8 |
| Ice Drill | Drills up from under the block | 14,000 | 50 |
| Wrecking Crane | Swings a wrecking ball | 150,000 | 280 |
| Flamethrower Turret | Blasts it with fire | 1.6M | 1,500 |
| Lava Pump | Sprays lava from underground | 22M | 8,000 |
| Sun Mirror Tower | Focuses sunlight into a beam | 350M | 45,000 |

```latex
\text{cost}(n) = \text{base} \times 1.15^{\,n} \qquad \text{cost of the next } k = \text{base} \times 1.15^{\,n} \times \frac{1.15^{\,k} - 1}{0.15}
```

**Upgrades.**

- **Tap power:** each tier doubles tap damage and upgrades the player's ice pick. Each tier costs 10 times the last.
- **Building upgrades:** double one building's damage and give it better parts. They unlock at 1, 10, 25, 50 and 100 owned.
- **Ice upgrades:** a bigger crystal burst on each rescue, and a little more crystals per damage.

All numbers are starting values. The economy simulation should hit three targets: the first rescue within 60 seconds, the first building within 30 seconds, and the first rebirth after about 30–40 minutes (reaching Layer 4).

## Buildings in detail

Each building has one pad and grows through five looks as the player owns more copies. Its upgrades show as better parts on the same model, so the plot always shows what the player has bought. Detail levels, below, combine both into one score per building.

| Building | 1 owned | 10 | 25 | 50 | 100 | Upgrade parts (in order) |
| --- | --- | --- | --- | --- | --- | --- |
| Ice Pick Post | One post | Three posts | Five posts on a stone base | Bigger base, gear on top | Golden base | Stone, iron, gold, diamond pick heads |
| Heat Lamp | One lamp | Lamp cluster | Lamps on a pole frame | Floodlight rig | Golden sun lamp | Brighter bulbs, orange, red, white-hot glow |
| Chisel Mill | Small wheel, 2 chisels | 4 chisels | Bigger wheel, 6 chisels | Twin wheels | Golden mill | Iron, steel, gold, crystal chisels |
| Ice Drill | Hand drill on a frame | Motor drill | Twin drills | Drill tower | Golden drill tower | Bigger bits, spiral bits, diamond bits, plasma bit |
| Wrecking Crane | Small crane | Taller boom | Two balls | Heavy-duty crane | Golden crane | Iron, spiked, steel, molten ball |
| Flamethrower Turret | One nozzle | Twin nozzles | Rotating turret | Quad turret | Golden turret | Orange, blue, purple, white flame |
| Lava Pump | Small pump, one hose | Two hoses | Lava pool beside it | Lava fountain | Golden pump | Hotter lava colours, bigger splashes |
| Sun Mirror Tower | One mirror | Mirror ring | Taller tower | Twin towers | Golden tower | Wider beam, double beam, rainbow beam |

- **Placement:** small buildings sit at the front pads, big ones at the back (see Plot and map layout).
- **Model budget:** five station models per building (40 in all), each with swappable upgrade parts. One model is shown per pad, never one per copy.
- **Fading:** once the next building up is owned, the previous station shrinks to 60% and loses its glow; the Ice Pick Posts become the fence ring around the ice.

## Detail levels

Every building has a detail level from 0 to 10, and every point adds something visible. Copies owned build up the structure; upgrades add parts, lights and effects. A building the player has invested in looks busier, more mechanical and more alive than one they just bought.

| Track | Points come from | What each point adds |
| --- | --- | --- |
| Structure | Owning 1, 10, 25, 50 and 100 copies | Base model, then a bigger frame, a base platform with a second unit, a taller structure, then gold trim |
| Parts and effects | Buying each of the 5 building upgrades | A better material on the working part, then lights, moving extras (gears, pistons, steam), hit particles, then a signature flourish |

**Example: the Ice Drill from detail 1 to 10.**

| Detail | Reached by | The Ice Drill gains |
| --- | --- | --- |
| 1 | 1 owned | A hand drill on a small frame |
| 2 | 1st upgrade | A steel drill bit |
| 3 | 10 owned | A motor housing and a taller frame |
| 4 | 2nd upgrade | Warning lights that blink on every hit |
| 5 | 25 owned | A stone base platform and a second drill |
| 6 | 3rd upgrade | Spinning gears and a puff of steam on every hit |
| 7 | 50 owned | A lattice drill tower with a smoke stack and a ladder |
| 8 | 4th upgrade | Ice chips and sparks flying on every hit |
| 9 | 100 owned | Gold trim and a crest on the tower |
| 10 | 5th upgrade | Diamond bits that leave a crystal trail: a Masterwork |

&#91;image: The Ice Drill at detail 1, 3, 5, 7 and 10: from a small wooden frame to a gold-trimmed Masterwork tower with twin drills, a smoke stack and a crystal trail\]

**Masterwork.** At detail 10 a building becomes a Masterwork: a soft sparkle aura, an idle animation between hits, a name plate with the player's name, and a star on its Build card. A Masterwork also deals +10% damage (a starting value for the economy simulation), so maxing a building is worth chasing.

**Showing it.**

- Each new detail point pops onto the building with a puff and a short camera nudge, the same moment as a first purchase.
- Build cards show the detail level as ten small pips, so players can see what's next ("3 more upgrades to Masterwork").
- Order matters only for timing: the two tracks can be filled in any order, and the model always shows whatever has been earned.

**How it's built.** Each building is one structure model per count milestone (5 per building, as before) with named attachment points. Each upgrade is a small part set that snaps onto those points, so the tracks combine automatically without a model for every combination. Lights, moving parts and particles run on the client; other players' plots show structure and lights but skip particles past 60 studs, and the reduced-effects setting turns hit particles off.

## Upgrades in detail

Upgrades are one-time purchases in the Upgrades panel. There are three kinds: the ice pick (tapping), building upgrades, and ice upgrades. About 60 in all at launch.

**Ice pick tiers** (tap power; each tier also changes the pick the player swings):

| Tier | Pick | Tap damage | Cost (crystals) |
| --- | --- | --- | --- |
| 1 | Wooden pick | 1 | Start |
| 2 | Stone pick | 2 | 100 |
| 3 | Iron pick | 4 | 1,000 |
| 4 | Gold pick | 8 | 10,000 |
| 5 | Diamond pick | 16 | 100,000 |
| 6 | Cosmic pick | 32 | 1M |

**Frost Touch** keeps tapping worthwhile late in a run: each tier makes every tap also deal a share of the player's building damage per second.

| Upgrade | Effect | Cost (crystals) | Unlocks when |
| --- | --- | --- | --- |
| Frost Touch I | Taps add 1% of building damage/s | 50,000 | Own a Wrecking Crane |
| Frost Touch II | 2% | 5M | Own a Flamethrower Turret |
| Frost Touch III | 3% | 500M | Own a Sun Mirror Tower |

**Building upgrades:** five per building (40 in all). Each doubles that building's damage and adds its next upgrade part.

| Upgrade | Unlocks at | Cost |
| --- | --- | --- |
| 1st | 1 owned | Building base cost × 10 |
| 2nd | 10 owned | × 50 |
| 3rd | 25 owned | × 500 |
| 4th | 50 owned | × 5,000 |
| 5th | 100 owned | × 50,000 |

**Ice upgrades:**

| Upgrade | Effect | Tiers | Tier costs (crystals) |
| --- | --- | --- | --- |
| Bigger Burst | Rescue fountain worth 30 → 45 → 60 seconds of income | 2 | 5,000 / 250,000 |
| Crystal Yield | +10% crystals per point of damage, per tier | 3 | 20,000 / 1M / 50M |
| Fast Sled | The next block arrives 1 second sooner, per tier | 2 | 2,000 / 100,000 |

Upgrades reset on rebirth. Costs are starting values for the economy simulation.

## Pets

Every rescued creature becomes a pet. Equipped pets follow the player and add to their crystal bonus, so freeing creatures is both how you collect and how you get stronger.

| Rarity | Crystal bonus when equipped | Glow through the ice |
| --- | --- | --- |
| Common | +10% | None |
| Uncommon | +25% | None |
| Rare | +50% | Soft blue |
| Epic | +100% | Purple |
| Legendary | +200% | Pulsing gold |
| Mythic | +400% | Shifting rainbow |

The chance of each rarity depends on the layer (see Glacier depth).

- **Pool:** 18 creatures at launch in one pool (4 Common, 4 Uncommon, 3 Rare, 3 Epic, 2 Legendary, 2 Mythic). New creatures arrive in updates.
- **Equip slots:** 1 at the start, so only one pet follows the player and picking it is a real choice. Rebirth ranks add more (a 2nd slot at rebirth 3, a 3rd at rebirth 6, a 4th at rebirth 10), and two Robux passes add up to 3 more, for a maximum of 7. Equipped bonuses add together.
- **Inventory:** 50 pets, with an Equip Best button and a delete button.
- **Golden pets:** combine 5 of the same pet into a Golden version with double the bonus.
- **Kept forever:** pets stay through rebirths.
- **Announcements:** a server-wide message when a Legendary or Mythic block arrives, so other players can come and watch the rescue.

## Creature roster

Eighteen creatures at launch: cute and fantasy snow animals, and no dinosaurs or prehistoric beasts, so the game reads differently from other frozen-creature games. Each creature first appears in a set layer and keeps appearing in every layer below the floor.

| Creature | Rarity | First found in | Look |
| --- | --- | --- | --- |
| Snow Bunny | Common | Fresh Snow | Round white bunny with fluffy earmuff ears |
| Penguin Chick | Common | Fresh Snow | Grey fluffball with a tiny orange beak |
| Frost Mouse | Common | Fresh Snow | Pale blue mouse with an icicle tail |
| Puffin Pal | Common | Fresh Snow | Puffin with a frosty striped beak |
| Arctic Fox Kit | Uncommon | Fresh Snow | White fox cub with a blue tail tip |
| Seal Pup | Uncommon | Fresh Snow | Round white pup with big dark eyes |
| Snowy Owlet | Uncommon | Fresh Snow | Big-eyed owl chick with frosted feathers |
| Ice Hedgehog | Uncommon | Fresh Snow | Hedgehog whose spikes are icicles |
| Polar Bear Cub | Rare | Blue Ice | Chubby cub wearing a scarf |
| Glacier Otter | Rare | Blue Ice | Otter floating on its back, holding a snowflake |
| Frost Turtle | Rare | Ancient Ice | Turtle with a shell of ice crystals |
| Mini Yeti | Epic | Ancient Ice | Small shaggy yeti with a big grin |
| Crystal Stag | Epic | Ancient Ice | Fawn with glowing crystal antlers |
| Ice Wolf Pup | Epic | Crystal Ice | Silver wolf pup with glowing blue eyes |
| Frost Dragon Hatchling | Legendary | Crystal Ice | Baby dragon, pale blue scales, frosty breath |
| Snow Phoenix | Legendary | Primordial Ice | White bird with icy flame feathers |
| Aurora Fox | Mythic | Primordial Ice | Fox whose tail ripples with northern lights |
| Spirit Whale | Mythic | Primordial Ice | Small floating whale made of aurora light |

- **Models:** 18 voxel pets from the existing pipeline. Golden versions reuse each model with a gold material, so no extra models.
- **Silhouettes** use the same model, coloured one dark shade, inside the ice.
- **Updates** add creatures per layer, and new layers bring their own.

## The Creature Book

The Creature Book is the long-term goal: every creature in the game, shown as a dark silhouette until the player rescues one. It is kept through rebirths and gives permanent rewards for filling it.

&#91;image: Creature Book: a completed Common page and an Uncommon page with two creatures found, one marked New, and two silhouettes\]

- **Pages:** one page per rarity, plus a Golden page. Each entry shows the creature, its first layer, how many have been rescued, and a "New!" badge until viewed.
- **First rescue moment:** the first time a creature is freed, the book flies open on screen, the page flips and the silhouette fills in with colour.
- **Hints:** a silhouette entry tells the player where to look ("Found in Ancient Ice or deeper").

| Page completed | Permanent reward |
| --- | --- |
| Common (4) | +5% crystals |
| Uncommon (4) | +5% crystals |
| Rare (3) | +10% crystals |
| Epic (3) | +10% crystals and a frosty name-tag border |
| Legendary (2) | +15% crystals and a golden name-tag border |
| Mythic (2) | An aurora trail behind the player |
| Golden (all 18) | The title "Ice Keeper" and a golden ice pick skin |

Completion shows as a percentage on the book button, and the leaderboards in the plaza include creatures rescued.

## How buildings, upgrades and pets look

Everything a player buys shows up in the world: buildings around the ice, upgrades on the buildings and the player's ice pick, and pets following the player.

**Buildings.** The plot has eight fixed building pads in a ring around the ice, one per type, so it never gets crowded. Small buildings sit close (the Ice Pick Post right at the base) and big ones sit further out or tower above (the Lava Pump, the Sun Mirror Tower). The first copy of a type rises out of the snow with a puff while the camera nudges toward it. More copies add a "×37" badge instead of more models, and the station grows at milestones:

| Owned | Ice Pick Post station |
| --- | --- |
| 1 | One post |
| 10 | Three posts |
| 25 | Five posts on a stone base |
| 50 | A bigger base with a gear on top |
| 100 | A golden base |

Every hit makes the ice shudder and pops a few crystals. Animations speed up with the number owned, up to a cap, so a richer plot looks busier.

Once a player owns the next building up, the older station shrinks and blends into the scenery (the Ice Pick Posts become a fence around the ice). The building they are working on now stays in the spotlight.

**Upgrades.**

- **Tap power** upgrades the ice pick the player swings on every tap: wood, stone, iron, gold, diamond, then cosmic, each with its own spark colour.
- **Building upgrades** give the building better parts (a stone pick head, then iron, then gold; a hotter flame), change its hit sparks, and add a star to its badge.
- **Ice upgrades** make the rescue burst bigger and turn the crystals from white to blue to gold.
- **Rebirths** give a rank title and colour on the player's name tag ("Rebirth 7") and change the colour of the plot's border.

**Pets.** Pets are the only animals in the game, and they follow the player everywhere. They hop when the player taps, cheer when a creature is freed, and each has its own idle animation. They are the random, fun part of the game: you never quite know what the next block holds.

**Progression at a glance.** Four things show how far a player has come, so buildings don't have to carry it all:

| What | How it shows progress |
| --- | --- |
| The ice block | Gets bigger with each level and turns into a new kind of ice at every layer. It is the centre of the plot, so it is seen first. |
| The ice pick | Wood, stone, iron, gold, diamond, cosmic, with matching sparks on every tap. Players carry it everywhere. |
| Pets | Rare, Golden and Mythic pets following the player are the main way to show off. |
| Rebirth rank | A title and colour on the name tag and a plot border colour. |

The ice block shows how far you have come, buildings show what is earning for you now, and the ice pick and pets are what you show off while walking around.

**Menus.** Each building card in the Build panel shows a 3D preview, the number owned, the price, damage per second and a bar for its share of income. Locked buildings show as dark silhouettes marked "???" until the player is close to affording them. Upgrades are a grid of square icons sorted by price, dimmed until affordable. Buying flashes the card and puffs the station in the world at the same moment.

## Plot and map layout

Each plot is a 100 × 100 stud square of snow with the ice block in the middle, eight building pads in a ring, and an open front facing the plaza. Small buildings sit at the front, big ones at the back, so a maxed plot looks impressive from the plaza.

&#91;image: Plot layout: the ice block in the centre, eight numbered building pads, the fence of old ice pick posts and the open front toward the plaza\]

**The plot** (positions in studs from the centre of the ice; +Z is the open front toward the plaza):

| Pad | Building | Position (X, Z) | Pad size |
| --- | --- | --- | --- |
| 1 | Ice Pick Post (becomes the fence ring) | (+24, +38) | 8 |
| 2 | Heat Lamp | (−25, +38) | 8 |
| 3 | Chisel Mill | (−40, +18) | 10 |
| 4 | Ice Drill | (−40, −12) | 10 |
| 5 | Wrecking Crane | (−25, −38) | 12 |
| 6 | Flamethrower Turret | (0, −42) | 12 |
| 7 | Lava Pump | (+26, −39) | 14 |
| 8 | Sun Mirror Tower | (+40, −9) | 16 |

- **Ice block:** 14 studs tall at level 1 (about 2.5 avatars), growing to 20 studs by level 50. It sits on a raised snow mound so it's visible over the fence.
- **Tapping spot:** the open area in front of the ice, where the player usually stands with their pets.
- **Border:** a low snow wall in the player's rebirth colour, open at the front.

**The map.**

- **Plaza** in the centre: the spawn point, the Golden Glacier landing ring, three leaderboards, the codes board, the daily and group reward chests, and the VIP lounge behind a gate.
- **Plots:** eight plots in a ring around the plaza, each with its open front facing the centre, so players see other players' ice glowing as they walk around.
- **Getting to your plot:** a glowing arrow and a short path lead from spawn to the player's plot; a Home button in the HUD walks or teleports them back.

## Rebirth

A rebirth resets the run in exchange for Frost Cores, which add 5% crystals each, forever.

```latex
\text{Frost Cores earned} = \left\lfloor \sqrt[3]{\text{crystals earned this run} \div 1{,}000{,}000} \right\rfloor
```

| Lost on rebirth | Kept |
| --- | --- |
| Crystals, buildings, upgrades, block level | Pets, Frost Cores, rebirth rank, Robux items |

**When:** the Rebirth button lights up once the player reaches Layer 4 (Crystal Ice, level 31). Rebirthing sends them back to level 1, but Frost Cores make every block go faster, so they pass their old depth quickly.

**Rebirth ranks open deeper layers:**

| Rank | Title | Name-tag and border colour | Opens |
| --- | --- | --- | --- |
| 1 | Ice Breaker | Light blue | – |
| 2 | Frost Finder | Teal | – |
| 3 | Glacier Diver | Purple | 2nd pet slot, and Layer 6: Frozen Core |
| 6 | Core Keeper | Gold | 3rd pet slot |
| 10 | Glacier Legend | Rainbow | 4th pet slot, and Layer 7 (update) |

So rebirth isn't just starting over: it's how players reach places they couldn't before.

## Social and events

Players share one world. Everyone can see each other's ice and what's glowing inside it, and server-wide golden blocks make players race each other.

- **Plots:** 8 plots per server around a central plaza. Your ice block, your buildings breaking it and the pets following you are visible to everyone who walks by.
- **Rare rescues are events:** when a Legendary or Mythic block arrives, the whole server is told, and other players can come and watch it break.
- **Golden Glacier rush:** every 5–8 minutes a golden ice block crashes into the plaza with a countdown and a sound. Everyone who taps it before it breaks gets a Frost Rush (×3 crystals for 60 seconds). The player who dealt the most damage gets ×5.
- **Leaderboards:** boards in the plaza for all-time crystals, rebirths and creatures rescued.
- **Daily reward and group reward:** a daily crystal chest, and +10% crystals for members of the group.
- **Codes:** a launch code, a tutorial-completion code, and milestone codes for likes.
- **Later update:** tapping a friend's ice gives them crystals and you a small share.

## Monetization

Launch with 6 passes and 4 kinds of products. Every price below is a starting point to check against the top clicker simulators before launch.

| Item | Type | Price (Robux) | What it does |
| --- | --- | --- | --- |
| 2x Crystals | Pass | 249 | Doubles all crystals, forever |
| Auto Pick | Pass | 149 | The server taps 5 times a second for you while you're in your plot |
| VIP | Pass | 299 | +20% crystals, a gold name tag, a VIP lounge in the plaza |
| Extra Pet Slot | Pass | 449 | One more pet follows you |
| Pet Squad | Pass | 899 | Two more pets follow you (with Extra Pet Slot, +3 in all) |
| Lucky Ice | Pass | 349 | Doubles the chance of Legendary and Mythic blocks |
| Crystal bundles | Product | 29 / 149 / 499 | 10 minutes, 1 hour or 6 hours of your current income |
| Shatter Now | Product | 25 | Breaks the current block instantly |
| Server Frost Rush | Product | 99 | ×2 crystals for everyone in the server for 15 minutes, with your name announced |
| Mythic Block | Product | 199 | Your next block rolls from a pool with better odds |

- **Gifts:** every pass can be bought as a gift for another player.
- **Mythic Block is a paid random item:** show its odds behind an info button and check PolicyService on the server, as in Steal Safari Pets.
- **Shatter Now sells best on a glowing block:** show its button bigger when a Rare or better creature is inside.
- **Crystal bundles scale with income,** so they stay worth buying at every stage.

**Pet slots are the priciest passes on purpose.** Every equipped pet adds its full bonus, so a second pet early on is the biggest boost in the game. Without passes, players earn slots through rebirths (3, 6 and 10); the passes let paying players skip ahead. The Pets panel shows locked slots with "Rebirth 3" or the pass price on them, and both passes can be gifted.

## UI and controls

Inside your plot, a tap anywhere on the screen swings your ice pick at the block, so phone players never have to aim. Outside your plot, taps only count on a golden block.

| Device | Hit the ice |
| --- | --- |
| Phone and tablet | Tap anywhere that isn't a button |
| PC | Click anywhere, or press Space |
| Gamepad | R2 or A |

**HUD.**

- **Top:** crystals and crystals per second, counting up smoothly.
- **Above the ice:** an HP bar with the crack percentage and the block level.
- **Left side:** Build, Upgrades, Pets, Rebirth and Shop buttons.
- **Build panel:** buy ×1, ×10, ×100 or Max. The next affordable building glows.
- **Phones:** nothing near the jump button or the bottom edge.

**Tutorial,** with an arrow guiding each step:

1. Tap the ice.
2. At 15 crystals, build an Ice Pick Post.
3. Free the first creature.
4. Equip your new pet.
5. Done: show the tutorial code.

The style follows the roblox-ui-style showcase kit from Steal Safari Pets, recoloured with icy blues and white.

## Screens

Every screen at launch, so the UI can be built from one list. All use the showcase window style from the UI kit.

| Screen | Opens from | What's on it |
| --- | --- | --- |
| HUD | Always | Crystals and crystals/s (top), layer and level badge, side buttons (Build, Upgrades, Pets, Book, Rebirth, Shop), Home button, Frost Rush timer when active |
| Ice block overhead | Always, above the ice | HP bar, crack %, block level, rarity glow label once 40% cracked |
| Build panel | Build button | Eight building cards (3D preview, owned, price, damage/s, income share bar), buy ×1/×10/×100/Max, locked buildings as "???" |
| Upgrades panel | Upgrades button | Grid of upgrade icons sorted by price, dimmed until affordable; Owned tab |
| Pets panel | Pets button | Inventory grid, equipped slots on top, Equip Best, delete, combine 5 into Golden |
| Creature Book | Book button | Pages by rarity, silhouettes, rescue counts, page rewards, completion % |
| Rescue reveal | Block shatters | Creature, name, rarity banner, "New!" badge, crystal burst total |
| New layer banner | Every 10th level | Layer name and number, new ice preview, "Rarer creatures ahead" |
| Rebirth | Rebirth button | Frost Cores you'd earn, what resets, what's kept, next layer opened, confirm |
| Robux shop | Shop button | Passes, crystal bundles, Shatter Now, Frost Rush, Mythic Block with an odds info button, gifting |
| Welcome back | Joining after time away | Offline crystals earned, a Collect button |
| Codes | Codes board in the plaza | Code entry and result |
| Settings | Gear button | Music, sound effects, reduced effects for low-end phones |

&#91;image: Build panel: eight building cards with owned counts, damage per second, income bars and prices, the next building highlighted and two locked\]

Phones: side buttons on the left edge, nothing near the jump button or the bottom edge; every panel closes with a big X and by tapping outside.

## Sound and effects

Sound and effects carry most of the "every tap feels good" pillar. Every sound comes from Roblox's catalog or is made for the game; nothing is copied from other games.

| Moment | Sound | Visual effect |
| --- | --- | --- |
| Tap | Short ice crunch, pitch rising during streaks | Ice chips, "+N", small crystal spray, pick swing |
| Building hit | Softer clink per building type | Building animation, the ice shudders |
| Crack stage | A louder crack | New crack layer, chunks falling, camera nudge |
| 80% damage | A slow heartbeat | Creature wiggles, glow brightens |
| Shatter | Glass-burst crash | Ice shards fly out, crystal fountain, frost puff |
| Rescue reveal | Happy jingle; bigger fanfare for Epic and up | Rarity banner, confetti in the rarity colour |
| New layer | Deep rumble and a whoosh | Ground shake, camera dip, layer banner |
| Buy building | Construction clunk | Station rises from the snow with a puff |
| Rebirth | Wind swell | Screen frosts over and clears |
| Golden Glacier | Alarm chime, then a crash | Golden block falls into the plaza with a countdown |
| Music | Calm, light wintry loop on the plot; a faster track during Frost Rush | – |

A "reduced effects" setting halves particles and turns off camera shake for low-end phones.

## Technical design

The server owns every number. The client sends tap counts and requests, and only animates what the server decides.

- **Taps:** the client counts taps and sends the total every 0.25 seconds. The server allows up to 20 taps per second, drops anything over that, and logs players who keep going over.
- **Server tick:** 4 times a second the server adds building damage, lowers the block's HP, adds crystals, and frees the creature when the HP reaches zero.
- **The creature roll:** the server rolls the creature when a block spawns and stores it on the block, so the silhouette and glow can show from the start. The roll is final; nothing on the client can change it.
- **The ice look:** a see-through ice shell around a copy of the pet model coloured one dark shade, as the silhouette. Each crack stage lowers the frost on the ice and swaps in a crack layer. The glow is a light inside the block in the rarity colour. Test glass and lights on a low-end phone early.
- **Replication:** crystals, crystals per second, block HP and the block's rarity are attributes updated about 4 times a second. The client counts smoothly between updates.
- **Saving:** PlayerData from Steal Safari Pets (session lock, schema version, separate Studio stores). It saves crystals, crystals earned this run and all time, buildings owned, upgrades, block level, the current block's creature, pets and equipped slots, Frost Cores, rebirths, creatures rescued and passes.
- **Big numbers:** Luau numbers reach about 1e308, which is enough. Display uses suffixes (K, M, B, T, Qa, Qi, Sx, Sp, Oc, No, Dc). Leaderboards store `math.floor(math.log10(total) * 1000)`, because OrderedDataStore only holds whole numbers up to about 9e18.
- **Offline earnings:** building income only, at 50%, capped at 2 hours, shown in a welcome-back popup.
- **Anti-cheat:** every RemoteEvent is rate-limited. The server computes all prices and checks every buy and equip. Auto Pick runs on the server, so autoclickers can never beat the 20-taps-a-second cap.
- **Phones:** building animations, ice chips and crystal particles run on the client only. Each plot shows one model per building type with a count badge.
- **Analytics funnels:** Joined, First tap, First building, First rescue, First pet equipped, Tutorial done, First rebirth, plus a shop funnel.

## Data and code structure

A plan for Claude Code: what is saved, where the numbers live, and how the client talks to the server.

**Saved player data (schema 1).**

| Field | Type | Reset on rebirth |
| --- | --- | --- |
| crystals | number | Yes |
| crystalsThisRun, crystalsAllTime | number | This run only |
| blockLevel | number | Yes (back to 1) |
| currentBlock | { creatureId, hpLeft } | Yes |
| buildings | map of buildingId → count | Yes |
| upgrades | list of upgradeIds | Yes |
| pets | list of { uid, creatureId, golden } | No |
| equipped | list of pet uids | No |
| bookSeen | map of creatureId → rescue count | No |
| frostCores, rebirths | number | No (they grow) |
| maxLayerOpened | number | No |
| creaturesRescued | number | No |
| tutorialStep, codesRedeemed, lastOnline | various | No |
| purchaseIds | list (receipt de-duplication) | No |

**Config modules** (all numbers live here, never in gameplay code):

- `LayerConfig`: layers, level ranges, ice look ids, rarity odds.
- `CreatureConfig`: the 18 creatures, rarity, first layer, model ids.
- `BuildingConfig`: base cost, damage/s, pad, the five station models, upgrade parts.
- `UpgradeConfig`: every upgrade, cost, effect, unlock rule.
- `RebirthConfig`: Frost Core formula, rank titles and colours, which layer each rank opens.
- `MonetizationConfig`, `CodesConfig` (server only), `AnalyticsConfig`.

**Remote events** (the client only asks; the server decides):

| Remote | Client sends | Server does |
| --- | --- | --- |
| TapBatch | Tap count for the last 0.25 s | Clamps to 20/s, applies damage |
| BuyBuilding | buildingId, amount | Checks price, adds buildings |
| BuyUpgrade | upgradeId | Checks unlock rule and price |
| EquipPet, CombineGolden, DeletePet | Pet uids | Checks ownership and slots |
| Rebirth | Nothing | Checks requirement, resets, grants Frost Cores |
| RedeemCode | Code text | Server-only code table |
| GoldenTap | Tap count | Only near the golden block |

State flows back as player attributes (crystals, rate, block HP, rarity glow) and a few events (rescue reveal, new layer, golden block).

## Reuse, build plan and out of scope

About half of this game already exists in Steal Safari Pets, which is what makes one week realistic.

| Reused from Steal Safari Pets | Used here for |
| --- | --- |
| PlayerData | Saving, schema versions, Studio-safe stores |
| Monetization config, receipts, gifts | All passes and products |
| UIKit and UITheme | HUD, panels, shop |
| Debug menu (F2) and admin window (F3) | Add crystals, force a rescue, set block level, pick the creature inside, spawn a golden block |
| Egg hatch animation and voxel pipeline | The rescue moment, the creatures and buildings |
| Offline earnings, codes, analytics funnels | Same systems, new values |
| Group upload tool and launch skills | Assets and launch |

**Build plan:**

1. **Day 0:** finish this doc, copy the template repo, create the group game and the products.
2. **Day 1:** greybox ice block with HP, tap batching, crystals, saving.
3. **Day 2:** buildings, upgrades, the server tick, economy simulation.
4. **Day 3:** the ice look (silhouette, glow, crack stages), the rescue moment, pets, equip slots, voxel models (overnight run).
5. **Day 4:** glacier layers, the Creature Book, rebirth, golden block rush, monetization, tutorial, funnels.
6. **Day 5:** polish, phone, gamepad and 2-player tests, bug bash.
7. **Day 6:** icon, thumbnails, video, private test with friends.
8. **Day 7:** launch, watch live servers, hotfix.

**Out of scope for v1:** trading, tapping friends' ice, zones, seasonal events, a second prestige layer.

**Open questions:**

- Names and looks for the 18 launch creatures.
- Whether the silhouette shows the exact creature or only a rough shape until 40%.
- Whether phones can handle see-through ice, lights and buildings animating in 8 plots at once.
