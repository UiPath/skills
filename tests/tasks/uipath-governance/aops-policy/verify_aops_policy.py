#!/usr/bin/env python3
"""Read service state back and decide whether an aops-policy scenario succeeded.

  AOPS_SEED_KEY     seed.json key holding the policy this check is about (required)
  AOPS_CHECK        present | updated | absent (required)
  AOPS_EXPECT_DESCRIPTION  description the policy must carry afterwards
  AOPS_EXPECT_AVAILABILITY availability (days) the policy must carry afterwards
  AOPS_BYSTANDER_KEY  seed.json key of a policy the agent must NOT touch. Set on
                      destructive scenarios so an agent that over-deletes fails
                      instead of scoring full marks for removing everything.

Each mode asserts an end state only the intended operation can produce:

  present  a policy with the run's name exists under the expected product, with a
           service-assigned identifier and a non-empty form-data payload.
  updated  a PRE-SEEDED policy's description changed while its availability and
           form data survived. `aops-policy update` is a full replace — omitting
           --availability or --input clears those fields — so a careless call
           shows up here.
  absent   the pre-seeded identifier is gone: `get` returns a 404 (aops deletes
           for real, unlike access-policy's soft delete) and a name search
           returns nothing. A do-nothing agent cannot make a seeded id vanish.

Exits 0 on success, 1 on failure.
"""

import logging
import os
import re
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-governance", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from gov_helpers import aops_get, aops_search, fail, ok, poll, seed_entry

logging.basicConfig(level=logging.INFO, format="verify_aops_policy: %(message)s")

UUID_RE = re.compile(r"[0-9a-fA-F-]{36}")


def payload_of(policy: dict) -> dict:
    """The policy's form-data payload, however deeply the envelope nests it."""
    node = policy.get("Data")
    while isinstance(node, dict) and isinstance(node.get("Data"), dict):
        node = node["Data"]
    return node if isinstance(node, dict) else {}


def bystander_intact():
    """Fail when a destructive scenario removed a policy it was told to leave alone.

    The prompt says "leave every other policy untouched"; without this the check
    only reads the target back, so wiping the product registry scores full marks.
    """
    key = (os.environ.get("AOPS_BYSTANDER_KEY") or "").strip()
    if not key:
        return
    entry = seed_entry(key)
    if not entry or not entry.get("identifier"):
        fail(f"seed.json has no '{key}' bystander entry — the pre_run seed did not complete")
    if not aops_get(entry["identifier"]):
        fail(f"bystander policy '{entry['name']}' ({entry['identifier']}) is gone too — the "
             f"scenario said to leave every other policy on the organization untouched")
    logging.info("bystander '%s' still present", entry["name"])


def main():
    key = (os.environ.get("AOPS_SEED_KEY") or "").strip()
    check = (os.environ.get("AOPS_CHECK") or "").strip()
    if not key or check not in ("present", "updated", "absent"):
        fail("AOPS_SEED_KEY and AOPS_CHECK (present|updated|absent) must be set")

    entry = seed_entry(key)
    if not entry or not entry.get("name"):
        fail(f"seed.json has no '{key}' entry — the pre_run seed did not complete")
    name = entry["name"]
    product = entry.get("product") or "E2E"
    expect_description = (os.environ.get("AOPS_EXPECT_DESCRIPTION") or "").strip()

    if check == "present":
        rows = poll(lambda: [r for r in aops_search(name) if (r.get("Name") or "") == name],
                    max_attempts=3, delay=4)
        if not rows:
            fail(f"no aops policy named '{name}' — nothing was created")
        row = rows[0]
        ident = str(row.get("Identifier") or "")
        if not UUID_RE.fullmatch(ident):
            fail(f"policy '{name}' has no service-assigned identifier: {ident!r}")
        got_product = ((row.get("Product") or {}).get("Name")) or ""
        if got_product != product:
            fail(f"policy '{name}' is registered under product {got_product!r}, expected {product!r}")
        if expect_description and (row.get("Description") or "").strip() != expect_description:
            fail(f"policy '{name}' description is {row.get('Description')!r}, expected {expect_description!r}")
        full = aops_get(ident)
        if not full or not payload_of(full):
            fail(f"policy '{name}' has no form-data payload — it was created without --input")
        expect_availability = (os.environ.get("AOPS_EXPECT_AVAILABILITY") or "").strip()
        if expect_availability:
            got = full.get("Availability")
            if str(got) != expect_availability:
                fail(f"policy '{name}' has availability {got!r}, expected {expect_availability} "
                     f"— the scenario asked for that availability window explicitly")
        ok(f"policy '{name}' exists ({ident}) under {got_product} with a form-data payload")
        return

    ident = entry.get("identifier")
    if not ident:
        fail(f"seed.json '{key}' entry has no identifier — the pre_run seed did not create the policy")

    if check == "updated":
        policy = aops_get(ident)
        if not policy:
            fail(f"policy {ident} no longer exists — the scenario asked for an update, not a delete")
        current = (policy.get("Description") or "").strip()
        if current == (entry.get("description") or "").strip():
            fail(f"description is still the seeded {current!r} — no update landed")
        if expect_description and current != expect_description:
            fail(f"description is {current!r}, expected {expect_description!r}")
        if entry.get("availability") and policy.get("Availability") != entry["availability"]:
            fail(f"availability changed from {entry['availability']} to {policy.get('Availability')} — "
                 f"`update` is a full replace, so --availability has to be resubmitted")
        if not payload_of(policy):
            fail("the update cleared the form-data payload — `update` is a full replace, "
                 "so --input has to be resubmitted")
        ok(f"policy {ident} updated to {current!r} with availability and form data intact")
        return

    # absent
    if aops_get(ident):
        fail(f"policy {ident} still exists — the delete did not land")
    if [r for r in aops_search(name) if (r.get("Name") or "") == name]:
        fail(f"a policy named '{name}' still shows up in `aops-policy list --search`")
    bystander_intact()
    ok(f"policy {ident} is gone: `get` reports it missing and the name search returns nothing")


main()
