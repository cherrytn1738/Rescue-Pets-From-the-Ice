--[[
FakeDataStore.luau (ModuleScript, tests only)

An in-memory stand-in for DataStoreService that can fail on purpose, so save code can be tested
without touching any real store. Used by tests/PlayerData.spec.luau (copied from the roblox-player-data skill).

  local fake = FakeDataStore.new()
  -- give the code under test fake.service as its DataStoreService, then:
  fake.saved.IcePets_PlayerData.Player_1 -- inspect (or seed) a stored record
  fake.outage.Player_1 = true          -- every request for that key errors
  fake.loseResponse.Player_1 = true    -- the NEXT write commits, then errors (a lost response)
  fake.calls["IcePets_PlayerData/Player_1"] -- how many UpdateAsync calls were made
  fake.opened.IcePets_PlayerData   -- true once that store name was opened

Values go through a JSON round trip, like a real DataStore, so the code under test never shares a
table with "the store" (a real one always hands back fresh copies).
]]
local HttpService = game:GetService("HttpService")

local FakeDataStore = {}

local function copy(value)
 if value == nil then return nil end
 return HttpService:JSONDecode(HttpService:JSONEncode(value))
end

function FakeDataStore.new()
 local fake = {saved = {}, calls = {}, outage = {}, loseResponse = {}, opened = {}, budget = 100}
 local stores = {}

 local function getStore(name)
  fake.opened[name] = true
  if stores[name] then return stores[name] end
  fake.saved[name] = fake.saved[name] or {}
  local data = fake.saved[name]
  local store = {}

  function store:UpdateAsync(key, transform)
   local id = name .. "/" .. key
   fake.calls[id] = (fake.calls[id] or 0) + 1
   if fake.outage[key] then error("simulated DataStore outage") end
   local value = transform(copy(data[key]), nil)
   if value == nil then return nil end -- the transform cancelled: nothing is written
   data[key] = copy(value)
   if fake.loseResponse[key] then
    fake.loseResponse[key] = nil
    error("simulated lost response (the write DID commit)")
   end
   return copy(value)
  end

  function store:GetAsync(key)
   if fake.outage[key] then error("simulated DataStore outage") end
   return copy(data[key])
  end

  function store:SetAsync(key, value)
   if fake.outage[key] then error("simulated DataStore outage") end
   data[key] = copy(value)
  end

  function store:RemoveAsync(key)
   if fake.outage[key] then error("simulated DataStore outage") end
   local old = data[key]
   data[key] = nil
   return copy(old)
  end

  -- OrderedDataStore reads: enough for leaderboard tests.
  function store:GetSortedAsync(ascending, pageSize)
   local items = {}
   for key, value in data do table.insert(items, {key = key, value = value}) end
   table.sort(items, function(a, b)
    if ascending then return a.value < b.value end
    return a.value > b.value
   end)
   local page = {}
   for index = 1, math.min(pageSize, #items) do page[index] = items[index] end
   return {IsFinished = true, GetCurrentPage = function() return page end}
  end

  stores[name] = store
  return store
 end

 fake.service = {}
 function fake.service:GetDataStore(name) return getStore(name) end
 function fake.service:GetOrderedDataStore(name) return getStore(name) end
 function fake.service:GetRequestBudgetForRequestType() return fake.budget end
 return fake
end

return FakeDataStore
