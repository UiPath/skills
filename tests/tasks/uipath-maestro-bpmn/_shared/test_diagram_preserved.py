#!/usr/bin/env python3
"""Unit tests for `edit_check.assert_diagram_preserved`, the evals' diagram-preservation grader."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared.edit_check import assert_diagram_preserved  # noqa: E402


BEFORE = """<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
    xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
    xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
    xmlns:bioc="http://bpmn.io/schema/bpmn/biocolor/1.0">
  <bpmn:collaboration id="Collab"><bpmn:participant id="Pool" processRef="P" /></bpmn:collaboration>
  <bpmn:process id="P">
    <bpmn:laneSet id="LS"><bpmn:lane id="Lane"><bpmn:flowNodeRef>A</bpmn:flowNodeRef><bpmn:flowNodeRef>Sub</bpmn:flowNodeRef></bpmn:lane></bpmn:laneSet>
    <bpmn:task id="A" />
    <bpmn:subProcess id="Sub"><bpmn:task id="C" /></bpmn:subProcess>
    <bpmn:sequenceFlow id="F" sourceRef="A" targetRef="Sub" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="D">
    <bpmndi:BPMNPlane id="Plane" bpmnElement="Collab">
      <bpmndi:BPMNShape id="Pool_di" bpmnElement="Pool"><dc:Bounds x="0" y="0" width="800" height="300" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Lane_di" bpmnElement="Lane"><dc:Bounds x="30" y="0" width="770" height="300" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="A_di" bpmnElement="A" bioc:fill="#E8F1FB"><dc:Bounds x="100" y="100" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Sub_di" bpmnElement="Sub" isExpanded="true"><dc:Bounds x="300" y="60" width="300" height="160" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="C_di" bpmnElement="C"><dc:Bounds x="340" y="100" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="F_di" bpmnElement="F" bioc:stroke="#2B5D8C"><di:waypoint x="200" y="140" /><di:waypoint x="300" y="140" /></bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
"""


def run_helper(after: str, removed: frozenset[str] = frozenset()) -> str | None:
    try:
        assert_diagram_preserved(ET.fromstring(BEFORE), ET.fromstring(after), removed)
    except SystemExit as exc:
        return str(exc)
    return None


def test_unchanged_passes() -> None:
    assert run_helper(BEFORE) is None


def test_expanded_subprocess_may_widen() -> None:
    after = BEFORE.replace('x="300" y="60" width="300"', 'x="300" y="60" width="460"')
    assert run_helper(after) is None


def test_task_resize_fails() -> None:
    after = BEFORE.replace('x="100" y="100" width="100"', 'x="100" y="100" width="140"')
    assert "resized" in run_helper(after)


@pytest.mark.parametrize(
    ("after", "expected"),
    [
        (BEFORE.replace('<bpmndi:BPMNEdge id="F_di"', '<bpmndi:BPMNEdge id="F_di_gone"').replace('bpmnElement="F"', 'bpmnElement="Other"'), "lost its diagram edge"),
        (BEFORE.replace(' bioc:stroke="#2B5D8C"', ""), "edge colors"),
    ],
)
def test_edge_loss_fails(after: str, expected: str) -> None:
    assert expected in run_helper(after)


def test_shape_without_bounds_reports_a_loss_not_a_traceback() -> None:
    after = BEFORE.replace('<dc:Bounds x="100" y="100" width="100" height="80" />', "")
    assert "lost its bounds" in run_helper(after)
