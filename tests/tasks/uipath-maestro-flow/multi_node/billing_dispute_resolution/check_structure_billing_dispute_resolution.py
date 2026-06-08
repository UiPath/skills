#!/usr/bin/env python3
"""Structural check for the full DevCon BillingDisputeResolution flow.

No execution — pure shape asserts on the agent-built `.flow`. Confirms the flow
reproduces the full orchestration AND honors the two edits this task pins:

  Required nodes (anti-hardcode — each targets a tenant resource a Script node
  cannot fake):
    - IxP extraction              (uipath.ixp.*)                 invoice parsing
    - Data Service query          (…dataservice.query-entity-records)  ERP/CRM lookup
    - inline autonomous agent     (uipath.agent.autonomous)      analyst + writer
    - context index               (uipath.agent.resource.context.index.*)  SOP grounding
    - API-workflow function       (uipath.core.api-workflow.*)   financial posting
    - switch + decision           (core.logic.switch / .decision) routing
    - end                         (core.control.end)             RETURNS the outcome

  Edits this task requires (the reason it differs from the raw DevCon flow):
    - NO human-in-the-loop node  — the HITL approval gate was removed.
    - NO send-email node         — the flow must NOT email; it RETURNS instead.
    - declares `out` variables   — the resolution is returned to the caller.
"""
import glob
import json
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    find_project_dir,
)


def _flow_nodes():
    project_dir = find_project_dir()
    nodes = []
    for path in glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True):
        with open(path) as f:
            nodes.extend(json.load(f).get("nodes") or [])
    return nodes


def _out_var_ids():
    project_dir = find_project_dir()
    out = []
    for path in glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True):
        with open(path) as f:
            flow = json.load(f)
        variables = flow.get("variables") or {}
        for v in variables.get("globals") or []:
            if v.get("direction") == "out":
                out.append(v["id"])
    return out


def _assert_absent(nodes, substr, why):
    hits = [n.get("type", "") for n in nodes if substr.lower() in str(n.get("type", "")).lower()]
    if hits:
        sys.exit(f"FAIL: {why} — found node type(s) {sorted(set(hits))} matching {substr!r}")


def main():
    # Positive: the full orchestration is present. Each hint targets a resource
    # node that a hardcoded Script cannot substitute for.
    assert_flow_has_node_type(["uipath.ixp"])
    assert_flow_has_node_type(["dataservice.query-entity-records"])
    assert_flow_has_node_type(["uipath.agent.autonomous"])
    assert_flow_has_node_type(["uipath.agent.resource.context.index"])
    assert_flow_has_node_type(["uipath.core.api-workflow"])
    assert_flow_has_node_type(["core.logic.switch"])
    assert_flow_has_node_type(["core.logic.decision"])
    assert_flow_has_node_type(["core.control.end"])
    print("OK: full orchestration present (IxP, Data Service, 2 inline agents, "
          "SOP context index, API-workflow, switch, decision, end)")

    nodes = _flow_nodes()

    # Edit 1 — HITL removed.
    _assert_absent(nodes, "human-in-the-loop", "HITL node must be removed")
    # Edit 2 — no terminal email; the flow returns instead of sending.
    _assert_absent(nodes, "send-email", "flow must NOT send email — return the outcome instead")
    print("OK: no human-in-the-loop node and no send-email node")

    # Edit 2 (cont.) — the outcome is RETURNED as flow output variables.
    out_vars = _out_var_ids()
    if not out_vars:
        sys.exit(
            "FAIL: flow declares no `out` variables — the resolution must be RETURNED "
            "to the caller (e.g. determination / rationale / resolution body), not emailed."
        )
    print(f"OK: flow returns its outcome via out variables {out_vars}")


if __name__ == "__main__":
    main()
