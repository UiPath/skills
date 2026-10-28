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

`--aspect layout` checks the canvas against what merge may do to make room
for an added node, as postconditions:
1. Only position and size change; nodes move right or down; nothing shrinks.
2. A container grows only when a child was added or moved, and no further than
   its children plus merge's body padding; an added or moved child fits inside.
3. A node moves only when something took its spot or it follows a node that
   moved or was added there, along an original edge or the edge an insert
   split; and by no more than its container's added nodes' width plus a gap
   each, one gap more, and its grown containers' growth.
4. Nothing lands on another node; sticky notes are free to sit anywhere.
5. Nodes keep their order in a row, and edges keep pointing right (a retry
   edge back to an earlier node is exempt).
6. An added node sits right of its leftmost predecessor and within two rows
   of the nearest one.

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
STICKY_NOTE_TYPE = "stickyNote"
# builder-sdk typescript/sdk/src/node-placement.ts (UiPath/builder-sdk#1501): the gap
# between two nodes in a row, the padding its overlap test adds, and a container body's.
GAP = 96
PADDING = 24
BODY_PADDING = {"x": 144, "y": 96}


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


def boxes_overlap(a: dict, b: dict, padding: int = 0) -> bool:
    ap, asz = a.get("position", {}), a.get("size", DEFAULT_SIZE)
    bp, bsz = b.get("position", {}), b.get("size", DEFAULT_SIZE)
    ax, ay, bx, by = ap.get("x", 0), ap.get("y", 0), bp.get("x", 0), bp.get("y", 0)
    return (
        ax < bx + bsz.get("width", 96) + padding
        and bx < ax + asz.get("width", 96) + padding
        and ay < by + bsz.get("height", 96) + padding
        and by < ay + asz.get("height", 96) + padding
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


def ends(edge: dict) -> tuple[str | None, str | None]:
    return edge.get("sourceNodeId"), edge.get("targetNodeId")


def downstream(source: str, edges: list[dict], parent_of: dict[str, str | None]) -> set[str]:
    """Nodes an edge path from `source` reaches without leaving its container."""
    reached: set[str] = set()
    frontier = {source}
    while frontier:
        frontier = {
            v for u, v in map(ends, edges)
            if u in frontier and parent_of.get(v) == parent_of.get(source) and v not in reached | {source}
        }
        reached |= frontier
    return reached


def is_back_edge(edge: dict, edges: list[dict], parent_of: dict[str, str | None], after: dict) -> bool:
    """An edge that closes a cycle by pointing left, as a retry `.stepToRef` does."""
    u, v = ends(edge)
    return box(after[v])[0] <= box(after[u])[0] and (u == v or u in downstream(v, edges, parent_of))


def entry_changes(changed: set[str], before: dict, after: dict, failures: list[str]) -> set[str]:
    """Invariant 1. Returns the nodes whose size grew."""
    grown: set[str] = set()
    for node_id in sorted(changed):
        rewritten = [k for k in differing_keys(before[node_id], after[node_id]) if k not in ("position", "size")]
        if rewritten:
            failures.append(f"{node_id!r} layout entry changed: {rewritten}")

        dx, dy = offset(before[node_id], after[node_id])
        if dx < 0 or dy < 0:
            failures.append(f"{node_id!r} moved left or up: {before[node_id].get('position')} -> {after[node_id].get('position')}")

        _, _, ow, oh = box(before[node_id])
        _, _, nw, nh = box(after[node_id])
        if nw < ow or nh < oh:
            failures.append(f"{node_id!r} shrank from {ow}x{oh} to {nw}x{nh}")
        elif (nw, nh) != (ow, oh):
            grown.add(node_id)
    return grown


def container_growth(
    grown: set[str], touched: set[str], solid: list[str], before: dict, after: dict, parent_of: dict[str, str | None]
) -> list[str]:
    """Invariant 2."""
    failures: list[str] = []
    for c in sorted(grown):
        if c not in touched:
            failures.append(f"{c!r} resized though no child of it was added or moved")
            continue

        body = [box(after[i]) for i in solid if parent_of.get(i) == c]
        _, _, ow, oh = box(before[c])
        _, _, nw, nh = box(after[c])
        fit_w = max(x + w for x, _, w, _ in body) + BODY_PADDING["x"]
        fit_h = max(y + h for _, y, _, h in body) + BODY_PADDING["y"]
        if nw > max(ow, fit_w) or nh > max(oh, fit_h):
            failures.append(f"container {c!r} grew to {nw}x{nh}, past its body's {fit_w}x{fit_h}")
    return failures


def moves_without_room(
    changed: set[str], added: set[str], grown: set[str], before: dict, after: dict, parent_of: dict[str, str | None]
) -> list[str]:
    """Invariant 3."""
    failures: list[str] = []
    for node_id in sorted(changed):
        dx, dy = offset(before[node_id], after[node_id])
        if (dx, dy) == (0, 0):
            continue

        scope = parent_of.get(node_id)
        runs = [box(after[a])[2] + GAP for a in added if parent_of.get(a) == scope and a in after]
        growth = [(box(after[c])[2] - box(before[c])[2], box(after[c])[3] - box(before[c])[3]) for c in grown if parent_of.get(c) == scope and c != node_id]
        room_x = (sum(runs) + GAP if runs else 0) + sum(w for w, _ in growth)
        room_y = sum(h for _, h in growth)
        if dx > room_x or dy > room_y:
            failures.append(
                f"{node_id!r} moved: {before[node_id].get('position')} -> {after[node_id].get('position')}, "
                f"but its container's added nodes and growth make at most {room_x} right and {room_y} down of room"
            )
    return failures


def moves_without_cause(
    changed: set[str],
    added: set[str],
    grown: set[str],
    original_edges: list[dict],
    edges: list[dict],
    before: dict,
    after: dict,
    parent_of: dict[str, str | None],
) -> list[str]:
    """Invariant 3's cause: what merge placed, or a grown container pushed, takes a spot and drags what follows it."""
    kept = {edge_key(e) for e in edges}
    split = {edge_key(e)[2] for e in original_edges if edge_key(e) not in kept}
    pairs = {ends(e) for e in original_edges}
    follows = [(u, v) for u, v in map(ends, edges) if (u, v) in pairs or (u in added and v in split)]
    moved = {i for i in changed if offset(before[i], after[i]) != (0, 0)}

    def pushed_by_growth(a: str) -> bool:
        for c in grown:
            if parent_of.get(c) != parent_of.get(a):
                continue
            dw, dh = box(after[c])[2] - box(before[c])[2], box(after[c])[3] - box(before[c])[3]
            x, y, w, h = box(after[a])
            if any(boxes_overlap(after[c], {"position": {"x": x - sx, "y": y - sy}, "size": {"width": w, "height": h}}, PADDING) for sx, sy in ((dw, 0), (0, dh))):
                return True
        return False

    placed = {a for a in added if a in after and (any(v == a for _, v in map(ends, edges)) or pushed_by_growth(a))}
    causes, frontier = set(), placed | grown
    while frontier:
        causes |= frontier
        frontier = {
            x for x in moved - causes
            if any(parent_of.get(c) == parent_of.get(x) and boxes_overlap(after[c], before[x], PADDING) for c in causes if c != x)
            or any(u in causes and v == x for u, v in follows)
        }
    return [f"{x!r} moved: {before[x].get('position')} -> {after[x].get('position')}, but nothing took its spot or pushed what it follows" for x in sorted(moved - causes)]


def new_overlaps(solid: list[str], changed: set[str], added: set[str], before: dict, after: dict, parent_of: dict[str, str | None]) -> list[str]:
    """Invariant 4."""
    failures: list[str] = []
    for i, a in enumerate(solid):
        for b in solid[i + 1:]:
            if parent_of.get(a) != parent_of.get(b) or not ({a, b} & (changed | added)):
                continue
            # An added node's spot may be its author's, so only a real overlap counts for it.
            if not boxes_overlap(after[a], after[b], 0 if {a, b} & added else PADDING):
                continue
            if a in before and b in before and boxes_overlap(before[a], before[b], PADDING):
                continue
            failures.append(f"{a!r} and {b!r} now overlap on the canvas")
    return failures


def order_changes(solid: list[str], edges: list[dict], before: dict, after: dict, parent_of: dict[str, str | None]) -> list[str]:
    """Invariant 5."""
    failures: list[str] = []
    kept = [i for i in solid if i in before]
    for i, a in enumerate(kept):
        for b in kept[i + 1:]:
            if parent_of.get(a) != parent_of.get(b) or not shares_row(before[a], before[b]):
                continue
            was, now = box(before[a])[0] - box(before[b])[0], box(after[a])[0] - box(after[b])[0]
            if (was > 0) - (was < 0) != (now > 0) - (now < 0):
                failures.append(f"{a!r} and {b!r} changed order in their row")

    on_canvas = set(solid)
    for e in edges:
        u, v = ends(e)
        if u not in on_canvas or v not in on_canvas or parent_of.get(u) != parent_of.get(v):
            continue
        if box(after[u])[0] < box(after[v])[0] or is_back_edge(e, edges, parent_of, after):
            continue
        was_right = u in before and v in before and box(before[u])[0] < box(before[v])[0]
        if was_right or ((u not in before or v not in before) and shares_row(after[u], after[v])):
            failures.append(f"edge {u!r} -> {v!r} now points left")
    return failures


def added_placement(
    added: set[str], solid: list[str], edges: list[dict], before: dict, after: dict, parent_of: dict[str, str | None]
) -> list[str]:
    """Invariant 6, and invariant 2's child fits inside."""
    failures: list[str] = []
    on_canvas = set(solid)
    for a in sorted(added):
        if a not in after:
            failures.append(f"new node {a!r} has no layout entry")
            continue
        if a not in on_canvas:
            continue

        preds = [u for u, v in map(ends, edges) if v == a and u in on_canvas and parent_of.get(u) == parent_of.get(a)]
        if not preds:
            continue
        x, y, _, h = box(after[a])
        if x <= min(box(after[u])[0] for u in preds):
            failures.append(f"new node {a!r} sits left of every node that leads to it ({', '.join(sorted(preds))})")
        if min(abs(y - box(after[u])[1]) for u in preds) > 2 * (h + GAP):
            failures.append(f"new node {a!r} at {after[a].get('position')} is more than two rows from every node that leads to it")

    for i in solid:
        parent = parent_of.get(i)
        if parent is None or parent not in after or (i in before and before[i] == after[i]):
            continue
        x, y, w, h = box(after[i])
        _, _, pw, ph = box(after[parent])
        if x < 0 or y < 0 or x + w > pw or y + h > ph:
            failures.append(f"{i!r} at {after[i].get('position')} is outside its container {parent!r} ({pw}x{ph})")
    return failures


def check_layout(original: dict, final: dict, removable_nodes: set[str] = frozenset()) -> list[str]:
    failures: list[str] = []
    before = original.get("layout", {}).get("nodes", {})
    after = final.get("layout", {}).get("nodes", {})
    original_ids = {n["id"] for n in original.get("nodes", [])}
    final_ids = {n["id"] for n in final.get("nodes", [])}
    parent_of = {n["id"]: n.get("parentId") for n in final.get("nodes", [])}
    sticky = {n["id"] for n in final.get("nodes", []) if n.get("type") == STICKY_NOTE_TYPE}
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
    solid = [i for i in kept if i not in sticky] + sorted(i for i in added if i not in sticky and i in after)

    grown = entry_changes(changed, before, after, failures)
    failures += container_growth(grown, touched, solid, before, after, parent_of)
    failures += moves_without_room(changed, added, grown, before, after, parent_of)
    failures += moves_without_cause(changed, added, grown, original.get("edges", []), edges, before, after, parent_of)
    failures += new_overlaps(solid, changed, added, before, after, parent_of)
    failures += order_changes(solid, edges, before, after, parent_of)
    failures += added_placement(added, solid, edges, before, after, parent_of)
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
