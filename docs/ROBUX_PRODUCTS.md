# Robux products and passes

The checklist for creating this game's game passes and developer products on the Creator Hub, and the list of what to create. Every item below is built and tested in Studio with simulated purchases; the only thing missing is its id. What to sell comes from `docs/GAME_DESIGN.md` ("Monetization").

All items belong to the game (universe 10778596196, owned by group 921449746). Icons are uploaded as the group (`python tools/upload_models.py <png>`); drafts for review are in `store-assets/icons/`.

## Created

All 28 items were created through Open Cloud on 2026-11-26 by `python tools/create_products.py` (on sale, icons from `store-assets/icons/`); their ids are in the tables below, in `MonetizationConfig.luau` and in `store-assets/icons/products_manifest.json`. The script is safe to re-run: it matches existing items by name and never makes duplicates (`--dry-run` lists without creating or changing).

**Changing a price:** edit the price in the table below and `ExpectedPrice` in `MonetizationConfig.luau` (they must agree), run `python tools/create_products.py --dry-run` to see what would change, then without `--dry-run`. It PATCHes the price of the item and its gift twin, then reads every item back and prints the price Roblox shows. The prices were last set this way on 2026-11-26 (Phase 4 of `OVERNIGHT_FINAL_REPORT.md`).

**Changing a description:** edit the store description in the table below and run the same two commands. The script PATCHes the description of any item whose Roblox description differs from the table (a gift twin's is always "A gift: <name> for another player in your server."), then reads every item back and prints its description. Auto Pick's ("2 times a second") was synced this way on 2026-11-28.

## Creating an item by hand

1. Creator Hub → the game → Monetization → **Passes** (bought once) or **Developer Products** (bought any number of times) → Create.
2. Name, description and icon (512 x 512 PNG, uploaded as the group). Set the price and make it **On Sale**.
3. Copy its id into `src/replicated/MonetizationConfig.luau`: the pass's or product's `Id`. Check its `ExpectedPrice` is the price you set.
4. **Gifts.** Every pass and every product can be bought for another player in the server, through a second **developer product** at the same price, named "Gift: <name>". Its id goes in the item's `GiftId` (passes too: a gifted pass is saved in the recipient's data, since Roblox has no record of it).
5. Every item's `Reward.Kind` already has a handler (`src/server/RobuxPerks.luau`).
6. The Mythic Block and the Mythic Block x3 are paid random items (`PaidRandom = true`, with `Odds`): the shop shows its odds behind an INFO button before purchase, and players where paid random items are restricted can't buy it or be gifted it (PolicyService).
7. Start a Play in Studio: `[PriceCheck] 28 items checked, 0 problems, 0 hidden` in Output means every id and price matches (14 items and 14 gift products).
8. Before launch: one real test purchase of a pass and of a product (`docs/LAUNCH_CHECKLIST.md`).

## Items (28: 6 passes, 8 products, 14 gift products)

Copy the name, description and price straight onto the Creator Hub. Paste each id into `MonetizationConfig.luau` (the Key column finds the entry).

### Game passes

| Key | Name | Price (Robux) | Store description | Id | Gift product (developer product, same price) | Gift id |
|---|---|---|---|---|---|---|
| DoubleCrystals | 2x Crystals | 349 | Doubles all your crystals, forever. | 2102063611 | Gift: 2x Crystals | 3736501716 |
| AutoPick | Auto Pick | 199 | Taps the ice 2 times a second for you while you're in your plot. | 2100372547 | Gift: Auto Pick | 3736501737 |
| VIP | VIP | 299 | +20% crystals, a gold name tag and the VIP lounge in the plaza. | 2098692454 | Gift: VIP | 3736501753 |
| ExtraPetSlot | Extra Pet Slot | 399 | One more pet follows you. | 2099292504 | Gift: Extra Pet Slot | 3736501769 |
| PetSquad | Pet Squad | 699 | Two more pets follow you (with Extra Pet Slot, +3 in all). | 2101811657 | Gift: Pet Squad | 3736501785 |
| LuckyIce | Lucky Ice | 349 | Doubles your chance of Legendary and Mythic blocks. | 2100576395 | Gift: Lucky Ice | 3736501801 |

### Developer products

| Key | Name | Price (Robux) | Store description | Id | Gift product (same price) | Gift id |
|---|---|---|---|---|---|---|
| CrystalPouch | Crystal Pouch | 29 | 10 minutes of your crystal income, right now. | 3736501812 | Gift: Crystal Pouch | 3736501820 |
| CrystalSack | Crystal Sack | 99 | 1 hour of your crystal income, right now. | 3736501831 | Gift: Crystal Sack | 3736501841 |
| CrystalChest | Crystal Chest | 499 | 6 hours of your crystal income, right now. | 3736501853 | Gift: Crystal Chest | 3736501858 |
| GiantCrystalChest | Giant Crystal Chest | 999 | 24 hours of your crystal income, right now. | 3736773791 | Gift: Giant Crystal Chest | 3736773801 |
| ShatterNow | Shatter Now | 29 | Breaks your current ice block instantly and frees the creature. | 3736501870 | Gift: Shatter Now | 3736501879 |
| ServerFrostRush | Server Frost Rush | 99 | x2 crystals for everyone in the server for 15 minutes, with your name announced. | 3736501890 | Gift: Server Frost Rush | 3736501900 |
| MythicBlock | Mythic Block | 199 | Your next ice block rolls with much better odds: 50% Rare, 30% Epic, 15% Legendary, 5% Mythic. | 3736501911 | Gift: Mythic Block | 3736501923 |
| MythicBlock3 | Mythic Block x3 | 499 | Your next three ice blocks roll with much better odds, each: 50% Rare, 30% Epic, 15% Legendary, 5% Mythic. | 3736773813 | Gift: Mythic Block x3 | 3736773819 |

Gift product description (the same for each): "A gift: <name> for another player in your server."

## What each item does (as built)

- **Passes** count the moment they're bought (no rejoin), and gifted passes count the moment the gift arrives.
- **2x Crystals** and **VIP** multiply every crystal (x2 and x1.2). **Auto Pick** taps 2 times a second on the server while you stand in your own plot; with your own taps it stays inside the 10-taps-a-second cap. **Lucky Ice** doubles the Legendary and Mythic chances of every block you roll (taken from Common). **VIP** also turns your name tag gold and opens the lounge door in the plaza. The pet-slot passes add equip slots.
- **Crystal bundles** pay 10 min / 1 h / 6 h / 24 h of your income (Pouch, Sack, Chest, Giant Crystal Chest): the HUD's crystals per second with the permanent bonuses but no rushes, your taps counted at least 4 a second (`Economy.SteadyIncome`).
- **Shatter Now** breaks the block on your mound. It can't be bought while the next block is still on its sled (the button hides then, and the server refuses). Its HUD button grows, turns gold and pulses when a Rare or better creature is inside.
- **Server Frost Rush** gives x2 crystals to everyone in the server for 15 minutes and announces the buyer; another one while it runs adds 15 minutes. It isn't saved, so it ends if the server shuts down.
- **Mythic Block**: your next block rolls 50% Rare / 30% Epic / 15% Legendary / 5% Mythic, from the whole roster (so the odds hold on any layer). It waits in your save until your next block arrives. **Mythic Block x3** adds three waiting blocks, each rolled with the same odds, one after another.
