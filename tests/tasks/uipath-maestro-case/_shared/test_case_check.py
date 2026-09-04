"""Unit tests for case_check runtime-payload helpers.

Run with ``pytest`` from any directory.

These pin the CLI #2266 contract: the ``uip maestro case debug --output json``
runtime payload must be readable whether its keys are camelCase (the documented
Studio Web shape, and what the CLI emits once case debug opts into
``preserveDataKeys``) or PascalCase (what a #2266-carrying CLI emits without the
opt-out). A checker must not depend on which CLI build the eval image runs.
"""

import os
import json
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from case_check import (  # noqa: E402
    _get_ci,
    collect_outputs,
    find_caseplan,
    find_project_dir,
    find_solution_dir,
    is_non_required,
    partition_return_to_origin_conditions,
    registry_audit_entries,
    run_debug,
)
import case_check  # noqa: E402


def _write_caseplan(path, nodes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"nodes": nodes}), encoding="utf-8")


def _write_case_project(root, solution, project, nodes):
    project_dir = root / solution / project
    _write_caseplan(project_dir / "caseplan.json", nodes)
    (project_dir / "project.uiproj").write_text(
        json.dumps({"ProjectType": "CaseManagement"}), encoding="utf-8"
    )
    (root / solution / f"{solution}.uipx").write_text("{}", encoding="utf-8")
    return project_dir


def test_find_caseplan_prefers_one_substantive_plan_over_scaffold_husk(tmp_path, monkeypatch):
    authored = tmp_path / "Case" / "Case" / "caseplan.json"
    husk = tmp_path / "CaseSolution" / "Case" / "caseplan.json"
    _write_caseplan(authored, [{"id": "trigger"}, {"id": "stage"}])
    _write_caseplan(husk, [{"id": "trigger"}])
    monkeypatch.chdir(tmp_path)

    assert find_caseplan() == os.path.join("Case", "Case", "caseplan.json")


def test_find_caseplan_accepts_identical_packaging_copy(tmp_path, monkeypatch):
    authored = tmp_path / "caseplan.json"
    packaged = tmp_path / "CaseSolution" / "Case" / "caseplan.json"
    nodes = [{"id": "trigger"}, {"id": "stage"}]
    _write_caseplan(authored, nodes)
    _write_caseplan(packaged, nodes)
    monkeypatch.chdir(tmp_path)

    assert find_caseplan() == "caseplan.json"


def test_find_caseplan_rejects_distinct_substantive_plans(tmp_path, monkeypatch):
    _write_caseplan(tmp_path / "First" / "caseplan.json", [{"id": "trigger"}, {"id": "first"}])
    _write_caseplan(tmp_path / "Second" / "caseplan.json", [{"id": "trigger"}, {"id": "second"}])
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit, match="Multiple distinct caseplan.json"):
        find_caseplan()


def test_project_and_solution_discovery_prefer_substantive_case_over_husk(
    tmp_path, monkeypatch, capsys
):
    substantive = _write_case_project(
        tmp_path,
        "Case",
        "Case",
        [{"id": "trigger"}, {"id": "stage"}],
    )
    _write_case_project(
        tmp_path,
        "CaseSolution",
        "Case",
        [{"id": "trigger"}],
    )
    monkeypatch.chdir(tmp_path)

    assert find_project_dir() == os.path.relpath(substantive, tmp_path)
    assert find_solution_dir() == "Case"
    notes = capsys.readouterr().out
    assert "ignoring 1 abandoned Case project scaffold(s)" in notes
    assert "ignoring 1 abandoned Case solution scaffold(s)" in notes


def test_project_discovery_still_refuses_distinct_substantive_cases(
    tmp_path, monkeypatch
):
    _write_case_project(
        tmp_path,
        "FirstSolution",
        "First",
        [{"id": "trigger"}, {"id": "first"}],
    )
    _write_case_project(
        tmp_path,
        "SecondSolution",
        "Second",
        [{"id": "trigger"}, {"id": "second"}],
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit, match="Multiple Case projects match"):
        find_project_dir()
    with pytest.raises(SystemExit, match="Multiple solution manifests match"):
        find_solution_dir()


def test_non_required_accepts_omitted_or_explicit_false():
    assert is_non_required({})
    assert is_non_required({"isRequired": False})


def test_non_required_rejects_required_or_invalid_values():
    assert not is_non_required({"isRequired": True})
    assert not is_non_required({"isRequired": "false"})


def test_registry_audit_entries_accepts_flat_and_named_envelopes():
    entries = [{"task": "Post Invoice"}]

    assert registry_audit_entries(entries) == entries
    assert registry_audit_entries({"resolutions": entries}) == entries
    assert registry_audit_entries({"resources": entries}) == entries


def test_registry_audit_entries_rejects_missing_or_non_object_entries():
    with pytest.raises(SystemExit, match="no resolutions/resources list"):
        registry_audit_entries({"status": "resolved"})
    with pytest.raises(SystemExit, match="entries must be objects"):
        registry_audit_entries({"resources": ["Post Invoice"]})


def test_get_ci_reads_camelcase_and_pascalcase():
    assert _get_ci({"finalStatus": "Completed"}, "finalStatus", "FinalStatus") == "Completed"
    assert _get_ci({"FinalStatus": "Completed"}, "finalStatus", "FinalStatus") == "Completed"
    assert _get_ci({}, "finalStatus", "FinalStatus", default="<none>") == "<none>"


def test_collect_outputs_handles_pascalcase_payload():
    pascal = {
        "Variables": {
            "Globals": {"result": "approved"},
            "GlobalVariables": [{"Name": "score", "Value": 7}],
            "Outputs": [{"Name": "note", "Value": "done"}],
        }
    }
    out = collect_outputs(pascal)
    assert "approved" in out
    assert 7 in out
    assert "done" in out


def test_collect_outputs_walks_pascalcase_runtime_task():
    """Task executions nested under PascalCase keys must still yield outputs."""
    pascal = {
        "Stages": [
            {
                "Tasks": [
                    {"DisplayName": "Triage", "Type": "rpa", "Outputs": [{"Value": "ok"}]}
                ]
            }
        ]
    }
    assert "ok" in collect_outputs(pascal)


def test_collect_outputs_pascalcase_matches_camelcase():
    camel = {"variables": {"globals": {"a": "x"}, "globalVariables": [{"value": 1}]}}
    pascal = {"Variables": {"Globals": {"a": "x"}, "GlobalVariables": [{"Value": 1}]}}
    assert sorted(map(str, collect_outputs(camel))) == sorted(map(str, collect_outputs(pascal)))


def test_return_to_origin_partition_checks_every_return_condition():
    valid_required = {
        "type": "return-to-origin",
        "marksStageComplete": True,
        "rules": [[{"rule": "required-tasks-completed"}]],
    }
    valid_connector = {
        "type": "return-to-origin",
        "marksStageComplete": True,
        "rules": [[{"rule": "wait-for-connector"}]],
    }
    malformed = {
        "type": "return-to-origin",
        "marksStageComplete": False,
        "rules": [[{"rule": "selected-tasks-completed"}]],
    }
    malformed_extra_rule = {
        "type": "return-to-origin",
        "marksStageComplete": True,
        "rules": [[
            {"rule": "required-tasks-completed"},
            {"rule": "selected-tasks-completed"},
        ]],
    }

    returns, invalid = partition_return_to_origin_conditions(
        [valid_required, valid_connector, malformed, malformed_extra_rule]
    )

    assert returns == [
        valid_required,
        valid_connector,
        malformed,
        malformed_extra_rule,
    ]
    assert invalid == [malformed, malformed_extra_rule]


def test_run_debug_gate_accepts_pascalcase_finalstatus(monkeypatch):
    """run_debug's Completed gate must pass on a PascalCase payload (the exact
    #2266 break that made case debug look like it 'did not complete')."""
    monkeypatch.setattr(case_check, "start_debug", lambda **kw: {"FinalStatus": "Completed"})
    assert run_debug() == {"FinalStatus": "Completed"}


def test_run_debug_gate_still_rejects_incomplete(monkeypatch):
    monkeypatch.setattr(case_check, "start_debug", lambda **kw: {"FinalStatus": "Faulted"})
    with pytest.raises(SystemExit, match="Case did not complete"):
        run_debug()


def test_timeout_reports_fail_not_traceback(monkeypatch):
    """A CLI that outruns its timeout must exit FAIL, with the partial output.

    ``TimeoutExpired`` carries bytes even under ``text=True`` on POSIX, so the
    handler has to decode before formatting.
    """
    def timing_out(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw["timeout"], output=b"half a payload\xff")

    monkeypatch.setattr(case_check.subprocess, "run", timing_out)
    with pytest.raises(SystemExit) as excinfo:
        case_check.assert_validate_passes("caseplan.json", timeout=7)

    msg = str(excinfo.value)
    assert "uip maestro case validate timed out after 7s" in msg
    assert "half a payload" in msg
