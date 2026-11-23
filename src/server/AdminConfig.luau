-- Who may use the admin window (F3) in live servers. Server only (never sent to clients).
-- In Studio (including Test > Clients and Servers) every player may, for testing.
-- In a live server ONLY these user ids may. The server checks this on every command.
return {
	AllowedUserIds = {
		11704150663, -- the developer
	},

	RequestCooldownSeconds = 0.5, -- per player, between admin commands

	-- Launch: straight up, plus a little sideways; no damage.
	LaunchUpSpeed = 150, -- studs per second
	LaunchSideSpeed = 25,
	LaunchPushSeconds = 0.35,
	LaunchBusySeconds = 4, -- how long the target counts as "being launched" (one effect at a time)

	JailSeconds = 5, -- the cage around the target
	RocketUpSpeed = 90, -- studs per second, straight up...
	RocketPushSeconds = 1.2, -- ...for this long; then gravity brings them back down
}
