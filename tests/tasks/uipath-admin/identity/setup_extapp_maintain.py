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
update-evidence problem (see identity_user_lifecycle_e2e.yaml).

EXITS NON-ZERO if any required fixture could not be seeded. coder_eval treats a
failing pre_run as a run ERROR. This matters: an earlier revision always exited 0,
so a silently failed `generate-secret` left no stale secret, the agent never ran
delete-secret, and the verify's "stale secret is gone" assertion passed
vacuously — emitting a success line identical to a real pass.

Writes the seeded ids and secret count to a state file so the verify can assert
its own preconditions and check id-absence (a rename preserves the id, so
name-absence alone cannot distinguish delete from rename).
"""

import json
import logging
import os
import sys
import tempfile
import time

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
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

STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_extapp_maintain_seed.json")


def die(message):
    logger.error("SEED FAILED: %s", message)
    sys.exit(1)


def _name(app):
    return app.get("Name") or app.get("name") or app.get("DisplayName") or ""


def _cid(app):
    return app.get("ClientId") or app.get("clientId") or app.get("Id") or app.get("id")


def apps():
    # `external-apps list` documents no pagination flags and rejects --limit
    # (ValidationError/invalid_argument); it returns the full set.
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


def secret_count(cid):
    """Number of secret records currently on the app, or None if unreadable."""
    got = run_cli(["admin", "external-apps", "get", cid])
    if not got or got.get("Result") != "Success":
        return None
    details = got.get("Data") if "Data" in got else got

    def find(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if "secret" in k.lower() and isinstance(v, list):
                    return v
            for v in node.values():
                r = find(v)
                if r is not None:
                    return r
        return None

    recs = find(details)
    return None if recs is None else len(recs)


def main():
    try:
        os.remove(STATE_FILE)
    except OSError:
        pass

    existing = apps()
    if existing is None:
        die("could not list external apps")
    for a in existing:
        if _name(a) in ALL_APPS and _cid(a):
            run_cli(["admin", "external-apps", "delete", _cid(a)])

    # quiet=True: `external-apps create` returns the client secret once.
    res = run_cli(["admin", "external-apps", "create", APP_ACTIVE, "--app-scope", SEED_SCOPES],
                  quiet=True)
    if not res or res.get("Result") != "Success":
        die(f"could not create '{APP_ACTIVE}': {res}")
    logger.info("Seeded app '%s' (%s)", APP_ACTIVE, SEED_SCOPES)

    res = run_cli(["admin", "external-apps", "create", APP_RETIRED, "--app-scope", "OR.Folders"],
                  quiet=True)
    if not res or res.get("Result") != "Success":
        die(f"could not create '{APP_RETIRED}': {res}")
    logger.info("Seeded app '%s'", APP_RETIRED)

    active_cid = poll(lambda: client_id(APP_ACTIVE))
    if not active_cid:
        die(f"'{APP_ACTIVE}' not resolvable after create")
    retired_cid = poll(lambda: client_id(APP_RETIRED))
    if not retired_cid:
        die(f"'{APP_RETIRED}' not resolvable after create")

    # quiet=True: this response carries the once-only client secret value.
    res = run_cli(["admin", "external-apps", "generate-secret", active_cid,
                   "--description", STALE_SECRET, "--expiration", "2030-01-01"],
                  quiet=True)
    if not res or res.get("Result") != "Success":
        die(f"could not seed the stale secret on '{APP_ACTIVE}' — without it the "
            "delete-secret assertion would pass vacuously")
    logger.info("Seeded stale secret '%s' on '%s'", STALE_SECRET, APP_ACTIVE)

    # NOT poll(): admin_helpers.poll returns the first TRUTHY result, so a single
    # eventually-consistent read of 1 would satisfy it and skip the retry entirely —
    # then die() below on a correct environment. Retry until the count is
    # SUFFICIENT, not merely non-zero.
    count = None
    for attempt in range(4):
        count = secret_count(active_cid)
        if count is not None and count >= 2:
            break
        if attempt < 3:
            logger.info("secret count=%s (<2) — retrying in 5s", count)
            time.sleep(5)
    if count is None:
        die(f"could not read the secret collection on '{APP_ACTIVE}' — the verify "
            "cannot assert an exact post-state without a seed baseline")
    if count < 2:
        die(f"expected >=2 secrets on '{APP_ACTIVE}' after seeding (creation secret + "
            f"stale secret), found {count} after retries")

    with open(STATE_FILE, "w") as f:
        json.dump({
            "active_client_id": str(active_cid),
            "retired_client_id": str(retired_cid),
            "secret_count_at_seed": count,
        }, f)
    logger.info("Recorded seed state: active=%s retired=%s secrets=%d",
                active_cid, retired_cid, count)


main()
