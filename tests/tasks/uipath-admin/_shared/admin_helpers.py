#!/usr/bin/env python3
"""Shared helpers for uipath-admin check and cleanup scripts."""

import json
import logging
import subprocess
import sys
import time

logger = logging.getLogger(__name__)


def run_cli(args: list[str], timeout: int = 30, quiet: bool = False) -> dict | None:
    """Run a uip CLI command and return parsed JSON, or None on failure.

    Set quiet=True for commands whose output contains secret material — notably
    `external-apps generate-secret`, which returns the client secret exactly
    once. The error paths below echo stderr/stdout into pre_run logs, and those
    are forwarded verbatim into downloadable CI artifacts, so a non-JSON banner
    or an output-then-nonzero-exit would put the secret in an artifact.
    """
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            if quiet:
                logger.warning("CLI returned exit code %d (output suppressed: may contain a secret)",
                               result.returncode)
            else:
                logger.warning(
                    "CLI returned exit code %d: %s",
                    result.returncode, result.stderr.strip() or result.stdout.strip(),
                )
            return None
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        if quiet:
            logger.warning("CLI returned non-JSON (output suppressed: may contain a secret)")
        else:
            logger.warning("CLI returned non-JSON: %s", result.stdout[:200])
        return None
    except subprocess.TimeoutExpired:
        logger.warning("CLI timed out after %ds", timeout)
        return None
    except Exception as e:
        logger.warning("CLI call failed: %s", e)
        return None


def find_all(data: dict, needle: str, fields: list[str]) -> list[dict]:
    """Find all items in data['Data'] where needle matches exactly in any field."""
    matches = []
    for item in data.get("Data", []):
        for field in fields:
            val = item.get(field) or ""
            if val == needle:
                matches.append(item)
                break
    return matches


def find_one(data: dict, needle: str, fields: list[str]) -> dict | None:
    """Find first item in data['Data'] where needle matches exactly in any field."""
    matches = find_all(data, needle, fields)
    return matches[0] if matches else None


def poll(fn, max_attempts: int = 4, delay: int = 5):
    """Retry fn() up to max_attempts times with delay between attempts.

    Returns the first truthy result. Returns None after all attempts fail.
    Handles eventual consistency in tenant APIs.
    """
    for i in range(max_attempts):
        result = fn()
        if result:
            return result
        if i < max_attempts - 1:
            logger.info("Attempt %d/%d returned falsy — retrying in %ds", i + 1, max_attempts, delay)
            time.sleep(delay)
    return None


def fail(message: str):
    """Print FAIL message and exit 1."""
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message: str):
    """Print OK message."""
    print(f"OK: {message}")


def first_list(o):
    """Return the first list found anywhere in a nested dict/list structure.

    Tolerates how an API/agent wraps a collection (bare list, under a key, or in
    a paginated envelope). Returns None if no list exists.
    """
    if isinstance(o, list):
        return o
    if isinstance(o, dict):
        for v in o.values():
            r = first_list(v)
            if r is not None:
                return r
    return None
