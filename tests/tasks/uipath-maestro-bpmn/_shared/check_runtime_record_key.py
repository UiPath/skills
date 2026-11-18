#!/usr/bin/env python3
"""Verify a record fetched by a run-time key is read by that key alone.

A curated "get" operation can declare lookup fields that select its field set
(Jira Get Issue: `project`, `issuetype`). Those are resolved at design time,
against the connection; a run-time expression there is `check`'s
`LOOKUP_RUNTIME_VALUE`, and the connector rejects it when the process runs.
A value pinned there instead reads only that one project. When the key
arrives at run time and may name any record, the step that reads it must take
the key alone: the connector's generic Retrieve (`get-record` with an
`object`) does.

Passes when some node of the connector:
  1. reads the record by a path parameter whose value is a run-time
     expression (the process input), and
  2. sends none of the named lookup fields, run-time or pinned.

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

    problems = []
    for node in nodes:
        node_id = node.attrib.get("id", "<unknown>")
        keyed = [k for k, v in path_parameters(node).items() if runtime(v)]
        if not keyed:
            problems.append(f"{node_id}: no path parameter reads a run-time value")
            continue
        params = {**query_parameters(node), **path_parameters(node)}
        bad = {f: params[f] for f in lookups if params.get(f, "").strip()}
        if bad:
            problems.append(f"{node_id}: sends design-time lookup(s) {bad}; the key alone must select the record")
            continue
        print(f"OK: {node_id} reads the record by run-time {keyed} alone")
        return
    fail("; ".join(problems))


if __name__ == "__main__":
    main()
