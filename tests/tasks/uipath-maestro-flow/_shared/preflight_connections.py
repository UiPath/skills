#!/usr/bin/env python3
"""Fail a task as ERROR, not FAILURE, when the tenant connection it needs is down.

Usage:
    preflight_connections.py <selector> [<selector> ...]

    <selector> := <connector-key>              any Enabled connection will do
                | <connector-key>=<folder>     that folder's connection must be Enabled

A `pre_run` failure lands the run as ``FinalStatus.ERROR``; a criterion failure
lands it as ``FAILURE``. Without this, a revoked grant or an asleep tenant reads
as an agent mistake:

  skill-flow-outlook-trigger-inbox   AADSTS50173, grant revoked 2026-08-31
  skill-flow-generic-dynamic-node    ServiceNow developer instance hibernating

Both were scored FAILURE on 2026-09-04 and root-caused as skill defects before
anyone read far enough into the checker output to find the 403.

The bare form passes when at least one connection for the key reports Enabled.
Connections live in several folders, so `--all-folders` is required; without it
an empty result is a false negative.

The `=<folder>` form is for a task whose fixture data lives in one specific
workspace. A tenant carries several Enabled connections per connector, and the
one flagged ``IsDefault`` is not necessarily the one holding the fixture:

  skill-flow-slack-channel-description-simulated   default connection reached a
                                                   workspace without the channel

Naming the folder makes that an ERROR identifying the connection rather than a
FAILURE scored against the skill.
"""

from __future__ import annotations

import json
import subprocess
import sys


def _connections(key: str) -> list[dict]:
    proc = subprocess.run(
        ["uip", "is", "connections", "list", key, "--all-folders", "--output", "json"],
        capture_output=True,
        text=True,
        timeout=90,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"`uip is connections list {key}` exited {proc.returncode}: {proc.stderr.strip()}")
    payload = json.loads(proc.stdout)
    if payload.get("Result") != "Success":
        raise RuntimeError(f"connections list for {key} failed: {payload.get('Message', payload)}")
    return payload.get("Data") or []


def main(selectors: list[str]) -> int:
    broken: list[str] = []
    for selector in selectors:
        key, sep, folder = selector.partition("=")
        # A trailing `=` would otherwise fall through to the bare check and
        # silently drop the folder assertion the caller asked for.
        if not key or (sep and not folder):
            broken.append(f"{selector!r}: expected <connector-key> or <connector-key>=<folder>")
            continue
        try:
            conns = _connections(key)
        except Exception as exc:  # noqa: BLE001 — any failure here is a blocked tenant
            broken.append(f"{key}: {exc}")
            continue
        if not conns:
            broken.append(f"{key}: no connection in any folder")
            continue
        enabled = [c for c in conns if c.get("State") == "Enabled"]
        if not enabled:
            states = ", ".join(f"{c.get('Name')}={c.get('State')}" for c in conns)
            broken.append(f"{key}: no Enabled connection ({states})")
            continue
        if not folder:
            print(f"OK: {key} — {len(enabled)}/{len(conns)} connection(s) Enabled")
            continue
        in_folder = [c for c in enabled if c.get("Folder") == folder]
        if not in_folder:
            where = ", ".join(f"{c.get('Name')}@{c.get('Folder')}" for c in enabled) or "none"
            broken.append(
                f"{key}: no Enabled connection in folder {folder!r} (Enabled elsewhere: {where})"
            )
            continue
        named = ", ".join(f"{c.get('Name')} ({c.get('Id')})" for c in in_folder)
        print(f"OK: {key} — Enabled in folder {folder!r}: {named}")

    if broken:
        print(
            "TENANT NOT READY — this is an environment failure, not an agent failure.\n  "
            + "\n  ".join(broken)
            + "\n\nReauthorize the connection, wake the provider instance, or restore the"
            + " named folder's connection, then re-run.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
