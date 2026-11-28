# Overnight re-test run (2026-11-28)

Branch `overnight-retest` (from `main` at 7e93c1b). Pushed after every phase; not merged.

## Summary

(Written at the end of the run.)

## Questions for you

(None yet.)

## Phase status

| Phase | State |
|---|---|
| 0. Lighting note (Unified Lighting) | Done |
| 1. Rebirth and Welcome Back screens | Done: both screens, 17 icons (approved), Double Welcome Back created (3737277177) and tested, screenshots |
| 2. Play-throughs | Not started |
| 3. Long-run stability | Not started |
| 4. Saves | Not started |
| 5. Security | Not started |
| 6. Phones and performance | Not started |
| 7. Final pre-publish audit | Not started |

## Visual changes outside the two screens

None yet.

## Decisions I made

- `references/` is in `.gitignore` and was never staged.
- **Welcome Back: the base crystals are still paid at join** (as before). Claim! only closes the screen and the x2 offer; x2 pays the same amount again. So a player who closes the game on the screen loses nothing.
- **The x2 offer is bound to its purchase prompt.** Roblox never refunds an unresolved receipt (its docs: "not removed or refunded after the escrow period expires") and a receipt carries no custom data, so the receipt pays only an offer whose prompt was opened, its saved amount, once. A prompted offer waits a day for a late receipt (a server stop between the purchase and the grant) and a new payout doesn't replace it meanwhile. Remaining edge, accepted: a crash between purchase and grant AND the player staying away more than a day AND later buying a new x2: the old receipt would then pay the new offer's amount and the new receipt nothing.
- **The x2 offer lasts 10 minutes** after the payout (`WelcomeBackRules.Settings.OfferSeconds`).
- **Closing the Welcome Back screen any way (Claim!, X, B, a tap outside) closes the offer**, unless a purchase is running.
- **Double Welcome Back's analytics:** its crystals are an IAP "Bundle" source with Sku `DoubleWelcomeBack` (no new source name needed).
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
