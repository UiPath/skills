"""Unit tests for check_customer_escalation_flow.py.

Run with ``pytest tests/tasks/uipath-maestro-flow/multi_node/customer_escalation``.

These tests pin down the contract that:
- A manual trigger plus Graph-API HTTP reply nodes is a legitimate shape
  (the skill's documented Tier-3 fallback when no Outlook connection
  exists in the sandbox).
- An Outlook-connector trigger plus a connector reply remains the
  happy path.
- Structural requirements (>=5 nodes, exactly one decision with >=2
  branches, >=2 scripts, Slack reference, non-trigger Outlook/Graph
  reference) are still enforced.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


CHECKER = Path(__file__).resolve().parent / "check_customer_escalation_flow.py"
Node = dict[str, Any]
Edge = dict[str, Any]


def _flow_dir(tmp_path: Path) -> Path:
    d = tmp_path / "CustomerEscalation" / "CustomerEscalation"
    d.mkdir(parents=True)
    return d


def _write_flow(tmp_path: Path, nodes: list[Node], edges: list[Edge]) -> None:
    payload = {"version": "1.0.0", "nodes": nodes, "edges": edges}
    (_flow_dir(tmp_path) / "CustomerEscalation.flow").write_text(json.dumps(payload))


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _manual_trigger_with_graph_replies() -> tuple[list[Node], list[Edge]]:
    nodes = [
        {"id": "start", "type": "core.trigger.manual"},
        {"id": "classify", "type": "core.action.script", "inputs": {"src": "urgency"}},
        {"id": "vip", "type": "core.action.script", "inputs": {"src": "vip"}},
        {"id": "decide", "type": "core.logic.decision"},
        {
            "id": "reply_vip",
            "type": "core.action.http.v2",
            "inputs": {"detail": {"url": "https://graph.microsoft.com/v1.0/me/messages/{id}/reply"}},
        },
        {
            "id": "reply_standard",
            "type": "core.action.http.v2",
            "inputs": {"detail": {"url": "https://graph.microsoft.com/v1.0/me/messages/{id}/reply"}},
        },
        {
            "id": "slack",
            "type": "core.action.http.v2",
            "inputs": {"detail": {"bodyParameters": {"targetConnector": "uipath-salesforce-slack"}}},
        },
        {"id": "end", "type": "core.control.end"},
    ]
    edges = [
        {"sourceNodeId": "decide", "targetNodeId": "reply_vip"},
        {"sourceNodeId": "decide", "targetNodeId": "reply_standard"},
    ]
    return nodes, edges


def _outlook_connector_shape() -> tuple[list[Node], list[Edge]]:
    nodes = [
        {"id": "start", "type": "uipath.connector.trigger.uipath-microsoft-outlook365.email-received"},
        {"id": "urgency", "type": "core.action.script"},
        {"id": "vip", "type": "core.action.script"},
        {"id": "decide", "type": "core.logic.decision"},
        {"id": "reply", "type": "uipath.connector.uipath-microsoft-outlook365.send-reply"},
        {"id": "slack", "type": "uipath.connector.uipath-salesforce-slack.send-direct-message"},
        {"id": "end", "type": "core.control.end"},
    ]
    edges = [
        {"sourceNodeId": "decide", "targetNodeId": "reply"},
        {"sourceNodeId": "decide", "targetNodeId": "slack"},
    ]
    return nodes, edges


def test_manual_trigger_with_graph_replies_passes(tmp_path: Path) -> None:
    """The Tier-3 fallback shape (the failing-run pattern) should PASS."""
    nodes, edges = _manual_trigger_with_graph_replies()
    _write_flow(tmp_path, nodes, edges)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_outlook_connector_happy_path_passes(tmp_path: Path) -> None:
    """The original IS-connector shape (Tier 1) should still PASS."""
    nodes, edges = _outlook_connector_shape()
    _write_flow(tmp_path, nodes, edges)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_missing_outlook_reference_fails(tmp_path: Path) -> None:
    """Flow with NO outlook/office365/graph reference on any reply node FAILS."""
    nodes, edges = _manual_trigger_with_graph_replies()
    # Strip Graph URLs from both reply nodes — now there's no Outlook
    # surface anywhere except trigger (which is just `manual`).
    for n in nodes:
        if n["id"].startswith("reply"):
            n["inputs"] = {"detail": {"url": "https://example.com/notify"}}
    _write_flow(tmp_path, nodes, edges)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "non-trigger Outlook reply reference" in result.stderr or "non-trigger Outlook reply reference" in result.stdout


def test_no_trigger_fails(tmp_path: Path) -> None:
    nodes, edges = _manual_trigger_with_graph_replies()
    nodes = [n for n in nodes if n["id"] != "start"]
    _write_flow(tmp_path, nodes, edges)
    result = _run(tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "trigger" in combined.lower()


def test_no_slack_reference_fails(tmp_path: Path) -> None:
    nodes, edges = _manual_trigger_with_graph_replies()
    nodes = [n for n in nodes if n["id"] != "slack"]
    _write_flow(tmp_path, nodes, edges)
    result = _run(tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "Slack" in combined or "slack" in combined


def test_decision_with_single_branch_fails(tmp_path: Path) -> None:
    nodes, edges = _manual_trigger_with_graph_replies()
    edges = [e for e in edges if e["targetNodeId"] != "reply_standard"]
    _write_flow(tmp_path, nodes, edges)
    result = _run(tmp_path)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert ">=2 outgoing edges" in combined or "branches" in combined.lower()
