#!/usr/bin/env python3
"""BusinessEventCase: the SDD's Business Events table reaches
metadata.businessEvents, each api-event WHEN cell becomes a rule naming its
event, and strict validate against the SDD raises no business-event finding.

No debug: nothing in the harness can send a business event to a running
case, so a debug run would wait on the stage exit forever."""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import find_caseplan, find_stages, read_caseplan  # noqa: E402

EVENTS = {"Invoice Approved", "Invoice Rejected", "Invoice Withdrawn"}
PAYLOAD_FIELD = "amount"
BUSINESS_EVENT_CODES = (
    "BUSINESS_EVENT",
    "STRICT_SDD_CONDITION_SELECTOR_MISSING",
    "STRICT_SDD_CONDITION_SELECTOR_MISMATCH",
    "STRICT_SDD_CONDITION_RULE_MISMATCH",
)


def api_event_rules(node: object) -> list[dict]:
    found = []
    if isinstance(node, dict):
        if node.get("rule") == "api-event":
            found.append(node)
        for value in node.values():
            found.extend(api_event_rules(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(api_event_rules(value))
    return found


def check_declarations(plan: dict) -> None:
    declared = (plan.get("metadata") or {}).get("businessEvents") or []
    names = {event.get("name") for event in declared if isinstance(event, dict)}
    if names != EVENTS:
        sys.exit(f"FAIL: metadata.businessEvents names {sorted(n for n in names if n)}, expected {sorted(EVENTS)}.")
    approved = next(event for event in declared if event.get("name") == "Invoice Approved")
    if PAYLOAD_FIELD not in str(approved.get("schema", "")):
        sys.exit(f"FAIL: Invoice Approved's schema does not carry the SDD payload's {PAYLOAD_FIELD!r} field: {approved.get('schema')!r}")
    rejected = next(event for event in declared if event.get("name") == "Invoice Rejected")
    if rejected.get("schema"):
        sys.exit(f"FAIL: Invoice Rejected declares no payload in the SDD but carries schema {rejected.get('schema')!r}.")


def check_rules(plan: dict) -> None:
    stage = next((s for s in find_stages(plan) if (s.get("data") or {}).get("label") == "Review"), None)
    if stage is None:
        sys.exit("FAIL: no stage labelled 'Review'.")
    exits = (stage.get("data") or {}).get("exitConditions") or []
    by_event = {}
    for condition in exits:
        for rule in api_event_rules(condition):
            by_event[rule.get("businessEventType")] = condition
    for event, marks in (("Invoice Approved", True), ("Invoice Rejected", False)):
        condition = by_event.get(event)
        if condition is None:
            sys.exit(f"FAIL: Review has no exit rule api-event with businessEventType {event!r}; found {sorted(k for k in by_event if k)}.")
        if bool(condition.get("marksStageComplete")) is not marks:
            sys.exit(f"FAIL: the {event!r} exit has marksStageComplete={condition.get('marksStageComplete')!r}, expected {marks}.")
    stage_ids = {id(s) for s in find_stages(plan)}
    outside = [r for r in api_event_rules({k: v for k, v in plan.items() if k != "nodes"})]
    outside += [r for n in plan.get("nodes", []) if id(n) not in stage_ids for r in api_event_rules(n)]
    if "Invoice Withdrawn" not in {r.get("businessEventType") for r in outside}:
        sys.exit("FAIL: no case-level exit rule api-event with businessEventType 'Invoice Withdrawn'.")
    unnamed = [r for r in api_event_rules(plan) if not r.get("businessEventType")]
    if unnamed:
        sys.exit(f"FAIL: {len(unnamed)} api-event rule(s) carry no businessEventType; they would never fire.")


def check_strict(plan_path: str) -> None:
    sdd = "sdd.md" if os.path.exists("sdd.md") else None
    if sdd is None:
        sys.exit("FAIL: no sdd.md in the working directory to validate against.")
    result = subprocess.run(
        ["uip", "maestro", "case", "validate", plan_path, "--strict", "--sdd", sdd, "--output", "json"],
        capture_output=True, text=True, timeout=120,
    )
    try:
        issues = (json.loads(result.stdout).get("Data") or {}).get("Issues") or []
    except json.JSONDecodeError:
        sys.exit(f"FAIL: strict validate did not return JSON: {result.stdout[:300]!r} {result.stderr[:300]!r}")
    hits = sorted({i.get("Code", "") for i in issues if any(c in i.get("Code", "") for c in BUSINESS_EVENT_CODES)})
    if hits:
        sys.exit(f"FAIL: strict validate against the SDD reports business-event findings: {hits}")


def main():
    plan_path = find_caseplan("BusinessEventCase/**/caseplan.json")
    plan = read_caseplan(plan_path)
    check_declarations(plan)
    check_rules(plan)
    check_strict(plan_path)
    print("OK: three business events declared; Review exits on Approved (complete) and Rejected; "
          "case exits on Withdrawn; strict --sdd raises no business-event finding")


if __name__ == "__main__":
    main()
