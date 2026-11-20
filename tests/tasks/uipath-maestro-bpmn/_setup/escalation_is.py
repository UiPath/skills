#!/usr/bin/env python3
"""Live Jira and Slack helper shared by the escalation e2e tasks.

Holds the tenant targets, connection discovery, Jira reads and deletes, Slack
deletes, and the cleanup journal helpers (`record_created_id`,
`journal_slack_posts`, `journal_slack_posts_in_log`) the graders and the
post_run teardown share. CLI plumbing comes from `_shared/bpmn_live.py`.

Assumes `uip` is on PATH and logged in and that the connections exist — this
is a tenant-gated e2e task.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
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
    element_output_records,
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
# The folder every escalation e2e's connections live in. Matched by name, as
# the flow suite does: each `connections list` row carries both `Folder` and
# `FolderKey`, so the key is read off the matched row rather than committed.
FOLDER_PATH = "Shared/uipath-maestro-flow"
FOLDER_NAME = "uipath-maestro-flow"  # leaf of the path, as reported
PROJECT_KEY = "CE"  # "Coder Eval" project on uipath-sandbox-380
ISSUETYPE_NAME = "Task"  # its id is per site and per project, so it is read at run time
# The flow suite's identified target on this same connection
# (the flow suite's escalation_slack_alert checker).
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing
SLACK_TS_RE = re.compile(r"^\d{9,11}\.\d{4,6}$")
SLACK_JOURNAL_KIND = "slack_message"
# The run's eval target, keyed by the `uip login status` field it must match.
# The pipeline exports these per run (a fresh org and tenant on ETE and
# provisioned runs), and coder-eval's default env_passthrough forwards them
# into the sandbox. The agent can re-login the shared session; it cannot
# change the grader's environment.
TARGET_ENV = {
    "BaseUrl": "UIPATH_URL",
    "OrganizationId": "UIPATH_ORGANIZATION_ID",
    "TenantId": "UIPATH_TENANT_ID",
}

# Flat cleanup journal in the sandbox CWD, one JSON record per line the moment
# a resource id is visible — post_run replays it even if the grader is
# SIGKILLed. Follows the `.created_keys` precedent in the flow suite.
JOURNAL = Path(".created-ids.jsonl")

# Per-call budgets for the live CLI steps this module contributes to the
# behavior criterion. The criterion's `timeout:` must cover their sum plus the
# checker's own steps -- test_behavior_checker.py asserts exactly that, so
# raising one of these without raising the criterion is a test failure, not a
# surprise timeout kill mid-cleanup.
LOGIN_STATUS_TIMEOUT = 30
CONNECTIONS_LIST_TIMEOUT = 120
JIRA_READ_TIMEOUT = 120
JIRA_DELETE_TIMEOUT = 120
SLACK_DELETE_TIMEOUT = 120

STEP_TIMEOUTS = (
    LOGIN_STATUS_TIMEOUT,
    CONNECTIONS_LIST_TIMEOUT,
    JIRA_READ_TIMEOUT,
    JIRA_DELETE_TIMEOUT,
    SLACK_DELETE_TIMEOUT,
)

# The post_run journal sweep is the ONLY cleanup that survives coder_eval
# SIGKILLing the graded command, so its worst case must fit inside its
# post_run `timeout:` -- which coder_eval caps at 300 (tasks.py: le=300).
# It therefore runs on its own tighter per-call budgets: one connection
# lookup, then per Jira issue a delete + one retry + a confirming reread, and
# per Slack message a delete + one retry.
TEARDOWN_CONNECTIONS_TIMEOUT = 60
TEARDOWN_DELETE_TIMEOUT = 45
TEARDOWN_READ_TIMEOUT = 45
POST_RUN_TIMEOUT_CAP = 300  # coder_eval models/tasks.py: Field(ge=1, le=300)

TEARDOWN_TIMEOUT = (
    TEARDOWN_CONNECTIONS_TIMEOUT
    + 2 * TEARDOWN_DELETE_TIMEOUT
    + TEARDOWN_READ_TIMEOUT
    + 2 * TEARDOWN_DELETE_TIMEOUT
)
# The sweep stops starting uip calls once the next one could outlast this, so
# it exits on its own before coder_eval kills it at POST_RUN_TIMEOUT_CAP.
TEARDOWN_BUDGET = POST_RUN_TIMEOUT_CAP - 10


def _now() -> float:
    return time.monotonic()


class TeardownClock:
    """Wall-clock budget for the post_run sweep."""

    def __init__(self, budget: float | None = None) -> None:
        self._budget = TEARDOWN_BUDGET if budget is None else budget
        self._start = _now()

    def remaining(self) -> float:
        return self._budget - (_now() - self._start)

    def allows(self, call_timeout: float) -> bool:
        """True when a call that may take `call_timeout` still fits the budget."""
        return _now() - self._start + call_timeout <= self._budget


def _normalize_target_value(value: object) -> str:
    return str(value or "").strip().rstrip("/").casefold()


def configured_target() -> dict[str, str]:
    """Read the run's eval target from the environment; refuse when unset."""

    missing = [
        name for name in TARGET_ENV.values() if not os.environ.get(name, "").strip()
    ]
    if missing:
        raise CheckFailure(
            f"no configured eval target: {missing} not set, so the live "
            "grader refuses to create Jira issues and Slack messages; export "
            "them for the eval tenant"
        )
    return {
        key: _normalize_target_value(os.environ[name])
        for key, name in TARGET_ENV.items()
    }


def assert_live_target() -> dict[str, str]:
    """Refuse to run unless the active `uip` session is the configured target."""

    expected = configured_target()
    completed = run_cli(["uip", "login", "status"], timeout=LOGIN_STATUS_TIMEOUT)
    _payload, data = payload_data(completed, "read active UiPath login")
    if not isinstance(data, dict):
        raise CheckFailure("UiPath login status returned no data object")
    if str(get_ci(data, "Status", "")).casefold() != "logged in":
        raise CheckFailure("UiPath CLI is not logged in")
    actual = {
        key: _normalize_target_value(get_ci(data, key, "")) for key in TARGET_ENV
    }
    if actual != expected:
        raise CheckFailure(
            f"live grader must target {expected}, active profile is {actual}"
        )
    return expected


def connection_ids(
    *, timeout: int = CONNECTIONS_LIST_TIMEOUT, connectors: tuple[str, ...] | None = None
) -> dict[str, str]:
    """Resolve the enabled Jira and Slack connection ids, scoped by folder.

    `connectors` limits resolution to those connector keys (default: both)."""

    listed = run_cli(
        ["uip", "is", "connections", "list", "--all-folders", "--refresh"],
        timeout=timeout,
    )
    _payload, rows = payload_data(listed, "discover connector connections")
    if not isinstance(rows, list):
        raise CheckFailure("connector discovery returned no list")
    ids: dict[str, str] = {}
    for connector_key, name in CONNECTION_NAMES.items():
        if connectors is not None and connector_key not in connectors:
            continue
        by_name = [
            row
            for row in rows
            if isinstance(row, dict)
            and get_ci(row, "ConnectorKey") == connector_key
            and get_ci(row, "Name") == name
            and str(get_ci(row, "State") or "").casefold() == "enabled"
        ]
        matches = [row for row in by_name if get_ci(row, "Folder") == FOLDER_NAME]
        # Accept a name-only match only when NO candidate reports folder
        # metadata (older CLI / env). If folders ARE reported but none is the
        # target folder, refuse to guess -- a same-named connection elsewhere
        # could be the wrong account. Mirrors the flow suite's connection_id().
        if not matches and by_name and not any(get_ci(row, "Folder") for row in by_name):
            matches = by_name
        if len(matches) != 1:
            folders = [get_ci(row, "Folder") for row in by_name]
            raise CheckFailure(
                f"expected one enabled {connector_key} connection named "
                f"{name!r} in folder {FOLDER_PATH!r}, found {len(matches)}"
                f"; candidates in folders {folders}"
            )
        identifier = get_ci(matches[0], "Id")
        if not isinstance(identifier, str):
            raise CheckFailure(f"{connector_key} connection has no id")
        ids[connector_key] = identifier
    return ids


def _jira_records(connection_id: str, resource: str) -> list[dict]:
    """The records of a Jira `run list` answer: a list, a wrapper's list, or one record."""
    listed = run_cli(
        ["uip", "is", "resources", "run", "list", JIRA_CONNECTOR, resource, "--connection-id", connection_id],
        timeout=JIRA_READ_TIMEOUT,
    )
    _payload, data = payload_data(listed, f"list Jira {resource}")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        if not any(data.get(field) for field in ("id", "Id", "key")):
            held = [item for value in data.values() if isinstance(value, list) for item in value]
            if held:
                return [item for item in held if isinstance(item, dict)]
        return [data]
    return []


def issuetype_id(connection_id: str) -> str:
    """The id of the Task issue type in PROJECT_KEY on the connection's Jira site.

    A project-scoped type wins; a global type counts only when the project has none."""
    project_ids = [
        str(get_ci(p, "id"))
        for p in _jira_records(connection_id, "project")
        if str(get_ci(p, "key") or "").casefold() == PROJECT_KEY.casefold() and get_ci(p, "id")
    ]
    if not project_ids:
        raise CheckFailure(f"project {PROJECT_KEY} is not on the connection's Jira site")
    named = [
        t
        for t in _jira_records(connection_id, "issuetype")
        if str(get_ci(t, "name") or "").casefold() == ISSUETYPE_NAME.casefold() and get_ci(t, "id") is not None
    ]

    def scope(t: dict) -> str:
        project = (t.get("scope") or {}).get("project") or {}
        return str(project.get("id") or "")

    chosen = [t for t in named if scope(t) == project_ids[0]] or [t for t in named if not scope(t)]
    if not chosen:
        raise CheckFailure(f"no {ISSUETYPE_NAME!r} issue type in project {PROJECT_KEY} on the connection's Jira site")
    return str(get_ci(chosen[0], "id"))


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
        timeout=JIRA_READ_TIMEOUT,
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


def delete_jira_issue(
    connection_id: str, issue_id: str, *, timeout: int = JIRA_DELETE_TIMEOUT
) -> bool:
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
        timeout=timeout,
    )
    try:
        payload_data(completed, f"delete Jira issue {issue_id}")
        return True
    except CheckFailure:
        return delete_target_is_absent(completed, "jira issue", issue_id)


def jira_issue_absent(
    connection_id: str, issue_key: str, *, timeout: int = JIRA_READ_TIMEOUT
) -> bool:
    """True ONLY when a tenant read CONFIRMS the issue is gone.

    False when it still exists OR when the read itself failed (transient 5xx /
    auth), so teardown never treats an ambiguous read as proof of deletion.
    Mirrors the flow suite's `issue_absent`; distinct from `get_issue_fields`,
    which raises on every failure alike.
    """

    completed = run_cli(
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
        timeout=timeout,
    )
    try:
        payload_data(completed, f"read Jira issue {issue_key}")
        return False  # a successful read means the issue still exists
    except CheckFailure:
        return delete_target_is_absent(completed, "jira issue", issue_key)


def delete_slack_message(
    connection_id: str,
    channel_id: str,
    timestamp: str,
    *,
    timeout: int = SLACK_DELETE_TIMEOUT,
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
        timeout=timeout,
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


def is_target_slack_post(channel: object, timestamp: object) -> bool:
    """True only for a message in the eval's own Slack channel with a real ts."""

    return (
        channel == SLACK_CHANNEL
        and isinstance(timestamp, str)
        and bool(SLACK_TS_RE.match(timestamp.strip()))
    )


def journal_slack_posts(variables_data, element_ids) -> None:
    """Journal the channel and ts each of these Slack steps returned in this run."""

    for record in element_output_records(variables_data, tuple(sorted(element_ids))):
        response = get_ci(record, "response")
        if not isinstance(response, dict):
            continue
        channel, timestamp = get_ci(response, "channel"), get_ci(response, "ts")
        if is_target_slack_post(channel, timestamp):
            record_created_id("slack_message", [channel, timestamp.strip()])


def _slack_responses(value) -> list[tuple[str, str]]:
    """(channel, ts) of every Slack post response found in `value`: an object
    holding a channel, a ts and the posted `message`."""

    if isinstance(value, str):
        return _slack_responses_in(value)
    if isinstance(value, list):
        return [pair for item in value for pair in _slack_responses(item)]
    if not isinstance(value, dict):
        return []

    channel, timestamp = get_ci(value, "channel"), get_ci(value, "ts")
    own = []
    if (
        is_target_slack_post(channel, timestamp)
        and isinstance(get_ci(value, "message"), dict)
    ):
        own = [(channel, timestamp.strip())]
    return own + [pair for item in value.values() for pair in _slack_responses(item)]


def _slack_responses_in(text: str) -> list[tuple[str, str]]:
    decoder = json.JSONDecoder()
    found: list[tuple[str, str]] = []
    index = text.find("{")
    while index != -1:
        try:
            value, end = decoder.raw_decode(text, index)
        except (ValueError, RecursionError):
            index = text.find("{", index + 1)
            continue
        found += _slack_responses(value)
        index = text.find("{", end)
    return found


def journal_slack_posts_in_log(log_file: Path, *payloads) -> None:
    """Journal the Slack posts this run's log and payloads show, for a run that
    died before its variables could be read. Only a response object with a
    channel, a ts and the posted message counts."""

    texts = [log_file.read_text(encoding="utf-8", errors="replace")] if log_file.is_file() else []
    texts += [json.dumps(payload, default=str) for payload in payloads if payload is not None]
    known = {tuple(value) for value in read_journal().get(SLACK_JOURNAL_KIND, [])}
    for text in texts:
        for pair in dict.fromkeys(_slack_responses_in(text)):
            if pair in known:
                continue
            known.add(pair)
            record_created_id(SLACK_JOURNAL_KIND, list(pair))


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
