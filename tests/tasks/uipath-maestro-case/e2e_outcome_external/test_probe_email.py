"""probe_email reads the sender's Sent Items: the connection's own mailbox is not the approver's."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "_setup"))

import outcome_probe  # noqa: E402

TOKEN = "OBT-745BDF77"
SENT = "2026-11-19T22:57:35Z"


def _message(**overrides):
    message = {
        "subject": f"Expense approval required — {TOKEN}",
        "sentDateTime": SENT,
        "isDraft": False,
        "toRecipients": [{"emailAddress": {"address": outcome_probe.APPROVER}}],
    }
    message.update(overrides)
    return message


def _probe(monkeypatch, messages):
    calls = []

    def fake(args):
        calls.append(args)
        return {"Result": "Success", "Data": messages}

    monkeypatch.setattr(outcome_probe, "_uip_json", fake)
    monkeypatch.setattr(outcome_probe, "debug_started_at", lambda: outcome_probe._to_epoch("2026-11-19T22:57:00Z"))
    return outcome_probe.probe_email(TOKEN), calls


def test_a_sent_message_to_the_approver_counts(monkeypatch):
    hits, calls = _probe(monkeypatch, [_message()])
    assert [h["subject"] for h in hits] == [f"Expense approval required — {TOKEN}"]
    assert "parentFolderId=SentItems&limit=100" in calls[0]


def test_drafts_other_recipients_and_other_tokens_do_not_count(monkeypatch):
    messages = [
        _message(isDraft=True),
        _message(toRecipients=[{"emailAddress": {"address": "someone@example.com"}}]),
        _message(subject="Expense approval required — OBT-00000000"),
    ]
    hits, _ = _probe(monkeypatch, messages)
    assert hits == []


def test_a_message_sent_before_the_harness_run_does_not_count(monkeypatch):
    hits, _ = _probe(monkeypatch, [_message(sentDateTime="2026-11-19T22:55:00Z")])
    assert hits == []
