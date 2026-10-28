#!/usr/bin/env python3
"""Check both semantic boolean branches without pinning authoring-loop spelling."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


BOOLEAN_BRANCH = re.compile(
    r"^(?:=js:)?(?:vars\.)?approved={2,3}(true|false)$",
    re.IGNORECASE,
)


def branch_values(value: Any) -> set[bool]:
    found: set[bool] = set()
    if isinstance(value, dict):
        expression = value.get("conditionExpression")
        if isinstance(expression, str):
            match = BOOLEAN_BRANCH.fullmatch(re.sub(r"\s+", "", expression))
            if match:
                found.add(match.group(1).lower() == "true")
        for child in value.values():
            found.update(branch_values(child))
    elif isinstance(value, list):
        for child in value:
            found.update(branch_values(child))
    return found


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: check_boolean_routing.py <caseplan.json>")
    path = Path(sys.argv[1])
    plan = json.loads(path.read_text(encoding="utf-8"))
    found = branch_values(plan)
    missing = {True, False} - found
    if missing:
        sys.exit(f"FAIL: missing approved boolean branch(es): {sorted(missing)}")
    print(f"OK: {path} contains approved true and false branches")


if __name__ == "__main__":
    main()
