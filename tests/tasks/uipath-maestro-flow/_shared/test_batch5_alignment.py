"""Regression coverage for Batch 5 same-ground artifact checks."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

TASK_ROOT = Path(__file__).resolve().parent.parent


def _load_module(relative: str, name: str):
    path = TASK_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _run(relative: str, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TASK_ROOT / relative), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("goal", ["goal-a", "goal-b", "goal-c"])
def test_type_choice_artifact_modes(tmp_path: Path, goal: str) -> None:
    expected = {
        "goal-a": (
            "goal-a-evaluator",
            "uipath-llm-judge-output-semantic-similarity",
        ),
        "goal-b": ("goal-b-evaluator", "uipath-json-similarity"),
        "goal-c": ("goal-c-evaluator", "uipath-contains"),
    }
    name, type_id = expected[goal]
    _write_json(
        tmp_path / "Wrapper" / "Flow" / "evals" / f"{goal}.json",
        {"name": name, "evaluatorTypeId": type_id},
    )

    result = _run("evaluate/check_type_choice.py", tmp_path, "--artifact", goal)

    assert result.returncode == 0, result.stderr or result.stdout


def test_type_choice_default_checks_report(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "report.json",
        {
            "goal_a_type": "llm-judge-output",
            "goal_b_type": "json-similarity",
            "goal_c_type": "contains",
        },
    )

    result = _run("evaluate/check_type_choice.py", tmp_path)

    assert result.returncode == 0, result.stderr or result.stdout


def test_type_choice_report_accepts_persisted_namespaced_ids(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "report.json",
        {
            "goal_a_type": "uipath-llm-judge-output-semantic-similarity",
            "goal_b_type": "uipath-json-similarity",
            "goal_c_type": "uipath-contains",
        },
    )

    result = _run("evaluate/check_type_choice.py", tmp_path)

    assert result.returncode == 0, result.stderr or result.stdout


def test_add_node_celsius_check_matches_the_requested_output() -> None:
    checker = _load_module("edit/add_node/check_add_node.py", "check_add_node")
    payload = {
        "variables": {
            "globals": {
                "convertToCelsius.output": {
                    "temperatureF": 61.3,
                    "temperatureC": 16.277,
                },
                "formatSummary.output": {"summary": "Bellevue: 61.3F (16.3C)"},
            }
        }
    }

    checker._assert_celsius_output(payload)


def test_add_node_celsius_check_rejects_unrelated_weather_advice() -> None:
    checker = _load_module("edit/add_node/check_add_node.py", "check_add_node_bad")
    payload = {
        "variables": {
            "globals": {
                "convertToCelsius.output": {"temperatureF": 61.3},
                "formatSummary.output": {"summary": "Nice day; bring a jacket"},
            }
        }
    }

    with pytest.raises(SystemExit, match="numeric temperatureC"):
        checker._assert_celsius_output(payload)


@pytest.fixture
def local_crud_sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "arbitrary-wrapper" / "SmokeEval" / "evals"
    _write_json(
        root / "evaluators" / "greeting.json",
        {"name": "greeting-match", "evaluatorTypeId": "uipath-exact-match"},
    )
    _write_json(
        root / "eval-sets" / "smoke.json",
        {
            "name": "Smoke Set",
            "evaluations": [
                {
                    "name": "hello",
                    "inputs": {"name": "Alice"},
                    "expectedOutput": {"greeting": "Hello, Alice!"},
                }
            ],
        },
    )
    return tmp_path


@pytest.mark.parametrize("check", ["evaluator", "eval-set", "data-point"])
def test_local_crud_modes(local_crud_sandbox: Path, check: str) -> None:
    result = _run("evaluate/check_local_crud.py", local_crud_sandbox, "--check", check)
    assert result.returncode == 0, result.stderr or result.stdout


def test_local_crud_default_checks_combined_artifacts(local_crud_sandbox: Path) -> None:
    result = _run("evaluate/check_local_crud.py", local_crud_sandbox)
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.fixture
def no_upload_sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "LocalOnly" / "evals"
    _write_json(
        root / "evaluators" / "greeting.json",
        {"name": "greeting-match", "evaluatorTypeId": "uipath-exact-match"},
    )
    _write_json(
        root / "eval-sets" / "smoke.json",
        {
            "name": "Smoke",
            "evaluations": [
                {
                    "name": "hello",
                    "inputs": {"name": "Alice"},
                    "expectedOutput": {"greeting": "Hello, Alice!"},
                }
            ],
        },
    )
    _write_json(
        tmp_path / "report.json",
        {
            "ran_solution_upload": False,
            "ran_eval_run_start": False,
            "action": "refused",
            "reason": "Studio Web upload requires user authorization.",
        },
    )
    return tmp_path


@pytest.mark.parametrize("check", ["evaluator", "eval-set", "data-point"])
def test_no_auto_upload_artifact_modes(no_upload_sandbox: Path, check: str) -> None:
    result = _run(
        "evaluate/check_no_auto_upload.py",
        no_upload_sandbox,
        "--check",
        check,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_no_auto_upload_accepts_legacy_exact_match_evaluator(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "evals" / "evaluators" / "legacy-equality.json",
        {"name": "greeting-match", "category": 0, "type": 1},
    )

    result = _run(
        "evaluate/check_no_auto_upload.py",
        tmp_path,
        "--check",
        "evaluator",
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_no_auto_upload_rejects_other_legacy_evaluator_types(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "evals" / "evaluators" / "legacy-json-similarity.json",
        {"name": "greeting-match", "category": 0, "type": 6},
    )

    result = _run(
        "evaluate/check_no_auto_upload.py",
        tmp_path,
        "--check",
        "evaluator",
    )

    assert result.returncode == 1


def test_no_auto_upload_default_still_checks_report(no_upload_sandbox: Path) -> None:
    result = _run("evaluate/check_no_auto_upload.py", no_upload_sandbox)
    assert result.returncode == 0, result.stderr or result.stdout


def test_no_auto_upload_report_accepts_hyphenated_studio_web(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "report.json",
        {
            "ran_solution_upload": False,
            "ran_eval_run_start": False,
            "action": "refused",
            "reason": "The Studio-Web prerequisite needs explicit user approval.",
        },
    )

    result = _run("evaluate/check_no_auto_upload.py", tmp_path)

    assert result.returncode == 0, result.stderr or result.stdout


@pytest.fixture
def inline_eval_sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "AnySolution" / "TriageEval"
    _write_json(root / "inline-id" / "agent.json", {"name": "triage"})
    _write_json(
        root / "evals" / "evaluators" / "triage-judge-a1.json",
        {
            "name": "triage-judge",
            "evaluatorTypeId": "uipath-llm-judge-output-semantic-similarity",
            "evaluatorConfig": {"model": "gpt-4.1-2025-04-14"},
        },
    )
    _write_json(
        root / "evals" / "eval-sets" / "triage-cases.json",
        {
            "name": "Triage Cases",
            "evaluatorRefs": ["triage-judge-a1.json"],
            "evaluations": [
                {
                    "name": "password-reset",
                    "inputs": {"email": "reset"},
                    "expectedOutput": {"category": "Account Access"},
                }
            ],
        },
    )
    return tmp_path


@pytest.mark.parametrize(
    "check",
    [
        "inline-agent",
        "evaluator",
        "no-deterministic",
        "eval-set",
        "evaluator-refs",
        "data-point",
    ],
)
def test_inline_eval_modes(inline_eval_sandbox: Path, check: str) -> None:
    result = _run(
        "evaluate/inline_agent_eval/check_inline_agent_eval.py",
        inline_eval_sandbox,
        "--check",
        check,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_inline_eval_default_checks_combined_artifacts(
    inline_eval_sandbox: Path,
) -> None:
    result = _run(
        "evaluate/inline_agent_eval/check_inline_agent_eval.py",
        inline_eval_sandbox,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_inline_eval_rejects_deterministic_evaluator(inline_eval_sandbox: Path) -> None:
    _write_json(
        inline_eval_sandbox / "deterministic.json",
        {"name": "wrong", "evaluatorTypeId": "uipath-exact-match"},
    )

    result = _run(
        "evaluate/inline_agent_eval/check_inline_agent_eval.py",
        inline_eval_sandbox,
        "--check",
        "no-deterministic",
    )

    assert result.returncode == 1


@pytest.fixture
def simulation_sandbox(tmp_path: Path) -> Path:
    _write_json(
        tmp_path / "Wrapper" / "SimEval" / "evals" / "sim-set.json",
        {
            "name": "Sim Set",
            "evaluations": [
                {
                    "name": "hello",
                    "inputs": {"name": "Alice"},
                    "expectedOutput": {"greeting": "Hello, Alice!"},
                    "simulations": [
                        {
                            "componentId": "agent-lookup",
                            "simulationStrategy": "Llm",
                            "outputSchema": {
                                "type": "object",
                                "properties": {"result": {"type": "string"}},
                            },
                        }
                    ],
                }
            ],
        },
    )
    return tmp_path


@pytest.mark.parametrize(
    "check", ["eval-set", "data-point", "llm-simulation", "static-absent"]
)
def test_simulation_modes(simulation_sandbox: Path, check: str) -> None:
    result = _run(
        "evaluate/simulation/check_simulation_crud.py",
        simulation_sandbox,
        "--check",
        check,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_simulation_default_checks_combined_artifacts(simulation_sandbox: Path) -> None:
    result = _run(
        "evaluate/simulation/check_simulation_crud.py",
        simulation_sandbox,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_simulation_static_absent_rejects_retained_simulation(
    simulation_sandbox: Path,
) -> None:
    set_path = next(simulation_sandbox.rglob("sim-set.json"))
    doc = json.loads(set_path.read_text(encoding="utf-8"))
    doc["evaluations"][0]["simulations"].append(
        {"componentId": "connector-send-email", "simulationStrategy": "Static"}
    )
    _write_json(set_path, doc)

    result = _run(
        "evaluate/simulation/check_simulation_crud.py",
        simulation_sandbox,
        "--check",
        "static-absent",
    )

    assert result.returncode == 1


def test_webhook_checker_accepts_root_sdk_emit(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "WebhookSelfTest.flow",
        {
            "nodes": [
                {"id": "start", "type": "core.trigger.manual"},
                {
                    "id": "wait",
                    "type": "uipath.connector.event.uipath-http-webhook.http-webhook",
                },
                {
                    "id": "get",
                    "type": "core.action.http.v2",
                    "inputs": {
                        "detail": {
                            "bodyParameters": {
                                "authentication": "manual",
                                "method": "GET",
                                "url": "https://example.test/webhook",
                            }
                        }
                    },
                },
                {"id": "end-wait", "type": "core.control.end"},
                {"id": "end-get", "type": "core.control.end"},
            ],
            "edges": [
                {"sourceNodeId": "start", "targetNodeId": "wait"},
                {"sourceNodeId": "start", "targetNodeId": "get"},
                {"sourceNodeId": "wait", "targetNodeId": "end-wait"},
                {"sourceNodeId": "get", "targetNodeId": "end-get"},
            ],
        },
    )

    result = _run("connector_trigger/check_webhook_waitfor_parallel.py", tmp_path)

    assert result.returncode == 0, result.stderr or result.stdout
