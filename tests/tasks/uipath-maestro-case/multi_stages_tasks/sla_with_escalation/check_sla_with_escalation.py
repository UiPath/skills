#!/usr/bin/env python3
"""SlaWithEscalation: root SLA (w + min) + regular-stage SLA (m) + escalations."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    find_node_by_label,
    get_default_sla,
    get_root,
    get_sla_rules,
    read_caseplan,
)


def main():
    plan = read_caseplan()
    root = get_root(plan)
    rules = get_sla_rules(root)

    if len(rules) < 3:
        sys.exit(
            f"FAIL: root.data.slaRules should have ≥3 entries (2 conditional + "
            f"1 default); got {len(rules)}"
        )
    if rules[-1].get("expression") != "=js:true":
        sys.exit(
            f"FAIL: trailing slaRules entry must be the default '=js:true'; "
            f"got expression={rules[-1].get('expression')!r}"
        )

    default = get_default_sla(root)
    if not default:
        sys.exit("FAIL: root.data.slaRules missing =js:true default rule")
    if default.get("count") != 3 or default.get("unit") != "w":
        sys.exit(
            f"FAIL: root default SLA should be count=3, unit=w; "
            f"got count={default.get('count')!r}, unit={default.get('unit')!r}"
        )

    conditional_rules = [r for r in rules if r.get("expression") != "=js:true"]
    if len(conditional_rules) < 2:
        sys.exit(
            f"FAIL: expected ≥2 conditional SLA rules (Urgent before Standard); "
            f"got {len(conditional_rules)}"
        )
    urgent = conditional_rules[0]
    if urgent.get("count") != 30 or urgent.get("unit") != "min":
        sys.exit(
            f"FAIL: 1st conditional rule (Urgent) should be count=30, unit=min; "
            f"got count={urgent.get('count')!r}, unit={urgent.get('unit')!r}"
        )
    standard = conditional_rules[1]
    if standard.get("count") != 5 or standard.get("unit") != "d":
        sys.exit(
            f"FAIL: 2nd conditional rule (Standard) should be count=5, unit=d; "
            f"got count={standard.get('count')!r}, unit={standard.get('unit')!r}"
        )

    default_escs = default.get("escalationRule") or []
    at_risk = [
        e for e in default_escs
        if (e.get("triggerInfo") or {}).get("type") == "at-risk"
    ]
    if not at_risk:
        sys.exit("FAIL: root default SLA has no at-risk escalation")
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
        "OK: root.data.slaRules has Urgent (30min, sla-breached UserGroup "
        "escalation) → Standard (5d) → default =js:true (3w, at-risk 80% "
        "MULTI-RECIPIENT escalation to User manager@corp.com + UserGroup "
        "Operations Leadership); 'Resolve' stage carries its own data.slaRules "
        "with default 1m AND a non-empty data.description; SLA units "
        "min/d/w/m all exercised"
    )


if __name__ == "__main__":
    main()
