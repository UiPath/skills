"""Ensure a Data Fabric entity exists in a folder, for a task whose activity
picks it on a solution-resource picker (`folderEntityName`).

Idempotent — used from a task's `pre_run` block:

    python3 ensure_folder_entity.py <definition.json> [<folder-path>]

The folder defaults to `Shared`. The entity is created there from the
definition (`uip df entities create <name> --file <definition> --folder-key`)
when the folder holds none by that name. Its key and the folder's are written
to `_setup/picker_entity.json` for the task's checker:

    {"name": ..., "key": ..., "folderKey": ..., "folderPath": ...}

Keep the entity name unique on the tenant: a picker name held by one entity
resolves without a folder key, so the task does not have to supply one.

Exits non-zero on infrastructure failure (login expired, folder missing, CLI
missing), which fails the pre_run gate rather than letting the agent run
against a tenant without the fixture.
"""
import json
import os
import subprocess
import sys

USAGE = "usage: ensure_folder_entity.py <definition.json> [<folder-path>]"


def uip_json(*args):
    r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FAIL: uip {' '.join(args)}\n{r.stderr[:800] or r.stdout[:800]}", file=sys.stderr)
        sys.exit(r.returncode or 1)
    return json.loads(r.stdout)


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(USAGE)
    definition_path = sys.argv[1]
    folder_path = sys.argv[2] if len(sys.argv) == 3 else "Shared"
    with open(definition_path) as f:
        definition = json.load(f)
    name = definition.get("displayName") or definition.get("name")
    if not name:
        sys.exit("FAIL: the definition has no displayName or name")

    folder_key = (uip_json("or", "folders", "get", folder_path).get("Data") or {}).get("Key")
    if not folder_key:
        sys.exit(f"FAIL: folder {folder_path!r} has no key")

    listed = uip_json("df", "entities", "list", "--folder-key", folder_key).get("Data") or []
    existing = next((e for e in listed if (e.get("Name") or "").lower() == name.lower()), None)
    if existing:
        key = existing.get("Id")
        print(f"OK: entity {name!r} already in {folder_path!r} ({key})")
    else:
        created = uip_json("df", "entities", "create", name, "--file", definition_path, "--folder-key", folder_key)
        key = (created.get("Data") or {}).get("Id")
        print(f"OK: created entity {name!r} in {folder_path!r} ({key})")

    os.makedirs("_setup", exist_ok=True)
    with open(os.path.join("_setup", "picker_entity.json"), "w") as f:
        json.dump({"name": name, "key": key, "folderKey": folder_key, "folderPath": folder_path}, f, indent=2)


if __name__ == "__main__":
    main()
