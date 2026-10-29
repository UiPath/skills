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
   each, one gap more, how far left of an added node the nodes it pushes sat,
   and its grown containers' growth plus a gap each.
4. Nothing lands on another node. Sticky notes may overlap anything, and move only with the original node they
   cover most.
5. Nodes keep their order in a row, and edges keep pointing right (a retry
   edge back to an earlier node is exempt).
6. An added node sits within two rows of a node it is wired to, or of an added
   branch beside it from the same node.

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
# GAP, PADDING and BODY_ORIGIN in builder-sdk typescript/sdk/src/node-placement.ts at
# 8a0fedc2 (UiPath/builder-sdk#1501); re-read them there when merge placement changes.
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


def shifted(entry: dict, dx: int, dy: int) -> dict:
    x, y, _, _ = box(entry)
    return {**entry, "position": {"x": x + dx, "y": y + dy}}


def rows_meet(a: dict, b: dict) -> bool:
    _, ay, _, ah = box(a)
    _, by, _, bh = box(b)
    return ay < by + bh + PADDING and by < ay + ah + PADDING


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


def retry_edges(
    original_edges: list[dict], edges: list[dict], before: dict, after: dict, parent_of: dict[str, str | None]
) -> set[tuple[str, str]]:
    """Final edges that may point left, as a retry `.stepToRef` does.

    An original back edge the edit kept, and a left-pointing edge that closes a cycle no kept back edge is on, such as
    the pieces of a split one or a retry the edit authored. A cycle through a kept back edge belongs to that edge: an
    insert elsewhere on it gets no pass.
    """
    back = {
        (u, v) for u, v in map(ends, original_edges)
        if u in before and v in before and box(before[v])[0] <= box(before[u])[0]
        and (u == v or u in downstream(v, original_edges, parent_of))
    }
    final = set(map(ends, edges))
    retries = back & final
    rest = [e for e in edges if ends(e) not in retries]
    for x, y in final - retries:
        if x in after and y in after and box(after[y])[0] <= box(after[x])[0] and (x == y or x in downstream(y, rest, parent_of)):
            retries.add((x, y))
    return retries


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
        if not body:
            failures.append(f"container {c!r} grew around a body with nothing on the canvas")
            continue

        _, _, ow, oh = box(before[c])
        _, _, nw, nh = box(after[c])
        fit_w = max(x + w for x, _, w, _ in body) + BODY_PADDING["x"]
        fit_h = max(y + h for _, y, _, h in body) + BODY_PADDING["y"]
        if nw > max(ow, fit_w) or nh > max(oh, fit_h):
            failures.append(f"container {c!r} grew to {nw}x{nh}, past its body's {fit_w}x{fit_h}")
    return failures


def run_sources(a: str, added: set[str], edges: list[dict], before: dict, parent_of: dict[str, str | None]) -> set[str]:
    """The original nodes the run of added nodes holding `a` starts from: where merge inserted it."""
    sources, seen, frontier = set(), {a}, {a}
    while frontier:
        preds = {u for u, v in map(ends, edges) if v in frontier and parent_of.get(u) == parent_of.get(a) and u not in seen}
        sources |= {u for u in preds if u in before}
        frontier = {u for u in preds if u in added}
        seen |= preds
    return sources


def pushed_from_left(
    added: set[str], kept: list[str], edges: list[dict], before: dict, after: dict, parent_of: dict[str, str | None]
) -> list[tuple[str, set[str], int]]:
    """Per added node, the nodes it pushes past the insertion, with how far left of it they sat.

    A node merge pushes has to clear the added one: an index tucked under its agent, or a lane
    node left of an insert that took the join's row, moves that much more than one slot.
    """
    found: list[tuple[str, set[str], int]] = []
    for a in sorted(added):
        if a not in after:
            continue

        scope = parent_of.get(a)
        sources = run_sources(a, added, edges, before, parent_of)
        anchor = min((box(before[u])[0] for u in sources), default=None)
        after_it = downstream(a, edges, parent_of) - sources
        pushed = {
            o for o in kept
            if parent_of.get(o) == scope and o not in sources and (anchor is None or box(before[o])[0] >= anchor)
            and (o in after_it or boxes_overlap(after[a], path(before[o], after[o]), PADDING))
        }
        in_row = [o for o in pushed if rows_meet(after[a], path(before[o], after[o]))]
        short = max((box(after[a])[0] - box(before[o])[0] for o in in_row), default=0)
        if short > 0:
            found.append((a, {a} | pushed, short))
    return found


def moves_without_room(
    changed: set[str],
    added: set[str],
    grown: set[str],
    tucked: list[tuple[str, set[str], int]],
    follows: list[tuple[str, str]],
    before: dict,
    after: dict,
    parent_of: dict[str, str | None],
) -> list[str]:
    """Invariant 3."""
    failures: list[str] = []
    moved = {i for i in changed if offset(before[i], after[i]) != (0, 0)}
    pushes = [(a, caused(seeds, moved, follows, before, after, parent_of), short) for a, seeds, short in tucked]
    for node_id in sorted(changed):
        dx, dy = offset(before[node_id], after[node_id])
        if (dx, dy) == (0, 0):
            continue

        scope = parent_of.get(node_id)
        runs = {a: box(after[a])[2] + GAP for a in added if parent_of.get(a) == scope and a in after}
        grew = [growth(c, before, after) for c in grown if parent_of.get(c) == scope and c != node_id]
        widening = sum(w + GAP for w, _ in grew if w)
        clear = max((short for _, pushed, short in pushes if node_id in pushed), default=0)
        room_x = (sum(runs.values()) + GAP + clear if runs else 0) + widening
        room_y = sum(h for _, h in grew)
        if dx > room_x or dy > room_y:
            failures.append(
                f"{node_id!r} moved: {before[node_id].get('position')} -> {after[node_id].get('position')}, "
                f"but its container's added nodes and growth make at most {room_x} right and {room_y} down of room"
            )
    return failures


def growth(c: str, before: dict, after: dict) -> tuple[int, int]:
    return box(after[c])[2] - box(before[c])[2], box(after[c])[3] - box(before[c])[3]


def followed_edges(
    original_edges: list[dict], edges: list[dict], added: set[str], retries: set[tuple[str, str]], parent_of: dict[str, str | None]
) -> list[tuple[str, str]]:
    """Final edges a push travels along: original ones, an added node's edge into the node an insert split off,
    and from a retry edge's source on to what its target reaches, as merge pushes round the cycle."""
    kept = {edge_key(e) for e in edges}
    split = {edge_key(e)[2] for e in original_edges if edge_key(e) not in kept}
    pairs = {ends(e) for e in original_edges}
    follows = [(u, v) for u, v in map(ends, edges) if (u, v) in pairs or (u in added and v in split)]
    original = [{"sourceNodeId": u, "targetNodeId": v} for u, v in pairs]
    for u, t in retries:
        follows += [(u, w) for w in downstream(t, original, parent_of) if w != u]
    return follows


def pushed_by_growth(a: str, grown: set[str], before: dict, after: dict, parent_of: dict[str, str | None]) -> bool:
    """Whether `a`, moved back by a sibling container's growth, sat in that container's way."""
    for c in grown:
        if parent_of.get(c) != parent_of.get(a):
            continue

        dw, dh = growth(c, before, after)
        for sx, sy in ((dw, 0), (0, dh)):
            if boxes_overlap(after[c], shifted(after[a], -sx, -sy), PADDING):
                return True
    return False


def path(entry_from: dict, entry_to: dict) -> dict:
    """The box a node pushed more than one slot covers on its way: a later push can meet it mid-way."""
    (x0, y0, w, h), (x1, y1, _, _) = box(entry_from), box(entry_to)
    if abs(x1 - x0) <= w + GAP and abs(y1 - y0) <= h + GAP:
        return entry_from
    return {"position": {"x": min(x0, x1), "y": min(y0, y1)}, "size": {"width": w + abs(x1 - x0), "height": h + abs(y1 - y0)}}


def took_spot(c: str, x: str, before: dict, after: dict, parent_of: dict[str, str | None]) -> bool:
    return c != x and parent_of.get(c) == parent_of.get(x) and boxes_overlap(after[c], path(before[x], after[x]), PADDING)


def caused(
    seeds: set[str],
    moved: set[str],
    follows: list[tuple[str, str]],
    before: dict,
    after: dict,
    parent_of: dict[str, str | None],
) -> set[str]:
    """Every node a push from `seeds` explains: one whose spot a cause took, or that follows a cause."""
    causes: set[str] = set()
    frontier = set(seeds)
    while frontier:
        causes |= frontier
        frontier = {
            x for x in moved - causes
            if any(took_spot(c, x, before, after, parent_of) for c in causes)
            or any(u in causes and v == x for u, v in follows)
        }
    return causes


def moves_without_cause(
    changed: set[str],
    added: set[str],
    grown: set[str],
    original_edges: list[dict],
    edges: list[dict],
    retries: set[tuple[str, str]],
    before: dict,
    after: dict,
    parent_of: dict[str, str | None],
) -> list[str]:
    """Invariant 3's cause: what merge placed, or a grown container pushed, takes a spot and drags what follows it."""
    moved = {i for i in changed if offset(before[i], after[i]) != (0, 0)}
    entered = {v for _, v in map(ends, edges)}
    placed = {a for a in added if a in after and (a in entered or pushed_by_growth(a, grown, before, after, parent_of))}
    follows = followed_edges(original_edges, edges, added, retries, parent_of)

    causes = caused(placed | grown, moved, follows, before, after, parent_of)
    return [
        f"{x!r} moved: {before[x].get('position')} -> {after[x].get('position')}, "
        "but nothing took its spot or pushed what it follows"
        for x in sorted(moved - causes)
    ]


def covered_area(a: dict, b: dict) -> int:
    ax, ay, aw, ah = box(a)
    bx, by, bw, bh = box(b)
    return max(0, min(ax + aw, bx + bw) - max(ax, bx)) * max(0, min(ay + ah, by + bh) - max(ay, by))


def sticky_moves(notes: set[str], solid: list[str], before: dict, after: dict, parent_of: dict[str, str | None]) -> list[str]:
    """A sticky note moves with the original node it covers most (ties by id), or not at all."""
    failures: list[str] = []
    for note in sorted(notes):
        cover = [(covered_area(before[note], before[i]), i) for i in solid if i in before and parent_of.get(i) == parent_of.get(note)]
        cover = sorted((c for c in cover if c[0] > 0), key=lambda c: (-c[0], c[1]))
        moved_with = offset(before[cover[0][1]], after[cover[0][1]]) if cover else (0, 0)
        if offset(before[note], after[note]) != moved_with:
            failures.append(
                f"sticky note {note!r} moved {offset(before[note], after[note])}, not with the node it covers "
                f"({cover[0][1] if cover else 'none'}, {moved_with})"
            )
    return failures


def new_overlaps(
    solid: list[str], changed: set[str], added: set[str], before: dict, after: dict, parent_of: dict[str, str | None]
) -> list[str]:
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


def order_changes(
    solid: list[str], edges: list[dict], retries: set[tuple[str, str]], before: dict, after: dict, parent_of: dict[str, str | None]
) -> list[str]:
    """Invariant 5."""
    failures: list[str] = []
    kept = [i for i in solid if i in before]
    for i, a in enumerate(kept):
        for b in kept[i + 1:]:
            if parent_of.get(a) != parent_of.get(b) or not shares_row(before[a], before[b]):
                continue
            was, now = box(before[a])[0] - box(before[b])[0], box(after[a])[0] - box(after[b])[0]
            if was and (was > 0) != (now > 0):
                failures.append(f"{a!r} and {b!r} changed order in their row")

    on_canvas = set(solid)
    for e in edges:
        u, v = ends(e)
        if u not in on_canvas or v not in on_canvas or parent_of.get(u) != parent_of.get(v):
            continue
        ux, vx = box(after[u])[0], box(after[v])[0]
        if ux < vx or (ux == vx and not shares_row(after[u], after[v])) or (u, v) in retries:
            continue
        was_right = u in before and v in before and box(before[u])[0] < box(before[v])[0]
        if was_right or u not in before or v not in before:
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
        _, y, _, h = box(after[a])
        succs = [v for u, v in map(ends, edges) if u == a and v in on_canvas and parent_of.get(v) == parent_of.get(a)]
        siblings = [
            v for u, v in map(ends, edges)
            if u in preds and v != a and v in added and v in on_canvas and parent_of.get(v) == parent_of.get(a)
        ]
        if min(abs(y - box(after[n])[1]) for n in preds + succs + siblings) > 2 * (h + GAP):
            failures.append(f"new node {a!r} at {after[a].get('position')} is more than two rows from every node it is wired to")

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
    tucked = pushed_from_left(added, kept, edges, before, after, parent_of)
    retries = retry_edges(original.get("edges", []), edges, before, after, parent_of)
    follows = followed_edges(original.get("edges", []), edges, added, retries, parent_of)
    nodes_moved = changed - sticky
    failures += moves_without_room(nodes_moved, added, grown, tucked, follows, before, after, parent_of)
    failures += moves_without_cause(nodes_moved, added, grown, original.get("edges", []), edges, retries, before, after, parent_of)
    failures += sticky_moves(changed & sticky, solid, before, after, parent_of)
    failures += new_overlaps(solid, changed, added, before, after, parent_of)
    failures += order_changes(solid, edges, retries, before, after, parent_of)
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
