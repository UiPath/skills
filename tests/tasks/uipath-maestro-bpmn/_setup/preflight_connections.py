#!/usr/bin/env python3
"""Fail a task as ERROR, not FAILURE, when the tenant connection it needs is down.

Usage:
    preflight_connections.py <selector> [<selector> ...]

    <selector> := <connector-key>              any live connection will do
                | <connector-key>=<folder>     that folder's connection must be live

A `pre_run` failure lands the run as ``FinalStatus.ERROR``; a criterion failure
lands it as ``FAILURE``. Without this, a revoked grant or an asleep tenant reads
as an agent mistake:

  skill-flow-outlook-trigger-inbox   AADSTS50173, grant revoked 2026-08-31
  skill-flow-generic-dynamic-node    ServiceNow developer instance hibernating

Both were scored FAILURE on 2026-09-04 and root-caused as skill defects before
anyone read far enough into the checker output to find the 403.

The bare form passes when at least one connection for the key answers a ping.
`State` from `connections list` is cached, so a revoked grant still reads
Enabled — per connections.md the selection is verified by ping. Connections live
in several folders, so `--all-folders` is required; without it an empty result
is a false negative.

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
    try:
        proc = subprocess.run(
            ["uip", "is", "connections", "list", key, "--all-folders", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=90,
        )
    except subprocess.TimeoutExpired as exc:
        # Fatal, unlike a ping timeout: without the candidate list there is
        # nothing to fall back to. Reported as a message rather than left to
        # surface as a traceback from inside a pre_run step.
        raise RuntimeError(f"`uip is connections list {key}` did not answer within {exc.timeout:.0f}s") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"`uip is connections list {key}` exited {proc.returncode}: {proc.stderr.strip()}")
    payload = json.loads(proc.stdout)
    if payload.get("Result") != "Success":
        raise RuntimeError(f"connections list for {key} failed: {payload.get('Message', payload)}")
    return payload.get("Data") or []


#: How many times a single connection is pinged before it is called refused.
PING_ATTEMPTS = 3
PING_TIMEOUT_S = 60


def _ping(connection_id: str) -> str | None:
    """``None`` when the connection answers as active, else why it did not.

    A ping that does not answer is RETRIED rather than believed. The call goes
    out to the tenant, several tasks run in parallel, and one hung request is
    not evidence about the connection — it stopped a whole suite once, on a
    connector three sibling tasks pinged clean in the same run, and the
    `TimeoutExpired` came out as a traceback from inside a `pre_run` step
    rather than as a reason. Only a timeout is retried: a connection that
    ANSWERS, saying it is disabled or revoked, is the thing this script exists
    to catch, and asking it again would just be slower.
    """
    last: str | None = None
    for attempt in range(1, PING_ATTEMPTS + 1):
        try:
            proc = subprocess.run(
                ["uip", "is", "connections", "ping", connection_id, "--output", "json"],
                capture_output=True,
                text=True,
                timeout=PING_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            last = f"ping did not answer within {PING_TIMEOUT_S}s ({attempt} of {PING_ATTEMPTS} attempts)"
            continue
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return proc.stderr.strip() or f"ping exited {proc.returncode} with no JSON"
        if payload.get("Result") == "Success" and (payload.get("Data") or {}).get("Status") == "Enabled":
            return None
        return str(payload.get("Message") or payload).strip()
    return last


def _first_live(candidates: list[dict]) -> tuple[dict | None, list[str]]:
    """The first candidate that pings clean, plus why the earlier ones did not.

    `State` from `connections list` is cached, so a revoked grant still reads
    Enabled — the failure mode this whole script exists to catch. Short-circuits,
    so the healthy case costs one ping.
    """
    refused: list[str] = []
    for c in candidates:
        reason = _ping(str(c.get("Id")))
        if reason is None:
            return c, refused
        refused.append(f"{c.get('Name')}@{c.get('Folder')}: {reason}")
    return None, refused


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
        candidates = enabled
        scope = ""
        if folder:
            candidates = [c for c in enabled if c.get("Folder") == folder]
            scope = f" in folder {folder!r}"
            if not candidates:
                where = ", ".join(f"{c.get('Name')}@{c.get('Folder')}" for c in enabled)
                broken.append(f"{key}: no Enabled connection{scope} (Enabled elsewhere: {where})")
                continue

        live, refused = _first_live(candidates)
        if live is None:
            broken.append(f"{key}: no live connection{scope} — {'; '.join(refused)}")
            continue
        print(f"OK: {key} — {live.get('Name')} ({live.get('Id')}) live{scope}")

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
