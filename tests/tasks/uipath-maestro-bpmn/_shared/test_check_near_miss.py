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
    "RejM": "endEvent",
    "EndF": "endEvent",
    "BodyEnd": "endEvent",
    "BodyRej": "endEvent",
    "BodyStart": "startEvent",
    "Agent": "serviceTask",
    "Audit": "serviceTask",
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
CATCH_ALL = "<bpmn:errorEventDefinition />"
TERMINATE = "<bpmn:terminateEventDefinition />"


def _ends(definition: str, *names: str) -> dict[str, str]:
    return {n: f'<bpmn:endEvent id="{n}">{definition}</bpmn:endEvent>' for n in names}


def _without(flows: list[tuple], *pairs: tuple) -> list[tuple]:
    return [f for f in flows if f[:2] not in pairs]


ERROR_ENDS = _ends(ERROR, "RejC", "RejF")
TERMINATE_ENDS = _ends(TERMINATE, "RejC", "RejF")
MESSAGE = "<bpmn:messageEventDefinition />"
ESCALATION = "<bpmn:escalationEventDefinition />"

# The guide's route: every reject edge into reject_merge, one notify, one end.
GUIDE_REJECTS = (
    _without(PRE_JOIN, ("GateC", "RejC"), ("GateF", "RejF"), ("Decision", "NotifyRej"))
    + [
        ("GateC", "RejectMerge", '=vars.Var_C == "Reject"'),
        ("GateF", "RejectMerge", '=vars.Var_F == "Reject"'),
        ("Decision", "RejectMerge", MANAGER_REJECT),
        ("RejectMerge", "NotifyRej"),
    ]
)


def _handler(
    start_attrs: str = "",
    error: str = ERROR,
    sub_attrs: str = ' triggeredByEvent="true"',
    inner: str = "",
    key: str = "OnReject",
) -> str:
    return (
        f'<bpmn:subProcess id="{key}"{sub_attrs}>'
        f'<bpmn:startEvent id="{key}Start"{start_attrs}>{error}</bpmn:startEvent>{inner}'
        f'<bpmn:endEvent id="{key}End" />'
        f'<bpmn:sequenceFlow id="{key}Flow" sourceRef="{key}Start" targetRef="{key}End" />'
        "</bpmn:subProcess>"
    )


def _boundary(attached: str = "Body", attrs: str = "") -> dict[str, str]:
    return {"Caught": f'<bpmn:boundaryEvent id="Caught" attachedToRef="{attached}"{attrs}>{ERROR}</bpmn:boundaryEvent>'}


# The parallel stage sits in embedded subprocess Body and completes at BodyEnd;
# Manager follows Body, and an error boundary on Body routes the rejection.
IN_BODY = [("BodyStart", "Fork")] + PRE_JOIN_GATES[1:-1] + [("Join", "BodyEnd")]
BODY = frozenset(n for flow in IN_BODY for n in flow[:2])
SUBPROCESS_BOUNDARY = (
    [("Start", "Body"), ("Body", "Manager"), ("Caught", "RejectMerge")]
    + IN_BODY
    + [
        ("Manager", "Decision"),
        ("Decision", "Provision"),
        ("Decision", "RejectMerge", MANAGER_REJECT),
        ("RejectMerge", "NotifyRej"),
    ]
    + APPROVED_TAIL
)

# Fork, reviews, join and Manager all sit in Body, which goes on to Provision.
WHOLE_BODY = (
    [("Start", "Body"), ("Body", "Provision"), ("BodyStart", "Fork")]
    + PRE_JOIN_GATES[1:]
    + [("Manager", "Decision"), ("Decision", "BodyEnd", '=vars.Var_M == "Approve"'), ("Decision", "RejM", MANAGER_REJECT)]
    + APPROVED_TAIL[:2]
)
WHOLE_BODY_NODES = frozenset(n for flow in WHOLE_BODY[2:-2] for n in flow[:2])

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
    "catch-all-handler": (PRE_JOIN, ERROR_ENDS, _handler(error=CATCH_ALL), frozenset()),
    "terminate-end": (PRE_JOIN, TERMINATE_ENDS, "", frozenset()),
    "guide-reject-merge-terminate": (GUIDE_REJECTS, _ends(TERMINATE, "EndRej"), "", frozenset()),
    "guide-reject-merge-throw-notify": (
        GUIDE_REJECTS,
        {**_ends(TERMINATE, "EndRej"), "NotifyRej": f'<bpmn:intermediateThrowEvent id="NotifyRej">{MESSAGE}</bpmn:intermediateThrowEvent>'},
        "",
        frozenset(),
    ),
    "guide-reject-merge-caught-error": (GUIDE_REJECTS, _ends(ERROR, "EndRej"), _handler(), frozenset()),
    "redo-loop": (PRE_JOIN + [("GateC", "Compliance", '=vars.Var_C == "Redo"')], ERROR_ENDS, _handler(), frozenset()),
    "review-on-reject-path": (
        _without(PRE_JOIN, ("GateC", "RejC")) + [("GateC", "Ack", '=vars.Var_C == "Reject"'), ("Ack", "RejC")],
        {**ERROR_ENDS, "Ack": '<bpmn:userTask id="Ack" />'},
        _handler(),
        frozenset(),
    ),
    "subprocess-error-boundary": (SUBPROCESS_BOUNDARY, {**ERROR_ENDS, **_boundary()}, "", BODY),
}

PRE_JOIN_MESSAGE = (
    "whose exits that skip the join stay out of the joined chain and end only at "
    "process-level terminate ends or caught error ends"
)
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
    "handler-not-event-subprocess": (PRE_JOIN, ERROR_ENDS, _handler(sub_attrs=""), frozenset()),
    "handler-in-sibling-subprocess": (
        PRE_JOIN,
        ERROR_ENDS,
        f'<bpmn:subProcess id="Other">{_handler()}</bpmn:subProcess>',
        frozenset(),
    ),
    "error-end-without-errorref": (PRE_JOIN, _ends(CATCH_ALL, "RejC", "RejF"), _handler(error=CATCH_ALL), frozenset()),
    "undeclared-error": (
        PRE_JOIN,
        _ends('<bpmn:errorEventDefinition errorRef="Ghost" />', "RejC", "RejF"),
        _handler(error=CATCH_ALL),
        frozenset(),
    ),
    "error-without-code": (
        PRE_JOIN,
        _ends('<bpmn:errorEventDefinition errorRef="NoCode" />', "RejC", "RejF"),
        _handler(error=CATCH_ALL),
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
        _without(PRE_JOIN, ("GateC", "RejC"))
        + [("GateC", "RejectRoute", '=vars.Var_C == "Reject"'), ("RejectRoute", "RejC"), ("RejectRoute", "Manager")],
        {**ERROR_ENDS, **_ends(TERMINATE, "EndOk", "EndRej")},
        _handler(),
        frozenset(),
    ),
    "escalate-to-manager": (
        PRE_JOIN + [("GateC", "Manager", '=vars.Var_C == "Escalate"')],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "reject-provisions": (
        PRE_JOIN + [("GateC", "Provision", '=vars.Var_C == "Hold"')],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "reject-exit-without-end": (
        _without(PRE_JOIN, ("GateC", "RejC")) + [("GateC", "Loop", '=vars.Var_C == "Reject"'), ("Loop", "Loop")],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "approve-to-plain-end": (
        _without(PRE_JOIN, ("GateF", "Join")) + [("GateF", "EndF", '=vars.Var_F == "Approve"')],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "service-task-ungated": (
        _without(PRE_JOIN, ("Fork", "Finance"), ("Finance", "GateF"), ("GateF", "Join"), ("GateF", "RejF"))
        + [("Fork", "Agent"), ("Agent", "Join")],
        ERROR_ENDS,
        _handler(inner='<bpmn:userTask id="Ack" />'),
        frozenset(),
    ),
    "shared-verdict-gate": (
        _without(PRE_JOIN, ("Compliance", "GateC"), ("Finance", "GateF"), ("GateF", "Join"), ("GateF", "RejF"))
        + [("Compliance", "GateC"), ("Finance", "GateC")],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "no-review-before-join": (
        [
            ("Start", "Intake"),
            ("Intake", "Fork"),
            ("Fork", "GateC"),
            ("GateC", "Join"),
            ("GateC", "RejC", '=vars.Var_C == "Reject"'),
            ("Fork", "GateF"),
            ("GateF", "Join"),
            ("GateF", "RejF", '=vars.Var_F == "Reject"'),
            ("Join", "Manager"),
            ("Manager", "Decision"),
            ("Decision", "Director"),
            ("Decision", "NotifyRej", MANAGER_REJECT),
            ("Director", "Decision2"),
            ("Decision2", "Provision"),
            ("Decision2", "NotifyRej", '=vars.Var_D == "Reject"'),
        ]
        + APPROVED_TAIL,
        {**ERROR_ENDS, "Intake": '<bpmn:userTask id="Intake" />'},
        _handler(),
        frozenset(),
    ),
    "handler-with-message-start": (
        PRE_JOIN,
        ERROR_ENDS,
        _handler(error="<bpmn:messageEventDefinition />"),
        frozenset(),
    ),
    "gate-without-reject-exit": (
        _without(PRE_JOIN, ("GateC", "RejC")) + [("GateC", "Join", '=vars.Var_C == "Reject"')],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "bypass-behind-gate": (
        _without(PRE_JOIN, ("Fork", "Finance"))
        + [("Fork", "Pre"), ("Pre", "Finance"), ("Pre", "RejF", '=vars.Var_P == "Reject"'), ("Finance", "Join")],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "review-feeds-review": (
        _without(PRE_JOIN, ("Finance", "GateF"), ("GateF", "Join"), ("GateF", "RejF")) + [("Finance", "Compliance")],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "timer-boundary": (
        SUBPROCESS_BOUNDARY,
        {**ERROR_ENDS, "Caught": '<bpmn:boundaryEvent id="Caught" attachedToRef="Body"><bpmn:timerEventDefinition /></bpmn:boundaryEvent>'},
        "",
        BODY,
    ),
    "boundary-catches-other-error": (
        SUBPROCESS_BOUNDARY,
        {**ERROR_ENDS, "Caught": '<bpmn:boundaryEvent id="Caught" attachedToRef="Body"><bpmn:errorEventDefinition errorRef="Other" /></bpmn:boundaryEvent>'},
        "",
        BODY,
    ),
    "subprocess-boundary-reaches-manager": (
        _without(SUBPROCESS_BOUNDARY, ("Caught", "RejectMerge")) + [("Caught", "Manager")],
        {**ERROR_ENDS, **_boundary()},
        "",
        BODY,
    ),
    "boundary-on-review": (SUBPROCESS_BOUNDARY, {**ERROR_ENDS, **_boundary("Compliance")}, "", BODY),
    "non-interrupting-boundary": (
        SUBPROCESS_BOUNDARY,
        {**ERROR_ENDS, **_boundary(attrs=' cancelActivity="false"')},
        "",
        BODY,
    ),
    "escalate-splits-to-manager": (
        PRE_JOIN + [("GateC", "X2", '=vars.Var_C == "Escalate"'), ("X2", "Join"), ("X2", "Manager", '=vars.Var_X == 1')],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "escalate-splits-to-plain-end": (
        PRE_JOIN + [("GateC", "X2", '=vars.Var_C == "Escalate"'), ("X2", "Join"), ("X2", "EndF", '=vars.Var_X == 1')],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "approve-forks-to-manager": (
        _without(PRE_JOIN, ("GateC", "Join"))
        + [("GateC", "P2", '=vars.Var_C == "Approve"'), ("P2", "Join"), ("P2", "Manager")],
        {**ERROR_ENDS, "P2": '<bpmn:parallelGateway id="P2" />'},
        _handler(),
        frozenset(),
    ),
    "pre-review-gate-to-plain-end": (
        _without(PRE_JOIN, ("Fork", "Finance")) + [("Fork", "Pre"), ("Pre", "Finance"), ("Pre", "EndF", '=vars.Var_P == 1')],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "hold-via-merge-to-provision": (
        PRE_JOIN + [("GateC", "HoldMerge", '=vars.Var_C == "Hold"'), ("HoldMerge", "Provision")],
        {**ERROR_ENDS, **_ends(TERMINATE, "EndOk")},
        _handler(),
        frozenset(),
    ),
    "hold-to-script-provision": (
        _without(PRE_JOIN, ("Decision", "Provision"))
        + [("Decision", "Record"), ("Record", "NotifyOk"), ("GateC", "Record", '=vars.Var_C == "Hold"')],
        {**ERROR_ENDS, **_ends(TERMINATE, "EndOk")},
        _handler(),
        frozenset(),
    ),
    "hold-to-approved-notify": (
        PRE_JOIN + [("GateC", "NotifyOk", '=vars.Var_C == "Hold"')],
        {**ERROR_ENDS, **_ends(TERMINATE, "EndOk")},
        _handler(),
        frozenset(),
    ),
    "reject-merge-reaches-manager": (
        GUIDE_REJECTS + [("RejectMerge", "Manager", '=vars.Var_X == 1')],
        _ends(TERMINATE, "EndRej", "EndOk"),
        "",
        frozenset(),
    ),
    "reject-merge-reaches-provision": (
        GUIDE_REJECTS + [("RejectMerge", "Provision", '=vars.Var_X == 1')],
        _ends(TERMINATE, "EndRej", "EndOk"),
        "",
        frozenset(),
    ),
    "escalate-into-other-review": (
        PRE_JOIN + [("GateC", "Finance", '=vars.Var_C == "Escalate"')],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "escalate-into-other-gate": (
        PRE_JOIN + [("GateC", "GateF", '=vars.Var_C == "Escalate"')],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "approve-into-other-review": (
        _without(PRE_JOIN, ("GateF", "Join")) + [("GateF", "Compliance", '=vars.Var_F == "Approve"')],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "skip-exit-loops": (
        PRE_JOIN + [("GateC", "Loop", '=vars.Var_C == "Hold"'), ("Loop", "Loop")],
        ERROR_ENDS,
        _handler(),
        frozenset(),
    ),
    "hold-provisions-terminate": (
        PRE_JOIN + [("GateC", "Provision", '=vars.Var_C == "Hold"')],
        {**ERROR_ENDS, **_ends(TERMINATE, "EndOk")},
        _handler(),
        frozenset(),
    ),
    "inner-handler-hides-outer": (
        _without(SUBPROCESS_BOUNDARY, ("Caught", "RejectMerge")),
        ERROR_ENDS,
        _handler(),
        BODY,
        _handler(key="InnerReject"),
    ),
    "inner-handler-hides-boundary": (
        SUBPROCESS_BOUNDARY,
        {**ERROR_ENDS, **_boundary()},
        "",
        BODY,
        _handler(key="InnerReject"),
    ),
    "boundary-to-manager-hides-handler": (
        _without(SUBPROCESS_BOUNDARY, ("Caught", "RejectMerge")) + [("Caught", "Manager")],
        {**ERROR_ENDS, **_boundary()},
        _handler(),
        BODY,
    ),
    "branch-never-joins": (
        _without(PRE_JOIN, ("GateF", "Join")) + [("GateF", "RejF2", '=vars.Var_F == "Approve"')],
        {**ERROR_ENDS, **_ends(ERROR, "RejF2")},
        _handler(),
        frozenset(),
    ),
    "terminate-in-subprocess": (WHOLE_BODY, {**TERMINATE_ENDS, **_ends(TERMINATE, "RejM")}, "", WHOLE_BODY_NODES),
    "handler-in-subprocess": (
        WHOLE_BODY,
        {**ERROR_ENDS, **_ends(TERMINATE, "RejM")},
        "",
        WHOLE_BODY_NODES,
        _handler(),
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
    "second-gate-on-one-exit": (
        PARALLEL_STAGE
        + STAGE_GATE
        + [
            ("NotifyRej", "EndRej"),
            ("Manager", "Decision"),
            ("Decision", "Audit", '=vars.Var_M == "Audit"'),
            ("Decision", "Gate2", '=vars.Var_M == "Go"'),
            ("Gate2", "EndOk", '=vars.Var_X == 1'),
            ("Gate2", "EndRej", '=vars.Var_X == 0'),
        ],
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


# The risk-tiered layout: the chain in subprocess Chain, both Manager exits end
# inside it, and gate Approved after Chain re-reads the verdicts.
RISK_TIERED = (
    [("Start", "Body"), ("Body", "Approved"), ("BodyStart", "Fork")]
    + PARALLEL_STAGE[1:]
    + [("Join", "Stage"), ("Stage", "Manager"), ("Stage", "BodyRej", PARALLEL_REJECT)]
    + [("Manager", "Decision"), ("Decision", "BodyEnd"), ("Decision", "RejM", MANAGER_REJECT)]
    + [("Approved", "Provision"), ("Approved", "NotifyRej", MANAGER_REJECT)]
    + APPROVED_TAIL
)
RISK_TIERED_NODES = frozenset(n for flow in RISK_TIERED[2:-5] for n in flow[:2])

# The stock stage gate with every review and end inside Body, then one process end.
SUBPROCESS_END_ACCEPTED = {
    "stock-shape-in-subprocess": (
        [("Start", "Body"), ("Body", "EndOk"), ("BodyStart", "Fork")]
        + PARALLEL_STAGE[1:]
        + STAGE_GATE
        + MANAGER_VERDICT
        + [("Provision", "NotifyOk"), ("NotifyOk", "BodyEnd"), ("NotifyRej", "BodyRej")],
        frozenset(
            {"BodyStart", "Fork", "Compliance", "Finance", "Join", "Stage", "Manager", "Decision"}
            | {"Provision", "NotifyOk", "NotifyRej", "BodyEnd", "BodyRej"}
        ),
        "",
    ),
    "risk-tiered-approved-gate": (RISK_TIERED, RISK_TIERED_NODES, ""),
}

# A plain end inside an embedded subprocess is not final: the subprocess
# completes and its outgoing flow runs.
STAGE_IN_BODY = (
    [
        ("Start", "Body"),
        ("Body", "Manager"),
        ("BodyStart", "Fork"),
        ("Fork", "Compliance"),
        ("Fork", "Finance"),
        ("Compliance", "Join"),
        ("Finance", "Join"),
        ("Join", "Stage"),
        ("Stage", "BodyEnd"),
        ("Stage", "BodyRej", PARALLEL_REJECT),
    ]
    + MANAGER_VERDICT
    + APPROVED_TAIL
)
STAGE_IN_BODY_NODES = frozenset({"BodyStart", "Fork", "Compliance", "Finance", "Join", "Stage", "BodyEnd", "BodyRej"})
STAGE_MESSAGE = "without an exclusive gateway that can exit to an end past every later review"
VERDICT_MESSAGE = "offers a second route to an end"

SUBPROCESS_END_REJECTED = {
    "stage-gate-in-subprocess": (STAGE_IN_BODY, ERROR_ENDS, STAGE_IN_BODY_NODES, "", STAGE_MESSAGE),
    "stage-gate-message-end-in-subprocess": (
        STAGE_IN_BODY,
        _ends(MESSAGE, "BodyRej"),
        STAGE_IN_BODY_NODES,
        "",
        STAGE_MESSAGE,
    ),
    "stage-gate-terminate-in-subprocess": (
        STAGE_IN_BODY,
        _ends(TERMINATE, "BodyRej"),
        STAGE_IN_BODY_NODES,
        "",
        STAGE_MESSAGE,
    ),
    "manager-reject-in-subprocess": (WHOLE_BODY, ERROR_ENDS, WHOLE_BODY_NODES, _handler(), VERDICT_MESSAGE),
    "manager-message-end-in-subprocess": (
        WHOLE_BODY,
        {**ERROR_ENDS, **_ends(MESSAGE, "RejM")},
        WHOLE_BODY_NODES,
        _handler(),
        VERDICT_MESSAGE,
    ),
    "manager-terminate-in-subprocess": (
        WHOLE_BODY,
        {**ERROR_ENDS, **_ends(TERMINATE, "RejM")},
        WHOLE_BODY_NODES,
        _handler(),
        VERDICT_MESSAGE,
    ),
    "manager-escalation-end-in-subprocess": (
        WHOLE_BODY,
        {**ERROR_ENDS, **_ends(ESCALATION, "RejM")},
        WHOLE_BODY_NODES,
        _handler(),
        VERDICT_MESSAGE,
    ),
}



def _nested_boundary(reject_end: str) -> str:
    """The codex shape one level deeper: the error boundary sits on Inner, inside Outer."""
    branch = "".join(
        f'<bpmn:userTask id="{r}" /><bpmn:exclusiveGateway id="Gate{r[0]}" />'
        f'<bpmn:endEvent id="Rej{r[0]}">{ERROR}</bpmn:endEvent>'
        for r in ("Compliance", "Finance")
    )
    flows = [
        ("InnerStart", "Fork"),
        ("Fork", "Compliance"),
        ("Fork", "Finance"),
        ("Compliance", "GateC"),
        ("GateC", "Join", '=vars.Var_C == "Approve"'),
        ("GateC", "RejC", '=vars.Var_C == "Reject"'),
        ("Finance", "GateF"),
        ("GateF", "Join", '=vars.Var_F == "Approve"'),
        ("GateF", "RejF", '=vars.Var_F == "Reject"'),
        ("Join", "InnerEnd"),
    ]
    inner_flows = "".join(
        f'<bpmn:sequenceFlow id="I{i}" sourceRef="{f[0]}" targetRef="{f[1]}">'
        + (f"<bpmn:conditionExpression>{f[2]}</bpmn:conditionExpression>" if len(f) > 2 else "")
        + "</bpmn:sequenceFlow>"
        for i, f in enumerate(flows)
    )
    outer_flows = [("Start", "Outer"), ("Outer", "Manager")] + MANAGER_VERDICT + APPROVED_TAIL
    process_flows = "".join(
        f'<bpmn:sequenceFlow id="P{i}" sourceRef="{f[0]}" targetRef="{f[1]}">'
        + (f"<bpmn:conditionExpression>{f[2]}</bpmn:conditionExpression>" if len(f) > 2 else "")
        + "</bpmn:sequenceFlow>"
        for i, f in enumerate(outer_flows)
    )
    process_nodes = "".join(
        f'<bpmn:{KINDS.get(n, "exclusiveGateway")} id="{n}" />'
        for n in ("Start", "Manager", "Decision", "Provision", "NotifyOk", "NotifyRej", "EndOk", "EndRej")
    )
    return (
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI">'
        '<bpmn:error id="Err" errorCode="REJECTED" /><bpmn:process id="P">'
        f'{process_nodes}<bpmn:subProcess id="Outer"><bpmn:startEvent id="OuterStart" />'
        '<bpmn:subProcess id="Inner"><bpmn:startEvent id="InnerStart" /><bpmn:parallelGateway id="Fork" />'
        f'{branch}<bpmn:parallelGateway id="Join" /><bpmn:endEvent id="InnerEnd" />{inner_flows}</bpmn:subProcess>'
        f'<bpmn:boundaryEvent id="Caught" attachedToRef="Inner">{ERROR}</bpmn:boundaryEvent>'
        f'<bpmn:endEvent id="OuterRej">{reject_end}</bpmn:endEvent><bpmn:endEvent id="OuterEnd" />'
        '<bpmn:sequenceFlow id="O0" sourceRef="OuterStart" targetRef="Inner" />'
        '<bpmn:sequenceFlow id="O1" sourceRef="Inner" targetRef="OuterEnd" />'
        '<bpmn:sequenceFlow id="O2" sourceRef="Caught" targetRef="OuterRej" />'
        f"</bpmn:subProcess>{process_flows}</bpmn:process>"
        '<bpmndi:BPMNDiagram id="D" /></bpmn:definitions>'
    )


def _load():
    spec = importlib.util.spec_from_file_location("check_near_miss", _CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load()


def _write(
    tmp_path: Path,
    flows: list[tuple],
    bodies: dict | None = None,
    extra: str = "",
    scoped: frozenset = frozenset(),
    body_extra: str = "",
) -> None:
    node_ids = sorted({node for flow in flows for node in flow[:2]} - {"Body"})
    xml = {n: (bodies or {}).get(n, f'<bpmn:{KINDS.get(n, "exclusiveGateway")} id="{n}" />') for n in node_ids}
    flow_xml = {True: "", False: ""}
    for i, flow in enumerate(flows):
        condition = f"<bpmn:conditionExpression>{flow[2]}</bpmn:conditionExpression>" if len(flow) > 2 else ""
        flow_xml[flow[0] in scoped] += (
            f'<bpmn:sequenceFlow id="F{i}" sourceRef="{flow[0]}" targetRef="{flow[1]}">{condition}</bpmn:sequenceFlow>'
        )
    nodes = "".join(xml[n] for n in node_ids if n not in scoped) + extra
    if scoped:
        inner = "".join(xml[n] for n in sorted(scoped))
        nodes += f'<bpmn:subProcess id="Body">{inner}{body_extra}{flow_xml[True]}</bpmn:subProcess>'
    project = tmp_path / "VendorOnboarding"
    project.mkdir()
    (project / "VendorOnboarding.bpmn").write_text(
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI">'
        '<bpmn:error id="Err" errorCode="REJECTED" /><bpmn:error id="Other" errorCode="OTHER" /><bpmn:error id="NoCode" />'
        f'<bpmn:process id="P">{nodes}{flow_xml[False]}</bpmn:process>'
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


@pytest.mark.parametrize("name", sorted(SUBPROCESS_END_REJECTED))
def test_subprocess_end_rejected(tmp_path, monkeypatch, name) -> None:
    flows, bodies, scoped, extra, message = SUBPROCESS_END_REJECTED[name]
    _write(tmp_path, flows, bodies, extra, scoped)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        checker.main()
    assert message in str(excinfo.value)


@pytest.mark.parametrize("name", sorted(SUBPROCESS_END_ACCEPTED))
def test_subprocess_end_accepted(tmp_path, monkeypatch, name) -> None:
    flows, scoped, extra = SUBPROCESS_END_ACCEPTED[name]
    _write(tmp_path, flows, {}, extra, scoped)
    monkeypatch.chdir(tmp_path)
    checker.main()


@pytest.mark.parametrize("reject_end", [MESSAGE, TERMINATE])
def test_nested_boundary_to_completing_end(tmp_path, monkeypatch, reject_end) -> None:
    project = tmp_path / "VendorOnboarding"
    project.mkdir()
    (project / "VendorOnboarding.bpmn").write_text(_nested_boundary(reject_end), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        checker.main()
    assert PRE_JOIN_MESSAGE in str(excinfo.value)
