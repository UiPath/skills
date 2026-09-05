#!/usr/bin/env python3
"""WarrantyClaimTriage: did the SLA responses declared in sdd.md survive into caseplan.json?

Why this check exists
---------------------
The `sla_response/*` family already covers SLA behaviour, but every one of those tasks
starts from an existing `caseplan.json` under `templates/` and grades a brownfield EDIT.
No task took an SDD that *declares* SLA responses through Phase 1 -> 4 and asserted the
emitted plan. Across all nine SDD fixtures in this suite, `sla-status-change` appears
zero times.

That matters because the two acting responses have different emit shapes and are easy to
confuse — the skill's own references warn about exactly this:

  * `start-task`  -> the follow-up task carries `sla-status-change` on its OWN task entry,
                     inside the breached stage. NO new stage, and NO stage-entry row: a
                     stage-entry rule would re-enter the stage and re-run its other tasks.
  * `enter-stage` -> a separate secondary stage carries the `sla-status-change` entry, and
                     it interrupts when the response takes the work over.

`uip maestro case validate` accepts both shapes, so validate passing is not evidence the
right one was emitted. These assertions are.

Read-only. Exit 0 clean, 1 on findings.
"""
from __future__ import annotations

import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-case")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, _shared_root)
from _shared.case_check import (  # noqa: E402
    find_caseplan,
    find_stages,
    get_case_exit_conditions,
    get_sla_rules,
    iter_stage_entry_conditions,
    iter_stage_exit_conditions,
    read_caseplan,
)

SLA_RULE = "sla-status-change"


def rules_of(cond: dict) -> list[dict]:
    """Flatten a condition's DNF rule matrix into a list of rule objects."""
    out: list[dict] = []
    for clause in cond.get("rules") or []:
        if isinstance(clause, list):
            out.extend(r for r in clause if isinstance(r, dict))
        elif isinstance(clause, dict):
            out.append(clause)
    return out


def rule_names(cond: dict) -> list[str]:
    return [str(r.get("rule", "")) for r in rules_of(cond)]


def label(node: dict) -> str:
    """Display name for a stage OR a task.

    The two differ in the emitted plan and it matters: a STAGE carries `data.label`,
    while a TASK carries `displayName` / `entryConditions` / `isRequired` at the TOP
    level with `data` left `{}` for an unresolved placeholder. Reading task names out
    of `data` returns None and makes every task look absent.
    """
    data = node.get("data") or {}
    return str(
        node.get("displayName")
        or data.get("displayName")
        or data.get("label")
        or node.get("id")
        or "?"
    )


def task_entry_conditions(task: dict) -> list[dict]:
    """Task entry conditions live at the top level; `data` is {} on a placeholder."""
    top = task.get("entryConditions")
    if isinstance(top, list):
        return top
    return ((task.get("data") or {}).get("entryConditions")) or []


def task_is_required(task: dict) -> bool:
    if "isRequired" in task:
        return bool(task.get("isRequired"))
    return bool((task.get("data") or {}).get("isRequired"))


def stage_tasks(stages: list[dict]):
    """Yield (stage, task) pairs. `_shared.iter_tasks` yields the task alone, but the
    start-task assertion is precisely about WHICH stage the task sits in."""
    for stage in stages:
        for lane in ((stage.get("data") or {}).get("tasks")) or []:
            if isinstance(lane, dict):
                yield stage, lane
            elif isinstance(lane, list):
                for task in lane:
                    if isinstance(task, dict):
                        yield stage, task


def main() -> int:
    path = find_caseplan()
    plan = read_caseplan(path)
    problems: list[str] = []

    stages = find_stages(plan, include_exception=True)
    by_name = {label(s): s for s in stages}

    # ---- 1. the case and the three primary stages each carry an SLA -------------
    if not get_sla_rules(plan):
        problems.append("root carries no slaRules — the 5 d case SLA was dropped")
    for name in ("Intake", "Assessment", "Settlement"):
        stage = by_name.get(name)
        if stage is None:
            problems.append(f"stage {name!r} is missing from the plan")
            continue
        if not get_sla_rules(stage):
            problems.append(f"stage {name!r} carries no slaRules — its SLA was dropped")

    # ---- 2. condition-based SLA on Assessment ----------------------------------
    assessment = by_name.get("Assessment")
    if assessment is not None:
        rules = get_sla_rules(assessment)
        # A condition-based SLA is an override row whose `expression` gates it, PLUS a
        # default row carrying the sentinel `=js:true`. Anything else is time-based.
        conditional = [
            r for r in rules
            if str(r.get("expression") or "").strip()
            and str(r.get("expression")).strip() != "=js:true"
        ]
        if not conditional:
            exprs = [r.get("expression") for r in rules]
            problems.append(
                "Assessment has no gated slaRules entry (expressions: "
                f"{exprs}) — the high-value override (4 h when claimValue > 5000) was "
                "flattened away"
            )
        if len(rules) < 2:
            problems.append(
                f"Assessment has {len(rules)} SLA rule(s); a condition-based SLA needs the "
                "override PLUS a default row"
            )

    # ---- 3. start-task: the rule is on the TASK, not on the stage ---------------
    chase = None
    for stage, task in stage_tasks(stages):
        if label(task) == "Chase Missing Paperwork":
            chase = (stage, task)
            break
    if chase is None:
        problems.append("task 'Chase Missing Paperwork' is missing — the start-task response was dropped")
    else:
        stage, task = chase
        if label(stage) != "Intake":
            problems.append(
                f"'Chase Missing Paperwork' sits in stage {label(stage)!r}; a start-task "
                "response lives INSIDE the breached stage (Intake)"
            )
        names = [n for c in task_entry_conditions(task) for n in rule_names(c)]
        if SLA_RULE not in names:
            problems.append(
                f"'Chase Missing Paperwork' task entry is {names or ['(none)']}; the "
                "start-task response must carry sla-status-change on its own task entry"
            )
        if "current-stage-entered" in names:
            problems.append(
                "'Chase Missing Paperwork' also carries current-stage-entered — it would "
                "then run on every case, not only on a breach"
            )

    # ---- 4. start-task must NOT have become a stage-entry rule ------------------
    intake = by_name.get("Intake")
    if intake is not None:
        for cond in iter_stage_entry_conditions(intake):
            if SLA_RULE in rule_names(cond):
                problems.append(
                    "Intake has an sla-status-change STAGE-entry rule; the start-task "
                    "response belongs on the task entry. A stage-entry rule re-enters the "
                    "stage and re-runs Validate Claim Details."
                )

    # ---- 5. enter-stage: the secondary lane carries it, interrupting ------------
    esc = by_name.get("Escalation Review")
    if esc is None:
        problems.append("secondary stage 'Escalation Review' is missing — the enter-stage response was dropped")
    else:
        conds = list(iter_stage_entry_conditions(esc))
        sla_conds = [c for c in conds if SLA_RULE in rule_names(c)]
        if not sla_conds:
            problems.append(
                "'Escalation Review' has no sla-status-change stage-entry rule — the "
                "enter-stage response is unreachable"
            )
        for c in sla_conds:
            if not c.get("isInterrupting"):
                problems.append(
                    "'Escalation Review' sla-status-change entry is not interrupting; the "
                    "lane takes the assessment over, so it must interrupt"
                )
        rto = [
            c for c in iter_stage_exit_conditions(esc)
            if str(c.get("type") or "") == "return-to-origin"
        ]
        if not rto:
            problems.append(
                "'Escalation Review' has no return-to-origin exit — a returning lane must "
                "hand the claim back to the assessor"
            )

    # ---- 6. the terminal lane closes the case without completing it ------------
    rejected = by_name.get("Claim Rejected")
    if rejected is None:
        problems.append("secondary stage 'Claim Rejected' is missing")
    exits = get_case_exit_conditions(plan)
    non_completing = [c for c in exits if c.get("marksCaseComplete") is False]
    completing = [c for c in exits if c.get("marksCaseComplete") is True]
    if not completing:
        problems.append("no case-exit row with marksCaseComplete true — the case can never complete")
    if not non_completing:
        problems.append(
            "no case-exit row with marksCaseComplete false — the rejected lane cannot close "
            "the case as an alternate disposition"
        )

    # ---- 7. the adhoc task stayed adhoc and optional ----------------------------
    for stage, task in stage_tasks(stages):
        if label(task) != "Add Claim Evidence":
            continue
        names = [n for c in task_entry_conditions(task) for n in rule_names(c)]
        if names != ["adhoc"]:
            problems.append(
                f"'Add Claim Evidence' task entry is {names or ['(none)']}; a manually "
                "triggered task carries adhoc as its only entry rule"
            )
        if task_is_required(task):
            problems.append("'Add Claim Evidence' is required; an adhoc task must be optional")
        break
    else:
        problems.append("task 'Add Claim Evidence' is missing — the adhoc surface was dropped")

    print(f"checked {path}")
    print(f"stages: {sorted(by_name)}")
    if not problems:
        print(
            "OK: SLA responses survived the build — case + 3 stage SLAs, a condition-based "
            "override on Assessment, start-task on the task entry inside Intake, "
            "interrupting enter-stage lane with return-to-origin, a non-completing case "
            "exit, and an adhoc optional task"
        )
        return 0

    print(f"\nFAIL: {len(problems)} SLA-response finding(s):", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
