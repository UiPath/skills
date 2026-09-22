#!/usr/bin/env python3
"""Put a saved dashboard into a placeholder process's slot before a task runs.

The by-id read, update, and delete all need a slot that holds a saved
dashboard, and a fresh eval tenant holds none: every placeholder slot
serves the template. So the slot is seeded in a `pre_run` step, the
mirror of clear_slot.py. The seed is `dashboards copy` from a key no task
writes to, because copy is the one write that authors nothing: the CLI
reads the template, names the copy, and creates. If copy leaves the slot
empty, a create from the template read with a name set is the fallback,
so a copy-only failure does not take the seeded tasks down with it.

Usage: seed_slot.py <process-key>. Idempotent: a slot that already reads
`Saved: true` is left as it is, whatever it holds.

Nothing in this script raises, and it always exits zero, because a failed
seed must never fail the task: the task's own criteria say what the agent
did with the slot it found.
"""

import json
import sys
import tempfile
from pathlib import Path

from _slot import TEMPLATE_SOURCE_KEY, uip_json

SEED_NAME = "Seeded by the uipath-insights eval"


def slot_is_saved(process_key: str) -> bool | None:
    read = uip_json("dashboards", "get", "--process-key", process_key)
    if read is None or read.get("Result") != "Success":
        return None
    return bool((read.get("Data") or {}).get("Saved"))


def seed_by_copy(process_key: str) -> str:
    copied = uip_json(
        "dashboards", "copy",
        "--from-process-key", TEMPLATE_SOURCE_KEY,
        "--to-process-key", process_key,
    )
    return str(((copied or {}).get("Data") or {}).get("CopyState") or "unavailable")


def seed_by_create(process_key: str) -> str:
    """The writes guide's authoring steps 1, 2 and 6 with nothing else changed."""
    with tempfile.TemporaryDirectory() as tmp:
        definition = Path(tmp) / "template.json"
        read = uip_json(
            "dashboards", "get", "--process-key", process_key,
            "--output-file", str(definition),
        )
        if read is None or read.get("Result") != "Success" or not definition.is_file():
            return "template read failed"
        try:
            body = json.loads(definition.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return "template file unreadable"
        body["name"] = SEED_NAME
        body["isVisible"] = True
        definition.write_text(json.dumps(body), encoding="utf-8")
        created = uip_json(
            "dashboards", "create", "--process-key", process_key,
            "--file", str(definition),
        )
        return str(((created or {}).get("Data") or {}).get("SlotState") or "unavailable")


def main(process_key: str) -> None:
    saved = slot_is_saved(process_key)
    if saved is None:
        print(f"seed_slot: slot {process_key} could not be read, leaving it alone")
        return
    if saved:
        print(f"seed_slot: slot {process_key} already holds a saved dashboard")
        return
    print(f"seed_slot: copy into {process_key} -> {seed_by_copy(process_key)}")
    if slot_is_saved(process_key):
        return
    print(f"seed_slot: create into {process_key} -> {seed_by_create(process_key)}")
    print(f"seed_slot: slot {process_key} saved after seeding: {slot_is_saved(process_key)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("seed_slot: usage: seed_slot.py <process-key>")
    else:
        main(sys.argv[1])
    sys.exit(0)
