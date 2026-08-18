#!/usr/bin/env python3
"""Verify the federated-credentials maintain e2e outcome by reading the host app's
credential list back.

  1. federated-credentials update — 'ce-fedcred-main' is still there and its
                                    subject now targets refs/heads/release, while
                                    issuer and audience survive unchanged. Update
                                    is a FULL REPLACE (all fields required), so an
                                    agent that sends only --subject without first
                                    reading the credential wipes or errors on the
                                    other fields and fails here.
  2. federated-credentials delete — 'ce-fedcred-legacy' is gone.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll, fail, ok, first_list as _first_list

logging.basicConfig(level=logging.INFO, format="verify_fedcred_maintained: %(message)s")

HOST = "ce-identity-fedcred-maintain-host"
CRED_MAIN = "ce-fedcred-main"
CRED_LEGACY = "ce-fedcred-legacy"
EXPECTED_SUBJECT = "repo:myorg/myrepo:ref:refs/heads/release"
SEEDED_SUBJECT = "repo:myorg/myrepo:ref:refs/heads/main"
REQUIRED_ISSUER = "token.actions.githubusercontent.com"
REQUIRED_AUDIENCE = "https://cloud.uipath.com"


def _get(item, *keys):
    for k in keys:
        v = item.get(k) or item.get(k[0].lower() + k[1:])
        if v:
            return v
    return ""


def client_id():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        return None
    for a in data.get("Data", []):
        if (a.get("Name") or a.get("name") or "") == HOST:
            return a.get("ClientId") or a.get("clientId") or a.get("Id") or a.get("id")
    return None


def main():
    cid = poll(client_id)
    if not cid:
        fail(f"host external app '{HOST}' not found — setup may have failed")

    def creds():
        data = run_cli(["admin", "external-apps", "federated-credentials", "list", cid])
        if not data or data.get("Result") != "Success":
            return None
        return _first_list(data.get("Data"))

    def retargeted():
        found = creds()
        if not found:
            return None
        for c in found:
            if _get(c, "Name") == CRED_MAIN and EXPECTED_SUBJECT in _get(c, "Subject"):
                return found
        return None

    found = poll(retargeted)
    if not found:
        found = creds()
        if found is None:
            fail(f"could not list federated credentials on '{HOST}' — cannot verify")
        summary = [(_get(c, "Name"), _get(c, "Subject")) for c in found]
        fail(f"no credential named '{CRED_MAIN}' targeting {EXPECTED_SUBJECT}; present: {summary}")

    main_cred = next(c for c in found if _get(c, "Name") == CRED_MAIN)
    subject = _get(main_cred, "Subject")
    if SEEDED_SUBJECT in subject:
        fail(f"'{CRED_MAIN}' still targets the seeded branch ({subject}) — retarget did not land")

    issuer = _get(main_cred, "Issuer")
    if REQUIRED_ISSUER not in issuer:
        fail(f"'{CRED_MAIN}' lost its issuer on update (got {issuer!r}) — "
             "federated-credentials update is a full replace; re-read the credential first")

    audience = _get(main_cred, "Audience")
    if REQUIRED_AUDIENCE not in audience:
        fail(f"'{CRED_MAIN}' lost its audience on update (got {audience!r}) — "
             "federated-credentials update is a full replace; re-read the credential first")

    if any(_get(c, "Name") == CRED_LEGACY for c in found):
        fail(f"credential '{CRED_LEGACY}' still exists on '{HOST}' — it was not deleted")

    ok(f"'{CRED_MAIN}' retargeted to {subject} with issuer and audience preserved, "
       f"'{CRED_LEGACY}' deleted")


main()
