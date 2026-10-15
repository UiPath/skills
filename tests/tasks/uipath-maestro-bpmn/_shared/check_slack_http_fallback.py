#!/usr/bin/env python3
"""SlackEmojiListTest (BPMN): connector-mode HTTP fallback + live checks.

The Slack catalog connector (``uipath-salesforce-slack``) has no activity for
"list a team's custom emoji" (Slack's ``emoji.list``), so the skill sends it as
a connector-mode ``Intsvc.UnifiedHttpRequest`` through the Slack connection
(skills/uipath-maestro-bpmn/references/v2-connector-nodes.md, "HTTP
requests"), then the process must debug green.

Two subcommands:

  check_fallback   Structural -- an ``Intsvc.UnifiedHttpRequest`` node on the
                   generic HTTP connector (``uipath-uipath-http``), body
                   ``authentication: "connector"`` with ``targetConnector``
                   ``uipath-salesforce-slack``, targeting ``emoji.list``. A V1
                   ``Intsvc.ActivityExecution`` on the Slack connector (the
                   catalog-miss shape the skill forbids) does not count.
  check_debug      Runtime -- ``uip maestro bpmn debug`` of an ephemeral import
                   finishes completed with no incidents against the live Slack
                   connection.

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per
check.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_slack_http_fallback.py check_fallback
    python3 $REFERENCE_DIR/_shared/check_slack_http_fallback.py check_debug
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    BodyShapeError,
    NS,
    body_object,
    context_inputs,
    fail,
    find_bpmn_file,
    has_type,
    parse_bpmn,
    resolve_project,
)
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    INCIDENTS_TIMEOUT,
    CheckFailure,
    DebugEvidence,
    connector_context,
    import_exact,
    incident_records,
    payload_data,
    require_clean_run,
    run_cli,
)

NAME_HINT = "SlackEmojiListTest"
SLACK_KEY = "uipath-salesforce-slack"
HTTP_CONNECTOR_KEY = "uipath-uipath-http"
# Bare token, so both '/emoji.list' and 'emoji.list' satisfy the check.
EMOJI_ENDPOINT = "emoji.list"
EMOJI_ENDPOINT_RE = re.compile(r"emoji[._]list")

LIVE_RUN_DIR = Path("slack-emoji-list-live")

# Worst-case wall clock check_debug can spend, priced the way
# _shared/test_criterion_budgets.py prices a run_debug(...) call: the call
# below passes no timeout/retries/backoff kwargs, so it prices at
# bpmn_live.debug_budget() == bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT (480).
# The surrounding CLI steps are not priced by that guard, so their sum is
# added by hand here and the check_debug criterion `timeout:` in
# slack_http_fallback.yaml documents the arithmetic:
#   90 (solution init) + 180 (solution import) + 480 (debug) + 120 (incidents)
#   = 870 + bpmn_live.CRITERION_MARGIN_SECONDS (60) = 930
# Flow's own criterion timeout (720) does not fit the extra CLI steps a BPMN
# live grade needs (solution init/import, a separate incidents read), so it
# is raised to 930 -- the one sanctioned deviation from "criteria identical"
# (LIVE-ADDENDUM: a property of the CLI surface, not of what is graded).


def node_blob(el: ET.Element) -> str:
    parts = [ET.tostring(el, encoding="unicode")]
    for inp in context_inputs(el):
        parts.append(inp.attrib.get("name") or "")
        parts.append(inp.attrib.get("value") or "")
        parts.append(inp.text or "")
    return "\n".join(parts).lower()


def is_slack_connector_node(el: ET.Element) -> bool:
    """True when ``el`` is itself a connector-mode Unified HTTP request through
    the Slack connection.

    ``connector_context`` reads the DIRECT-child activity, so the process and
    definitions ancestors that ``root.iter()`` also yields never match.
    """
    context = connector_context(el)
    key = context.get("connectorKey", "").strip().lower()
    if key != HTTP_CONNECTOR_KEY or not has_type(el, "Intsvc.UnifiedHttpRequest"):
        return False
    try:
        body = body_object(el)
    except BodyShapeError:
        return False
    return (
        body.get("authentication") == "connector"
        and str(body.get("targetConnector", "")).lower() == SLACK_KEY
    )


def references_emoji_endpoint(el: ET.Element) -> bool:
    return EMOJI_ENDPOINT_RE.search(node_blob(el)) is not None


def find_slack_connector_nodes(root: ET.Element) -> list[ET.Element]:
    """Every connector-mode Unified HTTP request through the Slack connection,
    whatever its host tag."""
    return [node for node in root.iter() if is_slack_connector_node(node)]


# ── subcommand: check_fallback ──────────────────────────────────────────────
def check_fallback() -> None:
    path, root = parse_bpmn(NAME_HINT)

    slack_nodes = find_slack_connector_nodes(root)
    if not slack_nodes:
        seen = sorted(
            {
                connector_context(n).get("connectorKey", "")
                for n in root.iter()
                if connector_context(n).get("connectorKey")
            }
        )
        fail(
            "No connector-mode Intsvc.UnifiedHttpRequest through the Slack "
            f"connection (targetConnector {SLACK_KEY!r}) found. The catalog "
            "connector has no 'list custom emoji' activity, so the process "
            "must send it as an HTTP request through the Slack connection. "
            f"connectorKey values seen: {seen}"
        )
    print(f"OK: {len(slack_nodes)} Slack connector-mode HTTP node(s) present")

    fallback_nodes = [n for n in slack_nodes if references_emoji_endpoint(n)]
    if not fallback_nodes:
        fail(
            f"No Slack connector-mode HTTP node targets the {EMOJI_ENDPOINT!r} "
            "endpoint (expected the '/emoji.list' path, which lists a team's "
            "custom emoji)."
        )
    print(
        f"OK: {len(fallback_nodes)} Slack connector node(s) target the "
        f"'{EMOJI_ENDPOINT}' endpoint"
    )
    print(f"OK: {path} -- all Slack HTTP-fallback structural checks passed")


# ── subcommand: check_debug ──────────────────────────────────────────────────
def check_debug() -> None:
    bpmn_path = find_bpmn_file(NAME_HINT)
    project_dir = resolve_project(os.path.basename(bpmn_path))
    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    imported_project = import_exact(
        Path(bpmn_path), project_dir, LIVE_RUN_DIR / "SlackEmojiListTestLiveEval"
    )

    debug_data, instance_id = bpmn_live.run_debug(
        imported_project, {}, LIVE_RUN_DIR / "debug.log"
    )
    print(f"OK: debug completed (instance {instance_id})")

    incidents = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "incidents", instance_id],
        timeout=INCIDENTS_TIMEOUT,
    )
    _payload, incidents_data = payload_data(incidents, "incidents")
    evidence = DebugEvidence(
        variables=None,
        variables_text="",
        incidents=incident_records(incidents_data),
        incidents_raw=incidents_data,
    )
    require_clean_run(debug_data, evidence)


DISPATCH = {
    "check_fallback": check_fallback,
    "check_debug": check_debug,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        fail(f"usage: {os.path.basename(sys.argv[0])} {{{'|'.join(DISPATCH)}}}")
    DISPATCH[sys.argv[1]]()


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        sys.exit(f"FAIL: {error}")
