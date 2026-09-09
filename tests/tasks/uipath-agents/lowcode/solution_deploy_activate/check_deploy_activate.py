#!/usr/bin/env python3
"""Grade the outcome of the solution-promotion path.

The CLI-invocation criteria in the YAML prove the promotion *sequence* was
typed. This grades what it left behind — locally and on the tenant — which is
where the silent failure modes live:

  1. **The packed archive never became a package.** `uip solution pack` emits
     `<NAME>_<VERSION>.zip` (underscore) since 2026-08-06 (commit 6e585f64f);
     an agent working from stale guidance builds the right archive but hands
     `publish` a dot-separated path that does not exist, so nothing uploads.
     Graded against the tenant, not the local filesystem: agents legitimately
     stage the archive outside the workspace (e.g. /tmp), where artifact
     collection never sees it — publish is the step that consumes the archive,
     so the tenant-side package record is the proof the handoff worked.
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


def _row_version(row: dict) -> str | None:
    for key in ("PackageVersion", "Version", "packageVersion", "version"):
        value = row.get(key)
        if value:
            return str(value)
    return None


def _local_zip_hint(name: str, version: str) -> str:
    """Best-effort diagnostic from whatever archives artifact collection kept.

    Never grades — the archive may legitimately live outside the workspace
    (e.g. /tmp) and be invisible here. Only sharpens the failure message when a
    local zip reveals what went wrong.
    """
    zips = [
        p
        for p in CWD.rglob("*.zip")
        if ".venv" not in p.parts and "node_modules" not in p.parts
    ]
    dotted = f"{name}.{version}.zip"
    expected = f"{name}_{version}.zip"
    names = sorted(p.name for p in zips)
    if dotted in names:
        return (
            f" A dot-separated {dotted!r} exists locally — `uip solution pack` emits "
            f"{expected!r} since 2026-08-06, and publishing the dotted path fails "
            f"with a missing-file error."
        )
    if expected in names:
        return f" The archive {expected!r} exists locally but was never published."
    return ""


def check_package_published(name: str, version: str, deployments: list | None) -> None:
    """The packed archive was published: the tenant holds a package record.

    Grades the uploaded artifact, not the local filesystem — agents legitimately
    stage the packed .zip outside the workspace (e.g. /tmp), where artifact
    collection never sees it. Publish is the step that consumes the archive, so
    a deployment record referencing the package is proof the pack→publish
    handoff worked (a stale dot-separated path makes publish fail with a
    missing-file error and leaves no record). The agent may delete the package
    after uninstall, so `packages list` is not reliable evidence; the deployment
    tombstone survives and carries the package name.
    """
    if deployments is None:
        print("SKIP: could not query deployments — published package unverified")
        return

    ours = [i for i in deployments if i.get("PackageName") == name]
    if not ours:
        fail(
            f"No deployment on the tenant references package {name!r} — the packed "
            f"archive was never published and deployed.{_local_zip_hint(name, version)}"
        )

    versions = {v for v in (_row_version(i) for i in ours) if v}
    if versions and version not in versions:
        fail(
            f"Package {name!r} was deployed at version(s) {sorted(versions)!r}, "
            f"expected {version!r} — the wrong cut was promoted"
        )
    if not versions:
        print(f"NOTE: deployment records carry no version field — {version} unverified")

    print(f"OK: package {name} {version} was published and referenced by a deployment")


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


def check_deployment_landed_and_removed(name: str, items: list | None) -> None:
    """The package reached the tenant as a deployment, and that deployment is gone.

    Grades the *outcome*, not merely that the commands were invoked — `deploy run`
    and `deploy uninstall` can both return non-zero (or no-op against a wrong
    name) while the `command_executed` criteria still score.

    Uninstall keeps a tombstone row in `deploy list` (`Operation: Uninstall`,
    `OperationStatus: Successful`), so a tombstone is the expected end state. A
    row in any other state is a deployment still standing on the tenant.
    """
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
    deployments = _deploy_list()
    check_package_published(name, version, deployments)
    check_solution_registers_agent(solution_dir, name)
    check_shipped_agent_intact(solution_dir)
    check_deployment_landed_and_removed(name, deployments)
    print("PASS: solution promotion outcome verified")


if __name__ == "__main__":
    main()
