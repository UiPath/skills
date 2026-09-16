#!/usr/bin/env python3
"""pre_run: name the Orchestrator folder and solution this run may deploy into.

Deliberately does NOT seed the runtime input value. The grader mints that
token when it runs the process (check_behavior.py), so the agent never sees
it and cannot hard-code the answer into the API workflow.

Everything here is a coordination fact the agent could not guess and that
teardown needs to find this run's objects again. Every tenant object this run
creates must carry `folderName` / `solutionName` (or embed `runId`), so
teardown can delete by prefix and a same-named leftover from an earlier run
can never satisfy this run's checks (see composition.py's folder-pinning
check).
"""
import json
import subprocess
import sys
import uuid

# Parent for every folder this suite creates. Hardcoded so the same path lands
# locally, in CI, and on the nightly VM without env coordination; created on
# first run so a fresh tenant works.
PARENT_FOLDER_PATH = "Shared/uipath-maestro-bpmn-e2e"

PREFIX = "api-workflow-composition"


def uip_json(*args):
    r = subprocess.run(
        ["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=120
    )
    try:
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        return {}


def ensure_parent_folder(path):
    """Idempotent, and race-safe against a parallel seed: if our create loses,
    re-GET and accept the peer's folder."""
    if uip_json("or", "folders", "get", path).get("Result") == "Success":
        return
    parent, _, name = path.rpartition("/")
    if not parent or not name:
        sys.exit(f"seed.py: {path!r} must nest under an existing folder (e.g. 'Shared/x').")
    created = uip_json("or", "folders", "create", name, "--parent", parent)
    if created.get("Result") == "Success":
        return
    if uip_json("or", "folders", "get", path).get("Result") == "Success":
        return
    msg = created.get("Message") or created.get("Instructions") or "unknown error"
    sys.exit(f"seed.py: failed to ensure parent folder {path}: {msg}")


ensure_parent_folder(PARENT_FOLDER_PATH)

# One id per run, shared by the folder and the solution/package name. The
# solution name must be unique because it becomes the published PACKAGE name:
# two concurrent runs sharing it would fight over versions in the tenant feed,
# and teardown could not tell whose versions to delete.
run_id = uuid.uuid4().hex[:8]

seed = {
    "runId": run_id,
    "parentFolderPath": PARENT_FOLDER_PATH,
    "folderName": f"{PREFIX}-{run_id}",
    "solutionName": f"GreetingPipeline{run_id}",
}

with open("seed.json", "w") as fh:
    json.dump(seed, fh, indent=2)
print(json.dumps(seed))
