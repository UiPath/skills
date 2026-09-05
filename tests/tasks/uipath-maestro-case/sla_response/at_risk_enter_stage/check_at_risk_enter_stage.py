#!/usr/bin/env python3
"""T3 — enter-stage on at-risk: separate interrupting lane, concrete at-risk escalationId."""

import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-case")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, _shared_root)
from _shared.sla_response_check import (  # noqa: E402
    assert_at_risk_shape,
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
            f"expected exactly 1 secondary lane for the at-risk takeover, found {len(lanes)}: "
            f"{[label_of(n) for n in lanes]}"
        )
    lane = lanes[0]
    lane_data = lane["data"]

    if not is_non_required(lane_data):
        fail(
            f"lane {label_of(lane)!r} has isRequired={lane_data.get('isRequired')!r}; an SLA lane "
            "must stay out of the happy-path required-stages-completed set"
        )

    hits = [(n, c, r) for n, c, r in iter_sla_status_change(plan) if n is lane]
    if len(hits) != 1:
        fail(f"lane {label_of(lane)!r} should carry exactly 1 sla-status-change entry, found {len(hits)}")
    _node, cond, rule = hits[0]
    where = f"{label_of(lane)} entry condition {cond.get('displayName')!r}"

    assert_sla_resolves(plan, rule, where, owner="root")
    assert_at_risk_shape(plan, rule, where)
    assert_interrupting(cond, True, where)

    exits = lane_data.get("exitConditions") or []
    kinds = {c.get("type") for c in exits}
    if "return-to-origin" not in kinds:
        fail(
            f"lane {label_of(lane)!r} exits with {sorted(kinds)}; a lane that returns to the "
            "interrupted work must exit `return-to-origin`"
        )

    print(
        f"PASS: interrupting at-risk lane {label_of(lane)!r} on root SLA {rule['slaId']} "
        f"via escalation {rule['escalationId']}; return-to-origin; isRequired False"
    )


if __name__ == "__main__":
    main()
