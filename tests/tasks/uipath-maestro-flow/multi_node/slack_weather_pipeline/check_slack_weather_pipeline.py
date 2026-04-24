#!/usr/bin/env python3
"""Slack weather pipeline: Slack connector + HTTP + decision all ran, output has verdict."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    run_debug,
)


def main():
    # Must have both a Slack connector and an HTTP node — proves the pipeline
    # isn't shortcutting by hardcoding the city or skipping the Slack read
    assert_flow_has_node_type(["uipath.connector", "core.action.http"])

    payload = run_debug(timeout=240)

    # Verdict proves the full chain executed: Slack → Script → HTTP → Decision → End
    assert_outputs_contain(
        payload, ["warm office today", "cold office today"], require_all=False
    )
    print("OK: Slack connector + HTTP + decision all executed, verdict present")


if __name__ == "__main__":
    main()
