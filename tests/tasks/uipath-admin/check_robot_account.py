#!/usr/bin/env python3
"""Verify robot account 'smoke-e2e-bot' exists."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, find_one, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="check_robot: %(message)s")


def main():
    # Poll for eventual consistency
    def find_robot():
        data = run_cli(["admin", "robot-accounts", "list", "--search", "smoke-e2e-bot"])
        if not data or data.get("Result") != "Success":
            return None
        return find_one(data, "smoke-e2e-bot", ["name"])

    if not poll(find_robot):
        fail("Robot account 'smoke-e2e-bot' not found after retries")

    ok("Robot account 'smoke-e2e-bot' exists")


main()
