#!/usr/bin/env python3
"""
Verify per-row constraint outcomes on a Data Fabric entity by querying the
server directly — not the agent's self-report.

Used to grade tests where multiple record inserts are attempted with a mix
of positive and negative-path shapes. After the agent finishes, this script
lists all records on the entity, extracts the value of a chosen key column
(default: `Code`), and asserts that each expected code is present or absent
per the `--expected-codes` map.

Usage:
    verify_constraint_outcomes.py \\
        --entity-name CE_ConstraintTest \\
        --expected-codes "OK1=present,NEG1=absent,OVR=absent,DTBAD=absent" \\
        [--key-column Code]                # column to extract; default Code
        [--allow-mismatches 0]             # tolerate N mismatches; default 0

Exit codes:
    0 — every expectation matched (or matches ≤ --allow-mismatches)
    1 — entity not found, uip call failed, or more mismatches than allowed
"""

import argparse
import json
import subprocess
import sys

UIP_TIMEOUT_SECONDS = 60
LIST_PAGE_SIZE = 200


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
        for ent in items:
            if isinstance(ent, dict) and (ent.get("Name") or ent.get("name")) == name:
                return (
                    ent.get("ID") or ent.get("Id") or ent.get("id"),
                    ent.get("FolderKey") or ent.get("folderKey") or "",
                )
    return None, None


def list_all_codes(entity_id: str, key_column: str, folder_key: str = "") -> set[str] | None:
    """Page through every record and collect the value of `key_column`."""
    seen: set[str] = set()
    cursor: str | None = None
    while True:
        args = ["df", "records", "list", entity_id, "--limit", str(LIST_PAGE_SIZE)]
        if folder_key:
            args += ["--folder-key", folder_key]
        if cursor:
            args += ["--cursor", cursor]
        code, out, err = run_uip(*args)
        if code != 0 or not out.strip():
            print(f"FAIL: uip df records list failed: {err.strip()}", file=sys.stderr)
            return None
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            print("FAIL: could not parse records list output", file=sys.stderr)
            return None
        inner = data.get("Data") if isinstance(data.get("Data"), dict) else {}
        items = inner.get("Items") or inner.get("Records") or inner.get("records") or []
        for r in items:
            if not isinstance(r, dict): continue
            val = r.get(key_column)
            if val is not None:
                seen.add(str(val))
        if not inner.get("HasNextPage"):
            break
        cursor = inner.get("NextCursor") or inner.get("nextCursor")
        if not cursor:
            break
    return seen


def parse_expectations(spec: str) -> dict[str, bool]:
    """`k1=present,k2=absent,...` → {"k1": True, "k2": False}."""
    out: dict[str, bool] = {}
    for piece in spec.split(","):
        piece = piece.strip()
        if not piece: continue
        if "=" not in piece:
            raise ValueError(f"bad --expected-codes item {piece!r} (want key=present|absent)")
        k, v = piece.split("=", 1)
        k, v = k.strip(), v.strip().lower()
        if v not in ("present", "absent"):
            raise ValueError(f"bad value for {k}: {v!r} (want present|absent)")
        out[k] = (v == "present")
    return out


def main() -> None:
    p = argparse.ArgumentParser(
        description="Assert per-row constraint outcomes by querying the entity."
    )
    p.add_argument("--entity-name", required=True)
    p.add_argument(
        "--expected-codes", required=True,
        help='Comma-separated "code=present|absent" pairs, e.g. "OK1=present,NEG1=absent"',
    )
    p.add_argument("--key-column", default="Code", help="Column to extract as row key (default: Code)")
    p.add_argument("--allow-mismatches", type=int, default=0,
                   help="Tolerate up to N per-code mismatches (default: 0 = strict)")
    args = p.parse_args()

    try:
        expectations = parse_expectations(args.expected_codes)
    except ValueError as e:
        p.error(str(e))

    entity_id, folder_key = find_entity_id(args.entity_name)
    if not entity_id:
        print(f"FAIL: entity '{args.entity_name}' not found", file=sys.stderr)
        sys.exit(1)

    seen = list_all_codes(entity_id, args.key_column, folder_key)
    if seen is None:
        sys.exit(1)

    matches = 0
    mismatches: list[str] = []
    for code, should_be_present in expectations.items():
        is_present = code in seen
        if is_present == should_be_present:
            matches += 1
            status = "✓"
        else:
            status = "✗"
            mismatches.append(
                f"{code}: expected {'present' if should_be_present else 'absent'}, "
                f"got {'present' if is_present else 'absent'}"
            )
        print(f"  {status} {code}: {'present' if should_be_present else 'absent'}")

    total = len(expectations)
    if len(mismatches) > args.allow_mismatches:
        print(
            f"\nFAIL: {len(mismatches)}/{total} mismatches "
            f"(allowed: {args.allow_mismatches}):",
            file=sys.stderr,
        )
        for m in mismatches:
            print(f"  - {m}", file=sys.stderr)
        sys.exit(1)

    print(
        f"\nOK: {matches}/{total} outcomes match "
        f"({len(mismatches)} mismatch(es) within --allow-mismatches {args.allow_mismatches})"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
