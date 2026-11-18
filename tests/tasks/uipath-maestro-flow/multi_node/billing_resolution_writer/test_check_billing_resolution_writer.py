"""Checker-level tests for check_billing_resolution_writer.py.

Only `run_debug` is replaced. The flow on disk is the task's reference flow
(an inline agent and a Slack send-message-to-channel node), with its variables
renamed the way an agent working from the v3 prompt might name them, so the
mapping by meaning, the trace lookups and the Slack read-back run for real.

Payloads follow the 2026-11-17 Studio Web run of this task
(adhoc-2026-11-17_15-00-15): the agent's `{subject, body}` at
`<agent>.output`, the Slack response `{ts, channel, message: {text, bot_profile}}`
at `<send>.output` (posted by the bot), and the flow's outputs as globals.

The packed-JSON case pins run adhoc-2026-09-23_16-15-07: the agent returned its
whole answer as one JSON string in `body`, which every substring check passes.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_billing_resolution_writer.py"
REFERENCE_FLOW = HERE / "BillingResolutionWriter.reference.flow"

AGENT_ID = "resolutionWriter"  # the reference flow's uipath.agent.autonomous node
SLACK_ID = "postResolution"  # its Slack send-message-to-channel node
TS = "1794932449.166699"
CHANNEL = "C0B2FDZD1M3"
RENAMES = {"customerName": "customer", "invoiceNumber": "invoice", "creditAmount": "approvedCreditUsd",
           "correlationId": "caseReference", "emailSubject": "subject", "emailBody": "body",
           "caseKey": "caseRefOut", "slackMessageId": "slackTs"}

PLAIN_BODY = (
    "Dear Northwind Traders,\n\nWe have completed our review of invoice MCS-2026-04872 "
    "and approved a credit of USD 1,610.00.\n\nThe credit will appear on your next statement.\n\n"
    "Kind regards,\nBilling Support Team"
)
SUBJECT = "Resolution of your billing dispute on invoice MCS-2026-04872"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_billing_resolution_writer", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    text = REFERENCE_FLOW.read_text()
    for old, new in RENAMES.items():
        text = text.replace(f'"{old}"', f'"{new}"').replace(f".{old}", f".{new}")
    project = tmp_path / "BillingResolutionWriter" / "BillingResolutionWriter"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    (project / "new.flow").write_text(text)
    monkeypatch.chdir(tmp_path)
    return project


def _payload(inputs, *, subject=SUBJECT, body=PLAIN_BODY, slack_text=None, case_out=None):
    case_ref = inputs["caseReference"]
    agent_output = {"subject": subject, "body": body}
    slack_output = {
        "ts": TS, "channel": CHANNEL, "ok": True,
        "message": {"type": "message", "ts": TS, "text": slack_text or f"{case_ref}\n\n{body}",
                    "bot_profile": {"name": "Coder Evals"}},
    }
    return {
        "finalStatus": "Completed",
        "elementExecutions": [
            {"elementId": "start", "elementType": "StartEvent", "status": "Completed"},
            {"elementId": AGENT_ID, "elementType": "ServiceTask", "status": "Completed"},
            {"elementId": SLACK_ID, "elementType": "SendTask", "status": "Completed"},
            {"elementId": "doneSuccess", "elementType": "EndEvent", "status": "Completed"},
        ],
        "variables": {"globals": {
            **{f"start.output.{k}": v for k, v in inputs.items()},
            f"{AGENT_ID}.output": agent_output,
            f"{SLACK_ID}.output": slack_output,
            "subject": subject, "body": body,
            "caseRefOut": case_out if case_out is not None else case_ref,
            "slackTs": TS,
        }},
    }


def _run(monkeypatch, **kw):
    checker = _load_checker()
    sent = {}

    def fake(*, inputs, **_):
        sent.update(inputs)
        return _payload(inputs, **kw)

    monkeypatch.setattr(checker, "run_debug", fake)
    checker.main()
    return checker, sent


def test_inputs_are_mapped_by_meaning(sandbox, monkeypatch):
    checker, sent = _run(monkeypatch)
    assert sent == {"customer": "Northwind Traders", "invoice": "MCS-2026-04872",
                    "approvedCreditUsd": 1610, "caseReference": checker.CASE_REF}


def test_a_signed_prose_email_posted_by_the_bot_passes(sandbox, monkeypatch, capsys):
    _run(monkeypatch)
    out = capsys.readouterr().out
    assert "came back unchanged" in out and "posted to #coding-agent-testing" in out


def test_the_credit_not_written_as_usd_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, body=PLAIN_BODY.replace("USD 1,610.00", "$1,610"))
    assert "USD 1,610.00" in str(exc.value)


def test_an_unsigned_email_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, body=PLAIN_BODY.replace("Billing Support Team", "Billing"))
    assert "not signed" in str(exc.value)


def test_packed_json_email_body_fails(sandbox, monkeypatch):
    packed = json.dumps({"subject": SUBJECT, "body": PLAIN_BODY}, separators=(",", ":"))
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, subject="Billing dispute resolution email drafted", body=packed)
    assert "serialized JSON object" in str(exc.value)


def test_a_multi_line_subject_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, subject="Resolution\nInvoice MCS-2026-04872")
    assert "one-line email subject" in str(exc.value)


def test_a_changed_case_reference_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, case_out="RESO-other")
    assert "unchanged" in str(exc.value)


def test_a_slack_message_that_does_not_start_with_the_case_reference_fails(sandbox, monkeypatch):
    checker = _load_checker()
    monkeypatch.setattr(checker, "run_debug", lambda *, inputs, **_: _payload(
        inputs, slack_text=f"{PLAIN_BODY}\n\nCase {inputs['caseReference']}"))
    with pytest.raises(SystemExit) as exc:
        checker.main()
    assert "does not start with the case reference" in str(exc.value)


def test_a_slack_message_without_the_body_fails(sandbox, monkeypatch):
    checker = _load_checker()
    monkeypatch.setattr(checker, "run_debug", lambda *, inputs, **_: _payload(
        inputs, slack_text=f"{inputs['caseReference']} credit approved for MCS-2026-04872"))
    with pytest.raises(SystemExit) as exc:
        checker.main()
    assert "missing required text" in str(exc.value)
