# Robux products and passes

The checklist for creating this game's game passes and developer products on the Creator Hub, and the list of what to create. Every item below is built and tested in Studio with simulated purchases; the only thing missing is its id. What to sell comes from `docs/GAME_DESIGN.md` ("Monetization").

All items belong to the game (universe 10778596196, owned by group 921449746). Icons are uploaded as the group (`python tools/upload_models.py <png>`); drafts for review are in `store-assets/icons/`.

## Creating an item

1. Creator Hub → the game → Monetization → **Passes** (bought once) or **Developer Products** (bought any number of times) → Create.
2. Name, description and icon (512 x 512 PNG, uploaded as the group). Set the price and make it **On Sale**.
3. Copy its id into `src/replicated/MonetizationConfig.luau`: the pass's or product's `Id`. Check its `ExpectedPrice` is the price you set.
4. **Gifts.** Every pass and every product can be bought for another player in the server, through a second **developer product** at the same price, named "Gift: <name>". Its id goes in the item's `GiftId` (passes too: a gifted pass is saved in the recipient's data, since Roblox has no record of it).
5. Every item's `Reward.Kind` already has a handler (`src/server/RobuxPerks.luau`).
6. The Mythic Block is a paid random item (`PaidRandom = true`, with `Odds`): the shop shows its odds behind an INFO button before purchase, and players where paid random items are restricted can't buy it or be gifted it (PolicyService).
7. Start a Play in Studio: `[PriceCheck] 24 items checked, 0 problems, 0 hidden` in Output means every id and price matches (12 items and 12 gift products).
8. Before launch: one real test purchase of a pass and of a product (`docs/LAUNCH_CHECKLIST.md`).

## Items to create (24: 6 passes, 6 products, 12 gift products)

Copy the name, description and price straight onto the Creator Hub. Paste each id into `MonetizationConfig.luau` (the Key column finds the entry).

### Game passes

| Key | Name | Price (Robux) | Store description | Id | Gift product (developer product, same price) | Gift id |
|---|---|---|---|---|---|---|
| DoubleCrystals | 2x Crystals | 249 | Doubles all your crystals, forever. | | Gift: 2x Crystals | |
| AutoPick | Auto Pick | 149 | Taps the ice 5 times a second for you while you're in your plot. | | Gift: Auto Pick | |
| VIP | VIP | 299 | +20% crystals, a gold name tag and the VIP lounge in the plaza. | | Gift: VIP | |
| ExtraPetSlot | Extra Pet Slot | 449 | One more pet follows you. | | Gift: Extra Pet Slot | |
| PetSquad | Pet Squad | 899 | Two more pets follow you (with Extra Pet Slot, +3 in all). | | Gift: Pet Squad | |
| LuckyIce | Lucky Ice | 349 | Doubles your chance of Legendary and Mythic blocks. | | Gift: Lucky Ice | |

### Developer products

| Key | Name | Price (Robux) | Store description | Id | Gift product (same price) | Gift id |
|---|---|---|---|---|---|---|
| CrystalPouch | Crystal Pouch | 29 | 10 minutes of your crystal income, right now. | | Gift: Crystal Pouch | |
| CrystalSack | Crystal Sack | 149 | 1 hour of your crystal income, right now. | | Gift: Crystal Sack | |
| CrystalChest | Crystal Chest | 499 | 6 hours of your crystal income, right now. | | Gift: Crystal Chest | |
| ShatterNow | Shatter Now | 25 | Breaks your current ice block instantly and frees the creature. | | Gift: Shatter Now | |
| ServerFrostRush | Server Frost Rush | 99 | x2 crystals for everyone in the server for 15 minutes, with your name announced. | | Gift: Server Frost Rush | |
| MythicBlock | Mythic Block | 199 | Your next ice block rolls with much better odds: 50% Rare, 30% Epic, 15% Legendary, 5% Mythic. | | Gift: Mythic Block | |

Gift product description (the same for each): "A gift: <name> for another player in your server."

## What each item does (as built)

- **Passes** count the moment they're bought (no rejoin), and gifted passes count the moment the gift arrives.
- **2x Crystals** and **VIP** multiply every crystal (x2 and x1.2). **Auto Pick** taps 5 times a second on the server while you stand in your own plot; with your own taps it stays inside the 20-taps-a-second cap. **Lucky Ice** doubles the Legendary and Mythic chances of every block you roll (taken from Common). **VIP** also turns your name tag gold and opens the lounge door in the plaza. The pet-slot passes add equip slots.
- **Crystal bundles** pay 10 min / 1 h / 6 h of your income: building damage per second plus your tap damage at 4 taps a second, times your crystal multiplier at that moment.
- **Shatter Now** breaks the block on your mound. It can't be bought while the next block is still on its sled (the button hides then, and the server refuses). Its HUD button grows, turns gold and pulses when a Rare or better creature is inside.
- **Server Frost Rush** gives x2 crystals to everyone in the server for 15 minutes and announces the buyer; another one while it runs adds 15 minutes. It isn't saved, so it ends if the server shuts down.
- **Mythic Block**: your next block rolls 50% Rare / 30% Epic / 15% Legendary / 5% Mythic, from the whole roster (so the odds hold on any layer). It waits in your save until your next block arrives.
