#!/usr/bin/env python3
"""pre_run: provide a process key for tests that start jobs / attach triggers.

Three paths supported (checked in order):

1. **Env var** — if TRACES_SMOKE_PROCESS_KEY is set (CI fallback for older tests),
   the test points at a pre-seeded process. No new tenant resources are created.

2. **Solution deploy from committed .zip fixture** — if
   `tests/fixtures/packages/e2e-stub-{version}.zip` (or `-long-` variant) exists,
   publish it to the solution feed and `deploy run` it. The deploy creates an
   Orchestrator folder + process under `Shared/`. Cleanup runs
   `solution deploy uninstall`.

3. Fall through with FAIL if neither is available.

Env vars:
    TRACES_SMOKE_PROCESS_KEY    Use this pre-existing process; skip fixture flow.
    SEED_PROCESS_VERSION        Stub package version (default 1.0.0).
    SEED_PROCESS_LONG           If set/truthy, use e2e-stub-long-{version}.zip
                                (long-running variant for O6 stop/restart).
    SEED_PROCESS_FOLDER_PARENT  Parent folder for the deploy (default Shared).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from manifest import append as manifest_append
from seed_common import FIXTURES_DIR, load_or_init_seed, log, naming_prefix, save_seed, uip_json


def _seed_from_env() -> dict | None:
    key = os.environ.get("TRACES_SMOKE_PROCESS_KEY")
    if not key:
        return None
    log(f"using TRACES_SMOKE_PROCESS_KEY={key} (no new deploy)")
    envelope = uip_json("or", "processes", "get", key, check=False)
    if envelope.get("Result") != "Success":
        log(f"WARN: processes get {key} failed; using key as-is without metadata")
        return {"process_key": key, "process_source": "env"}
    data = envelope.get("Data") or {}
    return {
        "process_key": key,
        "process_source": "env",
        "process_name": data.get("Name"),
        "package_id": data.get("PackageId") or data.get("ProcessKey"),
        "package_version": data.get("PackageVersion") or data.get("CurrentVersion"),
        "folder_path": data.get("FolderPath") or data.get("FolderName"),
    }


def _resolve_stub_zip() -> Path | None:
    """Return the path to the .zip fixture matching env-var selection, or None."""
    version = os.environ.get("SEED_PROCESS_VERSION", "1.0.0")
    if os.environ.get("SEED_PROCESS_LONG", "").lower() in ("1", "true", "yes"):
        filename = f"e2e-stub-long-{version}.zip"
    else:
        filename = f"e2e-stub-{version}.zip"
    path = FIXTURES_DIR / "packages" / filename
    return path if path.is_file() else None


def _seed_from_zip(zip_path: Path) -> dict | None:
    seed = load_or_init_seed()
    prefix = naming_prefix(seed)
    parent = os.environ.get("SEED_PROCESS_FOLDER_PARENT", "Shared")

    # 1) Publish the .zip to the solution feed. Idempotent on duplicate-version.
    publish = uip_json("solution", "publish", str(zip_path), check=False)
    if publish.get("Result") != "Success":
        msg = (publish.get("Message") or "").lower()
        if "already exists" in msg or "duplicate" in msg or "conflict" in msg:
            log(f"package already published — continuing")
        else:
            log(f"FAIL: solution publish {zip_path.name}: {publish}")
            return None
    pub_data = publish.get("Data") or {}
    package_name = pub_data.get("PackageName") or "e2e-stub"
    package_version = pub_data.get("PackageVersion") or os.environ.get("SEED_PROCESS_VERSION", "1.0.0")
    log(f"OK published {package_name} v{package_version}")

    # Optional: publish a second version so O4 (process rollback) can exercise
    # update-version → rollback against two real versions.
    if os.environ.get("SEED_PROCESS_TWO_VERSIONS", "").lower() in ("1", "true", "yes"):
        other_version = "1.0.1" if package_version == "1.0.0" else "1.0.0"
        other_zip = FIXTURES_DIR / "packages" / f"e2e-stub-{other_version}.zip"
        if other_zip.is_file():
            extra = uip_json("solution", "publish", str(other_zip), check=False)
            if extra.get("Result") == "Success":
                log(f"OK also published v{other_version}")
            else:
                log(f"WARN: second-version publish skipped — {extra.get('Message')}")
        else:
            log(f"WARN: SEED_PROCESS_TWO_VERSIONS set but {other_zip.name} missing")

    # 2) Deploy with unique names tied to the per-run uuid8 prefix.
    deployment_name = f"{prefix}-deploy"
    folder_name = f"{prefix}-folder"
    deploy = uip_json(
        "solution", "deploy", "run",
        "--name", deployment_name,
        "--package-name", package_name,
        "--package-version", package_version,
        "--folder-name", folder_name,
        "--folder-path", parent,
        timeout=420,
    )
    deploy_data = deploy.get("Data") or {}
    folder_path = deploy_data.get("FolderPath") or f"{parent}/{folder_name}"
    log(f"OK deployed {deployment_name} -> {folder_path}")

    # Record for post_run uninstall. (Folder + processes get cleaned up by uninstall.)
    manifest_append("deploy", deployment_name)

    # 3) Discover the process key inside the new folder.
    procs = uip_json("or", "processes", "list", "--folder-path", folder_path)
    items = procs.get("Data") or []
    if not items:
        log(f"FAIL: no processes found in {folder_path} after deploy")
        return None
    proc = items[0]
    process_key = proc.get("Key") or proc.get("Id")
    if not process_key:
        log(f"FAIL: first process missing Key: {proc}")
        return None
    log(f"OK process key {process_key} in {folder_path}")

    return {
        "process_key": process_key,
        "process_source": "deploy",
        "process_name": proc.get("Name"),
        "package_id": package_name,
        "package_version": package_version,
        "folder_path": folder_path,
        "deployment_name": deployment_name,
    }


def main() -> int:
    seed = load_or_init_seed()
    if "process_key" in seed:
        log(f"skip: process_key already in seed.json ({seed['process_key']})")
        return 0

    # Env var path takes precedence (legacy compatibility with traces tests).
    info = _seed_from_env()
    if info is None:
        zip_path = _resolve_stub_zip()
        if zip_path is None:
            log(
                "FAIL: cannot seed a process — set TRACES_SMOKE_PROCESS_KEY, "
                "or commit a stub .zip under tests/fixtures/packages/. "
                f"(version={os.environ.get('SEED_PROCESS_VERSION', '1.0.0')}, "
                f"long={os.environ.get('SEED_PROCESS_LONG', '')})"
            )
            return 1
        log(f"using fixture {zip_path.name}")
        info = _seed_from_zip(zip_path)
        if info is None:
            return 1

    seed.update(info)
    save_seed(seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
