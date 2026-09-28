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
        '<uipath:input name="_sortFieldName" type="string" target="query" value="priority" />' + IS_ASCENDING_FALSE,
    ],
    ids=["eval-node", "string-true", "second-entry", "sortfieldname"],
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
    ],
    ids=[
        "descending-false",
        "no-direction",
        "other-field",
        "split-entries",
        "isascending-only",
        "expression-body",
        "array-body",
    ],
)
def test_priority_desc_sort_rejected(inputs: str) -> None:
    assert not checker.has_priority_desc_sort(_query(inputs))
