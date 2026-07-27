#!/usr/bin/env python3
"""Verify a federated credential was attached to the marker external app."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll, fail, ok, first_list as _first_list

logging.basicConfig(level=logging.INFO, format="verify_fedcred: %(message)s")

APP = "ce-identity-fedcred-host"


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

    def has_cred():
        data = run_cli(["admin", "external-apps", "federated-credentials", "list", cid])
        if not data or data.get("Result") != "Success":
            return None
        creds = _first_list(data.get("Data"))
        return creds if (creds and len(creds) > 0) else None

    c = poll(has_cred)
    if not c:
        fail(f"app '{APP}' has no federated credentials — agent did not add one")
    ok(f"app '{APP}' has {len(c)} federated credential(s)")


main()
