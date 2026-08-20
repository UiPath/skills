#!/usr/bin/env python3
"""Pre-run seed for the federated-credentials maintain e2e: ensure a PERSISTENT
host external app exists and start the run with exactly two known credentials on
it.

  ce-fedcred-main    -> agent retargets its subject from the main branch to the
                        release branch, preserving issuer and audience.
  ce-fedcred-legacy  -> agent deletes it.

Why a persistent host (same rationale as setup_fedcred_host.py): identity-service
has a create->read cross-partition inconsistency (PLT-107839 investigation) — a
freshly-created app is not yet materialized in the org partition the
federated-credentials endpoint queries, so `federated-credentials create` 400s
with "Client not found in partition" on brand-new apps. This test therefore owns
its own durable host, created once and never deleted, and churns only the
credentials on it. A dedicated host (not the smoke's 'ce-identity-fedcred-host')
keeps the two tests from fighting over the same credential list under -jN.

Always exits 0.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll, first_list as _first_list

logging.basicConfig(level=logging.INFO, format="setup_fedcred_maintain: %(message)s")
logger = logging.getLogger(__name__)

HOST = "ce-identity-fedcred-maintain-host"
ISSUER = "https://token.actions.githubusercontent.com"

# DELIBERATELY UNGUESSABLE. `federated-credentials update` is a full replace, so
# the point of this test is that the agent must READ the credential before
# updating it. With a canonical audience (e.g. https://cloud.uipath.com) an agent
# that never read anything could reproduce the field from context and still pass
# the preservation check — the assertion would be measuring nothing. This value
# cannot be derived from the prompt or from UiPath convention, so preserving it
# is only possible via `federated-credentials get`/`list`.
AUDIENCE = "api://ce-fedcred-maintain-8f2ad9c4"
CRED_MAIN = "ce-fedcred-main"
CRED_LEGACY = "ce-fedcred-legacy"
SUBJECT_MAIN = "repo:myorg/myrepo:ref:refs/heads/main"
SUBJECT_LEGACY = "repo:myorg/legacy-repo:ref:refs/heads/main"


def find_host():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        return None
    for a in data.get("Data", []):
        if (a.get("Name") or a.get("name") or "") == HOST:
            return a.get("ClientId") or a.get("clientId") or a.get("Id") or a.get("id")
    return None


def clear_creds(cid):
    data = run_cli(["admin", "external-apps", "federated-credentials", "list", cid])
    if not data or data.get("Result") != "Success":
        return
    for c in (_first_list(data.get("Data")) or []):
        crid = c.get("Id") or c.get("id")
        if crid:
            run_cli(["admin", "external-apps", "federated-credentials", "delete", cid, crid])


def seed_cred(cid, name, subject):
    def create():
        res = run_cli([
            "admin", "external-apps", "federated-credentials", "create", cid,
            "--name", name,
            "--issuer", ISSUER,
            "--audience", AUDIENCE,
            "--subject", subject,
        ])
        return res if (res and res.get("Result") == "Success") else None

    # Retry: a host materializing for the first time can 400 here.
    res = poll(create)
    logger.info("Seeded credential '%s' (%s): %s", name, subject, "Success" if res else "FAILED")


def main():
    cid = find_host()
    if not cid:
        # Create the durable host once. Intentionally NOT deleted by cleanup so it
        # can materialize in the org partition and be reused by later runs.
        res = run_cli(["admin", "external-apps", "create", HOST, "--app-scope", "OR.Folders,OR.Jobs"])
        logger.info("Created persistent fed-cred host '%s': %s", HOST, (res or {}).get("Result"))
        cid = poll(find_host)

    if not cid:
        logger.warning("Host app '%s' not resolvable in list — cannot seed credentials", HOST)
        return

    clear_creds(cid)
    seed_cred(cid, CRED_MAIN, SUBJECT_MAIN)
    seed_cred(cid, CRED_LEGACY, SUBJECT_LEGACY)
    logger.info("Host '%s' ready (clientId=%s) with 2 seeded credentials", HOST, cid)


main()
sys.exit(0)
