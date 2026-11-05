#!/usr/bin/env python3
"""T4 — repair an SLA lane entry whose status contradicts the lane's stated intent.

The staged caseplan's Escalation Review lane is meant to be entered when the case SLA
**breaches** (the prompt says so, and so does the lane's description), but its
``sla-status-change`` entry carries ``escalationId: "any"``. That is the Case Designer's at-risk
wildcard: a valid rule that fires on every at-risk escalation of the SLA (here at 80%), not on
the breach. ``validate`` accepts it, so a green validate proves nothing.

The fix is to drop the key: a breach rule references the SLA alone (an absent
``escalationId`` is the persisted representation of Breached). Repointing it at a concrete
escalation, or inventing one, keeps the lane at-risk and is graded wrong.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.sla_response_check import (  # noqa: E402
    assert_breach_shape,
    assert_no_any_sentinel,
    assert_sla_resolves,
    assert_stage_count,
    escalation_map,
    fail,
    iter_sla_status_change,
    label_of,
    read_plan,
)

BASELINE_ESCALATIONS = {"Notify Case Owner"}


def main() -> None:
    plan = read_plan()
    assert_no_any_sentinel(plan)
    assert_stage_count(plan, 4)

    hits = list(iter_sla_status_change(plan))
    if len(hits) != 1:
        where = [(label_of(n), c.get("displayName")) for n, c, _ in hits]
        fail(
            f"the staged case had exactly 1 sla-status-change entry; found {len(hits)}: {where}. "
            "The repair changes that rule's status; it does not restructure the lane."
        )
    lane, cond, rule = hits[0]
    where = f"{label_of(lane)} entry condition {cond.get('displayName')!r}"

    assert_sla_resolves(plan, rule, where, owner="root")
    assert_breach_shape(rule, where)

    # Inventing an escalation for the rule to point at keeps it at-risk; the lane is a breach lane.
    names = {e["displayName"] for e in escalation_map(plan).values()}
    invented = names - BASELINE_ESCALATIONS
    if invented:
        fail(
            f"new escalation(s) {sorted(invented)} were added for the rule to point at. "
            "A breach rule needs no escalation; drop the escalationId instead."
        )

    print(f"PASS: {where} repaired to a plain breach rule on {rule['slaId']}; no escalation invented")


if __name__ == "__main__":
    main()
