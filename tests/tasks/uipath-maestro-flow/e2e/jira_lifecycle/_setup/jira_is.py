#!/usr/bin/env python3
"""Minimal live Jira helper for this task — wraps `uip is resources run`.

Self-contained (no shared module). Assumes `uip` is on PATH and logged in and
that the connection + CE project exist — this is a tenant-gated e2e task.

The connection is scoped to the curated single-record ops, so we create by
body / get by id / delete by id — never a JQL search.
"""

from __future__ import annotations

import json
import re
import subprocess
import time

CONNECTOR = "uipath-atlassian-jira"
FOLDER_PATH = "Shared/uipath-maestro-flow"
CONNECTION_NAME = "is-sandboxes-test@uipath.com-uipath-sandbox-380"
PROJECT_KEY = "CE"        # "Coder Eval" project on uipath-sandbox-380
ISSUETYPE_ID = "11457"    # "Task" issue type, scoped to the CE project


def _run(*args: str) -> dict:
    out = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=120,
    ).stdout
    return json.loads(out)


_RETRY_DELAY_SECONDS = 2

# Stopgap until UiPath/cli#5509 ships: the cli labels `is resources run` 5xx RetryWillNotFix.
_HTTP_5XX = re.compile(r"5\d\d\b")


def _is_transient(envelope: dict) -> bool:
    return (
        envelope.get("Retry") == "RetryLater"
        or envelope.get("ErrorCode") == "server_error"
        or bool(_HTTP_5XX.match(str(envelope.get("Message", ""))))
    )


def _read(*args: str) -> dict:
    envelope = _run(*args)
    if _is_transient(envelope):
        time.sleep(_RETRY_DELAY_SECONDS)
        envelope = _run(*args)
    return envelope


def connection_id() -> str:
    folder_key = _read("or", "folders", "get", FOLDER_PATH)["Data"]["Key"]
    conns = _read("is", "connections", "list", CONNECTOR, "--folder-key", folder_key, "--refresh")["Data"]
    return next(c["Id"] for c in conns if c["Name"] == CONNECTION_NAME)


def create_issue(conn_id: str, summary: str) -> str:
    body = {"fields": {"project": {"key": PROJECT_KEY}, "issuetype": {"id": ISSUETYPE_ID}, "summary": summary}}
    return _run(
        "is", "resources", "run", "create", CONNECTOR, "curated_create_issue",
        "--connection-id", conn_id, "--body", json.dumps(body),
    )["Data"]["key"]


def get_issue(conn_id: str, key: str) -> dict | None:
    """Return the issue's `fields` dict (includes `summary`, `status`, and
    `comment`), or None if it doesn't exist (404)."""
    env = _run(
        "is", "resources", "run", "get", CONNECTOR, "curated_get_issue",
        "--connection-id", conn_id,
        "--query", f"project={PROJECT_KEY}&issuetype={ISSUETYPE_ID}&issueId={key}",
    )
    if env.get("Result") == "Failure":
        return None
    return env["Data"].get("fields", {})


def delete_issue(conn_id: str, key: str) -> None:
    """Delete an issue by key. A 404 (already gone) is a no-op."""
    _run(
        "is", "resources", "run", "delete", CONNECTOR, "issue",
        "--connection-id", conn_id, "--query", f"issueId={key}",
        # The CLI never prompts and REFUSES an irreversible delete without this
        # flag ("Confirmation required … Re-run with --yes"). Without it every
        # teardown since 08-19 printed WARN and left its ticket in the CE project.
        "--yes",
    )
