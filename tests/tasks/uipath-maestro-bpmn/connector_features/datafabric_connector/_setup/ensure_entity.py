#!/usr/bin/env python3
"""Ensure a Data Fabric entity exists in the connected tenant, with the fields
the local definition requires.

Idempotent — used from a task's `pre_run` block. Reads a full DF entity
definition from a JSON file whose path is passed as the sole argument:

    python3 ensure_entity.py <definition.json>

The definition file is passed to `uip df entities create <name> --file`.
Must include `displayName` (or `name`) and a `fields[]` array of
`{name, type, ...}` entries — matching the write shape the CLI expects
(see `uip df entities create --help`).

When the entity is absent it is created from the definition. When it already
exists the live schema is read back with

    uip df entities get <ENTITY_ID> --output json

and every field in the local definition must be present on the live entity.
A missing field exits 1 with a `FAIL:` line on stderr — the fixture entity is
shared by more than one suite, so a definition that gained a field the tenant
entity never got must fail the pre_run gate loudly instead of letting the task
run against a schema that cannot satisfy it.

Field TYPES are reported, not enforced: the live schema names types in Data
Service's own vocabulary (`Data.Fields[].FieldDataType.Name`), which does not
match the create-time names one for one — the shared tenant entity reads back
INTEGER as DECIMAL, DATETIME as DATETIME_WITH_TZ and UUID as STRING (smoke run
35673274828) while both suites' graders pass against it. A type difference
prints a `WARN:` line so real drift stays visible without failing the gate.

Exits 0 when the entity was created, or already existed with every field.
Exits non-zero on a missing field, or on real infrastructure failure (login
expired, CLI missing, etc.), which fails the pre_run gate and blocks the agent
from running against a broken environment.
"""
import json
import subprocess
import sys
import time

USAGE = "usage: ensure_entity.py <definition.json>"


def uip_json(*args, retries=1):
    for attempt in range(retries):
        r = subprocess.run(["uip", *args, "--output", "json"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return json.loads(r.stdout)
        if attempt < retries - 1:
            time.sleep(2)
    print(f"FAIL: uip {' '.join(args)}\n{r.stderr[:800] or r.stdout[:800]}",
          file=sys.stderr)
    sys.exit(r.returncode)


def entity_id(row):
    """Pull the entity id out of a `--output-filter` row.

    `[?Name=='X'].Id` returns `[{"Id": "<guid>"}]`; older CLI builds wrap a
    projected scalar as `{"Value": "<guid>"}`.
    """
    if isinstance(row, dict):
        return row.get("Id") or row.get("ID") or row.get("Value")
    return row


def live_field_type(field):
    data_type = field.get("FieldDataType") or {}
    return (data_type.get("Name") or field.get("Type") or "").upper()


def reconcile(name, definition, ent_id):
    """Assert every field of the local definition exists on the live entity."""
    live = uip_json("df", "entities", "get", str(ent_id), retries=3)
    data = live.get("Data") or {}
    live_fields = {
        (f.get("Name") or "").lower(): f for f in (data.get("Fields") or [])
    }
    problems = []
    for field in definition.get("fields") or []:
        field_name = field.get("name") or field.get("Name")
        if not field_name:
            continue
        wanted = (field.get("type") or field.get("Type") or "").upper()
        live_field = live_fields.get(field_name.lower())
        if live_field is None:
            problems.append(field_name)
            continue
        got = live_field_type(live_field)
        # FILE fields surface as attachments on some tenants; accept either.
        same = (
            not wanted
            or not got
            or got == wanted
            or (wanted == "FILE" and live_field.get("IsAttachment"))
        )
        if not same:
            print(
                f"WARN: {name}.{field_name} reads back as {got}; definition "
                f"says {wanted} (Data Service type vocabulary differs; not enforced)",
                file=sys.stderr,
            )
    if problems:
        print(
            f"FAIL: entity {name} exists but is missing fields: {problems}",
            file=sys.stderr,
        )
        print(
            f"FAIL: add the missing field(s) to the tenant entity ({ent_id}) "
            f"or reconcile the shared definition; the fixture is shared across suites.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"OK: entity {name!r} ({ent_id}) already exists with all "
          f"{len(definition.get('fields') or [])} required fields")


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        print(__doc__)
        return
    if len(sys.argv) != 2:
        print(USAGE, file=sys.stderr)
        sys.exit(2)
    def_path = sys.argv[1]
    with open(def_path) as f:
        body = json.load(f)
    name = body.get("name") or body.get("displayName") or body.get("Name")
    if not name:
        print("FAIL: definition JSON must include `name` or `displayName`", file=sys.stderr)
        sys.exit(2)

    existing = uip_json("df", "entities", "list", "--include-folders",
                        "--output-filter", f"[?Name=='{name}'].Id",
                        retries=3)
    rows = existing.get("Data") or []
    if rows:
        reconcile(name, body, entity_id(rows[0]))
        return

    r = uip_json("df", "entities", "create", name, "--file", def_path)
    data = r.get("Data") or {}
    entity_id_value = data.get("Id") or data.get("ID")
    print(f"OK: created entity {name!r} ({entity_id_value})")


if __name__ == "__main__":
    main()
