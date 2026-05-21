#!/usr/bin/env python3
"""Verify john.doe@example.com was invited and appears in users list."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, find_one, fail, ok

logging.basicConfig(level=logging.INFO, format="check_user: %(message)s")


def main():
    data = run_cli(["admin", "users", "list", "--search", "john.doe@example.com"])
    if not data or data.get("Result") != "Success":
        fail("users list did not return Success")

    if not find_one(data, "john.doe@example.com", ["email", "userName"]):
        fail("john.doe@example.com not found in users list")

    ok("john.doe@example.com found in users list")


main()
