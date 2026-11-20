"""Guard: a `case debug` poll timeout is followed to a verdict, not failed.

The CLI gives up polling at 600s and exits non-zero with a timeout envelope
that names only the instance. The instance keeps running, so the grader follows
it within its own budget (round 11, io_binding).

    python3 -m pytest tests/tasks/uipath-maestro-case/_shared/test_case_check_debug_follow.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SUITE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SUITE))
sys.path.insert(0, str(SUITE / "_setup"))

import case_run  # noqa: E402
from _shared import case_check, case_run_path  # noqa: E402

INSTANCE = "62c2f4e5-0000-4000-8000-000000000001"
TIMEOUT_ENVELOPE = json.dumps({
    "Result": "Failure",
    "Message": f"Debug polling timed out after 600s — instance {INSTANCE} was still Running",
    "Code": "timeout",
    "Data": {"instanceId": INSTANCE},
})
ROWS = [{"elementId": "t1", "elementType": "ServiceTask", "status": "Completed"}]


@pytest.fixture
def debug(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    project = tmp_path / "Case"
    project.mkdir()
    monkeypatch.setattr(case_check.os.path, "isdir", lambda path: path == "/solution")
    monkeypatch.setattr(case_check, "find_project_dir", lambda *a, **k: str(project))
    monkeypatch.setattr(
        case_check, "_run",
        lambda cmd, timeout=0, what="": subprocess.CompletedProcess(cmd, 1, TIMEOUT_ENVELOPE, ""),
    )
    monkeypatch.setattr(case_check.time, "sleep", lambda s: None)
    monkeypatch.setattr(case_run, "instance_executions", lambda i: ROWS)
    monkeypatch.setattr(case_run, "instance_incidents", lambda i: [])


def _statuses(monkeypatch: pytest.MonkeyPatch, seq: list[str]) -> None:
    items = iter(seq)
    monkeypatch.setattr(case_run, "instance_status", lambda i: next(items, seq[-1]))


def test_instance_that_completes_passes(debug, monkeypatch) -> None:
    _statuses(monkeypatch, ["Running", "Running", "Completed"])

    payload = case_check.run_debug(timeout=900)

    assert payload["finalStatus"] == "Completed"
    assert payload["instanceId"] == INSTANCE
    assert payload["elementExecutions"] == ROWS


def test_instance_that_faults_fails_with_its_reason(debug, monkeypatch) -> None:
    _statuses(monkeypatch, ["Running", "Faulted"])
    monkeypatch.setattr(case_run, "instance_incidents", lambda i: [
        {"errorCode": "E1", "errorMessage": "boom", "elementId": "t1"}])

    with pytest.raises(SystemExit) as raised:
        case_check.run_debug(timeout=900)

    assert "incident [E1] boom (element t1)" in str(raised.value)


def test_instance_never_terminal_fails_naming_it(debug, monkeypatch) -> None:
    _statuses(monkeypatch, ["Running"])
    clock = iter(range(0, 100000, 400))
    monkeypatch.setattr(case_check.time, "monotonic", lambda: next(clock))

    with pytest.raises(SystemExit) as raised:
        case_check.run_debug(timeout=900)

    message = str(raised.value)
    assert INSTANCE in message and "still Running after 900s" in message


def test_a_timeout_without_an_instance_is_not_followed() -> None:
    assert case_check._debug_poll_timeout(json.dumps(
        {"Result": "Failure", "Message": "timed out", "Data": {}})) is None


def test_path_failures_name_the_incidents(monkeypatch) -> None:
    monkeypatch.setattr(case_run_path, "instance_incidents", lambda i: [
        {"errorCode": "E1", "errorMessage": "boom", "elementId": "t1"}])
    path = {"opening": [{"id": "S1"}], "automated": [], "human": [], "next": [],
            "required_ids": set()}
    run = {"status": "Faulted", "instance_id": INSTANCE, "executions": []}

    assert "incident [E1] boom (element t1)" in case_run_path.path_failures(path, run)


def test_path_failures_skip_incidents_for_a_parked_run(monkeypatch) -> None:
    monkeypatch.setattr(case_run_path, "instance_incidents", lambda i: pytest.fail("read"))
    path = {"opening": [{"id": "S1"}], "automated": [], "human": [], "next": [],
            "required_ids": set()}

    case_run_path.path_failures(path, {"status": "Suspended", "instance_id": INSTANCE, "executions": []})
