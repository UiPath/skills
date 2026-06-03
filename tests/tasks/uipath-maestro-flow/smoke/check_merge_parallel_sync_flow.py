#!/usr/bin/env python3
"""ParallelSync: structural check for the parallel-sync merge topology.

Validate-only — does NOT run `uip maestro flow debug` (a `bpmn:ParallelGateway`
join only synchronizes inside a live BPMN engine the test sandbox cannot
provision). Asserts a fork/join parallel-sync built around a `core.logic.merge`
node:

  1. Exactly one node with `type == "core.logic.merge"` (the join), with a
     non-empty `typeVersion` (the agent-under-test copies the registry
     `version`, so we do NOT pin a specific value).
  2. The merge *definition* is present in `definitions[]` with
     `model.type == "bpmn:ParallelGateway"`.
  3. Two parallel branches CONVERGE on the merge: at least 2 incoming edges
     (`targetNodeId == merge id`) originating from at least 2 DISTINCT source
     nodes (so it is a real fan-in, not two edges from one node).
  4. The sync CONTINUES: the merge has at least one outgoing edge
     (`sourceNodeId == merge id`).
  5. A FORK exists upstream: some node has at least 2 outgoing edges — the
     parallel split the branches diverge from.
  6. The converging branches are genuine branches, not orphans: each distinct
     source node that feeds the merge itself has an incoming edge.
"""

import glob
import json
import sys
from collections import Counter
from typing import NoReturn

NODE_TYPE = "core.logic.merge"


def _fail(msg: str) -> NoReturn:
    sys.exit(f"FAIL: {msg}")


def _read_flow() -> dict:
    flows = glob.glob("**/ParallelSync*.flow", recursive=True)
    if not flows:
        _fail("no ParallelSync*.flow found under cwd")
    with open(flows[0]) as f:
        return json.load(f)


def _find_merge(flow: dict) -> dict:
    matches = [n for n in flow.get("nodes", []) if n.get("type") == NODE_TYPE]
    if not matches:
        types = sorted({n.get("type") for n in flow.get("nodes", [])})
        _fail(f"no node with type {NODE_TYPE!r}; node types seen: {types}")
    if len(matches) > 1:
        _fail(f"expected exactly one {NODE_TYPE} node (the join), found {len(matches)}")
    node = matches[0]
    tv = node.get("typeVersion")
    if not isinstance(tv, str) or not tv.strip():
        _fail(
            "merge node typeVersion missing or empty — copy the `version` field "
            "from `uip maestro flow registry get core.logic.merge --output json`."
        )
    return node


def _check_definition(flow: dict) -> None:
    defs = [d for d in (flow.get("definitions") or []) if d.get("nodeType") == NODE_TYPE]
    if len(defs) != 1:
        types = sorted(d.get("nodeType") for d in (flow.get("definitions") or []))
        _fail(
            f"expected exactly one definitions[] entry with nodeType {NODE_TYPE!r}, "
            f"found {len(defs)}; definition nodeTypes: {types}. Append the object from "
            "`uip maestro flow registry get core.logic.merge --output json`."
        )
    model = defs[0].get("model") or {}
    if model.get("type") != "bpmn:ParallelGateway":
        _fail(
            f"merge definition model.type={model.get('type')!r}; must be "
            '"bpmn:ParallelGateway". Re-copy the definition from the registry.'
        )


def _check_convergence(flow: dict, merge_id: str) -> set:
    edges = flow.get("edges") or []
    incoming = [e for e in edges if e.get("targetNodeId") == merge_id]
    sources = {e.get("sourceNodeId") for e in incoming if e.get("sourceNodeId")}
    if len(incoming) < 2:
        _fail(
            f"merge {merge_id!r} has only {len(incoming)} incoming edge(s); a "
            "parallel-sync needs at least two branches converging on it."
        )
    if len(sources) < 2:
        _fail(
            f"merge {merge_id!r} has {len(incoming)} incoming edge(s) but only "
            f"{len(sources)} distinct source node(s) ({sorted(sources)}); the two "
            "parallel branches must come from two DIFFERENT upstream nodes."
        )
    return sources


def _check_continuation(flow: dict, merge_id: str) -> None:
    outgoing = [e for e in (flow.get("edges") or []) if e.get("sourceNodeId") == merge_id]
    if not outgoing:
        _fail(
            f"merge {merge_id!r} has no outgoing edge; the synchronized branch must "
            "continue to a downstream node (e.g. the End node)."
        )


def _check_fork(flow: dict) -> None:
    out_counts = Counter(
        e.get("sourceNodeId") for e in (flow.get("edges") or []) if e.get("sourceNodeId")
    )
    forks = [nid for nid, c in out_counts.items() if c >= 2]
    if not forks:
        _fail(
            "no fork found: no node has 2+ outgoing edges. A parallel-sync must "
            "diverge into branches from a single upstream node before converging."
        )


def _check_branches_wired(flow: dict, sources: set) -> None:
    edges = flow.get("edges") or []
    targets_with_incoming = {e.get("targetNodeId") for e in edges}
    orphans = [s for s in sources if s not in targets_with_incoming]
    if orphans:
        _fail(
            f"branch node(s) {sorted(orphans)} feed the merge but have no incoming "
            "edge — each parallel branch must itself be reached from the fork."
        )


def main():
    flow = _read_flow()
    merge = _find_merge(flow)
    merge_id = merge.get("id")

    _check_definition(flow)
    sources = _check_convergence(flow, merge_id)
    _check_continuation(flow, merge_id)
    _check_fork(flow)
    _check_branches_wired(flow, sources)

    print(
        f"OK: exactly one {NODE_TYPE} ({merge_id!r}); {len(sources)} distinct branches "
        f"converge on it ({sorted(sources)}); fork present; merge continues downstream; "
        "definition carries bpmn:ParallelGateway"
    )


if __name__ == "__main__":
    main()
