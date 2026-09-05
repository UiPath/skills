#!/usr/bin/env python3
"""Pre-run seed for the secret-rotate smoke: (re)create a confidential external
app whose client secret the agent will rotate. Always exits 0."""

import logging
import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="setup_rotateapp: %(message)s")
logger = logging.getLogger(__name__)

APP = "ce-identity-smoke-rotateapp"


def main():
    data = run_cli(["admin", "external-apps", "list"])
    if data and data.get("Result") == "Success":
        for a in data.get("Data", []):
            if (a.get("Name") or a.get("name") or "") == APP:
                cid = a.get("ClientId") or a.get("clientId") or a.get("Id") or a.get("id")
                if cid:
                    run_cli(["admin", "external-apps", "delete", cid])

    res = run_cli(["admin", "external-apps", "create", APP, "--app-scope", "OR.Folders,OR.Jobs"])
    logger.info("Seeded rotateapp '%s': %s", APP, (res or {}).get("Result"))


main()
sys.exit(0)
