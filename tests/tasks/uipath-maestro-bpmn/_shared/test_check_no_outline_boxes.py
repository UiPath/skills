"""check_no_outline_boxes.py: a built step passes, a skeleton box fails.

The skeleton and merged shapes are cut from run 2026-11-16 artifacts: Studio Web's
`refresh` gives a bare box a `BPMN.Variables` mapping, and `merge` kept the
skeleton's `bpmn:task` tag on a box the edited file made a `bpmn:scriptTask`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from _shared.check_no_outline_boxes import is_outline_box

_HEAD = '<root xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:uipath="http://uipath.org/schema/bpmn">'
_VARS = '<uipath:mapping version="v1"><uipath:type value="BPMN.Variables" version="v1" /></uipath:mapping>'


def _task(inner: str, tag: str = "task") -> ET.Element:
    return ET.fromstring(f'{_HEAD}<bpmn:{tag} id="t"><bpmn:extensionElements>{inner}</bpmn:extensionElements></bpmn:{tag}></root>')[0]


def test_skeleton_box_with_variable_plumbing_is_an_outline_box() -> None:
    assert is_outline_box(_task(_VARS))
    assert is_outline_box(ET.fromstring(f'{_HEAD}<bpmn:task id="t" /></root>')[0])


def test_merged_script_left_on_a_bare_task_still_counts_as_outline() -> None:
    box = _task(_VARS + '<uipath:scriptVersion value="v3" />')
    assert is_outline_box(box)


def test_a_task_with_an_activity_or_service_type_is_built() -> None:
    assert not is_outline_box(_task('<uipath:activity version="v1"><uipath:type value="Intsvc.SendTask" /></uipath:activity>'))
    assert not is_outline_box(_task('<uipath:mapping version="v1"><uipath:type value="Intsvc.ActivityExecution" version="v1" /></uipath:mapping>'))
