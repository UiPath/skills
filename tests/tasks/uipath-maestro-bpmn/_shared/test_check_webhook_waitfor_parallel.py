"""Unit tests for check_webhook_waitfor_parallel's manual GET read, V1 and V2."""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_webhook_waitfor_parallel as grader  # noqa: E402

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"
WEBHOOK_URL = "https://alpha.uipath.com/org/tenant/elements_/v1/webhooks/events/abc123"
BASE_URL = "http://gallupx-webhook-server.cloudelements.svc.cluster.local"
V2_BODY = {"authentication": "manual", "method": "GET", "url": WEBHOOK_URL}


def _root(activity: str) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:definitions xmlns:bpmn="{BPMN_NS}" xmlns:uipath="{UIPATH_NS}">'
        f'<bpmn:process id="P"><bpmn:sendTask id="T"><bpmn:extensionElements>'
        f'<uipath:activity version="v1">{activity}</uipath:activity>'
        f"</bpmn:extensionElements></bpmn:sendTask></bpmn:process></bpmn:definitions>"
    )


# Trimmed from skill-bpmn-webhook-waitfor-parallel 2026-10-22.
def _v2(body: dict, query: str = "{}") -> ET.Element:
    return _root(
        f'<uipath:type value="{grader.UNIFIED_HTTP_REQUEST}" version="v1" /><uipath:context>'
        f'<uipath:input name="connectorKey" type="string" value="uipath-uipath-http" />'
        f'<uipath:input name="method" type="string" value="POST" />'
        f'<uipath:input name="path" type="string" value="/http-request" />'
        f"</uipath:context>"
        f'<uipath:input name="queryParameters" type="json" target="queryParameters"><![CDATA[{query}]]></uipath:input>'
        f'<uipath:input name="body" type="json" target="body"><![CDATA[{json.dumps(body)}]]></uipath:input>'
    )


def _v1(url: str = WEBHOOK_URL, headers: str = "", activity_type: str = grader.HTTP_TYPE) -> ET.Element:
    return _root(
        f'<uipath:type value="{activity_type}" version="v1" /><uipath:context>'
        f'<uipath:input name="mode" type="string" value="manual" />'
        f'<uipath:input name="method" type="string" value="GET" />'
        f'<uipath:input name="url" type="string" value="{url}" />'
        f'<uipath:input name="headers" type="json" value=\'{headers}\' />'
        f"</uipath:context>"
    )


def _fails(root: ET.Element) -> str:
    with pytest.raises(SystemExit) as excinfo:
        grader.http_get_nodes(root)
    return str(excinfo.value)


def test_v2_manual_get_to_webhook_url_passes() -> None:
    assert len(grader.http_get_nodes(_v2(V2_BODY))) == 1


def test_v1_manual_get_to_webhook_url_passes() -> None:
    assert len(grader.http_get_nodes(_v1())) == 1


# builder-sdk manual `.http()`: UnifiedHttpRequest in the V1 context layout.
def test_unified_http_v1_layout_passes() -> None:
    assert len(grader.http_get_nodes(_v1(activity_type=grader.UNIFIED_HTTP_REQUEST))) == 1


def test_unified_http_v1_layout_base_url_fails() -> None:
    node = _v1(url=BASE_URL, activity_type=grader.UNIFIED_HTTP_REQUEST)
    assert "webhooks config" in _fails(node)


def test_v2_base_url_fails() -> None:
    assert "webhooks config" in _fails(_v2({**V2_BODY, "url": BASE_URL}))


def test_v1_base_url_fails() -> None:
    assert "webhooks config" in _fails(_v1(url=BASE_URL))


def test_scale_unit_webhook_url_passes() -> None:
    url = "https://cloud.uipath.com/elements_/scaleunit_/su1/v1/webhooks/connectors/k/events/abc123"
    assert len(grader.http_get_nodes(_v2({**V2_BODY, "url": url}))) == 1


def test_webhook_config_endpoint_is_skipped() -> None:
    url = "https://alpha.uipath.com/org/tenant/elements_/v1/webhooks/subscribers/c/webhook/config"
    assert grader.http_get_nodes(_v2({**V2_BODY, "url": url})) == []


def test_other_url_is_skipped() -> None:
    body = {**V2_BODY, "url": "https://example.com/webhook"}
    assert grader.http_get_nodes(_v2(body)) == []


def test_v2_connector_mode_is_skipped() -> None:
    body = {**V2_BODY, "authentication": "connector"}
    assert grader.http_get_nodes(_v2(body)) == []


def test_v2_post_is_skipped() -> None:
    assert grader.http_get_nodes(_v2({**V2_BODY, "method": "POST"})) == []


@pytest.mark.parametrize(
    ("body", "query", "field"),
    [
        ({**V2_BODY, "headers": {"X-Test": "1"}}, "{}", "headers"),
        ({**V2_BODY, "query": {"a": "1"}}, "{}", "query parameters"),
        (V2_BODY, '{"a":"1"}', "queryParameters"),
    ],
)
def test_v2_headers_or_query_fail(body: dict, query: str, field: str) -> None:
    assert f"must not set {field}" in _fails(_v2(body, query))


def test_v2_empty_headers_and_query_pass() -> None:
    body = {**V2_BODY, "headers": {}, "query": ""}
    assert len(grader.http_get_nodes(_v2(body))) == 1


def test_v1_headers_fail() -> None:
    assert "must not set headers" in _fails(_v1(headers='{"X-Test":"1"}'))
