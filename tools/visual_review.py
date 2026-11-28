"""visual_review.py - takes the visual review screenshots (store-assets/visual-review/) in one command.

    python tools/visual_review.py                       # every shot
    python tools/visual_review.py buildings ui          # some categories
    python tools/visual_review.py --only ice/crack_stage2 --only ui/window_shop
    python tools/visual_review.py --list                # the shot names
    python tools/visual_review.py --index               # only rebuild the gallery's shot list

Before running: Studio open on the place, "Enable Studio as MCP server" on, Studio maximized and in
front (screen captures need it; a sleeping display makes them time out), and a solo Play running (Test >
Play). The shots are defined in tools/studio/visual_review_shots.luau; this script runs each shot's
setup on the client, clicks what it asks for, waits, captures the viewport, crops the shot's region and
saves it as JPG (quality 90): desktop shots at 1920x1080, phone shots at their own size (844x390,
667x375), named <category>/<name>[_<size>].jpg. A shot may ask for real mouse clicks at screen points first (TapAt: the
click burst on the ice).

Before / after: the first time a run replaces a picture, the old one is kept in
store-assets/visual-review-before/ (same names), and store-assets/visual-review/index.html shows them
side by side. Delete that folder to start a new comparison.

The game state changes a lot (the save is reset by some categories): use a throwaway Studio save.
"""
import argparse, base64, io, json, os, re, shutil, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from run_specs import StudioMcp  # noqa: E402

SHOTS_LUAU = os.path.join(HERE, "studio", "visual_review_shots.luau")
OUT = os.path.join(REPO, "store-assets", "visual-review")
BEFORE = os.path.join(REPO, "store-assets", "visual-review-before")
CATEGORY_ORDER = ["buildings", "tools", "tools-samples", "ice", "ice-options", "pets", "rescue", "world", "ui", "book", "effects"]


class Studio:
    def __init__(self, studio_id=None):
        self.mcp = StudioMcp()
        self.studio_id = studio_id
        if not self.studio_id:
            studios = []
            for _ in range(15):
                studios = json.loads(self.mcp.call("list_roblox_studios", {}, 60) or "{}").get("studios", [])
                if studios:
                    break
                time.sleep(2)
            playing = [s for s in studios if s.get("mode") == "Play"] or studios
            if not playing:
                sys.exit("No Studio found. Open the place and turn on 'Enable Studio as MCP server'.")
            self.studio_id = playing[0]["id"]
        self.source = open(SHOTS_LUAU, encoding="utf8").read()

    def luau(self, code, dm="Client", timeout=180):
        return self.mcp.call("execute_luau", {"code": code, "datamodel_type": dm, "studio_id": self.studio_id}, timeout)

    def shot_code(self, shot, size="desktop"):
        return self.source.replace('"%SHOT%"', json.dumps(shot)).replace('"%SIZE%"', json.dumps(size))

    def click(self, path, wait_ms=600):
        actions = [{"action": "moveTo", "instance_path": path}, {"action": "wait", "wait_time_ms": 150},
                   {"action": "mouseButtonDown", "mouse_button": "left"}, {"action": "wait", "wait_time_ms": 80},
                   {"action": "mouseButtonUp", "mouse_button": "left"}, {"action": "wait", "wait_time_ms": wait_ms}]
        return self.mcp.call("user_mouse_input", {"actions": actions, "datamodel_type": "Client", "studio_id": self.studio_id}, 60)

    def tap_at_aside(self, points):
        """Real mouse clicks at these points (GUI coordinates: below the top bar, as Camera:WorldToScreenPoint
        gives them; user_mouse_input's x/y use the same space), on a second connection (made once) so they go on
        while this one captures."""
        if not getattr(self, "aside", None):
            self.aside = StudioMcp()
        actions = []
        for x, y in points:
            actions += [{"action": "moveTo", "x": x, "y": y}, {"action": "wait", "wait_time_ms": 30},
                        {"action": "mouseButtonDown", "mouse_button": "left"}, {"action": "wait", "wait_time_ms": 40},
                        {"action": "mouseButtonUp", "mouse_button": "left"}, {"action": "wait", "wait_time_ms": 90}]
        return self.aside.call("user_mouse_input", {"actions": actions, "datamodel_type": "Client", "studio_id": self.studio_id}, 60)

    def capture(self, name):
        result = self.mcp.request("tools/call", {"name": "screen_capture", "arguments": {"capture_id": name, "studio_id": self.studio_id}}, 120)
        for item in result.get("content", []):
            if item.get("type") == "image":
                return base64.b64decode(item["data"])
        return None


def press_escape():
    """Closes Roblox's purchase prompt after its shot (Windows: a key press to the window in front)."""
    if sys.platform != "win32":
        return
    import ctypes
    ctypes.windll.user32.keybd_event(0x1B, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(0x1B, 0, 2, 0)


def parse_json(text):
    match = re.search(r"[\[{].*[\]}]", text or "", re.S)
    return json.loads(match.group(0)) if match else None


def save(png, path, region, viewport, size):
    from PIL import Image
    image = Image.open(io.BytesIO(png)).convert("RGB")
    # the capture may be the viewport at another scale: map the region onto it
    sx = image.width / viewport[0]
    sy = image.height / viewport[1]
    crop = image.crop((0, 0, round(region[0] * sx), round(region[1] * sy)))
    target = (1920, 1080) if size == "desktop" else tuple(int(v) for v in size.split("x"))
    if crop.size != target:
        crop = crop.resize(target, Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        keep = os.path.join(BEFORE, os.path.relpath(path, OUT))
        if not os.path.exists(keep):
            os.makedirs(os.path.dirname(keep), exist_ok=True)
            shutil.copy2(path, keep)
    crop.save(path, "JPEG", quality=90)


def file_for(name, size):
    category, base = name.split("/", 1)
    suffix = "" if size == "desktop" else "_" + size
    return os.path.join(OUT, category, base + suffix + ".jpg")


def write_index():
    """store-assets/visual-review/shots.js: every picture (and its 'before', if any) for index.html."""
    entries = []
    for category in sorted(os.listdir(OUT)) if os.path.isdir(OUT) else []:
        folder = os.path.join(OUT, category)
        if not os.path.isdir(folder):
            continue
        for file in sorted(os.listdir(folder)):
            if not file.lower().endswith(".jpg"):
                continue
            rel = f"{category}/{file}"
            before = os.path.join(BEFORE, category, file)
            entries.append({"category": category, "name": file[:-4], "file": rel,
                            "before": ("../visual-review-before/" + rel) if os.path.exists(before) else None})
    order = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    entries.sort(key=lambda e: (order.get(e["category"], 99), e["name"]))
    with open(os.path.join(OUT, "shots.js"), "w", encoding="utf8") as f:
        f.write("// Written by tools/visual_review.py: every picture in this folder, for index.html.\n")
        f.write("window.SHOTS = " + json.dumps(entries, indent=1) + ";\n")
    return len(entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("categories", nargs="*", help="categories to take (default: all)")
    parser.add_argument("--only", action="append", default=[], help="one shot by name (repeatable)")
    parser.add_argument("--size", action="append", default=[], help="only these sizes (desktop, 844x390, 667x375)")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--index", action="store_true", help="only rebuild shots.js for index.html")
    parser.add_argument("--studio", help="the Studio id (default: the one in Play)")
    args = parser.parse_args()
    if args.index:
        print(write_index(), "pictures listed in store-assets/visual-review/shots.js")
        return 0

    studio = Studio(args.studio)
    shots = parse_json(studio.luau(studio.shot_code("?list"), "Client", 120))
    if not isinstance(shots, list):
        sys.exit("Couldn't read the shot list: is a solo Play running?")
    if args.list:
        for s in shots:
            print(s["Name"], " ".join(s["Sizes"]))
        return 0
    wanted = [s for s in shots
              if (not args.categories or s["Name"].split("/")[0] in args.categories)
              and (not args.only or s["Name"] in args.only)]
    by_category = {}
    for s in wanted:
        by_category.setdefault(s["Name"].split("/")[0], []).append(s)
    taken, failed = 0, []
    started = time.time()
    for category in sorted(by_category, key=lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99):
        print(f"== {category}: {len(by_category[category])} shots", flush=True)
        studio.luau(studio.shot_code(f"?prepare:{category}"), "Client", 180)
        for s in by_category[category]:
            for size in s["Sizes"]:
                if args.size and size not in args.size:
                    continue
                label = s["Name"] + ("" if size == "desktop" else f" [{size}]")
                try:
                    result = parse_json(studio.luau(studio.shot_code(s["Name"], size), "Client", 180))
                    if not isinstance(result, dict) or result.get("Error"):
                        raise RuntimeError((result or {}).get("Error", "setup failed"))
                    if result.get("GlacierHpShare") is not None:
                        share = float(result["GlacierHpShare"])
                        studio.luau(f'local g = workspace.GoldenGlacier g:SetAttribute("Hp", math.max(1, math.floor(g:GetAttribute("HpMax") * {share}))) return "ok"', "Server", 60)
                    for path in result.get("PreClose", []):
                        studio.click(path, 400)
                    for path in result.get("Clicks", []):
                        studio.click(path, 700)
                    tapping = None
                    if result.get("TapAt"):
                        # real clicks on the world (the click burst): a second MCP connection keeps clicking while
                        # this one captures, since a capture arrives too late for a 0.25 s burst after the last click
                        tapping = threading.Thread(target=studio.tap_at_aside, args=(result["TapAt"],))
                        tapping.start()
                    time.sleep(float(result.get("Wait", 1.5)))
                    png = studio.capture(f"vr_{taken}")
                    if tapping:
                        tapping.join()
                    if not png:
                        raise RuntimeError("no picture (is Studio in front and the display awake?)")
                    save(png, file_for(s["Name"], size), result["Region"], result["Viewport"], size)
                    taken += 1
                    # every tab of a window, after its first page
                    for index, tab in enumerate(result.get("TabPaths", [])[1:], start=2):
                        studio.click(tab, 900)
                        png = studio.capture(f"vr_{taken}")
                        if png:
                            tab_name = tab.rsplit(".", 1)[-1].removesuffix("Tab").lower()
                            save(png, file_for(f"{s['Name']}_tab{index}_{tab_name}", size), result["Region"], result["Viewport"], size)
                            taken += 1
                    time.sleep(float(result.get("After", 0)))  # (a window that opens late, closed below)
                    if result.get("Escape"):
                        press_escape()
                        time.sleep(1)
                    for path in result.get("Close", []):
                        studio.click(path, 400)
                    print(f"  ok   {label}", flush=True)
                except Exception as e:  # keep going: one bad shot shouldn't stop the set
                    failed.append(label)
                    print(f"  FAIL {label}: {e}", flush=True)
        studio.luau(studio.shot_code("?cleanup"), "Client", 60)
    count = write_index()
    print(f"{taken} pictures in {(time.time() - started) / 60:.1f} min; {len(failed)} failed; index lists {count}")
    for label in failed:
        print("  failed:", label)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
