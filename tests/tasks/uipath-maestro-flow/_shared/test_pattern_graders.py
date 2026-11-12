"""Each pattern grader passes a correct flow and fails the broken shape it guards.

Fixtures in `testdata/patterns/` are SDK 6.41.1 emits, stripped to nodes, edges,
subflows and variable updates: the pattern shapes as `compile` writes them, plus
the alternative authoring choices a grader must accept (a subflow in the loop
body, a recorded rejection, a var accumulator, an agent before the fan-out, a
do-while turn loop, routing on a transcript classifier). Broken cases are
mutations of a correct fixture, or an emit of the broken shape.
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

import pytest

SHARED = Path(__file__).resolve().parent
SUITE = SHARED.parent
PATTERNS = SUITE / "patterns"
FIXTURES = SHARED / "testdata" / "patterns"
BROWNFIELD = SUITE / "brownfield" / "fixture" / "BillingDisputeResolution" / "BillingDisputeResolution"


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.flow").read_text(encoding="utf-8"))


def grade(grader: str, flow: dict, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    (tmp_path / "X.flow").write_text(json.dumps(flow))
    return subprocess.run(
        [sys.executable, str(PATTERNS / grader)], cwd=tmp_path, capture_output=True, text=True, check=False
    )


def node(flow: dict, node_id: str) -> dict:
    return next(n for n in flow["nodes"] if n["id"] == node_id)


def edge(flow: dict, source: str, target: str, port: str = "output", target_port: str = "input") -> dict:
    flow["edges"].append({"sourceNodeId": source, "sourcePort": port, "targetNodeId": target, "targetPort": target_port})
    return flow


def retarget(flow: dict, source: str, port: str, target: str, target_port: str = "input") -> dict:
    for e in flow["edges"]:
        if e["sourceNodeId"] == source and e["sourcePort"] == port:
            e["targetNodeId"], e["targetPort"] = target, target_port
    return flow


def add(flow: dict, node_id: str, node_type: str, parent: str | None = None, inputs: dict | None = None) -> dict:
    flow["nodes"].append({"id": node_id, "type": node_type, "inputs": inputs or {}, **({"parentId": parent} if parent else {})})
    return flow


def drop_edges(flow: dict, keep: Callable[[dict], bool]) -> dict:
    flow["edges"] = [e for e in flow["edges"] if keep(e)]
    return flow


# ---------------------------------------------------------------- mutations


def triage_duplicated() -> dict:
    flow = fixture("triage_ai")
    for category in ("billing", "technical", "account"):
        add(flow, f"own_{category}", "core.control.end")
        retarget(flow, "pickCategory", f"outcome-{category}", f"own_{category}")
    return flow


def triage_negated() -> dict:
    """The negated spelling of a correct floor: below 0.7 goes to the person."""
    flow = fixture("triage_negated_inverted")
    gate = next(n for n in flow["nodes"] if n["type"] == "core.logic.decision" and "confidence" in json.dumps(n.get("inputs")))
    gate["inputs"]["expression"] = gate["inputs"]["expression"].replace("< 0.7", ">= 0.7")
    return flow


def triage_guarded() -> dict:
    """A correct floor behind an unrelated numeric guard on the same agent."""
    flow = fixture("triage_ai")
    gate = node(flow, "confidenceFloor")
    gate["inputs"]["expression"] = "$vars.classifyItem.output.reason.length > 0 && " + gate["inputs"]["expression"]
    return flow


def batch_unisolated() -> dict:
    return drop_edges(fixture("batch"), lambda e: e["sourcePort"] != "error")


def batch_synthesis_blind() -> dict:
    flow = fixture("batch")
    node(flow, "synthesize")["inputs"]["agentInputVariables"] = []
    return flow


def chat_no_exit() -> dict:
    return drop_edges(fixture("chat"), lambda e: not (e["sourceNodeId"] == "intakeComplete" and e["targetNodeId"] == "startProcess"))


def chat_no_report() -> dict:
    flow = fixture("chat")
    flow["nodes"] = [n for n in flow["nodes"] if n["id"] != "reportBack"]
    drop_edges(flow, lambda e: "reportBack" not in (e["sourceNodeId"], e["targetNodeId"]))
    return edge(flow, "startProcess", "end")


def panel_chained() -> dict:
    flow = fixture("panel")
    drop_edges(flow, lambda e: not (e["sourceNodeId"] == "start" and e["targetNodeId"] in ("finance", "ops")))
    drop_edges(flow, lambda e: e["sourceNodeId"] not in ("legal", "finance"))
    edge(flow, "legal", "finance", "success")
    return edge(flow, "finance", "ops", "success")


def voice_two_calls() -> dict:
    flow = fixture("voice")
    node(flow, "specialistB")["inputs"]["callContext"]["expression"] = "$vars.other.output.callContext"
    return flow


def voice_blind_router() -> dict:
    flow = fixture("voice")
    for case in node(flow, "routeCall")["inputs"]["cases"]:
        case["expression"] = "$vars.start.output.callContext.type === 'phone'"
    return flow


def review_end_in_body() -> dict:
    flow = add(fixture("batch_review"), "rejectEnd", "core.control.end", parent="processBatch")
    return retarget(flow, "reviewDecision", "outcome-reject", "rejectEnd")


def review_two_applies() -> dict:
    flow = add(fixture("batch_review"), "applyAgain", "core.logic.mock", parent="processBatch")
    retarget(flow, "reviewDecision", "outcome-approve", "applyAgain")
    return edge(flow, "applyAgain", "processBatch", target_port="continue")


def review_two_applies_joined() -> dict:
    """Each route has its own apply step, and both then meet at a shared record step."""
    flow = fixture("batch_review")
    add(flow, "applyAgain", "core.logic.mock", parent="processBatch")
    add(flow, "record", "core.action.script", parent="processBatch")
    retarget(flow, "reviewDecision", "outcome-approve", "applyAgain")
    retarget(flow, "applyDecision", "output", "record")
    edge(flow, "applyAgain", "record")
    return edge(flow, "record", "processBatch", "success", "continue")


def triage_without_person() -> dict:
    """Classify and route with the human fallback removed: what the near miss asks for."""
    flow = fixture("triage_ai")
    people = {n["id"] for n in flow["nodes"] if n["type"].startswith("uipath.human-in-the-loop")}
    flow["nodes"] = [n for n in flow["nodes"] if n["id"] not in people]
    return drop_edges(flow, lambda e: e["sourceNodeId"] not in people and e["targetNodeId"] not in people)


def export_gated() -> dict:
    return add(fixture("export"), "gate", "core.logic.decision")


CASES = [
    ("routing_triage/check_greenfield.py", "triage_ai", lambda: fixture("triage_ai"), 0),
    ("routing_triage/check_greenfield.py", "hybrid", lambda: fixture("hybrid"), 0),
    ("routing_triage/check_greenfield.py", "duplicated dispatch", triage_duplicated, 1),
    ("routing_triage/check_greenfield.py", "no confidence floor", lambda: fixture("triage_no_floor"), 1),
    ("routing_triage/check_greenfield.py", "floor on a flow variable", lambda: fixture("triage_var_floor"), 0),
    ("routing_triage/check_greenfield.py", "inverted floor", lambda: fixture("triage_inverted"), 1),
    ("routing_triage/check_greenfield.py", "null-safe floor", lambda: fixture("triage_nullish_floor"), 0),
    ("routing_triage/check_greenfield.py", "negated, inverted floor", lambda: fixture("triage_negated_inverted"), 1),
    ("routing_triage/check_greenfield.py", "negated floor", triage_negated, 0),
    ("routing_triage/check_greenfield.py", "floor bound in a variable", lambda: fixture("triage_tunable_floor"), 0),
    ("routing_triage/check_greenfield.py", "guard before the floor", triage_guarded, 0),
    ("routing_triage/check_greenfield.py", "two categories plus unrouted", lambda: fixture("triage_two_categories"), 1),
    ("batch_ai/check_greenfield.py", "batch", lambda: fixture("batch"), 0),
    ("batch_ai/check_greenfield.py", "var accumulator", lambda: fixture("batch_var"), 0),
    ("batch_ai/check_greenfield.py", "results reshaped by a script", lambda: fixture("batch_reshaped_results"), 0),
    ("batch_ai/check_greenfield.py", "unisolated failure", batch_unisolated, 1),
    ("batch_ai/check_greenfield.py", "failure terminates", lambda: fixture("batch_terminate"), 1),
    ("batch_ai/check_greenfield.py", "per-item subflow, one onError", lambda: fixture("batch_sub"), 0),
    ("batch_ai/check_greenfield.py", "synthesis ignores the loop", batch_synthesis_blind, 1),
    ("conversational_intake/check_greenfield.py", "chat back-edge", lambda: fixture("chat"), 0),
    ("conversational_intake/check_greenfield.py", "chat do-while", lambda: fixture("chat_do"), 0),
    ("conversational_intake/check_greenfield.py", "no exit", chat_no_exit, 1),
    ("conversational_intake/check_greenfield.py", "no report", chat_no_report, 1),
    ("parallel_agents/check_greenfield.py", "panel", lambda: fixture("panel"), 0),
    ("parallel_agents/check_greenfield.py", "agent before the fan-out", lambda: fixture("panel_prep"), 0),
    ("parallel_agents/check_greenfield.py", "chained reviewers", panel_chained, 1),
    ("voice_agents/check_greenfield.py", "session reason", lambda: fixture("voice"), 0),
    ("voice_agents/check_greenfield.py", "transcript classifier", lambda: fixture("voice_chain"), 0),
    ("voice_agents/check_greenfield.py", "two calls", voice_two_calls, 1),
    ("voice_agents/check_greenfield.py", "router ignores triage", voice_blind_router, 1),
    ("composition/check_batch_review.py", "batch review", lambda: fixture("batch_review"), 0),
    ("composition/check_batch_review.py", "recorded rejection", lambda: fixture("review_record"), 0),
    ("composition/check_batch_review.py", "approval recorded before the shared apply", lambda: fixture("review_recorded_before_apply"), 0),
    ("composition/check_batch_review.py", "review in a subflow", lambda: fixture("review_sub"), 0),
    ("composition/check_batch_review.py", "nested subflows", lambda: fixture("nested_subflows"), 0),
    ("composition/check_batch_review.py", "rejection still applied", lambda: fixture("reject_applies"), 1),
    ("composition/check_batch_review.py", "rejection applied in a subflow", lambda: fixture("subflow_rejection_applied"), 1),
    ("composition/check_batch_review.py", "End in the body", review_end_in_body, 1),
    ("composition/check_batch_review.py", "apply per route", review_two_applies, 1),
    ("composition/check_batch_review.py", "apply per route, then joined", review_two_applies_joined, 1),
    ("no_pattern/check_no_pattern.py", "export", lambda: fixture("export"), 0),
    ("no_pattern/check_no_pattern.py", "retrofitted gate", export_gated, 1),
    ("no_pattern_triage/check_near_miss.py", "classify and route", triage_without_person, 0),
    ("no_pattern_triage/check_near_miss.py", "human fallback added", lambda: fixture("triage_ai"), 1),
]


@pytest.mark.parametrize(("grader", "label", "build", "want"), CASES, ids=[f"{c[0].split('/')[0]}: {c[1]}" for c in CASES])
def test_grader(grader: str, label: str, build: Callable[[], dict], want: int, tmp_path: Path) -> None:
    result = grade(grader, build(), tmp_path)
    assert (result.returncode != 0) == bool(want), result.stdout + result.stderr


# ---------------------------------------------------------------- brownfield

REVIEW_GATE = "$vars.disputeAnalyst.output.confidence < 0.8"


def reviewed(mutate: Callable[[dict], None] = lambda flow: None) -> dict:
    """The fixture with a review inserted between the auto-resolve route and the credit log."""
    flow = json.loads((BROWNFIELD / "BillingDisputeResolution.flow").read_text(encoding="utf-8"))
    add(flow, "reviewGate", "core.logic.decision", inputs={"expression": REVIEW_GATE})
    add(flow, "reviewAuto", "uipath.human-in-the-loop.quick-form")
    retarget(flow, "routeByAction", "case-auto", "reviewGate")
    edge(flow, "reviewGate", "logCreditAmount", "false")
    edge(flow, "reviewGate", "reviewAuto", "true")
    edge(flow, "reviewAuto", "logCreditAmount", "outcome-approve")
    edge(flow, "reviewAuto", "returnRejection", "outcome-reject")
    mutate(flow)
    return flow


def inverted(flow: dict) -> None:
    node(flow, "reviewGate")["inputs"]["expression"] = "$vars.disputeAnalyst.output.confidence >= 0.8"


def gate_spelled(expression: str) -> Callable[[dict], None]:
    def mutate(flow: dict) -> None:
        node(flow, "reviewGate")["inputs"]["expression"] = expression
    return mutate


def rejection_posts(flow: dict) -> None:
    retarget(flow, "reviewAuto", "outcome-reject", "logCreditAmount")


def gate_bypassed(flow: dict) -> None:
    retarget(flow, "routeByAction", "case-auto", "logCreditAmount")


def posting_duplicated(flow: dict) -> None:
    post = node(flow, "financialPosting")
    flow["nodes"].append({**copy.deepcopy(post), "id": "financialPosting2"})
    retarget(flow, "reviewAuto", "outcome-approve", "financialPosting2")
    edge(flow, "financialPosting2", "resolutionWriter")


@pytest.mark.parametrize(
    ("label", "mutate", "want"),
    [("review inserted", lambda flow: None, 0), ("inverted gate", inverted, 1), ("rejection posts", rejection_posts, 1),
     ("threshold 0.80", gate_spelled("$vars.disputeAnalyst.output.confidence < 0.80"), 0),
     ("operands reversed", gate_spelled("0.8 > $vars.disputeAnalyst.output.confidence"), 0),
     ("percent", gate_spelled("$vars.disputeAnalyst.output.confidence * 100 < 80"), 0),
     ("bound in a variable", gate_spelled("$vars.disputeAnalyst.output.confidence < $vars.reviewFloor"), 0),
     ("gate bypassed", gate_bypassed, 1), ("posting duplicated", posting_duplicated, 1)],
)
def test_brownfield_grader(label: str, mutate: Callable[[dict], None], want: int, tmp_path: Path) -> None:
    project = tmp_path / "BillingDisputeResolution"
    shutil.copytree(BROWNFIELD, project)
    (project / "BillingDisputeResolution.flow").write_text(json.dumps(reviewed(mutate)))
    result = subprocess.run(
        [sys.executable, str(PATTERNS / "ai_decision_human_review" / "check_brownfield.py"),
         "--original", str(BROWNFIELD), "--project", str(project)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )
    assert (result.returncode != 0) == bool(want), result.stdout + result.stderr


# ---------------------------------------------------------------- canvas finish

CANVAS = SUITE / "patterns" / "canvas_finish" / "fixture" / "SupportTriage" / "SupportTriage"
ENDPOINTS = {"handleBilling": "https://billing.example.test/tickets",
             "handleTechnical": "https://support.example.test/tickets",
             "handleAccount": "https://accounts.example.test/requests"}


def finished(project: Path, keep: str = "") -> None:
    """Finish the canvas pattern by hand: real HTTP steps, a real prompt, the item wired in."""
    flow_path = project / "SupportTriage.flow"
    flow = json.loads(flow_path.read_text(encoding="utf-8"))
    for step, url in ENDPOINTS.items():
        if step != keep:
            n = node(flow, step)
            n["type"], n["inputs"] = "core.action.http", {"url": url, "method": "POST"}
    agent = node(flow, "classifyItem")
    agent["inputs"]["agentInputVariables"] = [{"id": "subject", "binding": "=js:$vars.start.output.subject"}]
    flow_path.write_text(json.dumps(flow))
    sidecar = project / agent["inputs"]["source"] / "agent.json"
    sidecar.write_text(sidecar.read_text(encoding="utf-8").replace("PLACEHOLDER - replace with your classification instructions.", "Classify the support email."))


def finish_grade(tmp_path: Path, prepare: Callable[[Path], None]) -> subprocess.CompletedProcess[str]:
    project = tmp_path / "SupportTriage"
    shutil.copytree(CANVAS, project)
    prepare(project)
    return subprocess.run(
        [sys.executable, str(PATTERNS / "canvas_finish" / "check_canvas_finish.py"), "--project", str(project)],
        cwd=tmp_path, capture_output=True, text=True, check=False,
    )


@pytest.mark.parametrize(
    ("label", "prepare", "want"),
    [("as the canvas inserted it", lambda project: None, 1),
     ("finished", finished, 0),
     ("one mock left", lambda project: finished(project, keep="handleAccount"), 1)],
)
def test_canvas_finish_grader(label: str, prepare: Callable[[Path], None], want: int, tmp_path: Path) -> None:
    result = finish_grade(tmp_path, prepare)
    assert (result.returncode != 0) == bool(want), result.stdout + result.stderr


def test_canvas_fixture_keeps_the_triage_shape(tmp_path: Path) -> None:
    result = grade("routing_triage/check_greenfield.py", json.loads((CANVAS / "SupportTriage.flow").read_text(encoding="utf-8")), tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
