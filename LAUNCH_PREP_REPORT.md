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
| 2. Robux items | In progress | |
| 3. Gaps | Not started | |
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
| 2x Crystals pass missing (no config entry, no multiplier) | |
| Auto Pick pass missing (only the TapService.AddTaps hook) | |
| VIP pass missing (+20%, gold name tag); the lounge waits for it | |
| Extra Pet Slot and Pet Squad: configured with Id 0 (only ids are missing) | |
| Lucky Ice: odds logic exists, no pass, and IceBlockService.AddLuck is never registered | |
| Crystal bundles (income-scaled) missing | |
| Shatter Now product, the HUD offer and the bigger button on a Rare+ block: missing | |
| Server Frost Rush product missing | |
| Mythic Block product and its better-odds pool missing (PolicyService and the shop's odds panel exist) | |
| Gifting a pass missing (products only) | |
| Shop shows only 2 passes and no products | |

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
| HUD: Shatter Now offer missing | |
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
