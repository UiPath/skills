"""Self-tests for check_publish.py, driven through the real mock dispatcher.

Each test stages a sandbox the way coder_eval does (mock_template + fixtures),
runs a publish sequence through `mocks/uip`, then grades the call log.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
MOCK_TEMPLATE = HERE.parent / "_shared" / "mock_template"
CHECKER = HERE / "check_publish.py"
PDD = "pdd-retail-account-onboarding.md"
MAP = "process-map-retail-account-onboarding.bpmn"
OWNER = "dana.reyes@fjordline.example"
DOC_PDD = "ah-answer_option-ovrbp-0-3-0-1"  # "Standard operating procedure" — closest to a PDD
DOC_MAP = "ah-answer_option-ovrbp-0-3-0-2"  # "Task/Process maps/flowcharts"


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    shutil.copytree(MOCK_TEMPLATE, tmp_path, dirs_exist_ok=True)
    shutil.copytree(HERE / "fixtures", tmp_path, dirs_exist_ok=True)
    return tmp_path


def uip(sandbox: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(sandbox / "mocks" / "uip"), *args],
        cwd=sandbox, capture_output=True, text=True, check=False,
    )


def grade(sandbox: Path, check: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER), check],
        cwd=sandbox, capture_output=True, text=True, check=False,
    )


def good_answers() -> dict:
    return {"OVR": {
        "ah-section-ovrbp-0-0": {
            "OVR-OVERVIEW_NAME": {"value": "Retail Account Onboarding"},
            "OVR-OVERVIEW_DESCRIPTION": {"value": "Automates retail current-account onboarding from CRM intake to T24 provisioning."},
            "OVR-OVERVIEW_CATEGORY": {"value": 12},
            "OVR-PROCESS_OWNER": OWNER,
            "OVR-PROCESS_DOCUMENTS": {"value": [DOC_PDD, DOC_MAP]},
            "OVR-COUNT_APPS": {
                "value": [21, 22],
                "new_applications": [
                    {"application_name": "Trapets", "application_version": "4.1"},
                    {"application_name": "Scrive", "application_version": "2026"},
                    {"application_name": "Temenos T24", "application_version": "R21"},
                ],
            },
        },
        "ah-section-ovrbp-0-1": {"OVR-OVERVIEW_PROCESS_SUBMITTER": OWNER},
    }}


def publish(sandbox: Path, answers: dict, *, pdd_type: str = "1", creates: int = 1, verify: bool = True) -> None:
    uip(sandbox, "ah", "--help")
    uip(sandbox, "ah", "idea-flows", "list", "--output", "json")
    schema = uip(sandbox, "ah", "automations", "schema", "get", "--idea-flow-id", "8",
                 "--destination", "./ah-schema.json", "--output", "json")
    assert schema.returncode == 0, schema.stderr
    assert json.loads((sandbox / "ah-schema.json").read_text())["user_inputs"]
    uip(sandbox, "ah", "auth-info", "get", "--output", "json")
    (sandbox / "ah-answers.json").write_text(json.dumps(answers))
    for _ in range(creates):
        uip(sandbox, "ah", "automations", "create", "--from-schema", "--idea-flow-id", "8",
            "--file", "./ah-answers.json", "--output", "json")
    uip(sandbox, "ah", "documents", "create", "4815", "--title", "PDD", "--description", "PDD",
        "--document-type-id", pdd_type, "--file", PDD, "--output", "json")
    uip(sandbox, "ah", "documents", "create", "4815", "--title", "Map", "--description", "Map",
        "--document-type-id", "6", "--file", MAP, "--output", "json")
    if verify:
        uip(sandbox, "ah", "documents", "list", "4815", "--output", "json")
        uip(sandbox, "ah", "automations", "get", "4815", "--all-fields", "--output", "json")


@pytest.mark.parametrize("check", ["create-once", "payload", "applications", "documents", "verify"])
def test_golden_publish_passes(sandbox: Path, check: str) -> None:
    publish(sandbox, good_answers())
    result = grade(sandbox, check)
    assert result.returncode == 0, result.stdout


def test_help_on_create_is_not_a_create(sandbox: Path) -> None:
    uip(sandbox, "ah", "automations", "create", "--help")
    publish(sandbox, good_answers())
    assert grade(sandbox, "create-once").returncode == 0


def test_payload_captured_at_call_time(sandbox: Path) -> None:
    publish(sandbox, good_answers())
    (sandbox / "ah-answers.json").write_text("{}")  # agent overwrites after the create
    assert grade(sandbox, "payload").returncode == 0


def test_duplicate_create_fails(sandbox: Path) -> None:
    publish(sandbox, good_answers(), creates=2)
    assert "exactly 1" in grade(sandbox, "create-once").stdout


def test_template_placeholders_fail(sandbox: Path) -> None:
    answers = good_answers()
    answers["OVR"]["ah-section-ovrbp-0-0"]["OVR-PROCESS_OWNER"] = "First.last@example.com"
    publish(sandbox, answers)
    assert "placeholders" in grade(sandbox, "payload").stdout


def test_archived_or_template_category_fails(sandbox: Path) -> None:
    for category in (1, 4):
        answers = good_answers()
        answers["OVR"]["ah-section-ovrbp-0-0"]["OVR-OVERVIEW_CATEGORY"] = {"value": category}
        box = sandbox / f"c{category}"
        shutil.copytree(sandbox, box, ignore=shutil.ignore_patterns("c*"))
        publish(box, answers)
        assert "category" in grade(box, "payload").stdout


def test_wrapped_owner_fails(sandbox: Path) -> None:
    answers = good_answers()
    answers["OVR"]["ah-section-ovrbp-0-0"]["OVR-PROCESS_OWNER"] = {"value": OWNER}
    publish(sandbox, answers)
    assert "direct string" in grade(sandbox, "payload").stdout


def test_out_of_scope_system_fails(sandbox: Path) -> None:
    answers = good_answers()
    answers["OVR"]["ah-section-ovrbp-0-0"]["OVR-COUNT_APPS"]["value"] = [21, 22, 25]  # Avaloq Core
    publish(sandbox, answers)
    assert grade(sandbox, "applications").returncode == 1


def test_missing_new_application_fails(sandbox: Path) -> None:
    answers = good_answers()
    apps = answers["OVR"]["ah-section-ovrbp-0-0"]["OVR-COUNT_APPS"]
    apps["new_applications"] = apps["new_applications"][:2]  # drops Temenos T24
    publish(sandbox, answers)
    assert "temenos t24" in grade(sandbox, "applications").stdout


def test_wrong_pdd_type_fails(sandbox: Path) -> None:
    publish(sandbox, good_answers(), pdd_type="9")
    assert "type id" in grade(sandbox, "documents").stdout


def test_regenerated_process_map_fails(sandbox: Path) -> None:
    (sandbox / MAP).write_text("<bpmn:definitions/>")  # bare BPMN with no bpmndi layout
    publish(sandbox, good_answers())
    assert "process map" in grade(sandbox, "documents").stdout


def test_no_read_back_fails(sandbox: Path) -> None:
    publish(sandbox, good_answers(), verify=False)
    assert grade(sandbox, "verify").returncode == 1


def test_no_calls_fails(sandbox: Path) -> None:
    assert "never invoked" in grade(sandbox, "payload").stdout
