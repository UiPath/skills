#!/usr/bin/env python3
"""T4 — repair the FE `"any"` escalation sentinel into a plain breach rule.

The staged caseplan is exactly one defect away from valid: its lane entry carries
``escalationId: "any"``, which the Case Designer accepts but released ``validate`` rejects
("The escalation referenced by rule ... no longer exists"). The fix is to drop the key —
a breach rule references the SLA alone — not to invent an escalation to satisfy it.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
            "The repair removes a bad reference, it does not restructure the lane."
        )
    lane, cond, rule = hits[0]
    where = f"{label_of(lane)} entry condition {cond.get('displayName')!r}"

    assert_sla_resolves(plan, rule, where, owner="root")
    assert_breach_shape(rule, where)

    # The cheap wrong fix is inventing an escalation so "any" resolves to something.
    names = {e["displayName"] for e in escalation_map(plan).values()}
    invented = names - BASELINE_ESCALATIONS
    if invented:
        fail(
            f"new escalation(s) {sorted(invented)} were invented to satisfy the reference. "
            "A breach rule needs no escalation — drop the escalationId instead."
        )

    print(f"PASS: {where} repaired to a plain breach rule on {rule['slaId']}; no escalation invented")


if __name__ == "__main__":
    main()
