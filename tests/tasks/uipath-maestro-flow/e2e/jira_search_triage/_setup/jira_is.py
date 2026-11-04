#!/usr/bin/env python3
"""Minimal live Jira helper for this task — wraps `uip is resources run`.

Self-contained (no shared module). Assumes `uip` is on PATH and logged in and
that the connection + CE project exist — this is a tenant-gated e2e task.
This helper uses the create / get / delete ops to seed and verify.
"""

from __future__ import annotations

import json
import subprocess

CONNECTOR = "uipath-atlassian-jira"
FOLDER_PATH = "Shared/uipath-maestro-flow"
CONNECTION_NAME = "is-sandboxes-test@uipath.com-uipath-sandbox-380"
PROJECT_KEY = "CE"        # "Coder Eval" project on the connection's Jira site
ISSUETYPE_NAME = "Task"  # resolved to its id per site: issuetype_id()


def _run(*args: str) -> dict:
    out = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=120,
    ).stdout
    return json.loads(out)


_ISSUETYPE_IDS: dict[str, str] = {}


def _listed(conn_id: str, resource: str) -> list[dict]:
    """Every object in a `uip is resources run list` answer, at any depth."""
    env = _run("is", "resources", "run", "list", CONNECTOR, resource, "--connection-id", conn_id)
    if env.get("Result") != "Success" or "Data" not in env:
        raise RuntimeError(f"uip is resources run list {resource} failed: {env.get('Message') or env.get('Result')}")
    found: list[dict] = []
    stack = [env["Data"]]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            found.append(node)
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return found


def issuetype_id(conn_id: str) -> str:
    """The id of the ISSUETYPE_NAME type in PROJECT_KEY on the connection's Jira site.

    Issue-type ids are per site and, in team-managed projects, per project, so the id is read at
    run time like the reporter's accountId. A project-scoped type wins; a global type counts only
    when the project has none of that name.
    """
    if conn_id in _ISSUETYPE_IDS:
        return _ISSUETYPE_IDS[conn_id]
    project_ids = [
        str(p.get("id") or p.get("Id"))
        for p in _listed(conn_id, "project")
        if str(p.get("key") or p.get("projectKey") or "").casefold() == PROJECT_KEY.casefold()
        and (p.get("id") or p.get("Id"))
    ]
    if not project_ids:
        raise RuntimeError(f"project {PROJECT_KEY} is not on the connection's Jira site")
    named = [
        t
        for t in _listed(conn_id, "issuetype")
        if str(t.get("name") or t.get("Name") or "").casefold() == ISSUETYPE_NAME.casefold()
        and (t.get("id") or t.get("Id")) is not None
    ]

    def scope(t: dict) -> str:
        project = (t.get("scope") or {}).get("project") or {}
        return str(project.get("id") or project.get("Id") or "")

    chosen = [t for t in named if scope(t) == project_ids[0]] or [t for t in named if not scope(t)]
    if not chosen:
        raise RuntimeError(f"no {ISSUETYPE_NAME!r} issue type in project {PROJECT_KEY} on the connection's Jira site")
    _ISSUETYPE_IDS[conn_id] = str(chosen[0].get("id") or chosen[0].get("Id"))
    return _ISSUETYPE_IDS[conn_id]


def connection_id() -> str:
    folder_key = _run("or", "folders", "get", FOLDER_PATH)["Data"]["Key"]
    conns = _run("is", "connections", "list", CONNECTOR, "--folder-key", folder_key, "--refresh")["Data"]
    return next(c["Id"] for c in conns if c["Name"] == CONNECTION_NAME)


def create_issue(conn_id: str, summary: str) -> str:
    body = {"fields": {"project": {"key": PROJECT_KEY}, "issuetype": {"id": issuetype_id(conn_id)}, "summary": summary}}
    return _run(
        "is", "resources", "run", "create", CONNECTOR, "curated_create_issue",
        "--connection-id", conn_id, "--body", json.dumps(body),
    )["Data"]["key"]


def get_issue(conn_id: str, key: str) -> dict | None:
    """Return the issue's `fields` dict (includes `summary` and `comment`),
    or None if it doesn't exist (404)."""
    env = _run(
        "is", "resources", "run", "get", CONNECTOR, "curated_get_issue",
        "--connection-id", conn_id,
        "--query", f"project={PROJECT_KEY}&issuetype={issuetype_id(conn_id)}&issueId={key}",
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
