"""cleanup_hitl_runs cancels and closes only what this run created."""
import importlib.util
import os
from datetime import datetime, timedelta, timezone

import pytest

SETUP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_setup", "cleanup_hitl_runs.py")
spec = importlib.util.spec_from_file_location("cleanup_hitl_runs", SETUP)
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)

ME = "6edeb96d-62a4-47c0-abf0-b819f2ff27b2"
START = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
AFTER = (START + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S.1234567Z")
BEFORE = (START - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S.1234567Z")
JOB = "11111111-2222-3333-4444-555555555555"


def task(task_id, *, created=AFTER, creator=ME, status="Unassigned", job=JOB, title="t"):
    return {"Id": task_id, "Status": status, "Type": "AppTask", "FolderId": 7, "CreatedTime": created,
            "CreatorUserKey": creator, "CreatorJobKey": job, "Title": title, "AssignedToUserKey": None}


class FakeUip:
    def __init__(self, tasks, instances=(), data=None):
        self.tasks, self.instances, self.data = tasks, list(instances), data or {}
        self.calls = []

    def __call__(self, args):
        self.calls.append(args)
        head = args[:2]
        if head == ["login", "status"]:
            return {"Result": "Success", "Data": {"UserId": ME, "UserEmail": "me@x.com"}}
        if head == ["tasks", "list"]:
            return {"Result": "Success", "Data": self.tasks}
        if args[:3] == ["tasks", "data", "get"]:
            return {"Result": "Success", "Data": self.data.get(args[3], {})}
        if args[:4] == ["maestro", "flow", "instances", "list"]:
            return {"Result": "Success", "Data": self.instances}
        return {"Result": "Success", "Data": {}}

    def verbs(self, *prefix):
        return [c for c in self.calls if c[:len(prefix)] == list(prefix)]


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    (tmp_path / cleanup.START_FILE).write_text(START.isoformat())
    monkeypatch.delenv(cleanup.CLEANUP_ENV, raising=False)
    return str(tmp_path)


def test_mark_records_the_start_time(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cleanup.mark()
    assert cleanup.parse_time((tmp_path / cleanup.START_FILE).read_text()) is not None


def test_the_start_and_token_files_match_the_grader():
    live_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hitl_live_run.py")).read()
    assert f'TOKENS_FILE = "{cleanup.TOKENS_FILE}"' in live_src


def test_an_open_task_carrying_this_runs_token_is_cancelled_and_closed(sandbox):
    open(os.path.join(sandbox, cleanup.TOKENS_FILE), "w").write("INV-abc123\n")
    uip = FakeUip([task(1)], instances=[{"InstanceId": "inst-1", "JobKey": JOB}], data={"1": {"invoiceNumber": "INV-abc123"}})
    assert cleanup.clean(uip, sandbox) == ["1"]
    assert uip.verbs("maestro", "flow", "debug-instance", "cancel") == [["maestro", "flow", "debug-instance", "cancel", "inst-1"]]
    assert uip.verbs("tasks", "complete")[0][2] == "1"


def test_tasks_from_before_the_run_or_already_completed_or_other_users_are_left_alone(sandbox):
    uip = FakeUip([task(1, created=BEFORE), task(2, status="Completed"), task(3, creator="someone-else")])
    assert cleanup.clean(uip, sandbox) == []
    assert uip.verbs("tasks", "complete") == [] and uip.verbs("tasks", "assign") == []


def test_a_task_by_the_same_identity_without_this_runs_token_is_left_alone(sandbox):
    open(os.path.join(sandbox, cleanup.TOKENS_FILE), "w").write("INV-abc123\n")
    uip = FakeUip([task(1)], instances=[{"InstanceId": "inst-1", "JobKey": JOB}], data={"1": {"invoiceNumber": "INV-other"}})
    assert cleanup.clean(uip, sandbox) == []
    assert not uip.verbs("maestro", "flow", "debug-instance", "cancel")


def test_a_task_carrying_a_recorded_token_is_closed_even_when_created_by_another_identity(sandbox):
    with open(os.path.join(sandbox, cleanup.TOKENS_FILE), "w") as f:
        f.write("INV-ABCD1234\n")
    uip = FakeUip([task(1, creator="svc"), task(2, creator="svc")], data={"1": {"Data": {"n": "INV-ABCD1234"}}})
    assert cleanup.clean(uip, sandbox) == ["1"]


def test_an_instance_unrelated_to_the_tasks_is_not_cancelled(sandbox):
    uip = FakeUip([task(1)], instances=[{"InstanceId": "other", "JobKey": "99999999-0000-0000-0000-000000000000"}])
    cleanup.clean(uip, sandbox)
    assert uip.verbs("maestro", "flow", "debug-instance", "cancel") == []


def test_nothing_is_done_without_a_start_marker(tmp_path):
    uip = FakeUip([task(1)])
    assert cleanup.clean(uip, str(tmp_path)) == []
    assert uip.calls == []


def test_cleanup_never_leaves_everything(sandbox, monkeypatch):
    monkeypatch.setenv(cleanup.CLEANUP_ENV, "never")
    uip = FakeUip([task(1)])
    assert cleanup.clean(uip, sandbox) == []
    assert uip.calls == []


def test_a_failing_cli_never_fails_the_step(sandbox, monkeypatch):
    monkeypatch.chdir(sandbox)
    def boom(args):
        raise RuntimeError("boom")

    monkeypatch.setattr(cleanup, "run_uip", boom)
    assert cleanup.main(["x", "clean"]) == 0
