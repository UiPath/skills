#!/usr/bin/env python3
"""Verify an external app named 'e2e-federated-app' has a federated credential."""

import logging
import sys

sys.path.insert(0, sys.path[0])
from admin_helpers import run_cli, find_one, fail, ok

logging.basicConfig(level=logging.INFO, format="check_fedcred: %(message)s")


def main():
    # Find the external app
    apps = run_cli(["admin", "external-apps", "list"])
    if not apps or apps.get("Result") != "Success":
        fail("external-apps list did not return Success")

    app = find_one(apps, "e2e-federated-app", ["name"])
    if not app:
        fail("External app 'e2e-federated-app' not found")

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


if __name__ == "__main__":
    main()
