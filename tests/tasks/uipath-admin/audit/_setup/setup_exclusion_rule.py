#!/usr/bin/env python3
"""Pre-run seed for the audit-exclusion tests.

Two modes, both driven entirely by environment variables so every exclusion test
shares this one script:

  plan-only (EXCL_PLAN_ONLY=1)
      Create nothing. Resolve a real event type from the live catalog and publish
      the run-scoped rule name plus that type into `seed.json`, so a create
      scenario grades the agent's own `exclusions create`.

  seeded
      Create one active rule carrying an EventType selector and a Status
      selector, and record its id and selectors in `seed.json`, so a rename or
      delete scenario has something real to act on.

  snapshot (EXCL_SNAPSHOT=1)
      Create nothing and seed nothing. Record the ids of the rules that already
      exist into `seed.json`, and mint this run's uuid8. A refusal scenario uses
      it so the post_run sweep can tell a rule the agent created from one that
      was already configured. `EXCL_SEED_KEY` / `EXCL_RULE_BASE` are not needed.

Env:
  EXCL_SEED_KEY      seed.json key to record under, e.g. `rule` (required)
  EXCL_RULE_BASE     base rule name; this run's uuid8 is appended so concurrent
                     runs never collide (required)
  EXCL_SNAPSHOT      `1` for the snapshot mode above (optional)
  EXCL_PLAN_ONLY     `1` for the plan-only mode above (optional)
  EXCL_STATUS        Status selector value; default `Success` (optional)
  EXCL_RENAME_BASE   when set, also publish `rename_to` — a second run-scoped
                     name a replacement scenario must rename the rule to
  EXCL_INACTIVE      `1` — create the rule with --inactive (optional)

Selector discovery: event-type ids are read from `uip admin audit org sources`,
never hardcoded, because the catalog differs per organization. Candidates are
tried in a deterministic order and the first one the service accepts is the one
recorded — a protected type answers `SelectorValueNotPermitted` and an already
covered one answers `OverlappingRuleExists`, and neither is a seed failure.

Sources, targets, and types whose names look like audit configuration or
platform monitoring are skipped up front: those are exactly the values the
service refuses, so trying them first would waste the seed's attempts.

Names carry this run's uuid8, so a same-named leftover cannot exist and a peer
run's in-flight rule is never touched.

Always exits 0 — a seed failure surfaces as a failing criterion, not a harness
error.
"""

import logging
import os
import sys

from admin_helpers import run_cli, scoped, update_seed

logging.basicConfig(level=logging.INFO, format="setup_exclusion_rule: %(message)s")
logger = logging.getLogger(__name__)

# Substrings that mark a catalog entry the service will not let a rule exclude.
PROTECTED_HINTS = ("audit", "monitor", "health", "telemetry", "diagnostic")
# How many candidate event types to try before giving up.
MAX_CANDIDATES = 6


def field(record, *names):
    """Case-insensitive lookup — the CLI host PascalCases keys under `Data`."""
    if not isinstance(record, dict):
        return None
    normalized = {str(k).lower(): v for k, v in record.items()}
    for name in names:
        if name.lower() in normalized:
            return normalized[name.lower()]
    return None


def looks_protected(*labels):
    joined = " ".join(str(label or "").lower() for label in labels)
    return any(hint in joined for hint in PROTECTED_HINTS)


def candidate_types():
    """Deterministically ordered (type_id, type_name) pairs from the live catalog."""
    data = run_cli(["admin", "audit", "org", "sources"], timeout=60)
    if not data or field(data, "Result") != "Success":
        logger.warning("Could not read 'audit org sources' — no selector ids to seed with")
        return []

    payload = field(data, "Data") or []
    out = []
    for source in payload if isinstance(payload, list) else []:
        source_name = field(source, "Name")
        if looks_protected(source_name):
            continue
        for target in field(source, "EventTargets") or []:
            target_name = field(target, "Name")
            if looks_protected(target_name):
                continue
            for event_type in field(target, "EventTypes") or []:
                type_id = field(event_type, "Id")
                type_name = field(event_type, "Name")
                if not type_id or not type_name or looks_protected(type_name):
                    continue
                out.append((str(type_id), str(type_name), str(source_name or ""), str(target_name or "")))
    # Sorted by name so two runs of the same task pick the same type.
    return sorted(out, key=lambda row: (row[1], row[0]))


def snapshot_existing():
    """Record the ids of the rules already configured, and mint this run's uuid8."""
    data = run_cli(["admin", "audit", "org", "exclusions", "list"], timeout=60)
    if not data or field(data, "Result") != "Success":
        logger.warning("Could not list exclusion rules — no snapshot recorded")
        return
    rules = field(data, "Data") or []
    ids = [
        str(field(rule, "PolicyId"))
        for rule in (rules if isinstance(rules, list) else [])
        if field(rule, "PolicyId")
    ]
    update_seed(excl_snapshot=ids)
    logger.info("Snapshotted %d pre-existing exclusion rule(s)", len(ids))


def main():
    if (os.environ.get("EXCL_SNAPSHOT") or "").strip().lower() in ("1", "true", "yes"):
        snapshot_existing()
        return

    seed_key = (os.environ.get("EXCL_SEED_KEY") or "").strip()
    base = (os.environ.get("EXCL_RULE_BASE") or "").strip()
    if not seed_key or not base:
        logger.warning("EXCL_SEED_KEY and EXCL_RULE_BASE are required — skipping seed")
        return

    status = (os.environ.get("EXCL_STATUS") or "Success").strip()
    plan_only = (os.environ.get("EXCL_PLAN_ONLY") or "").strip().lower() in ("1", "true", "yes")
    inactive = (os.environ.get("EXCL_INACTIVE") or "").strip().lower() in ("1", "true", "yes")
    rename_base = (os.environ.get("EXCL_RENAME_BASE") or "").strip()

    name = scoped(base)
    entry = {"name": name, "status": status}
    if rename_base:
        entry["rename_to"] = scoped(rename_base)

    candidates = candidate_types()
    if not candidates:
        logger.warning("No usable event type in the catalog — recording the name only")
        update_seed(**{seed_key: entry})
        return

    if plan_only:
        type_id, type_name, source_name, target_name = candidates[0]
        entry.update({
            "type_id": type_id,
            "type_name": type_name,
            "source_name": source_name,
            "target_name": target_name,
            # The selectors the scenario PLANNED. A create check compares the
            # agent's rule against these, so resolving the event-type name to a
            # different id — or inventing one — fails.
            "selectors": {"EventType": [type_id], "Status": [status]},
        })
        update_seed(**{seed_key: entry})
        logger.info("Planned rule '%s' on event type '%s' for the agent to create", name, type_name)
        return

    for type_id, type_name, source_name, target_name in candidates[:MAX_CANDIDATES]:
        args = ["admin", "audit", "org", "exclusions", "create",
                "--name", name, "--type", type_id, "--status", status]
        if inactive:
            args.append("--inactive")
        res = run_cli(args, timeout=60)
        policy_id = field(field(res, "Data") or {}, "PolicyId")
        if policy_id:
            entry.update({
                "id": str(policy_id),
                "type_id": type_id,
                "type_name": type_name,
                "source_name": source_name,
                "target_name": target_name,
                "selectors": {"EventType": [type_id], "Status": [status]},
            })
            update_seed(**{seed_key: entry})
            logger.info("Seeded rule '%s' (id=%s) excluding %s '%s' events",
                        name, policy_id, status, type_name)
            return
        code = field(field(res, "Context") or {}, "errorCode") if res else None
        logger.info("Event type '%s' rejected (%s) — trying the next candidate",
                    type_name, code or "no code")

    logger.warning("No candidate event type was accepted — recording the name only")
    update_seed(**{seed_key: entry})


main()
sys.exit(0)
