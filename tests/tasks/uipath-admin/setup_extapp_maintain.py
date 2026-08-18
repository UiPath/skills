#!/usr/bin/env python3
"""Pre-run seed for the external-app maintain e2e: (re)create two marker OAuth2
apps so the agent has existing registrations to inspect, edit, and retire.

  ce-identity-extapp-active   -> agent renames it and narrows its app scopes.
                                 Seeded with OR.Folders,OR.Jobs,OR.Assets plus a
                                 SECOND secret described 'ce-extapp-stale-secret'
                                 (the one the agent must delete). The creation
                                 secret stays, so delete-secret has a safe target.
  ce-identity-extapp-retired  -> agent deletes the whole app.

Grading an update and a delete on two separate apps avoids the delete-erases-the-
update-evidence problem (see identity_user_lifecycle_e2e.yaml). Always exits 0.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll

logging.basicConfig(level=logging.INFO, format="setup_extapp_maintain: %(message)s")
logger = logging.getLogger(__name__)

APP_ACTIVE = "ce-identity-extapp-active"
APP_RENAMED = "ce-identity-extapp-consolidated"
APP_RETIRED = "ce-identity-extapp-retired"
STALE_SECRET = "ce-extapp-stale-secret"

# Includes the post-rename name so a re-run starts from a clean slate.
ALL_APPS = (APP_ACTIVE, APP_RENAMED, APP_RETIRED)
SEED_SCOPES = "OR.Folders,OR.Jobs,OR.Assets"


def _name(app):
    return app.get("Name") or app.get("name") or app.get("DisplayName") or ""


def _cid(app):
    return app.get("ClientId") or app.get("clientId") or app.get("Id") or app.get("id")


def apps():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data", [])


def client_id(name):
    found = apps()
    if found is None:
        return None
    for a in found:
        if _name(a) == name:
            return _cid(a)
    return None


def main():
    existing = apps()
    if existing is None:
        logger.warning("Could not list external apps — seed skipped")
        return
    for a in existing:
        if _name(a) in ALL_APPS and _cid(a):
            run_cli(["admin", "external-apps", "delete", _cid(a)])

    res = run_cli(["admin", "external-apps", "create", APP_ACTIVE, "--app-scope", SEED_SCOPES])
    logger.info("Seeded app '%s' (%s): %s", APP_ACTIVE, SEED_SCOPES, (res or {}).get("Result"))

    res = run_cli(["admin", "external-apps", "create", APP_RETIRED, "--app-scope", "OR.Folders"])
    logger.info("Seeded app '%s': %s", APP_RETIRED, (res or {}).get("Result"))

    # Add the second, retirable secret to the active app.
    cid = poll(lambda: client_id(APP_ACTIVE))
    if not cid:
        logger.warning("App '%s' not resolvable — stale secret not seeded", APP_ACTIVE)
        return
    res = run_cli(["admin", "external-apps", "generate-secret", cid,
                   "--description", STALE_SECRET, "--expiration", "2030-01-01"])
    logger.info("Seeded stale secret '%s' on '%s': %s",
                STALE_SECRET, APP_ACTIVE, (res or {}).get("Result"))


main()
sys.exit(0)
