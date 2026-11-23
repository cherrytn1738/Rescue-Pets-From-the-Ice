# Robux products and passes

The checklist for creating this game's game passes and developer products on the Creator Hub, and the list of what exists. Nothing is on sale yet: `src/replicated/MonetizationConfig.luau` is empty. What to sell comes from `docs/GAME_DESIGN.md`.

All items belong to the game (universe 10778596196, owned by group 921449746). Icons are uploaded as the group (`python tools/upload_models.py <png>`).

## Creating an item

1. Creator Hub → the game → Monetization → **Passes** (bought once) or **Developer Products** (bought any number of times) → Create.
2. Name, description and icon (512 x 512 PNG, uploaded as the group). Set the price and make it **On Sale**.
3. Copy its id into `MonetizationConfig.luau` with `ExpectedPrice` = that price (see the file's header for every field).
4. A developer product that can be gifted needs a **second** developer product at the same price, named "Gift: <name>": its id is the item's `GiftId`.
5. A product's `Reward.Kind` needs a handler in `src/server/PurchaseRewards.luau` (`PurchaseRewards.Kinds`).
6. A paid random item (a random reward, or anything that changes the odds of one) gets `PaidRandom = true` and its `Odds`; the shop shows them before purchase, and restricted regions can't buy it.
7. Start a Play in Studio: `[PriceCheck] N items checked, 0 problems` in Output means every id and price matches.
8. Before launch: one real test purchase of a pass and of a product.

## Items

| Key | Kind | Name | Price (Robux) | Id | Gift id | Reward |
|---|---|---|---|---|---|---|
| | | | | | | |
