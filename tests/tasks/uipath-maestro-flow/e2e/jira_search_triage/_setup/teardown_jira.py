#!/usr/bin/env python3
"""post_run: delete every issue the run created (keys in `.created_keys`).
Idempotent and never fails the task."""

import sys
from pathlib import Path

import jira_is

try:
    kf = Path(".created_keys")
    keys = kf.read_text().split() if kf.is_file() else []
    if keys:
        conn = jira_is.connection_id()
        for key in keys:
            jira_is.delete_issue(conn, key)
            print(f"OK: deleted {key}")
    else:
        print("OK: nothing to delete")
except Exception as e:  # noqa: BLE001 — teardown must not fail the task
    print(f"WARN: teardown ignored error: {e}")
sys.exit(0)
