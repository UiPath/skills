#!/usr/bin/env python3
"""pre_run: provide a process key for tests that start jobs / attach triggers.

Two paths supported (checked in order):

1. **Env var** — if TRACES_SMOKE_PROCESS_KEY is set (CI mode), the test points at
   the pre-seeded traces process. seed.json is populated with that key; no new
   tenant resources are created.

2. **Stub upload** — if tests/fixtures/packages/e2e-stub.{VER}.nupkg exists,
   upload it and create a fresh process under Shared/. (Requires `uip codedagent`
   or equivalent packing — see fixtures/build_fixtures.sh.)

If neither path is available, exits non-zero so the task fails early with a clear
"can't seed a process" message rather than getting halfway through.

Env vars:
    TRACES_SMOKE_PROCESS_KEY    Use this existing process (preferred for CI).
    SEED_PROCESS_VERSION        Stub package version to upload (default 1.0.0).
    SEED_PROCESS_FOLDER         Folder path to create the process in (default Shared).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_common import FIXTURES_DIR, load_or_init_seed, log, naming_prefix, save_seed, uip_json
from manifest import append as manifest_append


def _seed_from_env() -> dict | None:
    """Use the existing process referenced by env var, no tenant mutation."""
    key = os.environ.get("TRACES_SMOKE_PROCESS_KEY")
    if not key:
        return None
    log(f"using TRACES_SMOKE_PROCESS_KEY={key} (no new process created)")
    # Look up package/folder details by fetching the process
    envelope = uip_json("or", "processes", "get", key, check=False)
    if envelope.get("Result") != "Success":
        log(f"WARN: processes get {key} failed; using key as-is without package metadata")
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


def _seed_from_stub() -> dict | None:
    """Upload stub package and create a fresh process. Returns None if stub fixtures missing."""
    version = os.environ.get("SEED_PROCESS_VERSION", "1.0.0")
    stub_path = FIXTURES_DIR / "packages" / f"e2e-stub.{version}.nupkg"
    if not stub_path.is_file():
        log(f"stub fixture missing at {stub_path} — falling through")
        return None

    seed = load_or_init_seed()
    prefix = naming_prefix(seed)
    folder = os.environ.get("SEED_PROCESS_FOLDER", "Shared")

    # Upload (idempotent on "version already exists")
    upload = uip_json("or", "packages", "upload", str(stub_path), check=False)
    if upload.get("Result") != "Success":
        msg = (upload.get("Message") or "").lower()
        if "already exists" in msg or "duplicate" in msg:
            log(f"stub package already uploaded — continuing")
        else:
            log(f"FAIL: stub upload failed: {upload}")
            return None
    else:
        log(f"OK uploaded stub from {stub_path.name}")

    # Discover the package id (from the .nupkg filename or upload response)
    package_id = (upload.get("Data") or {}).get("Title") or "e2e-stub"
    package_key = f"{package_id}:{version}"

    # Create the process
    process_name = f"{prefix}-proc"
    create = uip_json(
        "or", "processes", "create",
        "--name", process_name,
        "--package-key", package_id,
        "--package-version", version,
        "--folder-path", folder,
    )
    data = create.get("Data") or {}
    process_key = data.get("Key") or data.get("Id")
    if not process_key:
        log(f"FAIL: processes create returned no key: {create}")
        return None
    manifest_append("process", process_key, folder_path=folder)
    log(f"OK created process {process_name} key={process_key}")
    return {
        "process_key": process_key,
        "process_source": "stub",
        "process_name": process_name,
        "package_id": package_id,
        "package_version": version,
        "package_key": package_key,
        "folder_path": folder,
    }


def main() -> int:
    seed = load_or_init_seed()
    if "process_key" in seed:
        log(f"skip: process_key already in seed.json ({seed['process_key']})")
        return 0

    info = _seed_from_env() or _seed_from_stub()
    if info is None:
        log(
            "FAIL: cannot seed a process — set TRACES_SMOKE_PROCESS_KEY env var, "
            "or build stub fixtures via tests/fixtures/build_fixtures.sh"
        )
        return 1

    seed.update(info)
    save_seed(seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
