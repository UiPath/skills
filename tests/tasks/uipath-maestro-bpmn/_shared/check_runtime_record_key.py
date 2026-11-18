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
or pinned) and some node reads the record by a run-time key: a path
parameter, or a `jql` query (JQL by key reads any project too).

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_runtime_record_key.py <NAME_HINT> <CONNECTOR_KEY> <LOOKUP>[,<LOOKUP>...]
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import context_value, elements, fail, parse_bpmn, path_parameters, query_parameters  # noqa: E402

TASK_TAGS = ("sendTask", "serviceTask", "task")


def runtime(value: str) -> bool:
    value = value.strip()
    return value.startswith("=") and not value.startswith("=bindings.")


def main() -> None:
    if len(sys.argv) != 4:
        fail("usage: check_runtime_record_key.py <name_hint> <connector_key> <lookup>[,<lookup>...]")
    name_hint, connector_key, lookups = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    path, root = parse_bpmn(name_hint)

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
        keys = {**path_parameters(node), **{q: v for q, v in query.items() if q == "jql"}}
        keyed = [k for k, v in keys.items() if runtime(v)]
        if keyed:
            ok.append(f"{node_id} reads the record by run-time {keyed} alone")
    if bad_nodes:
        fail("; ".join(bad_nodes))
    if not ok:
        fail(f"no {connector_key} node reads the record by a run-time key")
    print("OK: " + "; ".join(ok))

if __name__ == "__main__":
    main()
