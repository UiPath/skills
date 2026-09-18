#!/usr/bin/env python3
"""post_run: reclaim every tenant object this run's seed.json prefix could
have created. Best-effort -- failures here never affect pass/fail (post_run
results are informational only), so this script always exits 0.

Order (folder delete is what actually reclaims the tenant --
`deploy uninstall` alone has been unreliable):
  1. Log `uip login status` for the run log.
  2. List deployments under the seeded folder path; uninstall each found
     (best-effort -- a deployment the agent never got to create is not an
     error).
  3. Delete the seeded folder itself, whether or not a deployment uninstall
     ran -- this is what actually reclaims the tenant folder + everything
     provisioned in it.
  4. Delete every package version whose name is the run's unique
     `solutionName` (from `uip solution packages list`).
  5. Delete every Studio Web solution discoverable from a `.uipx` under the
     sandbox CWD (mirrors `_shared`/`_setup/cleanup_solutions.py`'s glob),
     deduped by SolutionId so the same id is never deleted twice even if
     more than one `.uipx` under the tree points at it.
"""

from __future__ import annotations

import glob
import json
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="teardown: %(message)s")
logger = logging.getLogger(__name__)

LOGIN_STATUS_TIMEOUT = 30
DEPLOY_LIST_TIMEOUT = 60
DEPLOY_UNINSTALL_TIMEOUT = 300
FOLDER_DELETE_TIMEOUT = 60
PACKAGES_LIST_TIMEOUT = 60
PACKAGES_DELETE_TIMEOUT = 60
SOLUTION_DELETE_TIMEOUT = 60


def _run(args: list[str], timeout: int) -> dict:
    try:
        result = subprocess.run(
            [*args, "--output", "json"], capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        logger.warning("timed out: %s", " ".join(args))
        return {}
    try:
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        return {}


def _data(payload: dict) -> object:
    return payload.get("Data") if isinstance(payload, dict) else None


def uninstall_deployments(folder_path: str) -> None:
    payload = _run(
        ["uip", "solution", "deploy", "list", "--folder-path", folder_path, "--limit", "50"],
        DEPLOY_LIST_TIMEOUT,
    )
    rows = _data(payload)
    if not isinstance(rows, list) or not rows:
        logger.info("no deployments found under %s", folder_path)
        return
    for row in rows:
        name = row.get("Name") if isinstance(row, dict) else None
        if not name:
            continue
        result = _run(
            ["uip", "solution", "deploy", "uninstall", name, "--yes"],
            DEPLOY_UNINSTALL_TIMEOUT,
        )
        status = result.get("Result") if isinstance(result, dict) else None
        logger.info("uninstall %s -> %s", name, status or "unknown")


def delete_folder(folder_path: str) -> None:
    result = _run(["uip", "or", "folders", "delete", folder_path, "--yes"], FOLDER_DELETE_TIMEOUT)
    status = result.get("Result") if isinstance(result, dict) else None
    logger.info("delete folder %s -> %s", folder_path, status or "unknown/already gone")


def delete_package_versions(solution_name: str) -> None:
    payload = _run(["uip", "solution", "packages", "list", "--limit", "200"], PACKAGES_LIST_TIMEOUT)
    rows = _data(payload)
    if not isinstance(rows, list):
        logger.info("could not list packages; skipping package cleanup")
        return
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and str(row.get("name") or row.get("Name") or "") == solution_name
    ]
    for row in matches:
        version = row.get("version") or row.get("Version")
        if not version:
            continue
        result = _run(
            ["uip", "solution", "packages", "delete", solution_name, str(version), "--yes"],
            PACKAGES_DELETE_TIMEOUT,
        )
        status = result.get("Result") if isinstance(result, dict) else None
        logger.info("delete package %s %s -> %s", solution_name, version, status or "unknown")
    if not matches:
        logger.info("no published package versions named %s", solution_name)


def delete_studio_web_solutions() -> None:
    paths = glob.glob("**/*.uipx", recursive=True)
    seen: set[str] = set()
    for path in paths:
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as error:
            logger.warning("could not read %s: %s", path, error)
            continue
        solution_id = data.get("SolutionId")
        if not solution_id or solution_id in seen:
            continue
        seen.add(solution_id)
        result = _run(["uip", "solution", "delete", solution_id, "--yes"], SOLUTION_DELETE_TIMEOUT)
        status = result.get("Result") if isinstance(result, dict) else None
        logger.info("delete Studio Web solution %s (from %s) -> %s", solution_id, path, status or "not uploaded")


def main() -> int:
    _run(["uip", "login", "status"], LOGIN_STATUS_TIMEOUT)

    seed_path = Path("seed.json")
    if not seed_path.is_file():
        logger.info("no seed.json; nothing to reclaim")
        delete_studio_web_solutions()
        return 0

    try:
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        logger.warning("seed.json is not valid JSON: %s", error)
        delete_studio_web_solutions()
        return 0

    folder_path = f"{seed.get('parentFolderPath', '')}/{seed.get('folderName', '')}".strip("/")
    solution_name = seed.get("solutionName", "")

    try:
        if folder_path:
            uninstall_deployments(folder_path)
            delete_folder(folder_path)
        if solution_name:
            delete_package_versions(solution_name)
    except Exception as error:  # noqa: BLE001 - teardown must never fail the run
        logger.warning("orchestrator-side cleanup ignored error: %s", error)

    try:
        delete_studio_web_solutions()
    except Exception as error:  # noqa: BLE001 - teardown must never fail the run
        logger.warning("Studio Web cleanup ignored error: %s", error)

    return 0


if __name__ == "__main__":
    sys.exit(main())
