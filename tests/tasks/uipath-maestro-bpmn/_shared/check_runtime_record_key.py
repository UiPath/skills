#!/usr/bin/env python3
"""Verify a record fetched by a run-time key is read by that key alone.

A curated "get" operation can declare lookup fields that select its field set
(Jira Get Issue: `project`, `issuetype`). Those are resolved at design time,
against the connection; a run-time expression there is `check`'s
`LOOKUP_RUNTIME_VALUE` warning: it must carry the id the connector stores,
which a caller holding only the key does not have.
A value pinned there instead reads only that one project. When the key
arrives at run time and may name any record, the step that reads it must take
the key alone: the connector's generic Retrieve (`get-record` with an
`object`) does.

Passes when no node of the connector sends a named lookup field (run-time
or pinned) and some GET node reads the record by a key taken from a process
input (or a variable mapped from one): a path parameter, or a `jql` query
that pins no literal project (JQL by key reads any project too).

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_runtime_record_key.py <NAME_HINT> <CONNECTOR_KEY> <LOOKUP>[,<LOOKUP>...]
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    context_value,
    declared_variable_elements,
    elements,
    fail,
    parse_bpmn,
    path_parameters,
    query_parameters,
)

TASK_TAGS = ("sendTask", "serviceTask", "task")
INPUT_TAG = f"{{{NS['uipath']}}}input"
VAR_REF = re.compile(r"\bvars\.(\w+)")
# A project clause whose value is literal text, not a string closed and joined to an expression.
PINNED_PROJECT = re.compile(r"\bproject\s*(?:=|\bin\b)(?!\s*[\"'`]\s*\+|\s*\$\{)", re.IGNORECASE)


def reads_input(value: str, inputs: set[str]) -> bool:
    value = value.strip()
    return value.startswith("=") and any(name in inputs for name in VAR_REF.findall(value))


def input_variables(root) -> set[str]:
    """Process inputs, plus every variable an output mapping fills from one (`var` <- `source`)."""
    names = {v.attrib.get("name", "") for v in declared_variable_elements(root) if v.tag == INPUT_TAG}
    mappings = [(o.attrib.get("var", ""), o.attrib.get("source", "")) for o in root.iter(f"{{{NS['uipath']}}}output")]
    grown = True
    while grown:
        grown = False
        for var, source in mappings:
            if var and var not in names and reads_input(source, names):
                names.add(var)
                grown = True
    return names


def main() -> None:
    if len(sys.argv) != 4:
        fail("usage: check_runtime_record_key.py <name_hint> <connector_key> <lookup>[,<lookup>...]")
    name_hint, connector_key, lookups = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    path, root = parse_bpmn(name_hint)
    inputs = input_variables(root)

    nodes = [n for tag in TASK_TAGS for n in elements(root, tag) if context_value(n, "connectorKey") == connector_key]
    if not nodes:
        fail(f"no {connector_key} connector node in {path}")

    bad_nodes, ok = [], []
    for node in nodes:
        node_id = node.attrib.get("id", "<unknown>")
        query = query_parameters(node)
        params = {**query, **path_parameters(node)}
        bad = {f: params[f] for f in lookups if params.get(f, "").strip()}
        if bad:
            bad_nodes.append(f"{node_id}: sends design-time lookup(s) {bad}; the key alone must select the record")
            continue
        if context_value(node, "method").upper() != "GET":
            continue
        keys = {**path_parameters(node), **{q: v for q, v in query.items() if q == "jql" and not PINNED_PROJECT.search(v)}}
        keyed = [k for k, v in keys.items() if reads_input(v, inputs)]
        if keyed:
            ok.append(f"{node_id} reads the record by input key {keyed} alone")
    if bad_nodes:
        fail("; ".join(bad_nodes))
    if not ok:
        fail(f"no {connector_key} GET node reads the record by a process input's key (a jql must pin no literal project)")
    print("OK: " + "; ".join(ok))


if __name__ == "__main__":
    main()
