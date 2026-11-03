"""Send identity in check_escalation_slack_alert's resolve_contract, V1 and V2 node shapes."""

from __future__ import annotations

import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_GRADER = Path(__file__).parent / "check_escalation_slack_alert.py"
V1_SEND_AS = '<uipath:input name="send_as" type="string" target="query" value="user"/>'
V2_SEND_AS = (
    '<uipath:input name="queryParameters" type="json" target="queryParameters">'
    '<![CDATA[{"send_as":"user"}]]></uipath:input>'
)


def _load():
    spec = importlib.util.spec_from_file_location("check_escalation_slack_alert", _GRADER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = _load()


def _bpmn(query_inputs: str) -> ET.Element:
    """Trimmed from the CI run 2026-10-21 EscalationSlackAlert artifact."""
    return ET.fromstring(
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn"><bpmn:process id="Process_1">'
        "<bpmn:extensionElements><uipath:variables>"
        '<uipath:output name="severity" id="Var_Severity" type="string"/>'
        '<uipath:output name="engineeringNeeded" id="Var_EngineeringNeeded" type="boolean"/>'
        '<uipath:output name="caseKey" id="Var_CaseKey" type="string"/>'
        '<uipath:output name="slackMessageId" id="Var_SlackMessageId" type="string"/>'
        "</uipath:variables></bpmn:extensionElements>"
        '<bpmn:scriptTask id="Task_Classify" scriptFormat="JavaScript"/>'
        '<bpmn:sendTask id="Task_PostSlackAlert"><bpmn:extensionElements>'
        '<uipath:activity version="v1"><uipath:type value="Intsvc.ActivityExecution" version="v1"/>'
        "<uipath:context>"
        '<uipath:input name="connectorKey" type="string" value="uipath-salesforce-slack"/>'
        '<uipath:input name="objectName" type="string" value="send_message_to_channel_v2"/>'
        '<uipath:input name="path" type="string" value="/send_message_to_channel_v2"/>'
        '<uipath:input name="activityConfigurationVersion" type="string" value="v2"/>'
        "</uipath:context>"
        '<uipath:input name="pathParameters" type="json" target="pathParameters"><![CDATA[{}]]></uipath:input>'
        f"{query_inputs}"
        "</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
        "</bpmn:process></bpmn:definitions>"
    )


@pytest.mark.parametrize("query_inputs", [V2_SEND_AS, V1_SEND_AS], ids=["v2", "v1"])
def test_user_identity_passes(query_inputs: str) -> None:
    assert checker.resolve_contract(_bpmn(query_inputs)).slack_send_ids == ("Task_PostSlackAlert",)


@pytest.mark.parametrize(
    "query_inputs",
    [
        V2_SEND_AS.replace('"user"', '"bot"'),
        V2_SEND_AS.replace('"user"', '"user "'),
        V1_SEND_AS.replace('"user"', '"user "'),
        V2_SEND_AS.replace('{"send_as":"user"}', "{}"),
        V2_SEND_AS.replace('{"send_as":"user"}', "not json"),
        V2_SEND_AS + V1_SEND_AS,
        "",
    ],
    ids=["v2-bot", "v2-trailing-space", "v1-trailing-space", "v2-missing", "v2-not-json", "both-shapes", "none"],
)
def test_other_identity_fails(query_inputs: str) -> None:
    with pytest.raises(checker.CheckFailure, match="send_as"):
        checker.resolve_contract(_bpmn(query_inputs))
