#!/usr/bin/env python3
"""pre_run: provision the BYOG configuration the task's agent will pin to.

Registers a bring-your-own guardrail configuration named VALIDATOR_NAME
(pii_detection) directly via the CLI — the admin-side prerequisite the
agent under test must NOT be asked to do. Reset semantics: an existing
configuration with that name is deleted first, so reruns start clean
(ValidatorName is unique per tenant).

Fails loudly (non-zero exit) when the tenant does not have the BYOG
feature flag enabled — the task cannot be graded without a real
configuration to discover and pin.
"""
import json
import subprocess
import sys

VALIDATOR_NAME = "byog-smoke-agent-pin"
VALIDATOR_TYPE = "pii_detection"
# create does not probe the connection; any GUID registers. Prefer a real
# Integration Service connection when the tenant has one.
FALLBACK_CONNECTION_ID = "00000000-0000-0000-0000-000000000001"


def uip(*args):
    r = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=120,
    )
    try:
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        return {}


def main() -> None:
    # Reset: remove any leftover configuration with the fixed name.
    existing = uip("guardrails", "byo-configurations", "list")
    if existing.get("Code") == "ByoGuardrailsUnavailable":
        sys.exit(
            "seed_byog.py: BYOG feature is not enabled on this tenant "
            "(ByoGuardrailsUnavailable) — cannot provision the prerequisite "
            "configuration. Enable bring-your-own guardrails on the smoke "
            "tenant, then re-enable this task."
        )
    for c in existing.get("Data") or []:
        if c.get("ValidatorName") == VALIDATOR_NAME and c.get("Id"):
            uip("guardrails", "byo-configurations", "delete", str(c["Id"]), "--force")

    connection_id = FALLBACK_CONNECTION_ID
    connections = uip("is", "connections", "list")
    data = connections.get("Data")
    if isinstance(data, list) and data and isinstance(data[0], dict):
        connection_id = str(
            data[0].get("Id") or data[0].get("id") or FALLBACK_CONNECTION_ID
        )

    created = uip(
        "guardrails", "byo-configurations", "create",
        "--connection-id", connection_id,
        "--validator-name", VALIDATOR_NAME,
        "--validator-type", VALIDATOR_TYPE,
    )
    if created.get("Result") != "Success":
        sys.exit(
            "seed_byog.py: failed to create the BYOG configuration: "
            f"{json.dumps(created)[:500]}"
        )
    print(
        f"seed_byog.py: provisioned {VALIDATOR_NAME} "
        f"(Id={created.get('Data', {}).get('Id')}, connection={connection_id})"
    )


if __name__ == "__main__":
    main()
