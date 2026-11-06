"""Unit tests for check_generic_dynamic_node's node and output classification."""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_generic_dynamic_node as grader  # noqa: E402

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"
HTTP_BODY = {
    "authentication": "connector",
    "method": "GET",
    "targetConnector": grader.CONNECTOR_KEY,
    "path": "/table/acr_user",
    "url": "/table/acr_user",
}


def _process(activity_type: str, context: dict, body: dict | None = None) -> ET.Element:
    inputs = "".join(
        f'<uipath:input name="{k}" type="string" value="{v}" />' for k, v in context.items()
    )
    body_xml = (
        f'<uipath:input name="body" type="json" target="body"><![CDATA[{json.dumps(body)}]]></uipath:input>'
        if body is not None
        else ""
    )
    return ET.fromstring(
        f'<bpmn:definitions xmlns:bpmn="{BPMN_NS}" xmlns:uipath="{UIPATH_NS}">'
        f'<bpmn:process id="P"><bpmn:sendTask id="T"><bpmn:extensionElements>'
        f'<uipath:activity version="v1"><uipath:type value="{activity_type}" version="v1" />'
        f"<uipath:context>{inputs}</uipath:context>{body_xml}"
        f"</uipath:activity></bpmn:extensionElements></bpmn:sendTask></bpmn:process>"
        f"</bpmn:definitions>"
    )


def _http(**body) -> ET.Element:
    return _process(
        "Intsvc.UnifiedHttpRequest",
        {"connectorKey": "uipath-uipath-http", "objectName": "http-request", "method": "POST"},
        {**HTTP_BODY, **body},
    )


def test_generic_activity_still_passes() -> None:
    root = _process(
        grader.ACTIVITY_TYPE,
        {"connectorKey": grader.CONNECTOR_KEY, "objectName": "acr_user", "operation": "List"},
    )
    assert grader.find_generic_list_nodes(root)


def test_connector_mode_http_get_on_table_passes() -> None:
    assert grader.find_http_list_nodes(_http())
    assert grader.find_http_list_nodes(_http(url="/acr_user", path="/acr_user"))


def test_wrong_http_requests_fail() -> None:
    assert not grader.find_http_list_nodes(_http(method="POST"))
    assert not grader.find_http_list_nodes(_http(authentication="manual"))
    assert not grader.find_http_list_nodes(_http(targetConnector="uipath-uipath-http"))
    assert not grader.find_http_list_nodes(_http(url="/table/acr_user/{}", path="/table/acr_user/{}"))
    assert not grader.find_http_list_nodes(_http(url="/table/sys_user", path="/table/sys_user"))
    assert not grader.find_http_list_nodes(_http(url="/table/acr_user_x", path="/table/acr_user_x"))


def _variables(globals_: dict, outputs: dict | None = None) -> dict:
    return {
        "Variables": [
            {"Globals": globals_, "Elements": [{"ElementId": "T", "Outputs": outputs or {}}]}
        ]
    }


def test_response_body_result_array_counts_as_output() -> None:
    data = _variables({"OutputAcrUserRecords": {"Result": []}})
    assert grader.collect_array_candidates(data, [("OutputAcrUserRecords",)], (), ("T",))


def test_header_lists_do_not_count_as_output() -> None:
    headers = {"SetCookie": ["a=b"], "ContentType": "application/json"}
    data = _variables({"OutputAcrUserRecords": headers})
    assert not grader.collect_array_candidates(data, [("OutputAcrUserRecords",)], (), ("T",))
    data = _variables({"OutputAcrUserRecords": None}, {"Response": {"Headers": headers}})
    assert not grader.collect_array_candidates(data, [("OutputAcrUserRecords",)], (), ("T",))
    data = _variables({"OutputAcrUserRecords": None}, {"Response": {"Body": {"result": []}}})
    assert grader.collect_array_candidates(data, [("OutputAcrUserRecords",)], (), ("T",))


def test_plain_array_output_still_passes() -> None:
    data = _variables({"OutputAcrUserRecords": []})
    assert grader.collect_array_candidates(data, [("OutputAcrUserRecords",)], ("T",))
