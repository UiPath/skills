#!/usr/bin/env python3
"""Grade the diagnosis against the real job's fault, not against the agent's prose.

Three assertions:

  1. ./job_evidence.json is real `uip or jobs get` output for the incident's job —
     parses as JSON, carries the job id from incident.json, and shows State
     "Faulted". Proves the agent actually queried the job.
  2. ./diagnosis.txt names the actual upstream failure. The fault sentinel
     ("ORDER_SERVICE_UNREACHABLE" / 503) appears NOWHERE in the prompt or in
     incident.json — the only way to learn it is to read the job's Data.Info, so
     a plausible-sounding guess cannot pass.
  3. The diagnosis does not claim the run succeeded. `uip or jobs logs` reports
     "Workflow completed" even for a Faulted job (verified alpha 2026-08-18), and
     an agent that diagnoses from logs instead of `jobs get` reaches exactly that
     wrong conclusion. This is the trap the task exists to catch.

Cross-checked against the live job rather than trusting the captured file alone,
so a hand-written job_evidence.json still has to agree with the tenant.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

# Tokens from the fixture's thrown error. Kept out of the prompt on purpose.
SENTINELS = ("order_service_unreachable", "503")
SUCCESS_CLAIMS = (
    r"\bcompleted successfully\b",
    r"\bran successfully\b",
    r"\bno (?:error|failure|fault)s? (?:were )?(?:found|detected)\b",
    r"\bjob succeeded\b",
)


def fail(msg):
    sys.exit(f"FAIL: {msg}")


incident = json.loads(Path("incident.json").read_text())
job_id = str(incident.get("job_id") or "")
if not job_id:
    fail("incident.json has no job_id — fixture problem, not an agent problem")

# 1) Captured evidence is real jobs-get output for THIS job
ev_path = Path("job_evidence.json")
if not ev_path.is_file():
    fail("./job_evidence.json missing — no captured proof the agent inspected the job")
try:
    evidence = json.loads(ev_path.read_text())
except (OSError, json.JSONDecodeError) as exc:
    fail(f"./job_evidence.json is not valid JSON ({exc}) — expected raw `uip or jobs get` output")
ev_blob = json.dumps(evidence)
if job_id.lower() not in ev_blob.lower():
    fail(f"./job_evidence.json does not mention job {job_id} — it is about some other run")
if not re.search(r"faulted", ev_blob, re.I):
    fail("./job_evidence.json shows no Faulted state — the agent did not capture the fault")

# Cross-check the tenant so a fabricated evidence file cannot stand alone.
r = subprocess.run(
    ["uip", "or", "jobs", "get", job_id, "--output", "json"],
    capture_output=True, text=True, timeout=120,
)
raw = r.stdout or ""
if "{" in raw:
    live = json.loads(raw[raw.index("{"):]).get("Data") or {}
    live_state = str(live.get("State") or live.get("Status") or "")
    if live_state and live_state.lower() != "faulted":
        fail(f"live job {job_id} is {live_state!r}, not Faulted — fixture drift, re-check the seed")

# 2) The diagnosis names the real cause
diag_path = Path("diagnosis.txt")
if not diag_path.is_file():
    fail("./diagnosis.txt missing — the agent never recorded a root cause")
diag = diag_path.read_text().strip()
if not diag:
    fail("./diagnosis.txt is empty")
low = diag.lower()
hits = [s for s in SENTINELS if s in low]
if not hits:
    fail(
        "./diagnosis.txt does not name the actual failure. Expected the upstream error "
        f"reported in the job's Data.Info; got: {diag[:300]!r}. "
        "That string is only obtainable from `uip or jobs get` — `jobs logs` does not carry it."
    )

# 3) It did not conclude the run was fine
for pattern in SUCCESS_CLAIMS:
    if re.search(pattern, low):
        fail(
            f"./diagnosis.txt claims success (matched {pattern!r}) for a Faulted job. "
            "`uip or jobs logs` reports 'Workflow completed' even when the job faulted — "
            "diagnose from `uip or jobs get`'s Data.State / Data.Info instead."
        )

print(f"OK: job {job_id} confirmed Faulted; diagnosis names the real cause (matched {hits})")
