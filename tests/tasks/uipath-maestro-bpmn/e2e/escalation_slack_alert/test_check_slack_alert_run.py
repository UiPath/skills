"""check_slack_alert_run.py grades the run's Slack post and named outputs.

`fixtures/Process.bpmn` and `fixtures/run_seed.json` are the agent's process and
the seed from Studio Web run adhoc-2026-11-17_15-00-15 (passed). The runtime
payloads follow the shape `debug-instance variables-all` returns: PascalCase
Globals, each element's own `Outputs`, the Slack step's `Response` carrying
`ts`, `channel` and `message.text`.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


checker = _load("check_slack_alert_run", HERE / "check_slack_alert_run.py")
from _shared.bpmn_live import DebugEvidence  # noqa: E402

BPMN_TEXT = (FIXTURES / "Process.bpmn").read_text()
SEED = json.loads((FIXTURES / "run_seed.json").read_text())
CASE = SEED["cases"][0]
CORR = CASE["inputs"]["correlationId"]
TS = "1763405123.456789"


@pytest.fixture(autouse=True)
def _live_target(monkeypatch):
    monkeypatch.setattr(checker.escalation_is, "assert_live_target", lambda: {})


def _process(text: str = BPMN_TEXT) -> ET.Element:
    return ET.fromstring(text.encode()).find(f"{{{checker.BPMN_NS}}}process")


def _debug(slack_status="Completed"):
    return {
        "InstanceId": "inst-1",
        "FinalStatus": "Completed",
        "ElementExecutions": [
            {"ElementId": "start", "ElementType": "StartEvent", "Status": "Completed"},
            {"ElementId": "classify", "ElementType": "ScriptTask", "Status": "Completed"},
            {"ElementId": "sendSlackAlert", "ElementType": "SendTask", "Status": slack_status},
            {"ElementId": "done", "ElementType": "EndEvent", "Status": "Completed"},
        ],
    }


def _variables(*, text=None, channel="C0B2FDZD1M3", message_id=TS, next_steps_key="nextSteps", engineering=True):
    text = text or f"Escalation alert | Severity: Sev1 | Correlation ID: {CORR} | Next steps: Page on-call."
    response = {"ok": True, "channel": channel, "ts": TS, "message": {"text": text, "ts": TS}}
    outputs = {"Severity": "Sev1", "EngineeringNeeded": engineering, "CaseKey": CORR, "SlackMessageId": message_id}
    return {
        "Variables": [
            {
                "ParentElementId": None,
                "Globals": {
                    "CorrelationId": CORR,
                    "SeverityValue": "Sev1",
                    "EngineeringNeededValue": True,
                    "PostedSlackMessageId": TS,
                    **outputs,
                },
                "Elements": [
                    {"ElementId": "classify", "Outputs": {"Response": {
                        "severity": "Sev1", "engineeringNeeded": True, next_steps_key: "Page on-call.", "correlationId": CORR}}},
                    {"ElementId": "sendSlackAlert", "Outputs": {"Response": response}},
                    {"ElementId": "done", "Outputs": outputs},
                ],
            }
        ]
    }


def test_real_shape_passes():
    assert checker.assert_outcome(_process(), CASE, _debug(), _variables()) == TS


def test_rule_is_encoded_in_the_real_process():
    checker.assert_rule_encoded(BPMN_TEXT)
    with pytest.raises(checker.CheckFailure, match="never names"):
        checker.assert_rule_encoded(BPMN_TEXT.replace("Sev2", "SevX").replace("Sev3", "SevY"))


def test_a_next_steps_field_name_the_request_never_gives_is_not_required():
    """The request only asks for next steps in the message, not a field named
    `nextSteps` on the classifier."""
    checker.assert_outcome(_process(), CASE, _debug(), _variables(next_steps_key="followUp"))


@pytest.mark.parametrize("value", ["yes", "Yes", "YES", "true"])
def test_engineering_needed_yes_reads_as_true(value):
    checker.assert_outcome(_process(), CASE, _debug(), _variables(engineering=value))


@pytest.mark.parametrize("value", ["no", "No", "false"])
def test_engineering_needed_no_fails_where_true_is_expected(value):
    with pytest.raises(checker.CheckFailure, match="engineeringNeeded"):
        checker.assert_outcome(_process(), CASE, _debug(), _variables(engineering=value))


def test_engineering_needed_number_is_not_a_boolean():
    with pytest.raises(checker.CheckFailure, match="engineeringNeeded"):
        checker.assert_outcome(_process(), CASE, _debug(), _variables(engineering=1))


def test_slack_step_found_by_connector_key_alone():
    assert checker.slack_ids(_process()) == {"sendSlackAlert"}


def test_message_id_must_be_the_posted_ts():
    with pytest.raises(checker.CheckFailure, match="not the ts"):
        checker.assert_outcome(_process(), CASE, _debug(), _variables(message_id="1700000000.000001"))


def test_two_distinct_posted_messages_fail():
    variables = _variables()
    second = {"ok": True, "channel": "C0B2FDZD1M3", "ts": "1763405999.000001", "message": {"text": CORR}}
    variables["Variables"][0]["Elements"].append({"ElementId": "sendSlackAlert", "Outputs": {"Response": second}})
    with pytest.raises(checker.CheckFailure, match="exactly one posted"):
        checker.assert_outcome(_process(), CASE, _debug(), variables)


def test_main_checks_the_live_target_before_any_debug(tmp_path, monkeypatch):
    _studio_web_sandbox(tmp_path, monkeypatch, BPMN_TEXT)

    def refuse():
        raise checker.CheckFailure("wrong tenant")

    def no_debug(*a, **k):
        raise AssertionError("debug ran before the target check")

    monkeypatch.setattr(checker.escalation_is, "assert_live_target", refuse)
    monkeypatch.setattr(checker, "run_debug", no_debug)
    monkeypatch.setattr(checker, "import_exact", no_debug)
    with pytest.raises(checker.CheckFailure, match="wrong tenant"):
        checker.main()


def test_wrong_channel_fails():
    with pytest.raises(checker.CheckFailure, match="channel"):
        checker.assert_outcome(_process(), CASE, _debug(), _variables(channel="C999"))


def test_message_without_the_correlation_id_fails():
    with pytest.raises(checker.CheckFailure, match="does not carry"):
        checker.assert_outcome(_process(), CASE, _debug(), _variables(text="Severity: Sev1"))


def test_a_slack_step_that_did_not_complete_fails():
    with pytest.raises(checker.CheckFailure, match="no Slack step completed"):
        checker.assert_outcome(_process(), CASE, _debug(slack_status="Faulted"), _variables())


def test_bot_identity_fails():
    bot = BPMN_TEXT.replace('{"send_as":"user"}', '{"send_as":"bot"}')
    with pytest.raises(checker.CheckFailure, match="as 'user'"):
        checker.assert_outcome(_process(bot), CASE, _debug(), _variables())


def test_wrong_severity_fails():
    variables = _variables()
    scope = variables["Variables"][0]
    scope["Globals"]["Severity"] = "Sev2"
    scope["Elements"][2]["Outputs"]["Severity"] = "Sev2"
    with pytest.raises(checker.CheckFailure, match="severity"):
        checker.assert_outcome(_process(), CASE, _debug(), variables)


def _studio_web_sandbox(tmp_path, monkeypatch, bpmn_text: str) -> list:
    project = tmp_path / "EscalationSlackAlert" / "EscalationSlackAlert"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text('{"Name": "EscalationSlackAlert", "ProjectType": "ProcessOrchestration"}')
    (project / "Process.bpmn").write_text(bpmn_text)
    (tmp_path / "seed.json").write_text(json.dumps(SEED))
    monkeypatch.chdir(tmp_path)
    sent = []
    monkeypatch.setattr(checker, "import_exact", lambda bpmn, project_dir, solution: project_dir)
    monkeypatch.setattr(checker, "run_debug", lambda p, inputs, log, **k: (sent.append(inputs), (_debug(), "inst-1"))[1])
    monkeypatch.setattr(checker, "debug_evidence", lambda i: DebugEvidence(_variables(), "", [], []))
    return sent


def test_main_in_a_studio_web_layout(tmp_path, monkeypatch):
    sent = _studio_web_sandbox(tmp_path, monkeypatch, BPMN_TEXT)
    checker.main()
    assert sent == [CASE["inputs"]]


def test_main_journals_the_message_the_run_posted(tmp_path, monkeypatch):
    _studio_web_sandbox(tmp_path, monkeypatch, BPMN_TEXT)
    checker.main()
    lines = (tmp_path / ".created-ids.jsonl").read_text().splitlines()
    assert [json.loads(line) for line in lines] == [{"kind": "slack_message", "value": ["C0B2FDZD1M3", TS]}]


def test_a_run_that_fails_grading_still_journals_its_message(tmp_path, monkeypatch):
    _studio_web_sandbox(tmp_path, monkeypatch, BPMN_TEXT)
    monkeypatch.setattr(checker, "debug_evidence", lambda i: DebugEvidence(_variables(text="no ids"), "", [], []))
    with pytest.raises(checker.CheckFailure):
        checker.main()
    assert (tmp_path / ".created-ids.jsonl").is_file()


@pytest.mark.parametrize("fail_at", ["debug", "evidence"])
def test_a_failed_run_journals_the_posts_in_its_log(tmp_path, monkeypatch, fail_at):
    _studio_web_sandbox(tmp_path, monkeypatch, BPMN_TEXT)
    posted = json.dumps(_variables()["Variables"][0]["Elements"][1]["Outputs"])
    other = json.dumps({"channel": "C0B2FDZD1M3", "ts": "1763400000.000001"})

    def run_debug(project_dir, inputs, log, **k):
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        Path(log).write_text(f"{posted}\n{other}\n")
        if fail_at == "debug":
            raise checker.CheckFailure("debug stopped waiting")
        return _debug(), "inst-1"

    def evidence(instance_id):
        raise subprocess.TimeoutExpired("uip", 120)

    monkeypatch.setattr(checker, "run_debug", run_debug)
    if fail_at == "evidence":
        monkeypatch.setattr(checker, "debug_evidence", evidence)
    with pytest.raises((checker.CheckFailure, subprocess.TimeoutExpired)):
        checker.main()
    lines = (tmp_path / ".created-ids.jsonl").read_text().splitlines()
    assert [json.loads(line) for line in lines] == [{"kind": "slack_message", "value": ["C0B2FDZD1M3", TS]}]


def test_post_run_replays_the_journal_within_the_post_run_cap():
    import yaml

    task = yaml.safe_load((HERE / "escalation_slack_alert.yaml").read_text())
    sweeps = [step for step in task["post_run"] if "teardown_escalation.py" in step["command"]]
    assert len(sweeps) == 1
    assert sweeps[0]["timeout"] <= 300


def test_main_fails_a_process_that_only_knows_the_seeded_severity(tmp_path, monkeypatch):
    """The seeded Sev1 run alone cannot tell a classifier from a constant."""
    sent = _studio_web_sandbox(tmp_path, monkeypatch, BPMN_TEXT.replace("Sev2", "SevX").replace("Sev3", "SevY"))
    with pytest.raises(checker.CheckFailure, match="never names"):
        checker.main()
    assert sent == []
