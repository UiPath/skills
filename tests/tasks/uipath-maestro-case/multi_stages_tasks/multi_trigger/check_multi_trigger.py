#!/usr/bin/env python3
"""MultiTrigger: manual + infinite-hourly + bounded-scheduled timer triggers, each → Run."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_count,
    find_node_by_label,
    find_triggers,
    read_caseplan,
)


def main():
    plan = read_caseplan()

    triggers = find_triggers(plan)
    assert_count(len(triggers), 3, "trigger node(s)")

    service_types = []
    for t in triggers:
        uipath = ((t.get("data") or {}).get("uipath")) or {}
        service_types.append(uipath.get("serviceType"))

    if "None" not in service_types:
        sys.exit(
            f"FAIL: no manual trigger (serviceType='None'); got {service_types}"
        )
    timer_count = sum(1 for s in service_types if s == "Intsvc.TimerTrigger")
    if timer_count != 2:
        sys.exit(
            f"FAIL: expected 2 timer triggers (serviceType='Intsvc.TimerTrigger'); "
            f"got {timer_count} ({service_types})"
        )

    timer_cycles = [
        ((t.get("data") or {}).get("uipath") or {}).get("timeCycle")
        for t in triggers
        if ((t.get("data") or {}).get("uipath") or {}).get("serviceType")
        == "Intsvc.TimerTrigger"
    ]

    if "R/PT1H" not in timer_cycles:
        sys.exit(
            f"FAIL: missing infinite-hourly timer (timeCycle='R/PT1H'); "
            f"got cycles {timer_cycles}"
        )
    bounded_cycle = next(
        (c for c in timer_cycles if c and c.startswith("R5/") and "/P1D" in c),
        None,
    )
    if not bounded_cycle:
        sys.exit(
            f"FAIL: missing bounded scheduled timer (expected timeCycle starting "
            f"'R5/' and containing '/P1D'); got cycles {timer_cycles}"
        )
    if "2026-04-26T09:00:00" not in bounded_cycle:
        sys.exit(
            f"FAIL: bounded timer should include explicit start time "
            f"'2026-04-26T09:00:00'; got {bounded_cycle!r}"
        )

    run_stage = find_node_by_label(plan, "Run")
    trigger_edges = [
        e for e in plan.get("edges") or []
        if e.get("type") == "case-management:TriggerEdge"
        and e.get("target") == run_stage["id"]
    ]
    if len(trigger_edges) != 3:
        sys.exit(
            f"FAIL: expected 3 TriggerEdges into 'Run', got {len(trigger_edges)}"
        )

    sources = {e.get("source") for e in trigger_edges}
    expected_sources = {t["id"] for t in triggers}
    if sources != expected_sources:
        sys.exit(
            f"FAIL: TriggerEdge sources {sources} != trigger ids {expected_sources}"
        )

    print(
        "OK: 3 triggers (manual + infinite hourly R/PT1H + bounded daily "
        "R5/2026-04-26T09:00:00.000Z/P1D) each with its own TriggerEdge to Run"
    )


if __name__ == "__main__":
    main()
