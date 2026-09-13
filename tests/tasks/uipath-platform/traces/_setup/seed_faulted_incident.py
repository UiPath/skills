#!/usr/bin/env python3
"""Write incident.json for the standalone-diagnose traces e2e task.

Self-provisioning fixture: starts a fresh job against a dedicated,
deliberately-faulting agent process (traces-diagnose-fault-fixture) and waits
for it to fault, then hands the agent only the resulting job key + folder path
via incident.json -- mirroring a real overnight handover, but generated fresh
each run instead of depending on someone maintaining a live faulted job by hand.

FIXTURE_PROCESS_KEY is a plain resource identifier on the shared codereval/
DefaultTenant (alpha.uipath.com) eval tenant, not a secret -- same reasoning
already used to inline the traces-smoke-v3 process key in traces_e2e.yaml /
traces_feedback_e2e.yaml.
"""
import json
import subprocess
import sys
from pathlib import Path

FIXTURE_PROCESS_KEY = "328e7acc-1ab4-4bad-90a2-a6e74f21f681"  # traces-diagnose-fault-fixture
FIXTURE_FOLDER_PATH = "Shared/uipath-platform"

result = subprocess.run(
    [
        "uip", "or", "jobs", "start", FIXTURE_PROCESS_KEY,
        "--folder-path", FIXTURE_FOLDER_PATH,
        "--wait-for-completion", "--timeout", "90",
        "--output", "json",
    ],
    capture_output=True, text=True, timeout=100,
)

try:
    payload = json.loads(result.stdout)
except json.JSONDecodeError:
    sys.exit(f"FIXTURE START FAILED: could not parse `uip or jobs start` output:\n{result.stdout}\n{result.stderr}")

job = payload.get("Data") or {}
state = job.get("State")
job_key = job.get("Key")

if state != "Faulted" or not job_key:
    sys.exit(
        f"FIXTURE DID NOT FAULT AS EXPECTED: job ended in state {state!r} "
        f"(expected 'Faulted'). traces-diagnose-fault-fixture "
        f"({FIXTURE_PROCESS_KEY}) may no longer be reliably faulting -- check "
        f"the published package on the tenant before re-running this task."
    )

incident = {
    "job_key": job_key,
    "folder_path": FIXTURE_FOLDER_PATH,
    "reported_by": "overnight schedule handover",
}
Path("incident.json").write_text(json.dumps(incident, indent=2) + "\n")
print(f"OK: incident.json written for freshly-faulted job {job_key}")
