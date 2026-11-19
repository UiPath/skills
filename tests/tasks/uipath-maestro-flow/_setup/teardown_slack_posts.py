#!/usr/bin/env python3
"""post_run: delete the Slack messages the grader journalled in `.slack-posts.jsonl`.

Written by `_shared/slack_journal.py`. Honors FLOW_E2E_CLEANUP=never. Best-effort: always exits 0.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

JOURNAL = Path(".slack-posts.jsonl")
CLEANUP_ENV = "FLOW_E2E_CLEANUP"
CLEANUP_NEVER = "never"
CHANNEL_ID = "C0B2FDZD1M3"  # #coding-agent-testing
CONNECTOR_KEY = "uipath-salesforce-slack"
CONNECTION_NAME = "is-sandboxes"
FOLDER_NAME = "uipath-maestro-flow"
STATE_ENABLED = "enabled"
RESULT_SUCCESS = "Success"
ABSENT_MARKERS = ("message_not_found", "message not found", "message does not exist")
LIST_TIMEOUT = 60
DELETE_TIMEOUT = 45
DEADLINE_SECONDS = 270  # post_run timeout is 300 (coder_eval cap)
ATTEMPTS = 2


def run_uip(args: list[str], timeout: float) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None


def parse(done: subprocess.CompletedProcess | None) -> dict:
    try:
        data = json.loads(done.stdout)
    except (AttributeError, TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def read_posts() -> list[tuple[str, str]]:
    if not JOURNAL.is_file():
        return []

    posts = []
    for line in JOURNAL.read_text(encoding="utf-8").splitlines():
        try:
            channel, ts = json.loads(line)
        except (ValueError, TypeError):
            continue
        if channel == CHANNEL_ID and isinstance(ts, str):
            posts.append((channel, ts))
    return list(dict.fromkeys(posts))


def connection_id() -> str | None:
    done = run_uip(["is", "connections", "list", "--all-folders", "--refresh"], LIST_TIMEOUT)
    rows = parse(done).get("Data")
    if not isinstance(rows, list):
        return None

    ids = [
        row.get("Id")
        for row in rows
        if isinstance(row, dict)
        and row.get("ConnectorKey") == CONNECTOR_KEY
        and row.get("Name") == CONNECTION_NAME
        and row.get("Folder") == FOLDER_NAME
        and str(row.get("State") or "").lower() == STATE_ENABLED
    ]
    return ids[0] if len(ids) == 1 and isinstance(ids[0], str) else None


def is_gone(done: subprocess.CompletedProcess | None) -> bool:
    if done is None:
        return False
    if done.returncode == 0 and parse(done).get("Result") == RESULT_SUCCESS:
        return True
    text = f"{done.stdout}\n{done.stderr}".lower()
    return any(marker in text for marker in ABSENT_MARKERS)


def delete(connection: str, channel: str, ts: str, deadline: float) -> bool:
    query = json.dumps({"conversationId": channel, "timestampId": ts}, separators=(",", ":"))
    args = ["is", "resources", "run", "delete", CONNECTOR_KEY, "ChatDeleteTimestamp_POST",
            "--connection-id", connection, "--query", query, "--yes"]
    for _ in range(ATTEMPTS):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        if is_gone(run_uip(args, min(DELETE_TIMEOUT, remaining))):
            return True
    return False


def main() -> None:
    if os.environ.get(CLEANUP_ENV, "").lower() == CLEANUP_NEVER:
        print(f"{CLEANUP_ENV}={CLEANUP_NEVER}; keeping the journalled Slack messages")
        return

    posts = read_posts()
    if not posts:
        print("OK: no Slack messages to delete")
        return

    deadline = time.monotonic() + DEADLINE_SECONDS
    connection = connection_id()
    if connection is None:
        print("WARN: no usable Slack connection; journalled messages were not deleted")
        return

    leaked = 0
    for channel, ts in posts:
        if delete(connection, channel, ts, deadline):
            print(f"OK: deleted Slack message {ts}")
            continue
        leaked += 1
        print(f"WARN: could not confirm deletion of Slack message {ts} in {channel}")
    if not leaked:
        JOURNAL.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 - teardown must not fail the task
        print(f"WARN: teardown ignored error: {error}")
    sys.exit(0)
