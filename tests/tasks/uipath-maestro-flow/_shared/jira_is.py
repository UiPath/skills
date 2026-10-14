#!/usr/bin/env python3
"""Live Jira helper shared by the maestro-flow Jira graders — wraps
`uip is resources run`. Superset of the five per-task copies this module
replaces (each task's own `_setup/jira_is.py` is the pre_run/post_run
tooling's copy; this one is read-only from grading, never staged into an
agent sandbox).

Assumes `uip` is on PATH and logged in and that the connection + CE project
exist — this is a tenant-gated e2e/smoke suite. The connection is scoped to
the curated single-record ops, so we create by body / get by id / delete by
id — never a JQL search.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any

CONNECTOR = "uipath-atlassian-jira"
FOLDER_PATH = "Shared/uipath-maestro-flow"
FOLDER_NAME = "uipath-maestro-flow"  # leaf of FOLDER_PATH, as reported by connections list
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
    out = result.stdout
    # Tolerate diagnostic/log lines the CLI may print before the JSON envelope.
    i = out.find("{")
    try:
        envelope = json.loads(out[i:] if i > 0 else out)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"uip {_operation(args)} returned invalid JSON "
            f"(exit {result.returncode}, stdout length {len(out)})"
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


def _issue_not_found(env: dict) -> bool:
    """True only for an ISSUE-SPECIFIC not-found from the Jira operation — proof the
    requested issue key is absent. Requires BOTH a structured HTTP 404 AND an
    issue-scoped signal (the provider phrases a missing issue as e.g. "Issue does
    not exist ..."). A bare ``"404"``/``"not found"`` substring, or a 404 that
    refers to a missing connection/activity/other prerequisite (no issue mention),
    is NOT accepted — so a prerequisite failure can't masquerade as a confirmed
    issue deletion."""
    blob = json.dumps(env)
    structured_404 = bool(
        re.search(r"status code ['\"]?404\b", blob, re.I)
        or re.search(r'"providerErrorCode"\s*:\s*404\b', blob)
        or re.search(r'"statusCode"\s*:\s*"?404\b', blob)
    )
    issue_specific = bool(
        re.search(r"issue\s+(does\s+not\s+exist|not\s+found|no\s+longer\s+exists|is\s+not\s+found)", blob, re.I)
        or re.search(r"(does\s+not\s+exist|not\s+found|no\s+longer\s+exists).{0,40}\bissue\b", blob, re.I)
    )
    return structured_404 and issue_specific


def connection_id() -> str:
    # Resolve by (name, folder) across all folders — avoids depending on
    # `uip or folders get` (which can return a Failure envelope in CI) while
    # still scoping to the target folder so a same-named connection in another
    # folder can't be picked by accident.
    conns = _required_data(
        "is", "connections", "list", CONNECTOR, "--all-folders", "--refresh",
        retry_transient=True,
    )
    by_name = [c for c in conns if c["Name"] == CONNECTION_NAME]
    scoped = [c for c in by_name if c.get("Folder") == FOLDER_NAME]
    if scoped:
        return scoped[0]["Id"]
    # Only accept a name-only match when NO candidate reports folder metadata
    # (older CLI / env). If folders ARE reported but none is the target folder,
    # refuse to guess — a same-named connection elsewhere could be the wrong
    # Jira account.
    if any(c.get("Folder") for c in by_name):
        raise SystemExit(
            f"FAIL: no {CONNECTOR} connection named {CONNECTION_NAME!r} in folder "
            f"{FOLDER_NAME!r}; candidates in folders {[c.get('Folder') for c in by_name]}"
        )
    if not by_name:
        raise SystemExit(f"FAIL: no {CONNECTOR} connection named {CONNECTION_NAME!r}")
    return by_name[0]["Id"]


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


def issue_absent(conn_id: str, key: str) -> bool:
    """True ONLY when a tenant read CONFIRMS the issue does not exist (not-found /
    404). False when it exists OR when the read itself failed (transient 5xx /
    auth) — so a caller never treats an ambiguous read as proof of deletion.
    Distinct from :func:`get_issue`, which collapses every failure to ``None``."""
    env = _run(
        "is", "resources", "run", "get", CONNECTOR, "curated_get_issue",
        "--connection-id", conn_id,
        "--query", f"project={PROJECT_KEY}&issuetype={ISSUETYPE_ID}&issueId={key}",
    )
    if str(env.get("Result", "")).lower() != "failure":
        return False  # a successful read means the issue still exists
    return _issue_not_found(env)


def delete_issue(conn_id: str, key: str) -> bool:
    """Delete an issue by key. Returns True only when deletion is CONFIRMED —
    either a success envelope, or a not-found/404 (already gone). Returns False
    for any other Failure envelope (transient 5xx / auth) so the caller can retry
    or report instead of silently leaking the issue in the shared CE project."""
    env = _run(
        "is", "resources", "run", "delete", CONNECTOR, "issue",
        "--connection-id", conn_id, "--query", f"issueId={key}",
        # The CLI never prompts and REFUSES an irreversible delete without this
        # flag ("Confirmation required … Re-run with --yes"). Without it every
        # teardown since 08-19 printed WARN and left its ticket in the CE project.
        "--yes",
    )
    if str(env.get("Result", "")).lower() != "failure":
        return True
    return _issue_not_found(env)
