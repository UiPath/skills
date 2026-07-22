#!/usr/bin/env python3
"""Best-effort cleanup for Studio Web solutions created by BPMN debug runs."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


STATE = Path("bpmn-debug-solutions.json")


def main() -> int:
    policy = os.environ.get("BPMN_E2E_CLEANUP", "always").casefold()
    if policy == "never":
        print("cleanup_debug_solutions: BPMN_E2E_CLEANUP=never; preserving debug solutions")
        return 0
    if not STATE.is_file():
        print("cleanup_debug_solutions: no recorded debug solutions")
        return 0

    try:
        loaded = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cleanup_debug_solutions: could not read {STATE}: {exc}")
        return 0
    solution_ids = sorted({item for item in loaded if isinstance(item, str) and item})

    failed = 0
    for solution_id in solution_ids:
        try:
            result = subprocess.run(
                ["uip", "solution", "delete", solution_id, "--yes", "--output", "json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"cleanup_debug_solutions: warning: {solution_id}: {exc}")
            failed += 1
            continue
        if result.returncode == 0:
            print(f"cleanup_debug_solutions: deleted {solution_id}")
        else:
            detail = (result.stdout or result.stderr).strip().replace("\n", " ")[:400]
            print(
                "cleanup_debug_solutions: warning: failed to delete "
                f"{solution_id} (exit {result.returncode}): {detail}"
            )
            failed += 1
    if failed:
        print(
            f"cleanup_debug_solutions: warning: {failed}/{len(solution_ids)} "
            "recorded debug solutions could not be deleted"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
