#!/usr/bin/env python3
"""Query the tenant: the API workflow was deployed, RAN, and then taken down.

Three assertions. The middle one is the point of the task; the outer two prove it
happened against a real tenant and left nothing standing.

  1. `solution deploy list` still carries apiwf-deploy-<uuid8>
     -> a deployment was really created. Uninstalled deployments remain listed as
        history rows (`Operation: Uninstall`), so this holds after teardown.
  2. ./job_status.json shows the JOB in state Successful
     -> the deployed workflow actually executed. Read from Data.State, never by
        grepping the payload: `uip or jobs get` wraps every successful CALL in
        {"Result": "Success"}, so a substring match passes a Faulted job.
        Captured during the run because teardown removes the folder, and with it
        any way to query jobs afterwards (same pattern as
        operate/run_execute's run_85.json).
  3. the deploy's folder is GONE
     -> the agent tore its deployment back down.

(1) + (3) together are what make this reliable: a row with no folder behind it
means deployed-then-removed. A row WITH its folder means the tenant was left
dirty; no row at all means it never deployed.

Do NOT assert on ActivationStatus — it reads "None" both before activation and
after a successful uninstall, so it cannot distinguish the two. `Operation` +
`OperationStatus` are the fields that identify a completed uninstall.

Known gameability, accepted deliberately: job_status.json is a file the agent
writes, so a determined agent could fabricate it. The `command_executed` criteria
on `or jobs start` plus assertion (1) make that a conscious forgery rather than a
lazy shortcut — the same trade-off operate/run_execute makes.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

GUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def _pick(d, *names):
    """Fetch a key regardless of Pascal/camel/lower casing."""
    if not isinstance(d, dict):
        return None
    for n in names:
        for k in (n, n[:1].lower() + n[1:], n.lower()):
            if k in d:
                return d[k]
    return None


def _items(env):
    data = env.get("Data") or []
    if isinstance(data, dict):
        return _pick(data, "Deployments", "Value", "Items", "Results") or []
    return data


def uip_json(*args):
    r = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=120,
    )
    raw = r.stdout or ""
    if "{" not in raw:
        sys.exit(f"FAIL: uip {' '.join(args)} produced no JSON ({r.stderr.strip()[:200]})")
    try:
        return json.loads(raw[raw.index("{"):])
    except json.JSONDecodeError:
        sys.exit(f"FAIL: uip {' '.join(args)} produced unparseable output")


seed = json.loads(Path("seed.json").read_text())
uuid8 = seed.get("uuid8")
if not uuid8:
    sys.exit("FAIL: seed.json missing uuid8")

deploy_name = f"apiwf-deploy-{uuid8}"
folder_path = f"{seed.get('parent_folder_path') or 'Shared'}/apiwf-deploy-folder-{uuid8}"

# 1) A deployment was created (history rows survive teardown)
dl = uip_json("solution", "deploy", "list", "--limit", "200")
if dl.get("Result") != "Success":
    sys.exit(f"FAIL: `solution deploy list` Result={dl.get('Result')!r}: {dl.get('Message')!r}")
names = [_pick(d, "Name", "DeploymentName") for d in _items(dl) if isinstance(d, dict)]
if deploy_name not in names:
    sys.exit(
        f"FAIL: no deployment named {deploy_name!r} — the solution was never deployed. "
        f"Saw {names[:5]}"
    )

# 2) The deployed workflow ran, per evidence captured during the run
status_file = Path("job_status.json")
if not status_file.is_file():
    sys.exit(
        "FAIL: ./job_status.json missing — no captured proof the deployed process ran. "
        "The agent had to save the job's status output before tearing the deployment down."
    )
try:
    payload = json.loads(status_file.read_text())
except (OSError, json.JSONDecodeError) as exc:
    sys.exit(f"FAIL: ./job_status.json is not valid JSON ({exc}) — expected raw `uip or jobs get` output")

blob = json.dumps(payload)
if not GUID.search(blob):
    sys.exit("FAIL: ./job_status.json carries no job identifier — does not look like real CLI output")

# Read the JOB's state, not a substring of the envelope. `uip or jobs get` wraps
# every successful CALL in {"Result": "Success", ...}, so grepping the whole
# payload for /success/ passes a Faulted job — the envelope always contains it.
data = payload.get("Data") if isinstance(payload.get("Data"), dict) else payload
job_state = str(_pick(data, "State", "Status") or "")
if not job_state:
    sys.exit(
        f"FAIL: ./job_status.json has no job State field; got {blob[:300]}. "
        "Expected raw `uip or jobs get <jobId> --output json` output, whose Data.State "
        "carries the job's outcome."
    )
if job_state.strip().lower() != "successful":
    sys.exit(
        f"FAIL: the captured job finished in state {job_state!r}, not 'Successful'. "
        "The deployed API workflow was started but did not complete successfully."
    )

# 3) The deployment was torn back down
fg = uip_json("or", "folders", "get", folder_path)
if fg.get("Result") == "Success":
    sys.exit(
        f"FAIL: folder {folder_path!r} still exists — the deployment was left standing. "
        f"Tear it down with `uip solution deploy uninstall {deploy_name} --yes`."
    )

print(
    f"OK: {deploy_name!r} was deployed, ran a Successful job (per job_status.json), "
    f"and its folder {folder_path!r} is gone — tenant left clean"
)
