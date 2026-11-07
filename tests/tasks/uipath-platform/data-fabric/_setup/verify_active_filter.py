#!/usr/bin/env python3
"""Verify the Active-only walk used a server-side filter and returned the Active rows.

Reads the `uip` calls recorded by `_cli_recorder/uip` (so it sees a query
typed in Bash and one run from a script the agent wrote alike) and passes only if
  1. at least one successful `uip df records query <entity>` on the target entity
     sent a filterGroup whose AND-path contains `Active = true`, and
  2. the IDs in --ids are exactly the entity's rows with Active=true and
     Score 1-300 (read live), so a decoy or client-built file fails.

Exit 0 on pass, 1 with a reason on failure.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

UIP_TIMEOUT_SECONDS = 120
SORT_BY_SCORE = '{"sortOptions":[{"fieldName":"Score","isDescending":false}]}'
VALUE_OPTIONS = {
    "--body", "-f", "--file", "-l", "--limit", "-o", "--offset", "--cursor",
    "--folder-key", "--output", "--output-filter", "--log-level", "--log-file", "--profile",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def run_uip(*args: str) -> dict:
    result = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=UIP_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        fail(f"uip {' '.join(args[:3])} exited {result.returncode}: {result.stderr.strip()[:300]}")
    return json.loads(result.stdout)


def query_parts(argv: list[str]) -> tuple[str | None, str | None, str | None]:
    """Return (entity_id, inline_body, file_value) of a `df records query` argv."""
    start = next((i + 3 for i in range(len(argv)) if argv[i:i + 3] == ["df", "records", "query"]), None)
    if start is None:
        return None, None, None
    entity, body, file_value, i = None, None, None, start
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--") and "=" in arg:
            name, value = arg.split("=", 1)
            if name == "--body":
                body = value
            elif name == "--file":
                file_value = value
        elif arg in VALUE_OPTIONS:
            if i + 1 < len(argv):
                if arg == "--body":
                    body = argv[i + 1]
                elif arg in ("-f", "--file"):
                    file_value = argv[i + 1]
            i += 1
        elif not arg.startswith("-") and entity is None:
            entity = arg
        i += 1
    return entity, body, file_value


def sent_body(call: dict, inline: str | None, file_value: str | None) -> str | None:
    """The body the CLI used: --file wins over --body; "-" means stdin."""
    if file_value is not None:
        return call.get("stdin_body") if file_value == "-" else call.get("file_body")
    return call.get("stdin_body") if inline == "-" else inline


def is_and(operator) -> bool:
    return operator is None or str(operator).strip().lower() in ("0", "and")


def is_true(value) -> bool:
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")


def is_active_true(leaf) -> bool:
    """`Active = true`, or `Active in [true]` (the old text check accepted it too;
    the ID-set check below verifies what the server returned)."""
    if not isinstance(leaf, dict) or leaf.get("fieldName") != "Active":
        return False
    if leaf.get("operator") == "=":
        return is_true(leaf.get("value"))
    values = leaf.get("valueList")
    return leaf.get("operator") == "in" and isinstance(values, list) and len(values) == 1 and is_true(values[0])


def is_score_1_300(score) -> bool:
    """Score 1-300; an integral float (1.0) counts, since the field is DECIMAL."""
    return (isinstance(score, (int, float)) and not isinstance(score, bool)
            and float(score).is_integer() and 1 <= score <= 300)


def has_active_true(group) -> bool:
    """Active = true is required by this group (reached only through AND groups)."""
    if not isinstance(group, dict):
        return False
    filters = group.get("queryFilters") or []
    groups = group.get("filterGroups") or []
    if not is_and(group.get("logicalOperator")) and len(filters) + len(groups) > 1:
        return False
    if any(is_active_true(leaf) for leaf in filters):
        return True
    return any(has_active_true(child) for child in groups)


def find_entity_id(name: str) -> str:
    data = run_uip("df", "entities", "list", "--native-only").get("Data")
    records = data if isinstance(data, list) else (data or {}).get("Records") or []
    for entity in records:
        if isinstance(entity, dict) and (entity.get("Name") or entity.get("name")) == name:
            return str(entity.get("ID") or entity.get("Id") or entity.get("id"))
    fail(f"entity {name} not found")


def live_active_ids(entity_id: str) -> set[str]:
    ids, cursor = set(), None
    for _ in range(50):
        args = ["df", "records", "query", entity_id, "--limit", "100", "--body", SORT_BY_SCORE]
        if cursor:
            args += ["--cursor", cursor]
        data = run_uip(*args).get("Data") or {}
        for row in data.get("Items") or []:
            if is_true(row.get("Active")) and is_score_1_300(row.get("Score")):
                ids.add(str(row["Id"]).lower())
        if not data.get("HasNextPage"):
            return ids
        cursor = (data.get("NextCursor") or {}).get("Value")
    fail("records list did not finish paging")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--entity-name", required=True)
    parser.add_argument("--ids", required=True, type=Path)
    args = parser.parse_args()

    if not args.log.is_file():
        fail(f"no recorded uip calls at {args.log}")
    calls = []
    for line in args.log.read_text(encoding="utf-8").splitlines():
        try:
            calls.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not args.ids.is_file():
        fail(f"{args.ids} not found")
    reported = {line.strip().lower() for line in args.ids.read_text(encoding="utf-8").splitlines() if line.strip()}

    entity_id = find_entity_id(args.entity_name).lower()
    filtered = 0
    for call in calls:
        argv = call.get("argv") or []
        entity, inline, file_value = query_parts(argv)
        if entity is None or call.get("exit") != 0 or entity.lower() != entity_id:
            continue
        raw = sent_body(call, inline, file_value)
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            continue
        if isinstance(body, dict) and has_active_true(body.get("filterGroup")):
            filtered += 1
    if filtered == 0:
        fail(f"no successful records query on {args.entity_name} sent a filterGroup with Active = true")

    expected = live_active_ids(entity_id)
    if len(expected) != 300:
        fail(f"fixture has {len(expected)} Active rows with Score 1-300; expected 300")
    if reported != expected:
        fail(f"{args.ids}: {len(reported - expected)} ID(s) are not Active rows 1-300, "
             f"{len(expected - reported)} Active row(s) missing")
    print(f"OK: {filtered} filtered query call(s); {args.ids} holds exactly the 300 Active rows")


if __name__ == "__main__":
    main()
