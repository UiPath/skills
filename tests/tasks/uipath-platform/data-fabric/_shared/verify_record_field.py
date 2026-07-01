#!/usr/bin/env python3
"""
Read one live record from a Data Fabric entity and assert a field value
matches a regex.

Used as a `run_command` criterion to check "stored form" observations —
e.g. that a RELATIONSHIP field's value is a UUID (not an email / name)
after the agent inserted it. The check is against server state, not agent
self-report.

Usage:
    verify_record_field.py \\
        --entity-name CE_IntegrationOrder \\
        --field-name customerId \\
        --value-regex '^[0-9a-fA-F-]{8,}'

Options:
    --field-name is case-sensitive but the helper tries a case-insensitive
    fallback if the exact key is missing (agents sometimes emit lowercase
    variants alongside the platform's PascalCase key names).

Exit codes:
    0 — entity + record found and field value matches the regex
    1 — entity not found, no records, field not present on the sampled
        record, or the value doesn't match
"""

import argparse
import json
import re
import subprocess
import sys

UIP_TIMEOUT_SECONDS = 60


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


def find_entity_id(name: str) -> tuple[str | None, str | None]:
    """Return (id, folder_key) — folder_key is empty for tenant-scoped."""
    for extra in (["--include-folders"], []):
        code, out, _ = run_uip("df", "entities", "list", "--native-only", *extra)
        if code != 0 or not out.strip():
            continue
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            continue
        items = data.get("Data") if isinstance(data.get("Data"), list) else []
        for e in items:
            if isinstance(e, dict) and (e.get("Name") or e.get("name")) == name:
                return (
                    e.get("ID") or e.get("Id") or e.get("id"),
                    e.get("FolderKey") or e.get("folderKey") or "",
                )
    return None, None


def sample_record(entity_id: str, folder_key: str = "") -> dict | None:
    args = ["df", "records", "list", entity_id, "--limit", "1"]
    if folder_key:
        args += ["--folder-key", folder_key]
    code, out, err = run_uip(*args)
    if code != 0 or not out.strip():
        print(f"FAIL: uip df records list failed: {err.strip()}", file=sys.stderr)
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        print("FAIL: could not parse records list output", file=sys.stderr)
        return None
    inner = (data.get("Data") if isinstance(data.get("Data"), dict) else None) or {}
    items = inner.get("Items") or inner.get("Records") or []
    return items[0] if items else None


def lookup_field(rec: dict, name: str):
    """Exact match first; fall back to case-insensitive match."""
    if name in rec:
        return rec[name]
    lk = name.lower()
    for k, v in rec.items():
        if k.lower() == lk:
            return v
    return None


def main() -> None:
    p = argparse.ArgumentParser(description="Assert a live record's field value matches a regex.")
    p.add_argument("--entity-name", required=True)
    p.add_argument("--field-name", required=True)
    p.add_argument("--value-regex", required=True,
                   help='Regex the field value must match (e.g. "^[0-9a-fA-F-]{8,}" for UUID-shaped)')
    args = p.parse_args()

    try:
        pattern = re.compile(args.value_regex)
    except re.error as e:
        p.error(f"invalid --value-regex: {e}")

    eid, fk = find_entity_id(args.entity_name)
    if not eid:
        print(f"FAIL: entity '{args.entity_name}' not found", file=sys.stderr)
        sys.exit(1)

    rec = sample_record(eid, fk)
    if rec is None:
        print(f"FAIL: no records on '{args.entity_name}' to sample", file=sys.stderr)
        sys.exit(1)

    val = lookup_field(rec, args.field_name)
    if val is None:
        print(
            f"FAIL: field '{args.field_name}' not present on sampled record "
            f"(available fields: {sorted(rec.keys())})",
            file=sys.stderr,
        )
        sys.exit(1)

    if not pattern.match(str(val)):
        print(
            f"FAIL: field '{args.field_name}' value {val!r} does not match /{args.value_regex}/",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"OK: '{args.entity_name}'.'{args.field_name}' = {val!r} matches /{args.value_regex}/")
    sys.exit(0)


if __name__ == "__main__":
    main()
