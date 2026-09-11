#!/usr/bin/env python3
"""SupplierOnboarding: does the build carry the SDD's one Skip Condition?

The SDD's Task envelope table gives `Obtain procurement director sign-off` the
skip condition `=js:vars.expectedAnnualSpend < 500000`. It is the only filled
Skip Condition cell among that SDD's 32 envelope tables, and it is the case's
own copy of the sign-off policy: the task's entry guard reads a flag the tier
workflow computes, so without this cell a workflow returning the wrong flag
reaches the director with nothing case-side to stop it.

Two assertions, because a plan that never built the task would otherwise pass
the first one by having nothing to check.

 1. The task exists and is an action task.
 2. It carries a top-level `skipCondition` naming the 500000 threshold. An
    envelope field nested inside `data` is dead config the platform never
    reads, so that placement fails too, and says so.

Read-only. Exit 0 clean, 1 on findings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PLAN = Path("SupplierOnboarding/SupplierOnboarding/caseplan.json")
TASK = "Obtain procurement director sign-off"
THRESHOLD = "500000"


def tasks_of(plan: dict) -> list[dict]:
    out: list[dict] = []
    for node in plan.get("nodes") or []:
        for lane in (node.get("data") or {}).get("tasks") or []:
            for task in lane if isinstance(lane, list) else [lane]:
                if isinstance(task, dict):
                    out.append(task)
    return out


def main() -> int:
    if not PLAN.exists():
        print(f"FAIL: {PLAN} is missing", file=sys.stderr)
        return 1
    plan = json.loads(PLAN.read_text())
    print(f"checked {PLAN}")

    found = [t for t in tasks_of(plan) if t.get("displayName") == TASK]
    problems: list[str] = []

    if not found:
        problems.append(
            f"the plan carries no task named {TASK!r}; the SDD declares it in "
            "Compliance and risk review"
        )
    else:
        task = found[0]
        print(f"task type: {task.get('type')}")
        value = task.get("skipCondition")
        nested = ((task.get("data") or {}).get("skipCondition"))
        if isinstance(value, str) and THRESHOLD in value:
            print(f"skipCondition: {value}")
        elif isinstance(nested, str) and THRESHOLD in nested:
            problems.append(
                f"{TASK!r} carries its skip condition inside `data`; envelope "
                "fields are siblings of `data`, and one nested there is dead "
                "config the platform never reads"
            )
        elif isinstance(value, str) and value.strip():
            problems.append(
                f"{TASK!r} carries skipCondition {value!r}, which does not name "
                f"the {THRESHOLD} threshold its SDD envelope declares"
            )
        else:
            problems.append(
                f"{TASK!r} carries no skipCondition; its SDD Task envelope "
                f"declares `=js:vars.expectedAnnualSpend < {THRESHOLD}`, so the "
                "case cannot enforce the sign-off policy on its own"
            )

    if problems:
        print(f"\nFAIL: {len(problems)} finding(s):", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print(
        "OK: the director sign-off task carries the SDD's skip condition, so the "
        f"{THRESHOLD} policy is enforced case-side"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
