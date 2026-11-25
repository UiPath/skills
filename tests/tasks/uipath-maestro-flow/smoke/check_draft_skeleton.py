#!/usr/bin/env python3
"""Grade a draft-mode Flow skeleton: mock boxes, real control flow, no real nodes.

Usage (cwd = sandbox root):
    check_draft_skeleton.py [--trigger any|manual|scheduled] [--loop] [--switch-arms N] [--min-boxes N]

The Flow is found like every other Flow grader finds it, so a Studio Web
layout (`<Project>/new.flow`) passes too. A skeleton passes when:
  - it has one trigger, of the requested type when `--trigger` names one;
  - every action node is `core.logic.mock` with a `<Action> [<Kind>]` label,
    and there are at least `--min-boxes` (default 3) of them;
  - a decision or switch exists, and every arm that leads somewhere carries a
    label other than the SDK default (`True`/`False`, or `Case <value>` for that case's own value);
  - `--switch-arms N`: a switch has at least N labelled cases;
  - `--loop`: a loop exists and holds a mock box;
  - no decision, switch or loop reads a mock box's output;
  - every node has a numeric `ui.position` (`compile` lays out the canvas);
  - `uip maestro flow validate` reports Valid.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _shared.draft_flow import (  # noqa: E402
    DECISION, LOOP, MOCK, SWITCH, action_nodes, fail, is_trigger, label_of, load_flow, validate,
)

BOX_LABEL = re.compile(r"\S(?:.*?\S)? \[[A-Z][^\[\]]*\](?:\s*(?:→|->)\s*\S.*)?")
DECISION_DEFAULT_LABEL = re.compile(r"(?i)true|false")


def has_position(node: dict) -> bool:
    pos = (node.get("ui") or {}).get("position") or {}
    return all(isinstance(pos.get(k), (int, float)) and not isinstance(pos.get(k), bool) for k in ("x", "y"))


def is_labelled(label, default=None) -> bool:
    """A label counts unless it is empty, the decision default, or the SDK's `Case <value>` default."""
    text = str(label or "").strip()
    return bool(text) and not DECISION_DEFAULT_LABEL.fullmatch(text) and text != default


def default_case_label(case: dict) -> str:
    """The label the SDK gives a `value` case: `Case ` plus its compared value, as the expression spells it."""
    expression = case.get("expression") or ""
    return f"Case {expression.rsplit('===', 1)[1].strip()}" if "===" in expression else ""


def routed_edges(doc: dict, node_id: str) -> set[str]:
    return {e.get("sourcePort") for e in doc.get("edges") or [] if e.get("sourceNodeId") == node_id}


def arm_problems(doc: dict) -> tuple[int, list[str]]:
    """Count of control nodes that route, and a message per unlabelled arm."""
    routers, problems = 0, []
    for n in doc.get("nodes") or []:
        inputs = n.get("inputs") or {}
        ports = routed_edges(doc, n.get("id"))
        if n.get("type") == DECISION:
            routers += 1
            for port, key in (("true", "trueLabel"), ("false", "falseLabel")):
                if port in ports and not is_labelled(inputs.get(key)):
                    problems.append(f"decision {n['id']} arm {port!r} has no outcome label")
        elif n.get("type") == SWITCH:
            routers += 1
            for case in inputs.get("cases") or []:
                if f"case-{case.get('id')}" in ports and not is_labelled(case.get("label"), default_case_label(case)):
                    problems.append(f"switch {n['id']} case {case.get('id')!r} has no outcome label")
    return routers, problems


def expressions(node: dict) -> list[str]:
    inputs = node.get("inputs") or {}
    found = [inputs.get("expression")]
    found += [c.get("expression") for c in inputs.get("cases") or []]
    collection = inputs.get("collection")
    found.append(collection.get("expression") if isinstance(collection, dict) else collection)
    return [e for e in found if isinstance(e, str)]


def mock_reads(doc: dict, mock_ids: set[str]) -> list[str]:
    reads = []
    for n in doc.get("nodes") or []:
        if n.get("type") in (DECISION, SWITCH, LOOP):
            for expr in expressions(n):
                reads += [f"{n['id']} reads {m}" for m in mock_ids if re.search(rf"\$vars\.{re.escape(m)}\b", expr)]
    return reads


def loop_holds_mock(doc: dict, loop_id: str) -> bool:
    edges = doc.get("edges") or []
    types = {n.get("id"): n.get("type") for n in doc.get("nodes") or []}
    seen, todo = set(), [e["targetNodeId"] for e in edges if e.get("sourceNodeId") == loop_id and e.get("sourcePort") == "start"]
    while todo:
        cur = todo.pop()
        if cur in seen or cur == loop_id:
            continue
        seen.add(cur)
        if types.get(cur) == MOCK:
            return True
        todo += [e["targetNodeId"] for e in edges if e.get("sourceNodeId") == cur]
    return False


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trigger", default="any", choices=["any", "manual", "scheduled"])
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--switch-arms", type=int, default=0)
    ap.add_argument("--min-boxes", type=int, default=3)
    args = ap.parse_args(argv)

    path, doc = load_flow()
    nodes = doc.get("nodes") or []

    triggers = [n.get("type") for n in nodes if is_trigger(n)]
    want = None if args.trigger == "any" else f"core.trigger.{args.trigger}"
    if len(triggers) != 1 or (want and triggers[0] != want):
        return fail(f"expected one trigger{' ' + want if want else ''}, found {triggers}")

    real = sorted({n.get("type", "") for n in action_nodes(doc) if n.get("type") != MOCK})
    if real:
        return fail(f"skeleton has real action nodes: {real}")
    boxes = [n for n in nodes if n.get("type") == MOCK]
    if len(boxes) < args.min_boxes:
        return fail(f"expected >= {args.min_boxes} core.logic.mock boxes, found {len(boxes)}")
    bad = [n.get("id") for n in boxes if not BOX_LABEL.fullmatch(label_of(n))]
    if bad:
        return fail(f"boxes without an '<Action> [<Kind>]' label (optional `→ <variable>`): {bad}")

    routers, problems = arm_problems(doc)
    if not routers:
        return fail("no decision or switch")
    if problems:
        return fail("; ".join(problems))

    if args.switch_arms:
        arms = max(
            (sum(1 for c in (n.get("inputs") or {}).get("cases") or [] if is_labelled(c.get("label"), default_case_label(c)))
             for n in nodes if n.get("type") == SWITCH),
            default=0,
        )
        if arms < args.switch_arms:
            return fail(f"expected a switch with >= {args.switch_arms} labelled cases, found {arms}")

    if args.loop and not any(n.get("type") == LOOP and loop_holds_mock(doc, n["id"]) for n in nodes):
        return fail("expected a loop whose body holds a mock box")

    reads = mock_reads(doc, {n["id"] for n in boxes})
    if reads:
        return fail(f"routing reads a mock output (it is always null): {reads}")

    unplaced = [n.get("id") for n in nodes if not has_position(n)]
    if unplaced:
        return fail(f"no layout: nodes without a numeric ui.position: {unplaced}")

    print(f"Skeleton OK: {len(boxes)} mock boxes in {path}", flush=True)
    return validate(path)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
