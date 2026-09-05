#!/usr/bin/env python3
"""Verify the federated-credentials maintain e2e outcome by reading the host app's
credential list back.

  1. federated-credentials update — 'ce-fedcred-main' still carries the SEEDED
                                    CREDENTIAL ID, its subject now targets
                                    refs/heads/release, and issuer + audience are
                                    byte-identical to the seeded values. Update is
                                    a FULL REPLACE (all fields required), so an
                                    agent that sends only --subject drops the
                                    other fields and fails here.
  2. federated-credentials delete — the legacy credential's SEEDED ID is absent,
                                    and exactly one credential remains. Id
                                    absence plus cardinality is what distinguishes
                                    a delete from a rename: renaming preserves the
                                    id, and a name-only check would pass.

Expected issuer/audience come from the seed state file, not from constants here.
The audience is randomized per run precisely so it cannot be a stale hardcoded
value that drifted from what was seeded.

SCOPE OF THE CLAIM: this asserts the end state, NOT that the agent read the
credential first. The agent runs with Bash/Read/Grep in a container where the
repo and this state file are both reachable, so no value in this test is
unavailable to it. The assertion is still load-bearing for the behaviour under
test — a partial-payload update wipes omitted fields regardless of what the agent
knows — but "it passed, therefore it read the credential" does not follow.
"""

import json
import logging
import os
import sys
import tempfile

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from admin_helpers import run_cli, poll, fail, ok, first_list as _first_list

logging.basicConfig(level=logging.INFO, format="verify_fedcred_maintained: %(message)s")

HOST = "ce-identity-fedcred-maintain-host"
CRED_MAIN = "ce-fedcred-main"
CRED_LEGACY = "ce-fedcred-legacy"
EXPECTED_SUBJECT = "repo:myorg/myrepo:ref:refs/heads/release"

STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_fedcred_maintain_seed.json")


def _get(item, *keys):
    for k in keys:
        v = item.get(k) or item.get(k[0].lower() + k[1:])
        if v:
            return v
    return ""


def _cid_of(item):
    return str(item.get("Id") or item.get("id") or "")


def load_seed():
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except (OSError, ValueError) as exc:
        fail(f"seed state file {STATE_FILE} missing or malformed ({exc}) — cannot verify "
             "preconditions; setup_fedcred_maintain.py did not complete")
    for key in ("client_id", "audience", "issuer", "main_credential_id",
                "legacy_credential_id", "credential_count_at_seed"):
        if not state.get(key):
            fail(f"seed state is missing '{key}' — setup did not record a complete baseline")
    return state


def main():
    seed = load_seed()
    cid = str(seed["client_id"])
    want_audience = str(seed["audience"])
    want_issuer = str(seed["issuer"])
    main_id = str(seed["main_credential_id"])
    legacy_id = str(seed["legacy_credential_id"])
    count_at_seed = int(seed["credential_count_at_seed"])

    def creds():
        data = run_cli(["admin", "external-apps", "federated-credentials", "list", cid])
        if not data or data.get("Result") != "Success":
            return None
        return _first_list(data.get("Data"))

    def retargeted():
        found = creds()
        if not found:
            return None
        # Poll on the POST-state (the new subject), not merely on the seeded id.
        # The id exists from seed time, so matching on it alone made poll return on
        # attempt 1 unconditionally and every downstream assertion — issuer,
        # audience, legacy absence, cardinality — ran against a single unretried
        # read, one eventual-consistency lag from failing a correct agent. The
        # specific "not retargeted" diagnosis is preserved below by re-reading
        # after the poll is exhausted.
        for c in found:
            if _cid_of(c) == main_id and EXPECTED_SUBJECT in _get(c, "Subject"):
                return found
        return None

    found = poll(retargeted)
    if not found:
        found = creds()
        if found is None:
            fail(f"could not list federated credentials on '{HOST}' — cannot verify")
        mine = next((c for c in found if _cid_of(c) == main_id), None)
        if mine is None:
            summary = [(_cid_of(c), _get(c, "Name")) for c in found]
            fail(f"no credential with the seeded id {main_id} on '{HOST}'; present: {summary}")
        fail(f"credential {main_id} does not target {EXPECTED_SUBJECT} "
             f"(subject={_get(mine, 'Subject')!r}) — retarget did not land")

    main_cred = next(c for c in found if _cid_of(c) == main_id)

    subject = _get(main_cred, "Subject")

    issuer = _get(main_cred, "Issuer").strip()
    if issuer != want_issuer:
        fail(f"credential {main_id} issuer changed on update (got {issuer!r}, seeded {want_issuer!r}) — "
             "federated-credentials update is a full replace; every field must be supplied")

    audience = _get(main_cred, "Audience").strip()
    if audience != want_audience:
        fail(f"credential {main_id} audience changed on update (got {audience!r}, seeded "
             f"{want_audience!r}) — federated-credentials update is a full replace; every field "
             "must be supplied")

    # Id-absence, not name-absence: a rename preserves the id, so checking that
    # nothing is named 'ce-fedcred-legacy' would accept an archive-instead-of-delete.
    ids = {_cid_of(c) for c in found}
    if legacy_id in ids:
        surviving = next((_get(c, "Name") for c in found if _cid_of(c) == legacy_id), "?")
        fail(f"the legacy credential (id={legacy_id}) still exists as '{surviving}' — it was renamed "
             "or left in place, not deleted")

    expected_after = count_at_seed - 1
    if len(found) != expected_after:
        summary = [(_cid_of(c), _get(c, "Name")) for c in found]
        fail(f"'{HOST}' carries {len(found)} credential(s); expected exactly {expected_after} "
             f"(seed baseline {count_at_seed} minus the deleted legacy one) — present: {summary}")

    ok(f"seed baseline host={cid} main={main_id} legacy={legacy_id} count={count_at_seed} "
       f"audience={want_audience} | credential {main_id} retargeted to {subject} with issuer and "
       f"audience byte-identical to seed | legacy id {legacy_id} absent | credential count "
       f"{count_at_seed}->{len(found)}")


main()
