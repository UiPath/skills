#!/usr/bin/env python3
"""CM-Golden rebuild: structural topology and runtime-contract grader.

Checks that the generated caseplan.json encodes the golden feature-coverage
design, not just a structurally valid case:

  - 8 stages: 7 primary + the "Stage 4 - return to origin" secondary lane
  - condition-derived transition chain S1->S2->S3->S6 plus S2->S4 (reject
    lane) and S7->S8
  - exactly 1 Manual trigger (not an event trigger)
  - 2 case-exit rules: required-stages-completed (marksCaseComplete) +
    Stage 4 lane exit (does not mark complete)
  - 15 tasks, per-stage task-type multisets covering all 9 task types
  - the named Stage 2 timer is explicitly marked run-once
  - direct task-output passing and connector activity v2 are enabled
  - SLA escalation, timer durations, and the EXP case-identifier prefix survive
"""

from __future__ import annotations

import json
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

EXPECTED_CASEPLAN = os.path.join("CMGoldenExpense", "CMGoldenExpense", "caseplan.json")

# Stage key -> expected task-type multiset (sorted). Keys are matched as
# normalized prefixes of the stage label ("Stage 4" matches
# "Stage 4 - return to origin").
STAGE_TASK_TYPES = {
    "Stage 1": ["agent", "process", "rpa"],
    "Stage 2": ["action", "api-workflow", "wait-for-timer", "wait-for-timer"],
    "Stage 3": ["case-management", "execute-connector-activity", "wait-for-connector"],
    "Stage 4": ["action"],
    "Stage 5": ["wait-for-timer"],
    "Stage 6": ["wait-for-timer"],
    "Stage 7": ["wait-for-timer"],
    "Stage 8": ["wait-for-timer"],
}
SECONDARY_STAGE = "Stage 4"
EXPECTED_TRANSITIONS = [
    ("Stage 1", "Stage 2"),
    ("Stage 2", "Stage 3"),
    ("Stage 2", "Stage 4"),  # reject lane: selected-stage-exited("Stage 2")
    ("Stage 3", "Stage 6"),
    ("Stage 7", "Stage 8"),
]
TIMER_DURATIONS = ["pt20s", "pt10s", "pt20m", "pt5s"]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _label(node: dict) -> str:
    return (node.get("data") or {}).get("label") or ""


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _read_plan() -> dict:
    if os.path.exists(EXPECTED_CASEPLAN):
        return read_caseplan(EXPECTED_CASEPLAN)
    return read_caseplan()


def _stage_tasks(stage: dict) -> list[dict]:
    tasks: list[dict] = []
    for lane in ((stage.get("data") or {}).get("tasks") or []):
        if isinstance(lane, dict):
            tasks.append(lane)
        elif isinstance(lane, list):
            tasks.extend(t for t in lane if isinstance(t, dict))
    return tasks


def _is_secondary(node: dict) -> bool:
    return (
        (node.get("data") or {}).get("stageType") == "secondary"
        or node.get("type") == "case-management:ExceptionStage"
    )


def main():
    plan = _read_plan()
    assert_tasks_nested(plan)

    # -- stages -------------------------------------------------------------
    all_stages = find_stages(plan, include_exception=True)
    stage_by_key: dict[str, dict] = {}
    for key in STAGE_TASK_TYPES:
        knorm = _norm(key)
        matches = [s for s in all_stages if _norm(_label(s)).startswith(knorm)]
        if not matches:
            _fail(
                f"missing stage {key!r}; stages present: "
                f"{[_label(s) for s in all_stages]}"
            )
        if len(matches) > 1:
            _fail(f"multiple stages match {key!r}: {[_label(s) for s in matches]}")
        stage_by_key[key] = matches[0]
    if len(all_stages) != len(STAGE_TASK_TYPES):
        _fail(
            f"expected exactly {len(STAGE_TASK_TYPES)} stages, got "
            f"{len(all_stages)}: {[_label(s) for s in all_stages]}"
        )

    # -- secondary lane -----------------------------------------------------
    secondaries = [s for s in all_stages if _is_secondary(s)]
    if len(secondaries) != 1 or secondaries[0] is not stage_by_key[SECONDARY_STAGE]:
        _fail(
            "exactly one secondary stage expected and it must be "
            f"{SECONDARY_STAGE!r}; secondaries found: "
            f"{[_label(s) for s in secondaries]}"
        )

    # -- trigger ------------------------------------------------------------
    triggers = find_triggers(plan)
    if len(triggers) != 1:
        _fail(f"expected exactly 1 Manual trigger; got {len(triggers)}")
    svc = (((triggers[0].get("data") or {}).get("uipath")) or {}).get("serviceType")
    if svc == "Intsvc.EventTrigger":
        _fail("case trigger must be Manual, not an Intsvc.EventTrigger")

    # -- transitions ----------------------------------------------------------
    for src_key, dst_key in EXPECTED_TRANSITIONS:
        src_id = stage_by_key[src_key]["id"]
        dst_id = stage_by_key[dst_key]["id"]
        if not find_transitions(plan, source=src_id, target=dst_id):
            _fail(
                f"missing condition-derived transition {src_key!r} -> {dst_key!r} "
                "(entry selected-stage-completed/-exited or exitToStageId)"
            )

    # -- case exits -----------------------------------------------------------
    case_exits = get_case_exit_conditions(plan)
    if len(case_exits) < 2:
        _fail(f"expected >=2 case-exit rules (happy + Stage 4 lane); got {len(case_exits)}")
    happy = False
    lane_exit = False
    stage4_id = stage_by_key[SECONDARY_STAGE]["id"]
    for case_exit in case_exits:
        rule = first_rule_of_condition(case_exit) or {}
        name = rule.get("rule")
        if name == "required-stages-completed" and case_exit.get("marksCaseComplete") is True:
            happy = True
        if (
            name in ("selected-stage-completed", "selected-stage-exited")
            and rule.get("selectedStageId") == stage4_id
            and case_exit.get("marksCaseComplete") is not True
        ):
            lane_exit = True
    if not happy:
        _fail("missing case-exit 'required-stages-completed' with marksCaseComplete=true")
    if not lane_exit:
        _fail(
            "missing case-exit on the 'Stage 4 - return to origin' lane "
            "(selected-stage-completed, marksCaseComplete=false)"
        )

    # -- tasks: count + per-stage type multisets -------------------------------
    tasks = list(iter_tasks(plan))
    expected_total = sum(len(v) for v in STAGE_TASK_TYPES.values())
    if len(tasks) != expected_total:
        _fail(f"expected exactly {expected_total} tasks, got {len(tasks)}")
    for key, expected_types in STAGE_TASK_TYPES.items():
        got = sorted(t.get("type") or "?" for t in _stage_tasks(stage_by_key[key]))
        if got != sorted(expected_types):
            _fail(f"stage {key!r} task types {got} != expected {sorted(expected_types)}")

    # -- run-once task contract --------------------------------------------------
    stage2_tasks = _stage_tasks(stage_by_key["Stage 2"])
    run_once = next(
        (
            task
            for task in stage2_tasks
            if task.get("displayName") == "Wait for timer - S2 run once"
        ),
        None,
    )
    if run_once is None or run_once.get("shouldRunOnlyOnce") is not True:
        _fail("'Wait for timer - S2 run once' must set shouldRunOnlyOnce=true")

    # -- SLA escalation ---------------------------------------------------------
    sla_rules = get_sla_rules(plan)
    if not sla_rules:
        _fail("case-level metadata.slaRules missing (1h SLA with escalations)")
    if "song.zhao@uipath.com" not in json.dumps(sla_rules, default=str).lower():
        _fail("SLA escalation notify recipient lost")
    sla0 = sla_rules[0] if isinstance(sla_rules, list) else sla_rules
    if not (sla0.get("count") == 1 and sla0.get("unit") == "h"):
        _fail(
            "SLA duration lost: expected count=1 unit='h' (1h case SLA); got "
            f"count={sla0.get('count')!r} unit={sla0.get('unit')!r}"
        )
    escalations = sla0.get("escalationRule") or []
    esc_types = {((e.get("triggerInfo") or {}).get("type")) for e in escalations}
    if "at-risk" not in esc_types or not esc_types & {"breached", "sla-breached"}:
        _fail(f"SLA escalations lost: need at-risk + (sla-)breached; got {sorted(esc_types)}")
    if not any(
        (e.get("triggerInfo") or {}).get("atRiskPercentage") == 70 for e in escalations
    ):
        _fail("SLA at-risk threshold lost: no escalation with atRiskPercentage=70")

    # -- runtime contracts (functional-build facts, run4-oracle-verified) --------
    # Direct task-output passing is what makes the lowered vars.<id> gates
    # resolve at runtime; intsvcActivityConfig v2 is the connector-task contract.
    if (plan.get("metadata") or {}).get("caseDirectlyPassTaskOutputs") is not True:
        _fail("metadata.caseDirectlyPassTaskOutputs must be true (SDD: task-output passing = Direct)")
    if (plan.get("metadata") or {}).get("intsvcActivityConfig") != "v2":
        _fail("metadata.intsvcActivityConfig must be 'v2'")

    # -- content fidelity not covered by the semantic checker -------------------
    raw = json.dumps(plan, default=str).lower()
    missing_durations = [d for d in TIMER_DURATIONS if d not in raw]
    if missing_durations:
        _fail(f"timer durations lost: {missing_durations}")
    case_identifier = (plan.get("metadata") or {}).get("caseIdentifier")
    if case_identifier != "EXP":
        _fail(f"metadata.caseIdentifier must be 'EXP'; got {case_identifier!r}")

    print(
        "OK: CM-Golden caseplan preserves 8 stages (1 secondary), "
        f"{len(tasks)} tasks across all 9 types, "
        "transition/case-exit topology, run-once contract, runtime flags, "
        "SLA escalation, timer durations, and case identifier"
    )


if __name__ == "__main__":
    main()
