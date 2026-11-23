"""Unit tests for check_managed_http_fallback's query_params evidence on the
generic HTTP connector, which stores the host and the path as separate inputs."""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_managed_http_fallback as grader  # noqa: E402

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"
QUERY = '<![CDATA[{"showHidden":true}]]>'


# Trimmed from skill-bpmn-query-params 2026-10-09.
def _node(query: str = QUERY) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:sendTask xmlns:bpmn="{BPMN_NS}" xmlns:uipath="{UIPATH_NS}" id="T">'
        f'<bpmn:extensionElements><uipath:activity version="v1">'
        f'<uipath:type value="{grader.ACTIVITY_TYPE}" version="v1" /><uipath:context>'
        f'<uipath:input name="connectorKey" type="string" value="{grader.GENERIC_HTTP_CONNECTOR_KEY}" />'
        f"</uipath:context>"
        f'<uipath:input name="method" type="string" target="body" value="GET" />'
        f'<uipath:input name="url" type="string" target="body" value="https://tasks.googleapis.com" />'
        f'<uipath:input name="path" type="string" target="body" value="/tasks/v1/lists/@default/tasks" />'
        f'<uipath:input name="query" type="object" target="body">{query}</uipath:input>'
        f"</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
    )


def _missing(node: ET.Element) -> list[str]:
    required = grader.FALLBACK_CHECKS["query_params"]["required"]
    return grader.require_all(grader.node_blob(node), required)


def test_split_url_and_path_passes() -> None:
    node = _node()
    assert grader.is_managed_http_node(node)
    assert _missing(node) == []


def test_missing_show_hidden_fails() -> None:
    assert _missing(_node(query="<![CDATA[{}]]>")) == ["showhidden", "true"]
