#!/usr/bin/env python3
"""Cancel case instances this task started that its own solution cleanup cannot reach.

`_shared/cleanup_solutions.py` deletes the Studio Web solution the run uploaded, and the
instances of that solution go with it. It cannot touch `SupplierContractNegotiation`: the
happy path starts that as a child case, it belongs to a different solution, and it is
started fire-and-forget, so nothing ever closes it. Left alone, every run that reaches
'Setting up the supplier' leaves one more live instance on the tenant.

Only instances created during this task are eligible. The floor is the oldest `.uipx`
file's modification time, which is when the run built its solution -- an instance older
than the build cannot belong to this run.

Best-effort by design: post_run results are informational, so this always exits 0.
"""

from __future__ import annotations

import datetime
import glob
import json
import os
import subprocess
import sys
from pathlib import Path

LIVE = {"Running", "Paused", "Suspended"}
RUN_STATE = "supplier-onboarding-run.json"


def uip(args: list[str], timeout: int = 120) -> dict:
    try:
        proc = subprocess.run(["uip", *args, "--output", "json"],
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {}
    start = proc.stdout.find("{")
    if start < 0:
        return {}
    try:
        return json.loads(proc.stdout[start:])
    except json.JSONDecodeError:
        return {}


def our_package_id() -> str | None:
    """The package every instance of THIS run belongs to.

    An instance record names no solution: `ReleaseName` is absent and `PackageId` is a bare
    GUID, so nothing here can be matched by name. What separates our own case from a child case
    it started is that they are different packages. The driver records the instance it drove, so
    that instance's package is the one to spare. Without it, nothing is eligible: cancelling on a
    guess would take out the run's own case.
    """
    state = Path(f".{RUN_STATE}")
    if not state.exists():
        return None
    try:
        instance_id = json.loads(state.read_text(encoding="utf-8")).get("instance_id")
    except (json.JSONDecodeError, OSError):
        return None
    if not instance_id:
        return None
    for row in (uip(["maestro", "case", "instance", "list"]).get("Data") or []):
        if row.get("InstanceId") == instance_id:
            return row.get("PackageId")
    return None


def run_floor_iso() -> str | None:
    """When this run built its solution. Nothing older than that is ours."""
    stamps = [os.path.getmtime(p) for p in glob.glob("**/*.uipx", recursive=True)]
    if not stamps:
        return None
    oldest = datetime.datetime.fromtimestamp(min(stamps), datetime.timezone.utc)
    return oldest.strftime("%Y-%m-%dT%H:%M:%S")


def main() -> int:
    if os.environ.get("CASE_E2E_CLEANUP", "always") == "never":
        print("cleanup_child_cases: CASE_E2E_CLEANUP=never, leaving instances in place")
        return 0

    floor = run_floor_iso()
    if floor is None:
        print("cleanup_child_cases: no .uipx under the sandbox, nothing to attribute to this run")
        return 0

    ours = our_package_id()
    if ours is None:
        print("cleanup_child_cases: this run's own package is unknown, so nothing is eligible")
        return 0

    rows = (uip(["maestro", "case", "instance", "list"]).get("Data")) or []
    if not isinstance(rows, list):
        print("cleanup_child_cases: could not list instances")
        return 0

    for row in rows:
        created = row.get("CreatedTimeUtc") or ""
        instance_id = row.get("InstanceId")
        if not instance_id or created < floor:
            continue
        if row.get("PackageId") == ours:
            continue
        if row.get("LatestRunStatus") not in LIVE:
            continue
        name = row.get("PackageId") or "?"
        folder = row.get("FolderKey") or ""
        args = ["maestro", "case", "instance", "cancel", instance_id]
        if folder:
            args += ["-f", folder]
        reply = uip(args)
        ok = reply.get("Result") == "Success"
        print(f"cleanup_child_cases: {'cancelled' if ok else 'could not cancel'} {instance_id} ({name})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
