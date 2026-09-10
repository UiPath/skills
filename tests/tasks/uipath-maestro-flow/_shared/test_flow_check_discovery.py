"""Discovery tests for the abandoned-scaffold heuristic in ``_find_project``.

`uip maestro flow init` chained without a `cd` into the solution runs outside
any solution and auto-scaffolds a duplicate ``<Name>Solution/`` holding a
trigger-only project (cli#2470). An agent that rebuilds correctly inside the
real solution then leaves two ``project.uiproj`` files, and every grader routed
through ``_find_project`` used to refuse to guess — zeroing a good build.

The real two-solution artifact from that run is reproduced by
:func:`_billing_dispute_fixture` (17-node build + 1-node husk).
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flow_check import (  # noqa: E402
    _find_project,
    find_flow_file,
    find_flow_files,
    find_project_dir,
)
import validate_flow  # noqa: E402

PATTERN = "**/project.uiproj"


def _make_flow_project(root, solution, project, node_count, *, flow_body=None):
    """Create <root>/<solution>/<project>/{project.uiproj,<project>.flow}."""
    proj = root / solution / project
    proj.mkdir(parents=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    flow = (
        flow_body
        if flow_body is not None
        else json.dumps(
            {"nodes": [{"id": f"n{i}", "type": "core.trigger"} for i in range(node_count)]}
        )
    )
    (proj / f"{project}.flow").write_text(flow)
    return proj


def _billing_dispute_fixture(root):
    """The shipped shape of the billing-dispute run: the real solution plus the
    auto-scaffolded ``<Name>Solution/`` wrapper the agent never deleted."""
    _make_flow_project(root, "BillingDisputeResolution", "BillingDisputeResolution", 17)
    _make_flow_project(
        root, "BillingDisputeResolutionSolution", "BillingDisputeResolution", 1
    )


def test_picks_the_build_over_the_auto_scaffolded_husk(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _billing_dispute_fixture(tmp_path)

    found = _find_project(PATTERN)

    assert found == os.path.join("BillingDisputeResolution", "BillingDisputeResolution")
    note = capsys.readouterr().out
    assert "note: ignoring 1 abandoned scaffold(s):" in note
    assert (
        os.path.join("BillingDisputeResolutionSolution", "BillingDisputeResolution")
        in note
    )
    assert "(1 node)" in note
    assert "FAIL" not in note


def test_ignores_several_husks_at_once(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _make_flow_project(tmp_path, "Real", "Build", 9)
    _make_flow_project(tmp_path, "HuskA", "Build", 1)
    _make_flow_project(tmp_path, "HuskB", "Build", 0)

    assert _find_project(PATTERN) == os.path.join("Real", "Build")
    assert "note: ignoring 2 abandoned scaffold(s):" in capsys.readouterr().out


def test_refuses_when_two_candidates_are_substantive(tmp_path, monkeypatch):
    """Two real builds is a genuine ambiguity — the refusal must stand."""
    monkeypatch.chdir(tmp_path)
    _make_flow_project(tmp_path, "SolutionA", "BuildA", 3)
    _make_flow_project(tmp_path, "SolutionB", "BuildB", 3)

    with pytest.raises(SystemExit, match="Multiple Flow projects match"):
        _find_project(PATTERN)


def test_collapses_byte_identical_substantive_projects(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    body = json.dumps(
        {"nodes": [{"id": f"n{i}", "type": "core.action.script"} for i in range(3)]}
    )
    first = _make_flow_project(
        tmp_path, "SolutionA", "Build", 3, flow_body=body
    )
    _make_flow_project(tmp_path, "SolutionB", "Build", 3, flow_body=body)

    assert _find_project(PATTERN) == os.path.relpath(first, tmp_path)
    assert (
        "ignoring 1 byte-identical Flow project duplicate(s)"
        in capsys.readouterr().out
    )


def test_refuses_when_a_candidate_flow_is_unreadable(tmp_path, monkeypatch):
    """Unknown node count is not a husk — stay conservative and refuse."""
    monkeypatch.chdir(tmp_path)
    _make_flow_project(tmp_path, "Real", "Build", 17)
    _make_flow_project(tmp_path, "Broken", "Build", 0, flow_body="{not valid json")

    with pytest.raises(SystemExit, match="Multiple Flow projects match"):
        _find_project(PATTERN)


def test_refuses_when_a_candidate_has_no_flow_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_flow_project(tmp_path, "Real", "Build", 17)
    bare = tmp_path / "Bare" / "Build"
    bare.mkdir(parents=True)
    (bare / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))

    with pytest.raises(SystemExit, match="Multiple Flow projects match"):
        _find_project(PATTERN)


def test_refusal_lists_node_counts_per_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_flow_project(tmp_path, "SolutionA", "BuildA", 3)
    _make_flow_project(tmp_path, "SolutionB", "BuildB", 5)

    with pytest.raises(SystemExit) as excinfo:
        _find_project(PATTERN)

    message = str(excinfo.value)
    assert "(3 nodes)" in message
    assert "(5 nodes)" in message


def test_refusal_marks_an_unknown_node_count(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_flow_project(tmp_path, "SolutionA", "BuildA", 3)
    _make_flow_project(tmp_path, "SolutionB", "BuildB", 0, flow_body="{not valid json")

    with pytest.raises(SystemExit, match="node count unknown"):
        _find_project(PATTERN)


def test_single_project_is_unchanged_and_silent(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _make_flow_project(tmp_path, "OnlySolution", "OnlyBuild", 4)

    assert _find_project(PATTERN) == os.path.join("OnlySolution", "OnlyBuild")
    assert capsys.readouterr().out == ""


def test_single_husk_project_is_still_selected(tmp_path, monkeypatch):
    """One candidate never goes through the husk split — a lone trigger-only
    project is still the project under test."""
    monkeypatch.chdir(tmp_path)
    _make_flow_project(tmp_path, "OnlySolution", "OnlyBuild", 1)

    assert _find_project(PATTERN) == os.path.join("OnlySolution", "OnlyBuild")


def test_structure_discovery_falls_back_to_one_root_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "BareEmit.flow").write_text(json.dumps({"nodes": []}))

    assert find_flow_files() == ["BareEmit.flow"]
    assert find_flow_file() == "BareEmit.flow"


def test_structure_discovery_ignores_non_flow_sidecar_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_flow_project(tmp_path, "AgentSidecar", "Agent", 0)
    manifest = tmp_path / "AgentSidecar" / "Agent" / "project.uiproj"
    manifest.write_text(json.dumps({"ProjectType": "Agent"}))
    (tmp_path / "BareEmit.flow").write_text(json.dumps({"nodes": []}))

    assert find_flow_file() == "BareEmit.flow"


def test_solution_flow_beats_root_scratch_emit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = _make_flow_project(tmp_path, "Solution", "Build", 4)
    (tmp_path / "Build.flow").write_text(json.dumps({"nodes": [{"id": "scratch"}]}))

    assert find_flow_files() == [os.path.join("Solution", "Build", "Build.flow")]
    assert find_flow_file() == os.path.join("Solution", "Build", "Build.flow")
    assert project.name == "Build"


def test_substantive_root_emit_beats_abandoned_project_scaffold(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    _make_flow_project(tmp_path, "GeneratedSolution", "Build", 1)
    root = tmp_path / "Build.flow"
    root.write_text(
        json.dumps(
            {"nodes": [{"id": f"n{i}", "type": "core.action.script"} for i in range(4)]}
        )
    )

    assert find_flow_files() == ["Build.flow"]
    assert find_flow_file() == "Build.flow"
    assert "ignoring abandoned project scaffold(s)" in capsys.readouterr().out


def test_root_husk_does_not_override_project_husk(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = _make_flow_project(tmp_path, "Solution", "Build", 1)
    (tmp_path / "Build.flow").write_text(
        json.dumps({"nodes": [{"id": "start", "type": "core.trigger.manual"}]})
    )

    assert find_flow_file() == os.path.join("Solution", "Build", "Build.flow")
    assert project.name == "Build"


def test_root_fallback_refuses_distinct_candidates_and_lists_them(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "A.flow").write_text(json.dumps({"nodes": [{"id": "a"}]}))
    (tmp_path / "B.flow").write_text(json.dumps({"nodes": [{"id": "b"}]}))

    with pytest.raises(SystemExit) as excinfo:
        find_flow_files()

    message = str(excinfo.value)
    assert "Multiple distinct root-level .flow files" in message
    assert "A.flow" in message
    assert "B.flow" in message


def test_root_fallback_collapses_byte_identical_copies(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    body = json.dumps({"nodes": [{"id": "same"}]})
    (tmp_path / "A.flow").write_text(body)
    (tmp_path / "B.flow").write_text(body)

    assert find_flow_files() == ["A.flow"]


def test_debug_discovery_stays_project_scoped(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "BareEmit.flow").write_text(json.dumps({"nodes": []}))

    with pytest.raises(SystemExit, match="No project.uiproj found"):
        find_project_dir()


def test_validate_flow_uses_root_fallback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "BareEmit.flow").write_text(json.dumps({"nodes": []}))
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="valid\n", stderr="")

    monkeypatch.setattr(validate_flow.subprocess, "run", fake_run)

    assert validate_flow.main() == 0
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command == [
        "uip",
        "maestro",
        "flow",
        "validate",
        "BareEmit.flow",
        "--output",
        "json",
    ]
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert 0 < kwargs["timeout"] <= 80


# ── flow_glob is a preference, not a gate (Studio Web keeps ``new.flow``) ────


def _make_studioweb_project(root, name, node_count=3):
    """Studio Web export shape: ``<Name>/<Name>/new.flow`` — the scaffolded
    file name is kept, so nothing in the project is called ``<Name>.flow``."""
    proj = _make_flow_project(root, name, name, node_count)
    (proj / f"{name}.flow").rename(proj / "new.flow")
    return proj


def test_named_glob_falls_back_to_the_projects_own_flow(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _make_studioweb_project(tmp_path, "TransformMapDemo")

    path = find_flow_file(flow_glob="TransformMapDemo*.flow")

    assert os.path.normpath(path) == os.path.join(
        "TransformMapDemo", "TransformMapDemo", "new.flow"
    )
    assert "no .flow matching 'TransformMapDemo*.flow'" in capsys.readouterr().out


def test_named_glob_still_selects_by_name_when_present(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    proj = _make_flow_project(tmp_path, "Sol", "Main", 3)
    (proj / "Helper.flow").write_text(json.dumps({"nodes": []}))

    path = find_flow_file(flow_glob="Main*.flow")

    assert os.path.normpath(path) == os.path.join("Sol", "Main", "Main.flow")
    assert capsys.readouterr().out == ""


def test_named_glob_fallback_refuses_an_ambiguous_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj = _make_studioweb_project(tmp_path, "Demo")
    (proj / "Subflow.flow").write_text(json.dumps({"nodes": []}))

    with pytest.raises(SystemExit) as excinfo:
        find_flow_file(flow_glob="Demo*.flow")
    assert "Multiple .flow files match" in str(excinfo.value)


def test_named_glob_fails_on_a_project_with_no_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj = _make_flow_project(tmp_path, "Sol", "Empty", 1)
    (proj / "Empty.flow").unlink()

    with pytest.raises(SystemExit) as excinfo:
        find_flow_files(flow_glob="Empty*.flow")
    assert "No .flow file under selected Flow project" in str(excinfo.value)


def test_root_fallback_accepts_a_differently_named_lone_emit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "new.flow").write_text(json.dumps({"nodes": []}))

    assert find_flow_files(flow_glob="Demo*.flow") == ["new.flow"]


def test_advisory_load_flow_falls_back_to_a_lone_generated_flow(tmp_path, monkeypatch):
    import advisory_flow_utils

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["advisory_x.py"])
    _make_studioweb_project(tmp_path, "BillingDisputeAnalyst")

    path, _flow, nodes = advisory_flow_utils.load_flow("BillingDisputeAnalyst.flow")

    assert path.name == "new.flow"
    assert len(nodes) == 3


def test_advisory_load_flow_refuses_two_unnamed_candidates(tmp_path, monkeypatch):
    import advisory_flow_utils

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["advisory_x.py"])
    _make_studioweb_project(tmp_path, "A")
    _make_studioweb_project(tmp_path, "B")

    with pytest.raises(SystemExit) as excinfo:
        advisory_flow_utils.load_flow("A.flow")
    assert "found 2" in str(excinfo.value)


# ── hidden scratch dirs are not deliverables ─────────────────────────────────


def test_hidden_scratch_projects_do_not_compete(tmp_path, monkeypatch, capsys):
    """eval-local-crud, run 2026-09-10_11-06-05: the agent kept two failed
    ``flow init`` attempts under dot-dirs beside the real build. All three were
    1-node flows, so the husk heuristic could not separate them."""
    monkeypatch.chdir(tmp_path)
    _make_flow_project(tmp_path, "SmokeEval", "SmokeEval", 1)
    _make_flow_project(tmp_path / ".flow-auto", "SmokeEvalSolution", "SmokeEval", 1)
    _make_flow_project(tmp_path, ".smokeeval-scaffold", "SmokeEval", 1)

    assert os.path.normpath(find_project_dir(PATTERN)) == os.path.join("SmokeEval", "SmokeEval")
    assert [os.path.normpath(p) for p in find_flow_files()] == [
        os.path.join("SmokeEval", "SmokeEval", "SmokeEval.flow")
    ]
    assert capsys.readouterr().out == ""
