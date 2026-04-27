#!/usr/bin/env python3
"""OutlookTriggerInbox: regression test for PR #348 — reference-ID reuse.

Two checks:

  check_trigger_node      Structural — flow contains the email-received trigger.
  check_folder_id_fresh   Regression — parentFolderId written into the flow is
                          a live MailFolder ID on the currently-bound Outlook
                          connection. Catches "agent resolved-but-reused a
                          stale ID" (the `command_executed` check in the YAML
                          catches "agent skipped the resolve entirely").

A `flow debug` check is intentionally omitted from this task — see the task
YAML description for the infrastructure rationale.

Privacy: never logs folder display names. Only counts + truncated IDs.
"""

import glob
import json
import os
import subprocess
import sys

CONNECTOR_KEY = "uipath-microsoft-outlook365"
TRIGGER_TYPE_MARKER = "uipath.connector.trigger.uipath-microsoft-outlook365.email-received"
SHARED_FOLDER_PATH = "Shared"


def _uip_json(args: list[str]) -> dict:
    """Run a uip CLI command and return parsed JSON. Fails the test on
    non-zero exit or invalid JSON."""
    result = subprocess.run(args, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
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


def _read_flow() -> tuple[dict, str]:
    flows = glob.glob("**/OutlookTriggerInbox*.flow", recursive=True)
    if not flows:
        sys.exit("FAIL: no OutlookTriggerInbox*.flow found under cwd")
    with open(flows[0]) as f:
        return json.load(f), flows[0]


def _find_shared_folder_key() -> str:
    folders = _uip_json(["uip", "or", "folders", "list", "--output", "json"]).get("Data", [])
    for f in folders:
        if f.get("Path") == SHARED_FOLDER_PATH:
            return f["Key"]
    sys.exit(f"FAIL: no '{SHARED_FOLDER_PATH}' folder in Orchestrator")


def _find_default_outlook_connection() -> tuple[str, str, str]:
    """Return (connection_id, folder_key, connection_name) for the default
    enabled Outlook connection in Shared."""
    folder_key = _find_shared_folder_key()
    conns_raw = _uip_json(
        [
            "uip", "is", "connections", "list", CONNECTOR_KEY,
            "--folder-key", folder_key, "--output", "json",
        ]
    ).get("Data", [])
    if not isinstance(conns_raw, list) or not conns_raw:
        sys.exit(
            f"FAIL: no {CONNECTOR_KEY} connection in folder {SHARED_FOLDER_PATH}. "
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
    """execute list returns Data shaped as either {items: [...], Pagination: ...}
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

    conn_id, _folder_key, _conn_name = _find_default_outlook_connection()
    live = _uip_json(
        [
            "uip", "is", "resources", "execute", "list", CONNECTOR_KEY, "MailFolder",
            "--connection-id", conn_id, "--output", "json",
        ]
    )
    live_ids = {f.get("id") for f in _extract_list_items(live)}
    if not live_ids:
        sys.exit("FAIL: execute list MailFolder returned no folders on the bound connection")

    if flow_folder_id not in live_ids:
        # Truncate the IDs in the error to avoid leaking full Exchange IDs while
        # still giving enough signal to diagnose.
        sys.exit(
            f"FAIL (PR #348 regression): parentFolderId={flow_folder_id[:12]}... is NOT among "
            f"the {len(live_ids)} MailFolder IDs on the current connection. The agent "
            f"reused a reference ID from another connection or session."
        )
    print(f"OK: parentFolderId resolves on current connection ({len(live_ids)} folders checked)")


DISPATCH = {
    "check_trigger_node": check_trigger_node,
    "check_folder_id_fresh": check_folder_id_fresh,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.exit(f"usage: {sys.argv[0]} {{{'|'.join(DISPATCH)}}}")
    DISPATCH[sys.argv[1]]()


if __name__ == "__main__":
    main()
