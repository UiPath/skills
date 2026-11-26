"""The rule contract the consumer fixtures assume is decision-keyed and self-consistent.

Case and BPMN tasks bind a rule through a saved copy of its contract: a project's
`entry-points.json`, or a saved `describe` result. These offline tests check each copy
against its own `.dmn`, and the saved describe result against the rule it describes.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

TASKS = Path(__file__).resolve().parents[2]
NS = {"dmn": "https://www.omg.org/spec/DMN/20230324/MODEL/"}
LOAN_RULES = TASKS / "uipath-rules" / "_shared" / "fixtures" / "LoanRules"
CREDIT_RISK = TASKS / "uipath-maestro-case" / "single_node" / "business_rule" / "fixtures" / "BusinessRuleSingleCase" / "CreditRisk"
RULE_DESCRIBE = TASKS / "uipath-maestro-case" / "edit" / "add_business_rule_task" / "fixtures" / "rule-describe.json"
PROJECTS = {"LoanRules (two decisions)": LOAN_RULES, "CreditRisk (case fixture)": CREDIT_RISK}


def entry_points(project: Path) -> list:
    return json.loads((project / "entry-points.json").read_text(encoding="utf-8"))["entryPoints"]


def decisions(project: Path) -> dict:
    """The decisions of the project's one `.dmn`, id to name."""
    (dmn,) = project.glob("*.dmn")
    root = ET.parse(dmn).getroot()
    return {d.get("id"): d.get("name") for d in root.findall("dmn:decision", NS)}


@pytest.mark.parametrize("project", PROJECTS.values(), ids=PROJECTS.keys())
def test_every_entry_point_is_decision_keyed(project):
    names = decisions(project)
    (dmn,) = project.glob("*.dmn")
    for entry in entry_points(project):
        path, _, decision_id = entry["filePath"].partition("#")
        assert path == f"/{dmn.name}", entry["filePath"]
        output = entry["output"]
        assert output.get("x-uipath-decision-keyed") is True, entry["filePath"]
        # A decision's entry point answers under its own name; the whole-file one under every name.
        expected = {names[decision_id]} if decision_id else set(names.values())
        assert set(output["properties"]) == expected, entry["filePath"]
        for decision in output["properties"].values():
            assert decision["type"] == "object" and decision["properties"], entry["filePath"]


def test_the_saved_describe_result_matches_the_rule_contract():
    """The case `edit` task's saved describe result answers in the shape the case `single_node` rule has."""
    outputs = json.loads(RULE_DESCRIBE.read_text(encoding="utf-8"))["Data"]["Outputs"]
    described = next(o for o in outputs if o["id"] == "output")
    assert described["source"] == "=result"
    (entry,) = entry_points(CREDIT_RISK)
    assert described["_jsonSchema"]["properties"] == entry["output"]["properties"]
