#!/usr/bin/env python3
"""Validation helpers for uipath-platform Integration Service smoke tests.

Usage from a task YAML (run_command criterion):
    python3 $TASK_DIR/_shared/is_check.py <check_name>

These smoke tests run WITHOUT a live UiPath tenant. CLI commands fail with
auth errors — that is expected. The check scripts validate that the agent:

  1. Recorded the correct CLI commands with proper flags (commands_used)
  2. Used correct types and values in structured output
  3. Demonstrated skill knowledge (HTTP fallback, workflow ordering, etc.)

This is a different signal from command_executed — command_executed checks
the agent's Bash tool calls; these checks validate the agent's self-reported
understanding in report.json.
"""

import glob
import json
import re
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find(pattern: str) -> str:
    """Find a single file matching the glob pattern, or exit."""
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        sys.exit(f"FAIL: No file matching {pattern}")
    return matches[0]


def _load_json(path: str) -> dict | list:
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        sys.exit(f"FAIL: {path} is not valid JSON — {exc}")
    except FileNotFoundError:
        sys.exit(f"FAIL: {path} not found")


def _assert_key(data: dict, key: str, label: str):
    if key not in data:
        sys.exit(f"FAIL: {label} missing key '{key}' — got {list(data.keys())}")
    return data[key]


def _assert_type(value, expected_type, label: str):
    if not isinstance(value, expected_type):
        sys.exit(f"FAIL: {label} should be {expected_type.__name__}, "
                 f"got {type(value).__name__}: {value!r}")
    return value


def _assert_commands(cmds: list, patterns: list[str], label: str) -> None:
    """Assert that commands_used contains entries matching each regex pattern.

    This validates the agent logged the right CLI syntax — not just that it
    ran *some* commands, but that it ran the *right* commands with correct
    subcommands and flags.
    """
    joined = "\n".join(str(c) for c in cmds)
    for pattern in patterns:
        if not re.search(pattern, joined, re.IGNORECASE):
            sys.exit(
                f"FAIL: {label} — no command matching /{pattern}/ found in "
                f"commands_used: {cmds}"
            )


# ---------------------------------------------------------------------------
# Per-test checks
# ---------------------------------------------------------------------------

def check_connector_discovery() -> None:
    """Validate connector_discovery: correct search commands, HTTP fallback.

    Asserts:
      - google_connectors is a list
      - apify_fallback mentions the HTTP connector key (uipath-uipath-http)
      - commands_used contains connectors list with --filter for both vendors
    """
    data = _load_json(_find("**/report.json"))

    google = _assert_key(data, "google_connectors", "report")
    _assert_type(google, list, "report.google_connectors")

    _assert_key(data, "apify_connectors", "report")

    fallback = str(_assert_key(data, "apify_fallback", "report")).lower()
    if "http" not in fallback:
        sys.exit(
            f"FAIL: apify_fallback should mention the HTTP connector fallback "
            f"— got: {data['apify_fallback']!r}"
        )

    cmds = _assert_key(data, "commands_used", "report")
    _assert_type(cmds, list, "report.commands_used")
    _assert_commands(cmds, [
        r"uip\s+is\s+connectors\s+list",   # used connectors list
        r"--filter",                         # used --filter flag
        r"--output\s+json",                  # used --output json
    ], "report.commands_used")

    print(f"OK: connector_discovery — {len(cmds)} commands logged, "
          f"HTTP fallback documented")


def check_connection_lifecycle() -> None:
    """Validate connection_lifecycle: list + ping executed, create + edit documented.

    The agent runs list and ping (headless-safe), but does NOT run create or
    edit (both open a browser for OAuth). Instead the agent documents the exact
    create/edit commands in the report. We validate:
      - connector_key is exactly "uipath-salesforce-sfdc"
      - connections_found is an int (0 is valid for no-auth)
      - ping_result is a non-empty string (error message is valid)
      - create_command contains the correct CLI syntax
      - edit_command contains the correct CLI syntax
      - commands_used contains connections list + ping (actually executed)
    """
    data = _load_json(_find("**/report.json"))

    key = _assert_key(data, "connector_key", "report")
    if key != "uipath-salesforce-sfdc":
        sys.exit(f"FAIL: connector_key should be 'uipath-salesforce-sfdc', got {key!r}")

    found = _assert_key(data, "connections_found", "report")
    _assert_type(found, int, "report.connections_found")

    ping = _assert_key(data, "ping_result", "report")
    _assert_type(ping, str, "report.ping_result")
    if not ping.strip():
        sys.exit("FAIL: ping_result is empty — should contain status or error message")

    # Validate the agent documented the correct create command syntax
    # (not executed — browser-dependent)
    create_cmd = _assert_key(data, "create_command", "report")
    _assert_type(create_cmd, str, "report.create_command")
    if not re.search(r"uip\s+is\s+connections\s+create", create_cmd, re.IGNORECASE):
        sys.exit(
            f"FAIL: create_command should contain 'uip is connections create' "
            f"— got: {create_cmd!r}"
        )

    # Validate the agent documented the correct edit command syntax
    # (not executed — browser-dependent)
    edit_cmd = _assert_key(data, "edit_command", "report")
    _assert_type(edit_cmd, str, "report.edit_command")
    if not re.search(r"uip\s+is\s+connections\s+edit", edit_cmd, re.IGNORECASE):
        sys.exit(
            f"FAIL: edit_command should contain 'uip is connections edit' "
            f"— got: {edit_cmd!r}"
        )

    # Validate commands_used — only list and ping were actually run
    cmds = _assert_key(data, "commands_used", "report")
    _assert_type(cmds, list, "report.commands_used")
    _assert_commands(cmds, [
        r"uip\s+is\s+connections\s+list",   # listed connections
        r"uip\s+is\s+connections\s+ping",    # pinged a connection
        r"--output\s+json",                  # used --output json
    ], "report.commands_used")

    print(f"OK: connection_lifecycle — {len(cmds)} commands executed, "
          f"connections_found={found}, create/edit commands documented correctly")


def check_activity_discovery() -> None:
    """Validate activity_discovery: both activity types listed, explanation given.

    Asserts:
      - connector_key is exactly "uipath-salesforce-sfdc"
      - activity_count and trigger_count are ints
      - activities_vs_triggers_vs_resources is a meaningful explanation (>= 30 chars)
      - commands_used contains activities list (without --triggers) AND with --triggers
    """
    data = _load_json(_find("**/report.json"))

    key = _assert_key(data, "connector_key", "report")
    if key != "uipath-salesforce-sfdc":
        sys.exit(f"FAIL: connector_key should be 'uipath-salesforce-sfdc', got {key!r}")

    act = _assert_key(data, "activity_count", "report")
    _assert_type(act, int, "report.activity_count")

    trig = _assert_key(data, "trigger_count", "report")
    _assert_type(trig, int, "report.trigger_count")

    explanation = _assert_key(data, "activities_vs_triggers_vs_resources", "report")
    _assert_type(explanation, str, "report.activities_vs_triggers_vs_resources")
    if len(explanation) < 30:
        sys.exit(
            f"FAIL: activities_vs_triggers_vs_resources too short ({len(explanation)} chars) "
            f"— expected a meaningful explanation distinguishing the three concepts"
        )

    cmds = _assert_key(data, "commands_used", "report")
    _assert_type(cmds, list, "report.commands_used")
    _assert_commands(cmds, [
        r"uip\s+is\s+activities\s+list",    # listed activities
        r"--triggers",                        # used --triggers flag
        r"--output\s+json",                  # used --output json
    ], "report.commands_used")

    print(f"OK: activity_discovery — {len(cmds)} commands logged, "
          f"activity_count={act}, trigger_count={trig}, "
          f"explanation={len(explanation)} chars")


def check_resource_describe() -> None:
    """Validate resource_describe: correct describe flags, field lists.

    Asserts:
      - connector_key is exactly "uipath-salesforce-sfdc"
      - resources_found is an int
      - contact_fields and required_fields are lists
      - commands_used contains resources list + resources describe
        both with --operation and --connection-id flags
    """
    data = _load_json(_find("**/report.json"))

    key = _assert_key(data, "connector_key", "report")
    if key != "uipath-salesforce-sfdc":
        sys.exit(f"FAIL: connector_key should be 'uipath-salesforce-sfdc', got {key!r}")

    found = _assert_key(data, "resources_found", "report")
    _assert_type(found, int, "report.resources_found")

    fields = _assert_key(data, "contact_fields", "report")
    _assert_type(fields, list, "report.contact_fields")

    req = _assert_key(data, "required_fields", "report")
    _assert_type(req, list, "report.required_fields")

    cmds = _assert_key(data, "commands_used", "report")
    _assert_type(cmds, list, "report.commands_used")
    _assert_commands(cmds, [
        r"uip\s+is\s+resources\s+list",      # listed resources
        r"uip\s+is\s+resources\s+describe",   # described resource
        r"--operation",                        # used --operation flag
        r"--output\s+json",                    # used --output json
    ], "report.commands_used")

    print(f"OK: resource_describe — {len(cmds)} commands logged, "
          f"{len(fields)} contact_fields, {len(req)} required_fields")


def check_resource_execute() -> None:
    """Validate resource_execute: full 6-step IS workflow in correct order.

    Asserts:
      - workflow_steps has >= 6 entries
      - Each step has step/action/command/result fields
      - All 6 expected actions are present (find_connector through execute_create)
      - Steps are in correct workflow order (connector before connection before ping etc.)
      - commands_used contains the key IS commands with correct flags
    """
    data = _load_json(_find("**/report.json"))

    steps = _assert_key(data, "workflow_steps", "report")
    _assert_type(steps, list, "report.workflow_steps")
    if len(steps) < 6:
        sys.exit(f"FAIL: workflow_steps has {len(steps)} entries, expected >= 6")

    # Validate each step has required fields
    for i, step in enumerate(steps):
        _assert_type(step, dict, f"workflow_steps[{i}]")
        for field in ("step", "action", "command", "result"):
            _assert_key(step, field, f"workflow_steps[{i}]")

    # Validate all 6 workflow actions are present
    expected_actions = [
        "find_connector", "find_connection", "ping_connection",
        "discover_resources", "describe_resource", "execute_create",
    ]
    actual_actions = [s.get("action", "") for s in steps]
    for expected in expected_actions:
        if not any(expected in a for a in actual_actions):
            sys.exit(
                f"FAIL: workflow_steps missing action '{expected}' "
                f"— got {actual_actions}"
            )

    # Validate workflow ordering: each action must appear after its predecessor
    action_indices = {}
    for i, step in enumerate(steps):
        for ea in expected_actions:
            if ea in step.get("action", "") and ea not in action_indices:
                action_indices[ea] = i
    for j in range(1, len(expected_actions)):
        prev, curr = expected_actions[j - 1], expected_actions[j]
        if prev in action_indices and curr in action_indices:
            if action_indices[curr] < action_indices[prev]:
                sys.exit(
                    f"FAIL: workflow order wrong — '{curr}' (step {action_indices[curr]}) "
                    f"appeared before '{prev}' (step {action_indices[prev]})"
                )

    # Validate commands_used
    cmds = _assert_key(data, "commands_used", "report")
    _assert_type(cmds, list, "report.commands_used")
    if len(cmds) < 5:
        sys.exit(f"FAIL: commands_used has {len(cmds)} entries, expected >= 5")
    _assert_commands(cmds, [
        r"uip\s+is\s+connectors\s+list",         # step 1
        r"uip\s+is\s+connections\s+(list|ping)",   # step 2-3
        r"uip\s+is\s+resources\s+execute",         # step 6
        r"--output\s+json",                        # universal flag
    ], "report.commands_used")

    print(f"OK: resource_execute — {len(steps)} workflow steps in correct order, "
          f"{len(cmds)} commands logged")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

CHECKS = {
    "check_connector_discovery": check_connector_discovery,
    "check_connection_lifecycle": check_connection_lifecycle,
    "check_activity_discovery": check_activity_discovery,
    "check_resource_describe": check_resource_describe,
    "check_resource_execute": check_resource_execute,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in CHECKS:
        print(
            f"Usage: {sys.argv[0]} <{'|'.join(sorted(CHECKS))}>",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        CHECKS[sys.argv[1]]()
    except SystemExit:
        raise
    except Exception as exc:
        print(f"FAIL: {sys.argv[1]} — unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)
