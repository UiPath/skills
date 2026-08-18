#!/usr/bin/env python3
"""Verify the external-app maintain e2e outcome by reading tenant state back.

  1. external-apps update   — 'ce-identity-extapp-consolidated' exists (renamed
                              from 'ce-identity-extapp-active', which must be
                              gone) and its app scopes are now OR.Folders +
                              OR.Jobs with OR.Assets dropped. Scopes are REPLACED
                              not merged, so a lazy update leaves OR.Assets in
                              place and fails here.
  2. delete-secret          — no secret described 'ce-extapp-stale-secret'
                              remains, while at least one secret survives.
  3. external-apps delete   — 'ce-identity-extapp-retired' is gone.

Scope and secret assertions read the values nested under scope-/secret-named keys
rather than the whole JSON blob, so an unrelated field mentioning OR.Assets
cannot mask a failed narrowing.
"""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_extapp_maintained: %(message)s")

APP_SEEDED = "ce-identity-extapp-active"
APP_RENAMED = "ce-identity-extapp-consolidated"
APP_RETIRED = "ce-identity-extapp-retired"
STALE_SECRET = "ce-extapp-stale-secret"
REQUIRED_SCOPES = ("OR.Folders", "OR.Jobs")
DROPPED_SCOPE = "OR.Assets"


def _name(app):
    return app.get("Name") or app.get("name") or app.get("DisplayName") or ""


def _cid(app):
    return app.get("ClientId") or app.get("clientId") or app.get("Id") or app.get("id")


def apps():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data", [])


def collect(obj, key_needle):
    """Collect every value nested under a key whose name contains key_needle."""
    out = []

    def walk(node, under):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, under or key_needle in k.lower())
        elif isinstance(node, list):
            for v in node:
                walk(v, under)
        elif under and node is not None:
            out.append(str(node))

    walk(obj, False)
    return out


def secret_records(details):
    """Return the list of secret records if the app details expose one."""
    if isinstance(details, dict):
        for k, v in details.items():
            if "secret" in k.lower() and isinstance(v, list):
                return v
        for v in details.values():
            found = secret_records(v)
            if found is not None:
                return found
    return None


def main():
    def renamed_present():
        found = apps()
        if found is None:
            return None
        for a in found:
            if _name(a) == APP_RENAMED:
                return a
        return None

    app = poll(renamed_present)
    if not app:
        found = apps() or []
        names = sorted(n for n in (_name(a) for a in found) if n.startswith("ce-identity-extapp"))
        fail(f"external app '{APP_RENAMED}' not found — rename did not land; markers present: {names}")

    found = apps()
    if found is None:
        fail("could not list external apps — cannot verify tenant state")
    names = [_name(a) for a in found]
    if APP_SEEDED in names:
        fail(f"app still named '{APP_SEEDED}' — a new app was created instead of updating the existing one")
    if APP_RETIRED in names:
        fail(f"app '{APP_RETIRED}' still exists — it was not deleted")

    cid = _cid(app)
    got = run_cli(["admin", "external-apps", "get", cid])
    if not got or got.get("Result") != "Success":
        fail(f"external-apps get failed for '{APP_RENAMED}' (clientId={cid}) — cannot verify scopes or secrets")
    details = got.get("Data") if isinstance(got, dict) and "Data" in got else got

    scopes = " ".join(collect(details, "scope"))
    missing = [s for s in REQUIRED_SCOPES if s not in scopes]
    if missing:
        fail(f"app '{APP_RENAMED}' is missing requested scopes {missing}; scopes={scopes[:400]}")
    if DROPPED_SCOPE in scopes:
        fail(f"app '{APP_RENAMED}' still carries {DROPPED_SCOPE} — scopes are replaced, not merged; scopes={scopes[:400]}")

    blob = json.dumps(details)
    if STALE_SECRET in blob:
        fail(f"secret described '{STALE_SECRET}' still present on '{APP_RENAMED}' — delete-secret did not land")

    secrets = secret_records(details)
    if secrets is None:
        logging.warning("app details expose no secret collection — cannot assert a secret survived")
    elif len(secrets) < 1:
        fail(f"app '{APP_RENAMED}' has no secrets left — the surviving secret was deleted too")

    ok(f"app renamed to '{APP_RENAMED}' with scopes narrowed to {list(REQUIRED_SCOPES)}, "
       f"'{STALE_SECRET}' deleted, '{APP_RETIRED}' deleted")


main()
