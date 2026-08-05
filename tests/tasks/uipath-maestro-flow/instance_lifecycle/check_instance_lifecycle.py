#!/usr/bin/env python3
"""Operate lifecycle outcome check: an instance of the seeded Case process
reached the Cancelled terminal state on the tenant.

Verifies tenant state (not the agent's prose): lists instances for the seeded
process key and asserts at least one is Cancelled. Requires cloud auth and the
E2E_CASE_PROCESS_KEY / E2E_CASE_FOLDER_KEY environment variables (the same
process the agent drove).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _parse_json(stdout: str):
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        for i, line in enumerate(stdout.split("\n")):
            if line.strip().startswith(("{", "[")):
                try:
                    return json.loads("\n".join(stdout.split("\n")[i:]))
                except json.JSONDecodeError:
                    continue
    return None


def main():
    process_key = os.environ.get("E2E_CASE_PROCESS_KEY")
    folder_key = os.environ.get("E2E_CASE_FOLDER_KEY")
    if not process_key:
        _fail("E2E_CASE_PROCESS_KEY not set — cannot verify instance state")

    cmd = [
        "uip", "maestro", "case", "instance", "list",
        "--process-key", process_key, "--output", "json",
    ]
    if folder_key:
        cmd += ["--folder-key", folder_key]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        _fail(f"instance list exit {r.returncode}\nstdout: {r.stdout}\nstderr: {r.stderr}")

    data = _parse_json(r.stdout)
    if data is None:
        _fail(f"could not parse instance list JSON\n{r.stdout[:1000]}")
    # Tolerate a bare list or a {Data: [...]} / {instances: [...]} envelope.
    instances = data
    if isinstance(data, dict):
        instances = data.get("Data") or data.get("instances") or data.get("Instances") or []
    if not isinstance(instances, list):
        _fail(f"unexpected instance list shape: {type(instances).__name__}")

    def _state(inst: dict) -> str:
        for k in ("state", "State", "status", "Status", "latestRunStatus"):
            v = inst.get(k)
            if isinstance(v, str):
                return v
        return ""

    cancelled = [i for i in instances if isinstance(i, dict) and "cancel" in _state(i).lower()]
    if not cancelled:
        states = sorted({_state(i) for i in instances if isinstance(i, dict)})
        _fail(
            f"no Cancelled instance found for process {process_key}; "
            f"instance states present: {states}"
        )
    print(f"OK: {len(cancelled)} cancelled instance(s) for process {process_key}")


if __name__ == "__main__":
    main()
