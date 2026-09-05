#!/usr/bin/env python3
"""Pre-run seed for the federated-credentials smoke: ensure a PERSISTENT host
external app exists (created once, never deleted) and start the run with no
federated credentials on it.

Why persistent: identity-service has a create->read cross-partition
inconsistency (PLT-107839 investigation) — a freshly-created app's client record
is not materialized in the org partition that the federated-credentials endpoint
queries, so `federated-credentials create` 400s with "Client not found in
partition" on brand-new apps. A durable, already-materialized app resolves
reliably, so the test churns only the credential on this host. Always exits 0.
"""

import logging
import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from admin_helpers import run_cli, poll, first_list as _first_list

logging.basicConfig(level=logging.INFO, format="setup_fedcred_host: %(message)s")
logger = logging.getLogger(__name__)

HOST = "ce-identity-fedcred-host"


def find_host():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        return None
    for a in data.get("Data", []):
        if (a.get("Name") or a.get("name") or "") == HOST:
            return a.get("ClientId") or a.get("clientId") or a.get("Id") or a.get("id")
    return None


def clear_fed_creds(cid):
    data = run_cli(["admin", "external-apps", "federated-credentials", "list", cid])
    if not data or data.get("Result") != "Success":
        return  # not materialized yet, or none — nothing to clear
    for c in (_first_list(data.get("Data")) or []):
        crid = c.get("Id") or c.get("id")
        if crid:
            run_cli(["admin", "external-apps", "federated-credentials", "delete", cid, crid])


def main():
    cid = find_host()
    if not cid:
        # Create the persistent host once. It is intentionally NOT deleted by any
        # cleanup so it can materialize in the org partition and be reused.
        res = run_cli(["admin", "external-apps", "create", HOST, "--app-scope", "OR.Folders,OR.Jobs"])
        logger.info("Created persistent fed-cred host '%s': %s", HOST, (res or {}).get("Result"))
        cid = poll(find_host)

    if not cid:
        logger.warning("Host app '%s' not resolvable in list — cannot pre-clear", HOST)
        return

    clear_fed_creds(cid)
    logger.info("Host '%s' ready (clientId=%s), federated credentials cleared", HOST, cid)


main()
sys.exit(0)
