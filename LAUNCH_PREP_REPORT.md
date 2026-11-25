# Launch prep: overnight report

Branch `overnight-launch-prep` (from `main` at 348b0e5). Pushed after every phase; not merged.

## Summary

_(Written at the end of the run.)_

## Questions for you

_(Collected as the run goes.)_

## Check by eye or ear

_(Collected as the run goes.)_

## Phase status

| Phase | State | Commit |
|---|---|---|
| 1. Audit | Done | see git log |
| 2. Robux items | Done (icons: agent still rendering, committed separately) | see git log |
| 3. Gaps | In progress | |
| 4. New-player playthrough | Not started | |
| 5. Multiplayer | Not started | |
| 6. Performance, phone, gamepad | Not started | |
| 7. Saves and security | Not started | |
| 8. Launch material | Not started | |
| 9. Launch checklist | Not started | |

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
| Milestone codes for likes missing | |
| "Other players can come and watch" a rare block: the server is told (toast) but nothing points them to it, and its break isn't announced | |
| Golden Glacier alarm chime missing | |

### UI and screens

| Gap | Outcome |
|---|---|
| Build card: no 3D preview; locked cards are "???" text, not dark silhouettes | |
| Build card: next tier's glowing silhouette and "N more upgrades to Masterwork" hint missing | |
| Rescue reveal: confetti in the rarity colour missing | |
| New layer banner: the new ice preview missing | |
| Creature Book first rescue: no fly-in / page-flip animation (the silhouette does fill in) | |
| HUD: Shatter Now offer missing | Built (Phase 2) |
| HUD menu and Upgrades icons are placeholders (text/emoji; UITheme.Icons empty) | |
| Upgrade tile doesn't flash on purchase | |

### Sound and effects

| Gap | Outcome |
|---|---|
| Heartbeat at 80% silent (no sound) | |
| Music ids empty (your pick); faster Frost Rush track (doc: later) | |
| "Equip" sound has no entry (silent; not in the doc's table) | |
| First copy of a building rises from the snow with a puff and camera nudge; puff per detail point: missing | |
| Evolution moment (shake, white glow, "Your X evolved!" banner) missing | |
| Building hits don't pop crystals | |
| Pick tiers have no spark colour; ice upgrades don't change crystal colour (white, blue, gold) | |
| No model animation: hit motions, moving extras (gears, pistons, rune rings), Masterwork idle | |
| Crystal Ice sparkle rate isn't updated live when reduced effects is switched | |
| New layer: shake but no separate camera dip | |

### Gameplay and other

| Gap | Outcome |
|---|---|
| Masterwork name plate with the player's name missing | |
| Building badge shows "(detail/10)" rather than a star per upgrade | |
| Creature Book rewards: Mythic page aurora trail and Golden page golden pick skin are text only | |
| The next block slides in, but there is no sled object | |
| Pace targets (rebirth at 30-40 min) not re-checked since the level-31 change (Phase 4) | |
| Doc wording: "pet bonus speeds up every hit" / "Frost Cores make every block go faster", but pets and Frost Cores multiply crystals, not damage | |
| Space and gamepad A also make the character jump while tapping | |

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

**Icon drafts:** being rendered from the game's own models by a background agent into `store-assets/icons/`; committed when done (see the Phase 8 section).
