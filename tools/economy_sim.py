"""Economy simulation runner: plays tools/economy/EconomySim.luau in Roblox Studio (Edit mode) with
the game's real config modules, and prints the report (time to the first building, first rescue,
each layer, and the first rebirth), checked against the design doc's targets.

    python tools/economy_sim.py            every tap speed's first run, then the 4 taps/s player for 8 runs (3 seeds)
    python tools/economy_sim.py --first    the first runs only (quicker)
    python tools/economy_sim.py --runs=12  more runs for the 4 taps/s player

Needs Studio open with "Enable Studio as MCP server" on, like tools/run_specs.py (it reuses its
MCP client and source collection).
"""
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from run_specs import StudioMcp, collect_sources, long_string  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    sources = collect_sources()
    if "--first" in sys.argv:
        sources["SimOnly"] = "first"
    for arg in sys.argv[1:]:
        if arg.startswith("--runs="):
            sources["SimRuns"] = arg.split("=", 1)[1]
    sim = (ROOT / "tools" / "economy" / "EconomySim.luau").read_text(encoding="utf-8")
    lines = ["local sources = {}"]
    for name, text in sources.items():
        lines.append(f"sources[{json.dumps(name)}] = {long_string(text)}")
    lines.append(f"local sim = {long_string(sim)}")
    lines.append("""
local chunk = assert(loadstring(sim, "=EconomySim"))
local ok, result = xpcall(function() return chunk()(sources) end, function(m) return tostring(m) .. "\\n" .. debug.traceback() end)
return (if ok then "SIM_OK\\n" else "SIM_FAIL\\n") .. tostring(result)
""")
    client = StudioMcp()
    try:
        for _ in range(15):
            studios = json.loads(client.call("list_roblox_studios", {}, 60) or "{}").get("studios", [])
            if studios:
                break
            time.sleep(2)
        output = client.call("execute_luau", {"datamodel_type": "Edit", "code": "\n".join(lines)}, 600)
    finally:
        client.close()
    text = output.strip().strip('"').replace("\\n", "\n")
    print(text)
    return 0 if "SIM_OK" in text else 1


if __name__ == "__main__":
    sys.exit(main())
