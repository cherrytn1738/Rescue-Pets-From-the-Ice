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
| 1. Rebirth and Welcome Back screens | Not started |
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

## Phase 0: Lighting note

- `LightingConfig.Style` holds the Unified Lighting settings: `LightingStyle = "Realistic"`, `PrioritizeLightingQuality = false`. A script can read and set both (checked in Studio: Edit mode reads Realistic / false, and writes go through), so `LightingConfig.Apply` sets them where they differ, at every server start, on each client at a look switch, and in Edit mode through `tools/studio/lighting.luau`. A Studio without the properties skips them quietly.
- `tools/studio/lighting.luau` no longer tries `Lighting.Technology` (reading it now fails: the property is gone) and reports the style instead. Run in Edit mode tonight: "lighting: PinkDusk, with its skybox / style: Realistic, PrioritizeLightingQuality false".
- AGENTS.md (the MCP notes and the `LightingConfig` line), `docs/LAUNCH_CHECKLIST.md` (the Technology box is now a ticked Unified Lighting line) and `docs/VISUAL_PASS_GUIDE.md` (the Lighting row; the "can't check Technology" note removed) say this instead of "Technology = Future". Nothing asks you to check Technology any more.
- Spec: `LightingConfig` +2 checks (the style values, Apply sets them).
