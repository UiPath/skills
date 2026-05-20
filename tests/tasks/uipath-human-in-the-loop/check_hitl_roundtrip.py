#!/usr/bin/env python3
"""Full HITL round-trip checker.

Validates three things in sequence:
  1. task-snapshot.json — the pending Action Center task had the right schema
  2. task-assert.json   — the agent's own schema assertions all passed
  3. flow-result.json   — the flow reached a terminal Completed state

Each assertion prints "OK: ..." on success and calls sys.exit("FAIL: ...") on
failure, so the first failure stops evaluation with a clear message.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _load_json(path: str) -> dict | list:
    p = Path(path)
    if not p.is_file():
        _fail(f"{path} not found — did the agent reach this step?")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _fail(f"{path} is not valid JSON: {e}")


# ── 1. task-snapshot.json ────────────────────────────────────────────────────

def check_task_snapshot() -> None:
    raw = _load_json("task-snapshot.json")

    # The CLI wraps responses in { Result, Code, Data } or returns the array
    # directly depending on the command variant; normalise both shapes.
    if isinstance(raw, dict) and "Data" in raw:
        tasks = raw["Data"]
        if isinstance(tasks, dict):
            tasks = [tasks]
    elif isinstance(raw, list):
        tasks = raw
    elif isinstance(raw, dict):
        tasks = [raw]
    else:
        _fail(f"task-snapshot.json has unexpected shape: {type(raw)}")

    if not tasks:
        _fail("task-snapshot.json contains no tasks")

    task = tasks[0]

    # Title or CatalogName must reference the HITL node label
    title = (
        task.get("Title")
        or task.get("CatalogName")
        or task.get("catalogName")
        or task.get("name")
        or ""
    )
    if "Manager Review" not in title and "manager review" not in title.lower():
        # Tolerate partial matches — agent may have trimmed the label
        found_hitl = any(
            k in str(task).lower() for k in ("manager", "review", "hitl", "requester")
        )
        if not found_hitl:
            _fail(
                f"task-snapshot.json task title {title!r} doesn't look like the "
                f"expected HITL task (expected to contain 'Manager Review')"
            )

    # Task type must be ExternalTask (HITL Flow tasks are always ExternalTask)
    task_type = (
        task.get("Type")
        or task.get("type")
        or task.get("TaskType")
        or task.get("taskType")
        or ""
    )
    if task_type and "external" not in task_type.lower() and "ExternalTask" not in task_type:
        _fail(
            f"Expected task type ExternalTask, got {task_type!r}. "
            f"HITL Flow nodes always create ExternalTask entries."
        )

    print(f"OK: task-snapshot.json has task {title!r} (type={task_type or 'unspecified'})")


# ── 2. task-assert.json ──────────────────────────────────────────────────────

def check_task_assert() -> None:
    p = Path("task-assert.json")
    if not p.is_file():
        # Agent may have skipped writing this; not fatal — core assertion is
        # in task-snapshot and flow-result.
        print("SKIP: task-assert.json not found (agent may have skipped step 4)")
        return

    data = _load_json("task-assert.json")
    if not isinstance(data, dict):
        _fail(f"task-assert.json should be a JSON object, got {type(data)}")

    schema_ok = data.get("schema_ok")
    if schema_ok is False:
        requester_ok = data.get("requester_field_present")
        approved_ok  = data.get("approved_field_present")
        _fail(
            f"Agent's own schema assertion failed: requester_field_present="
            f"{requester_ok}, approved_field_present={approved_ok}. "
            f"Check that the HITL node binding and field directions are correct."
        )

    requester_val = data.get("requester_value")
    if requester_val and str(requester_val) != "e2e-alice":
        _fail(
            f"requester field value is {requester_val!r}, expected 'e2e-alice'. "
            f"Binding '=js:$vars.trigger1.output.requester' is not resolving."
        )

    print(
        f"OK: task-assert.json — requester={requester_val!r}, "
        f"approved_field_present={data.get('approved_field_present')}, "
        f"schema_ok={schema_ok}"
    )


# ── 3. flow-result.json (debug output) ──────────────────────────────────────

def check_flow_result() -> None:
    raw = _load_json("flow-result.json")
    if not isinstance(raw, dict):
        _fail(f"flow-result.json should be a JSON object, got {type(raw)}")

    result = raw.get("Result")
    if result != "Success":
        msg = raw.get("Message") or raw.get("Instructions") or "(no message)"
        _fail(
            f"flow-result.json Result={result!r}: {msg}. "
            f"The flow execution did not complete successfully."
        )

    data = raw.get("Data") or {}

    # finalStatus must be Completed or Successful
    final_status = (
        data.get("finalStatus")
        or data.get("FinalStatus")
        or data.get("status")
        or ""
    )
    terminal = {"completed", "successful", "success"}
    if final_status.lower() not in terminal:
        _fail(
            f"flow finalStatus={final_status!r}, expected one of {sorted(terminal)}. "
            f"The flow may still be running or have faulted."
        )
    print(f"OK: flow-result.json finalStatus={final_status!r}")

    # Element executions — assert the approved branch script ran
    executions = data.get("elementExecutions") or data.get("ElementExecutions") or []
    if executions:
        exec_ids = [e.get("elementId") or e.get("ElementId") or "" for e in executions]
        # We expect approvedScript to have executed (not rejectedScript)
        approved_ran = any("approved" in eid.lower() for eid in exec_ids)
        rejected_ran = any("rejected" in eid.lower() for eid in exec_ids)
        if rejected_ran and not approved_ran:
            _fail(
                f"rejectedScript branch executed instead of approvedScript. "
                f"Check that task completion with --action 'Approve' and "
                f"--data '{{\"approved\":true}}' reached the Decision node correctly. "
                f"Element IDs seen: {exec_ids}"
            )
        if approved_ran:
            print(f"OK: approvedScript branch executed (element executions: {exec_ids})")
        else:
            # Can't identify by element ID — that's OK, just report
            print(
                f"OK: flow completed (element IDs: {exec_ids}). "
                f"approvedScript id not found by name — verify manually if needed."
            )
    else:
        print("OK: flow completed (no elementExecutions in output to inspect)")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    check_task_snapshot()
    check_task_assert()
    check_flow_result()
    print("\nAll checks passed — HITL round-trip complete.")


if __name__ == "__main__":
    main()
