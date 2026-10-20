#!/usr/bin/env python3
"""Fail a task as ERROR, not FAILURE, when the memory space it attaches is missing.

Usage:
    preflight_memory_space.py <memory-space>=<folder> [<memory-space>=<folder> ...]

`uip agent memory add` attaches an existing space; it cannot create one. With the
space absent the agent correctly stops, and the task reads FAILURE:

  skill-agent-inline-memory-space   UiPathAgentsSupportMemory missing from
                                    Shared/uipath-agents, 2026-10-20

`--search` is a substring match, so the row must match name and folder exactly.
"""

from __future__ import annotations

import json
import subprocess
import sys

LIST_TIMEOUT_S = 90


def _page(name: str, cursor: str | None) -> dict:
    cmd = [
        "uip", "solution", "resources", "list",
        "--source", "remote", "--kind", "MemorySpace", "--search", name,
        "--output", "json",
    ]
    if cursor:
        cmd += ["--next-page", cursor]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=LIST_TIMEOUT_S)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"`uip solution resources list` did not answer within {exc.timeout:.0f}s") from exc

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(proc.stderr.strip() or f"`uip solution resources list` exited {proc.returncode} with no JSON")

    if proc.returncode != 0 or payload.get("Result") != "Success":
        raise RuntimeError(f"`uip solution resources list` failed: {payload.get('Message', payload)}")

    return payload


def _folders(name: str) -> list[str]:
    """Every folder holding a memory space named exactly ``name``."""
    folders: list[str] = []
    cursor = None
    while True:
        payload = _page(name, cursor)
        folders += [str(r.get("Folder")) for r in payload.get("Data") or [] if r.get("Name") == name]

        cursor = (payload.get("Pagination") or {}).get("NextPage")
        if not cursor:
            return folders


def main(selectors: list[str]) -> int:
    broken: list[str] = []
    for selector in selectors:
        name, _, folder = selector.partition("=")
        if not name or not folder:
            broken.append(f"{selector!r}: expected <memory-space>=<folder>")
            continue

        try:
            folders = _folders(name)
        except Exception as exc:  # noqa: BLE001 — any failure here is a blocked tenant
            broken.append(f"{name}: {exc}")
            continue

        if folder not in folders:
            where = f"found in: {', '.join(folders)}" if folders else "none on the tenant"
            broken.append(f"{name}: not in folder {folder!r} ({where})")
            continue

        print(f"OK: memory space {name} in {folder}")

    if broken:
        print(
            "TENANT NOT READY — this is an environment failure, not an agent failure.\n  "
            + "\n  ".join(broken)
            + "\n\nRecreate the memory space in the named folder, or restore the `uip` login, then re-run.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
