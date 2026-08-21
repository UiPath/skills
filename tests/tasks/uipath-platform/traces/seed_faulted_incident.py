#!/usr/bin/env python3
"""Write incident.json for the standalone-diagnose traces e2e task.

Requires a job that has ALREADY faulted on the tenant — the point of the task is
that the agent inspects a run it did not start. Provide it via
E2E_FAULTED_JOB_KEY (optionally E2E_FAULTED_FOLDER_PATH, defaults to
Shared/uipath-platform).

Exits non-zero with an explicit message when the fixture is absent, so an
unprovisioned tenant reads as a missing fixture rather than a skill regression.
"""
import json
import os
import sys
from pathlib import Path

job_key = os.environ.get("E2E_FAULTED_JOB_KEY", "").strip()
if not job_key:
    sys.exit(
        "FIXTURE NOT PROVISIONED: E2E_FAULTED_JOB_KEY is unset. This task needs a "
        "pre-faulted Agent-type job on the tenant (see the task description); export "
        "its job key to the runner before enabling this task."
    )

incident = {
    "job_key": job_key,
    "folder_path": os.environ.get("E2E_FAULTED_FOLDER_PATH", "Shared/uipath-platform"),
    "reported_by": "overnight schedule handover",
}
Path("incident.json").write_text(json.dumps(incident, indent=2) + "\n")
print(f"OK: incident.json written for job {job_key}")
