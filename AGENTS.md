# Rescue Pets From the Ice

## Purpose

Help build Rescue Pets From the Ice, a Roblox game, while teaching the developer Roblox development. The design is in [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md), the source of truth for gameplay rules, numbers and features.

Priorities, in order:

1. Fun and reliable gameplay
2. Simple, maintainable architecture
3. Security for important game state
4. Incremental development
5. Scalability when justified

Do not over-engineer early versions of the game.

## Ids

Use exactly these. Never guess another id; if one is needed and not listed here or in a config, ask.

| What | Id |
|---|---|
| Group (owns the game and every asset) | 921449746 |
| Universe | 10778596196 |
| Start place | 88645847284794 |
| Developer's user id (admin allowlist) | 11704150663 |
| GitHub repository | https://github.com/cherrytn1738/Rescue-Pets-From-the-Ice (default branch `main`) |

Game pass and developer product ids go in `src/replicated/MonetizationConfig.luau` once they are created on the Creator Hub (`docs/ROBUX_PRODUCTS.md`).

## Development Environment

- Windows 10
- Roblox Studio, Luau
- Rojo 7.7.1, pinned in `rokit.toml`; repository `.luau` files are the source of truth
- Roblox Studio MCP (`Roblox_Studio`, defined in `.mcp.json`) for inspecting and testing the open place
- Blender MCP (`blender`, defined at user scope) for building models
- Git/GitHub for version control

Edit script source in the repository. Use Studio/MCP to inspect and test the live game and to manage non-script objects (parts, models, terrain, lighting). Never edit Rojo-managed script Source in Studio.

Keep the Rojo mappings in `default.project.json` stable unless a feature needs a change.

## Rules

- **Server-authoritative.** The server owns every important value; the client asks and the server checks and decides (see Architecture Principles).
- **Secrets.** Never commit, print, echo or log a secret. The Open Cloud API key comes only from the `ROBLOX_API_KEY` user environment variable: never put it on a command line, in a file or in code. Check it only as set/missing (`if ($env:ROBLOX_API_KEY) { "set" } else { "missing" }`).
- **Studio never touches live DataStores.** Studio playtests use the Studio stores (`IcePets_PlayerData_Studio`, `IcePets_PlayerData_StudioFresh`). `StudioUseLiveSaves` exists for a deliberate, announced check only. Specs use fakes and never touch any real store.
- **Never force-push** (`git push --force`, `-f`, `--force-with-lease`), and don't rewrite pushed history.
- **Uploads always go to group 921449746.** Every mesh, image, audio file, model and product icon is created by the group: `creationContext.creator.groupId = "921449746"` in Open Cloud's `/assets/v1/assets` request, never a `userId` and never another group. Use `python tools/upload_models.py <files>` (`.fbx` Models, `.png`/`.jpg` Images, `.ogg`/`.mp3` Audio). It keeps an `upload_manifest.json` beside the files (asset ids, hashes, creator), skips unchanged files, updates group-owned Models in place, and makes a NEW asset for a changed picture or sound (swap the new id into the game). If Roblox refuses an audio upload (a quota, ID verification), it stops and prints Roblox's message: report it, don't work around it. `--dry-run` sends nothing; `--check` re-reads moderation.
- **The voxel skill (`lihfolk-stud-voxel`) is for pets only**, never for buildings, terrain, props or the map.
- **Nothing from Steal Pets.** This repo started from copies of Steal Pets' reusable systems. Never reuse that game's DataStore names, asset ids, product ids, group or universe, and never edit its folder (`../StealPetsFromOthers`).

## Working Style

The developer is learning Roblox development. Explain important Roblox concepts clearly, but avoid unnecessary theory.

Before a significant change:

1. Inspect the relevant files and Studio objects first.
2. Preserve working behavior unless the change requires replacing it.
3. Explain the intended change briefly.
4. Implement the smallest coherent milestone.
5. Check the result for obvious problems.
6. Playtest through MCP when useful.
7. Report what still needs manual checking in Studio.

For small changes, bug fixes and obvious tasks, skip the explanation and make the change.

Prefer finishing coherent milestones over many tiny steps. Do not make unrelated changes while building or debugging a feature.

## Game Identity

See [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md) for what the game is, its core loop and its established decisions. Do not reconsider a decision written there unless explicitly asked. Pet names, models, art, UI and branding are original.

## Current Development Priority

Setup is done: Rojo, MCP, the save, monetization plumbing, the UI kit, the debug and admin windows, codes, offline earnings and analytics helpers. There is no gameplay yet; an empty baseplate with the HUD shell is the expected state.

Next: the first milestone from `docs/GAME_DESIGN.md`. Do not assume planned work is implemented; inspect the repository and Studio first.

Keep placeholder balance values configurable, in config modules under `src/replicated/`. Every number from the design lives in a config, never in gameplay code:

- `LayerConfig`: the six ice layers (levels, look, rarity odds), the floor layer, block HP (`BlockHp(level)`), crack stages, block size, `LayerForLevel`.
- `CreatureConfig`: rarities (bonus, glow, announced), the 18 creatures (rarity, first layer, look, `ModelId`), pet rules, Creature Book rewards, `PoolForLayer`.
- `BuildingConfig`: the eight buildings (base cost, damage/s, pad, station looks, upgrade parts), cost growth (`Cost`, `CostOfNext`), Masterwork.
- `UpgradeConfig`: ice pick tiers, Frost Touch, building upgrades, ice upgrades, and `Upgrades` (every upgrade's saved id and cost).
- `RebirthConfig`: Frost Cores (`FrostCoresFor`), ranks, pet slots and layers they open, what a rebirth resets.

The specs `tests/<Name>Config.spec.luau` read the design doc's own tables (`tests/DesignDoc.luau`; the runner sends `docs/*.md` as sources), so a config and the doc can't drift apart silently: when the doc's numbers change, change the config in the same commit. Ids (creatures, buildings, upgrades, layers) are saved: never rename one.

## Architecture Principles

The server controls or validates:

- currency, rewards and progression
- purchases, prices and ownership
- which pets each player has rescued and owns
- important gameplay results
- everything that is saved

The client handles:

- input
- UI
- camera
- animations
- local visual and audio feedback

Never trust client-sent values for rewards, prices, ownership, progression, multipliers or results. The client asks; the server checks and decides.

Keep RemoteEvents few and declared in `default.project.json`. On the server, check every remote argument (type, range, rate).

Do not add frameworks, service layers, dependencies or abstractions unless they solve a real current problem.

## Roblox Studio MCP Rules

Before changing an existing system:

- inspect the relevant DataModel hierarchy and read the relevant repository files
- check existing properties and configuration instead of guessing
- avoid duplicating Instances that already exist

When making changes:

- edit repository source and let Rojo sync
- use Studio/MCP for runtime tests and non-script objects
- keep object names descriptive and consistent

After implementing, check Studio's Output for errors, playtest through MCP when relevant, and report what still needs manual checking. Judge visual correctness from a playtest, not from properties alone.

Known Studio/MCP behavior:

- Before trusting a test, confirm Studio has the edited code (search the script's Source). If Rojo stopped, Studio silently runs old code.
- Studio's MCP server only finds an open Studio a few seconds after it starts: call `list_roblox_studios` (retry for a few seconds) before other tools.
- `screen_capture` needs Studio in the foreground; in the background it comes back black or grey. Take one capture per call: a timed-out capture can arrive as the next call's result.
- Edit-mode tweens don't step while Studio is in the background, so UI timing checks can fail there.
- If `start_stop_play` hangs on "Start play hasn't finished yet", start Play from Edit with `task.spawn(function() game:GetService("StudioTestService"):ExecutePlayModeAsync({}) end)` and wait in a separate call.
- `require()` from `execute_luau` gets its own copy of a module, so state set up by the game's scripts isn't there. Drive UI by clicking the real buttons with `user_mouse_input`.
- MCP can't run Import 3D or click the Rojo plugin. Ask the developer.
- `Lighting.Technology` can't be read or set from MCP (execute_luau lacks the capability, `inspect_instance` lists no Lighting properties). The developer set it to Future by hand (polish pass 3). A night-time point-light shadow test (`Shadows = true`, quality level 21) still showed no local-light shadows, so the tools can't confirm Future; judge it in Properties.
- A plot maxed with the debug menu at a low block level shatters every block the tick it arrives, so the ice block is never seen. Set the block level high (debug `SetBlockLevel`, e.g. 400) before judging the block or taking screenshots. The `SetRebirths` debug action changes the rank colour only after a respawn or a rescue.
- `ProximityPromptService.Enabled` is saved with the place. `UIKit` switches it off while a window is open, so never run `UIKit` (or a window script) in Edit mode. `UIKit` turns prompts back on when it loads on a client.
- 2-player tests: from Edit, `task.spawn(function() game:GetService("StudioTestService"):ExecuteMultiplayerTestAsync(2, {}) end)`; after about 20 s `list_roblox_studios` shows a server and two clients. End it with `StudioTestService:EndTest("done")` on the server instance. Test players have negative user ids (Player1 = -1): never treat only positive ids as real players.
- Overnight runs: Windows turns the display off after 10 idle minutes, and then every `screen_capture` times out.

## Rojo Workflow

The repository is authoritative. Rojo maps:

- `src/server` -> ServerScriptService
- `src/replicated` -> ReplicatedStorage (plus the RemoteEvents and RemoteFunctions declared in `default.project.json`)
- `src/player` -> StarterPlayer.StarterPlayerScripts

`Name.server.luau` is a Script, `Name.client.luau` a LocalScript, `Name.luau` a ModuleScript.

Normal workflow: Design -> Edit files -> Rojo sync -> Test in Studio -> Fix -> Commit -> Push

- Never edit Rojo-managed scripts in Studio, and never treat the place as the source of truth for scripts.
- Delete synced files one at a time, never a whole synced folder at once (that has crashed `rojo serve`). After deleting, check `rojo` is still running.
- After a Rojo restart, the developer reconnects the Studio plugin by hand.
- Hand-built objects (models, parts, terrain, lighting) live in the place file, not in Git. Keep them out of Rojo-mapped services (use Workspace or ServerStorage), and remind the developer to save and back up the place after changing them.

## Development Workflow

Design -> Implement -> Test -> Fix -> Commit -> Continue

Before significantly changing a working system, consider a Git checkpoint.

For debugging:

1. Identify the likely cause.
2. Inspect only the relevant code and objects.
3. Make the smallest useful change.
4. Test it.
5. Avoid unrelated refactoring.

If a cosmetic issue doesn't block the milestone, record it for later polish.

For long unattended runs: work on a branch, commit after each phase, and keep a report file updated after each step (done, failed, still to do by hand, what to look at by eye).

Pushing and destructive git commands (reset, clean) are the developer's call. Force-pushing is never allowed.

## Testing

- Specs live in `tests/` (not synced). Each `Name.spec.luau` returns `function(sources)` and returns its number of passed checks. It loads the modules it tests with `loadstring(sources.X)()` and swaps their globals with `setfenv` for fakes (players, `tests/FakeDataStore.luau`, MarketplaceService, a clock).
- Run them with the spec runner: `python tools/run_specs.py` (every spec) or `python tools/run_specs.py PlayerData Codes` (some). It needs Studio open with any place in Edit mode and "Enable Studio as MCP server" on. It sends every `.luau` file under `src/` and `tests/` to Studio as `sources` and runs each spec in Edit mode through Studio's MCP server, so nothing is synced into the place, nothing is left behind and Rojo doesn't need to be running. It exits non-zero when a spec fails.
- Specs never touch a real save, a live Instance or a real purchase.
- Every new system gets a spec, and every save change adds checks to `tests/PlayerData.spec.luau`.
- Command-bar helper scripts live in `tools/studio/`.

Studio-only test switches are Workspace attributes, read only when `RunService:IsStudio()` is true, and never saved. Remove each one before saving the place:

- `StudioFreshSave` (true): play as a brand-new player on a throwaway record (`IcePets_PlayerData_StudioFresh`, a new key every Play).
- `StudioUseLiveSaves` (true): Studio uses the LIVE store and warns in Output. Only on purpose, and say so first.
- `StudioTimeAway` (number, seconds): a joining player whose save has a leave time counts as away this long (`OfflineEarnings`).
- `StudioPaidRandomRestricted` (true): everyone counts as living where paid random items are restricted (`PaidRandomPolicy`).
- `StudioScreenSize` (Vector2, set on the CLIENT): the UI lays out as if the screen were that size (phone checks; `UIKit`), with the touch layout.
- `StudioGamepad` (true, set on the CLIENT): `UIKit.UsingGamepad()` answers yes, for gamepad tests from MCP.

## Systems

What is already in the repo (copied from Steal Pets and stripped of that game):

- **Debug menu** (`DebugService`, `DebugActions`, `DebugRules`, `DebugConfig`; client `DebugMenu.client`, built with `ActionMenu`): **F2** or the small purple **DEBUG** button on the right edge. A target picker (any player here) and actions for the save (and, for performance tests, "Fill every empty plot with a maxed dummy plot" / "Free the dummy plots again") (save now, add crystals, set block level, set the ice pick tier, show it, reset to a fresh save that keeps receipts), offline earnings, analytics funnels, codes, Robux (give/remove a pass for this session, simulate a receipt or a gift, replay a duplicate receipt) and the Studio switches, plus teleport, walk speed and respawn. Access: everyone in Studio; live, only `DebugConfig.AllowedUserIds`, which is empty and must stay empty in shipped builds unless on purpose. The server checks every request (about one a second); others are rejected and logged (`[Debug] REJECTED`). To add an action, add one entry to `ACTIONS` in `DebugActions.luau`; the server validates every input against its `Params`. Every new system adds debug actions for itself.
- **Admin window** (`AdminService`, `AdminCommands`, `AdminRules`, `AdminConfig`; client `AdminWindow.client`): **F3** or the small red **ADMIN** button. (While either window is open, both edge buttons slide to its left, so neither sits on top of it; on a screen too narrow for that they hide until it closes.) Live servers: only the developer (`AdminConfig.AllowedUserIds = { 11704150663 }`); everyone in Studio. Commands: Launch, Rocket, Jail (effects in `PlayerEffects`), ServerInfo, Kick. Each prints `[Admin]` lines; others get `[Admin] REJECTED`. From MCP: `AdminRequest:InvokeServer("Run", { Action, Target, Args, Confirmed = true })`.
- **Robux** (`MonetizationConfig`, `MonetizationRules`, `Receipts` (the only `ProcessReceipt`), `Gifting`, `GamePasses`, `RobuxShop`, `PurchaseRewards`, `PaidRandomPolicy`, `RobuxPerks` (what every item does: the reward kinds Pass, CrystalBundle, ShatterNow, ServerFrostRush, MythicBlock, and the pass perks); client `ShopWindow.client`, `PriceCache`, `ShatterOffer.client`, `VipLounge.client`): every pass and product of the design doc is in the config with `Id = 0` (and `GiftId = 0`); only the ids are missing (`docs/ROBUX_PRODUCTS.md`). Passes are gifted through a "Gift: <name>" developer product each, and a gifted pass is saved (`GiftedPasses`). The debug action "Show the target's Robux perks" prints every multiplier. To sell something new: create it on the Creator Hub, add it to `MonetizationConfig` with its real id, and register its reward kind in `PurchaseRewards.Kinds` (`{ CanGive, Give }`); a reward kind that isn't registered is refused before the prompt, and its receipt answers `NotProcessedYet`, so no Robux is ever taken for nothing. An item without a real id runs a SIMULATED purchase in Studio through the real receipt handler. `[Purchase]`, `[Gift]` and `[PriceCheck]` lines in Output; pass ownership shows as `Owns_<Key>` player attributes; purchase notices go to the client on `PurchaseNotice`. The developer account counts as owning every pass: test a pass purchase as a Studio test player (Test > Clients and Servers). Paid random items must follow `PaidRandomPolicy` and show their odds.
- **Promo codes** (`CodeService`, `CodeRules`, `CodesConfig`; client `CodesWindow.client`): `CodesConfig` is server-only (a code never reaches a client before it is typed) and empty. A code's reward is a `PurchaseRewards` reward, so it needs a registered reward kind. Each player redeems a code once (`Codes` in the save); attempts are rate-limited. `[Codes]` lines in Studio.
- **Offline earnings** (`OfflineEarnings`, `OfflineEarningsRules`; client `OfflineEarningsPopup.client`): measures the time away from `PlayerData.TakeLeftAt` (or `StudioTimeAway`), capped by `OfflineEarningsRules.Settings`. Nothing is paid until gameplay registers an earner with `OfflineEarnings.SetEarner(function(player, data, secondsAway, settings) return amount, label end)`. The popup follows the player's `OfflineEarnings` attribute (JSON `{ Amount, Seconds, Capped, Label, At }`). `[Offline]` lines in Studio.
- **Analytics** (`Analytics` on the server, `AnalyticsConfig` and `AnalyticsRules`): Roblox's AnalyticsService, server only. In Studio nothing is sent; each step prints an `[Analytics]` line instead. Only the player object, step numbers and config names are sent, never names or ids. The one-time onboarding funnel (`AnalyticsConfig.Onboarding`, empty until the game adds steps; logged in order, early steps wait in the save's `Funnels.Waiting`) and the Robux shop funnel (1 Opened shop, 2 Viewed item, 3 Prompt shown, 4 Purchased; the window reports on `ShopVisit`). **Never rename or reorder a step or funnel** once live; add new steps at the end.
- **UI kit**: see UI below.
- **Building and pick models** (uploaded as group 921449746; ids in `ASSET_IDS.md`, written into `BuildingConfig.ModelIds`, `UpgradeConfig.PickModelIds` and `EffectsConfig.Textures` by `python tools/write_asset_ids.py` after `tools/upload_models.py`). Studio templates live in the place file: `ServerStorage.BuildingTemplates.<Id>.T<tier>` (a Model with a `Root` PrimaryPart carrying the named attachments, and `Upgrades.U1..U5`) and `ServerStorage.PickTemplates.Pick<tier>` (Tools), built in Edit mode by `tools/studio/build_templates.luau` (one set at a time: `ONLY = "IcePickPost"`, ..., `"Picks"`). Rebuild them after re-uploading a model, then save the place. `PlotService` clones the tier's station onto its pad facing the ice (a greybox stand-in if a template is missing), `PickService` keeps the player's pick tier in their hand (spec `tests/Pick.spec.luau`), a faded Ice Pick Post becomes the fence ring round the ice (`BuildingConfig.Fence`), and `BuildingEffects.client` puts the particles, lights and the Legendary ground ring on the attachments.

- **Building and reward moments** (client): `BuildMoments.client` (the first copy rises from the snow with a puff and a camera nudge; a new station milestone flashes white with "Your X evolved!"; a building upgrade flashes and puffs), `RareWatch.client` (a beam in the rarity colour over another plot holding a Legendary or Mythic block until it is freed), rescue confetti (RescueMoment), the sled under an arriving block, crystal colours by ice upgrades and spark colours by pick tier (`IceLooks.CrystalColours`, `IceLooks.PickSparks`). Server: a star per building upgrade on the station badge, a Masterwork name plate, the golden pick skin (Creature Book Golden page, `PickService`) and the aurora trail (Mythic page, `RankService`).
- **Plot parts** (`tools/blender/plot_parts.py`, `store-assets/plot/`, ids in `MapConfig.PlotModels`): the frozen ice stage, the ice-block walls (long and short) and the ice gate with its two name boards, in the buildings' style. `tools/studio/build_templates.luau` with `ONLY = "Plot"` builds `ServerStorage.PlotTemplates`; `PlotService` shows them over the plot's own Parts, which turn invisible and keep the collision (with a template missing, the plain Parts show). The owner's name is a SurfaceGui on the boards (`NameBoardLeft`/`NameBoardRight`, both faces). `...Trim` meshes carry the `RankColour` attribute, and `RankService` colours them with the rebirth rank.
- **World** (`tools/studio/build_world.luau`, Edit mode, then save the place): removes the Baseplate and builds the snow terrain (in every plot the drifts and ice patches from `MapConfig.PlotGround`; the plots' own Base parts are invisible floors), frozen ponds, hills, mountains, the snowy pines (`Workspace.Scenery`, `store-assets/scenery/`) and the winter sky (`tools/make_skybox.py`). Re-run it after changing `MapConfig.PlotGround`. Smooth terrain draws a filled layer's surface 2 studs above its top; the script allows for it and reports the measured surface.

## Code Guidelines

- Clear, beginner-readable Luau
- Descriptive names over clever abstractions
- One clear responsibility per script
- Current Roblox APIs and patterns
- No unnecessary dependencies or premature optimization
- Comments only where they explain non-obvious intent
- Tuning values in config modules, not scattered magic numbers
- When several designs work, choose the simplest secure one

## UI

Style follows the roblox-ui-style skill, recoloured icy blue and white: every token is in `src/replicated/UITheme.luau` (window themes `Ice`, `Polar` and `Showcase`; card palettes; buttons `Go`, `Buy`, `Neutral`, `Gift`, `Frost`), and every screen is built from `src/replicated/UIKit.luau` (labels, the studded button, cards, scroll lists, tabs, progress bars, the responsive `Screen` root and the `Window` shell) and `src/replicated/ShowcaseKit.luau` (the showcase window, cards, buy and info buttons, stickers, HUD buttons). Build new UI from the kit, not raw Instances. The F2 debug and F3 admin windows (`ActionMenu`) keep their plain tool look on purpose.

- **HUD** (`HUD.client`): the left-edge menu (SHOP, CODES), at the top left on touch screens. Windows find their button with `UIKit.MenuButton("Shop")`. From MCP, click `LocalPlayer.PlayerGui.HUD.Root.Menu.Grid.ShopButton` (or `CodesButton`); a window's close button is `LocalPlayer.PlayerGui.<Name>Window.Root.Panel.Close`.
- **Pictures:** `UITheme.Icons`, `ShopIcons` and `Sheets` are empty until this game's own pictures are made and uploaded (as group 921449746); a missing picture falls back to text. The only image ids in the kit are the two public library images from the skill (`UITheme.Assets`: the checker and the Robux icon).
- **Audio:** play every sound through `Audio` (never a raw Sound) so the player's Music / Sound effects volume (Settings, saved) applies; note each id's source and licence beside it in `src/replicated/AudioConfig.luau`. The sound effects are original, made by `python tools/make_sfx.py` into `store-assets/audio/<Name>.ogg` and uploaded as the group (ids in `AudioConfig.Files`); a changed sound gets a new id. Ogg files get a random serial number when written, so the script only rewrites a sound whose samples changed (`store-assets/audio/sources.json`). When sounds play is in `SoundRules` (settings `AudioConfig.Rules`, spec `tests/SoundRules.spec.luau`): your taps capped at 3 at once, building hits only an occasional quiet chip from your own plot, other plots only Legendary and Mythic rescue jingles within 60 studs. `GameSounds.client` plays the income tick, book pages and the debug menu's "Play a sound" (Sound group). Music: `MusicPlayer.client` crossfades `AudioConfig.Music.Plaza` / `.Plot`; their ids are empty until the developer picks licensed tracks, and an empty id plays nothing.

Support desktop and mobile/touch; check phone layouts with `StudioScreenSize` (for example `Vector2.new(844, 390)`).

Do not copy another game's proprietary assets, branding or exact layout.

## Persistence

Use the player-data lifecycle in `src/server/PlayerData.luau` (from the roblox-player-data skill): one record per player (`Player_<UserId>` in `IcePets_PlayerData`), a session lease, UpdateAsync only. Its session data is the real state: systems change it through `PlayerData.Edit`, and call `PlayerData.MarkImportant` after anything important (saved on the next 5 s tick, but at most every 15 s per player; Robux grants use `PlayerData.SaveNow`). Gameplay touches a player's data only while `PlayerData.IsReady(player)`. Do not create new DataStores for new systems unless justified.

The store names are this game's own: `IcePets_PlayerData` (live), `IcePets_PlayerData_Studio` (Studio's default) and `IcePets_PlayerData_StudioFresh` (`StudioFreshSave`). Never use Steal Pets' names (`PlayerData`, `PlayerData_Studio`, ...); `tests/PlayerData.spec.luau` checks it.

Keep these protections:

- distinguish failed loads from new players
- a failed-load session never overwrites saved data with defaults
- periodic autosave
- save on PlayerRemoving
- save on BindToClose
- validate and sanitize loaded data
- bounded retries
- Studio playtests use a separate Studio store, never the real save

Current schema: Schema 1.

- 1, the game (docs/GAME_DESIGN.md, "Data and code structure"; this code's names are PascalCase): `Crystals`, `CrystalsThisRun`, `CrystalsAllTime` (amounts: finite, non-negative, may be fractional), `BlockLevel` (from 1), `CurrentBlock` (`{ CreatureId, HpLeft }`, or none: the server rolls a new block), `Buildings` (`{ [building id] = count }`), `Upgrades` (upgrade ids), `Pets` (`{ Uid, CreatureId, Golden }`, at most `CreatureConfig.Pets.InventorySize`), `Equipped` (owned pet uids, at most `MaxEquipSlots`), `BookSeen` (`{ [creature id] = rescue count }`), `FrostCores`, `Rebirths`, `MaxLayerOpened` (starts at `LayerConfig.FloorLayer`), `CreaturesRescued`, `TutorialStep` (1-5, 5 = done), `MythicBlocks` (Mythic Blocks bought, not rolled yet). The doc's `codesRedeemed` is `Codes`, `lastOnline` is `LeftAt` and `purchaseIds` is `Receipts`; bought pass ownership is never saved, but a pass received as a gift is (`GiftedPasses`, `{ [pass key] = true }`). Progress that can't be read fails closed; unknown creature, building and upgrade ids are dropped; a block that can't be read is rolled again. The rebirth reset list is `RebirthConfig.ResetOnRebirth`. Display attributes: `Crystals`, `BlockLevel`, `Rebirths`, `FrostCores`.
- 1, bookkeeping: `Receipts` (granted Robux receipts `{ Id = PurchaseId, Product, At, For }`, the most recent 50), `PendingGifts` (`{ [product key] = { Recipient, RecipientName, Store, Key, State = "prompted" | "purchased", At } }`), `GiftInbox` (store only: gifts other players sent, `{ Id, Product, From, FromName }`; other servers add to it with `PlayerData.UpdateRecord`, and the owner's saves MERGE it, never overwrite it), `ReceivedGifts` (gift ids given, the most recent 100), `Codes` (redeemed promo codes, upper case letters and digits, the most recent 200), `Funnels` (`{ Onboarding = steps logged, Waiting = { steps reached early } }`), `LeftAt` (store only: the server's `os.time()` at every save, handed out once per session by `PlayerData.TakeLeftAt`), plus `Session` and `LastWriteId` (lease bookkeeping). A debug reset keeps `Receipts`, `PendingGifts` and `ReceivedGifts`.
- The fields from `docs/GAME_DESIGN.md` ("Data and code structure") join schema 1 while nothing is live. Once the game is public, every change to what is saved bumps the schema and adds a validation step.

Robux grants follow the skills' receipt rules (`Receipts.luau`, the game's only `ProcessReceipt` handler; never assign `ProcessReceipt` anywhere else):

- Give the reward and record the PurchaseId in the same data, with no yield in between.
- Save, and only then answer `PurchaseGranted`. Anything that can't apply now answers `NotProcessedYet`, so Roblox retries.

Game pass ownership is never saved: it comes from Roblox (`GamePasses`). The one exception is a pass received as a gift (bought as its gift product by someone else): Roblox has no record of it, so it is saved in `GiftedPasses` and kept through a debug reset, like `MythicBlocks`.

## Multiplayer

Player state stays isolated unless the design says otherwise.

- A gift is written into the recipient's saved record (their `GiftInbox`), so it reaches them once even if they leave or the server shuts down.
- Leaving, death, travel and disconnect clean up active gameplay objects, UI state and animation state.

## Project Documentation

Docs are the source of truth for evolving design details:

- `AGENTS.md`: these rules
- [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md): the source of truth for the design: gameplay rules, numbers and features. When a milestone settles a design detail, update it there in the same commit.
- [`docs/ROBUX_PRODUCTS.md`](docs/ROBUX_PRODUCTS.md): the game passes and products to create on the Creator Hub, and their ids once made.

Add a doc only when it's justified. If docs conflict with the code or the developer's latest instruction, point out the conflict instead of guessing.

## Context Efficiency

Use the smallest relevant set of files, scripts and Studio objects. Do not inspect or rewrite the whole project for a focused change. Do not reread every doc for small tasks.

Ask only when ambiguity materially changes the implementation. Otherwise inspect the project and make the simplest reasonable choice.

## Claude Development Behavior

Claude is the primary implementation agent.

For routine work: inspect the relevant files and Studio state, edit repository source, let Rojo sync, verify with MCP, test when practical, then report a short summary and the remaining manual checks.

For architecture, security-sensitive systems, hard debugging and important tradeoffs, reason more carefully before editing.

Do not add complexity just because it is easy to generate.

## Current Scope Boundaries

Build what `docs/GAME_DESIGN.md` describes, milestone by milestone; do not build a later milestone's features early unless asked. Monetization follows the design doc's table (built; ids still to paste).

Keep art, cosmetics, final balance and future content separate from gameplay architecture unless explicitly requested.
