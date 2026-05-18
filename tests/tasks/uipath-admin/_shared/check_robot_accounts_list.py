#!/usr/bin/env python3
"""Verify uip admin robot-accounts list returns Success with a valid array."""

import json
import subprocess
import sys


def main():
    result = subprocess.run(
        ["uip", "admin", "robot-accounts", "list", "--output", "json"],
        capture_output=True, text=True, timeout=30,
    )
    data = json.loads(result.stdout)
    assert data["Result"] == "Success" and data["Code"] == "RobotAccountList", f"Failed: {data}"
    assert isinstance(data["Data"], list), f"Data is not a list: {type(data['Data'])}"
    print(f"OK: {len(data['Data'])} robot account(s) returned")


if __name__ == "__main__":
    main()
