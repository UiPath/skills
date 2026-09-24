"""Checker-level tests for check_billing_resolution_writer.py.

The case these pin: on 2026-09-23 (run adhoc-2026-09-23_16-15-07, v2 arm) the
inline agent's prompt asked for JSON text while its `returns` declared
`{ subject, body }`, and the runtime returned

    subject: "Billing dispute resolution email drafted"
    body:    '{"subject":"Resolution for Invoice INV-2026-0042","body":"Dear …"}'

in 3 of 3 debug runs. Mapped straight through, that blob passes every assert the
checker had: the invoice and credit substrings are inside the JSON, the blob IS a
leaf of the executed agent's output, and the Slack message carries body[:80]. So
the checker gave full credit to a JSON blob as the customer email (the likely
false passes on 08-31_01, 08-31_22 and 09-02).

Only `run_debug` is replaced. The flow on disk is the task's own reference flow,
so every source-structure and Slack assert runs for real against the payload.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_billing_resolution_writer.py"
REFERENCE_FLOW = HERE / "BillingResolutionWriter.reference.flow"

AGENT_ID = "resolutionWriter"  # the reference flow's uipath.agent.autonomous node
SLACK_ID = "postResolution"  # its Slack send-message-to-channel node
TS = "1790180467.760159"
CHANNEL = "C0B2FDZD1M3"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_billing_resolution_writer", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """A solution tree holding the reference flow, as the agent's sandbox would."""
    project = tmp_path / "BillingResolutionWriter" / "BillingResolutionWriter"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    shutil.copy(REFERENCE_FLOW, project / "BillingResolutionWriter.flow")
    monkeypatch.chdir(tmp_path)
    return project


def _payload(checker, *, subject: str, body: str) -> dict:
    """The 09-23 v2 debug envelope's `Data`, with this run's inputs, the agent's
    output mapped straight to emailSubject/emailBody, and the Slack text built
    the way the task asks (correlationId prefix + the body verbatim)."""
    slack_text = f"{checker.CORRELATION_ID}: {body}"
    agent_output = {"subject": subject, "body": body}
    slack_output = {
        "ts": TS,
        "channel": CHANNEL,
        "ok": True,
        "message": {"type": "message", "ts": TS, "text": slack_text},
    }
    return {
        "finalStatus": "Completed",
        "elementExecutions": [
            {"elementId": "start", "elementType": "StartEvent", "status": "Completed"},
            {"elementId": AGENT_ID, "elementType": "ServiceTask", "status": "Completed"},
            {"elementId": SLACK_ID, "elementType": "SendTask", "status": "Completed"},
            {"elementId": "doneSuccess", "elementType": "EndEvent", "status": "Completed"},
        ],
        "variables": {
            "elements": [
                {"elementId": AGENT_ID, "outputs": agent_output},
                {"elementId": SLACK_ID, "outputs": {"response": slack_output}},
            ],
            "globals": {
                "start.output.customerName": "Northwind Traders",
                "start.output.invoiceNumber": checker.INVOICE,
                "start.output.creditAmount": 1610,
                "start.output.correlationId": checker.CORRELATION_ID,
                f"{AGENT_ID}.output": agent_output,
                f"{AGENT_ID}.error": None,
                f"{SLACK_ID}.output": slack_output,
                "emailSubject": subject,
                "emailBody": body,
                "caseKey": checker.CORRELATION_ID,
                "slackMessageId": TS,
            },
        },
    }


PLAIN_BODY = (
    "Dear Northwind Traders,\n\nWe have completed our review of invoice MCS-2026-04872 "
    "and approved a credit of $1,610.\n\nBest regards,\nBilling Support"
)
# The 09-23 cmd 23 shape, with this task's invoice and credit.
PACKED_BODY = json.dumps(
    {"subject": "Resolution for Invoice MCS-2026-04872", "body": PLAIN_BODY},
    separators=(",", ":"),
)


def test_plain_prose_email_passes(sandbox, monkeypatch, capsys):
    checker = _load_checker()
    payload = _payload(checker, subject="Resolution for Invoice MCS-2026-04872", body=PLAIN_BODY)
    monkeypatch.setattr(checker, "run_debug", lambda **_: payload)
    checker.main()
    assert "OK: Slack message posted" in capsys.readouterr().out


def test_packed_json_email_body_fails(sandbox, monkeypatch):
    checker = _load_checker()
    payload = _payload(checker, subject="Billing dispute resolution email drafted", body=PACKED_BODY)
    monkeypatch.setattr(checker, "run_debug", lambda **_: payload)
    with pytest.raises(SystemExit) as exc:
        checker.main()
    assert "emailBody is a serialized JSON object (keys: subject, body)" in str(exc.value)


def test_packed_json_email_subject_fails(sandbox, monkeypatch):
    # The 2026-08-31_06 mirror image: the JSON went into `subject`.
    checker = _load_checker()
    payload = _payload(checker, subject=PACKED_BODY, body=PLAIN_BODY)
    monkeypatch.setattr(checker, "run_debug", lambda **_: payload)
    with pytest.raises(SystemExit) as exc:
        checker.main()
    assert "emailSubject is a serialized JSON object" in str(exc.value)
