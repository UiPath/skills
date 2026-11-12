#!/usr/bin/env python3
"""Assert the runtime profile of the project that owns a named ``.flow``.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/project_profile.py --flow-name InvoiceIntake \
        --expect-profile Lite --expect-sentinel
    python3 .../project_profile.py --flow-name Plain --expect-profile Standard \
        --expect-no-sentinel

Scoped to ONE project on purpose. A bare ``find . -name .maestro_automate``
passes when any unrelated scaffold carries the marker, which does not show that
the project the task asked for is a Maestro Automate one.

Project resolution mirrors the CLI: the ``.flow`` may sit in the project root
or under ``content/`` / ``flow_files/`` (and ``project.uiproj``'s ``MainFile``
may nest it deeper still), so this climbs to the nearest enclosing
``project.uiproj`` rather than assuming a depth.

The profile is read from ``operate.json``. A Studio Web project has no
``operate.json`` at design time; there the marker decides (see ``read_profile``).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SENTINEL = ".maestro_automate"
PROJECT_FILE = "project.uiproj"
STUDIO_WEB_FLOW_FILE = "new.flow"
MAX_CLIMB = 16


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def find_flow(flow_name: str) -> list[Path]:
    # Studio Web names the main file new.flow in a project called flow_name.
    return sorted([*Path(".").rglob(f"{flow_name}.flow"), *Path(".").rglob(f"{flow_name}/new.flow")])


def project_dir_for(flow_path: Path) -> Path:
    current = flow_path.parent.resolve()
    for _ in range(MAX_CLIMB):
        if (current / PROJECT_FILE).is_file():
            return current
        if current.parent == current:
            break
        current = current.parent
    return flow_path.parent.resolve()


def read_profile(project: Path, flow_path: Path) -> tuple[str | None, str]:
    """The project's runtime profile and where it was read from.

    ``operate.json`` wins when the project has one: the CLI's ``flow init``
    writes it. A Studio Web project has none at design time, so its profile is
    the one packaging derives from the marker: Lite with it, Standard without.
    Only a Studio Web project (main file ``new.flow``) takes that route; a CLI
    project that lost its ``operate.json`` still fails.
    """
    operate = project / "operate.json"
    if operate.is_file():
        try:
            data = json.loads(operate.read_text())
        except json.JSONDecodeError as err:
            raise ValueError(f"{operate} is not valid JSON: {err}") from err
        return (data.get("runtimeOptions") or {}).get("profile"), f"{operate} runtimeOptions.profile"
    if flow_path.name != STUDIO_WEB_FLOW_FILE:
        raise ValueError(f"no operate.json in {project}")
    marker = project / SENTINEL
    return ("Lite" if marker.is_file() else "Standard"), f"{marker} ({'present' if marker.is_file() else 'absent'})"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow-name", required=True)
    parser.add_argument("--expect-profile", choices=["Lite", "Standard"])
    sentinel = parser.add_mutually_exclusive_group()
    sentinel.add_argument("--expect-sentinel", action="store_true")
    sentinel.add_argument("--expect-no-sentinel", action="store_true")
    args = parser.parse_args()

    matches = find_flow(args.flow_name)
    if not matches:
        return fail(f"no {args.flow_name}.flow anywhere under {Path.cwd()}")
    if len({p.resolve() for p in matches}) > 1:
        return fail(f"{args.flow_name}.flow is ambiguous: {matches}")

    project = project_dir_for(matches[0])
    marker = (project / SENTINEL).is_file()

    if args.expect_sentinel and not marker:
        return fail(f"no {SENTINEL} in {project}")
    if args.expect_no_sentinel and marker:
        return fail(f"unexpected {SENTINEL} in {project}")

    if args.expect_profile:
        try:
            found, source = read_profile(project, matches[0])
        except ValueError as err:
            return fail(str(err))
        if found != args.expect_profile:
            return fail(f"{source} gives profile {found!r}, expected {args.expect_profile!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
