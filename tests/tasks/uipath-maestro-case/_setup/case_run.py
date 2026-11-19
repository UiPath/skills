#!/usr/bin/env python3
"""Run a case under ``uip maestro case debug`` and report what executed.

For a case whose first human step parks it: the CLI returns a non-zero exit
with ``Data.finalStatus`` ``Suspended`` and the element executions so far, or,
when the instance stays Running past its poll budget, a ``timeout`` envelope
that carries only ``Data.instanceId``. Either way this module reads the run's
element executions (from the instance when the CLI has none) and lets the
caller judge the path. The graders import it from the reference tree; the
task's post_run runs it from the sandbox's ``_setup`` to cancel this task's
debug instances so none is left waiting on a human step or an SLA clock.

    python3 _setup/case_run.py --mark-task-start         # pre_run
    python3 _setup/case_run.py --cancel-debug-instances  # post_run

A task that already runs ``localize_tenant_ids.py`` as pre_run needs no mark:
the map it writes marks the start.
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
for candidate in (os.path.dirname(HERE), os.getcwd()):
    if os.path.isdir(os.path.join(candidate, "_shared")):
        sys.path.insert(0, candidate)
        break

TERMINAL = {"completed", "successful", "faulted", "failed", "cancelled", "canceled", "stopped"}
DONE = {"completed", "successful"}
FAILED = {"faulted", "failed", "cancelled", "canceled", "stopped"}
# Written by the task's pre_run; the first that exists marks the start of this task.
TASK_START_MARKERS = (
    os.path.join("_setup", ".task-start"),
    os.path.join("_setup", ".tenant-ids.map.json"),
)


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


def instance_folder_key(instance_id: str) -> str | None:
    for item in _rows(_uip(["maestro", "case", "instance", "list"]), "Items"):
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


def cancel_instance(instance_id: str) -> None:
    """Best-effort: stop a parked debug instance so its human tasks and SLA timers go away."""
    args = ["maestro", "case", "instance", "cancel", instance_id, "--comment", "eval cleanup"]
    result = _uip(args)
    if _ci(result, "Result") != "Success":
        folder_key = instance_folder_key(instance_id)
        if folder_key:
            result = _uip([*args, "--folder-key", str(folder_key)])
    print(f"  cancel {instance_id}: {_ci(result, 'Result')} {_ci(result, 'Message') or ''}".rstrip())


def debug_case(timeout: int = 1500) -> dict:
    """Run the case once. Returns ``{status, instance_id, executions, envelope, stderr}``.

    Fails (exit) only when the run never started: no project, refresh failure,
    or output that names no instance.
    """
    from _shared.case_check import (  # noqa: PLC0415
        _parse_json,
        _run,
        debug_fault_is_transient,
        find_project_dir,
        find_solution_dir,
    )

    in_studio_web = os.path.isdir("/solution")
    if in_studio_web:
        project_dir = find_project_dir("/solution/**/project.uiproj")
    else:
        project_dir = find_project_dir()
        solution_dir = find_solution_dir()
        r = _run(["uip", "solution", "resources", "refresh", "--solution-folder",
                  solution_dir, "--output", "json"], timeout=180,
                 what="uip solution resources refresh")
        # Refresh is not idempotent; re-running it over the agent's own refresh
        # fails with this message while the resources are already on disk.
        if r.returncode != 0 and not (
            os.path.isdir(os.path.join(solution_dir, "resources"))
            and "Node already added to the graph" in r.stdout + r.stderr
        ):
            sys.exit(f"FAIL: solution resources refresh exit {r.returncode}\n{r.stdout}\n{r.stderr}")

    cmd = ["uip", "maestro", "case", "debug", project_dir, "--log-level", "debug", "--output", "json"]
    for attempt in (1, 2):
        r = _run(cmd, timeout=timeout, what="uip maestro case debug")
        envelope = _parse_json(r.stdout) or {}
        data = _ci(envelope, "Data") if isinstance(_ci(envelope, "Data"), dict) else {}
        if _ci(data, "instanceId", "InstanceId"):
            break
        fault = debug_fault_is_transient(f"{r.stdout}\n{r.stderr}")
        if fault is None or attempt == 2:
            sys.exit(
                f"FAIL: case debug did not start an instance (exit {r.returncode})\n"
                f"stdout: {r.stdout[-3000:]}\nstderr: {r.stderr[-3000:]}"
            )
        print(f"NOTE: retrying `uip maestro case debug` once — {fault}.", flush=True)
        time.sleep(15)

    instance_id = str(_ci(data, "instanceId", "InstanceId"))
    executions = [row for row in _ci(data, "elementExecutions", "ElementExecutions", default=[]) or []
                  if isinstance(row, dict)]
    status = str(_ci(data, "finalStatus", "FinalStatus", "lastStatus", "LastStatus") or "")
    return {
        "status": status,
        "instance_id": instance_id,
        "executions": executions,
        "envelope": {k: v for k, v in envelope.items() if k != "Data"},
        "stderr": (r.stderr or "")[-3000:],
    }


def wait_for(run: dict, done, *, budget: int = 480, every: int = 20) -> dict:
    """Re-read the instance until ``done(executions)`` or the run is terminal.

    The CLI stops polling at a parked or still-running instance; the instance
    keeps going, so its own element executions are the source of truth.
    """
    waited = 0
    while not done(run["executions"]) and run["status"].lower() not in TERMINAL and waited < budget:
        time.sleep(every)
        waited += every
        rows = instance_executions(run["instance_id"])
        if rows:
            run["executions"] = rows
    return run


# ── what the run must show ───────────────────────────────────────────────────

AUTOMATED_TYPES = {
    "agent", "process", "rpa", "api-workflow", "case-management",
    "execute-connector-activity", "function", "business-rule",
}
HUMAN_TYPES = {"action", "wait-for-user"}
STARTS_ON_ENTRY = {"current-stage-entered", "runs-sequentially"}
MOVES_ON = {"selected-stage-completed", "selected-stage-exited"}


def _first_rules(conditions) -> list[dict]:
    rules = []
    for condition in conditions or []:
        for group in (condition or {}).get("rules") or []:
            if isinstance(group, list) and group and isinstance(group[0], dict):
                rules.append(group[0])
    return rules


def _selected(rule: dict) -> set[str]:
    ids = rule.get("selectedStageIds")
    if isinstance(ids, list):
        return {str(i) for i in ids}
    return {str(rule["selectedStageId"])} if rule.get("selectedStageId") else set()


def _tasks(stage: dict) -> list[dict]:
    out = []
    for lane in (stage.get("data") or {}).get("tasks") or []:
        out.extend(t for t in (lane if isinstance(lane, list) else [lane]) if isinstance(t, dict))
    return out


def _label(node: dict) -> str:
    return (node.get("data") or {}).get("label") or node.get("id") or "?"


def opening_path(plan: dict) -> dict:
    """What a run must reach, read from the built plan rather than from names.

    ``opening``: stages entered when the case starts (a case-entered rule).
    ``automated``: their required automated tasks that start on stage entry or
    in sequence. ``human``: their required human tasks that start the same way;
    the run must open them and then waits there. ``next``: stages entered once
    an opening stage completes or exits, required only when no human task
    holds the opening stage open.
    """
    stages = [n for n in plan.get("nodes") or [] if "Stage" in str(n.get("type"))]
    opening = [s for s in stages
               if any(r.get("rule") == "case-entered"
                      for r in _first_rules((s.get("data") or {}).get("entryConditions")))]
    opening_ids = {s.get("id") for s in opening}
    starting = [
        (s, t) for s in opening for t in _tasks(s)
        if t.get("isRequired") is not False
        and (not t.get("entryConditions")
             or any(r.get("rule") in STARTS_ON_ENTRY for r in _first_rules(t.get("entryConditions"))))
    ]
    automated = [(s, t) for s, t in starting if t.get("type") in AUTOMATED_TYPES]
    human = [(s, t) for s, t in starting if t.get("type") in HUMAN_TYPES]
    following = [
        s for s in stages if s.get("id") not in opening_ids
        and any(r.get("rule") in MOVES_ON and _selected(r) & opening_ids
                for r in _first_rules((s.get("data") or {}).get("entryConditions")))
    ]
    required = {t.get("id") for s in stages for t in _tasks(s) if t.get("isRequired") is not False}
    return {"opening": opening, "automated": automated, "human": human,
            "next": [] if human else following,
            "required_ids": required | {s.get("id") for s in stages}}


def _statuses(executions: list[dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in executions:
        out.setdefault(element_of(row), []).append(status_of(row))
    return out


def path_reached(path: dict, executions: list[dict]) -> bool:
    seen = _statuses(executions)
    automated_done = all(
        any(s.lower() in DONE for s in seen.get(t.get("id"), [])) for _, t in path["automated"]
    )
    human_open = all(t.get("id") in seen for _, t in path["human"])
    moved_on = not path["next"] or any(s.get("id") in seen for s in path["next"])
    return automated_done and human_open and moved_on


def path_failures(path: dict, run: dict) -> list[str]:
    """Why the run did not take the opening path; empty when it did."""
    seen = _statuses(run["executions"])
    problems = []
    if not path["opening"]:
        return ["the plan has no stage the case enters when it starts (case-entered)"]
    if not path["automated"]:
        problems.append("the opening stage(s) have no required automated task to run: "
                        + ", ".join(_label(s) for s in path["opening"]))
    for stage in path["opening"]:
        if stage.get("id") not in seen:
            problems.append(f"opening stage {_label(stage)!r} was never entered")
    for stage, task in path["automated"]:
        got = seen.get(task.get("id"), [])
        if not any(s.lower() in DONE for s in got):
            problems.append(
                f"{task.get('type')} task {task.get('displayName')!r} in {_label(stage)!r} "
                f"did not complete (statuses {got or 'none: never started'})"
            )
    for stage, task in path["human"]:
        if task.get("id") not in seen:
            problems.append(
                f"human task {task.get('displayName')!r} in {_label(stage)!r} was never opened"
            )
    if path["next"] and not any(s.get("id") in seen for s in path["next"]):
        problems.append("the case never moved on to "
                        + " / ".join(repr(_label(s)) for s in path["next"]))
    failed = [f"{element} {sorted(set(states))}" for element, states in seen.items()
              if element in path["required_ids"] and any(s.lower() in FAILED for s in states)]
    if failed:
        problems.append(f"required elements failed: {failed}")
    return problems


def run_opening_path(plan: dict, *, timeout: int = 1500, budget: int = 480) -> tuple[dict, dict]:
    """Debug the case, follow the instance until the opening path is decided, cancel it."""
    path = opening_path(plan)
    run = debug_case(timeout=timeout)
    try:
        run = wait_for(run, lambda rows: path_reached(path, rows), budget=budget)
    finally:
        if run["status"].lower() not in TERMINAL:
            cancel_instance(run["instance_id"])
    return path, run


# ── post_run: cancel this task's debug instances ─────────────────────────────


def _our_stage_ids() -> set[str]:
    """Stage ids of every case plan in the sandbox (post_run has no ``_shared``)."""
    stage_ids: set[str] = set()
    for name in ("caseplan.case", "caseplan.json"):
        for path in glob.glob(f"**/{name}", recursive=True):
            try:
                with open(path, encoding="utf-8") as fh:
                    plan = json.load(fh)
            except (OSError, ValueError):
                continue
            stage_ids.update(
                str(node.get("id")) for node in plan.get("nodes") or []
                if "Stage" in str(node.get("type")) and node.get("id")
            )
    return stage_ids


def cancel_debug_instances() -> int:
    """Cancel every open Studio Web Debug instance this task started.

    The tenant is shared, so an instance counts as ours only when it started
    after this task did and its element executions carry one of our stage ids.
    """
    marker = next((m for m in TASK_START_MARKERS if os.path.exists(m)), None)
    if marker is None:
        print("case_run: no task-start marker; nothing to cancel")
        return 0
    since = datetime.fromtimestamp(os.path.getmtime(marker), timezone.utc)
    since_iso = since.strftime("%Y-%m-%dT%H:%M:%S")
    stage_ids = _our_stage_ids()
    if not stage_ids:
        print("case_run: no caseplan stage ids; cannot tell our instances apart")
        return 0
    for item in _rows(_uip(["maestro", "case", "instance", "list"]), "Items"):
        if str(_ci(item, "Source") or "") != "Studio Web Debug":
            continue
        if str(_ci(item, "CreatedTimeUtc") or "") < since_iso:
            continue
        if str(_ci(item, "LatestRunStatus") or "").lower() in TERMINAL:
            continue
        instance_id = str(_ci(item, "InstanceId") or "")
        rows = instance_executions(instance_id)
        if any(element_of(row) in stage_ids for row in rows):
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
