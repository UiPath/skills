#!/usr/bin/env python3
"""BellevueWeather (BPMN, simulated): a weather-HTTP node is present and live
output contains one branch message.

Name-agnostic sibling of ``_shared/check_weather_bpmn.py`` (the committed
non-simulated Bellevue port): the two graders make exactly the same
assertions, in the same order, over the same live-debug surface. The only
difference is that this one never pins the project/file name -- the
simulated persona (see
``uipath-maestro-flow/interactive/bellevue_weather_simulated/bellevue_weather_simulated.yaml``)
withholds "BellevueWeather" until asked, so a correctly-built, differently
named process must still be gradable. This mirrors how Flow's own
``check_weather_flow_simulated.py`` relates to the retired non-simulated
``check_weather_flow.py``: "Identical assertions to the retired non-simulated
original ... Name-agnostic runtime checker for the simulated variant."

Ported from Flow `_shared/check_weather_flow_simulated.py` (itself the
name-agnostic sibling of the retired Flow `multi_node/bellevue_weather/
check_weather_flow.py`), translated the same way `_shared/check_weather_bpmn.py`
already translates the non-simulated pair: a JSON node-type scan + inline
`flow debug` payload becomes an XML scan over the registry-driven
`Intsvc.HttpExecution` managed-HTTP shell (see
skills/uipath-maestro-bpmn/references/structural-bpmn.md,
references/registry-workflow.md) plus the BPMN live-debug surface
(`_shared/bpmn_live.py`, per LIVE-ADDENDUM's canonical pattern: ephemeral
solution import, `bpmn debug`, `debug-instance variables-all`/`incidents`).
The canonical live grader this file's plumbing is modeled on is
`_shared/check_jira_get_issue.py`; the non-simulated sibling
`_shared/check_weather_bpmn.py` is the exact structural template.

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per
check.

Assertion map (Flow -> BPMN):
  F check_weather_flow_simulated.py:20-21
                                  assert_flow_has_any_node_type(
                                    ["core.action.http", "custom-codereval-openmeteoapis"])
                                  -> any element carrying an Intsvc.HttpExecution
                                     uipath:activity wrapper. BPMN has no curated
                                     Open-Meteo Integration Service connector, so
                                     only the managed-HTTP construct from
                                     PORTING-BRIEF's construct-translation table
                                     remains; the Flow grader's connector-fallback
                                     branch has nothing to translate to (same as
                                     check_weather_bpmn.py).
  F check_weather_flow_simulated.py:22
                                  run_debug(timeout=240) implicitly requires
                                  finalStatus == "Completed" (flow_check.run_debug
                                  raises on a non-Completed status internally;
                                  `bpmn debug` returns only an instance id, so the
                                  check is explicit here)
                                  -> FinalStatus in COMPLETED_STATUSES and
                                     debug-instance incidents is empty
  F check_weather_flow_simulated.py:23-24
                                  assert_outputs_contain(payload,
                                    ["nice day", "bring a jacket"], require_all=False)
                                  -> either verdict string found among the root
                                     scope's variable leaves AND every element's
                                     Outputs in `debug-instance variables-all`
                                     (LIVE-ADDENDUM: a root PUBLIC OUTPUT has read
                                     back null even when mapped correctly, so the
                                     search is not scoped to one declared output
                                     variable)
  I                locate/parse .bpmn, name-agnostic (the simulated persona
                    withholds the project name, mirroring Flow's own
                    name-agnostic glob for this variant: no fixed basename hint)
                    -> bpmn_check.find_bpmn_file()/resolve_project()
  I                ephemeral solution init + `solution projects import` + sha256
                    pin of the imported bytes against the submitted file --
                    `bpmn debug` runs against an imported project, unlike
                    `flow debug`, which runs directly against the discovered
                    project directory -> LIVE-ADDENDUM canonical live pattern
                    (mirrors check_jira_get_issue.py / check_weather_bpmn.py)
  DROPPED          require_no_private_connector_values / require_sequence_integrity /
                    require_di_for_visible_elements / connection-binding checks --
                    not in Flow; the `bpmn validate` criterion covers structure

Flow's grader does not assert a Script node or a Decision node exists (only
the weather-API node type and the branch output are graded), so this checker
does not add a structural check for the exclusiveGateway either -- adding one
would be a BPMN-only requirement the Flow prompt/grader never had.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# .../uipath-maestro-bpmn (for _shared), same convention as check_jira_get_issue.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from _shared.bpmn_check import (  # noqa: E402
    find_bpmn_file,
    has_typed_uipath_extension,
    resolve_project,
)
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    get_ci,
    incident_records,
    payload_data,
    root_scope,
    run_cli,
    sha256,
)

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
ACTIVITY_TYPE = "Intsvc.HttpExecution"
VERDICTS = ("nice day", "bring a jacket")

LIVE_RUN_DIR = Path("bellevue-weather-simulated-live")
SOLUTION_INIT_TIMEOUT = 90
SOLUTION_IMPORT_TIMEOUT = 180
VARIABLES_ALL_TIMEOUT = 120
INCIDENTS_TIMEOUT = 120
COMPLETED_STATUSES = {"Completed", "Successful"}

# Worst-case wall clock this checker can spend, priced the way
# _shared/test_criterion_budgets.py prices a run_debug(...) call: the debug
# call below passes no timeout/retries/backoff kwargs, so it prices at
# bpmn_live.debug_budget() == bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT (480).
# The surrounding CLI steps (solution init/import, variables-all, incidents)
# are not priced by that guard, so their sum is added by hand here and the
# criterion `timeout:` in bellevue_weather_simulated.yaml documents the
# arithmetic (identical to check_weather_bpmn.py's own budget):
#   90 (solution init) + 180 (solution import) + 480 (debug)
#   + 120 (variables-all) + 120 (incidents) = 990
#   + bpmn_live.CRITERION_MARGIN_SECONDS (60) = 1050
# Flow's own criterion timeout (600) does not cover this larger live-debug
# surface, so it is raised to 1050 -- the one sanctioned deviation
# LIVE-ADDENDUM allows, because the budget is a property of the CLI surface,
# not of what is graded.


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _leaves(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _leaves(v)
    elif isinstance(value, list):
        for v in value:
            yield from _leaves(v)
    elif value is not None:
        yield value


def find_http_execution_nodes(root: ET.Element) -> list[ET.Element]:
    """Every element carrying an Intsvc.HttpExecution uipath:activity wrapper.

    Scans every descendant, not a fixed tag list (registry templates may emit
    the managed-HTTP activity as sendTask, serviceTask, or a plain task) --
    mirrors bpmn_live.index_runtime_connectors' own scanning discipline. Skips
    ``bpmn:extensionElements`` nodes themselves: ``has_typed_uipath_extension``
    matches an element whose OWN direct children include a matching
    ``uipath:activity`` (the wrapper task) as well as an ``extensionElements``
    node (whose direct child literally is that ``uipath:activity``), which
    would otherwise double-count every match once per node.
    """
    return [
        el
        for el in root.iter()
        if el.tag != f"{{{BPMN_NS}}}extensionElements"
        and has_typed_uipath_extension(el, "activity", ACTIVITY_TYPE)
    ]


def collect_output_haystack(variables_data: object) -> str:
    """Value leaves of the root scope's Globals AND every element's Outputs.

    A root public output has been observed to read back null even when
    correctly mapped (LIVE-ADDENDUM), so the search is not scoped to one
    declared output variable -- it mirrors Flow's own
    assert_outputs_contain(), which flattens the whole outputs payload.
    """
    leaves = list(_leaves(get_ci(root_scope(variables_data), "Globals", {})))
    for scope in get_ci(variables_data, "Variables", []) or []:
        for element in get_ci(scope, "Elements", []) or []:
            leaves.extend(_leaves(get_ci(element, "Outputs", {})))
    return "\n".join(str(v) for v in leaves).lower()


def main() -> None:
    # Name-agnostic: no hint. The simulated persona withholds the project
    # name unless asked, so the submitted .bpmn may not be named
    # "BellevueWeather*" -- find_bpmn_file() falls back to "exactly one
    # .bpmn" or "the one with project.uiproj beside it" when several exist.
    bpmn_path = find_bpmn_file()

    try:
        root = ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        _fail(f"{bpmn_path} is not well-formed XML: {exc}")

    http_nodes = find_http_execution_nodes(root)
    if not http_nodes:
        _fail(
            f"{bpmn_path} has no element carrying an {ACTIVITY_TYPE} uipath:activity "
            "wrapper (no managed-HTTP weather node found)"
        )
    print(f"OK: bpmn has a managed-HTTP node ({ACTIVITY_TYPE})")

    project_dir = resolve_project(os.path.basename(bpmn_path))
    original_hash = sha256(Path(bpmn_path))

    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    solution_dir = LIVE_RUN_DIR / "BellevueWeatherSimulatedLiveEval"
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
    variables = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "variables-all", instance_id],
        timeout=VARIABLES_ALL_TIMEOUT,
    )
    _payload, variables_data = payload_data(variables, "variables-all")

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
            detail.append(f"incidents: {incidents_list}")
        raise CheckFailure(
            f"final status was {final_status!r}"
            + ("; " + "; ".join(detail) if detail else "")
        )
    if incidents_list is None:
        raise CheckFailure(f"incidents response has an unknown shape: {incidents_data!r}")
    if incidents_list:
        raise CheckFailure(f"unexpected incidents: {incidents_list}")
    print("OK: bpmn debug completed (FinalStatus=%s, no incidents)" % final_status)

    haystack = collect_output_haystack(variables_data)
    if not any(verdict in haystack for verdict in VERDICTS):
        _fail(
            f"outputs do not contain either verdict string {list(VERDICTS)!r}\n"
            f"outputs: {haystack[:1000]}"
        )
    print("OK: bpmn outputs contain a weather branch message")
    print("PASS: all BellevueWeather (simulated) checks passed")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
