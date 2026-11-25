# Launch checklist

Every step you do by hand to launch Rescue Pets From the Ice, in order. Tick each box as you go. Ids, keys and prices are in `docs/ROBUX_PRODUCTS.md`; the game is universe 10778596196, start place 88645847284794, owned by group 921449746.

## 1. Before you start

- [x] Merge the `overnight-launch-prep` branch into `main` (done in the launch fix pass). Pull, and make sure `rojo serve` is running and the Studio plugin is connected.
- [ ] Save the place in Studio and keep a backup copy of the `.rbxl` (File > Save to File As...). The building, pick, plot and plaza templates, the world and the streaming settings live only in the place file.
- [ ] Run every spec: `python tools/run_specs.py` (Studio open in Edit mode). All must pass.
- [ ] Workspace attributes: none of the Studio test switches may be set (`StudioFreshSave`, `StudioUseLiveSaves`, `StudioTimeAway`, `StudioPaidRandomRestricted`); on the client switches `StudioScreenSize`, `StudioGamepad` are never saved. Check Workspace > Attributes is empty of them.
- [ ] `ProximityPromptService.Enabled` is ticked (it is saved with the place; the UI kit turns it off while a window is open in Edit mode).

## 2. Robux items (24 to create)

For each item in `docs/ROBUX_PRODUCTS.md` (6 passes, 6 products, and a "Gift: <name>" developer product for each of the 12):

- [ ] Upload its icon as the group: `python tools/upload_models.py store-assets/icons/<Key>.png` (drafts are in `store-assets/icons/`; replace any you don't like first).
- [ ] Creator Hub > the game > Monetization > Passes / Developer Products > Create: the name, description and price from the table, the icon, **On Sale**.
- [ ] Create its gift product (a developer product): "Gift: <name>", same price, "A gift: <name> for another player in your server."
- [ ] Paste the item's id into `Id` and the gift product's id into `GiftId` in `src/replicated/MonetizationConfig.luau` (find it by Key). Check `ExpectedPrice` matches what you set.

Then:

- [ ] Run the specs again (the Monetization spec checks the config against the design doc).
- [ ] Start a Play in Studio and read Output: **`[PriceCheck] 24 items checked, 0 problems, 0 hidden`**. Any warning names the item: a wrong id, an item not on sale, or a price that differs from `ExpectedPrice`. Fix and Play again until it is clean.
- [ ] The VIP lounge appears in the plaza once the VIP pass is in the config (it already is); check it once in Play.

## 3. Who can use the developer tools

- [ ] `src/server/DebugConfig.luau`: `AllowedUserIds` is **empty** (the F2 debug menu gives crystals, passes and receipts; in a live game nobody should have it).
- [ ] `src/server/AdminConfig.luau`: `AllowedUserIds` is **only `11704150663`** (you).

## 4. The place

- [ ] Lighting > Technology is **Future** (Properties; the tools can't read it).
- [ ] Workspace > StreamingEnabled is ticked, StreamingTargetRadius 240, StreamingMinRadius 96, StreamOutBehavior Opportunistic (set in the launch fix pass; saved with the place).
- [ ] Every template MeshPart is RenderFidelity Automatic: if you rebuild templates, `tools/studio/build_templates.luau` already sets it.
- [ ] Music: in the Toolbox (Creator Store > Audio, licensed tracks from Roblox, APM or ProSoundEffects), pick two loops and paste their ids into `AudioConfig.Music` with the source and licence beside each:
  - Plaza: a light, playful winter tune, about 100-120 BPM (bells, pizzicato, glockenspiel).
  - Plot: a calm, cosy loop, about 80-95 BPM (soft piano, music box or mallets, no vocals).
  Play once and walk in and out of your plot: the music crossfades. An empty id simply plays nothing.
- [ ] Every audio file is approved: `python tools/upload_models.py --check --manifest store-assets/audio/upload_manifest.json`.
- [ ] Every UI icon is approved: `python tools/upload_models.py --check --manifest store-assets/ui-icons/upload_manifest.json` (27 images, all approved on 2026-11-25), and the leaderboard model: `--manifest store-assets/plaza/upload_manifest.json` (approved at upload).

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

- [ ] A **pass** (cheapest: Auto Pick, 149): buy it from the shop in the live game. It works at once (no rejoin): Auto Pick taps for you in your plot. Output in the Developer Console (F9 > Server): `[Purchase] <name> bought the Auto Pick pass`.
- [ ] A **product** (cheapest: Shatter Now, 25): buy it with a block on your mound. The block shatters; the server log shows `[Purchase] <name> Shatter Now (<id>): PurchaseGranted, gave ...`.
- [ ] Rejoin: the product's crystals or rescue are still there; the pass still works.

## 9. The first hour live

- [ ] **Developer Console > Server log** (F9 in a live server, or the Creator Hub's error reports): no red errors. Watch for:
  - `[Purchase]` lines: every receipt `PurchaseGranted`; any `NotProcessedYet` repeating means a reward can't apply (read its note).
  - `[PriceCheck]` problems.
  - `[Taps] ... tapping faster than 20/s`: autoclickers (they are capped; this is only a log).
  - DataStore warnings (throttling, failed saves). A failed load kicks the player with a message instead of overwriting their save.
- [ ] **Creator Hub > Analytics:** concurrent players, average session length (target 10-20 min), the onboarding funnel (Joined -> First tap -> First building -> First rescue -> First pet equipped -> Tutorial done -> First rebirth): a big drop at one step is where players get lost. The shop funnel: opened -> viewed -> prompted -> purchased.
- [ ] **Server memory and performance** (Developer Console > Memory / Server Stats): 8 maxed plots is the heaviest case.
- [ ] Join a live server yourself on a phone: the HUD, a window, tapping, buying.
- [ ] Hotfix plan: fix in the repo, specs, publish; a running server keeps the old code until it closes (if urgent, use "Migrate to Latest Update" on the place, Creator Hub or Studio, which restarts servers with the new version).
