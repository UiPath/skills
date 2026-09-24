#!/usr/bin/env python3
"""Own one dashboard slot for the life of a task: pick it, fill it, clear it.

    slot.py new     write seed.json with a fresh process_key; the slot is free
    slot.py seed    put a saved dashboard into that slot (idempotent)
    slot.py clear   delete whatever is saved in that slot (idempotent)

The key is a fresh GUID per run, on the pattern of uipath-platform's
_setup/seed.py. A fixed placeholder key collided the first day two gate runs
overlapped: skills runs 35721927455 and 35721932318 both ran create_smoke on
the same key a minute apart, one agent created, the other read `Saved: true`
and correctly stopped, and its create criterion failed for a reason that had
nothing to do with the skill. The key belongs to no Maestro process, so a
dashboard saved under it is an orphan nobody's Monitoring tab reads, and
`clear` in post_run removes it.

`seed` copies from a key no task ever writes to, so its slot always serves
the template: copy is the one write that authors nothing, the CLI names the
copy and creates. If the copy leaves the slot empty, a create from the
template read with a name set is the fallback. copy_smoke.yaml reads the same
key as its source.

Nothing here raises, and every command exits zero, because a failed seed or
clear must never fail the task: the task's own criteria say what the agent
did with the slot it found, and the live read at the end says what the slot
holds.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

SEED_FILE = Path("seed.json")
TEMPLATE_SOURCE_KEY = "00000000-0000-0000-0000-00000000000a"
SEED_NAME = "Seeded by the uipath-insights eval"


def uip_json(*args: str) -> dict | None:
    """Run one `uip insights` command and parse its JSON envelope, or None."""
    exe = shutil.which("uip")
    if exe is None:
        return None
    try:
        proc = subprocess.run(
            [exe, "insights", *args, "--output", "json"],
            capture_output=True,
            text=True,
            # copy and delete each make three or four backend calls, and two
            # gate runs can hit the tenant at once; 50 seconds was tight.
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def data_of(envelope: dict | None) -> dict:
    return (envelope or {}).get("Data") or {}


def outcome(envelope: dict | None, key: str) -> str:
    """One line for the run log: the Data field on success, the envelope's
    own words on failure, so a seed or clear that did not land says why."""
    if envelope is None:
        return "no JSON envelope (uip missing, timed out, or printed nothing)"
    value = data_of(envelope).get(key)
    if value is not None:
        return str(value)
    return (
        f"{envelope.get('Result')} / {envelope.get('ErrorCode')}: "
        f"{envelope.get('Message')}"
    )


def read_key() -> str | None:
    try:
        return json.loads(SEED_FILE.read_text(encoding="utf-8"))["process_key"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def slot_is_saved(key: str) -> bool | None:
    read = uip_json("dashboards", "get", "--process-key", key)
    if read is None or read.get("Result") != "Success":
        return None
    return bool(data_of(read).get("Saved"))


def cmd_new() -> None:
    key = str(uuid.uuid4())
    SEED_FILE.write_text(json.dumps({"process_key": key}), encoding="utf-8")
    print(f"slot: new key {key}")


def seed_by_copy(key: str) -> str:
    copied = uip_json(
        "dashboards", "copy",
        "--from-process-key", TEMPLATE_SOURCE_KEY,
        "--to-process-key", key,
    )
    return outcome(copied, "CopyState")


def seed_by_create(key: str) -> str:
    """The writes guide's authoring steps 1, 2 and 6 with nothing else changed."""
    with tempfile.TemporaryDirectory() as tmp:
        definition = Path(tmp) / "template.json"
        read = uip_json(
            "dashboards", "get", "--process-key", key,
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
            "dashboards", "create", "--process-key", key,
            "--file", str(definition),
        )
        return outcome(created, "SlotState")


def cmd_seed(key: str) -> None:
    saved = slot_is_saved(key)
    if saved is None:
        print(f"slot: {key} could not be read, leaving it alone")
        return
    if saved:
        print(f"slot: {key} already holds a saved dashboard")
        return
    print(f"slot: copy into {key} -> {seed_by_copy(key)}")
    if slot_is_saved(key):
        return
    print(f"slot: create into {key} -> {seed_by_create(key)}")
    print(f"slot: {key} saved after seeding: {slot_is_saved(key)}")


def cmd_clear(key: str) -> None:
    read = uip_json("dashboards", "get", "--process-key", key)
    if read is None or read.get("Result") != "Success":
        print(f"slot: {key} could not be read, leaving it alone")
        return
    data = data_of(read)
    if not data.get("Saved"):
        print(f"slot: {key} already serves the template")
        return
    dashboard_id = str(data.get("Id"))
    gone = uip_json("dashboards", "delete", dashboard_id, "--yes")
    print(f"slot: delete of dashboard {dashboard_id} -> {outcome(gone, 'DeleteState')}")


def main(argv: list[str]) -> None:
    command = argv[0] if argv else ""
    if command == "new":
        cmd_new()
        return
    if command not in ("seed", "clear"):
        print("slot: usage: slot.py new | seed | clear")
        return
    key = read_key()
    if key is None:
        print("slot: seed.json has no process_key; run `slot.py new` first")
        return
    (cmd_seed if command == "seed" else cmd_clear)(key)


if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit(0)
