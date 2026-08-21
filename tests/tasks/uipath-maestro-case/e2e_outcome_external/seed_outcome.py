#!/usr/bin/env python3
"""pre_run: mint this run's reference token and stage the SDD that carries it.

Renders ``sdd-template.md`` into the sandbox as ``sdd.md`` with ``{{RUN_TOKEN}}``
replaced by a fresh token, and records the token in ``seed.json`` for the graders.

Why a per-run token: ``uip maestro case debug`` has no ``--input`` flag, so the
reference cannot be injected at execution time — it has to be baked into the
design the agent builds from. And because the Outlook mailbox and the Jira project
are SHARED sandboxes that other suites write to, the graders cannot assert on "the
newest record"; they match this run's token exactly. That also keeps parallel
replicates from seeing each other's records.

Runs from the sandbox CWD (same contract as tests/tasks/uipath-platform/seed.py).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid

PLACEHOLDER = "{{RUN_TOKEN}}"
TEMPLATE = "sdd-template.md"
STAGED = "sdd.md"

# Kept in sync with outcome_probe.py (duplicated rather than imported so pre_run
# stays a standalone script with no import-path assumptions).
REQUIRED_CONNECTIONS = {
    "Outlook 365 sandbox": "dd657127-91f5-4568-a3a3-c024bc03fb0f",
    "Jira sandbox": "f5273a4d-d492-4bcd-a106-5a20bf89a3ef",
}


def check_connections() -> list[str]:
    """Verify both connections are live BEFORE an agent run is spent on the task.

    coder_eval has no skip semantics, so a revoked connection discovered at grading
    time is scored as a skill failure. Failing here instead makes the run error out
    with the cause named, and costs nothing.
    """
    problems = []
    for label, connection_id in REQUIRED_CONNECTIONS.items():
        try:
            proc = subprocess.run(
                ["uip", "is", "connections", "ping", connection_id,
                 "--force-refresh", "--output", "json"],
                capture_output=True, text=True, timeout=120)
            payload = json.loads(proc.stdout)
        except Exception as exc:
            problems.append(f"{label} ({connection_id}): ping failed — {exc!r}")
            continue
        status = (payload.get("Data") or {}).get("Status")
        if payload.get("Result") != "Success" or status != "Enabled":
            problems.append(f"{label} ({connection_id}): Result="
                            f"{payload.get('Result')} Status={status}")
    return problems


def main() -> int:
    problems = check_connections()
    if problems:
        print("seed_outcome: ENVIRONMENT gap — required sandbox connections are not "
              "usable, so this task cannot measure outcomes:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    here = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(here, TEMPLATE)

    if not os.path.exists(template_path):
        print(f"seed_outcome: missing {template_path}", file=sys.stderr)
        return 1

    with open(template_path) as fh:
        body = fh.read()

    if PLACEHOLDER not in body:
        print(f"seed_outcome: {TEMPLATE} has no {PLACEHOLDER} placeholder",
              file=sys.stderr)
        return 1

    token = "OBT-" + uuid.uuid4().hex[:8].upper()
    rendered = body.replace(PLACEHOLDER, token)

    with open(STAGED, "w") as fh:
        fh.write(rendered)
    with open("seed.json", "w") as fh:
        json.dump({"run_token": token}, fh, indent=1)

    print(f"seed_outcome: run_token={token} "
          f"({rendered.count(token)} occurrences in {STAGED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
