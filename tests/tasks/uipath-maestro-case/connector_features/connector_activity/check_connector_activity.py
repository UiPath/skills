#!/usr/bin/env python3
"""ConnectorActivityCase: a RESOLVED execute-connector-activity task is wired.

Asserts the connector-activity plugin resolved a real Integration Service
activity and connection into the caseplan (Rule 8 — no fabricated IDs), rather
than leaving a `data: {}` skeleton. Does NOT run debug: executing a connector
activity has real side effects, so this task verifies the build only.

Also asserts the two things that make a resolved connector task actually run:
the SDD's `\n` survives as two characters rather than a real line break, and the
SDD's declared extract survives the `caseShape.outputs` copy. Both pass
`uip maestro case validate` and both fail at runtime, so the build is the only
place to catch them.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_task_type_present,
    task_is_skeleton,
)


def main():
    task = assert_task_type_present("execute-connector-activity")
    if task_is_skeleton(task):
        sys.exit(
            "FAIL: execute-connector-activity task is a skeleton (missing "
            "data.typeId / data.connectionId) — the connector must resolve "
            "against a live Integration Service connection on the tenant"
        )
    data = task.get("data") or {}
    context = data.get("context", [])
    ck_entry = next((c for c in context if c.get("name") == "connectorKey"), None)
    ck = ck_entry.get("value") if ck_entry else None
    if ck != "uipath-salesforce-slack":
        sys.exit(
            f"FAIL: expected connectorKey 'uipath-salesforce-slack'; got {ck!r} — "
            "agent may have resolved against the wrong connector"
        )
    problems = []

    # A real line break inside a `=js:` string throws `Invalid or unexpected token` the
    # moment the runtime compiles it. The SDD writes the two characters `\` and `n`, so
    # anything holding a real newline lost an escape level on the way into the plan.
    for holder, value in walk_strings(data):
        if "\n" in value and value.startswith("=js:"):
            problems.append(
                f"{holder} holds a real line break inside a `=js:` expression; the SDD "
                f"writes it as the two characters \\n, and a JavaScript string cannot span "
                f"lines: {value[:90]!r}"
            )

    # `case spec` returns the connector's own outputs and never the SDD's rows, so a task
    # built by copying `caseShape.outputs` wholesale drops every declared extract.
    outputs = data.get("outputs") or []
    names = [str(o.get("var") or o.get("name") or "") for o in outputs]
    if "lastPostStatus" not in names:
        problems.append(
            f"no output writes 'lastPostStatus'; the SDD extracts `response.status -> "
            f"lastPostStatus` and the plan carries {names or 'no outputs'}"
        )

    if problems:
        sys.exit("FAIL: " + "; ".join(problems))

    print(
        f"OK: execute-connector-activity resolved "
        f"(displayName={task.get('displayName')!r}, "
        f"typeId={str(data.get('typeId'))[:12]}…, connectionId set, connectorKey={ck!r}, "
        f"outputs={names})"
    )


def walk_strings(node, path="data"):
    """Every string in the task's `data`, with a readable path to it."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from walk_strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_strings(value, f"{path}[{index}]")
    elif isinstance(node, str):
        yield path, node


if __name__ == "__main__":
    main()
