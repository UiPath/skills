#!/usr/bin/env python3
"""ParallelAfterPredecessor: emitted `data.tasks` grouping for siblings after one predecessor.

`uip maestro case validate` accepts every grouping of a task set — a strict chain,
a shared set, a shared set at index 0, and even mixed entry rules inside one set all
return Status: Valid (probed on uip 1.198.0-preview.102). Grouping is therefore
unenforced by the CLI, so these assertions read the emitted structure directly.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    find_stages,
    first_rule_of_condition,
    read_caseplan,
)

STAGE = "Issuing Permit"
PREDECESSOR = "Collect Fees"
SIBLINGS = ("Wait For Payment Confirmation", "Track Payment Deadline")
DOWNSTREAM = "Generate Permit"


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def stage_by_label(plan: dict, label: str) -> dict:
    for stage in find_stages(plan):
        data = stage.get("data") or {}
        if label in (data.get("displayName"), data.get("label")):
            return stage
    seen = [(s.get("data") or {}).get("displayName") for s in find_stages(plan)]
    fail(f"stage {label!r} not found; saw {seen}")


def task_sets(stage: dict) -> list[list[dict]]:
    return [lane or [] for lane in (stage.get("data") or {}).get("tasks") or []]


def set_index(stage: dict, label: str) -> int:
    for idx, lane in enumerate(task_sets(stage)):
        for task in lane:
            if label in ((task or {}).get("displayName"), (task or {}).get("label")):
                return idx
    seen = [
        (t or {}).get("displayName") or (t or {}).get("label")
        for lane in task_sets(stage)
        for t in lane
    ]
    fail(f"task {label!r} not found in stage tasks; saw {seen}")


def entry_rules(stage: dict, label: str) -> list[str]:
    for lane in task_sets(stage):
        for task in lane:
            if label in ((task or {}).get("displayName"), (task or {}).get("label")):
                rules = []
                for cond in task.get("entryConditions") or []:
                    rule = first_rule_of_condition(cond)
                    if rule:
                        rules.append(rule.get("rule"))
                return rules
    fail(f"task {label!r} not found when reading entry conditions")


def main() -> None:
    plan = read_caseplan()
    stage = stage_by_label(plan, STAGE)
    sets = task_sets(stage)

    pred = set_index(stage, PREDECESSOR)
    a, b = (set_index(stage, name) for name in SIBLINGS)
    down = set_index(stage, DOWNSTREAM)

    # 1. The two independent siblings share ONE task set.
    if a != b:
        fail(
            f"{SIBLINGS[0]!r} (set {a}) and {SIBLINGS[1]!r} (set {b}) must share one "
            f"task set — parallel-after-predecessor siblings are grouped, not chained"
        )

    # 2. That set comes AFTER the predecessor — this is not stage-start parallelism.
    if a <= pred:
        fail(
            f"sibling task set {a} must come after the {PREDECESSOR!r} set {pred}; "
            f"siblings starting at stage entry are plain `parallel`, not "
            f"`parallel-after-predecessor`"
        )

    # 3. The predecessor is alone in its set (a strict step, not a sibling).
    if len(sets[pred]) != 1:
        labels = [(t or {}).get("displayName") for t in sets[pred]]
        fail(f"{PREDECESSOR!r} must be alone in its task set; set {pred} holds {labels}")

    # 4. Exactly the two siblings share the set — nothing else drifted in.
    if len(sets[a]) != 2:
        labels = [(t or {}).get("displayName") for t in sets[a]]
        fail(f"sibling set {a} must hold exactly the two siblings; holds {labels}")

    # 5. Downstream work waits for the whole sibling set.
    if down <= a:
        fail(f"{DOWNSTREAM!r} (set {down}) must come after the sibling set {a}")

    # 6. Every task in the run carries runs-sequentially as its only entry rule.
    #    On the first set that means "stage entered"; on later sets, "previous set
    #    completed" — which is what makes both siblings start together.
    for name in (PREDECESSOR, *SIBLINGS, DOWNSTREAM):
        rules = entry_rules(stage, name)
        if rules != ["runs-sequentially"]:
            fail(
                f"{name!r} must carry exactly one `runs-sequentially` entry rule; "
                f"got {rules!r}"
            )

    # 7. The regression this guards: duplicate selected-task gates naming the
    #    predecessor instead of grouping the siblings into one set.
    for name in SIBLINGS:
        for lane in task_sets(stage):
            for task in lane:
                if name not in ((task or {}).get("displayName"), (task or {}).get("label")):
                    continue
                blob = str(task.get("entryConditions") or "")
                if "selected-tasks-completed" in blob:
                    fail(
                        f"{name!r} uses a selected-tasks-completed gate; "
                        f"parallel-after-predecessor siblings use task-set grouping "
                        f"plus runs-sequentially, not duplicate sibling gates"
                    )

    print(
        f"OK: {STAGE!r} emits [[{PREDECESSOR}], "
        f"[{SIBLINGS[0]}, {SIBLINGS[1]}], [{DOWNSTREAM}]] "
        f"with runs-sequentially throughout"
    )


if __name__ == "__main__":
    main()
