"""Guard: `uip maestro case debug` is retried once for tenant faults, never for plan faults.

The debug graders drive a live tenant. Three faults observed on 2026-09-11 were
the service's and not the plan's — a 403 and a 504 on `poll-instance-status`,
and a debug instance cancelled mid-run — and all three passed on re-run (4/4
across both harnesses). Everything else must still fail on the first attempt:
retrying a plan defect into a pass is the failure mode this test exists to
prevent.

    python3 -m pytest tests/tasks/uipath-maestro-case/_shared/test_case_check_debug_retry.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import case_check  # noqa: E402

TRANSIENT = [
    # verbatim shapes from the 2026-09-11 nightlies and CI run 34510099349
    'Failed during poll-instance-status: 403 Forbidden on GET /api/v1/debug-instances/fc07737f/element-executions',
    'Failed during poll-instance-status: 504 Gateway Timeout on GET /api/v1/debug-instances/918e7df2/element-executions',
    '{"Result": "Success", "Code": "CaseDebug", "Data": {"finalStatus": "Cancelled"}}',
    'Failed during start-instance: 429 Too Many Requests',
    'Failed during poll-instance-status: 503 Service Unavailable',
]

PLAN_FAULTS = [
    'Failed during start-instance: 400 Bad Request',
    'ValidationError: unknown option "-instance-id"',
    '{"Result": "Failure", "ErrorCode": "invalid_argument", "Message": "Resource is not configured"}',
    '{"Result": "Success", "Data": {"finalStatus": "Faulted"}}',
    'Failed during poll-instance-status: 404 Not Found',
]


@pytest.mark.parametrize("output", TRANSIENT)
def test_tenant_faults_are_named(output: str) -> None:
    assert case_check.debug_fault_is_transient(output) is not None, output


@pytest.mark.parametrize("output", PLAN_FAULTS)
def test_plan_faults_are_not_retried(output: str) -> None:
    assert case_check.debug_fault_is_transient(output) is None, output


class _Recorder:
    """Stands in for subprocess.run: scripted returncodes, counted calls."""

    def __init__(self, *results: tuple[int, str]) -> None:
        self.results = list(results)
        self.debug_calls = 0

    def __call__(self, cmd, **kwargs):  # noqa: ANN001, ANN003
        joined = " ".join(cmd)
        if "debug" in joined:
            self.debug_calls += 1
            code, out = self.results.pop(0)
            return subprocess.CompletedProcess(cmd, code, out, "")
        # `solution resources refresh`
        return subprocess.CompletedProcess(cmd, 0, "{}", "")


OK_PAYLOAD = json.dumps({"Result": "Success", "Data": {"finalStatus": "Completed"}})


@pytest.fixture
def _stub_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(case_check, "find_project_dir", lambda *a, **k: str(tmp_path))
    monkeypatch.setattr(case_check, "find_solution_dir", lambda *a, **k: str(tmp_path))
    monkeypatch.setattr(case_check.time, "sleep", lambda _s: None)


def test_transient_fault_retries_once_and_succeeds(
    monkeypatch: pytest.MonkeyPatch, _stub_paths: None, capsys: pytest.CaptureFixture[str]
) -> None:
    rec = _Recorder((1, 'Failed during poll-instance-status: 403 Forbidden on GET /x'), (0, OK_PAYLOAD))
    monkeypatch.setattr(subprocess, "run", rec)
    payload = case_check.start_debug()
    assert payload["finalStatus"] == "Completed"
    assert rec.debug_calls == 2
    assert "retrying" in capsys.readouterr().out


def test_transient_fault_twice_still_fails_and_says_it_retried(
    monkeypatch: pytest.MonkeyPatch, _stub_paths: None
) -> None:
    fault = (1, 'Failed during poll-instance-status: 504 Gateway Timeout on GET /x')
    rec = _Recorder(fault, fault)
    monkeypatch.setattr(subprocess, "run", rec)
    with pytest.raises(SystemExit) as exc:
        case_check.start_debug()
    assert rec.debug_calls == 2
    assert "after one retry" in str(exc.value)


def test_plan_fault_fails_on_the_first_attempt(
    monkeypatch: pytest.MonkeyPatch, _stub_paths: None
) -> None:
    rec = _Recorder((1, '{"Result": "Failure", "Message": "Resource is not configured"}'), (0, OK_PAYLOAD))
    monkeypatch.setattr(subprocess, "run", rec)
    with pytest.raises(SystemExit) as exc:
        case_check.start_debug()
    assert rec.debug_calls == 1, "a plan fault must never be retried"
    assert "after one retry" not in str(exc.value)


def test_clean_exit_reporting_cancelled_is_retried_by_run_debug(
    monkeypatch: pytest.MonkeyPatch, _stub_paths: None
) -> None:
    cancelled = (0, json.dumps({"Result": "Success", "Data": {"finalStatus": "Cancelled"}}))
    rec = _Recorder(cancelled, (0, OK_PAYLOAD))
    monkeypatch.setattr(subprocess, "run", rec)
    payload = case_check.run_debug()
    assert payload["finalStatus"] == "Completed"
    assert rec.debug_calls == 2


def test_faulted_is_not_retried_by_run_debug(
    monkeypatch: pytest.MonkeyPatch, _stub_paths: None
) -> None:
    faulted = (0, json.dumps({"Result": "Success", "Data": {"finalStatus": "Faulted"}}))
    rec = _Recorder(faulted, (0, OK_PAYLOAD))
    monkeypatch.setattr(subprocess, "run", rec)
    with pytest.raises(SystemExit):
        case_check.run_debug()
    assert rec.debug_calls == 1, "a Faulted case is the plan's fault"
