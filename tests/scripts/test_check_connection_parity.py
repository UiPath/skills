"""
Behaviour tests for scripts/check_connection_parity.py: a Maestro Case solution
must declare every connector its caseplan calls as a solution resource.

Each test builds a small solution tree in tmp_path and asserts the exit code and
the message the author sees.

Run from repo root:
    pytest tests/scripts/test_check_connection_parity.py
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_connection_parity.py"

_spec = importlib.util.spec_from_file_location("check_connection_parity_behaviour", SCRIPT)
parity = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parity)


def binding(connection_id, attribute="ConnectionId"):
    return {"resource": "Connection", "propertyAttribute": attribute, "default": connection_id}


def make_solution(root, *, connection_ids=(), sidecar_keys=None, emitted=(), plan_extra=None, plan_name="caseplan.json"):
    """root/proj with a caseplan, an optional bindings_v2.json and emitted connection resources."""
    project = root / "proj"
    project.mkdir(parents=True)
    plan = {"bindings": [b for cid in connection_ids for b in (binding(cid), binding("folder", "folderKey"))]}
    plan.update(plan_extra or {})
    (project / plan_name).write_text(json.dumps(plan), encoding="utf-8")
    if sidecar_keys is not None:
        resources = [{"resource": "Connection", "key": k} for k in sidecar_keys]
        (project / "bindings_v2.json").write_text(json.dumps({"resources": resources}), encoding="utf-8")
    for folder, connector, name in emitted:
        target = root / "resources" / folder / "connection" / connector
        target.mkdir(parents=True, exist_ok=True)
        (target / f"{name}.json").write_text("{}", encoding="utf-8")
    return root


def run_check(solution, quiet=False):
    return parity.check(str(solution), quiet=quiet)


def test_consistent_solution_passes_and_reports_the_four_counts(tmp_path, capsys):
    solution = make_solution(
        tmp_path,
        connection_ids=["c1"],
        sidecar_keys=["c1"],
        emitted=[("Shared", "uipath-slack", "main")],
        plan_extra={"steps": [{"connectorKey": "uipath-slack"}]},
    )
    assert run_check(solution) == 0
    out = capsys.readouterr().out
    assert "caseplan connections   A = 1" in out
    assert "bindings_v2 entries    B = 1" in out
    assert "emitted resources      C = 1  ['uipath-slack']" in out
    assert "connectorKeys called   D = 1  ['uipath-slack']" in out
    assert "OK: every connector the case calls is declared as a solution resource" in out


def test_quiet_run_prints_nothing_on_success(tmp_path, capsys):
    solution = make_solution(tmp_path, connection_ids=["c1"], sidecar_keys=["c1"], emitted=[("S", "uipath-slack", "m")])
    assert run_check(solution, quiet=True) == 0
    assert capsys.readouterr().out == ""


def test_directory_without_a_caseplan_is_skipped(tmp_path, capsys):
    (tmp_path / "proj").mkdir()
    assert run_check(tmp_path) == 0
    assert "SKIP: no case plan" in capsys.readouterr().out
    assert run_check(tmp_path, quiet=True) == 0
    assert capsys.readouterr().out == ""


def test_missing_solution_directory_is_skipped(tmp_path, capsys):
    assert run_check(tmp_path / "absent") == 0
    assert "SKIP: no case plan" in capsys.readouterr().out


def test_caseplan_connection_missing_from_the_sidecar_blocks(tmp_path, capsys):
    solution = make_solution(tmp_path, connection_ids=["c1"])
    assert run_check(solution) == 1
    out = capsys.readouterr().out
    assert "(bindings_v2.json absent)" in out
    assert "BLOCKED: connector(s) referenced by the case are not declared as solution resources" in out
    assert "proj: caseplan declares 1 connection(s) but bindings_v2.json has 0" in out


def test_sidecar_entry_without_an_emitted_file_blocks(tmp_path, capsys):
    solution = make_solution(tmp_path, connection_ids=["c1"], sidecar_keys=["c1"])
    assert run_check(solution) == 1
    out = capsys.readouterr().out
    assert "bindings_v2.json has 1 Connection entry(ies) but 0 resource file(s) on disk" in out
    assert "uip solution resources refresh" in out


def test_called_connector_with_no_emitted_resource_blocks(tmp_path, capsys):
    solution = make_solution(tmp_path, plan_extra={"steps": [{"connectorKey": "uipath-jira"}]})
    assert run_check(solution) == 1
    assert "proj: caseplan calls connector 'uipath-jira' with no emitted resource under resources/*/connection/uipath-jira/" in capsys.readouterr().out


def test_connector_key_in_a_task_context_array_is_found(tmp_path, capsys):
    plan_extra = {"tasks": [{"context": [{"name": "connectorKey", "value": "uipath-gmail"}]}]}
    solution = make_solution(tmp_path, plan_extra=plan_extra)
    assert run_check(solution) == 1
    assert "calls connector 'uipath-gmail'" in capsys.readouterr().out


def test_connector_key_inside_an_escaped_json_string_is_found(tmp_path, capsys):
    plan_extra = {"payload": json.dumps({"connectorKey": "uipath-box"})}
    solution = make_solution(tmp_path, plan_extra=plan_extra)
    assert run_check(solution) == 1
    assert "calls connector 'uipath-box'" in capsys.readouterr().out


def test_placeholder_connector_key_needs_no_resource(tmp_path, capsys):
    solution = make_solution(tmp_path, plan_extra={"steps": [{"connectorKey": "placeholder"}]})
    assert run_check(solution) == 0
    assert "connectorKeys called   D = 0" in capsys.readouterr().out


def test_newest_plan_name_wins_within_a_project(tmp_path, capsys):
    solution = make_solution(tmp_path, plan_name="caseplan.case", plan_extra={"steps": [{"connectorKey": "uipath-new"}]})
    (solution / "proj" / "caseplan.json").write_text(json.dumps({"steps": [{"connectorKey": "uipath-old"}]}), encoding="utf-8")
    assert run_check(solution) == 1
    out = capsys.readouterr().out
    assert "uipath-new" in out
    assert "uipath-old" not in out


def test_every_project_in_the_solution_is_checked(tmp_path, capsys):
    solution = make_solution(tmp_path, connection_ids=["c1"], sidecar_keys=["c1"], emitted=[("S", "uipath-slack", "m")])
    other = solution / "other"
    other.mkdir()
    (other / "caseplan.json").write_text(json.dumps({"steps": [{"connectorKey": "uipath-jira"}]}), encoding="utf-8")
    assert run_check(solution) == 1
    out = capsys.readouterr().out
    assert "other: caseplan calls connector 'uipath-jira'" in out
    assert "proj: " not in out.split("BLOCKED")[1]


def test_invalid_caseplan_json_exits_with_the_path(tmp_path):
    solution = make_solution(tmp_path)
    (solution / "proj" / "caseplan.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        run_check(solution)
    assert "caseplan.json is not valid JSON" in str(exc.value)


def test_invalid_sidecar_json_exits_with_the_path(tmp_path):
    solution = make_solution(tmp_path)
    (solution / "proj" / "bindings_v2.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        run_check(solution)
    assert "bindings_v2.json is not valid JSON" in str(exc.value)


def test_cli_exit_codes_and_usage(tmp_path):
    clean = make_solution(tmp_path / "clean", connection_ids=["c1"], sidecar_keys=["c1"], emitted=[("S", "uipath-slack", "m")])
    broken = make_solution(tmp_path / "broken", plan_extra={"steps": [{"connectorKey": "uipath-jira"}]})

    def cli(*args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False)

    ok = cli(str(clean), "--quiet")
    assert (ok.returncode, ok.stdout) == (0, "")

    bad = cli(str(broken))
    assert bad.returncode == 1
    assert "BLOCKED" in bad.stdout

    usage = cli()
    assert usage.returncode == 2
    assert "check_connection_parity.py <solutionDir> [--quiet]" in usage.stderr
