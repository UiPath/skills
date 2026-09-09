#!/usr/bin/env python3
"""Verify an external OAuth2 app with the smoke marker name was created AND
carries the requested application scopes (Critical Rule #6: application scopes,
not a scopeless or user-scoped app). Reads the app back with external-apps get
and confirms the requested OR.* scope values are present."""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_external_app: %(message)s")

MARKER = "ce-identity-smoke-app"
# The prompt asks for application scopes for Folders and Jobs.
REQUIRED_SCOPES = ("OR.Folders", "OR.Jobs")


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

    # Read the app back and confirm the requested application scopes were set.
    got = run_cli(["admin", "external-apps", "get", cid])
    data = got.get("Data") if isinstance(got, dict) and "Data" in got else got
    blob = json.dumps(data)
    missing = [s for s in REQUIRED_SCOPES if s not in blob]
    assert not missing, f"app '{MARKER}' exists but is missing requested application scopes {missing}; app={blob[:400]}"
    ok(f"external app '{MARKER}' created with application scopes {list(REQUIRED_SCOPES)} (clientId={cid})")


main()
