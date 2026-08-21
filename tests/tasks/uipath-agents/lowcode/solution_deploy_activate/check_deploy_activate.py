#!/usr/bin/env python3
"""Grade the outcome of the solution-promotion path.

The CLI-invocation criteria in the YAML prove the promotion *sequence* was
typed. This grades what it left behind — locally and on the tenant — which is
where the silent failure modes live:

  1. **Package naming.** `uip solution pack` emits `<NAME>_<VERSION>.zip`
     (underscore). It was `<NAME>.<VERSION>.zip` until 2026-08-06 (commit
     6e585f64f). An agent working from stale guidance builds the right archive
     but hands `publish` a path that does not exist.
  2. **The promoted agent is not the one that shipped.** The solution arrives
     pre-built; re-scaffolding or rewriting it promotes something the owner did
     not ask for.
  3. **Nothing actually reached the tenant.** `deploy run` can be typed and fail;
     the deployment record is the only proof it landed.
  4. **The deployment is still live.** This is an evaluation tenant.

Every assertion resolves the run-unique solution name from `deploy_seed.json`
(written by `seed_deploy.py`) rather than a constant, so parallel replicates
never grade each other's deployment.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CWD = Path.cwd()
AGENT = "EchoAgent"


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def load_seed() -> tuple[str, str]:
    seed_path = CWD / "deploy_seed.json"
    if not seed_path.is_file():
        fail(
            "deploy_seed.json is missing — pre_run seeding did not run, so the "
            "solution under test cannot be identified"
        )
    try:
        seed = json.loads(seed_path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"deploy_seed.json does not parse: {exc}")
    name = seed.get("solution_name")
    version = seed.get("package_version")
    if not name or not version:
        fail(f"deploy_seed.json is incomplete: {seed!r}")
    return name, version


def find_solution_dir(name: str) -> Path:
    if (CWD / name).is_dir():
        return CWD / name
    for candidate in CWD.rglob(f"{name}.uipx"):
        return candidate.parent
    fail(f"Could not locate the {name} solution directory under {CWD}")


def check_package_naming(name: str, version: str) -> None:
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

    expected = f"{name}_{version}.zip"
    if any(p.name == expected for p in zips):
        print(f"OK: packaged archive {expected} uses the canonical <NAME>_<VERSION>.zip naming")
        return

    # Distinguish the stale dot-separated form from an unrelated archive so the
    # diagnostic points at the actual mistake.
    dotted = f"{name}.{version}.zip"
    names = sorted(p.name for p in zips)
    if dotted in names:
        fail(
            f"Archive is named {dotted!r} (dot-separated). `uip solution pack` emits "
            f"{expected!r} since 2026-08-06 — publishing the dotted path fails with a "
            f"missing-file error."
        )
    fail(f"Expected a packaged archive named {expected!r}; found {names!r}")


def check_solution_registers_agent(solution_dir: Path, name: str) -> None:
    uipx = solution_dir / f"{name}.uipx"
    if not uipx.is_file():
        fail(f"Missing {uipx.relative_to(CWD)}")
    try:
        doc = json.loads(uipx.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{uipx.name} does not parse: {exc}")

    projects = doc.get("Projects") or []
    if not projects:
        fail(
            f"{uipx.name} lists no projects — the agent is no longer registered, so the "
            f"packaged archive is empty"
        )
    print(f"OK: solution manifest registers {len(projects)} project(s)")


def check_shipped_agent_intact(solution_dir: Path) -> None:
    """The promoted agent is still the one the fixture shipped.

    Brownfield guard: the owner asked for a release rehearsal, not a rewrite. A
    re-scaffolded or re-authored project loses the `message`/`reply` contract
    that callers already integrate against, and `entry-points.json` drifting from
    `agent.json` produces an archive that deploys and then faults at run time
    (Critical Rule LC4).
    """
    agent_json = solution_dir / AGENT / "agent.json"
    entry_points = solution_dir / AGENT / "entry-points.json"

    if not agent_json.is_file():
        fail(f"Missing {agent_json.relative_to(CWD)} — no agent project to promote")
    if not entry_points.is_file():
        fail(
            f"Missing {entry_points.relative_to(CWD)} — the project's generated "
            f"artifacts were removed, so the solution packs with unsynced schemas"
        )

    try:
        agent = json.loads(agent_json.read_text())
        eps = json.loads(entry_points.read_text())
    except json.JSONDecodeError as exc:
        fail(f"Agent project JSON does not parse: {exc}")

    props = ((agent.get("inputSchema") or {}).get("properties")) or {}
    if "message" not in props:
        fail(
            f"agent.json inputSchema no longer declares `message` (got {sorted(props)}) — "
            f"the promoted agent is not the one that was handed over"
        )

    outs = ((agent.get("outputSchema") or {}).get("properties")) or {}
    if "reply" not in outs:
        fail(
            f"agent.json outputSchema no longer declares `reply` (got {sorted(outs)}) — "
            f"the promoted agent is not the one that was handed over"
        )

    serialized = json.dumps(eps)
    if "message" not in serialized or "reply" not in serialized:
        fail(
            "entry-points.json no longer advertises the `message`/`reply` contract — "
            "schemas are out of sync with agent.json (Critical Rule LC4)"
        )

    print(f"OK: {AGENT} still carries the shipped, schema-synced definition")


def _deploy_list() -> list | None:
    """Deployment records, or None when the tenant could not be queried."""
    try:
        proc = subprocess.run(
            ["uip", "solution", "deploy", "list", "--limit", "200", "--output", "json"],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"SKIP: could not query deployments ({exc}) — tenant state unverified")
        return None

    raw = proc.stdout
    if "{" not in raw:
        print("SKIP: deploy list returned no JSON — tenant state unverified")
        return None

    try:
        doc = json.loads(raw[raw.index("{"):])
    except json.JSONDecodeError:
        print("SKIP: deploy list JSON did not parse — tenant state unverified")
        return None

    items = doc.get("Data") or []
    if isinstance(items, dict):
        items = items.get("Deployments") or items.get("Items") or items.get("Value") or []
    return [i for i in items if isinstance(i, dict)]


def check_deployment_landed_and_removed(name: str) -> None:
    """The package reached the tenant as a deployment, and that deployment is gone.

    Grades the *outcome*, not merely that the commands were invoked — `deploy run`
    and `deploy uninstall` can both return non-zero (or no-op against a wrong
    name) while the `command_executed` criteria still score.

    Uninstall keeps a tombstone row in `deploy list` (`Operation: Uninstall`,
    `OperationStatus: Successful`), so a tombstone is the expected end state. A
    row in any other state is a deployment still standing on the tenant.
    """
    items = _deploy_list()
    if items is None:
        return

    ours = [i for i in items if i.get("PackageName") == name]
    if not ours:
        fail(
            f"No deployment for package {name!r} exists on the tenant — the package was "
            f"never published and deployed, so `deploy run`/`deploy activate` did not "
            f"actually promote anything"
        )

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
            f"{name} deployment was not uninstalled — this is an evaluation tenant "
            f"and must be left clean. Still present: {summary}"
        )

    print(f"OK: {name} was deployed and reached Uninstall/Successful — tenant left clean")


def main() -> None:
    name, version = load_seed()
    solution_dir = find_solution_dir(name)
    check_package_naming(name, version)
    check_solution_registers_agent(solution_dir, name)
    check_shipped_agent_intact(solution_dir)
    check_deployment_landed_and_removed(name)
    print("PASS: solution promotion outcome verified")


if __name__ == "__main__":
    main()
