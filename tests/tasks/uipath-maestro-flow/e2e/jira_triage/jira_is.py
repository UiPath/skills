#!/usr/bin/env python3
"""Minimal live Jira helper for this task — wraps `uip is resources run`.

Self-contained (no shared module). Assumes `uip` is on PATH and logged in and
that the connection + CE project exist — this is a tenant-gated e2e task.

The connection is scoped to the curated single-record ops, so we create by
body / get by id / delete by id — never a JQL search.
"""

from __future__ import annotations

import json
import subprocess

CONNECTOR = "uipath-atlassian-jira"
FOLDER_PATH = "Shared/uipath-maestro-flow"
CONNECTION_NAME = "is-sandboxes-test@uipath.com-uipath-sandbox-380"
PROJECT_KEY = "CE"        # "Coder Eval" project on uipath-sandbox-380
ISSUETYPE_ID = "11457"    # "Task" issue type, scoped to the CE project
# "In Progress" transition id on the CE project's workflow. Seeded so the flow's
# Update-Issue-Status node has a concrete target (there is no curated op to list
# transitions on this connection — `issue_transitions` GET 401s).
STATUS_ID = "31"
EXPECTED_STATUS = "In Progress"
# The connection's own service account (is-sandboxes-test@uipath.com). Seeded so
# the flow's Update-Issue-Assignee node has a valid assignee; user lookup by
# email/name is not in the curated scope.
ASSIGNEE_ACCOUNT_ID = "712020:b53bf3dc-8817-419e-99e1-5670aeb7ffe6"


def _run(*args: str) -> dict:
    out = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=120,
    ).stdout
    return json.loads(out)


def connection_id() -> str:
    folder_key = _run("or", "folders", "get", FOLDER_PATH)["Data"]["Key"]
    conns = _run("is", "connections", "list", CONNECTOR, "--folder-key", folder_key, "--refresh")["Data"]
    return next(c["Id"] for c in conns if c["Name"] == CONNECTION_NAME)


def get_issue(conn_id: str, key: str) -> dict | None:
    """Return the issue's `fields` dict (includes `summary`, `status`,
    `assignee`, and `comment`), or None if it doesn't exist (404)."""
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
    )
