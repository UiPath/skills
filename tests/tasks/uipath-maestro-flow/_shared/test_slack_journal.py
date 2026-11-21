"""The graders journal the Slack messages their own debug runs posted, and post_run deletes them."""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

SHARED = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SHARED)
sys.path.insert(0, ROOT)

from _shared import flow_check, slack_journal  # noqa: E402

spec = importlib.util.spec_from_file_location("teardown_slack_posts", os.path.join(ROOT, "_setup", "teardown_slack_posts.py"))
teardown = importlib.util.module_from_spec(spec)
spec.loader.exec_module(teardown)

CHANNEL = "C0B2FDZD1M3"
TS = "1794932449.166699"
OTHER_TS = "1794932450.000100"
CONNECTION = "849e85d8-1aa9-4d52-8bbd-20041c8f05d8"
SEND_ID = "postAlert"
SEND_TYPE = "uipath.connector.uipath-salesforce-slack.send-message-to-channel"
READ_ID = "readHistory"
READ_TYPE = "uipath.connector.uipath-salesforce-slack.get-message"


def _response(ts=TS, channel=CHANNEL):
    return {"ok": True, "channel": channel, "ts": ts, "message": {"type": "message", "ts": ts, "text": "alert"}}


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    project = tmp_path / "P" / "P"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"Name": "P", "ProjectType": "Flow"}))
    flow = {"nodes": [{"id": "start", "type": "core.trigger.manual"},
                      {"id": SEND_ID, "type": SEND_TYPE}, {"id": READ_ID, "type": READ_TYPE}], "edges": []}
    (project / "P.flow").write_text(json.dumps(flow))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(flow_check, "_DEBUG_ATTEMPT_RAWS", [])
    return tmp_path


def _envelope(globals_):
    return json.dumps({"Result": "Success", "Data": {"finalStatus": "Completed", "variables": {"globals": globals_}}})


def _last_run(monkeypatch, *raws):
    monkeypatch.setattr(flow_check, "_DEBUG_ATTEMPT_RAWS", list(raws))


def _journal(sandbox):
    return slack_journal.read_journal(sandbox / ".slack-posts.jsonl")


def test_a_normal_run_journals_the_send_nodes_post(sandbox, monkeypatch):
    def run():
        _last_run(monkeypatch, _envelope({f"{SEND_ID}.output": _response()}))

    with slack_journal.journal_slack_posts():
        run()
    assert _journal(sandbox) == [(CHANNEL, TS)]


def test_a_failed_run_still_journals_its_post(sandbox, monkeypatch):
    with pytest.raises(SystemExit):
        with slack_journal.journal_slack_posts():
            _last_run(monkeypatch, _envelope({f"{SEND_ID}.output": _response()}))
            sys.exit("FAIL: flow did not complete")
    assert _journal(sandbox) == [(CHANNEL, TS)]


def test_an_unparseable_run_journals_the_response_shaped_post(sandbox, monkeypatch):
    _last_run(monkeypatch, f"timeout, partial stdout {json.dumps(_response())} cut off {{")
    slack_journal.journal_last_debug()
    assert _journal(sandbox) == [(CHANNEL, TS)]


def test_a_retried_run_journals_the_earlier_attempts_post(sandbox, monkeypatch):
    first = _envelope({f"{SEND_ID}.output": _response()})
    second = _envelope({f"{SEND_ID}.output": _response(OTHER_TS)})
    _last_run(monkeypatch, first, second)
    slack_journal.journal_last_debug()
    assert _journal(sandbox) == [(CHANNEL, TS), (CHANNEL, OTHER_TS)]


def test_decoys_are_not_journaled(sandbox, monkeypatch):
    channel_only = {"channel": CHANNEL, "ts": OTHER_TS}
    globals_ = {
        f"{SEND_ID}.output": channel_only,
        f"{READ_ID}.output": _response(OTHER_TS),
        "start.output.echo": _response(OTHER_TS),
    }
    _last_run(monkeypatch, _envelope(globals_))
    slack_journal.journal_last_debug()
    assert _journal(sandbox) == []


def test_the_same_post_is_journaled_once(sandbox, monkeypatch):
    _last_run(monkeypatch, _envelope({f"{SEND_ID}.output": _response()}))
    slack_journal.journal_last_debug()
    slack_journal.journal_last_debug()
    assert _journal(sandbox) == [(CHANNEL, TS)]


def test_journalling_never_masks_the_runs_failure(sandbox, monkeypatch):
    (sandbox / "P" / "P" / "P.flow").unlink()
    _last_run(monkeypatch, _envelope({f"{SEND_ID}.output": _response()}))
    with pytest.raises(SystemExit, match="boom"):
        with slack_journal.journal_slack_posts():
            sys.exit("boom")


def test_a_swallowed_journal_error_warns_on_stderr(sandbox, monkeypatch, capsys):
    _last_run(monkeypatch, _envelope({f"{SEND_ID}.output": _response()}))
    monkeypatch.setattr(slack_journal, "read_journal", lambda: (_ for _ in ()).throw(OSError("disk")))
    slack_journal.journal_last_debug()
    err = capsys.readouterr().err
    assert err.count("WARN") == 1 and "disk" in err


def test_the_teardown_channel_is_the_graders_channel():
    from _shared.escalation_inputs import SLACK_CHANNEL
    assert teardown.CHANNEL_ID == SLACK_CHANNEL


def test_the_grader_and_teardown_share_the_journal_file():
    assert str(slack_journal.JOURNAL) == str(teardown.JOURNAL)


class FakeUip:
    def __init__(self, rows=None, fail=(), absent=(), not_ok=(), bare=()):
        self.rows, self.fail, self.absent = rows if rows is not None else [self.row()], set(fail), set(absent)
        self.not_ok = set(not_ok)
        self.bare = set(bare)
        self.deleted = []

    @staticmethod
    def row(**over):
        row = {"ConnectorKey": teardown.CONNECTOR_KEY, "Name": teardown.CONNECTION_NAME,
               "Folder": teardown.FOLDER_NAME, "State": "Enabled", "Id": CONNECTION}
        return {**row, **over}

    def __call__(self, args, timeout):
        if args[:3] == ["is", "connections", "list"]:
            body = {"Result": "Success", "Data": self.rows}
            return subprocess.CompletedProcess(args, 0, json.dumps(body), "")
        query = json.loads(args[args.index("--query") + 1])
        ts = query["timestampId"]
        self.deleted.append((query["conversationId"], ts, args[args.index("--connection-id") + 1]))
        if ts in self.absent:
            return subprocess.CompletedProcess(args, 1, json.dumps({"Result": "Failure", "Message": "message_not_found"}), "")
        if ts in self.fail:
            return subprocess.CompletedProcess(args, 1, json.dumps({"Result": "Failure", "Message": "500"}), "")
        if ts in self.not_ok:
            return subprocess.CompletedProcess(
                args, 0, json.dumps({"Result": "Success", "Data": {"ok": False, "error": "cant_delete_message"}}), "")
        if ts in self.bare:
            return subprocess.CompletedProcess(args, 0, json.dumps({"Result": "Success", "Data": {}}), "")
        return subprocess.CompletedProcess(args, 0, json.dumps({"Result": "Success", "Data": {"ok": True}}), "")


def _seed(sandbox, *posts):
    (sandbox / ".slack-posts.jsonl").write_text("".join(json.dumps(p) + "\n" for p in posts))


def test_teardown_deletes_each_journaled_pair_and_clears_the_journal(sandbox, monkeypatch, capsys):
    _seed(sandbox, [CHANNEL, TS], [CHANNEL, OTHER_TS], [CHANNEL, TS])
    fake = FakeUip()
    monkeypatch.setattr(teardown, "run_uip", fake)
    teardown.main()
    assert fake.deleted == [(CHANNEL, TS, CONNECTION), (CHANNEL, OTHER_TS, CONNECTION)]
    assert not (sandbox / ".slack-posts.jsonl").exists()


def test_teardown_treats_an_absent_message_as_deleted(sandbox, monkeypatch):
    _seed(sandbox, [CHANNEL, TS])
    fake = FakeUip(absent={TS})
    monkeypatch.setattr(teardown, "run_uip", fake)
    teardown.main()
    assert not (sandbox / ".slack-posts.jsonl").exists()


def test_teardown_retries_once_then_keeps_the_journal_and_continues(sandbox, monkeypatch, capsys):
    _seed(sandbox, [CHANNEL, TS], [CHANNEL, OTHER_TS])
    fake = FakeUip(fail={TS})
    monkeypatch.setattr(teardown, "run_uip", fake)
    teardown.main()
    assert [d[1] for d in fake.deleted] == [TS, TS, OTHER_TS]
    assert "could not confirm deletion" in capsys.readouterr().out
    assert (sandbox / ".slack-posts.jsonl").exists()


def test_teardown_does_not_count_a_slack_ok_false_as_deleted(sandbox, monkeypatch, capsys):
    _seed(sandbox, [CHANNEL, TS])
    monkeypatch.setattr(teardown, "run_uip", FakeUip(not_ok={TS}))
    teardown.main()
    assert "could not confirm deletion" in capsys.readouterr().out
    assert (sandbox / ".slack-posts.jsonl").exists()


def test_teardown_counts_a_success_without_slack_ok_as_deleted(sandbox, monkeypatch):
    _seed(sandbox, [CHANNEL, TS])
    monkeypatch.setattr(teardown, "run_uip", FakeUip(bare={TS}))
    teardown.main()
    assert not (sandbox / ".slack-posts.jsonl").exists()


def test_teardown_tolerates_a_dead_cli_and_bad_lines(sandbox, monkeypatch):
    (sandbox / ".slack-posts.jsonl").write_text("not json\n" + json.dumps([CHANNEL, TS]) + "\n[1]\n")
    monkeypatch.setattr(teardown, "run_uip", lambda args, timeout: None)
    teardown.main()
    assert (sandbox / ".slack-posts.jsonl").exists()


def test_teardown_needs_exactly_one_matching_connection(sandbox, monkeypatch):
    _seed(sandbox, [CHANNEL, TS])
    rows = [FakeUip.row(Folder="elsewhere"), FakeUip.row(State="Disabled")]
    fake = FakeUip(rows=rows)
    monkeypatch.setattr(teardown, "run_uip", fake)
    teardown.main()
    assert fake.deleted == []


def test_teardown_honors_the_cleanup_opt_out(sandbox, monkeypatch):
    _seed(sandbox, [CHANNEL, TS])
    fake = FakeUip()
    monkeypatch.setattr(teardown, "run_uip", fake)
    monkeypatch.setenv(teardown.CLEANUP_ENV, "never")
    teardown.main()
    assert fake.deleted == []
    assert (sandbox / ".slack-posts.jsonl").exists()


def test_teardown_stops_deleting_when_its_deadline_passes(sandbox, monkeypatch):
    _seed(sandbox, [CHANNEL, TS])
    fake = FakeUip()
    monkeypatch.setattr(teardown, "run_uip", fake)
    monkeypatch.setattr(teardown, "DEADLINE_SECONDS", -1)
    teardown.main()
    assert fake.deleted == []
    assert (sandbox / ".slack-posts.jsonl").exists()


def test_the_teardown_fits_the_post_run_timeout():
    assert teardown.LIST_TIMEOUT + teardown.DELETE_TIMEOUT < teardown.DEADLINE_SECONDS < 300


@pytest.mark.parametrize("yaml_path", [
    "e2e/escalation_slack_alert/escalation_slack_alert.yaml",
    "e2e/escalation_orchestrator_paths/escalation_orchestrator_paths.yaml",
    "multi_node/billing_resolution_writer/billing_resolution_writer.yaml",
])
def test_each_posting_task_runs_the_teardown_in_post_run(yaml_path):
    text = open(os.path.join(ROOT, yaml_path), encoding="utf-8").read()
    post_run = text.split("post_run:", 1)[1].split("initial_prompt:", 1)[0]
    assert "_setup/teardown_slack_posts.py" in post_run
    assert "timeout: 300" in post_run.split("teardown_slack_posts.py", 1)[1]


@pytest.mark.parametrize("grader", [
    "e2e/escalation_slack_alert/check_escalation_slack_alert.py",
    "e2e/escalation_orchestrator_paths/check_escalation_orchestrator_paths.py",
    "multi_node/billing_resolution_writer/check_billing_resolution_writer.py",
])
def test_each_posting_grader_journals_around_its_debug_run(grader):
    text = open(os.path.join(ROOT, grader), encoding="utf-8").read()
    assert "with journal_slack_posts():\n" in text
    guarded = text.split("with journal_slack_posts():\n", 1)[1].lstrip().split("\n", 1)[0]
    assert "run_debug(" in guarded


def test_teardown_reads_only_posts_in_the_test_channel(sandbox):
    _seed(sandbox, [CHANNEL, TS], ["C0OTHERCHAN", OTHER_TS], ["D0DIRECT", "1.2"])
    assert teardown.read_posts() == [(CHANNEL, TS)]
