#!/usr/bin/env python3
"""pre_run: seed the escalation cases for the Jira-ticket outcome eval.

No live issue is created here; the agent's flow creates one per case when the
grader runs `flow debug`. The prompt names no variables, so each case's
inputs are keyed by MEANING (the grader maps them onto whatever inputs the
agent declared) and its expected results are values the grader looks for
among the declared outputs. The prompt's rules:

- Sev1: an Enterprise customer's production is down with no workaround.
- Sev2: production is down but there is a workaround.
- Sev3: everything else, including non-Enterprise customers who are down
  without a workaround.
- Engineering is needed for Sev1 and Sev2; a ticket is opened for every
  escalation, duplicates included.

Two cases: an Enterprise outage with no workaround (Sev1), and a duplicate
Standard-tier outage with no workaround (Sev3, and it still gets a ticket).
A fresh case reference per run is in each ticket title, which is how the
grader proves the ticket it reads back is this run's.

Resolving the connection and the CE project's Task type here is the
preflight: when the Jira connection cannot read the project (403 Forbidden),
the run ends as ERROR before the agent starts, instead of a FAILURE scored
against the agent.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path

import jira_is

tag = secrets.token_hex(4)
conn = jira_is.connection_id()
jira_is.issuetype_id(conn)  # preflight only: the CE project and its Task type are readable
cases = [
    {
        "name": "enterprise-down-no-workaround-sev1",
        "inputs": {
            "senderEmail": "jane.doe@acmecorp.com",
            "senderDomain": "acmecorp.com",
            "subject": "Production down: checkout API returning 500s",
            "body": "Critical outage since 09:15 UTC. All checkout requests fail with HTTP 500.",
            "tier": "Enterprise",
            "productionDown": True,
            "workaround": False,
            "attachments": False,
            "match": "single",
            "duplicate": False,
            "caseRef": f"ESC-JIRA-{tag}-1",
        },
        "expected": {"severity": "Sev1", "engineering": True},
    },
    {
        "name": "duplicate-standard-down-no-workaround-sev3",
        "inputs": {
            "senderEmail": "sam.lee@smallshop.com",
            "senderDomain": "smallshop.com",
            "subject": "Storefront still down",
            "body": "Following up on my earlier email: every visitor still gets an error page.",
            "tier": "Standard",
            "productionDown": True,
            "workaround": False,
            "attachments": False,
            "match": "single",
            "duplicate": True,
            "caseRef": f"ESC-JIRA-{tag}-2",
        },
        "expected": {"severity": "Sev3", "engineering": False},
    },
]
seed = {"tag": tag, "project_key": jira_is.PROJECT_KEY, "cases": cases}
Path("seed.json").write_text(json.dumps(seed, indent=2) + "\n", encoding="utf-8")
print(f"OK: wrote seed ({len(cases)} cases, tag={tag}, project={jira_is.PROJECT_KEY})")
