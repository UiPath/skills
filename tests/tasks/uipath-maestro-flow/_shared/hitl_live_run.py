#!/usr/bin/env python3
"""Run a Flow whose path waits on a human task, and play the human.

`run_debug` cannot grade a HITL flow: the run suspends on the Action Center
task, so `uip maestro flow debug` either polls until its own timeout or returns
early when the Orchestrator job reports `Suspended`. Neither ends `Completed`. This helper:

1. starts `uip maestro flow debug` in the background and reads the personal
   folder, job key and instance id from its stderr log lines
   (`Personal folder — key: <k>, id: <n>`, `Debug session started — jobKey: <k>`,
   `Debug instance created — instanceId: <id>`);
2. polls `uip tasks list` for an open task this run created (`CreatorJobKey`
   on the row is the run's job key, or a per-run marker is in the task data).
   A quick form's task lands in the run's personal folder, an app task in the
   app's own folder (`Shared/uipath-agents/ExpenseReviewSol`), so the caller's
   folder paths are listed too, and now and then every folder;
3. completes it with the chosen outcome (`uip tasks complete`). `--data`
   replaces the task's data, so it carries only the form's own fields: the
   `Data` object inside the record `uip tasks data get` prints, plus the
   answers. Sending the whole record faults the run with 170001 "Failure
   mapping the data from the task result";
4. waits for the run to finish: the CLI's own envelope when it is still
   polling, else `uip maestro flow debug-instance status` / `variables`, and
   returns a payload shaped like `run_debug`'s `Data` (`finalStatus`,
   `elementExecutions`, `variables`), so the `flow_check` assertions read it.

After `bound_calls_by(deadline)`, each bounded `uip` call outlives the deadline
by at most MIN_CALL_SECONDS, so a grader's criterion timeout can be sized from
its deadlines; `cancel` is exempt, since it must run after a missed deadline.

Used by the uipath-human-in-the-loop e2e tasks only.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Callable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flow_check  # noqa: E402
from flow_check import _get_ci, _leaves, _parse_json  # noqa: E402

FOLDER_RE = re.compile(r"Personal folder\W+key:\s*([0-9a-fA-F-]{36}),\s*id:\s*(\d+)")
JOB_RE = re.compile(r"Debug session started\W+jobKey:\s*([0-9a-fA-F-]{36})")
INSTANCE_RE = re.compile(r"Debug instance created\W+instanceId:\s*([0-9a-fA-F-]{36})")
PIMS_TERMINAL = {"completed", "faulted", "cancelled", "canceled", "failed"}
TASK_POLL_SECONDS = 10
STATUS_POLL_SECONDS = 5
MAX_CANDIDATES = 25
FOLDER_GRACE_SECONDS = 60
ALL_FOLDERS_EVERY = 6  # polls; the tenant-wide list is ~5 MB, so not every poll
MIN_CALL_SECONDS = 30
DEADLINE_SECONDS = 600
CLI_TIMEOUT = 540
END_TYPE = "core.control.end"
TOKENS_FILE = ".hitl-run-tokens"  # read by _setup/cleanup_hitl_runs.py
_call_deadline: float | None = None


def bound_calls_by(deadline: float | None) -> None:
    """Cap each later bounded `uip` call at the time left before `deadline`."""
    global _call_deadline
    _call_deadline = deadline


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def uip_json(args: list[str], timeout: int = 90, *, bounded: bool = True) -> dict | None:
    """Run `uip <args> --output json`; the parsed envelope, or None."""
    if bounded and _call_deadline is not None:
        timeout = min(timeout, max(MIN_CALL_SECONDS, int(_call_deadline - time.monotonic())))
    try:
        r = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        print(f"note: `uip {' '.join(args)}` timed out after {timeout}s", file=sys.stderr)
        return None
    data = _parse_json(r.stdout)
    if r.returncode != 0 or data is None or _get_ci(data, "Result") != "Success":
        print(
            f"note: `uip {' '.join(args)}` exit {r.returncode}: "
            f"{(r.stdout or '')[-600:]} {(r.stderr or '')[-400:]}",
            file=sys.stderr,
        )
        return data if data is not None and r.returncode == 0 else None
    return data


def text_leaves(value: Any) -> list[str]:
    return [str(v) for v in _leaves(value) if v is not None]


def has_amount(value: Any, amount: float) -> bool:
    """True when a leaf equals `amount`, as a number or as text (with or
    without thousands separators or trailing zeros)."""
    for leaf in _leaves(value):
        if isinstance(leaf, bool):
            continue
        if isinstance(leaf, (int, float)) and abs(float(leaf) - amount) < 0.005:
            return True
        if isinstance(leaf, str):
            for token in re.findall(r"\d[\d,]*(?:\.\d+)?", leaf):
                try:
                    if abs(float(token.replace(",", "")) - amount) < 0.005:
                        return True
                except ValueError:
                    continue
    return False


def has_text(value: Any, needle: str) -> bool:
    folded = needle.casefold()
    return any(folded in leaf.casefold() for leaf in text_leaves(value))


def row_job_keys(row: dict) -> set[str]:
    keys = {
        str(_get_ci(row, "CreatorJobKey") or ""),
        str(_get_ci(row, "WaitJobKey") or ""),
    }
    source = _get_ci(row, "TaskSource") or {}
    if isinstance(source, dict):
        keys.add(str(_get_ci(source, "SourceId") or ""))
    return {k.lower() for k in keys if k and not k.startswith("00000000")}


def is_open(row: dict) -> bool:
    status = str(_get_ci(row, "Status") or "").lower()
    return status != "completed" and not _get_ci(row, "IsDeleted") and not _get_ci(row, "IsCompleted")


@dataclass
class RunIds:
    folder_key: str | None = None
    folder_id: str | None = None
    job_key: str | None = None
    instance_id: str | None = None

    def read(self, text: str) -> None:
        if m := FOLDER_RE.search(text):
            self.folder_key, self.folder_id = m.group(1), m.group(2)
        if m := JOB_RE.search(text):
            self.job_key = m.group(1)
        if m := INSTANCE_RE.search(text):
            self.instance_id = m.group(1)


@dataclass
class FoundTask:
    row: dict
    data: Any
    folder_id: str

    @property
    def task_id(self) -> str:
        return str(_get_ci(self.row, "Id"))

    @property
    def task_type(self) -> str:
        return str(_get_ci(self.row, "Type") or "")


@dataclass
class DebugRun:
    proc: subprocess.Popen
    stdout_path: str
    stderr_path: str
    ids: RunIds = field(default_factory=RunIds)
    stdout_file: Any = None
    stderr_file: Any = None
    out_dir: str | None = None

    def stderr(self) -> str:
        try:
            with open(self.stderr_path, encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return ""

    def stdout(self) -> str:
        try:
            with open(self.stdout_path, encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return ""

    def refresh_ids(self) -> RunIds:
        self.ids.read(self.stderr())
        envelope = _parse_json(self.stdout()) if self.proc.poll() is not None else None
        data = _get_ci(envelope or {}, "Data") or {}
        if isinstance(data, dict):
            self.ids.instance_id = self.ids.instance_id or _get_ci(data, "instanceId", "InstanceId")
            self.ids.job_key = self.ids.job_key or _get_ci(data, "jobKey", "JobKey")
        return self.ids

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
        for handle in (self.stdout_file, self.stderr_file):
            if handle is not None:
                handle.close()

    def finish(self) -> None:
        self.stop()
        if self.out_dir:
            shutil.rmtree(self.out_dir, ignore_errors=True)


def start_debug(project_dir: str, inputs: dict, cli_timeout: int) -> DebugRun:
    out_dir = tempfile.mkdtemp(prefix="hitl-debug-")
    stdout_path = os.path.join(out_dir, "stdout.json")
    stderr_path = os.path.join(out_dir, "stderr.log")
    env = dict(os.environ)
    env["UIP_LOG_LEVEL"] = "info"
    cmd = [
        "uip", "maestro", "flow", "debug", project_dir,
        "--output", "json",
        "--inputs", json.dumps(inputs),
        "--timeout", str(cli_timeout),
    ]
    print(f"debug inputs: {inputs}")
    stdout_file = open(stdout_path, "w")
    stderr_file = open(stderr_path, "w")
    try:
        proc = subprocess.Popen(cmd, stdout=stdout_file, stderr=stderr_file, env=env)
    except BaseException:
        stdout_file.close()
        stderr_file.close()
        shutil.rmtree(out_dir, ignore_errors=True)
        raise
    return DebugRun(proc, stdout_path, stderr_path, stdout_file=stdout_file, stderr_file=stderr_file, out_dir=out_dir)


def wait_for_ids(run: DebugRun, deadline: float) -> RunIds:
    """Block until the CLI has named the folder and the run, or has exited.
    Once the run is named, wait FOLDER_GRACE_SECONDS more for the folder."""
    named_at = None
    while time.monotonic() < deadline:
        ids = run.refresh_ids()
        if ids.folder_id and (ids.job_key or ids.instance_id):
            return ids
        if ids.job_key or ids.instance_id:
            named_at = named_at if named_at is not None else time.monotonic()
            if time.monotonic() - named_at >= FOLDER_GRACE_SECONDS:
                return ids
        if run.proc.poll() is not None:
            return run.refresh_ids()
        time.sleep(3)
    return run.refresh_ids()


def list_tasks(
    folder_id: str | None, *, as_admin: bool = False, folder_path: str | None = None
) -> list[dict]:
    """`uip tasks list` rows of one folder (by id or path), or of every folder
    the grader can see when neither is given."""
    args = ["tasks", "list"]
    if folder_id:
        args += ["--folder-id", str(folder_id)]
    elif folder_path:
        args += ["--folder-path", folder_path]
    if as_admin:
        args.append("--as-admin")
    data = uip_json(args, timeout=120)
    rows = _get_ci(data or {}, "Data") or []
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def task_data(task_id: str, folder_id: str) -> Any:
    """The task's form data. `uip tasks data get` prints the whole task record
    (Status, Action, TaskSource, Id, ...) with the form data under `Data`."""
    envelope = uip_json(["tasks", "data", "get", str(task_id), "--folder-id", str(folder_id)])
    return form_data(_get_ci(envelope or {}, "Data"))


def form_data(record: Any) -> Any:
    if isinstance(record, dict) and isinstance(_get_ci(record, "Data"), dict):
        return _get_ci(record, "Data")
    return record


def node_folder_paths(node: dict) -> list[str]:
    """Folder paths a HITL node names (an app task's `inputs.app.folderPath`)."""
    found: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for k, v in value.items():
                if str(k).lower() == "folderpath" and isinstance(v, str) and "/" in v:
                    found.append(v)
                else:
                    walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)

    walk(node.get("inputs") or {})
    return list(dict.fromkeys(found))


def find_run_task(
    ids: RunIds,
    matches: Callable[[dict, Any], bool],
    deadline: float,
    run: DebugRun,
    *,
    folder_paths: tuple[str, ...] | list[str] = (),
    lister: Callable[..., list[dict]] = list_tasks,
    data_reader: Callable[[str, str], Any] = task_data,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[FoundTask | None, list[str]]:
    """Poll for the open task this run created. A row carrying the run's job
    key, or an open row whose data `matches`, is the run's task. Lists the
    run's folder and `folder_paths` each poll, and every folder each
    ALL_FOLDERS_EVERY-th poll (job-key matches only there). Returns the task
    (or None) and what was seen, for the failure message."""
    seen_data: dict[str, Any] = {}
    notes: list[str] = []
    polls = 0
    while True:
        polls += 1
        ids = run.refresh_ids() if run is not None else ids
        folder = ids.folder_id
        rows = lister(folder) if folder else []
        if not rows and polls % 3 == 0:
            rows = lister(folder, as_admin=True) if folder else lister(None)
        for path in folder_paths:
            rows = [*rows, *lister(None, folder_path=path)]
        job = (ids.job_key or "").lower()
        if job and polls % ALL_FOLDERS_EVERY == 0:
            known = {str(_get_ci(r, "Id")) for r in rows}
            rows = [*rows] + [
                r for r in lister(None)
                if job in row_job_keys(r) and str(_get_ci(r, "Id")) not in known
            ]
        open_rows = sorted(
            (r for r in rows if is_open(r)),
            key=lambda r: int(_get_ci(r, "Id") or 0),
            reverse=True,
        )
        by_job = [r for r in open_rows if job and job in row_job_keys(r)]
        for row in by_job + [r for r in open_rows[:MAX_CANDIDATES] if r not in by_job]:
            if time.monotonic() >= deadline:
                break
            task_id = str(_get_ci(row, "Id"))
            row_folder = str(_get_ci(row, "FolderId", "OrganizationUnitId") or folder or "")
            if task_id not in seen_data:
                read = data_reader(task_id, row_folder)
                if read is not None:
                    seen_data[task_id] = read
            data = seen_data.get(task_id)
            bundle = {"title": _get_ci(row, "Title"), "data": data}
            if row in by_job or matches(row, bundle):
                return FoundTask(row, data, row_folder), notes
        notes = [
            f"poll {polls}: folder {folder} + {list(folder_paths)}, {len(rows)} task(s), "
            f"{len(open_rows)} open, {len(by_job)} on job {ids.job_key}"
        ]
        if time.monotonic() + TASK_POLL_SECONDS >= deadline:
            return None, notes
        sleep(TASK_POLL_SECONDS)


def take_task(task: FoundTask) -> None:
    """Assign the task to the grader's own identity when it is not already, so
    it can be completed. Best-effort: a failure is reported by `complete`."""
    status = uip_json(["login", "status"]) or {}
    me = _get_ci(status, "Data") or {}
    my_key = str(_get_ci(me, "UserId") or "").lower()
    email = _get_ci(me, "UserEmail", "UserName")
    assigned = str(_get_ci(task.row, "AssignedToUserKey") or "").lower()
    if not email or (assigned and assigned == my_key):
        return
    verb = "reassign" if assigned else "assign"
    uip_json(["tasks", verb, task.task_id, "--user", str(email)])


def complete_task(task: FoundTask, actions: list[str], data: dict) -> str:
    """Complete with the first action name the API accepts; returns it."""
    take_task(task)
    tried = []
    for action in dict.fromkeys(a for a in actions if a):
        tried.append(action)
        result = uip_json(
            [
                "tasks", "complete", task.task_id,
                "--type", task.task_type or "FormTask",
                "--folder-id", task.folder_id,
                "--action", action,
                "--data", json.dumps(data),
            ]
        )
        if result is not None and _get_ci(result, "Result") == "Success":
            print(f"OK: completed task {task.task_id} ({task.task_type}) with action {action!r}")
            return action
    fail(f"could not complete task {task.task_id} ({task.task_type}) with any of {tried}")
    return ""


def cancel(run: DebugRun) -> None:
    ids = run.refresh_ids()
    run.stop()
    if ids.instance_id:
        uip_json(["maestro", "flow", "debug-instance", "cancel", ids.instance_id], timeout=60, bounded=False)


def wait_for_result(run: DebugRun, deadline: float) -> dict:
    """The finished run as a `run_debug`-shaped payload."""
    remaining = max(1, int(deadline - time.monotonic()))
    if run.proc.poll() is None:
        try:
            run.proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            pass
    raw = run.stdout()
    flow_check._LAST_DEBUG_RAW = raw
    flow_check._LAST_DEBUG_STDERR = run.stderr()
    envelope = _parse_json(raw) if run.proc.poll() is not None else None
    data = _get_ci(envelope or {}, "Data") or {}
    if isinstance(data, dict) and str(_get_ci(data, "finalStatus", "FinalStatus")) == "Completed":
        print("note: the CLI's own debug poll saw the run complete")
        return data
    run.stop()
    ids = run.refresh_ids()
    if not ids.instance_id:
        fail(f"the debug run named no instance id to follow; stdout: {raw[-1500:]}")
    status: dict = {}
    while True:
        result = uip_json(["maestro", "flow", "debug-instance", "status", ids.instance_id])
        status = _get_ci(result or {}, "Data") or {}
        state = str(_get_ci(status, "status", "Status") or "")
        if state.lower() in PIMS_TERMINAL or time.monotonic() + STATUS_POLL_SECONDS >= deadline:
            break
        time.sleep(STATUS_POLL_SECONDS)
    variables = _get_ci(
        uip_json(["maestro", "flow", "debug-instance", "variables", ids.instance_id]) or {},
        "Data",
    )
    payload = {
        "instanceId": ids.instance_id,
        "finalStatus": _get_ci(status, "status", "Status"),
        "elementExecutions": _get_ci(status, "elementExecutions", "ElementExecutions") or [],
        "variables": variables or {},
    }
    flow_check._LAST_DEBUG_RAW = json.dumps({"Data": payload})
    state = _get_ci(payload, "finalStatus")
    print(f"note: followed instance {ids.instance_id} after the CLI returned; status {state}")
    return payload


def _record_instance(token: str, instance_id: str | None) -> bool:
    if not instance_id:
        return False
    with open(TOKENS_FILE, "a") as f:
        f.write(f"{token} {instance_id}\n")
    return True


def run_with_task(
    project_dir: str,
    inputs: dict,
    token: str,
    hitl: dict,
    actions: list[str],
    check_task: Callable[[FoundTask], None],
    answer: Callable[[FoundTask], dict],
    label: str,
) -> dict:
    """Debug the flow, find the run's task by `token` in its data, run
    `check_task`, complete it with `answer(task)` under `actions`, and return
    the completed run's payload. Cancels the instance unless it completed."""
    deadline = time.monotonic() + DEADLINE_SECONDS
    bound_calls_by(deadline)
    with open(TOKENS_FILE, "a") as f:
        f.write(f"{token}\n")
    run = start_debug(project_dir, inputs, CLI_TIMEOUT)
    payload = None
    try:
        ids = wait_for_ids(run, deadline)
        print(f"run: folder {ids.folder_id}, job {ids.job_key}, instance {ids.instance_id}")
        recorded = _record_instance(token, ids.instance_id)
        task, notes = find_run_task(
            ids,
            lambda _row, bundle: has_text(bundle, token),
            deadline,
            run,
            folder_paths=node_folder_paths(hitl),
        )
        if not recorded:
            _record_instance(token, run.refresh_ids().instance_id)
        if task is None:
            out = run.stdout()[-1500:] if run.proc.poll() is not None else "(still running)"
            fail(
                f"the run created no open Action Center task for {label} {token}; "
                f"{'; '.join(notes)}; debug stdout: {out}; stderr tail: {run.stderr()[-1500:]}"
            )
        check_task(task)
        complete_task(task, actions, answer(task))
        payload = wait_for_result(run, deadline)
        require_completed(payload)
    finally:
        if not is_completed(payload):
            cancel(run)
        run.finish()
    return payload


def is_completed(payload: dict | None) -> bool:
    return _get_ci(payload or {}, "finalStatus", "FinalStatus") == "Completed"


def require_completed(payload: dict) -> None:
    status = _get_ci(payload, "finalStatus", "FinalStatus")
    if status != "Completed":
        incidents = None
        instance = _get_ci(payload, "instanceId", "InstanceId")
        if instance:
            incidents = _get_ci(
                uip_json(["maestro", "flow", "debug-instance", "incidents", instance]) or {},
                "Data",
            )
        flow_check._fail_with_capture(
            f"the run did not complete after the task was answered (finalStatus={status}); "
            f"incidents: {json.dumps(incidents)[:1500]}"
        )


def completed_ids(payload: dict) -> set[str]:
    return {
        str(_get_ci(e, "elementId", "ElementId", "nodeId", "NodeId"))
        for e in _get_ci(payload, "elementExecutions", "ElementExecutions", "Elements", "elements") or []
        if str(_get_ci(e, "status", "Status")).lower() == "completed"
    }


def load_flow(project_dir: str) -> dict:
    flows = sorted(
        os.path.join(project_dir, n) for n in os.listdir(project_dir) if n.endswith(".flow")
    )
    if not flows:
        fail(f"no .flow file in {project_dir}")
    with open(flows[0], encoding="utf-8") as f:
        return json.load(f)


def reachable(edges: list[dict], starts: set[str]) -> set[str]:
    out: dict[str, set[str]] = {}
    for e in edges:
        out.setdefault(str(e.get("sourceNodeId")), set()).add(str(e.get("targetNodeId")))
    seen, todo = set(), list(starts)
    while todo:
        node = todo.pop()
        if node in seen:
            continue
        seen.add(node)
        todo.extend(out.get(node, ()))
    return seen


def bypassing(flow: dict, node_id: str) -> set[str]:
    """Steps the trigger reaches without passing through `node_id`."""
    edges = [e for e in flow.get("edges") or [] if str(e.get("sourceNodeId")) != node_id]
    nodes = flow.get("nodes") or []
    starts = {str(n.get("id")) for n in nodes if str(n.get("type", "")).startswith("core.trigger")}
    if not starts:
        targets = {str(e.get("targetNodeId")) for e in flow.get("edges") or []}
        starts = {str(n.get("id")) for n in nodes if str(n.get("id")) not in targets}
    return reachable(edges, starts - {node_id}) - {node_id}


def port_targets(edges: list[dict], source: str, port: str) -> set[str]:
    return {
        str(e.get("targetNodeId"))
        for e in edges
        if str(e.get("sourceNodeId")) == source and e.get("sourcePort") == port
    }


def posting_steps(flow: dict, marker: str) -> set[str]:
    """Steps that build `marker`, the stand-in for posting."""
    updates = (flow.get("variables") or {}).get("variableUpdates") or {}
    skipped = (END_TYPE, "core.trigger", "uipath.human-in-the-loop")
    return {
        str(n.get("id"))
        for n in flow.get("nodes") or []
        if not str(n.get("type", "")).startswith(skipped)
        and marker in json.dumps([n.get("inputs"), n.get("outputs"), updates.get(str(n.get("id")))])
    }


def hitl_nodes(flow: dict) -> list[dict]:
    return [
        n for n in flow.get("nodes") or []
        if str(n.get("type", "")).startswith("uipath.human-in-the-loop")
    ]
