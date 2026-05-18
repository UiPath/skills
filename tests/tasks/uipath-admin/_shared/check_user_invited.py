#!/usr/bin/env python3
"""Verify john.doe@example.com was invited and appears in users list."""

import json
import subprocess
import sys


def main():
    result = subprocess.run(
        ["uip", "admin", "users", "list", "--search", "john.doe@example.com", "--output", "json"],
        capture_output=True, text=True, timeout=30,
    )
    data = json.loads(result.stdout)
    assert data["Result"] == "Success", f"Failed: {data}"

    found = any(
        "john.doe@example.com" in (u.get("email", "") or u.get("userName", "") or "")
        for u in data.get("Data", [])
    )

    if not found:
        print("FAIL: john.doe@example.com not found in users list")
        sys.exit(1)

    print("OK: john.doe@example.com found in users list")


if __name__ == "__main__":
    main()
