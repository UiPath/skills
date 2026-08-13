#!/usr/bin/env python3
"""Scale-and-shape guard for the context_scale fixture.

This fixture exists to measure *cost* (tokens, wall clock, peak context) across
skill variants. Cost is only comparable if every variant built a case of the
same magnitude — otherwise a variant "wins" by building less. This checker is
the Goodhart guard: it asserts the case is genuinely large and carries the
shapes the requirements call for, without pinning exact names (a variant may
name stages differently and still be correct).

Floors are set from the 2026-08-11 measured baseline, which produced:
    stages=9  tasks=33  conditions=66  stage_slas=5
    secondary=4  return_to_origin=2  case_exits=3
Each floor sits below the baseline with headroom, so a faithful build passes
and a truncated one does not.

Schema notes (verified against a real caseplan, schema v27):
  - stage.data.tasks is a list of task *sets*; each set is a list of tasks.
  - stage SLA lives at stage.data.slaRules (absent on secondary stages).
  - a secondary stage carries stage.data.stageType; primaries do not.
  - case-level exits live at metadata.caseExitRules, not at the root.

Exit 0 = pass. Exit 1 = fail, with every unmet expectation listed.
"""
import json
import os
import sys

CANDIDATES = [
    "AutoClaimSettlement/AutoClaimSettlementCase/caseplan.json",
    "AutoClaimSettlement/AutoClaimSettlement/caseplan.json",
]

MIN_STAGES = 7
MIN_TASKS = 24
MIN_CONDITIONS = 45
MIN_STAGE_SLAS = 3
MIN_CASE_EXITS = 3
STAGE_TYPE = "case-management:Stage"


def find_caseplan():
    for rel in CANDIDATES:
        if os.path.isfile(rel):
            return rel
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", ".venv", "__pycache__")]
        if "caseplan.json" in files:
            return os.path.join(root, "caseplan.json")
    return None


def flatten_task_sets(raw):
    """stage.data.tasks is a list of task sets; tolerate a flat list too."""
    out = []
    for entry in raw or []:
        if isinstance(entry, list):
            out.extend(x for x in entry if isinstance(x, dict))
        elif isinstance(entry, dict):
            out.append(entry)
    return out


def main():
    path = find_caseplan()
    if not path:
        print("FAIL: no caseplan.json found under the working directory")
        return 1

    with open(path) as fh:
        plan = json.load(fh)

    metadata = plan.get("metadata") or {}
    stages = [n for n in (plan.get("nodes") or []) if n.get("type") == STAGE_TYPE]

    tasks = []
    stage_slas = secondary = return_to_origin = conditions = 0

    for st in stages:
        data = st.get("data") or {}
        stage_tasks = flatten_task_sets(data.get("tasks"))
        tasks.extend(stage_tasks)

        if data.get("slaRules"):
            stage_slas += 1
        if data.get("stageType"):
            secondary += 1

        entry = data.get("entryConditions") or []
        exit_ = data.get("exitConditions") or []
        conditions += len(entry) + len(exit_)
        for t in stage_tasks:
            conditions += len(t.get("entryConditions") or [])

        for cond in exit_:
            blob = json.dumps(cond)
            if "return-to-origin" in blob or "returnToOrigin" in blob:
                return_to_origin += 1

    case_exits = len(metadata.get("caseExitRules") or [])
    case_sla = bool(metadata.get("slaRules"))

    failures = []
    if len(stages) < MIN_STAGES:
        failures.append(f"stages: {len(stages)} < {MIN_STAGES}")
    if len(tasks) < MIN_TASKS:
        failures.append(f"tasks: {len(tasks)} < {MIN_TASKS}")
    if conditions < MIN_CONDITIONS:
        failures.append(f"conditions: {conditions} < {MIN_CONDITIONS}")
    if stage_slas < MIN_STAGE_SLAS:
        failures.append(f"stages carrying an SLA: {stage_slas} < {MIN_STAGE_SLAS}")
    if not case_sla:
        failures.append("no case-level SLA (metadata.slaRules) — requirements set a 10-day target")
    if secondary < 1:
        failures.append("no secondary stage — requirements describe turn-down, withdrawal, "
                        "and escalation lanes")
    if return_to_origin < 1:
        failures.append("no return-to-origin stage exit — escalation must resume the "
                        "interrupted stage")
    if case_exits < MIN_CASE_EXITS:
        failures.append(f"case exit routes: {case_exits} < {MIN_CASE_EXITS} "
                        "(paid / turned down / withdrawn)")

    print(f"caseplan: {path}")
    print(f"  stages={len(stages)} tasks={len(tasks)} conditions={conditions} "
          f"stage_slas={stage_slas} case_sla={case_sla} secondary={secondary} "
          f"return_to_origin={return_to_origin} case_exits={case_exits}")

    if failures:
        print("FAIL — build is smaller or simpler than the requirements demand:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("PASS — case is at comparable scale to the measured baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
