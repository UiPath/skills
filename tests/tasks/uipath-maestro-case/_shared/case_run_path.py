"""Run a case under ``uip maestro case debug`` and judge the opening path.

For a case whose first human step parks it: the CLI returns a non-zero exit
with ``Data.finalStatus`` ``Suspended`` and the element executions so far, or,
when the instance stays Running past its poll budget, a ``timeout`` envelope
that carries only ``Data.instanceId``. Either way this module reads the run's
element executions (from the instance when the CLI has none) and lets the
caller judge the path. Graders import it from the reference tree; the
instance helpers come from ``_setup/case_run.py``, which post_run runs.
"""

from __future__ import annotations

import json
import os
import sys
import time

CASE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CASE_ROOT, "_setup"))
sys.path.insert(0, CASE_ROOT)
from case_run import (  # noqa: E402
    DONE,
    FAILED,
    TERMINAL,
    cancel_instance,
    element_of,
    instance_executions,
    instance_incidents,
    record_debug_instance,
    status_of,
)
from _shared.case_check import _get_ci as _ci  # noqa: E402

CANCELLED = "Cancelled"
RETRY_SLEEP_S = 15
MAX_DEBUG_CALLS = 2


def _debug_attempt(cmd: list[str], timeout: int) -> tuple:
    """Run ``cmd`` once. Returns ``(proc, envelope, data)``."""
    from _shared.case_check import _parse_json, _run  # noqa: PLC0415

    r = _run(cmd, timeout=timeout, what="uip maestro case debug")
    envelope = _parse_json(r.stdout) or {}
    data = _ci(envelope, "Data") if isinstance(_ci(envelope, "Data"), dict) else {}
    return r, envelope, data


def _debug_with_retry(cmd: list[str], timeout: int) -> tuple:
    """Run ``cmd``, retrying a transient start fault or a Cancelled run within one shared budget of ``MAX_DEBUG_CALLS``."""
    from _shared.case_check import (  # noqa: PLC0415
        debug_fault_is_transient,
        retry_after_cancelled,
    )

    for call in range(1, MAX_DEBUG_CALLS + 1):
        last = call == MAX_DEBUG_CALLS
        r, envelope, data = _debug_attempt(cmd, timeout)
        if _ci(data, "instanceId", "InstanceId"):
            status = str(_ci(data, "finalStatus", "FinalStatus", "lastStatus", "LastStatus") or "")
            if status != CANCELLED or last:
                return r, envelope, data
            retry_after_cancelled()
            continue
        fault = debug_fault_is_transient(f"{r.stdout}\n{r.stderr}")
        if fault is None or last:
            sys.exit(
                f"FAIL: case debug did not start an instance (exit {r.returncode})\n"
                f"stdout: {r.stdout[-3000:]}\nstderr: {r.stderr[-3000:]}"
            )
        print(f"NOTE: retrying `uip maestro case debug` once — {fault}.", flush=True)
        time.sleep(RETRY_SLEEP_S)


def debug_case(timeout: int = 1500) -> dict:
    """Run the case. Returns ``{status, instance_id, executions, envelope, stderr}``.

    Fails (exit) only when the run never started: no project, refresh failure,
    or output that names no instance. At most ``MAX_DEBUG_CALLS`` debug calls.
    """
    from _shared.case_check import (  # noqa: PLC0415
        _run,
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
    r, envelope, data = _debug_with_retry(cmd, timeout)

    instance_id = str(_ci(data, "instanceId", "InstanceId"))
    record_debug_instance(instance_id)
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
    deadline = time.monotonic() + budget
    while (not done(run["executions"]) and run["status"].lower() not in TERMINAL
           and time.monotonic() < deadline):
        time.sleep(every)
        rows = instance_executions(run["instance_id"])
        if rows:
            run["executions"] = rows
    return run


# ── what the run must show ───────────────────────────────────────────────────

HUMAN_TYPES = {"action", "wait-for-user"}
WAITING_TYPES = {"wait-for-timer", "wait-for-connector"}
TASK_TYPES_SNAPSHOT = os.path.join(CASE_ROOT, "_shared", "task_types.json")


def _snapshot_authorable() -> list[dict]:
    with open(TASK_TYPES_SNAPSHOT, encoding="utf-8") as snapshot:
        return json.load(snapshot)["Data"]["Authorable"]


AUTOMATED_TYPES = (
    {entry["Type"] for entry in _snapshot_authorable()} - HUMAN_TYPES - WAITING_TYPES
)
STARTS_ON_ENTRY = {"current-stage-entered", "runs-sequentially"}
CHAINED = "selected-tasks-completed"
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


def _starting(stage: dict) -> list[dict]:
    """The stage's required tasks that start on entry or in sequence, then
    those chained by selected-tasks-completed behind an automated one."""
    required = [t for t in _tasks(stage) if t.get("isRequired") is not False]
    starting = [
        t for t in required
        if not t.get("entryConditions")
        or any(r.get("rule") in STARTS_ON_ENTRY for r in _first_rules(t.get("entryConditions")))
    ]
    completing = {t.get("id") for t in starting if t.get("type") in AUTOMATED_TYPES}
    grew = True
    while grew:
        grew = False
        for task in required:
            if task in starting:
                continue
            for rule in _first_rules(task.get("entryConditions")):
                after = {str(i) for i in rule.get("selectedTasksIds") or []}
                if rule.get("rule") != CHAINED or not after or not after <= completing:
                    continue
                starting.append(task)
                grew = True
                if task.get("type") in AUTOMATED_TYPES:
                    completing.add(task.get("id"))
                break
    return starting


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
    starting = [(s, t) for s in opening for t in _starting(s)]
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
    return problems + _incident_lines(run)


def _incident_lines(run: dict) -> list[str]:
    if str(run.get("status", "")).lower() not in FAILED:
        return []
    from _shared.case_check import debug_failure_lines  # noqa: PLC0415

    incidents = instance_incidents(run["instance_id"])
    lines = debug_failure_lines({"finalStatus": run["status"], "incidents": incidents})
    return [line for line in lines if line.startswith("incident ")]


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
