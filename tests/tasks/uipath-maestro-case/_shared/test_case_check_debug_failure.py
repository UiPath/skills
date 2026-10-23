"""Guard: a `case debug` that does not complete says WHY in the FAIL message.

`uip maestro case debug --output json` drops the incidents of a faulted run
(UiPath/cli#5519). The CLI names the first one only in a stderr WARN line, and
the harness deletes the debug solution afterwards — so unless the checker prints
the incident, a fault cannot be diagnosed without a live rerun (UiPath/skills#4215).

    uvx --with pyyaml pytest tests/tasks/uipath-maestro-case/_shared/test_case_check_debug_failure.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import case_check  # noqa: E402

# Shape of the real Data object from run adhoc-2026-10-22_19-29-29
# (skill-case-e2e-outcome-external, v2), trimmed to the rows that matter.
FAULTED_DATA = {
    "instanceId": "369171be-2d8c-458e-a6ae-c29489287211",
    "finalStatus": "Faulted",
    "elementExecutions": [
        {"elementId": "trigger_1", "elementType": "StartEvent", "status": "Completed"},
        {"elementId": "Stage_DHFjiy", "elementType": "CaseStage", "status": "InProgress"},
        {"elementId": "tJ2dcRjxB", "elementType": "SendTask", "status": "Failed"},
    ],
}

# The WARN line maestro-sdk's resolveFaultIncidents logs on stderr.
WARN = (
    "[WARN] Debug session faulted with 2 incident(s). "
    "First: [ConnectorError] Request failed with status 400 (element tJ2dcRjxB)\n"
)


def test_completed_run_has_no_failure_lines() -> None:
    assert case_check.debug_failure_lines({"finalStatus": "Completed"}, WARN) == []


def test_data_incidents_win() -> None:
    """Once the CLI inlines `Data.incidents` (as flow debug does), use them."""
    data = {
        **FAULTED_DATA,
        "incidents": [
            {"errorCode": "E1", "errorMessage": "boom", "elementId": "tJ2dcRjxB"},
            {"errorCode": None, "errorMessage": "second"},
        ],
    }
    assert case_check.debug_failure_lines(data, WARN) == [
        "incident [E1] boom (element tJ2dcRjxB)",
        "incident [no-code] second",
        "element tJ2dcRjxB (SendTask) Failed",
    ]


def test_stderr_warn_line_when_data_has_none() -> None:
    assert case_check.debug_failure_lines(FAULTED_DATA, WARN) == [
        "incident [ConnectorError] Request failed with status 400 "
        "(element tJ2dcRjxB) (first of 2)",
        "element tJ2dcRjxB (SendTask) Failed",
    ]


def test_stderr_incidents_json_line_beats_the_warn_summary() -> None:
    listed = [{"errorCode": "C9", "errorMessage": "full text", "elementId": "tJ2dcRjxB"}]
    stderr = f"[INFO] Incidents: {json.dumps(listed)}\n{WARN}"
    assert case_check.debug_failure_lines(FAULTED_DATA, stderr)[0] == (
        "incident [C9] full text (element tJ2dcRjxB)"
    )


def test_failed_elements_alone_when_no_incident_text() -> None:
    """Today's debug_result.json: no incidents anywhere, but the element is named."""
    assert case_check.debug_failure_lines(FAULTED_DATA) == [
        "element tJ2dcRjxB (SendTask) Failed",
    ]


def test_nothing_known_still_says_so() -> None:
    assert case_check.debug_failure_lines({"finalStatus": "Faulted"}) == [
        "no incident or failed element in the debug output (finalStatus=Faulted)",
    ]


def test_accepts_the_whole_envelope_and_pascal_case() -> None:
    envelope = {"Result": "Success", "Data": {
        "FinalStatus": "Faulted",
        "ElementExecutions": [{"ElementId": "t1", "ElementType": "Task", "Status": "Faulted"}],
    }}
    assert case_check.debug_failure_lines(envelope) == ["element t1 (Task) Faulted"]


def test_start_debug_fail_message_leads_with_the_reason(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A Faulted run exits 1 with a Success envelope on stdout and the WARN on stderr."""
    monkeypatch.setattr(case_check, "find_project_dir", lambda *a, **k: str(tmp_path))
    monkeypatch.setattr(case_check, "find_solution_dir", lambda *a, **k: str(tmp_path))
    stdout = json.dumps({"Result": "Success", "Code": "CaseDebug", "Data": FAULTED_DATA})

    def fake_run(cmd, **kwargs):  # noqa: ANN001, ANN003
        if "debug" in cmd:
            return subprocess.CompletedProcess(cmd, 1, stdout, "lots of debug noise\n" + WARN)
        return subprocess.CompletedProcess(cmd, 0, "{}", "")

    monkeypatch.setattr(case_check.subprocess, "run", fake_run)
    with pytest.raises(SystemExit) as exc:
        case_check.start_debug()
    message = str(exc.value)
    why = message.index("incident [ConnectorError]")
    assert why < message.index("stdout:"), message
    assert "element tJ2dcRjxB (SendTask) Failed" in message
