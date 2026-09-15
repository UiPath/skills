#!/usr/bin/env python3
"""NameToAge: an API-workflow node executes and the output holds a plausible age."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_int_in_range,
    run_debug,
)


def main():
    assert_flow_has_node_type(["uipath.core.api-workflow"])
    payload = run_debug(timeout=240)
    age = assert_output_int_in_range(payload, 40, 60)
    print(f"OK: API workflow node present; age = {age}")


if __name__ == "__main__":
    main()
