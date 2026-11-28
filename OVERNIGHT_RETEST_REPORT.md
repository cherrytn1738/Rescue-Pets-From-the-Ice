# Overnight re-test run (2026-11-28)

Branch `overnight-retest` (from `main` at 7e93c1b). Pushed after every phase; not merged.

## Summary

All 8 phases are done, committed and pushed to `overnight-retest` (not merged). All 26 specs pass (8,093 checks).

- **New:** picture-first Rebirth and Welcome Back screens (17 new icons, all approved), and the 19 R$ **Double Welcome Back** (product 3737277177). Its receipt pays only an offer whose prompt was opened, once; tested with simulated purchases, a duplicate receipt and a purchase after the offer was gone.
- **Play-throughs:**
  - a new player reaches the first rebirth in 29.2 minutes (target 33-37; question 1);
  - Layer 6, a returning player (2 h and 24 h), every reward kind, and Auto Pick at 2 taps a second all work.
- **An hour with three busy players:** no errors, and nothing grew without a limit.
- **Security:** wrong and spammed input at all 15 remotes gained nothing.
- **Fixed:**
  - a rebirth threw away a bought Mythic Block;
  - a server could freeze working out Frost Cores for a huge run;
  - the codes list could outgrow what the save accepts;
  - the settings sliders could save an older value;
  - the x2 price badge covered the amount on phones;
  - notices left a dark ghost line as they faded (the one visual change outside the two screens);
  - the asset check skipped 46 ids (all fine).
- **Phones:** 60 fps in every view in Studio with 8 maxed plots at night. Fewer triangles than at launch prep, but more draw calls across the ring at night. Three phone risks are proposed, not changed (question 3), and the Pets window is cramped on a landscape phone (question 5).
- **Ready to publish** from tonight's side: the allowlists are right, no Studio switch is set, a clean Play has no game errors, the price check is 29/0, and all 249 asset ids are approved.
- **For you:**
  - answer the questions below;
  - try a real controller once;
  - merge the branch;
  - **save the place and keep a backup copy** (File > Save to File As...). The templates, the world and the lighting live only in the place file.

## Questions for you

1. **The first rebirth came 4 minutes early in the live run: 29.2 minutes against the 33-37 target (Phase 2).**
   - Reasons: the scripted player buys perfectly, the early Rare came at level 6, and your account most likely gets the +10% group bonus, which the economy simulation leaves out.
   - The simulation (4 taps a second, no group bonus) averages 34:47, inside the target.
   - **My suggestion: change nothing now.** After launch, watch how long real players take to reach "First rebirth" in the onboarding funnel.
   - If you'd rather slow it, the smallest lever is the block HP growth before level 31 (`LayerConfig.BlockHp`). Say so and I'll run the simulation first.
2. **Double Welcome Back keeps a bought-but-not-yet-granted x2 for a day** (`WelcomeBackRules.Settings.PendingSeconds`), so a receipt that arrives late still pays what was bought.
   - The one edge left: a server crash between the purchase and the grant, AND you away more than a day, AND you then buying x2 again. The old receipt would then pay the new amount, and the new receipt nothing.
   - OK as it is, or should the pending window be longer?
3. **Phone performance (Phase 6) has three proposals,** each of which changes how something looks:
   - with reduced effects on, skip the northern lights and lamp lights, and other plots' upgrade parts;
   - show fewer of other players' followers, and stop animating them sooner;
   - lower-detail station templates for other plots.

   Which, if any?
4. **The next screens to redesign the picture-first way:** the list in Phase 1 ("Other menus that are still text-heavy"). Which first?
5. **The Pets window on a landscape phone** shows only a 45 px sliver of the pet grid (Phase 6; the same on `main`). Two options:
   - with a short screen, shrink the slots row and the buttons (the slots to about 60 px, the buttons to about 44): the grid gets about one full row of cards;
   - move the slots into the grid's first row.

   I'd do the first. Say which, and I'll do it and retake the shots.
6. **By hand (no decision needed):** a real controller, once. Try PLOT, the Tools tab, buying a tool and a building, and x2 and Claim! on Welcome Back. Moving between buttons with the D-pad can't be driven from a script.

## Phase status

| Phase | State |
|---|---|
| 0. Lighting note (Unified Lighting) | Done |
| 1. Rebirth and Welcome Back screens | Done: both screens, 17 icons (approved), Double Welcome Back created (3737277177) and tested, screenshots |
| 2. Play-throughs | Done: first rebirth at 29.2 min, Layer 6, returning player, every reward kind |
| 3. Long-run stability | Done: 66 minutes, 3 players, no errors, nothing growing without a limit, no fix needed |
| 4. Saves | Done: every new field checked; a rebirth no longer loses a bought Mythic Block |
| 5. Security | Done: abuse at all 15 remotes gave nothing; 3 fixes (a frozen server on a huge run, the codes list, the settings sliders) |
| 6. Phones and performance | Done: 60 fps in every view with 8 maxed plots at night; 56 followers measured; gamepad pass; every window at both phone sizes (2 fixes, 3 older layout problems reported) |
| 7. Final pre-publish audit | Done: allowlists right, no switches, clean Play, PriceCheck 29/0, 249 asset ids approved, whole visual set retaken |

## Visual changes outside the two screens

- **Notices fade out cleanly** (`src/player/Banners.luau`). A toast's outline now fades with its text; before, the last half second of every notice showed a dark, unreadable copy of the line. That was a bug, found in the phone screenshots. Nothing else about the notices changed.

## Decisions I made

- `references/` is in `.gitignore` and was never staged.
- **Welcome Back: the base crystals are still paid at join** (as before). Claim! only closes the screen and the x2 offer; x2 pays the same amount again. So a player who closes the game on the screen loses nothing.
- **The x2 offer is bound to its purchase prompt.** Roblox never refunds an unresolved receipt (its docs: "not removed or refunded after the escrow period expires") and a receipt carries no custom data, so the receipt pays only an offer whose prompt was opened, its saved amount, once. A prompted offer waits a day for a late receipt (a server stop between the purchase and the grant) and a new payout doesn't replace it meanwhile. Remaining edge, accepted: a crash between purchase and grant AND the player staying away more than a day AND later buying a new x2: the old receipt would then pay the new offer's amount and the new receipt nothing.
- **The x2 offer lasts 10 minutes** after the payout (`WelcomeBackRules.Settings.OfferSeconds`).
- **Closing the Welcome Back screen any way (Claim!, X, B, a tap outside) closes the offer**, unless a purchase is running.
- **Double Welcome Back's analytics:** its crystals are an IAP "Bundle" source with Sku `DoubleWelcomeBack` (no new source name needed).
- **A rebirth keeps a bought Mythic Block that's on the mound** (Phase 4): the design doc already counted Robux items as kept, so the code now matches it, and the doc says so in words.
- **`tools/check_asset_ids.py` reads three more configs** (IceLooks, LightingConfig, SwingConfig), so the ice atlases, skyboxes and swing animations are checked too.
- **The Pets window's phone layout was left alone** (an older problem, and it isn't one of the two screens): it's a question instead.
- **The rebirth screen opens with the close button selected on a gamepad** (as built in Phase 1), not REBIRTH, so a pad player can't rebirth by accident.
- **New debug action "Simulate a purchase from the shop"** (prompt hooks, then the receipt), because Studio's own test prompt for a real id can't be clicked from a script, and Double Welcome Back's receipt pays only a prompted offer. The duplicate-receipt action replays its PurchaseId.

## Phase 0: Lighting note

- `LightingConfig.Style` holds the Unified Lighting settings: `LightingStyle = "Realistic"`, `PrioritizeLightingQuality = false`. A script can read and set both (checked in Studio: Edit mode reads Realistic / false, and writes go through), so `LightingConfig.Apply` sets them where they differ, at every server start, on each client at a look switch, and in Edit mode through `tools/studio/lighting.luau`. A Studio without the properties skips them quietly.
- `tools/studio/lighting.luau` no longer tries `Lighting.Technology` (reading it now fails: the property is gone) and reports the style instead. Run in Edit mode tonight: "lighting: PinkDusk, with its skybox / style: Realistic, PrioritizeLightingQuality false".
- AGENTS.md (the MCP notes and the `LightingConfig` line), `docs/LAUNCH_CHECKLIST.md` (the Technology box is now a ticked Unified Lighting line) and `docs/VISUAL_PASS_GUIDE.md` (the Lighting row; the "can't check Technology" note removed) say this instead of "Technology = Future". Nothing asks you to check Technology any more.
- Spec: `LightingConfig` +2 checks (the style values, Apply sets them).

## Phase 1: the Rebirth and Welcome Back screens

### Rebirth screen (`src/player/RebirthWindow.client.luau`)

Pictures first, built from the UI kit (ShowcaseKit cards, UIKit labels, bar and buttons) and the game's own icons:
- **Corner badge:** icy rebirth arrows round a Frost Core (`RebirthBadge`), popping in over the top-left corner.
- **Before → After:** two big gold cards, each a Frost Core and the crystal bonus from Frost Cores (`+0%` → `+1,670%`, `CRYSTALS` under it), and between them a white arrow with the Frost Cores this rebirth gives shown big (Frost Core icon + `+334`, cyan).
- **The rank, smaller:** a dark card with the current rank's badge and name → the rank after this rebirth (badge and name in the rank colour), then the next unlock as a picture (a pet slot and/or a layer) and "at Rebirth 6". Before the first rebirth it shows the plain "No rank" badge.
- **One red line,** "Resets crystals, buildings, upgrades and level!", with an icon for each (crystal pile, Build, Upgrades, ice block).
- **KEPT** with five icons, each with a green tick: pets, the Creature Book, Frost Cores, the rank badge, Robux items (a gift box).
- **The level bar:** "Level 12 / 31", filling to the rebirth level; full at 31.
- **A big green REBIRTH button,** grey and inactive until the bar is full. Pressed once it asks "SURE?" (or "0 CORES. SURE?"), as before, so a mashed A button never rebirths by accident; a gamepad still starts on the close button.
- Every number is from the player's server-published data and RebirthConfig, as before; the server does the rebirth.
- On a phone the BEFORE/AFTER headings go and the bar and the button sit side by side.

### Welcome Back screen (`src/player/OfflineEarningsPopup.client.luau`, window name kept)

- **Corner badge:** an ice-blue alarm clock with a snowflake (`WelcomeClock`); the huge "Welcome Back!" title; one line: "Your buildings broke ice while you were away:".
- **The middle:** a big crystal pile (`CrystalPile`) with gold rays (`Sunburst`) turning slowly behind it (one turn every 24 s), the amount in big gold numbers counting up in 0.9 s ("+5.17M CRYSTALS"), and the time away under it ("Away for 1h 30m", plus "(earns up to 2h)" when capped; this also answers last run's question 3 about the misleading cap line).
- **x2:** a shimmering rainbow button with the doubled total ("x2 +10.3M") and a small green Robux price pill (the live price from Roblox, 19). Buying it counts the amount up to double, plays the reward sound and closes the screen.
- **Claim!:** a big green button (Claim! alone and centred when there's no offer).
- Gamepad: starts on Claim!, never on the purchase.

### Double Welcome Back (the x2), 19 R$

- **Created on Roblox** by `python tools/create_products.py` (dry run first, then real): developer product **3737277177**, 19 Robux, on sale, with its own icon (`store-assets/icons/DoubleWelcomeBack.png`: the alarm clock behind a crystal pile, a gold "x2"). **No gift twin**: the doc's gift column says "(none: not giftable)" and the script now skips the twin for such a row. The id is in `MonetizationConfig` (`NoGift = true`, `ShopHidden = true`: not in the shop window, never giftable), `docs/ROBUX_PRODUCTS.md` and `products_manifest.json`. The design doc's Monetization table has its row.
- **Server:** `WelcomeBackRules` (pure) and `WelcomeBack` (the reward kind `WelcomeBackDouble`); `OfflineEarnings.OnPaid` saves the offer `{ Amount, At }` in the save at every payout; `PurchaseRewards` gained prompt hooks (`OnPrompt`, `OnPromptFinished`, `OnClose`) that the shop calls round Roblox's prompt; `RobuxShop` passes `{ Prompting = true }` to `CanGive` before a prompt and has a new request `CloseOffer` (Claim!). The receipt pays exactly the saved amount, once, only for a prompted offer, then removes it.
- **Tested in Studio Play** (debug "Simulate a purchase from the shop" runs the prompt hooks and then the real receipt handler; "Simulate a receipt" is a bare receipt):

| Test | Result |
|---|---|
| A payout makes the offer | `WelcomeBackOffer = {"Amount":3445200,"Until":...}`, x2 shown |
| A bare receipt with no prompt | NotProcessedYet: "the welcome-back offer was never prompted"; nothing paid |
| The simulated purchase | PurchaseGranted, gave exactly 3.45M (the saved amount); the offer gone |
| The same receipt again (duplicate) | "already granted, nothing given" |
| Buying again | refused: "There's no welcome-back reward to double." |
| A new offer, Claim! (the real button), then a purchase and a bare receipt | refused / NotProcessedYet "the offer is closed"; nothing paid |
| Gifting it (the shop's Gift request) | refused |
| The real x2 button with the real product id | Roblox's (Studio test) purchase prompt opened; the server marked the offer prompted; Escape cancelled it and x2 came back (the cancel path) |
| x2 bought with the screen open | the amount counted up to "+5.22M CRYSTALS", +2.61M crystals paid, the screen closed |
| 26 specs | all pass; new `WelcomeBack` spec (50 checks: the rules, the kind through the real PurchaseRewards and MonetizationConfig, a late receipt after a server stop pays what was bought and not the newer offer) |

### Icons (17 new, all uploaded as group 921449746 and approved)

Made with the icon pipeline in the game's style (`tools/icons/render_icons.py` builders, `compose_icons.py` UI specs; three are 2D): `RebirthBadge` (icy arrows round a Frost Core), `FrostCore`, rank badges `Rank0` (no rank), `Rank1`, `Rank2`, `Rank3`, `Rank6`, `Rank10` (one shield in the rank colours with 0-5 stars; Rank10 rainbow), `UnlockPetSlot`, `UnlockLayer`, `IceBlock` (level), `CrystalPile`, `RobuxItems` (gift box), `WelcomeClock`, `Sunburst`, `Tick`, `ArrowRight`. Ids in `UITheme.Icons`; contact sheet `store-assets/ui-icons/contact_sheet.png`. The kept row reuses the existing Pets and Book icons, the reset row the Build and Upgrades icons.

### Pop-in, sounds, sizes, gamepad

- **Pop-in:** the window's own pop, plus the corner badge, the cards, the cores, the rank row, the pile, its rays and the buttons popping in one after another (`ShowcaseKit.PopIn`).
- **Sounds:** the usual Open, Close and Click; Reward when the Welcome Back screen opens and again when x2 arrives.
- **Sizes:** desktop, 844x390 and 667x375 all fit with nothing cut off (screenshots below). On phones the Rebirth screen drops the BEFORE/AFTER headings and puts the bar beside REBIRTH.
- **Gamepad** (StudioGamepad): Welcome Back opens with Claim! selected, x2 sits to its left; B closes the screen (and closes the offer, like Claim!). Rebirth opens with the close button selected; REBIRTH is selectable. D-pad moves can't be sent from MCP (its keyboard D-pad doesn't drive Roblox's selection), so moving between the buttons with a real pad is a by-hand check.
- **The Welcome Back pictures load before the screen opens** (`ContentProvider:PreloadAsync`, at most 3 s, during the 1-second join pause): in the first screenshot the clock hadn't loaded yet.

### Screenshots

`store-assets/visual-review/screens-redesign/` (in the gallery, category "screens-redesign"): `rebirth_<size>_1_before`, `rebirth_<size>_2_after` (ready: rebirth 2 → 3, 12 Frost Cores, +14), `rebirth_<size>_3_after_no_cores_yet`, `welcome_back_<size>_1_before`, `welcome_back_<size>_2_after`, each at desktop, 844x390 and 667x375. The regular `ui/` shots (`window_rebirth`, new `window_rebirth_ready`, `offline_earnings_popup`) were retaken too.

### Other menus that are still text-heavy (suggestions only; nothing changed)

- **Build:** locked rows say "??? Keep earning crystals to find out..."; owned/damage lines are small text. A big building picture, a big price and a big "x12" owned number would do.
- **Upgrades:** every card has a description sentence ("Next block arrives 1 s sooner", "Rescue fountain: 45 s of income", "+10% crystals per damage"). A big "+10%" or "-1 s" number on the icon instead.
- **Creature Book:** "4/4 found on this page · book 50% complete" and "Reward earned: +5% crystals" lines, and "Rescued x1 · from Fresh Snow" on each card. A progress bar and a big "+5%" badge; the layer as a small ice-layer icon.
- **Pets:** the "1/4 equipped · pets give +1% crystals" line; the bonus could be a big "+400%" on each card (it already is) and a slot row of icons.
- **Shop:** pass cards carry a sentence each ("Doubles all your crystals, forever."). A big "x2" or "+1 slot" badge on the picture, with the sentence behind the INFO button.
- **Codes:** "Enter a code to get free rewards!" and "Codes aren't case-sensitive. Each one works once." could be one picture of a ticket.
- **Toasts and notices** ("Your Mythic Block arrived: a Rare creature is inside!") could lead with the rarity colour and an icon.

## Phase 2: play-throughs

### A fresh player to the first rebirth

A scripted new player (`StudioFreshSave` and `StudioIgnoreOwnedPasses` on: no passes), 4 taps a second through the real tap remote, following the tutorial, buying the best payback (buildings, upgrades and tools), redeeming ICELAUNCH and THAWED, using the PLOT button's remote from the plaza at minute 3, and stopping at the rebirth level so I could rebirth through the new Rebirth screen with real clicks. Full log: `docs/playthrough_2026-11-28.txt`.

| Milestone | Tonight | 2026-11-26 | 2026-11-25 |
|---|---|---|---|
| Tutorial done, first building, ICELAUNCH, THAWED | 0.3 min | 0.5 | 0.4 |
| Tools: Stone Hammer / Copper Axe / Iron Pick / Steel Sword | 0.2 / 2.0 / 3.9 / 6.5 min (levels 1, 6, 10, 14) | (no tools then) | |
| Frost Spear / Gold Hammer / Crystal Axe / Ice Drill | 9.7 / 11.7 / 12.9 / 15.2 min (levels 18, 20, 21, 23) | | |
| Diamond Sword / Flame Pick / Thunder Hammer / Aurora Blade | 17.9 / 19.6 / 22.7 / 24.6 min (levels 25, 26, 28, 29) | | |
| Layer 2 (Blue Ice) | 4.5 min | 5.1 | 4.4 |
| First Rare or better | **5.8 min** (level 6) | 24.8 | 5.9 |
| Layer 3 (Ancient Ice) | 13.0 min | 16.4 | 13.7 |
| Rebirth ready (level 31, Layer 4) | **29.2 min, +5 Frost Cores** | 43.1 (+4) | 34.5 (+5) |
| PLOT button from the plaza (minute 3) | landed on its own plot's tapping spot (z = 151, plot 1) | | |
| First rebirth through the new screen | REBIRTH → "SURE?" → reborn, +5 Frost Cores, the frost-over and the banner | | |
| Onboarding funnel | all 7 steps in order (Joined, First tap, First building, First rescue, First pet equipped, Tutorial done, First rebirth) | 7 | 7 |

- **Against the 33-37 minute target: 29.2 minutes, about 4 minutes fast** for a near-perfect player. The early Rare guarantee (first Rare at level 6) took the luck out (last run waited until level 24). Real players are slower than this bot, so I changed nothing; a proposal is in the questions.
- **Nowhere stuck:** no "saving up for 4+ minutes" line all run; rescues came every 0.3-2.5 minutes, the slowest at levels 28-30. The tutorial's step 3 (free your first creature) passes in seconds. Auto-equip kept the best pet in the one slot.
- **No errors or warnings** from the game in Output.

### A later run: rebirth 3, into Layer 6

A fresh save set to rebirth 3 (Layer 6 open), tool 13, 900 billion crystals:

| Check | Result |
|---|---|
| Lava Axe (14), Starfall Spear (15), Comet Hammer (16), Cosmic Pick (17) | each **refused one level below its unlock level** ("Reach level 33/37/41/45") and **bought at it** |
| Starbreaker (18) at level 45 | refused ("Reach level 48") |
| Block HP at levels 39 / 40 / 41 / 42 / 50 | 4.914e8 / 7.372e8 / 8.993e8 / 1.097e9 / 5.385e9, exactly `LayerConfig.BlockHp`; growth **x1.50 up to 40, then x1.22** |
| Level 51 | the block is Layer 6, Frozen Core (attributes Layer 6, Level 51) |
| Five rescues at levels 51-55 | Frost Turtle, Seal Pup, Polar Bear Cub, Frost Turtle, Snow Bunny: all from Layer 6's pool |
| A Mythic (Aurora Fox) Layer 6 block | the black Frozen Core ice with orange veins, the creature's outline and yellow eyes, its glow and sparkles, the gold Shatter Now button; checked in a screenshot |

At level 51, 75 seconds of tapping with the Cosmic Pick (8 taps a second) didn't break a block (6.6 billion HP); that's expected without buildings, so the rescues above were forced through the server's real shatter.

### A returning player (your Studio save, owned passes ignored)

| Check | Result |
|---|---|
| Codes (after "forget my codes") | THAWED: 250 crystals, then "You already redeemed that code."; ICELAUNCH: 500, then "icelaunch" refused as already redeemed |
| Daily chest | +249K; same day "Already opened today. Come back in 11h 31m."; after the day change (debug) +249K again |
| Away 2 hours | **+2.61M** (725/s building income x 3,600 s = 50% of 2 h), not capped; the new Welcome Back screen showed "+2.61M CRYSTALS", "Away for 2h" and "x2 +5.22M" |
| Claim! (a real click) | the screen closed, the offer closed on the server; a purchase after it was refused |
| Away 24 hours | **+2.61M, capped**; "Away for 1d (earns up to 2h)" |
| x2 (a real click on the real product) | Roblox's purchase prompt opened (Studio's test prompt); cancelling it (Escape) brought x2 back; then the purchase (simulated, real receipt handler) paid +2.61M, the screen counted up to +5.22M and closed |
| Rejoining mid-block | the same Crystal Stag came back, its HP kept (1.99189e9 of 1.99232e9), and **its Mythic Block look kept** (`MythicBlock` true) after two rejoins |
| A save with old IcePick ids | **couldn't be checked live:** Studio refuses DataStore writes from Edit mode ("Access forbidden"), and a write during Play is overwritten by the session's own save. The migration is covered by the PlayerData spec (an old save with IcePick4 loads as every tool up to the Gold Hammer, through the real load path) |

### Every reward kind through the simulated receipt (the real receipt handler)

| Item | Result |
|---|---|
| Crystal Pouch / Sack / Chest / Giant Chest | PurchaseGranted: 508K / 2.99M / 17.9M / 71.7M |
| Shatter Now | PurchaseGranted: the Common block shattered |
| Server Frost Rush | PurchaseGranted: x2 for everyone, 15 minutes |
| Mythic Block x3, then the same receipt again | 3 waiting; the duplicate: "already granted, nothing given", still 3 |
| Lucky Ice, as a gift to themselves (its gift product) | PurchaseGranted; `Owns_LuckyIce` true |
| Double Welcome Back (with an offer), then a duplicate | PurchaseGranted 2.87M; the duplicate gave nothing |
| Mythic Block | PurchaseGranted (4 waiting); the next block rolled from its odds (an Epic Crystal Stag with the Mythic look) and kept the look through two rejoins |
| **Auto Pick** | **2.00 taps a second** (measured from the block's HP with a 2,000-damage tool, buildings subtracted); with my own taps far over the cap on top: 10.5 a second over 15 s (the cap of 10 plus the bucket's first 10) |

Found while doing this (fixed, see Phase 4): a rebirth with a bought Mythic Block still on the mound rolled it away.

## Phase 3: three players for an hour

A Studio test with 3 players on fresh saves, sampled every 3-4 minutes for 66 minutes, the fast day-night cycle on all the time (it went round the three looks many times). A bot on each client did everything at once:
- tapped 15 a second, over the cap of 10;
- bought buildings and upgrades (about 3,000 purchases each);
- rebirthed every 9 minutes (12 rebirths each);
- forced each rarity in turn every 150 s, Legendary and Mythic included (305 rescues each);
- joined and spawned Golden Glaciers (25-29 each, about 8,270 glacier taps);
- pressed PLOT every 5 minutes and walked to the other plots;
- deleted pets, and opened and closed every window in turn.

**Nothing kept growing without a limit, so nothing needed fixing.** The numbers (the clients as the range over the three):

| Minute | Server memory MB / Lua heap MB / Workspace | Clients memory MB | Clients Lua heap MB | Clients Workspace | Clients PlayerGui | Clients' followers and effects |
|---|---|---|---|---|---|---|
| 0 | 2,007 / 10.7 / 2,256 | 1,967-2,050 | 8.0-12.5 | 3,472-3,696 | 1,835-2,130 | 659-905 |
| 10 | 2,048 / 11.1 / 2,368 | 2,049-2,104 | 8.0-10.8 | 3,704-3,960 | 1,835 | 668-913 |
| 21 | 2,057 / 11.6 / 2,741 | 2,096-2,147 | 10.1-11.4 | 4,170-4,448 | 7,152-7,777 | 718-1,003 |
| 31 | 2,031 / 7.1 / 2,878 | 1,903-2,138 | 10.0-10.5 | 5,067-5,226 | 7,998-8,623 | 1,305-1,468 |
| 42 | 2,043 / 7.5 / 2,104 | 1,955-2,165 | 9.2-9.8 | 4,774-4,777 | 8,625-9,250 | 1,975 |
| 52 | 2,024 / 7.9 / 2,621 | 1,945-2,162 | 9.9-10.5 | 5,303-5,416 | 8,625-9,250 | 1,987-2,059 |
| 63 | 1,854 / 8.5 / 2,391 | 1,868-2,165 | 10.4-11.3 | 5,681-5,760 | 8,753-9,315 | 2,694-2,748 |

What the growing columns are:
- **Clients' Workspace** grew only by `ClientEffects`. At the end, that folder held the 12 pets following the players (4 each: the rebirth ranks had opened pet slots, and auto-equip had picked the best creatures: an Aurora Fox is 237 instances, a Spirit Whale 197). The rest of the Workspace stayed at about 3,000 (2,916 at the start, 3,005 at the end). The cap is 7 followers per player. Rescue models, chips and confetti came and went: a rescue model seen once was gone seconds later.
- **PlayerGui** jumped each time a window was opened for the first time:
  - Pets at minute 17 (+5,400: a card per pet, at most 50);
  - Book at minute 24;
  - Rebirth at minute 31.

  It stayed at about 9,300 once every window had been built.
- **Client memory** rose by 100-120 MB in the first 35 minutes (more creature models and textures, the windows), then levelled off. For example, Player 3 went from 2,149 to 2,165 MB between minutes 35 and 63.
- **Server Lua heap** rose by 0.045 MB a minute in both stretches (minutes 0-21 and 24-63). The collector's one full pass, at minute 24, brought it down to 6.7 MB, below the 10.7 MB at the start: garbage waiting to be collected, not a leak.
- Sounds: 79 on each client at the start and at the end.

**Script errors:** 0 on the server and on every client in each 10-minute count. Output was free of errors and warnings on all four at the end.

**Remote traffic** (RemoteEvents client to server, counted on the server):
- TapBatch: 46,462, about 4 a second per player (the client batches its taps);
- GoldenTap: 8,268;
- GoHome: 154;
- ShopVisit: 6.

Server to each client: GameEvent about 3,200 in the hour (under 1 a second).

**DataStore budget:**
- UpdateAsync: 714 calls in 62.4 minutes with 3 players, 11.4 a minute (3.8 per player). The budget left kept rising (11,076 UpdateAsync left at the end).
- GetSortedAsync: 1.6 a minute.
- Leaderboard writes: 0. That's expected: fresh test saves are throwaway records, and `LeaderboardService.Write` skips those.

**Per-frame systems** (MicroProfiler through LibMP, each script's own time, averaged over a capture at the end with all 12 followers out):
- Client: 1.29 ms of scripts per frame in a 16.7 ms frame (60 fps held). The biggest are:
  - PetFollow: 0.29 ms (about 0.024 ms per follower);
  - ClientMain: 0.25 ms (the ice blocks, tap feedback);
  - HUD: 0.09 ms;
  - NameTags: 0.07 ms;
  - BuildingEffects: 0.04 ms.
- Server: 0.19 ms per frame for ServerMain (everything) with three bots tapping 15 a second.

**For Phase 6:** a full server is up to 56 followers. That's about 13,000 client-side parts, plus about 1.4 ms of PetFollow a frame on a desktop. This is the biggest per-player cost found, so Phase 6 measures it on purpose.

## Phase 4: saves

(Committed before Phase 3's results: the 66-minute run was still going.)

| Field (added since the last test) | Survives a rejoin | Survives a rebirth | Bad values cleaned | Where it's checked |
|---|---|---|---|---|
| `CurrentBlock.Mythic` | yes (spec; live: a Mythic Crystal Stag through two rejoins) | **now yes** (it was lost: fixed below) | anything but `true` dropped, the block kept | PlayerData, World specs |
| `BookGolden` | yes | yes (kept) | unknown creatures and non-`true` dropped | PlayerData, World |
| `BookNew` (incl. `Golden:<id>`) | yes | yes | repeats, unknown ids, junk dropped | PlayerData, World |
| `Settings` (Music, Sounds, ReducedEffects, AutoEquip, DayNight) | yes, incl. AutoEquip and DayNight off | yes | **new checks:** NaN volume → full, negative → 0, infinite → full, a switch that isn't a boolean → its default (on); not a table → defaults | PlayerData, World |
| Tool ids (`Tool2`...`Tool18` in `Upgrades`) | yes | reset with upgrades (by design) | unknown and repeated ids dropped; old `IcePick<n>` ids become every tool up to the matching one | PlayerData, Pick |
| `WelcomeBack` (the x2 offer) | **new:** a prompted offer saved and loaded exactly | **new:** kept through a rebirth | **new:** unreadable → no offer (a string, NaN, infinite or non-positive amount, a fractional time, a non-whole Prompted) | PlayerData, World, WelcomeBack |
| A debug reset | | | keeps a prompted offer (a purchase may be on its way), drops an unprompted one | PlayerData |

**Fixed: a rebirth threw away a bought Mythic Block still on the mound.** A rebirth resets the block, so a Mythic Block (bought with Robux, rolled into the current block) that wasn't broken yet was simply re-rolled as an ordinary block. Now `RebirthService.Apply` keeps it: the same creature, Mythic look kept, at level 1's HP (`IceBlockService.Refresh` shows it instead of rolling a new one). An ordinary block is still rolled again. World spec +2 checks.

The IcePick-to-Tool migration can't be checked live (Studio refuses DataStore writes from Edit mode, see Phase 2); the PlayerData spec loads an old save holding `IcePick4` through the real load path and gets every tool up to the Gold Hammer.

Specs: 26 of 26 pass (8,093 checks).

## Phase 5: security

A solo Play on a fresh save (1M crystals and three pets given first), with a client script firing wrong types, NaN, ±infinity, huge strings, other players' ids, bursts and spam at every client-to-server remote.

**Nothing was gained.** Crystals fell only by one valid "Max" building purchase, plus the 250 of the one code redeemed once. The pet count fell by one valid delete. Frost Cores, rebirths and upgrades didn't change. Output stayed free of errors.

| Remote | Kind | Server checks | Rate limit | Tonight's abuse, and the result |
|---|---|---|---|---|
| `DebugRequest` | Function | **Access first:** everyone in Studio; live, only `DebugConfig.AllowedUserIds` (empty). Then every input against the action's `Params` (type, range, choice) | 1 per 0.1 s per player | (Checked in the earlier runs; the live list is still empty, see Phase 7) |
| `AdminRequest` | Function | **Access first:** live, only 11704150663. Then the command's arguments (a target in this server, a filtered message) | 1 per 0.5 s per player (`AdminConfig.RequestCooldownSeconds`) | (as above) |
| `TapBatch` | Event | A whole number 1-1,000; standing in your own plot | **One bucket shared with GoldenTap: 10 taps a second, holding 10** | NaN, ±inf, -5, 2.5, 0, "10", a table, nil, true, 1e308: no damage. 165,000 taps asked in 10 s: 109 counted (10.9/s). 20 batches from the plaza: no damage |
| `GoldenTap` | Event | A Golden Glacier active; a whole number 1-1,000; near it | the same bucket | NaN, inf, -1, "x", a table (no glacier up): ignored |
| `BuyBuilding` | Function | A known building id; amount 1, 10, 100 or "Max"; the cost from the save, paid from the save | 1 per 0.1 s (shared with BuyUpgrade) | Amounts NaN, 5, -1, inf; ids "x", a table, nil: all "Unknown building". 20 at once with crystals: 1 bought, 19 "Slow down" |
| `BuyUpgrade` | Function | A known upgrade id; its unlock (the tool before it, the building it needs); not owned yet; the price from the config | the same | Tool18, Tool3 (not unlocked), FrostTouch1 (no crane), "NoSuch", 5, NaN: refused. The same tool 10 at once: 1 bought, 9 "Slow down", then "Already owned" |
| `PetRequest` | Function | A known action; uids you own; no repeats; a rarity name; a lock, combine or equip within your own pets and slots | 1 per 0.15 s | Delete { u, u } refused; delete a sparse list: only your own first pet; Equip, Delete and Lock with other uids, a 5,000-character uid, a table: refused; CombineGolden without 5: refused; DeleteBelow NaN: refused |
| `PurchaseRequest` | Function | A known action and product key (≤ 32 characters); the reward kind's CanGive before Roblox's prompt; gifts: another player in this server | 1 per 0.5 s, and one prompt at a time (30 s lock) | x2 without an offer: refused; CloseOffer on another product: "Nothing to close"; gift to yourself, a NaN or 1e300 id, a non-giftable product: refused; a 33-character key, a table, an unknown action: "Unknown request" |
| `RedeemCode` | Function | A string, trimmed and capped in length; upper case letters and digits; each code once per player | 1 per second, 6 a minute | 100,000 spaces, a table, NaN: "Type a code first"; THAWED twice: once |
| `RebirthRequest` | Function | "Rebirth" only; level 31 or more | 1 per 2 s | Below 31: refused; another action: refused; again within 2 s: "Slow down" |
| `SaveSettings` | Event | A table; both volumes numbers (NaN refuses the save, others clamped to 0-1); every switch a boolean or absent | 1 per 0.5 s | NaN volume: refused; inf / -1: saved as 1 / 0; "yes" or "off" for a switch: refused; a string: refused |
| `GoHome` | Event | A plot, a live character, not jailed | 1 per 3 s (`GameConfig.Teleport`) | 30 presses from the plaza: 1 teleport; 10 more within 3 s: none |
| `ShopVisit` | Event | "Robux" only; a known action; a known item key ≤ 32 characters; one visit at a time (analytics only, gives nothing) | 1 per 0.2 s, 40 a minute | Open, 100 Info, 20 Open in one frame: 1 "Opened shop" logged, the rest dropped; arguments in the wrong order: ignored |
| `GameEvent`, `PurchaseNotice` | Event (server to client) | The server connects an empty handler, so anything a client fires at them is dropped | | Fired at the server: nothing happened |

**Fixed (found by reading the handlers for this phase):**
- **A frozen server on a huge run.** `RebirthConfig.FrostCoresFor` corrects the cube root with `while (cores + 1) ^ 3 <= units do cores += 1 end`. Past 2^50 cores (about 10^51 crystals in a run), adding 1 doesn't change a double any more, so the loop never ended and the server would hang on the rebirth screen's preview or the rebirth itself. It now stops nudging that far out, and returns 0 for NaN or anything that isn't a number. The economy doesn't reach 10^51 in normal play, but the debug menu's "Set crystals" can, and it would freeze the test server. Spec +6 checks.
- **More than 200 redeemed codes.** The save keeps the most recent 200 (`MAX_CODES` at load), but `CodeService` let the list grow past that, which the save's check would refuse. It now trims to 200 at once, like the load does. Codes spec +1 check (59).
- **Settings sliders could lose the last change.** The window sent a save on every slider step, and the server takes one save every half second, so a quick drag could end with an older value saved. The window now waits 0.6 s after the last change and sends the latest (no change to how it looks).
- AGENTS.md said the debug menu takes "about one request a second"; it is one every 0.1 s (`DebugConfig.RequestCooldownSeconds`). Text fixed.

## Phase 6: phones and performance

### Performance

**Setup:** a solo Play on this PC, Studio in front, at night (the most lights: 48 lamps, the northern lights). The other 7 plots were maxed dummy plots (debug "Fill every empty plot": every building and upgrade, block level 400, Layer 6), and every block on all 8 plots was Legendary or Mythic (8 of 8 glowing). Camera views:
- the plaza;
- across the ring;
- the tapping spot.

Each view was sampled for 6 s, plus 4 s across each look switch. Studio caps at 60 fps, so the render CPU and GPU times say more than the fps.

| View | Reduced effects | fps (worst frame) | Render CPU | GPU | Triangles | Draw calls |
|---|---|---|---|---|---|---|
| Plaza | off | 60 (34 ms) | 12.8 ms | 1.6 ms | 557k | 667 |
| Across the ring | off | 60 (22 ms) | 13.8 ms | 1.8 ms | 1,141k | 882 |
| Tapping spot | off | 60 (22 ms) | 11.8 ms | 1.3 ms | 38k | 172 |
| Switch night → day | off | 60 (23 ms) | 11.9 ms | 2.7 ms | | |
| Switch day → night | off | 60 (28 ms) | 12.1 ms | 3.3 ms | | |
| Plaza | on | 59 (28 ms) | 13.3 ms | 1.6 ms | 557k | 673 |
| Across the ring | on | 60 (20 ms) | 13.8 ms | 1.8 ms | 1,141k | 882 |
| Tapping spot | on | 60 (24 ms) | 11.7 ms | 1.3 ms | 37k | 166 |
| Switch night → day | on | 60 (22 ms) | 11.8 ms | 2.7 ms | | |
| Switch day → night | on | 60 (25 ms) | 12.4 ms | 3.4 ms | | |

**Followers (the cost Phase 3 pointed at):**
- My player with the most a player can have (7 Spirit Whales: rank 10 and both slot passes): 1,372 instances.
- Then 49 copies round the plaza and my plot, so 56 in all (a full server). That added 9,700 instances, 28k triangles and 34 draw calls, and render CPU went up 0.4 ms (plaza: 13.8 → 14.1 ms, 58.6 → 57.2 fps).
- The copies stand still, so PetFollow's animation (0.024 ms a follower here, Phase 3) comes on top: about 1.4 ms a frame for 56 on this PC.

**Memory, the game's own share:** textures 123 MB, particles 27 MB, sounds 13 MB, mesh parts 3 MB. Studio's total (3.1 GB) and its Lua heap (1.3 GB) are mostly Studio and its plugins, so they say little about a phone.

**Against the launch-prep measurement** (daytime, before streaming and Automatic render fidelity):
- triangles at the plaza: 821k → 557k; across the ring: 1,323k → 1,141k;
- render CPU 2-3 ms lower in every view;
- the views that ran at 51-58 fps then all hold 60 now;
- one figure went up: draw calls across the ring at night, 690 → 882, likely the night lamps and the northern lights;
- textures went up from 65 to 123 MB (an atlas per layer, three skyboxes, the new icons).

**Reduced effects changes almost nothing here** (draw calls -0 to -6), as before. The cost is geometry and lights, not particles.

**Phone risks (proposals only; each one changes how something looks, so nothing was changed):**
1. **Across the ring at night: 1.1M triangles and 882 draw calls.** A mid-range phone will drop frames there. Ideas:
   - with reduced effects on, skip the northern lights and the lamps' lights;
   - with reduced effects on, show other plots' stations without their upgrade parts;
   - a lower-detail copy of each station template for other players' plots.
2. **56 followers in a full server: about 13,000 parts, plus their animation.** Ideas:
   - with reduced effects on, show only your own pets and those of players near you;
   - stop animating followers beyond 100 studs (today: 220).
3. **Textures, 123 MB:** fine for most phones; keep an eye on it as layers are added.

Looking at a busy server on a real phone is in `docs/LAUNCH_CHECKLIST.md`.

### Gamepad

With `StudioGamepad` on and the keyboard tool sending pad buttons:

| Check | Result |
|---|---|
| R2 taps | 5 presses, 5 taps (the block lost 5 HP with a 1-damage tool) |
| A taps in your plot | 3 presses, 3 taps; no tap while a button is selected |
| D-pad left with nothing selected | selects the first HUD button (Build) |
| Every HUD button selectable | all 9, PLOT included |
| Upgrades window | opens with its first tab selected, inside the window; the Upgrades, Tools and Owned tabs selectable; on the Tools tab, all 22 buy buttons selectable; a selected button lifts (scale 1.05) and carries the gold `SelectionRim` |
| Build window (buying) | opens with the first amount tab selected; 4 amount tabs and 8 buy buttons selectable |
| Robux shop (buying) | opens on the Passes tab; both tabs and 14 buy buttons selectable |
| B | closes each window; the selection goes back to the HUD |
| The two new screens | Phase 1: Welcome Back opens with Claim! selected, x2 to its left; Rebirth opens with the close button selected, REBIRTH selectable |

**What couldn't be checked from a script:** Roblox's own selection doesn't react to pad buttons sent this way. Simulated D-pad presses don't move between buttons, and a simulated A doesn't press the selected button. So "A on PLOT", "A on a buy button" and the D-pad moving between cards need a real controller. In the same way, the gold rim didn't show in the screenshot (Roblox probably draws it only while a real pad is in use). Everything the game's own code handles (taps, D-pad left, B, the first selection, every target selectable) works. **Please try a real controller once:** PLOT, the Tools tab, buy a tool and a building, the x2 and Claim! on Welcome Back.

### Every window at 844x390 and 667x375

These are from the Phase 7 retake: every window and each of its tabs, the HUD, the tutorial steps, the offers and the notices, at both phone sizes (contact sheets checked one by one).

**Fixed:**
- **Welcome Back: the "19" Robux badge covered the end of a long x2 amount** ("x2 +2.07M") on both phones. The x2 caption now keeps clear of the badge (it centres in the space left of it, and shrinks if it must). This is part of tonight's new screen. Retaken: clear at both sizes.
- **Notices left a dark ghost when fading out.** The toast faded its text but not its outline, so for the last half second each line showed as dark, unreadable outlined text (seen on the phone shots, where the announcement repeats). The outline now fades with the text (`Banners`). Listed under visual changes.

**Older layout problems (the same on `main`; not changed, a proposal in the questions):**
- **Pets window on a landscape phone:** the slots row, the summary and the five buttons keep their full size. That leaves the pet grid about 45 px tall at 844x390 (less at 667x375), so a pet card is never fully visible; you only see the tops of the cards and have to scroll.
- **Upgrades > Tools at 667x375:** the cards' buy buttons sit just below the fold until you scroll.
- **Upgrades > Owned with nothing owned** is an empty box: there's no "nothing yet" line.

**Everything else fits at both sizes:** HUD, Build (4 tabs), Upgrades, Book (7 tabs; short tab names at 667x375), Shop (2 tabs), Codes, Settings, Rebirth (both states), Welcome Back, the shatter offers, the Golden Glacier bar, the server notices, the update screen and every tutorial step. Nothing is off screen or overlapping a button, except where a shot caught a passing moment (a Book card or a "Page complete!" banner from a rescue during the shot, a layer banner).


## Phase 7: final pre-publish audit

| Check | Result |
|---|---|
| `DebugConfig.AllowedUserIds` | **empty** |
| `AdminConfig.AllowedUserIds` | **only 11704150663** |
| Studio test switches | **none set** (Workspace has no attributes; `StudioFreshSave` and `StudioIgnoreOwnedPasses`, used tonight, are cleared; `StudioGamepad` was only ever set on a Play client). `ProximityPromptService.Enabled` is on. |
| A clean Play (no switches, your Studio save) | **no errors or warnings from the game.** Output: `[Server] started`, `[Client] started`, `[HUD] ready`, the save LOADED from `IcePets_PlayerData_Studio`, an offline payout, the price check. The only other lines are from outside the game (next row). |
| Lines not from the game | `rbxassetid://203785492 failed: Asset type does not match` three times per Play. Nothing a script can read refers to it: a search of every service on the client and the server, plus the repo, finds nothing. It also showed in the earlier runs, so it's Studio or a plugin. Also Studio's Assistant plugin: "plugin version changed... restart Roblox Studio" (an MCP note, not the game). |
| `[PriceCheck]` | **29 items checked, 0 problems, 0 hidden** |
| `python tools/check_asset_ids.py` | **249 ids, 248 group-owned and approved, 0 problems** (+1 public library image). The check missed 46 uploaded ids (IceLooks: the ice atlases and kit; LightingConfig: the three skyboxes and the aurora; SwingConfig: the swing animations). It reads those configs now, and all 46 are the group's and approved. |
| ServerStorage | only the five template folders the code uses: BuildingTemplates (8), ToolTemplates (18), IceTemplates (1), PlotTemplates (4), PlazaTemplates (3). Nothing unused. |
| Docs against the code | `GAME_DESIGN.md`: the rebirth section now says a bought Mythic Block survives a rebirth (the Phase 4 fix; "Robux items" were already listed as kept). AGENTS.md: the debug rate (Phase 5). `LAUNCH_CHECKLIST.md`: the asset check's new count, both allowlists checked, and a new line for a phone in a busy server. |
| Specs | **26 of 26 pass (8,093 checks)** at the end of every phase |
| Visual review | **the whole set retaken:** 482 pictures in 41 minutes, 0 failed, 0 blank. Then the two fixed shots were taken again (Welcome Back, the rare-block notice). The 80 pictures not retaken are records, not shots: the ice-options part 1 record, the old lighting comparisons and tonight's Phase 1 before/after set. Before/after: `store-assets/visual-review/index.html` (old pictures in `store-assets/visual-review-before/`, which stays out of Git, 110 MB) |

**What to look at by eye in the new set:**
- `screens-redesign/`: the two new screens, before and after, at three sizes;
- `ui/offline_earnings_popup*` and `ui/window_rebirth*`;
- `ui/window_pets_844x390` (the cramped grid in question 5);
- `day-night/` (unchanged code, retaken).

Some shots caught a passing moment from the shot before: a Book card, "Page complete!", a layer banner, or a Golden Glacier that had already melted (`ui/golden_glacier_tap_bar_844x390`). The game is fine there; retake one with `python tools/visual_review.py --only ui/<name>` if you want a clean picture.
