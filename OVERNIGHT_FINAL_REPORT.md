# Overnight final run (2026-11-26)

Branch `overnight-final` (from `main` at fca7285). Pushed after every phase; not merged.

## Summary

(written at the end of the run)

## Questions for you

(collected during the run; see the end of the run for the final list)

## Phase status

| Phase | State |
|---|---|
| 1. Regression play-throughs | Done |
| 2. Long-run stability | Running (3 players, 66 minutes) |
| 3. Live-ops readiness | Code and specs done; Studio checks after Phase 2 |
| 4. Price research | Done (report only) |
| 5. Final pre-publish audit | To do |
| 6. Visual pass prep | Tools written; screenshots to do |

## Visual changes made

None so far. New UI pieces for the new features (built from the UI kit): the "Updating the game" screen and the server message panel (`ServerNotices.client`).

## Decisions I made

- **Playthrough bot:** it follows the tutorial (equips its first pet at step 4) and then relies on auto-equip, instead of equipping by hand after every rescue as last time. A sensible player follows the arrow; the old bot's manual equip hid the auto-equip question below.
- **Studio test players for balance runs:** your account owns every pass now that the ids are real.
- **New debug actions** (F2), so tests and the visual pass can set things up exactly:
  - "Set one building's count and upgrades" (tiers and Masterwork);
  - "Set the current block's HP left" (crack stages);
  - "Daily chest: last opened yesterday";
  - "Analytics: send the target's batched crystal events now";
  - "Soft shutdown: show everyone the update screen" and "the 'update coming' warning".

  Each has spec checks.
- **New tool:** `tools/check_asset_ids.py`. It checks every asset id in the configs against Open Cloud (owner and moderation); `upload_models.py --check` only re-checks assets that weren't approved yet.

## Phase 1: regression play-throughs

### A fresh player to the first rebirth

A scripted new player played a fresh save as a Studio test player (Test > Clients and Servers), so it owned no passes. It:
- tapped 4 a second through the real tap remote;
- followed the tutorial (it equips its first pet when step 4 asks);
- bought whatever paid back fastest;
- redeemed ICELAUNCH and THAWED;
- relied on auto-equip after the tutorial;
- rebirthed as soon as it could.

The log is `docs/playthrough_2026-11-26.txt`.

| Milestone | Tonight | Last time (2026-11-25) |
|---|---|---|
| First building / first rescue / tutorial done (THAWED) | 0.5 min | 0.4 min |
| Layer 2 (Blue Ice) | 5.1 min | 4.4 min |
| First Rare or better | **24.8 min** (Frost Turtle) | 5.9 min |
| Layer 3 (Ancient Ice) | 16.4 min | 13.7 min |
| First rebirth (level 31) | **43.1 min, +4 Frost Cores** | 34.5 min, +5 |
| Onboarding funnel | all 7 steps, in order | all 7 |

**Why it was slower:** mostly luck. No Rare came until level 24, against level 13 last time. Players have one equip slot before rebirth ranks, so the equipped pet's bonus is a big share of income. At equal building counts, income was 4-25% lower than last time, and the gap closed once the Rare arrived.
- Rescue gaps at levels 21-30: 1.9-3.7 min, against 1.3-3.0 last time.
- I found no code change that slows the first run: the economy numbers are untouched, and auto-equip equips what EquipBest did.

**What this means:** a near-perfect player takes 34-43 minutes depending on pet luck; real players will be slower. Two proposals (questions below, nothing changed):
- a guaranteed Rare early, for example the first block of layer 2, to cut the luck;
- watching the live "First rebirth" funnel step before touching balance.

**Found:**
1. **Auto-equip never starts for a player who skips the tutorial's "Equip your new pet" step.**
   - Auto-equip waits for the tutorial (your decision), and the tutorial waits for a manual equip.
   - My first attempt tonight didn't equip by hand: after 13 minutes it had 4 pets and **0 equipped**, so the whole pet bonus was missing.
   - A real player follows the arrow, but one who closes everything and just taps would play without pets. A question below.
2. **Studio Play as you is no longer a normal player.** Since the passes have real ids, your account owns every pass, so a solo Play has 2x Crystals, VIP, Auto Pick, Lucky Ice and the slot passes. The first attempt tonight ran as you by mistake (layer 2 at 1.6 min) and was thrown away. For balance checks use Test > Clients and Servers (test players own nothing). This is noted in the visual pass guide too.
3. **Analytics, as a bonus check:** the new progression funnels (layers 1-4, then rank 1 at the rebirth) and the crystal economy events (codes, upgrades, buildings, rescues, taps) logged as designed. No errors or warnings in Output on the server or the client.

### A returning player

Studio test player, Studio save (no fresh save):
- **Session A:** set block level 25, bought 10 Heat Lamps and 10 Chisel Mills (90 crystals/s from buildings), and tapped the block a little. Left with the Seal Pup's block partly broken.
- **Session B:** StudioTimeAway = 2 hours.
- **Session C:** StudioTimeAway = 24 hours.

| Check | Result |
|---|---|
| Offline earnings after 2 h | **324,000 crystals** = 90/s x 3,600 s (50% of 2 h), popup shown, not capped (exactly at the cap) |
| Offline earnings after 24 h | **324,000, Capped = true**; the popup says "You were away for 1d. You earned: +324K crystals" |
| Rejoining mid-block | The same Seal Pup, its HP kept (lower by the buildings' damage since the last save) |
| Daily chest | First open **+28.2K** (300 s of steady income = 94/s x 300); again the same day: "Already opened today. Come back in 11h 8m." (nothing given); after the day change (new debug action "Daily chest: last opened yesterday"): **+28.2K** again |
| THAWED | First: "Code redeemed: 250 crystals!"; again: "You already redeemed that code." (nothing given) |
| ICELAUNCH | First: "Code redeemed: 500 crystals!"; again: "You already redeemed that code." |

**Found:**
1. **The welcome-back popup says "You earn for up to 1h while you're away."** The real rule is half your building income for up to 2 hours away (3,600 s of income at 50%), as the design doc says. So the line reads as if the cap were 1 hour away. A text fix is proposed in the questions; I didn't change it.
2. **The daily chest's prompt is switched off while the welcome-back popup is open.** That is by design (prompts are off while any window is open). A returning player has to close the popup first, which is natural, but it's why my first scripted try failed.

### Every reward kind through the simulated receipt (after tonight's changes)

As Player1 in a 3-player session, through the real receipt handler (F2 > Robux > Simulate a receipt):

| Item | Result |
|---|---|
| Crystal Pouch / Sack / Chest | PurchaseGranted: 2.4K / 14.4K / 86.4K crystals. A new player's steady income is 4/s x 600 / 3,600 / 21,600 s. |
| Shatter Now | PurchaseGranted: the Common block shattered |
| Server Frost Rush | PurchaseGranted: x2 for everyone for 15 minutes |
| Mythic Block | PurchaseGranted: waits for the next block |
| Lucky Ice pass as a gift to Player2 | PurchaseGranted, and Player2's `Owns_LuckyIce` turned false to true |
| Crystal Sack as a gift to Player2 | PurchaseGranted: 14.4K to Player2 |
| The same receipt again | "already granted, nothing given" |

The analytics IAP events showed for each bundle, including the gift to Player2.

## Phase 4: price research (report only; nothing changed)

Prices come from Roblox's public pass and developer-product lists for 12 games, fetched without logging in on 2026-11-26. The product lists still mark old items as for sale, so I used items updated in 2025-26 and marked older ones.

**Games** (players online when fetched):
- Pet Simulator 99 (PS99, ~100k)
- Bee Swarm Simulator (BSS, ~47k)
- Tap Simulator REBORN (TSR, ~43k)
- Bubble Gum Simulator INFINITY (BGSI, ~8k). Its passes are currently "[50% OFF]", so the full price is double.
- Rebirth Champions: Ultimate (RCU, ~5.7k)
- Muscle Legends (ML, ~2.7k)
- Arm Wrestle Simulator (AWS, ~1.4k)
- Race Clicker (RC, ~0.7k)
- Pet Simulator X (PSX, legacy)
- Strongman Simulator (SS)
- Clicker Simulator! (CS, a small 2026 game)
- Mining Simulator 2 (MS2)

PS99, BSS, TSR and BGSI have the most players, so they count most.

| Item type | Ours | What others charge | Median |
|---|---|---|---|
| 2x currency pass | 2x Crystals 249 | ML 249, RC 250, MS2 349, BGSI 399, RCU 399, SS 599 | 374 |
| Auto-tap pass | Auto Pick 149 | Two groups: SS 29, AWS 29, RCU 79, or PS99 350, RC 399, ML 499 | 214 |
| VIP pass | VIP 299 | AWS 219, BGSI 299, PSX/RC 300, MS2 349, PS99 400, RCU/SS 599 | 325 |
| Pet equip slots | +1 for 449, +2 for 899 | SS +1 399 / +2 899, ML +2 499 / +3 799, RC +2 700, TSR +1 249 / +3 749, RCU +2 199 / +3 399, CS +2 149 / +5 399, BGSI +3 299, MS2 +4 999 | ~250 per slot; ours is the highest at ~450 |
| Luck pass | Lucky Ice 349 | Entry tier: PS99 275, RC 250, TSR 249, CS 199, RCU 199, PSX 300, BGSI 399, MS2 499. Second tier: 399-800 | 262 for the entry tier |
| Currency packs | 29 / 149 / 499 (scale with income) | ML 14-2,199 (6 tiers), RC 45-2,250 (6), AWS 19-799 (6), SS 49/129/199, BGSI 19/174/319 | small ~22, medium 99-199, top 319-2,250 |
| Instant skip | Shatter Now 25 | RC 29, BGSI 29, PS99 79, TSR 49-299 (by length), ML 99, SS 99 | 39 for the cheapest skip in each game |
| Server-wide boost | Server Frost Rush 99 (x2, 15 min) | CS 79 / 199 / 499, AWS 79 / 395 / 949, SS 699-999 (1 h) | 79 for the cheapest in each game |
| Paid random roll | Mythic Block 199 | PS99 90, ML 99, CS 199, AWS 259, RCU 299, RC 399, TSR 399 (x1 eggs); x3 packs cost 2-3x, x10 packs 7.5-9x | ~259 |

**Proposed changes** (none made):

| Item | Now | Proposed | Why |
|---|---|---|---|
| 2x Crystals | 249 | **349** | The genre median is 374. It's our strongest pass, yet it costs less than VIP (+20%). |
| Auto Pick | 149 | **199** | Cheap next to PS99 (350) and RC (399). Stays mid-priced because buildings do most of the damage later on. |
| VIP | 299 | keep | On the median. |
| Extra Pet Slot | 449 | **399** | The highest price per slot found. Matches SS's +1. Our players start with only 1 equip slot (2-4 come from rebirth ranks), so one more slot is worth more here than in games that start with 3 or more; that argues against going below 399. |
| Pet Squad | 899 | **699** | Should be cheaper per slot than the single slot (350 against 399). RC's +2 costs 700. |
| Lucky Ice | 349 | keep | Between the entry luck tier (262) and the super tier (650-800). |
| Crystal Pouch | 29 | keep | Impulse tier. |
| Crystal Sack | 149 | **99** | At 149, an hour is only ~15% better value per minute than the Pouch. At 99 it's a clear step up, at a common price. |
| Crystal Chest | 499 | keep | Best value. Consider a 24-hour pack at ~999-1,199 as a top tier. |
| Shatter Now | 25 | **29** | 29 is the usual floor for a repeat skip. Later, the price could scale with block level. |
| Server Frost Rush | 99 | keep | In the entry band. Per minute it's cheaper than SS's 1-hour shared boosts. |
| Mythic Block | 199 | keep | Below the median, which is fair since it rolls ordinary creatures. Consider a 3-pack at ~499. |

**Where our shop is unusual for the genre:**
- Pet slots are expensive, and the 2-slot pass has no bulk discount.
- The 2x pass is cheap.
- The packs scale with income, which is rare and good: they never go stale.
- There are only 3 pack tiers, and no starter pack.

**Common patterns:**
- **Prices end in 9.** 81% of the 1,518 items for sale end in 9. The most common prices are 799, 399, 299, 199, 79, 599, 249, 149, 99 and 999.
- **Gift prices:** gifts cost the same as the item everywhere gifting exists, as ours do.
- **Luck ladders:** Lucky, then Super, then Hunter (for example TSR 249 / 799 / 1,999). The expensive top makes the middle look reasonable.
- **Bundles:** they show the saving (TSR's Pet Bundle: 1,349 against 1,426 bought separately).
- **Starter packs:** one per player (PS99 79 / 399 / 799, TSR 9-99).
- **Price testing:** PS99 sells the same offer at 9 / 29 / 49 / 99.

**How to change a price:** set the price on the Creator Hub, then change `ExpectedPrice` in `MonetizationConfig.luau` and the price in `docs/ROBUX_PRODUCTS.md`. Start a Play and check that PriceCheck shows 0 problems.

**Gaps in the data:**
- The lists show what is for sale, not what each game's shop actually displays, and they don't give boost durations.
- Fandom wikis refused automated fetches.
- The PSX server-boost reading is from memory.
- Prices are what a logged-out request saw; sales or regional pricing could change them.
