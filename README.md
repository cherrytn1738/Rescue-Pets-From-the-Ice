# Rescue Pets From the Ice

A Roblox game. The design lives in [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md).

Written in Luau. The scripts live in this repository and are synced into Roblox Studio with Rojo.

## Setup

1. Install [Rokit](https://github.com/rojo-rbx/rokit), then run `rokit install` in this folder. It installs the Rojo version pinned in `rokit.toml` (7.7.1).
2. Install the Rojo plugin in Roblox Studio (`rojo plugin install`).
3. Open the start place (place 88645847284794) in Studio. Turn on Game Settings > Security > "Enable Studio Access to API Services": saves use DataStores, and without it every load fails closed and kicks.
4. Run `rojo serve` here, then press Connect in Studio's Rojo plugin.
5. Press Play. Studio playtests save to a separate Studio DataStore, never to live player saves.

Rojo maps `src/server` to ServerScriptService, `src/replicated` to ReplicatedStorage and `src/player` to StarterPlayerScripts (`default.project.json`). Edit scripts here, not in Studio. Hand-built parts, models and lighting live in the place file, which is not in Git: publish it or save backups.

## Tests

The specs in `tests/` run inside Studio in Edit mode: `python tools/run_specs.py` (all) or `python tools/run_specs.py PlayerData` (one). Studio must be open with a place and "Enable Studio as MCP server" on. AGENTS.md (Testing) explains how.

## Docs

- [`docs/GAME_DESIGN.md`](docs/GAME_DESIGN.md): the game design, the source of truth for rules and numbers.
- [`AGENTS.md`](AGENTS.md): how the project is built: ids, rules, architecture, workflow, testing and saving.
- [`docs/ROBUX_PRODUCTS.md`](docs/ROBUX_PRODUCTS.md): the game passes and products to create on the Creator Hub.
