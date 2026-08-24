#!/usr/bin/env python3
"""pre_run: scaffold a VALID, ready-to-ship API workflow solution in the sandbox.

mode:operate / lifecycle:setup — the artifact is already correct. The agent's job
is the post-publish lifecycle: pack -> publish -> deploy -> start a job -> confirm
it ran. Authoring is NOT the graded behavior (the build-mode tasks cover that), so
the project is seeded rather than written by the agent.

Scaffolds with the documented CLI path (`uip solution init` + `uip api-workflow
init`) instead of hand-writing files, so the project carries the real Studio Web
shape (project.uiproj / entry-points.json / bindings_v2.json) and is registered in
the parent .uipx. Both commands are offline — this seed needs no tenant auth.

Then appends a Response activity so the deployed job returns a payload, and
validates. A seed that does not validate exits non-zero, failing pre_run loudly
rather than handing the agent a broken artifact and grading it on the fallout.

Writes ./ApiWfSolution/ (containing OrderStatus/) into the agent's working dir.
"""
import json
import subprocess
import sys
from pathlib import Path

SOLUTION_DIR = "ApiWfSolution"
PROJECT_NAME = "OrderStatus"


def uip(*args, cwd=None):
    """Run a uip command, return parsed JSON (empty dict when not JSON)."""
    r = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=180, cwd=cwd,
    )
    try:
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        return {}


def die(msg):
    sys.exit(f"seed_api_workflow_project.py: {msg}")


# 1) Solution shell
res = uip("solution", "init", SOLUTION_DIR)
if res.get("Result") != "Success" and not Path(SOLUTION_DIR).is_dir():
    die(f"`uip solution init {SOLUTION_DIR}` failed: {res.get('Message')!r}")

# 2) API workflow project, registered in the solution's .uipx.
#    init's <name> takes no slashes, so it must run from inside the solution dir.
res = uip("api-workflow", "init", PROJECT_NAME, cwd=SOLUTION_DIR)
wf_path = Path(SOLUTION_DIR) / PROJECT_NAME / "Workflow.json"
if not wf_path.is_file():
    die(f"`uip api-workflow init {PROJECT_NAME}` produced no Workflow.json: {res.get('Message')!r}")

# 3) Append a Response so the deployed job returns a payload the check can read.
wf = json.loads(wf_path.read_text())
root = wf["do"][0]
seq_key = next(iter(root))
root[seq_key]["do"].append({
    "Response_1": {
        "response": {"status": "${'ok'}"},
        "markJobAsFailed": False,
        "then": "end",
        "metadata": {
            "activityType": "Response",
            "displayName": "Response",
            "fullName": "Response",
        },
    }
})
wf_path.write_text(json.dumps(wf, indent=2))

# 4) The seed must be shippable. A non-Valid seed is a harness bug, not an agent
#    failure — fail pre_run here rather than letting the agent inherit it.
res = uip("api-workflow", "validate", str(wf_path))
status = (res.get("Data") or {}).get("Status")
if status != "Valid":
    die(f"seeded workflow is not Valid (Status={status!r}): {res.get('Instructions')!r}")

print(f"OK: seeded {wf_path} (Status: Valid), registered in {SOLUTION_DIR}")
