#!/usr/bin/env python3
"""Verify a solution-authored (local) Data Fabric entity on disk.

Usage:
  verify_local_entity.py <EntityName> <field>:<sqlType>[:required] ...

Finds the single .uipx solution under the cwd, then checks:
  - resources/solution_folder/entity/native/<EntityName>.json exists
  - its FolderId is the unassigned-folder sentinel (it is local, not a
    tenant entity copied down)
  - the resource key matches the entity Id
  - every listed field exists with that SqlType name, and is required when
    `:required` is given

Exits 0 on success, 1 with a reason on the first failed check.
"""

import glob
import json
import os
import sys

UNASSIGNED_FOLDER_ID = "99999999-9999-9999-9999-999999999999"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def solution_root() -> str:
    found = [p for p in glob.glob("**/*.uipx", recursive=True) if "node_modules" not in p]
    if len(found) != 1:
        fail(f"expected exactly one .uipx under {os.getcwd()}, found {found}")
    return os.path.dirname(found[0]) or "."


def main() -> None:
    if len(sys.argv) < 2:
        fail("usage: verify_local_entity.py <EntityName> <field>:<sqlType>[:required] ...")
    name, specs = sys.argv[1], sys.argv[2:]
    root = solution_root()

    path = os.path.join(root, "resources", "solution_folder", "entity", "native", f"{name}.json")
    if not os.path.isfile(path):
        fail(f"no local entity resource at {path}")
    resource = json.load(open(path))["resource"]
    entity = json.loads(resource["spec"]["resourceJson"])

    if entity.get("FolderId") != UNASSIGNED_FOLDER_ID:
        fail(f"FolderId is {entity.get('FolderId')!r}, not the local sentinel")
    if resource.get("key") != entity.get("Id"):
        fail(f"resource key {resource.get('key')!r} != entity Id {entity.get('Id')!r}")

    fields = {f["Name"].lower(): f for f in entity.get("Fields", []) if not f.get("IsSystemField")}
    for spec in specs:
        parts = spec.split(":")
        field, sql_type = parts[0], parts[1].upper()
        required = len(parts) > 2 and parts[2] == "required"
        f = fields.get(field.lower())
        if f is None:
            fail(f"field {field!r} missing; have {sorted(fields)}")
        actual = f["SqlType"]["Name"].upper()
        if actual != sql_type:
            fail(f"field {field!r} is {actual}, expected {sql_type}")
        if required and not f.get("IsRequired"):
            fail(f"field {field!r} should be required")

    print(f"OK: {name} is local with {len(specs)} expected fields")


if __name__ == "__main__":
    main()
