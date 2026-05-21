#!/usr/bin/env python3
"""Verify the agent picked the correct evaluator `--type` for each goal.

Reads `report.json` written by the agent and asserts:

  Goal A — natural-language similarity → llm-judge-output
  Goal B — deterministic JSON shape similarity → json-similarity
  Goal C — substring presence → contains

Each goal must use the kebab-case spelling exactly as the CLI accepts it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPORT = Path("report.json")
EXPECTED = {
    "goal_a_type": "llm-judge-output",
    "goal_b_type": "json-similarity",
    "goal_c_type": "contains",
}


def main() -> None:
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


if __name__ == "__main__":
    main()
