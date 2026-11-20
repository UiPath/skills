#!/usr/bin/env python3
"""TimerHoldCase: a wait-for-timer whose duration comes from the holdFor input.

Plan check: a wait-for-timer task has `timerType: timeDuration` and the value
`=js:vars.<id>`, where `<id>` is the id of a declared input named holdFor with
the default PT10S. That is the form the Case Designer saves when a variable is
picked; a bare `=vars.<id>` (C#) or a literal duration does not pass.

Run check (default): also runs the case once under `uip maestro case debug` and
requires that wait-for-timer task to complete. `--plan-only` skips the run.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_run_evidence import assert_completed, fail  # noqa: E402
from _shared.case_check import get_variables, iter_tasks, read_caseplan, run_debug  # noqa: E402

INPUT = "holdFor"
DEFAULT = "PT10S"
JS_VAR = re.compile(r"^=js:\s*vars\.([A-Za-z_]\w*)\s*$")


def _hold_for_ids(plan: dict) -> set[str]:
    """Ids a timer may read for holdFor: its inputOutputs row id and its inputs row id."""
    variables = get_variables(plan)
    named = [
        v
        for group in ("inputOutputs", "inputs")
        for v in variables.get(group) or []
        if str(v.get("name") or "") == INPUT
    ]
    return {str(v["id"]) for v in named if v.get("id")}


def _hold_for_default(plan: dict) -> str | None:
    for v in get_variables(plan).get("inputs") or []:
        if str(v.get("name") or "") == INPUT:
            return None if v.get("default") is None else str(v.get("default"))
    return None


def timer_task(plan: dict) -> dict:
    """The wait-for-timer task that reads holdFor as `=js:vars.<id>`; fails with the reason otherwise."""
    timers = [t for t in iter_tasks(plan) if t.get("type") == "wait-for-timer"]
    if not timers:
        types = sorted({str(t.get("type")) for t in iter_tasks(plan)})
        fail(f"the case has no wait-for-timer task; task types: {types}")
    ids = _hold_for_ids(plan)
    if not ids:
        fail(f"no input named {INPUT} is declared")
    default = _hold_for_default(plan)
    if default != DEFAULT:
        fail(f"input {INPUT} defaults to {default!r}, expected {DEFAULT!r}")
    seen = []
    for task in timers:
        data = task.get("data") or {}
        value = str(data.get("timeDuration") or "")
        seen.append((task.get("displayName"), data.get("timerType"), value))
        match = JS_VAR.match(value)
        if data.get("timerType") == "timeDuration" and match and match.group(1) in ids:
            return task
    fail(
        f"no wait-for-timer reads {INPUT} as a duration through '=js:vars.<id>' "
        f"(ids {sorted(ids)}); timers (name, timerType, timeDuration): {seen}"
    )
    raise AssertionError("unreachable")


def main() -> None:
    plan = read_caseplan()
    task = timer_task(plan)
    if "--plan-only" in sys.argv[1:]:
        print(f"OK: timer {task.get('displayName')!r} reads {INPUT} as {task['data']['timeDuration']}")
        return
    payload = run_debug(timeout=840)
    assert_completed(payload, task)
    print(f"OK: debug Completed; timer {task.get('displayName')!r} reading {INPUT} completed")


if __name__ == "__main__":
    main()
