#!/usr/bin/env python3
"""pre_run: provision the BYOG configuration the task's agent will pin to.

Registers a bring-your-own guardrail configuration named VALIDATOR_NAME
(pii_detection) directly via the CLI — the admin-side prerequisite the
agent under test must NOT be asked to do. Reset semantics: an existing
configuration with that name is deleted first, so reruns start clean
(ValidatorName is unique per tenant).

The configuration is deliberately backed by an inert placeholder GUID,
never a real Integration Service connection: binding a live credentialed
connection to a guardrail provider would route guardrail payloads (which
can carry PII) to whatever third-party service that connection points at.
This task only pins the configuration in agent.json — the guardrail is
never executed — so the connection does not need to resolve
(`ValidConnection` simply reads false).

Fails closed (non-zero exit) whenever tenant state cannot be read or
reset — including when the BYOG feature flag is off — so the task never
runs against unknown state.
"""
import json
import subprocess
import sys

VALIDATOR_NAME = "byog-smoke-agent-pin"
VALIDATOR_TYPE = "pii_detection"
# Inert by design — see module docstring. create does not probe it.
PLACEHOLDER_CONNECTION_ID = "00000000-0000-0000-0000-000000000001"


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
    existing = uip("guardrails", "byo-configurations", "list")
    if existing.get("Code") == "ByoGuardrailsUnavailable":
        sys.exit(
            "seed_byog.py: BYOG feature is not enabled on this tenant "
            "(ByoGuardrailsUnavailable) — cannot provision the prerequisite "
            "configuration. Enable bring-your-own guardrails on the smoke "
            "tenant, then re-enable this task."
        )
    if existing.get("Result") != "Success":
        sys.exit(
            "seed_byog.py: could not read the tenant's BYOG configurations "
            f"— refusing to seed against unknown state: {json.dumps(existing)[:500]}"
        )

    # Reset: remove any leftover configuration with the fixed name. A failed
    # delete means the create below would hit the tenant-unique-name check
    # against a stale record — fail closed instead.
    for c in existing.get("Data") or []:
        if c.get("ValidatorName") == VALIDATOR_NAME and c.get("Id"):
            deleted = uip(
                "guardrails", "byo-configurations", "delete",
                str(c["Id"]), "--force",
            )
            if deleted.get("Result") != "Success":
                sys.exit(
                    "seed_byog.py: failed to delete leftover configuration "
                    f"{c['Id']}: {json.dumps(deleted)[:500]}"
                )

    created = uip(
        "guardrails", "byo-configurations", "create",
        "--connection-id", PLACEHOLDER_CONNECTION_ID,
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
        f"(Id={created.get('Data', {}).get('Id')})"
    )


if __name__ == "__main__":
    main()
