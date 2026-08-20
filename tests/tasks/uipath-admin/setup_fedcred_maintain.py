#!/usr/bin/env python3
"""Pre-run seed for the federated-credentials maintain e2e: ensure a PERSISTENT
host external app exists and start the run with exactly two known credentials on
it.

  ce-fedcred-main    -> agent retargets its subject from the main branch to the
                        release branch, preserving issuer and audience.
  ce-fedcred-legacy  -> agent deletes it.

Why a persistent host (same rationale as setup_fedcred_host.py): identity-service
has a create->read cross-partition inconsistency (PLT-107839 investigation) — a
freshly-created app is not yet materialized in the org partition the
federated-credentials endpoint queries, so `federated-credentials create` 400s
with "Client not found in partition" on brand-new apps. This test therefore owns
its own durable host, created once and never deleted, and churns only the
credentials on it. A dedicated host (not the smoke's 'ce-identity-fedcred-host')
keeps the two tests from fighting over the same credential list under -jN.

The host is created with --no-secret. Creating it confidential (the default) mints
a client secret that is never recorded and never revoked, leaving a permanent
orphaned OAuth credential with OR.Folders,OR.Jobs on a shared staging org.

The audience is randomized per run and written to the state file, never
hardcoded. A fixed value could be copied out of this file — the agent runs with
Bash/Read/Grep in a container where $SKILLS_REPO_PATH is mounted — so a fixed
value proves nothing about provenance. Randomizing does not fix that either (the
state file lives in the same container), and this test does NOT claim to prove
the credential was read. What it does assert is the product-relevant outcome: a
partial-payload update wipes omitted fields, so an agent that supplies all three
fields made a correct full-replace call.

EXITS NON-ZERO if any required fixture could not be seeded — the legacy
credential especially, since without it the "legacy was deleted" assertion passes
vacuously. Note the create below is known-flaky on a cold host.
"""

import json
import logging
import os
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll, first_list as _first_list

logging.basicConfig(level=logging.INFO, format="setup_fedcred_maintain: %(message)s")
logger = logging.getLogger(__name__)

HOST = "ce-identity-fedcred-maintain-host"
ISSUER = "https://token.actions.githubusercontent.com"
CRED_MAIN = "ce-fedcred-main"
CRED_LEGACY = "ce-fedcred-legacy"
SUBJECT_MAIN = "repo:myorg/myrepo:ref:refs/heads/main"
SUBJECT_LEGACY = "repo:myorg/legacy-repo:ref:refs/heads/main"

STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_fedcred_maintain_seed.json")


def die(message):
    logger.error("SEED FAILED: %s", message)
    sys.exit(1)


def find_host():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        return None
    for a in data.get("Data", []):
        if (a.get("Name") or a.get("name") or "") == HOST:
            return a.get("ClientId") or a.get("clientId") or a.get("Id") or a.get("id")
    return None


def creds(cid):
    data = run_cli(["admin", "external-apps", "federated-credentials", "list", cid])
    if not data or data.get("Result") != "Success":
        return None
    return _first_list(data.get("Data"))


def clear_creds(cid):
    existing = creds(cid)
    if existing is None:
        die(f"could not list federated credentials on '{HOST}' — refusing to seed onto unknown state")
    for c in existing:
        crid = c.get("Id") or c.get("id")
        if crid:
            run_cli(["admin", "external-apps", "federated-credentials", "delete", cid, crid])


def seed_cred(cid, name, subject, audience):
    def create():
        res = run_cli([
            "admin", "external-apps", "federated-credentials", "create", cid,
            "--name", name,
            "--issuer", ISSUER,
            "--audience", audience,
            "--subject", subject,
        ])
        return res if (res and res.get("Result") == "Success") else None

    # Retry: a host materializing for the first time can 400 here.
    if not poll(create):
        die(f"could not seed credential '{name}' after retries — without it the "
            "corresponding assertion would pass vacuously")
    logger.info("Seeded credential '%s' (%s)", name, subject)


def main():
    try:
        os.remove(STATE_FILE)
    except OSError:
        pass

    cid = find_host()
    if not cid:
        # Create the durable host once. --no-secret: see module docstring.
        res = run_cli(["admin", "external-apps", "create", HOST,
                       "--app-scope", "OR.Folders,OR.Jobs", "--no-secret"])
        if not res or res.get("Result") != "Success":
            die(f"could not create the durable host '{HOST}': {res}")
        logger.info("Created persistent fed-cred host '%s' (--no-secret)", HOST)
        cid = poll(find_host)

    if not cid:
        die(f"host app '{HOST}' not resolvable in list — cannot seed credentials")

    audience = f"api://ce-fedcred-maintain-{uuid.uuid4().hex[:12]}"

    clear_creds(cid)
    seed_cred(cid, CRED_MAIN, SUBJECT_MAIN, audience)
    seed_cred(cid, CRED_LEGACY, SUBJECT_LEGACY, audience)

    seeded = creds(cid)
    if seeded is None:
        die("could not read the credential list back after seeding")
    by_name = {}
    for c in seeded:
        nm = c.get("Name") or c.get("name") or ""
        cr = c.get("Id") or c.get("id")
        if nm and cr:
            by_name[nm] = str(cr)
    for required in (CRED_MAIN, CRED_LEGACY):
        if required not in by_name:
            die(f"credential '{required}' not present after seeding (read back: {sorted(by_name)})")
    if len(seeded) != 2:
        die(f"expected exactly 2 credentials on '{HOST}' after seeding, found {len(seeded)}")

    with open(STATE_FILE, "w") as f:
        json.dump({
            "client_id": str(cid),
            "audience": audience,
            "issuer": ISSUER,
            "main_credential_id": by_name[CRED_MAIN],
            "legacy_credential_id": by_name[CRED_LEGACY],
            "credential_count_at_seed": len(seeded),
        }, f)
    logger.info("Host '%s' ready (clientId=%s) with 2 credentials; audience recorded to state", HOST, cid)


main()
