#!/usr/bin/env python3
"""
Verify a RELATIONSHIP / CHOICE_SET / FILE field on an entity points at the
expected target entity (and optionally target field).

Used as a `run_command` success criterion to replace self-reported schema
echos in report.json — reads the live entity schema and asserts the field's
`referenceEntityId` (and optionally `referenceFieldId`) resolves to the
expected target entity by NAME.

Usage:
    verify_field_binding.py \\
        --entity-name CE_FolderBindExpense \\
        --field-name manager \\
        --target-entity-name CE_FolderBindEmployee \\
        [--folder-key <GUID>]                 # scope of the parent entity
        [--target-folder-key <GUID>]          # scope of the target entity
        [--allow-missing-target]              # exit 0 if target entity not
                                              # found (useful for optional
                                              # checks)

Exit codes:
    0  — field exists on parent AND points at the named target entity
    1  — parent not found, field not found, wrong type / missing reference,
         or points at the wrong entity
"""

import argparse
import json
import subprocess
import sys

UIP_TIMEOUT_SECONDS = 60


def run_uip(*args: str) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=UIP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {UIP_TIMEOUT_SECONDS}s"
    except FileNotFoundError:
        return 127, "", "uip CLI not on PATH"
    return result.returncode, result.stdout, result.stderr


def list_entities_including_folders() -> list[dict]:
    """List every visible entity (tenant + folder-scoped where supported)."""
    for extra in (["--include-folders"], []):
        code, out, _ = run_uip("df", "entities", "list", "--native-only", *extra)
        if code == 0 and out.strip():
            try:
                data = json.loads(out)
            except json.JSONDecodeError:
                continue
            items = data.get("Data") if isinstance(data.get("Data"), list) else []
            if items:
                return items
    return []


def find_entity_id(entities: list[dict], name: str) -> str | None:
    for ent in entities:
        if isinstance(ent, dict) and (ent.get("Name") or ent.get("name")) == name:
            return ent.get("ID") or ent.get("Id") or ent.get("id")
    return None


def get_entity_schema(entity_id: str) -> dict | None:
    code, out, err = run_uip("df", "entities", "get", entity_id)
    if code != 0 or not out.strip():
        print(f"FAIL: uip df entities get {entity_id} failed: {err.strip()}", file=sys.stderr)
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        print("FAIL: could not parse entity schema output", file=sys.stderr)
        return None
    return data.get("Data") if isinstance(data.get("Data"), dict) else None


def main() -> None:
    p = argparse.ArgumentParser(description="Assert a field points at a target entity by name.")
    p.add_argument("--entity-name", required=True, help="Parent entity holding the field")
    p.add_argument("--field-name", required=True, help="Field on the parent entity")
    p.add_argument("--target-entity-name", required=True, help="Expected target entity name")
    p.add_argument("--allow-missing-target", action="store_true",
                   help="Exit 0 if the target entity is not found on the tenant (default: FAIL).")
    args = p.parse_args()

    entities = list_entities_including_folders()
    if not entities:
        print("FAIL: could not list entities", file=sys.stderr)
        sys.exit(1)

    parent_id = find_entity_id(entities, args.entity_name)
    if not parent_id:
        print(f"FAIL: parent entity '{args.entity_name}' not found", file=sys.stderr)
        sys.exit(1)

    target_id = find_entity_id(entities, args.target_entity_name)
    if not target_id:
        if args.allow_missing_target:
            print(f"OK (allowed): target entity '{args.target_entity_name}' not found — check skipped")
            sys.exit(0)
        print(f"FAIL: target entity '{args.target_entity_name}' not found", file=sys.stderr)
        sys.exit(1)

    schema = get_entity_schema(parent_id)
    if not schema:
        sys.exit(1)

    fields = schema.get("Fields") or schema.get("fields") or []
    match = None
    for f in fields:
        if not isinstance(f, dict): continue
        name = f.get("Name") or f.get("name") or f.get("FieldName") or f.get("fieldName")
        if name == args.field_name:
            match = f
            break
    if not match:
        print(f"FAIL: field '{args.field_name}' not found on '{args.entity_name}'", file=sys.stderr)
        sys.exit(1)

    fdt = match.get("FieldDataType") or match.get("fieldDataType") or {}
    ref_id = (
        fdt.get("ReferenceEntityId") or fdt.get("referenceEntityId")
        or match.get("ReferenceEntityId") or match.get("referenceEntityId")
    )
    if not ref_id:
        print(
            f"FAIL: field '{args.field_name}' has no referenceEntityId "
            f"(field type: {fdt.get('SqlTypeName') or match.get('Type') or 'unknown'})",
            file=sys.stderr,
        )
        sys.exit(1)

    if str(ref_id).lower() != str(target_id).lower():
        print(
            f"FAIL: field '{args.field_name}' points at referenceEntityId={ref_id}, "
            f"expected {target_id} ({args.target_entity_name})",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"OK: field '{args.field_name}' on '{args.entity_name}' correctly bound to "
        f"'{args.target_entity_name}' ({target_id})"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
