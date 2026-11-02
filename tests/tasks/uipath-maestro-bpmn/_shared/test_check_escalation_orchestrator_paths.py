"""Slack-miss failure detail and send identity in check_escalation_orchestrator_paths."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

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


V1_SEND_AS = '<uipath:input name="send_as" type="string" target="query" value="user"/>'
V2_SEND_AS = (
    '<uipath:input name="queryParameters" type="json" target="queryParameters">'
    '<![CDATA[{"send_as":"user"}]]></uipath:input>'
)


def _process(*query_inputs: str) -> ET.Element:
    """Slack sendTasks trimmed from the CI run 2026-10-21 CustomerEscalationOrchestrator artifact."""
    tasks = "".join(
        f'<bpmn:sendTask id="{slack_id}"><bpmn:extensionElements>'
        '<uipath:activity version="v1"><uipath:context>'
        '<uipath:input name="connectorKey" type="string" value="uipath-salesforce-slack"/>'
        '<uipath:input name="activityConfigurationVersion" type="string" value="v2"/>'
        f"</uipath:context>{inputs}</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
        for slack_id, inputs in zip(SLACK_IDS, query_inputs)
    )
    return ET.fromstring(
        '<bpmn:process xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        f'xmlns:uipath="http://uipath.org/schema/bpmn" id="Process_1">{tasks}</bpmn:process>'
    )


@pytest.mark.parametrize(
    "query_inputs",
    [(V2_SEND_AS, V2_SEND_AS), (V1_SEND_AS, V2_SEND_AS)],
    ids=["v2", "v1-and-v2-nodes"],
)
def test_user_identity_passes(query_inputs) -> None:
    checker.assert_send_identity(_process(*query_inputs), SLACK_IDS)


@pytest.mark.parametrize(
    "triage_inputs",
    [
        V2_SEND_AS.replace('"user"', '"bot"'),
        V2_SEND_AS.replace('"user"', '"user "'),
        V1_SEND_AS.replace('"user"', '"user "'),
        V2_SEND_AS.replace('{"send_as":"user"}', "{}"),
        V2_SEND_AS + V1_SEND_AS,
    ],
    ids=["v2-bot", "v2-trailing-space", "v1-trailing-space", "v2-missing", "both-shapes-on-one-node"],
)
def test_other_identity_fails(triage_inputs: str) -> None:
    with pytest.raises(checker.CheckFailure, match="SendTask_SlackTriage"):
        checker.assert_send_identity(_process(V2_SEND_AS, triage_inputs), SLACK_IDS)
