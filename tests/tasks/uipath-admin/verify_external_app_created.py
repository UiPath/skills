#!/usr/bin/env python3
"""Verify an external OAuth2 app with the smoke marker name was created."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_external_app: %(message)s")

MARKER = "ce-identity-smoke-app"


def find():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        return None
    for a in data.get("Data", []):
        if (a.get("Name") or a.get("name") or a.get("DisplayName") or "") == MARKER:
            return a
    return None


def main():
    a = poll(find)
    if not a:
        fail(f"no external app named '{MARKER}' found — create may have failed")
    cid = a.get("ClientId") or a.get("clientId") or a.get("Id") or a.get("id")
    ok(f"external app '{MARKER}' created (clientId={cid})")


main()
