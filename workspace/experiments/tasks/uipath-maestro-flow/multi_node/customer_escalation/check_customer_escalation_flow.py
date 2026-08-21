#!/usr/bin/env python3
"""Customer-escalation flow: structural assertions.

Checks the .flow file the agent produced. Static-only because the prompt is
validate-only (no live Outlook / Slack tenant). Mirrors the
check_devcon_expense_approval.py shape.

The trigger type is intentionally NOT pinned to Outlook: when no
`uipath-microsoft-outlook365` connection exists in the sandbox, the flow
skill's documented Tier-3 fallback is `core.trigger.manual` plus Graph
API HTTP replies. The flow's semantic intent ("talks to Outlook") is
already proved by the non-trigger Outlook-or-Graph reference assertion
below.

Asserts:
  1. Total node count >= 5 (trigger + 2 scripts + decision + at least one branch action)
  2. Exactly one trigger node present (any type — manual fallback is legitimate)
  3. >=2 script nodes (urgency + VIP classifier)
  4. Exactly one core.logic.decision node, with >=2 outgoing edges (two branches)
  5. Slack connector referenced somewhere in the flow (VIP branch DM)
  6. Outlook reply referenced by at least one *non-trigger* node — matches
     `outlook`, `office365`, or `graph.microsoft.com` (Graph API replies
     are the same surface the connector wraps).
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path
from typing import Any, NoReturn


FLOW_GLOB = "CustomerEscalation/CustomerEscalation/CustomerEscalation.flow"


def fail(msg: str) -> NoReturn:
    sys.exit(f"FAIL: {msg}")


def load_flow() -> dict[str, Any]:
    matches = glob.glob(FLOW_GLOB)
    if not matches:
        fail(f"No flow file matching {FLOW_GLOB}")
    path = Path(matches[0])
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def node_type(node: dict) -> str:
    return (node.get("type") or "").lower()


def references(node: dict, needle: str) -> bool:
    """Cheap 'does this node mention <needle>' check across type + serialized
    inputs/extension fields. Catches connector keys like
    `uipath.connector.microsoft-office365.<op>` and the slack equivalents
    regardless of which slot the agent put them in."""
    needle = needle.lower()
    if needle in node_type(node):
        return True
    blob = json.dumps(node, default=str).lower()
    return needle in blob


def is_trigger(node: dict) -> bool:
    t = node_type(node)
    return "trigger" in t or node.get("isTrigger") is True


def main() -> None:
    flow = load_flow()
    nodes = flow.get("nodes")
    edges = flow.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        fail("Flow must contain nodes[] and edges[]")

    if len(nodes) < 5:
        fail(f"Expected >=5 nodes (trigger + 2 scripts + decision + branch action(s)), found {len(nodes)}")

    triggers = [n for n in nodes if is_trigger(n)]
    if not triggers:
        fail("No trigger node found")
    if len(triggers) > 1:
        fail(f"Expected exactly one trigger node, found {len(triggers)}")

    scripts = [n for n in nodes if node_type(n) == "core.action.script"]
    if len(scripts) < 2:
        fail(f"Expected >=2 core.action.script nodes (urgency + VIP classifier), found {len(scripts)}")

    decisions = [n for n in nodes if node_type(n) == "core.logic.decision"]
    if len(decisions) != 1:
        fail(f"Expected exactly one core.logic.decision node, found {len(decisions)}")
    decision_id = decisions[0].get("id")
    if not decision_id:
        fail("Decision node missing id")

    out_edges = [
        e for e in edges
        if decision_id in (e.get("sourceNodeId"), e.get("source"), e.get("from"), e.get("sourceId"))
    ]
    if len(out_edges) < 2:
        fail(f"Decision node must have >=2 outgoing edges (VIP + standard), found {len(out_edges)}")

    if not any(references(n, "slack") for n in nodes):
        fail("No Slack connector reference found anywhere in flow (VIP branch should DM via Slack)")

    outlook_needles = ("outlook", "office365", "graph.microsoft.com")
    non_trigger_outlook = [
        n for n in nodes
        if not is_trigger(n) and any(references(n, needle) for needle in outlook_needles)
    ]
    if not non_trigger_outlook:
        fail(
            "No non-trigger Outlook reply reference found "
            f"(expected one of {outlook_needles} on a reply-to-sender action on at least one branch)"
        )

    print(
        f"PASS: {len(nodes)} nodes, {len(scripts)} scripts, decision with {len(out_edges)} branches, "
        f"Slack and Outlook reply references present"
    )


if __name__ == "__main__":
    main()
