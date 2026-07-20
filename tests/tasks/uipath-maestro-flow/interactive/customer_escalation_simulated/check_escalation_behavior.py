#!/usr/bin/env python3
"""Customer-escalation flow: BEHAVIORAL (capability) correctness check.

Companion to the reference `check_customer_escalation_flow.py`, rewritten for
the *simulated* variant. The reference checker pins the implementation SHAPE
(">=2 core.action.script nodes", "exactly 1 core.logic.decision"). That shape
is fair for the non-simulated task, whose prompt dictates it ("use one script
node for urgency and another for VIP"). It is a BOOBY TRAP for the simulated
task: the non-technical persona never knows — and is forbidden to utter — the
words "script", "node" or "decision", so a correct flow that classifies with an
autonomous agent node, or routes with a `switch`, is failed for a requirement
that could never be elicited.

This checker instead asserts the flow's OBSERVABLE BEHAVIOUR — the capabilities
the persona actually described — and stays agnostic about *how* they are built
(script, connector, agent node, switch, if, …). Static-only: the sandbox has no
live Outlook/Slack tenant, so we read the .flow rather than execute it.

Asserts the flow can:
  1. Start from a trigger (any trigger — manual fallback is legitimate).
  2. Route/branch on the incoming email (a decision / switch / if / branch, or
     an agent node that emits a routing signal) with >=2 outcomes.
  3. Consider BOTH routing signals the persona asked for: urgency and VIP
     (referenced anywhere — a script, a condition, or an agent prompt).
  4. Notify on Slack (the high-touch VIP+urgent branch).
  5. Reply to the sender by email (a non-trigger Outlook / Office365 / Graph
     reference).
  6. Create a support ticket on the standard branch (a ticketing connector —
     Jira / ServiceNow / create-issue — OR a script that builds a ticket).

Name is intentionally NOT checked here — it is a separately-weighted criterion
so a working-but-misnamed flow keeps most of its credit.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path
from typing import Any, NoReturn

FLOW_GLOB = "**/*.flow"


def fail(msg: str) -> NoReturn:
    sys.exit(f"FAIL: {msg}")


def load_flow() -> dict[str, Any]:
    matches = [m for m in glob.glob(FLOW_GLOB, recursive=True) if "/." not in "/" + m]
    if not matches:
        fail(f"No .flow file found (searched {FLOW_GLOB})")
    path = Path(sorted(matches)[0])
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def node_type(node: dict) -> str:
    return (node.get("type") or "").lower()


def is_trigger(node: dict) -> bool:
    return "trigger" in node_type(node) or node.get("isTrigger") is True


def node_refs(node: dict, *needles: str) -> bool:
    """True if any needle appears in this node's serialized JSON. Ties a
    capability to a real node regardless of which node type or property slot
    expresses it — while avoiding false positives from a dangling reference to
    a node that no longer exists."""
    blob = json.dumps(node, default=str).lower()
    return any(needle in blob for needle in needles)


def any_node_refs(nodes: list[dict], *needles: str, exclude_triggers: bool = False) -> bool:
    return any(
        (not exclude_triggers or not is_trigger(n)) and node_refs(n, *needles) for n in nodes
    )


def main() -> None:
    flow = load_flow()
    nodes = flow.get("nodes")
    edges = flow.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        fail("Flow must contain nodes[] and edges[]")

    # 1. Trigger
    if not any(is_trigger(n) for n in nodes):
        fail("No trigger node found (flow should start on a new email / trigger)")

    # 2. Routing with >=2 outcomes — accept decision, switch, if, branch, or an
    #    agent node that classifies. Prove branching by outgoing edges OR by
    #    multiple terminal nodes.
    routing_nodes = [
        n
        for n in nodes
        if any(k in node_type(n) for k in ("decision", "switch", "logic.if", "branch"))
        or "agent" in node_type(n)
    ]
    if not routing_nodes:
        fail("No routing construct found (need a decision / switch / if / agent-based classifier)")

    def out_edge_count(node_id: Any) -> int:
        return sum(
            1
            for e in edges
            if node_id in (e.get("sourceNodeId"), e.get("source"), e.get("from"), e.get("sourceId"))
        )

    max_branches = max((out_edge_count(n.get("id")) for n in routing_nodes), default=0)
    terminals = [n for n in nodes if "end" in node_type(n) or "terminate" in node_type(n)]
    if max_branches < 2 and len(terminals) < 2:
        fail("Routing does not fan out into >=2 branches (VIP-urgent vs standard)")

    # 3. Both routing signals referenced on a real node (script / condition / agent prompt)
    if not any_node_refs(nodes, "urgent", "urgen"):
        fail("No 'urgency' signal on any node (flow should classify emails by urgency)")
    if not any_node_refs(nodes, "vip"):
        fail("No 'VIP' signal on any node (flow should classify the sender as VIP or not)")

    # 4. Slack notification (VIP+urgent branch)
    if not any_node_refs(nodes, "slack"):
        fail("No Slack node (the high-touch branch should notify on Slack)")

    # 5. Reply to sender by email on a non-trigger node
    if not any_node_refs(nodes, "outlook", "office365", "graph.microsoft.com", exclude_triggers=True):
        fail("No non-trigger Outlook/Graph email-reply node (flow should reply to the sender)")

    # 6. Support ticket on the standard branch (connector or a script that builds one)
    if not any_node_refs(nodes, "jira", "servicenow", "create-issue", "createissue", "ticket"):
        fail("No support-ticket node (standard branch should create a ticket)")

    print(
        f"PASS: {len(nodes)} nodes — trigger, routing into "
        f"{max(max_branches, len(terminals))} branches, urgency+VIP signals, "
        f"Slack notify, email reply, and ticket creation all present"
    )


if __name__ == "__main__":
    main()
