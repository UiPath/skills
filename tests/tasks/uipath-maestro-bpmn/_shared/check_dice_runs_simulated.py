#!/usr/bin/env python3
"""DiceRoller (BPMN, simulated): a scriptTask runs and produces an integer in [1, 6].

Name-agnostic runtime checker for the simulated variant, modeled the same way
`_shared/check_weather_bpmn_simulated.py` relates to its own non-simulated
sibling: the simulated persona
(`uipath-maestro-flow/interactive/cli_dice_roller_simulated/cli_dice_roller_simulated.yaml`)
withholds "DiceRoller" until asked, so a correctly-built, differently named
process must still be gradable -- no name hint is passed to `find_bpmn_file()`.

Ported from Flow `_shared/check_dice_runs_simulated.py`, translated the same
way `_shared/check_weather_bpmn_simulated.py` and `_shared/check_jira_get_issue.py`
already translate a Flow live check: a JSON node-type scan + inline `flow
debug` payload becomes an XML scan for a `bpmn:scriptTask` element (the
`BPMN.ScriptTask` registry construct -- see
skills/uipath-maestro-bpmn/references/structural-bpmn.md "Script tasks --
Jint authoring contract") plus the BPMN live-debug surface
(`_shared/bpmn_live.py`, per LIVE-ADDENDUM's canonical pattern: ephemeral
solution import, `bpmn debug`, `debug-instance variables-all`/`incidents`).
The canonical live grader this file's plumbing is modeled on is
`_shared/check_jira_get_issue.py`.

Note: the registry LOOKUP key is `BPMN.ScriptTask`, but a correctly-authored
scriptTask serializes its mapping `uipath:type` as `BPMN.Variables`, not the
literal string "BPMN.ScriptTask" (structural-bpmn.md: "The mapping's type
child is `<uipath:type value="BPMN.Variables" version="v1" />`, not
`BPMN.ScriptTask`" -- any other value silently breaks script dispatch). So
this checker asserts a `bpmn:scriptTask` ELEMENT exists, never a literal
"BPMN.ScriptTask" string match, which would fail a correct build.

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per
check.

Assertion map (Flow -> BPMN):
  F check_dice_runs_simulated.py:22  assert_flow_has_node_type(["core.action.script"])
                                  -> at least one bpmn:scriptTask element present
                                     anywhere in the process (the BPMN.ScriptTask
                                     registry construct)
  F check_dice_runs_simulated.py:23  run_debug(timeout=600) implicitly requires
                                  finalStatus == "Completed" (flow_check.run_debug
                                  raises on a non-Completed status internally;
                                  `bpmn debug` returns only an instance id, so the
                                  check is explicit here)
                                  -> FinalStatus in COMPLETED_STATUSES and
                                     debug-instance incidents is empty
  F check_dice_runs_simulated.py:24  assert_output_int_in_range(payload, 1, 6)
                                  -> value-leaf search (never the whole JSON
                                     payload -- see the docstring on
                                     assert_output_int_in_range: "Extracts
                                     integers from output values only, not from
                                     the full debug payload") over the root
                                     scope's Globals AND every element's Outputs
                                     in `debug-instance variables-all`
                                     (LIVE-ADDENDUM: a root PUBLIC OUTPUT has read
                                     back null even when mapped correctly, so the
                                     search is not scoped to one declared output
                                     variable)
  I                locate/parse .bpmn, name-agnostic (the simulated persona
                    withholds the project name) -> bpmn_check.find_bpmn_file()/
                    resolve_project()
  I                ephemeral solution init + `solution projects import` + sha256
                    pin of the imported bytes against the submitted file --
                    `bpmn debug` runs against an imported project, unlike
                    `flow debug`, which runs directly against the discovered
                    project directory -> LIVE-ADDENDUM canonical live pattern
                    (mirrors check_jira_get_issue.py / check_weather_bpmn_simulated.py)
  DROPPED          require_no_private_connector_values / require_sequence_integrity /
                    require_di_for_visible_elements / connection-binding checks --
                    not in Flow; the `bpmn validate` criterion covers structure

Flow's grader does not assert anything about how the die is rolled (only that
a Script node exists and the run produces 1-6), so this checker does not
inspect the script source either -- adding a source-pattern check would be a
BPMN-only requirement the Flow prompt/grader never had.
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# .../uipath-maestro-bpmn (for _shared), same convention as check_jira_get_issue.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from _shared.bpmn_check import elements, find_bpmn_file, resolve_project  # noqa: E402
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

LIVE_RUN_DIR = Path("dice-roller-simulated-live")
SOLUTION_INIT_TIMEOUT = 90
SOLUTION_IMPORT_TIMEOUT = 180
VARIABLES_ALL_TIMEOUT = 120
INCIDENTS_TIMEOUT = 120
COMPLETED_STATUSES = {"Completed", "Successful"}
ROLL_LO, ROLL_HI = 1, 6
INT_RE = re.compile(r"-?\d+")

# Worst-case wall clock this checker can spend, priced the way
# _shared/test_criterion_budgets.py prices a run_debug(...) call: the debug
# call below passes no timeout/retries/backoff kwargs, so it prices at
# bpmn_live.debug_budget() == bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT (480).
# The surrounding CLI steps (solution init/import, variables-all, incidents)
# are not priced by that guard, so their sum is added by hand here and the
# criterion `timeout:` in cli_dice_roller_simulated.yaml documents the
# arithmetic (identical to check_jira_get_issue.py's / check_weather_bpmn_simulated.py's
# own budget):
#   90 (solution init) + 180 (solution import) + 480 (debug)
#   + 120 (variables-all) + 120 (incidents) = 990
#   + bpmn_live.CRITERION_MARGIN_SECONDS (60) = 1050
# Flow's own criterion timeout (1320) already covers this, so it is kept
# verbatim rather than raised.


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


def collect_output_leaves(variables_data: object) -> list:
    """Value leaves of the root scope's Globals AND every element's Outputs.

    A root public output has been observed to read back null even when
    correctly mapped (LIVE-ADDENDUM), so the search is not scoped to one
    declared output variable -- it mirrors Flow's own
    assert_output_int_in_range()/collect_outputs(), which flattens the whole
    outputs payload (declared globals + element outputs) rather than the
    entire debug response, so a stray digit inside an id, timestamp or other
    metadata field elsewhere in the payload can never produce a false match.
    """
    leaves = list(_leaves(get_ci(root_scope(variables_data), "Globals", {})))
    for scope in get_ci(variables_data, "Variables", []) or []:
        for element in get_ci(scope, "Elements", []) or []:
            leaves.extend(_leaves(get_ci(element, "Outputs", {})))
    return leaves


def find_int_in_range(leaves: list, lo: int, hi: int) -> int | None:
    """First integer in [lo, hi] found in the stringified leaf values.

    Mirrors flow_check.assert_output_int_in_range's exact rule: regex over
    the individual OUTPUT VALUE leaves only (never the raw variables-all JSON
    blob, whose element ids, timestamps and status strings would spuriously
    match a small target range like [1, 6]).
    """
    haystack = "\n".join(str(v) for v in leaves)
    for match in INT_RE.findall(haystack):
        value = int(match)
        if lo <= value <= hi:
            return value
    return None


def main() -> None:
    # Name-agnostic: no hint. The simulated persona withholds the project
    # name unless asked, so the submitted .bpmn may not be named
    # "DiceRoller*" -- find_bpmn_file() falls back to "exactly one .bpmn" or
    # "the one with project.uiproj beside it" when several exist.
    bpmn_path = find_bpmn_file()

    try:
        root = ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        _fail(f"{bpmn_path} is not well-formed XML: {exc}")

    script_tasks = elements(root, "scriptTask")
    if not script_tasks:
        _fail(f"{bpmn_path} has no bpmn:scriptTask element (no Script node found)")
    print(f"OK: bpmn has a scriptTask ({len(script_tasks)} found)")

    project_dir = resolve_project(os.path.basename(bpmn_path))
    original_hash = sha256(Path(bpmn_path))

    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    solution_dir = LIVE_RUN_DIR / "DiceRollerSimulatedLiveEval"
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

    leaves = collect_output_leaves(variables_data)
    roll = find_int_in_range(leaves, ROLL_LO, ROLL_HI)
    if roll is None:
        haystack = "\n".join(str(v) for v in leaves)
        _fail(
            f"No integer in [{ROLL_LO}, {ROLL_HI}] found in outputs\n"
            f"Outputs: {haystack[:1000]}"
        )
    print(f"OK: scriptTask present; dice value = {roll}")
    print("PASS: all DiceRoller (simulated) checks passed")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
