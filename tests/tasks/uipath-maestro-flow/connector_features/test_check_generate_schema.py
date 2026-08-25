from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


CHECKER = Path(__file__).with_name("check_generate_schema.py")
FLOW_CHECK = CHECKER.parents[1] / "_shared" / "flow_check.py"


def _flow(*, parent_values: bool = True) -> dict:
    parameters = [
        ["fields_sub_project_sub_key", "PROJ" if parent_values else ""],
        ["fields_sub_issuetype_sub_id", "10001"],
    ]
    configuration = {
        "essentialConfiguration": {
            "customFieldsRequestDetails": {
                "objectActionName": "GenerateSchema",
                "parameterValues": parameters,
            }
        }
    }
    return {
        "nodes": [
            {"id": "start", "type": "core.trigger.manual"},
            {
                "id": "jira",
                "type": "uipath.connector.uipath-atlassian-jira.create-issue",
                "inputs": {
                    "detail": {
                        "configuration": "=jsonString:" + json.dumps(configuration),
                        "bodyParameters": {"fields.summary": "Schema test"},
                    }
                },
            },
        ],
        "edges": [{"sourceNodeId": "start", "targetNodeId": "jira"}],
    }


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_accepts_root_sdk_emit_with_arbitrary_filename(tmp_path: Path) -> None:
    (tmp_path / "workflow.flow").write_text(json.dumps(_flow()), encoding="utf-8")

    result = _run(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr


def test_accepts_co_located_shared_helper_in_isolated_task_dir(tmp_path: Path) -> None:
    task_dir = tmp_path / "task"
    shared = task_dir / "_shared"
    shared.mkdir(parents=True)
    staged_checker = task_dir / CHECKER.name
    staged_checker.write_bytes(CHECKER.read_bytes())
    (shared / "__init__.py").write_text("", encoding="utf-8")
    (shared / "flow_check.py").write_bytes(FLOW_CHECK.read_bytes())
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "workflow.flow").write_text(json.dumps(_flow()), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(staged_checker)],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_prefers_solution_flow_over_root_scratch_emit(tmp_path: Path) -> None:
    project = tmp_path / "GenerateSchemaTestSolution" / "GenerateSchemaTest"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(
        json.dumps({"ProjectType": "Flow"}), encoding="utf-8"
    )
    (project / "GenerateSchemaTest.flow").write_text(
        json.dumps(_flow()), encoding="utf-8"
    )
    (tmp_path / "scratch.flow").write_text(
        json.dumps({"nodes": [], "edges": []}), encoding="utf-8"
    )

    result = _run(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr


def test_rejects_empty_generate_schema_parent_value(tmp_path: Path) -> None:
    (tmp_path / "workflow.flow").write_text(
        json.dumps(_flow(parent_values=False)), encoding="utf-8"
    )

    result = _run(tmp_path)

    assert result.returncode != 0
    assert "missing parent values" in result.stderr


def test_tokens_outside_jira_configuration_cannot_spoof_result(tmp_path: Path) -> None:
    flow = _flow()
    jira = flow["nodes"][1]
    jira["inputs"]["detail"]["configuration"] = "=jsonString:{}"
    flow["description"] = (
        "GenerateSchema fields_sub_project_sub_key fields_sub_issuetype_sub_id"
    )
    (tmp_path / "workflow.flow").write_text(json.dumps(flow), encoding="utf-8")

    result = _run(tmp_path)

    assert result.returncode != 0
    assert "essentialConfiguration" in result.stderr
