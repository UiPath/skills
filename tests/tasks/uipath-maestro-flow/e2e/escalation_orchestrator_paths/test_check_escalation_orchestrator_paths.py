"""Unit tests for the CustomerEscalationOrchestrator effects grader.

Two layouts, both cut down from real agent builds: the two-branch flow every
2026-11-17/18 nightly produced (classify Script, Decision, one Slack node and
one End per branch) and a single-Slack-node flow that renders the alert or the
notice from the path. The request allows both. Payloads have the shape
`uip maestro flow debug --output json` returns.
"""

from __future__ import annotations

import importlib.util
import json
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CHANNEL = "C0B2FDZD1M3"


def _grader():
    spec = importlib.util.spec_from_file_location(
        "check_escalation_orchestrator_paths", os.path.join(HERE, "check_escalation_orchestrator_paths.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed_cases():
    spec = importlib.util.spec_from_file_location("orchestrator_seed", os.path.join(HERE, "_setup", "seed.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_seed()["cases"]


def _slack_node(node_id: str) -> dict:
    return {
        "id": node_id,
        "type": "uipath.connector.uipath-salesforce-slack.send-message-to-channel",
        "inputs": {
            "detail": {
                "connector": "uipath-salesforce-slack",
                "connectionId": "849e85d8-1aa9-4d52-8bbd-20041c8f05d8",
                "connectionFolderKey": "5da18ec0-7de1-4e57-aaf1-ddc8a369c199",
                "bodyParameters": {"channel": CHANNEL, "messageToSend": "=js:$vars.classify.output.message"},
                "queryParameters": {"send_as": "user"},
            }
        },
    }


TWO_BRANCH = [
    {"id": "start", "type": "core.trigger.manual"},
    {"id": "classify", "type": "core.action.script"},
    {"id": "isEscalation", "type": "core.logic.decision"},
    _slack_node("escalationAlert"),
    {"id": "endEscalation", "type": "core.control.end"},
    _slack_node("triageNotice"),
    {"id": "endTriage", "type": "core.control.end"},
]
ONE_SLACK = [
    {"id": "start", "type": "core.trigger.manual"},
    _slack_node("notify"),
    {"id": "end", "type": "core.control.end"},
]


def _write_project(root, nodes) -> None:
    project = root / "CustomerEscalationOrchestrator" / "CustomerEscalationOrchestrator"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(
        json.dumps({"Name": "CustomerEscalationOrchestrator", "ProjectType": "Flow"})
    )
    (project / "new.flow").write_text(json.dumps({"nodes": nodes, "edges": []}))


def _payload(case: dict, sends: list[str], ts: str, *, path_in_text: str | None = None, executed=()) -> dict:
    corr = case["inputs"]["correlationId"]
    path = path_in_text or case["expected"]["escalationPath"].replace("_", " ")
    globals_ = {**case["expected"], "slackMessageId": ts}
    for i, nid in enumerate(sends):
        globals_[f"{nid}.output"] = {
            "ok": True,
            "channel": CHANNEL,
            "ts": ts if i == 0 else f"{ts[:-1]}9",
            "message": {"text": f"{path.title()} for case {corr}"},
        }
    return {
        "finalStatus": "Completed",
        "elementExecutions": [{"elementId": i, "status": "Completed"} for i in [*executed, *sends]],
        "variables": {"globals": globals_},
    }


def _two_branch_payload(case: dict, n: int) -> dict:
    escalation = case["expected"]["escalationPath"] == "escalation"
    send, end = ("escalationAlert", "endEscalation") if escalation else ("triageNotice", "endTriage")
    return _payload(case, [send], f"17866475{n:02d}.771239", executed=("start", "classify", "isEscalation", end))


def _one_slack_payload(case: dict, n: int) -> dict:
    return _payload(case, ["notify"], f"17866475{n:02d}.771239", executed=("start", "end"))


@pytest.mark.parametrize("nodes,build", [(TWO_BRANCH, _two_branch_payload), (ONE_SLACK, _one_slack_payload)],
                         ids=["two-branch", "one-slack-node"])
def test_main_passes_every_seeded_case_on_either_layout(tmp_path, monkeypatch, nodes, build):
    _write_project(tmp_path, nodes)
    monkeypatch.chdir(tmp_path)
    cases = _seed_cases()
    (tmp_path / "seed.json").write_text(json.dumps({"cases": cases}))
    payloads = iter([build(c, n) for n, c in enumerate(cases)])
    grader = _grader()
    monkeypatch.setattr(grader, "run_debug", lambda **kwargs: next(payloads))
    grader.main()


@pytest.fixture
def two_branch(tmp_path, monkeypatch):
    _write_project(tmp_path, TWO_BRANCH)
    monkeypatch.chdir(tmp_path)
    return {c["name"]: c for c in _seed_cases()}


def test_fails_when_a_case_posts_both_the_alert_and_the_notice(two_branch):
    case = two_branch["duplicate-escalation"]
    payload = _payload(case, ["triageNotice", "escalationAlert"], "1786647501.771239",
                       executed=("start", "classify", "isEscalation", "endTriage"))
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(payload, case)
    assert "2 Slack sends completed" in str(exc.value)


def test_fails_when_the_message_does_not_name_the_path(two_branch):
    case = two_branch["unknown-customer"]
    payload = _payload(case, ["triageNotice"], "1786647501.771239", path_in_text="triage notice",
                       executed=("start", "classify", "isEscalation", "endTriage"))
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(payload, case)
    assert "unknown_customer" in str(exc.value)


def test_fails_when_the_path_order_is_wrong(two_branch):
    # Missing domain AND no match: the domain check comes first.
    case = two_branch["missing-domain"]
    wrong = {**case, "expected": {**case["expected"], "escalationPath": "unknown_customer"}}
    payload = _two_branch_payload(wrong, 1)
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(payload, case)
    assert "'escalationPath'" in str(exc.value)


def test_fails_when_no_slack_send_ran(two_branch):
    case = two_branch["sev2-degraded-with-workaround"]
    payload = _payload(case, ["escalationAlert"], "1786647501.771239",
                       executed=("start", "classify", "isEscalation", "endEscalation"))
    payload["elementExecutions"] = [e for e in payload["elementExecutions"] if e["elementId"] != "escalationAlert"]
    with pytest.raises(SystemExit) as exc:
        _grader().check_case(payload, case)
    assert "no uipath-salesforce-slack node completed" in str(exc.value)
