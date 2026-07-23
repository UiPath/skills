#!/usr/bin/env python3
"""pre_run: generate seed.json with uuid8 and optional process/folder context."""
import json, os, subprocess, sys, uuid

# Parent folder under which tests place any new folder they create
# (folders_hierarchy's tree, deploy_round_trip's deploy folder, etc.).
# Hardcoded so the same path lands locally, on CI, and on the nightly VM
# without secret/env coordination across launchers. `ensure_parent_folder`
# creates it on first run so this works on any tenant.
PARENT_FOLDER_PATH = "Shared/uipath-platform-e2e"

def uip_json(*args):
    r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        return {}

def ensure_parent_folder(path):
    """Idempotent: returns once the folder exists. Creates it under its
    last-segment parent if missing. Errors out if the immediate parent
    itself isn't there (we don't recursively create — `Shared` is the only
    expected ancestor and it exists on every tenant).

    Race-safe under parallel seeds: on a fresh tenant, two `seed.py` runs
    can both see the parent missing and both call `folders create`; one
    wins, the other gets a non-Success. Re-GET after a failed create — if
    the folder now exists (peer created it), treat the create as a
    successful no-op."""
    got = uip_json("or", "folders", "get", path)
    if got.get("Result") == "Success":
        return
    parent, _, name = path.rpartition("/")
    if not parent or not name:
        print(f"seed.py: PARENT_FOLDER_PATH {path!r} must be nested under an existing folder (e.g. 'Shared/x').", file=sys.stderr)
        sys.exit(1)
    created = uip_json("or", "folders", "create", name, "--parent", parent)
    if created.get("Result") == "Success":
        return
    # Create lost (likely a concurrent seed beat us). Re-GET to confirm.
    recheck = uip_json("or", "folders", "get", path)
    if recheck.get("Result") == "Success":
        return
    msg = created.get("Message") or created.get("Instructions") or "unknown error"
    print(f"seed.py: failed to ensure parent folder {path}: {msg}", file=sys.stderr)
    sys.exit(1)

ensure_parent_folder(PARENT_FOLDER_PATH)

seed = {
    "uuid8": uuid.uuid4().hex[:8],
    "parent_folder_path": PARENT_FOLDER_PATH,
}

key = os.environ.get("E2E_PROCESS_KEY", "")
if not key:
    print(
        "seed.py: E2E_PROCESS_KEY is not set — seed.json will omit "
        "process_key/folder_a_path, and every e2e task that needs them will "
        "fail its check with 'seed.json missing ...'. Export E2E_PROCESS_KEY "
        "to the Key (GUID) of an existing process on the test tenant.",
        file=sys.stderr,
    )
if key:
    seed["process_key"] = key
    # `or processes get` doesn't populate FolderPath, so derive the folder from
    # `processes list` matched by Key. The list paginates (default page size),
    # sorted Id desc — under a busy parallel run, processes created by other
    # tasks can push the seeded stub off page 1, so page through every folder
    # until we find it instead of trusting the first page.
    fp, offset = "", 0
    while True:
        page = (uip_json("or", "processes", "list", "--all-folders",
                         "--limit", "200", "--offset", str(offset)).get("Data") or [])
        if isinstance(page, dict):
            page = page.get("Value") or page.get("Items") or page.get("Results") or []
        match = next((p for p in page if (p.get("Key") or "").lower() == key.lower()), None)
        if match:
            fp = match.get("FolderPath") or match.get("FolderName") or ""
            break
        if len(page) < 200:  # last page reached, key not found anywhere
            break
        offset += 200
    if not fp:
        print(f"seed.py: could not resolve folder for E2E_PROCESS_KEY={key} via 'or processes list' — check the key is correct and the process exists.", file=sys.stderr)
        sys.exit(1)
    seed["folder_path"] = fp
    seed["folder_a_path"] = fp

json.dump(seed, open("seed.json", "w"))
