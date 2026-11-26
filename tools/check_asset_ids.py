"""check_asset_ids.py - checks every asset id the game's configs use: owned by the group, and approved.

    python tools/check_asset_ids.py

It reads the asset ids (numbers of 10+ digits) from the config modules under src/replicated/ that hold
uploaded assets (models, pictures, sounds) and asks Open Cloud about each (GET /assets/v1/assets/{id}):
who created it and its moderation state. Read only: nothing is changed. Prints one line per problem and
a summary; exits non-zero if any id isn't the group's or isn't approved.

Not checked (on purpose): MonetizationConfig (product and pass ids, see tools/create_products.py) and
the two public library images in UITheme.Assets (the checker and the Robux icon, from the UI skill).
The API key comes from the ROBLOX_API_KEY environment variable (asset read) and is never printed.
"""
import json, os, re, sys, time, urllib.error, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUP = "921449746"
FILES = ["AudioConfig", "BuildingConfig", "CreatureConfig", "EffectsConfig", "MapConfig", "UITheme", "UpgradeConfig"]
PUBLIC = {"385956923": "UITheme.Assets.Checker (public library image)", "11560341132": "UITheme.Assets.Robux (public library image)"}


def ids():
    found = {}
    for name in FILES:
        text = open(os.path.join(REPO, "src", "replicated", name + ".luau"), encoding="utf8").read()
        for line in text.splitlines():
            code = line.split("--", 1)[0]  # (ids in comments don't count)
            for number in re.findall(r"(?<![\w.])(\d{10,})(?![\w.])", code):
                found.setdefault(number, name)
    return found


def get(asset_id, key):
    request = urllib.request.Request(f"https://apis.roblox.com/assets/v1/assets/{asset_id}", headers={"x-api-key": key})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(2 ** attempt * 2)
                continue
            return {"error": f"HTTP {e.code}: {e.read().decode('utf8', 'replace')[:200]}"}
        except urllib.error.URLError as e:
            if attempt < 3:
                time.sleep(2)
                continue
            return {"error": f"network: {e.reason}"}


def main():
    key = os.environ.get("ROBLOX_API_KEY")
    if not key:
        sys.exit("ROBLOX_API_KEY is missing")
    found = ids()
    problems, ok, skipped = [], 0, 0
    for asset_id, source in sorted(found.items(), key=lambda item: item[1]):
        if asset_id in PUBLIC:
            skipped += 1
            continue
        time.sleep(0.25)
        asset = get(asset_id, key)
        if "error" in asset:
            problems.append(f"{source}: {asset_id}: {asset['error']}")
            continue
        creator = (asset.get("creationContext") or {}).get("creator") or {}
        state = ((asset.get("moderationResult") or {}).get("moderationState") or "?").replace("MODERATION_STATE_", "")
        owner = f"group {creator['groupId']}" if creator.get("groupId") else f"user {creator.get('userId', '?')}"
        if str(creator.get("groupId")) != GROUP:
            problems.append(f"{source}: {asset_id} ({asset.get('assetType', '?')}) is owned by {owner}, not group {GROUP}")
        elif state.lower() != "approved":
            problems.append(f"{source}: {asset_id} ({asset.get('assetType', '?')}) is {state}")
        else:
            ok += 1
    for problem in problems:
        print("PROBLEM", problem)
    print(f"{len(found)} asset ids in the configs: {ok} group-owned and approved, {len(problems)} problems, {skipped} public library images skipped")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
