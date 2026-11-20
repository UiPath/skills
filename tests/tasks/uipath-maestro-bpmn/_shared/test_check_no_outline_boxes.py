"""check_no_outline_boxes.py: a built step passes, a skeleton box and a lost tag fail.

Shapes cut from real files: a Studio Web skeleton box (refresh gives it a
`BPMN.Variables` mapping), the step `merge` left as `bpmn:task` (branch CI run
43940797824), and the same step after a Task was changed to Script task on the
Studio Web canvas (alpha popoc/DefaultTenant, Solution 26).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from _shared.check_no_outline_boxes import findings, is_outline_box, lost_script_type

_HEAD = '<root xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:uipath="http://uipath.org/schema/bpmn">'
_TYPE = '<uipath:type value="BPMN.Variables" version="v1" />'
_SCRIPT_MAPPING = (
    f'<uipath:mapping version="v1">{_TYPE}'
    '<uipath:input name="args" type="json" target="bodyField">{}</uipath:input>'
    '<uipath:output name="basePrice" type="json" source="=result.response" var="basePrice" />'
    "</uipath:mapping>"
)


def _el(tag: str, inner: str, attrs: str = "", body: str = "") -> ET.Element:
    return ET.fromstring(
        f'{_HEAD}<bpmn:{tag} id="t"{attrs}><bpmn:extensionElements>{inner}</bpmn:extensionElements>{body}</bpmn:{tag}></root>'
    )[0]


def test_skeleton_box_is_an_outline_box() -> None:
    assert is_outline_box(_el("task", f'<uipath:mapping version="v1">{_TYPE}</uipath:mapping>'))
    assert is_outline_box(ET.fromstring(f'{_HEAD}<bpmn:task id="t" /></root>')[0])
    assert is_outline_box(_el("task", '<uipath:loopCharacteristics collection="=vars.items" />'))


def test_a_set_step_or_service_type_is_built() -> None:
    set_step = f'<uipath:mapping version="v1">{_TYPE}<uipath:output name="q" type="number" source="=1" var="q" /></uipath:mapping>'
    assert not is_outline_box(_el("task", set_step))
    assert not is_outline_box(_el("task", '<uipath:activity version="v1"><uipath:type value="Intsvc.SendTask" /></uipath:activity>'))


def test_merge_left_a_script_step_as_bpmn_task() -> None:
    merged = _el("task", _SCRIPT_MAPPING + '<uipath:scriptVersion value="v3" />', ' scriptFormat="JavaScript"', "<bpmn:script>return 1;</bpmn:script>")
    assert lost_script_type(merged)
    assert not is_outline_box(merged)


def test_the_canvas_script_task_passes_and_the_merged_one_fails() -> None:
    body = f'<bpmn:extensionElements>{_SCRIPT_MAPPING}</bpmn:extensionElements><bpmn:script>return 1;</bpmn:script>'
    canvas = ET.fromstring(f'{_HEAD}<bpmn:scriptTask id="t" scriptFormat="JavaScript">{body}</bpmn:scriptTask></root>')
    merged = ET.fromstring(f'{_HEAD}<bpmn:task id="t" scriptFormat="JavaScript">{body}</bpmn:task></root>')
    assert findings(canvas) == ([], [])
    assert findings(merged) == (["t"], [])
