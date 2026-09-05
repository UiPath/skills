#!/usr/bin/env python3
"""OutlookTriggerInbox: regression test for PR #348 — reference-ID reuse.

Two checks:

  check_trigger_node      Structural — flow contains the email-received trigger.
  check_folder_binding    Structural — trigger binds both an Outlook connection
                          and a non-empty MailFolder reference.
  check_folder_id_fresh   Regression — parentFolderId written into the flow is
                          a live MailFolder ID on the currently-bound Outlook
                          connection. Catches "agent resolved-but-reused a
                          stale ID" (the `command_executed` check in the YAML
                          catches "agent skipped the resolve entirely").
                          Reports three causes separately: dead connection,
                          displayName written instead of id, stale id.

A `flow debug` check is intentionally omitted from this task — see the task
YAML description for the infrastructure rationale.

Privacy: never logs folder display names, nor the configured reference value
(which may itself be a name). Only counts and lengths.
"""

import json
import subprocess
import os
import sys
from pathlib import Path

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-flow")
    if os.environ.get("SKILLS_REPO_PATH")
    else str(Path(__file__).resolve().parents[2])
)
sys.path.insert(0, _shared_root)
from _shared.flow_check import find_flow_file  # noqa: E402

CONNECTOR_KEY = "uipath-microsoft-outlook365"
TRIGGER_TYPE_MARKER = "uipath.connector.trigger.uipath-microsoft-outlook365.email-received"
TEST_FOLDER_PATH = "Shared/uipath-maestro-flow"


# Credential failures: the tenant's grant, not anything the agent built.
_CONNECTION_DEAD_MARKERS = (
    "invalid_grant",
    "aadsts50173",  # grant revoked
    "aadsts700082",  # refresh token expired
    "reauthorize your account",
)


def _connection_is_dead(blob: str) -> bool:
    lowered = blob.lower()
    return any(marker in lowered for marker in _CONNECTION_DEAD_MARKERS)


def _dead_credential_remedy(args: list[str]) -> str:
    """Which credential to reauthorize. The MailFolder resolve runs on the
    Outlook connection's grant; every other call in this checker (`or folders
    get`, `is connections list`) runs on the CLI's own session. Both are
    environment failures, but they are fixed in different places, so a dead CLI
    login must not be reported as a dead Outlook connection."""
    if "resources" in args:
        return (
            "The tenant's Outlook connection cannot authenticate, so no MailFolder ID "
            "can be resolved and this task's assertion never ran. Reauthorize the "
            f"connection in {TEST_FOLDER_PATH} and re-run"
        )
    return (
        "The CLI's own session cannot authenticate, so this checker never reached the "
        "MailFolder resolve. Re-run `uip login` and re-run this task"
    )


def _parse_uip_stdout(args: list[str], result: subprocess.CompletedProcess) -> dict:
    if result.returncode != 0:
        blob = f"{result.stdout}\n{result.stderr}"
        if _connection_is_dead(blob):
            sys.exit(
                f"FAIL (ENVIRONMENT, not a skill regression): {' '.join(args)} "
                f"exit={result.returncode}. {_dead_credential_remedy(args)}; do not "
                "read this as the agent reusing or inventing an ID.\n"
                f"stderr: {result.stderr}\nstdout: {result.stdout}"
            )
        sys.exit(
            f"FAIL: {' '.join(args)} exit={result.returncode}\n"
            f"stderr: {result.stderr}\nstdout: {result.stdout}"
        )
    # Strip any CLI banner lines preceding the JSON body
    out = result.stdout
    idx = out.find("{")
    if idx < 0:
        sys.exit(f"FAIL: no JSON in stdout of {' '.join(args)}\n{out}")
    try:
        return json.loads(out[idx:])
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: JSON parse error on {' '.join(args)}: {e}\n{out}")


def _uip_json(args: list[str]) -> dict:
    """Run a uip CLI command and return parsed JSON. Fails the test on
    non-zero exit or invalid JSON."""
    return _parse_uip_stdout(args, subprocess.run(args, capture_output=True, text=True, timeout=120))


def _uip_resources_run(tail_args: list[str]) -> dict:
    """Invoke ``uip is resources <verb> <tail...>`` tolerating both the
    post-rename verb (``run``, current) and the legacy verb (``execute``).

    Sandboxes can carry either CLI version depending on which
    @uipath/integrationservice-tool install ranks first in Node's
    parent-walking module resolution. The fallback on
    ``unknown command 'run'`` keeps the checker green across both shapes
    until the sandbox PATH is fully isolated (see coder_eval companion
    PR).
    """
    primary = ["uip", "is", "resources", "run", *tail_args]
    result = subprocess.run(primary, capture_output=True, text=True, timeout=120)
    needs_fallback = (
        result.returncode != 0
        and "unknown command 'run'" in (result.stdout + result.stderr)
    )
    if needs_fallback:
        legacy = ["uip", "is", "resources", "execute", *tail_args]
        result = subprocess.run(legacy, capture_output=True, text=True, timeout=120)
        return _parse_uip_stdout(legacy, result)
    return _parse_uip_stdout(primary, result)


def _read_flow() -> tuple[dict, str]:
    path = find_flow_file(flow_glob="OutlookTriggerInbox*.flow")
    with open(path) as f:
        return json.load(f), path


def _find_test_folder_key() -> str:
    resp = _uip_json(["uip", "or", "folders", "get", TEST_FOLDER_PATH, "--output", "json"])
    key = resp.get("Data", {}).get("Key")
    if not key:
        sys.exit(f"FAIL: no '{TEST_FOLDER_PATH}' folder in Orchestrator")
    return key


def _bound_connection_id(trigger: dict) -> str:
    """The connection the trigger is actually bound to, from its persisted
    ``inputs.detail.connectionId``. `node configure` requires the field, so it
    is present on any flow that validated. Falling back to the folder's default
    connection would validate the ID against the wrong grant whenever the two
    differ — a dead default would then mask a healthy bound connection."""
    detail = trigger.get("inputs", {}).get("detail", {}) or {}
    conn_id = detail.get("connectionId")
    return conn_id if isinstance(conn_id, str) and conn_id.strip() else ""


def _find_default_outlook_connection() -> tuple[str, str, str]:
    """Return (connection_id, folder_key, connection_name) for the default
    enabled Outlook connection in the test folder."""
    folder_key = _find_test_folder_key()
    conns_raw = _uip_json(
        [
            "uip", "is", "connections", "list", CONNECTOR_KEY,
            "--folder-key", folder_key, "--output", "json",
        ]
    ).get("Data", [])
    if not isinstance(conns_raw, list) or not conns_raw:
        sys.exit(
            f"FAIL: no {CONNECTOR_KEY} connection in folder {TEST_FOLDER_PATH}. "
            f"Provision an Outlook connection in the test tenant first."
        )
    defaults = [c for c in conns_raw if c.get("IsDefault") == "Yes" and c.get("State") == "Enabled"]
    chosen = defaults[0] if defaults else conns_raw[0]
    return chosen["Id"], folder_key, chosen.get("Name", "")


def _find_trigger_node(flow: dict) -> dict:
    for n in flow.get("nodes", []):
        if TRIGGER_TYPE_MARKER in n.get("type", ""):
            return n
    sys.exit(
        f"FAIL: no trigger node with type containing {TRIGGER_TYPE_MARKER!r}; "
        f"types seen: {sorted({n.get('type') for n in flow.get('nodes', [])})}"
    )


def _extract_list_items(resp: dict) -> list[dict]:
    """resources run list returns Data shaped as either {items: [...], Pagination: ...}
    or a plain list. Handle both."""
    data = resp.get("Data", [])
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        return [x for x in (data.get("items") or data.get("Items") or []) if isinstance(x, dict)]
    return []


# ── subcommand: check_trigger_node ─────────────────────────────────────
def check_trigger_node():
    flow, _ = _read_flow()
    _find_trigger_node(flow)
    print("OK: Outlook email-received trigger node present")


def check_folder_binding():
    flow, _ = _read_flow()
    trigger = _find_trigger_node(flow)
    detail = trigger.get("inputs", {}).get("detail", {}) or {}
    connection_id = detail.get("connectionId")
    parent_folder_id = (detail.get("eventParameters") or {}).get("parentFolderId")
    if not connection_id:
        sys.exit("FAIL: trigger.inputs.detail.connectionId is missing")
    if not parent_folder_id:
        sys.exit("FAIL: trigger.inputs.detail.eventParameters.parentFolderId is missing")
    print("OK: Outlook connection and MailFolder reference are both bound")


# ── subcommand: check_folder_id_fresh ──────────────────────────────────
def check_folder_id_fresh():
    flow, _ = _read_flow()
    trigger = _find_trigger_node(flow)
    ep = trigger.get("inputs", {}).get("detail", {}).get("eventParameters", {}) or {}
    flow_folder_id = ep.get("parentFolderId")
    if not flow_folder_id:
        sys.exit(
            "FAIL: trigger.inputs.detail.eventParameters.parentFolderId is missing. "
            "The agent did not configure the required reference field."
        )

    # Prefer the trigger's own binding; fall back to the folder default only
    # when the flow never persisted one.
    conn_id = _bound_connection_id(trigger) or _find_default_outlook_connection()[0]
    live = _uip_resources_run(
        ["list", CONNECTOR_KEY, "MailFolder", "--connection-id", conn_id, "--output", "json"]
    )
    # Read the item id case-insensitively (a CLI that PascalCases --output json
    # keys per PR #2266 emits `Id`, not `id`) and drop any None so a missed key
    # can't collapse the set to `{None}` and falsely accuse the agent.
    live_ids = {
        fid
        for f in _extract_list_items(live)
        if (fid := (f.get("id") or f.get("Id")))
    }
    if not live_ids:
        sys.exit(
            "FAIL: resources run/execute list MailFolder returned no folders on the bound connection"
        )

    if flow_folder_id in live_ids:
        print(f"OK: parentFolderId resolves on current connection ({len(live_ids)} folders checked)")
        return

    # describe declares Reference{LookupNames:["displayName"], LookupValue:"id"},
    # so a display name here means the resolve was skipped, not a stale id.
    live_names = {
        name.lower()
        for f in _extract_list_items(live)
        if (name := (f.get("displayName") or f.get("DisplayName")))
    }
    if flow_folder_id.lower() in live_names:
        sys.exit(
            "FAIL: parentFolderId holds a folder's displayName, not its id. The field "
            "is a reference (LookupNames=[displayName], LookupValue=id), so the agent "
            "must write the `id` returned by `resources run list MailFolder`. This is a "
            "skipped or failed resolve, NOT the PR #348 stale-reference regression."
        )

    # The configured value is never echoed, not even truncated: reaching here
    # means it matched no live id AND no live display name, so it can still BE a
    # display name (a renamed or deleted folder, or one past the returned page).
    # Report its shape instead.
    sys.exit(
        f"FAIL (PR #348 regression): the configured parentFolderId ({len(flow_folder_id)} chars) "
        f"is not among the {len(live_ids)} MailFolder IDs on the bound connection, and is not "
        "one of their display names either. The agent reused a reference ID from another "
        "connection or session."
    )


DISPATCH = {
    "check_trigger_node": check_trigger_node,
    "check_folder_binding": check_folder_binding,
    "check_folder_id_fresh": check_folder_id_fresh,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.exit(f"usage: {sys.argv[0]} {{{'|'.join(DISPATCH)}}}")
    DISPATCH[sys.argv[1]]()


if __name__ == "__main__":
    main()
