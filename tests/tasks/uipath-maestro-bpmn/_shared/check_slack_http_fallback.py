#!/usr/bin/env python3
"""SlackEmojiListTest (BPMN): connector-mode HTTP fallback + live checks.

Ported from Flow `connector_features/slack-http-fallback/
check_slack_http_fallback.py`: same scenario (the Slack catalog connector,
``uipath-salesforce-slack``, has no native activity for "list a team's custom
emoji" -- Slack's ``emoji.list`` endpoint -- so the skill must fall back to a
connector-mode HTTP request that reuses the existing Slack connection's
managed auth, then the process must debug green), translated from a JSON
node/``inputs.detail`` walk to an XML walk over the registry-driven
``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §"Connectionless
vs connector HTTP") plus the BPMN live-debug surface (``_shared/
bpmn_live.py``, per LIVE-ADDENDUM's canonical pattern: ephemeral solution
import, ``bpmn debug``, ``debug-instance incidents``).

Two subcommands (subcommand-dispatched, matching Flow's own checker):

  check_fallback   Structural -- the emoji list is built as a connector-mode
                    HTTP node bound to the Slack connector (NOT a curated
                    native activity for something else), targeting the Slack
                    ``emoji.list`` endpoint.
  check_debug       Runtime -- ``uip maestro bpmn debug`` finishes with a
                    completed final status and no incidents, against the live
                    Slack connection.

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per
check.

Assertion map (Flow → BPMN):
  F check_slack_http_fallback.py:_is_slack_http_fallback (a fallback node exists)
                                  → find_fallback_nodes(): an element carrying Intsvc.ActivityExecution
                                    or Intsvc.HttpExecution whose connectorKey context field equals
                                    uipath-salesforce-slack
  F check_slack_http_fallback.py:_is_slack_http_fallback (HTTP-shaped, not a native op)
                                  → discriminated by the emoji.list endpoint match below, not by a
                                    node `type` string: BPMN's registry wrapper is the SAME
                                    Intsvc.ActivityExecution tag for both a curated native activity
                                    (e.g. Get Channel Info) and an HTTP fallback, unlike Flow's node
                                    `type`, which differs per shape (see GUESS)
  F check_slack_http_fallback.py:EMOJI_ENDPOINT blob search (json.dumps(fallback_nodes).lower())
                                  → references_emoji_endpoint(): 'emoji.list' found anywhere across
                                    every uipath:input name/value/text at any depth under the node,
                                    plus the node's raw XML as a lenient fallback -- mirrors Flow's own
                                    whole-node-blob substring search
  F check_slack_http_fallback.py:check_debug (run_debug(timeout=300); flow_check.run_debug raises
                                  internally on a non-Completed status)
                                  → FinalStatus in COMPLETED_STATUSES and debug-instance incidents is
                                    empty (bpmn debug returns only an instance id, so the check is
                                    explicit here)
  I                locate/parse .bpmn (file exists, well-formed XML, project directory resolved)
                                  → bpmn_check.find_bpmn_file()/resolve_project()
  I                ephemeral solution init + `solution projects import` + sha256 pin of the imported
                    bytes against the submitted file -- `bpmn debug` runs against an imported project,
                    unlike `flow debug`, which runs directly against the discovered project directory
                                  → LIVE-ADDENDUM canonical live pattern (mirrors
                                    e2e/jira_get_issue and multi_node/slack_channel_description)
  T                curated (Intsvc.ActivityExecution) OR the connector-authenticated form of
                    Intsvc.HttpExecution -- accept either wrapper tag (BATCH1-ADDENDUM; same
                    tolerance and same open GUESS as check_non_catalog_http_fallback.py)
                                  → ACTIVITY_TYPES tuple checked via has_type()
  T                collect uipath:input elements at any depth under the node
                                  → context_inputs() uses `.//uipath:input`
  T                endpoint value found in a context field, a sibling uipath:input's own
                    value/text, or inside the target="body" JSON payload (the skill does not pin
                    where the endpoint lands)
                                  → references_emoji_endpoint()

GUESS (flag for reviewer): same open question as check_non_catalog_http_fallback.py --
registry-workflow.md documents `Intsvc.HttpExecution`'s `mode` context field as
hardcoded to "manual" (connectionless) with no documented connector-authenticated
alternative; the skill's own contract splits connector-mode HTTP as
`Intsvc.ActivityExecution` (a connector object/operation, here reused via a
generic "http-request" passthrough objectName under the Slack connectorKey --
see the real CI-passing SpotifyProfileTest.bpmn fixture, which authors exactly
this shape for the non-catalog case) and reserves `Intsvc.HttpExecution` for
connectionless/manual calls only. To stay faithful to both the porting brief
and the skill's documented contract without inventing a hard requirement on one
wrapper tag, this checker classifies purely by `connectorKey` (+ the emoji.list
endpoint match), and accepts either wrapper tag carrying them.

No Flow assertions dropped: node existence, the HTTP-fallback shape (translated
via connectorKey since BPMN's node `type` cannot distinguish curated vs raw the
way Flow's node.type string does), and the emoji.list endpoint substring all
have a BPMN counterpart above. check_debug's only requirement in Flow is that
`flow debug` completes (finalStatus Completed); no output-content assertion is
made there, so none is added here either.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_slack_http_fallback.py check_fallback
    python3 $REFERENCE_DIR/_shared/check_slack_http_fallback.py check_debug
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import NS, context_inputs, fail, find_bpmn_file, has_type, parse_bpmn, resolve_project  # noqa: E402
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    connector_context,
    get_ci,
    incident_records,
    payload_data,
    run_cli,
    sha256,
)

NAME_HINT = "SlackEmojiListTest"
SLACK_KEY = "uipath-salesforce-slack"
# Slack endpoint that lists a team's custom emoji. Bare token, so both '/emoji.list'
# and 'emoji.list' forms satisfy the check, mirroring Flow's own tolerance.
# T: the Slack connector's generic (non-curated) resource for that endpoint is
# named ``emoji_list`` / ``emoji_list_GET`` -- the same endpoint, connector
# naming (CI run 35538279757: the agent's node ran to completion against it).
EMOJI_ENDPOINT = "emoji.list"
EMOJI_ENDPOINT_RE = re.compile(r"emoji[._]list")
ACTIVITY_TYPES = ("Intsvc.ActivityExecution", "Intsvc.HttpExecution", "Intsvc.UnifiedHttpRequest")

LIVE_RUN_DIR = Path("slack-emoji-list-live")
SOLUTION_INIT_TIMEOUT = 90
SOLUTION_IMPORT_TIMEOUT = 180
INCIDENTS_TIMEOUT = 120
COMPLETED_STATUSES = {"Completed", "Successful"}

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
    """True when ``el`` is itself the connector-activity host element (a
    sendTask/serviceTask/plain task carrying its OWN
    ``extensionElements/uipath:activity``) for the Slack connector.

    ``connector_context`` (bpmn_live.py) resolves the activity via a
    DIRECT-child path (``./extensionElements/activity``), not a recursive
    ``.//`` search -- root.iter() walks every ancestor of the real host
    element too (the process, the definitions root, the host's own
    extensionElements/activity wrapper), and each of those "contains" the
    same connectorKey/type tokens somewhere in its serialized subtree. Only
    the direct-child lookup correctly isolates the one true host element
    instead of matching every ancestor as well.
    """
    context = connector_context(el)
    if context.get("connectorKey", "").strip().lower() != SLACK_KEY:
        return False
    return any(has_type(el, token) for token in ACTIVITY_TYPES)


def references_emoji_endpoint(el: ET.Element) -> bool:
    return EMOJI_ENDPOINT_RE.search(node_blob(el)) is not None


def find_slack_connector_nodes(root: ET.Element) -> list[ET.Element]:
    """Every element carrying an Intsvc.ActivityExecution/HttpExecution node
    whose connectorKey is the Slack connector. Scans every descendant, not a
    fixed tag list (registry templates may emit a connector activity as
    sendTask, serviceTask, or a plain task)."""
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
            f"No {SLACK_KEY!r} connector node found. The catalog connector has "
            "no native 'list custom emoji' activity, so the process must fall "
            "back to a connector-mode HTTP request bound to the Slack "
            f"connection. connectorKey values seen: {seen}"
        )
    print(f"OK: {len(slack_nodes)} {SLACK_KEY!r} connector node(s) present")

    fallback_nodes = [n for n in slack_nodes if references_emoji_endpoint(n)]
    if not fallback_nodes:
        fail(
            f"No {SLACK_KEY!r} connector node targets the {EMOJI_ENDPOINT!r} "
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
    original_hash = sha256(Path(bpmn_path))

    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    solution_dir = LIVE_RUN_DIR / "SlackEmojiListTestLiveEval"
    initialized = run_cli(
        ["uip", "solution", "init", str(solution_dir)], timeout=SOLUTION_INIT_TIMEOUT
    )
    payload_data(initialized, "initialize ephemeral solution")
    solution_files = sorted(solution_dir.glob("*.uipx"))
    if len(solution_files) != 1:
        raise CheckFailure(
            f"solution init produced {len(solution_files)} .uipx files in "
            f"{solution_dir}, expected exactly one"
        )
    solution_file = solution_files[0]
    imported = run_cli(
        [
            "uip",
            "solution",
            "projects",
            "import",
            str(project_dir.resolve()),
            "--solutionFile",
            str(solution_file),
        ],
        timeout=SOLUTION_IMPORT_TIMEOUT,
    )
    payload_data(imported, "import exact BPMN project")
    imported_project = solution_dir / project_dir.name
    if sha256(imported_project / os.path.basename(bpmn_path)) != original_hash:
        raise CheckFailure("solution import changed the submitted BPMN bytes")
    print(f"OK: imported exact artifact (sha256={original_hash})")

    debug_data, instance_id = bpmn_live.run_debug(
        imported_project, {}, LIVE_RUN_DIR / "debug.log"
    )
    print(f"OK: debug completed (instance {instance_id})")

    final_status = get_ci(debug_data, "FinalStatus")
    incidents = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "incidents", instance_id],
        timeout=INCIDENTS_TIMEOUT,
    )
    _payload, incidents_data = payload_data(incidents, "incidents")
    incidents_list = incident_records(incidents_data)

    if final_status not in COMPLETED_STATUSES:
        detail = []
        faulted = [
            f"{get_ci(item, 'ElementId')}={get_ci(item, 'Status')}"
            for item in get_ci(debug_data, "ElementExecutions", []) or []
            if isinstance(item, dict)
            and str(get_ci(item, "Status") or "").casefold() != "completed"
        ]
        if faulted:
            detail.append(f"non-completed elements: {faulted}")
        if incidents_list:
            detail.append(f"incidents: {json.dumps(incidents_list)[:1500]}")
        raise CheckFailure(
            f"final status was {final_status!r}"
            + ("; " + "; ".join(detail) if detail else "")
        )
    if incidents_list is None:
        raise CheckFailure(f"incidents response has an unknown shape: {incidents_data!r}")
    if incidents_list:
        raise CheckFailure(f"unexpected incidents: {incidents_list}")
    print(
        "OK: uip maestro bpmn debug finished with FinalStatus=%s (no incidents)"
        % final_status
    )


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
