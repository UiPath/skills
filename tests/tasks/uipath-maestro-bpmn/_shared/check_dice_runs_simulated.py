#!/usr/bin/env python3
"""DiceRoller (BPMN, simulated): a scriptTask runs and produces an integer in [1, 6].

Name-agnostic runtime checker for the simulated variant: the simulated persona
(`uipath-maestro-flow/interactive/cli_dice_roller_simulated/cli_dice_roller_simulated.yaml`)
withholds "DiceRoller" until asked, so a correctly-built, differently named
process must still be gradable -- no name hint is passed to `find_bpmn_file()`.

Ported from Flow `_shared/check_dice_runs_simulated.py`, translated the same
way `_shared/check_jira_get_issue.py` already translates a Flow live check: a JSON node-type scan + inline `flow
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
                                  -> first whole-integer leaf in [1, 6] (an int,
                                     or a string that is only an integer; Flow's
                                     digit-run regex would read `7.5` as 5) over
                                     the root scope's Globals AND every
                                     element's Outputs in
                                     `debug-instance variables-all`
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
                    (mirrors check_jira_get_issue.py)
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

from _shared.bpmn_check import elements, fail, find_bpmn_file, resolve_project  # noqa: E402
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    debug_evidence,
    import_exact,
    output_leaves,
    require_clean_run,
)

LIVE_RUN_DIR = Path("dice-roller-simulated-live")
ROLL_LO, ROLL_HI = 1, 6
INT_RE = re.compile(r"-?\d+")

# Worst-case wall clock this checker can spend, priced the way
# _shared/test_criterion_budgets.py prices a run_debug(...) call: the debug
# call below passes timeout=600 (Flow's own run_debug timeout), so it
# prices at bpmn_live.debug_budget(600) == 600. The surrounding CLI
# steps are not priced by that guard, so their 510 s (90 init + 180 import
# + 120 variables-all + 120 incidents) is added by hand here and the
# criterion `timeout:` in
# cli_dice_roller_simulated.yaml documents the arithmetic:
#   90 (solution init) + 180 (solution import) + 600 (debug)
#   + 120 (variables-all) + 120 (incidents) = 1110
#   + bpmn_live.CRITERION_MARGIN_SECONDS (60) = 1170
# Flow's own criterion timeout (1320) already covers this, so it is kept
# verbatim rather than raised.


def find_int_in_range(leaves: list, lo: int, hi: int) -> int | None:
    """First whole-integer leaf in [lo, hi]: an int, or a string that is only
    an integer. `roll: 7.5` or a timestamp never yields a digit run.
    """
    for leaf in leaves:
        if isinstance(leaf, bool):
            continue
        if isinstance(leaf, int):
            value = leaf
        elif isinstance(leaf, str) and INT_RE.fullmatch(leaf.strip()):
            value = int(leaf.strip())
        else:
            continue
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
        fail(f"{bpmn_path} is not well-formed XML: {exc}")

    script_tasks = elements(root, "scriptTask")
    if not script_tasks:
        fail(f"{bpmn_path} has no bpmn:scriptTask element (no Script node found)")
    print(f"OK: bpmn has a scriptTask ({len(script_tasks)} found)")

    project_dir = resolve_project(os.path.basename(bpmn_path))
    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    imported_project = import_exact(
        Path(bpmn_path), project_dir, LIVE_RUN_DIR / "DiceRollerSimulatedLiveEval"
    )

    debug_data, instance_id = bpmn_live.run_debug(
        imported_project, {}, LIVE_RUN_DIR / "debug.log", timeout=600
    )
    print(f"OK: debug completed (instance {instance_id})")

    evidence = debug_evidence(instance_id)
    require_clean_run(debug_data, evidence)

    leaves = output_leaves(evidence.variables)
    roll = find_int_in_range(leaves, ROLL_LO, ROLL_HI)
    if roll is None:
        haystack = "\n".join(str(v) for v in leaves)
        fail(
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
