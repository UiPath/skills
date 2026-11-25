"""What a `uip maestro case debug` run did, read back from its instance.

`case debug` returns element statuses only. The values sit on the debug
instance, which `uip maestro case instance variables-all <id> --folder-key <key>`
returns:

- `Data.Variables[]` holds one block per scope. The root block
  (`ParentElementId` null) has `Globals`, every case variable by id, and
  `GlobalDefinitions[id].Name`, the name the plan gives it.
- A task's own runtime `Inputs` / `Outputs` are on its element (`ElementId` is
  the plan's task id), in the block of the stage's tasks subprocess.
- The CLI PascalCases every key, nested ones too (`echoResponse.json.probe`
  comes back as `EchoResponse.Json.Probe`), so every read here ignores case.

The folder key comes from `uip maestro case instance list`, which lists Studio
Web Debug instances across folders. Shapes as recorded from real debug runs in
single_node/http_request/testdata/http_run_evidence.json.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import _get_ci, _parse_json, _run  # noqa: E402

LIST_ATTEMPTS = 6
LIST_SLEEP_S = 5
LIST_DEADLINE_S = 180
LIST_CALL_TIMEOUT_S = 180


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def since_iso(minutes: int = 30) -> str:
    """A `--from-date` safely before the debug run starts."""
    start = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    return start.strftime("%Y-%m-%dT%H:%M:%SZ")


READ_TIMEOUT_S = 180


def _uip(args: list[str], what: str) -> Any:
    r = _run(["uip", *args, "--output", "json"], timeout=READ_TIMEOUT_S, what=what)
    data = _parse_json(r.stdout)
    if r.returncode != 0 or not isinstance(data, dict) or data.get("Result") != "Success":
        fail(f"{what} failed (exit {r.returncode}): {(r.stdout or r.stderr)[:1500]}")
    return data.get("Data")


def folder_key_of(instance_id: str, since: str) -> str:
    """The folder the debug instance runs in (the invoker's personal workspace)."""
    deadline = time.monotonic() + LIST_DEADLINE_S
    for attempt in range(LIST_ATTEMPTS):
        cursor = None
        for _page in range(10):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            args = ["maestro", "case", "instance", "list", "--from-date", since, "--limit", "500"]
            if cursor:
                args += ["--next-page", cursor]
            r = _run(["uip", *args, "--output", "json"], timeout=min(LIST_CALL_TIMEOUT_S, remaining),
                     what="uip maestro case instance list")
            envelope = _parse_json(r.stdout) or {}
            items = envelope.get("Data") or []
            if isinstance(items, dict):
                items = items.get("Items") or items.get("items") or []
            for item in items:
                if str(_get_ci(item, "InstanceId")) == instance_id:
                    return str(_get_ci(item, "FolderKey"))
            pagination = envelope.get("Pagination") or {}
            cursor = pagination.get("NextPage")
            if not pagination.get("HasMore") or not cursor:
                break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        if attempt < LIST_ATTEMPTS - 1:
            time.sleep(min(LIST_SLEEP_S, remaining))
    fail(f"debug instance {instance_id} is not in `uip maestro case instance list --from-date {since}`")


class RunEvidence:
    """Case variables by name and task elements by id, from `variables-all` Data."""

    def __init__(self, variables_all: Any):
        self.folder_key: str | None = None  # set by read_run: the folder the instance runs in
        blocks = _get_ci(variables_all or {}, "Variables") or []
        if isinstance(variables_all, dict) and not blocks and "Globals" in variables_all:
            blocks = [variables_all]
        self.globals: dict = {}
        self.definitions: dict = {}
        self.elements: dict[str, list[dict]] = {}
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if _get_ci(block, "ParentElementId") is None:
                self.globals.update(_get_ci(block, "Globals") or {})
                self.definitions.update(_get_ci(block, "GlobalDefinitions") or {})
            for element in _get_ci(block, "Elements") or []:
                element_id = str(_get_ci(element, "ElementId") or "")
                self.elements.setdefault(element_id, []).append(element)

    def has(self, name: str) -> bool:
        return self._key(name) is not None

    def value(self, name: str) -> Any:
        """The case variable the plan calls ``name``; fails when the run has none."""
        key = self._key(name)
        if key is None:
            known = sorted(
                str(_get_ci(d, "Name")) for d in self.definitions.values() if isinstance(d, dict)
            )
            fail(f"the run has no case variable named {name!r}; it has {known}")
        return self.globals.get(key)

    def _key(self, name: str) -> str | None:
        wanted = name.lower()
        for key, definition in self.definitions.items():
            if isinstance(definition, dict) and str(_get_ci(definition, "Name") or "").lower() == wanted:
                return key
        for key in self.globals:
            if key.lower() == wanted:
                return key
        return None

    def task_io(self, task_id: str) -> tuple[dict, dict]:
        """(Inputs, Outputs) of the task's last run; fails when it never ran."""
        if not self.elements.get(task_id):
            fail(f"the run has no inputs or outputs for task {task_id}")
        return self.task_io_or_empty(task_id)

    def task_io_or_empty(self, task_id: str) -> tuple[dict, dict]:
        runs = self.elements.get(task_id) or []
        if not runs:
            return {}, {}
        last = runs[-1]
        return (_get_ci(last, "Inputs") or {}), (_get_ci(last, "Outputs") or {})


def read_run(payload: dict, since: str) -> RunEvidence:
    instance_id = str(_get_ci(payload, "instanceId", "InstanceId") or "")
    if not instance_id:
        fail(f"case debug returned no instanceId: {json.dumps(payload, default=str)[:600]}")
    folder_key = folder_key_of(instance_id, since)
    data = _uip(
        ["maestro", "case", "instance", "variables-all", instance_id, "--folder-key", folder_key],
        "uip maestro case instance variables-all",
    )
    evidence = RunEvidence(data)
    evidence.folder_key = folder_key
    return evidence


def ci(value: Any, *path: str) -> Any:
    """Follow ``path`` through nested dicts, ignoring key case; None when absent."""
    for key in path:
        if not isinstance(value, dict):
            return None
        value = _get_ci(value, key)
    return value


def text_of(value: Any) -> str:
    return json.dumps(value, default=str).lower()


def leaf_values(value: Any, key: str):
    """Every value stored under ``key`` (any case) anywhere in ``value``."""
    if isinstance(value, dict):
        for k, v in value.items():
            if str(k).lower() == key.lower():
                yield v
            yield from leaf_values(v, key)
    elif isinstance(value, list):
        for item in value:
            yield from leaf_values(item, key)


def execution_of(payload: dict, task_id: str) -> dict | None:
    runs = [
        e for e in _get_ci(payload, "elementExecutions", "ElementExecutions") or []
        if _get_ci(e, "elementId", "ElementId") == task_id
    ]
    return runs[-1] if runs else None


def assert_completed(payload: dict, task: dict) -> dict:
    execution = execution_of(payload, str(task.get("id")))
    name = task.get("displayName")
    if execution is None:
        fail(f"task {name!r} (id {task.get('id')}) did not run")
    status = _get_ci(execution, "status", "Status")
    if status not in ("Completed", "Successful"):
        fail(f"task {name!r} finished {status!r}")
    return execution
