--[[
WelcomeBackRules: the "Double Welcome Back" offer (docs/GAME_DESIGN.md, "Offline earnings" and "Monetization").
Pure functions, so tests/WelcomeBack.spec.luau runs every case; the server (WelcomeBack) applies them and the
Welcome Back screen (OfflineEarningsPopup.client) only shows the result.

When a returning player is paid their offline earnings, the server saves an offer in their data:
	WelcomeBack = { Amount, At, Prompted? }
 * Amount: the crystals they were just paid. Buying x2 pays exactly that much again, once.
 * At: the server's os.time() when the offer was made.
 * Prompted: the server's os.time() when Roblox's purchase prompt opened for it (a purchase may be on its way).
Rules:
 * The x2 can be prompted while the offer is OPEN: made less than OfferSeconds ago and not prompted.
 * A receipt pays only a prompted offer: its saved Amount, once; then the offer is gone. A receipt that finds
   no prompted offer pays nothing (the receipt handler answers NotProcessedYet), so a late or replayed receipt
   never pays twice and never pays another offer's amount.
 * A prompt closed without buying unprompts the offer (it can be prompted again while open).
 * Claim (the Claim! button) closes an offer that isn't prompted. A prompted one stays for its receipt.
 * A new offer never replaces a prompted one younger than PendingSeconds: its purchase may still arrive (a
   server that stopped between the purchase and the grant), and it must pay what was bought.
]]
local WelcomeBackRules = {}

WelcomeBackRules.Settings = {
	OfferSeconds = 600, -- how long the x2 button can be bought after the screen opens
	PendingSeconds = 86400, -- how long a prompted offer waits for its receipt before a new offer replaces it
}

local MAX_AMOUNT = 1e300 -- PlayerData's largest amount

local function isTime(value): boolean
	return type(value) == "number" and value == value and value > 0 and value < math.huge and value % 1 == 0
end

local function isAmount(value): boolean
	return type(value) == "number" and value == value and value > 0 and value <= MAX_AMOUNT
end

-- A saved offer as it may be trusted, or nil (missing, or anything that can't be read: no offer).
function WelcomeBackRules.Clean(value)
	if type(value) ~= "table" or not isAmount(value.Amount) or not isTime(value.At) then
		return nil
	end
	if value.Prompted ~= nil and not isTime(value.Prompted) then
		return nil
	end
	return { Amount = value.Amount, At = value.At, Prompted = value.Prompted }
end

-- Whether a prompted offer may still get its receipt (a new offer doesn't replace it yet).
function WelcomeBackRules.IsPending(offer, now: number): boolean
	return offer ~= nil and offer.Prompted ~= nil and now - offer.Prompted < WelcomeBackRules.Settings.PendingSeconds
end

-- The offer after a payout of `amount`: a new one, unless the old one is pending. Returns the offer to keep
-- and whether it is the new one.
function WelcomeBackRules.Make(old, amount: number, now: number)
	if WelcomeBackRules.IsPending(old, now) then
		return old, false
	end
	if not isAmount(amount) or not isTime(now) then
		return nil, false
	end
	return { Amount = amount, At = now }, true
end

-- Open: x2 can be prompted (made less than OfferSeconds ago, not prompted).
function WelcomeBackRules.IsOpen(offer, now: number): boolean
	if offer == nil or offer.Prompted ~= nil then
		return false
	end
	local age = now - offer.At
	return age >= 0 and age < WelcomeBackRules.Settings.OfferSeconds
end

-- Why x2 can't be prompted, or nil when it can.
function WelcomeBackRules.PromptProblem(offer, now: number): string?
	if offer == nil then
		return "There's no welcome-back reward to double."
	end
	if offer.Prompted ~= nil then
		return "That purchase is already on its way."
	end
	if not WelcomeBackRules.IsOpen(offer, now) then
		return "The welcome-back offer has ended."
	end
	return nil
end

-- The prompt opened (call only when IsOpen).
function WelcomeBackRules.Prompt(offer, now: number)
	offer.Prompted = now
end

-- The prompt closed. Bought: the offer waits for its receipt; not bought: open again (while its time lasts).
function WelcomeBackRules.PromptClosed(offer, purchased: boolean)
	if offer and not purchased then
		offer.Prompted = nil
	end
end

-- What a receipt pays: the prompted offer's Amount, or nil and why not.
function WelcomeBackRules.Grant(offer): (number?, string?)
	if offer == nil then
		return nil, "the welcome-back offer is closed (claimed, ended or already paid)"
	end
	if offer.Prompted == nil then
		return nil, "the welcome-back offer was never prompted"
	end
	return offer.Amount, nil
end

-- The offer after Claim!: gone, unless a purchase may be on its way.
function WelcomeBackRules.Claim(offer)
	if offer and offer.Prompted ~= nil then
		return offer
	end
	return nil
end

-- What the screen needs (the WelcomeBackOffer player attribute): { Amount, Until } while x2 can be bought, else nil.
function WelcomeBackRules.View(offer, now: number)
	if not WelcomeBackRules.IsOpen(offer, now) then
		return nil
	end
	return { Amount = offer.Amount, Until = offer.At + WelcomeBackRules.Settings.OfferSeconds }
end

return WelcomeBackRules
