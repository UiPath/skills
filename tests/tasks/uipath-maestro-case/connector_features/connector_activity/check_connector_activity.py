#!/usr/bin/env python3
"""ConnectorActivityCase: a RESOLVED execute-connector-activity task is wired.

Asserts the connector-activity plugin resolved a real Integration Service
activity and connection into the caseplan (Rule 8 — no fabricated IDs), rather
than leaving a `data: {}` skeleton, AND that the resolved node is editable in
Studio Web (spliced activity metadata, not a hand-assembled `context`). Does NOT
run debug: executing a connector activity has real side effects, so this task
verifies the build only.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_studio_web_activity_ready,
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
    activity_name = assert_studio_web_activity_ready(
        data, "execute-connector-activity task"
    )
    print(
        f"OK: execute-connector-activity resolved and editable in Studio Web "
        f"(displayName={task.get('displayName')!r}, connectorKey={ck!r}, "
        f'"Select activity"={activity_name!r})'
    )


if __name__ == "__main__":
    main()
