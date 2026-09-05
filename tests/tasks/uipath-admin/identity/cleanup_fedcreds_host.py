#!/usr/bin/env python3
"""Best-effort teardown for the federated-credentials smoke: delete the
federated credentials on the persistent host app, but KEEP the host app itself
(it is a durable fixture — see setup_fedcred_host.py). Always exits 0."""

import logging
import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from admin_helpers import run_cli, first_list as _first_list

logging.basicConfig(level=logging.INFO, format="cleanup_fedcreds_host: %(message)s")
logger = logging.getLogger(__name__)

HOST = "ce-identity-fedcred-host"


def main():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list external apps — skipping cleanup")
        return
    cid = None
    for a in data.get("Data", []):
        if (a.get("Name") or a.get("name") or "") == HOST:
            cid = a.get("ClientId") or a.get("clientId") or a.get("Id") or a.get("id")
            break
    if not cid:
        return
    creds = run_cli(["admin", "external-apps", "federated-credentials", "list", cid])
    if not creds or creds.get("Result") != "Success":
        return
    for c in (_first_list(creds.get("Data")) or []):
        crid = c.get("Id") or c.get("id")
        if crid:
            logger.info("Deleting federated credential id=%s on host", crid)
            run_cli(["admin", "external-apps", "federated-credentials", "delete", cid, crid])


main()
sys.exit(0)
