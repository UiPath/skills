"""Get-by-Id through a generic List in check_df_smoke_update, V1 and V2 node shapes."""

from __future__ import annotations

import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "_check_df_smoke_update", Path(__file__).parent / "check_df_smoke_update.py"
)
checker = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(checker)


def _list(inputs: str) -> ET.Element:
    return ET.fromstring(
        '<bpmn:sendTask xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn" id="Get_1"><bpmn:extensionElements>'
        '<uipath:activity version="v1"><uipath:context>'
        '<uipath:input name="objectName" type="string" value="FlowCodeEvalEntity" />'
        '<uipath:input name="operation" type="string" value="List" />'
        f"</uipath:context>{inputs}</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
    )


def _v2_query(payload: str) -> str:
    return (
        '<uipath:input name="queryParameters" type="json" target="queryParameters">'
        f"<![CDATA[{payload}]]></uipath:input>"
    )


@pytest.mark.parametrize(
    ("inputs", "counted"),
    [
        ('<uipath:input name="where" type="string" target="query" value="Id = 7" />', True),
        (_v2_query('{"where":"=js:\'Id = \' + vars.Create_response.Id"}'), True),
        (_v2_query('{"id":"=js:vars.Create_response.Id"}'), True),
        (_v2_query('{"where":"title = \'X\'"}'), False),
        (_v2_query('{"queryExpression":"Id = \'=js:vars.Create_response.Id\'"}'), True),
        (_v2_query('{"queryExpression":"title = \'X\'"}'), False),
        (_v2_query("{}"), False),
    ],
    ids=[
        "v1-where-id",
        "v2-where-id",
        "v2-id",
        "v2-where-other",
        "v2-query-expression-id",
        "v2-query-expression-other",
        "v2-no-filter",
    ],
)
def test_list_by_id_counts_as_a_get(inputs: str, counted: bool) -> None:
    assert checker.is_retrieval_node(_list(inputs), "FlowCodeEvalEntity") is counted
