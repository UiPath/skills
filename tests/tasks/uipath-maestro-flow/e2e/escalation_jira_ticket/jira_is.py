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
FOLDER_NAME = "uipath-maestro-flow"  # leaf of FOLDER_PATH, as reported by connections list
CONNECTION_NAME = "is-sandboxes-test@uipath.com-uipath-sandbox-380"
PROJECT_KEY = "CE"        # "Coder Eval" project on uipath-sandbox-380
ISSUETYPE_ID = "11457"    # "Task" issue type, scoped to the CE project


def _run(*args: str) -> dict:
    out = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=120,
    ).stdout
    # Tolerate diagnostic/log lines the CLI may print before the JSON envelope.
    i = out.find("{")
    return json.loads(out[i:] if i > 0 else out)


def connection_id() -> str:
    # Resolve by (name, folder) across all folders — avoids depending on
    # `uip or folders get` (which can return a Failure envelope in CI) while
    # still scoping to the target folder so a same-named connection in another
    # folder can't be picked by accident.
    conns = _run("is", "connections", "list", CONNECTOR, "--all-folders", "--refresh")["Data"]
    by_name = [c for c in conns if c["Name"] == CONNECTION_NAME]
    scoped = [c for c in by_name if c.get("Folder") == FOLDER_NAME]
    if scoped:
        return scoped[0]["Id"]
    # Only accept a name-only match when NO candidate reports folder metadata
    # (older CLI / env). If folders ARE reported but none is the target folder,
    # refuse to guess — a same-named connection elsewhere could be the wrong
    # Jira account. Fail the prerequisite instead.
    if any(c.get("Folder") for c in by_name):
        raise SystemExit(
            f"FAIL: no {CONNECTOR} connection named {CONNECTION_NAME!r} in folder "
            f"{FOLDER_NAME!r}; candidates in folders {[c.get('Folder') for c in by_name]}"
        )
    if not by_name:
        raise SystemExit(f"FAIL: no {CONNECTOR} connection named {CONNECTION_NAME!r}")
    return by_name[0]["Id"]


def create_issue(conn_id: str, summary: str) -> str:
    body = {"fields": {"project": {"key": PROJECT_KEY}, "issuetype": {"id": ISSUETYPE_ID}, "summary": summary}}
    return _run(
        "is", "resources", "run", "create", CONNECTOR, "curated_create_issue",
        "--connection-id", conn_id, "--body", json.dumps(body),
    )["Data"]["key"]


def get_issue(conn_id: str, key: str) -> dict | None:
    """Return the issue's `fields` dict, or None if it doesn't exist (404)."""
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
