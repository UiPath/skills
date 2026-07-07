#!/usr/bin/env python3
"""Check: agent resolved a push-time "connection not found" instead of
dismissing it.

The seed's `bindings.json` carries a stale connection id in
`ConnectionId.defaultValue`, but the real Integration Service connection (per
`uip is connections list`) has id `22222222-2222-2222-2222-222222222222`. Push
resolves the connection by that id (`GET /Connections/<id>`); a wrong id is
warned-and-skipped (non-virtual kind, exits 0). The skill must drive the agent
to diagnose the mismatch and correct the binding so the connection imports — not
accept the warning.

Check: `slack-triage/bindings.json` has a `connection` resource whose
`ConnectionId.defaultValue` is now the real connection id. That value is what
push resolves against, so correcting it is what makes the connection import. The
code keeps referencing the binding `key` alias (`retrieve("slack-triage")`), so
the `retrieve()` argument is not constrained here.

The re-push after the fix is graded separately in the task YAML via a
`command_executed` count on `uip codedagent push`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.project_root import find_project_root  # noqa: E402

REAL_ID = "22222222-2222-2222-2222-222222222222"
ROOT = find_project_root("slack-triage")


def check_bindings() -> None:
    path = ROOT / "bindings.json"
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    conns = [r for r in data.get("resources", []) if r.get("resource") == "connection"]
    if not conns:
        sys.exit("FAIL: bindings.json has no connection resource")
    conn_id = conns[0].get("value", {}).get("ConnectionId", {}).get("defaultValue")
    if conn_id != REAL_ID:
        sys.exit(
            f"FAIL: connection ConnectionId is '{conn_id}', expected '{REAL_ID}' — "
            "the binding was not corrected to the real connection id."
        )


def main() -> None:
    check_bindings()
    print("PASS: connection binding ConnectionId corrected to the real connection id")


if __name__ == "__main__":
    main()
