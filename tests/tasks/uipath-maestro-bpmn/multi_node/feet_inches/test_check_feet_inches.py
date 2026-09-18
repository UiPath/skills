"""The variable-passing check must see reads in the script body, where the Jint
contract puts them, not only in mapping inputs."""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_feet_inches import NS, _read_text  # noqa: E402


def _script_task(payload: str) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:scriptTask xmlns:bpmn="{NS["bpmn"]}" '
        f'xmlns:uipath="{NS["uipath"]}" id="Task_1">{payload}</bpmn:scriptTask>'
    )


def test_read_text_sees_a_read_in_the_script_body() -> None:
    task = _script_task(
        "<bpmn:extensionElements><uipath:mapping>"
        '<uipath:input name="args" type="json" target="bodyField">'
        '{"vars":"=vars","metadata":"=metadata"}</uipath:input>'
        "</uipath:mapping></bpmn:extensionElements>"
        "<bpmn:script>return vars.Var_Upstream * 12;</bpmn:script>"
    )
    assert "Var_Upstream" in _read_text(task)


def test_read_text_still_sees_a_read_in_a_mapping_input() -> None:
    task = _script_task(
        "<bpmn:extensionElements><uipath:mapping>"
        '<uipath:input name="value" type="double">=vars.Var_Upstream</uipath:input>'
        "</uipath:mapping></bpmn:extensionElements>"
    )
    assert "Var_Upstream" in _read_text(task)
