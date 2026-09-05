"""Unit tests for project_files — both sandbox layouts a task can leave behind.

CLI: ``<Solution>/<Project>/...`` plus ``<Solution>/<Solution>.uipx``.
Studio Web export: ``<Project>/...`` at the sandbox root, no ``.uipx``.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project_files import (  # noqa: E402
    find_project_dir,
    find_project_file,
    main,
    solution_registration_error,
)


def _cli_layout(root, *, projects=("IPAgent",), types=("Agent",)):
    sol = root / "IPSol"
    for name, ptype in zip(projects, types):
        proj = sol / name
        proj.mkdir(parents=True)
        (proj / "project.uiproj").write_text(json.dumps({"ProjectType": ptype}))
        (proj / "agent.json").write_text("{}")
    (sol / "IPSol.uipx").write_text(
        json.dumps({"Projects": [{"Name": n, "Type": t} for n, t in zip(projects, types)]})
    )
    return sol


def _studio_web_layout(root, *, project="IPAgent", ptype="Agent", flow=False):
    proj = root / project
    proj.mkdir(parents=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": ptype}))
    if flow:
        (proj / "new.flow").write_text('{"nodes": []}')
    else:
        (proj / "agent.json").write_text("{}")
    return proj


def test_cli_layout_wins_when_present(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sol = _cli_layout(tmp_path)

    assert find_project_dir("IPSol", "IPAgent") == sol / "IPAgent"
    assert find_project_file("IPSol", "IPAgent", "agent.json") == sol / "IPAgent" / "agent.json"


def test_studio_web_layout_resolves_project_at_sandbox_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj = _studio_web_layout(tmp_path)

    assert find_project_dir("IPSol", "IPAgent") == proj
    assert find_project_file("IPSol", "IPAgent", "agent.json") == proj / "agent.json"


def test_flow_named_after_project_falls_back_to_the_lone_new_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj = _studio_web_layout(tmp_path, project="DocsFlow", ptype="Flow", flow=True)

    assert find_project_file("DocsFlowSol", "DocsFlow", "DocsFlow.flow") == proj / "new.flow"
    # Nested paths and non-flow files are never remapped.
    assert find_project_file("DocsFlowSol", "DocsFlow", "bindings_v2.json") == proj / "bindings_v2.json"


def test_nested_project_found_by_unique_marker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj = tmp_path / "work" / "Other" / "IPAgent"
    proj.mkdir(parents=True)
    (proj / "agent.json").write_text("{}")

    assert find_project_dir("IPSol", "IPAgent") == proj


def test_missing_project_keeps_the_canonical_cli_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert find_project_dir("IPSol", "IPAgent") == tmp_path / "IPSol" / "IPAgent"
    assert find_project_file("IPSol", "IPAgent", "agent.json") == tmp_path / "IPSol" / "IPAgent" / "agent.json"


def test_registered_reads_the_uipx_strictly(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _cli_layout(tmp_path)

    assert solution_registration_error("IPSol") is None
    assert solution_registration_error("IPSol", project_type="Agent") is None
    assert solution_registration_error("IPSol", min_projects=1, max_projects=1) is None
    assert "expected at least 2" in solution_registration_error("IPSol", min_projects=2)
    assert "expected at most 0" in solution_registration_error("IPSol", min_projects=0, max_projects=0)
    assert "Projects[0].Type" in solution_registration_error("IPSol", project_type="Flow")


def test_registered_accepts_exported_manifests_only_without_any_uipx(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _studio_web_layout(tmp_path)

    assert solution_registration_error("IPSol") is None
    assert solution_registration_error("IPSol", project_type="Agent") is None
    assert solution_registration_error("IPSol", min_projects=1, max_projects=1) is None
    assert "expected at least 2" in solution_registration_error("IPSol", min_projects=2)
    assert "ProjectType" in solution_registration_error("IPSol", project_type="Flow")


def test_registered_fails_when_a_different_uipx_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    other = tmp_path / "OtherSol"
    other.mkdir()
    (other / "OtherSol.uipx").write_text(json.dumps({"Projects": [{"Name": "X"}]}))
    _studio_web_layout(tmp_path)

    assert "no IPSol.uipx found" in solution_registration_error("IPSol")


def test_registered_fails_on_an_empty_sandbox(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert "registers 0 project(s); expected at least 1" in solution_registration_error("IPSol")


@pytest.mark.parametrize("layout", ["cli", "studio_web"])
def test_cli_exists_and_registered(tmp_path, monkeypatch, capsys, layout):
    monkeypatch.chdir(tmp_path)
    (_cli_layout if layout == "cli" else _studio_web_layout)(tmp_path)

    assert main(["exists", "IPSol", "IPAgent", "agent.json"]) == 0
    assert main(["registered", "IPSol", "--min-projects", "1", "--project-type", "Agent"]) == 0
    assert main(["exists", "IPSol", "IPAgent", "missing.json"]) == 1
    assert "Missing IPSol/IPAgent/missing.json" in capsys.readouterr().err


def test_cli_usage_errors(capsys):
    assert main([]) == 2
    assert main(["registered"]) == 2
    assert main(["registered", "IPSol", "--min-projects"]) == 2
    assert main(["registered", "IPSol", "--bogus"]) == 2
