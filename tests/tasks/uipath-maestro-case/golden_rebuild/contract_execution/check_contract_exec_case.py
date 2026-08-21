#!/usr/bin/env python3
"""ContractExecution rebuild: structural topology and SLA-contract grader.

Checks that the generated caseplan.json encodes the SDD's lifecycle, not just
a structurally valid case:

  - 8 stages: 5 primary + 3 secondary lanes (rejected / withdrawn / overall-SLA
    intervention), each secondary entered by an INTERRUPTING condition
  - condition-derived transitions incl. the corrections loop that re-enters
    Stage 1 from Counsel review, and all three fan-ins to Contract rejected
  - exactly 1 Manual trigger (not an event trigger)
  - 3 case-exit rules: one completing (required-stages-completed) plus the
    rejected and withdrawn terminal exits, both non-completing
  - 30 tasks, per-stage task-type multisets, required set, run-once set
  - the Overall SLA Intervention lane exits `return-to-origin`
  - one case SLA (10d) + 7 stage SLAs with at-risk(70%)/breach escalations,
    and the notify recipients the SDD names
  - every `sla-status-change` trigger points at an SLA declared in its own
    scope: task triggers at their stage's SLA, the intervention lane's stage
    entry at the case SLA
  - direct task-output passing, connector activity v2, and the CTR constant
    case identifier survive
"""

from __future__ import annotations

from collections import Counter
import os
import re
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.case_check import (  # noqa: E402
    assert_tasks_nested,
    find_stages,
    find_transitions,
    find_triggers,
    first_rule_of_condition,
    get_case_exit_conditions,
    get_sla_rules,
    iter_tasks,
    read_caseplan,
)

EXPECTED_CASEPLAN = os.path.join("ContractExecution", "ContractExecution", "caseplan.json")
FIXTURE_SDD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "sdd.md")

CHECKING = "Checking the request"
COUNSEL = "Counsel review"
SENIOR = "Senior counsel review"
SIGNATURE = "Signature and filing"
EXECUTED = "Contract executed"
REJECTED = "Contract rejected"
WITHDRAWN = "Contract withdrawn"
INTERVENTION = "Overall SLA Intervention"

# Stage label -> expected task-type multiset (sorted before comparison).
STAGE_TASK_TYPES = {
    CHECKING: ["action", "action", "agent", "api-workflow", "api-workflow"],
    COUNSEL: ["action", "action", "api-workflow", "api-workflow", "api-workflow"],
    SENIOR: ["action", "action", "agent", "api-workflow", "api-workflow"],
    SIGNATURE: ["api-workflow", "api-workflow", "case-management", "wait-for-connector"],
    EXECUTED: ["api-workflow", "api-workflow", "api-workflow"],
    REJECTED: ["api-workflow", "api-workflow", "api-workflow"],
    WITHDRAWN: ["api-workflow", "api-workflow", "api-workflow"],
    INTERVENTION: ["action", "api-workflow"],
}
SECONDARY_STAGES = {REJECTED, WITHDRAWN, INTERVENTION}

EXPECTED_TRANSITIONS = [
    (CHECKING, COUNSEL),
    (COUNSEL, CHECKING),  # corrections loop: selected-stage-exited("Counsel review")
    (COUNSEL, SENIOR),
    (COUNSEL, REJECTED),
    (SENIOR, SIGNATURE),
    (SENIOR, REJECTED),
    (SIGNATURE, EXECUTED),
    (SIGNATURE, REJECTED),
]

# `Required` / `Run Only Once` columns of the SDD task tables.
REQUIRED_TASKS = {
    "Validate Request Details",
    "Pull Counterparty Records",
    "Notify Assigned Counsel",
    "Counsel Decision",
    "Run Policy and Authority Check",
    "Senior Counsel Decision",
    "Prepare and Send Signature Packet",
    "Wait for Signature Result",
    "Deliver Executed Copy",
    "File Contract",
    "Notify Requester of Rejection",
    "Log Rejection Decision",
    "Confirm Withdrawal",
    "Tidy Up Open Work",
    "Handle Overall SLA Breach",
    "General Counsel Review",
}
RUN_ONCE_TASKS = {
    "Prepare and Send Signature Packet",
    "Open Obligation Tracking",
    "Deliver Executed Copy",
    "File Contract",
    "Notify Requester of Rejection",
    "Log Rejection Decision",
    "Confirm Withdrawal",
    "Tidy Up Open Work",
    "Handle Overall SLA Breach",
    "General Counsel Review",
}

# Stage label -> (SLA duration count, unit). Stages the SDD gives an SLA to;
# the intervention lane deliberately has none.
STAGE_SLA_DURATIONS = {
    CHECKING: (1, "d"),
    COUNSEL: (4, "d"),
    SENIOR: (2, "d"),
    SIGNATURE: (2, "d"),
    EXECUTED: (1, "d"),
    REJECTED: (1, "d"),
    WITHDRAWN: (1, "d"),
}
CASE_SLA_DURATION = (10, "d")

# Tasks whose entry condition is `sla-status-change` on their own stage's SLA.
SLA_TRIGGERED_TASKS = {
    "Handle Checking SLA Breach": CHECKING,
    "Handle Counsel SLA Breach": COUNSEL,
    "Handle Senior Counsel SLA Breach": SENIOR,
    "Handle Signature SLA Breach": SIGNATURE,
    "Handle Executed Wrap Up SLA Breach": EXECUTED,
    "Handle Rejected Wrap Up SLA Breach": REJECTED,
    "Handle Withdrawn Wrap Up SLA Breach": WITHDRAWN,
}

NOTIFY_RE = re.compile(r"Notify:\s*(?:UserGroup|Role)\s*:\s*([^|\n]+?)\s*(?=\||$)")
# `| Case Identifier | Type: constant. Prefix: CTR |`
CASE_IDENTIFIER_RE = re.compile(
    r"^\|\s*Case Identifier\s*\|\s*Type:\s*(?P<type>\w+)\.\s*Prefix:\s*(?P<prefix>\S+?)\s*\|",
    re.M,
)


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _label(node: dict) -> str:
    return (node.get("data") or {}).get("label") or ""


def _read_plan() -> dict:
    if os.path.exists(EXPECTED_CASEPLAN):
        return read_caseplan(EXPECTED_CASEPLAN)
    return read_caseplan()


def _read_fixture() -> str:
    try:
        with open(FIXTURE_SDD, encoding="utf-8") as stream:
            return stream.read()
    except OSError as exc:
        _fail(f"cannot read fixture SDD {FIXTURE_SDD}: {exc}")


def _expected_notify_recipients() -> set[str]:
    recipients = {name.strip() for name in NOTIFY_RE.findall(_read_fixture())}
    if len(recipients) < 3:
        _fail(f"fixture parse error: too few SLA notify recipients; got {sorted(recipients)}")
    return recipients


def _expected_case_identifier() -> tuple[str, str]:
    """Return (prefix, type) from the SDD's Case Identifier row."""
    match = CASE_IDENTIFIER_RE.search(_read_fixture())
    if match is None:
        _fail("fixture parse error: no 'Case Identifier | Type: <type>. Prefix: <prefix>' row")
    return match.group("prefix"), match.group("type")


def _stage_tasks(stage: dict) -> list[dict]:
    tasks: list[dict] = []
    for lane in ((stage.get("data") or {}).get("tasks") or []):
        if isinstance(lane, dict):
            tasks.append(lane)
        elif isinstance(lane, list):
            tasks.extend(task for task in lane if isinstance(task, dict))
    return tasks


def _is_secondary(node: dict) -> bool:
    return (
        (node.get("data") or {}).get("stageType") == "secondary"
        or node.get("type") == "case-management:ExceptionStage"
    )


def _index_stages(plan: dict) -> dict[str, dict]:
    all_stages = find_stages(plan, include_exception=True)
    stage_by_label: dict[str, dict] = {}
    for label in STAGE_TASK_TYPES:
        matches = [s for s in all_stages if _norm(_label(s)) == _norm(label)]
        if not matches:
            _fail(
                f"missing stage {label!r}; stages present: "
                f"{[_label(s) for s in all_stages]}"
            )
        if len(matches) > 1:
            _fail(f"multiple stages match {label!r}: {[_label(s) for s in matches]}")
        stage_by_label[label] = matches[0]
    if len(all_stages) != len(STAGE_TASK_TYPES):
        _fail(
            f"expected exactly {len(STAGE_TASK_TYPES)} stages, got {len(all_stages)}: "
            f"{[_label(s) for s in all_stages]}"
        )
    return stage_by_label


def _check_secondary_lanes(stage_by_label: dict[str, dict]):
    actual_secondary = {
        label for label, stage in stage_by_label.items() if _is_secondary(stage)
    }
    if actual_secondary != SECONDARY_STAGES:
        _fail(
            f"secondary stages {sorted(actual_secondary)} != expected "
            f"{sorted(SECONDARY_STAGES)}"
        )
    for label in sorted(SECONDARY_STAGES):
        entries = (stage_by_label[label].get("data") or {}).get("entryConditions") or []
        if not entries:
            _fail(f"secondary stage {label!r} has no entry conditions")
        not_interrupting = [
            condition.get("displayName")
            for condition in entries
            if condition.get("isInterrupting") is not True
        ]
        if not_interrupting:
            _fail(
                f"secondary stage {label!r} entry condition(s) {not_interrupting} must be "
                "interrupting (SDD: Interrupting = Yes)"
            )
    for label in sorted(set(STAGE_TASK_TYPES) - SECONDARY_STAGES):
        interrupting = [
            condition.get("displayName")
            for condition in ((stage_by_label[label].get("data") or {}).get("entryConditions") or [])
            if condition.get("isInterrupting") is True
        ]
        if interrupting:
            _fail(
                f"primary stage {label!r} entry condition(s) {interrupting} must NOT be "
                "interrupting"
            )


def _check_transitions(plan: dict, stage_by_label: dict[str, dict]):
    for src_label, dst_label in EXPECTED_TRANSITIONS:
        src_id = stage_by_label[src_label]["id"]
        dst_id = stage_by_label[dst_label]["id"]
        if not find_transitions(plan, source=src_id, target=dst_id):
            _fail(
                f"missing condition-derived transition {src_label!r} -> {dst_label!r} "
                "(entry selected-stage-completed/-exited or exitToStageId)"
            )


def _check_case_exits(plan: dict, stage_by_label: dict[str, dict]):
    case_exits = get_case_exit_conditions(plan)
    if len(case_exits) != 3:
        _fail(
            "expected exactly 3 case-exit rules (executed completing + rejected + "
            f"withdrawn non-completing); got {len(case_exits)}"
        )
    seen = set()
    for case_exit in case_exits:
        rule = first_rule_of_condition(case_exit) or {}
        name = rule.get("rule")
        marks = case_exit.get("marksCaseComplete")
        if name == "required-stages-completed":
            if marks is not True:
                _fail("the required-stages-completed case exit must set marksCaseComplete=true")
            seen.add("executed")
            continue
        if name not in ("selected-stage-completed", "selected-stage-exited"):
            _fail(f"unexpected case-exit rule {name!r}")
        for label in (REJECTED, WITHDRAWN):
            if rule.get("selectedStageId") == stage_by_label[label]["id"]:
                if marks is True:
                    _fail(
                        f"the {label!r} case exit is terminal-but-incomplete; "
                        "marksCaseComplete must be false"
                    )
                seen.add(label)
    missing = {"executed", REJECTED, WITHDRAWN} - seen
    if missing:
        _fail(f"missing case exit(s) for: {sorted(missing)}")


def _check_tasks(stage_by_label: dict[str, dict], plan: dict):
    tasks = list(iter_tasks(plan))
    expected_total = sum(len(types) for types in STAGE_TASK_TYPES.values())
    if len(tasks) != expected_total:
        _fail(f"expected exactly {expected_total} tasks, got {len(tasks)}")
    for label, expected_types in STAGE_TASK_TYPES.items():
        got = sorted(task.get("type") or "?" for task in _stage_tasks(stage_by_label[label]))
        if got != sorted(expected_types):
            _fail(f"stage {label!r} task types {got} != expected {sorted(expected_types)}")

    names = Counter(task.get("displayName") for task in tasks)
    duplicated = sorted(name for name, count in names.items() if count > 1)
    if duplicated:
        _fail(f"duplicate task display names: {duplicated}")

    required = {task.get("displayName") for task in tasks if task.get("isRequired") is True}
    if required != REQUIRED_TASKS:
        _fail(
            "required-task set differs from the SDD\n"
            f"  extra={sorted(required - REQUIRED_TASKS)}\n"
            f"  missing={sorted(REQUIRED_TASKS - required)}"
        )
    run_once = {
        task.get("displayName") for task in tasks if task.get("shouldRunOnlyOnce") is True
    }
    if run_once != RUN_ONCE_TASKS:
        _fail(
            "run-once task set differs from the SDD\n"
            f"  extra={sorted(run_once - RUN_ONCE_TASKS)}\n"
            f"  missing={sorted(RUN_ONCE_TASKS - run_once)}"
        )


def _check_return_to_origin(stage_by_label: dict[str, dict]):
    exits = (stage_by_label[INTERVENTION].get("data") or {}).get("exitConditions") or []
    returns = [c for c in exits if c.get("type") == "return-to-origin"]
    if len(returns) != 1:
        _fail(
            f"{INTERVENTION!r} must have exactly one return-to-origin exit "
            f"(the lane resumes the interrupted stage); got {len(returns)} of "
            f"{[c.get('type') for c in exits]}"
        )
    if returns[0].get("marksStageComplete") is not True:
        _fail(f"{INTERVENTION!r} return-to-origin exit must set marksStageComplete=true")
    for label in sorted(set(STAGE_TASK_TYPES) - {INTERVENTION}):
        stray = [
            c.get("displayName")
            for c in ((stage_by_label[label].get("data") or {}).get("exitConditions") or [])
            if c.get("type") == "return-to-origin"
        ]
        if stray:
            _fail(f"stage {label!r} must not use return-to-origin; found {stray}")


def _check_slas(plan: dict, stage_by_label: dict[str, dict]) -> dict[str, str]:
    """Validate case + stage SLAs and return {sla_id: owning scope label}."""
    expected_recipients = _expected_notify_recipients()
    owners: dict[str, str] = {}
    actual_recipients: set[str] = set()

    def _check_escalations(rules: list, where: str):
        if len(rules) != 1:
            _fail(f"{where}: expected exactly 1 SLA rule, got {len(rules)}")
        escalations = rules[0].get("escalationRule") or []
        types = {(e.get("triggerInfo") or {}).get("type") for e in escalations}
        if "at-risk" not in types or not types & {"breached", "sla-breached"}:
            _fail(f"{where}: SLA needs at-risk + (sla-)breached escalations; got {sorted(types)}")
        if not any(
            (e.get("triggerInfo") or {}).get("atRiskPercentage") == 70 for e in escalations
        ):
            _fail(f"{where}: no escalation with atRiskPercentage=70 (SDD: at-risk at 70%)")
        for escalation in escalations:
            for recipient in ((escalation.get("action") or {}).get("recipients") or []):
                value = recipient.get("value")
                if isinstance(value, str) and value.strip():
                    actual_recipients.add(value.strip())

    case_rules = get_sla_rules(plan)
    if not case_rules:
        _fail("case-level metadata.slaRules missing (10 business-day case SLA)")
    _check_escalations(case_rules, "case SLA")
    case_sla = case_rules[0]
    if (case_sla.get("count"), case_sla.get("unit")) != CASE_SLA_DURATION:
        _fail(
            f"case SLA duration lost: expected {CASE_SLA_DURATION}; got "
            f"({case_sla.get('count')!r}, {case_sla.get('unit')!r})"
        )
    if not case_sla.get("id"):
        _fail("case SLA has no id; the intervention lane cannot reference it")
    owners[case_sla["id"]] = "case"

    for label, stage in stage_by_label.items():
        rules = get_sla_rules(stage)
        if label not in STAGE_SLA_DURATIONS:
            if rules:
                _fail(f"stage {label!r} must not declare an SLA (SDD gives it none)")
            continue
        _check_escalations(rules, f"stage {label!r} SLA")
        rule = rules[0]
        if (rule.get("count"), rule.get("unit")) != STAGE_SLA_DURATIONS[label]:
            _fail(
                f"stage {label!r} SLA duration lost: expected "
                f"{STAGE_SLA_DURATIONS[label]}; got "
                f"({rule.get('count')!r}, {rule.get('unit')!r})"
            )
        if not rule.get("id"):
            _fail(f"stage {label!r} SLA has no id; its breach-handler task cannot reference it")
        owners[rule["id"]] = label

    if actual_recipients != expected_recipients:
        _fail(
            "SLA notify recipients differ from the SDD\n"
            f"  extra={sorted(actual_recipients - expected_recipients)}\n"
            f"  missing={sorted(expected_recipients - actual_recipients)}"
        )
    return owners


def _check_sla_triggers(stage_by_label: dict[str, dict], owners: dict[str, str]):
    seen: dict[str, str] = {}
    for label, stage in stage_by_label.items():
        for task in _stage_tasks(stage):
            for condition in task.get("entryConditions") or []:
                rule = first_rule_of_condition(condition) or {}
                if rule.get("rule") != "sla-status-change":
                    continue
                name = task.get("displayName")
                sla_id = rule.get("slaId")
                if owners.get(sla_id) != label:
                    _fail(
                        f"task {name!r} sla-status-change points at slaId={sla_id!r} "
                        f"(owner={owners.get(sla_id)!r}) but lives on stage {label!r}; a "
                        "breach handler must trigger on its own stage's SLA"
                    )
                seen[name] = label
    if seen != SLA_TRIGGERED_TASKS:
        _fail(
            "sla-status-change task triggers differ from the SDD\n"
            f"  actual={sorted(seen.items())}\n"
            f"  expected={sorted(SLA_TRIGGERED_TASKS.items())}"
        )

    entries = (stage_by_label[INTERVENTION].get("data") or {}).get("entryConditions") or []
    rules = [first_rule_of_condition(c) or {} for c in entries]
    sla_entries = [r for r in rules if r.get("rule") == "sla-status-change"]
    if len(sla_entries) != 1 or owners.get(sla_entries[0].get("slaId")) != "case":
        _fail(
            f"{INTERVENTION!r} must be entered by exactly one sla-status-change on the "
            f"CASE SLA; got {[(r.get('rule'), owners.get(r.get('slaId'))) for r in rules]}"
        )


def main():
    plan = _read_plan()
    assert_tasks_nested(plan)

    stage_by_label = _index_stages(plan)
    _check_secondary_lanes(stage_by_label)

    triggers = find_triggers(plan)
    if len(triggers) != 1:
        _fail(f"expected exactly 1 Manual trigger; got {len(triggers)}")
    service_type = (((triggers[0].get("data") or {}).get("inputs")) or {}).get("serviceType")
    if service_type == "Intsvc.EventTrigger":
        _fail("case trigger must be Manual (SDD T02), not an Intsvc.EventTrigger")

    _check_transitions(plan, stage_by_label)
    _check_case_exits(plan, stage_by_label)
    _check_tasks(stage_by_label, plan)
    _check_return_to_origin(stage_by_label)
    owners = _check_slas(plan, stage_by_label)
    _check_sla_triggers(stage_by_label, owners)

    metadata = plan.get("metadata") or {}
    prefix, identifier_type = _expected_case_identifier()
    if metadata.get("caseIdentifier") != prefix:
        _fail(
            f"metadata.caseIdentifier must be the SDD's constant prefix {prefix!r}; got "
            f"{metadata.get('caseIdentifier')!r}. The SDD's separate 'Case ID reference "
            "for task inputs' row (=metadata.ExternalId) is what task `caseId` inputs "
            "bind — it does not configure the case identifier itself"
        )
    if metadata.get("caseIdentifierType") != identifier_type:
        _fail(
            f"metadata.caseIdentifierType must be {identifier_type!r}; got "
            f"{metadata.get('caseIdentifierType')!r}"
        )
    if metadata.get("caseDirectlyPassTaskOutputs") is not True:
        _fail(
            "metadata.caseDirectlyPassTaskOutputs must be true "
            "(SDD: task-output passing = Direct) - the lowered vars.<id> gates do not "
            "resolve at runtime without it"
        )
    if metadata.get("intsvcActivityConfig") != "v2":
        _fail("metadata.intsvcActivityConfig must be 'v2'")

    print(
        "OK: ContractExecution caseplan preserves 8 stages (3 interrupting secondary "
        "lanes), the corrections loop and rejection fan-in, 3 case exits, 30 tasks "
        "with the SDD's required/run-once sets, the return-to-origin intervention "
        "lane, the case + 7 stage SLAs with escalations and recipients, "
        "sla-status-change scoping, and the CTR constant identifier"
    )


if __name__ == "__main__":
    main()
