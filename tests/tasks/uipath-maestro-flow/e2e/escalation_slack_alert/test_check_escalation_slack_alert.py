"""Unit tests for the EscalationSlackAlert effects grader.

The flows are cut down from what agents built on the 2026-11-17 nightly: a
manual trigger, a classifier, the real `send-message-to-channel` node (its
`detail` as the agent bound it) and an End. Payloads have the shape
`uip maestro flow debug --output json` returns: `elementExecutions` plus
`variables.globals` holding the named outputs and each node's `<id>.output`.
"""

from __future__ import annotations

import importlib.util
import json
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CHANNEL = "C0B2FDZD1M3"
TS = "1786647595.771239"


def _grader():
    spec = importlib.util.spec_from_file_location(
        "check_escalation_slack_alert", os.path.join(HERE, "check_escalation_slack_alert.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _slack_node(node_id: str, send_as: str = "user") -> dict:
    return {
        "id": node_id,
        "type": "uipath.connector.uipath-salesforce-slack.send-message-to-channel",
        "inputs": {
            "detail": {
                "connector": "uipath-salesforce-slack",
                "connectionId": "849e85d8-1aa9-4d52-8bbd-20041c8f05d8",
                "connectionFolderKey": "5da18ec0-7de1-4e57-aaf1-ddc8a369c199",
                "bodyParameters": {"channel": CHANNEL, "messageToSend": "=js:$vars.classify.output.message"},
                "queryParameters": {"send_as": send_as},
            }
        },
    }


def _write_project(root, nodes) -> None:
    project = root / "EscalationSlackAlert" / "EscalationSlackAlert"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"Name": "EscalationSlackAlert", "ProjectType": "Flow"}))
    (project / "new.flow").write_text(json.dumps({"nodes": nodes, "edges": []}))


CASE = {
    "name": "enterprise-production-down-sev1",
    "inputs": {"correlationId": "E2E-abc-SEV1", "customerTier": "Enterprise",
               "productionDown": True, "workaroundAvailable": False},
    "expected": {"severity": "Sev1", "engineeringNeeded": True, "caseKey": "E2E-abc-SEV1"},
}
NEXT_STEPS = "Page the on-call engineer and open a bridge."


def _payload(text: str, *, outputs: dict | None = None, executed=("start", "postSlackAlert", "end"),
             ts_out: str = TS) -> dict:
    globals_ = {
        "severity": "Sev1",
        "engineeringNeeded": True,
        "nextSteps": NEXT_STEPS,
        "caseKey": "E2E-abc-SEV1",
        "slackMessageId": TS,
        "postSlackAlert.output": {"ok": True, "channel": CHANNEL, "ts": ts_out, "message": {"text": text}},
    }
    globals_.update(outputs or {})
    return {
        "finalStatus": "Completed",
        "elementExecutions": [{"elementId": i, "status": "Completed"} for i in executed],
        "variables": {"globals": globals_},
    }


GOOD_TEXT = f"[SEV1] E2E-abc-SEV1 Production down. Next steps: {NEXT_STEPS}"


@pytest.fixture
def no_script_flow(tmp_path, monkeypatch):
    """Severity worked out in the End mapping and the message expression: no
    Script node at all. The request allows it; the old grader required a Script."""
    _write_project(tmp_path, [
        {"id": "start", "type": "core.trigger.manual"},
        _slack_node("postSlackAlert"),
        {"id": "end", "type": "core.control.end"},
    ])
    monkeypatch.chdir(tmp_path)


def test_passes_with_no_script_node_when_outputs_and_message_are_right(no_script_flow):
    assert _grader().check_case(_payload(GOOD_TEXT), CASE) == TS


def test_next_steps_rendered_as_a_list_still_count(no_script_flow):
    payload = _payload(
        "Sev1 alert for E2E-abc-SEV1\n- page the on-call engineer\n- open a bridge",
        outputs={"nextSteps": ["Page the on-call engineer", "Open a bridge"]},
    )
    _grader().check_case(payload, CASE)


def test_fails_when_the_message_leaves_out_the_next_steps(no_script_flow):
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(_payload("[Sev1] E2E-abc-SEV1 Production down."), CASE)
    assert "missing required field" in str(exc.value)


def test_fails_when_next_steps_is_not_returned(no_script_flow):
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(_payload(GOOD_TEXT, outputs={"nextSteps": ""}), CASE)
    assert "nextSteps" in str(exc.value)


def test_fails_when_the_tier_rule_is_ignored(no_script_flow):
    sev3 = {**CASE, "expected": {**CASE["expected"], "severity": "Sev3", "engineeringNeeded": False}}
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(_payload(GOOD_TEXT), sev3)
    assert "'severity'" in str(exc.value)


def test_fails_when_the_ts_was_not_returned_by_the_send_that_ran(no_script_flow):
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(_payload(GOOD_TEXT, ts_out="1786647000.000001"), CASE)
    assert "does not match any executed Slack node" in str(exc.value)


def test_fails_when_the_slack_send_did_not_run(no_script_flow):
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(_payload(GOOD_TEXT, executed=("start", "end")), CASE)
    assert "no uipath-salesforce-slack node completed" in str(exc.value)


def test_main_runs_every_seeded_case(no_script_flow, tmp_path, monkeypatch):
    grader = _grader()
    sev3_case = {
        "name": "standard-production-down-sev3",
        "inputs": {**CASE["inputs"], "correlationId": "E2E-abc-SEV3", "customerTier": "Standard"},
        "expected": {"severity": "Sev3", "engineeringNeeded": False, "caseKey": "E2E-abc-SEV3"},
    }
    (tmp_path / "seed.json").write_text(json.dumps({"cases": [CASE, sev3_case]}))
    sev3_payload = _payload(
        f"Sev3 E2E-abc-SEV3. Next steps: {NEXT_STEPS}",
        outputs={"severity": "Sev3", "engineeringNeeded": False, "caseKey": "E2E-abc-SEV3"},
    )
    payloads = iter([_payload(GOOD_TEXT), sev3_payload])
    calls = []

    def fake_debug(**kwargs):
        calls.append(kwargs["inputs"]["correlationId"])
        return next(payloads)

    monkeypatch.setattr(grader, "run_debug", fake_debug)
    grader.main()
    assert calls == ["E2E-abc-SEV1", "E2E-abc-SEV3"]


def test_main_rejects_a_bot_send(tmp_path, monkeypatch):
    _write_project(tmp_path, [
        {"id": "start", "type": "core.trigger.manual"},
        _slack_node("postSlackAlert", send_as="bot"),
        {"id": "end", "type": "core.control.end"},
    ])
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        _grader().main()
    assert "send_as" in str(exc.value)
