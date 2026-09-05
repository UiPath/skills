#!/usr/bin/env python3
"""Check solution-selection outcomes without depending on authoring commands."""

from __future__ import annotations

import argparse
import json
import subprocess
import os
import sys
from pathlib import Path

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-flow")
    if os.environ.get("SKILLS_REPO_PATH")
    else str(Path(__file__).resolve().parents[1])
)
sys.path.insert(0, _shared_root)
from _shared.flow_check import find_flow_file, find_project_dir  # noqa: E402

SELECTED = Path("WeatherSelection-7K4M")
PROJECT_PATTERN = "WeatherSelection-7K4M/**/project.uiproj"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def selected_flow() -> Path:
    path = Path(find_flow_file(PROJECT_PATTERN, flow_glob="WeatherAlert.flow"))
    if SELECTED not in path.parents:
        fail(f"WeatherAlert.flow is outside {SELECTED}: {path}")
    return path


def read_solution(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"could not read {path}: {error}")
    if not isinstance(value, dict):
        fail(f"{path} is not a JSON object")
    return value


def check_flow() -> None:
    print(f"OK: selected solution contains {selected_flow()}")


def check_existing_untouched() -> None:
    for name in ("SolarReports", "TideTracker"):
        path = Path(name) / f"{name}.uipx"
        projects = read_solution(path).get("Projects")
        if projects != []:
            fail(f"{path} should still contain no projects, found {projects!r}")
    print("OK: pre-existing solutions contain no registered projects")


def check_project() -> None:
    project_dir = Path(find_project_dir(PROJECT_PATTERN))
    if SELECTED not in project_dir.parents:
        fail(f"Flow project is outside {SELECTED}: {project_dir}")
    print(f"OK: selected solution contains a Flow project at {project_dir}")


def check_solution() -> None:
    path = SELECTED / f"{SELECTED.name}.uipx"
    projects = read_solution(path).get("Projects")
    if not isinstance(projects, list) or not any(
        project.get("Type") == "Flow"
        for project in projects
        if isinstance(project, dict)
    ):
        fail(f"{path} does not register a Flow project")
    print(f"OK: {path} registers a Flow project")


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
    path = selected_flow()
    result = subprocess.run(
        ["uip", "maestro", "flow", "validate", str(path), "--output", "json"],
        capture_output=True,
        text=True,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)


CHECKS = {
    "existing-untouched": check_existing_untouched,
    "flow": check_flow,
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
