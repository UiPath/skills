#!/usr/bin/env python3
"""Live ``uipath-atlassian-jira`` helpers for the maestro-flow Jira e2e tasks.

Thin wrapper around ``uip is resources run`` (create / get / delete) against a
real Jira sandbox connection. Shared by:

- ``seed_jira.py``  (pre_run)  — write seed.json, optionally create a seed issue.
- ``teardown_jira.py`` (post_run) — delete the issues the task created.
- ``check_jira_*.py`` (grading) — re-read tenant state to prove the flow really
  hit Jira (not a fabricated output).

Connection-scope note
---------------------
The sandbox connection is scoped to the CURATED single-record operations only.
``curated_create_issue`` (create by body), ``curated_get_issue`` (retrieve by
id) and ``delete issue`` (by id) work; the broader Jira REST surface
(``issue_createmeta``, JQL ``/search``, ``list``) returns 401 "scope does not
match". Every helper here therefore keys off an EXACT issue id — never a
search/list. Teardown consequently deletes issues by known key, not by a JQL
label sweep.

Payload casing: ``uip is resources run --output json`` wraps results in a
``Data`` field (PascalCase); nested Jira fields are the provider's camelCase
(``fields``, ``summary``, ``key``). :func:`_data` reads the envelope
case-insensitively, mirroring the coded IS check.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any

CONNECTOR = "uipath-atlassian-jira"

# Canonical maestro-flow Jira sandbox targets. Override any via env for a
# different tenant/project (see seed_jira.py). These are non-secret pointers to
# the shared coder-eval sandbox, not credentials.
DEFAULT_FOLDER_PATH = "Shared/uipath-maestro-flow"
DEFAULT_CONNECTION_NAME = "is-sandboxes-test@uipath.com-uipath-sandbox-380"
DEFAULT_PROJECT_KEY = "CE"          # "Coder Eval" project on uipath-sandbox-380
DEFAULT_ISSUETYPE_ID = "11457"      # "Task" issue type, scoped to the CE project


class JiraError(RuntimeError):
    """Raised when a live Jira operation fails."""


def _uip(*args: str, timeout: int = 120) -> dict:
    """Run ``uip <args> --output json`` and return the parsed envelope.

    Raises :class:`JiraError` on process failure, non-JSON output, or a
    ``Result == "Failure"`` envelope.
    """
    uip = shutil.which("uip")
    if uip is None:
        raise JiraError("`uip` not on PATH — required for live Jira ops")
    proc = subprocess.run(
        [uip, *args, "--output", "json"],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    try:
        env = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise JiraError(
            f"`uip {' '.join(args)}` returned non-JSON (exit {proc.returncode}): "
            f"{e}; raw: {proc.stdout[:300]!r} {proc.stderr[:300]!r}"
        )
    if proc.returncode != 0 or (isinstance(env, dict) and env.get("Result") == "Failure"):
        msg = (env.get("Message") if isinstance(env, dict) else None) or proc.stderr or proc.stdout
        raise JiraError(f"`uip {' '.join(args)}` failed: {str(msg)[:400]}")
    return env


def _data(env: dict) -> Any:
    """Return the ``Data`` payload of an envelope, tolerant of casing."""
    if not isinstance(env, dict):
        return env
    for k in ("Data", "data"):
        if k in env:
            return env[k]
    return env


def resolve_folder_key(folder_path: str = DEFAULT_FOLDER_PATH) -> str:
    data = _data(_uip("or", "folders", "get", folder_path))
    key = data.get("Key") if isinstance(data, dict) else None
    if not key:
        raise JiraError(f"could not resolve folder key for {folder_path!r}: {data}")
    return key


def resolve_connection_id(
    connection_name: str = DEFAULT_CONNECTION_NAME,
    folder_path: str = DEFAULT_FOLDER_PATH,
) -> str:
    """Resolve a connection's id by name within a folder.

    Uses the control-plane ``uip is connections list`` (which — unlike the
    scope-limited data-plane ``is resources`` reads — works for this
    connection), then matches by ``Name``.
    """
    folder_key = resolve_folder_key(folder_path)
    env = _uip(
        "is", "connections", "list", CONNECTOR,
        "--folder-key", folder_key, "--refresh",
    )
    conns = _data(env)
    conns = conns if isinstance(conns, list) else []
    match = next((c for c in conns if c.get("Name") == connection_name), None)
    if not match:
        raise JiraError(
            f"connection {connection_name!r} not found in {folder_path!r} "
            f"(got {[c.get('Name') for c in conns]})"
        )
    conn_id = match.get("Id") or match.get("ConnectionId")
    if not conn_id:
        raise JiraError(f"connection {connection_name!r} has no Id: {match}")
    return conn_id


class Jira:
    """Bound live Jira client for one connection + project + issue type."""

    def __init__(self, connection_id: str, project_key: str, issuetype_id: str):
        self.connection_id = connection_id
        self.project_key = project_key
        self.issuetype_id = issuetype_id

    @classmethod
    def from_seed(cls, seed: dict) -> "Jira":
        conn_id = resolve_connection_id(
            seed.get("connection_name", DEFAULT_CONNECTION_NAME),
            seed.get("folder_path", DEFAULT_FOLDER_PATH),
        )
        return cls(
            connection_id=conn_id,
            project_key=seed.get("project_key", DEFAULT_PROJECT_KEY),
            issuetype_id=seed.get("issuetype_id", DEFAULT_ISSUETYPE_ID),
        )

    def create_issue(self, summary: str) -> str:
        """Create an issue in the bound project; return its key (e.g. ``CE-42``)."""
        body = {
            "fields": {
                "project": {"key": self.project_key},
                "issuetype": {"id": self.issuetype_id},
                "summary": summary,
            }
        }
        data = _data(_uip(
            "is", "resources", "run", "create", CONNECTOR, "curated_create_issue",
            "--connection-id", self.connection_id,
            "--body", json.dumps(body),
        ))
        key = data.get("key") or data.get("Key") if isinstance(data, dict) else None
        if not key:
            raise JiraError(f"create_issue returned no key: {data}")
        return key

    def get_issue(self, key: str) -> dict | None:
        """Return the ``fields`` dict for ``key``, or ``None`` if it 404s."""
        try:
            data = _data(_uip(
                "is", "resources", "run", "get", CONNECTOR, "curated_get_issue",
                "--connection-id", self.connection_id,
                "--query",
                f"project={self.project_key}&issuetype={self.issuetype_id}&issueId={key}",
            ))
        except JiraError as e:
            if "404" in str(e):
                return None
            raise
        if isinstance(data, dict):
            return data.get("fields") or data.get("Fields") or {}
        return {}

    def delete_issue(self, key: str) -> bool:
        """Delete ``key``. Returns True on delete or if already absent (404)."""
        try:
            _uip(
                "is", "resources", "run", "delete", CONNECTOR, "issue",
                "--connection-id", self.connection_id,
                "--query", f"issueId={key}",
            )
            return True
        except JiraError as e:
            if "404" in str(e):
                return True
            raise
