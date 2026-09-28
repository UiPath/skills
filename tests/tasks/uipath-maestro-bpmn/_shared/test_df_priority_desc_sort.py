"""Priority-DESC sort detection in check_df_e2e_contract_intake_pipeline."""

from __future__ import annotations

import importlib.util
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_SHARED = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(_SHARED.parent))
sys.path.insert(0, str(_SHARED))

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"

IS_ASCENDING_FALSE = '<uipath:input name="isAscending" type="boolean" target="query" value="false" />'
IS_ASCENDING_TRUE = '<uipath:input name="isAscending" type="boolean" target="query" value="true" />'
SORT_FIELD_BODY = '<uipath:input name="body" type="json" target="body"><![CDATA[{"_sortFieldName": "priority"}]]></uipath:input>'
SORT_FIELD_QUERY = '<uipath:input name="_sortFieldName" type="string" target="query" value="priority" />'
DOCUMENTED_QUERY = (
    '<uipath:input name="queryExpression" type="string" target="query" value="contractTitle = &apos;Q&apos;" />'
    + IS_ASCENDING_FALSE
    + SORT_FIELD_BODY
)
FILTER_TREE_WITH_SORT = (
    '<uipath:input name="queryExpression" type="json" target="query"><![CDATA['
    '{"groupOperator": 0, "index": 0, "filters": [], "groups": [], '
    '"sortOptions": [{"fieldName": "priority", "isDescending": true}]}]]></uipath:input>'
)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _SHARED / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load("check_df_e2e_contract_intake_pipeline")


def _query(inputs: str) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:sendTask xmlns:bpmn="{BPMN_NS}" xmlns:uipath="{UIPATH_NS}" id="Task_QueryRecords">'
        '<bpmn:extensionElements><uipath:activity version="v1">'
        '<uipath:type value="Intsvc.ActivityExecution" version="v1" />'
        "<uipath:context>"
        '<uipath:input name="objectName" type="string" value="QueryEntityRecordsCurated" />'
        "</uipath:context>"
        '<uipath:input name="entityName" type="string" target="path" value="ContractRegistry" />'
        f"{inputs}"
        "</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
    )


def _sort_body(sort_options: str) -> str:
    return (
        '<uipath:input name="body" type="json" target="body">'
        f'<![CDATA[{{"sortOptions": {sort_options}}}]]></uipath:input>'
    )


@pytest.mark.parametrize(
    "inputs",
    [
        IS_ASCENDING_FALSE + _sort_body('[{"fieldName": "priority", "isDescending": true}]'),
        _sort_body('[{"fieldName": "Priority", "isDescending": "true"}]'),
        _sort_body('[{"fieldName": "status", "isDescending": false}, {"fieldName": "priority", "isDescending": true}]'),
        '<uipath:input name="sortFieldName" type="string" target="query" value="priority" />' + IS_ASCENDING_FALSE,
        IS_ASCENDING_FALSE + SORT_FIELD_BODY,
        IS_ASCENDING_FALSE + '<uipath:input name="body" type="json" target="body"><![CDATA[{"_sortFieldName": "Priority"}]]></uipath:input>',
        DOCUMENTED_QUERY,
    ],
    ids=["eval-node", "string-true", "second-entry", "sortfieldname", "body-sortfieldname", "body-capitalized", "documented"],
)
def test_priority_desc_sort_accepted(inputs: str) -> None:
    assert checker.has_priority_desc_sort(_query(inputs))


@pytest.mark.parametrize(
    "inputs",
    [
        IS_ASCENDING_FALSE + _sort_body('[{"fieldName": "priority", "isDescending": false}]'),
        _sort_body('[{"fieldName": "priority"}]'),
        IS_ASCENDING_FALSE + _sort_body('[{"fieldName": "status", "isDescending": true}]'),
        _sort_body('[{"fieldName": "status", "isDescending": true}, {"fieldName": "priority", "isDescending": false}]'),
        IS_ASCENDING_FALSE,
        '<uipath:input name="body" type="json" target="body" value="=vars.sortBody" />',
        '<uipath:input name="body" type="json" target="body"><![CDATA[[{"fieldName": "priority"}]]]></uipath:input>',
        SORT_FIELD_BODY,
        IS_ASCENDING_TRUE + SORT_FIELD_BODY,
        IS_ASCENDING_FALSE + SORT_FIELD_QUERY,
        IS_ASCENDING_FALSE + SORT_FIELD_BODY + '<uipath:input name="body" type="json" target="body"><![CDATA[{}]]></uipath:input>',
        IS_ASCENDING_FALSE + '<uipath:input name="body" type="json" target="body"><![CDATA[{"_sortFieldName": "priorityLabel"}]]></uipath:input>',
        IS_ASCENDING_FALSE + FILTER_TREE_WITH_SORT,
    ],
    ids=[
        "descending-false",
        "no-direction",
        "other-field",
        "split-entries",
        "isascending-only",
        "expression-body",
        "array-body",
        "body-sortfieldname-no-direction",
        "body-sortfieldname-ascending",
        "query-sortfieldname",
        "overridden-body",
        "body-sortfieldname-other-field",
        "sort-in-filter-tree",
    ],
)
def test_priority_desc_sort_rejected(inputs: str) -> None:
    assert not checker.has_priority_desc_sort(_query(inputs))
