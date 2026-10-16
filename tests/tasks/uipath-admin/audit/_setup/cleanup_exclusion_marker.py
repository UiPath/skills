#!/usr/bin/env python3
"""Best-effort cleanup for the audit-exclusion tests: remove this run's rules.

An exclusion rule is organization-wide and suppresses events for as long as it
exists, so a rule left behind by a failed run keeps muting the audit trail for
every later run. Both modes below therefore run as pre_run as well as post_run.

  marker mode — EXCL_CLEANUP_MARKER=<substring>
      Delete rules whose name carries BOTH the marker and this run's uuid8 (from
      seed.json). This is how a seeded scenario removes what it created.

  snapshot mode — EXCL_CLEANUP_UNSNAPSHOTTED=1
      Delete rules that did not exist when `setup_exclusion_rule.py
      EXCL_SNAPSHOT=1` ran, EXCEPT any whose name carries the reserved test
      prefix. A refusal scenario uses this: the rule an agent must not have
      created carries a name the agent chose, which no marker can match.

CONCURRENCY: several agents run these tasks against one organization at the same
time, so cleanup must never touch a peer run's rule — or, far worse, a rule an
administrator configured. Marker mode is pinned to this run's uuid8. Snapshot
mode deletes only rules that appeared during this run AND do not carry the
reserved prefix, so a peer's seeded rule (which always carries it) is protected
while an agent-named rule is not. There is deliberately no exact-name escape
hatch and no unguarded "delete everything new" path.

Always exits 0 — cleanup failures never affect pass/fail.
"""

import logging
import os
import sys

from admin_helpers import load_seed, owned_by_this_run, run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_exclusion_marker: %(message)s")
logger = logging.getLogger(__name__)

# Every rule these tests seed is named from a `ce-audit-excl*` base. Snapshot
# mode leaves those alone: one of them appearing mid-run belongs to a peer run.
RESERVED_PREFIX = "ce-audit-excl"


def field(record, *names):
    """Case-insensitive lookup — the CLI host PascalCases keys under `Data`."""
    if not isinstance(record, dict):
        return None
    normalized = {str(k).lower(): v for k, v in record.items()}
    for name in names:
        if name.lower() in normalized:
            return normalized[name.lower()]
    return None


def list_rules():
    data = run_cli(["admin", "audit", "org", "exclusions", "list"], timeout=60)
    if not data or field(data, "Result") != "Success":
        logger.warning("Could not list exclusion rules — skipping cleanup")
        return None
    rules = field(data, "Data") or []
    if not isinstance(rules, list):
        logger.warning("Unexpected rule listing shape — skipping cleanup")
        return None
    return rules


def delete(name, policy_id, why):
    logger.info("Deleting exclusion rule '%s' (id=%s) — %s", name, policy_id, why)
    res = run_cli(["admin", "audit", "org", "exclusions", "delete", str(policy_id)], timeout=60)
    if not res or field(res, "Result") != "Success":
        logger.warning("Delete did not report success for id=%s", policy_id)


def clean_by_marker(marker, rules):
    for rule in rules:
        name = str(field(rule, "Name") or "")
        policy_id = field(rule, "PolicyId")
        if policy_id and marker in name and owned_by_this_run(name):
            delete(name, policy_id, "seeded by this run")


def clean_unsnapshotted(rules):
    seed = load_seed()
    snapshot = seed.get("excl_snapshot")
    if snapshot is None:
        logger.warning(
            "No excl_snapshot in seed.json (pre_run snapshot never ran) — "
            "skipping snapshot cleanup rather than guessing which rules are new"
        )
        return
    known = {str(i).strip().lower() for i in snapshot}
    for rule in rules:
        name = str(field(rule, "Name") or "")
        policy_id = field(rule, "PolicyId")
        if not policy_id or str(policy_id).strip().lower() in known:
            continue
        if RESERVED_PREFIX in name.lower():
            logger.info("Leaving '%s' alone — reserved test prefix, likely a peer run's rule", name)
            continue
        delete(name, policy_id, "created during this run and not in the pre-run snapshot")


def main():
    marker = (os.environ.get("EXCL_CLEANUP_MARKER") or "").strip()
    unsnapshotted = (os.environ.get("EXCL_CLEANUP_UNSNAPSHOTTED") or "").strip().lower() in ("1", "true", "yes")
    if not marker and not unsnapshotted:
        logger.warning("Neither EXCL_CLEANUP_MARKER nor EXCL_CLEANUP_UNSNAPSHOTTED set — nothing to do")
        return

    rules = list_rules()
    if rules is None:
        return

    if marker:
        clean_by_marker(marker, rules)
    if unsnapshotted:
        clean_unsnapshotted(rules)


main()
sys.exit(0)
