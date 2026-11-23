#!/usr/bin/env python3
"""DF query_every_row (BPMN): a whole-entity read pages instead of making one capped query.

The connector returns at most `limit` records per query and caps `limit` at 1000, so a
read of every record must re-run the query with a moving `start` until a page comes back
short. Passes when one Query Entity Records node on FlowCodeEvalEntity:

  1. sits on a sequence-flow cycle (the query runs again),
  2. takes its `start` from an `=`-expression (each run reads the next page), and
  3. has a literal `limit` from 1 to 1000, or an `=`-expression.

`sorted` additionally requires that node to sort, or pages can repeat or skip records.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    BodyShapeError,
    body_object,
    context_value,
    elements,
    fail,
    parse_bpmn,
    query_parameters,
)

CONNECTOR_KEY = "uipath-uipath-dataservice"
QUERY_OBJECTS = {"queryentityrecords", "queryentityrecordscurated", "queryentityrecords_v3"}
ENTITY = "FlowCodeEvalEntity"
PAGE_CAP = 1000
SORT_KEYS = ("_sortFieldName", "sortBy", "sortField", "orderBy")


def query_nodes(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask") + elements(root, "serviceTask")
        if context_value(task, "connectorKey") == CONNECTOR_KEY
        and context_value(task, "objectName").lower() in QUERY_OBJECTS
        and ENTITY in ET.tostring(task, encoding="unicode")
    ]


def on_cycle(root: ET.Element, node_id: str) -> bool:
    edges: dict[str, list[str]] = {}
    for flow in elements(root, "sequenceFlow"):
        edges.setdefault(flow.get("sourceRef", ""), []).append(flow.get("targetRef", ""))

    seen: set[str] = set()
    stack = list(edges.get(node_id, []))
    while stack:
        current = stack.pop()
        if current == node_id:
            return True
        if current in seen:
            continue
        seen.add(current)
        stack.extend(edges.get(current, []))
    return False


def is_expression(value: str) -> bool:
    return value.strip().startswith("=")


def limit_ok(value: str) -> bool:
    if not value or is_expression(value):
        return True
    try:
        return 1 <= int(value) <= PAGE_CAP
    except ValueError:
        return False


def page_problem(root: ET.Element, task: ET.Element) -> str | None:
    params = query_parameters(task)
    node = task.get("id", "?")
    if not on_cycle(root, node):
        return f"{node}: no sequence flow leads back to it, so it reads one page"
    if not is_expression(params.get("start", "")):
        return f"{node}: start is {params.get('start')!r}, not an =-expression, so every run reads the same page"
    if not limit_ok(params.get("limit", "")):
        return f"{node}: limit {params.get('limit')!r} is outside 1 to {PAGE_CAP}"
    return None


def is_sorted(task: ET.Element) -> bool:
    try:
        body = body_object(task)
    except BodyShapeError:
        body = {}
    params = query_parameters(task)
    return any(body.get(key) or params.get(key) for key in SORT_KEYS)


def paged_node(root: ET.Element) -> ET.Element:
    nodes = query_nodes(root)
    if not nodes:
        fail(f"no Query Entity Records node on {ENTITY}")

    problems = []
    for task in nodes:
        problem = page_problem(root, task)
        if problem is None:
            return task
        problems.append(problem)
    fail("no query pages through the entity: " + "; ".join(problems))


def main(argv: list[str]) -> None:
    mode = argv[1] if len(argv) > 1 else "paged"
    _, root = parse_bpmn()
    task = paged_node(root)

    if mode == "sorted" and not is_sorted(task):
        fail(f"{task.get('id')}: the paged query sets no sort field, so pages can repeat or skip records")

    print(f"OK: {task.get('id')} pages {ENTITY}")


if __name__ == "__main__":
    main(sys.argv)
