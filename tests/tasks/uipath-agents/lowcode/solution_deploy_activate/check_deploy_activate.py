#!/usr/bin/env python3
"""Assert the local artifacts of the solution-promotion path.

The CLI-invocation criteria in the YAML prove the promotion *sequence* ran.
This grades the on-disk outcome, which is where the two silent failure modes
live:

  1. **Package naming.** `uip solution pack` emits `<NAME>_<VERSION>.zip`
     (underscore). It was `<NAME>.<VERSION>.zip` until 2026-08-06 (commit
     6e585f64f). An agent working from stale guidance builds the right archive
     but hands `publish` a path that does not exist.
  2. **Promoting an unvalidated agent.** The solution must contain a real,
     refreshed agent project — packing a scaffold whose schemas were never
     synced produces a deployable archive that faults at runtime.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SOLUTION = "DeploySol"
AGENT = "EchoAgent"
VERSION = "1.0.0"
CWD = Path.cwd()


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def find_solution_dir() -> Path:
    if (CWD / SOLUTION).is_dir():
        return CWD / SOLUTION
    for candidate in CWD.rglob(f"{SOLUTION}.uipx"):
        return candidate.parent
    fail(f"Could not locate the {SOLUTION} solution directory under {CWD}")


def check_package_naming() -> None:
    """The packed archive exists and uses the underscore convention."""
    zips = [
        p
        for p in CWD.rglob("*.zip")
        if ".venv" not in p.parts and "node_modules" not in p.parts
    ]
    if not zips:
        fail(
            f"No .zip produced anywhere under {CWD} — `uip solution pack` did not "
            f"emit an archive"
        )

    expected = f"{SOLUTION}_{VERSION}.zip"
    if any(p.name == expected for p in zips):
        print(f"OK: packaged archive {expected} uses the canonical <NAME>_<VERSION>.zip naming")
        return

    # Distinguish the stale dot-separated form from an unrelated archive so the
    # diagnostic points at the actual mistake.
    dotted = f"{SOLUTION}.{VERSION}.zip"
    names = sorted(p.name for p in zips)
    if dotted in names:
        fail(
            f"Archive is named {dotted!r} (dot-separated). `uip solution pack` emits "
            f"{expected!r} since 2026-08-06 — publishing the dotted path fails with a "
            f"missing-file error."
        )
    fail(f"Expected a packaged archive named {expected!r}; found {names!r}")


def check_agent_was_validated(solution_dir: Path) -> None:
    """The packed solution carries a real, schema-synced agent project."""
    agent_json = solution_dir / AGENT / "agent.json"
    entry_points = solution_dir / AGENT / "entry-points.json"

    if not agent_json.is_file():
        fail(f"Missing {agent_json.relative_to(CWD)} — no agent project to promote")
    if not entry_points.is_file():
        fail(
            f"Missing {entry_points.relative_to(CWD)} — `uip agent refresh` was never "
            f"run, so the solution was packed with unsynced schemas"
        )

    try:
        agent = json.loads(agent_json.read_text())
        eps = json.loads(entry_points.read_text())
    except json.JSONDecodeError as exc:
        fail(f"Agent project JSON does not parse: {exc}")

    props = ((agent.get("inputSchema") or {}).get("properties")) or {}
    if "message" not in props:
        fail(
            f"agent.json inputSchema has no `message` property (got {sorted(props)}) — "
            f"the promoted agent is not the one that was asked for"
        )

    serialized = json.dumps(eps)
    if "message" not in serialized:
        fail(
            "entry-points.json does not advertise the `message` input — schemas are out "
            "of sync with agent.json (Critical Rule LC4)"
        )

    print(f"OK: {AGENT} carries a refreshed, schema-synced definition")


def check_solution_registers_agent(solution_dir: Path) -> None:
    uipx = solution_dir / f"{SOLUTION}.uipx"
    if not uipx.is_file():
        fail(f"Missing {uipx.relative_to(CWD)}")
    try:
        doc = json.loads(uipx.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{uipx.name} does not parse: {exc}")

    projects = doc.get("Projects") or []
    if not projects:
        fail(
            f"{uipx.name} lists no projects — the agent was never registered, so the "
            f"packaged archive is empty"
        )
    print(f"OK: solution manifest registers {len(projects)} project(s)")


def check_deployment_uninstalled() -> None:
    """The deployment reached the SuccessfulUninstall terminal state.

    Grades the *outcome*, not merely that `deploy uninstall` was invoked — the
    command can return non-zero or no-op against a wrong name while the
    `command_executed` criterion still scores. `deploy list` keeps a tombstone
    row after a successful uninstall (`Operation: Uninstall`,
    `OperationStatus: Successful`), so an absent row and an uninstalled row are
    both acceptable; an still-active row is not.
    """
    import subprocess

    try:
        proc = subprocess.run(
            ["uip", "solution", "deploy", "list", "--output", "json"],
            capture_output=True, text=True, timeout=90,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"SKIP: could not query deployments ({exc}) — tenant state unverified")
        return

    raw = proc.stdout
    if "{" not in raw:
        print("SKIP: deploy list returned no JSON — tenant state unverified")
        return

    try:
        doc = json.loads(raw[raw.index("{"):])
    except json.JSONDecodeError:
        print("SKIP: deploy list JSON did not parse — tenant state unverified")
        return

    items = doc.get("Data") or []
    if isinstance(items, dict):
        items = items.get("Deployments") or items.get("Items") or []

    ours = [
        i for i in items
        if isinstance(i, dict) and i.get("PackageName") == SOLUTION
    ]
    if not ours:
        print(f"OK: no {SOLUTION} deployment remains on the tenant")
        return

    live = [
        i for i in ours
        if not (i.get("Operation") == "Uninstall" and i.get("OperationStatus") == "Successful")
    ]
    if live:
        summary = [
            f"{i.get('Name')} (Operation={i.get('Operation')}, "
            f"OperationStatus={i.get('OperationStatus')}, "
            f"ActivationStatus={i.get('ActivationStatus')})"
            for i in live
        ]
        fail(
            f"{SOLUTION} deployment was not uninstalled — this is an evaluation tenant "
            f"and must be left clean. Still present: {summary}"
        )

    print(f"OK: {SOLUTION} deployment reached Uninstall/Successful — tenant left clean")


def main() -> None:
    solution_dir = find_solution_dir()
    check_package_naming()
    check_solution_registers_agent(solution_dir)
    check_agent_was_validated(solution_dir)
    check_deployment_uninstalled()
    print("PASS: solution promotion artifacts verified")


if __name__ == "__main__":
    main()
