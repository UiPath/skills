"""Unit tests for solution_cleanup.py. Run with ``pytest`` from any directory.

This script deletes tenant solutions. A regression here destroys a solution no
run of these tasks created, which no later run can undo, so every branch that
spares an id is pinned.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import solution_cleanup as sc  # noqa: E402


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def deletes(monkeypatch):
    """Every id handed to `uip solution delete`, without running it."""
    called = []
    monkeypatch.setattr(sc.subprocess, "run", lambda argv, **_: called.append(argv[3]))
    return called


def manifest(folder: Path, name: str, solution_id: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(json.dumps({"SolutionId": solution_id}), encoding="utf-8")
    return path


def test_a_solution_the_run_created_is_deleted(workspace, deletes):
    sc.record("FeeRules")
    manifest(workspace / "FeeRules", "FeeRules.uipx", "created-by-this-run")

    sc.delete("FeeRules")

    assert deletes == ["created-by-this-run"]


def test_a_manifest_already_on_disk_is_left_alone(workspace, deletes):
    # The finding: a manifest that was there before the run names a solution this run did not
    # create, and the glob deleted it anyway.
    manifest(workspace / "FeeRules", "FeeRules.uipx", "someone-elses-solution")
    sc.record("FeeRules")

    sc.delete("FeeRules")

    assert deletes == []


def test_the_same_id_copied_to_a_new_path_is_left_alone(workspace, deletes):
    # A new path is not a new solution. Recording the ids as well as the paths is what catches
    # a pre-existing manifest copied somewhere else during the run.
    manifest(workspace / "FeeRules", "FeeRules.uipx", "someone-elses-solution")
    sc.record("FeeRules")
    manifest(workspace / "FeeRules" / "copy", "FeeRules.uipx", "someone-elses-solution")

    sc.delete("FeeRules")

    assert deletes == []


def test_a_manifest_outside_the_task_project_is_out_of_scope(workspace, deletes):
    sc.record("FeeRules")
    manifest(workspace / "SomeOtherSolution", "Other.uipx", "not-this-tasks-solution")

    sc.delete("FeeRules")

    assert deletes == []


def test_a_manifest_with_no_solution_id_is_skipped(workspace, deletes):
    sc.record("FeeRules")
    (workspace / "FeeRules").mkdir()
    (workspace / "FeeRules" / "FeeRules.uipx").write_text('{"Name": "FeeRules"}', encoding="utf-8")

    sc.delete("FeeRules")

    assert deletes == []


def test_an_unreadable_manifest_does_not_stop_the_cleanup(workspace, deletes):
    sc.record("FeeRules")
    (workspace / "FeeRules").mkdir()
    (workspace / "FeeRules" / "broken.uipx").write_text("{not json", encoding="utf-8")
    manifest(workspace / "FeeRules", "FeeRules.uipx", "created-by-this-run")

    sc.delete("FeeRules")

    assert deletes == ["created-by-this-run"]


def test_no_record_deletes_nothing_rather_than_everything(workspace, deletes):
    # A `pre_run` that never ran leaves no state. Reading that as "nothing was here before" is
    # the glob's behaviour and the bug; with no record there is no evidence, so nothing goes.
    manifest(workspace / "FeeRules", "FeeRules.uipx", "unknown-provenance")

    sc.delete("FeeRules")

    assert deletes == []
