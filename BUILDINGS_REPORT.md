# Overnight run 2: buildings, upgrade parts, picks, effects

(Filled in step by step; the final summary is at the end.)

## Step 0: sync with the design doc (done)

- `BuildingConfig` follows the new doc tables:
  - `Tiers`: the five tier themes.
  - `Stations`: each building's five tier forms.
  - `UpgradeParts`: now a list of five, one per upgrade.
  - `LegendaryForm` and `SignatureAura`: each Legendary's name and aura.
- `tests/BuildingConfig.spec.luau` reads all four of those doc tables.
- All 17 specs pass (2,801 checks).
