#!/usr/bin/env python3
"""Customer-escalation BPMN process: BEHAVIORAL (capability) correctness check.

Ported from Flow `interactive/customer_escalation_simulated/`'s
``check_escalation_behavior.py``: same non-technical-persona scenario (an
Outlook-triggered triage that routes on urgency+VIP into a Slack-notify path
or a ticket-creation path), translated from a JSON nodes[]/edges[] walk to an
XML walk over the ``.bpmn`` process. The simulated persona never utters
"trigger", "connector", "decision", "script", or "node", so — exactly as the
Flow checker's docstring argues — this stays agnostic about *how* the process
implements each capability (script task, connector activity, agent node,
gateway, …) and only asserts the OBSERVABLE BEHAVIOUR the persona actually
described. Static-only: the sandbox has no live Outlook/Slack tenant, so we
read the ``.bpmn`` rather than execute it.

Assertion map (Flow → BPMN):
  F check_escalation_behavior.py:93     any trigger node                      -> elements(root, "startEvent")
  F check_escalation_behavior.py:99-108 decision/switch/if/branch/agent node,  -> gateway (exclusive/inclusive) + agent
                                         >=2 outcomes                            (Orchestrator.StartAgentJob) nodes; branch via
                                                                                 sequenceFlow sourceRef fan-out or >=2 endEvents
  F check_escalation_behavior.py:131-136 'urgent'/'urgen' and 'vip' referenced -> urgent/VIP text anywhere in the BPMN
                                         anywhere on a node                       document (script bodies, conditions,
                                                                                 agent prompts/inputs)
  F check_escalation_behavior.py:139-140 'slack' referenced anywhere on a node -> "slack" text anywhere on a flow element
  F check_escalation_behavior.py:143-148 'outlook'/'office365'/                -> same substrings, anywhere on a
                                         'graph.microsoft.com' on a             non-startEvent flow element
                                         non-trigger node
  F check_escalation_behavior.py:151-157 'jira'/'servicenow'/'create-issue'/   -> same substrings, anywhere on a
                                         'createissue'/'ticket' on a node        flow element
  I               locate/parse .bpmn (file exists, well-formed XML)           -> parse_bpmn()
  T               substring/text search across the whole element XML          -> node_text() / any_element_refs(),
                                         (any node type, any property slot)       mirrors Flow's json.dumps(node).lower()
  T               'conditions' explicitly named as a valid urgency/VIP        -> urgent/VIP search covers the whole
                                         signal location (sequenceFlow                document text, not just node
                                         conditionExpression lives on an edge,        elements, since a BPMN
                                         not a node)                                  conditionExpression is not itself
                                                                                       a "node"
  DROPPED         require_no_private_connector_values                        (not in Flow)
  DROPPED         require_sequence_integrity                                 (not in Flow; `bpmn validate` criterion covers structure)
  DROPPED         require_di_for_visible_elements                            (not in Flow; `bpmn validate` criterion covers structure)
  DROPPED         connection-binding check (=bindings.<id> resolves to a      (Flow never checked connections)
                  declared Connection binding)
  DROPPED         gateway-precedes-branch sequence-flow reaches() ordering    (Flow only checked branch fan-out
                  check                                                        count, not order)

Name is intentionally NOT checked here — it is a separately-weighted criterion
so a working-but-misnamed process keeps most of its credit.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import NS, elements, fail, parse_bpmn  # noqa: E402

# Flow element tags treated as "nodes" for text search — mirrors Flow's
# nodes[] (as opposed to edges[]/sequenceFlow, which is searched separately
# and only for the urgency/VIP signal, since "conditions" is an explicitly
# named valid location for that signal).
_NODE_TAGS = (
    "startEvent",
    "endEvent",
    "intermediateCatchEvent",
    "intermediateThrowEvent",
    "boundaryEvent",
    "task",
    "scriptTask",
    "serviceTask",
    "sendTask",
    "receiveTask",
    "userTask",
    "businessRuleTask",
    "callActivity",
    "subProcess",
    "exclusiveGateway",
    "inclusiveGateway",
    "parallelGateway",
    "eventBasedGateway",
)

AGENT_TOKEN = "startagentjob"  # Orchestrator.StartAgentJob, matched loosely


def collect_nodes(root: ET.Element) -> list[ET.Element]:
    nodes: list[ET.Element] = []
    for tag in _NODE_TAGS:
        nodes.extend(elements(root, tag))
    return nodes


def node_text(node: ET.Element) -> str:
    """Serialized lowercase XML of one node — ties a capability to a real
    element regardless of which sub-element or attribute expresses it, the
    same tolerance Flow's ``json.dumps(node).lower()`` gave a JSON node."""
    return ET.tostring(node, encoding="unicode").lower()


def any_element_refs(
    nodes: list[ET.Element], *needles: str, exclude_start_events: bool = False
) -> bool:
    return any(
        (not exclude_start_events or node.tag.rsplit("}", 1)[-1] != "startEvent")
        and any(needle in node_text(node) for needle in needles)
        for node in nodes
    )


def out_edge_count(root: ET.Element, node_id: str) -> int:
    return sum(
        1
        for flow in elements(root, "sequenceFlow")
        if flow.attrib.get("sourceRef") == node_id
    )


def main() -> None:
    path, root = parse_bpmn()
    nodes = collect_nodes(root)
    if not nodes:
        fail("BPMN process has no flow elements")

    # 1. Trigger — any start event (manual, or a connector Intsvc.EventTrigger).
    if not elements(root, "startEvent"):
        fail("No start event found (process should start on a new email / trigger)")

    # 2. Routing with >=2 outcomes — accept an exclusive/inclusive gateway, or
    #    an agent node (Orchestrator.StartAgentJob) that classifies. Prove
    #    branching by outgoing sequence flows OR by multiple end events.
    gateway_nodes = elements(root, "exclusiveGateway") + elements(root, "inclusiveGateway")
    agent_nodes = [n for n in nodes if AGENT_TOKEN in node_text(n)]
    routing_nodes = gateway_nodes + [n for n in agent_nodes if n not in gateway_nodes]
    if not routing_nodes:
        fail(
            "No routing construct found (need an exclusive/inclusive gateway "
            "or an agent-based classifier feeding one)"
        )

    def node_id(n: ET.Element) -> str:
        return n.attrib.get("id", "")

    max_branches = max(
        (out_edge_count(root, node_id(n)) for n in routing_nodes), default=0
    )
    terminals = elements(root, "endEvent")
    if max_branches < 2 and len(terminals) < 2:
        fail("Routing does not fan out into >=2 branches (VIP-urgent vs standard)")

    # 3. Both routing signals referenced anywhere in the BPMN text (a script
    #    body, a sequenceFlow condition, or an agent prompt/input). Search the
    #    whole document since a conditionExpression lives on an edge, not a
    #    node, and the persona's own wording explicitly names "conditions" as
    #    a valid signal location.
    document_text = ET.tostring(root, encoding="unicode").lower()
    if not any(needle in document_text for needle in ("urgent", "urgen")):
        fail(
            "No 'urgency' signal anywhere in the BPMN (process should "
            "classify emails by urgency)"
        )
    if "vip" not in document_text:
        fail(
            "No 'VIP' signal anywhere in the BPMN (process should classify "
            "the sender as VIP or not)"
        )

    # 4. Slack notification (VIP+urgent branch)
    if not any_element_refs(nodes, "slack"):
        fail("No Slack node (the high-touch branch should notify on Slack)")

    # 5. Reply to sender by email on a non-trigger (non-startEvent) node
    if not any_element_refs(
        nodes,
        "outlook",
        "office365",
        "graph.microsoft.com",
        exclude_start_events=True,
    ):
        fail(
            "No non-trigger Outlook/Graph email-reply node (process should "
            "reply to the sender)"
        )

    # 6. Support ticket on the standard branch (connector or a script that
    #    builds one)
    if not any_element_refs(
        nodes, "jira", "servicenow", "create-issue", "createissue", "ticket"
    ):
        fail("No support-ticket node (standard branch should create a ticket)")

    print(
        f"PASS: {path} — {len(nodes)} flow elements — start event, routing into "
        f"{max(max_branches, len(terminals))} branches, urgency+VIP signals, "
        f"Slack notify, email reply, and ticket creation all present"
    )


if __name__ == "__main__":
    main()
