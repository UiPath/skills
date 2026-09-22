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
            # Verify the delete actually happened; retry once on an unconfirmed
            # (transient) failure, then confirm via a tenant reread before giving
            # up. Only claim success on a confirmed deletion / not-found.
            ok = jira_is.delete_issue(conn, key)
            if not ok:
                ok = jira_is.delete_issue(conn, key)
            if not ok and jira_is.issue_absent(conn, key):
                ok = True  # tenant read CONFIRMS a 404 (not just an ambiguous failure)
            print(f"OK: deleted {key}" if ok
                  else f"WARN: could NOT confirm deletion of {key} — may be leaked in CE project")
    else:
        print("OK: nothing to delete")
except Exception as e:  # noqa: BLE001 — teardown must not fail the task
    print(f"WARN: teardown ignored error: {e}")
sys.exit(0)
