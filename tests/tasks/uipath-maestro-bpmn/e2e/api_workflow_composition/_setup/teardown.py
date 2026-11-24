#!/usr/bin/env python3
"""post_run: reclaim every tenant object this run's seed.json prefix could
have created. Best-effort -- failures here never affect pass/fail (post_run
results are informational only), so this script always exits 0.

Order (folder delete is what actually reclaims the tenant --
`deploy uninstall` alone has been unreliable):
  1. Log `uip login status` for the run log.
  2. Uninstall every deployment of the run's `solutionName` package, in any
     folder (agents may deploy straight into `parentFolderPath`), or sitting
     in a run folder: the seeded folder and every folder under
     `parentFolderPath` whose name contains `runId` (deepest first). Then
     delete those folders.
  3. Delete the run's `solutionName` package, latest version first, until
     `uip solution packages list --name` returns none.
  4. Delete the Studio Web solutions named exactly `solutionName` and created
     within the last MAX_SOLUTION_AGE. The ids and creation times come from
     `uip solution list`, not from a `.uipx` in the sandbox, so neither a
     manifest copied in from another solution nor a seed.json edited to name
     an older one can select it.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="teardown: %(message)s")
logger = logging.getLogger(__name__)

LOGIN_STATUS_TIMEOUT = 30
DEPLOY_LIST_TIMEOUT = 60
DEPLOY_UNINSTALL_TIMEOUT = 120
FOLDER_DELETE_TIMEOUT = 60
PACKAGES_LIST_TIMEOUT = 60
PACKAGES_DELETE_TIMEOUT = 60
SOLUTION_DELETE_TIMEOUT = 60
SOLUTION_LIST_TIMEOUT = 60
FOLDERS_LIST_TIMEOUT = 60

UNINSTALL_EXIT_GRACE = 15

PAGE_SIZE = 100
MAX_PAGES = 20
MAX_PACKAGE_VERSIONS = 10
SUCCESS = "Success"

# Both tasks that mount this teardown cap the agent at 3900s and grading adds
# under an hour, so a solution older than this was not created by this run.
MAX_SOLUTION_AGE = timedelta(hours=4)

# post_run is killed at 300s (api_workflow_composition.yaml); stop short so
# later phases are skipped cleanly instead of killed mid-call.
POST_RUN_BUDGET_SECONDS = 280
DEADLINE = time.monotonic() + POST_RUN_BUDGET_SECONDS


def _run(args: list[str], timeout: int) -> dict:
    remaining = int(DEADLINE - time.monotonic())
    if remaining <= 0:
        logger.warning("deadline reached, skipped: %s", " ".join(args))
        return {}
    try:
        result = subprocess.run(
            [*args, "--output", "json"], capture_output=True, text=True, timeout=min(timeout, remaining)
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


def _list_all(args: list[str], timeout: int) -> list:
    rows: list = []
    for page in range(MAX_PAGES):
        payload = _run([*args, "--limit", str(PAGE_SIZE), "--offset", str(page * PAGE_SIZE)], timeout)
        data = _data(payload)
        if not isinstance(data, list):
            return rows
        rows += data
        pagination = payload.get("Pagination") or {}
        if not pagination.get("HasMore", len(data) == PAGE_SIZE):
            return rows
    logger.warning("stopped after %d pages: %s", MAX_PAGES, " ".join(args))
    return rows


def run_folder_paths(parent_folder_path: str, run_id: str) -> list[str]:
    rows = _list_all(
        ["uip", "or", "folders", "list", "--all", "--path", parent_folder_path, "--name", run_id],
        FOLDERS_LIST_TIMEOUT,
    )
    paths = {
        str(row.get("Path"))
        for row in rows
        if isinstance(row, dict) and row.get("Path") and run_id in str(row.get("Name") or "")
    }
    return sorted(paths, key=lambda path: path.count("/"), reverse=True)


def uninstall_deployments(solution_name: str, folder_paths: list[str]) -> None:
    rows = _list_all(["uip", "solution", "deploy", "list"], DEPLOY_LIST_TIMEOUT)
    names = sorted({
        row["Name"]
        for row in rows
        if isinstance(row, dict)
        and row.get("Name")
        and (row.get("PackageName") == solution_name or row.get("FolderPath") in folder_paths)
    })
    if not names:
        logger.info("no deployments found for %s", solution_name)
        return
    for name in names:
        result = _run(
            ["uip", "solution", "deploy", "uninstall", name, "--yes", "--timeout", str(DEPLOY_UNINSTALL_TIMEOUT)],
            DEPLOY_UNINSTALL_TIMEOUT + UNINSTALL_EXIT_GRACE,
        )
        status = result.get("Result") if isinstance(result, dict) else None
        logger.info("uninstall %s -> %s", name, status or "unknown")


def delete_folder(folder_path: str) -> None:
    result = _run(["uip", "or", "folders", "delete", folder_path, "--yes"], FOLDER_DELETE_TIMEOUT)
    status = result.get("Result") if isinstance(result, dict) else None
    logger.info("delete folder %s -> %s", folder_path, status or "unknown/already gone")


def delete_package_versions(solution_name: str) -> None:
    for _ in range(MAX_PACKAGE_VERSIONS):
        rows = _list_all(["uip", "solution", "packages", "list", "--name", solution_name], PACKAGES_LIST_TIMEOUT)
        latest = next(
            (row.get("LatestVersion") for row in rows if isinstance(row, dict) and row.get("Name") == solution_name),
            None,
        )
        if not latest:
            logger.info("no published package versions left for %s", solution_name)
            return
        result = _run(
            ["uip", "solution", "packages", "delete", solution_name, str(latest), "--yes"],
            PACKAGES_DELETE_TIMEOUT,
        )
        status = result.get("Result") if isinstance(result, dict) else None
        logger.info("delete package %s %s -> %s", solution_name, latest, status or "unknown")
        if status != SUCCESS:
            return
    logger.warning("stopped after %d package versions: %s", MAX_PACKAGE_VERSIONS, solution_name)


def created_within_run_window(row: dict, now: datetime) -> bool:
    try:
        created = datetime.fromisoformat(str(row.get("CreationTime") or "").replace("Z", "+00:00"))
    except ValueError:
        return False
    if created.tzinfo is None:
        return False
    return timedelta(minutes=-5) <= now - created <= MAX_SOLUTION_AGE


def run_solution_ids(solution_name: str) -> list[str]:
    rows = _list_all(["uip", "solution", "list", "--name", solution_name], SOLUTION_LIST_TIMEOUT)
    now = datetime.now(timezone.utc)
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or not row.get("Id"):
            continue
        if str(row.get("Name") or "").casefold() != solution_name.casefold():
            continue
        if created_within_run_window(row, now):
            ids.add(str(row["Id"]))
        else:
            logger.warning(
                "keep Studio Web solution %s (%s): CreationTime %s is not within this run",
                row["Id"], solution_name, row.get("CreationTime"),
            )
    return sorted(ids)


def delete_studio_web_solutions(solution_name: str) -> None:
    solution_ids = run_solution_ids(solution_name)
    if not solution_ids:
        logger.info("no Studio Web solution named %s", solution_name)
    for solution_id in solution_ids:
        result = _run(["uip", "solution", "delete", solution_id, "--yes"], SOLUTION_DELETE_TIMEOUT)
        status = result.get("Result") if isinstance(result, dict) else None
        logger.info("delete Studio Web solution %s (%s) -> %s", solution_id, solution_name, status or "unknown")


def main() -> int:
    _run(["uip", "login", "status"], LOGIN_STATUS_TIMEOUT)

    seed_path = Path("seed.json")
    if not seed_path.is_file():
        logger.info("no seed.json; nothing to reclaim")
        return 0

    try:
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        logger.warning("seed.json is not valid JSON: %s", error)
        return 0

    parent_folder_path = seed.get("parentFolderPath", "")
    folder_path = f"{parent_folder_path}/{seed.get('folderName', '')}".strip("/")
    solution_name = seed.get("solutionName", "")
    run_id = seed.get("runId", "")

    try:
        folder_paths = run_folder_paths(parent_folder_path, run_id) if parent_folder_path and run_id else []
        if folder_path and folder_path not in folder_paths:
            folder_paths.append(folder_path)
        uninstall_deployments(solution_name, folder_paths)
        for path in folder_paths:
            delete_folder(path)
        if solution_name:
            delete_package_versions(solution_name)
    except Exception as error:  # noqa: BLE001 - teardown must never fail the run
        logger.warning("orchestrator-side cleanup ignored error: %s", error)

    try:
        if solution_name:
            delete_studio_web_solutions(solution_name)
    except Exception as error:  # noqa: BLE001 - teardown must never fail the run
        logger.warning("Studio Web cleanup ignored error: %s", error)

    return 0


if __name__ == "__main__":
    sys.exit(main())
