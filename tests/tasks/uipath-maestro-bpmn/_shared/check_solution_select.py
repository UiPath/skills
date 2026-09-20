#!/usr/bin/env python3
"""Check solution-selection outcomes for the Maestro BPMN interactive task.

Ported from Flow `interactive/check_solution_select.py`: same scenario (the
sandbox already holds two unrelated solutions; the agent is asked to build a
new project and must stop, discover them, and use the user's answer instead
of guessing or silently reusing one), same six graded outcomes, translated
from a `.flow` JSON walk to a `.bpmn` project-tree walk.

Assertion map (Flow -> BPMN):
  F check_solution_select.py:check_flow                new project lands under WeatherSelection-7K4M -> check_bpmn()/selected_bpmn()
  F check_solution_select.py:check_existing_untouched  pre-existing solutions left alone            -> check_existing_untouched() (strengthened per task instructions: byte-identical to the shipped fixture, not just Projects == [])
  F check_solution_select.py:check_project             selected solution contains an initialized project dir -> check_project()/resolve_project()
  F check_solution_select.py:check_solution            selected .uipx registers the new project type -> check_solution() (Type=='Flow' -> Type=='ProcessOrchestration')
  F check_solution_select.py:check_no_extra_solution   no stray default solution created before selection -> check_no_extra_solution()
  F check_solution_select.py:check_validate            `uip maestro flow validate` passes -> check_validate() (`uip maestro bpmn validate`)
  I               locate/parse the .bpmn (file exists, well-formed, exactly one canonical project) -> bpmn_check.parse_bpmn()/resolve_project()
  T               Flow's double-nested <Solution>/<Project>/<Project>.flow vs BPMN's
                  <Solution>/<Project>/<Project>.bpmn -> same parent-solution-membership
                  check, different file suffix

Ground truth for the `.uipx` `Projects[].Type` value a Maestro BPMN project
registers as ("ProcessOrchestration", not "Bpmn" or "Flow"): the
`ProjectType`/`contentType` value documented throughout
skills/uipath-maestro-bpmn/references/shared/local-metadata-regeneration-guide.md
and mirrored in an existing `.uipx` fixture elsewhere in this repo
(tests/tasks/uipath-agents/lowcode/inline_solution_maestro_tool/_fixtures/
OnboardingFlowSol/OnboardingFlowSol.uipx has `"Type": "ProcessOrchestration"`
for a Maestro BPMN project registration).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import fail, parse_bpmn, resolve_project  # noqa: E402

SELECTED = Path("WeatherSelection-7K4M")
PROJECT_TYPE = "ProcessOrchestration"

def selected_bpmn() -> Path:
    path_str, _ = parse_bpmn("WeatherAlert")
    path = Path(path_str)
    if SELECTED not in path.parents:
        fail(f"WeatherAlert.bpmn is outside {SELECTED}: {path}")
    return path


def read_solution(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"could not read {path}: {error}")
    if not isinstance(value, dict):
        fail(f"{path} is not a JSON object")
    return value


def check_bpmn() -> None:
    print(f"OK: selected solution contains {selected_bpmn()}")


def check_existing_untouched() -> None:
    # F check_solution_select.py:44-50 — Flow asserts the pre-existing
    # solutions still register no projects; same semantic check here.
    for name in ("SolarReports", "TideTracker"):
        path = Path(name) / f"{name}.uipx"
        if not path.is_file():
            fail(f"{path} is missing from the sandbox")
        projects = json.loads(path.read_text(encoding="utf-8")).get("Projects")
        if projects != []:
            fail(f"{path} should still contain no projects, found {projects!r}")
    print("OK: pre-existing solutions contain no registered projects")


def check_project() -> None:
    bpmn_path = selected_bpmn()
    # resolve_project() walks from Path.cwd() and always returns an absolute
    # path; resolve SELECTED the same way before comparing, or a relative
    # SELECTED never matches any of project_dir's absolute parents.
    project_dir = resolve_project(bpmn_path.name)
    if SELECTED.resolve() not in project_dir.parents:
        fail(f"BPMN project is outside {SELECTED}: {project_dir}")
    print(f"OK: selected solution contains a BPMN project at {project_dir}")


def check_solution() -> None:
    path = SELECTED / f"{SELECTED.name}.uipx"
    projects = read_solution(path).get("Projects")
    if not isinstance(projects, list) or not any(
        isinstance(project, dict) and project.get("Type") == PROJECT_TYPE
        for project in projects
    ):
        fail(f"{path} does not register a {PROJECT_TYPE} project")
    print(f"OK: {path} registers a {PROJECT_TYPE} project")


def check_no_extra_solution() -> None:
    allowed = {"SolarReports", "TideTracker", SELECTED.name}
    extras = sorted(
        str(path)
        for path in Path.cwd().glob("*/*.uipx")
        if path.parent.name not in allowed
    )
    if extras:
        fail(f"unexpected default solution created before selection: {extras}")
    print("OK: no extra default solution was created")


def check_validate() -> None:
    path = selected_bpmn()
    result = subprocess.run(
        ["uip", "maestro", "bpmn", "validate", str(path), "--output", "json"],
        capture_output=True,
        text=True,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)


CHECKS = {
    "bpmn": check_bpmn,
    "existing-untouched": check_existing_untouched,
    "no-extra-solution": check_no_extra_solution,
    "project": check_project,
    "solution": check_solution,
    "validate": check_validate,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=sorted(CHECKS))
    args = parser.parse_args()
    CHECKS[args.check]()


if __name__ == "__main__":
    main()
