-- GameConfig spec, and the template for new specs. tests/ is outside the Rojo mappings, so specs are
-- never part of the game.
--
-- Run: python tools/run_specs.py GameConfig (every spec: python tools/run_specs.py). The runner sends
-- every .luau file under src/ and tests/ to Studio (Edit mode) as `sources` (name -> source text)
-- and calls this function with it; it returns the number of checks that passed.
--
-- Load modules with loadstring(sources.X)() so every run gets a fresh copy of the current source.
-- Use fakes for players, DataStores and MarketplaceService: a spec never touches a real save, a
-- live Instance or a real purchase.
return function(sources)
	local passed = 0
	local function check(condition, message)
		assert(condition, message)
		passed += 1
	end

	local GameConfig = assert(loadstring(sources.GameConfig))()

	check(type(GameConfig) == "table", "GameConfig returns a table")
	check(type(GameConfig.Version) == "number", "GameConfig has a Version number")
	check(GameConfig.GameName == "Rescue Pets From the Ice", "GameConfig names the game")

	return passed
end
