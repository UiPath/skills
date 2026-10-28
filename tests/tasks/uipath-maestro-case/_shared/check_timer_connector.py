#!/usr/bin/env python3
"""ScheduledComplianceSweep: did the SDD's timer trigger, connector waits, ordered
chains, and run-once hold survive into caseplan.json?

Why this check exists
---------------------
Across the greenfield SDD fixtures in this suite, the trigger declared in the SDD's
`### Case Triggers` table is `Manual` 8 times and an event trigger twice. A TIMER
trigger is declared zero times, so no task ever exercised projecting one from an SDD
into `caseplan.json`. Timer triggers ARE covered elsewhere (`multi_trigger`,
`in_arg_trigger_bind`), but only in prompt-driven builds — never through the SDD.

`wait-for-connector` had the same problem for a different reason: exactly one
greenfield SDD (`golden_rebuild`) declared it, and that task costs ~$50 and ~40
minutes, so the single SDD-driven cover of the connector shapes was also the slowest
in the suite.

The assertions below are all on shapes verified against the plugin references and a
real emitted plan, not inferred:

  * a timer trigger is `uipath.case.trigger` with `data.inputs.serviceType == "timer"`
    and the SDD's `timeCycle` verbatim (triggers/timer/impl-json.md, and the same
    assertion in multi_trigger's checker).
  * task ENVELOPE fields are top-level siblings of `data` — `shouldRunOnlyOnce`,
    `isRequired`, `entryConditions`. case-schema.md warns an envelope field misplaced
    inside `data` passes `validate` silently and is dead config.
  * the emitted run-once field is `shouldRunOnlyOnce`; `runOnlyOnce` is the sdd.md
    spelling and never appears in caseplan.json.

Read-only. Exit 0 clean, 1 on findings.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    find_caseplan,
    find_stages,
    find_triggers,
    get_case_exit_conditions,
    read_caseplan,
)

TIME_CYCLE = "R10/2026-09-01T06:00:00Z/P1D"

# Task name -> declared SDD type. Seven of the nine closed enum values.
EXPECTED_TYPES = {
    "Extract Account Records": "rpa",
    "Score Account Records": "process",
    "Wait For Regulator Feed": "wait-for-connector",
    "Fetch Regulator Notices": "execute-connector-activity",
    "Hold For Corrections": "wait-for-timer",
    "Record Sweep Outcome": "api-workflow",
    "Attach Late Evidence": "action",
}


def rules_of(cond: dict) -> list[dict]:
    out: list[dict] = []
    for clause in cond.get("rules") or []:
        if isinstance(clause, list):
            out.extend(r for r in clause if isinstance(r, dict))
        elif isinstance(clause, dict):
            out.append(clause)
    return out


def rule_names(cond: dict) -> list[str]:
    return [str(r.get("rule", "")) for r in rules_of(cond)]


def stage_label(stage: dict) -> str:
    return str((stage.get("data") or {}).get("label") or stage.get("id") or "?")


def task_name(task: dict) -> str:
    """Tasks carry displayName at the TOP level; `data` is {} on a placeholder."""
    return str(task.get("displayName") or (task.get("data") or {}).get("label") or task.get("id") or "?")


def task_entries(task: dict) -> list[dict]:
    top = task.get("entryConditions")
    return top if isinstance(top, list) else ((task.get("data") or {}).get("entryConditions") or [])


def iter_stage_tasks(stages):
    for stage in stages:
        for lane in ((stage.get("data") or {}).get("tasks")) or []:
            if isinstance(lane, dict):
                yield stage, lane
            elif isinstance(lane, list):
                for t in lane:
                    if isinstance(t, dict):
                        yield stage, t


def main() -> int:
    path = find_caseplan()
    plan = read_caseplan(path)
    problems: list[str] = []

    stages = find_stages(plan, include_exception=True)
    by_stage = {stage_label(s): s for s in stages}
    tasks = {task_name(t): (s, t) for s, t in iter_stage_tasks(stages)}

    # ---- 1. the timer trigger ---------------------------------------------------
    triggers = find_triggers(plan)
    timers = [
        t for t in triggers
        if ((t.get("data") or {}).get("inputs") or {}).get("serviceType") == "timer"
    ]
    if not timers:
        seen = [((t.get("data") or {}).get("inputs") or {}).get("serviceType") for t in triggers]
        problems.append(
            f"no timer trigger emitted (serviceType 'timer'); trigger serviceTypes are {seen} "
            "— the SDD declares a Timer trigger, not a manual one"
        )
    else:
        cycles = [((t.get("data") or {}).get("inputs") or {}).get("timeCycle") for t in timers]
        if TIME_CYCLE not in cycles:
            problems.append(
                f"timer trigger timeCycle is {cycles}; the SDD declares {TIME_CYCLE!r} and it is "
                "consumed verbatim — no parsing, no decomposition"
            )

    # ---- 2. the three stages ----------------------------------------------------
    for name in ("Collect Records", "External Signals", "Disposition"):
        if name not in by_stage:
            problems.append(f"stage {name!r} is missing; stages are {sorted(by_stage)}")

    # ---- 3. every declared task type survived -----------------------------------
    for name, want in EXPECTED_TYPES.items():
        if name not in tasks:
            problems.append(f"task {name!r} ({want}) is missing from the plan")
            continue
        got = str(tasks[name][1].get("type") or "")
        # Emitted type may be bare or namespaced; compare on the trailing segment.
        if got.split(":")[-1] != want:
            problems.append(f"task {name!r} has type {got!r}; the SDD declares {want!r}")

    # ---- 4. ordered chains carry runs-sequentially, not stage-entered -----------
    for name in ("Extract Account Records", "Score Account Records",
                 "Wait For Regulator Feed", "Fetch Regulator Notices",
                 "Hold For Corrections", "Record Sweep Outcome"):
        if name not in tasks:
            continue
        names = [n for c in task_entries(tasks[name][1]) for n in rule_names(c)]
        if "runs-sequentially" not in names:
            problems.append(
                f"task {name!r} entry is {names or ['(none)']}; it sits in an ordered chain and "
                "must carry runs-sequentially"
            )
        if "current-stage-entered" in names:
            problems.append(
                f"task {name!r} carries current-stage-entered alongside its sequential rule — "
                "the two together break the ordering"
            )

    # ---- 5. the run-once hold ---------------------------------------------------
    if "Hold For Corrections" in tasks:
        hold = tasks["Hold For Corrections"][1]
        if hold.get("shouldRunOnlyOnce") is not True:
            nested = (hold.get("data") or {}).get("shouldRunOnlyOnce")
            extra = (
                " (it is set inside `data`, where the platform never reads it)"
                if nested is not None else ""
            )
            problems.append(
                f"'Hold For Corrections' shouldRunOnlyOnce is {hold.get('shouldRunOnlyOnce')!r}; "
                f"the SDD sets Run Only Once: Yes{extra}"
            )

    # ---- 6. the adhoc task stayed adhoc and optional ----------------------------
    if "Attach Late Evidence" in tasks:
        adhoc = tasks["Attach Late Evidence"][1]
        names = [n for c in task_entries(adhoc) for n in rule_names(c)]
        if names != ["adhoc"]:
            problems.append(
                f"'Attach Late Evidence' entry is {names or ['(none)']}; a manually triggered task "
                "carries adhoc as its only entry rule"
            )
        if adhoc.get("isRequired") is True:
            problems.append("'Attach Late Evidence' is required; an adhoc task must be optional")

    # ---- 7. the case can complete ----------------------------------------------
    exits = get_case_exit_conditions(plan)
    if not [c for c in exits if c.get("marksCaseComplete") is True]:
        problems.append("no case-exit rule with marksCaseComplete true — the case can never complete")

    print(f"checked {path}")
    print(f"stages: {sorted(by_stage)}")
    print(f"tasks:  {sorted(tasks)}")
    if not problems:
        print(
            "OK: timer trigger with the SDD's verbatim timeCycle, all 7 declared task types "
            "(rpa, process, wait-for-connector, execute-connector-activity, wait-for-timer, "
            "api-workflow, action), ordered chains on runs-sequentially, a run-once hold, an "
            "adhoc optional task, and a completable case"
        )
        return 0

    print(f"\nFAIL: {len(problems)} finding(s):", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
