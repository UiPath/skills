#!/usr/bin/env python3
"""post_run: sweep uploaded `acme-echo` versions off the tenant package feed.

Deletes every version of the `acme-echo` package except the pre-seeded
`0.0.1` baseline, so the next run's patch bump never collides with
`Version already exists`. Sweeping (rather than deleting only this run's
version) also heals debris left by runs whose cleanup never fired.

The uip CLI has no package-delete verb, so deletion calls the
Orchestrator OData API directly (`DELETE /odata/Processes('Id:Version')`)
with the token from the same `.auth` file the CLI reads.

Best-effort, idempotent (NotFound = OK), exits 0 always.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

PACKAGE_ID = "acme-echo"
BASELINE_VERSION = "0.0.1"

AUTH_CANDIDATES = (
    os.path.expanduser("~/.uipath/.auth"),
    "/.uipath/.auth",
)


def read_auth() -> tuple[str, str] | None:
    """Return (bearer_token, orchestrator_base_url) or None."""
    for path in AUTH_CANDIDATES:
        try:
            with open(path, encoding="utf-8") as f:
                pairs = dict(
                    line.strip().split("=", 1) for line in f if "=" in line
                )
        except OSError:
            continue
        token = pairs.get("UIPATH_ACCESS_TOKEN")
        url = (pairs.get("UIPATH_URL") or "").rstrip("/")
        org = pairs.get("UIPATH_ORGANIZATION_NAME")
        tenant = pairs.get("UIPATH_TENANT_NAME")
        if token and url and org and tenant:
            return token, f"{url}/{org}/{tenant}/orchestrator_"
    return None


def feed_versions() -> list[str]:
    r = subprocess.run(
        ["uip", "or", "packages", "versions", PACKAGE_ID, "--output", "json"],
        capture_output=True, text=True, timeout=120,
    )
    try:
        env = json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        return []
    data = env.get("Data") or []
    if isinstance(data, dict):
        data = data.get("Value") or data.get("Items") or data.get("Results") or []
    versions = []
    for item in data:
        if isinstance(item, dict) and item.get("Version"):
            versions.append(str(item["Version"]))
    return versions


def main() -> None:
    auth = read_auth()
    if auth is None:
        print("cleanup: no usable .auth file found — skipping feed sweep")
        return
    token, orchestrator = auth

    for version in feed_versions():
        if version == BASELINE_VERSION:
            continue
        url = f"{orchestrator}/odata/Processes('{PACKAGE_ID}:{version}')"
        req = urllib.request.Request(
            url, method="DELETE",
            headers={
                "Authorization": f"Bearer {token}",
                # Cloudflare rejects urllib's default Python-urllib UA (error 1010)
                "User-Agent": "uipath-skills-tests-cleanup/1.0",
            },
        )
        try:
            urllib.request.urlopen(req, timeout=30)
            print(f"cleanup: deleted {PACKAGE_ID}:{version}")
        except urllib.error.HTTPError as e:
            print(f"cleanup: skipped {PACKAGE_ID}:{version} — HTTP {e.code}")
        except Exception as e:  # noqa: BLE001 — best-effort sweep
            print(f"cleanup: skipped {PACKAGE_ID}:{version} — {e}")


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.exit(0)
