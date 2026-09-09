#!/usr/bin/env python3
"""Verify a PAT with the smoke marker description was created on the tenant.

Reads the PAT collection back from the live tenant (not the agent's output) and
asserts a token with the marker description exists and carries scopes. Exits 0
on success (ok), 1 on failure (fail) so a run_command criterion can gate on it.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_pat: %(message)s")

MARKER = "ce-identity-smoke-pat"


def main():
    def find():
        data = run_cli(["admin", "pat", "list"])
        if not data or data.get("Result") != "Success":
            return None
        for t in data.get("Data", []):
            # PAT records use PascalCase Description; tolerate camelCase too.
            desc = t.get("Description") or t.get("description") or ""
            if desc == MARKER:
                return t
        return None

    tok = poll(find)
    if not tok:
        fail(f"no PAT with description '{MARKER}' found after retries — create may have failed")
    scopes = tok.get("Scopes") or tok.get("scopes")
    if not scopes:
        fail(f"PAT '{MARKER}' exists but carries no Scopes: {tok}")
    expiration = tok.get("Expiration") or tok.get("expiration")
    if not expiration:
        fail(f"PAT '{MARKER}' created but has no Expiration: {tok}")
    ok(f"PAT '{MARKER}' created with scopes={scopes} expiration={expiration}")


main()
