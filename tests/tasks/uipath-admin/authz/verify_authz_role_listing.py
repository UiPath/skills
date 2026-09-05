#!/usr/bin/env python3
"""Verify a saved role listing came from the service and honours its filter.

  AUTHZ_ROLE_FILE       file the agent saved the retrieval into (required)
  AUTHZ_EXPECT_TYPE     role type every row must carry: BuiltIn | Custom
                        (optional — omit when the listing is unfiltered)
  AUTHZ_EXPECT_CONTAINS substring every row's Name must contain, for a
                        name-filtered listing (optional)
  AUTHZ_REQUIRE_SEED_KEY  seed.json key of a role this run seeded that must appear
                          in the listing — run-scoped, so a concurrent run's
                          identically-based role cannot satisfy it (optional)
  AUTHZ_REQUIRE_NAME      exact role name that must appear (optional; prefer the
                          seed key for anything this run created)
  AUTHZ_MIN_ROWS        minimum rows the listing must yield (default 1)

Filters are graded by their effect on the data rather than by the flags typed: a
`--role-type BuiltIn` read must not return Custom rows, and a name-filtered read
must not return rows outside the filter. Each row must also carry the
service-assigned Id and ScopeType, which an agent cannot invent for real roles.

Exits 0 on success, 1 on failure.
"""

import json
import logging
import os
import re
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from admin_helpers import fail, ok, seed_entry

logging.basicConfig(level=logging.INFO, format="verify_authz_role_listing: %(message)s")

UUID = re.compile(r"[0-9a-fA-F-]{36}")


def dicts(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from dicts(v)
    elif isinstance(o, list):
        for v in o:
            yield from dicts(v)


def main():
    path = (os.environ.get("AUTHZ_ROLE_FILE") or "").strip()
    expect_type = (os.environ.get("AUTHZ_EXPECT_TYPE") or "").strip()
    contains = (os.environ.get("AUTHZ_EXPECT_CONTAINS") or "").strip()
    require_name = (os.environ.get("AUTHZ_REQUIRE_NAME") or "").strip()
    require_key = (os.environ.get("AUTHZ_REQUIRE_SEED_KEY") or "").strip()
    if require_key:
        entry = seed_entry(require_key)
        if not entry:
            fail(f"seed.json has no '{require_key}' entry — the role was never seeded for this run")
        require_name = entry["name"]
    min_rows = int(os.environ.get("AUTHZ_MIN_ROWS") or 1)

    if not path:
        fail("AUTHZ_ROLE_FILE must be set")
    if not os.path.exists(path):
        fail(f"{path} was not written — the agent saved no role listing")

    try:
        with open(path, encoding="utf-8-sig") as fh:
            saved = json.load(fh)
    except (json.JSONDecodeError, OSError) as e:
        fail(f"{path} is not readable JSON: {e}")

    result = saved.get("Result") if isinstance(saved, dict) else None
    if result not in (None, "Success"):
        fail(f"the saved retrieval did not succeed: Result={result}")

    # Role rows carry Type / OwnerServiceName; the ActionDetails entries nested
    # inside each role also carry Name + Id + ScopeType, so they are excluded by
    # their permission-only fields.
    rows = [
        x for x in dicts(saved)
        if x.get("Name") and x.get("Id") and x.get("ScopeType")
        and ("Type" in x or "OwnerServiceName" in x)
        and "ResourceAction" not in x
    ]
    if len(rows) < min_rows:
        fail(f"only {len(rows)} role records in {os.path.basename(path)}, expected at least {min_rows}")
    if not all(UUID.fullmatch(str(r.get("Id"))) for r in rows):
        fail("some rows carry no service-assigned role UUID — not a real role listing")

    if expect_type:
        # The service reports built-ins as "BUILTIN" and custom roles as "Custom",
        # so the comparison is case-insensitive.
        off_type = sorted({str(r.get("Type")) for r in rows if str(r.get("Type")).lower() != expect_type.lower()})
        if off_type:
            fail(f"listing is not limited to {expect_type} roles — it also returned {off_type}")

    if contains:
        stray = sorted({str(r.get("Name")) for r in rows if contains.lower() not in str(r.get("Name")).lower()})
        if stray:
            fail(f"listing is not limited to names containing {contains!r} — it also returned {stray[:5]}")

    if require_name and not any(str(r.get("Name")) == require_name for r in rows):
        fail(f"'{require_name}' is missing from the listing — it was not read back from the service; "
             f"names found: {sorted({str(r.get('Name')) for r in rows})[:8]}")

    ok(f"{len(rows)} role records retrieved"
       + (f", all {expect_type}" if expect_type else "")
       + (f", all matching {contains!r}" if contains else "")
       + (f", including '{require_name}'" if require_name else ""))


main()
