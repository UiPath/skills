#!/usr/bin/env python3
"""Minimal live Jira/Slack helper for this task — wraps `uip is resources run`.

Plays the role `jira_is.py` plays for the flow suite's escalation_jira_ticket
task: connection discovery, tenant rereads, and deletions, defined once so the
grader and the post_run teardown issue identical calls. CLI plumbing comes
from `_shared/bpmn_live.py`; this file holds only the task's tenant targets.

Assumes `uip` is on PATH and logged in and that the connections exist — this
is a tenant-gated e2e task.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Walk up to the directory that holds `_shared` so the import works regardless
# of how deep this task lives under tests/tasks/uipath-maestro-bpmn/.
_directory = os.path.dirname(os.path.abspath(__file__))
while _directory != os.path.dirname(_directory) and not os.path.isdir(
    os.path.join(_directory, "_shared")
):
    _directory = os.path.dirname(_directory)
sys.path.insert(0, _directory)

from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    delete_target_is_absent,
    get_ci,
    payload_data,
    run_cli,
)

JIRA_CONNECTOR = "uipath-atlassian-jira"
SLACK_CONNECTOR = "uipath-salesforce-slack"
CONNECTION_NAMES = {
    JIRA_CONNECTOR: "is-sandboxes-test@uipath.com-uipath-sandbox-380",
    SLACK_CONNECTOR: "is-sandboxes",
}
# Shared/uipath-maestro-flow — the folder every escalation e2e's connections
# live in, matched by key because `connections list` reports keys, not paths.
CONNECTION_FOLDER_KEY = "5da18ec0-7de1-4e57-aaf1-ddc8a369c199"
JIRA_PROJECT_KEY = "CE"  # "Coder Eval" project on uipath-sandbox-380
JIRA_ISSUE_TYPE_ID = "11457"  # "Task" issue type, scoped to the CE project
SLACK_CHANNEL_ID = "C01H4SPS77W"
EXPECTED_LIVE_TARGET = {
    "BaseUrl": "https://alpha.uipath.com",
    "Organization": "codereval",
    "Tenant": "DefaultTenant",
}

# Flat cleanup journal in the sandbox CWD, one JSON record per line the moment
# a resource id is visible — post_run replays it even if the grader is
# SIGKILLed. Follows the `.created_keys` precedent in the flow suite.
JOURNAL = Path(".created-ids.jsonl")


def assert_live_target() -> dict[str, str]:
    """Refuse to run against anything but the Alpha codereval tenant."""

    completed = run_cli(["uip", "login", "status"], timeout=60)
    _payload, data = payload_data(completed, "read active UiPath login")
    if not isinstance(data, dict):
        raise CheckFailure("UiPath login status returned no data object")
    if str(get_ci(data, "Status", "")).casefold() != "logged in":
        raise CheckFailure("UiPath CLI is not logged in")
    actual = {
        key: str(get_ci(data, key, "")).rstrip("/")
        for key in EXPECTED_LIVE_TARGET
    }
    expected = {
        key: value.rstrip("/") for key, value in EXPECTED_LIVE_TARGET.items()
    }
    if actual != expected:
        raise CheckFailure(
            f"live grader must target {expected}, active profile is {actual}"
        )
    return expected


def connection_ids() -> dict[str, str]:
    """Resolve the enabled Jira and Slack connection ids, scoped by folder."""

    listed = run_cli(
        ["uip", "is", "connections", "list", "--all-folders"],
        timeout=180,
    )
    _payload, rows = payload_data(listed, "discover connector connections")
    if not isinstance(rows, list):
        raise CheckFailure("connector discovery returned no list")
    ids: dict[str, str] = {}
    for connector_key, name in CONNECTION_NAMES.items():
        matches = [
            row
            for row in rows
            if isinstance(row, dict)
            and get_ci(row, "ConnectorKey") == connector_key
            and get_ci(row, "Name") == name
            and get_ci(row, "FolderKey") == CONNECTION_FOLDER_KEY
            and str(get_ci(row, "State") or "").casefold() == "enabled"
        ]
        if len(matches) != 1:
            raise CheckFailure(
                f"expected one enabled {connector_key} connection named "
                f"{name!r}, found {len(matches)}"
            )
        identifier = get_ci(matches[0], "Id")
        if not isinstance(identifier, str):
            raise CheckFailure(f"{connector_key} connection has no id")
        ids[connector_key] = identifier
    return ids


def get_issue_fields(connection_id: str, issue_key: str) -> dict:
    """Re-read a Jira issue from the tenant; return its `fields` object."""

    fetched = run_cli(
        [
            "uip",
            "is",
            "resources",
            "run",
            "get",
            JIRA_CONNECTOR,
            "issue",
            "--connection-id",
            connection_id,
            "--query",
            json.dumps({"issueId": issue_key}, separators=(",", ":")),
        ],
        timeout=120,
    )
    _payload, data = payload_data(fetched, f"read Jira issue {issue_key}")
    if not isinstance(data, dict) or get_ci(data, "key") != issue_key:
        raise CheckFailure(
            f"Jira read did not return issue {issue_key!r}: {data!r}"
        )
    fields = get_ci(data, "fields")
    if not isinstance(fields, dict):
        raise CheckFailure(f"Jira issue {issue_key} returned no fields object")
    return fields


def delete_jira_issue(connection_id: str, issue_id: str) -> bool:
    """Delete an issue by key/id. True only when deletion is CONFIRMED —
    a success envelope or an issue-specific not-found (already gone)."""

    completed = run_cli(
        [
            "uip",
            "is",
            "resources",
            "run",
            "delete",
            JIRA_CONNECTOR,
            "issue",
            "--connection-id",
            connection_id,
            "--query",
            json.dumps({"issueId": issue_id}, separators=(",", ":")),
            "--yes",
        ],
        timeout=120,
    )
    try:
        payload_data(completed, f"delete Jira issue {issue_id}")
        return True
    except CheckFailure:
        return delete_target_is_absent(completed, "jira issue", issue_id)


def delete_slack_message(
    connection_id: str, channel_id: str, timestamp: str
) -> bool:
    """Delete one bot message. Same confirmed-deletion contract as Jira."""

    completed = run_cli(
        [
            "uip",
            "is",
            "resources",
            "run",
            "delete",
            SLACK_CONNECTOR,
            "ChatDeleteTimestamp_POST",
            "--connection-id",
            connection_id,
            "--query",
            json.dumps(
                {"conversationId": channel_id, "timestampId": timestamp},
                separators=(",", ":"),
            ),
            "--yes",
        ],
        timeout=120,
    )
    try:
        payload_data(completed, f"delete Slack message {timestamp}")
        return True
    except CheckFailure:
        return delete_target_is_absent(completed, "slack message", timestamp)


def record_created_id(kind: str, value) -> None:
    """Append a created resource id to the cleanup journal, immediately."""

    try:
        with JOURNAL.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"kind": kind, "value": value}) + "\n")
    except OSError:
        pass  # journalling is a cleanup backstop; never fail grading over it


def read_journal(path: Path = JOURNAL) -> dict[str, list]:
    """Parse the journal back into {kind: [values]}; tolerant of bad lines."""

    records: dict[str, list] = {}
    if not path.is_file():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = record.get("kind")
        value = record.get("value")
        if isinstance(kind, str) and value is not None:
            records.setdefault(kind, []).append(value)
    return records
