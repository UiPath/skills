#!/usr/bin/env python3
"""Verify a Jira connection exists on the tenant for the given connector key.

Usage:
    check_connection_available.py <connector_key>

Runs `uip is connections list <connector_key> --output json` and inspects the
response. Fails with a clear, actionable message when the tenant has no
connection — this is a precondition for the path-params eval, since
`uip maestro flow node configure` rejects an empty `connectionId` and the
agent is forced into hand-authored `inputs.detail` (which is harder to verify).

Exit codes:
  0 — at least one connection found
  1 — no connection found OR CLI error (message printed to stderr)
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from typing import NoReturn


def _fail(message: str) -> NoReturn:
    sys.exit(f"FAIL: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        _fail("usage: check_connection_available.py <connector_key>")

    connector_key = sys.argv[1]

    uip = shutil.which("uip")
    if uip is None:
        _fail(
            "`uip` binary not on PATH — cannot verify connection availability. "
            "Install with: npm install -g @uipath/cli@latest"
        )

    try:
        proc = subprocess.run(
            [
                uip,
                "is",
                "connections",
                "list",
                connector_key,
                "--all-folders",
                "--refresh",
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        _fail(f"`uip is connections list {connector_key}` timed out after 30s")

    if proc.returncode != 0:
        _fail(
            f"`uip is connections list {connector_key}` exited {proc.returncode}: "
            f"{(proc.stderr or proc.stdout).strip()[:500]}"
        )

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        _fail(f"CLI returned non-JSON output: {exc}; raw: {proc.stdout[:300]!r}")

    data = payload.get("Data")
    connections: list[dict] = []
    if isinstance(data, list):
        connections = data
    elif isinstance(data, dict):
        message = data.get("Message", "")
        if "No connections found" in str(message):
            _fail(
                f"No connection found on the tenant for connector {connector_key!r}. "
                f"This eval requires at least one configured connection so the agent can "
                f"run `uip maestro flow node configure` with a real `connectionId`. "
                f"Without one, the CLI rejects the configure call and the agent is forced "
                f"to hand-author `inputs.detail`, which is out of scope for this task. "
                f"Fix: add a Jira connection in Integration Service for the test tenant, "
                f"or update the task to target a connector that has a live connection."
            )
        nested = data.get("Connections") or data.get("value")
        if isinstance(nested, list):
            connections = nested

    if not connections:
        _fail(
            f"No connection found on the tenant for connector {connector_key!r} "
            f"(CLI returned an empty list). See above for remediation."
        )

    print(
        f"OK: {len(connections)} connection(s) available for {connector_key!r} "
        f"(first: {connections[0].get('Name', '<unnamed>')})"
    )


if __name__ == "__main__":
    main()
