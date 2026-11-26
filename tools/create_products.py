"""create_products.py - creates every Robux item of this game through Open Cloud, safely re-runnable.

    python tools/create_products.py --dry-run     # read everything, list what exists, show what it would create
    python tools/create_products.py               # create what's missing, then write the ids into the game

What it creates (universe 10778596196, owned by group 921449746):
  * each game pass in docs/ROBUX_PRODUCTS.md ("Game passes" table) as a game pass;
  * each developer product ("Developer products" table) as a developer product;
  * for every item, its gift twin: a developer product "Gift: <name>", same price, same icon.
Name, store description and price come from the doc's tables; every price must match the item's ExpectedPrice
in src/replicated/MonetizationConfig.luau (the script stops otherwise). The icon is store-assets/icons/<Key>.png.
Everything is created on sale (isForSale = true).

Safe to re-run: before creating anything it lists the universe's existing passes and developer products and
matches them by name, so an item that already exists is never created twice (its id is taken instead). Ids
are kept in store-assets/icons/products_manifest.json. After a successful run it writes every Id and GiftId
into MonetizationConfig.luau and the doc's Items tables.

The API key comes from the ROBLOX_API_KEY environment variable (game-pass and developer-product read and
write for this universe). It is never printed, logged or written anywhere. If Roblox refuses a call
(scope, ownership, beta access, moderation...), the script stops and prints Roblox's own error message.
Calls stay under 3 a second. Standard library only.
"""
import argparse, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request, uuid

UNIVERSE = 10778596196
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DOC = os.path.join(REPO, "docs", "ROBUX_PRODUCTS.md")
CONFIG = os.path.join(REPO, "src", "replicated", "MonetizationConfig.luau")
ICONS = os.path.join(REPO, "store-assets", "icons")
MANIFEST = os.path.join(ICONS, "products_manifest.json")
API = "https://apis.roblox.com"
PASSES = f"/game-passes/v1/universes/{UNIVERSE}/game-passes"
PRODUCTS = f"/developer-products/v2/universes/{UNIVERSE}/developer-products"
GAP = 0.4  # seconds between calls: under 3 a second
GIFT_DESCRIPTION = "A gift: {name} for another player in your server."


class Refused(Exception):
    pass


# Reading the items ------------------------------------------------------------------------------------------

def doc_table(text, heading):
    """The rows of the first table after a '### heading' line, as dicts keyed by the header cells."""
    at = text.index("### " + heading)
    lines = [l for l in text[at:].splitlines()[1:]]
    rows, header = [], None
    for line in lines:
        if not line.startswith("|"):
            if header:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
        elif set(line.replace("|", "").strip()) <= set("-: "):
            continue
        else:
            rows.append(dict(zip(header, cells)))
    return rows


def read_items():
    text = open(DOC, encoding="utf-8").read()
    config = open(CONFIG, encoding="utf-8").read()
    items = []
    for kind, heading in (("pass", "Game passes"), ("product", "Developer products")):
        for row in doc_table(text, heading):
            key = row["Key"]
            price = int(row["Price (Robux)"])
            m = re.search(r'Key = "%s".*?ExpectedPrice = (\d+)' % re.escape(key), config, re.S)
            if not m:
                sys.exit(f"{key}: not in MonetizationConfig.luau")
            if int(m.group(1)) != price:
                sys.exit(f"{key}: the doc says {price} Robux but MonetizationConfig's ExpectedPrice is {m.group(1)}")
            icon = os.path.join(ICONS, key + ".png")
            if not os.path.isfile(icon):
                sys.exit(f"{key}: no icon at {icon}")
            items.append({"key": key, "kind": kind, "name": row["Name"], "price": price,
                          "description": row["Store description"], "icon": icon})
    return items


# HTTP --------------------------------------------------------------------------------------------------------

last_call = [0.0]


def call(method, path, fields=None, files=None, retries=4):
    key = os.environ.get("ROBLOX_API_KEY")
    if not key:
        sys.exit("ROBLOX_API_KEY is missing")
    body, headers = None, {"x-api-key": key}
    if fields is not None or files:
        boundary = uuid.uuid4().hex
        parts = []
        for name, value in (fields or {}).items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        for name, path_ in (files or {}).items():
            data = open(path_, "rb").read()
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{os.path.basename(path_)}"\r\n'
                         f'Content-Type: image/png\r\n\r\n'.encode() + data + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    for attempt in range(retries + 1):
        wait = GAP - (time.time() - last_call[0])
        if wait > 0:
            time.sleep(wait)
        last_call[0] = time.time()
        request = urllib.request.Request(API + path, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")[:800]
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 ** attempt * 2)
                continue
            raise Refused(f"{method} {path} -> HTTP {e.code}: {text}")
        except urllib.error.URLError as e:
            if attempt < retries:
                time.sleep(2 ** attempt * 2)
                continue
            raise Refused(f"{method} {path} -> network error: {e.reason}")


def list_all(path, field, id_field):
    found, token = {}, ""
    while True:
        query = "?pageSize=50" + ("&pageToken=" + urllib.parse.quote(token) if token else "")
        page = call("GET", path + "/creator" + query)
        for item in page.get(field) or []:
            found[item["name"]] = {"id": int(item[id_field]),
                                   "price": (item.get("priceInformation") or {}).get("defaultPriceInRobux"),
                                   "forSale": item.get("isForSale")}
        token = page.get("nextPageToken") or ""
        if not token:
            return found


# Writing the ids back ----------------------------------------------------------------------------------------

def write_back(manifest):
    config = open(CONFIG, encoding="utf-8", newline="").read()
    for key, entry in manifest.items():
        pattern = re.compile(r'(Key = "%s",.*?Id = )\d+(, GiftId = )\d+' % re.escape(key), re.S)
        config, n = pattern.subn(lambda m: f"{m.group(1)}{entry['Id']}{m.group(2)}{entry['GiftId']}", config, count=1)
        if n != 1:
            sys.exit(f"{key}: couldn't find its Id/GiftId in MonetizationConfig.luau")
    open(CONFIG, "w", encoding="utf-8", newline="").write(config)

    doc = open(DOC, encoding="utf-8", newline="").read()
    lines = doc.split("\n")
    for i, line in enumerate(lines):
        cells = line.split("|")
        if len(cells) == 9 and cells[1].strip() in manifest:  # | Key | Name | Price | Desc | Id | Gift | Gift id |
            entry = manifest[cells[1].strip()]
            cells[5] = f" {entry['Id']} "
            cells[7] = f" {entry['GiftId']} "
            lines[i] = "|".join(cells)
    open(DOC, "w", encoding="utf-8", newline="").write("\n".join(lines))


# Main --------------------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="read and list only; create nothing, write nothing")
    args = parser.parse_args()

    items = read_items()
    manifest = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {}
    print(f"{len(items)} items, {len(items)} gift twins ({sum(i['kind'] == 'pass' for i in items)} passes)")

    try:
        passes = list_all(PASSES, "gamePasses", "gamePassId")
        products = list_all(PRODUCTS, "developerProducts", "productId")
    except Refused as e:
        print("REFUSED while listing what exists:", e)
        return 1
    print(f"already in the universe: {len(passes)} game passes, {len(products)} developer products")

    created = 0
    try:
        for item in items:
            entry = manifest.setdefault(item["key"], {"Id": 0, "GiftId": 0})
            for role in ("main", "gift"):
                if role == "main":
                    name, description, is_pass = item["name"], item["description"], item["kind"] == "pass"
                else:
                    name, description, is_pass = "Gift: " + item["name"], GIFT_DESCRIPTION.format(name=item["name"]), False
                existing = (passes if is_pass else products).get(name)
                field = "Id" if role == "main" else "GiftId"
                what = "game pass" if is_pass else "developer product"
                if existing:
                    entry[field] = existing["id"]
                    note = "" if existing["price"] == item["price"] else f"  (PRICE ON ROBLOX IS {existing['price']}, not {item['price']})"
                    print(f"  exists   {what:17} {name:28} id {existing['id']}{note}")
                    continue
                if args.dry_run:
                    print(f"  would create {what:13} {name:28} {item['price']} Robux, icon {os.path.basename(item['icon'])}")
                    continue
                fields = {"name": name, "description": description, "price": str(item["price"]), "isForSale": "true"}
                result = call("POST", PASSES if is_pass else PRODUCTS, fields, {"imageFile": item["icon"]})
                new_id = int(result.get("gamePassId") if is_pass else result.get("productId"))
                entry[field] = new_id
                (passes if is_pass else products)[name] = {"id": new_id, "price": item["price"], "forSale": True}
                created += 1
                print(f"  CREATED  {what:17} {name:28} id {new_id}")
                if not args.dry_run:
                    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1, sort_keys=True)
    except Refused as e:
        print("REFUSED:", e)
        print("Stopped. Nothing else was created; the manifest has every id made so far.")
        return 1

    if args.dry_run:
        print("dry run: nothing created, nothing written")
        return 0
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1, sort_keys=True)
    missing = [k for k, v in manifest.items() if not v["Id"] or not v["GiftId"]]
    if missing:
        print("missing ids for:", ", ".join(missing))
        return 1
    write_back(manifest)
    print(f"created {created}; every Id and GiftId written into MonetizationConfig.luau and docs/ROBUX_PRODUCTS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
