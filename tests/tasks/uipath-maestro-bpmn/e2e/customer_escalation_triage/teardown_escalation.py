#!/usr/bin/env python3
"""post_run: delete every Jira issue and Slack message the run created.

Replays the flat journal the grader appends to the moment each id is visible
(`escalation_is.JOURNAL`) — the only cleanup that survives coder_eval
SIGKILLing the graded command. Solutions are not swept here: the standard
`_shared/cleanup_solutions.py` post_run step globs the ephemeral .uipx.
Idempotent and never fails the task.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import escalation_is

try:
    records = escalation_is.read_journal()
    if not records:
        print("OK: nothing journalled to delete")
        sys.exit(0)
    connections = escalation_is.connection_ids()
    leaked = 0
    for issue in dict.fromkeys(records.get("jira_issue", [])):
        ok = escalation_is.delete_jira_issue(
            connections[escalation_is.JIRA_CONNECTOR], issue
        )
        print(f"OK: deleted Jira {issue}" if ok
              else f"WARN: could NOT confirm deletion of Jira {issue}")
        leaked += 0 if ok else 1
    for record in records.get("slack_message", []):
        channel_id, timestamp = record
        ok = escalation_is.delete_slack_message(
            connections[escalation_is.SLACK_CONNECTOR], channel_id, timestamp
        )
        print(f"OK: deleted Slack {timestamp}" if ok
              else f"WARN: could NOT confirm deletion of Slack {timestamp}")
        leaked += 0 if ok else 1
    if not leaked:
        escalation_is.JOURNAL.unlink(missing_ok=True)
except Exception as error:  # noqa: BLE001 — teardown must not fail the task
    print(f"WARN: teardown ignored error: {error}")
sys.exit(0)
