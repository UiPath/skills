"""The rule contract the consumer fixtures assume is the one `uip rules refresh` writes.

Case and BPMN tasks bind a rule through a saved copy of its contract: a project's
`entry-points.json`, or a saved `describe` result. If the CLI changes the shape it
writes, those copies go stale and the consumer tasks grade against a contract no real
rule has. Nothing else compares them, so this file does.

The tests that run `uip rules refresh` skip when `uip` is not installed. The offline
tests always run.
"""

import copy
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

TASKS = Path(__file__).resolve().parents[2]
NS = {"dmn": "https://www.omg.org/spec/DMN/20230324/MODEL/"}
LOAN_RULES = TASKS / "uipath-rules" / "_shared" / "fixtures" / "LoanRules"
CREDIT_RISK = TASKS / "uipath-maestro-case" / "single_node" / "business_rule" / "fixtures" / "BusinessRuleSingleCase" / "CreditRisk"
RULE_DESCRIBE = TASKS / "uipath-maestro-case" / "edit" / "add_business_rule_task" / "fixtures" / "rule-describe.json"
PROJECTS = {"LoanRules (two decisions)": LOAN_RULES, "CreditRisk (case fixture)": CREDIT_RISK}

# The CI job that installs `uip` sets RULES_CONTRACT_REQUIRE_UIP, so a broken install fails
# there instead of skipping the one comparison the job exists to run.
if shutil.which("uip") is None and os.environ.get("RULES_CONTRACT_REQUIRE_UIP"):
    pytest.fail("RULES_CONTRACT_REQUIRE_UIP is set but `uip` is not on PATH", pytrace=False)
needs_uip = pytest.mark.skipif(shutil.which("uip") is None, reason="`uip` is not installed; the refresh comparison needs it")


def entry_points(project: Path) -> list:
    return json.loads((project / "entry-points.json").read_text(encoding="utf-8"))["entryPoints"]


def contract(project: Path) -> list:
    """The entry points without `uniqueId`, which identifies an entry point and is not its shape."""
    entries = copy.deepcopy(entry_points(project))
    for entry in entries:
        entry.pop("uniqueId", None)
    return sorted(entries, key=lambda entry: entry["filePath"])


def decisions(project: Path) -> dict:
    """The decisions of the project's one `.dmn`, id to name."""
    (dmn,) = project.glob("*.dmn")
    root = ET.parse(dmn).getroot()
    return {d.get("id"): d.get("name") for d in root.findall("dmn:decision", NS)}


@needs_uip
@pytest.mark.parametrize("project", PROJECTS.values(), ids=PROJECTS.keys())
def test_refresh_reproduces_the_committed_contract(project, tmp_path):
    work = tmp_path / project.name
    shutil.copytree(project, work)
    completed = subprocess.run(["uip", "rules", "refresh", str(work), "--output", "json"],
                               capture_output=True, text=True, timeout=120)
    assert completed.returncode == 0, completed.stdout or completed.stderr
    assert contract(work) == contract(project), (
        f"`uip rules refresh` now writes a different contract for {project.name}. Regenerate the "
        f"committed entry-points.json and every consumer fixture copied from it"
    )


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
