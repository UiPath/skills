"""post_run cancel of _setup/case_run.py in a task with no pinned tenant IDs.

Such a task runs no localize pre_run, so the task-start mark comes from
`case_run.py --mark-task-start`, run as pre_run from the sandbox. No tenant is
touched.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "_setup" / "case_run.py"
SPEC = importlib.util.spec_from_file_location("case_run_post_run", SCRIPT)
assert SPEC and SPEC.loader
case_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(case_run)

PLAN = {"nodes": [{"id": "Stage_ours1", "type": "case-management:Stage"}]}


def test_a_task_marked_at_start_cancels_its_open_debug_instance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "_setup").mkdir()
    subprocess.run(
        [sys.executable, str(SCRIPT), "--mark-task-start"], cwd=tmp_path, check=True
    )
    monkeypatch.chdir(tmp_path)
    plan_dir = tmp_path / "Case" / "Case"
    plan_dir.mkdir(parents=True)
    (plan_dir / "caseplan.json").write_text(json.dumps(PLAN))
    listing = [
        {"InstanceId": "ours", "Source": "Studio Web Debug", "CreatedTimeUtc": "2999-01-01T00:00:00",
         "LatestRunStatus": "Running", "FolderKey": "f"},
    ]
    cancelled = []

    def uip(args, timeout=120):
        if args[:4] == ["maestro", "case", "instance", "list"]:
            return {"Result": "Success", "Data": listing}
        if args[:4] == ["maestro", "case", "instance", "element-executions"]:
            return {"Result": "Success", "Data": {"ElementExecutions": [{"ElementId": "Stage_ours1"}]}}
        if args[:4] == ["maestro", "case", "instance", "cancel"]:
            cancelled.append(args[4])
            return {"Result": "Success"}
        return {"Result": "Failure"}

    monkeypatch.setattr(case_run, "_uip", uip)

    assert case_run.cancel_debug_instances() == 0
    assert cancelled == ["ours"]


def _paged_uip(pages: dict, calls: list):
    def uip(args, timeout=120):
        calls.append(args)
        if args[:4] == ["maestro", "case", "instance", "list"]:
            cursor = args[args.index("--next-page") + 1] if "--next-page" in args else None
            return pages[cursor]
        return {"Result": "Failure"}

    return uip


def test_folder_key_is_found_on_a_later_page_of_a_filtered_list(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "_setup").mkdir()
    (tmp_path / "_setup" / ".task-start").write_text("x")
    monkeypatch.chdir(tmp_path)
    pages = {
        None: {"Result": "Success", "Data": [{"InstanceId": "other", "FolderKey": "f0"}],
               "Pagination": {"HasMore": True, "NextPage": "c2"}},
        "c2": {"Result": "Success", "Data": [{"InstanceId": "ours", "FolderKey": "f1"}],
               "Pagination": {"HasMore": False}},
    }
    calls: list = []
    monkeypatch.setattr(case_run, "_uip", _paged_uip(pages, calls))

    assert case_run.instance_folder_key("ours") == "f1"
    first = calls[0]
    assert first[first.index("--limit") + 1] == "500"
    assert "--from-date" in first
    assert calls[1][calls[1].index("--next-page") + 1] == "c2"


def test_cancel_follows_pagination_to_an_instance_on_page_two(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "_setup").mkdir()
    (tmp_path / "_setup" / ".task-start").write_text("x")
    monkeypatch.chdir(tmp_path)
    plan_dir = tmp_path / "Case" / "Case"
    plan_dir.mkdir(parents=True)
    (plan_dir / "caseplan.json").write_text(json.dumps(PLAN))
    ours = {"InstanceId": "ours", "Source": "Studio Web Debug", "CreatedTimeUtc": "2999-01-01T00:00:00",
            "LatestRunStatus": "Running", "FolderKey": "f"}
    pages = {
        None: {"Result": "Success", "Data": [], "Pagination": {"HasMore": True, "NextPage": "c2"}},
        "c2": {"Result": "Success", "Data": [ours], "Pagination": {"HasMore": False}},
    }
    cancelled: list = []
    base = _paged_uip(pages, [])

    def uip(args, timeout=120):
        if args[:4] == ["maestro", "case", "instance", "element-executions"]:
            return {"Result": "Success", "Data": {"ElementExecutions": [{"ElementId": "Stage_ours1"}]}}
        if args[:4] == ["maestro", "case", "instance", "cancel"]:
            cancelled.append(args[4])
            return {"Result": "Success"}
        return base(args, timeout)

    monkeypatch.setattr(case_run, "_uip", uip)

    assert case_run.cancel_debug_instances() == 0
    assert cancelled == ["ours"]


def test_a_list_that_never_ends_stops_at_the_page_cap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    calls: list = []

    def uip(args, timeout=120):
        calls.append(args)
        return {"Result": "Success", "Data": [], "Pagination": {"HasMore": True, "NextPage": "again"}}

    monkeypatch.setattr(case_run, "_uip", uip)

    assert case_run.instance_folder_key("missing") is None
    assert len(calls) == case_run.MAX_LIST_PAGES


def _sandbox_with_plan(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "_setup").mkdir()
    (tmp_path / "_setup" / ".task-start").write_text("x")
    monkeypatch.chdir(tmp_path)
    plan_dir = tmp_path / "Case" / "Case"
    plan_dir.mkdir(parents=True)
    (plan_dir / "caseplan.json").write_text(json.dumps(PLAN))


def _row(instance_id: str) -> dict:
    return {"InstanceId": instance_id, "Source": "Studio Web Debug", "CreatedTimeUtc": "2999-01-01T00:00:00",
            "LatestRunStatus": "Running", "FolderKey": "f"}


def test_a_recorded_debug_instance_is_cancelled_without_reading_others(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _sandbox_with_plan(monkeypatch, tmp_path)
    case_run.record_debug_instance("ours")
    listing = [_row(f"other{n}") for n in range(30)] + [_row("ours")]
    cancelled: list = []
    read: list = []

    def uip(args, timeout=120):
        if args[:4] == ["maestro", "case", "instance", "list"]:
            return {"Result": "Success", "Data": listing}
        if args[:4] == ["maestro", "case", "instance", "element-executions"]:
            read.append(args[4])
            return {"Result": "Success", "Data": {"ElementExecutions": []}}
        if args[:4] == ["maestro", "case", "instance", "cancel"]:
            cancelled.append(args[4])
            return {"Result": "Success"}
        return {"Result": "Failure"}

    monkeypatch.setattr(case_run, "_uip", uip)
    monkeypatch.setattr(case_run, "SCAN_DEADLINE_S", 0)

    assert case_run.cancel_debug_instances() == 0
    assert cancelled == ["ours"]
    assert read == []


def test_a_recorded_instance_is_cancelled_even_with_no_stage_ids(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "_setup").mkdir()
    monkeypatch.chdir(tmp_path)
    case_run.record_debug_instance("ours")
    cancelled: list = []

    def uip(args, timeout=120):
        if args[:4] == ["maestro", "case", "instance", "cancel"]:
            cancelled.append(args[4])
            return {"Result": "Success"}
        return {"Result": "Failure"}

    monkeypatch.setattr(case_run, "_uip", uip)

    assert case_run.cancel_debug_instances() == 0
    assert cancelled == ["ours"]


def test_an_unrecorded_instance_is_read_only_within_the_scan_deadline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _sandbox_with_plan(monkeypatch, tmp_path)
    listing = [_row(f"other{n}") for n in range(30)]
    read: list = []

    def uip(args, timeout=120):
        if args[:4] == ["maestro", "case", "instance", "list"]:
            return {"Result": "Success", "Data": listing}
        if args[:4] == ["maestro", "case", "instance", "element-executions"]:
            read.append(args[4])
        return {"Result": "Success", "Data": {"ElementExecutions": []}}

    monkeypatch.setattr(case_run, "_uip", uip)
    monkeypatch.setattr(case_run, "SCAN_DEADLINE_S", 0)

    assert case_run.cancel_debug_instances() == 0
    assert read == []


def test_debug_case_records_the_instance_it_started(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    sys.path.insert(0, str(SCRIPT.parent.parent))
    from _shared import case_run_path  # noqa: PLC0415

    monkeypatch.chdir(tmp_path)
    project = tmp_path / "Case"
    project.mkdir()
    started = {"Data": {"instanceId": "run-1", "finalStatus": "Suspended", "elementExecutions": []}}
    monkeypatch.setattr(case_run_path.os.path, "isdir", lambda path: path == "/solution")
    monkeypatch.setattr("_shared.case_check.find_project_dir", lambda *a, **k: str(project))
    monkeypatch.setattr(case_run_path, "_debug_with_retry", lambda cmd, timeout: (subprocess.CompletedProcess(cmd, 0, "", ""), started, started["Data"]))

    run = case_run_path.debug_case()

    assert run["instance_id"] == "run-1"
    assert (tmp_path / "_setup" / ".debug-instances").read_text() == "run-1\n"
