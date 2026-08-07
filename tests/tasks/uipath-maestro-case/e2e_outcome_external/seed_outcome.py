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
import sys
import uuid

PLACEHOLDER = "{{RUN_TOKEN}}"
TEMPLATE = "sdd-template.md"
STAGED = "sdd.md"


def main() -> int:
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
