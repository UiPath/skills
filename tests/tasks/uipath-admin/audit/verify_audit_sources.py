#!/usr/bin/env python3
"""Verify the agent retrieved the real audit **sources** catalog from the tenant.

Grades the outcome, not the command string: the saved payload must contain
genuine source records AND its source-id set must match what this script reads
back from the live tenant itself. A fabricated or hand-written file cannot pass,
because the harness never trusts the agent's file as the source of truth.

Scope discipline is graded the same way, without hardcoding any assumption about
the two catalogs: when the live org and tenant catalogs genuinely differ, an
org-scope save must look like the live ORG catalog and a tenant-scope save like
the live TENANT one. If the tenant happens to expose identical catalogs at both
scopes, the discriminating assertion is skipped rather than failing on a fact
about the environment that the agent does not control.

Env:
  AUDIT_SOURCES_ORG_FILE     path the agent saved the org-scope JSON to
  AUDIT_SOURCES_TENANT_FILE  path the agent saved the tenant-scope JSON to
  AUDIT_REQUIRE_TYPE         case-insensitive event-type name the saved catalog
                             must contain (e.g. "User Login"). Proves the agent
                             retrieved a catalog deep enough to discover the type
                             GUID its investigation needs, rather than a truncated
                             or summarized copy.
At least one of the two file paths is required.

Logging: source names are catalog labels ("Identity", "Governance"), not PII, so
they are safe to print. Ids are still truncated — they are tenant identifiers.
"""

import logging
import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_shared")
)
sys.path.insert(0, _shared_root)
from audit_helpers import (  # noqa: E402  (path set above)
    SOURCE_SIGNATURE,
    env_str,
    fail,
    field,
    find_records,
    gid,
    keys_of,
    live_query,
    ok,
    unwrap,
    load_saved,
)

logging.basicConfig(level=logging.INFO, format="verify_audit_sources: %(message)s")
logger = logging.getLogger(__name__)


def source_ids(records):
    return {str(field(r, "Id")) for r in records if field(r, "Id")}


def saved_sources(path, scope):
    """Parse + shape-check one saved sources file. Returns the record list."""
    payload = unwrap(load_saved(path))
    records = find_records(payload, SOURCE_SIGNATURE)
    if records is None:
        fail(
            f"{path!r} holds no audit-sources collection (no list of records "
            f"carrying {list(SOURCE_SIGNATURE)}); top-level keys={keys_of(payload)}"
        )
    if not records:
        # The sources catalog is a static per-scope registry — it is never empty
        # on a provisioned org, so an empty save means the retrieval failed.
        fail(f"{path!r} holds an EMPTY sources collection — {scope} catalog is never empty")
    sample = records[0]
    if field(sample, "Id") is None or field(sample, "Name") is None:
        fail(f"{scope} source record missing Id/Name; keys={keys_of(sample)}")
    return records


def live_sources(scope):
    """Read the catalog back from the tenant. None when the read itself failed."""
    data = live_query(scope, "sources")
    if not data or str(field(data, "Result")).lower() != "success":
        return None
    records = find_records(unwrap(data), SOURCE_SIGNATURE)
    return records or None


def nested_names(records):
    """Every source / target / type name in the catalog, lowercased.

    Catalog labels ("Identity", "User Login") are static taxonomy, not PII, so
    they are safe to compare and report.
    """
    names = set()

    def walk(node):
        if isinstance(node, dict):
            label = field(node, "Name")
            if label:
                names.add(str(label).lower())
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(records)
    return names


def check_required_type(saved, wanted):
    """The saved catalog must expose the event type the investigation needs."""
    needle = wanted.lower()
    for scope, records in saved.items():
        if any(needle in name for name in nested_names(records)):
            logger.info("catalog exposes an event type matching %r at %s scope", wanted, scope)
            return
    fail(
        f"no event source/target/type named like {wanted!r} appears in the saved catalog — "
        "the retrieval was truncated or summarized rather than the full nested catalog "
        "needed to discover the type GUID"
    )


def main():
    targets = [
        ("org", env_str("AUDIT_SOURCES_ORG_FILE")),
        ("tenant", env_str("AUDIT_SOURCES_TENANT_FILE")),
    ]
    requested = [(scope, path) for scope, path in targets if path]
    if not requested:
        fail("internal: set AUDIT_SOURCES_ORG_FILE and/or AUDIT_SOURCES_TENANT_FILE")

    saved = {}
    live = {}
    for scope, path in requested:
        saved[scope] = saved_sources(path, scope)
        live[scope] = live_sources(scope)
        if live[scope] is None:
            # The harness could not read the catalog itself, so the agent's file
            # cannot be corroborated. Fail loudly rather than passing on the
            # agent's unverified word — a silent downgrade to "shape looks fine"
            # is exactly the weak grading this conversion removes.
            fail(
                f"harness could not read the live {scope} sources catalog to corroborate "
                f"{path!r} — check that the run's principal holds the Audit.Read scope"
            )

    for scope, path in requested:
        saved_ids = source_ids(saved[scope])
        live_ids = source_ids(live[scope])
        if not saved_ids:
            fail(f"{path!r} sources carry no Id values — cannot corroborate against the tenant")
        overlap = saved_ids & live_ids
        if not overlap:
            fail(
                f"{path!r} does not match the live {scope} catalog: none of its "
                f"{len(saved_ids)} source ids appear among the {len(live_ids)} read back "
                f"from the tenant (saved sample={gid(sorted(saved_ids)[0])}, "
                f"live sample={gid(sorted(live_ids)[0])}) — the saved data is not this tenant's"
            )
        logger.info(
            "%s: %d saved sources, %d live, %d corroborated",
            scope, len(saved_ids), len(live_ids), len(overlap),
        )

    # Scope discipline — only assertable when the tenant actually exposes
    # different catalogs at the two scopes. Self-calibrating: the expectation is
    # derived from the live tenant, never hardcoded.
    if len(requested) == 2:
        live_org, live_tenant = source_ids(live["org"]), source_ids(live["tenant"])
        if live_org != live_tenant:
            for scope, other in (("org", "tenant"), ("tenant", "org")):
                own = source_ids(saved[scope]) & source_ids(live[scope])
                foreign = source_ids(saved[scope]) & source_ids(live[other])
                if len(foreign) > len(own):
                    fail(
                        f"the {scope}-scope save matches the live {other} catalog more "
                        f"closely than the {scope} one ({len(foreign)} vs {len(own)} ids) "
                        f"— looks like the wrong scope was queried"
                    )
            logger.info("scope discipline confirmed: org and tenant catalogs are distinct")
        else:
            logger.info(
                "live org and tenant catalogs are identical on this tenant — "
                "skipping the discriminating scope assertion"
            )

    required_type = env_str("AUDIT_REQUIRE_TYPE")
    if required_type:
        check_required_type(saved, required_type)

    names = [str(field(r, "Name")) for r in saved[requested[0][0]][:4] if field(r, "Name")]
    ok(
        "audit sources corroborated against the live tenant for "
        f"{[scope for scope, _ in requested]}; sample categories={names}"
    )


main()
