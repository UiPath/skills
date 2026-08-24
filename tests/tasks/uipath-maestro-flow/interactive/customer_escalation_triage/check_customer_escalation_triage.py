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

# Load by file path under a suite-unique module name: three sibling suites each
# ship a `_shared` package, so a plain `from _shared... import` resolves against
# whichever suite loaded first in the same process (pytest full-tree runs).
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "maestro_flow_shared_flow_check", os.path.join(_directory, "_shared", "flow_check.py")
)
_flow_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_flow_check)
assert_output_nonempty = _flow_check.assert_output_nonempty
run_debug = _flow_check.run_debug


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
