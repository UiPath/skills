#!/usr/bin/env python3
"""Verify the local-CRUD smoke produced real artifacts on disk.

Checks (beyond the `command_executed` matchers, which only prove the agent
ran the right shell command):

  1. An evaluator JSON file exists somewhere under SmokeEval/ with
     name == "greeting-match" and evaluatorTypeId == "uipath-exact-match".
  2. An eval-set JSON file exists with name == "Smoke Set", carrying at
     least one data point in `evaluations[]` whose name == "hello" with
     non-empty `inputs` and `expectedOutput`.

These checks fail if the agent ran the commands but they errored, or if
the agent fabricated stdout without producing real files.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path("SmokeEval")


def _load_jsons(root: Path) -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for p in root.rglob("*.json"):
        try:
            out.append((p, json.loads(p.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def main() -> None:
    if not PROJECT.is_dir():
        sys.exit(f"FAIL: project directory {PROJECT} does not exist")

    docs = _load_jsons(PROJECT)
    if not docs:
        sys.exit(f"FAIL: no JSON files found under {PROJECT}")

    evaluator_match = next(
        (
            (p, d)
            for p, d in docs
            if isinstance(d, dict)
            and d.get("name") == "greeting-match"
            and d.get("evaluatorTypeId") == "uipath-exact-match"
        ),
        None,
    )
    if not evaluator_match:
        sys.exit(
            'FAIL: no evaluator JSON under SmokeEval/ has name="greeting-match" '
            'and evaluatorTypeId="uipath-exact-match"'
        )
    print(f"OK: evaluator file {evaluator_match[0]} matches")

    set_match = next(
        (
            (p, d)
            for p, d in docs
            if isinstance(d, dict)
            and d.get("name") == "Smoke Set"
            and isinstance(d.get("evaluations"), list)
        ),
        None,
    )
    if not set_match:
        sys.exit('FAIL: no eval-set JSON under SmokeEval/ has name="Smoke Set"')

    cases = set_match[1].get("evaluations") or []
    hello = next(
        (c for c in cases if isinstance(c, dict) and c.get("name") == "hello"),
        None,
    )
    if not hello:
        sys.exit(
            f'FAIL: eval set "Smoke Set" ({set_match[0]}) has no data point '
            f'named "hello". Got: {[c.get("name") for c in cases if isinstance(c, dict)]}'
        )
    if not hello.get("inputs"):
        sys.exit('FAIL: data point "hello" has empty inputs')
    if not (hello.get("expectedOutput") or hello.get("expected")):
        sys.exit('FAIL: data point "hello" has no expectedOutput / expected field')
    print(
        f"OK: eval set {set_match[0]} contains data point 'hello' with inputs + expected"
    )


if __name__ == "__main__":
    main()
