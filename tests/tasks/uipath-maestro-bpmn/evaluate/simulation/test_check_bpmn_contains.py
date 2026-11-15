from __future__ import annotations

import subprocess
import sys
from pathlib import Path


CHECKER = Path(__file__).with_name("check_bpmn_contains.py")

BPMN = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Defs_1">
  <bpmn:process id="Process_1">
    <bpmn:startEvent id="Event_start"/>
    <bpmn:serviceTask id="connectorSendEmail" name="Send Email"/>
    <bpmn:task id="agentLookup" name="Agent Lookup"/>
  </bpmn:process>
</bpmn:definitions>
"""


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _write_bpmn(tmp_path: Path) -> None:
    project = tmp_path / "SimEval"
    project.mkdir()
    (project / "SimEval.bpmn").write_text(BPMN, encoding="utf-8")


def test_passes_when_all_ids_present(tmp_path: Path) -> None:
    _write_bpmn(tmp_path)

    result = _run(tmp_path, "--bpmn-name", "SimEval", "agentLookup", "connectorSendEmail")

    assert result.returncode == 0, result.stdout + result.stderr


def test_fails_when_an_id_is_missing(tmp_path: Path) -> None:
    _write_bpmn(tmp_path)

    result = _run(tmp_path, "--bpmn-name", "SimEval", "agentLookup", "missingId")

    assert result.returncode == 1
    assert "missingId" in result.stdout + result.stderr
