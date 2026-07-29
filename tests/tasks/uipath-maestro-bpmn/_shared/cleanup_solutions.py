#!/usr/bin/env python3
"""Best-effort cleanup for Studio Web solutions created by BPMN live debug.

``uip maestro bpmn debug`` may upload a local solution before execution. This
post-run hook removes SolutionIds embedded in local ``.uipx`` files or returned
in saved debug JSON. It never fails an evaluation; CI must not accumulate test
solutions, while developers can preserve them with ``BPMN_E2E_CLEANUP=never``.
"""

from __future__ import annotations

import glob
import json
import os
import subprocess


def solution_ids(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and key.lower() == "solutionid" and isinstance(child, str) and child:
                yield child
            yield from solution_ids(child)
    elif isinstance(value, list):
        for child in value:
            yield from solution_ids(child)


def main() -> int:
    policy = os.environ.get("BPMN_E2E_CLEANUP", "always").lower()
    if policy not in {"always", "never"}:
        print(f"cleanup_solutions: invalid BPMN_E2E_CLEANUP={policy!r}; using always")
        policy = "always"

    ids = set()
    for path in glob.glob("**/*.uipx", recursive=True):
        try:
            with open(path, encoding="utf-8") as handle:
                ids.update(solution_ids(json.load(handle)))
        except (OSError, json.JSONDecodeError) as error:
            print(f"cleanup_solutions: skip {path}: {error}")
            continue
    for path in glob.glob("debug-evidence/**/*.json", recursive=True):
        try:
            with open(path, encoding="utf-8") as handle:
                ids.update(solution_ids(json.load(handle)))
        except (OSError, json.JSONDecodeError) as error:
            print(f"cleanup_solutions: skip {path}: {error}")

    for solution_id in sorted(ids):
        if policy == "never":
            print(f"cleanup_solutions: preserving {solution_id}")
            continue
        try:
            result = subprocess.run(
                ["uip", "solution", "delete", solution_id, "--yes", "--output", "json"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                print(f"cleanup_solutions: deleted {solution_id}")
            else:
                print(f"cleanup_solutions: could not delete {solution_id}: {result.stdout[:300]}")
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"cleanup_solutions: could not delete {solution_id}: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
