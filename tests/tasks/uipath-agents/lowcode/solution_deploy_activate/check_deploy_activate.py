#!/usr/bin/env python3
"""Grade the outcome of the solution-promotion path.

The CLI-invocation criteria in the YAML prove the promotion *sequence* was
typed. This grades what it left behind — locally and on the tenant — which is
where the silent failure modes live:

  1. **The packed archive never became a package.** `uip solution pack` emits
     `<NAME>_<VERSION>.zip` (underscore) since 2026-08-06 (commit 6e585f64f);
     an agent working from stale guidance builds the right archive but hands
     `publish` a dot-separated path that does not exist, so nothing uploads.
     Detectable only while a tenant record survives (see below).
  2. **The wrong package was promoted.** Packing with `--name <other>` publishes
     and deploys a package that is not the seeded `<NAME>`.
  3. **The promoted agent is not the one that shipped.** The solution arrives
     pre-built; re-scaffolding or rewriting it promotes something the owner did
     not ask for.
  4. **The deployment is still live.** This is an evaluation tenant.

Tenant end state after a correct run is one of:

  * an `Uninstall`/`Successful` tombstone row in `deploy list` (agent stopped
    after `deploy uninstall`), or
  * no deployment row at all — `uip solution deploy delete` removes the
    tombstone (prescribed by `project-lifecycle.md` § Uninstall Deployment, and
    asked for by the prompt), and agents often `packages delete` too.

A fully torn-down tenant holds no record that a deployment ever existed, so the
tenant alone cannot prove publish/deploy happened. Proof is layered:

  * a surviving deployment row or package record is graded here (name,
    version, live state);
  * when the tenant is clean, the YAML's `publish`, `deploy run
    --skip-activate`, `deploy activate` and `deploy uninstall` criteria
    (pass_threshold 1.0 each) carry the proof that the steps ran, and this
    check fails if local archives of *this* solution (matched by its
    run-unique `SolutionId`) show it was packed only under another name.

Every assertion resolves the run-unique solution name from `deploy_seed.json`
(written by `seed_deploy.py`) rather than a constant, so parallel replicates
never grade each other's deployment. The decision logic is the pure function
`grade_promotion`, so it can be replayed against recorded `deploy list` /
`packages list` outputs without a tenant.
"""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
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


class GradeFailure(Exception):
    """Raised by `grade_promotion`; `main` turns it into a FAIL exit."""


def _rows_for(name: str, items: list | None, key: str) -> list[dict]:
    return [i for i in (items or []) if isinstance(i, dict) and i.get(key) == name]


def _is_tombstone(row: dict) -> bool:
    return row.get("Operation") == "Uninstall" and row.get("OperationStatus") == "Successful"


def grade_promotion(
    name: str,
    version: str,
    deployments: list | None,
    packages: list | None,
    archives: list[dict],
    zip_hint: str = "",
) -> list[str]:
    """Decide the tenant-side verdict. Pure: no I/O.

    `deployments`: rows from `uip solution deploy list` (None = query failed).
    `packages`: rows from `uip solution packages list --name <name>` (None =
    query failed or not run). `archives`: `{"file", "packageName",
    "packageVersion"}` for each local archive whose `solutionMetadata.json`
    names this run's `SolutionId`. Returns the OK/NOTE lines; raises
    `GradeFailure` with the failure message.
    """
    if deployments is None:
        return ["SKIP: could not query deployments — tenant state unverified"]

    ours = _rows_for(name, deployments, "PackageName")
    if ours:
        versions = {v for v in (_row_version(i) for i in ours) if v}
        if versions and version not in versions:
            raise GradeFailure(
                f"Package {name!r} was deployed at version(s) {sorted(versions)!r}, "
                f"expected {version!r} — the wrong cut was promoted"
            )
        live = [i for i in ours if not _is_tombstone(i)]
        if live:
            summary = [
                f"{i.get('Name')} (Operation={i.get('Operation')}, "
                f"OperationStatus={i.get('OperationStatus')}, "
                f"ActivationStatus={i.get('ActivationStatus')})"
                for i in live
            ]
            raise GradeFailure(
                f"{name} deployment was not uninstalled — this is an evaluation tenant "
                f"and must be left clean. Still present: {summary}"
            )
        lines = [f"OK: package {name} {version} was published and referenced by a deployment"]
        if not versions:
            lines.append(f"NOTE: deployment records carry no version field — {version} unverified")
        lines.append(f"OK: {name} was deployed and reached Uninstall/Successful — tenant left clean")
        return lines

    # No deployment row: either `deploy delete` removed the tombstone (expected
    # end state) or nothing was ever deployed. The tenant cannot tell these
    # apart; rule out what local and package evidence can.
    off_name = sorted({a["packageName"] for a in archives if a.get("packageName") != name})
    on_name = [a for a in archives if a.get("packageName") == name]
    if off_name and not on_name:
        raise GradeFailure(
            f"No deployment on the tenant references package {name!r} — the packed "
            f"archive was never published and deployed. This solution was packed as "
            f"{off_name!r} instead of the seeded {name!r}, so the wrong package was promoted."
            f"{zip_hint}"
        )

    pkg_rows = _rows_for(name, packages, "Name")
    if pkg_rows:
        pkg_versions = {
            str(r.get("LatestVersion") or r.get("Version") or "") for r in pkg_rows
        } - {""}
        if pkg_versions and version not in pkg_versions:
            raise GradeFailure(
                f"Package {name!r} is on the tenant at version(s) {sorted(pkg_versions)!r}, "
                f"expected {version!r} — the wrong cut was published"
            )
        return [
            f"OK: package {name} {version} is published on the tenant",
            f"OK: no deployment row for {name} — removed by `deploy delete` after "
            f"uninstall; tenant left clean (deploy steps graded by the YAML criteria)",
        ]

    note = "" if packages is not None else " (packages list unavailable)"
    return [
        f"OK: no deployment or package for {name} remains on the tenant{note} — "
        f"consistent with full teardown (uninstall, `deploy delete`, `packages delete`)",
        "NOTE: a clean tenant carries no record of the deployment; publish/deploy/"
        "activate/uninstall are graded by the YAML command criteria",
    ]


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


def _packages_list(name: str) -> list | None:
    """Package records matching `name`, or None when the tenant could not be queried."""
    try:
        proc = subprocess.run(
            ["uip", "solution", "packages", "list", "--name", name,
             "--limit", "50", "--output", "json"],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    raw = proc.stdout
    if "{" not in raw:
        return None
    try:
        doc = json.loads(raw[raw.index("{"):])
    except json.JSONDecodeError:
        return None
    if doc.get("Result") != "Success":
        return None
    items = doc.get("Data") or []
    return [i for i in items if isinstance(i, dict)]


def _solution_id(solution_dir: Path, name: str) -> str | None:
    try:
        return json.loads((solution_dir / f"{name}.uipx").read_text()).get("SolutionId")
    except (OSError, json.JSONDecodeError, AttributeError):
        return None


def _local_archives(solution_id: str | None) -> list[dict]:
    """Packed archives of THIS solution, found in the workspace or /tmp.

    Matched by `solutionMetadata.json` `spec.projectKey` == the run-unique
    `SolutionId` (re-minted by `seed_deploy.py`), so archives from other runs
    sharing /tmp are ignored. Best-effort: archives staged where this check
    cannot see them are simply absent.
    """
    if not solution_id:
        return []
    candidates = [
        p for p in CWD.rglob("*.zip")
        if ".venv" not in p.parts and "node_modules" not in p.parts
    ]
    tmp = Path("/tmp")
    if tmp.is_dir() and tmp.resolve() != CWD.resolve():
        for pattern in ("*.zip", "*/*.zip", "*/*/*.zip"):
            try:
                candidates.extend(tmp.glob(pattern))
            except OSError:
                pass
    found, seen = [], set()
    for path in candidates:
        try:
            key = path.resolve()
            if key in seen:
                continue
            seen.add(key)
            with zipfile.ZipFile(path) as zf:
                spec = json.loads(zf.read("solutionMetadata.json")).get("spec") or {}
        except (OSError, KeyError, zipfile.BadZipFile, json.JSONDecodeError, AttributeError):
            continue
        if spec.get("projectKey") == solution_id:
            found.append({
                "file": str(path),
                "packageName": spec.get("packageName"),
                "packageVersion": spec.get("packageVersion"),
            })
    return found


def main() -> None:
    name, version = load_seed()
    solution_dir = find_solution_dir(name)
    deployments = _deploy_list()
    packages = None
    if deployments is not None and not _rows_for(name, deployments, "PackageName"):
        packages = _packages_list(name)
    archives = _local_archives(_solution_id(solution_dir, name))
    try:
        lines = grade_promotion(
            name, version, deployments, packages, archives, _local_zip_hint(name, version)
        )
    except GradeFailure as exc:
        fail(str(exc))
    check_solution_registers_agent(solution_dir, name)
    check_shipped_agent_intact(solution_dir)
    for line in lines:
        print(line)
    print("PASS: solution promotion outcome verified")


if __name__ == "__main__":
    main()
