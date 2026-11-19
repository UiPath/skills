"""check_business_rule_run.py against debug run evidence.

testdata/ holds what `uip maestro case debug` and `instance variables-all`
returned for a BusinessRuleSingleCase build, plus that build's plan. That run
faulted the rule task, and no completed run's instance evidence is recorded, so
`_completed()` synthesizes the completed case: it sets the statuses to
Completed, the rule task's Outputs to the decision the rule returns (in the
PascalCased shape the CLI gives every key) and riskBand to the band. The input
shape (`JobArguments.CreditScore`) and every other key are as recorded. No
tenant is touched.

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


def _completed(band: object = "LOW_RISK", rule_band: object = "LOW_RISK"):
    debug = copy.deepcopy(EVIDENCE["debug"]["Data"])
    debug["finalStatus"] = "Completed"
    for execution in debug["elementExecutions"]:
        execution["status"] = "Completed"
    variables_all = copy.deepcopy(EVIDENCE["variables_all"])
    root = next(b for b in variables_all["Data"]["Variables"] if b["ParentElementId"] is None)
    root["Globals"]["RiskBand"] = band
    for element in _rule_elements(variables_all):
        element["Outputs"] = {"RiskDecision": {"RiskBand": rule_band}}
    return debug, variables_all


def _rule_elements(variables_all: dict) -> list[dict]:
    return [
        element
        for block in variables_all["Data"]["Variables"]
        for element in block.get("Elements") or []
        if element["ElementId"] == RULE_TASK
    ]


def _rule_task(plan: dict) -> dict:
    return next(t for n in plan["nodes"] for lane in n["data"].get("tasks") or [] for t in lane)


def _globals(variables_all: dict) -> dict:
    return next(b for b in variables_all["Data"]["Variables"] if b["ParentElementId"] is None)["Globals"]


def test_a_synthesized_completed_run_with_low_risk_passes() -> None:
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


@pytest.mark.parametrize("band", ["HIGH_RISK", None, "", "NOT_LOW_RISK", "low_risk"])
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
    """A literal rule name, no folderPath binding and other input and output
    spellings pass when the run produced LOW_RISK."""
    plan = copy.deepcopy(PLAN)
    plan["bindings"] = []
    task = _rule_task(plan)
    task["data"]["name"] = "CreditRisk"
    task["data"]["folderPath"] = ""
    task["data"]["inputs"][0]["value"] = "=js:vars.creditScore"
    task["data"]["outputs"] = []
    debug, variables_all = _completed()
    assert grader.check_run(plan, debug, grader.RunEvidence(variables_all["Data"]))


def _without_outputs(variables_all: dict) -> dict:
    for element in _rule_elements(variables_all):
        element["Outputs"] = {}
    return variables_all


def test_no_run_outputs_pass_when_the_plan_binds_risk_band_from_the_rule() -> None:
    debug, variables_all = _completed()
    evidence = grader.RunEvidence(_without_outputs(variables_all)["Data"])
    assert grader.check_run(PLAN, debug, evidence) == ["Score Credit Risk"]


@pytest.mark.parametrize("source", [None, "LOW_RISK", "=js:'LOW_RISK'"])
def test_no_run_outputs_fail_when_risk_band_is_only_defaulted_or_a_literal(source: object) -> None:
    plan = copy.deepcopy(PLAN)
    task = _rule_task(plan)
    if source is None:
        task["data"]["outputs"] = [o for o in task["data"]["outputs"] if o["var"] != "riskBand"]
        for variable in plan["variables"]["inputOutputs"]:
            if variable["name"] == "riskBand":
                variable["default"] = "LOW_RISK"
    else:
        next(o for o in task["data"]["outputs"] if o["var"] == "riskBand")["source"] = source
    debug, variables_all = _completed()
    evidence = grader.RunEvidence(_without_outputs(variables_all)["Data"])
    with pytest.raises(SystemExit, match="riskBand"):
        grader.check_run(plan, debug, evidence)


def test_a_rule_that_returned_another_band_fails_although_the_variable_says_low_risk() -> None:
    debug, variables_all = _completed(rule_band="HIGH_RISK")
    with pytest.raises(SystemExit, match="Outputs"):
        grader.check_run(PLAN, debug, grader.RunEvidence(variables_all["Data"]))


def test_a_business_rule_task_bound_to_another_rule_fails() -> None:
    plan = copy.deepcopy(PLAN)
    for binding in plan["bindings"]:
        if binding["name"] == "name":
            binding["default"] = "FraudRisk"
            binding["resourceKey"] = "solution_folder.FraudRisk"
    debug, variables_all = _completed()
    with pytest.raises(SystemExit, match="CreditRisk"):
        grader.check_run(plan, debug, grader.RunEvidence(variables_all["Data"]))


def test_a_build_that_feeds_the_trigger_input_straight_to_the_task_passes() -> None:
    """The request names creditScore as the trigger input, not a case variable."""
    debug, variables_all = _completed()
    root = next(b for b in variables_all["Data"]["Variables"] if b["ParentElementId"] is None)
    root["Globals"].pop("CreditScore")
    root["GlobalDefinitions"].pop("CreditScore")
    assert grader.check_run(PLAN, debug, grader.RunEvidence(variables_all["Data"]))
