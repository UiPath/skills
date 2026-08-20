#!/usr/bin/env python3
"""pre_run: put a genuinely FAULTED API-workflow job on the tenant to diagnose.

Self-seeding by design. The equivalent platform task
(uipath-platform/traces/traces_diagnose_faulted_job_e2e.yaml) waits on an
externally-provisioned E2E_FAULTED_JOB_KEY and has never run because nobody
provisioned it — a fixture that needs a human is a task that stays skipped. This
one manufactures its own fault every run.

Runs in TWO PHASES because coder-eval caps a single pre_run step at 300s and the
deploy alone costs ~120s. Each phase is its own pre_run entry with its own budget:

  `deploy` — scaffold a project, drop in fixtures/faulting-workflow.json (a
             workflow that PASSES `validate` and throws at runtime), pack,
             publish, deploy. Writes .fault_fixture.json.
  `fault`  — start a job on the deployed process, poll until Faulted, write
             incident.json: the job id and folder path, nothing else, which is
             all the agent gets.

The deployment is deliberately LEFT STANDING. Verified on alpha 2026-08-18 (uip
1.200.0): uninstalling a deployment destroys its job records, after which
`uip or jobs get <jobId>` returns Result: Failure with an empty State. The agent
cannot diagnose a job whose deployment is gone, so teardown belongs in post_run.

Exits non-zero on any failure: a broken fixture must fail pre_run loudly rather
than let the agent be graded on it.
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

SOLUTION_DIR = "FaultSolution"
PROJECT_NAME = "OrderStatus"
# The fixture faults on the first poll in practice (the throw is immediate), so a
# short budget is plenty and keeps the phase inside coder-eval's 300s pre_run cap.
POLL_BUDGET_S = 120
POLL_SLEEP_S = 5
TERMINAL = {"faulted", "successful", "stopped"}


def uip(*args, cwd=None, timeout=300):
    r = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=timeout, cwd=cwd,
    )
    raw = r.stdout or ""
    env = {}
    if "{" in raw:
        try:
            env = json.loads(raw[raw.index("{"):])
        except json.JSONDecodeError:
            env = {}
    return env


def die(msg):
    sys.exit(f"seed_faulted_job.py: FIXTURE SETUP FAILED — {msg}")


PHASE = sys.argv[1] if len(sys.argv) > 1 else "deploy"
if PHASE not in ("deploy", "fault"):
    sys.exit(f"seed_faulted_job.py: unknown phase {PHASE!r} (expected 'deploy' or 'fault')")

seed_path = Path("seed.json")
if not seed_path.is_file():
    die("no seed.json; uipath-platform/seed.py must run first (it supplies uuid8 + parent_folder_path)")
seed = json.loads(seed_path.read_text())
uuid8 = seed.get("uuid8")
parent = seed.get("parent_folder_path") or "Shared"
if not uuid8:
    die("seed.json has no uuid8")

package_name = f"apiwffault-pkg-{uuid8}"
deploy_name = f"apiwffault-{uuid8}"
folder_name = f"apiwffault-folder-{uuid8}"
folder_path = f"{parent}/{folder_name}"

if PHASE == "fault":
    # ---- phase 2: drive the deployed process to a Faulted job -----------------
    try:
        fx = json.loads(Path(".fault_fixture.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        die(f"phase 'fault' needs .fault_fixture.json from phase 'deploy' ({exc})")
    folder_path = fx["folder_path"]

    res = uip("or", "processes", "list", "--folder-path", folder_path)
    items = res.get("Data") or []
    if isinstance(items, dict):
        items = items.get("Value") or items.get("Items") or []
    keys = [p.get("Key") or p.get("Id") for p in items if isinstance(p, dict)]
    if not keys:
        die(f"no process in {folder_path!r} after deploy")

    res = uip("or", "jobs", "start", str(keys[0]))
    jobs = ((res.get("Data") or {}).get("Jobs") or []) if isinstance(res.get("Data"), dict) else []
    job_id = (jobs[0].get("Key") if jobs and isinstance(jobs[0], dict) else None)
    if not job_id:
        die(f"could not start a job on process {keys[0]!r}: {res.get('Message')!r}")

    state = ""
    deadline = time.monotonic() + POLL_BUDGET_S
    while time.monotonic() < deadline:
        data = uip("or", "jobs", "get", str(job_id)).get("Data") or {}
        state = str(data.get("State") or data.get("Status") or "")
        if state.lower() in TERMINAL:
            break
        time.sleep(POLL_SLEEP_S)
    if state.lower() != "faulted":
        die(f"job {job_id} reached state {state!r} within {POLL_BUDGET_S}s, expected 'Faulted' — the fixture did not fail as designed")

    # The handover: job id and where it ran. Nothing about WHY.
    Path("incident.json").write_text(json.dumps({
        "job_id": job_id,
        "folder_path": folder_path,
        "reported_by": "overnight schedule monitor",
    }, indent=2) + "\n")
    print(f"OK: job {job_id} is Faulted in {folder_path}; incident.json written")
    sys.exit(0)

# ---- phase 1: build and deploy the faulting workflow -------------------------
# 1) Project shell in the documented Studio Web shape
if uip("solution", "init", SOLUTION_DIR).get("Result") != "Success" and not Path(SOLUTION_DIR).is_dir():
    die(f"`uip solution init {SOLUTION_DIR}` failed")
uip("api-workflow", "init", PROJECT_NAME, cwd=SOLUTION_DIR)
wf_path = Path(SOLUTION_DIR) / PROJECT_NAME / "Workflow.json"
if not wf_path.is_file():
    die(f"`uip api-workflow init {PROJECT_NAME}` produced no Workflow.json")

# 2) The checked-in faulting workflow replaces the scaffold's empty one
fixture = Path(__file__).resolve().parent / "fixtures" / "faulting-workflow.json"
if not fixture.is_file():
    die(f"fixture missing: {fixture}")
shutil.copyfile(fixture, wf_path)

res = uip("api-workflow", "validate", str(wf_path))
if (res.get("Data") or {}).get("Status") != "Valid":
    die(f"fixture does not validate — it must pass validate and fail only at RUNTIME: {res.get('Instructions')!r}")

# 3) Ship it
res = uip("solution", "pack", ".", "./out", "--name", package_name, "--version", "1.0.0", cwd=SOLUTION_DIR)
if res.get("Result") != "Success":
    die(f"pack failed: {res.get('Message')!r}")
zip_path = Path(SOLUTION_DIR) / "out" / f"{package_name}_1.0.0.zip"
if not zip_path.is_file():
    die(f"packed archive not found at {zip_path}")

res = uip("solution", "publish", str(zip_path))
if res.get("Result") != "Success":
    die(f"publish failed: {res.get('Message')!r}")

res = uip(
    "solution", "deploy", "run",
    "--name", deploy_name,
    "--package-name", package_name,
    "--package-version", "1.0.0",
    "--folder-name", folder_name,
    "--parent-folder-path", parent,
)
if res.get("Result") != "Success":
    die(f"deploy failed: {res.get('Message')!r}")

# The scaffold has served its purpose — it is now deployed. Remove it before the
# agent starts: fixtures/faulting-workflow.json carries the fault sentinel the
# checker requires the agent to find in the job's Data.Info, and leaving a copy in
# the working directory would let the agent read it off disk instead. That would
# contradict the prompt ("that is everything we have") and hollow out the test.
shutil.rmtree(SOLUTION_DIR, ignore_errors=True)

# Teardown coordinates for post_run + phase 2, kept out of the agent's handover.
Path(".fault_fixture.json").write_text(json.dumps({
    "uuid8": uuid8,
    "deploy_name": deploy_name,
    "package_name": package_name,
    "folder_path": folder_path,
}, indent=2) + "\n")

print(f"OK: deployed {deploy_name} to {folder_path}; run phase 'fault' next")
