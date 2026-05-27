#!/usr/bin/env python3
"""
Pre-run / post-run cleanup: delete native Data Fabric entities whose Name
matches a given base prefix.

Usage (typically called from a task's pre_run before a greenfield test):
    python3 cleanup_entities_by_name.py --name-prefix EmployeeDirectory

Matches entity names that are either equal to <prefix> exactly, or start
with `<prefix>_` (the suffixed-name convention used by greenfield e2e tasks,
e.g. `EmployeeDirectory_1716163200`). Catches leftovers from prior runs
where the agent failed before writing report.json, so the next run starts
from a clean slate and is forced to actually run `entities create`.

Auth:
  Uses the active `uip` login. The script calls `uip df entities list`
  and `uip df entities delete`, so the CLI must be logged in. If the CLI
  is not logged in or any uip call fails, the script logs a SKIP and
  exits 0 — cleanup never fails the test.

Exit 0 always.
"""

import argparse
import json
import subprocess
import sys


UIP_TIMEOUT_SECONDS = 60


def run_uip(*args: str) -> tuple[int, str, str]:
    """Run `uip <args> --output json`. Return (exit_code, stdout, stderr)."""
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


def list_native_entities() -> list[dict]:
    code, out, err = run_uip("df", "entities", "list", "--native-only")
    if code != 0 or not out.strip():
        print(f"SKIP: uip df entities list failed (exit {code}): {err.strip()}")
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError as e:
        print(f"SKIP: could not parse entities list output: {e}")
        return []
    inner = data.get("Data") if isinstance(data, dict) else None
    if isinstance(inner, dict):
        return inner.get("Records") or inner.get("records") or []
    if isinstance(inner, list):
        return inner
    return []


def match_by_prefix(entities: list[dict], prefix: str) -> list[tuple[str, str]]:
    """Return (id, name) pairs for entities matching the prefix.

    A name matches when it equals `<prefix>` exactly OR starts with `<prefix>_`.
    """
    suffix_match = f"{prefix}_"
    out: list[tuple[str, str]] = []
    for ent in entities:
        if not isinstance(ent, dict):
            continue
        name = ent.get("Name") or ent.get("name") or ""
        eid = ent.get("ID") or ent.get("Id") or ent.get("id") or ""
        if not name or not eid:
            continue
        if name == prefix or name.startswith(suffix_match):
            out.append((eid, name))
    return out


def delete_entity(entity_id: str, name: str) -> None:
    code, out, err = run_uip(
        "df", "entities", "delete", entity_id,
        "--confirm",
        "--reason", "greenfield-test pre/post-run cleanup",
    )
    if code == 0:
        print(f"OK: deleted leftover entity {name} ({entity_id})")
    else:
        # Non-zero is treated as a warning, not a failure — the test must
        # not be blocked by cleanup quirks (entity in use, transient API
        # error, already deleted in a parallel run, etc.).
        msg = (err.strip() or out.strip())[:200]
        print(f"WARN: uip df entities delete {entity_id} failed (exit {code}): {msg}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete native Data Fabric entities matching a name prefix."
    )
    parser.add_argument(
        "--name-prefix",
        required=True,
        help="Base entity name (matches `<prefix>` exactly or `<prefix>_*`).",
    )
    args = parser.parse_args()

    entities = list_native_entities()
    matches = match_by_prefix(entities, args.name_prefix)
    if not matches:
        print(f"OK: no leftover entities matching `{args.name_prefix}` / `{args.name_prefix}_*`")
        sys.exit(0)

    print(f"Found {len(matches)} leftover entity/entities matching `{args.name_prefix}`:")
    for eid, name in matches:
        print(f"  - {name} ({eid})")
        delete_entity(eid, name)

    sys.exit(0)


if __name__ == "__main__":
    main()
