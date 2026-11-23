"""Spec runner: runs the specs in tests/ inside Roblox Studio (Edit mode), through Studio's own MCP
server (StudioMCP, started by %LOCALAPPDATA%\\Roblox\\mcp.bat).

    python tools/run_specs.py                 every tests/*.spec.luau
    python tools/run_specs.py PlayerData Codes   only these specs (names without .spec.luau)
    python tools/run_specs.py --list          just list the specs it would run

Needs Roblox Studio open with any place (Edit mode, not Play) and Assistant > ... > Manage MCP
Servers > "Enable Studio as MCP server" on. If several Studios are open, pass --studio <id> (the
script prints the ids it sees).

How it works: it reads every .luau file under src/ and tests/ and sends them to Studio as one
`sources` table (name -> source text), the same table the old copy-a-spec-into-src/server
procedure built from the DataModel. Each spec is `function(sources) -> passed count` and loads the
modules it tests with loadstring(sources.X)(), so nothing is synced into the place, nothing is left
behind, and Rojo doesn't need to be running. Specs use fakes (tests/FakeDataStore.luau, fake
players); they never touch a real DataStore or purchase.

Names follow Rojo: src/server/PlayerData.luau -> "PlayerData", ServerMain.server.luau ->
"ServerMain", tests/FakeDataStore.luau -> "FakeDataStore", tests/Codes.spec.luau -> "CodesSpec".
"""
import argparse
import json
import os
import pathlib
import queue
import re
import subprocess
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
MCP_BAT = os.path.expandvars(r"%LOCALAPPDATA%\Roblox\mcp.bat")
CALL_TIMEOUT = 300


def module_name(path: pathlib.Path) -> str:
    name = path.name
    for suffix in (".server.luau", ".client.luau", ".luau"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    if name == "init":
        name = path.parent.name
    if name.endswith(".spec"):
        name = name[: -len(".spec")] + "Spec"
    return name


def collect_sources() -> dict:
    """name -> source. A Script and a ModuleScript may share a name in different services (the
    server's OfflineEarnings module and the client's OfflineEarnings popup): the plain name is the
    ModuleScript's, and every Script/LocalScript is also under "<Name>.server" / "<Name>.client"."""
    sources, owners = {}, {}
    for folder in ("src", "tests"):
        for path in sorted((ROOT / folder).rglob("*.luau")):
            name = module_name(path)
            text = path.read_text(encoding="utf-8")
            kind = next((k for k in ("server", "client") if path.name.endswith(f".{k}.luau")), None)
            if kind:
                sources[f"{name}.{kind}"] = text
            if name in owners:
                if kind is None and owners[name] is not None:
                    pass  # a module takes the plain name from a script
                elif kind is not None and owners[name] is None:
                    continue  # the module already has it
                else:
                    raise SystemExit(f"two modules map to the name {name!r}: rename one ({path})")
            sources[name], owners[name] = text, kind
    return sources


def long_string(text: str) -> str:
    level = 0
    while ("]" + "=" * level + "]") in text:
        level += 1
    eq = "=" * level
    # A newline right after the opening bracket is dropped by Luau, so add one to keep the text exact.
    return f"[{eq}[\n{text}]{eq}]"


def build_chunk(sources: dict, spec: str) -> str:
    lines = ["local sources = {}"]
    for name, text in sources.items():
        lines.append(f"sources[{json.dumps(name)}] = {long_string(text)}")
    lines.append(
        f"""
local specSource = sources[{json.dumps(spec)}]
local chunk, compileError = loadstring(specSource, "={spec}")
if not chunk then
	return "SPEC_RESULT FAIL compile: " .. tostring(compileError)
end
local ok, result = xpcall(function()
	return chunk()(sources)
end, function(message)
	return tostring(message) .. "\\n" .. debug.traceback()
end)
if ok then
	return "SPEC_RESULT PASS " .. tostring(result)
end
return "SPEC_RESULT FAIL " .. tostring(result)
"""
    )
    return "\n".join(lines)


class StudioMcp:
    """The smallest MCP client that works with StudioMCP: JSON-RPC over stdio, one line per message."""

    def __init__(self):
        if not os.path.exists(MCP_BAT):
            raise SystemExit(f"Studio's MCP launcher is missing: {MCP_BAT} (install or update Roblox Studio)")
        self.proc = subprocess.Popen(
            ["cmd.exe", "/c", MCP_BAT], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        self.lines = queue.Queue()
        self.next_id = 1
        threading.Thread(target=self._read, daemon=True).start()
        self.request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "run_specs", "version": "1"},
        })
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    def _read(self):
        for raw in self.proc.stdout:
            self.lines.put(raw)

    def _send(self, message):
        self.proc.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
        self.proc.stdin.flush()

    def request(self, method, params, timeout=60):
        rid = self.next_id
        self.next_id += 1
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        while True:
            try:
                raw = self.lines.get(timeout=timeout)
            except queue.Empty:
                raise SystemExit(f"Studio's MCP server didn't answer {method} within {timeout} s")
            try:
                message = json.loads(raw)
            except ValueError:
                continue
            if message.get("id") == rid:
                if "error" in message:
                    raise SystemExit(f"MCP error on {method}: {message['error']}")
                return message["result"]

    def call(self, tool, args, timeout=CALL_TIMEOUT) -> str:
        result = self.request("tools/call", {"name": tool, "arguments": args}, timeout)
        text = "\n".join(item.get("text", "") for item in result.get("content", []) if item.get("type") == "text")
        return ("TOOL ERROR: " + text) if result.get("isError") else text

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.terminate()
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description="Run tests/*.spec.luau in Roblox Studio through its MCP server.")
    parser.add_argument("specs", nargs="*", help="spec names without .spec.luau (default: all)")
    parser.add_argument("--studio", help="studio_id from list_roblox_studios, when several Studios are open")
    parser.add_argument("--list", action="store_true", help="list the specs and exit")
    options = parser.parse_args()

    sources = collect_sources()
    available = sorted(name[: -len("Spec")] for name in sources if name.endswith("Spec"))
    wanted = options.specs or available
    unknown = [name for name in wanted if name not in available]
    if unknown:
        raise SystemExit(f"no such spec: {', '.join(unknown)} (have: {', '.join(available)})")
    if options.list:
        print("\n".join(wanted))
        return 0

    client = StudioMcp()
    try:
        # A freshly started MCP server takes a few seconds to find the open Studios.
        studios = []
        for _ in range(15):
            studios = json.loads(client.call("list_roblox_studios", {}, 60) or "{}").get("studios", [])
            if studios:
                break
            time.sleep(2)
        if not studios:
            raise SystemExit("No Studio is connected: open a place in Studio and enable Studio as MCP server.")
        base = {"datamodel_type": "Edit"}
        if options.studio:
            base["studio_id"] = options.studio
        elif len(studios) > 1:
            print("Several Studios are connected; using the active one. Pass --studio <id> to pick:")
            for studio in studios:
                print("  ", json.dumps(studio))

        failures = 0
        total = 0
        for spec in wanted:
            output = client.call("execute_luau", dict(base, code=build_chunk(sources, spec + "Spec")))
            match = re.search(r"SPEC_RESULT (PASS|FAIL) ?(.*)", output, re.S)
            if match and match.group(1) == "PASS":
                count = match.group(2).strip().strip('"')
                total += int(count) if count.isdigit() else 0
                print(f"PASS  {spec:<20} {count} checks")
            else:
                failures += 1
                detail = match.group(2).strip() if match else output.strip()
                print(f"FAIL  {spec:<20} {detail}")
        print(f"\n{len(wanted) - failures}/{len(wanted)} specs passed, {total} checks")
        return 1 if failures else 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
