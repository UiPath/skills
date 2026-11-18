"""check_business_rule_run.py against a real debug run's instance evidence.

testdata/ holds what alpha returned on 2026-11-18 for the BusinessRuleSingleCase
artifact of nightly 2026-11-18_04-23-44, plus that run's plan. The org it ran in
faulted the rule task for a reason of its own (the rule engine refused a debug
job there), so `_completed()` rewrites the statuses and riskBand to what the
eval tenant's completed run produces. The input shape (`JobArguments.CreditScore`)
and every other key are as recorded. No tenant is touched.

    cd tests && uv run -q --with pytest python -m pytest -q tasks/uipath-maestro-case/single_node/business_rule
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
EVIDENCE = json.loads((HERE / "testdata" / "business_rule_run_evidence.json").read_text())
PLAN = json.loads((HERE / "testdata" / "plan.json").read_text())
RULE_TASK = "tZybvNTGY"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


grader = _load("check_business_rule_run_under_test", HERE / "check_business_rule_run.py")


def _completed(band: object = "LOW_RISK"):
    debug = copy.deepcopy(EVIDENCE["debug"]["Data"])
    debug["finalStatus"] = "Completed"
    for execution in debug["elementExecutions"]:
        execution["status"] = "Completed"
    variables_all = copy.deepcopy(EVIDENCE["variables_all"])
    root = next(b for b in variables_all["Data"]["Variables"] if b["ParentElementId"] is None)
    root["Globals"]["RiskBand"] = band
    return debug, variables_all


def _globals(variables_all: dict) -> dict:
    return next(b for b in variables_all["Data"]["Variables"] if b["ParentElementId"] is None)["Globals"]


def test_a_completed_run_with_low_risk_passes() -> None:
    debug, variables_all = _completed()
    evidence = grader.RunEvidence(variables_all["Data"])
    assert grader.check_run(PLAN, debug, evidence) == ["Score Credit Risk"]


def test_the_recorded_faulted_run_fails_on_the_rule_task() -> None:
    evidence = grader.RunEvidence(EVIDENCE["variables_all"]["Data"])
    with pytest.raises(SystemExit, match="'Score Credit Risk' finished 'Failed'"):
        grader.check_run(PLAN, EVIDENCE["debug"]["Data"], evidence)


def test_the_recorded_input_shape_carries_the_score() -> None:
    evidence = grader.RunEvidence(EVIDENCE["variables_all"]["Data"])
    inputs, _ = evidence.task_io(RULE_TASK)
    assert list(grader._leaf_values(inputs, "creditScore")) == [742]


@pytest.mark.parametrize("band", ["HIGH_RISK", None, ""])
def test_a_wrong_or_missing_band_fails(band: object) -> None:
    debug, variables_all = _completed(band)
    with pytest.raises(SystemExit, match="riskBand"):
        grader.check_run(PLAN, debug, grader.RunEvidence(variables_all["Data"]))


def test_a_band_kept_as_the_whole_decision_object_passes() -> None:
    debug, variables_all = _completed({"RiskBand": "LOW_RISK"})
    assert grader.check_run(PLAN, debug, grader.RunEvidence(variables_all["Data"]))


def test_a_rule_fed_another_score_fails() -> None:
    debug, variables_all = _completed()
    for block in variables_all["Data"]["Variables"]:
        for element in block["Elements"]:
            if element["ElementId"] == RULE_TASK:
                element["Inputs"] = {"JobArguments": {"CreditScore": None}}
    with pytest.raises(SystemExit, match="creditScore"):
        grader.check_run(PLAN, debug, grader.RunEvidence(variables_all["Data"]))


def test_a_case_without_a_business_rule_task_fails() -> None:
    plan = copy.deepcopy(PLAN)
    for node in plan["nodes"]:
        for lane in node["data"].get("tasks") or []:
            for task in lane:
                task["type"] = "process"
    debug, variables_all = _completed()
    with pytest.raises(SystemExit, match="no business-rule task"):
        grader.check_run(plan, debug, grader.RunEvidence(variables_all["Data"]))


def test_the_binding_layout_is_not_pinned() -> None:
    """The old grader required folderPath binding default '' and exact input
    and output spellings; a run that produced LOW_RISK passes whatever they are."""
    plan = copy.deepcopy(PLAN)
    plan["bindings"] = []
    task = next(t for n in plan["nodes"] for lane in n["data"].get("tasks") or [] for t in lane)
    task["data"]["inputs"][0]["value"] = "=js:vars.creditScore"
    task["data"]["outputs"] = []
    debug, variables_all = _completed()
    assert grader.check_run(plan, debug, grader.RunEvidence(variables_all["Data"]))
