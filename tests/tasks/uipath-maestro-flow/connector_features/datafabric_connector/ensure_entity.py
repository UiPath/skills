#!/usr/bin/env python3
"""Ensure a Data Fabric entity exists in the connected tenant.

Idempotent — used from a task's `pre_run` block. Reads a full DF entity
definition from a JSON file whose path is passed as the sole argument:

    python3 ensure_entity.py <definition.json>

The definition file is passed verbatim to `uip df entities create --file`
(same shape returned by `uip df entities get`). Must include at least
`Name` and `Fields[]` with `Name` + `FieldDataType.Name`.

Exits 0 whether the entity already existed or was created. Exits non-zero
only on real infrastructure failure (login expired, CLI missing, etc.),
which fails the pre_run gate and blocks the agent from running against a
broken environment.
"""
import json
import subprocess
import sys


def uip_json(*args):
    r = subprocess.run(["uip", *args, "--output", "json"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FAIL: uip {' '.join(args)}\n{r.stderr[:800] or r.stdout[:800]}",
              file=sys.stderr)
        sys.exit(r.returncode)
    return json.loads(r.stdout)


def main():
    if len(sys.argv) != 2:
        print("usage: ensure_entity.py <definition.json>", file=sys.stderr)
        sys.exit(2)
    def_path = sys.argv[1]
    body = json.load(open(def_path))
    name = body.get("name") or body.get("displayName") or body.get("Name")
    if not name:
        print("FAIL: definition JSON must include `name` or `displayName`", file=sys.stderr)
        sys.exit(2)

    existing = uip_json("df", "entities", "list", "--include-folders",
                        "--output-filter", f"[?Name=='{name}'].Id")
    if existing.get("Data"):
        print(f"OK: entity {name!r} already exists ({existing['Data'][0]})")
        return

    r = uip_json("df", "entities", "create", name, "--file", def_path)
    data = r.get("Data") or {}
    entity_id = data.get("Id") or data.get("ID")
    print(f"OK: created entity {name!r} ({entity_id})")


if __name__ == "__main__":
    main()
