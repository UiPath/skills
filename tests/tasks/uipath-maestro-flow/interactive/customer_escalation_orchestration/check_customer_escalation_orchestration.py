#!/usr/bin/env python3
"""Run seeded escalation cases and verify full orchestration outcomes."""

from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path
from typing import Any, NoReturn


_directory = os.path.dirname(os.path.abspath(__file__))
while _directory != os.path.dirname(_directory) and not os.path.isdir(
    os.path.join(_directory, "_shared")
):
    _directory = os.path.dirname(_directory)
sys.path.insert(0, _directory)

from _shared.flow_check import assert_output_nonempty, run_debug  # noqa: E402


FLOW_GLOB = "CustomerEscalationOrchestration/CustomerEscalationOrchestration/CustomerEscalationOrchestration.flow"
REQUIRED_OUTPUTS = [
    "accountId",
    "contactId",
    "severity",
    "engineeringHandoff",
    "route",
    "jiraAction",
    "jiraIssueKey",
    "driveAction",
    "outlookAction",
    "slackAction",
    "responseDraft",
    "exceptionCode",
    "caseKey",
]


def fail(message: str) -> NoReturn:
    raise SystemExit(f"FAIL: {message}")


def normalized(value: Any) -> Any:
    """Normalize runtime scalar output without accepting loose substrings."""
    if isinstance(value, str):
        text = value.strip()
        lowered = text.casefold()
        if lowered in ("true", "yes"):
            return True
        if lowered in ("false", "no"):
            return False
        return lowered
    return value


def assert_named_equals(payload: dict, name: str, expected: Any) -> None:
    actual = assert_output_nonempty(payload, name)
    if normalized(actual) != normalized(expected):
        fail(f"output {name!r}: expected {expected!r}, got {actual!r}")


def assert_named_contains(payload: dict, name: str, needles: list[str]) -> None:
    actual = assert_output_nonempty(payload, name)
    haystack = json.dumps(actual, default=str).casefold()
    missing = [needle for needle in needles if needle.casefold() not in haystack]
    if missing:
        fail(f"output {name!r} missing {missing}; got {actual!r}")


def load_flow() -> dict[str, Any]:
    matches = glob.glob(FLOW_GLOB)
    if not matches:
        fail(f"No flow file matching {FLOW_GLOB}")
    path = Path(matches[0])
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def _node_type(node: dict[str, Any]) -> str:
    return str(node.get("type") or "").lower()


def _node_label(node: dict[str, Any]) -> str:
    return json.dumps(node, default=str).casefold()


def _source(edge: dict[str, Any]) -> Any:
    return edge.get("sourceNodeId") or edge.get("source") or edge.get("from") or edge.get("sourceId")


def _target(edge: dict[str, Any]) -> Any:
    return edge.get("targetNodeId") or edge.get("target") or edge.get("to") or edge.get("targetId")


def _reachable(start: set[str], edges: list[dict[str, Any]]) -> set[str]:
    graph: dict[str, list[str]] = {}
    for edge in edges:
        source = _source(edge)
        target = _target(edge)
        if isinstance(source, str) and isinstance(target, str):
            graph.setdefault(source, []).append(target)
    seen: set[str] = set()
    stack = list(start)
    while stack:
        node = stack.pop()
        for child in graph.get(node, []):
            if child not in seen:
                seen.add(child)
                stack.append(child)
    return seen


def assert_structural_orchestration() -> None:
    flow = load_flow()
    nodes = flow.get("nodes")
    edges = flow.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        fail("Flow must contain nodes[] and edges[]")

    if len(nodes) < 8:
        fail(f"Expected a multi-stage orchestration with >=8 nodes, found {len(nodes)}")

    branch_nodes = [
        node
        for node in nodes
        if "core.logic.decision" in _node_type(node)
        or "core.logic.switch" in _node_type(node)
    ]
    if len(branch_nodes) < 2:
        fail(
            "Expected at least two branch nodes for severity, duplicate, and exception routing; "
            f"found {len(branch_nodes)}"
        )

    scripts_or_agents = [
        node
        for node in nodes
        if "core.action.script" in _node_type(node)
        or "uipath.agent" in _node_type(node)
    ]
    if len(scripts_or_agents) < 4:
        fail(f"Expected >=4 script/agent stages, found {len(scripts_or_agents)}")

    flow_blob = json.dumps(flow, default=str).casefold()
    required_surface_terms = {
        "outlook": "Outlook email parsing / acknowledgement",
        "salesforce": "Salesforce account/contact/case lookup",
        "jira": "Jira duplicate/create/update routing",
        "drive": "Drive summary or attachment archiving",
        "slack": "Slack escalation notification",
        "severity agent": "inline severity agent handoff",
        "draft agent": "response draft agent handoff",
        "invalid_agent_json": "invalid agent JSON exception path",
        "salesforce_no_match": "missing Salesforce match exception path",
    }
    for term, label in required_surface_terms.items():
        if term not in flow_blob:
            fail(f"Flow does not mention required surface/policy: {label} ({term!r})")

    variables = flow.get("variables") or {}
    globals_list = variables.get("globals") or []
    out_vars = {
        str(item.get("id") or item.get("name"))
        for item in globals_list
        if item.get("direction") == "out"
    }
    missing_outputs = [name for name in REQUIRED_OUTPUTS if name not in out_vars]
    if missing_outputs:
        fail(f"Flow does not declare required out variables: {missing_outputs}")

    trigger_ids = {
        str(node.get("id"))
        for node in nodes
        if "trigger" in _node_type(node) or node.get("isTrigger") is True
    }
    end_ids = {str(node.get("id")) for node in nodes if "core.control.end" in _node_type(node)}
    if not trigger_ids:
        fail("No trigger node found")
    if not end_ids:
        fail("No end node found")
    reachable = _reachable(trigger_ids, edges)
    if not end_ids & reachable:
        fail("No end node is reachable from the trigger")

    # Guard against a relabeled basic triage flow that never models service stages.
    service_stage_hits = 0
    for node in nodes:
        blob = _node_label(node)
        if any(term in blob for term in ("salesforce", "jira", "drive", "slack", "outlook")):
            service_stage_hits += 1
    if service_stage_hits < 4:
        fail(
            "Expected at least four distinct service-facing stages mentioning Outlook, "
            f"Salesforce, Jira, Drive, or Slack; found {service_stage_hits}"
        )


def verify_case(case: dict[str, Any]) -> None:
    payload = run_debug(inputs=case["inputs"], timeout=360)
    for name, expected in case["expected"].items():
        assert_named_equals(payload, name, expected)
    assert_named_contains(payload, "responseDraft", case.get("draft_contains") or [])
    print(f"OK: {case['name']} produced the expected orchestration outputs")


def main() -> None:
    assert_structural_orchestration()
    seed_path = Path("seed.json")
    if not seed_path.is_file():
        fail("seed.json is missing; pre_run did not complete")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    cases = seed.get("cases")
    if not isinstance(cases, list) or len(cases) != 4:
        fail("seed.json must contain exactly four cases")
    for case in cases:
        verify_case(case)


if __name__ == "__main__":
    main()
