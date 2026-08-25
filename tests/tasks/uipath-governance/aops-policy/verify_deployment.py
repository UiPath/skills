#!/usr/bin/env python3
"""Read deployment state back and decide whether a deployment scenario succeeded.

  AOPS_DEPLOY_CHECK  user_pinned | group_pinned | tenant_roundtrip (required)
  AOPS_SEED_KEY      seed.json key of the policy the agent had to deploy (required)
  AOPS_PINNED_FILE   tenant_roundtrip only — file the agent saved the pinned tenant record to

  user_pinned       the caller's user carries an E2E entry pointing at the seeded policy AND every pin
                    from the pre-run snapshot is still there (configure is a full replace — dropping
                    a pre-existing pin is the failure this guards).
  group_pinned      the marker group (auto-registered on first configure) carries the E2E entry.
  tenant_roundtrip  the tenant is back to its snapshot (pin removed again), and the saved record from
                    the pinned moment shows the E2E/E2E entry alongside every snapshot entry.

Exits 0 on success, 1 on failure.
"""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from gov_helpers import fail, load_seed, ok, poll, seed_entry, subject_policies, tenant_policies

logging.basicConfig(level=logging.INFO, format="verify_deployment: %(message)s")

PRODUCT = "E2E"
LICENSE = "E2E"


def norm(e: dict) -> tuple:
    g = lambda *ks: next((e[k] for k in ks if k in e), None)  # noqa: E731
    return (str(g("ProductIdentifier", "productIdentifier") or ""),
            str(g("LicenseTypeIdentifier", "licenseTypeIdentifier") or ""),
            str(g("PolicyIdentifier", "policyIdentifier") or "").lower())


def dicts(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from dicts(v)
    elif isinstance(o, list):
        for v in o:
            yield from dicts(v)


def main():
    check = (os.environ.get("AOPS_DEPLOY_CHECK") or "").strip()
    key = (os.environ.get("AOPS_SEED_KEY") or "").strip()
    if check not in ("user_pinned", "group_pinned", "tenant_roundtrip") or not key:
        fail("AOPS_DEPLOY_CHECK (user_pinned|group_pinned|tenant_roundtrip) and AOPS_SEED_KEY must be set")
    entry = seed_entry(key)
    if not entry or not entry.get("identifier"):
        fail(f"seed.json has no '{key}' policy with an identifier — the pre_run seed did not complete")
    pid = str(entry["identifier"]).lower()
    dep = (load_seed().get("deployment") or {})

    if check == "user_pinned":
        uid = dep.get("userId")
        if not uid or "user_snapshot" not in dep:
            fail("no user snapshot in seed.json — the pre_run snapshot did not complete")
        entries = poll(lambda: subject_policies("user", uid), max_attempts=3, delay=4) or []
        own = {norm(e)[0]: norm(e)[2] for e in entries
               if not (e.get("GroupName") or e.get("groupName"))
               and str(e.get("DeploymentLevel") or e.get("deploymentLevel") or "USER").upper() == "USER"
               and (e.get("PolicyIdentifier") or e.get("policyIdentifier"))}
        if own.get(PRODUCT) != pid:
            fail(f"user {uid} does not carry policy {pid} for product {PRODUCT} (own pins: {own})")
        lost = [p for p in dep["user_snapshot"] if own.get(p["productIdentifier"]) != str(p["policyIdentifier"]).lower()
                and p["productIdentifier"] != PRODUCT]
        if lost:
            fail(f"pre-existing user pins were dropped by the deploy (configure is a full replace): {lost}")
        ok(f"user {uid} is governed by {entry['name']} for {PRODUCT}; {len(dep['user_snapshot'])} prior pin(s) intact")
        return

    if check == "group_pinned":
        subjects = load_seed().get("subjects") or {}
        gid = subjects.get("groupId")
        if not gid:
            fail("seed.json has no marker group — the pre_run did not create it")
        entries = poll(lambda: subject_policies("group", gid), max_attempts=3, delay=4) or []
        got = {norm(e)[0]: norm(e)[2] for e in entries if e.get("PolicyIdentifier") or e.get("policyIdentifier")}
        if got.get(PRODUCT) != pid:
            fail(f"group {gid} ({subjects.get('groupName')}) does not carry policy {pid} for {PRODUCT}: {got}")
        ok(f"group {subjects.get('groupName')} is governed by {entry['name']} for {PRODUCT}")
        return

    # tenant_roundtrip
    tid = dep.get("tenantId")
    if not tid or "tenant_snapshot" not in dep:
        fail("no tenant snapshot in seed.json — the pre_run snapshot did not complete")
    snapshot = {norm(e) for e in dep["tenant_snapshot"]}
    path = (os.environ.get("AOPS_PINNED_FILE") or "pinned.json").strip()
    if not os.path.exists(path):
        fail(f"{path} was not written — the pinned tenant record was never saved")
    saved = json.load(open(path, encoding="utf-8-sig"))
    rows = {norm(x) for x in dicts(saved) if ("ProductIdentifier" in x or "productIdentifier" in x)
            and ("LicenseTypeIdentifier" in x or "licenseTypeIdentifier" in x)}
    if (PRODUCT, LICENSE, pid) not in rows:
        fail(f"{path} does not show {entry['name']} pinned for {PRODUCT}/{LICENSE}: {sorted(rows)[:6]}")
    missing = [s for s in snapshot if s not in rows and s[0] != PRODUCT]
    if missing:
        fail(f"the pin dropped pre-existing tenant assignments (configure is a full replace): {missing}")
    live = poll(lambda: tenant_policies(tid), max_attempts=3, delay=4)
    if live is None:
        fail("could not read the tenant's assignments back")
    now = {norm(e) for e in live}
    if (PRODUCT, LICENSE, pid) in now:
        fail(f"the {PRODUCT}/{LICENSE} pin is still on the tenant — it was not removed again")
    if {s for s in snapshot if s[0] != PRODUCT} - now:
        fail(f"tenant assignments differ from the snapshot after the round trip: missing {sorted({s for s in snapshot if s[0] != PRODUCT} - now)}")
    ok(f"tenant {tid}: pinned {entry['name']} for {PRODUCT}/{LICENSE} (recorded in {path}), then removed it; "
       f"{len(snapshot)} prior assignment(s) intact")


main()
