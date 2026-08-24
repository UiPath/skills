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
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flow_check import _find_project  # noqa: E402

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
