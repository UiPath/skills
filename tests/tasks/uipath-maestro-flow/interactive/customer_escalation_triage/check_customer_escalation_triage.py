#!/usr/bin/env python3
"""Execute seeded escalation cases and verify named business outcomes."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


_directory = os.path.dirname(os.path.abspath(__file__))
while _directory != os.path.dirname(_directory) and not os.path.isdir(
    os.path.join(_directory, "_shared")
):
    _directory = os.path.dirname(_directory)
sys.path.insert(0, _directory)

from _shared.flow_check import assert_output_nonempty, run_debug  # noqa: E402


def normalized(value: Any) -> Any:
    """Normalize scalar runtime values without accepting loose substrings."""
    if isinstance(value, str):
        text = value.strip()
        lowered = text.casefold()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return lowered
    return value


def assert_named_equals(payload: dict, name: str, expected: Any) -> None:
    actual = assert_output_nonempty(payload, name)
    if normalized(actual) != normalized(expected):
        raise SystemExit(
            f"FAIL: output {name!r}: expected {expected!r}, got {actual!r}"
        )


def verify_case(case: dict) -> None:
    payload = run_debug(inputs=case["inputs"], timeout=300)
    for name, expected in case["expected"].items():
        assert_named_equals(payload, name, expected)
    print(f"OK: {case['name']} produced the expected business outcomes")


def main() -> None:
    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    cases = seed.get("cases")
    if not isinstance(cases, list) or len(cases) != 2:
        raise SystemExit("FAIL: seed.json must contain exactly two cases")
    for case in cases:
        verify_case(case)


if __name__ == "__main__":
    main()
