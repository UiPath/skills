#!/usr/bin/env python3
"""post_run teardown for the maestro-flow Jira e2e tasks.

Deletes every issue this task created, by EXACT key — the connection scope
forbids JQL/label sweeps (see jira_is.py § connection-scope note), so there is
no orphan-collecting search. Keys come from two sources, unioned:

  1. ``.created_keys`` — appended by the check (create task) and by the seed
     (get task) as issues are made, so cleanup survives a failed/interrupted
     check.
  2. ``seed.json`` ``issue_key`` — the get task's seed issue.

MUST be idempotent and MUST NOT fail the task: every path is wrapped so the
script always exits 0. A 404 (already gone) counts as success.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jira_is  # noqa: E402

WORKDIR = Path.cwd()


def _load_seed() -> dict:
    for candidate in (WORKDIR / "seed.json",):
        if candidate.is_file():
            try:
                return json.loads(candidate.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
    return {}


def _collect_keys(seed: dict) -> list[str]:
    keys: list[str] = []
    kf = WORKDIR / ".created_keys"
    if kf.is_file():
        keys.extend(kf.read_text().split())
    if seed.get("issue_key"):
        keys.append(seed["issue_key"])
    # de-dup, preserve order
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def main() -> None:
    seed = _load_seed()
    keys = _collect_keys(seed)
    if not keys:
        print("OK: teardown — no created keys to clean up")
        return
    try:
        jira = jira_is.Jira.from_seed(seed)
    except Exception as e:  # noqa: BLE001 — teardown never fails the task
        print(f"WARN: teardown could not bind Jira client ({e}); leaving {keys}")
        return
    for key in keys:
        try:
            jira.delete_issue(key)
            print(f"OK: deleted {key}")
        except Exception as e:  # noqa: BLE001
            print(f"WARN: could not delete {key}: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 — belt and suspenders: always exit 0
        print(f"WARN: teardown error (ignored): {e}")
    sys.exit(0)
