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
    "RejC": "endEvent",
    "RejF": "endEvent",
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

PRE_JOIN_GATES = [
    ("Start", "Fork"),
    ("Fork", "Compliance"),
    ("Fork", "Finance"),
    ("Compliance", "GateC"),
    ("GateC", "Join", '=vars.Var_C == "Approve"'),
    ("GateC", "RejC", '=vars.Var_C == "Reject"'),
    ("Finance", "GateF"),
    ("GateF", "Join", '=vars.Var_F == "Approve"'),
    ("GateF", "RejF", '=vars.Var_F == "Reject"'),
    ("Join", "Manager"),
]
PRE_JOIN = PRE_JOIN_GATES + MANAGER_VERDICT + APPROVED_TAIL
ERROR = '<bpmn:errorEventDefinition errorRef="Err" />'
TERMINATE = "<bpmn:terminateEventDefinition />"


def _ends(definition: str, *names: str) -> dict[str, str]:
    return {n: f'<bpmn:endEvent id="{n}">{definition}</bpmn:endEvent>' for n in names}


ERROR_ENDS = _ends(ERROR, "RejC", "RejF")
TERMINATE_ENDS = _ends(TERMINATE, "RejC", "RejF")


def _handler(start_attrs: str = "", error: str = ERROR) -> str:
    return (
        '<bpmn:subProcess id="OnReject" triggeredByEvent="true">'
        f'<bpmn:startEvent id="Caught"{start_attrs}>{error}</bpmn:startEvent>'
        '<bpmn:endEvent id="Handled" />'
        '<bpmn:sequenceFlow id="H0" sourceRef="Caught" targetRef="Handled" />'
        "</bpmn:subProcess>"
    )


BOUNDARY = {"Caught": f'<bpmn:boundaryEvent id="Caught" attachedToRef="Body">{ERROR}</bpmn:boundaryEvent>'}
BODY = frozenset(n for flow in PRE_JOIN for n in flow[:2]) - {"Start", "NotifyRej", "EndRej"}

PRE_JOIN_ACCEPTED = {
    "vendor-onboarding-run": (
        PRE_JOIN_GATES
        + [
            ("Manager", "Decision"),
            ("Decision", "Provision"),
            ("Decision", "RejM", MANAGER_REJECT),
            ("Provision", "NotifyOk"),
            ("NotifyOk", "EndOk"),
        ],
        {**ERROR_ENDS, **_ends(ERROR, "RejM")},
        _handler(),
        frozenset(),
    ),
    "error-end-event-subprocess": (PRE_JOIN, ERROR_ENDS, _handler(), frozenset()),
    "terminate-end": (PRE_JOIN, TERMINATE_ENDS, "", frozenset()),
    "error-end-boundary": (
        PRE_JOIN + [("Caught", "NotifyRej")],
        {**ERROR_ENDS, **BOUNDARY},
        "",
        BODY,
    ),
}

PRE_JOIN_MESSAGE = "without an exclusive gateway that can exit to an end past every later review"
PRE_JOIN_REJECTED = {
    "plain-end": (PRE_JOIN, {}, "", frozenset()),
    "uncaught-error-end": (PRE_JOIN, ERROR_ENDS, "", frozenset()),
    "non-interrupting-handler": (PRE_JOIN, ERROR_ENDS, _handler(' isInterrupting="false"'), frozenset()),
    "handler-catches-other-error": (
        PRE_JOIN,
        ERROR_ENDS,
        _handler(error='<bpmn:errorEventDefinition errorRef="Other" />'),
        frozenset(),
    ),
    "one-branch-ungated": (
        [f for f in PRE_JOIN if f[0] != "GateF" and f[1] != "GateF"] + [("Finance", "Join")],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "branch-bypasses-gate": (PRE_JOIN + [("Finance", "Join")], ERROR_ENDS, _handler(), frozenset()),
    "reject-reaches-manager": (
        [f for f in PRE_JOIN if f[:2] != ("GateC", "RejC")]
        + [("GateC", "RejectRoute", '=vars.Var_C == "Reject"'), ("RejectRoute", "RejC"), ("RejectRoute", "Manager")],
        {**ERROR_ENDS, **_ends(TERMINATE, "EndOk", "EndRej")},
        _handler(),
        frozenset(),
    ),
    "boundary-reaches-manager": (
        PRE_JOIN + [("Caught", "Manager")],
        {**ERROR_ENDS, **BOUNDARY},
        "",
        BODY,
    ),
}

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
    "reviews-share-later-verdict": (
        PARALLEL_STAGE
        + STAGE_GATE
        + [("Manager", "Director"), ("Director", "Decision")]
        + MANAGER_VERDICT[1:]
        + APPROVED_TAIL,
        "no exclusive gateway after Manager offers a second route",
    ),
    "rejection-loops": (
        PARALLEL_STAGE
        + STAGE_GATE
        + [
            ("Manager", "Decision"),
            ("Decision", "Provision"),
            ("Decision", "DeadLoop", MANAGER_REJECT),
            ("DeadLoop", "DeadLoop"),
        ]
        + APPROVED_TAIL,
        "no exclusive gateway after Manager offers a second route",
    ),
    "rejection-reconverges": (
        PARALLEL_STAGE
        + [("Join", "Stage"), ("Stage", "Manager"), ("Stage", "EndRej", PARALLEL_REJECT)]
        + MANAGER_VERDICT
        + [("NotifyRej", "Provision")]
        + APPROVED_TAIL[:2],
        "no exclusive gateway after Manager offers a second route",
    ),
}


def _load():
    spec = importlib.util.spec_from_file_location("check_near_miss", _CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load()


def _write(
    tmp_path: Path, flows: list[tuple], bodies: dict | None = None, extra: str = "", scoped: frozenset = frozenset()
) -> None:
    node_ids = sorted({node for flow in flows for node in flow[:2]})
    xml = {n: (bodies or {}).get(n, f'<bpmn:{KINDS.get(n, "exclusiveGateway")} id="{n}" />') for n in node_ids}
    nodes = "".join(xml[n] for n in node_ids if n not in scoped) + extra
    if scoped:
        nodes += '<bpmn:subProcess id="Body">' + "".join(xml[n] for n in node_ids if n in scoped) + "</bpmn:subProcess>"
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


@pytest.mark.parametrize("name", sorted(PRE_JOIN_ACCEPTED))
def test_pre_join_accepted(tmp_path, monkeypatch, name) -> None:
    _write(tmp_path, *PRE_JOIN_ACCEPTED[name])
    monkeypatch.chdir(tmp_path)
    checker.main()


@pytest.mark.parametrize("name", sorted(PRE_JOIN_REJECTED))
def test_pre_join_rejected(tmp_path, monkeypatch, name) -> None:
    _write(tmp_path, *PRE_JOIN_REJECTED[name])
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        checker.main()
    assert PRE_JOIN_MESSAGE in str(excinfo.value)
