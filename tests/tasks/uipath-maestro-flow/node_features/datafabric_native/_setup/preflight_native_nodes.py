#!/usr/bin/env python3
"""Fail a task as ERROR, not FAILURE, when this CLI build does not carry the
native `core.datafabric.*` nodes.

Usage:
    preflight_native_nodes.py <node-type> [<node-type> ...]

Whether the registry serves these four is a property of the CLI build, not of
the tenant: `pullRemoteNodes` passes a hardcoded `ENABLED_MANIFEST_FLAGS` set as
`getFeatureFlag`, and the entity flags were only added to it in UiPath/cli#4087.
A CLI predating that answers "Node not found" no matter what the tenant is
entitled to, and there is no admin setting that changes the answer.

Without this probe an older `uip` on the runner grades as a skill defect: the
agent correctly falls back to the connector per
`plugins/data-fabric/impl.md#registry-validation`, the native criteria all miss,
and the task reads FAILURE. A `pre_run` failure lands the run as
``FinalStatus.ERROR`` instead, which names the real cause.
"""

from __future__ import annotations

import json
import subprocess
import sys


def _resolves(node_type: str) -> str | None:
    """``None`` when the registry serves the type, else why it did not."""
    proc = subprocess.run(
        ["uip", "maestro", "flow", "registry", "get", node_type, "--output", "json"],
        capture_output=True,
        text=True,
        timeout=90,
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.stderr.strip() or f"registry get exited {proc.returncode} with no JSON"
    if payload.get("Code") != "NodeGetSuccess":
        return payload.get("Message") or f"Code={payload.get('Code')!r}, expected 'NodeGetSuccess'"
    if not (payload.get("Data") or {}).get("Node"):
        return "NodeGetSuccess but Data.Node is empty"
    return None


def main() -> int:
    node_types = sys.argv[1:]
    if not node_types:
        print("usage: preflight_native_nodes.py <node-type> [<node-type> ...]", file=sys.stderr)
        return 2

    failures = []
    for node_type in node_types:
        why = _resolves(node_type)
        if why:
            failures.append((node_type, why))
        else:
            print(f"OK: registry serves {node_type}")

    if failures:
        print(
            "\nThis CLI build does not carry the native Data Fabric nodes, so the\n"
            "native path this task grades cannot be exercised. Upgrade with\n"
            "`uip tools update` (the entity flags landed in UiPath/cli#4087) and\n"
            "`uip maestro flow registry pull --force`.",
            file=sys.stderr,
        )
        for node_type, why in failures:
            print(f"  {node_type}: {why}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
