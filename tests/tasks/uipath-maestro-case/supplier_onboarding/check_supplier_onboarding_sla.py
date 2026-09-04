#!/usr/bin/env python3
"""SupplierOnboarding: the case SLA, seven stage SLAs and their start-task wiring.

The SDD's §1.2 SLA Response Map decides every SLA response:

- at-risk (70%) on the case and on all seven stages → notify-only.
- breach on a stage → start-task: that stage's escalation action task AND its
  supplier delay-notice connector task, each carrying the `sla-status-change`
  rule on its OWN entryConditions against its OWN stage's SLA. Never a
  stage-entry rule — that re-enters the stage and re-runs its tasks
  (_shared/sla_response_check.py).
- breach on the case (root) → the three Procurement Director Post-Mortem
  Review tasks, one per wrap-up stage, all referencing the root SLA.

A breach rule references `slaId` alone; an absent `escalationId` IS the
persisted Breached representation.
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

from _shared.sla_response_check import (  # noqa: E402
    assert_no_any_sentinel,
    sla_owner_map,
    sla_rules_of,
)
import supplier_onboarding_expected as E  # noqa: E402
from supplier_onboarding_plan import (  # noqa: E402
    fail,
    find_task,
    iter_rules,
    load_plan,
    rule_names,
    stage_of,
)

STAGE_SLA_TITLE = {label: f"{label} SLA" for label in E.ALL_STAGES}


def default_rule(rules: list[dict], where: str) -> dict:
    defaults = [rule for rule in rules if rule.get("expression") == "=js:true"]
    if len(defaults) != 1:
        fail(
            f"{where}: expected exactly one default SLA rule (expression '=js:true'), "
            f"got {len(defaults)} of {len(rules)} rule(s): "
            f"{[r.get('displayName') for r in rules]}"
        )
    return defaults[0]


def check_duration(rule: dict, count: int, unit: str, title: str, where: str) -> None:
    if (rule.get("count"), rule.get("unit")) != (count, unit):
        fail(
            f"{where}: SLA duration must be {count} {unit}, got "
            f"{rule.get('count')!r} {rule.get('unit')!r}"
        )
    if E.norm(rule.get("displayName")) != E.norm(title):
        fail(
            f"{where}: SLA title must be {title!r}, got {rule.get('displayName')!r}"
        )


def check_escalations(rule: dict, where: str) -> None:
    escalations = rule.get("escalationRule") or []
    at_risk = [
        esc for esc in escalations if (esc.get("triggerInfo") or {}).get("type") == "at-risk"
    ]
    breached = [
        esc
        for esc in escalations
        if (esc.get("triggerInfo") or {}).get("type") == "sla-breached"
    ]
    if not at_risk:
        fail(f"{where}: missing the 70% at-risk escalation authored in the SDD")
    if not breached:
        fail(f"{where}: missing the breach escalation authored in the SDD")
    for esc in at_risk:
        percentage = (esc.get("triggerInfo") or {}).get("atRiskPercentage")
        if percentage != E.AT_RISK_PERCENTAGE:
            fail(
                f"{where}: at-risk escalation {esc.get('displayName')!r} must fire at "
                f"{E.AT_RISK_PERCENTAGE}% of the SLA, got {percentage!r}"
            )
    for esc in escalations:
        if not esc.get("id") or not esc.get("displayName"):
            fail(
                f"{where}: every escalation needs a non-empty id and displayName "
                f"(schema v27); got {esc!r}"
            )
        if not esc.get("recipients") and not (esc.get("action") or {}).get("recipients"):
            fail(
                f"{where}: escalation {esc.get('displayName')!r} has no recipient; the "
                "SDD names one for every at-risk and breach row"
            )


def check_sla_definitions(plan: dict) -> None:
    root = default_rule(sla_rules_of(plan), "case (root) SLA")
    check_duration(root, *E.CASE_SLA, E.CASE_SLA_TITLE, "case (root) SLA")
    check_escalations(root, "case (root) SLA")

    for label in E.ALL_STAGES:
        stage = stage_of(plan, label)
        rules = sla_rules_of(stage)
        if not rules:
            fail(f"stage {label!r} carries no slaRules; the SDD gives every stage an SLA")
        rule = default_rule(rules, f"{label} SLA")
        count, unit = E.STAGE_SLA[label]
        check_duration(rule, count, unit, STAGE_SLA_TITLE[label], f"{label} SLA")
        check_escalations(rule, f"{label} SLA")


def owner_of(plan: dict, sla_id: str | None) -> str | None:
    return sla_owner_map(plan).get(sla_id)


def check_start_task_wiring(plan: dict) -> None:
    owners = sla_owner_map(plan)
    normalized_owners = {sla_id: E.norm(owner) for sla_id, owner in owners.items()}

    for stage_name, specs in E.TASKS.items():
        stage = stage_of(plan, stage_name)
        for spec in specs:
            if spec["entry"] not in ("sla-stage", "sla-root"):
                continue
            task = find_task(plan, stage, spec["name"])
            if task is None:
                fail(f"{stage_name} is missing task {spec['name']!r}")
            where = f"{stage_name} / {spec['name']}"
            rules = [
                rule
                for rule in iter_rules(task.get("entryConditions") or [])
                if rule.get("rule") == "sla-status-change"
            ]
            if not rules:
                fail(
                    f"{where}: this task is the SDD's start-task response to an SLA "
                    "breach, so it must carry an sla-status-change entry rule; rules "
                    f"found: {sorted(rule_names(task.get('entryConditions') or []))}"
                )
            expected_owner = E.norm(stage_name) if spec["entry"] == "sla-stage" else "root"
            for rule in rules:
                sla_id = rule.get("slaId")
                if sla_id not in owners:
                    fail(
                        f"{where}: sla-status-change references slaId {sla_id!r}, which "
                        f"resolves to no declared SLA (declared: {sorted(owners)})"
                    )
                if normalized_owners[sla_id] != expected_owner:
                    fail(
                        f"{where}: sla-status-change must reference the "
                        f"{'root (case)' if expected_owner == 'root' else stage_name!r} "
                        f"SLA, but slaId {sla_id!r} is owned by {owners[sla_id]!r}"
                    )
                if "escalationId" in rule:
                    fail(
                        f"{where}: a Breached response references the SLA alone — an "
                        "absent escalationId IS the persisted Breached representation, "
                        f"but the rule carries escalationId={rule['escalationId']!r}"
                    )


def check_no_stage_entry_sla(plan: dict) -> None:
    offenders = []
    for label in E.ALL_STAGES:
        stage = stage_of(plan, label)
        conditions = (stage.get("data") or {}).get("entryConditions") or []
        if "sla-status-change" in rule_names(conditions):
            offenders.append(label)
    if offenders:
        fail(
            "every SLA breach in this SDD is a start-task response, so no stage may "
            "carry an sla-status-change ENTRY rule (that re-enters the stage and "
            f"re-runs its tasks); offending stages: {offenders}"
        )


def main() -> None:
    plan = load_plan()
    assert_no_any_sentinel(plan)
    check_sla_definitions(plan)
    check_start_task_wiring(plan)
    check_no_stage_entry_sla(plan)
    print(
        "OK: case SLA 15 d + 7 stage SLAs with 70% at-risk and breach escalations; "
        "14 stage-breach start-tasks and 3 case-breach post-mortem tasks reference "
        "the right SLA in the Breached shape"
    )


if __name__ == "__main__":
    main()
