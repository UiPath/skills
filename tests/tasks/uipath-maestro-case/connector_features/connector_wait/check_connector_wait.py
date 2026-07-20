#!/usr/bin/env python3
"""ConnectorWaitCase: a RESOLVED wait-for-connector task is wired.

Asserts the connector-trigger plugin resolved a real Integration Service event
into the caseplan (Rule 8 — no fabricated IDs) with the correct serviceType,
rather than leaving a `data: {}` skeleton. Does NOT run debug: a
wait-for-connector suspends waiting for a real external event.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_task_type_present,
    task_is_skeleton,
)


def main():
    task = assert_task_type_present("wait-for-connector")
    if task_is_skeleton(task):
        sys.exit(
            "FAIL: wait-for-connector task is a skeleton (missing data.typeId / "
            "data.connectionId) — the connector event must resolve against a "
            "live Integration Service connection on the tenant"
        )
    data = task.get("data") or {}
    svc = data.get("serviceType")
    if svc != "Intsvc.WaitForEvent":
        sys.exit(
            f"FAIL: wait-for-connector data.serviceType must be "
            f"'Intsvc.WaitForEvent'; got {svc!r}"
        )
    context = data.get("context", [])
    ck_entry = next((c for c in context if c.get("name") == "connectorKey"), None)
    ck = ck_entry.get("value") if ck_entry else None
    if ck != "uipath-microsoft-outlook365":
        sys.exit(
            f"FAIL: expected connectorKey 'uipath-microsoft-outlook365'; got {ck!r} — "
            "agent may have resolved against the mock connector"
        )
    print(
        f"OK: wait-for-connector resolved "
        f"(displayName={task.get('displayName')!r}, "
        f"serviceType={svc}, connectorKey={ck!r}, typeId + connectionId set)"
    )


if __name__ == "__main__":
    main()
