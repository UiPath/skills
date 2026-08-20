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
import re
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_extapp_maintained: %(message)s")

APP_SEEDED = "ce-identity-extapp-active"
APP_RENAMED = "ce-identity-extapp-consolidated"
APP_RETIRED = "ce-identity-extapp-retired"
STALE_SECRET = "ce-extapp-stale-secret"

# The prompt asks for the app to reach Orchestrator folders and jobs ONLY, so the
# assertion is set EQUALITY, not "required present and Assets absent". A superset
# check would pass an agent that widened the app to OR.Robots/OR.Users while
# nominally satisfying the request — the opposite of least privilege.
EXPECTED_SCOPES = frozenset({"OR.Folders", "OR.Jobs"})
STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_extapp_maintain_seed.txt")


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

    # The rename must have happened IN PLACE. Comparing names only would accept
    # delete-the-app-and-create-a-new-one, which is a different (and destructive)
    # operation than `external-apps update`.
    try:
        with open(STATE_FILE) as f:
            seeded_cid = f.read().strip()
    except OSError:
        fail(f"seed state file {STATE_FILE} missing — cannot prove the rename was in place; "
             "setup_extapp_maintain.py did not record the seeded clientId")
    if not seeded_cid:
        fail("seed state file is empty — cannot prove the rename was in place")
    if str(cid) != seeded_cid:
        fail(f"'{APP_RENAMED}' has clientId={cid} but the seeded app was {seeded_cid} — the app was "
             "replaced (delete + create), not renamed in place via `external-apps update`")

    got = run_cli(["admin", "external-apps", "get", cid])
    if not got or got.get("Result") != "Success":
        fail(f"external-apps get failed for '{APP_RENAMED}' (clientId={cid}) — cannot verify scopes or secrets")
    details = got.get("Data") if isinstance(got, dict) and "Data" in got else got

    scope_text = " ".join(collect(details, "scope"))
    actual_scopes = frozenset(re.findall(r"\bOR\.[A-Za-z]+\b", scope_text))
    if not actual_scopes:
        fail(f"could not read any OR.* scope off '{APP_RENAMED}' — cannot verify the narrowing; "
             f"scope fields={scope_text[:300]!r}")
    if actual_scopes != EXPECTED_SCOPES:
        extra = sorted(actual_scopes - EXPECTED_SCOPES)
        missing = sorted(EXPECTED_SCOPES - actual_scopes)
        fail(f"app '{APP_RENAMED}' scopes are {sorted(actual_scopes)}, expected exactly "
             f"{sorted(EXPECTED_SCOPES)} (extra={extra}, missing={missing}) — scopes are replaced, "
             "not merged, and the request was folders and jobs ONLY")

    blob = json.dumps(details)
    if STALE_SECRET in blob:
        fail(f"secret described '{STALE_SECRET}' still present on '{APP_RENAMED}' — delete-secret did not land")

    # Non-vacuous: if the secret collection cannot be read at all we cannot tell
    # "one secret survived" from "every secret was deleted", so fail rather than
    # warn. Previously this path only logged, letting the assertion pass silently.
    secrets = secret_records(details)
    if secrets is None:
        fail(f"could not read a secret collection off '{APP_RENAMED}' — cannot assert that the "
             "non-stale secret survived; `external-apps get` shape may have changed")
    if len(secrets) < 1:
        fail(f"app '{APP_RENAMED}' has no secrets left — the surviving secret was deleted too")

    ok(f"app {seeded_cid} renamed in place to '{APP_RENAMED}' with scopes exactly "
       f"{sorted(EXPECTED_SCOPES)}, '{STALE_SECRET}' deleted ({len(secrets)} secret(s) remain), "
       f"'{APP_RETIRED}' deleted")


main()
