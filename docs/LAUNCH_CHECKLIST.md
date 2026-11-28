# Launch checklist

Every step you do by hand to launch Rescue Pets From the Ice, in order. Tick each box as you go. Ids, keys and prices are in `docs/ROBUX_PRODUCTS.md`; the game is universe 10778596196, start place 88645847284794, owned by group 921449746.

## 1. Before you start

- [x] Merge the `overnight-launch-prep` branch into `main` (done in the launch fix pass). Pull, and make sure `rojo serve` is running and the Studio plugin is connected.
- [ ] Save the place in Studio and keep a backup copy of the `.rbxl` (File > Save to File As...). The building, pick, plot and plaza templates, the world and the streaming settings live only in the place file.
- [ ] Merge the `overnight-retest` branch into `main` (2026-11-28: the new Rebirth and Welcome Back screens, Double Welcome Back, Unified Lighting, fixes from the re-test; `OVERNIGHT_RETEST_REPORT.md`).
- [ ] Run every spec: `python tools/run_specs.py` (Studio open in Edit mode). All 26 must pass.
- [x] Merge the `overnight-final` branch into `main` (merged 2026-11-26: soft shutdown, announcements, analytics, the visual review tools).
- [ ] Workspace attributes: none of the Studio test switches may be set (`StudioFreshSave`, `StudioUseLiveSaves`, `StudioTimeAway`, `StudioPaidRandomRestricted`, `StudioIgnoreOwnedPasses`), nor the day-night debug ones (`DayCycleLook`, a `DayCycleSpeed` other than 1: they are set by the server at start, never saved on purpose); the client switches `StudioScreenSize`, `StudioGamepad` are never saved. Check Workspace > Attributes is empty of them.
- [ ] `ProximityPromptService.Enabled` is ticked (it is saved with the place; the UI kit turns it off while a window is open in Edit mode).

## 2. Robux items (all 29 created)

- [x] All 29 items (6 passes, 9 products, 14 "Gift: <name>" products) were created on sale through Open Cloud by `python tools/create_products.py` on 2026-11-26 (the Giant Crystal Chest and the Mythic Block x3 later the same day; Double Welcome Back, 19, on 2026-11-28, with no gift twin), with the icons from `store-assets/icons/`. Their ids are in `src/replicated/MonetizationConfig.luau`, `docs/ROBUX_PRODUCTS.md` and `store-assets/icons/products_manifest.json`.
- [x] Studio Play: `[PriceCheck] 29 items checked, 0 problems, 0 hidden`.
- [ ] Double Welcome Back is sold only on the Welcome Back screen (not in the shop): check it once in a live server after being away (the x2 button with its 19 Robux badge, then Claim!).
- [ ] Look at each item on the Creator Hub (Monetization > Passes / Developer Products): name, description, price, icon and On Sale as you want them. The script is safe to re-run; it never makes duplicates.
- [ ] The VIP lounge is built only once the VIP pass has a real id (it now has): check it once in Play.
- [x] Prices set from the research in `OVERNIGHT_FINAL_REPORT.md` (Phase 4), on Roblox through `tools/create_products.py` (2x Crystals 349, Auto Pick 199, Extra Pet Slot 399, Pet Squad 699, Crystal Sack 99, Shatter Now 29, gift twins the same). To change a price later: edit the table in `docs/ROBUX_PRODUCTS.md` and `ExpectedPrice` in `MonetizationConfig.luau`, run `python tools/create_products.py --dry-run`, then without `--dry-run`, then Play and check PriceCheck shows 0 problems.
- [ ] Studio note: your account owns every pass, so a solo Play is not a normal player. Turn on F2 > Testing switches > "Ignore owned passes" (`StudioIgnoreOwnedPasses`) to play without them, or use a test player (Test > Clients and Servers). Remove the attribute before saving the place.

## 3. Who can use the developer tools

- [ ] `src/server/DebugConfig.luau`: `AllowedUserIds` is **empty** (the F2 debug menu gives crystals, passes and receipts; in a live game nobody should have it).
- [ ] `src/server/AdminConfig.luau`: `AllowedUserIds` is **only `11704150663`** (you).

## 4. The place

- [x] Lighting uses Unified Lighting: **LightingStyle Realistic**, PrioritizeLightingQuality off (Technology no longer exists). Both are in `LightingConfig.Style`, which every server applies at start, so there is nothing to check by hand.
- [ ] Workspace > StreamingEnabled is ticked, StreamingTargetRadius 240, StreamingMinRadius 96, StreamOutBehavior Opportunistic (set in the launch fix pass; saved with the place).
- [ ] Every template MeshPart is RenderFidelity Automatic: if you rebuild templates, `tools/studio/build_templates.luau` already sets it.
- [ ] Music: in the Toolbox (Creator Store > Audio, licensed tracks from Roblox, APM or ProSoundEffects), pick two loops and paste their ids into `AudioConfig.Music` with the source and licence beside each:
  - Plaza: a light, playful winter tune, about 100-120 BPM (bells, pizzicato, glockenspiel).
  - Plot: a calm, cosy loop, about 80-95 BPM (soft piano, music box or mallets, no vocals).
  Play once and walk in and out of your plot: the music crossfades. An empty id simply plays nothing.
- [ ] Every audio file is approved: `python tools/upload_models.py --check --manifest store-assets/audio/upload_manifest.json`.
- [ ] Every asset id the game uses is the group's and approved: `python tools/check_asset_ids.py` (on 2026-11-26: 160 ids, all group-owned and approved; it reads the configs and asks Open Cloud about each id).
- [ ] Every UI icon is approved: `python tools/upload_models.py --check --manifest store-assets/ui-icons/upload_manifest.json` (62 images, all approved on 2026-11-28, the Rebirth and Welcome Back screens' 17 included), and the leaderboard model: `--manifest store-assets/plaza/upload_manifest.json` (approved at upload).

## 5. Codes

- [ ] Launch codes that work from day one: **ICELAUNCH** (500 crystals) for the game description and socials, **THAWED** (250 crystals, shown at the end of the tutorial).
- [ ] Likes milestone codes are written but switched off: `LIKES1K`, `LIKES5K`, `LIKES10K`, `LIKES25K`, `LIKES50K`, `LIKES100K` in `src/server/CodesConfig.luau`. When the game reaches a milestone: set that code's `Active = true`, publish, and announce it.
- [ ] Put the launch code in the game description ("Use code ICELAUNCH for free crystals!").

## 6. Experience settings (Creator Hub > the game > Configure)

- [ ] **Server size: 8 players** (one per plot; `MapConfig.PlotCount = 8`).
- [ ] **Genre:** Simulation (or Simulator, whichever the Hub offers).
- [ ] **Devices:** Computer, Phone, Tablet, Console (gamepad is supported: R2/A tap; every window works with the D-pad).
- [ ] **Audio:** every sound effect is the game's own, uploaded by the group, so it plays in the group's game. Toolbox music from Roblox's licensed libraries is public.
- [ ] **Maturity questionnaire:** fill it in (no violence, no chat changes; random paid items: yes, the Mythic Block, with odds shown).
- [ ] **Paid random items:** the Mythic Block shows its odds and is refused where they're restricted (PolicyService); nothing to switch on.
- [ ] **Icon and thumbnails:** pick from `store-assets/launch/` (icon concepts and 1920x1080 thumbnails) and upload them on the Hub (Places > Start place > Icon / Thumbnails).
- [ ] **Description:** what the game is, the launch code, and the group (+10% crystals for members).
- [ ] **Studio access to API services** is only needed in Studio (DataStores); live servers always have it.
- [ ] Private servers: optional (free or a price); decide.

## 7. Publish

- [ ] In Studio: File > **Publish to Roblox** (to the existing place 88645847284794, owned by the group). Rojo must be connected so the scripts are current.
- [ ] Set the game **Public** when you're ready.

## 8. One real test purchase (live game, not Studio)

Your own account counts as owning every pass (you made them), so test the pass with a second account or a friend.

- [ ] A **pass** (cheapest: Auto Pick, 199): buy it from the shop in the live game. It works at once (no rejoin): Auto Pick taps for you in your plot. Output in the Developer Console (F9 > Server): `[Purchase] <name> bought the Auto Pick pass`.
- [ ] A **product** (cheapest in the shop: Shatter Now or the Crystal Pouch, 29): buy it with a block on your mound. The block shatters; the server log shows `[Purchase] <name> Shatter Now (<id>): PurchaseGranted, gave ...`.
- [ ] Rejoin: the product's crystals or rescue are still there; the pass still works.

## 9. The first hour live

- [ ] **Developer Console > Server log** (F9 in a live server, or the Creator Hub's error reports): no red errors. Watch for:
  - `[Purchase]` lines: every receipt `PurchaseGranted`; any `NotProcessedYet` repeating means a reward can't apply (read its note).
  - `[PriceCheck]` problems.
  - DataStore warnings (throttling, failed saves). A failed load kicks the player with a message instead of overwriting their save.
- [ ] **Creator Hub > Analytics:** concurrent players, average session length (target 10-20 min), the onboarding funnel (Joined -> First tap -> First building -> First rescue -> First pet equipped -> Tutorial done -> First rebirth): a big drop at one step is where players get lost. The shop funnel: opened -> viewed -> prompted -> purchased.
- [ ] **Server memory and performance** (Developer Console > Memory / Server Stats): 8 maxed plots is the heaviest case.
- [ ] Join a live server yourself on a phone: the HUD, a window, tapping, buying.
- [ ] **Updates (soft shutdown):** publishing alone leaves running servers on the old version until they empty. To move everyone: Creator Hub > the game > **Configurations > Server management** > select the place > **Restart Servers**, with **"Restart only servers with outdated versions"** ticked (optionally "Delay server restart", 1-60 min). Players see an "update coming" warning (with a delay), then "Updating the game, back in a moment"; every save is written first and Roblox moves them to a new server. "Shut Down All Servers" also brings them back, through a temporary reserved server. Check it the first time on a server you're in.
- [ ] **Announcements:** F3 (admin window, you only) > Server > **Announce** (this server) or **AnnounceAll** (every server). Messages go through Roblox's text filter. Use it for "update in 5 minutes", events and likes codes.
- [ ] **Analytics after the first day:** Creator Hub > Analytics: the Onboarding, RobuxShop, **LayersReached** and **RebirthRanks** funnels; the **Economy** page (currency Crystals: where they come from and what they're spent on); custom events **GoldenGlacierJoined / Won / Escaped**. What each answers is in `OVERNIGHT_FINAL_REPORT.md` (Phase 3).
- [ ] Hotfix plan: fix in the repo, specs, publish, then Restart Servers (above).
