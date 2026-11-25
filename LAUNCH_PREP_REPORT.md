# Launch prep: overnight report

Branch `overnight-launch-prep` (from `main` at 348b0e5). Pushed after every phase; not merged.

## Summary

All nine phases are done on `overnight-launch-prep`. It is pushed after every phase and not merged. All 20 specs pass (4,900 checks, up from 4,639).

- **Robux:** every pass and product in the design doc is built and tested with simulated purchases, including gifts for all of them (passes too), duplicate receipts and the restricted-region refusal. Only the Creator Hub ids are missing; `docs/ROBUX_PRODUCTS.md` has every name, description and price, ready to copy. Icon drafts for all 12 items are in `store-assets/icons/` (not uploaded).
- **Gaps:** most of the audit's gaps are filled. Among them:
  - the heartbeat and Golden Glacier alarm sounds (uploaded as the group);
  - the likes milestone codes;
  - the come-and-watch beams for rare blocks;
  - the building rise, evolution and upgrade moments;
  - confetti, the crystal and spark colours, the sled and the camera dip;
  - badge stars, the Masterwork plate, the aurora trail and the golden pick;
  - Space and A tap instead of jumping in your plot.

  The deferred gaps (3D build previews, model animation, the book's fly-in animation, menu icon art) are listed with reasons in the gap table below.
- **Playthrough:** a scripted new player, tapping 4/s and buying sensibly, reached the **first rebirth at 34.5 minutes** (target 30-40):
  - first rescue and first building at 24 s;
  - layer 2 at 4.4 min, first Rare at 5.9 min, layer 3 at 13.7 min;
  - all 7 onboarding funnel steps logged.

  It played near-perfectly, so real players will be slower; the proposals are in Phase 4.
- **Multiplayer (3 players):** all pass: the Glacier race (x5 for the top tapper, x3 for the rest), other plots' sounds, the rare beams and announcement, the leaderboards, a pass gift, Server Frost Rush, and a player leaving cleanly.
- **Security:** one high-severity exploit fixed: a repeated pet id in Delete could force a save rollback, for example a free re-roll of a paid Mythic Block. Seven smaller issues were fixed too. Abusive input on every remote from a client gained nothing and caused no server errors.
- **Saves:** specs now cover an every-field round trip, two live servers fighting over one save, and a rebirth keeping everything it should.
- **Performance:** about 51-58 fps and 15-17 ms render in Studio with all 8 plots maxed. Phones will struggle with the 1.3M triangles across the ring; reduced effects doesn't help, because the cost is the Precise meshes. Proposals are in Phase 6.
- **Phone and gamepad:**
  - Phone layouts are clean at 844x390. At 667x375 the banners, toasts and notice were fixed.
  - The gamepad works for tapping, B to close, and the first selection in every window. D-pad moves between buttons couldn't be tested from Studio.
- **Launch material:** 5 thumbnail drafts and 3 game icon concepts are in `store-assets/launch/`, plus a camera-preset script for full-size retakes. `docs/LAUNCH_CHECKLIST.md` lists every manual step, in order.

**Please save the place in Studio and keep a backup copy** (File > Save to File As). Nothing this run needs to be in the place file: everything is scripts, built at runtime. But the place holds the templates and the world from earlier passes, and Lighting Technology = Future.

## Questions for you

1. **Mythic Block odds:** 50% Rare / 30% Epic / 15% Legendary / 5% Mythic, rolled from the whole roster, so a level-1 player can pull a layer-5 creature. OK, or should it be limited to the player's own layer?
2. **Stacking:** every bonus multiplies: pets x book x Crystal Yield x Frost Cores x 2x Crystals x VIP x group x Frost Rush x Server Rush. At the top that's 2 x 1.2 x 1.1 x 5 x 2 = 26x on top of the save's own multipliers. Keep it, or make the passes and rushes add up instead?
3. **Crystal bundles:** "current income" = building damage/s + tap damage at 4 taps/s, x the multiplier at that moment (a rush included). Bought crystals also count toward the next rebirth's Frost Cores. OK?
4. **Server Frost Rush:** a second purchase adds 15 minutes rather than stacking to x4, and a rush ends if its server closes. OK?
5. **Doc vs code:** the doc's loop says pets and Frost Cores make every hit faster, but the formula (and the code) multiply crystals, not damage. Which is right?
6. **Phones:** do you want Automatic (level-of-detail) copies of the station templates for faded and other players' stations, or StreamingEnabled? (Phase 6.) This needs your go-ahead, because it changes the model setup.
7. **Daily chest:** it pays 300 s of crystals/s including any rush running, so claiming during a rush pays 2-10x. Leave it, or use the bundle-style income without rushes?
8. **Likes codes:** LIKES1K ... LIKES100K pay 5, 10, 15, 20, 30 and 60 minutes of income. OK?
9. **Space and A:** inside your plot (and next to a standing Golden Glacier) they now tap instead of jumping; outside they jump. OK?
10. **Pace proposals** (Phase 4): a "rebirth at level 31" goal on the HUD from level 25? An auto-equip-best option or a "new best pet" toast? A "delete all Commons" button before the pet inventory (50) fills during the second run?
11. **Menu and upgrade icons** are still words and emoji. Should they be made like the Robux icon drafts?
12. **Legendary glow:** gold light through the blue ice reads lime green (visible in `thumb_maxed_plot_legendary.png`). Retint it?
13. **Book tabs** on the smallest phones: the tab row scrolls, and MYTHIC sits half off the edge. Shorter tab names there?

## Check by eye or ear

- **Icon drafts:** `store-assets/icons/contact_sheet.png` (all 12 items) and `store-assets/launch/icon_concept_1-3.png`. Thumbnail drafts: `store-assets/launch/thumb_*.png`.
- **New sounds:** the 80% heartbeat and the Golden Glacier alarm chime (F2 debug menu > Sound > Play a sound > Heartbeat / GoldenAlarm). In game: your block at 80% cracked, and a Golden Glacier countdown.
- **Golden Glacier:** the new golden-ice look, and its TAP IT! label on a dark plate in front of the block. The label's final style wasn't seen live.
- **Shop:** both tabs, every card, and the Mythic Block INFO odds. Gift mode for a pass ("THEY OWN IT" when the other player has it).
- **Shatter Now** button on the right edge of your plot: plain blue normally; gold, bigger and pulsing with a Rare or better inside.
- **VIP:** the plaza lounge and its gold door (VIP owners walk through; others get a toast), and the gold "VIP · Name" tag seen by others.
- **Building moments:**
  - your first building rising out of the snow;
  - "Your X evolved!" with a white flash at 10, 25, 50 and 100 owned;
  - the flash and puff on a building upgrade;
  - stars on the station badge, and the "<name>'s Masterwork" plate.
- **Rescue and block:**
  - confetti in the rarity colour;
  - the sled under an arriving block;
  - the camera dip on a new layer;
  - crystals turning white, then blue, then gold with ice upgrades;
  - tap sparks in your pick's colour.
- **Creature Book rewards:** the aurora trail (Mythic page) and the golden pick (Golden page).
- **Rare blocks:** the beam over another player's Legendary or Mythic plot.
- **Purchase notice:** "Thanks! You got ..." now shows in the lower middle of the screen.
- **A real controller:** D-pad between buttons and A on a selected button (the input tool can't send real gamepad input).
- **A real phone:** frame rate looking across a full server, and the HUD bar and Book tabs at small sizes.
- **Lighting:** Technology is Future in Properties.

## Phase status

| Phase | State | Commit |
|---|---|---|
| 1. Audit | Done | see git log |
| 2. Robux items | Done (icons: agent still rendering, committed separately) | see git log |
| 3. Gaps | Done | see git log |
| 4. New-player playthrough | Done: first rebirth at 34.5 min (target 30-40) | see git log |
| 5. Multiplayer | Done (3 players) | see git log |
| 6. Performance, phone, gamepad | Done (proposals for phone geometry) | see git log |
| 7. Saves and security | Done | see git log |
| 8. Launch material | Done (drafts) | see git log |
| 9. Launch checklist | Done | see git log |

## Phase 1: gap list (docs/GAME_DESIGN.md against the code)

Every section of the design doc was checked against the code (by reading it, not by running it). Everything not listed here is built. "Outcome" is filled in as later phases deal with each gap.

### Monetization

| Gap | Outcome |
|---|---|
| 2x Crystals pass missing (no config entry, no multiplier) | Built (Phase 2) |
| Auto Pick pass missing (only the TapService.AddTaps hook) | Built: server taps 5/s in your plot, inside the 20/s cap |
| VIP pass missing (+20%, gold name tag); the lounge waits for it | Built: x1.2, gold "VIP" tag, lounge door |
| Extra Pet Slot and Pet Squad: configured with Id 0 (only ids are missing) | Ids are yours to paste (gift twins added) |
| Lucky Ice: odds logic exists, no pass, and IceBlockService.AddLuck is never registered | Built |
| Crystal bundles (income-scaled) missing | Built (10 min / 1 h / 6 h) |
| Shatter Now product, the HUD offer and the bigger button on a Rare+ block: missing | Built (right-edge button; gold, bigger, pulsing on Rare+) |
| Server Frost Rush product missing | Built (x2 for all, 15 min, banner, HUD timer) |
| Mythic Block product and its better-odds pool missing (PolicyService and the shop's odds panel exist) | Built (odds 50/30/15/5: a question for you) |
| Gifting a pass missing (products only) | Built (a gift product per pass; saved as GiftedPasses) |
| Shop shows only 2 passes and no products | Fixed: 6 passes, 6 products |

### Social and events

| Gap | Outcome |
|---|---|
| Milestone codes for likes missing | Built: LIKES1K/5K/10K/25K/50K/100K, 5-60 min of income, off until you switch each on |
| "Other players can come and watch" a rare block: the server is told (toast) but nothing points them to it, and its break isn't announced | Built: a beam in the rarity colour over that plot until it breaks; the break is announced |
| Golden Glacier alarm chime missing | Built (new sound, uploaded) |

### UI and screens

| Gap | Outcome |
|---|---|
| Build card: no 3D preview; locked cards are "???" text, not dark silhouettes | Deferred: needs the building templates on the client (they live in ServerStorage; copies would cost phone memory) |
| Build card: next tier's glowing silhouette and "N more upgrades to Masterwork" hint missing | Hint built ("3 more to Masterwork"); silhouette deferred with the previews |
| Rescue reveal: confetti in the rarity colour missing | Built |
| New layer banner: the new ice preview missing | Deferred (the next block arriving in the new ice shows it a moment later) |
| Creature Book first rescue: no fly-in / page-flip animation (the silhouette does fill in) | Deferred (polish) |
| HUD: Shatter Now offer missing | Built (Phase 2) |
| HUD menu and Upgrades icons are placeholders (text/emoji; UITheme.Icons empty) | Deferred: needs icon art (a question for you) |
| Upgrade tile doesn't flash on purchase | Built |

### Sound and effects

| Gap | Outcome |
|---|---|
| Heartbeat at 80% silent (no sound) | Built (new sound, uploaded) |
| Music ids empty (your pick); faster Frost Rush track (doc: later) | Yours (LAUNCH_CHECKLIST.md) |
| "Equip" sound has no entry (silent; not in the doc's table) | Left: the button click already sounds |
| First copy of a building rises from the snow with a puff and camera nudge; puff per detail point: missing | Built (BuildMoments.client) |
| Evolution moment (shake, white glow, "Your X evolved!" banner) missing | Built |
| Building hits don't pop crystals | Built (your own plot, at most every 0.6 s) |
| Pick tiers have no spark colour; ice upgrades don't change crystal colour (white, blue, gold) | Built |
| No model animation: hit motions, moving extras (gears, pistons, rune rings), Masterwork idle | Deferred: needs moving parts split out of the 40 models (no new models this run) |
| Crystal Ice sparkle rate isn't updated live when reduced effects is switched | Fixed |
| New layer: shake but no separate camera dip | Built (Effects.Dip; off with reduced effects) |

### Gameplay and other

| Gap | Outcome |
|---|---|
| Masterwork name plate with the player's name missing | Built |
| Building badge shows "(detail/10)" rather than a star per upgrade | Built (★ per upgrade, MASTERWORK at 10) |
| Creature Book rewards: Mythic page aurora trail and Golden page golden pick skin are text only | Built (Trail on the character; gold Foil pick) |
| The next block slides in, but there is no sled object | Built (wooden deck on runners, shown while sliding) |
| Pace targets (rebirth at 30-40 min) not re-checked since the level-31 change (Phase 4) | See Phase 4 |
| Doc wording: "pet bonus speeds up every hit" / "Frost Cores make every block go faster", but pets and Frost Cores multiply crystals, not damage | A question for you (the code follows the Economy formula) |
| Space and gamepad A also make the character jump while tapping | Fixed: where you can tap they tap instead of jumping |

Built and checked (not gaps): the group bonus (+10%, group 921449746), the daily chest, the launch and tutorial codes, the reduced-effects setting (particles halved, no camera shake), the rare-block announcement toast, the Golden Glacier rush (5-8 min, countdown, x3 / x5), three leaderboards, the tap cap with logging, the 4-a-second server tick, offline earnings (buildings only, 50%, 2 hours away = 3600 s of income), the analytics funnels, the Pets panel's locked-slot labels.

## Phase 2: Robux items (code-complete)

Every pass and product in the doc's Monetization table is in `MonetizationConfig` with `Id = 0`, `GiftId = 0`, the doc's price and a registered reward kind (`src/server/RobuxPerks.luau`). The only thing left is creating them on the Creator Hub and pasting ids: `docs/ROBUX_PRODUCTS.md` has every key, name, store description and price, ready to copy (24 items: 6 passes, 6 products and a "Gift:" product for each).

| Item | Key | Price | What was built |
|---|---|---|---|
| 2x Crystals | DoubleCrystals | 249 | x2 on every crystal |
| Auto Pick | AutoPick | 149 | the server taps 5/s while you stand in your own plot; shares the 20/s bucket with your taps, never logged as cheating |
| VIP | VIP | 299 | x1.2, gold "VIP · Name" tag with a gold border, the plaza lounge (built only when this pass is in the config) with a door only VIP owners pass |
| Extra Pet Slot / Pet Squad | ExtraPetSlot / PetSquad | 449 / 899 | (already built) +1 / +2 equip slots; now giftable |
| Lucky Ice | LuckyIce | 349 | doubles Legendary and Mythic odds (taken from Common) |
| Crystal Pouch / Sack / Chest | CrystalPouch / CrystalSack / CrystalChest | 29 / 149 / 499 | 600 / 3,600 / 21,600 s of income |
| Shatter Now | ShatterNow | 25 | breaks your block now; refused while the next block is on its sled; HUD button on the right edge, gold, 35% bigger and pulsing on a Rare+ block |
| Server Frost Rush | ServerFrostRush | 99 | x2 for everyone in the server for 15 min, big banner with the buyer's name, HUD timer; buying again adds 15 min |
| Mythic Block | MythicBlock | 199 | paid random: odds behind the shop's INFO button, PolicyService checked for buyer and gift recipient; the next block rolls 50/30/15/5 Rare/Epic/Legendary/Mythic |

Locked pet slots already showed "Rebirth N" or the pass price (Pets panel); unchanged.

**Tested in Studio** (2-player test, as Player1 and Player2, through the real shop remote and receipt handler; simulated because no ids exist):
- All six passes bought: multiplier 2.40 (2 x 1.2); Auto Pick: block HP 81 -> 61 in 4 s with no taps (exactly 5 taps/s); Lucky on.
- Crystal Pouch: 5.76K crystals = 600 s x 4 taps/s x 1 damage x 2.4. Crystal Sack gifted to Player2: 34,560 (= 3,600 x 4 x 2.4 with the rush).
- Mythic Block: "1 waiting", then Shatter Now: level 1 -> 2; the next block rolled was Rare (PolarBearCub); waiting back to 0. Shatter Now on the sled: refused ("Wait for your next block to arrive").
- Server Frost Rush: x2 for both players (Player2's multiplier showed the x2), 898 s left; a second one: 1,797 s.
- Gifts: VIP to Player2 (Owns_VIP true, "(gift)", saved); Crystal Sack to Player2; VIP again: refused ("already has VIP"); Lucky Ice pass gift through the debug receipt: arrived.
- Duplicate receipt: "already granted, nothing given".
- Restricted region (StudioPaidRandomRestricted): buying and gifting the Mythic Block refused; a normal product still worked.
- Player1 saw Player2's tag as "VIP · Player2" in gold.
- The shop shows both tabs with every item; the Mythic Block card has the INFO (odds) button.

**Specs:** Monetization now checks the config against the doc's own Monetization table (names, prices, the three bundles), that every reward kind is registered, the bundle and rush rules, and that the Mythic Block rolls exactly its shown odds. PlayerData checks the two new save fields (GiftedPasses, MythicBlocks: saved, loaded, kept through a debug reset, fail closed when unreadable, cleaned). 20/20 specs, 4,740 checks.

**How the bonuses stack** (crystals per point of damage; every factor multiplies):

1. 1 crystal per point of damage. (Damage itself: tap damage = pick tier x Frost Touch; building damage = base x 2 per building upgrade x Masterwork +10%.)
2. x (1 + pet bonus) (the equipped pets' rarity bonuses, Golden x2)
3. x (1 + Creature Book bonus)
4. x (1 + Crystal Yield)
5. x (1 + 0.05 x Frost Cores)
6. x 2 (2x Crystals) x 1.2 (VIP)
7. x 1.1 (group member)
8. x 3 or x 5 (Golden Glacier Frost Rush, 60 s)
9. x 2 (Server Frost Rush, 15 min)

Steps 2-5 are `EconomyRules.Multiplier`; 6-9 are server-only extras (`Economy.AddExtra`). The doc's formula names only 2-5; it didn't say how passes and rushes combine, so they multiply like everything else (a question below). The debug action "Show the target's Robux perks" prints the factors for any player.

**Decisions made** (all placeholders in config):
- Mythic Block odds 50% Rare / 30% Epic / 15% Legendary / 5% Mythic, from the whole roster (so a level-1 player can get a layer-5 creature and the shown odds are always true).
- A crystal bundle's "current income" = building damage/s + tap damage at 4 taps/s, x the current multiplier (a new player with no buildings still gets something; a bundle bought during a rush is worth more).
- A second Server Frost Rush adds 15 minutes rather than stacking to x4; it isn't saved (ends with the server).
- Bought crystals count toward this run's total, so they raise the Frost Cores of the next rebirth.
- The VIP lounge door is client-side (your own character's physics), since the lounge gives no advantage.
- Item names: Crystal Pouch / Sack / Chest for the bundles.

**Icon drafts** (not uploaded): `store-assets/icons/` has a 512x512 draft for all 12 items, plus `contact_sheet.png` (all of them, with 64 px copies) and `README.md`. Each is rendered in headless Blender from the game's own models: creatures posed with their own clips, the real gold pick, a simple ice block and crystal gems. They're composited in Pillow with a bright gradient, a thick outline, sparkles and a short badge ("2X", "AUTO", "VIP", "+1", "+2", "LUCK x2", "10 MIN", "1 HOUR", "6 HOURS", "SHATTER!", "x2 SERVER", "?"). Regenerate with `python tools/icons/compose_icons.py --render` (about 100 s). The pass icons were checked inside the circle crop Roblox uses for passes. Known weak spots: the crown on VIP is 2D; the Lucky Ice silhouette reads as "a creature" more than a dragon; Shatter Now is busy at 64 px; the Mythic Block's rainbow is pastel. Note: the creature rarities follow `CreatureConfig` (e.g. Spirit Whale and Aurora Fox are Mythic there).

## Phase 3: gaps filled

Built (each from the doc; see the gap table for every outcome):
- **Sounds:** the 80% heartbeat and the Golden Glacier alarm chime (as the countdown starts), made in `tools/make_sfx.py`, uploaded as the group (Heartbeat 85965699278351, GoldenAlarm 78520467096529, pending moderation at upload), in AudioConfig. The generator now skips sounds whose samples haven't changed (Ogg files get a random serial number, which would have re-uploaded all 28).
- **Likes milestone codes:** LIKES1K, LIKES5K, LIKES10K, LIKES25K, LIKES50K, LIKES100K (5, 10, 15, 20, 30, 60 minutes of the player's income), `Active = false` until you reach each milestone.
- **Come and watch:** a beam in the rarity colour (Mythic: rainbow) over another player's plot while it holds a Legendary or Mythic block; the server announces the break ("X freed a Legendary Crystal Stag!") and the beam goes out.
- **Building moments:** the first copy rises out of the snow (tested: pivot -4.4 -> 0.6 studs) with a puff and a camera nudge; a station milestone (10/25/50/100) flashes white with a bigger puff, a shake and "Your X evolved!"; a building upgrade flashes and puffs; the upgrade tile flashes.
- **Effects:** rescue confetti in the rarity colour; building hits pop crystals on your own block; crystals white -> blue -> gold with ice upgrades (0 / 3 / 6 of 7 tiers); tap sparks by pick tier (orange, grey, white, gold, cyan, violet); the sled under an arriving block; the new-layer camera dip; Crystal Ice sparkles follow the reduced-effects setting live.
- **Badges and rewards:** a ★ per building upgrade and MASTERWORK on the station badge (tested: "Ice Pick Post ×111 ★★★★★ MASTERWORK"); the Masterwork name plate ("<name>'s Masterwork", tested on all 8); the golden pick skin (Golden page; spec-checked); the aurora trail (Mythic page); the Build card's "N more to Masterwork".
- **Controls:** where you can tap, Space and gamepad A tap instead of jumping (a high-priority ContextAction that sinks them); elsewhere they still jump.

Group bonus, daily chest and the reduced-effects setting were already built and working (no change needed).

Deferred (with the reason in the gap table): Build-card 3D previews and silhouettes, model animation (moving extras, hit motions, Masterwork idle), the book's fly-in animation, the new-layer banner's ice preview, menu icons (art).

Specs: Codes (the six milestone codes), Pick (golden skin), SoundRules (the two new sounds). 20/20 pass.

## Phase 4: new-player playthrough

A scripted player on a fresh save (StudioFreshSave): it taps 4 a second through the real tap remote, follows the tutorial, buys whatever pays back fastest (cost / extra crystals per second, the "sensible player" rule), equips its best pets after every rescue, redeems the launch code after its first building and the tutorial code when it's shown, and rebirths the moment it can. It never left its plot, so it never joined a Golden Glacier rush or opened the daily chest. The full log is in `docs/playthrough_2026-11-25.txt`.

| Milestone | Time | Doc target |
|---|---|---|
| First tap / tutorial step 2 | 0.1 min | - |
| First rescue | 0.4 min (24 s) | within 60 s: OK |
| First building | 0.4 min (a Heat Lamp: it paid back faster than the Ice Pick Post; the tutorial accepts any building) | within 30 s: OK |
| Tutorial done (THAWED shown) | 0.4 min | - |
| Layer 2 (Blue Ice) | 4.4 min | - |
| First Rare | 5.9 min (Glacier Otter) | - |
| Layer 3 (Ancient Ice) | 13.7 min | - |
| Layer 4 / level 31 / first rebirth | 34.5 min, +5 Frost Cores | 30-40 min: OK |

Rescue gaps: 0.3-0.5 min for the first 9 levels, 0.7-1.1 min in Blue Ice, 1.3-3.0 min in Ancient Ice (levels 21-30). The doc says 1-3 minutes, slowing to 4-6 past level 30: the start is faster than that (good for onboarding) and the end matches. 30 rescues, 29 pets kept, 170 buildings by the rebirth; no Epic or better in the whole first run (Ancient Ice has 5% Epic and only 10 blocks were rolled there).

Onboarding funnel, all 7 steps logged in order on the server: 1 Joined, 2 First tap, 3 First building, 4 First rescue, 5 First pet equipped, 6 Tutorial done, 7 First rebirth.

Bug found and fixed: the Shatter Now offer threw an error every frame while the player's plot index wasn't known yet (`false ~= nil` passed a check).

**Where a new player could get stuck or confused** (no balance changed; proposals):
1. **This was a near-perfect player.** It bought the best-payback item the moment it could and equipped its best pets every time. A real new player buys less well and will likely need 40-50 minutes. Proposal: watch the live "First rebirth" funnel step and session length; if most players quit before it, lower `RebirthConfig.RequiredLevel` or `LayerConfig.BlockHp` growth a little.
2. **Levels 25-30 drag**: 2-3 minutes a rescue while saving millions of crystals with nothing new to see (the last new building, the Flamethrower Turret, came at 17 min). Proposal: show the rebirth goal on the HUD from level 25 ("Rebirth at level 31: 3 more"), so the player knows the wait leads somewhere.
3. **Equipping isn't automatic.** After the tutorial a player who never opens PETS keeps their first pet. Proposal: a "NEW BEST PET!" toast with an Equip button, or an auto-equip-best setting.
4. **The pet inventory (50) fills during the second run** (29 pets after the first). Players will hit "inventory full" without a quick way out. Proposal: a "delete all Commons" button or auto-delete for duplicates of a set rarity.
5. **The Ice Pick Post is a worse buy than the Heat Lamp** from the very start (0.1 damage/s for 15 vs 1 for 120). The tutorial points at the Post, which is fine as a first step, but players who follow "the next affordable building glows" will notice the Post never pays. No change suggested (it is the cheap starter), only noted.
6. **No Epic in the first run**, so the Epic and better book pages and their rewards only appear after a rebirth. Fine for a long-term goal; the Rare at 6 minutes keeps the first session exciting.
7. The bot never saw a Golden Glacier (it stayed home). Real players get a rush every 5-8 minutes, which will speed them up.

## Phase 7: saves and security

### Every remote and what the server checks

No remote is created in code; every one is declared in `default.project.json`. An error inside a RemoteFunction handler reaches only the caller; the server never invokes a client. Every per-player limiter is cleared when the player leaves.

| Remote | Server checks | Problem found | Fixed |
|---|---|---|---|
| TapBatch | whole number 1-1000, not NaN; only in your own plot; a 20/s bucket (1 s burst) shared with GoldenTap and Auto Pick; logs players who keep going over (every 30 s at most) | none | - |
| GoldenTap | glacier active; same number checks and bucket; within 40 studs of the glacier | the distance uses your character's position (a teleport exploit can reach it, but walking there is allowed anyway) | accepted as is |
| BuyBuilding | 0.1 s between buys; known building id; amount 1/10/100/"Max" only; price and spending on the server | none | - |
| BuyUpgrade | same limiter; known id; unlock rules; price | none | - |
| PetRequest | known action; 0.15 s apart; data ready; uids must be owned strings (64 chars), lists 1-60 | **High:** a repeated uid in Delete (`{"a","a"}`) removed a second, unpicked pet and could leave a deleted pet equipped; the next save then refused the data and kicked the player WITHOUT saving: a rollback tool (e.g. a free re-roll of a paid Mythic Block). Low: requests that changed nothing still forced a save; MarkSeen accepted a map | Yes: lists with repeats or extra keys are refused; Delete never `table.remove(list, nil)`; Equipped is cleaned after every request; no-op requests don't save; MarkSeen needs a plain list (spec checks added) |
| RebirthRequest | action "Rebirth"; once per 2 s; data ready; level 31 | none | - |
| RedeemCode | 1 s apart, 6 a minute (checked first); text cut to 64 and normalised; once per player | none | - |
| PurchaseRequest | known action; key a string up to 32; 0.5 s apart; one open prompt at a time; data ready; real id (or simulated in Studio); gift: a whole-number recipient in this server, loaded, paid-random rules both ways | Low: a recipient id like 1e300 could make `GetPlayerByUserId` throw after the 30 s prompt lock was set (locking the player out of the shop) | Yes: ids must be under 2^53 and the recipient is looked up before the lock |
| SaveSettings | a table; 0.5 s apart; volumes numbers, NaN refused, clamped 0-1; ReducedEffects a boolean | none | - |
| ShopVisit (analytics) | shop "Robux"; 0.2 s apart, 40 a minute; Info key must be a real item | Medium: spamming "Open" started a new funnel visit each time (fake funnel numbers, and it spends the analytics budget) | Yes: one visit at a time, a new one at most every 15 s |
| DebugRequest / AdminRequest | access checked on the server for every request (live: DebugConfig empty = nobody; Admin = you only); limiter; every argument checked against the action's params | Medium: every refused request wrote a warning (log flooding) | Yes: a refusal is logged at most once a minute per user |
| GoHome | no arguments; once per 2 s; only to your own plot | Low: it let a jailed player out early | Yes: refused while jailed |
| GameEvent, PurchaseNotice (server to client) | - | Low: a client firing them made Roblox queue the calls and warn | Yes: empty handlers |
| (Saves) | - | Low: gameplay marked a save important many times a minute (rescue, build, pet), up to one write every 5 s per key | Yes: important saves at most every 15 s (Robux grants still save at once with SaveNow); spec checked |
| (Crystals) | - | Low: crystals past 1e300 would make the save refuse the player every session | Yes: Grant caps at 1e300 |

Not changed (a proposal): the daily chest pays 300 s x your current crystals/s, which includes a running Frost Rush or Server Frost Rush (claiming during a rush pays 2-10x). Once a day, so small; the fix would be to use the bundle-style income without rushes.

### Abuse test from a client (Studio, 3-player session)

A client script sent abusive input on every remote, in every argument slot (1,288 calls):
- NaN, ±inf, -1, 0, 0.5, ±1e308 and 2^53;
- strings: empty, "1" and 100,000 characters;
- empty, list and deeply nested tables, booleans, Instances and a Vector3;
- other players' ids (-2, 1, 99999999).

On top of that:
- every pet action and every purchase action with junk;
- gifts to 1e300, -1e300, NaN, 2^60, yourself and a missing player;
- 200 tap batches of 1,000 taps at once;
- junk settings;
- 60 shop "Open" spams.

Results:
- **Nothing was gained:** pets, buildings, upgrades, rebirths and level were unchanged. The 200,000-tap spam earned 42 crystals (the 1-second burst), and "[Taps] ... 980 taps dropped" was logged once.
- **Settings:** NaN was refused; -5 and 50 were clamped to 0 and 1.
- **Accepted calls:** only two MarkSeen no-ops, which don't save.
- **Server log:** no errors. The shop-visit funnel counted one visit for 60 opens.

### Saves: what the specs now cover

| Case | Covered by |
|---|---|
| Rejoin keeps everything | PlayerData spec: a save with every field set away from its default round-trips field by field after leaving and rejoining. The spec fails if a field is added that the round trip doesn't cover. |
| A rebirth resets exactly ResetOnRebirth | World spec: each reset field goes to a new player's value. Every other field (book, settings, codes, receipts, gifted passes, Mythic Blocks, daily chest, tutorial, funnels...) stays unchanged; Frost Cores, Rebirths and MaxLayerOpened may only grow. |
| Two servers fight over one save | PlayerData spec, two live PlayerData servers on one store: (1) B can't load while A holds the lease (the player is kicked there, the record untouched). (2) A keeps saving. (3) Once A stalls past its lease, B takes over and saves. (4) A has already stopped gameplay before its lease ran out, can't save, and its next autosave tick stops the session. (5) The record stays B's. |
| BindToClose saves | Already covered: shutdown saves and releases every session; a receipt during shutdown gives nothing. |
| Bad or corrupt fields | Already covered for dozens of cases. Added: crystals past 1e300 fail closed and are left untouched; a block whose HP can't be read is rolled again; settings that aren't a table go back to the defaults; gifted passes and Mythic Blocks. |
| Saving rate | An important change saves on the next tick; a second one within 15 s waits. |

## Phase 5: multiplayer (3 players, then 2)

Studio coped with 3 players (a server and 3 clients).

| Test | Result |
|---|---|
| Golden Glacier race (Player1 20 taps/s, Player2 8/s, Player3 4/s) | Pass: 190 / 76 / 38 taps. Player1 (most damage) got **x5** and the others **x3**, each with 58 s left on the rush. |
| Other plots' sounds | Pass. Player1, 30 studs from Player2's block, heard Player2's **Legendary** jingle at 0.27 (= 0.6 x 0.45, quieter). Player2's **Common** next to Player1 was silent. Player2's **Mythic**, with Player1 75 studs away, was silent. Player3, at home and far away, heard nothing. |
| Rare-rescue announcement | Pass: everyone got the "Announce" toast. A beam stood over Player2's plot on Player1's and Player3's screens (not on Player2's own). It went out the moment the block broke, with "Player2 freed a Legendary ...". |
| Leaderboards | Pass: after the 120 s refresh, all-time crystals, rebirths and creatures rescued listed the test players (from Studio's own leaderboard stores). |
| Pass gift Player1 -> Player2 (Auto Pick, simulated) | Pass: it arrived, marked "(gift)", and Auto Pick tapped 5/s for Player2. |
| Server Frost Rush (bought by Player3) | Pass: x2 for all three players (perks readout), with the banner and the HUD timer. |
| A player leaving (Player3 kicked with 3 stations and pets) | Pass: plot owner 0, name board cleared, 0 stations, block reset. Nothing named Player3 was left on the server or on the other clients (pets gone). |

Found and fixed in these sessions:
- **The debug "Reset to a fresh save" left the old stations on the plot**; the plot only refreshed on the next purchase. It now refreshes the stations, rolls a new block and publishes the pets. Spec-checked, and verified live (stations 1 -> 0).
- **The Golden Glacier** was a flat, Neon-bright yellow square under Future lighting; it's now golden Ice with a softer light. Its "TAP IT!" label sat on top of the HUD's crystal counter; it now stands in front of the block's lower half, in white text on a dark plate. The new block look was seen live; the label's final style wasn't (the glacier melted first), so check it by eye.
- **The purchase notice** ("Thanks! You got ...") sat at the top, over the HUD and any window's tabs. It now shows in the lower middle and shrinks to fit a small phone.

## Phase 6: performance, phone, gamepad

### Performance

Measured on a client with all 8 plots full: 2 real players and 6 debug dummy plots, each with 100 of every building and every upgrade, every block at level 400, and Legendary blocks glowing.

| View | Reduced effects | fps | Render CPU | Triangles | Draw calls |
|---|---|---|---|---|---|
| Plaza | off | 56 | 15.5 ms | 821k | 667 |
| Across the ring | off | 51 | 17.1 ms | 1,323k | 690 |
| Tapping spot | off | 58 | 14.5 ms | 317k | 442 |
| Plaza | on | 56 | 15.4 ms | 814k | 630 |
| Across the ring | on | 51 | 17.2 ms | 1,322k | 652 |
| Tapping spot | on | 57 | 14.5 ms | 317k | 418 |

- **Scene size:** 3,016 MeshParts in the plots, all RenderFidelity Precise; 6,400 BaseParts and 23,700 instances on the client; 10,850 instances on the server.
- **Memory:** Studio reports 2.2 GB for the client and 2.0 GB for the server. In Studio that includes Studio itself and its plugins (Lua heap 559 MB), so it says little about a phone. Of the game's own share: textures 65 MB, particles 29 MB, sounds 11 MB.
- **Network receive** reads 0 KB/s in a local Studio test (there is no real network). Measure it live (F9 > Stats).

**What would struggle on a phone:** geometry, not effects. Reduced effects barely changes the numbers (draw calls -5%). The 1.3 million triangles and ~700 draw calls come from 8 plots of Precise station meshes, so a low-end phone will drop frames looking across the ring. Suggested fixes (not done, because they change how the models are set up; a question below):
1. **Precise only where you look closely.** Use a second "Automatic" (level-of-detail) copy of each tier template for faded stations and for other players' plots. RenderFidelity can't be changed by scripts in a live game, so this needs separate templates.
2. **Streaming.** Turn on Workspace StreamingEnabled and stream each plot by distance, so far plots aren't in a phone's memory at all.
3. **Reduced effects.** With it on, hide other plots' faded stations (already shrunk to 60%) or their decorative upgrade parts.

### Phone layouts

Checked at StudioScreenSize 844x390 and 667x375. Every window was opened from the HUD and audited for text that doesn't fit, text too small to read, buttons under 36 px, anything off screen and overlapping buttons; screenshots too.
- **844x390:** the HUD and all 8 windows are clean.
- **667x375:**
  - The big banners and the toasts ran off the screen. Fixed: they shrink to fit.
  - The purchase notice could overlap a window's tabs. Fixed (above).
  - The Creature Book's tab row is wider than the window, so MYTHIC is cut off at the edge. The row scrolls sideways, so it's reachable (a question below).
- **Build cards** on a phone show 1.5 cards at a time (the list scrolls). The detail pips line ("★★★☆☆☆☆☆☆☆ 7 more to Masterwork") is small but readable.

### Gamepad

Tested with the StudioGamepad switch and gamepad buttons sent through Studio's input tool.
- **Tapping:** R2 and A tap the ice in your plot with 0 jumps, and so does Space. In the plaza, Space jumps and doesn't tap.
- **Menu:** D-pad left selects the first menu button (BUILD), and B closes a window.
- **Windows:** every window (Build, Upgrades, Pets, Book, Rebirth, Shop, Codes, Settings) opened in gamepad mode selects a button inside itself, and every button in it is selectable.
- **Not testable here:** Studio's input tool sends gamepad buttons as keyboard input, which Roblox's built-in gamepad UI navigation ignores. So moving between buttons with the D-pad and pressing A on a selected button couldn't be tested; check with a real controller.
- **Fixed:** the Rebirth window selected REBIRTH first, so mashing A could rebirth by accident (it takes two presses). It now starts on the close button.

## Phase 8: launch material (for your review; nothing uploaded)

### Thumbnails

In `store-assets/launch/`, at 1920x1080:
- `thumb_maxed_plot_legendary.png`: a maxed plot with its Masterworks, the Legendary block glowing, and the HUD.
- `thumb_mythic_rescue.png`: the Spirit Whale bursting out with "Spirit Whale rescued! NEW! MYTHIC", and the HUD.
- `thumb_golden_glacier_rush.png`: two players at the golden glacier in the plaza.
- `thumb_creature_book.png`: the Mythic page complete, with "Reward earned: an aurora trail".
- `thumb_fresh_plot_start.png`: a level-1 plot with the first block, and the HUD.

Notes on them:
- They are drafts for composition. The Studio test window's view is only 1565x620, so each is a 16:9 crop scaled up 1.74x, and a bit soft. Retake the ones you like at full size: `tools/studio/thumbnail_cameras.luau` has camera presets for the same scenes (run it on the client in Play), with the game window full screen.
- The Mythic rescue is **staged** from the game's own pieces (the Spirit Whale model, frozen ice shards and confetti, the real banner). The real moment lasts under a second and the capture tool lags 1-2 s.
- The debug and admin buttons and the tutorial hints are hidden in all of them.

### Game icon concepts

Also in `store-assets/launch/`, 512x512 with no text, rendered from the game's models (see the icon drafts in Phase 2):
- `icon_concept_1.png`: a Snow Bunny bursting out of cracked ice. The clearest at small size.
- `icon_concept_2.png`: a Polar Bear Cub in a glowing rainbow block, close up.
- `icon_concept_3.png`: three pets in front of a big glowing block with a pick.

## Phase 9: launch checklist

`docs/LAUNCH_CHECKLIST.md` lists every step to do by hand, in order:
- merge the branch, then save and back up the place;
- the 24 Robux items (icons, names, prices, gift twins, pasting ids), and the `[PriceCheck] 24 items checked, 0 problems, 0 hidden` line;
- DebugConfig empty, and the admin allowlist only you;
- Lighting Technology set to Future;
- music from the Toolbox (mood and tempo), and audio moderation;
- the codes: ICELAUNCH and THAWED live, the LIKES codes switched on at each milestone;
- the experience settings: server size 8, genre, devices, audio, maturity, icon, thumbnails, description;
- publishing;
- one real test purchase of a pass (with a second account, since yours owns every pass) and of a product;
- what to watch in the first hour.
