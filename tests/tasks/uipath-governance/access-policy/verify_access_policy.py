#!/usr/bin/env python3
"""Read tenant state back and decide whether an access-policy scenario succeeded.

  GOV_SEED_KEY      seed.json key holding the policy this check is about (required)
  GOV_CHECK         present | updated | deleted (required)
  GOV_EXPECT_DESCRIPTION  description the policy must carry after the agent's work
  GOV_EXPECT_STATUS       status the policy must carry (default Simulated)
  GOV_BYSTANDER_KEY  seed.json key of a policy the agent must NOT touch. Set on
                     destructive scenarios so an agent that over-deletes fails
                     instead of scoring full marks for removing everything.

Each mode asserts an end state only the intended operation can produce:

  present  the policy exists on the tenant under the run's name, with the
           expected status and description, and a service-assigned UUID.
  updated  a PRE-SEEDED policy's description changed, while its selectors,
           executable rule and actor rule survived. `access-policy update` is a
           full-body replace that also demands recursive camelCase, so a
           careless call either fails or silently drops those rules.
  deleted  the pre-seeded policy is soft-deleted: `get` still succeeds but
           reports Status "Deleted" with a DeletedOn stamp, and the row no
           longer appears in `list`. A do-nothing agent cannot produce that.

Exits 0 on success, 1 on failure.
"""

import logging
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from gov_helpers import ap_by_name, ap_get, fail, ok, poll, seed_entry

logging.basicConfig(level=logging.INFO, format="verify_access_policy: %(message)s")

UUID_RE = re.compile(r"[0-9a-fA-F-]{36}")


def rules_intact(policy: dict) -> str | None:
    """Return a description of what the update dropped, or None when all intact."""
    missing = []
    if not (policy.get("Selectors") or []):
        missing.append("Selectors")
    if not ((policy.get("ExecutableRule") or {}).get("Values") or []):
        missing.append("ExecutableRule.Values")
    if not ((policy.get("ActorRule") or {}).get("Values") or []):
        missing.append("ActorRule.Values")
    return ", ".join(missing) or None


def bystander_intact():
    """Fail when a destructive scenario removed a policy it was told to leave alone.

    The prompt says "leave every other policy untouched"; without this the check
    only reads the target back, so deleting the whole tenant scores full marks.
    """
    key = (os.environ.get("GOV_BYSTANDER_KEY") or "").strip()
    if not key:
        return
    entry = seed_entry(key)
    if not entry or not entry.get("id"):
        fail(f"seed.json has no '{key}' bystander entry — the pre_run seed did not complete")
    policy = ap_get(entry["id"])
    if not policy:
        fail(f"bystander policy '{entry['name']}' ({entry['id']}) could not be read back")
    status = policy.get("Status")
    if status == "Deleted":
        fail(f"bystander policy '{entry['name']}' was deleted too — the scenario said to "
             f"leave every other policy on the tenant untouched")
    logging.info("bystander '%s' still present with status %s", entry["name"], status)


def main():
    key = (os.environ.get("GOV_SEED_KEY") or "").strip()
    check = (os.environ.get("GOV_CHECK") or "").strip()
    if not key or check not in ("present", "updated", "deleted"):
        fail("GOV_SEED_KEY and GOV_CHECK (present|updated|deleted) must be set")

    entry = seed_entry(key)
    if not entry or not entry.get("name"):
        fail(f"seed.json has no '{key}' entry — the pre_run seed did not complete")
    name = entry["name"]
    expect_status = (os.environ.get("GOV_EXPECT_STATUS") or "Simulated").strip()
    expect_description = (os.environ.get("GOV_EXPECT_DESCRIPTION") or "").strip()

    if check == "present":
        policy = poll(lambda: ap_by_name(name), max_attempts=3, delay=4)
        if not policy:
            fail(f"no policy named '{name}' on the tenant — nothing was created")
        pid = str(policy.get("Id") or "")
        if not UUID_RE.fullmatch(pid):
            fail(f"policy '{name}' has no service-assigned UUID: {pid!r}")
        status = policy.get("Status")
        if status != expect_status:
            fail(f"policy '{name}' has status {status!r}, expected {expect_status!r} "
                 f"(an Active policy would enforce on the shared test organization)")
        if expect_description and (policy.get("Description") or "").strip() != expect_description:
            fail(f"policy '{name}' description is {policy.get('Description')!r}, "
                 f"expected {expect_description!r}")
        dropped = rules_intact(policy)
        if dropped:
            fail(f"policy '{name}' is missing {dropped}")
        ok(f"policy '{name}' exists ({pid}) with status {status} and its rules intact")
        return

    pid = entry.get("id")
    if not pid:
        fail(f"seed.json '{key}' entry has no id — the pre_run seed did not create the policy")
    policy = ap_get(pid)
    if not policy:
        fail(f"could not read policy {pid} back from the service")

    if check == "updated":
        seeded_description = (entry.get("description") or "").strip()
        current = (policy.get("Description") or "").strip()
        if current == seeded_description:
            fail(f"description is still the seeded {seeded_description!r} — no update landed")
        if expect_description and current != expect_description:
            fail(f"description is {current!r}, expected {expect_description!r}")
        if policy.get("Status") != expect_status:
            fail(f"status is {policy.get('Status')!r}, expected {expect_status!r} — "
                 f"the update must not change enforcement on the shared organization")
        dropped = rules_intact(policy)
        if dropped:
            fail(f"the update dropped {dropped} — `update` replaces the whole body, "
                 f"so every rule has to be resubmitted")
        ok(f"policy {pid} updated to {current!r} with status {policy.get('Status')} and rules intact")
        return

    # deleted
    status = policy.get("Status")
    if status != "Deleted":
        fail(f"policy {pid} still has status {status!r} — the delete did not land "
             f"(access-policy delete is a soft delete: Status becomes 'Deleted')")
    if not policy.get("DeletedOn"):
        fail(f"policy {pid} reports status Deleted with no DeletedOn stamp")
    if ap_by_name(entry["name"]):
        fail(f"policy '{entry['name']}' still appears in `access-policy list`")
    bystander_intact()
    ok(f"policy {pid} is soft-deleted (DeletedOn {policy.get('DeletedOn')}) and gone from `list`")


main()
