#!/usr/bin/env python3
"""Pre-run seed for aops-policy scenario tests.

  AOPS_SEED_KEY     key to record this policy under in seed.json (default "policy")
  AOPS_POLICY_BASE  base name; the run's id is appended (required)
  AOPS_PRODUCT      product to register the policy under (default E2E)
  AOPS_DESCRIPTION  seeded description (read back by the checks)
  AOPS_AVAILABILITY availability in days (default 365)
  AOPS_PLAN_ONLY    "1" records the intended name WITHOUT creating anything —
                    for scenarios where the agent itself does the create

The seeded policy is registered only; it is never deployed to a tenant, user or
group, so it cannot change which policy any subject is governed by. The form
data comes from the product's own template, so the payload is always valid for
whichever product the scenario targets.

Priority is always 1: the service validates --priority against the product's
current policy count (range 1..count+1), and that count moves as concurrent runs
create and delete policies — 1 is the only value that is always in range.
Inserting at 1 renumbers the product's other policies, so no check asserts
another policy's priority.

Always exits 0: a failed seed leaves seed.json without the entry, so the
scenario's own check fails rather than passing for free.
"""

import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from gov_helpers import aops_create, aops_form_data, run_id, scoped, update_seed

logging.basicConfig(level=logging.INFO, format="setup_aops_policy: %(message)s")
logger = logging.getLogger(__name__)


def main():
    base = (os.environ.get("AOPS_POLICY_BASE") or "").strip()
    if not base:
        logger.warning("AOPS_POLICY_BASE is not set — nothing seeded")
        return
    key = (os.environ.get("AOPS_SEED_KEY") or "policy").strip()
    product = (os.environ.get("AOPS_PRODUCT") or "E2E").strip()
    description = (os.environ.get("AOPS_DESCRIPTION") or "Seeded by the aops-policy suite").strip()
    availability = (os.environ.get("AOPS_AVAILABILITY") or "365").strip()
    plan_only = (os.environ.get("AOPS_PLAN_ONLY") or "").strip() == "1"

    name = scoped(base)
    entry = {"name": name, "product": product, "description": description,
             "availability": int(availability) if availability.isdigit() else 365}

    if plan_only:
        update_seed(**{key: entry})
        logger.info("Run %s will author '%s' itself (nothing created)", run_id(), name)
        return

    form_path = os.path.join(tempfile.gettempdir(), f"aops-form-{run_id()}-{key}.json")
    if not aops_form_data(product, form_path):
        logger.warning("Could not fetch the %s form-data template — nothing seeded", product)
        return

    created = aops_create(name=name, product=product, description=description,
                          form_data_path=form_path, availability=entry["availability"])
    try:
        os.remove(form_path)
    except OSError:
        pass
    if not created:
        logger.warning("Create failed for '%s' — nothing recorded in seed.json", name)
        return

    entry["identifier"] = created.get("Identifier")
    entry["priority"] = created.get("Priority")
    update_seed(**{key: entry})
    logger.info("Seeded %s policy '%s' (identifier=%s)", product, name, entry["identifier"])


main()
sys.exit(0)
