#!/usr/bin/env python3
"""
Post-run cleanup: delete test-created Data Fabric entities via REST API.

Usage (called automatically via task post_run):
    python3 cleanup_entities.py [--entity-id <id>]

Reads entity_id from (in priority order):
  1. --entity-id CLI flag
  2. report.json in CWD

Auth:
  Reads UIP_BEARER_TOKEN and UIP_TENANT_URL from environment.
  If not set, falls back to deriving the tenant URL from `uip login status`
  (org+tenant → https://<org>.uipath.com/<tenant>) while using UIP_BEARER_TOKEN
  for the token. If neither is available, cleanup is skipped with a SKIP message.

  In CI: set UIP_BEARER_TOKEN (and optionally UIP_TENANT_URL) in the env.
  For non-production environments (staging, gov, on-prem), set UIP_TENANT_URL
  explicitly — the derived URL only works for production cloud tenants.
  Locally: cleanup is a no-op — tests still pass.

Deletes via: POST <tenant-url>/dataservice_/api/Entity/<entityId>/delete

Exit 0 always — cleanup failures never fail the test.
"""

import json
import os
import subprocess
import sys
import argparse
import urllib.request
import urllib.error


def get_auth_token() -> tuple[str, str]:
    """Return (token, tenant_url).

    Token source: UIP_BEARER_TOKEN environment variable.
    Tenant URL source: UIP_TENANT_URL env var, or derived from `uip login status`
    as https://<Organization>.uipath.com/<Tenant>.

    uip login status does not expose the Bearer token — it must be supplied via
    env var. In CI, set UIP_BEARER_TOKEN. Locally, cleanup is skipped.
    """
    token = os.environ.get("UIP_BEARER_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "UIP_BEARER_TOKEN env var not set — cleanup requires a Bearer token. "
            "Set it in CI. Skipping locally is expected."
        )

    tenant_url = os.environ.get("UIP_TENANT_URL", "").strip()
    if not tenant_url:
        # Derive from uip login status: https://<org>.uipath.com/<tenant>
        try:
            result = subprocess.run(
                ["uip", "login", "status", "--output", "json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(f"uip login status failed (exit {result.returncode}): {result.stderr}")
            if not result.stdout.strip():
                raise RuntimeError(f"uip login status returned empty output; stderr: {result.stderr}")
            data = json.loads(result.stdout)
            inner = data.get("Data") or data
            org = inner.get("Organization") or ""
            tenant = inner.get("Tenant") or "DefaultTenant"
            if not org:
                raise RuntimeError(f"Could not extract Organization from: {data}")
            tenant_url = f"https://{org}.uipath.com/{tenant}"
            print(
                f"WARN: UIP_TENANT_URL not set — derived {tenant_url} from uip login status. "
                "Set UIP_TENANT_URL explicitly for staging, gov-cloud, or on-prem tenants.",
                file=sys.stderr,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to derive tenant URL: {e}") from e

    return token, tenant_url.rstrip("/")


def delete_entity(tenant_url: str, token: str, entity_id: str) -> None:
    url = f"{tenant_url}/dataservice_/api/Entity/{entity_id}/delete"
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        data=b"{}",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"OK: deleted entity {entity_id} — HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"SKIP: entity {entity_id} not found (already deleted or never created)")
        else:
            raise RuntimeError(f"DELETE {url} returned HTTP {e.code}: {e.read().decode()}") from e


def resolve_entity_ids(args) -> list[str]:
    ids = []

    if args.entity_id:
        ids.append(args.entity_id)
        return ids

    report_path = os.path.join(os.getcwd(), "report.json")
    if not os.path.exists(report_path):
        print(f"SKIP: no report file found at {report_path}")
        return ids

    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        print(f"SKIP: could not parse {report_path}: {e}")
        return ids

    # Collect all entity IDs from the report
    for key in ("entity_id", "tenant_entity_id", "folder_entity_id"):
        val = report.get(key)
        if val and val not in ids:
            ids.append(val)

    if not ids:
        print(f"SKIP: no entity_id keys found in {report_path}")

    return ids


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete test-created Data Fabric entities")
    parser.add_argument("--entity-id", help="Entity ID to delete directly")
    args = parser.parse_args()

    entity_ids = resolve_entity_ids(args)
    if not entity_ids:
        sys.exit(0)

    try:
        token, tenant_url = get_auth_token()
    except RuntimeError as e:
        print(f"SKIP: {e}")
        sys.exit(0)

    for entity_id in entity_ids:
        try:
            delete_entity(tenant_url, token, entity_id)
        except RuntimeError as e:
            print(f"WARN: could not delete entity {entity_id}: {e}")

    sys.exit(0)


if __name__ == "__main__":
    main()
