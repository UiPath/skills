#!/usr/bin/env python3
"""
Read a Data Fabric entity's schema and assert a set of field-constraint values.

Used as a `run_command` criterion to check that agent-authored schema
constraints (lengthLimit, decimalPrecision, minValue, maxValue, isRequired,
isUnique, etc.) actually echo back correctly under `entities get`.

Usage:
    verify_field_constraints.py \\
        --entity-name CE_IntegrationOrder \\
        --assertions "amount.decimalPrecision=2,amount.minValue=0,amount.maxValue=1000000" \\
        [--ignore-field-case]

Assertion syntax: comma-separated `<field>.<key>=<value>` triples.
    - Field names are case-sensitive by default (matched against
      Fields[].Name/FieldName). With --ignore-field-case, letter case and
      separators are ignored.
    - Constraint keys are case-insensitive (`decimalPrecision`, `DecimalPrecision`,
      `LengthLimit`, and `lengthLimit` all match the same schema attribute).
    - Values are parsed as int → float → string in that order. Booleans:
      `true` / `false` case-insensitive.

Exit codes:
    0 — every assertion matched
    1 — entity not found, field not found, or any assertion failed
"""

import argparse
import json
import re
import subprocess
import sys
import time

UIP_TIMEOUT_SECONDS = 120
ENTITY_LOOKUP_ATTEMPTS = 2
TENANT_SCOPE = "00000000-0000-0000-0000-000000000000"


def run_uip(*args: str) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=UIP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {UIP_TIMEOUT_SECONDS}s"
    except FileNotFoundError:
        return 127, "", "uip CLI not on PATH"
    return r.returncode, r.stdout, r.stderr


def entity_folder_key(entity: dict) -> str:
    folder_key = (
        entity.get("FolderKey")
        or entity.get("folderKey")
        or entity.get("FolderId")
        or entity.get("folderId")
        or ""
    )
    return "" if str(folder_key).lower() == TENANT_SCOPE else str(folder_key)


def find_entity_id(name: str) -> tuple[str | None, str | None]:
    """Return (id, folder_key) — folder_key is empty for tenant-scoped."""
    include_folders_supported = True
    for attempt in range(ENTITY_LOOKUP_ATTEMPTS):
        extras = (["--include-folders"], []) if include_folders_supported else ([],)
        for extra in extras:
            code, out, err = run_uip(
                "df", "entities", "list", "--native-only", *extra
            )
            if code != 0 or not out.strip():
                detail = f"{out}\n{err}".lower()
                if extra and (
                    "unknown option" in detail or "unknown argument" in detail
                ):
                    include_folders_supported = False
                continue
            try:
                data = json.loads(out)
            except json.JSONDecodeError:
                continue
            inner = data.get("Data") if isinstance(data, dict) else None
            items = (
                inner
                if isinstance(inner, list)
                else (inner or {}).get("Records")
                or (inner or {}).get("records")
                or []
            )
            for e in items:
                if isinstance(e, dict) and (
                    e.get("Name") or e.get("name")
                ) == name:
                    return (
                        e.get("ID") or e.get("Id") or e.get("id"),
                        entity_folder_key(e),
                    )
        if attempt + 1 < ENTITY_LOOKUP_ATTEMPTS:
            time.sleep(2)
    return None, None


def get_schema(entity_id: str, folder_key: str = "") -> dict | None:
    args = ["df", "entities", "get", entity_id]
    if folder_key:
        args += ["--folder-key", folder_key]
    code, out, err = run_uip(*args)
    if code != 0 or not out.strip():
        print(f"FAIL: uip df entities get failed: {err.strip()}", file=sys.stderr)
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        print("FAIL: could not parse entity schema output", file=sys.stderr)
        return None
    return data.get("Data") if isinstance(data.get("Data"), dict) else None


def parse_value(raw: str):
    """int → float → bool → string."""
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    return raw


def parse_assertions(spec: str) -> list[tuple[str, str, object]]:
    out: list[tuple[str, str, object]] = []
    for piece in spec.split(","):
        piece = piece.strip()
        if not piece: continue
        m = re.match(r'^([^.]+)\.([^=]+)=(.*)$', piece)
        if not m:
            raise ValueError(f'bad assertion {piece!r} (want field.key=value)')
        field, key, val = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        out.append((field, key, parse_value(val)))
    return out


def field_data_type(schema: dict, field_name: str, ignore_case: bool = False) -> dict | None:
    def comparable(value: str) -> str:
        if not ignore_case:
            return value
        return re.sub(r"[^a-z0-9]", "", value.casefold())

    for f in (schema.get("Fields") or []):
        if not isinstance(f, dict): continue
        actual_name = f.get("Name") or f.get("FieldName") or f.get("name") or f.get("fieldName")
        names_match = isinstance(actual_name, str) and comparable(actual_name) == comparable(field_name)
        if names_match:
            fdt = f.get("FieldDataType") or f.get("fieldDataType") or {}
            # Merge top-level constraint fields onto fdt (some CLI versions emit at either level).
            merged = {**f, **fdt}
            return merged
    return None


def get_ci(d: dict, key: str):
    """Case-insensitive dict lookup."""
    lk = key.lower()
    for k, v in d.items():
        if k.lower() == lk:
            return v
    return None


def main() -> None:
    p = argparse.ArgumentParser(description="Assert per-field schema constraint values on an entity.")
    p.add_argument("--entity-name", required=True)
    p.add_argument("--assertions", required=True,
                   help='Comma-separated field.key=value assertions, e.g. "amount.decimalPrecision=2,Name.lengthLimit=200"')
    p.add_argument(
        "--ignore-field-case",
        action="store_true",
        help="Match custom field names ignoring case and separators (constraint keys are always case-insensitive)",
    )
    args = p.parse_args()

    try:
        assertions = parse_assertions(args.assertions)
    except ValueError as e:
        p.error(str(e))

    eid, fk = find_entity_id(args.entity_name)
    if not eid:
        print(f"FAIL: entity '{args.entity_name}' not found", file=sys.stderr)
        sys.exit(1)

    schema = get_schema(eid, fk)
    if not schema:
        sys.exit(1)

    failures: list[str] = []
    for field_name, key, expected in assertions:
        fdt = field_data_type(schema, field_name, args.ignore_field_case)
        if fdt is None:
            failures.append(f"{field_name}.{key}: field '{field_name}' not found on entity")
            print(f"  ✗ {field_name}.{key}: field not found")
            continue
        actual = get_ci(fdt, key)
        ok = actual == expected or (
            isinstance(actual, (int, float)) and isinstance(expected, (int, float)) and float(actual) == float(expected)
        )
        if ok:
            print(f"  ✓ {field_name}.{key} = {expected}")
        else:
            failures.append(f"{field_name}.{key}: expected {expected!r}, got {actual!r}")
            print(f"  ✗ {field_name}.{key}: expected {expected!r}, got {actual!r}")

    if failures:
        print(f"\nFAIL: {len(failures)}/{len(assertions)} assertions failed", file=sys.stderr)
        sys.exit(1)
    print(f"\nOK: {len(assertions)}/{len(assertions)} schema constraints match")
    sys.exit(0)


if __name__ == "__main__":
    main()
