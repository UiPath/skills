#!/usr/bin/env python3
"""T5b — a case-breach oversight lane that the source wants to run alongside the work.

Same requirement family as T5a, one clause different: the case team keeps working while
the lane runs. The product cannot do that. Every entry into a secondary stage interrupts:
the compiler emits cancelStagesAndTasks for an sla-status-change secondary entry written
isInterrupting:false, and at runtime (debug instance 72162d9b, 2026-10-06) the breach
exited the active stage and cancelled its in-flight task. So the built lane must carry
isInterrupting True — the honest shape — and stay secondary and non-required; promoting
it to a regular stage to dodge the interrupt would make it required for case completion.
Whether the reply tells the user the work will pause is graded separately.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import is_non_required  # noqa: E402
from _shared.sla_response_check import (  # noqa: E402
    assert_breach_shape,
    assert_interrupting,
    assert_no_any_sentinel,
    assert_sla_resolves,
    assert_stage_count,
    fail,
    is_secondary,
    iter_sla_status_change,
    label_of,
    read_plan,
)


def main() -> None:
    plan = read_plan()
    assert_no_any_sentinel(plan)
    assert_stage_count(plan, 4)

    hits = list(iter_sla_status_change(plan))
    if len(hits) != 1:
        where = [(label_of(n), c.get("displayName")) for n, c, _ in hits]
        fail(f"expected exactly 1 sla-status-change entry rule, found {len(hits)}: {where}")
    lane, cond, rule = hits[0]

    if label_of(lane) in {"Intake", "Review", "Decision"}:
        fail(
            f"the oversight entry landed on baseline stage {label_of(lane)!r}; the case-SLA "
            "response should open its own lane"
        )
    if not is_secondary(lane):
        fail(
            f"lane {label_of(lane)!r} has stageType={(lane['data'].get('stageType'))!r}; a "
            "SLA oversight lane stays `secondary` — promoting it to a regular stage to avoid the "
            "interrupt would make it required for case completion"
        )
    if not is_non_required(lane["data"]):
        fail(
            f"lane {label_of(lane)!r} has isRequired={lane['data'].get('isRequired')!r}; an "
            "oversight lane must stay out of the required-stages-completed set"
        )

    where = f"{label_of(lane)} entry condition {cond.get('displayName')!r}"
    assert_sla_resolves(plan, rule, where, owner="root")
    assert_breach_shape(rule, where)
    if cond.get("isInterrupting") is not True:
        fail(
            f"{where} has isInterrupting={cond.get('isInterrupting')!r}; a secondary-stage entry "
            "always interrupts at runtime (the breach exits the active stage and cancels its "
            "tasks whatever the flag says), so the only honest value is True"
        )

    print(
        f"PASS: oversight lane {label_of(lane)!r} on root SLA {rule['slaId']} (no escalationId), "
        "isInterrupting True; stays secondary + isRequired False"
    )


if __name__ == "__main__":
    main()
