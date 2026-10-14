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
from typing import Any

CONNECTOR = "uipath-atlassian-jira"
FOLDER_PATH = "Shared/uipath-maestro-flow"
CONNECTION_NAME = "is-sandboxes-test@uipath.com-uipath-sandbox-380"
PROJECT_KEY = "CE"        # "Coder Eval" project on uipath-sandbox-380
ISSUETYPE_ID = "11457"    # "Task" issue type, scoped to the CE project


def _operation(args: tuple[str, ...]) -> str:
    return " ".join(args[:3])


def _run(*args: str) -> dict[str, Any]:
    result = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=120,
    )
    try:
        envelope = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"uip {_operation(args)} returned invalid JSON "
            f"(exit {result.returncode}, stdout length {len(result.stdout)})"
        ) from exc
    if not isinstance(envelope, dict):
        raise RuntimeError(f"uip {_operation(args)} returned a non-object JSON envelope")
    return envelope


def _is_transient(envelope: dict[str, Any]) -> bool:
    return envelope.get("Retry") == "RetryLater" or envelope.get("ErrorCode") == "server_error"


def _failure_summary(envelope: dict[str, Any]) -> str:
    keys = ("Result", "ErrorCode", "Retry", "StatusCode", "Message")
    summary = {key: envelope[key] for key in keys if key in envelope}
    return json.dumps(summary, sort_keys=True, default=str)


def _required_data(*args: str, retry_transient: bool = False) -> Any:
    envelope = _run(*args)
    if retry_transient and _is_transient(envelope):
        envelope = _run(*args)
    if envelope.get("Result") != "Success" or "Data" not in envelope:
        raise RuntimeError(
            f"uip {_operation(args)} failed: {_failure_summary(envelope)}"
        )
    return envelope["Data"]


def connection_id() -> str:
    folder = _required_data("or", "folders", "get", FOLDER_PATH, retry_transient=True)
    folder_key = folder["Key"]
    conns = _required_data(
        "is", "connections", "list", CONNECTOR,
        "--folder-key", folder_key, "--refresh",
    )
    return next(c["Id"] for c in conns if c["Name"] == CONNECTION_NAME)


def myself(conn_id: str) -> str:
    """Return the connection user's Atlassian accountId."""
    return _required_data(
        "is", "resources", "run", "get", CONNECTOR, "myself",
        "--connection-id", conn_id,
    )["accountId"]


def create_issue(conn_id: str, summary: str) -> str:
    body = {"fields": {"project": {"key": PROJECT_KEY}, "issuetype": {"id": ISSUETYPE_ID}, "summary": summary}}
    return _required_data(
        "is", "resources", "run", "create", CONNECTOR, "curated_create_issue",
        "--connection-id", conn_id, "--body", json.dumps(body),
    )["key"]


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
        # The CLI never prompts and REFUSES an irreversible delete without this
        # flag ("Confirmation required … Re-run with --yes"). Without it every
        # teardown since 08-19 printed WARN and left its ticket in the CE project.
        "--yes",
    )
