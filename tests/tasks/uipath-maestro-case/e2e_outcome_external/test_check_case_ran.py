"""Guard: check_case_ran.py prints the incident when the case does not complete.

Run with synthetic `debug_result.json` contents, so no tenant is touched
(UiPath/skills#4215).

    uvx --with pyyaml pytest tests/tasks/uipath-maestro-case/e2e_outcome_external/test_check_case_ran.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


check_case_ran = _load("check_case_ran_under_test", HERE / "check_case_ran.py")
import outcome_probe  # noqa: E402  (on sys.path once check_case_ran is loaded)

FAULTED = {
    "envelope": {"Result": "Success", "Code": "CaseDebug",
                 "Instructions": "Debug completed with status: Faulted"},
    "data": {
        "finalStatus": "Faulted",
        "elementExecutions": [
            {"elementId": "tJ2dcRjxB", "elementType": "SendTask", "status": "Failed"},
        ],
    },
    "stderr_tail": ("[WARN] Debug session faulted with 1 incident(s). "
                    "First: [ConnectorError] mail send refused (element tJ2dcRjxB)\n"),
    "debug_started_at": "2026-10-22T22:49:00+00:00",
}


def test_faulted_run_prints_incident_and_element(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_case_ran, "ensure_debug_ran", lambda: FAULTED)
    with pytest.raises(SystemExit) as exc:
        check_case_ran.main()
    message = str(exc.value)
    assert message.startswith("FAIL: case did not complete (finalStatus=Faulted)")
    assert "incident [ConnectorError] mail send refused (element tJ2dcRjxB)" in message
    assert "element tJ2dcRjxB (SendTask) Failed" in message


def test_result_without_stderr_tail_still_names_the_element(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A debug_result.json written before this change has no stderr_tail."""
    old = {k: v for k, v in FAULTED.items() if k != "stderr_tail"}
    monkeypatch.setattr(check_case_ran, "ensure_debug_ran", lambda: old)
    with pytest.raises(SystemExit) as exc:
        check_case_ran.main()
    assert "element tJ2dcRjxB (SendTask) Failed" in str(exc.value)


def test_completed_run_passes(monkeypatch: pytest.MonkeyPatch,
                              capsys: pytest.CaptureFixture[str]) -> None:
    done = {**FAULTED, "data": {"finalStatus": "Completed"}}
    monkeypatch.setattr(check_case_ran, "ensure_debug_ran", lambda: done)
    assert check_case_ran.main() == 0
    assert "OK: case executed to finalStatus=Completed" in capsys.readouterr().out


def test_probe_keeps_the_debug_stderr(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """outcome_probe stores the CLI's stderr tail, where the incident WARN line is."""
    probe = outcome_probe
    calls = []

    def fake(args, timeout=180):  # noqa: ANN001
        calls.append(args)
        if args[:2] == ["solution", "resources"]:
            return {"Result": "Success"}, ""
        return ({"Result": "Success", "Code": "CaseDebug",
                 "Data": {"finalStatus": "Faulted"}}, "x" * 9000 + "WARN tail")

    monkeypatch.setattr(probe, "_find_dir", lambda pattern: str(tmp_path))
    monkeypatch.setattr(probe, "_uip_json_and_stderr", fake)
    monkeypatch.setattr(probe, "_uip_json", lambda args, timeout=180: fake(args, timeout)[0])
    result = probe._do_debug("2026-10-22T22:49:00")
    assert result["stderr_tail"].endswith("WARN tail")
    assert len(result["stderr_tail"]) == probe.STDERR_TAIL_CHARS
    assert result["data"]["finalStatus"] == "Faulted"
