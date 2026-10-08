#!/usr/bin/env python3
"""Cross-run mutex for the live compliance-pack e2e task.

    python3 _setup/tenant_lock.py acquire   # pre_run, before any pack change
    python3 _setup/tenant_lock.py release   # last post_run step

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
OWNER_FILE = ".compliance-lock-owner"
WAIT_SECONDS = int(os.environ.get("COMPLIANCE_LOCK_WAIT", "1200"))
STALE_SECONDS = int(os.environ.get("COMPLIANCE_LOCK_STALE", "1500"))
POLL_SECONDS = float(os.environ.get("COMPLIANCE_LOCK_POLL", "15"))


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


def lock_entries():
    """[(epoch, owner, key)] for every asset named exactly LOCK_NAME; None if listing failed."""
    payload = run_cli(["or", "assets", "list", "--folder-path", LOCK_FOLDER, "--name", LOCK_NAME])
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


def delete(key):
    return key is not None and run_cli(["or", "assets", "delete", str(key), "--yes"]) is not None


def acquire():
    owner = f"{os.environ.get('GITHUB_RUN_ID', 'local')}-{uuid.uuid4().hex[:12]}"
    deadline = time.time() + WAIT_SECONDS
    while time.time() < deadline:
        now = time.time()
        created = run_cli([
            "or", "assets", "create", LOCK_NAME, f"{owner}|{now:.0f}",
            "--folder-path", LOCK_FOLDER, "--type", "Text",
            "--description", "Held by a coder-eval compliance-pack e2e run; safe to delete if stale.",
        ])
        entries = lock_entries()
        if entries is None:
            log.warning("Cannot list %s/%s — proceeding UNLOCKED", LOCK_FOLDER, LOCK_NAME)
            return
        # Held = the oldest entry is ours, whichever attempt created it (an
        # earlier create may only now be visible to list).
        if entries and entries[0][1] == owner:
            with open(OWNER_FILE, "w") as fh:
                fh.write(owner)
            log.info("Acquired %s/%s as %s", LOCK_FOLDER, LOCK_NAME, owner)
            return
        ours = [key for _, o, key in entries if o == owner]
        if ours:
            # A duplicate slipped through and an older holder wins: back off.
            for key in ours:
                delete(key)
            log.info("Lost tie-break to %s — waiting", entries[0][1])
        elif entries:
            epoch, holder, key = entries[0]
            age = now - epoch
            if age > STALE_SECONDS:
                log.warning("Breaking stale lock held by %s (%.0fs old)", holder, age)
                delete(key)
                continue
            log.info("Held by %s for %.0fs — waiting", holder, age)
        elif created:
            log.info("Created but not listed yet — rechecking")
            time.sleep(3)
            continue
        else:
            log.warning("Create failed and no lock exists — lock unusable, proceeding UNLOCKED")
            return
        time.sleep(POLL_SECONDS + random.uniform(0, 5))
    log.warning("Waited %ss without the lock — proceeding UNLOCKED", WAIT_SECONDS)


def release():
    if not os.path.exists(OWNER_FILE):
        log.info("This run does not hold the lock — nothing to release")
        return
    with open(OWNER_FILE) as fh:
        owner = fh.read().strip()
    for _, o, key in lock_entries() or []:
        if o == owner:
            log.info("Released %s/%s (%s)", LOCK_FOLDER, LOCK_NAME,
                     "deleted" if delete(key) else "DELETE FAILED — will go stale")
            return
    log.warning("Lock entry for %s not found at release", owner)


if __name__ == "__main__":
    {"acquire": acquire, "release": release}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: log.error("usage: tenant_lock.py acquire|release"))()
    sys.exit(0)
