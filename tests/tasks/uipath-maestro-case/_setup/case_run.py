#!/usr/bin/env python3
"""Mark a task's start and cancel the debug instances it left running.

Runs from the sandbox's ``_setup``, so it stays self-contained (no ``_shared``).
Cancelling leaves no instance waiting on a human step or an SLA clock. The run
and path logic the graders use is ``_shared/case_run_path.py``, which imports
this module's instance helpers.

    python3 _setup/case_run.py --mark-task-start         # pre_run
    python3 _setup/case_run.py --cancel-debug-instances  # post_run

A task that already runs ``localize_tenant_ids.py`` as pre_run needs no mark:
the map it writes marks the start.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

TERMINAL = {"completed", "successful", "faulted", "failed", "cancelled", "canceled", "stopped"}
DONE = {"completed", "successful"}
FAILED = {"faulted", "failed", "cancelled", "canceled", "stopped"}
# Written by the task's pre_run; the first that exists marks the start of this task.
TASK_START_MARKERS = (
    os.path.join("_setup", ".task-start"),
    os.path.join("_setup", ".tenant-ids.map.json"),
)
# Debug instance ids the grader started, one per line.
DEBUG_INSTANCE_MARKER = os.path.join("_setup", ".debug-instances")
LIST_LIMIT = 500
LIST_DEADLINE_S = 180
LIST_CALL_TIMEOUT_S = 120
MAX_LIST_PAGES = 10


def _uip(args: list[str], timeout: int = 120) -> dict:
    try:
        r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True,
                           text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"Result": "Failure", "Message": repr(exc)}
    try:
        parsed = json.loads(r.stdout)
    except ValueError:
        return {"Result": "Failure", "Message": (r.stderr or r.stdout or "")[-500:]}
    return parsed if isinstance(parsed, dict) else {"Result": "Failure", "Data": parsed}


def _ci(mapping, *keys, default=None):
    if not isinstance(mapping, dict):
        return default
    lowered = {k.lower(): k for k in mapping if isinstance(k, str)}
    for key in keys:
        if key.lower() in lowered:
            return mapping[lowered[key.lower()]]
    return default


def _rows(payload: dict, *keys: str) -> list:
    data = _ci(payload, "Data")
    if isinstance(data, list):
        return data
    return _ci(data, *keys, "items", default=[]) or []


def status_of(row: dict) -> str:
    return str(_ci(row, "status", "Status") or "")


def element_of(row: dict) -> str:
    return str(_ci(row, "elementId", "ElementId") or "")


def _task_start_iso() -> str | None:
    marker = next((m for m in TASK_START_MARKERS if os.path.exists(m)), None)
    if marker is None:
        return None
    since = datetime.fromtimestamp(os.path.getmtime(marker), timezone.utc)
    return since.strftime("%Y-%m-%dT%H:%M:%S")


def _list_instances():
    """Instances started since this task did, following ``Pagination.NextPage``."""
    since = _task_start_iso()
    deadline = time.monotonic() + LIST_DEADLINE_S
    cursor = None
    for _page in range(MAX_LIST_PAGES):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        args = ["maestro", "case", "instance", "list", "--limit", str(LIST_LIMIT)]
        if since:
            args += ["--from-date", f"{since}Z"]
        if cursor:
            args += ["--next-page", cursor]
        payload = _uip(args, timeout=int(min(LIST_CALL_TIMEOUT_S, remaining)))
        yield from (row for row in _rows(payload, "Items") if isinstance(row, dict))
        pagination = _ci(payload, "Pagination") or {}
        cursor = _ci(pagination, "NextPage")
        if not _ci(pagination, "HasMore") or not cursor:
            return


def instance_folder_key(instance_id: str) -> str | None:
    for item in _list_instances():
        if str(_ci(item, "InstanceId") or "") == instance_id:
            return _ci(item, "FolderKey")
    return None


def instance_executions(instance_id: str) -> list[dict]:
    """Element executions of an instance, read from the instance itself."""
    args = ["maestro", "case", "instance", "element-executions", instance_id]
    payload = _uip(args)
    if _ci(payload, "Result") != "Success":
        folder_key = instance_folder_key(instance_id)
        if folder_key:
            payload = _uip([*args, "--folder-key", str(folder_key)])
    return [row for row in _rows(payload, "ElementExecutions") if isinstance(row, dict)]


def instance_status(instance_id: str) -> str:
    """Run status of an instance, read from the instance itself."""
    args = ["maestro", "case", "instance", "get", instance_id]
    payload = _uip(args)
    if _ci(payload, "Result") != "Success":
        folder_key = instance_folder_key(instance_id)
        if folder_key:
            payload = _uip([*args, "--folder-key", str(folder_key)])
    data = _ci(payload, "Data")
    return str(_ci(data, "status", "latestRunStatus") or "")


def instance_incidents(instance_id: str) -> list[dict]:
    """Incidents of an instance, read from the instance itself."""
    args = ["maestro", "case", "instance", "incidents", instance_id]
    payload = _uip(args)
    if _ci(payload, "Result") != "Success":
        folder_key = instance_folder_key(instance_id)
        if folder_key:
            payload = _uip([*args, "--folder-key", str(folder_key)])
    return [row for row in _rows(payload, "Incidents") if isinstance(row, dict)]


def cancel_instance(instance_id: str) -> None:
    """Best-effort: stop a parked debug instance so its human tasks and SLA timers go away."""
    args = ["maestro", "case", "instance", "cancel", instance_id, "--comment", "eval cleanup"]
    result = _uip(args)
    if _ci(result, "Result") != "Success":
        folder_key = instance_folder_key(instance_id)
        if folder_key:
            result = _uip([*args, "--folder-key", str(folder_key)])
    print(f"  cancel {instance_id}: {_ci(result, 'Result')} {_ci(result, 'Message') or ''}".rstrip())


# ── post_run: cancel this task's debug instances ─────────────────────────────


def record_debug_instance(instance_id: str) -> None:
    os.makedirs(os.path.dirname(DEBUG_INSTANCE_MARKER), exist_ok=True)
    with open(DEBUG_INSTANCE_MARKER, "a", encoding="utf-8") as fh:
        fh.write(f"{instance_id}\n")


def _recorded_instances() -> list[str]:
    try:
        with open(DEBUG_INSTANCE_MARKER, encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip()]
    except OSError:
        return []


def cancel_debug_instances() -> int:
    """Cancel the debug instances this task's graders recorded.

    The tenant is shared with parallel runs, so an instance that was not
    recorded is never touched, whatever its stages are called.
    """
    for instance_id in _recorded_instances():
        cancel_instance(instance_id)
    return 0


def mark_task_start() -> int:
    os.makedirs(os.path.dirname(TASK_START_MARKERS[0]), exist_ok=True)
    with open(TASK_START_MARKERS[0], "w", encoding="utf-8") as fh:
        fh.write(datetime.now(timezone.utc).isoformat() + "\n")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--mark-task-start"]:
        sys.exit(mark_task_start())
    if sys.argv[1:] == ["--cancel-debug-instances"]:
        try:
            sys.exit(cancel_debug_instances())
        except Exception as exc:  # post_run is informational; never fail it
            print(f"case_run: cleanup error {exc!r}")
            sys.exit(0)
    sys.exit(__doc__)
