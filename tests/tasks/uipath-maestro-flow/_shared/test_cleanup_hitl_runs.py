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


TOKEN = "INV-abc123"
INSTANCE = "inst-1"


def write_tokens(sandbox, *lines):
    with open(os.path.join(sandbox, cleanup.TOKENS_FILE), "w") as f:
        f.write("\n".join(lines) + "\n")


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
    write_tokens(sandbox, TOKEN, f"{TOKEN} {INSTANCE}")
    uip = FakeUip([task(1)], data={"1": {"invoiceNumber": TOKEN}})
    assert cleanup.clean(uip, sandbox) == ["1"]
    assert uip.verbs("maestro", "flow", "debug-instance", "cancel") == [["maestro", "flow", "debug-instance", "cancel", INSTANCE]]
    assert uip.verbs("tasks", "complete")[0][2] == "1"
    assert [c[-1] for c in uip.verbs("tasks", "complete")] == ["{}"] and uip.verbs("tasks", "complete")[0][-3] == "Reject"


def test_a_recorded_instance_is_cancelled_even_when_no_task_was_found(sandbox):
    write_tokens(sandbox, f"{TOKEN} {INSTANCE}")
    uip = FakeUip([])
    assert cleanup.clean(uip, sandbox) == []
    assert uip.verbs("maestro", "flow", "debug-instance", "cancel") == [["maestro", "flow", "debug-instance", "cancel", INSTANCE]]


def test_a_token_with_no_instance_cancels_nothing(sandbox):
    write_tokens(sandbox, TOKEN)
    uip = FakeUip([])
    cleanup.clean(uip, sandbox)
    assert uip.verbs("maestro", "flow", "debug-instance", "cancel") == []


def test_approve_is_never_a_fallback_action(sandbox):
    write_tokens(sandbox, TOKEN)
    uip = FakeUip([task(1)], data={"1": {"n": TOKEN}})
    uip_fail = lambda args: (uip(args), None)[1] if args[:2] == ["tasks", "complete"] else uip(args)
    cleanup.clean(uip_fail, sandbox)
    attempts = uip.verbs("tasks", "complete")
    assert attempts and all("Approve" not in call for call in attempts)


def test_tasks_from_before_the_run_or_already_completed_are_left_alone(sandbox):
    write_tokens(sandbox, TOKEN)
    data = {str(i): {"n": TOKEN} for i in (1, 2, 3)}
    uip = FakeUip([task(1, created=BEFORE), task(2, status="Completed"), task(3)], data=data)
    assert cleanup.clean(uip, sandbox) == ["3"]
    assert [c[2] for c in uip.verbs("tasks", "complete")] == ["3"]


def test_tasks_without_the_token_are_left_alone(sandbox):
    write_tokens(sandbox, TOKEN)
    uip = FakeUip([task(1), task(3, creator="someone-else")])
    assert cleanup.clean(uip, sandbox) == []
    assert uip.verbs("tasks", "complete") == [] and uip.verbs("tasks", "assign") == []


def test_a_task_by_the_same_identity_without_this_runs_token_is_left_alone(sandbox):
    write_tokens(sandbox, TOKEN)
    uip = FakeUip([task(1)], data={"1": {"invoiceNumber": "INV-other"}})
    assert cleanup.clean(uip, sandbox) == []


def test_a_task_carrying_a_recorded_token_is_closed_even_when_created_by_another_identity(sandbox):
    write_tokens(sandbox, "INV-ABCD1234")
    uip = FakeUip([task(1, creator="svc"), task(2, creator="svc")], data={"1": {"Data": {"n": "INV-ABCD1234"}}})
    assert cleanup.clean(uip, sandbox) == ["1"]


def test_only_recorded_instances_are_cancelled(sandbox):
    write_tokens(sandbox, f"{TOKEN} {INSTANCE}")
    uip = FakeUip([task(1)], data={"1": {"n": TOKEN}})
    cleanup.clean(uip, sandbox)
    assert [c[-1] for c in uip.verbs("maestro", "flow", "debug-instance", "cancel")] == [INSTANCE]
    assert uip.verbs("maestro", "flow", "instances", "list") == []


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
