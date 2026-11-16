#!/usr/bin/env python3
"""Unit tests for write_validate_warnings.py. Stdlib and pytest only."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

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
    _validate_prints(monkeypatch, json.dumps({"Data": {"Status": "Valid", "Warnings": WARNINGS}}))

    assert _write(tmp_path, monkeypatch) == f"LoyaltyDiscount.bpmn:\n{WARNINGS}"


def test_writes_none_when_validate_reports_no_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "LoyaltyDiscount.bpmn").write_text("<bpmn:definitions/>")
    _validate_prints(monkeypatch, json.dumps({"Data": {"Status": "Valid"}}))

    assert _write(tmp_path, monkeypatch) == writer.NO_WARNINGS


def test_unparseable_validate_output_lists_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "LoyaltyDiscount.bpmn").write_text("<bpmn:definitions/>")
    _validate_prints(monkeypatch, "not json")

    assert _write(tmp_path, monkeypatch) == writer.NO_WARNINGS
