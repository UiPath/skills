"""caseplan discovery across the two authoring layouts, and the task-YAML CLI.

CLI: ``<Solution>/<Project>/caseplan.json``. Studio Web export:
``<Project>/caseplan.case`` (same JSON body), no solution wrapper.
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import case_check  # noqa: E402
from case_check import find_caseplan, main  # noqa: E402

PLAN = json.dumps({"nodes": [{"id": "t", "type": "case-management:Trigger"}, {"id": "s1", "type": "stage"}]})


def test_cli_layout_still_preferred(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj = tmp_path / "AgedSol" / "Aged"
    proj.mkdir(parents=True)
    (proj / "caseplan.json").write_text(PLAN)

    assert find_caseplan() == os.path.join("AgedSol", "Aged", "caseplan.json")


def test_studio_web_caseplan_case_is_discovered_when_no_json_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj = tmp_path / "Aged"
    proj.mkdir()
    (proj / "caseplan.case").write_text(PLAN)

    assert find_caseplan() == os.path.join("Aged", "caseplan.case")


def test_explicit_pattern_does_not_fall_back(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Aged").mkdir()
    (tmp_path / "Aged" / "caseplan.case").write_text(PLAN)

    with pytest.raises(SystemExit):
        find_caseplan("Aged/caseplan.json")


def test_cli_locate_prints_the_discovered_path(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Aged").mkdir()
    (tmp_path / "Aged" / "caseplan.case").write_text(PLAN)

    assert main(["locate"]) == 0
    assert capsys.readouterr().out.strip() == os.path.join("Aged", "caseplan.case")


def test_cli_validate_runs_uip_on_the_discovered_plan(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Aged").mkdir()
    (tmp_path / "Aged" / "caseplan.case").write_text(PLAN)
    seen = {}

    def fake_run(cmd, *, timeout, what):
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="{}", stderr="")

    monkeypatch.setattr(case_check, "_run", fake_run)

    assert main(["validate"]) == 0
    assert seen["cmd"][:4] == ["uip", "maestro", "case", "validate"]
    assert seen["cmd"][4] == os.path.join("Aged", "caseplan.case")
    assert "OK: uip maestro case validate passed" in capsys.readouterr().out


def test_cli_validate_propagates_a_failing_validate(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Aged").mkdir()
    (tmp_path / "Aged" / "caseplan.json").write_text(PLAN)
    monkeypatch.setattr(
        case_check,
        "_run",
        lambda cmd, *, timeout, what: subprocess.CompletedProcess(cmd, 1, stdout="", stderr="bad plan"),
    )

    assert main(["validate"]) == 1
    assert "bad plan" in capsys.readouterr().err


def test_cli_reports_a_missing_plan_as_a_fail_not_a_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    assert main(["validate"]) == 1
    assert "FAIL: No caseplan.json found" in capsys.readouterr().err


def test_cli_usage(capsys):
    assert main([]) == 2
    assert main(["frobnicate"]) == 2
