#!/usr/bin/env python3
"""Data-grounded execution check: a test execution actually ran to a TERMINAL state.

Proves the connector's Execute activity produced a real execution that reached a
terminal status (not just that Execute was invoked).

Reads result.json (agent) -> {"execution_id": "<id>", "status": "<status>"}.
"""
import json
import sys

TERMINAL = {
    "passed", "failed", "completed", "cancelled", "canceled",
    "error", "done", "stopped", "faulted", "successful", "partiallypassed",
}


def main():
    try:
        res = json.load(open("result.json", encoding="utf-8"))
    except OSError:
        print("FAIL: result.json missing — agent did not record the execution outcome")
        sys.exit(1)
    if not res.get("execution_id"):
        print("FAIL: no execution_id — Execute did not produce a real execution")
        sys.exit(1)
    status = str(res.get("status", "")).strip().lower()
    if not status:
        print("FAIL: no status recorded")
        sys.exit(1)
    if status not in TERMINAL:
        print(f"FAIL: execution status {status!r} is not terminal (still Pending/Running?)")
        sys.exit(1)
    print(f"OK: execution {res['execution_id']} reached terminal status {status!r}")


if __name__ == "__main__":
    main()
