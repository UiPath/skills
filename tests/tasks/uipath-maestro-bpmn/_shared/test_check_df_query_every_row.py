"""check_df_query_every_row: a paged whole-entity read passes, one capped query does not."""

from __future__ import annotations

import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "_check_df_query_every_row", Path(__file__).parent / "check_df_query_every_row.py"
)
checker = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(checker)

PAGED_QUERY = '{"start":"=js:vars.pageStart","limit":1000,"isAscending":true}'
LOOP = [("start", "nextPage"), ("nextPage", "page"), ("page", "collect"), ("collect", "more"), ("more", "nextPage"), ("more", "done")]
STRAIGHT = [("start", "page"), ("page", "done")]


def _process(query: str, flows: list[tuple[str, str]], body: str = '{"_sortFieldName":"Id"}') -> ET.Element:
    flow_xml = "".join(
        f'<bpmn:sequenceFlow id="Flow_{source}_{target}" sourceRef="{source}" targetRef="{target}" />'
        for source, target in flows
    )
    return ET.fromstring(
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn"><bpmn:process id="P">'
        '<bpmn:sendTask id="page"><bpmn:extensionElements><uipath:activity version="v1"><uipath:context>'
        '<uipath:input name="connectorKey" type="string" value="uipath-uipath-dataservice" />'
        '<uipath:input name="objectName" type="string" value="QueryEntityRecordsCurated" />'
        '</uipath:context>'
        '<uipath:input name="pathParameters" type="json" target="pathParameters"><![CDATA[{"entityName":"FlowCodeEvalEntity"}]]></uipath:input>'
        f'<uipath:input name="queryParameters" type="json" target="queryParameters"><![CDATA[{query}]]></uipath:input>'
        f'<uipath:input name="body" type="json" target="body"><![CDATA[{body}]]></uipath:input>'
        f"</uipath:activity></bpmn:extensionElements></bpmn:sendTask>{flow_xml}</bpmn:process></bpmn:definitions>"
    )


@pytest.mark.parametrize(
    ("query", "flows", "paged"),
    [
        (PAGED_QUERY, LOOP, True),
        ('{"start":"=js:vars.pageStart","limit":"=js:vars.pageSize"}', LOOP, True),
        ('{"start":0,"limit":1000}', STRAIGHT, False),
        (PAGED_QUERY, STRAIGHT, False),
        ('{"start":0,"limit":1000}', LOOP, False),
        ('{"start":"=js:vars.pageStart","limit":5000}', LOOP, False),
    ],
    ids=["paged", "expression-limit", "one-query", "no-loop", "fixed-start", "over-cap"],
)
def test_paged(query: str, flows: list[tuple[str, str]], paged: bool) -> None:
    root = _process(query, flows)
    task = checker.query_nodes(root)[0]
    assert (checker.page_problem(root, task) is None) is paged


@pytest.mark.parametrize(
    ("body", "query", "sorted_"),
    [
        ('{"_sortFieldName":"Id"}', PAGED_QUERY, True),
        ("{}", '{"start":"=js:vars.pageStart","limit":1000,"sortBy":"Id"}', True),
        ("{}", PAGED_QUERY, False),
    ],
    ids=["body-sort", "query-sort", "unsorted"],
)
def test_sorted(body: str, query: str, sorted_: bool) -> None:
    task = checker.query_nodes(_process(query, LOOP, body))[0]
    assert checker.is_sorted(task) is sorted_
