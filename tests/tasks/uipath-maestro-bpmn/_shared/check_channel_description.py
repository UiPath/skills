#!/usr/bin/env python3
"""SlackChannelDescription (BPMN): structural + live checks.

Ported from Flow `tests/tasks/uipath-maestro-flow/_shared/check_channel_description.py`:
same scenario (a manual-start process retrieves the channel description of
#office-bellevue via the Slack Integration Service connector and outputs it),
translated from a JSON node walk + inline `flow debug` payload to an XML walk
over the registry-driven `Intsvc.ActivityExecution` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4) plus the
BPMN live-debug surface (`_shared/bpmn_live.py`, per LIVE-ADDENDUM's canonical
pattern: ephemeral solution import, `bpmn debug`, `debug-instance
variables-all`/`incidents`).

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per
check. Nothing is created against the tenant by this scenario (it only reads
a channel's description), so there is no side-effect record to tear down --
matching Flow's own grader, which has no teardown either.

Assertion map (Flow → BPMN):
  F check_channel_description.py:27  assert_flow_uses_connector_target('uipath-salesforce-slack')
                                       → find_connector_nodes(): any element carrying
                                         Intsvc.ActivityExecution whose connectorKey context field
                                         equals uipath-salesforce-slack. No operation filter -- Flow's
                                         own assertion has none either, so this port keeps the same
                                         breadth rather than narrowing it.
  F check_channel_description.py:28  run_debug(timeout=240) implicitly requires finalStatus ==
                                       "Completed" (flow_check.run_debug raises on a non-Completed
                                       status internally; `bpmn debug` returns only an instance id, so
                                       the check is explicit here)
                                       → FinalStatus in COMPLETED_STATUSES and debug-instance
                                         incidents is empty
  F check_channel_description.py:29  assert_outputs_contain(payload, ADDRESS_FRAGMENTS, require_all=True)
                                       → every fragment found among the root scope's variable leaves
                                         AND every element's Outputs (incl. nested connector `response`)
                                         in `debug-instance variables-all` (LIVE-ADDENDUM: a root PUBLIC
                                         OUTPUT has read back null even when mapped correctly, so the
                                         search is not scoped to one declared output variable)
  I               locate/parse .bpmn (file exists, well-formed XML, project directory resolved)
                                       → bpmn_check.find_bpmn_file()/resolve_project()
  I               ephemeral solution init + `solution projects import` + sha256 pin of the imported
                    bytes against the submitted file -- `bpmn debug` runs against an imported project,
                    unlike `flow debug`, which runs directly against the discovered project directory
                                       → LIVE-ADDENDUM canonical live pattern (mirrors
                                         e2e/jira_get_issue/_shared/check_jira_get_issue.py)
  DROPPED         the HTTP-proxy fallback branch of assert_flow_uses_connector_target (a
                    `core.action.http.v2` node with bodyParameters.targetConnector) -- a legacy Flow
                    accommodation for connector-backed flows authored before native connector node
                    types existed. The BPMN skill's registry enrichment always emits
                    Intsvc.ActivityExecution for a connector activity (registry-workflow.md §3), so no
                    analogous construct exists to translate.
  DROPPED         require_no_private_connector_values / require_sequence_integrity /
                    require_di_for_visible_elements / connection-binding checks -- not in Flow; the
                    `bpmn validate` criterion covers structure.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# …/uipath-maestro-bpmn (for _shared), same convention as _shared/check_jira_get_issue.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from _shared.bpmn_check import find_bpmn_file, resolve_project  # noqa: E402
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    connector_context,
    debug_evidence,
    import_exact,
    output_haystack,
    require_clean_run,
)

CONNECTOR_KEY = "uipath-salesforce-slack"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
NAME_HINT = "SlackChannelDescription"

ADDRESS_FRAGMENTS = [
    "700 Bellevue Way NE",
    "Suite 2000",
    "Bellevue",
    "WA 98004",
]

LIVE_RUN_DIR = Path("slack-channel-description-live")

# Worst-case wall clock this checker can spend, priced the way
# _shared/test_criterion_budgets.py prices a run_debug(...) call: the debug
# call below passes no timeout/retries/backoff kwargs, so it prices at
# bpmn_live.debug_budget() == bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT (480).
# The surrounding CLI steps (solution init/import, variables-all, incidents)
# are not priced by that guard, so their sum is added by hand here and the
# criterion `timeout:` in slack_channel_description.yaml documents the
# arithmetic (mirrors e2e/jira_get_issue/jira_get_issue.yaml):
#   90 (solution init) + 180 (solution import) + 480 (debug)
#   + 120 (variables-all) + 120 (incidents) = 990
#   + bpmn_live.CRITERION_MARGIN_SECONDS (60) = 1050
# Flow's own criterion timeout (600) does not fit the extra CLI steps a BPMN
# live grade needs (solution init/import, separate variables-all/incidents
# reads), so it is raised to 1050 -- the one sanctioned deviation from
# "criteria identical" (LIVE-ADDENDUM: a property of the CLI surface, not of
# what is graded).


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def find_connector_nodes(root: ET.Element, connector_key: str) -> list[ET.Element]:
    """Every element carrying an Intsvc.ActivityExecution targeting connector_key.

    No operation filter: Flow's own assertion (`assert_flow_uses_connector_target`)
    only requires SOME connector node for the key, not a specific op, so this
    mirrors that breadth. Scans every descendant, not a fixed tag list (registry
    templates may emit a connector activity as sendTask, serviceTask, or a plain
    task) -- mirrors bpmn_live.index_runtime_connectors' own scanning discipline.
    """
    found = []
    for node in root.iter():
        context = connector_context(node)
        if context.get("connectorKey") != connector_key:
            continue
        if ACTIVITY_TYPE not in ET.tostring(node, encoding="unicode"):
            continue
        found.append(node)
    return found


def main() -> None:
    bpmn_path = find_bpmn_file(NAME_HINT)
    raw = Path(bpmn_path).read_text(encoding="utf-8")
    if CONNECTOR_KEY not in raw:
        _fail(f"{bpmn_path} does not reference the {CONNECTOR_KEY} connector")
    print(f"OK: bpmn references {CONNECTOR_KEY}")

    try:
        root = ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        _fail(f"{bpmn_path} is not well-formed XML: {exc}")

    connector_nodes = find_connector_nodes(root, CONNECTOR_KEY)
    if not connector_nodes:
        _fail(
            f"bpmn does not reference a {CONNECTOR_KEY} connector node "
            f"({ACTIVITY_TYPE})"
        )
    print(f"OK: bpmn references a {CONNECTOR_KEY} connector node")

    project_dir = resolve_project(os.path.basename(bpmn_path))
    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    imported_project = import_exact(
        Path(bpmn_path), project_dir, LIVE_RUN_DIR / "SlackChannelDescriptionLiveEval"
    )

    debug_data, instance_id = bpmn_live.run_debug(
        imported_project, {}, LIVE_RUN_DIR / "debug.log"
    )
    print(f"OK: debug completed (instance {instance_id})")

    evidence = debug_evidence(instance_id)
    require_clean_run(debug_data, evidence)

    haystack = output_haystack(evidence.variables)
    missing = [f for f in ADDRESS_FRAGMENTS if f.lower() not in haystack]
    if missing:
        _fail(
            f"outputs missing address fragments {missing}; "
            f"expected all of {ADDRESS_FRAGMENTS}\noutputs: {haystack[:1000]}"
        )
    print("OK: bpmn outputs contain the Bellevue office address")
    print("PASS: all SlackChannelDescription checks passed")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
