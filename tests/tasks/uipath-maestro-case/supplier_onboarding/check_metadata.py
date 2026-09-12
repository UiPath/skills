#!/usr/bin/env python3
"""SupplierOnboarding: does the case shell carry the settings the SDD asks for?

Five assertions. `uip maestro case validate` accepts every failure below, and each one
changes what the case does rather than how it looks.

 1. The case is named as the SDD names it. Every solution path and every deployed
    reference is built from that name.
 2. The case identifier is the constant prefix the source's own reference numbers use.
    A generated identifier instead of `SUP` breaks the match against those numbers.
 3. The case app is enabled. Disabled, the people this case routes to have nowhere to
    open it.
 4. Task outputs pass directly. Turned off, a task's result never reaches the next
    task's input and every downstream expression reads an empty slot.
 5. Three case exit conditions, each on the stage the SDD names, and only the onboarded
    one marks the case complete. A rejected or withdrawn application that marks the
    case complete reports a successful onboarding that never happened.

Read-only. Exit 0 clean, 1 on findings.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import expected as E  # noqa: E402
import caseplan_reader as P  # noqa: E402


def _rule_names(condition: dict) -> list[str]:
    return [
        str(rule.get("rule") or "")
        for row in condition.get("rules") or []
        for rule in row or []
    ]


def _selected_stage_ids(condition: dict) -> list[str]:
    return [
        str(rule.get("selectedStageId") or "")
        for row in condition.get("rules") or []
        for rule in row or []
        if rule.get("selectedStageId")
    ]


def main() -> int:
    plan = P.load()
    meta = P.metadata(plan)
    problems: list[str] = []

    if plan.get("name") != E.CASE_NAME:
        problems.append(
            f"the case is named {plan.get('name')!r}; the SDD names it {E.CASE_NAME!r}"
        )

    if meta.get("caseIdentifier") != E.CASE_IDENTIFIER_PREFIX:
        problems.append(
            f"the case identifier prefix is {meta.get('caseIdentifier')!r}; the SDD "
            f"takes {E.CASE_IDENTIFIER_PREFIX!r} verbatim from the source's own "
            f"reference numbers"
        )
    if meta.get("caseIdentifierType") != "constant":
        problems.append(
            f"the case identifier type is {meta.get('caseIdentifierType')!r}; the SDD "
            f"asks for 'constant', so the prefix is fixed rather than generated"
        )

    if meta.get("caseAppEnabled") is not True:
        problems.append(
            f"caseAppEnabled is {meta.get('caseAppEnabled')!r}; the SDD enables the "
            f"case app, and without it nobody this case routes to can open it"
        )

    if meta.get("caseDirectlyPassTaskOutputs") is not True:
        problems.append(
            f"caseDirectlyPassTaskOutputs is "
            f"{meta.get('caseDirectlyPassTaskOutputs')!r}; the SDD passes task outputs "
            f"directly, and without it a task's result never reaches the next input"
        )

    ids_by_label = P.stage_ids(plan)
    labels_by_id = {sid: label for label, sid in ids_by_label.items()}
    exits = P.case_exits(plan)
    if len(exits) != len(E.CASE_EXITS):
        problems.append(
            f"the case carries {len(exits)} exit condition(s); the SDD writes "
            f"{len(E.CASE_EXITS)}"
        )

    # Match on the pair the SDD keys each row by: the rule and the stage it names.
    # Order is the build's own, so it is not part of the contract.
    seen = {}
    for condition in exits:
        for name in _rule_names(condition):
            stages = [labels_by_id.get(sid, sid) for sid in _selected_stage_ids(condition)]
            seen[(name, stages[0] if stages else None)] = condition

    for rule, stage, completes in E.CASE_EXITS:
        condition = seen.get((rule, stage))
        if condition is None:
            got = sorted(f"{r} on {s}" for r, s in seen)
            problems.append(
                f"no case exit condition runs {rule!r} on stage {stage!r}; the plan "
                f"has {got}"
            )
            continue
        actual = condition.get("marksCaseComplete")
        if bool(actual) is not completes:
            problems.append(
                f"the exit on {rule!r}/{stage!r} sets marksCaseComplete={actual!r}; "
                f"the SDD sets {completes!r}, so this disposition "
                f"{'must' if completes else 'must not'} report the case complete"
            )

    if not problems:
        print(f"checked {P.find_caseplan()}")
        print(
            f"OK: the case is {E.CASE_NAME!r} with the constant prefix "
            f"{E.CASE_IDENTIFIER_PREFIX!r}, the case app on, task outputs passing "
            f"directly, and {len(E.CASE_EXITS)} exit conditions on the stages the SDD "
            f"names, of which only the onboarded one marks the case complete"
        )
        return 0

    print(f"\nFAIL: {len(problems)} case-shell finding(s):", file=sys.stderr)
    for item in problems:
        print(f"  - {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
