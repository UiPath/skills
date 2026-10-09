"""Approval-chain near-miss shapes in patterns/approval_chain/check_near_miss."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_CHECKER = Path(__file__).resolve().parents[1] / "patterns" / "approval_chain" / "check_near_miss.py"

KINDS = {
    "Start": "startEvent",
    "Fork": "parallelGateway",
    "Join": "parallelGateway",
    "Compliance": "userTask",
    "Finance": "userTask",
    "Manager": "userTask",
    "Director": "userTask",
    "Record": "scriptTask",
    "Provision": "serviceTask",
    "NotifyOk": "sendTask",
    "NotifyRej": "sendTask",
    "EndOk": "endEvent",
    "EndRej": "endEvent",
}
PARALLEL_REJECT = '=vars.Var_C == "Reject" || vars.Var_F == "Reject"'
MANAGER_REJECT = '=vars.Var_M == "Reject"'
PARALLEL_STAGE = [
    ("Start", "Fork"),
    ("Fork", "Compliance"),
    ("Fork", "Finance"),
    ("Compliance", "Join"),
    ("Finance", "Join"),
]
APPROVED_TAIL = [("Provision", "NotifyOk"), ("NotifyOk", "EndOk"), ("NotifyRej", "EndRej")]
STAGE_GATE = [("Join", "Stage"), ("Stage", "Manager"), ("Stage", "NotifyRej", PARALLEL_REJECT)]
MANAGER_VERDICT = [
    ("Manager", "Decision"),
    ("Decision", "Provision"),
    ("Decision", "NotifyRej", MANAGER_REJECT),
]

SHAPES_ACCEPTED = {
    "stage-gate": PARALLEL_STAGE + STAGE_GATE + MANAGER_VERDICT + APPROVED_TAIL,
    "reject-merge": PARALLEL_STAGE
    + [
        ("Join", "Stage"),
        ("Stage", "Manager"),
        ("Stage", "RejectMerge", PARALLEL_REJECT),
        ("Manager", "Decision"),
        ("Decision", "Provision"),
        ("Decision", "RejectMerge", MANAGER_REJECT),
        ("RejectMerge", "NotifyRej"),
    ]
    + APPROVED_TAIL,
    "rejects-share-end": PARALLEL_STAGE
    + [("Join", "Stage"), ("Stage", "Manager"), ("Stage", "EndRej", PARALLEL_REJECT)]
    + MANAGER_VERDICT
    + APPROVED_TAIL,
    "per-reviewer-gates": PARALLEL_STAGE
    + [
        ("Join", "GateC"),
        ("GateC", "GateF"),
        ("GateC", "NotifyRej", '=vars.Var_C == "Reject"'),
        ("GateF", "Manager"),
        ("GateF", "NotifyRej", '=vars.Var_F == "Reject"'),
    ]
    + MANAGER_VERDICT
    + APPROVED_TAIL,
    "script-before-verdict": PARALLEL_STAGE
    + STAGE_GATE
    + [
        ("Manager", "Record"),
        ("Record", "Decision"),
        ("Decision", "Provision"),
        ("Decision", "NotifyRej", MANAGER_REJECT),
    ]
    + APPROVED_TAIL,
    "two-sequential-reviews": PARALLEL_STAGE
    + STAGE_GATE
    + [
        ("Manager", "Decision"),
        ("Decision", "Director"),
        ("Decision", "NotifyRej", MANAGER_REJECT),
        ("Director", "Decision2"),
        ("Decision2", "Provision"),
        ("Decision2", "NotifyRej", '=vars.Var_D == "Reject"'),
    ]
    + APPROVED_TAIL,
}

SHAPES_REJECTED = {
    "serial-pair-behind-gateway": (
        [("Start", "Fork"), ("Fork", "Compliance"), ("Compliance", "Finance"), ("Finance", "Join")]
        + STAGE_GATE
        + MANAGER_VERDICT
        + APPROVED_TAIL,
        "no parallel gateway reaches two review tasks",
    ),
    "no-stage-gate": (
        PARALLEL_STAGE + [("Join", "Manager")] + MANAGER_VERDICT + APPROVED_TAIL,
        "without an exclusive gateway that can exit to an end past every later review",
    ),
    "alternative-reviews": (
        PARALLEL_STAGE
        + [
            ("Join", "Pick"),
            ("Pick", "Manager", "=vars.Var_C == 1"),
            ("Pick", "Director", "=vars.Var_F == 1"),
            ("Manager", "EndOk"),
            ("Director", "EndRej"),
        ],
        "without an exclusive gateway that can exit to an end past every later review",
    ),
    "verdict-bypassed": (
        PARALLEL_STAGE + STAGE_GATE + [("Manager", "Provision")] + APPROVED_TAIL,
        "reaches an end without an exclusive gateway",
    ),
    "single-exit-verdict": (
        PARALLEL_STAGE + STAGE_GATE + [("Manager", "Decision"), ("Decision", "Provision")] + APPROVED_TAIL,
        "offers a second route to an end",
    ),
    "provision-before-verdict": (
        PARALLEL_STAGE
        + STAGE_GATE
        + [
            ("Manager", "Provision"),
            ("Provision", "Decision"),
            ("Decision", "NotifyOk"),
            ("Decision", "NotifyRej", MANAGER_REJECT),
            ("NotifyOk", "EndOk"),
            ("NotifyRej", "EndRej"),
        ],
        "before its verdict gateway",
    ),
    "skip-manager": (
        PARALLEL_STAGE
        + STAGE_GATE
        + [("Stage", "Provision", '=vars.Var_C == "Fast"')]
        + MANAGER_VERDICT
        + APPROVED_TAIL,
        "can finish without its approval",
    ),
}


def _load():
    spec = importlib.util.spec_from_file_location("check_near_miss", _CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load()


def _write(tmp_path: Path, flows: list[tuple]) -> None:
    node_ids = sorted({node for flow in flows for node in flow[:2]})
    nodes = "".join(f'<bpmn:{KINDS.get(n, "exclusiveGateway")} id="{n}" />' for n in node_ids)
    flow_xml = ""
    for i, flow in enumerate(flows):
        condition = f"<bpmn:conditionExpression>{flow[2]}</bpmn:conditionExpression>" if len(flow) > 2 else ""
        flow_xml += f'<bpmn:sequenceFlow id="F{i}" sourceRef="{flow[0]}" targetRef="{flow[1]}">{condition}</bpmn:sequenceFlow>'
    project = tmp_path / "VendorOnboarding"
    project.mkdir()
    (project / "VendorOnboarding.bpmn").write_text(
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI">'
        f'<bpmn:process id="P">{nodes}{flow_xml}</bpmn:process>'
        '<bpmndi:BPMNDiagram id="D" /></bpmn:definitions>',
        encoding="utf-8",
    )


@pytest.mark.parametrize("name", sorted(SHAPES_ACCEPTED))
def test_shape_accepted(tmp_path, monkeypatch, name) -> None:
    _write(tmp_path, SHAPES_ACCEPTED[name])
    monkeypatch.chdir(tmp_path)
    checker.main()


@pytest.mark.parametrize("name", sorted(SHAPES_REJECTED))
def test_shape_rejected(tmp_path, monkeypatch, name) -> None:
    flows, message = SHAPES_REJECTED[name]
    _write(tmp_path, flows)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        checker.main()
    assert message in str(excinfo.value)
