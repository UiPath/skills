#!/usr/bin/env python3
"""T5a — case breach enters a separate interrupting lane that ends the case (exit-only)."""

import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-case")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, _shared_root)
from _shared.sla_response_check import (  # noqa: E402
    assert_breach_shape,
    assert_interrupting,
    assert_no_any_sentinel,
    assert_sla_resolves,
    assert_stage_count,
    fail,
    iter_sla_status_change,
    is_non_required,
    label_of,
    read_plan,
    secondary_stages,
)


def main() -> None:
    plan = read_plan()
    assert_no_any_sentinel(plan)
    assert_stage_count(plan, 4)

    lanes = secondary_stages(plan)
    if len(lanes) != 1:
        fail(
            f"expected exactly 1 secondary lane for the case-SLA breach, found {len(lanes)}: "
            f"{[label_of(n) for n in lanes]}"
        )
    lane = lanes[0]
    if not is_non_required(lane["data"]):
        fail(f"lane {label_of(lane)!r} must be isRequired False")

    hits = [(n, c, r) for n, c, r in iter_sla_status_change(plan) if n is lane]
    if len(hits) != 1:
        fail(f"lane {label_of(lane)!r} should carry exactly 1 sla-status-change entry, found {len(hits)}")
    _node, cond, rule = hits[0]
    where = f"{label_of(lane)} entry condition {cond.get('displayName')!r}"

    assert_sla_resolves(plan, rule, where, owner="root")
    assert_breach_shape(rule, where)
    assert_interrupting(cond, True, where)

    kinds = {c.get("type") for c in lane["data"].get("exitConditions") or []}
    if "exit-only" not in kinds:
        fail(
            f"lane {label_of(lane)!r} exits with {sorted(kinds)}; a terminal lane exits `exit-only` "
            "plus a root case-exit row"
        )

    exit_rules = (plan.get("metadata") or {}).get("caseExitRules") or []
    non_completing = [r for r in exit_rules if r.get("marksCaseComplete") is False]
    if not non_completing:
        kinds = [(r.get("displayName"), r.get("marksCaseComplete")) for r in exit_rules]
        fail(
            "no case-exit rule with marksCaseComplete false; an escalated close-out is a "
            f"non-completing outcome, separate from normal completion. caseExitRules: {kinds}"
        )
    if not any(r.get("marksCaseComplete") is True for r in exit_rules):
        fail("the normal completion rule (marksCaseComplete true) was removed")

    print(
        f"PASS: interrupting breach lane {label_of(lane)!r} on root SLA {rule['slaId']} "
        f"(no escalationId); exit-only + {len(non_completing)} non-completing case-exit rule(s)"
    )


if __name__ == "__main__":
    main()
