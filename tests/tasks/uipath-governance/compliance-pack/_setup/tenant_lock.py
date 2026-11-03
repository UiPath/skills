#!/usr/bin/env python3
"""Cross-run mutex for the live compliance-pack e2e task.

DO NOT COPY. This is a one-off for `full_apply_e2e_live`, the only task that
still changes the real pack. Its timeouts are budgeted for that one task's
copies across the three nightly runs; a second user (worse, under the same
LOCK_NAME) outgrows that budget, so more copies run unlocked and timed-out
pre_run steps become routine. A task that touches tenant-wide state should
run against the `uip` shim (mock_template/mocks/uip) instead.

    python3 _setup/tenant_lock.py acquire     # pre_run, before any pack change
    python3 _setup/tenant_lock.py may-clean   # exit 1: skip the live cleanup
    python3 _setup/tenant_lock.py release     # last post_run step

Compliance-pack state is tenant-global, and the claude / codex / delegate
nightly runs all start at 04:00 UTC on the same test tenant. The smoke tasks
run against a `uip` shim (mock_template/mocks/uip), so `full_apply_e2e_live`
is the only task that still enables / disables the real pack — but its
copies in the concurrent runs would still undo each other mid-run. This lock
serialises them.

The lock is an Orchestrator Text asset (`LOCK_NAME` in `LOCK_FOLDER`) whose
value is `<owner>|<epoch>`. Asset names are unique per folder, so a second
`assets create` fails while the lock is held. Belt and braces, in case a
duplicate ever slips through: after a successful create the script lists the
lock entries and only the oldest `<epoch>|<owner>` keeps it — the others
delete their own entry and wait.

A holder older than STALE_SECONDS is treated as a crashed run (its post_run
never released) and the lock is broken.

Never gates the task: always exits 0. If the lock cannot be used at all (no
auth, folder missing, CLI error) or WAIT_SECONDS pass, it logs why and lets
the task proceed unlocked — the pre-lock behaviour.

The one exception is `may-clean`, which exits 1 when this run saw another
run hold the lock and never got it itself. The task's live cleanup disables
the pack, so running it then would undo the holder mid-run; the task skips
it and takes the false red alone. A run that is unlocked because the lock is
unusable still cleans up, as before the lock existed.
"""

import json
import logging
import os
import random
import subprocess
import sys
import time
import uuid

logging.basicConfig(level=logging.INFO, format="tenant_lock: %(message)s")
log = logging.getLogger(__name__)

LOCK_NAME = "coder-eval-compliance-pack-lock"
LOCK_FOLDER = os.environ.get("COMPLIANCE_LOCK_FOLDER", "Shared")
OWNER_FILE = ".compliance-lock-owner"      # written once the lock is held
PENDING_FILE = ".compliance-lock-pending"  # this run's owner id, written before the first create
CONTENDED_FILE = ".compliance-lock-contended"  # another run was seen holding the lock
WAIT_SECONDS = float(os.environ.get("COMPLIANCE_LOCK_WAIT", "1200"))
# A holder lives through the rest of pre_run (2 x 300s steps + 120s cleanup),
# the agent (task_timeout 1200s in the nightly/default experiments), grading,
# and post_run (2 x 120s): ~2300s. Only an entry older than that is a crash.
STALE_SECONDS = float(os.environ.get("COMPLIANCE_LOCK_STALE", "2400"))
POLL_SECONDS = float(os.environ.get("COMPLIANCE_LOCK_POLL", "15"))
CALL_SECONDS = 60.0   # per CLI call, further capped by the time left
MIN_CALL_SECONDS = 5.0


def run_cli(args, timeout=60):
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        log.warning("`uip %s` failed: %s", " ".join(args), e)
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = None
    if result.returncode != 0 or not payload or payload.get("Result") != "Success":
        log.info("`uip %s` → exit %d: %s", " ".join(args), result.returncode,
                 (result.stdout or result.stderr).strip()[:300])
        return None
    return payload


def field(entry, *names):
    """Case-insensitive lookup — the CLI's casing for asset fields is not pinned."""
    lowered = {k.lower(): v for k, v in entry.items()}
    for name in names:
        if lowered.get(name.lower()) not in (None, ""):
            return lowered[name.lower()]
    return None


def lock_entries(timeout=CALL_SECONDS):
    """[(epoch, owner, key)] for every asset named exactly LOCK_NAME; None if listing failed."""
    payload = run_cli(["or", "assets", "list", "--folder-path", LOCK_FOLDER, "--name", LOCK_NAME], timeout=timeout)
    if payload is None:
        return None
    data = payload.get("Data")
    if isinstance(data, dict):
        data = field(data, "Value", "Items", "Result", "Assets") or []
    out = []
    for entry in data if isinstance(data, list) else []:
        if not isinstance(entry, dict) or field(entry, "Name") != LOCK_NAME:
            continue
        value = str(field(entry, "StringValue", "Value", "ValueText") or "")
        owner, _, epoch = value.rpartition("|")
        try:
            epoch = float(epoch)
        except ValueError:
            epoch = 0.0  # unreadable holder → treated as stale
        out.append((epoch, owner, field(entry, "Key", "Id")))
    return sorted(out, key=lambda e: (e[0], e[1]))


def delete(key, timeout=CALL_SECONDS):
    return key is not None and run_cli(["or", "assets", "delete", str(key), "--yes"], timeout=timeout) is not None


def read_file(path):
    try:
        with open(path) as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def acquire():
    # coder-eval caps each pre_run step at 300s, so the task chains two acquire
    # steps to wait longer; the second is a no-op once the first got the lock.
    if os.path.exists(OWNER_FILE):
        log.info("Already held by this run — nothing to do")
        return
    # One owner across both steps: if step 1 was killed after its create, step 2
    # recognises that entry as its own instead of waiting behind it.
    owner = read_file(PENDING_FILE)
    if not owner:
        owner = f"{os.environ.get('GITHUB_RUN_ID', 'local')}-{uuid.uuid4().hex[:12]}"
        with open(PENDING_FILE, "w") as fh:
            fh.write(owner)
    created_keys = []  # every lock entry this run created, for cleanup if it gives up
    deadline = time.time() + WAIT_SECONDS

    def left():
        return deadline - time.time()

    def call_timeout():
        return max(1.0, min(CALL_SECONDS, left()))

    def give_up(reason):
        # Never leave an entry behind when proceeding unlocked: an orphan would
        # block every other run's create until it goes stale.
        keys = set(created_keys) | {key for _, o, key in lock_entries(timeout=15) or [] if o == owner}
        for key in keys:
            if not delete(key, timeout=15):
                log.warning("Could not delete own lock entry %s — it will go stale", key)
        log.warning("%s — proceeding UNLOCKED", reason)

    while left() > MIN_CALL_SECONDS:
        now = time.time()
        created = run_cli([
            "or", "assets", "create", LOCK_NAME, f"{owner}|{now:.0f}",
            "--folder-path", LOCK_FOLDER, "--type", "Text",
            "--description", "Held by a coder-eval compliance-pack e2e run; safe to delete if stale.",
        ], timeout=call_timeout())
        if created and isinstance(created.get("Data"), dict):
            key = field(created["Data"], "Key", "Id")
            if key is not None:
                created_keys.append(key)
        entries = lock_entries(timeout=call_timeout())
        if entries is None:
            give_up(f"Cannot list {LOCK_FOLDER}/{LOCK_NAME}")
            return
        # Held = the oldest entry is ours, whichever attempt (or step) created it.
        if entries and entries[0][1] == owner:
            with open(OWNER_FILE, "w") as fh:
                fh.write(owner)
            log.info("Acquired %s/%s as %s", LOCK_FOLDER, LOCK_NAME, owner)
            return
        if entries:
            # Written before any wait, so a step killed mid-wait still counts as contended.
            open(CONTENDED_FILE, "w").close()
        ours = [key for _, o, key in entries if o == owner]
        if ours:
            # A duplicate slipped through and an older holder wins: back off.
            for key in ours:
                if delete(key, timeout=call_timeout()) and key in created_keys:
                    created_keys.remove(key)
            log.info("Lost tie-break to %s — waiting", entries[0][1])
        elif entries:
            epoch, holder, key = entries[0]
            age = now - epoch
            if age > STALE_SECONDS:
                log.warning("Breaking stale lock held by %s (%.0fs old)", holder, age)
                if delete(key, timeout=call_timeout()):
                    continue
                log.warning("Could not delete the stale lock — backing off")
            log.info("Held by %s for %.0fs — waiting", holder, age)
        elif created:
            log.info("Created but not listed yet — rechecking")
            time.sleep(min(3.0, max(0.0, left())))
            continue
        else:
            give_up("Create failed and no lock exists — lock unusable")
            return
        time.sleep(min(POLL_SECONDS + random.uniform(0, 5), max(0.0, left())))
    give_up(f"Waited {WAIT_SECONDS:.0f}s without the lock")


def release():
    owner = read_file(OWNER_FILE) or read_file(PENDING_FILE)
    if not owner:
        log.info("This run never took part in the lock — nothing to release")
        return
    mine = [key for _, o, key in lock_entries() or [] if o == owner]
    for key in mine:
        log.info("Released %s/%s (%s)", LOCK_FOLDER, LOCK_NAME,
                 "deleted" if delete(key) else "DELETE FAILED — will go stale")
    if not mine:
        log.info("No lock entry for %s at release", owner)
    for path in (OWNER_FILE, PENDING_FILE, CONTENDED_FILE):
        if os.path.exists(path):
            os.remove(path)


def may_clean():
    """False only when another run held the lock and this run never got it."""
    if os.path.exists(CONTENDED_FILE) and not os.path.exists(OWNER_FILE):
        log.warning("Another run holds the lock — skipping the live cleanup so it is not undone mid-run")
        return False
    return True


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "may-clean":
        sys.exit(0 if may_clean() else 1)
    {"acquire": acquire, "release": release}.get(command, lambda: log.error("usage: tenant_lock.py acquire|may-clean|release"))()
    sys.exit(0)
