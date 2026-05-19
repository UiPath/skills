#!/usr/bin/env python3
"""post_run cleanup: read created-resources.jsonl and delete each resource via uip.

Reverse dependency order (deepest first), idempotent (NotFound = success),
best-effort (always exits 0; per project pattern in cleanup_solutions.py).

Per-kind handlers know how to call the right `uip ... delete` command for each
resource type the seed scripts and tests create. Unknown kinds are logged + skipped."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

# Ensure _shared/ is importable when invoked via post_run command
sys.path.insert(0, str(Path(__file__).resolve().parent))
from manifest import MANIFEST_FILE, load, sort_for_deletion

logging.basicConfig(level=logging.INFO, format="cleanup_platform: %(message)s")
logger = logging.getLogger(__name__)


def _is_not_found(envelope: dict, stderr: str) -> bool:
    code = (envelope.get("Code") or "").lower()
    msg = (envelope.get("Message") or "").lower()
    instr = (envelope.get("Instructions") or "").lower()
    haystacks = code + " " + msg + " " + instr + " " + stderr.lower()
    return any(
        marker in haystacks
        for marker in (
            "notfound",
            "not found",
            "does not exist",
            "no longer exists",
            "no such",
        )
    )


def _run_uip_delete(args: list[str]) -> tuple[bool, str]:
    """Run a `uip ... delete` command. Returns (success, info)."""
    cmd = ["uip", *args, "--output", "json"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return False, "timeout"
    envelope = {}
    if r.stdout.strip():
        try:
            envelope = json.loads(r.stdout)
        except json.JSONDecodeError:
            pass
    if r.returncode == 0 and envelope.get("Result") == "Success":
        return True, "deleted"
    if _is_not_found(envelope, r.stderr):
        return True, "not-found (idempotent)"
    return False, f"exit {r.returncode}: {(envelope.get('Message') or r.stderr or r.stdout or '').strip()[:200]}"


def _delete_folder(record: dict) -> tuple[bool, str]:
    key = record["key"]
    return _run_uip_delete(["or", "folders", "delete", key])


def _delete_process(record: dict) -> tuple[bool, str]:
    key = record["key"]
    extra = record.get("extra") or {}
    args = ["or", "processes", "delete", key]
    folder_path = extra.get("folder_path")
    if folder_path:
        args += ["--folder-path", folder_path]
    return _run_uip_delete(args)


def _delete_queue(record: dict) -> tuple[bool, str]:
    return _run_uip_delete(["resource", "queues", "delete", record["key"]])


def _delete_queue_item(record: dict) -> tuple[bool, str]:
    extra = record.get("extra") or {}
    args = ["resource", "queue-items", "delete", record["key"]]
    folder_path = extra.get("folder_path")
    if folder_path:
        args += ["--folder-path", folder_path]
    return _run_uip_delete(args)


def _delete_asset(record: dict) -> tuple[bool, str]:
    return _run_uip_delete(["resource", "assets", "delete", record["key"]])


def _delete_bucket(record: dict) -> tuple[bool, str]:
    extra = record.get("extra") or {}
    args = ["resource", "buckets", "delete", record["key"]]
    folder_path = extra.get("folder_path")
    if folder_path:
        args += ["--folder-path", folder_path]
    return _run_uip_delete(args)


def _delete_bucket_file(record: dict) -> tuple[bool, str]:
    extra = record.get("extra") or {}
    bucket_key = extra.get("bucket_key")
    folder_path = extra.get("folder_path")
    path = record["key"]  # we store the path as the key for bucket-files
    if not bucket_key:
        return False, "no bucket_key in extra"
    args = ["resource", "bucket-files", "delete", bucket_key, path]
    if folder_path:
        args += ["--folder-path", folder_path]
    return _run_uip_delete(args)


def _delete_trigger(record: dict) -> tuple[bool, str]:
    extra = record.get("extra") or {}
    args = ["resource", "triggers", "delete", record["key"]]
    trigger_type = extra.get("type")
    folder_path = extra.get("folder_path")
    if trigger_type:
        args += ["--type", trigger_type]
    if folder_path:
        args += ["--folder-path", folder_path]
    return _run_uip_delete(args)


def _delete_webhook(record: dict) -> tuple[bool, str]:
    return _run_uip_delete(["resource", "webhooks", "delete", record["key"]])


def _delete_library(record: dict) -> tuple[bool, str]:
    return _run_uip_delete(["resource", "libraries", "delete", record["key"]])


def _delete_role(record: dict) -> tuple[bool, str]:
    return _run_uip_delete(["or", "roles", "delete-role", record["key"]])


def _delete_deploy(record: dict) -> tuple[bool, str]:
    return _run_uip_delete(["solution", "deploy", "uninstall", record["key"]])


def _delete_solution_package(record: dict) -> tuple[bool, str]:
    extra = record.get("extra") or {}
    version = extra.get("version")
    if not version:
        return False, "no version in extra"
    return _run_uip_delete(["solution", "packages", "delete", record["key"], version])


HANDLERS = {
    "folder": _delete_folder,
    "process": _delete_process,
    "queue": _delete_queue,
    "queue-item": _delete_queue_item,
    "asset": _delete_asset,
    "bucket": _delete_bucket,
    "bucket-file": _delete_bucket_file,
    "trigger": _delete_trigger,
    "webhook": _delete_webhook,
    "library": _delete_library,
    "role": _delete_role,
    "deploy": _delete_deploy,
    "solution-package": _delete_solution_package,
}


def main() -> int:
    records = load(MANIFEST_FILE)
    if not records:
        logger.info("no resources to clean up (manifest empty or absent)")
        return 0

    ordered = sort_for_deletion(records)
    deleted = 0
    skipped = 0
    failed = 0

    for record in ordered:
        kind = record.get("kind", "")
        key = record.get("key", "")
        handler = HANDLERS.get(kind)
        if not handler:
            logger.warning("no handler for kind=%r key=%s — skipping", kind, key)
            skipped += 1
            continue
        try:
            ok, info = handler(record)
        except Exception as e:
            logger.warning("handler raised for kind=%s key=%s: %s", kind, key, e)
            failed += 1
            continue
        if ok:
            logger.info("OK %s %s — %s", kind, key, info)
            deleted += 1
        else:
            logger.warning("FAIL %s %s — %s", kind, key, info)
            failed += 1

    logger.info("summary deleted=%d skipped=%d failed=%d", deleted, skipped, failed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
