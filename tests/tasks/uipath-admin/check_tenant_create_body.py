#!/usr/bin/env python3
"""Verify the tenant create body the agent wrote to disk is a valid
CreateTenantRequestDto.

`tenants create` only works via `--file` (the inline path returns
`HTTP 400: The Services field is required.`), and OMS rejects a
`{"<name>": true}` services map on create — `services` must be a plain
string array of catalog names. This check grades that local artifact, so it
works with or without an authenticated tenant.

Target tenant name comes from CHECK_TENANT_NAME. Scans the sandbox working
directory for JSON files and passes when one of them names the fixture tenant
and carries both a non-empty `region` and a `services` list of strings.
"""

import glob
import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import fail, ok

logging.basicConfig(level=logging.INFO, format="check_tenant_create_body: %(message)s")

SKIP_DIRS = ("node_modules", ".git", ".venv", "__pycache__")
MAX_BYTES = 1_000_000


def load_candidates():
    """Yield (path, parsed-dict) for every small JSON object under cwd."""
    for path in glob.glob("**/*.json", recursive=True):
        if any(part in SKIP_DIRS for part in path.replace("\\", "/").split("/")):
            continue
        try:
            if os.path.getsize(path) > MAX_BYTES:
                continue
            with open(path, encoding="utf-8", errors="ignore") as fh:
                body = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(body, dict):
            yield path, body


def name_of(body):
    return str(body.get("name") or body.get("Name") or "")


def services_of(body):
    for key in ("services", "Services"):
        if key in body:
            return body[key]
    return None


def region_of(body):
    return str(body.get("region") or body.get("Region") or "")


def main():
    wanted = (os.environ.get("CHECK_TENANT_NAME") or "").strip()
    if not wanted:
        fail("CHECK_TENANT_NAME not set — cannot identify the create body")

    named = [(p, b) for p, b in load_candidates() if name_of(b) == wanted]
    if not named:
        fail(
            f"no JSON file under the working directory names tenant '{wanted}' — "
            "agent did not write a `tenants create --file` body"
        )

    problems = []
    for path, body in named:
        region = region_of(body)
        services = services_of(body)
        if not region:
            problems.append(f"{path}: missing `region` (required on create)")
            continue
        if isinstance(services, dict):
            problems.append(
                f"{path}: `services` is a {{name: true}} map — that is the "
                "`services add` shape; OMS rejects it on create"
            )
            continue
        if not isinstance(services, list):
            problems.append(f"{path}: `services` is missing or not an array")
            continue
        if not all(isinstance(s, str) for s in services):
            problems.append(f"{path}: `services` must be an array of catalog name strings")
            continue
        ok(
            f"{path} is a valid CreateTenantRequestDto for '{wanted}' "
            f"(region={region}, services={len(services)} name(s))"
        )
        return

    fail("; ".join(problems))


main()
