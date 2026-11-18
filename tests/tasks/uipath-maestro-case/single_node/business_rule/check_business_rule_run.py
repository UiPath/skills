#!/usr/bin/env python3
"""BusinessRuleSingleCase: run the case once under debug and check what the
rule decided.

The staged CreditRisk rule (decision RiskDecision) returns LOW_RISK for a
creditScore of 700 or more and HIGH_RISK below it. The request starts the case
with 742 when no score is given, which is what a debug run does, so the right
result is LOW_RISK. The grader reads it from the debug instance by the names the
request gives (`creditScore`, `riskBand`), and checks that the business-rule
task completed with 742 as its input. Any binding, task name or variable layout
that gets there passes; a rule that was edited, unbound or fed the wrong score
does not.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from case_run_evidence import (  # noqa: E402
    RunEvidence,
    assert_completed,
    fail,
    read_run,
    since_iso,
    text_of,
)
from _shared.case_check import iter_tasks, read_caseplan, run_debug  # noqa: E402

SCORE = 742
EXPECTED_BAND = "LOW_RISK"
OTHER_BAND = "HIGH_RISK"


def _leaf_values(value, key: str):
    """Every value stored under ``key`` (any case) anywhere in ``value``."""
    if isinstance(value, dict):
        for k, v in value.items():
            if str(k).lower() == key.lower():
                yield v
            yield from _leaf_values(v, key)
    elif isinstance(value, list):
        for item in value:
            yield from _leaf_values(item, key)


def check_run(plan: dict, payload: dict, evidence: RunEvidence) -> list[str]:
    rule_tasks = [t for t in iter_tasks(plan) if t.get("type") == "business-rule"]
    if not rule_tasks:
        types = sorted({str(t.get("type")) for t in iter_tasks(plan)})
        fail(f"the case has no business-rule task to run CreditRisk; task types: {types}")
    for task in rule_tasks:
        assert_completed(payload, task)
        inputs, _ = evidence.task_io(str(task.get("id")))
        scores = list(_leaf_values(inputs, "creditScore"))
        if SCORE not in scores:
            fail(
                f"task {task.get('displayName')!r} ran the rule with creditScore {scores or 'unset'}, "
                f"expected {SCORE}; its inputs: {text_of(inputs)[:400]}"
            )

    score = evidence.value("creditScore")
    if score != SCORE:
        fail(f"creditScore is {score!r} in the run, expected the default {SCORE}")
    band = evidence.value("riskBand")
    band_text = text_of(band)
    if EXPECTED_BAND.lower() not in band_text or OTHER_BAND.lower() in band_text:
        fail(f"riskBand is {band!r} after the run, expected {EXPECTED_BAND!r} for a score of {SCORE}")
    return [str(t.get("displayName")) for t in rule_tasks]


def main() -> None:
    plan = read_caseplan()
    since = since_iso()
    payload = run_debug(timeout=540)
    evidence = read_run(payload, since)
    names = check_run(plan, payload, evidence)
    print(
        f"OK: debug Completed; business-rule task(s) {names} completed with creditScore "
        f"{SCORE}; riskBand={EXPECTED_BAND}"
    )


if __name__ == "__main__":
    main()
