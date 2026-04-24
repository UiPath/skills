#!/usr/bin/env python3
"""CustomerEscalation: structural checks for the multi-branch escalation flow.

The flow is validate-only (see task YAML description): seeding an inbox email
via the shared Outlook connection is unreliable, and the flow has real side
effects (Slack DMs to rocky.madden@uipath.com, outbound Outlook replies) that
shouldn't run in CI. Instead we verify the *shape* of the .flow:

  check_trigger           Outlook email-received trigger present.
  check_pre_decision      Two script nodes sit between trigger and decision.
  check_decision_fanout   Exactly one decision node with two outgoing edges.
  check_vip_branch        Branch A (VIP) has >=2 Slack send-message nodes and
                          >=1 Outlook action node.
  check_standard_branch   Branch B (non-VIP) has >=1 script node (ticket gen)
                          and >=1 Outlook action node.

"VIP branch" is identified as whichever decision branch contains Slack nodes;
this is agnostic to how the agent names its condition expression.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from collections import deque
from typing import Iterable

OUTLOOK_TRIGGER_MARKER = (
    "uipath.connector.trigger.uipath-microsoft-outlook365.email-received"
)
OUTLOOK_ACTION_MARKER = "uipath.connector.uipath-microsoft-outlook365."
SLACK_SEND_MARKER = "uipath.connector.uipath-salesforce-slack.send-message"
SCRIPT_TYPE = "core.action.script"
DECISION_TYPE = "core.logic.decision"


def _fail(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    sys.exit(f"FAIL: {msg}")


def _read_flow() -> dict:
    flows = glob.glob("**/CustomerEscalation*.flow", recursive=True)
    if not flows:
        _fail("no CustomerEscalation*.flow found under cwd")
    with open(flows[0]) as f:
        return json.load(f)


def _nodes_by_id(flow: dict) -> dict[str, dict]:
    return {n["id"]: n for n in flow.get("nodes", []) if "id" in n}


def _edges(flow: dict) -> list[dict]:
    return list(flow.get("edges", []) or [])


def _find_single(flow: dict, type_marker: str, *, substring: bool = False) -> dict:
    if substring:
        matches = [n for n in flow.get("nodes", []) if type_marker in n.get("type", "")]
        label = f"containing {type_marker!r}"
    else:
        matches = [n for n in flow.get("nodes", []) if n.get("type") == type_marker]
        label = repr(type_marker)
    if not matches:
        _fail(
            f"no node with type {label}; "
            f"types seen: {sorted({n.get('type') for n in flow.get('nodes', [])})}"
        )
    if len(matches) > 1:
        _fail(
            f"expected exactly 1 node with type {label}, found {len(matches)}: "
            f"{[n['id'] for n in matches]}"
        )
    return matches[0]


def _outgoing(edges: list[dict], source_id: str) -> list[str]:
    return [e["target"] for e in edges if e.get("source") == source_id]


def _reachable(
    start: str, edges: list[dict], stop_types: set[str], node_map: dict[str, dict]
) -> set[str]:
    """BFS forward from start, collecting node IDs. Does not cross nodes whose
    type is in stop_types (used to keep branches from re-merging past End /
    another Decision and contaminating the count)."""
    seen: set[str] = set()
    q = deque([start])
    while q:
        nid = q.popleft()
        if nid in seen:
            continue
        seen.add(nid)
        if node_map.get(nid, {}).get("type") in stop_types:
            continue
        for tgt in _outgoing(edges, nid):
            if tgt not in seen:
                q.append(tgt)
    return seen


def _count_types(ids: Iterable[str], node_map: dict[str, dict]) -> dict[str, int]:
    counts: dict[str, int] = {
        "script": 0,
        "slack_send": 0,
        "outlook_action": 0,
        "decision": 0,
        "end": 0,
    }
    for nid in ids:
        n = node_map.get(nid)
        if not n:
            continue
        t = n.get("type", "")
        if t == SCRIPT_TYPE:
            counts["script"] += 1
        elif t == SLACK_SEND_MARKER:
            counts["slack_send"] += 1
        elif OUTLOOK_ACTION_MARKER in t and OUTLOOK_TRIGGER_MARKER not in t:
            counts["outlook_action"] += 1
        elif t == DECISION_TYPE:
            counts["decision"] += 1
        elif t == "core.control.end":
            counts["end"] += 1
    return counts


def _branch_counts(flow: dict) -> tuple[dict[str, int], dict[str, int]]:
    """Return (vip_branch_counts, standard_branch_counts).

    Each decision target seeds a forward walk; walks stop at End nodes so they
    don't leak into each other through a post-merge join. The branch with any
    Slack node is the VIP branch.
    """
    node_map = _nodes_by_id(flow)
    edges = _edges(flow)
    decision = _find_single(flow, DECISION_TYPE)
    targets = _outgoing(edges, decision["id"])
    if len(targets) != 2:
        _fail(
            f"decision node {decision['id']} has {len(targets)} outgoing edges, expected 2. "
            f"Targets: {targets}"
        )
    stop = {"core.control.end", "core.logic.terminate"}
    # Exclude the decision node itself from each branch's reach
    reach_a = _reachable(targets[0], edges, stop, node_map) - {decision["id"]}
    reach_b = _reachable(targets[1], edges, stop, node_map) - {decision["id"]}
    counts_a = _count_types(reach_a, node_map)
    counts_b = _count_types(reach_b, node_map)
    if counts_a["slack_send"] > 0 and counts_b["slack_send"] == 0:
        return counts_a, counts_b
    if counts_b["slack_send"] > 0 and counts_a["slack_send"] == 0:
        return counts_b, counts_a
    _fail(
        "could not disambiguate VIP vs standard branches by Slack presence. "
        f"Branch-A counts={counts_a}, Branch-B counts={counts_b}. "
        "The VIP branch should contain Slack send-message nodes; the standard branch should not."
    )


# ── subcommands ─────────────────────────────────────────────────────────


def check_trigger() -> None:
    flow = _read_flow()
    _find_single(flow, OUTLOOK_TRIGGER_MARKER)
    print("OK: Outlook email-received trigger node present")


def check_pre_decision() -> None:
    """Between trigger and decision there must be >=2 script nodes (urgency +
    VIP lookup). We walk forward from the trigger and stop at the decision."""
    flow = _read_flow()
    node_map = _nodes_by_id(flow)
    edges = _edges(flow)
    trigger = _find_single(flow, OUTLOOK_TRIGGER_MARKER)
    decision = _find_single(flow, DECISION_TYPE)
    reach = _reachable(trigger["id"], edges, {DECISION_TYPE}, node_map)
    reach -= {trigger["id"], decision["id"]}
    script_count = sum(1 for nid in reach if node_map[nid].get("type") == SCRIPT_TYPE)
    if script_count < 2:
        _fail(
            f"expected >=2 script nodes between trigger and decision, found {script_count}. "
            f"Pre-decision types: {[node_map[nid].get('type') for nid in reach]}"
        )
    print(f"OK: {script_count} script nodes sit between trigger and decision")


def check_decision_fanout() -> None:
    flow = _read_flow()
    decision = _find_single(flow, DECISION_TYPE)
    targets = _outgoing(_edges(flow), decision["id"])
    if len(targets) != 2:
        _fail(f"decision node has {len(targets)} outgoing edges, expected 2")
    print("OK: 1 decision node with exactly 2 outgoing edges")


def check_vip_branch() -> None:
    flow = _read_flow()
    vip, _ = _branch_counts(flow)
    if vip["slack_send"] < 2:
        _fail(
            f"VIP branch has {vip['slack_send']} Slack send-message nodes, expected >=2"
        )
    if vip["outlook_action"] < 1:
        _fail(
            f"VIP branch has {vip['outlook_action']} Outlook action nodes, expected >=1"
        )
    print(
        f"OK: VIP branch has {vip['slack_send']} Slack + {vip['outlook_action']} Outlook nodes"
    )


def check_standard_branch() -> None:
    flow = _read_flow()
    _, std = _branch_counts(flow)
    if std["script"] < 1:
        _fail(
            f"standard branch has {std['script']} script nodes, expected >=1 (ticket generator)"
        )
    if std["outlook_action"] < 1:
        _fail(
            f"standard branch has {std['outlook_action']} Outlook action nodes, expected >=1"
        )
    print(
        f"OK: standard branch has {std['script']} script + {std['outlook_action']} Outlook nodes"
    )


DISPATCH = {
    "check_trigger": check_trigger,
    "check_pre_decision": check_pre_decision,
    "check_decision_fanout": check_decision_fanout,
    "check_vip_branch": check_vip_branch,
    "check_standard_branch": check_standard_branch,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.exit(f"usage: {sys.argv[0]} {{{'|'.join(DISPATCH)}}}")
    DISPATCH[sys.argv[1]]()


if __name__ == "__main__":
    main()
