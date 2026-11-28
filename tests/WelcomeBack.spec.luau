-- WelcomeBack spec: the Welcome Back screen's x2 offer, the developer product Double Welcome Back (WelcomeBackRules, the
-- server's WelcomeBack and its reward kind through the real PurchaseRewards and MonetizationConfig). The offer is saved
-- when offline earnings are paid; x2 can be prompted only while it is open; a receipt pays only a prompted offer, its
-- saved amount, once; Claim! closes it; a late, replayed or second receipt pays nothing.
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end

	local Rules = assert(loadstring(sources.WelcomeBackRules, "WelcomeBackRules"))()
	local S = Rules.Settings
	check(S.OfferSeconds >= 300 and S.OfferSeconds <= 1800, "the x2 stays on offer for a few minutes after the screen opens")
	check(S.PendingSeconds >= 3600, "a prompted offer waits for its receipt (a server stop between purchase and grant)")

	-- Clean: a saved offer as it may be trusted.
	local clean = Rules.Clean({ Amount = 500.5, At = 1000, Prompted = 1010, Extra = "x" })
	check(clean and clean.Amount == 500.5 and clean.At == 1000 and clean.Prompted == 1010 and clean.Extra == nil, "a saved offer loads exactly")
	for _, bad in { "x", { Amount = -1, At = 5 }, { Amount = 0, At = 5 }, { Amount = 0 / 0, At = 5 }, { Amount = math.huge, At = 5 },
		{ Amount = 5, At = 1.5 }, { Amount = 5, At = 5, Prompted = "soon" }, { At = 5 } } do
		check(Rules.Clean(bad) == nil, "an unreadable offer is no offer")
	end

	-- Make: a payout makes an offer.
	local offer, made = Rules.Make(nil, 1200, 1000)
	check(made and offer.Amount == 1200 and offer.At == 1000 and offer.Prompted == nil, "a payout makes an offer of that amount")
	check(Rules.IsOpen(offer, 1000) and Rules.IsOpen(offer, 1000 + S.OfferSeconds - 1), "open while its time lasts")
	check(not Rules.IsOpen(offer, 1000 + S.OfferSeconds), "...and closed after OfferSeconds")
	check(Rules.PromptProblem(offer, 1000 + S.OfferSeconds) ~= nil and Rules.PromptProblem(nil, 1000) ~= nil, "an ended or missing offer can't be prompted")
	local view = Rules.View(offer, 1010)
	check(view and view.Amount == 1200 and view.Until == 1000 + S.OfferSeconds, "the screen sees the amount and until when")
	check(Rules.View(offer, 1000 + S.OfferSeconds) == nil, "...and nothing once it has ended")

	-- Prompting and the prompt's end.
	check(Rules.PromptProblem(offer, 1010) == nil, "an open offer can be prompted")
	Rules.Prompt(offer, 1010)
	check(offer.Prompted == 1010 and not Rules.IsOpen(offer, 1011) and Rules.PromptProblem(offer, 1011) ~= nil, "a prompted offer can't be prompted again")
	check(Rules.View(offer, 1011) == nil, "...and the screen hides x2 while the purchase runs")
	Rules.PromptClosed(offer, false)
	check(offer.Prompted == nil and Rules.IsOpen(offer, 1012), "a prompt closed without buying opens the offer again")
	Rules.Prompt(offer, 1020)
	Rules.PromptClosed(offer, true)
	check(offer.Prompted == 1020, "a prompt closed with a purchase keeps it waiting for its receipt")

	-- Grant: only a prompted offer pays, its own amount.
	check(Rules.Grant(offer) == 1200, "the receipt pays the prompted offer's saved amount")
	check(Rules.Grant(nil) == nil and Rules.Grant({ Amount = 5, At = 1000 }) == nil, "no offer, or one never prompted, pays nothing")

	-- Claim.
	check(Rules.Claim({ Amount = 5, At = 1000 }) == nil, "Claim! closes an offer that isn't prompted")
	check(Rules.Claim(offer) == offer, "...but keeps one whose purchase may be on its way")

	-- A new payout never replaces a pending offer (its receipt must pay what was bought).
	local kept, newOne = Rules.Make(offer, 99999, 1020 + 60)
	check(kept == offer and not newOne and kept.Amount == 1200, "a later payout keeps a prompted offer that's still waiting")
	local replaced, newTwo = Rules.Make(offer, 99999, 1020 + S.PendingSeconds)
	check(newTwo and replaced.Amount == 99999 and replaced.Prompted == nil, "...until PendingSeconds have passed")
	check(Rules.Make(nil, 0, 1000) == nil and Rules.Make(nil, 0 / 0, 1000) == nil, "nothing paid, no offer")

	-- The server module and its reward kind, through the real PurchaseRewards and MonetizationConfig.
	local now = 5000
	local players = {}
	local function newPlayer(name)
		local attributes = {}
		local player = { Name = name, UserId = #players + 1, attributes = attributes }
		function player:SetAttribute(key, value)
			attributes[key] = value
		end
		table.insert(players, player)
		return player
	end
	local datas, granted, important, paidHooks, loadedHooks = {}, {}, 0, {}, {}
	local fakePlayerData = {
		Edit = function(player)
			return datas[player]
		end,
		MarkImportant = function()
			important += 1
		end,
		OnLoaded = function(callback)
			table.insert(loadedHooks, callback)
		end,
	}
	local server = {
		PlayerData = fakePlayerData,
		Economy = { Grant = function(player, data, amount, source, sku)
			data.Crystals += amount
			table.insert(granted, { player = player, amount = amount, source = source, sku = sku })
		end },
		OfflineEarnings = { OnPaid = function(callback)
			table.insert(paidHooks, callback)
		end },
		PaidRandomPolicy = { IsAllowed = function()
			return true
		end, REFUSED = "restricted" },
	}
	local function encode(value)
		return `{value.Amount}|{value.Until}`
	end
	local replicated = {
		WelcomeBackRules = Rules,
		NumberFormat = assert(loadstring(sources.NumberFormat, "NumberFormat"))(),
		MonetizationConfig = assert(loadstring(sources.MonetizationConfig, "MonetizationConfig"))(),
	}
	local function load(name)
		local chunk = assert(loadstring(sources[name], name))
		setfenv(chunk, setmetatable({
			game = { GetService = function(_, service)
				if service == "HttpService" then
					return { JSONEncode = function(_, value)
						return encode(value)
					end }
				end
				return replicated
			end },
			script = { Parent = server },
			require = function(module)
				return module
			end,
			os = { time = function()
				return now
			end },
			warn = function() end,
		}, { __index = getfenv(1) }))
		return chunk()
	end
	server.PurchaseRewards = load("PurchaseRewards")
	local PurchaseRewards = server.PurchaseRewards
	local WelcomeBack = load("WelcomeBack")
	WelcomeBack.Start()
	check(#paidHooks == 1 and #loadedHooks == 1, "WelcomeBack listens to offline payouts and loads")
	local product = replicated.MonetizationConfig.GetProduct("DoubleWelcomeBack")
	check(product and product.Reward.Kind == "WelcomeBackDouble" and PurchaseRewards.Kinds.WelcomeBackDouble ~= nil, "the product's reward kind is registered")

	local me = newPlayer("Me")
	datas[me] = { Crystals = 0 }
	-- A payout makes the offer and tells the screen.
	paidHooks[1](me, datas[me], 1500, 7200)
	check(datas[me].WelcomeBack.Amount == 1500 and me.attributes.WelcomeBackOffer == `1500|{now + S.OfferSeconds}`, "a payout saves the offer and shows x2")
	-- A receipt without a prompt pays nothing.
	local given, problem = PurchaseRewards.Give(me, product, { Key = product.Key })
	check(given == nil and problem ~= nil and datas[me].Crystals == 0, "a receipt for an offer never prompted pays nothing")
	-- The shop prompts it.
	check(PurchaseRewards.CanGive(me, product, { Prompting = true }), "x2 can be prompted while the offer is open")
	PurchaseRewards.Prompting(me, product)
	check(datas[me].WelcomeBack.Prompted == now and important == 1 and me.attributes.WelcomeBackOffer == nil, "the prompt marks it (saved soon) and hides x2")
	check(not PurchaseRewards.CanGive(me, product, { Prompting = true }), "...and it can't be prompted twice")
	-- Claim! while the purchase runs doesn't close it.
	check(PurchaseRewards.Close(me, product) and datas[me].WelcomeBack ~= nil, "Claim! during the purchase keeps the offer for its receipt")
	-- The receipt pays the saved amount, once.
	given = PurchaseRewards.Give(me, product, { Key = product.Key })
	check(given ~= nil and datas[me].Crystals == 1500 and granted[1].amount == 1500 and granted[1].source == "Bundle" and granted[1].sku == "DoubleWelcomeBack",
		"the receipt pays the offer's amount once more (analytics: a bundle, DoubleWelcomeBack)")
	check(datas[me].WelcomeBack == nil and me.attributes.WelcomeBackOffer == nil, "...and the offer is gone")
	given = PurchaseRewards.Give(me, product, { Key = product.Key })
	check(given == nil and datas[me].Crystals == 1500, "a second receipt (another purchase, or a late one) pays nothing")
	check(not PurchaseRewards.CanGive(me, product, { Prompting = true }), "and x2 can't be bought again")

	-- Claim! without buying closes the offer: a receipt after that pays nothing.
	paidHooks[1](me, datas[me], 800, 3600)
	check(PurchaseRewards.Close(me, product) and datas[me].WelcomeBack == nil and me.attributes.WelcomeBackOffer == nil, "Claim! closes an open offer")
	check(not PurchaseRewards.CanGive(me, product, { Prompting = true }) and PurchaseRewards.Give(me, product, { Key = product.Key }) == nil
		and datas[me].Crystals == 1500, "...after which x2 can't be prompted and a receipt pays nothing")

	-- A prompt closed without buying: open again, and it still pays only after a new prompt.
	paidHooks[1](me, datas[me], 300, 3600)
	PurchaseRewards.Prompting(me, product)
	PurchaseRewards.PromptFinished(me, product, false)
	check(datas[me].WelcomeBack.Prompted == nil and me.attributes.WelcomeBackOffer ~= nil, "a cancelled prompt shows x2 again")
	-- The offer ends: x2 can't be prompted, and a load drops it.
	now += S.OfferSeconds
	check(not PurchaseRewards.CanGive(me, product, { Prompting = true }), "x2 can't be prompted once the offer has ended")
	loadedHooks[1](me)
	check(datas[me].WelcomeBack == nil and me.attributes.WelcomeBackOffer == nil, "an ended offer is dropped at load")

	-- A purchase on its way survives a rejoin with a new payout, and pays the amount bought, not the new one.
	paidHooks[1](me, datas[me], 400, 3600)
	PurchaseRewards.Prompting(me, product)
	PurchaseRewards.PromptFinished(me, product, true)
	now += 120 -- the server stopped before the receipt; the player rejoins two minutes later
	loadedHooks[1](me)
	paidHooks[1](me, datas[me], 999999, 120)
	check(datas[me].WelcomeBack.Amount == 400 and me.attributes.WelcomeBackOffer == nil, "a new payout keeps the offer still waiting for its receipt (no x2 shown)")
	local before = datas[me].Crystals
	given = PurchaseRewards.Give(me, product, { Key = product.Key })
	check(given ~= nil and datas[me].Crystals == before + 400, "the late receipt pays what was bought (400), not the new payout")

	-- The product itself: hidden from the shop, never a gift, 19 Robux.
	check(product.ExpectedPrice == 19 and product.ShopHidden and product.Tab == nil, "Double Welcome Back: 19 Robux, not listed in the shop")
	check(product.NoGift and product.GiftId == 0 and replicated.MonetizationConfig.GetGiftable("DoubleWelcomeBack") == nil, "...and can't be gifted")

	return passed
end
