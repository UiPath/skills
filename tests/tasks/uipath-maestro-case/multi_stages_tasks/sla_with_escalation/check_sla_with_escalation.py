#!/usr/bin/env python3
"""SlaWithEscalation: root and regular-stage conditional SLAs + escalations."""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    find_node_by_label,
    get_default_sla,
    get_sla_rules,
    read_caseplan,
)


def _matches_priority_expression(expression: object, expected_value: str) -> bool:
    if not isinstance(expression, str):
        return False
    pattern = (
        r"""=js:\s*vars\.priority\s*===\s*"""
        + rf"""(?P<quote>["']){re.escape(expected_value)}(?P=quote)\s*"""
    )
    return re.fullmatch(pattern, expression, re.IGNORECASE) is not None


def main():
    plan = read_caseplan()
    rules = get_sla_rules(plan)

    if len(rules) != 3:
        sys.exit(
            "FAIL: case-level slaRules should have exactly 3 entries "
            f"(2 conditional + 1 default); got {len(rules)}"
        )
    if rules[-1].get("expression") != "=js:true":
        sys.exit(
            f"FAIL: trailing slaRules entry must be the default '=js:true'; "
            f"got expression={rules[-1].get('expression')!r}"
        )

    default = get_default_sla(plan)
    if not default:
        sys.exit("FAIL: case-level slaRules missing =js:true default rule")
    if default.get("count") != 3 or default.get("unit") != "w":
        sys.exit(
            f"FAIL: case-level default SLA should be count=3, unit=w; "
            f"got count={default.get('count')!r}, unit={default.get('unit')!r}"
        )

    conditional_rules = [r for r in rules if r.get("expression") != "=js:true"]
    if len(conditional_rules) != 2:
        sys.exit(
            f"FAIL: expected exactly 2 conditional SLA rules (Urgent before Standard); "
            f"got {len(conditional_rules)}"
        )
    urgent = conditional_rules[0]
    if urgent.get("count") != 30 or urgent.get("unit") != "min":
        sys.exit(
            f"FAIL: 1st conditional rule (Urgent) should be count=30, unit=min; "
            f"got count={urgent.get('count')!r}, unit={urgent.get('unit')!r}"
        )
    if not _matches_priority_expression(urgent.get("expression"), "Urgent"):
        sys.exit(
            "FAIL: 1st conditional rule must be exactly the priority-is-Urgent "
            f"predicate; got expression={urgent.get('expression')!r}"
        )
    standard = conditional_rules[1]
    if standard.get("count") != 5 or standard.get("unit") != "d":
        sys.exit(
            f"FAIL: 2nd conditional rule (Standard) should be count=5, unit=d; "
            f"got count={standard.get('count')!r}, unit={standard.get('unit')!r}"
        )
    if not _matches_priority_expression(standard.get("expression"), "Standard"):
        sys.exit(
            "FAIL: 2nd conditional rule must be exactly the priority-is-Standard "
            f"predicate; got expression={standard.get('expression')!r}"
        )

    default_escs = default.get("escalationRule") or []
    at_risk = [
        e for e in default_escs
        if (e.get("triggerInfo") or {}).get("type") == "at-risk"
    ]
    if not at_risk:
        sys.exit("FAIL: case-level default SLA has no at-risk escalation")
    if (at_risk[0].get("triggerInfo") or {}).get("atRiskPercentage") != 80:
        sys.exit(
            f"FAIL: at-risk escalation should be atRiskPercentage=80; got "
            f"{(at_risk[0].get('triggerInfo') or {}).get('atRiskPercentage')!r}"
        )
    at_risk_recipients = (at_risk[0].get("action") or {}).get("recipients") or []
    if len(at_risk_recipients) < 2:
        sys.exit(
            f"FAIL: at-risk escalation should be MULTI-RECIPIENT (≥2 recipients on "
            f"one notification); got {len(at_risk_recipients)} recipients"
        )
    at_risk_scopes = {r.get("scope") for r in at_risk_recipients}
    if not {"User", "UserGroup"}.issubset(at_risk_scopes):
        sys.exit(
            f"FAIL: at-risk MULTI-RECIPIENT escalation should include both 'User' "
            f"and 'UserGroup' scopes; got scopes {sorted(s for s in at_risk_scopes if s)}"
        )
    user_values = {
        r.get("value")
        for r in at_risk_recipients
        if r.get("scope") == "User"
    }
    if "manager@corp.com" not in user_values:
        sys.exit(
            f"FAIL: at-risk escalation should target User 'manager@corp.com'; "
            f"got User recipient values {sorted(v for v in user_values if v)}"
        )

    urgent_escs = urgent.get("escalationRule") or []
    breached = [
        e for e in urgent_escs
        if (e.get("triggerInfo") or {}).get("type") == "sla-breached"
    ]
    if not breached:
        sys.exit(
            "FAIL: conditional Urgent rule has no sla-breached escalation "
            "attached"
        )
    group_recipients = [
        r for r in ((breached[0].get("action") or {}).get("recipients") or [])
        if r.get("scope") == "UserGroup"
    ]
    if not group_recipients:
        sys.exit(
            "FAIL: sla-breached escalation on Urgent rule should have a "
            "UserGroup recipient"
        )

    resolve = find_node_by_label(plan, "Resolve")
    stage_rules = get_sla_rules(resolve)
    if len(stage_rules) != 2:
        sys.exit(
            "FAIL: stage 'Resolve' should have exactly one conditional SLA plus "
            f"default; got {len(stage_rules)} rule(s)"
        )
    if stage_rules[-1].get("expression") != "=js:true":
        sys.exit(
            f"FAIL: stage 'Resolve' trailing SLA must be the '=js:true' default; "
            f"got expression={stage_rules[-1].get('expression')!r}"
        )
    stage_conditionals = [
        rule for rule in stage_rules if rule.get("expression") != "=js:true"
    ]
    if len(stage_conditionals) != 1:
        sys.exit(
            "FAIL: stage 'Resolve' must have exactly one conditional SLA rule; "
            f"got {len(stage_conditionals)}"
        )
    stage_urgent = stage_conditionals[0]
    if stage_urgent.get("count") != 2 or stage_urgent.get("unit") != "w":
        sys.exit(
            f"FAIL: stage 'Resolve' Urgent conditional SLA should be count=2, "
            f"unit=w; got count={stage_urgent.get('count')!r}, "
            f"unit={stage_urgent.get('unit')!r}"
        )
    stage_expression = stage_urgent.get("expression")
    if not _matches_priority_expression(stage_expression, "Urgent"):
        sys.exit(
            "FAIL: stage 'Resolve' conditional SLA must be exactly the "
            f"priority-is-Urgent predicate; got expression={stage_expression!r}"
        )
    stage_display_name = stage_urgent.get("displayName")
    if stage_display_name != "Resolve Urgent SLA":
        sys.exit(
            "FAIL: stage 'Resolve' conditional SLA displayName should be "
            f"'Resolve Urgent SLA'; got {stage_display_name!r}"
        )

    stage_default = get_default_sla(resolve)
    if not stage_default:
        sys.exit(
            f"FAIL: stage 'Resolve' missing default SLA on data.slaRules; "
            f"got {(resolve.get('data') or {}).get('slaRules')!r}"
        )
    if stage_default.get("count") != 1 or stage_default.get("unit") != "m":
        sys.exit(
            f"FAIL: 'Resolve' stage default SLA should be count=1, unit=m; "
            f"got count={stage_default.get('count')!r}, "
            f"unit={stage_default.get('unit')!r}"
        )

    resolve_desc = (resolve.get("data") or {}).get("description")
    if not isinstance(resolve_desc, str) or not resolve_desc.strip():
        sys.exit(
            f"FAIL: stage 'Resolve' should carry a non-empty data.description "
            f"(stated in sdd.md); got {resolve_desc!r}"
        )

    print(
        "OK: case-level slaRules has Urgent (30min, sla-breached UserGroup "
        "escalation) → Standard (5d) → default =js:true (3w, at-risk 80% "
        "MULTI-RECIPIENT escalation to User manager@corp.com + UserGroup "
        "Operations Leadership); 'Resolve' stage carries its own data.slaRules "
        "with conditional Urgent 2w before default 1m AND a non-empty "
        "data.description; SLA units "
        "min/d/w/m all exercised"
    )


if __name__ == "__main__":
    main()
