#!/usr/bin/env python3
"""Unit tests for the two diagram-preservation checks.

The skill ships `scripts/check-diagram-preserved.py` to agents and the evals use
`edit_check.assert_diagram_preserved`. Each case runs both, so they cannot drift.
"""

from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared.edit_check import assert_diagram_preserved  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
SCRIPT = REPO / "classic" / "skills" / "uipath-maestro-bpmn" / "scripts" / "check-diagram-preserved.py"

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


def run_script(tmp_path: Path, after: str, removed: str | None = None) -> tuple[int, list[str]]:
    before_path, after_path = tmp_path / "before.bpmn", tmp_path / "after.bpmn"
    before_path.write_text(BEFORE)
    after_path.write_text(after)
    args = [sys.executable, str(SCRIPT), str(before_path), str(after_path)]
    if removed:
        args += ["--removed", removed]
    proc = subprocess.run(args, capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout).get("Losses", [])


def run_helper(after: str, removed: frozenset[str] = frozenset()) -> str | None:
    try:
        assert_diagram_preserved(ET.fromstring(BEFORE), ET.fromstring(after), removed)
    except SystemExit as exc:
        return str(exc)
    return None


def test_unchanged_passes(tmp_path: Path) -> None:
    assert run_script(tmp_path, BEFORE) == (0, [])
    assert run_helper(BEFORE) is None


def test_expanded_subprocess_may_widen(tmp_path: Path) -> None:
    after = BEFORE.replace('x="300" y="60" width="300"', 'x="300" y="60" width="460"')
    assert run_script(tmp_path, after) == (0, [])
    assert run_helper(after) is None


def test_task_resize_fails(tmp_path: Path) -> None:
    after = BEFORE.replace('x="100" y="100" width="100"', 'x="100" y="100" width="140"')
    code, losses = run_script(tmp_path, after)
    assert code == 1 and any("resized" in loss for loss in losses)
    assert "resized" in run_helper(after)


@pytest.mark.parametrize(
    ("after", "expected"),
    [
        (BEFORE.replace('<bpmndi:BPMNEdge id="F_di"', '<bpmndi:BPMNEdge id="F_di_gone"').replace('bpmnElement="F"', 'bpmnElement="Other"'), "lost its diagram edge"),
        (BEFORE.replace(' bioc:stroke="#2B5D8C"', ""), "edge colors"),
    ],
)
def test_edge_loss_fails(tmp_path: Path, after: str, expected: str) -> None:
    code, losses = run_script(tmp_path, after)
    assert code == 1 and any(expected in loss for loss in losses)
    assert expected in run_helper(after)


def test_shape_without_bounds_reports_a_loss_not_a_traceback(tmp_path: Path) -> None:
    after = BEFORE.replace('<dc:Bounds x="100" y="100" width="100" height="80" />', "")
    code, losses = run_script(tmp_path, after)
    assert code == 1 and any("lost its bounds" in loss for loss in losses)
    assert "lost its bounds" in run_helper(after)


def test_removed_id_still_in_model_is_reported(tmp_path: Path) -> None:
    after = BEFORE.replace(' bioc:fill="#E8F1FB"', "")
    code, losses = run_script(tmp_path, after, removed="A")
    assert code == 1
    assert any("named in --removed but is still in the model" in loss for loss in losses)
    assert any("colors" in loss for loss in losses)
