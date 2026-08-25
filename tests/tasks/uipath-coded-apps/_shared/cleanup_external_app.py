#!/usr/bin/env python3
"""post_run: delete the OAuth external application recorded in report.json.

Dashboard build/deploy tests that run against a live tenant mint a fresh
External Application per run via `uip admin external-apps create` (see the
skill's dashboards/plugins/build/impl.md). The created app's `ClientId` is
the OAuth client the dashboard authenticates with; left behind, it
accumulates one orphan external app per run on the tenant.

The create step must record that ClientId into report.json (or the
`.external_app_to_cleanup` marker) for this script to find it. This script
deletes it via `uip admin external-apps delete <clientId>` — the CLI path
that `@uipath/admin-tool` provides (preseeded in tests/docker/Dockerfile).

Read priority for the client ID:
  1. report.json `external_app_client_id` key
  2. report.json `clientId` key (as written into intent.json)
  3. `.external_app_to_cleanup` marker file

Exits 0 always — cleanup failures never fail the test.
"""
import json
import os
import re
import subprocess
import sys

# A UUID is the only shape a UiPath external-app Client ID takes. Refusing to
# delete anything that isn't a bare UUID guards against a malformed report.json
# feeding an unexpected value straight into `external-apps delete`.
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def load_client_id() -> str:
    if os.path.exists("report.json"):
        try:
            r = json.load(open("report.json"))
            cid = (r.get("external_app_client_id") or r.get("clientId") or "").strip()
            if cid:
                return cid
        except Exception:
            pass
    if os.path.exists(".external_app_to_cleanup"):
        try:
            return open(".external_app_to_cleanup").read().strip()
        except Exception:
            pass
    return ""


client_id = load_client_id()
if not client_id:
    sys.exit(0)

if not UUID_RE.match(client_id):
    print(
        f"SKIP: client id '{client_id}' is not a UUID — refusing to delete",
        file=sys.stderr,
    )
    sys.exit(0)

try:
    subprocess.run(
        ["uip", "admin", "external-apps", "delete", client_id, "--output", "json"],
        capture_output=True, timeout=60,
    )
except subprocess.TimeoutExpired:
    print(f"TIMEOUT: external-app delete for '{client_id}' exceeded 60s; leaving it in place", file=sys.stderr)
except Exception as e:
    # Any other failure — network, CLI crash, non-zero exit — is non-fatal.
    # Docstring contract: cleanup failures never fail the test.
    print(f"WARN: external-app delete for '{client_id}' failed: {e}", file=sys.stderr)
sys.exit(0)
