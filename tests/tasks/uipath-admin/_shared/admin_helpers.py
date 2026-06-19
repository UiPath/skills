#!/usr/bin/env python3
"""Shared helpers for uipath-admin check and cleanup scripts."""

import json
import logging
import subprocess
import sys
import time

logger = logging.getLogger(__name__)


def run_cli(args: list[str], timeout: int = 30) -> dict | None:
    """Run a uip CLI command and return parsed JSON, or None on failure."""
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            logger.warning(
                "CLI returned exit code %d: %s",
                result.returncode, result.stderr.strip() or result.stdout.strip(),
            )
            return None
        return json.loads(result.stdout)
    except json.JSONDecodeError:
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


def fail(message: str):
    """Print FAIL message and exit 1."""
    print(f"FAIL: {message}")
    sys.exit(1)


def ok(message: str):
    """Print OK message."""
    print(f"OK: {message}")
