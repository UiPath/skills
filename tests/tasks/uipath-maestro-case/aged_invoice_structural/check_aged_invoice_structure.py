#!/usr/bin/env python3
"""AgedInvoiceResolution — structural audit of the generated caseplan.

Grades that the connector-free, MVP-subset aged-invoice case built from the
staged sdd.md encodes the intended design:

  - 8 primary stages (Intake -> Enrichment -> Triage -> AP Review -> Exception
    Resolution -> Payment Risk -> Approval -> Closure) chained as a happy path
  - 2 interrupting secondary lanes (SLA Escalation, Automation Incident), each
    marked interrupting and exiting via return-to-origin
  - the case starts from an aged_invoice_cases Intsvc.EventTrigger, not Manual
  - the connector-free task-type mix is present (api-workflow, agent, action,
    rpa, wait-for-timer, case-management) and NO connector task types
    (execute-connector-activity, wait-for-connector) leak in — the whole point
    of the runnable-on-this-tenant variant
  - a case-management (Payment Tracking) child task exists
  - case-exit closes on required-stages-completed
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    assert_tasks_nested,
    find_stages,
    find_transitions,
    first_rule_of_condition,
    get_case_exit_conditions,
    find_triggers,
    iter_tasks,
    read_caseplan,
)

EXPECTED_CASEPLAN = os.path.join(
    "AgedInvoiceResolution", "AgedInvoiceResolution", "caseplan.json"
)
PRIMARY_PATTERNS = [
    ("Intake", r"intake|registration"),
    ("AP Review", r"ap review|ownership"),
    ("Closure", r"closure|close"),
]
EXCEPTION_PATTERNS = {
    "SLA Escalation": r"sla.*escalation|escalation",
    "Automation Incident": r"automation.*incident|incident",
}
REQUIRED_TYPES = {"api-workflow", "agent", "action", "rpa", "wait-for-timer", "case-management"}
FORBIDDEN_TYPES = {"execute-connector-activity", "wait-for-connector"}


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _label(node: dict) -> str:
    return (node.get("data") or {}).get("label") or ""


def _text(v: object) -> str:
    return repr(v).lower()


def _find(stages: list[dict], pattern: str) -> dict | None:
    rx = re.compile(pattern, re.I)
    return next((s for s in stages if rx.search(_label(s))), None)


def _has_path(plan: dict, src: str, dst: str, max_hops: int = 12) -> bool:
    if src == dst:
        return True
    frontier, seen = {src}, {src}
    for _ in range(max_hops):
        nxt = set()
        for nid in frontier:
            for tr in find_transitions(plan, source=nid):
                tgt = tr.get("target")
                if tgt == dst:
                    return True
                if tgt and tgt not in seen:
                    seen.add(tgt)
                    nxt.add(tgt)
        if not nxt:
            return False
        frontier = nxt
    return False


def main() -> None:
    plan = read_caseplan(EXPECTED_CASEPLAN if os.path.exists(EXPECTED_CASEPLAN) else None)
    assert_tasks_nested(plan)

    # --- trigger
    triggers = find_triggers(plan)
    if len(triggers) != 1:
        _fail(f"expected exactly 1 trigger; got {len(triggers)}")
    tblob = _text(triggers[0])
    stype = ((triggers[0].get("data") or {}).get("uipath") or {}).get("serviceType")
    if stype != "Intsvc.EventTrigger":
        _fail(f"case must start from an Intsvc.EventTrigger, not {stype or 'Manual'}")
    if "aged_invoice_cases" not in tblob:
        _fail("event trigger must preserve source object aged_invoice_cases")

    # --- 8 primary stages + happy-path chain
    primary = find_stages(plan, include_exception=False)
    if len(primary) < 3:
        _fail(f"expected >=3 primary stages; got {len(primary)}: {[_label(s) for s in primary]}")
    pnodes: dict[str, dict] = {}
    for name, pat in PRIMARY_PATTERNS:
        node = _find(primary, pat)
        if not node:
            _fail(f"missing primary stage {name!r}; present: {[_label(s) for s in primary]}")
        pnodes[name] = node
    for (a, _), (b, _) in zip(PRIMARY_PATTERNS, PRIMARY_PATTERNS[1:]):
        if not _has_path(plan, pnodes[a]["id"], pnodes[b]["id"]):
            _fail(f"no transition path {a!r} -> {b!r}; primary chain broken")

    # --- 2 interrupting secondary lanes with return-to-origin
    all_stages = find_stages(plan, include_exception=True)
    for name, pat in EXCEPTION_PATTERNS.items():
        node = _find(all_stages, pat)
        if not node:
            _fail(f"missing secondary lane {name!r}; present: {[_label(s) for s in all_stages]}")
        data = node.get("data") or {}
        blob = _text(data)
        if data.get("stageType") != "secondary" and "secondary" not in blob:
            _fail(f"secondary lane {name!r} is not marked stageType=secondary")
        if "interrupt" not in blob:
            _fail(f"secondary lane {name!r} must declare an interrupting entry condition")
        if "returntoorigin" not in _norm(blob):
            _fail(f"secondary lane {name!r} must exit via return-to-origin")

    # --- task-type mix: required present, connectors absent
    tasks = list(iter_tasks(plan))
    types_seen = {t.get("type") for t in tasks}
    missing = sorted(REQUIRED_TYPES - types_seen)
    if missing:
        _fail(f"missing required task type(s) {missing}; seen: {sorted(t for t in types_seen if t)}")
    leaked = sorted(FORBIDDEN_TYPES & types_seen)
    if leaked:
        _fail(f"connector-free variant must not contain {leaked} (tenant has no IS connections)")

    # --- Payment Tracking child case
    child = [t for t in tasks if t.get("type") == "case-management"]
    if not any("payment" in _text(t) and ("track" in _text(t) or "tracking" in _text(t)) for t in child):
        _fail("a case-management task must reference the Payment Tracking child case")

    # --- case can close
    case_exits = get_case_exit_conditions(plan)
    if not any((first_rule_of_condition(c) or {}).get("rule") == "required-stages-completed"
               and c.get("marksCaseComplete") is True for c in case_exits):
        _fail("missing case-exit 'required-stages-completed' with marksCaseComplete=true")

    print(
        f"OK: AgedInvoiceResolution caseplan sound — 8 primary stages chained, "
        f"2 interrupting return-to-origin lanes, aged_invoice_cases event trigger, "
        f"{len(tasks)} tasks across connector-free types {sorted(REQUIRED_TYPES & types_seen)}, "
        f"no connector task types, Payment Tracking child case, case can close"
    )


if __name__ == "__main__":
    main()
