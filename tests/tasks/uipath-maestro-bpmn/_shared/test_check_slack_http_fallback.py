"""Unit tests for check_slack_http_fallback's node classification."""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_slack_http_fallback as grader  # noqa: E402

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"
CONNECTOR_BODY = {
    "authentication": "connector",
    "targetConnector": grader.SLACK_KEY,
    "method": "GET",
    "url": "/emoji.list",
}


def _node(activity_type: str, connector_key: str, body: dict) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:sendTask xmlns:bpmn="{BPMN_NS}" xmlns:uipath="{UIPATH_NS}" id="T">'
        f'<bpmn:extensionElements><uipath:activity version="v1">'
        f'<uipath:type value="{activity_type}" version="v1" /><uipath:context>'
        f'<uipath:input name="connectorKey" type="string" value="{connector_key}" />'
        f"</uipath:context>"
        f'<uipath:input name="body" type="json" target="body"><![CDATA[{json.dumps(body)}]]></uipath:input>'
        f"</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
    )


def test_connector_mode_unified_http_passes() -> None:
    node = _node("Intsvc.UnifiedHttpRequest", grader.HTTP_CONNECTOR_KEY, CONNECTOR_BODY)
    assert grader.is_slack_connector_node(node)
    assert grader.references_emoji_endpoint(node)


def test_v1_slack_activity_fails() -> None:
    node = _node("Intsvc.ActivityExecution", grader.SLACK_KEY, {})
    assert not grader.is_slack_connector_node(node)


def test_manual_unified_http_fails() -> None:
    body = {**CONNECTOR_BODY, "authentication": "manual"}
    node = _node("Intsvc.UnifiedHttpRequest", grader.HTTP_CONNECTOR_KEY, body)
    assert not grader.is_slack_connector_node(node)
