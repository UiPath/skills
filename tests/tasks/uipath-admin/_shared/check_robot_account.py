#!/usr/bin/env python3
"""Verify a robot account named 'smoke-e2e-bot' exists."""

import json
import subprocess
import sys


def run_cli(args: list[str]) -> dict:
    result = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=30,
    )
    return json.loads(result.stdout)


def main():
    data = run_cli(["admin", "robot-accounts", "list", "--search", "smoke-e2e-bot"])
    assert data["Result"] == "Success", f"robot-accounts list failed: {data}"

    found = any(
        "smoke-e2e-bot" in (r.get("name", "") or "")
        for r in data.get("Data", [])
    )

    if not found:
        print("FAIL: Robot account 'smoke-e2e-bot' not found")
        sys.exit(1)

    print("OK: Robot account 'smoke-e2e-bot' exists")


if __name__ == "__main__":
    main()
