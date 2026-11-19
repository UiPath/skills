"""Unit tests for the EscalationSlackAlert effects grader.

Flows carry `variables.globals` and a real `send-message-to-channel` node as
agents build them; one uses the input names of a named-variable prompt, the
other names an agent might pick. Payloads have the shape
`uip maestro flow debug --output json` returns: `elementExecutions`, the
declared outputs in `variables.globals`, inputs as `start.output.<id>`, and the
Slack node's response under `<id>.output` with `ts`, `channel` and
`message.text`/`message.blocks`.
"""

from __future__ import annotations

import importlib.util
import json
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CHANNEL = "C0B2FDZD1M3"
TS = "1794932449.166699"
REF = "ESC-abc123-1"


def _module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grader():
    return _module("check_escalation_slack_alert", os.path.join(HERE, "check_escalation_slack_alert.py"))


def _seed_cases():
    return _module("slack_alert_seed", os.path.join(HERE, "_setup", "seed.py")).build_seed()["cases"]


SLACK_NODE = {
    "id": "postAlert",
    "type": "uipath.connector.uipath-salesforce-slack.send-message-to-channel",
    "inputs": {
        "detail": {
            "connector": "uipath-salesforce-slack",
            "endpoint": "/send_message_to_channel_v2",
            "connectionId": "849e85d8-1aa9-4d52-8bbd-20041c8f05d8",
            "connectionFolderKey": "5da18ec0-7de1-4e57-aaf1-ddc8a369c199",
            "bodyParameters": {"channel": CHANNEL, "messageToSend": "=js:$vars.triage.output.message"},
        }
    },
}
# The input names an agent declares for a named-variable prompt.
NIGHTLY_IO = (
    [("senderEmail", "string"), ("subject", "string"), ("body", "string"), ("customerTier", "string"),
     ("productionDown", "boolean"), ("workaroundAvailable", "boolean"), ("correlationId", "string")],
    [("severity", "string"), ("engineeringNeeded", "boolean"), ("caseKey", "string"),
     ("slackMessageId", "string")],
)
# Names a v3 agent might pick from the business prompt.
V3_IO = (
    [("senderEmailAddress", "string"), ("emailSubject", "string"), ("emailBody", "string"),
     ("tier", "string"), ("isProductionDown", "boolean"), ("hasWorkaround", "boolean"),
     ("caseReference", "string")],
    [("severityLevel", "string"), ("requiresEngineering", "boolean"), ("caseRef", "string"),
     ("slackTs", "string")],
)


def _flow(io_names) -> dict:
    ins, outs = io_names
    return {
        "nodes": [{"id": "start", "type": "core.trigger.manual"},
                  {"id": "triage", "type": "core.action.script"},
                  SLACK_NODE,
                  {"id": "end", "type": "core.control.end"}],
        "edges": [],
        "variables": {"globals": [
            *({"id": i, "name": i, "direction": "in", "type": t, "triggerNodeId": "start"} for i, t in ins),
            *({"id": o, "name": o, "direction": "out", "type": t} for o, t in outs),
        ]},
    }


def _write_project(root, flow) -> None:
    project = root / "EscalationSlackAlert" / "EscalationSlackAlert"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"Name": "EscalationSlackAlert", "ProjectType": "Flow"}))
    (project / "EscalationSlackAlert.flow").write_text(json.dumps(flow))


def _text(severity: str, ref: str, steps=("Page the on-call engineer", "Open an incident bridge")) -> str:
    return f":rotating_light: *{severity}* | {ref}\n" + "\n".join(f"• {s}" for s in steps)


def _payload(io_names, *, severity="Sev1", engineering=True, ref=REF, text=None, ts=TS,
             posted_ts=None, executed=("start", "triage", "postAlert", "end")) -> dict:
    _ins, outs = io_names
    sev_out, eng_out, ref_out, ts_out = (o for o, _t in outs)
    text = _text(severity, ref) if text is None else text
    posted_ts = posted_ts or ts
    return {
        "finalStatus": "Completed",
        "elementExecutions": [{"elementId": i, "status": "Completed"} for i in executed],
        "variables": {"globals": {
            "start.output.customerTier": "Enterprise",
            sev_out: severity,
            eng_out: engineering,
            ref_out: ref,
            ts_out: ts,
            "postAlert.output": {
                "ts": posted_ts, "warning": "missing_charset", "channel": CHANNEL, "ok": True,
                "message": {"type": "message", "ts": posted_ts, "bot_id": "B0BB8SFGWAZ", "text": text,
                            "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]},
                "response_metadata": {"warnings": ["missing_charset"]},
            },
        }},
    }


CASE = {"name": "enterprise-down-no-workaround-sev1",
        "inputs": {"senderEmail": "jane.doe@acmecorp.com", "subject": "Production down", "body": "All down.",
                   "tier": "Enterprise", "productionDown": True, "workaround": False, "caseRef": REF},
        "expected": {"severity": "Sev1", "engineering": True}}


@pytest.fixture
def v3(tmp_path, monkeypatch):
    _write_project(tmp_path, _flow(V3_IO))
    monkeypatch.chdir(tmp_path)
    return _grader()


def test_seeded_values_map_onto_the_names_the_agent_picked():
    grader = _grader()
    assert grader.feed(_flow(V3_IO), CASE) == {
        "senderEmailAddress": "jane.doe@acmecorp.com", "emailSubject": "Production down",
        "emailBody": "All down.", "tier": "Enterprise", "isProductionDown": True,
        "hasWorkaround": False, "caseReference": REF,
    }
    assert grader.feed(_flow(NIGHTLY_IO), CASE) == {
        "senderEmail": "jane.doe@acmecorp.com", "subject": "Production down", "body": "All down.",
        "customerTier": "Enterprise", "productionDown": True, "workaroundAvailable": False,
        "correlationId": REF,
    }


def test_a_yes_no_input_declared_as_text_gets_lowercase_true_false():
    ins, outs = V3_IO
    flow = _flow(([(i, "string") for i, _t in ins], outs))
    inputs = _grader().feed(flow, CASE)
    assert inputs["isProductionDown"] == "true" and inputs["hasWorkaround"] == "false"


def test_a_role_with_no_input_fails_naming_the_inputs():
    ins, outs = V3_IO
    flow = _flow(([(i, t) for i, t in ins if i != "tier"], outs))
    with pytest.raises(SystemExit) as exc:
        _grader().feed(flow, CASE)
    assert "could not map tier onto inputs ['senderEmailAddress'" in str(exc.value)


def test_passes_with_outputs_found_by_value_under_any_name(v3):
    holders = v3.check_case(_flow(V3_IO), _payload(V3_IO), CASE)
    assert holders == {"severity": ["severityLevel"], "engineering needed": ["requiresEngineering"],
                       "case reference": ["caseRef"], "Slack message id": ["slackTs"]}


def test_fails_when_a_standard_outage_is_not_sev3(v3):
    sev3 = {**CASE, "inputs": {**CASE["inputs"], "tier": "Standard"},
            "expected": {"severity": "Sev3", "engineering": False}}
    with pytest.raises(SystemExit) as exc:
        v3.check_case(_flow(V3_IO), _payload(V3_IO), sev3)
    assert "no declared output is 'Sev3' (severity)" in str(exc.value)


def test_fails_when_the_case_reference_is_changed(v3):
    with pytest.raises(SystemExit) as exc:
        v3.check_case(_flow(V3_IO), _payload(V3_IO, ref=REF.lower()), CASE)
    assert "(case reference)" in str(exc.value)


def test_fails_when_the_first_line_lacks_the_case_reference(v3):
    text = "Escalation alert\nSev1 " + REF + "\n• Page on-call\n• Open a bridge"
    with pytest.raises(SystemExit) as exc:
        v3.check_case(_flow(V3_IO), _payload(V3_IO, text=text), CASE)
    assert "does not start with a line carrying the case reference" in str(exc.value)


def test_fails_when_the_first_line_lacks_the_severity(v3):
    text = f"New escalation {REF}\nSeverity Sev1\n- Page on-call\n- Open a bridge"
    with pytest.raises(SystemExit) as exc:
        v3.check_case(_flow(V3_IO), _payload(V3_IO, text=text), CASE)
    assert "first line does not carry the severity" in str(exc.value)


@pytest.mark.parametrize("steps", [("Page on-call",), ("a", "b", "c", "d")], ids=["one", "four"])
def test_fails_unless_two_or_three_bulleted_next_steps_follow(v3, steps):
    with pytest.raises(SystemExit) as exc:
        v3.check_case(_flow(V3_IO), _payload(V3_IO, text=_text("Sev1", REF, steps)), CASE)
    assert "two or three next steps as bullets" in str(exc.value)


def test_numbered_or_dashed_steps_count_as_the_list(v3):
    text = f"[SEV-1] {REF}\nNext steps:\n1. Page on-call\n2. Open a bridge\n3. Update the customer"
    v3.check_case(_flow(V3_IO), _payload(V3_IO, text=text), CASE)


def test_a_node_that_only_echoes_the_ts_is_not_taken_for_the_send(v3):
    payload = _payload(V3_IO)
    globals_ = payload["variables"]["globals"]
    payload["variables"]["globals"] = {"triage.output": {"slackMessageId": TS, "severity": "Sev1"}, **globals_}
    v3.check_case(_flow(V3_IO), payload, CASE)


def test_fails_when_the_ts_was_not_returned_by_the_send_that_ran(v3):
    with pytest.raises(SystemExit) as exc:
        v3.check_case(_flow(V3_IO), _payload(V3_IO, posted_ts="1794932000.000001"), CASE)
    assert "does not match any executed Slack node" in str(exc.value)


def test_fails_when_the_slack_send_did_not_run(v3):
    with pytest.raises(SystemExit) as exc:
        v3.check_case(_flow(V3_IO), _payload(V3_IO, executed=("start", "triage", "end")), CASE)
    assert "no uipath-salesforce-slack node completed" in str(exc.value)


def test_fails_when_no_one_output_holds_a_result_in_every_case(v3):
    # Two boolean outputs that each happen to fit one case: neither is the answer.
    per_case = [{"engineering needed": ["requiresEngineering", "slackOk"]},
                {"engineering needed": ["slackFailed"]}]
    with pytest.raises(SystemExit) as exc:
        v3.check_same_outputs(per_case)
    assert "no single output holds the engineering needed in every case" in str(exc.value)


def test_main_runs_every_seeded_case_with_the_agents_input_names(v3, tmp_path, monkeypatch):
    cases = _seed_cases()
    (tmp_path / "seed.json").write_text(json.dumps({"cases": cases}))
    payloads = iter([
        _payload(V3_IO, severity=c["expected"]["severity"], engineering=c["expected"]["engineering"],
                 ref=c["inputs"]["caseRef"], ts=f"17949324{n:02d}.166699")
        for n, c in enumerate(cases)
    ])
    calls = []

    def fake_debug(**kwargs):
        calls.append(kwargs["inputs"])
        return next(payloads)

    monkeypatch.setattr(v3, "run_debug", fake_debug)
    v3.main()
    assert [c["caseReference"] for c in calls] == [c["inputs"]["caseRef"] for c in cases]
    assert [(c["tier"], c["isProductionDown"], c["hasWorkaround"]) for c in calls] == [
        ("Enterprise", True, False), ("Standard", True, False), ("Standard", True, True)]


def test_seed_expects_v3_severities():
    expected = {c["name"]: (c["expected"]["severity"], c["expected"]["engineering"]) for c in _seed_cases()}
    assert expected == {"enterprise-down-no-workaround-sev1": ("Sev1", True),
                        "standard-down-no-workaround-sev3": ("Sev3", False),
                        "standard-down-with-workaround-sev2": ("Sev2", True)}


def test_posted_texts_reads_a_payload_with_capitalized_variable_keys(v3):
    payload = _payload(V3_IO)
    payload["Variables"] = {"Globals": payload.pop("variables")["globals"]}
    assert _text("Sev1", REF) in v3.posted_texts(payload, TS)
