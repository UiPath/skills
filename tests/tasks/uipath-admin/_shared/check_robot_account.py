#!/usr/bin/env python3
"""Verify robot account 'smoke-e2e-bot' exists."""

import logging
import sys

sys.path.insert(0, sys.path[0])
from admin_helpers import run_cli, find_one, fail, ok

logging.basicConfig(level=logging.INFO, format="check_robot: %(message)s")


def main():
    data = run_cli(["admin", "robot-accounts", "list", "--search", "smoke-e2e-bot"])
    if not data or data.get("Result") != "Success":
        fail("robot-accounts list did not return Success")

    if not find_one(data, "smoke-e2e-bot", ["name"]):
        fail("Robot account 'smoke-e2e-bot' not found")

    ok("Robot account 'smoke-e2e-bot' exists")


if __name__ == "__main__":
    main()
