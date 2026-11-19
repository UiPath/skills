#!/usr/bin/env python3
"""Unit tests for write_validate_warnings.py. Stdlib and pytest only."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("write_validate_warnings", HERE / "write_validate_warnings.py")
assert SPEC and SPEC.loader
writer = importlib.util.module_from_spec(SPEC)
sys.modules["write_validate_warnings"] = writer
SPEC.loader.exec_module(writer)

WARNINGS = "1 warning(s):\n  - [Task_a] VARIABLE_NOT_SET: Variable 'Order Total' is not set at this point in the flow"


def _validate_prints(monkeypatch: pytest.MonkeyPatch, stdout: str) -> None:
    def fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(writer.subprocess, "run", fake_run)


def _write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "warnings.txt"
    monkeypatch.setattr(sys, "argv", ["write_validate_warnings.py", str(out)])
    assert writer.main() == 0
    return out.read_text(encoding="utf-8")


def test_lists_the_warnings_of_each_built_process(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "LoyaltyDiscount.bpmn").write_text("<bpmn:definitions/>")
    _validate_prints(monkeypatch, json.dumps({"Result": "Success", "Data": {"Status": "Valid", "Warnings": WARNINGS}}))

    assert _write(tmp_path, monkeypatch) == f"LoyaltyDiscount.bpmn:\n{WARNINGS.splitlines()[1].strip()}"


def test_writes_none_when_validate_reports_no_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "LoyaltyDiscount.bpmn").write_text("<bpmn:definitions/>")
    _validate_prints(monkeypatch, json.dumps({"Result": "Success", "Data": {"Status": "Valid"}}))

    assert _write(tmp_path, monkeypatch) == writer.NO_WARNINGS


def test_unparseable_validate_output_is_unknown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "LoyaltyDiscount.bpmn").write_text("<bpmn:definitions/>")
    _validate_prints(monkeypatch, "not json")

    assert _write(tmp_path, monkeypatch).startswith(writer.UNKNOWN)


def test_failed_validate_lists_the_warnings_from_instructions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "LoyaltyDiscount.bpmn").write_text("<bpmn:definitions/>")
    instructions = "Found 1 error(s):\n  - [warning] [Task_a] VARIABLE_NOT_SET: x\n  - [error] [Gateway_1] MISSING_CONDITION_EXPRESSION: y"
    _validate_prints(monkeypatch, json.dumps({"Result": "Failure", "Instructions": instructions}))

    assert _write(tmp_path, monkeypatch) == "LoyaltyDiscount.bpmn:\n- [warning] [Task_a] VARIABLE_NOT_SET: x"


@pytest.mark.parametrize("error", [FileNotFoundError("uip"), subprocess.TimeoutExpired("uip", 60)])
def test_validate_that_cannot_run_is_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    (tmp_path / "LoyaltyDiscount.bpmn").write_text("<bpmn:definitions/>")

    def raising_run(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(writer.subprocess, "run", raising_run)

    assert _write(tmp_path, monkeypatch).startswith(writer.UNKNOWN)


def test_parser_note_on_compiled_output_is_left_out(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "ScriptDemo.bpmn").write_text("<bpmn:definitions/>")
    warnings = "1 warning(s):\n  - [(xml)] unknown attribute <type>"
    _validate_prints(monkeypatch, json.dumps({"Result": "Success", "Data": {"Warnings": warnings}}))

    assert _write(tmp_path, monkeypatch) == writer.NO_WARNINGS


def test_no_built_process_is_unknown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert _write(tmp_path, monkeypatch).startswith(writer.UNKNOWN)


@pytest.mark.parametrize(
    "instructions",
    [
        "Could not read file: LoyaltyDiscount.bpmn",
        "Found 1 error(s):\n  - [error] [(xml)] XML_NOT_WELL_FORMED: unexpected end of file",
        "Found 1 error(s):\n  - [warning] [(xml)] unresolved reference <X>\n  - [error] [(xml)] BPMN_PARSE_ERROR: bad",
    ],
)
def test_validate_that_stops_before_its_rules_is_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, instructions: str
) -> None:
    (tmp_path / "LoyaltyDiscount.bpmn").write_text("<bpmn:definitions/>")
    _validate_prints(monkeypatch, json.dumps({"Result": "Failure", "Instructions": instructions}))

    assert _write(tmp_path, monkeypatch).startswith(writer.UNKNOWN)


def _warnings_judge() -> dict:
    task = yaml.safe_load((HERE / "auto_build_final_report.yaml").read_text(encoding="utf-8"))
    judges = [
        c for c in task["success_criteria"]
        if c["type"] == "llm_judge" and ".validate-warnings.txt" in c.get("files", [])
    ]
    assert len(judges) == 1
    return judges[0]


def test_judge_reads_what_the_writer_writes() -> None:
    command = next(
        c["command"] for c in yaml.safe_load((HERE / "auto_build_final_report.yaml").read_text())["success_criteria"]
        if c["type"] == "run_command" and "write_validate_warnings.py" in c["command"]
    )
    assert command.endswith(" .validate-warnings.txt")
    assert _warnings_judge()["files"] == [".validate-warnings.txt"]


def test_clean_report_rule_allows_a_value_assumption() -> None:
    prompt = " ".join(_warnings_judge()["prompt"].split())
    assert "presents something as a `validate` warning or validator finding" in prompt
    assert "a missing order total counts as 0" in prompt
    assert f"starts with `{writer.UNKNOWN}`, score 0.0" in prompt
