"""Unit tests for check_df_picker.py — the Data Fabric picker grader.

Synthetic stubs only; no tenant. Every case writes the fixture entity's
resource into the solution, so a pass has to come from what the task selects.
"""

import json
import subprocess
import sys
from pathlib import Path

CHECKER = Path(__file__).with_name("check_df_picker.py")
NAME, KEY, FOLDER = "SkillPickerEvalEntity", "00000000-0000-4000-8000-00000000e001", "00000000-0000-4000-8000-00000000f001"


def binding(bid, key, default, attribute="name", resource="entity"):
    return {"id": bid, "type": "string", "resource": resource, "resourceKey": key,
            "name": bid, "propertyAttribute": attribute, "default": default}


def plan(query, bindings, task_bindings=None):
    task = {"type": "execute-connector-activity", "data": {
        "typeId": "t", "connectionId": "c",
        "context": [{"name": "connectorKey", "value": "uipath-uipath-dataservice"}],
        "inputs": [{"name": "queryParameters", "body": query}],
        "bindings": bindings if task_bindings is None else task_bindings,
    }}
    return {"bindings": bindings,
            "nodes": [{"type": "case-management:Stage", "data": {"tasks": [[task]]}}]}


def run(tmp_path, caseplan):
    (tmp_path / "_setup").mkdir()
    (tmp_path / "_setup" / "picker_entity.json").write_text(json.dumps(
        {"name": NAME, "key": KEY, "folderKey": FOLDER, "folderPath": "Shared"}))
    resource = tmp_path / "DfPickerCase/resources/solution_folder/entity/native"
    resource.mkdir(parents=True)
    (resource / "e.json").write_text(json.dumps({"resource": {"name": NAME, "key": KEY}}))
    plan_dir = tmp_path / "DfPickerCase/DfPickerCase"
    plan_dir.mkdir(parents=True)
    (plan_dir / "caseplan.case").write_text(json.dumps(caseplan))
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True)


BOUND = [binding("b1", KEY, NAME), binding("b2", KEY, FOLDER, "folderKey")]
QUERY = {"entityScope": "folder", "folderEntityName": "=bindings.b1", "folderEntityName_folderKey": "=bindings.b2"}


def test_passes_when_the_task_binds_the_fixture_entity_in_its_folder(tmp_path):
    r = run(tmp_path, plan(QUERY, BOUND))
    assert r.returncode == 0, r.stdout + r.stderr


def test_fails_when_the_task_picks_another_entity_beside_an_unused_fixture_binding(tmp_path):
    other = binding("b9", "other-key", "WrongEntity")
    r = run(tmp_path, plan({**QUERY, "folderEntityName": "=bindings.b9"}, [*BOUND, other]))
    assert r.returncode == 1
    assert "folderEntityName" in r.stderr + r.stdout


def test_fails_on_a_literal_entity_name(tmp_path):
    r = run(tmp_path, plan({**QUERY, "folderEntityName": NAME}, BOUND))
    assert r.returncode == 1


def test_fails_on_another_scope(tmp_path):
    r = run(tmp_path, plan({**QUERY, "entityScope": "tenant"}, BOUND))
    assert r.returncode == 1
    assert "entityScope" in r.stderr + r.stdout


def test_fails_without_a_folder_key(tmp_path):
    query = {k: v for k, v in QUERY.items() if k != "folderEntityName_folderKey"}
    r = run(tmp_path, plan(query, BOUND))
    assert r.returncode == 1
    assert "folderEntityName_folderKey" in r.stderr + r.stdout


def test_fails_when_the_folder_key_names_another_folder(tmp_path):
    wrong = [BOUND[0], binding("b2", KEY, "other-folder", "folderKey")]
    r = run(tmp_path, plan(QUERY, wrong))
    assert r.returncode == 1
    assert "folderKey" in r.stderr + r.stdout


def test_fails_when_the_task_does_not_list_its_entity_binding(tmp_path):
    r = run(tmp_path, plan(QUERY, BOUND, task_bindings=[]))
    assert r.returncode == 1
    assert "data.bindings" in r.stderr + r.stdout
