#!/usr/bin/env python3
"""Verify a saved permission-catalog read came from the service and honours its scope.

  AUTHZ_PERM_FILE        file the agent saved the retrieval into (required)
  AUTHZ_EXPECT_SCOPE     scope the listing must be limited to: ORGANIZATION |
                         TENANT | PROJECT (required)
  AUTHZ_EXPECT_NAMESPACE comma-separated namespaces the rows must stay within,
                         e.g. `DOCUMENTUNDERSTANDING` for a service-filtered read
                         (optional; AUTHZ is always allowed — its permissions are
                         returned by every filter)
  AUTHZ_MIN_ROWS         minimum rows the catalog must yield (default 15)

Scope is graded by its effect on the data, not by the flag the agent typed: a
scoped read returns rows of the requested ScopeType plus the scope-agnostic `ANY`
rows the service includes in every filter. A row of any other ScopeType means the
listing was not scoped as asked.

The row floor is what makes the check un-fabricable: dozens of real
NAMESPACE.RESOURCE.ACTION names with consistent scope typing cannot be invented.

Exits 0 on success, 1 on failure.
"""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import fail, ok

logging.basicConfig(level=logging.INFO, format="verify_authz_permission_listing: %(message)s")

ALWAYS_ALLOWED_SCOPE = "ANY"
ALWAYS_ALLOWED_NAMESPACE = "AUTHZ"


def dicts(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from dicts(v)
    elif isinstance(o, list):
        for v in o:
            yield from dicts(v)


def main():
    path = (os.environ.get("AUTHZ_PERM_FILE") or "").strip()
    expect_scope = (os.environ.get("AUTHZ_EXPECT_SCOPE") or "").strip().upper()
    namespaces = {n.strip().upper() for n in (os.environ.get("AUTHZ_EXPECT_NAMESPACE") or "").split(",") if n.strip()}
    min_rows = int(os.environ.get("AUTHZ_MIN_ROWS") or 15)

    if not path or not expect_scope:
        fail("AUTHZ_PERM_FILE and AUTHZ_EXPECT_SCOPE must be set")
    if not os.path.exists(path):
        fail(f"{path} was not written — the agent saved no permission catalog")

    try:
        with open(path, encoding="utf-8-sig") as fh:
            saved = json.load(fh)
    except (json.JSONDecodeError, OSError) as e:
        fail(f"{path} is not readable JSON: {e}")

    result = saved.get("Result") if isinstance(saved, dict) else None
    if result not in (None, "Success"):
        fail(f"the saved retrieval did not succeed: Result={result}")

    rows = [x for x in dicts(saved) if x.get("Name") and x.get("ScopeType")]
    if len(rows) < min_rows:
        fail(f"only {len(rows)} permission records in {os.path.basename(path)}; "
             f"a real {expect_scope}-scoped catalog returns at least {min_rows}")

    dotted = [r for r in rows if str(r.get("Name")).count(".") >= 2]
    if not dotted:
        fail("no NAMESPACE.RESOURCE.ACTION style permission names — not a real catalog")

    off_scope = sorted({str(r.get("ScopeType")).upper() for r in rows} - {expect_scope, ALWAYS_ALLOWED_SCOPE})
    if off_scope:
        fail(f"listing is not limited to {expect_scope} — it also returned {off_scope} rows")
    if not any(str(r.get("ScopeType")).upper() == expect_scope for r in rows):
        fail(f"no {expect_scope}-scoped rows at all — the scope filter returned the wrong slice")

    if namespaces:
        allowed = namespaces | {ALWAYS_ALLOWED_NAMESPACE}
        off_ns = sorted({str(r.get("Namespace")).upper() for r in rows} - allowed)
        if off_ns:
            fail(f"listing is not limited to {sorted(namespaces)} — it also returned {off_ns} permissions")

    ok(f"{len(rows)} permissions retrieved, all {expect_scope}-scoped"
       + (f" within {sorted(namespaces)}" if namespaces else ""))


main()
