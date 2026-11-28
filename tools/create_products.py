"""create_products.py - creates every Robux item of this game through Open Cloud, safely re-runnable.

    python tools/create_products.py --dry-run     # read everything, list what exists, show what it would create or change
    python tools/create_products.py               # create what's missing, fix prices and descriptions, then write the ids into the game

What it creates (universe 10778596196, owned by group 921449746):
  * each game pass in docs/ROBUX_PRODUCTS.md ("Game passes" table) as a game pass;
  * each developer product ("Developer products" table) as a developer product;
  * for every item, its gift twin: a developer product "Gift: <name>", same price, same icon; except an item whose
    gift column in the doc says "(none: ...)" (Double Welcome Back: never giftable), which has no twin (GiftId 0).
Name, store description and price come from the doc's tables; every price must match the item's ExpectedPrice
in src/replicated/MonetizationConfig.luau (the script stops otherwise). The icon is store-assets/icons/<Key>.png.
Everything is created on sale (isForSale = true).

Safe to re-run: before creating anything it lists the universe's existing passes and developer products and
matches them by name, so an item that already exists is never created twice (its id is taken instead).

Prices and descriptions: an item that exists on Roblox with a different price or store description than the doc's
gets the doc's, through PATCH on the game pass or developer product (multipart form fields "price" and
"description"; only the fields that differ are sent). Its gift twin follows (the twin's description is
GIFT_DESCRIPTION). At the end it reads every item back and prints the price and description Roblox shows. To change a
price: edit the doc's table and ExpectedPrice; to change a description, the doc's table; run with --dry-run, then
without. Ids
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
GAP = 0.4  # seconds between calls: under 3 a second (PATCH on a developer product allows 3 a second)
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
            gift_cell = next((v for k, v in row.items() if k.startswith("Gift product")), "")
            items.append({"key": key, "kind": kind, "name": row["Name"], "price": price,
                          "description": row["Store description"], "icon": icon,
                          "gift": not gift_cell.startswith("(none")})
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
                                   "description": item.get("description"),
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
    print(f"{len(items)} items, {sum(i['gift'] for i in items)} gift twins ({sum(i['kind'] == 'pass' for i in items)} passes)")

    try:
        passes = list_all(PASSES, "gamePasses", "gamePassId")
        products = list_all(PRODUCTS, "developerProducts", "productId")
    except Refused as e:
        print("REFUSED while listing what exists:", e)
        return 1
    print(f"already in the universe: {len(passes)} game passes, {len(products)} developer products")

    created, repriced, described = 0, 0, 0
    try:
        for item in items:
            entry = manifest.setdefault(item["key"], {"Id": 0, "GiftId": 0})
            for role in ("main", "gift") if item["gift"] else ("main",):
                if role == "main":
                    name, description, is_pass = item["name"], item["description"], item["kind"] == "pass"
                else:
                    name, description, is_pass = "Gift: " + item["name"], GIFT_DESCRIPTION.format(name=item["name"]), False
                existing = (passes if is_pass else products).get(name)
                field = "Id" if role == "main" else "GiftId"
                what = "game pass" if is_pass else "developer product"
                if existing:
                    entry[field] = existing["id"]
                    changes = {}
                    if existing["price"] != item["price"]:
                        changes["price"] = str(item["price"])
                    if (existing["description"] or "") != description:
                        changes["description"] = description
                    if not changes:
                        print(f"  exists   {what:17} {name:28} id {existing['id']}, {item['price']} Robux, description as the doc")
                        continue
                    notes = []
                    if "price" in changes:
                        notes.append(f"price {existing['price']} -> {item['price']} Robux")
                    if "description" in changes:
                        notes.append(f"description {existing['description']!r} -> {description!r}")
                    if args.dry_run:
                        print(f"  would update {what:13} {name:28} id {existing['id']}: " + "; ".join(notes))
                        continue
                    path = (PASSES if is_pass else PRODUCTS) + f"/{existing['id']}"
                    call("PATCH", path, changes)
                    print(f"  UPDATED  {what:17} {name:28} id {existing['id']}: " + "; ".join(notes))
                    if "price" in changes:
                        existing["price"] = item["price"]
                        repriced += 1
                    if "description" in changes:
                        existing["description"] = description
                        described += 1
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
        print("dry run: nothing created, changed or written")
        return 0

    # Read everything back: the price and description each item has on Roblox now.
    try:
        passes = list_all(PASSES, "gamePasses", "gamePassId")
        products = list_all(PRODUCTS, "developerProducts", "productId")
    except Refused as e:
        print("REFUSED while reading the prices back:", e)
        return 1
    wrong = 0
    print("as Roblox shows them now:")
    for item in items:
        checks = [(item["name"], (passes if item["kind"] == "pass" else products).get(item["name"]), item["description"])]
        if item["gift"]:
            checks.append(("Gift: " + item["name"], products.get("Gift: " + item["name"]), GIFT_DESCRIPTION.format(name=item["name"])))
        for name, found, description in checks:
            price = found and found["price"]
            shown = found and found["description"]
            marks = []
            if price != item["price"]:
                marks.append(f"price EXPECTED {item['price']}")
            if shown != description:
                marks.append(f"description EXPECTED {description!r}")
            wrong += len(marks)
            print(f"  {name:30} {price} Robux{'' if found and found['forSale'] else ' (NOT FOR SALE)'}  {shown!r}"
                  + (f"   <- {'; '.join(marks)}" if marks else ""))
    if wrong:
        print(f"{wrong} prices or descriptions on Roblox don't match the doc")
        return 1
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1, sort_keys=True)
    has_gift = {i["key"]: i["gift"] for i in items}
    missing = [k for k, v in manifest.items() if not v["Id"] or (has_gift.get(k, True) and not v["GiftId"])]
    if missing:
        print("missing ids for:", ", ".join(missing))
        return 1
    write_back(manifest)
    print(f"created {created}, repriced {repriced}, descriptions updated {described}; every Id and GiftId written into MonetizationConfig.luau and docs/ROBUX_PRODUCTS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
