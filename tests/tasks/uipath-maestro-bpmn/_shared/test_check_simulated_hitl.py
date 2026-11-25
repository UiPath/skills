import os
import sys
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bpmn_check import NS  # noqa: E402
from check_simulated_hitl import check_schema  # noqa: E402


def _hitl(output_attrs: str) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:definitions xmlns:bpmn="{NS["bpmn"]}" '
        f'xmlns:uipath="{NS["uipath"]}"><bpmn:process>'
        '<bpmn:userTask id="Task_1"><bpmn:extensionElements>'
        '<uipath:activity version="v1">'
        '<uipath:type value="Actions.HITL" version="v2" />'
        '<uipath:context><uipath:input name="taskTitle" type="string" value="Approve or reject" /></uipath:context>'
        f'<uipath:output name="Process response" type="Actions.HITL" {output_attrs} />'
        "</uipath:activity></bpmn:extensionElements></bpmn:userTask>"
        "</bpmn:process></bpmn:definitions>"
    )


def test_schema_accepts_response_output_with_source() -> None:
    check_schema(_hitl('source="=result" var="resp"'))


def test_schema_rejects_response_output_without_source() -> None:
    with pytest.raises(SystemExit, match="source="):
        check_schema(_hitl('var="resp"'))
