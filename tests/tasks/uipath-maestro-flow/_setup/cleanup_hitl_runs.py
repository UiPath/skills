#!/usr/bin/env python3
"""Cancel the debug instances and open Action Center tasks a HITL e2e run left behind.

`mark` (pre_run) records the start time. `clean` (post_run) lists open tasks and
touches only those created at or after that time that carry a token the grader
recorded in `.hitl-run-tokens`. Parallel tasks share the eval identity, so the
creator never marks a task as this run's. Each line is `token` or
`token instanceId`: it cancels each instance recorded by id, then completes each
task so it leaves the inbox. Best-effort: always exits 0.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Callable

START_FILE = ".hitl-run-start"
TOKENS_FILE = ".hitl-run-tokens"  # written by _shared/hitl_live_run.py
CLEANUP_ENV = "FLOW_E2E_CLEANUP"
CLEANUP_NEVER = "never"
CALL_TIMEOUT = 120
CLOSE_ACTIONS = ("Reject", "reject", "Cancel")

Runner = Callable[[list[str]], dict | None]


def run_uip(args: list[str]) -> dict | None:
    try:
        r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=CALL_TIMEOUT)
        data = json.loads(r.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    ok = r.returncode == 0 and isinstance(data, dict) and data.get("Result") == "Success"
    return data if ok else None


def parse_time(text: object) -> datetime | None:
    raw = str(text or "").strip().replace("Z", "+00:00")
    head, plus, tail = raw.partition("+")
    if "." in head:
        whole, _dot, frac = head.partition(".")
        head = f"{whole}.{frac[:6]}"
    try:
        parsed = datetime.fromisoformat(head + plus + tail)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def mark() -> None:
    with open(START_FILE, "w") as f:
        f.write(datetime.now(timezone.utc).isoformat())


def read_lines(path: str) -> list[str]:
    if not os.path.isfile(path):
        return []
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]


def data_rows(envelope: dict | None) -> list[dict]:
    rows = (envelope or {}).get("Data")
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def is_open(row: dict) -> bool:
    return str(row.get("Status") or "").lower() != "completed" and not row.get("IsDeleted") and not row.get("IsCompleted")


def own_tasks(rows: list[dict], started: datetime, tokens: list[str], task_text: Callable[[dict], str]) -> list[dict]:
    mine = []
    for row in rows:
        created = parse_time(row.get("CreatedTime"))
        if not is_open(row) or created is None or created < started:
            continue
        if any(t in task_text(row) for t in tokens):
            mine.append(row)
    return mine


def cancel_instances(instance_ids: list[str], uip: Runner) -> None:
    for instance in instance_ids:
        uip(["maestro", "flow", "debug-instance", "cancel", instance])


def close_task(task: dict, email: str, uip: Runner) -> bool:
    task_id = str(task.get("Id"))
    folder = str(task.get("FolderId") or "")
    if email:
        verb = "reassign" if task.get("AssignedToUserKey") else "assign"
        uip(["tasks", verb, task_id, "--user", email])
    for action in CLOSE_ACTIONS:
        done = uip(["tasks", "complete", task_id, "--type", str(task.get("Type") or "FormTask"),
                    "--folder-id", folder, "--action", action, "--data", "{}"])
        if done is not None:
            return True
    return False


def clean(uip: Runner | None = None, cwd: str = ".") -> list[str]:
    uip = uip or run_uip
    if os.environ.get(CLEANUP_ENV, "").lower() == CLEANUP_NEVER:
        return []
    marker = read_lines(os.path.join(cwd, START_FILE))
    started = parse_time(marker[0]) if marker else None
    if started is None:
        return []
    entries = [line.split() for line in read_lines(os.path.join(cwd, TOKENS_FILE))]
    tokens = list(dict.fromkeys(e[0] for e in entries))
    instances = list(dict.fromkeys(e[1] for e in entries if len(e) > 1))
    me = (uip(["login", "status"]) or {}).get("Data") or {}
    email = str(me.get("UserEmail") or me.get("UserName") or "")

    def task_text(row: dict) -> str:
        data = uip(["tasks", "data", "get", str(row.get("Id")), "--folder-id", str(row.get("FolderId") or "")])
        return json.dumps(data) + str(row.get("Title") or "")

    tasks = own_tasks(data_rows(uip(["tasks", "list"])), started, tokens, task_text)
    cancel_instances(instances, uip)
    return [str(t.get("Id")) for t in tasks if close_task(t, email, uip)]


def main(argv: list[str]) -> int:
    try:
        if argv[1:] == ["mark"]:
            mark()
        elif argv[1:] == ["clean"]:
            print(f"cleanup_hitl_runs: closed tasks {clean()}")
    except Exception as e:
        print(f"cleanup_hitl_runs: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
