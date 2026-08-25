#!/usr/bin/env python3
"""Verify the external-app maintain e2e outcome by reading tenant state back.

  1. external-apps update  — 'ce-identity-extapp-consolidated' exists, the seeded
                             name is gone, and the app still carries the SEEDED
                             CLIENT ID (so delete-and-recreate cannot masquerade
                             as an in-place rename). Its app scopes are exactly
                             OR.Folders + OR.Jobs.
  2. delete-secret         — exactly one secret fewer than at seed time, and none
                             described 'ce-extapp-stale-secret'.
  3. external-apps delete  — the retired app's seeded CLIENT ID is absent, which
                             a rename cannot satisfy (a rename keeps the id).

Every assertion is checked against the seed state file, so a partial seed failure
fails loudly instead of passing vacuously. Scope reading targets the app-scope
field specifically: a union over all scope-named keys conflated --app-scope with
--user-scope, letting `--app-scope OR.Folders --user-scope OR.Jobs` satisfy a set
equality check while the app could not actually reach jobs under its own identity.
"""

import json
import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_extapp_maintained: %(message)s")

APP_SEEDED = "ce-identity-extapp-active"
APP_RENAMED = "ce-identity-extapp-consolidated"
APP_RETIRED = "ce-identity-extapp-retired"
STALE_SECRET = "ce-extapp-stale-secret"
EXPECTED_SCOPES = frozenset({"OR.Folders", "OR.Jobs"})

STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_extapp_maintain_seed.json")

# Keys that carry APPLICATION scopes. Deliberately excludes anything matching
# "user" so delegated scopes cannot be counted toward the app-scope assertion.
APP_SCOPE_KEYS = ("appscope", "applicationscope", "scope")
USER_SCOPE_MARKERS = ("user", "delegat")


def _name(app):
    return app.get("Name") or app.get("name") or app.get("DisplayName") or ""


def _cid(app):
    return app.get("ClientId") or app.get("clientId") or app.get("Id") or app.get("id")


def apps():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data", [])


def app_scope_names(node):
    """Collect application scope names from the real ExternalClientDetails shape.

    Verified against run 32339130747 artifacts, the payload nests scopes two
    levels deep as OBJECTS, not strings:

        {"Resources": [{"Name": "OAuth Api Access",
                        "Scopes": [{"Name": "OR.Folders", "Description": ...,
                                    "Type": 1}, ...]}]}

    An earlier revision walked the tree carrying a "key hint" and collected any
    leaf under a scope-named key. That silently returned NOTHING here, because
    descending into each scope OBJECT replaced the hint with the object's own
    keys ("Name"/"Description"/"Type"), none of which look scope-ish. The verify
    then failed a correctly-narrowed app with "could not read any OR.* scope".

    Containers whose key marks them delegated/user scopes are skipped, so a
    `--user-scope` grant cannot be counted toward the application scope set.
    NOTE: no observed payload has yet contained user scopes, so their exact
    representation is unconfirmed; this exclusion is defensive.
    """
    out = []

    def walk(node, in_user_container=False):
        if isinstance(node, dict):
            for key, value in node.items():
                lk = key.lower()
                user_ctx = in_user_container or any(m in lk for m in USER_SCOPE_MARKERS)
                if any(s in lk for s in APP_SCOPE_KEYS) and isinstance(value, list):
                    if user_ctx:
                        continue  # delegated scopes are not application scopes
                    for entry in value:
                        if isinstance(entry, dict):
                            # NO Type filter. An earlier revision dropped
                            # entries whose Type != 1, inferred from payloads
                            # where EVERY scope was Type 1 — evidence that cannot
                            # distinguish "app scopes are Type 1" from
                            # "everything is Type 1". The artifact census shows
                            # Type is contextual (1 under external-apps get,
                            # 2 in the `scopes list` catalog), so it does not mark
                            # app-vs-user at all, and filtering on it silently
                            # dropped legitimate scopes — failing a correct agent.
                            name = entry.get("Name") or entry.get("name") or entry.get("Value")
                            if name:
                                out.append(str(name))
                        elif entry is not None:
                            out.append(str(entry))  # tolerate a bare string list
                    continue
                walk(value, user_ctx)
        elif isinstance(node, list):
            for entry in node:
                walk(entry, in_user_container)

    walk(node)
    return out


def secret_records(details):
    if isinstance(details, dict):
        for k, v in details.items():
            if "secret" in k.lower() and isinstance(v, list):
                return v
        for v in details.values():
            found = secret_records(v)
            if found is not None:
                return found
    return None


def load_seed():
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except (OSError, ValueError) as exc:
        fail(f"seed state file {STATE_FILE} missing or malformed ({exc}) — cannot verify "
             "preconditions; setup_extapp_maintain.py did not complete")
    for key in ("active_client_id", "retired_client_id", "secret_count_at_seed"):
        if not state.get(key):
            fail(f"seed state is missing '{key}' — setup did not record a complete baseline")
    return state


def main():
    seed = load_seed()
    seeded_active = str(seed["active_client_id"])
    seeded_retired = str(seed["retired_client_id"])
    secrets_at_seed = int(seed["secret_count_at_seed"])

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
    ids = {str(_cid(a)) for a in found if _cid(a)}

    if APP_SEEDED in names:
        fail(f"app still named '{APP_SEEDED}' — a new app was created instead of updating the existing one")

    cid = str(_cid(app))
    if cid != seeded_active:
        fail(f"'{APP_RENAMED}' has clientId={cid} but the seeded app was {seeded_active} — the app was "
             "replaced (delete + create), not renamed in place via `external-apps update`")

    # Id-absence, not name-absence: renaming the retired app would leave its name
    # gone while the registration still exists.
    if seeded_retired in ids:
        surviving = next((_name(a) for a in found if str(_cid(a)) == seeded_retired), "?")
        fail(f"the retired app (clientId={seeded_retired}) still exists as '{surviving}' — it was "
             "renamed or left in place, not deleted")

    got = run_cli(["admin", "external-apps", "get", cid])
    if not got or got.get("Result") != "Success":
        fail(f"external-apps get failed for '{APP_RENAMED}' (clientId={cid}) — cannot verify scopes or secrets")
    details = got.get("Data") if isinstance(got, dict) and "Data" in got else got

    scope_names = app_scope_names(details)
    actual_scopes = frozenset(n for n in scope_names if n.startswith("OR."))
    if not actual_scopes:
        fail(f"could not read any OR.* application scope off '{APP_RENAMED}' — cannot verify the "
             f"narrowing; application scope names read={scope_names[:20]!r}")
    if actual_scopes != EXPECTED_SCOPES:
        extra = sorted(actual_scopes - EXPECTED_SCOPES)
        missing = sorted(EXPECTED_SCOPES - actual_scopes)
        fail(f"app '{APP_RENAMED}' application scopes are {sorted(actual_scopes)}, expected exactly "
             f"{sorted(EXPECTED_SCOPES)} (extra={extra}, missing={missing}) — scopes are replaced, "
             "not merged, and the request was folders and jobs ONLY")

    secrets = secret_records(details)
    if secrets is None:
        fail(f"could not read a secret collection off '{APP_RENAMED}' — cannot assert the "
             "post-delete secret count; `external-apps get` shape may have changed")

    blob = json.dumps(details)
    if STALE_SECRET in blob:
        fail(f"secret described '{STALE_SECRET}' still present on '{APP_RENAMED}' — delete-secret did not land")

    # Exact cardinality against the seed baseline. "at least one left" accepted
    # a seed that never created the stale secret, and also accepted an agent that
    # generated replacement secrets while deleting the wrong one.
    expected_after = secrets_at_seed - 1
    if len(secrets) != expected_after:
        fail(f"'{APP_RENAMED}' has {len(secrets)} secret(s); expected exactly {expected_after} "
             f"(seed baseline {secrets_at_seed} minus the one stale secret) — a different number "
             "means an extra secret was generated or more than one was deleted")

    ok(f"seed baseline active={seeded_active} retired={seeded_retired} secrets={secrets_at_seed} | "
       f"app {cid} renamed IN PLACE to '{APP_RENAMED}' (seeded id preserved) | application scopes "
       f"exactly {sorted(actual_scopes)} | secrets {secrets_at_seed}->{len(secrets)} with "
       f"'{STALE_SECRET}' absent | retired id {seeded_retired} absent from {len(ids)} listed apps")


main()
