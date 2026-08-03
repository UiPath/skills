#!/usr/bin/env python3
"""T5b — case breach opens a NON-interrupting oversight lane (the carve-out).

Same requirement family as T5a, one clause different: the case team keeps working while
the lane runs. The lane must stay secondary and non-required — promoting it to a regular
stage would make it required for case completion.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
            "non-interrupting SLA oversight lane still stays `secondary` — promoting it to a "
            "regular stage would make it required for case completion"
        )
    if lane["data"].get("isRequired") is not False:
        fail(
            f"lane {label_of(lane)!r} has isRequired={lane['data'].get('isRequired')!r}; an "
            "oversight lane must stay out of the required-stages-completed set"
        )

    where = f"{label_of(lane)} entry condition {cond.get('displayName')!r}"
    assert_sla_resolves(plan, rule, where, owner="root")
    assert_breach_shape(rule, where)
    assert_interrupting(cond, False, where)

    print(
        f"PASS: non-interrupting oversight lane {label_of(lane)!r} on root SLA {rule['slaId']} "
        "(no escalationId); stays secondary + isRequired False"
    )


if __name__ == "__main__":
    main()
