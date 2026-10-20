"""Slack-miss failure detail in check_escalation_orchestrator_paths."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

_GRADER = Path(__file__).parent / "check_escalation_orchestrator_paths.py"
SLACK_IDS = ("SendTask_SlackEscalation", "SendTask_SlackTriage")
EXECUTIONS = [
    {"ElementId": "Script_Classify", "Status": "Completed"},
    {"ElementId": "SendTask_SlackEscalation", "Status": "Terminated"},
]
INCIDENT = {"ElementId": "SendTask_SlackEscalation", "ErrorMessage": "channel_not_found"}


def _load():
    spec = importlib.util.spec_from_file_location("check_escalation_orchestrator_paths", _GRADER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = _load()


def _detail(monkeypatch, fetch) -> str:
    monkeypatch.setattr(checker, "fetch_incidents", fetch)
    return checker.slack_miss_detail(SLACK_IDS, EXECUTIONS, "instance-1")


def test_reports_slack_status_and_incidents(monkeypatch) -> None:
    detail = _detail(monkeypatch, lambda _id: ([INCIDENT], {"Items": [INCIDENT]}))
    assert "['SendTask_SlackEscalation=Terminated']" in detail
    assert "channel_not_found" in detail


def test_no_incidents_reports_status_only(monkeypatch) -> None:
    detail = _detail(monkeypatch, lambda _id: ([], {}))
    assert detail == "Slack sendTask states: ['SendTask_SlackEscalation=Terminated']"


def test_unknown_incidents_shape_shows_raw(monkeypatch) -> None:
    detail = _detail(monkeypatch, lambda _id: (None, {"Unexpected": [INCIDENT]}))
    assert "incidents response has an unknown shape" in detail
    assert '"Unexpected"' in detail


def test_incidents_timeout_keeps_status(monkeypatch) -> None:
    def timeout(_id):
        raise subprocess.TimeoutExpired("uip", 120)

    detail = _detail(monkeypatch, timeout)
    assert "SendTask_SlackEscalation=Terminated" in detail
    assert "incidents unavailable" in detail


def test_unreached_slack_task(monkeypatch) -> None:
    monkeypatch.setattr(checker, "fetch_incidents", lambda _id: ([], {}))
    assert checker.slack_miss_detail(SLACK_IDS, EXECUTIONS[:1], "instance-1") == "no Slack sendTask reached"
