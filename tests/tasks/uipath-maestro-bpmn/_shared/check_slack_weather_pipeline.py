#!/usr/bin/env python3
"""SlackWeatherPipeline (BPMN): structural + live checks.

Ported from Flow `tests/tasks/uipath-maestro-flow/_shared/check_slack_weather_pipeline.py`:
same scenario (a manual-start process reads the #office-bellevue Slack
channel description, extracts the city, fetches weather for that city from
open-meteo, and decides warm/cold), translated from a JSON node walk + inline
`flow debug` payload to an XML walk over the registry-driven
`Intsvc.ActivityExecution`/`Intsvc.HttpExecution` connector shells (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3-4) plus the
BPMN live-debug surface (`_shared/bpmn_live.py`, per LIVE-ADDENDUM's canonical
pattern: ephemeral solution import, `bpmn debug`, `debug-instance
variables-all`/`incidents`). Mirrors the structure of the CI-passing
`_shared/check_channel_description.py` and `_shared/check_jira_get_issue.py`
(same connector tenant, same live sequence and budget arithmetic).

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per
check. Nothing is created against the tenant by this scenario (it only reads
a channel's description and calls a public weather API), so there is no
side-effect record to tear down -- matching Flow's own grader, which has no
teardown either.

Assertion map (Flow → BPMN):
  F check_slack_weather_pipeline.py:23  assert_flow_uses_connector_target('uipath-salesforce-slack')
                                          → find_connector_nodes(): any element carrying
                                            Intsvc.ActivityExecution whose connectorKey context field
                                            equals uipath-salesforce-slack. No operation filter -- Flow's
                                            own assertion has none either (it does not care whether the
                                            Slack node reads the channel description via a curated or
                                            generic op), so this port keeps the same breadth rather than
                                            narrowing it. Mirrors check_channel_description.py's
                                            find_connector_nodes() (same connector, same tenant folder).
  F check_slack_weather_pipeline.py:24  assert_flow_has_api_node_targeting(['open-meteo', 'openmeteoapis'])
                                          → find_weather_node(): any element carrying Intsvc.HttpExecution
                                            OR Intsvc.ActivityExecution whose own uipath:activity
                                            extension (not the node's full serialized subtree, which
                                            would falsely inherit a descendant match onto every ancestor)
                                            contains 'open-meteo' or 'openmeteoapis' (case-insensitive). Keeps
                                            Flow's own tolerance for either a raw HTTP node or a curated
                                            connector node -- the BPMN skill's node-selection ladder may
                                            pick either, and PORTING-BRIEF's construct table designates
                                            Intsvc.HttpExecution manual mode as the expected shape without
                                            requiring it (Flow does not gate on manual vs. connected mode
                                            either).
  F check_slack_weather_pipeline.py:28-29  payload = run_debug(timeout=240); implicitly requires
                                          finalStatus == 'Completed' (flow_check.run_debug raises on a
                                          non-Completed status internally; `bpmn debug` returns only an
                                          instance id, so the check is explicit here)
                                          → FinalStatus in COMPLETED_STATUSES and debug-instance
                                            incidents is empty
  F check_slack_weather_pipeline.py:31  assert_output_nonempty(payload, 'weatherVerdict')
                                          + lines 32-37 exactly one of ALLOWED_VERDICTS found
                                          → verdict_text(): the `weatherVerdict` root Global, resolved
                                            by its declared output id then by name. Only when it reads
                                            back null (LIVE-ADDENDUM: a root PUBLIC OUTPUT has read back
                                            null even when mapped correctly) does the search widen to
                                            bpmn_live.output_haystack(). The exact-one-hit check is
                                            verbatim Flow logic.
  I               locate/parse .bpmn (file exists, well-formed XML, project directory resolved)
                                          → bpmn_check.find_bpmn_file()/resolve_project()
  I               ephemeral solution init + `solution projects import` + sha256 pin of the imported
                    bytes against the submitted file -- `bpmn debug` runs against an imported project,
                    unlike `flow debug`, which runs directly against the discovered project directory
                                          → LIVE-ADDENDUM canonical live pattern (mirrors
                                            check_channel_description.py / check_jira_get_issue.py)
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

# …/uipath-maestro-bpmn (for _shared), same convention as _shared/check_channel_description.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from _shared.bpmn_check import find_bpmn_file, resolve_project  # noqa: E402
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    CheckFailure,
    UIPATH_NS,
    connector_context,
    debug_evidence,
    get_ci,
    import_exact,
    normalized_identifier,
    output_haystack,
    q,
    require_clean_run,
    resolve_runtime_key,
    root_scope,
)

SLACK_CONNECTOR_KEY = "uipath-salesforce-slack"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
# registry-workflow.md lists Intsvc.UnifiedHttpRequest beside HttpExecution for the managed HTTP sendTask; the eval
# agent emits either (CI run 35538279757).
HTTP_TYPES = ("Intsvc.HttpExecution", "Intsvc.UnifiedHttpRequest")
HTTP_TYPE = HTTP_TYPES[0]
WEATHER_HINTS = ("open-meteo", "openmeteoapis")
NAME_HINT = "SlackWeatherPipeline"

ALLOWED_VERDICTS = ("warm office today", "cold office today")
VERDICT_OUTPUT = "weatherVerdict"

LIVE_RUN_DIR = Path("slack-weather-pipeline-live")

# Worst-case wall clock this checker can spend, priced the way
# _shared/test_criterion_budgets.py prices a run_debug(...) call: the debug
# call below passes no timeout/retries/backoff kwargs, so it prices at
# bpmn_live.debug_budget() == bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT (480).
# The surrounding CLI steps (solution init/import, variables-all, incidents)
# are not priced by that guard, so their sum is added by hand here and the
# criterion `timeout:` in slack_weather_pipeline.yaml documents the
# arithmetic (mirrors check_channel_description.py / check_jira_get_issue.py):
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


def find_weather_node(root: ET.Element) -> list[ET.Element]:
    """Every element that is an API-capable node actually targeting open-meteo.

    Mirrors Flow's assert_flow_has_api_node_targeting: an API-capable node is
    one carrying Intsvc.HttpExecution (a manual/connectionless HTTP call) or
    Intsvc.ActivityExecution (a curated connector, in case the skill's
    node-selection ladder picks one for the weather call instead), and it
    targets the service only when a weather hint appears anywhere in that
    node's OWN uipath:activity extension.

    Scoped to the node's own `./extensionElements/activity` child (not a
    blind substring search over the node's full serialized subtree): an
    ancestor (bpmn:process, bpmn:definitions) serializes its whole descendant
    tree, so a naive `ET.tostring(node)` scan would have every ancestor of the
    real weather node "inherit" both the type token and the hint text and
    falsely match too (caught by a synthetic-fixture gate before this port
    shipped). Scoping to the immediate `uipath:activity` child keeps a Slack
    connector node (also Intsvc.ActivityExecution) or a Script node that
    merely mentions the service from satisfying this gate, same as
    connector_context()'s own scoping discipline.
    """
    found = []
    for node in root.iter():
        activity = node.find(f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'activity')}")
        if activity is None:
            continue
        raw = ET.tostring(activity, encoding="unicode")
        if not any(t in raw for t in HTTP_TYPES) and ACTIVITY_TYPE not in raw:
            continue
        if any(hint in raw.lower() for hint in WEATHER_HINTS):
            found.append(node)
    return found


def verdict_identifiers(root: ET.Element) -> list[str]:
    """Declared output id(s) named weatherVerdict, then the name itself."""
    wanted = normalized_identifier(VERDICT_OUTPUT)
    ids = [
        node.attrib["id"]
        for variables in root.iter(q(UIPATH_NS, "variables"))
        for node in variables.findall(q(UIPATH_NS, "output"))
        if node.attrib.get("id") and normalized_identifier(node.attrib.get("name", "")) == wanted
    ]
    return [*ids, VERDICT_OUTPUT]


def verdict_text(variables_data: object, identifiers: list[str]) -> str | None:
    globals_ = get_ci(root_scope(variables_data), "Globals", {}) or {}
    if not isinstance(globals_, dict):
        return None
    for identifier in identifiers:
        wanted = normalized_identifier(identifier)
        if not any(normalized_identifier(key) == wanted for key in globals_):
            continue
        value = resolve_runtime_key(globals_, identifier, VERDICT_OUTPUT)
        if value is not None:
            return str(value).lower()
    return None


def main() -> None:
    bpmn_path = find_bpmn_file(NAME_HINT)

    try:
        root = ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        _fail(f"{bpmn_path} is not well-formed XML: {exc}")

    connector_nodes = find_connector_nodes(root, SLACK_CONNECTOR_KEY)
    if not connector_nodes:
        _fail(
            f"bpmn does not reference a {SLACK_CONNECTOR_KEY} connector node "
            f"({ACTIVITY_TYPE})"
        )
    print(f"OK: bpmn references a {SLACK_CONNECTOR_KEY} connector node")

    weather_nodes = find_weather_node(root)
    if not weather_nodes:
        _fail(
            f"bpmn does not reference an API-capable node ({' / '.join(HTTP_TYPES)} or "
            f"{ACTIVITY_TYPE}) targeting one of {WEATHER_HINTS}"
        )
    print(f"OK: bpmn references an API node targeting open-meteo")

    project_dir = resolve_project(os.path.basename(bpmn_path))
    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    imported_project = import_exact(
        Path(bpmn_path), project_dir, LIVE_RUN_DIR / "SlackWeatherPipelineLiveEval"
    )

    debug_data, instance_id = bpmn_live.run_debug(
        imported_project, {}, LIVE_RUN_DIR / "debug.log"
    )
    print(f"OK: debug completed (instance {instance_id})")

    evidence = debug_evidence(instance_id)
    require_clean_run(debug_data, evidence)

    haystack = verdict_text(evidence.variables, verdict_identifiers(root))
    source = VERDICT_OUTPUT
    if haystack is None:
        haystack = output_haystack(evidence.variables)
        source = f"outputs ({VERDICT_OUTPUT} read back null)"
    hits = [v for v in ALLOWED_VERDICTS if v in haystack]
    if len(hits) != 1:
        found = "both verdicts" if len(hits) > 1 else "neither verdict"
        _fail(
            f"{source} must contain exactly one of {list(ALLOWED_VERDICTS)}; "
            f"found {found}\n{source}: {haystack[:1000]}"
        )
    print(f"OK: bpmn outputs carry {hits[0]!r}")
    print("PASS: all SlackWeatherPipeline checks passed")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
