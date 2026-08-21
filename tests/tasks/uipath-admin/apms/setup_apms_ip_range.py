#!/usr/bin/env python3
"""Pre-run seed for IP-restriction tests: add marker entries to the IP allowlist.

  APMS_RANGE_BASE        base name for the entry; this run's uuid8 is appended
                         (required)
  APMS_SEED_KEY          seed.json key to record the entry under (required)
  APMS_RANGE_COUNT       how many distinct networks to allocate (default 1)
  APMS_RANGE_CLAIM       how many of those networks to actually create now
                         (default: all of them; 0 = publish the plan only, for a
                         scenario where the AGENT does the creating). A re-CIDR
                         scenario uses COUNT=2 CLAIM=1: one network seeded, the
                         other published as the target to move to.

CONCURRENCY: the service keys allowlist entries by CIDR, not by name — creating an
entry for a network that is already allowed RENAMES the existing entry instead of
adding a row. Two agents running this task at once would therefore fight over one
row if they used a fixed CIDR. So the CIDR is not fixed: this seed allocates the
first free block out of the documentation ranges (RFC 5737 TEST-NET-1/2/3, split
into /28s = 48 slots), re-reads the allowlist to confirm it owns what it created,
and retries on the next block if a peer won the race.

Both the entry name and the allocated networks are recorded in seed.json, which
the agent's prompt and the verify script read — so nothing about this run's
objects is guessable from another run.

Safe by construction: an allowlist entry has no effect while enforcement is
Disabled, and these tests never enable it.

Always exits 0.
"""

import ipaddress
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli, run_id, scoped, update_seed

logging.basicConfig(level=logging.INFO, format="setup_apms_ip_range: %(message)s")
logger = logging.getLogger(__name__)

# RFC 5737 documentation ranges — never routable, safe to allowlist.
POOL = ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")
BLOCK = 30  # 64 blocks per /24 -> 192 slots across the three ranges


def allowlist() -> list[dict] | None:
    data = run_cli(["admin", "ip-restriction", "ip-ranges", "list"])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data") or []


def candidate_blocks() -> list[str]:
    out = []
    for net in POOL:
        out.extend(str(sub) for sub in ipaddress.ip_network(net).subnets(new_prefix=BLOCK))
    return out


def claim(name: str, wanted: int) -> list[str]:
    """Create `wanted` entries under `name`, each on a block nobody else holds."""
    claimed: list[str] = []
    for cidr in candidate_blocks():
        if len(claimed) == wanted:
            break
        rows = allowlist()
        if rows is None:
            logger.warning("Could not read the allowlist — aborting allocation")
            return claimed
        if any((r.get("IpNetwork") or "") == cidr for r in rows):
            continue  # already allowed (peer run or real entry) — try the next block

        res = run_cli(["admin", "ip-restriction", "ip-ranges", "create", "--name", name, "--cidr", cidr])
        if not res or res.get("Result") != "Success":
            logger.info("Create rejected for %s — trying the next block", cidr)
            continue

        # Confirm we own it: a peer that claimed the same block first would have
        # renamed the row out from under us.
        rows = allowlist() or []
        mine = next((r for r in rows if (r.get("IpNetwork") or "") == cidr
                     and (r.get("Name") or "") == name), None)
        if mine:
            claimed.append(cidr)
            logger.info("Claimed %s for '%s' (id=%s)", cidr, name, mine.get("Id"))
        else:
            logger.info("Lost the race for %s — trying the next block", cidr)
    return claimed


def planned_blocks(token: str, wanted: int) -> list[str]:
    """Blocks derived from the run id, for scenarios where the AGENT creates the
    entry (nothing can be reserved in advance without creating it). 192 slots make
    a clash between concurrent runs unlikely; if one happens, the peer's create
    renames this run's row and the check fails loudly rather than passing wrongly."""
    blocks = candidate_blocks()
    start = int(token, 16) % len(blocks)
    return [blocks[(start + i) % len(blocks)] for i in range(wanted)]


def main():
    base = (os.environ.get("APMS_RANGE_BASE") or "").strip()
    seed_key = (os.environ.get("APMS_SEED_KEY") or "").strip()
    count = int(os.environ.get("APMS_RANGE_COUNT") or 1)
    if not base or not seed_key:
        logger.warning("APMS_RANGE_BASE and APMS_SEED_KEY are required — skipping seed")
        return

    name = scoped(base)

    raw_claim = (os.environ.get("APMS_RANGE_CLAIM") or "").strip()
    to_claim = count if raw_claim == "" else int(raw_claim)

    if to_claim == 0:
        # Nothing to reserve: the agent creates the entry, so publish the name and
        # the networks it should use. Blocks are derived from the run id, keeping
        # concurrent runs on different networks without pre-creating anything.
        cidrs = planned_blocks(run_id(), count)
        update_seed(**{seed_key: {"name": name, "cidrs": cidrs, "ids": []}})
        logger.info("Planned entry '%s' on %s for the agent to add", name, cidrs)
        return

    claimed = claim(name, to_claim)
    if not claimed:
        logger.warning("Could not claim any block for '%s' — the pool may be saturated", name)
        return

    # Extra networks the scenario needs but must NOT exist yet (a re-CIDR target).
    planned = [c for c in planned_blocks(run_id(), count + len(claimed))
               if c not in claimed][:count - len(claimed)]

    rows = allowlist() or []
    ids = [r.get("Id") for r in rows if (r.get("Name") or "") == name]
    update_seed(**{seed_key: {"name": name, "cidrs": claimed + planned, "ids": ids}})
    logger.info("Seeded allowlist entry '%s' on %s (target networks: %s)", name, claimed, planned or "-")


main()
sys.exit(0)
