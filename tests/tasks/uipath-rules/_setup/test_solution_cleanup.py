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


class _Completed:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


@pytest.fixture
def deletes(monkeypatch):
    """Every id handed to `uip solution delete`, without running it. Each call succeeds."""
    called = []
    monkeypatch.setattr(sc.subprocess, "run",
                        lambda argv, **_: (called.append(argv[3]), _Completed(0))[1])
    return called


@pytest.fixture
def refused(monkeypatch):
    """Every id handed to `uip solution delete`, each call exiting non-zero as a 403 does."""
    called = []
    monkeypatch.setattr(sc.subprocess, "run",
                        lambda argv, **_: (called.append(argv[3]), _Completed(1))[1])
    return called


def manifest(folder: Path, name: str, solution_id: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(json.dumps({"SolutionId": solution_id}), encoding="utf-8")
    return path


def test_a_solution_the_run_created_is_deleted(workspace, deletes):
    # The layout `uip rules init FeeRules` actually writes: the manifest sits in the solution
    # directory, beside the project rather than inside it. The old filter looked for the project
    # name in the manifest's path, matched nothing here, and deleted nothing at all.
    sc.record()
    (workspace / "FeeRulesSolution" / "FeeRules").mkdir(parents=True)
    manifest(workspace / "FeeRulesSolution", "FeeRulesSolution.uipx", "created-by-this-run")

    sc.delete()

    assert deletes == ["created-by-this-run"]


def test_a_manifest_already_on_disk_is_left_alone(workspace, deletes):
    # The finding this script exists for: a manifest that was there before the run names a
    # solution this run did not create, and the glob deleted it anyway.
    manifest(workspace / "FeeRulesSolution", "FeeRulesSolution.uipx", "someone-elses-solution")
    sc.record()

    sc.delete()

    assert deletes == []


def test_the_same_id_copied_to_a_new_path_is_left_alone(workspace, deletes):
    # A new path is not a new solution. Recording the ids as well as the paths is what catches
    # a pre-existing manifest copied somewhere else during the run.
    manifest(workspace / "FeeRulesSolution", "FeeRulesSolution.uipx", "someone-elses-solution")
    sc.record()
    manifest(workspace / "copy", "FeeRulesSolution.uipx", "someone-elses-solution")

    sc.delete()

    assert deletes == []


def test_a_manifest_that_was_already_there_is_left_alone_wherever_it_sits(workspace, deletes):
    # The record, not a directory name, is what spares it — which is the whole reason the path
    # filter went: a name the layout chooses cannot carry ownership.
    manifest(workspace / "SomeOtherSolution", "Other.uipx", "not-this-tasks-solution")
    sc.record()

    sc.delete()

    assert deletes == []


def test_a_manifest_with_no_solution_id_is_skipped(workspace, deletes):
    sc.record()
    (workspace / "FeeRulesSolution").mkdir()
    (workspace / "FeeRulesSolution" / "FeeRulesSolution.uipx").write_text('{"Name": "FeeRules"}', encoding="utf-8")

    sc.delete()

    assert deletes == []


def test_an_unreadable_manifest_does_not_stop_the_cleanup(workspace, deletes):
    sc.record()
    (workspace / "FeeRulesSolution").mkdir()
    (workspace / "FeeRulesSolution" / "broken.uipx").write_text("{not json", encoding="utf-8")
    manifest(workspace / "FeeRulesSolution", "FeeRulesSolution.uipx", "created-by-this-run")

    sc.delete()

    assert deletes == ["created-by-this-run"]


def test_no_record_deletes_nothing_rather_than_everything(workspace, deletes):
    # A `pre_run` that never ran leaves no state. Reading that as "nothing was here before" is
    # the glob's behaviour and the bug; with no record there is no evidence, so nothing goes.
    manifest(workspace / "FeeRulesSolution", "FeeRulesSolution.uipx", "unknown-provenance")

    sc.delete()

    assert deletes == []


def test_a_refused_delete_is_reported_rather_than_counted(workspace, refused, capsys):
    # A 403 exits non-zero and the solution is still on the tenant. Reporting it as deleted hid
    # a cleanup failure behind a line saying the opposite.
    sc.record()
    manifest(workspace / "FeeRulesSolution", "FeeRulesSolution.uipx", "refused-by-the-tenant")

    sc.delete()

    assert refused == ["refused-by-the-tenant"]
    printed = capsys.readouterr().out
    assert "deleted nothing" in printed
    assert "FAILED to delete, still on the tenant: ['refused-by-the-tenant']" in printed
