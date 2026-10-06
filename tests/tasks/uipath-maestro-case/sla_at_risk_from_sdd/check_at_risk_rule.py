#!/usr/bin/env python3
"""The at-risk start-task rule survives into caseplan.json as an at-risk rule.

The fixture's "Chase Missing Paperwork" task enters on the template's 3-argument
form, sla-status-change("Intake","Intake SLA","Intake at risk"). Built
correctly, that task's entry rule names Intake's SLA AND an escalationId that
resolves, on that same SLA, to the escalation whose displayName is "Intake at
risk" with triggerInfo.type "at-risk". A rule with no escalationId is a breach
rule: the at-risk response would fire only at the deadline.
"""
import json
import os
import sys


def caseplan():
    for d, ds, fs in os.walk("."):
        ds[:] = [x for x in ds if x not in (".venv", "node_modules", ".git")]
        if "caseplan.json" in fs:
            return os.path.join(d, "caseplan.json")
    sys.exit("FAIL: no caseplan.json was built")


def main():
    plan = json.load(open(caseplan(), encoding="utf-8"))
    stages = [n for n in plan.get("nodes", []) if n.get("type") == "case-management:Stage"]
    intake = next((s for s in stages if (s.get("data") or {}).get("label") == "Intake"), None)
    if not intake:
        sys.exit("FAIL: no stage labelled Intake")
    slas = (intake["data"].get("slaRules") or [])
    task = next((t for g in intake["data"].get("tasks") or [] for t in g if t.get("displayName") == "Chase Missing Paperwork"), None)
    if not task:
        sys.exit("FAIL: Intake has no task named Chase Missing Paperwork")
    rules = [r for c in task.get("entryConditions") or [] for g in c.get("rules") or [] for r in g if r.get("rule") == "sla-status-change"]
    if not rules:
        sys.exit("FAIL: Chase Missing Paperwork has no sla-status-change entry rule")
    rule = rules[0]
    sla = next((s for s in slas if s.get("id") == rule.get("slaId")), None)
    if not sla:
        sys.exit(f"FAIL: the rule's slaId {rule.get('slaId')!r} is not one of Intake's SLAs {[s.get('id') for s in slas]}")
    esc_id = rule.get("escalationId")
    if not esc_id:
        sys.exit("FAIL: the rule has no escalationId, so it is a breach rule, not at-risk")
    esc = next((e for e in sla.get("escalationRule") or [] if e.get("id") == esc_id), None)
    if not esc:
        sys.exit(f"FAIL: escalationId {esc_id!r} is not an escalation on {sla.get('displayName')!r}")
    if (esc.get("triggerInfo") or {}).get("type") != "at-risk":
        sys.exit(f"FAIL: escalation {esc.get('displayName')!r} is not at-risk: {esc.get('triggerInfo')}")
    if esc.get("displayName") != "Intake at risk":
        sys.exit(f"FAIL: the rule selects escalation {esc.get('displayName')!r}, not 'Intake at risk'")
    print(f"OK: at-risk rule on {sla.get('displayName')!r} -> escalation {esc.get('displayName')!r}")


if __name__ == "__main__":
    main()
