#!/usr/bin/env python3
"""Fail a task as ERROR, not FAILURE, when a native Data Fabric entity node
is unavailable on the tenant.

Usage:
    preflight_native_entity_nodes.py

Checks `uip maestro flow registry get` for all four `core.datafabric.*`
node types. Each is gated by its own tenant feature flag
(`canvas.nodes.{read,create,update,delete}-entity`); per
references/author/plugins/data-fabric/impl.md, the correct agent response
to an unavailable native node is to fall back to the Data Fabric
Integration Service connector — which would make this task's native-node
checks fail through no fault of the skill. A `pre_run` failure lands the
run as `FinalStatus.ERROR` (environment problem) rather than `FAILURE`
(skill defect), the same distinction `_shared/preflight_connections.py`
draws for connector connections.
"""
import json
import subprocess
import sys

NODE_TYPES = [
    "core.datafabric.read",
    "core.datafabric.create",
    "core.datafabric.update",
    "core.datafabric.delete",
]


def main() -> int:
    missing = []
    for node_type in NODE_TYPES:
        r = subprocess.run(
            ["uip", "maestro", "flow", "registry", "get", node_type, "--output", "json"],
            capture_output=True, text=True,
        )
        if r.returncode != 0 or "Node not found" in (r.stdout + r.stderr):
            missing.append(node_type)

    if missing:
        print(
            "FAIL: native Data Fabric entity node(s) unavailable on this tenant: "
            f"{', '.join(missing)}. Run `uip tools update` and "
            "`uip maestro flow registry pull --force`, then retry; if it still "
            "fails, ask the tenant admin about the matching `canvas.nodes.*-entity` "
            "feature flag.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: all native entity node types available: {', '.join(NODE_TYPES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
