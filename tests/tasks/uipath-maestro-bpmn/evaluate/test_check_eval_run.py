from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_eval_run.py")
_spec = importlib.util.spec_from_file_location("check_eval_run", CHECKER)
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _write(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")


def _row(name: str, score: float, status: str = "Completed") -> dict:
    return {"DataPoint": name, "Status": status, "EvaluatorScores": [{"Score": score}]}


def _project(tmp_path: Path, expected: dict[str, int]) -> None:
    root = tmp_path / "ProductCheck" / "ProductCheck"
    _write(
        root / "evals" / "evaluators" / "product-match.json",
        {
            "id": "product-match",
            "evaluatorTypeId": "uipath-exact-match",
            "evaluatorConfig": {"name": "product-match"},
        },
    )
    _write(
        root / "evals" / "eval-sets" / "product-checks.json",
        {
            "name": "Product Checks",
            "evaluations": [
                {"name": n, "inputs": {}, "expectedOutput": {"product": v}}
                for n, v in expected.items()
            ],
        },
    )


def test_artifacts_pass_with_both_cases(tmp_path: Path) -> None:
    _project(tmp_path, {"correct": 42, "wrong-on-purpose": 41})
    result = _run(tmp_path, "--check", "artifacts")
    assert result.returncode == 0, result.stderr


def test_artifacts_reject_wrong_expected_value(tmp_path: Path) -> None:
    # A failing case "fixed" to expect 42 would make every run pass trivially.
    _project(tmp_path, {"correct": 42, "wrong-on-purpose": 42})
    result = _run(tmp_path, "--check", "artifacts")
    assert result.returncode != 0
    assert "wrong-on-purpose" in result.stderr


def test_artifacts_single_case_for_compare_task(tmp_path: Path) -> None:
    _project(tmp_path, {"correct": 42})
    assert _run(tmp_path, "--check", "artifacts", "--data-points", "correct").returncode == 0
    assert _run(tmp_path, "--check", "artifacts").returncode != 0


def test_run_id_prefers_eval_set_run_id(tmp_path: Path) -> None:
    path = tmp_path / "run-start.json"
    _write(path, {"Result": "Success", "Data": {"ProjectId": "p-1", "EvalSetRunId": "r-9"}})
    assert check.run_id_from(path) == "r-9"


@pytest.mark.parametrize(
    "envelope",
    [
        {"Result": "Success", "Data": [_row("correct", 1.0), _row("wrong-on-purpose", 0.0)]},
        {
            "Result": "Success",
            "Code": "BpmnEvalRunCompleted",
            "Data": {"Results": [_row("correct", 1.0), _row("wrong-on-purpose", 0.0)]},
        },
    ],
)
def test_verify_scores_accepts_flat_and_nested_rows(envelope: dict) -> None:
    check.verify_scores(envelope)


@pytest.mark.parametrize(
    "rows",
    [
        [_row("correct", 1.0), _row("wrong-on-purpose", 1.0)],
        [_row("correct", 0.0), _row("wrong-on-purpose", 0.0)],
        [_row("correct", 1.0), _row("wrong-on-purpose", 0.0, status="WorkloadFailed")],
        [_row("correct", 1.0)],
    ],
)
def test_verify_scores_rejects_bad_runs(rows: list[dict]) -> None:
    with pytest.raises(SystemExit):
        check.verify_scores({"Result": "Success", "Data": rows})


def test_failed_only(tmp_path: Path) -> None:
    path = tmp_path / "eval-evidence" / "failed-only.json"
    _write(path, {"Result": "Success", "Data": [_row("wrong-on-purpose", 0.0)]})
    assert _run(tmp_path, "--check", "failed-only").returncode == 0
    _write(path, {"Result": "Success", "Data": [_row("correct", 1.0), _row("wrong-on-purpose", 0.0)]})
    assert _run(tmp_path, "--check", "failed-only").returncode != 0


def test_export(tmp_path: Path) -> None:
    assert _run(tmp_path, "--check", "export").returncode != 0
    (tmp_path / "bpmn-eval-results-20260101.csv").write_text(
        "DataPoint,Score\ncorrect,1\nwrong-on-purpose,0\n", encoding="utf-8"
    )
    assert _run(tmp_path, "--check", "export").returncode == 0


def test_verify_run_list() -> None:
    payload = {
        "Result": "Success",
        "Data": [
            {"EvalSetRunId": "r-1", "Status": "Completed"},
            {"EvalSetRunId": "r-2", "Status": "Completed"},
        ],
    }
    check.verify_run_list(payload, "r-1", "r-2")
    payload["Data"][1]["Status"] = "Running"
    with pytest.raises(SystemExit):
        check.verify_run_list(payload, "r-1", "r-2")
    with pytest.raises(SystemExit):
        check.verify_run_list(payload, "r-1", "r-3")


def test_compare(tmp_path: Path) -> None:
    evidence = tmp_path / "eval-evidence"
    _write(evidence / "run-1.json", {"Result": "Success", "Data": {"EvalSetRunId": "r-1"}})
    _write(evidence / "run-2.json", {"Result": "Success", "Data": {"EvalSetRunId": "r-2"}})
    _write(evidence / "compare.json", {"Result": "Success", "Data": {"Base": "r-1", "Target": "r-2"}})
    assert _run(tmp_path, "--check", "compare").returncode == 0
    _write(evidence / "compare.json", {"Result": "Success", "Data": {"Base": "r-1"}})
    assert _run(tmp_path, "--check", "compare").returncode != 0
