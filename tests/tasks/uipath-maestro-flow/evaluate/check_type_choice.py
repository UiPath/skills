#!/usr/bin/env python3
"""Verify the persisted evaluator types and the agent's reasoning report.

Reads `report.json` written by the agent and asserts:

  Goal A — natural-language similarity → llm-judge-output
  Goal B — deterministic JSON shape similarity → json-similarity
  Goal C — substring presence → contains

Pass ``--artifact goal-a|goal-b|goal-c`` to check one persisted evaluator;
without it, check the report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPORT = Path("report.json")
EXPECTED = {
    "goal_a_type": "llm-judge-output",
    "goal_b_type": "json-similarity",
    "goal_c_type": "contains",
}
ARTIFACT_EXPECTED = {
    "goal-a": ("goal-a-evaluator", "uipath-llm-judge-output-semantic-similarity"),
    "goal-b": ("goal-b-evaluator", "uipath-json-similarity"),
    "goal-c": ("goal-c-evaluator", "uipath-contains"),
}


def _load_jsons() -> list[tuple[Path, dict]]:
    docs = []
    for path in Path(".").rglob("*.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            docs.append((path, value))
    return docs


def _check_artifact(goal: str) -> None:
    name, type_id = ARTIFACT_EXPECTED[goal]
    match = next(
        (
            path
            for path, doc in _load_jsons()
            if doc.get("name") == name and doc.get("evaluatorTypeId") == type_id
        ),
        None,
    )
    if match is None:
        sys.exit(f"FAIL: no {name!r} evaluator artifact has type {type_id!r}")
    print(f"OK: {match} persists {name!r} with type {type_id!r}")


def _check_report() -> None:
    if not REPORT.is_file():
        sys.exit(f"FAIL: missing {REPORT}")
    try:
        doc = json.loads(REPORT.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {REPORT} is not valid JSON: {e}")

    failures: list[str] = []
    for key, want in EXPECTED.items():
        got = doc.get(key)
        if got != want:
            failures.append(f"{key}: got {got!r}, expected {want!r}")

    if failures:
        sys.exit("FAIL: " + " | ".join(failures))
    print(
        f"OK: all 3 evaluator-type choices match expected ({list(EXPECTED.values())})"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", choices=ARTIFACT_EXPECTED)
    args = parser.parse_args()
    if args.artifact:
        _check_artifact(args.artifact)
    else:
        _check_report()


if __name__ == "__main__":
    main()
