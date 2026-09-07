"""The coded-action domain model, built from turtle.py's tokens.

One TTL holds one action plus the read nodes it names. `marker_of` is the load-bearing part: the
`func:name(args)` marker in ont:statements is what binds the job's input to the action's params and
reads, and it resolves BY NAME against params union ont:bindsTo -- never positionally.
"""

from __future__ import annotations

import re

# The runtimes a coded action can name. One today; the point of the predicate is that adding a
# second needs no migration and no defaulting rule.
PROCESS_TYPES = frozenset({"CODED_FUNCTION"})

from coded_action.turtle import (
    first_quoted,
    is_directive,
    list_items,
    quoted_objects,
    subject_of,
    ttl_statements,
)




def ttl_model(text: str) -> dict:
    """Every subject in the file, plus the coded actions among them."""
    nodes: dict[str, list[str]] = {}
    unterminated: list[str] = []
    for body, terminated in ttl_statements(text):
        subject = subject_of(body)
        if not subject or is_directive(subject):
            continue
        nodes.setdefault(subject, []).append(body[body.index(subject) + len(subject) :])
        if not terminated:
            unterminated.append(subject)
    actions = {}
    for subject, bodies in nodes.items():
        body = "\n".join(bodies)
        if not re.search(r"(?:^|;|\s)a\s+[^;]*\bfno:Function\b", body):
            continue
        if first_quoted(body, "ont:language") != "CODED":
            continue
        actions[subject] = parse_action(subject, body, nodes)
    return {"nodes": nodes, "actions": actions, "unterminated": unterminated}


def parse_action(subject: str, body: str, nodes: dict[str, list[str]]) -> dict:
    statements = list_items(body, "ont:statements")
    reads = list_items(body, "ont:reads") or []
    expects = list_items(body, "fno:expects") or []
    read_nodes = {}
    for node in reads:
        node_body = "\n".join(nodes.get(node, []))
        read_nodes[node] = {
            "defined": node in nodes,
            "bindsTo": first_quoted(node_body, "ont:bindsTo"),
            "statement": first_quoted(node_body, "ont:statement"),
        }
    param_nodes = {}
    for node in expects:
        node_body = "\n".join(nodes.get(node, []))
        param_nodes[node] = {
            "defined": node in nodes,
            "paramName": first_quoted(node_body, "ont:paramName"),
        }
    return {
        "name": subject.split(":", 1)[-1],
        "statements": statements,
        "statements_is_list": statements is not None,
        "statements_scalar": first_quoted(body, "ont:statements"),
        "reads": reads,
        "read_nodes": read_nodes,
        "params": param_nodes,
        "writes": quoted_objects(body, "ont:writes"),
        "writes_is_list": list_items(body, "ont:writes") is not None,
        "process": first_quoted(body, r"ont:process(?![A-Za-z])"),
        "processType": first_quoted(body, "ont:processType"),
    }


def marker_of(action: dict) -> tuple[str, list[str]] | None:
    statements = action["statements"]
    if not statements or len(statements) != 1:
        return None
    match = re.fullmatch(r"func:(\w+)\(([^)]*)\)", statements[0].strip())
    if not match:
        return None
    return match.group(1), [arg.strip() for arg in match.group(2).split(",") if arg.strip()]
