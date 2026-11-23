-- Who may use the debug menu outside Studio. Server only (never sent to clients).
-- In Studio (including Test > Clients and Servers) every player has access automatically.
-- In a live server ONLY the user ids listed here do. Keep it empty unless you need it, and remove
-- ids again when you're done.
return {
	AllowedUserIds = {
		-- 12345678, -- example: a developer's user id
	},

	RequestCooldownSeconds = 0.1, -- per player, between debug requests
}
