"""The Studio Web flavor copies the target to ``.flow-sdk/original/<Name>.bpmn`` before an edit.

That undo copy is the scaffold as it was (no diagram, ``_Implicit_EndEvent``), so a grader
that reads it fails MISSING_DI_SHAPE/MISSING_DI_EDGE on a correct run (nightly
2026-11-24 on release/v1.207, before #4754). Every ``.bpmn`` lookup must skip it and
still grade the real file beside it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent
sys.path.insert(0, str(HERE))

import bpmn_check  # noqa: E402

REAL = "<bpmn:definitions xmlns:bpmn='http://www.omg.org/spec/BPMN/20100524/MODEL'/>"
SNAPSHOT = "<snapshot/>"


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module


def _workspace(tmp_path: Path, name: str = "P", *, snapshot_name: str | None = "Process.bpmn", main: str = "Process.bpmn") -> Path:
    project = tmp_path / name
    (project / ".flow-sdk" / "original").mkdir(parents=True)
    (project / main).write_text(REAL)
    (project / "project.uiproj").write_text("{}")
    if snapshot_name:
        (project / ".flow-sdk" / "original" / snapshot_name).write_text(SNAPSHOT)
    return tmp_path


def test_is_scratch_bpmn_skips_the_snapshot() -> None:
    assert bpmn_check.is_scratch_bpmn(".flow-sdk/original/Process.bpmn")
    assert bpmn_check.is_scratch_bpmn("P/.flow-sdk/original/P.bpmn")
    assert not bpmn_check.is_scratch_bpmn("P/Process.bpmn")


def test_validate_bpmn_discovers_only_the_real_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _workspace(tmp_path)
    monkeypatch.chdir(root)
    found = _load(HERE / "validate_bpmn.py")._bpmn_files()
    assert [p.relative_to(root).as_posix() for p in found] == ["P/Process.bpmn"]


@pytest.mark.parametrize("snapshot_name", ["Process.bpmn", "P.bpmn"])
def test_find_bpmn_file_ignores_the_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, snapshot_name: str) -> None:
    monkeypatch.chdir(_workspace(tmp_path, snapshot_name=snapshot_name))
    assert bpmn_check.find_bpmn_file() == "P/Process.bpmn"
    assert bpmn_check.find_bpmn_file("P") == "P/Process.bpmn"


def test_resolve_bpmn_file_ignores_the_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _workspace(tmp_path)
    monkeypatch.chdir(root)
    assert bpmn_check.resolve_bpmn_file("P.bpmn").relative_to(root).as_posix() == "P/Process.bpmn"


def test_a_real_file_next_to_a_same_named_snapshot_is_the_one_graded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_workspace(tmp_path, snapshot_name="P.bpmn", main="P.bpmn"))
    assert bpmn_check.find_bpmn_file("P") == "P/P.bpmn"
    assert bpmn_check.resolve_bpmn_file("P.bpmn").as_posix().endswith("P/P.bpmn")


def test_only_a_snapshot_is_no_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = tmp_path / "P" / ".flow-sdk" / "original"
    project.mkdir(parents=True)
    (project / "Process.bpmn").write_text(SNAPSHOT)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        bpmn_check.find_bpmn_file()


def test_fresh_solution_check_ignores_the_snapshot(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    module = _load(TASKS / "smoke" / "check_fresh_solution.py")
    root = _workspace(tmp_path, name="Returns", snapshot_name=None, main="Returns.bpmn")
    taken = root / "Taken" / "Returns" / ".flow-sdk" / "original"
    taken.mkdir(parents=True)
    (taken / "Returns.bpmn").write_text(SNAPSHOT)
    # The snapshot inside the taken solution is no "put in the existing solution" evidence.
    with pytest.raises(SystemExit):
        module.check(root, "Returns", "Taken")
    assert "no solution other than Taken registers" in capsys.readouterr().out


def test_api_workflow_composition_find_bpmn_ignores_the_snapshot(tmp_path: Path) -> None:
    module = _load(TASKS / "e2e" / "api_workflow_composition" / "composition.py")
    root = _workspace(tmp_path)
    assert module.find_bpmn(root) == root / "P" / "Process.bpmn"
    (root / "P" / "Process.bpmn").unlink()
    assert module.find_bpmn(root) is None  # only the snapshot is left: no artifact
