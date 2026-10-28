#!/usr/bin/env python3
"""A brownfield edit changed only what the task asked for.

Compares the Flow project the agent left behind with the committed fixture it
started from. Every original node, edge, binding, variable and definition must
survive, and every definition and every node the task did not name must be
byte-for-byte the same JSON (the bar builder-sdk's own round-trip corpus test
uses). Agent sidecars
(`<uuid>/agent.json` and their `resources/*/resource.json`) count as part of the
flow: a context index that loses its id still validates, so only a comparison
with the original catches it.

`--aspect layout` checks the canvas instead: a node the edit added has a layout
entry that overlaps no other node in its container, and original nodes keep
their position and size except where merge made room. Merge may move an
original node right or down when it is downstream of an added node or a grown
container in the same container, or a grown sibling container covers it; a
container may grow when a child was added or moved. A moved node keeps its
place in its row, moves at least as far as its predecessor, and lands on no
other node. An added node sits inside its container and, on a row it shares
with a neighbour it is wired to, on the side the edge points. An edge that
closes a cycle by pointing left (a retry) is exempt from direction and reach.

`--aspect merged` checks that the `.flow` came out of the skill's decompile ->
compile -> merge loop, not a hand edit.

`--removable-node` names an original node the edit may change or delete, with
its edges, node variables and layout entry; the task's own grader checks
whether it had to go.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_brownfield_preserved.py \\
        --original $REFERENCE_DIR/<fixture>/<Sol>/<Project> --project <Sol>/<Project> \\
        [--changed-node ID ...] [--removable-node ID ...] [--removed-edge SRC:PORT>TGT:PORT ...] \\
        [--changed-agent UUID ...] [--aspect graph|layout|merged]

Exit 0 on pass; exit 1 with one `FAIL:` line per difference.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

DEFAULT_SIZE = {"width": 96, "height": 96}


def load_project(project_dir: Path) -> tuple[dict, dict[str, dict]]:
    flow_path = project_dir / f"{project_dir.name}.flow"
    if not flow_path.is_file():
        raise SystemExit(f"FAIL: {flow_path} not found")
    flow = json.loads(flow_path.read_text(encoding="utf-8"))
    agents: dict[str, dict] = {}
    for agent_json in sorted(project_dir.glob("*/agent.json")):
        agent_dir = agent_json.parent
        resources = {
            p.parent.name: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(agent_dir.glob("resources/*/resource.json"))
        }
        agents[agent_dir.name] = {
            "agent": json.loads(agent_json.read_text(encoding="utf-8")),
            "resources": resources,
        }
    return flow, agents


def edge_key(edge: dict) -> tuple[str, str, str, str]:
    return (
        edge.get("sourceNodeId", ""),
        edge.get("sourcePort", ""),
        edge.get("targetNodeId", ""),
        edge.get("targetPort", ""),
    )


def parse_edge(spec: str) -> tuple[str, str, str, str]:
    source, target = spec.split(">", 1)
    source_node, source_port = source.split(":", 1)
    target_node, target_port = target.split(":", 1)
    return (source_node, source_port, target_node, target_port)


def subflow_parts(flow: dict, key: str) -> list[dict]:
    parts = list(flow.get(key, []))
    for subflow in (flow.get("subflows") or {}).values():
        if isinstance(subflow, dict):
            parts += subflow.get(key, [])
    return parts


def binding_signature(binding: dict) -> str:
    return json.dumps({k: v for k, v in binding.items() if k != "id"}, sort_keys=True)


def differing_keys(before: dict, after: dict) -> list[str]:
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


def check_graph(
    original: dict,
    final: dict,
    original_agents: dict[str, dict],
    final_agents: dict[str, dict],
    changed_nodes: set[str],
    removed_edges: set[tuple[str, str, str, str]],
    changed_agents: set[str],
    removable_nodes: set[str] = frozenset(),
) -> list[str]:
    failures: list[str] = []

    for key in ("id", "name", "version", "runtime"):
        if original.get(key) != final.get(key):
            failures.append(f"top-level {key!r} changed: {original.get(key)!r} -> {final.get(key)!r}")

    final_nodes = {n["id"]: n for n in final.get("nodes", [])}
    for node in original.get("nodes", []):
        after = final_nodes.get(node["id"])
        if after is None:
            if node["id"] not in removable_nodes:
                failures.append(f"node {node['id']!r} was removed")
        elif node["id"] not in changed_nodes | removable_nodes and after != node:
            failures.append(f"node {node['id']!r} changed ({', '.join(differing_keys(node, after))})")

    original_ids = set(final_nodes) & {n["id"] for n in original.get("nodes", [])}
    gone = {n["id"] for n in original.get("nodes", [])} - original_ids
    untouched = original_ids - changed_nodes - removable_nodes
    final_edges = Counter(edge_key(e) for e in final.get("edges", []))
    original_edges = {edge_key(e) for e in original.get("edges", [])}
    for edge in sorted(original_edges - removed_edges):
        if not final_edges[edge] and edge[0] not in gone and edge[2] not in gone:
            failures.append("edge removed: {}:{} -> {}:{}".format(*edge))
    for edge in sorted(removed_edges):
        if final_edges[edge]:
            failures.append("edge the edit should replace is still there: {}:{} -> {}:{}".format(*edge))
    for edge, count in sorted(final_edges.items()):
        if count > 1:
            failures.append("edge written {}x: {}:{} -> {}:{}".format(count, *edge))
        elif edge not in original_edges and edge[0] in untouched and edge[2] in untouched:
            failures.append("edge added between untouched nodes: {}:{} -> {}:{}".format(*edge))

    original_bindings = Counter(binding_signature(b) for b in original.get("bindings", []))
    final_bindings = Counter(binding_signature(b) for b in final.get("bindings", []))
    for signature, count in original_bindings.items():
        name = json.loads(signature).get("name")
        if final_bindings[signature] < count:
            failures.append(f"binding removed or altered: {name!r}")
        elif final_bindings[signature] > count:
            failures.append(f"binding duplicated: {name!r}")
    for signature in final_bindings.keys() - original_bindings.keys():
        failures.append(f"binding added: {json.loads(signature).get('name')!r}")

    variables, final_variables = original.get("variables", {}), final.get("variables", {})
    final_globals = {v["id"]: v for v in final_variables.get("globals", [])}
    for var in variables.get("globals", []):
        if final_globals.get(var["id"]) != var:
            failures.append(f"flow variable {var['id']!r} removed or changed")
    final_node_vars = {v["id"]: v for v in final_variables.get("nodes", [])}
    for var in variables.get("nodes", []):
        owner = var.get("binding", {}).get("nodeId")
        if owner in changed_nodes or owner in removable_nodes:
            continue
        if final_node_vars.get(var["id"]) != var:
            failures.append(f"node variable {var['id']!r} removed or changed")

    final_definitions = {(d.get("nodeType"), d.get("version")): d for d in final.get("definitions", [])}
    used_types = {n.get("type") for n in subflow_parts(final, "nodes")}
    for definition in original.get("definitions", []):
        key = (definition.get("nodeType"), definition.get("version"))
        after = final_definitions.get(key)
        if after is None:
            if key[0] in used_types:
                failures.append(f"definition {key[0]}@{key[1]} removed")
        elif after != definition:
            failures.append(f"definition {key[0]}@{key[1]} changed ({', '.join(differing_keys(definition, after))})")

    for uuid, sidecar in original_agents.items():
        after = final_agents.get(uuid)
        if after is None:
            failures.append(f"agent project {uuid} was removed")
            continue
        if uuid not in changed_agents and after["agent"] != sidecar["agent"]:
            keys = differing_keys(sidecar["agent"], after["agent"])
            failures.append(f"agent {uuid} agent.json changed ({', '.join(keys)})")
        for resource_dir, resource in sidecar["resources"].items():
            if after["resources"].get(resource_dir) != resource:
                failures.append(f"agent {uuid} resource {resource_dir} removed or changed")

    return failures


def boxes_overlap(a: dict, b: dict) -> bool:
    ap, asz = a.get("position", {}), a.get("size", DEFAULT_SIZE)
    bp, bsz = b.get("position", {}), b.get("size", DEFAULT_SIZE)
    ax, ay, bx, by = ap.get("x", 0), ap.get("y", 0), bp.get("x", 0), bp.get("y", 0)
    return (
        ax < bx + bsz.get("width", 96)
        and bx < ax + asz.get("width", 96)
        and ay < by + bsz.get("height", 96)
        and by < ay + asz.get("height", 96)
    )


def box(entry: dict) -> tuple[int, int, int, int]:
    p, size = entry.get("position", {}), entry.get("size", DEFAULT_SIZE)
    return p.get("x", 0), p.get("y", 0), size.get("width", 96), size.get("height", 96)


def shares_row(a: dict, b: dict) -> bool:
    _, ay, _, ah = box(a)
    _, by, _, bh = box(b)
    return ay < by + bh and by < ay + ah


def offset(before: dict, after: dict) -> tuple[int, int]:
    bx, by, _, _ = box(before)
    ax, ay, _, _ = box(after)
    return ax - bx, ay - by


def downstream(source: str, edges: list[dict], parent_of: dict[str, str | None]) -> set[str]:
    """Nodes an edge path from `source` reaches without leaving its container."""
    reached: set[str] = set()
    frontier = {source}
    while frontier:
        frontier = {
            e.get("targetNodeId") for e in edges
            if e.get("sourceNodeId") in frontier
            and parent_of.get(e.get("targetNodeId")) == parent_of.get(source)
            and e.get("targetNodeId") not in reached | {source}
        }
        reached |= frontier
    return reached


def back_edges(edges: list[dict], parent_of: dict[str, str | None], after: dict) -> list[dict]:
    """Edges that close a cycle in their container by pointing left, as a retry `.stepToRef` does."""
    back = []
    for e in edges:
        u, v = e.get("sourceNodeId"), e.get("targetNodeId")
        if u not in after or v not in after or parent_of.get(u) != parent_of.get(v):
            continue
        if box(after[v])[0] <= box(after[u])[0] and (u == v or u in downstream(v, edges, parent_of)):
            back.append(e)
    return back


def grown_containers(changed: set[str], touched: set[str], before: dict, after: dict, failures: list[str]) -> set[str]:
    grown: set[str] = set()
    for node_id in sorted(changed):
        _, _, ow, oh = box(before[node_id])
        _, _, nw, nh = box(after[node_id])
        if (ow, oh) == (nw, nh):
            continue
        if node_id not in touched:
            failures.append(f"{node_id!r} resized from {ow}x{oh} to {nw}x{nh} though no child of it was added or moved")
        elif nw < ow or nh < oh:
            failures.append(f"container {node_id!r} shrank from {ow}x{oh} to {nw}x{nh}")
        else:
            grown.add(node_id)
    return grown


def moves_without_room(
    changed: set[str], room: set[str], grown: set[str], before: dict, after: dict, parent_of: dict[str, str | None]
) -> list[str]:
    failures: list[str] = []
    for node_id in sorted(changed):
        rewritten = [k for k in differing_keys(before[node_id], after[node_id]) if k not in ("position", "size")]
        if rewritten:
            failures.append(f"{node_id!r} layout entry changed: {rewritten}")
            continue

        dx, dy = offset(before[node_id], after[node_id])
        if (dx, dy) == (0, 0):
            continue

        covered = any(
            c != node_id and parent_of.get(c) == parent_of.get(node_id) and boxes_overlap(after[c], before[node_id])
            for c in grown
        )
        if dx < 0 or dy < 0 or not (node_id in room or covered):
            failures.append(f"{node_id!r} moved: {before[node_id].get('position')} -> {after[node_id].get('position')}")
    return failures


def order_changes(
    kept: list[str],
    added: set[str],
    changed: set[str],
    edges: list[dict],
    before: dict,
    after: dict,
    parent_of: dict[str, str | None],
) -> list[str]:
    failures: list[str] = []
    for i, a in enumerate(kept):
        for b in kept[i + 1:]:
            if parent_of.get(a) != parent_of.get(b) or not shares_row(before[a], before[b]):
                continue
            was, now = box(before[a])[0] - box(before[b])[0], box(after[a])[0] - box(after[b])[0]
            if (was > 0) - (was < 0) != (now > 0) - (now < 0):
                failures.append(f"{a!r} and {b!r} changed order in their row")

    for e in edges:
        u, v = e.get("sourceNodeId"), e.get("targetNodeId")
        if (u in added) == (v in added) or u not in after or v not in after or parent_of.get(u) != parent_of.get(v):
            continue
        if shares_row(after[u], after[v]) and box(after[u])[0] >= box(after[v])[0]:
            failures.append(f"{v!r} sits left of {u!r} in their row, against the edge between them")

    for e in edges:
        u, v = e.get("sourceNodeId"), e.get("targetNodeId")
        if u not in changed or v not in kept or parent_of.get(u) != parent_of.get(v):
            continue
        if box(before[v])[0] > box(before[u])[0] and offset(before[v], after[v])[0] < offset(before[u], after[u])[0]:
            failures.append(f"{v!r} moved less than its predecessor {u!r}")
    return failures


def overlaps_after_edit(
    added: set[str], changed: set[str], kept: list[str], before: dict, after: dict, parent_of: dict[str, str | None]
) -> list[str]:
    failures: list[str] = []
    for node_id in sorted(added):
        if node_id not in after:
            failures.append(f"new node {node_id!r} has no layout entry")
            continue

        parent = parent_of.get(node_id)
        if parent is not None and parent in after:
            x, y, w, h = box(after[node_id])
            _, _, pw, ph = box(after[parent])
            if x < 0 or y < 0 or x + w > pw or y + h > ph:
                failures.append(f"new node {node_id!r} at {after[node_id].get('position')} is outside its container {parent!r} ({pw}x{ph})")

        for other_id, other in after.items():
            if other_id != node_id and parent_of.get(other_id) == parent_of.get(node_id) and boxes_overlap(after[node_id], other):
                failures.append(f"new node {node_id!r} overlaps {other_id!r} on the canvas")

    for node_id in sorted(changed):
        for other_id in kept:
            if other_id == node_id or parent_of.get(other_id) != parent_of.get(node_id):
                continue
            if other_id in changed and other_id < node_id:
                continue
            if boxes_overlap(after[node_id], after[other_id]) and not boxes_overlap(before[node_id], before[other_id]):
                failures.append(f"moved node {node_id!r} now overlaps {other_id!r} on the canvas")
    return failures


def check_layout(original: dict, final: dict, removable_nodes: set[str] = frozenset()) -> list[str]:
    failures: list[str] = []
    before = original.get("layout", {}).get("nodes", {})
    after = final.get("layout", {}).get("nodes", {})
    original_ids = {n["id"] for n in original.get("nodes", [])}
    final_ids = {n["id"] for n in final.get("nodes", [])}
    parent_of = {n["id"]: n.get("parentId") for n in final.get("nodes", [])}
    added = final_ids - original_ids

    edges = []
    for i, e in enumerate(final.get("edges", [])):
        if not (isinstance(e, dict) and e.get("sourceNodeId") and e.get("targetNodeId")):
            failures.append(f"edge {i} ({e.get('id') if isinstance(e, dict) else e!r}) has no sourceNodeId or targetNodeId")
            continue
        edges.append(e)

    kept: list[str] = []
    for node_id in sorted(original_ids):
        if node_id not in before or (node_id in removable_nodes and node_id not in final_ids):
            continue
        if node_id not in after:
            failures.append(f"layout entry for {node_id!r} removed")
            continue
        kept.append(node_id)

    changed = {i for i in kept if after[i] != before[i]}
    touched = {parent_of[i] for i in added | changed if parent_of.get(i) is not None}
    grown = grown_containers(changed, touched, before, after, failures)
    back = back_edges(edges, parent_of, after)
    edges = [e for e in edges if not any(e is b for b in back)]
    room = set().union(*(downstream(i, edges, parent_of) for i in added | grown))

    failures += moves_without_room(changed, room, grown, before, after, parent_of)
    failures += order_changes(kept, added, changed, edges, before, after, parent_of)
    failures += overlaps_after_edit(added, changed, kept, before, after, parent_of)
    return failures


def check_merged(original: dict, final: dict) -> list[str]:
    # merge takes every edge from the compiled source, which numbers them edge_0..edge_N
    # (builder-sdk FLOW_PARITY.md §6.2), so a surviving original edge id means a hand edit.
    # A tripwire, not proof (a hand edit can renumber too), and it inverts if merge ever keeps
    # original edge ids the way compile now keeps node ids (builder-sdk #1249, #1253).
    original_ids = {e["id"] for e in subflow_parts(original, "edges")}
    kept = sorted(original_ids & {e.get("id") for e in subflow_parts(final, "edges")})
    if not kept:
        return []
    return [
        f"{len(kept)} of {len(original_ids)} original edge ids survive (e.g. {kept[0]!r}): the .flow was "
        "edited by hand, not written by `uip maestro flow merge`, which renumbers every edge. When the "
        "merge candidate changes something the task did not ask for, the skill's answer is to fix the "
        ".flow.ts and merge again, not to patch the .flow (uipath-maestro-flow references/brownfield.md, "
        "'Merge warnings: what the round trip changed')"
    ]


OK_MESSAGES = {
    "graph": "OK: graph preserved outside the requested change",
    "layout": "OK: layout preserved outside the requested change",
    "merged": "OK: the .flow was written by `uip maestro flow merge` (no original edge id survives)",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--changed-node", action="append", default=[])
    parser.add_argument("--removable-node", action="append", default=[])
    parser.add_argument("--removed-edge", action="append", default=[])
    parser.add_argument("--changed-agent", action="append", default=[])
    parser.add_argument("--aspect", choices=("graph", "layout", "merged"), default="graph")
    args = parser.parse_args(argv)

    original, original_agents = load_project(args.original)
    final, final_agents = load_project(args.project)

    if args.aspect == "layout":
        failures = check_layout(original, final, set(args.removable_node))
    elif args.aspect == "merged":
        failures = check_merged(original, final)
    else:
        failures = check_graph(
            original,
            final,
            original_agents,
            final_agents,
            set(args.changed_node),
            {parse_edge(e) for e in args.removed_edge},
            set(args.changed_agent),
            set(args.removable_node),
        )

    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        return 1
    print(OK_MESSAGES[args.aspect])
    return 0


if __name__ == "__main__":
    sys.exit(main())
