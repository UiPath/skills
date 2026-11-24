#!/usr/bin/env python3
"""pre_run: name the solution and the Orchestrator folder this run deploys into.

Writes `seed.json` with the same keys as api_workflow_composition's seed, so
that task's `_setup/teardown.py` (mounted beside this file) reclaims this run's
deployment, folders, package versions and Studio Web solutions by `runId` and
`solutionName`. The runtime inputs are picked by check_agent_deploy_behavior.py
after the agent stops, so the agent never sees them.
"""
import json
import subprocess
import sys
import uuid

PARENT_FOLDER_PATH = "Shared/uipath-maestro-bpmn-e2e"
PREFIX = "agent-deploy-run"


def uip_json(*args):
    r = subprocess.run(
        ["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=120
    )
    try:
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        return {}


def ensure_parent_folder(path):
    if uip_json("or", "folders", "get", path).get("Result") == "Success":
        return
    parent, _, name = path.rpartition("/")
    created = uip_json("or", "folders", "create", name, "--parent", parent)
    if created.get("Result") == "Success":
        return
    if uip_json("or", "folders", "get", path).get("Result") == "Success":
        return
    msg = created.get("Message") or created.get("Instructions") or "unknown error"
    sys.exit(f"seed_agent_deploy.py: failed to ensure parent folder {path}: {msg}")


ensure_parent_folder(PARENT_FOLDER_PATH)

run_id = uuid.uuid4().hex[:8]
seed = {
    "runId": run_id,
    "parentFolderPath": PARENT_FOLDER_PATH,
    "folderName": f"{PREFIX}-{run_id}",
    "solutionName": f"NameClassifier{run_id}",
}

with open("seed.json", "w") as fh:
    json.dump(seed, fh, indent=2)
print(json.dumps(seed))
