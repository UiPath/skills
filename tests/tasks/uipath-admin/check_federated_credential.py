#!/usr/bin/env python3
"""Verify an external app named 'e2e-federated-app' has a federated credential."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, find_one, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="check_fedcred: %(message)s")


def main():
    # Find the external app (poll for eventual consistency)
    def find_app():
        apps = run_cli(["admin", "external-apps", "list"])
        if not apps or apps.get("Result") != "Success":
            return None
        return find_one(apps, "e2e-federated-app", ["name"])

    app = poll(find_app)
    if not app:
        fail("External app 'e2e-federated-app' not found after retries")

    client_id = app.get("id")
    if not client_id:
        fail("App found but missing 'id' field")

    ok(f"Found app (id={client_id})")

    # Check federated credentials
    creds = run_cli(["admin", "external-apps", "federated-credentials", "list", client_id])
    if not creds or creds.get("Result") != "Success":
        fail("federated-credentials list did not return Success")

    cred_count = len(creds.get("Data", []))
    if cred_count < 1:
        fail(f"Expected at least 1 federated credential, got {cred_count}")

    ok(f"App has {cred_count} federated credential(s)")


main()
