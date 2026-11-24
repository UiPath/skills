"""check_error_boundary_handler.py: an omitted cancelActivity is interrupting (BPMN default true).

The builder SDK omits the default, so the compiled boundary carries no attribute
(Studio Web run 45307831896); only an explicit cancelActivity="false" is
non-interrupting, which is how the canvas reads it too.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CHECK = Path(__file__).resolve().parent.parent / "structural" / "error_boundary_handler" / "check_error_boundary_handler.py"

BPMN = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="D">
  <bpmn:error id="Err" name="Fail" errorCode="500" />
  <bpmn:process id="P" isExecutable="true">
    <bpmn:startEvent id="S"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sendTask id="T"><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:sendTask>
    <bpmn:boundaryEvent id="B" attachedToRef="T"{attrs}><bpmn:outgoing>F3</bpmn:outgoing><bpmn:errorEventDefinition errorRef="Err" /></bpmn:boundaryEvent>
    <bpmn:task id="R"><bpmn:incoming>F3</bpmn:incoming><bpmn:outgoing>F4</bpmn:outgoing></bpmn:task>
    <bpmn:endEvent id="E1"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent>
    <bpmn:endEvent id="E2"><bpmn:incoming>F4</bpmn:incoming></bpmn:endEvent>
    <bpmn:sequenceFlow id="F1" sourceRef="S" targetRef="T" />
    <bpmn:sequenceFlow id="F2" sourceRef="T" targetRef="E1" />
    <bpmn:sequenceFlow id="F3" sourceRef="B" targetRef="R" />
    <bpmn:sequenceFlow id="F4" sourceRef="R" targetRef="E2" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="Dg"><bpmndi:BPMNPlane id="Pl" bpmnElement="P">
    <bpmndi:BPMNShape id="sS" bpmnElement="S"><dc:Bounds x="0" y="0" width="36" height="36" /></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="sT" bpmnElement="T"><dc:Bounds x="80" y="0" width="100" height="80" /></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="sB" bpmnElement="B"><dc:Bounds x="110" y="62" width="36" height="36" /></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="sR" bpmnElement="R"><dc:Bounds x="200" y="100" width="100" height="80" /></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="sE1" bpmnElement="E1"><dc:Bounds x="300" y="0" width="36" height="36" /></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="sE2" bpmnElement="E2"><dc:Bounds x="350" y="120" width="36" height="36" /></bpmndi:BPMNShape>
    <bpmndi:BPMNEdge id="eF1" bpmnElement="F1"><di:waypoint x="36" y="18" /><di:waypoint x="80" y="18" /></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="eF2" bpmnElement="F2"><di:waypoint x="180" y="18" /><di:waypoint x="300" y="18" /></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="eF3" bpmnElement="F3"><di:waypoint x="128" y="98" /><di:waypoint x="200" y="140" /></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="eF4" bpmnElement="F4"><di:waypoint x="300" y="140" /><di:waypoint x="350" y="138" /></bpmndi:BPMNEdge>
  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>
</bpmn:definitions>
"""


def _run(tmp_path: Path, attrs: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / "InvoiceServiceRecovery.bpmn").write_text(BPMN.replace("{attrs}", attrs), encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECK)], cwd=tmp_path, capture_output=True, text=True, check=False)


def test_omitted_cancel_activity_is_interrupting(tmp_path: Path) -> None:
    result = _run(tmp_path, "")
    assert result.returncode == 0, result.stderr


def test_explicit_true_is_interrupting(tmp_path: Path) -> None:
    result = _run(tmp_path, ' cancelActivity="true"')
    assert result.returncode == 0, result.stderr


def test_explicit_false_is_not_interrupting(tmp_path: Path) -> None:
    result = _run(tmp_path, ' cancelActivity="false"')
    assert result.returncode == 1
    assert "no interrupting" in result.stderr
