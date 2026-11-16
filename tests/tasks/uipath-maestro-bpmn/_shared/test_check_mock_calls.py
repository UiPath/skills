"""check_mock_calls.py grades the mock dispatcher's call log, run as the YAML runs it.

The log lines below are the real ones R14 v2 left in `mocks/.calls.jsonl` for
diagnose-stuck-gateway and operate-diagnose-minimal-fault-triage, where the agent
issued its reads from a shell `for` loop and a transcript regex missed every one
(builder-sdk#1882). Each task's patterns are read from its YAML, so a pattern edit
is exercised here before an eval run sees it.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_SHARED = Path(__file__).resolve().parent
_SUITE = _SHARED.parent
_SCRIPT = _SHARED / "check_mock_calls.py"


def _record(args: str, rule: str | None, exit_code: int = 0) -> str:
    return json.dumps(
        {
            "ts": 0,
            "args": args,
            "matched_rule": rule,
            "fixture": None,
            "exit_code": exit_code,
            **({} if rule else {"error": "unmocked_default"}),
        }
    )


# R14 v2 diagnose-stuck-gateway, verbatim but for timestamps.
STUCK_GATEWAY_LOG = [
    _record("maestro bpmn --help", None, 1),
    _record("maestro bpmn instance get inst-triage-001 -f folder-public --output json", None, 1),
    _record(
        "maestro bpmn instance element-executions inst-triage-001 -f folder-public --output json",
        "instance element-executions inst-triage-001 -f folder-public",
    ),
    _record(
        "maestro bpmn instance cursors inst-triage-001 -f folder-public --output json",
        "instance cursors inst-triage-001 -f folder-public",
    ),
]

# R14 v2 operate-diagnose-minimal-fault-triage, verbatim but for timestamps.
FAULT_TRIAGE_LOG = [
    _record(
        "maestro bpmn job status job-triage-001 --folder-key folder-public --output json",
        "maestro bpmn job status job-triage-001",
    ),
    _record(
        "maestro bpmn instance incidents inst-triage-001 -f folder-public --output json",
        "maestro bpmn instance incidents inst-triage-001",
    ),
    _record(
        "maestro bpmn instance variables inst-triage-001 -f folder-public --output json",
        "maestro bpmn instance variables inst-triage-001",
    ),
    _record(
        "maestro bpmn instance asset inst-triage-001 -f folder-public --output json",
        "maestro bpmn instance asset inst-triage-001",
    ),
]


def _criteria(task: str) -> list[dict]:
    data = yaml.safe_load((_SUITE / task).read_text(encoding="utf-8"))
    return [
        c
        for c in data["success_criteria"]
        if c["type"] == "run_command" and "check_mock_calls.py" in c["command"]
    ]


def _run(command: str, cwd: Path) -> subprocess.CompletedProcess:
    argv = shlex.split(command.replace("$REFERENCE_DIR", str(_SUITE)))
    assert argv[0] == "python3"
    return subprocess.run([sys.executable, *argv[1:]], cwd=cwd, capture_output=True, text=True)


def _sandbox(tmp_path: Path, lines: list[str]) -> Path:
    (tmp_path / "mocks").mkdir()
    (tmp_path / "mocks" / ".calls.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    ("task", "log", "count"),
    [
        ("diagnose/stuck_gateway/stuck_gateway.yaml", STUCK_GATEWAY_LOG, 2),
        ("operate-diagnose/minimal_fault_triage.yaml", FAULT_TRIAGE_LOG, 4),
    ],
)
def test_every_read_passes_on_the_loop_runs_log(tmp_path, task, log, count) -> None:
    criteria = _criteria(task)
    assert len(criteria) == count
    sandbox = _sandbox(tmp_path, log)
    for criterion in criteria:
        proc = _run(criterion["command"], sandbox)
        assert proc.returncode == 0, (criterion["description"], proc.stderr)


@pytest.mark.parametrize(
    ("task", "args", "rule"),
    [
        # Folder context is part of what is graded: the manifest answers a read
        # without one, and that must not pass.
        (
            "diagnose/stuck_gateway/stuck_gateway.yaml",
            "maestro bpmn instance cursors inst-triage-001 --output json",
            "instance cursors inst-triage-001",
        ),
        (
            "operate-diagnose/minimal_fault_triage.yaml",
            "maestro bpmn instance incidents inst-triage-001 --output json",
            "maestro bpmn instance incidents inst-triage-001",
        ),
        # A wrong folder.
        (
            "operate-diagnose/minimal_fault_triage.yaml",
            "maestro bpmn instance incidents inst-triage-001 -f folder-public-2",
            "maestro bpmn instance incidents inst-triage-001",
        ),
    ],
)
def test_a_read_without_folder_context_fails(tmp_path, task, args, rule) -> None:
    sandbox = _sandbox(tmp_path, [_record(args, rule)])
    verb = re.search(r"instance (\S+)", args).group(1)
    criterion = next(c for c in _criteria(task) if f"instance {verb} " in c["command"])
    assert _run(criterion["command"], sandbox).returncode == 1


def test_an_unmocked_or_failed_call_does_not_count(tmp_path) -> None:
    args = "maestro bpmn instance cursors inst-triage-001 -f folder-public"
    sandbox = _sandbox(
        tmp_path,
        [_record(args, None, 1), _record(args, "instance cursors inst-triage-001", 1)],
    )
    criterion = next(
        c for c in _criteria("diagnose/stuck_gateway/stuck_gateway.yaml") if "cursors" in c["command"]
    )
    assert _run(criterion["command"], sandbox).returncode == 1


def test_a_missing_log_fails(tmp_path) -> None:
    proc = _run(f"python3 $REFERENCE_DIR/_shared/check_mock_calls.py '^maestro'", tmp_path)
    assert proc.returncode == 1
    assert "no served call" in proc.stderr
