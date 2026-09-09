#!/usr/bin/env python3
"""Verify the agent rotated the marker app's client secret.

Reads the app back with `external-apps get` and looks for the marker secret
description the agent was asked to set. Exits 1 if not found (rotate failed or
`get` does not expose secret metadata — in which case this needs a rethink).
"""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_secret_rotated: %(message)s")

APP = "ce-identity-smoke-rotateapp"
SECRET_MARKER = "ce-identity-smoke-rotated"


def client_id():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        return None
    for a in data.get("Data", []):
        if (a.get("Name") or a.get("name") or "") == APP:
            return a.get("ClientId") or a.get("clientId") or a.get("Id") or a.get("id")
    return None


def main():
    cid = poll(client_id)
    if not cid:
        fail(f"external app '{APP}' not found — setup may have failed")

    def rotated():
        data = run_cli(["admin", "external-apps", "get", cid])
        if not data or data.get("Result") != "Success":
            return None
        blob = json.dumps(data.get("Data") if isinstance(data, dict) else data)
        return SECRET_MARKER in blob

    if not poll(rotated):
        fail(f"no secret described '{SECRET_MARKER}' on app '{APP}' — rotate failed or get hides secrets")
    ok(f"rotated secret '{SECRET_MARKER}' present on app '{APP}'")


main()
