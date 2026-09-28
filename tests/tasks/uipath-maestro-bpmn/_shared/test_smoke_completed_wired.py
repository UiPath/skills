"""HITL completion wiring in check_smoke_completed_wired."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SHARED = Path(__file__).resolve().parent
sys.path.insert(0, str(_SHARED.parent))

HITL = (
    '<bpmn:userTask id="Hitl"><bpmn:extensionElements><uipath:activity version="v1">'
    '<uipath:type value="Actions.HITL" version="v1" /></uipath:activity>'
    "</bpmn:extensionElements></bpmn:userTask>"
)
RECORD = '<bpmn:scriptTask id="Record" />'
END = '<bpmn:endEvent id="End" />'
START = '<bpmn:startEvent id="Start" />'
OUTCOME_SPLIT = (
    '<bpmn:exclusiveGateway id="Split" default="ToReject" />'
    '<bpmn:task id="Approve" /><bpmn:task id="Reject" />'
    '<bpmn:exclusiveGateway id="Merge" />'
)


def _load():
    spec = importlib.util.spec_from_file_location("check_smoke_completed_wired", _SHARED / "check_smoke_completed_wired.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load()


def _write(tmp_path: Path, nodes: str, flows: list[tuple[str, str]]) -> None:
    ids = [part.split('id="', 1)[1].split('"', 1)[0] for part in nodes.split("<bpmn:")[1:] if 'id="' in part]
    flow_xml = "".join(
        f'<bpmn:sequenceFlow id="F{i}" sourceRef="{s}" targetRef="{t}" />' for i, (s, t) in enumerate(flows)
    )
    shapes = "".join(f'<bpmndi:BPMNShape id="S_{i}" bpmnElement="{i}" />' for i in ids)
    edges = "".join(f'<bpmndi:BPMNEdge id="E_F{i}" bpmnElement="F{i}" />' for i in range(len(flows)))
    (tmp_path / "PurchaseApprovalBpmn.bpmn").write_text(
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
        'xmlns:uipath="http://uipath.org/schema/bpmn">'
        f'<bpmn:process id="P">{nodes}{flow_xml}</bpmn:process>'
        f'<bpmndi:BPMNDiagram id="D"><bpmndi:BPMNPlane id="Pl" bpmnElement="P">{shapes}{edges}'
        "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "nodes,flows",
    [
        (START + HITL + RECORD + END, [("Start", "Hitl"), ("Hitl", "Record"), ("Record", "End")]),
        (
            START + HITL + OUTCOME_SPLIT + RECORD + END,
            [
                ("Start", "Hitl"),
                ("Hitl", "Split"),
                ("Split", "Approve"),
                ("Split", "Reject"),
                ("Approve", "Merge"),
                ("Reject", "Merge"),
                ("Merge", "Record"),
                ("Record", "End"),
            ],
        ),
    ],
    ids=["direct-step", "outcome-gateway"],
)
def test_wired_accepted(tmp_path, monkeypatch, nodes, flows) -> None:
    _write(tmp_path, nodes, flows)
    monkeypatch.chdir(tmp_path)
    checker.main()


@pytest.mark.parametrize(
    "nodes,flows",
    [
        (START + HITL + END, [("Start", "Hitl"), ("Hitl", "End")]),
        (
            START + HITL + '<bpmn:exclusiveGateway id="Split" />' + END,
            [("Start", "Hitl"), ("Hitl", "Split"), ("Split", "End")],
        ),
        (START + HITL + END, [("Start", "Hitl")]),
    ],
    ids=["direct-end", "gateway-to-end", "unwired"],
)
def test_wired_rejected(tmp_path, monkeypatch, nodes, flows) -> None:
    _write(tmp_path, nodes, flows)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        checker.main()
    assert str(exc.value).startswith("FAIL:")
