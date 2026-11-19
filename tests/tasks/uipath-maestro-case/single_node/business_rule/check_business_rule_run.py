#!/usr/bin/env python3
"""BusinessRuleSingleCase: run the case once under debug and check what the
rule decided.

The staged CreditRisk rule (decision RiskDecision) returns LOW_RISK for a
creditScore of 700 or more and HIGH_RISK below it. The request starts the case
with 742 when no score is given, which is what a debug run does, so the right
result is LOW_RISK. From the debug instance the grader checks that a
business-rule task bound to CreditRisk completed with 742 as its input, and
that the case variable the request names, riskBand, holds LOW_RISK. When the
run shows the task's own riskBand output it must be LOW_RISK; when it shows
none, the plan must set riskBand from the rule's result (not a literal or a
default), with no other row writing riskBand. Any binding layout, task name or input wiring that gets there
passes; a rule that was edited, unbound, swapped or fed the wrong score does
not, nor does a riskBand that holds LOW_RISK without the rule producing it.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_run_evidence import (  # noqa: E402
    RunEvidence,
    assert_completed,
    fail,
    leaf_values,
    read_run,
    since_iso,
    text_of,
)
from _shared.case_check import (  # noqa: E402
    get_bindings,
    get_variables,
    iter_tasks,
    read_caseplan,
    run_debug,
)

RULE = "CreditRisk"
SCORE = 742
EXPECTED_BAND = "LOW_RISK"
BAND_LITERAL = re.compile(r"low_risk|high_risk", re.IGNORECASE)
RULE_OUTPUT_READ = re.compile(
    r"(?:result|output|riskdecision|riskband)(?:\.\w+|\[\d+\])*", re.IGNORECASE
)
JS_PREFIX = "=js:"


def _rule_names(plan: dict, task: dict) -> set[str]:
    """The rule a business-rule task names, literally or through its binding."""
    name = str((task.get("data") or {}).get("name") or "")
    if not name.startswith("=bindings."):
        return {name}
    binding_id = name[len("=bindings."):]
    return {
        str(binding.get("resourceKey") or "").rsplit(".", 1)[-1]
        for binding in get_bindings(plan)
        if binding.get("id") == binding_id
    }


def _bare(expression: str) -> str:
    """``expression`` without quotes, the ``=js:`` or ``=`` prefix and whitespace."""
    text = re.sub(r"\s+", "", expression.replace('"', "").replace("'", ""))
    return text.removeprefix(JS_PREFIX).removeprefix("=")


def _risk_band_writers(node: object, ids: set[str]) -> list[dict]:
    """Every row under ``node`` whose ``var`` or ``target`` is one of the riskBand variable ids."""
    if isinstance(node, list):
        return [w for item in node for w in _risk_band_writers(item, ids)]
    if not isinstance(node, dict):
        return []
    own = [node] if node.get("var") in ids or _bare(str(node.get("target") or "")) in ids else []
    return own + [w for value in node.values() for w in _risk_band_writers(value, ids)]


def _binds_risk_band(plan: dict, task: dict) -> bool:
    """The only row in the plan that writes the riskBand case variable is an output row
    of ``task`` that sets it from the rule's result."""
    variables = get_variables(plan)
    declared = [
        v
        for group in ("inputOutputs", "outputs", "inputs")
        for v in variables.get(group) or []
        if str(v.get("name") or "").lower() == "riskband"
    ]
    if any(BAND_LITERAL.search(_bare(str(v.get("default") or ""))) for v in declared):
        return False
    ids = {str(v.get("id")) for v in declared}
    writers = _risk_band_writers(plan.get("nodes"), ids)
    for row in (task.get("data") or {}).get("outputs") or []:
        source = str(row.get("source") or "")
        if row.get("var") not in ids or not source.startswith("="):
            continue
        if '"' in source or "'" in source or BAND_LITERAL.search(source):
            continue
        if RULE_OUTPUT_READ.fullmatch(_bare(source)):
            return len(writers) == 1 and writers[0] is row
    return False


def _bands(value) -> list:
    """The band ``value`` holds: itself when it is not an object, else every riskBand in it."""
    if isinstance(value, (dict, list)):
        return list(leaf_values(value, "riskBand"))
    return [value]


def check_run(plan: dict, payload: dict, evidence: RunEvidence) -> list[str]:
    rule_tasks = [t for t in iter_tasks(plan) if t.get("type") == "business-rule"]
    if not rule_tasks:
        types = sorted({str(t.get("type")) for t in iter_tasks(plan)})
        fail(f"the case has no business-rule task to run CreditRisk; task types: {types}")
    credit_tasks = [
        t for t in rule_tasks if RULE.lower() in {n.lower() for n in _rule_names(plan, t)}
    ]
    if not credit_tasks:
        bound = {str(t.get("displayName")): sorted(_rule_names(plan, t)) for t in rule_tasks}
        fail(f"no business-rule task is bound to {RULE}; the rule tasks name {bound}")
    for task in credit_tasks:
        assert_completed(payload, task)
        inputs, outputs = evidence.task_io(str(task.get("id")))
        scores = list(leaf_values(inputs, "creditScore"))
        if SCORE not in scores:
            fail(
                f"task {task.get('displayName')!r} ran the rule with creditScore {scores or 'unset'}, "
                f"expected {SCORE}; its inputs: {text_of(inputs)[:400]}"
            )
        returned = list(leaf_values(outputs, "riskBand"))
        if returned and any(b != EXPECTED_BAND for b in returned):
            fail(
                f"task {task.get('displayName')!r} returned riskBand {returned} in its "
                f"Outputs, expected {EXPECTED_BAND!r}; its outputs: {text_of(outputs)[:400]}"
            )
        if not returned and not _binds_risk_band(plan, task):
            rows = [
                (o.get("var"), o.get("source"))
                for o in (task.get("data") or {}).get("outputs") or []
            ]
            fail(
                f"the run shows no riskBand from task {task.get('displayName')!r}, and the plan "
                f"does not set the riskBand case variable from its result; its output rows: {rows}"
            )

    band = evidence.value("riskBand")
    bands = _bands(band)
    if not bands or any(b != EXPECTED_BAND for b in bands):
        fail(f"riskBand is {band!r} after the run, expected {EXPECTED_BAND!r} for a score of {SCORE}")
    return [str(t.get("displayName")) for t in credit_tasks]


def main() -> None:
    plan = read_caseplan()
    since = since_iso()
    payload = run_debug(timeout=540)
    evidence = read_run(payload, since)
    names = check_run(plan, payload, evidence)
    print(
        f"OK: debug Completed; {RULE} task(s) {names} completed with creditScore "
        f"{SCORE}; riskBand={EXPECTED_BAND}"
    )


if __name__ == "__main__":
    main()
