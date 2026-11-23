#!/usr/bin/env python3
"""upload_models.py - upload FBX models and PNG/JPG pictures to Roblox with the Open Cloud Assets API,
always created by the game's group (GROUP_ID below).

Python 3 standard library only (nothing to pip install). If `python` isn't on PATH, Blender's own
Python works: "C:\\Program Files\\Blender Foundation\\Blender <ver>\\<ver>\\python\\bin\\python.exe".

The API key comes from the ROBLOX_API_KEY environment variable. It is never printed, logged or
written anywhere. The key needs the Assets API's Read and Write operations (scopes asset:read and
asset:write) for the creator you upload as.

An upload manifest (JSON, safe to commit: no secrets) maps each file to its asset id and a SHA-256
of its content. Re-runs skip unchanged files and update an existing asset (a new version, same id)
instead of creating a duplicate. Only .fbx Models can be updated: a changed picture becomes a new
asset (a new id to swap into the game). An asset whose manifest entry doesn't name this game's group
as its creator is never updated in place either: a changed file becomes a new group asset with a new
id. A pending operation is saved before polling, so a run that is cut off resumes on the next run
instead of uploading again.

Rescue Pets From the Ice: every upload is created by the group 921449746 (the game's owner), never by
a user and never by another game's group. Group-owned assets load in the game with no permission grant.

  python tools/upload_models.py assets/models/Pets1.fbx      # manifest: assets/models/upload_manifest.json
  python tools/upload_models.py assets/ui-icons/Shop.png    # manifest: assets/ui-icons/upload_manifest.json
  python tools/upload_models.py --check assets/models/Pets1.fbx   # re-check moderation of assets not approved yet
  python tools/upload_models.py --dry-run assets/models/*.fbx

Endpoints (create.roblox.com/docs/cloud, Assets API v1):
  POST  /assets/v1/assets               create: multipart "request" (JSON) + "fileContent"
  PATCH /assets/v1/assets/{assetId}     update: same form; only .fbx Model content can be updated
  GET   /assets/v1/operations/{id}      poll until done; response.assetId, response.moderationResult
  GET   /assets/v1/assets/{assetId}     moderation state of an existing asset
Limits: 20 MB per file; 120 create/update and 300 operation requests a minute per key.
"""
import argparse, glob, hashlib, json, os, random, sys, time, urllib.error, urllib.request, uuid
from datetime import datetime, timezone

API = "https://apis.roblox.com"
MAX_BYTES = 20 * 1024 * 1024
GROUP_ID = "921449746"  # the group that owns Rescue Pets From the Ice: every upload is created by it, never a user
GROUP_CREATOR = {"groupId": GROUP_ID}
# extension -> (content type, assetType). Only .fbx Models can be updated in place.
CONTENT_TYPES = {".fbx": ("model/fbx", "Model"), ".png": ("image/png", "Image"),
                 ".jpg": ("image/jpeg", "Image"), ".jpeg": ("image/jpeg", "Image")}


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__("HTTP %s: %s" % (status, message))
        self.status = status


def short_message(raw):
    """The server's error message, trimmed. Error bodies never contain the key."""
    try:
        body = json.loads(raw or b"{}")
        message = body.get("message") or (body.get("errors") or [{}])[0].get("message") or ""
    except (ValueError, AttributeError, IndexError):
        message = (raw or b"").decode("utf-8", "replace")
    return " ".join(str(message).split())[:200] or "no message"


def call(method, url, key, body=None, content_type=None, retry_unsafe=True, attempts=6):
    """One API call with backoff on 429 (rate limited) and 5xx. A create (retry_unsafe=False) is only
    retried on 429 and 503, where the server did not take the upload, so a retry can't duplicate it."""
    for attempt in range(attempts):
        request = urllib.request.Request(url, data=body, method=method)
        request.add_header("x-api-key", key)
        if content_type:
            request.add_header("Content-Type", content_type)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as error:
            raw = error.read()
            retryable = error.code in (429, 503) or (retry_unsafe and error.code >= 500)
            if not retryable or attempt == attempts - 1:
                raise ApiError(error.code, short_message(raw))
            wait = error.headers.get("Retry-After")
            wait = float(wait) if wait and wait.replace(".", "", 1).isdigit() else min(60, 2 ** attempt) + random.random()
            print("    HTTP %d, retrying in %.0f s" % (error.code, wait))
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            if not retry_unsafe or attempt == attempts - 1:
                raise ApiError("network", str(getattr(error, "reason", error))[:200])
            time.sleep(min(60, 2 ** attempt) + random.random())
    raise ApiError("retry", "gave up after %d attempts" % attempts)


def multipart(request_json, path, content_type):
    """A multipart/form-data body with the "request" JSON and the file as "fileContent"."""
    boundary = "----upload-" + uuid.uuid4().hex
    filename = os.path.basename(path).replace('"', "")
    with open(path, "rb") as handle:
        content = handle.read()
    body = b"".join([
        ("--%s\r\nContent-Disposition: form-data; name=\"request\"\r\n\r\n" % boundary).encode(),
        json.dumps(request_json).encode(), b"\r\n",
        ("--%s\r\nContent-Disposition: form-data; name=\"fileContent\"; filename=\"%s\"\r\n"
         "Content-Type: %s\r\n\r\n" % (boundary, filename, content_type)).encode(),
        content, b"\r\n",
        ("--%s--\r\n" % boundary).encode(),
    ])
    return body, "multipart/form-data; boundary=" + boundary


def moderation(state):
    """Roblox's state strings have not always matched its docs, so match loosely."""
    text = (state or "").upper()
    if "APPROVED" in text:
        return "approved"
    if "REJECTED" in text:
        return "REJECTED"
    return "pending review" if text else "unknown"


def operation_id(operation):
    return operation.get("operationId") or operation.get("path", "").rpartition("/")[2]


def poll(api, key, op_id, timeout):
    """Wait for an operation. Returns its final JSON, or None if it is still running at the timeout."""
    deadline, wait = time.time() + timeout, 1.5
    while True:
        operation = call("GET", "%s/assets/v1/operations/%s" % (api, op_id), key)
        if operation.get("done"):
            return operation
        if time.time() + wait > deadline:
            return None
        time.sleep(wait)
        wait = min(wait * 1.5, 10)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path):
    """The manifest, with each entry's creator spelled out. An entry without its own creator belongs
    to the manifest's top-level creator; one that isn't this game's group is never updated in place."""
    manifest = {"creator": GROUP_CREATOR, "assets": {}}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            manifest = json.load(handle)
    old_creator = manifest.get("creator")
    for entry in manifest["assets"].values():
        if entry.get("assetId") and "creator" not in entry and old_creator:
            entry["creator"] = old_creator
    manifest["creator"] = GROUP_CREATOR
    return manifest


def save_manifest(path, manifest):
    manifest["assets"] = {name: entry for name, entry in manifest["assets"].items() if entry}
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=1, sort_keys=True)
    os.replace(temporary, path)  # a crash mid-write can't corrupt the manifest


def finish_operation(entry, operation, name):
    """Record a finished operation in the manifest entry. Returns True on success."""
    entry.pop("operationId", None)
    pending_hash = entry.pop("pendingSha256", None)
    if operation.get("error") and operation["error"].get("code"):
        print("  %s: FAILED (%s)" % (name, short_message(json.dumps(operation["error"]).encode())))
        return False
    result = operation.get("response") or {}
    entry["assetId"] = str(result.get("assetId") or entry.get("assetId") or "")
    entry["sha256"] = pending_hash or entry.get("sha256")
    entry["moderationState"] = (result.get("moderationResult") or {}).get("moderationState", "")
    entry["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state = moderation(entry["moderationState"])
    print("  %s: asset %s, %s" % (name, entry["assetId"] or "?", state))
    return bool(entry["assetId"]) and state != "REJECTED"


def upload(args, key, manifest, manifest_path, path):
    """Upload one file if it changed. Returns True when the file ends up uploaded and not rejected."""
    root = os.path.dirname(os.path.abspath(manifest_path))
    name = os.path.relpath(os.path.abspath(path), root).replace("\\", "/")
    entry = manifest["assets"].setdefault(name, {})
    extension = os.path.splitext(path)[1].lower()
    if extension not in CONTENT_TYPES:
        print("  %s: skipped (only %s)" % (name, ", ".join(CONTENT_TYPES)))
        return False
    if os.path.getsize(path) > MAX_BYTES:
        print("  %s: FAILED (over 20 MB: split the batch)" % name)
        return False
    if entry.get("operationId") and not args.dry_run:  # a previous run was cut off mid-processing
        print("  %s: resuming operation" % name)
        operation = poll(args.api, key, entry["operationId"], args.timeout)
        if operation is None:
            print("  %s: still processing; run again later" % name)
            return False
        finish_operation(entry, operation, name)
        save_manifest(manifest_path, manifest)
    digest = sha256(path)
    if entry.get("assetId") and entry.get("sha256") == digest:
        print("  %s: unchanged (asset %s, %s)" % (name, entry["assetId"], moderation(entry.get("moderationState"))))
        return moderation(entry.get("moderationState")) != "REJECTED"
    file_type, asset_type = CONTENT_TYPES[extension]
    updatable = asset_type == "Model" and entry.get("creator") == GROUP_CREATOR
    if entry.get("assetId") and updatable:
        action, method, url = "update", "PATCH", "%s/assets/v1/assets/%s" % (args.api, entry["assetId"])
        request_json = {"assetType": asset_type, "assetId": entry["assetId"],
                        "creationContext": {"creator": GROUP_CREATOR}}
    else:
        if entry.get("assetId"):  # a picture, or an asset the group doesn't own: a new group asset
            print("  %s: replaces asset %s with a NEW group asset (swap the new id into the game)" % (name, entry["assetId"]))
            entry["previousAssetId"] = entry.pop("assetId")
            entry.pop("moderationState", None)
            entry.pop("revision", None)
        action, method, url = "create", "POST", "%s/assets/v1/assets" % args.api
        display = os.path.splitext(os.path.basename(path))[0][:50]
        request_json = {"assetType": asset_type, "displayName": display, "description": args.description,
                        "creationContext": {"creator": GROUP_CREATOR}}
    if args.dry_run:
        print("  %s: would %s as group %s" % (name, action, GROUP_ID))
        return True
    entry["creator"] = GROUP_CREATOR
    print("  %s: %s..." % (name, action))
    body, content_type = multipart(request_json, path, file_type)
    try:
        operation = call(method, url, key, body, content_type, retry_unsafe=(method != "POST"))
    except ApiError as error:
        print("  %s: FAILED (%s)" % (name, error))
        return False
    entry["operationId"], entry["pendingSha256"] = operation_id(operation), digest
    save_manifest(manifest_path, manifest)  # saved before polling, so a crash can't cause a duplicate
    if not operation.get("done"):
        operation = poll(args.api, key, entry["operationId"], args.timeout)
        if operation is None:
            print("  %s: still processing; run again to finish" % name)
            return False
    ok = finish_operation(entry, operation, name)
    save_manifest(manifest_path, manifest)
    return ok


def check(args, key, manifest, manifest_path):
    """Refresh the moderation state of every asset that wasn't approved yet."""
    ok = True
    for name, entry in sorted(manifest["assets"].items()):
        if entry.get("operationId"):
            operation = poll(args.api, key, entry["operationId"], args.timeout)
            ok = (finish_operation(entry, operation, name) if operation else False) and ok
        elif entry.get("assetId") and moderation(entry.get("moderationState")) != "approved":
            asset = call("GET", "%s/assets/v1/assets/%s" % (args.api, entry["assetId"]), key)
            entry["moderationState"] = (asset.get("moderationResult") or {}).get("moderationState", "")
            state = moderation(entry["moderationState"])
            print("  %s: asset %s, %s" % (name, entry["assetId"], state))
            ok = ok and state != "REJECTED"
        save_manifest(manifest_path, manifest)
    return ok


def main():
    parser = argparse.ArgumentParser(description="Upload FBX models with the Roblox Open Cloud Assets API.")
    parser.add_argument("files", nargs="*", help=".fbx files (wildcards work)")
    parser.add_argument("--manifest", help="upload manifest (default: upload_manifest.json beside the first file)")
    parser.add_argument("--description", default="Uploaded by upload_models.py")
    parser.add_argument("--timeout", type=float, default=300, help="seconds to wait for each operation")
    parser.add_argument("--check", action="store_true", help="only re-check pending operations and moderation")
    parser.add_argument("--dry-run", action="store_true", help="show what would be uploaded; send nothing")
    parser.add_argument("--api", default=API, help=argparse.SUPPRESS)  # for tests against a local mock
    args = parser.parse_args()

    files = sorted({p for pattern in args.files for p in (glob.glob(pattern) or [pattern])})
    manifest_path = args.manifest or os.path.join(os.path.dirname(os.path.abspath(files[0])) if files else ".", "upload_manifest.json")
    manifest = load_manifest(manifest_path)
    key = os.environ.get("ROBLOX_API_KEY", "").strip()
    if not key and not args.dry_run:
        sys.exit("ROBLOX_API_KEY is not set. Set it as a user environment variable and restart the terminal.")

    print("manifest:", manifest_path)
    if args.check:
        ok = check(args, key, manifest, manifest_path)
    else:
        missing = [p for p in files if not os.path.isfile(p)]
        if missing or not files:
            sys.exit("No such file: %s" % (", ".join(missing) or "(none given)"))
        ok = True
        for path in files:
            ok = upload(args, key, manifest, manifest_path, path) and ok
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
